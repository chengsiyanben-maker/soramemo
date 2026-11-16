-- 定期の手入れ（11/6）：データの整理・圧縮・処理の速さ。記録は1行も消さない（消す処理の範囲も今のまま）
--   1. 毎日の処理（データ担当の持ち場の、SQL で動くもの）に時間の上限（statement_timeout）と待つ上限（lock_timeout）を付ける。
--      時刻と中身は今のまま。止まってもその処理だけが失敗し、ほかの処理は巻き込まない。
--      cron の記録（cron.job_run_details）は1日 → 8日残す（週に1回の点検 docs/pm/maint/weekly-check.sql で、7日分の所要時間と失敗を見るため）
--      経営の処理（co-*・co3-*）は経営の持ち場なので、ここでは変えない（報告に依頼文）
--      insights-cleanup は移行の中では例として書かれているだけ（本番にあるかは点検で見る）なので、ここでは足さない
--   2. 日付だけで探す処理のための BRIN 索引（とても小さい索引。表の大きさの千分の1ほど）
--      ・airport_tracks_all(day)：全機の航跡。cold-archive の候補探し（cold_candidates）・移す日の読み出し（cold_rows）・消す（cold_done）が
--        主キー（iata, day, …）の2番目の列 day だけで探すので、今は毎晩、表を丸ごと読んでいる
--      ・rwy_samples(at)・ga_events(at)：同じく cold-archive が時刻だけで探す（今ある索引は空港や種類が先頭）
--      ・atc_msgs(at)：毎晩の atc-cleanup が時刻だけで探す（今ある索引は空港が先頭）
--      どの表も時刻の順に足されるので、BRIN がよく効く。書き込みの重さはほとんど増えない
--   3. 出入りの激しい表の自動掃除（autovacuum）を早めにする
--      ・track_points（30分ごとに36時間より前を消す）・live_positions（10分ごとに15分より前を消す）
--      死んだ行が2割たまるまで待つ今の設定だと、表が膨らんだままになりやすい。2%（＋1000行）で掃除を始める
--   RLS：表は作らない・権限も変えない（索引と設定と毎日の処理の文だけ）。
--   影響：チェックイン・経営の画面とロジックは変わらない（返す値も同じ）。

-- 2. BRIN 索引（作るときは表を1回読む。書き込みは止めるが短い。rwy-learn（日本時間 5:15）の時間を避けて流す）
create index if not exists airport_tracks_all_day_brin on public.airport_tracks_all using brin (day) with (pages_per_range = 32);
create index if not exists rwy_samples_at_brin on public.rwy_samples using brin (at) with (pages_per_range = 32);
create index if not exists ga_events_at_brin on public.ga_events using brin (at) with (pages_per_range = 32);
create index if not exists atc_msgs_at_brin on public.atc_msgs using brin (at) with (pages_per_range = 32);

-- 3. 自動掃除を早めに
alter table public.track_points set (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_scale_factor = 0.05);
alter table public.live_positions set (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_threshold = 1000, autovacuum_analyze_scale_factor = 0.05);

-- 1. 毎日の処理に時間の上限（時刻・中身は今のまま。cron-history-cleanup だけ残す日数を 1日 → 8日）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 頻繁に動くもの
  execute $q$ select cron.schedule('archive-cleanup', '*/30 * * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s'; delete from public.track_points where t < now() - interval '36 hours'; $job$) $q$;
  execute $q$ select cron.schedule('live-positions-cleanup', '*/10 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s'; delete from public.live_positions where seen_at < now() - interval '15 minutes' $job$) $q$;
  execute $q$ select cron.schedule('alert-watchdog', '*/15 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s'; select ops.alert_watchdog() $job$) $q$;
  -- 毎晩の掃除（見張りの途中の記録・古い時刻表など。航路と機体の記録は消さない）
  execute $q$ select cron.schedule('cron-history-cleanup', '10 19 * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; delete from cron.job_run_details where end_time < now() - interval '8 days' $job$) $q$;
  execute $q$ select cron.schedule('atc-cleanup', '17 19 * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s'; delete from public.atc_msgs where at < now() - interval '7 days' $job$) $q$;
  execute $q$ select cron.schedule('ga-cleanup', '17 19 * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; delete from public.ga_watch where updated_at < now() - interval '1 hour' $job$) $q$;
  execute $q$ select cron.schedule('flight-watch-cleanup', '20 19 * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s'; delete from public.flight_alerts where created_at < now() - interval '2 days'; delete from public.flight_schedule where std < now() - interval '14 days'; $job$) $q$;
  execute $q$ select cron.schedule('rwy-samples-cleanup', '23 19 * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; delete from public.arr_watch where updated_at < now() - interval '30 minutes' $job$) $q$;
  execute $q$ select cron.schedule('archive-cleanup-daily', '40 20 * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; delete from public.archive_runs where day < (now() at time zone 'Asia/Tokyo')::date - 366; $job$) $q$;
  -- 毎晩の学習（到着予想・地上走行の時間）
  execute $q$ select cron.schedule('eta-calib', '35 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.refresh_eta_calib() $job$) $q$;
  execute $q$ select cron.schedule('taxi-out', '40 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.refresh_taxi_out() $job$) $q$;
end
$outer$;
