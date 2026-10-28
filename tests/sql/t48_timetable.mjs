// 計画の時刻表：表は利用者から読めない・書けない、その日に飛ぶ便だけを関数で読める（曜日・期間）、入れ替えは取り込み役だけ
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
const as = async (role, sql) => { try { await db.exec(`set role ${role}`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message; } finally { await db.exec('reset role'); } };
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const day = (n) => new Date(Date.now() + 9 * 3600e3 + n * 864e5).toISOString().slice(0, 10);   // 日本時間で n 日後
const d0 = day(7), dow = new Date(d0 + 'T12:00:00Z').getUTCDay(), bit = 1 << dow, other = 1 << ((dow + 1) % 7);
const rows = JSON.stringify([
  { operator: 'ANA', dep: 'HND', arr: 'OKA', flight: 'NH461', days: bit, valid_from: day(0), valid_to: day(30), dep_time: '07:30', arr_time: '10:15', arr_day: 0, aircraft: '789' },
  { operator: 'ANA', dep: 'HND', arr: 'OKA', flight: 'NH463', days: other, valid_from: day(0), valid_to: day(30), dep_time: '08:30', arr_time: '11:15', arr_day: 0, aircraft: null },
  { operator: 'ANA', dep: 'HND', arr: 'CTS', flight: 'NH51', days: 127, valid_from: day(10), valid_to: day(30), dep_time: '06:30', arr_time: '08:00', arr_day: 0, aircraft: null },
  { operator: 'ANA', dep: 'ITM', arr: 'OKA', flight: 'NH1', days: 127, valid_from: day(0), valid_to: day(30), dep_time: '06:30', arr_time: '08:00', arr_day: 0, aircraft: null },
]);
let r = await as('anon', `select public.timetable_replace('ANA', 'HND', '${rows}'::jsonb)`);
check('利用者は入れ替えられない', String(r).startsWith('ERROR'), r);
r = await as('service_role', `select public.timetable_replace('ANA', 'HND', '${rows}'::jsonb)`);
check('取り込み役は入れ替えられる（その空港を出発する行だけ）', r === 3, r);
for (const role of ['anon', 'authenticated']) {
  r = await as(role, `select count(*) from public.timetable`);
  check(`${role} は表を直接読めない`, String(r).startsWith('ERROR'), r);
}
r = await as('anon', `select public.plan_timetable('${d0}', 'ANA')`);
check('その日の曜日・期間に合う便だけ', r && r.f.length === 1 && r.f[0][0] === 'NH461' && r.f[0][3] === '07:30' && r.f[0][6] === '789', r);
check('時刻表が出ている最後の日', r && r.until === day(30), r);
r = await as('anon', `select public.plan_timetable('${day(500)}', 'ANA')`);
check('遠すぎる日は返さない', r === null, r);
r = await as('service_role', `select public.timetable_replace('ANA', 'HND', '[]'::jsonb)`);
r = await as('anon', `select public.plan_timetable('${d0}', 'ANA')`);
check('入れ替えると前の行は消える', r && r.f.length === 0, r);
if (bad) process.exit(1);
