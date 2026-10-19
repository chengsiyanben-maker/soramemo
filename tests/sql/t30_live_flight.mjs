// 国際線：乗る便を出発から到着まで追うための時刻表の引き当て（便名の0は無視・出発空港は省ける）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, arr_status) values
  (current_date, 'NH0106', 'HND', 'LAX', now() + interval '2 hours', now() + interval '12 hours', 'ODPT', null),
  (current_date - 2, 'NH0106', 'HND', 'LAX', now() - interval '2 days', now() - interval '1 day', 'ODPT', null),
  (current_date, 'JL0001', 'HND', 'SFO', now() - interval '3 hours', now() + interval '6 hours', 'ODPT', 'Cancelled')`);
let r = (await db.query(`select public.live_flight_sched('NH106', null) as x`)).rows[0].x;
check('便名の0を無視して、いちばん近い日の便を返す', r?.flight === 'NH0106' && r.arr === 'LAX' && Date.parse(r.std) > Date.now(), r);
r = (await db.query(`select public.live_flight_sched('JL1', 'HND') as x`)).rows[0].x;
check('欠航も返す', r?.cancelled === true, r);
r = (await db.query(`select public.live_flight_sched('NH106', 'NRT') as x`)).rows[0].x;
check('出発空港が違えば返さない', r === null, r);
r = await as('anon', `select public.live_flight_sched('NH106', null)`);
check('匿名では呼べない（flight-live だけが使う）', String(r).startsWith('ERROR'), r);
if (bad) process.exit(1);
