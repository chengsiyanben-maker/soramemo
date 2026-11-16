-- 定期の手入れ 11/16（データ担当）：時間の上限のない毎日・裏の処理をなくす。表・列・索引・RLS・権限・関数の中身は変えない
--   1. 毎晩の仕事 ops-log-cleanup（運用の記録の90日より前を消す。ops_log は運用の記録で、航路・機体の記録ではない）に
--      statement_timeout（2分）と lock_timeout（5s）を付ける。時刻と中身は今のまま（main で上限のなかった SQL の仕事の残り。
--      ほかの上限のない SQL の仕事は 173（もとは maint/2026-11-06 の 153）にある）
--   2. 裏の処理（Edge Functions）が service_role で呼ぶ「書く関数」12個に lock_timeout を付ける。
--      service_role には statement_timeout がなく、ほかの処理がつかんだ行や表を待ち続けると、毎分・30秒ごとの処理がうしろに詰まる。
--      関数の設定（alter function … set）は statement_timeout には効かない（20261105000152 の説明のとおり）が、lock_timeout は効く。
--      待ちが上限を超えたらその回だけ失敗し、どの呼び出し元もエラーを記録して次の回でやり直す（daily-archive・cold-archive・
--      rwy-learn・timetable-sync・world-status・odpt-status・flight-watch・airport-traffic の index.ts で確かめた）
--        毎晩・数時間ごと（5s）：archive_airport_daily・archive_rotations・archive_track_points・archive_user_flights・cold_done・
--                                  airport_tracks_put・reg_legs_route・timetable_replace・world_status_put
--        毎分・30秒ごと（10s）：apply_flight_status・flight_alerts_put・reg_legs_touch（2つの記録の処理が同じ機体を書くので、短い待ちは許す）
--   ※ maint/2026-11-07・11-09・11-10 は cold_done・archive_airport_daily・airport_tracks_put を create or replace で作り直す。
--     create or replace は関数の設定を消すので、それらはこの移行より前に入れる（反映の順は報告に書いた）
-- 影響：チェックイン・経営とも画面と値は変わらない（待ちすぎたときに、その回の取り込みが次の回に回るだけ）。経営の関数は変えない

-- 1
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$
    select cron.schedule('ops-log-cleanup', '35 19 * * *', $job$
      set statement_timeout = '2min'; set lock_timeout = '5s';
      delete from public.ops_log where at < now() - interval '90 days'
    $job$)
  $q$;
end
$outer$;

-- 2
alter function public.archive_airport_daily(date) set lock_timeout = '5s';
alter function public.archive_rotations(date) set lock_timeout = '5s';
alter function public.archive_track_points(date) set lock_timeout = '5s';
alter function public.archive_user_flights(date) set lock_timeout = '5s';
alter function public.cold_done(text, date, text, int, int) set lock_timeout = '5s';
alter function public.airport_tracks_put(jsonb) set lock_timeout = '5s';
alter function public.reg_legs_route(jsonb) set lock_timeout = '5s';
alter function public.timetable_replace(text, text, jsonb) set lock_timeout = '5s';
alter function public.world_status_put(text, timestamptz, jsonb) set lock_timeout = '5s';
alter function public.apply_flight_status(jsonb) set lock_timeout = '10s';
alter function public.flight_alerts_put(jsonb) set lock_timeout = '10s';
alter function public.reg_legs_touch(jsonb) set lock_timeout = '10s';
