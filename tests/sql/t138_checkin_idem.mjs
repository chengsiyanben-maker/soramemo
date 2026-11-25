// 印と便の「送り直しても二重にならない」仕組み（移行 200・data/idem）
//   1. checkins.client_id：同じ人の同じ ID は2つ入らない。別の人なら同じ ID でもよい。null は何件でもよい（今までの印）
//   2. flights：1つの到着の印から便は1つだけ。arr_checkin が null の便は何件でもよい
//   3. 本番に同じ arr_checkin の便が2行あると、索引を作らずに通る（止まらない）。片付いたあとでもう一度流すと作る
//   4. manual_flights.client_id：本人が on conflict do nothing で2回送っても1行。client_id は直せない・price などは今までどおり直せる
//   5. 権限：利用者は checkins・flights に書けない。RLS は ON のまま。もう一度流しても同じ・lock_timeout は元に戻る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;  -- Supabase の初めの権限と同じ（移行が外したものだけ外れる）`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_checkin_idem.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
let lastErr = null;
const fails = async (sql) => { try { await db.exec(sql); return false; } catch (e) { lastErr = e.message; return true; } finally { await db.exec('reset role'); } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 200 番', /^\d{8}000200_checkin_idem\.sql$/.test(mine), mine);

const U1 = '11111111-1111-4111-8111-111111111111', U2 = '22222222-2222-4222-8222-222222222222';
const C1 = '0193a6f2-7b1c-7d2e-8f00-1234567890ab';
await db.exec(`insert into auth.users (id) values ('${U1}'), ('${U2}')`);
const A = await q1(`select min(id) from public.airports`), B = await q1(`select min(id) from public.airports where id > (select min(id) from public.airports)`);
const ci = (u, cid) => `insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at${cid === undefined ? '' : ', client_id'})
  values ('${u}', ${A}, 35.55, 139.78, 20, now()${cid === undefined ? '' : `, ${cid === null ? 'null' : `'${cid}'`}`}) returning id`;
// 前からある印（列がまだない）
await db.exec(ci(U1));
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. checkins
check('checkins.client_id は uuid', await q1(`select data_type from information_schema.columns where table_name = 'checkins' and column_name = 'client_id'`) === 'uuid', null);
check('前からある印の client_id は null', await q1(`select count(*)::int from public.checkins where client_id is null`) === 1, null);
const first = await q1(ci(U1, C1));
check('同じ人・同じ ID の2つ目は入らない', await fails(ci(U1, C1)), null);
check('別の人なら同じ ID でもよい', !(await fails(ci(U2, C1))), null);
check('ID なし（null）は何件でもよい', !(await fails(ci(U1, null))) && !(await fails(ci(U1, null))), null);
check('ID で1行を引ける（索引 checkins_user_client）', await q1(`select id from public.checkins where user_id = '${U1}' and client_id = '${C1}'`) === first
  && await q1(`select count(*)::int from pg_indexes where indexname = 'checkins_user_client' and indexdef like '%UNIQUE%'`) === 1, null);

// 2. flights
const fl = (arr) => `insert into public.flights (user_id, from_airport, to_airport, arr_checkin, dep_at, arr_at, distance_km)
  values ('${U1}', ${B}, ${A}, ${arr === null ? 'null' : arr}, now() - interval '2 hours', now(), 500)`;
const uniq = async () => await q1(`select coalesce((select indisunique from pg_index where indexrelid = to_regclass('public.flights_arr_checkin')), false)`);
check('索引 flights_arr_checkin が一意になった（名前は同じ・同じ形の索引は1本だけ）', await uniq() === true
  && await q1(`select count(*)::int from pg_indexes where tablename = 'flights' and indexdef like '%(arr_checkin)%'`) === 1, null);
check('1つ目の便は入る', !(await fails(fl(first))), null);
check('同じ到着の印から2つ目の便は入らない', await fails(fl(first)), null);
check('arr_checkin が null の便は何件でもよい', !(await fails(fl(null))) && !(await fails(fl(null))), null);

// 3. 同じ arr_checkin の便が本番にあったとき
await db.exec(`drop index public.flights_arr_checkin; create index flights_arr_checkin on public.flights (arr_checkin) where arr_checkin is not null`);  // 188 のあとの形に戻す
await db.exec(fl(first));
let threw = false; try { await db.exec(fs.readFileSync(dir + mine, 'utf8')); } catch { threw = true; }
check('重なった便があっても移行は止まらない・索引は一意にしない（前の索引は残る）', !threw && await uniq() === false
  && await q1(`select count(*)::int from pg_indexes where indexname = 'flights_arr_checkin'`) === 1, threw);
check('重なった便は消さない（2行のまま）', await q1(`select count(*)::int from public.flights where arr_checkin = ${first}`) === 2, null);
await db.exec(`update public.flights set arr_checkin = null where id = (select max(id) from public.flights where arr_checkin = ${first})`);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('片付いたあとでもう一度流すと一意にする', await uniq() === true, null);

// 4. manual_flights（本人が画面から送る形）
const asU1 = `set role authenticated; select set_config('request.jwt.claim.sub', '${U1}', false);`;
const mf = `insert into public.manual_flights (from_airport, to_airport, flown_on, client_id) values (${B}, ${A}, current_date, '${C1}') on conflict (user_id, client_id) do nothing`;
check('本人は client_id 付きで足せる', !(await fails(asU1 + mf)), null);
check('同じ ID を on conflict do nothing で送り直しても失敗しない', !(await fails(asU1 + mf)), null);
check('同じ ID の便は1行だけ', await q1(`select count(*)::int from public.manual_flights where client_id = '${C1}'`) === 1, null);
check('ID なしの便は今までどおり何件でも足せる',
  !(await fails(asU1 + `insert into public.manual_flights (from_airport, to_airport, flown_on) values (${B}, ${A}, current_date)`))
  && !(await fails(asU1 + `insert into public.manual_flights (from_airport, to_airport, flown_on) values (${B}, ${A}, current_date)`)), null);
check('本人でも client_id は直せない', await fails(asU1 + `update public.manual_flights set client_id = gen_random_uuid()`), null);
check('price・seat は今までどおり直せる', !(await fails(asU1 + `update public.manual_flights set price = 12000, seat = '12A' where client_id = '${C1}'`)), lastErr);
await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub', '${U2}', false);`);
check('別の人の便は見えない', await q1(`select count(*)::int from public.manual_flights`) === 0, null);
await db.exec('reset role');

// 5. 権限・RLS・もう一度
for (const t of ['checkins', 'flights']) {
  check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
  check(`利用者は ${t} に書けない`, await fails(asU1 + (t === 'checkins' ? ci(U1, '3f2504e0-4f89-41d3-9a0c-0305e82c3301') : fl(null))), null);
}
check('manual_flights の RLS は ON', await q1(`select relrowsecurity from pg_class where oid = 'public.manual_flights'::regclass`) === true, null);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても列・索引は1つずつ', await q1(`select count(*)::int from information_schema.columns where table_schema = 'public' and column_name = 'client_id' and table_name in ('checkins', 'manual_flights')`) === 2
  && await q1(`select count(*)::int from pg_indexes where indexname in ('checkins_user_client', 'flights_arr_checkin', 'manual_user_client')`) === 3 && await uniq() === true, null);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
