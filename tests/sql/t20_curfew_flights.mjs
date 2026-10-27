// 門限チャレンジ：伊丹・福岡だけ、門限の前後の便を返す（遠い時間の便・ほかの空港の便は出さない）
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
const close = `((((now() at time zone 'Asia/Tokyo') - interval '5 hours')::date + interval '21 hours') at time zone 'Asia/Tokyo')`;
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (current_date, 'JL2089', 'HND', 'ITM', ${close} - interval '90 minutes', ${close} - interval '20 minutes', 'ODPT'),
  (current_date, 'NH039', 'HND', 'ITM', ${close} - interval '70 minutes', ${close} - interval '5 minutes', 'ODPT'),
  (current_date, 'JL2201', 'ITM', 'FUK', ${close} - interval '30 minutes', ${close} + interval '40 minutes', 'ODPT'),
  (current_date, 'JL2001', 'HND', 'ITM', ${close} - interval '10 hours', ${close} - interval '9 hours', 'ODPT'),
  (current_date, 'JL909', 'HND', 'OKA', ${close} - interval '1 hours', ${close} + interval '2 hours', 'ODPT')`);
await db.exec(`update public.flight_schedule set eta = ${close} + interval '15 minutes', arr_status = 'EstimatedArrival' where flight = 'NH039'`);
let r = await as('anon', `select public.curfew_flights('ITM')`);
const fl = r?.flights ?? [];
check('伊丹：門限の前後の到着2便と出発1便（9時間前の便・那覇行きは出さない）', fl.length === 3 && fl.map((f) => f.flight).sort().join() === 'JL2089,JL2201,NH039', r);
check('変更後の時刻（門限の15分後）が入る', fl.find((f) => f.flight === 'NH039')?.est != null, fl);
r = await as('anon', `select public.curfew_flights('HND')`);
check('門限のない空港は null', r === null, r);
r = await as('anon', `select public.curfew_flights('FUK')`);
check('福岡も返す（門限22時）', r && Array.isArray(r.flights), r);
if (bad) process.exit(1);
