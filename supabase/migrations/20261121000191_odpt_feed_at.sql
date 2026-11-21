-- ODPT のデータの時刻をサーバーから返す（11/21 PM「改善担当の見回りの指摘」2。report-sweep-1121.md の 2）
-- ・画面（PR #107・index.html の loadOdptAt）は rpc/odpt_feed_at を POST して { status_at, timetable_at } を待っている。
--   関数がないので毎回 404 になり、出典に「運航情報 ○時○分・時刻表 ○月○日時点」が出ていなかった（ODPT の約束：dc:date を出典の近くに出す）
-- ・odpt_feed_at()：移行179 の odpt_feed_dates を読むだけ。
--     status_at    … FlightInformationDeparture／FlightInformationArrival（運航情報）の dc:date のいちばん新しいもの
--     timetable_at … FlightSchedule（時刻表）の dc:date のいちばん新しいもの
--   どちらも dc:date がなければ null（取り込んだ時刻 fetched_at では埋めない：ODPT のデータの時刻ではないため）
-- ・表は変えない（odpt_feed_dates の RLS は移行179 のまま：anon・authenticated は読むだけ、書くのは service_role の関数だけ）。
--   この関数は呼ぶ人の権限で読む（security invoker）。行は十数行なので軽いが、念のため statement_timeout 2秒
-- 影響：チェックイン（出典の文に時刻が入る。画面のコードはもう入っている）。経営は使わない
set lock_timeout = '10s';

create or replace function public.odpt_feed_at()
returns jsonb
language sql stable security invoker
set search_path = public set statement_timeout = '2s' as $$
  select jsonb_build_object(
    'status_at',    max(dc_date) filter (where feed like 'FlightInformation%'),
    'timetable_at', max(dc_date) filter (where feed like 'FlightSchedule:%'))
    from public.odpt_feed_dates
$$;
revoke all on function public.odpt_feed_at() from public;
grant execute on function public.odpt_feed_at() to anon, authenticated, service_role;
