// フライトの記録で選ぶ予定の便：出発・到着の時刻に近い順に返す・時刻表は利用者から直接は読めない
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
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, aircraft, source) values
  ('2026-10-15','JL501','HND','CTS','2026-10-15 07:00+09','2026-10-15 08:35+09','763','ODPT'),
  ('2026-10-15','NH55','HND','CTS','2026-10-15 08:00+09','2026-10-15 09:35+09','78G','ODPT'),
  ('2026-10-15','JL503','HND','CTS','2026-10-15 08:30+09','2026-10-15 10:05+09','738','ODPT'),
  ('2026-10-15','JL511','HND','CTS','2026-10-15 12:00+09','2026-10-15 13:35+09','738','ODPT'),
  ('2026-10-15','JL901','HND','OKA','2026-10-15 08:00+09','2026-10-15 10:40+09','763','ODPT')`);
let r = await as('anon', `select public.flight_candidates('HND','CTS','2026-10-15 07:20+09','2026-10-15 09:50+09')`);
check('近い順に返す（NH55 がいちばん近い）', Array.isArray(r) && r[0]?.flight === 'NH55' && r.length === 3 && !r.some((x) => x.flight === 'JL511' || x.flight === 'JL901'), r);
r = await as('anon', `select public.flight_candidates('HND','CTS','2026-10-15 09:50+09','2026-10-15 07:20+09')`);
check('到着が出発より前なら何も返さない', Array.isArray(r) && r.length === 0, r);
r = await as('anon', `select count(*) from public.flight_schedule`);
check('時刻表の表は利用者から直接読めない', String(r).startsWith('ERROR'), r);
if (bad) process.exit(1);
