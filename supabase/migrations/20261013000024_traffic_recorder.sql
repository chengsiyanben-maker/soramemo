-- 羽田の周りの機体の線を、誰も地図を開いていなくても記録しておく。
-- 30秒ごとに airport-traffic を呼ぶと、関数が adsb.lol から位置を取り、traffic_trails に点を足していく。
-- これで、地図を開いた瞬間から、近づいてくる機体の長い線が出る（線は20分ぶんまで）。
-- 呼び出しは1日およそ2,900回。Supabase の無料枠（関数の呼び出し 月50万回）に収まる。
--
-- pg_cron と pg_net が使える環境（Supabase）だけで設定する。手元のテスト（PGlite）では何もしない。
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、機体の記録の定期実行は設定しない';
    return;
  end if;

  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';

  -- 30秒ごとに羽田の機体を記録する（同じ名前で登録し直すと、上書きになる）
  execute $q$
    select cron.schedule('traffic-record-hnd', '30 seconds', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/airport-traffic?iata=HND',
        headers := '{"User-Agent": "soramemo (traffic-recorder)"}'::jsonb,
        timeout_milliseconds := 15000)
    $job$)
  $q$;

  -- 定期実行の記録は増え続けるので、毎日1回、1日より古い分を消す
  execute $q$
    select cron.schedule('cron-history-cleanup', '10 19 * * *', $job$
      delete from cron.job_run_details where end_time < now() - interval '1 day'
    $job$)
  $q$;
end
$outer$;
