-- 定期の手入れ 11/16：本番で SQL Editor に貼って流す「読むだけ」の SQL（書き換えなし・一時ファイルを使わない・20秒で止まる）
-- 結果は1つの表で出る。表を CSV で保存して docs/pm/maint/2026-11-16-result.csv に置くか、会話に貼ってください
--   kind = job  ：pg_cron の仕事ごとに、文に statement_timeout があるか・前の記録（今は1日分だけ残る）の回数・失敗・いちばん長い秒
--   kind = func ：裏の処理が呼ぶ書く関数12個に lock_timeout が付いているか（移行 170 を反映したあとに 5s／10s になる）
set statement_timeout = '20s';

with runs as (
  select jobid,
         count(*)                                              as n,
         count(*) filter (where status <> 'succeeded')         as failed,
         round(max(extract(epoch from (end_time - start_time)))::numeric, 1) as max_sec,
         max(start_time)                                       as last_start
    from cron.job_run_details
   where start_time > now() - interval '7 days'
   group by jobid
)
select 'job' as kind,
       j.jobname as name,
       j.schedule as detail,
       (j.command ilike '%statement_timeout%') as has_timeout,
       (j.command ilike '%net.http_%') as is_http,
       coalesce(r.n, 0) as runs,
       coalesce(r.failed, 0) as failed,
       r.max_sec,
       r.last_start
  from cron.job j
  left join runs r on r.jobid = j.jobid
union all
select 'func', p.proname, array_to_string(p.proconfig, ' '),
       coalesce(array_to_string(p.proconfig, ' ') like '%lock_timeout%', false), null, null, null, null, null
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
   and p.proname in ('archive_airport_daily','archive_rotations','archive_track_points','archive_user_flights','cold_done',
                     'airport_tracks_put','reg_legs_route','timetable_replace','world_status_put',
                     'apply_flight_status','flight_alerts_put','reg_legs_touch')
order by 1, 4, 2;
