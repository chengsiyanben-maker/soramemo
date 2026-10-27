// 路線・空港ごとの定時率と、空港の航跡、利用者のフライトの航跡の対象
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
// 路線・空港ごとの定時率（航空会社の実際の出発時刻がある便だけ）と、空港の航跡、利用者のフライトの航跡の対象
const y = `(now() at time zone 'Asia/Tokyo')::date - 1`;
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, atd, atd_src, dep_delay, cancelled) values
  (${y}, 'JL501', 'HND', 'CTS', now(), now(), now(), 'odpt', 3, false),
  (${y}, 'JL503', 'HND', 'CTS', now(), now(), now(), 'odpt', 14, false),
  (${y}, 'JL505', 'HND', 'CTS', now(), now(), now(), 'odpt', 15, false),
  (${y}, 'JL507', 'HND', 'CTS', now(), now(), now(), 'odpt', 40, false),
  (${y}, 'JL509', 'HND', 'CTS', now(), now(), now(), 'adsb', 60, false),
  (${y}, 'JL511', 'HND', 'CTS', now(), now(), null, null, null, true),
  (${y}, 'JL513', 'HND', 'CTS', now(), now(), now(), 'odpt', 0, false),
  (${y}, 'JL515', 'HND', 'CTS', now(), now(), now(), 'odpt', 1, false),
  (${y}, 'JL101', 'HND', 'ITM', now(), now(), now(), 'odpt', 0, false),
  ((now() at time zone 'Asia/Tokyo')::date, 'JL517', 'HND', 'CTS', now(), now(), now(), 'odpt', 90, false),
  (${y} - 40, 'JL519', 'HND', 'CTS', now(), now(), now(), 'odpt', 90, false)`);
let r = await as('anon', `select public.route_ontime('HND', 'CTS', 30)`);
check('定時率：15分未満を定時、推定の時刻と欠航は分母に入れない。今日と30日より前は数えない',
  r?.flights === 8 && r.measured === 6 && r.ontime === 4 && r.cancelled === 1 && Number(r.avg_late) === 28, r);
r = await as('anon', `select public.airport_ontime('HND', 30)`);
check('空港の定時率：5便以上数えられた路線だけ一覧に出す', r?.measured === 7 && r.ontime === 5 && r.routes.length === 1 && r.routes[0].arr === 'CTS', r);
await db.exec(`insert into public.flight_tracks (svc_date, flight, dep, pts, alts) values
  (${y}, 'JL501', 'HND', 'abc', '{10,20}'), (${y}, 'JL101', 'HND', 'def', '{30}'), (${y} - 40, 'JL519', 'HND', 'ghi', '{1}')`);
r = await as('anon', `select public.airport_tracks('HND', ${y})`);
check('空港の航跡：その日の出発・到着の便の航跡を、便名なしで返す', r?.length === 2 && r.every((x) => x.d === 1 && !('flight' in x)), r);
r = await as('anon', `select public.airport_tracks('CTS', ${y})`);
check('到着の便は d=0', r?.length === 1 && r[0].d === 0, r);
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta) select ${y}, 'NH' || g, 'ITM', 'FUK', now(), now() from generate_series(1000, 3199) g;
  insert into public.flight_tracks (svc_date, flight, dep, pts) select ${y}, 'NH' || g, 'ITM', 'x' from generate_series(1000, 3199) g`);
r = await as('anon', `select public.airport_tracks('HND', ${y})`);
check('ほかの空港の便が2000便を超えても、その空港の航跡は欠けない', r?.length === 2, r?.length);
r = await as('anon', `select public.airport_tracks('HND', ${y} - 40)`);
check('31日より前の日も返す（記録はずっと残す）', Array.isArray(r) && r.length === 1, r);
r = await as('anon', `select public.airport_tracks('HND', (now() at time zone 'Asia/Tokyo')::date)`);
check('今日の分はまだ返さない', Array.isArray(r) && r.length === 0, r);
r = await as('anon', `select count(*) from public.archive_user_flights(${y})`);
check('利用者のフライトの対象は、匿名では呼べない', String(r).startsWith('ERROR'), r);
await db.exec(`insert into auth.users (id) values ('00000000-0000-0000-0000-000000000001');
  insert into public.flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no) values
  ('00000000-0000-0000-0000-000000000001', (select id from public.airports where iata = 'HND' limit 1), (select id from public.airports where iata = 'CTS' limit 1),
   ((${y})::timestamp at time zone 'Asia/Tokyo') + interval '10 hours', ((${y})::timestamp at time zone 'Asia/Tokyo') + interval '12 hours', 800, 'JL0501'),
  ('00000000-0000-0000-0000-000000000001', (select id from public.airports where iata = 'HND' limit 1), (select id from public.airports where iata = 'CTS' limit 1),
   ((${y} - 1)::timestamp at time zone 'Asia/Tokyo') + interval '22 hours', ((${y} - 1)::timestamp at time zone 'Asia/Tokyo') + interval '23 hours', 800, 'JL503')`);
r = (await db.query(`select flight, dep from public.archive_user_flights(${y})`)).rows;
check('その日（日本時間）に出たフライトだけ、便名の0を取って返す', r.length === 1 && r[0].flight === 'JL501' && r[0].dep === 'HND', r);
if (bad) process.exit(1);
