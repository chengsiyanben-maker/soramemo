-- 便ごとの実績は1年（365日）残す（運営者のパソコンにも毎日保存している）。航跡31日・機体のつながり60日はそのまま
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron') then return; end if;
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('archive-cleanup-daily', '40 20 * * *', $job$
      delete from public.flight_tracks where svc_date < (now() at time zone 'Asia/Tokyo')::date - 31;
      delete from public.flight_history where svc_date < (now() at time zone 'Asia/Tokyo')::date - 365;
      delete from public.archive_runs where day < (now() at time zone 'Asia/Tokyo')::date - 365;
      delete from public.rotation_obs where svc_date < (now() at time zone 'Asia/Tokyo')::date - 60;
    $job$)
  $q$;
end
$outer$;
