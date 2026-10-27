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
// 機体の位置から推定した離陸・着陸の時刻：門限チャレンジと便の候補で返す（到着空港以外での着陸・離陸の推定が不確かな便は返さない）
const close = `((((now() at time zone 'Asia/Tokyo') - interval '5 hours')::date + interval '21 hours') at time zone 'Asia/Tokyo')`;
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (current_date, 'IJ123', 'HND', 'ITM', ${close} - interval '80 minutes', ${close} - interval '10 minutes', 'ODPT'),
  (current_date, 'BC107', 'HND', 'ITM', ${close} - interval '70 minutes', ${close} - interval '5 minutes', 'ODPT'),
  (current_date, '6J21', 'HND', 'ITM', ${close} - interval '60 minutes', ${close} + interval '5 minutes', 'ODPT')`);
await db.exec(`insert into public.flight_watch (schedule_id, state)
  select id, jsonb_build_object('phase','air','takeoff_at', extract(epoch from std + interval '10 minutes') * 1000, 'takeoff_est', false,
    'eta', extract(epoch from sta + interval '18 minutes') * 1000) from public.flight_schedule where flight = '6J21'`);
await db.exec(`insert into public.flight_watch (schedule_id, state)
  select id, jsonb_build_object('phase','landed','takeoff_at', extract(epoch from std + interval '12 minutes') * 1000, 'takeoff_est', false,
    'landed_at', extract(epoch from sta + interval '3 minutes') * 1000, 'landed_iata', 'ITM') from public.flight_schedule where flight = 'IJ123'`);
await db.exec(`insert into public.flight_watch (schedule_id, state)
  select id, jsonb_build_object('phase','landed','takeoff_at', extract(epoch from std) * 1000, 'takeoff_est', true,
    'landed_at', extract(epoch from sta) * 1000, 'landed_iata', 'KIX') from public.flight_schedule where flight = 'BC107'`);
let r = await as('anon', `select public.curfew_flights('ITM')`);
const ij = (r?.flights ?? []).find((f) => f.flight === 'IJ123'), bc = (r?.flights ?? []).find((f) => f.flight === 'BC107');
check('門限チャレンジ：推定の着陸時刻が入る', ij && ij.inferred != null && ij.actual == null, r);
check('ほかの空港に降りた便・離陸が不確かな便は、推定の時刻を返さない', bc && bc.inferred == null && bc.dep_actual == null, bc);
const sn = (r?.flights ?? []).find((f) => f.flight === '6J21');
check('飛行中の便は到着予想（推定）が入る', sn && sn.predicted != null && sn.inferred == null, sn);
r = await as('anon', `select public.flight_candidates('HND', 'ITM', ${close} - interval '70 minutes', ${close} - interval '5 minutes')`);
const c = (r ?? []).find((f) => f.flight === 'IJ123');
check('便の候補：推定の離陸・着陸時刻が入る', c && c.atd_est != null && c.ata_est != null && c.atd == null, r);
r = await as('anon', `select public.inferred_time('{}'::jsonb, 'landed_at')`);
check('推定の時刻の関数は利用者から呼べない', String(r).startsWith('ERROR'), r);
if (bad) process.exit(1);
