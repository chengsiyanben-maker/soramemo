-- 経営の毎日・毎時の仕事（co・co3 の20本）に時間の上限（statement_timeout）と lock_timeout を付ける（データ担当からの依頼。11/13 速さの見直しの 4）
--   時刻と中身は今のまま。上限は仕事の文の先頭で付ける（関数の設定では効かない。20261105000152 の説明のとおり）
--   上限：15分ごと・毎時のものは1分、外の取り込み（pg_net で頼むだけ）は30秒、ふつうの毎晩の仕事は3分、
--         全部の会社の1日を記録する co3-daily と、月・シーズンの締めは5分。どれも lock_timeout は5秒（待ち続けない）
--   時間切れになった仕事はその回だけ止まり（途中までの書き込みは戻る）、次の回にまた動く。ほかの仕事は止めない
--   co3-trouble-detect は 20261028000119 で止めたので、ここでも作らない
--   表・関数・RLS・権限は変えない。画面は変わらない

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 15分ごと・毎時
  execute $q$ select cron.schedule('co3-legs-check', '*/15 * * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; select public.co3_legs_check() $job$) $q$;
  execute $q$ select cron.schedule('co3-trouble-expire', '5 * * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; select public.co3_trouble_expire() $job$) $q$;
  -- 毎晩（ふつう）
  execute $q$ select cron.schedule('co-sky', '20 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co_sky_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co-rank', '45 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co_rank_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co-size', '15 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co_size_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co3-route-real', '25 20 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_route_real_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co3-satisfaction', '0 18 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_satisfaction_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co3-slots', '0 18 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_slots_decide() $job$) $q$;
  execute $q$ select cron.schedule('co3-breakdown', '0 19 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_breakdown_draw() $job$) $q$;
  execute $q$ select cron.schedule('co3-events', '5 19 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_events_draw() $job$) $q$;
  execute $q$ select cron.schedule('co3-orders', '10 19 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_orders_deliver() $job$) $q$;
  execute $q$ select cron.schedule('co3-codeshare', '15 19 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_cs_daily(); select public.co3_ally_daily(); $job$) $q$;
  execute $q$ select cron.schedule('co3-checks', '30 15 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_checks_run() $job$) $q$;
  execute $q$ select cron.schedule('co3-heavy', '35 15 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_heavy_run() $job$) $q$;
  execute $q$ select cron.schedule('co3-weather-cleanup', '40 19 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; delete from public.co3_wx where at < now() - interval '3 days' $job$) $q$;
  -- 毎晩（重いもの・締め）
  execute $q$ select cron.schedule('co3-daily', '50 14 * * *', $job$ set statement_timeout = '5min'; set lock_timeout = '5s'; select public.co3_daily_record() $job$) $q$;
  execute $q$ select cron.schedule('co3-season-close', '0 21 * * *', $job$ set statement_timeout = '5min'; set lock_timeout = '5s';
      select public.co3_season_close() where extract(day from (now() at time zone 'Asia/Tokyo')) = 1 and extract(month from (now() at time zone 'Asia/Tokyo'))::int in (1, 4, 7, 10) $job$) $q$;
  execute $q$ select cron.schedule('co3-month-close', '5 21 * * *', $job$ set statement_timeout = '5min'; set lock_timeout = '5s';
      select public.co3_month_close() where extract(day from (now() at time zone 'Asia/Tokyo')) = 1 $job$) $q$;
  -- 外の取り込み（関数を頼むだけ。返事は待たない）
  if exists (select 1 from pg_extension where extname = 'pg_net') then
    execute $q$ select cron.schedule('co3-weather', '2 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s';
      select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/co3-weather', headers := '{"User-Agent": "soramemo (co3-weather)"}'::jsonb, timeout_milliseconds := 50000)
    $job$) $q$;
    execute $q$ select cron.schedule('co3-typhoon', '17 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s';
      select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/co3-typhoon', headers := '{"User-Agent": "soramemo (co3-typhoon)"}'::jsonb, timeout_milliseconds := 50000)
    $job$) $q$;
  end if;
end
$outer$;
