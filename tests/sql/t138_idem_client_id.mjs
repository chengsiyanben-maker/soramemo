// 印と便の「送り直しても二重にならない」仕組み（移行 200・data/idem）
//   1. checkins・flights・manual_flights・intl_flights に client_id（uuid・null 可）が足される。前からの行は null のまま
//   2. 同じ人・同じ client_id は2行にならない（関数 checkin の2回目・同時に2回）。null どうし・別の人の同じ ID は入る
//   3. 画面からの記録帳・国際線の記録は upsert（on conflict (user_id, client_id) do nothing）で送り直しても1行
//   4. 権限・RLS は前のまま：利用者は checkins・flights に書けない。記録帳は本人の分だけ・client_id は update で変えられない
//   5. もう一度流しても同じ・lock_timeout は元に戻る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated;
alter default privileges in schema public grant all on sequences to anon, authenticated;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_idem_client_id.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } finally { await db.exec('reset role'); } };
const asUser = async (uid, sql) => { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); try { return (await db.query(sql)).rows; } finally { await db.exec('reset role'); } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 200 番', /^\d{8}000200_idem_client_id\.sql$/.test(mine), mine);

const A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
const C1 = '0193a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5b', C2 = '0193a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5c';
const ap = await q1(`select string_agg(id::text, ',' order by id) from (select id from public.airports where game_target order by id limit 2) x`);
const [P1, P2] = ap.split(',');
// 前からの印・便・記録帳（移行の前）
await db.exec(`insert into auth.users (id) values ('${A}'),('${B}');
insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values ('${A}', ${P1}, 35.5, 139.7, 20, now(), now() - interval '3 hours');
insert into public.manual_flights (user_id, from_airport, to_airport, flown_on) values ('${A}', ${P1}, ${P2}, '2025-05-01');`);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. 列
for (const t of ['checkins', 'flights', 'manual_flights', 'intl_flights']) {
  check(`${t}.client_id は uuid・null 可`, await q1(`select data_type || ':' || is_nullable from information_schema.columns where table_schema='public' and table_name='${t}' and column_name='client_id'`) === 'uuid:YES', null);
}
check('前からの印と記録帳の client_id は null', await q1(`select count(*)::int from public.checkins where client_id is null`) === 1 && await q1(`select count(*)::int from public.manual_flights where client_id is null`) === 1, null);

// 2. 関数 checkin と同じ書き方（service_role）で
const ins = (uid, cid) => `insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, client_id) values ('${uid}', ${P2}, 35.5, 139.7, 20, now(), ${cid ? `'${cid}'` : 'null'})`;
await db.exec(ins(A, C1));
check('同じ人・同じ ID の2回目の印は入らない（23505）', await (async () => { try { await db.exec(ins(A, C1)); return false; } catch (e) { return e.code === '23505'; } })(), null);
check('ID の大文字小文字が違っても同じ ID（uuid として比べる）', await fails(ins(A, C1.toUpperCase())), null);
await db.exec(ins(A, null)); await db.exec(ins(A, null));
check('ID なし（null）は何回でも入る（前と同じ）', await q1(`select count(*)::int from public.checkins where user_id='${A}' and client_id is null`) === 3, null);
await db.exec(ins(B, C1));
check('別の人の同じ ID は入る', await q1(`select count(*)::int from public.checkins where client_id='${C1}'`) === 2, null);
check('2回目の印を ID で1行だけ引ける', await q1(`select count(*)::int from public.checkins where user_id='${A}' and client_id='${C1}'`) === 1, null);
// 便：着いた印と同じ ID
const dep = await q1(`select id from public.checkins where user_id='${A}' and client_id is null order by created_at limit 1`);
const arr = await q1(`select id from public.checkins where user_id='${A}' and client_id='${C1}'`);
const fins = `insert into public.flights (user_id, from_airport, to_airport, dep_checkin, arr_checkin, dep_at, arr_at, distance_km, client_id) values ('${A}', ${P1}, ${P2}, ${dep}, ${arr}, now() - interval '3 hours', now(), 500, '${C1}')`;
await db.exec(fins);
check('同じ ID の便は2つにならない', await fails(fins), null);
check('送り直しで、着いた印から便を引ける', await q1(`select count(*)::int from public.flights where user_id='${A}' and arr_checkin=${arr}`) === 1, null);
check('ID で引く索引がある（checkins_user_cid）', await q1(`select count(*)::int from pg_indexes where indexname in ('checkins_user_cid','flights_user_cid','manual_flights_user_cid','intl_flights_user_cid')`) === 4, null);

// 3. 記録帳・国際線の記録（本人が画面から）
const up = `insert into public.manual_flights (from_airport, to_airport, flown_on, client_id) values (${P1}, ${P2}, '2025-06-01', '${C2}') on conflict (user_id, client_id) do nothing returning id`;
check('記録帳：1回目は1行入る', (await asUser(A, up)).length === 1, null);
check('記録帳：送り直し（同じ ID の upsert）は0行・エラーにならない', (await asUser(A, up)).length === 0, null);
check('記録帳：同じ ID の行は1つ', await q1(`select count(*)::int from public.manual_flights where client_id='${C2}'`) === 1, null);
check('記録帳：別の人は同じ ID でも入る', (await asUser(B, up)).length === 1, null);
const iup = `insert into public.intl_flights (flown_on, dep, arr, client_id) values ('2025-06-01', 'HND', 'LAX', '${C2}') on conflict (user_id, client_id) do nothing returning id`;
const iupOk = await (async () => { try { return [(await asUser(A, iup)).length, (await asUser(A, iup)).length]; } catch (e) { return e.message; } })();
check('国際線の記録：送り直しても1行', JSON.stringify(iupOk) === '[1,0]', iupOk);

// 4. 権限・RLS
check('利用者は checkins に書けない', await fails(`set role authenticated; select set_config('request.jwt.claim.sub','${A}',false); ${ins(A, C2)}`), null);
check('利用者は checkins の client_id を書き換えられない', await fails(`set role authenticated; select set_config('request.jwt.claim.sub','${A}',false); update public.checkins set client_id = null`), null);
check('利用者は flights に書けない', await fails(`set role authenticated; update public.flights set client_id = null`), null);
check('記録帳の client_id は update で変えられない', await fails(`set role authenticated; select set_config('request.jwt.claim.sub','${A}',false); update public.manual_flights set client_id = null`), null);
check('ほかの人の記録帳は読めない（ID も見えない）', (await asUser(B, `select client_id from public.manual_flights`)).length === 1, null);
check('自分の印の client_id は読める', (await asUser(A, `select client_id from public.checkins where client_id is not null`)).length === 1, null);
check('ほかの人の印は読めない', (await asUser(B, `select 1 from public.checkins where user_id='${A}'`)).length === 0, null);
for (const t of ['checkins', 'flights', 'manual_flights', 'intl_flights']) check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid='public.${t}'::regclass`) === true, null);
check('anon は記録帳を読めない', await (async () => { try { await db.exec('set role anon'); return (await db.query('select * from public.manual_flights')).rows.length === 0; } catch { return true; } finally { await db.exec('reset role'); } })(), null);

// 5. もう一度
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても列は4つ・行はそのまま', await q1(`select count(*)::int from information_schema.columns where table_schema='public' and column_name='client_id' and table_name in ('checkins','flights','manual_flights','intl_flights')`) === 4
  && await q1(`select count(*)::int from public.checkins where client_id='${C1}'`) === 2, null);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
