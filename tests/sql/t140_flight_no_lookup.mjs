// 記録帳の便名と flight_lookup（移行 202）
//   1. manual_flights.flight_no：本人は便名つきで足せて、あとから直せる。形のおかしな便名は入らない。ほかの人の行は読めず直せない。ログインなしは何もできない
//   2. flight_lookup：flight_history から出発・到着・時刻・機体を返す。前の 0・小文字・共同運航の便名でも見つかる。区間が2つの日は定刻の順に2つ。
//      flight_history にない日は時刻表から（src = schedule）。両方にあれば flight_history だけ。おかしな入力は空。anon・authenticated が呼べ、表は直接読めない
//   3. その日の行だけを索引の先頭（svc_date）で読む。表・RLS・ほかの権限は変わらず、列1つ・関数1つが増えるだけ。2回流しても壊れない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to anon, authenticated, service_role;
alter default privileges in schema public grant select, insert, update, delete on tables to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const NEW = '20261126000202_flight_no_lookup.sql';
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const rows = async (sql, p) => (await db.query(sql, p)).rows;
const U1 = '00000000-0000-0000-0000-000000000001', U2 = '00000000-0000-0000-0000-000000000002';
const as = async (role, uid, sql, p) => {
  try { await db.exec(`set role ${role}`); await db.query(`select set_config('request.jwt.claim.sub', $1, false)`, [uid || '']);
    const r = await db.query(sql, p); return { ok: true, rows: r.rows, n: r.affectedRows }; }
  catch (e) { return { ok: false, err: e.message.split('\n')[0] }; }
  finally { await db.exec(`reset role`); await db.exec(`select set_config('request.jwt.claim.sub', '', false)`); } };
const SHAPE = `select (select json_agg(x order by x) from (select table_name || '.' || column_name || ':' || data_type x from information_schema.columns where table_schema = 'public') s) cols,
  (select json_agg(x order by x) from (select tablename || ':' || policyname || ':' || coalesce(qual, '') || ':' || coalesce(with_check, '') x from pg_policies where schemaname = 'public') s) pol,
  (select json_agg(x order by x) from (select table_name || ':' || grantee || ':' || privilege_type x from information_schema.role_table_grants where table_schema = 'public') s) grants,
  (select json_agg(x order by x) from (select p.oid::regprocedure::text || ':' || coalesce(p.proacl::text, '') x from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public') s) fns,
  (select count(*)::int from pg_indexes where schemaname = 'public') nidx`;

for (const f of files) if (f < NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`insert into auth.users (id) values ('${U1}'), ('${U2}')`);
const ap = (await rows(`select id, iata from public.airports where iata in ('HND', 'ITM', 'CTS') order by iata`));
const id = Object.fromEntries(ap.map(a => [a.iata, a.id]));
const before = (await rows(SHAPE))[0];

await db.exec(fs.readFileSync(dir + NEW, 'utf8'));

