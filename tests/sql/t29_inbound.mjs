// 乗る便の機体はいまどこ：機体のつながりの記録から前の便を推定し、出発の遅れの見込みを出す
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
const T = `(now() at time zone 'Asia/Tokyo')::date`;
// 乗る便 JL0509（羽田→新千歳、2時間後）。前の便の候補は JL0500（伊丹→羽田、50分後着）と JL0300（福岡→羽田）
await db.exec(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, aircraft) values
  (${T}, 'JL0509', 'HND', 'CTS', now() + interval '2 hours', now() + interval '3 hours 30 minutes', 'ODPT', '738'),
  (${T}, 'JL0500', 'ITM', 'HND', now() - interval '20 minutes', now() + interval '50 minutes', 'ODPT', '738'),
  (${T}, 'JL0300', 'FUK', 'HND', now() - interval '10 minutes', now() + interval '80 minutes', 'ODPT', '738'),
  (${T}, 'JL0777', 'HND', 'OKA', now() + interval '1 hour', now() + interval '3 hours', 'ODPT', '763')`);
await db.exec(`insert into public.rotation_obs (svc_date, reg, prev_flight, next_flight, iata, turn_min) values
  (${T} - 7, 'JA301J', 'JL0500', 'JL0509', 'HND', 70), (${T} - 6, 'JA302J', 'JL0500', 'JL0509', 'HND', 70),
  (${T} - 5, 'JA303J', 'JL0300', 'JL0509', 'HND', 40)`);
let r = await as('anon', `select public.inbound_aircraft('JL509', 'HND')`);
check('便名の0の違いを無視して乗る便を見つけ、多い方の前の便（JL0500）を選ぶ', r?.found && r.inbound?.flight === 'JL0500' && Number(r.inbound.share) > 0.5, r);
check('前の便が定刻なら遅れの見込みは0', Number(r?.late) === 0 && r.arr_src === 'sched', r);
// 前の便が航空会社の見込みで100分遅れ → 到着が2時間30分後、折り返し35分で、出発は65分遅れの見込み
await db.exec(`update public.flight_schedule set eta = sta + interval '100 minutes' where flight = 'JL0500'`);
r = await as('anon', `select public.inbound_aircraft('JL509', 'HND')`);
check('前の便の見込みの遅れから、出発の遅れを見込む（折り返し35分）', r?.arr_src === 'est' && Math.abs(Number(r.late) - 65) <= 1, r);
// 前の便が飛んでいて、機体の位置からの到着予想がある
await db.exec(`update public.flight_schedule set eta = null where flight = 'JL0500';
  insert into public.flight_watch (schedule_id, state) select id, jsonb_build_object('phase', 'air', 'reg', 'JA305J', 'type', 'B738',
    'eta', extract(epoch from now() + interval '70 minutes') * 1000, 'last', jsonb_build_object('lat', 35.0, 'lon', 137.0, 'alt_ft', 30000, 'at', extract(epoch from now()) * 1000))
  from public.flight_schedule where flight = 'JL0500'`);
r = await as('anon', `select public.inbound_aircraft('JL509', 'HND')`);
check('機体の位置からの到着予想と、今の位置・登録記号を返す', r?.arr_src === 'predicted' && r.inbound.pos?.alt === 30000 && r.reg === 'JA305J', r);
r = await as('anon', `select public.inbound_aircraft('JL777', 'HND')`);
check('記録がない便は、前の便なしで返す', r?.found && r.inbound === null, r);
r = await as('anon', `select public.inbound_aircraft('JL1', 'HND')`);
check('時刻表にない便は found=false', r?.found === false, r);
r = await as('anon', `select public.inbound_aircraft('bad', 'HND')`);
check('形の違う便名は null', r === null || r === 'ok', r);
if (bad) process.exit(1);
