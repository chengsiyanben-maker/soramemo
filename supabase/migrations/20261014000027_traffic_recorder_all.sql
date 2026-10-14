-- 機体の線の記録を、羽田だけから7空港すべてに広げる（地図を開いた瞬間から、どの空港でも長い線が出て、実際の機体で運用を判定できる）。
-- 呼び出しは今までどおり30秒に1回（1日およそ2,900回）。関数の中で、羽田は毎回、ほかの6空港は1分に1回だけ adsb.lol に取りに行く。
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、機体の記録の定期実行は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  if exists (select 1 from cron.job where jobname = 'traffic-record-hnd') then
    perform cron.unschedule('traffic-record-hnd');
  end if;
  execute $q$
    select cron.schedule('traffic-record', '30 seconds', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/airport-traffic?iata=RECORD',
        headers := '{"User-Agent": "soramemo (traffic-recorder)"}'::jsonb,
        timeout_milliseconds := 25000)
    $job$)
  $q$;
end
$outer$;
