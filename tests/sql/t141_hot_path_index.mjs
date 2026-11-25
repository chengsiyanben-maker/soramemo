// 定期の手入れ 11/26 の2回目：よく呼ばれる関数が「大きくなる表」を全部読みしないことの見張り（移行はなし）
//   画面・Edge Functions・毎分〜毎時の処理から呼ばれる関数（SQL と plpgsql）を、全部読みを禁じて（enable_seqscan off）実際に呼び、
//   その取引の中で全部読みになった表を pg_stat_xact_user_tables の差で数える。全部読みしてよいのは、行の数が増えない小さな表だけ。
//   新しい移行で索引が使えない形になったら、ここで落ちて気づける（本番では表が大きくなってから遅くなるので、先に止める）
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

// 全部読みしてよい小さな表（行の数が利用者や日数で増えない、または数百行まで）
const SMALL = new Set(['public.airports', 'public.airline_codes', 'public.game_events', 'public.odpt_feed_dates', 'public.eta_calib',
  'public.eta_calib_mode', 'ops.airport_notices', 'public.atc_feeders',
  // 通知の購読：1端末1行。今は小さい。利用者が数千を超えたら、配列の GIN 索引（airports・flights・sp_airports・ga_airports）を足す
  'public.push_subs']);

// 種：関数が早く戻らず、中の文まで進むだけの行
const U = '00000000-0000-0000-0000-0000000000a1';
await db.exec(`insert into auth.users (id, email) values ('${U}', 'a@example.com'); select set_config('request.jwt.claim.sub', '${U}', false);
insert into public.flight_history (svc_date, flight, dep, arr, std, sta, atd, ata, reg, callsign, type, also)
select d, 'NH' || (100 + i), case when i % 2 = 0 then 'HND' else 'ITM' end, case when i % 2 = 0 then 'ITM' else 'HND' end,
       d + time '08:00' + make_interval(mins => i * 40), d + time '09:10' + make_interval(mins => i * 40),
       d + time '08:05' + make_interval(mins => i * 40), d + time '09:20' + make_interval(mins => i * 40), 'JA8' || (10 + i % 3) || 'A', 'ANA' || (100 + i), 'B788', array['JL9' || i]
  from generate_series(current_date - 9, current_date, interval '1 day') d(d), generate_series(1, 8) i;
insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source, aircraft)
select current_date + k, 'NH' || (100 + i), case when i % 2 = 0 then 'HND' else 'ITM' end, case when i % 2 = 0 then 'ITM' else 'HND' end,
       current_date + k + time '08:00' + make_interval(mins => i * 40), current_date + k + time '09:10' + make_interval(mins => i * 40), 'test', 'B788'
  from generate_series(-1, 1) k, generate_series(1, 8) i;
insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr)
select 'G-XWB' || (i % 3), 'BAW' || i, current_date - k, 'A35K', now() - make_interval(days => k, hours => 3), now() - make_interval(days => k, hours => 1), 'LHR', 'HND'
  from generate_series(0, 9) k, generate_series(5, 7) i;
insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day) select 'BAW' || i, 'HND', 0, -1, 600, 8, 10, current_date - 1 from generate_series(5, 7) i;
insert into public.foreign_legs (day, callsign, iata, dep_here, at, flight, airline, reg, type)
select current_date - k, 'BAW5', 'HND', 0, now() - make_interval(days => k), 'BA5', 'BA', 'G-XWB0', 'A35K' from generate_series(0, 9) k;
insert into public.live_positions (callsign, hex, lat, lon, alt_ft, ground, seen_at, reg) values ('BAW5', 'abc', 35.5, 139.8, 3000, false, now(), 'G-XWB0');
insert into public.push_subs (endpoint, p256dh, auth, flights, airports) values ('https://e/1', 'k', 'a', array['BA5@' || current_date, 'NH102@' || current_date], array['HND']);
insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts)
select 'HND', current_date - k, 'ANA' || (100 + i), now() - make_interval(days => k, mins => i), 1, 'x' from generate_series(0, 9) k, generate_series(1, 8) i;
insert into public.flight_tracks (svc_date, flight, dep, pts) select svc_date, flight, dep, 'x' from public.flight_history;`);

