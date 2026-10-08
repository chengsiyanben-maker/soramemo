-- 便の照合（運航確認）
-- 毎晩、前日以前の未確認のフライトを OpenSky の到着記録と照らし合わせる（Edge Function: verify-flights）。
alter table public.flights add column verify_attempts integer not null default 0;
alter table public.flights add column verify_note text;

-- 照合の対象：未確認・7日以内・前日以前に到着・3回まで
create index flights_to_verify on public.flights (arr_at) where status in ('provisional', 'with_flight_no') and verify_attempts < 3;

-- 定期実行の例（Supabase の「Database」→「Extensions」で pg_cron と pg_net を有効にしてから、値を埋めて実行する）
-- select cron.schedule('verify-flights-nightly', '30 18 * * *',  -- 毎日 18:30 UTC ＝ 日本時間 3:30
--   $$ select net.http_post(
--        url := 'https://<プロジェクト>.supabase.co/functions/v1/verify-flights',
--        headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', '<CRON_SECRET と同じ値>'),
--        body := '{}'::jsonb) $$);