// 1. 記録帳の便名
const ins = await as('authenticated', U1, `insert into public.manual_flights (from_airport, to_airport, flown_on, airline, flight_no) values ($1, $2, '2026-11-01', 'JL', 'JL123') returning id, flight_no`, [id.HND, id.ITM]);
check('1 本人は便名つきで足せる', ins.ok && ins.rows[0]?.flight_no === 'JL123', ins);
const mid = ins.rows?.[0]?.id;
const ins0 = await as('authenticated', U1, `insert into public.manual_flights (from_airport, to_airport, flown_on) values ($1, $2, '2026-11-02') returning flight_no`, [id.ITM, id.HND]);
check('1 便名なしでも今までどおり足せる', ins0.ok && ins0.rows[0].flight_no === null, ins0);
check('1 形のおかしな便名は入らない', !(await as('authenticated', U1, `insert into public.manual_flights (from_airport, to_airport, flown_on, flight_no) values ($1, $2, '2026-11-01', 'jl 123')`, [id.HND, id.ITM])).ok);
check('1 他人の user_id では足せない', !(await as('authenticated', U1, `insert into public.manual_flights (user_id, from_airport, to_airport, flown_on, flight_no) values ($3, $1, $2, '2026-11-01', 'NH1')`, [id.HND, id.ITM, U2])).ok);
const up = await as('authenticated', U1, `update public.manual_flights set flight_no = 'JL125' where id = $1`, [mid]);
check('1 本人はあとから便名を直せる', up.ok && (await rows(`select flight_no from public.manual_flights where id = $1`, [mid]))[0].flight_no === 'JL125', up);
check('1 直せる列は前のまま（日付は直せない）', !(await as('authenticated', U1, `update public.manual_flights set flown_on = '2026-10-01' where id = $1`, [mid])).ok);
const up2 = await as('authenticated', U2, `update public.manual_flights set flight_no = 'NH9' where id = $1`, [mid]);
check('1 他人の行は直せない（0行）', up2.ok && (await rows(`select flight_no from public.manual_flights where id = $1`, [mid]))[0].flight_no === 'JL125', up2);
const rd2 = await as('authenticated', U2, `select count(*)::int n from public.manual_flights`);
check('1 他人の行は読めない', rd2.ok && rd2.rows[0].n === 0, rd2);
check('1 ログインなしは読めない（0行か拒否）', (r => !r.ok || r.rows[0].n === 0)(await as('anon', null, `select count(*)::int n from public.manual_flights`)));
check('1 ログインなしは足せない', !(await as('anon', null, `insert into public.manual_flights (user_id, from_airport, to_airport, flown_on) values ($3, $1, $2, '2026-11-01')`, [id.HND, id.ITM, U1])).ok);