// よく呼ばれる所（呼ぶ元）
const CALLS = [
  // 画面（運用タブ・案内板・乗る便・空の道すじ）
  [`select public.airport_board('HND', 'dep')`, '案内板'],
  [`select public.airport_yesterday('HND')`, '昨日の空港'],
  [`select public.curfew_flights('HND')`, '門限'],
  [`select public.flight_alerts('HND')`, 'お知らせ'],
  [`select public.livery_board(array['JA8089','G-XWB0'])`, '特別塗装機の案内'],
  [`select public.livery_plans_upcoming('HND')`, '特別塗装機の予定'],
  [`select public.special_now()`, '特別塗装機のいま'],
  [`select public.flight_facts('[{"flight":"NH102","date":"${new Date().toISOString().slice(0, 10)}"}]'::jsonb)`, '便の事実'],
  [`select public.flight_lookup(current_date, 'NH102')`, '記録帳の便名'],
  [`select public.live_flight_sched('NH102', 'HND')`, '乗る便の時刻'],
  [`select public.spot_departures(array['HND','NRT'])`, '撮る人の出発'],
  [`select public.world_status_now(array['LAX','HNL'])`, '海外の空港のいま'],
  [`select public.usual_late('BA5', null, current_date, 'HND', null)`, 'いつもより遅い（便名）'],
  [`select public.usual_late(null, 'G-XWB0', current_date, null, null)`, 'いつもより遅い（登録記号）'],
  [`select public.airport_tracks('HND', current_date)`, '空の道すじ（今日）'],
  [`select public.airport_tracks('HND', current_date - 1)`, '空の道すじ（昨日）'],
  [`select public.track_quota_take('${U}'::uuid, 'HND', current_date - 10)`, '空の道すじの回数'],
  [`select public.my_pins()`, 'ピン止め'],
  [`select public.rl_check('k', 10, 60)`, '回数の守り'],
  // 毎分〜毎時の処理・Edge Functions
  [`select public.foreign_watch_sync()`, '海外の便の見張り（5分ごと）'],
  [`select ops.alert_watchdog()`, 'お知らせの見張り（15分ごと）'],
  [`select public.world_status_put('faa', now(), '[{"iata":"LAX","kind":"gdp","reason":"x"}]'::jsonb)`, '海外の止まり具合（2分ごと）'],
  // 運航情報：羽田の便のゲートと見込みを変える（時刻表の変更の記録の引き金も動く）
  [`select public.apply_flight_status((select jsonb_agg(jsonb_build_object('id', id, 'dep_gate', '12', 'etd', std + interval '30 minutes')) from public.flight_schedule where dep = 'HND'))`, '運航情報（毎分）'],
  [`select public.flight_alerts_put(jsonb_build_array(jsonb_build_object('flight', 'NH102', 'dep', 'HND', 'arr', 'ITM', 'svc_date', current_date, 'kind', 'delay', 'late', 30, 'message', 'x', 'gkey', 'NH102@' || current_date || '@HND', 'rank', 1)))`, 'お知らせを書く'],
  [`select public.alert_push_claim(jsonb_build_array(jsonb_build_object('sub_id', (select min(id) from public.push_subs), 'gkey', 'NH102@' || current_date || '@HND', 'svc_date', current_date, 'rank', 1, 'late', 30, 'body', 'x')))`, '送る前の印'],
  [`select public.reg_legs_touch(jsonb_build_array(jsonb_build_object('reg', 'JA811A', 'cs', 'ANA102', 'type', 'B788', 'at', now(), 'iata', 'HND', 'dir', 'dep')))`, '機体の区間'],
  [`select public.airport_hour_bad_roll(current_date - 2, current_date)`, '遅れの集計（毎時）'],
  [`select public.rwy_learned_roll(current_date - 2, current_date)`, '滑走路の集計（毎時）'],
  [`select public.flights_fill_actual(3, 2000)`, '実際の時刻を埋める（毎晩）'],
  [`select * from public.flights_track_todo(300)`, '航跡を埋める（毎晩）'],
  [`delete from public.track_points where t < now() - interval '36 hours'`, '航跡の掃除（30分ごと）'],
  [`delete from public.live_positions where seen_at < now() - interval '15 minutes'`, '位置の掃除（10分ごと）'],
];
const X = `select schemaname || '.' || relname t, seq_scan n from pg_stat_xact_user_tables`;
for (const [call, label] of CALLS) {
  let err = '', scans = [];
  try {
    await db.exec(`begin; set local enable_seqscan = off; set local statement_timeout = 10000`);
    const a = Object.fromEntries((await db.query(X)).rows.map(r => [r.t, r.n]));
    await db.query(call);
    scans = (await db.query(X)).rows.filter(r => r.n - (a[r.t] || 0) > 0).map(r => r.t);
  } catch (e) { err = e.message.split('\n')[0]; }
  await db.exec('rollback').catch(() => {});
  const big = scans.filter(t => !SMALL.has(t) && !t.startsWith('pg_temp'));   // 関数の中の一時の表は数えない
  check(`${label}：呼べて、大きくなる表を全部読みしない`, !err && big.length === 0, err || big);
}
// 見張りそのものが効くこと（索引のない列で絞ると落ちる）
{
  await db.exec(`begin; set local enable_seqscan = off`);
  const a = Object.fromEntries((await db.query(X)).rows.map(r => [r.t, r.n]));
  await db.query(`select count(*) from public.flight_history where aircraft = 'x'`);
  const s = (await db.query(X)).rows.filter(r => r.n - (a[r.t] || 0) > 0).map(r => r.t);
  await db.exec('rollback');
  check('見張りの確かめ：索引のない絞り込みは全部読みとして数えられる', s.includes('public.flight_history'), s);
}
if (bad) process.exit(1);
