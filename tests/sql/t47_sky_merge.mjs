// 空の道：全機の航跡に、JAL・ANA の便の航跡のうち全機の航跡にない便を足す。同じ便（便名）は1本。今日の分は全機の航跡だけ
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
const day = (await db.query(`select ((now() at time zone 'Asia/Tokyo')::date - 1)::text as d`)).rows[0].d;
const today = (await db.query(`select (now() at time zone 'Asia/Tokyo')::date::text as d`)).rows[0].d;
// 松山：全機の航跡は1本（JAL433 の到着）。JAL・ANA の航跡は3便（JAL433 は重なり、ANA591 と JAL434 は全機の航跡にない）
await db.exec(`insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('MYJ', '${day}', 'JAL433', '${day} 01:00+00', 0, 'all433');
insert into public.flight_history (svc_date, flight, dep, arr, std, sta, ata, callsign) values
  ('${day}', 'JL433', 'HND', 'MYJ', '${day} 23:30+00'::timestamptz - interval '1 day', '${day} 01:00+00', '${day} 01:02+00', 'JAL433'),
  ('${day}', 'JL434', 'MYJ', 'HND', '${day} 02:00+00', '${day} 03:30+00', null, 'JAL434'),
  ('${day}', 'NH591', 'HND', 'MYJ', '${day} 04:00+00', '${day} 05:30+00', '${day} 05:35+00', 'ANA591');
insert into public.flight_tracks (svc_date, flight, dep, pts) values ('${day}', 'JL433', 'HND', 'jl433'), ('${day}', 'JL434', 'MYJ', 'jl434'), ('${day}', 'NH591', 'HND', 'nh591');
insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) values ('MYJ', '${today}', 'JAL435', now(), 0, 'today435')`);
const t = (await db.query(`select public.airport_tracks('MYJ', '${day}') as j`)).rows[0].j;
check('全機の1本＋全機の航跡にない JAL・ANA の2便＝3本', t.length === 3, t);
check('同じ便（JAL433）は全機の航跡の1本だけ', t.filter((x) => x.p === 'all433').length === 1 && !t.some((x) => x.p === 'jl433'), t);
check('出発・到着と時間帯も付く', t.some((x) => x.p === 'jl434' && x.d === 1 && x.h === 11) && t.some((x) => x.p === 'nh591' && x.d === 0 && x.h === 14), t);
check('時刻の順', t.map((x) => x.p).join(',') === 'all433,jl434,nh591', t.map((x) => x.p));
const n = (await db.query(`select jsonb_array_length(public.airport_tracks('MYJ', '${today}')) as n`)).rows[0].n;
check('今日の分は全機の航跡だけ', n === 1, n);
// 全機の航跡がない日は、前と同じく JAL・ANA の航跡だけ
await db.exec(`delete from public.airport_tracks_all where day = '${day}'`);
check('全機の航跡がない日は JAL・ANA の3便', (await db.query(`select jsonb_array_length(public.airport_tracks('MYJ', '${day}')) as n`)).rows[0].n === 3);
await db.exec('set role anon'); const an = (await db.query(`select jsonb_array_length(public.airport_tracks('MYJ', '${day}')) as n`)).rows[0].n;
let denied = false; try { await db.query('select * from public.flight_tracks'); } catch { denied = true; } await db.exec('reset role');
check('匿名でも呼べる・表は読めない', an === 3 && denied);
if (bad) process.exit(1);
