// 特別塗装機の画面（livery_board）：いま・今日の足あと・30日に来た空港。発着がまだない便は時刻表で埋める。
// 特別塗装機として見えたことがない機体は返さない（ほかの機体の記録は読めない）。表は匿名から直接読めないまま
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const today = (await db.query(`select (now() at time zone 'Asia/Tokyo')::date::text as d`)).rows[0].d;
check('便名から時刻表の便名', (await db.query(`select public.cs_flight('JAL0113') a, public.cs_flight('ANA18') b, public.cs_flight('UAL32') c`)).rows[0].a === 'JL113');
await db.exec(`insert into public.livery_sightings (reg, name, airline, callsign, lat, lon, alt_ft, iata, phase, src, seen_at) values
  ('JA339J', 'JAL Jubilee Express', 'JAL', 'JAL113', 35.1, 137.2, 24300, null, null, 'x', now() - interval '2 minutes'),
  ('JA819A', 'ポケモンジェット 赤', 'ANA', 'ANA18', 34.6, 135.4, 0, null, null, 'x', now() - interval '3 hours');
insert into public.live_positions (callsign, lat, lon, kt, seen_at) values ('JAL113', 35.1, 137.2, 450, now());
insert into public.reg_legs (reg, callsign, day, first_at, last_at, dep, arr) values
  ('JA339J', 'JAL503', '${today}', now() - interval '6 hours', now() - interval '5 hours', 'HND', 'CTS'),
  ('JA339J', 'JAL113', '${today}', now() - interval '20 minutes', now() - interval '1 minute', null, null),
  ('JA339J', 'JAL503', '${today}'::date - 3, now() - interval '3 days', now() - interval '3 days', 'HND', 'CTS'),
  ('JA819A', 'ANA18', '${today}'::date - 40, now() - interval '40 days', now() - interval '40 days', 'ITM', 'HND'),
  ('JA111A', 'ANA1', '${today}', now() - interval '1 hour', now(), 'HND', 'FUK');
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values
  ('${today}', 'JL113', 'HND', 'ITM', now() - interval '30 minutes', now() + interval '35 minutes', 'test')`);
const b = (await db.query(`select public.livery_board(array['JA339J','JA819A','JA111A']) as j`)).rows[0].j;
const by = Object.fromEntries(b.map((x) => [x.reg, x]));
check('見えたことのない機体は返さない', !by.JA111A && b.length === 2, b.map((x) => x.reg));
const j = by.JA339J;
check('いま飛んでいる（15分以内）・速さも', j.now && j.now.callsign === 'JAL113' && j.now.kt === 450, j.now);
check('今日の足あとは2便、時刻の順', j.today.length === 2 && j.today[0].cs === 'JAL503' && j.today[1].cs === 'JAL113', j.today);
check('発着がまだない便は時刻表で埋める', j.today[1].dep === 'HND' && j.today[1].arr === 'ITM' && j.today[1].sch === true && !!j.today[1].sta, j.today[1]);
check('30日に来た空港（到着の数）', j.arr30.CTS === 2 && j.arr30.ITM === 1, j.arr30);
const p = by.JA819A;
check('15分より前に見えた機体は「いま」なし・30日より前は数えない', p.now === null && p.today.length === 0 && p.last_day === null && Object.keys(p.arr30).length === 0, p);
await db.exec('set role anon');
const a = (await db.query(`select jsonb_array_length(public.livery_board(array['JA339J'])) as n`)).rows[0].n;
let denied = false; try { await db.query('select * from public.reg_legs'); } catch { denied = true; }
await db.exec('reset role');
check('匿名でも呼べる', a === 1); check('表は匿名から直接読めない', denied);
await db.exec(`insert into public.push_subs (endpoint, p256dh, auth, sp_regs) values ('https://fcm.googleapis.com/x', 'k', 'a', array['JA339J'])`);
check('機体ごとの通知の列', (await db.query(`select count(*)::int n from public.push_subs where sp_regs @> array['JA339J']`)).rows[0].n === 1);
let tooMany = false; try { await db.exec(`update public.push_subs set sp_regs = array(select 'JA' || g from generate_series(100, 120) g)`); } catch { tooMany = true; }
check('機体ごとの通知は20機まで', tooMany);
await db.exec('set role anon'); let subDenied = false; try { await db.query('select * from public.push_subs'); } catch { subDenied = true; } await db.exec('reset role');
check('通知の申し込みは匿名から読めない', subDenied);
if (bad) process.exit(1);
