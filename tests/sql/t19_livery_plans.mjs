// 特別塗装機で飛ぶ予定の便：表は利用者から読めない・これからの便だけ関数で読める・その空港の便が先
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
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  (current_date, 'JL909', 'HND', 'OKA', now() + interval '3 hours', now() + interval '6 hours', 'ODPT'),
  (current_date, 'JL123', 'ITM', 'HND', now() + interval '1 hours', now() + interval '2 hours', 'ODPT'),
  (current_date, 'JL555', 'HND', 'CTS', now() - interval '5 hours', now() - interval '3 hours', 'ODPT')`);
await db.exec(`insert into public.livery_plans (schedule_id, flight, dep, arr, std, livery, note) select id, flight, dep, arr, std, 'JAL Jubilee Express', 'JAL Jubilee Expressで運航いたします。' from public.flight_schedule`);
let r = await as('anon', `select count(*) from public.livery_plans`);
check('予定の表は利用者から直接読めない', String(r).startsWith('ERROR'), r);
r = await as('anon', `select public.livery_plans_upcoming('OKA')`);
check('これからの便だけ（5時間前の便は出さない）、選んだ空港（那覇）の便が先', Array.isArray(r) && r.length === 2 && r[0].flight === 'JL909' && r[1].flight === 'JL123', r);
if (bad) process.exit(1);
