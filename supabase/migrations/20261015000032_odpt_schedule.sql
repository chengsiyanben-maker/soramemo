-- 遅れ・ダイバートのお知らせ用のダイヤを、ODPT の公式のフライト時刻表（JAL・ANA、公共交通オープンデータ基本ライセンス）から毎日入れる。
-- ・schedule-sync 関数を毎日2回（日本時間4:40・16:40）呼ぶ。今日と明日の便を flight_schedule に入れる（同じ日・便名・出発空港は上書き）
-- ・live_positions：機体の記録（airport-traffic）が取った日本中の機体の最新の位置。便の見張り（flight-watch）は adsb.lol に別に問い合わせず、ここを読む
create table if not exists public.live_positions (
  callsign  text primary key check (length(callsign) <= 10),
  hex       text,
  lat       double precision not null,
  lon       double precision not null,
  alt_ft    integer,
  ground    boolean not null default false,
  fpm       integer,
  seen_at   timestamptz not null
);
create index if not exists live_positions_seen on public.live_positions (seen_at);
alter table public.live_positions enable row level security;
revoke all on public.live_positions from public, anon, authenticated;

create table if not exists public.schedule_sync_runs (
  id     int primary key default 1 check (id = 1),
  ran_at timestamptz not null default 'epoch',
  result jsonb
);
insert into public.schedule_sync_runs (id) values (1) on conflict do nothing;
alter table public.schedule_sync_runs enable row level security;
revoke all on public.schedule_sync_runs from public, anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、ダイヤの取り込みの定期実行は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('schedule-sync', '40 7,19 * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/schedule-sync',
        headers := '{"User-Agent": "soramemo (schedule-sync)"}'::jsonb,
        timeout_milliseconds := 120000)
    $job$)
  $q$;
  -- 古い位置は10分ごとに消す
  execute $q$ select cron.schedule('live-positions-cleanup', '*/10 * * * *', $job$ delete from public.live_positions where seen_at < now() - interval '15 minutes' $job$) $q$;
end
$outer$;