// 2. flight_lookup
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, atd, ata, atd_src, ata_src, aircraft, type, reg, also) values
  ('2026-11-01', 'JL123', 'HND', 'ITM', '2026-11-01 08:00+09', '2026-11-01 09:10+09', '2026-11-01 08:05+09', '2026-11-01 09:12+09', 'odpt', 'adsb', '767', 'B763', 'JA602J', '{}'),
  ('2026-11-01', 'NH771', 'ITM', 'CTS', '2026-11-01 13:00+09', '2026-11-01 14:50+09', null, null, null, null, '738', 'B738', 'JA51AN', '{}'),
  ('2026-11-01', 'NH771', 'HND', 'ITM', '2026-11-01 10:00+09', '2026-11-01 11:10+09', null, null, null, null, '738', 'B738', 'JA51AN', '{}'),
  ('2026-11-01', 'JL2001', 'HND', 'CTS', '2026-11-01 07:00+09', '2026-11-01 08:30+09', null, null, null, null, '738', 'B738', 'JA301J', '{HD31}'),
  ('2026-10-31', 'JL123', 'HND', 'ITM', '2026-10-31 08:00+09', '2026-10-31 09:10+09', null, null, null, null, '767', 'B763', 'JA999J', '{}')`);
const today = (await rows(`select (now() at time zone 'Asia/Tokyo')::date::text d`))[0].d;
await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source, atd) values ($1, 'JL123', 'HND', 'ITM', ($1::date + time '08:00') at time zone 'Asia/Tokyo', ($1::date + time '09:10') at time zone 'Asia/Tokyo', '767', 'test', ($1::date + time '08:03') at time zone 'Asia/Tokyo')`, [today]);
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source) values ('2026-11-01', 'JL123', 'HND', 'ITM', '2026-11-01 08:00+09', '2026-11-01 09:10+09', '767', 'test')`);
const L = async (role, d, f) => { const r = await as(role, role === 'anon' ? null : U1, `select public.flight_lookup($1::date, $2) v`, [d, f]); return r.ok ? r.rows[0].v : r; };
const a = await L('anon', '2026-11-01', 'JL123');
check('2 日付＋便名で出発・到着・時刻・機体が返る', a.rows?.length === 1 && a.rows[0].dep === 'HND' && a.rows[0].arr === 'ITM' && a.rows[0].reg === 'JA602J' && a.rows[0].type === 'B763'
  && new Date(a.rows[0].std).toISOString() === '2026-10-31T23:00:00.000Z' && new Date(a.rows[0].ata).toISOString() === '2026-11-01T00:12:00.000Z' && a.rows[0].ata_src === 'adsb', a);
check('2 両方にある日は flight_history だけ', a.rows?.length === 1 && a.rows[0].src === 'history', a);
check('2 前の 0・小文字・前後の空白でも見つかる', (await L('authenticated', '2026-11-01', ' jl0123 ')).rows?.[0]?.reg === 'JA602J');
const cs = await L('anon', '2026-11-01', 'HD31');
check('2 共同運航の便名でも見つかる', cs.rows?.length === 1 && cs.rows[0].flight === 'JL2001' && cs.rows[0].also[0] === 'HD31', cs);
const two = await L('anon', '2026-11-01', 'NH771');
check('2 区間が2つの日は定刻の順に2つ', two.rows?.length === 2 && two.rows[0].dep === 'HND' && two.rows[1].dep === 'ITM', two);
check('2 日付が違えば別の便', (await L('anon', '2026-10-31', 'JL123')).rows?.[0]?.reg === 'JA999J');
const sc = await L('anon', today, 'JL123');
check('2 flight_history にない日は時刻表から（src = schedule）', sc.rows?.length === 1 && sc.rows[0].src === 'schedule' && sc.rows[0].atd_src === 'odpt' && sc.rows[0].reg === null, sc);
check('2 見つからない便は空', JSON.stringify((await L('anon', '2026-11-01', 'JL999')).rows) === '[]');
for (const [d, f] of [['2026-11-01', 'JL 123'], ['2026-11-01', ''], ['2026-11-01', null], [null, 'JL123'], ['2026-11-01', "JL123' or 1=1"]]) {
  const r = await L('anon', d, f); check(`2 おかしな入力は空（${d} / ${f}）`, JSON.stringify(r.rows) === '[]', r);
}
check('2 flight_history は直接読めない', !(await as('anon', null, `select count(*) from public.flight_history`)).ok);
check('2 authenticated も呼べる', (await L('authenticated', '2026-11-01', 'JL123')).rows?.length === 1);

// 3. 読み方と形
const def = (await rows(`select prosrc from pg_proc where proname = 'flight_lookup'`))[0].prosrc;
const body = def.replace(/\bp_date\b/g, '($1::date)').replace(/\bp_flight\b/g, '($2::text)');
await db.exec(`set enable_seqscan = off`);
const pl = (await db.exec(`explain (generic_plan) ${body}`))[0].rows.map(r => r['QUERY PLAN']).join('\n');
await db.exec(`reset enable_seqscan`);
check('3 flight_history・flight_schedule を全部読まない（その日を索引で）', !/Seq Scan on flight_(history|schedule)/.test(pl) && /flight_history_pkey/.test(pl), pl);
const after = (await rows(SHAPE))[0];
const added = after.cols.filter(c => !before.cols.includes(c));
check('3 列は manual_flights.flight_no だけ増える', JSON.stringify(added) === JSON.stringify(['manual_flights.flight_no:text']) && before.cols.every(c => after.cols.includes(c)), added);
check('3 RLS の方針は同じ', JSON.stringify(after.pol) === JSON.stringify(before.pol));
check('3 索引の数は同じ', after.nidx === before.nidx, [before.nidx, after.nidx]);
const newFns = after.fns.filter(x => !before.fns.includes(x));
check('3 関数は flight_lookup だけ増え、ほかの権限は同じ', newFns.length === 1 && newFns[0].startsWith('flight_lookup(date,text)') && before.fns.every(x => after.fns.includes(x)), newFns);
const g = (await rows(`select privilege_type, column_name from information_schema.column_privileges where table_name = 'manual_flights' and grantee = 'authenticated' and privilege_type = 'UPDATE' order by 2`)).map(r => r.column_name);
check('3 本人が直せる列は fare・seat・airline・price・flight_no', JSON.stringify(g) === JSON.stringify(['airline', 'fare', 'flight_no', 'price', 'seat']), g);
let again = true; try { await db.exec(fs.readFileSync(dir + NEW, 'utf8')); } catch (e) { again = false; console.log(e.message); }
check('3 2回流しても壊れない', again && JSON.stringify((await rows(SHAPE))[0]) === JSON.stringify(after));
for (const f of files) if (f > NEW) await db.exec(fs.readFileSync(dir + f, 'utf8'));
check('3 後の移行も流せる', true);
if (bad) process.exit(1);
