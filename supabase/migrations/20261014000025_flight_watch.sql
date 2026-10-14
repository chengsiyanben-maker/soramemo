-- 予定の便（ダイヤ）と今飛んでいる機体を照らし合わせて、遅れ・ダイバートを知らせる仕組み。
-- ・flight_schedule：予定の便。読み込むのは運営者の道具（tools/load_schedule.mjs、service_role）だけ。出典の列を必ず入れる
--   （公式の時刻表を使う。公式でないダイヤは本番に入れない。ダイヤが空なら、関数は何もしない）
-- ・flight_watch：便ごとの見張りの状態（離陸・着陸の時刻など）。関数（flight-watch）だけが書く
-- ・flight_alerts：出したお知らせ。利用者は public.flight_alerts()（直近12時間）で読む
-- ・push_subs：スマホへの通知の宛先（ブラウザの購読）と、知らせてほしい空港。関数（push-subscribe）だけが書く

create table if not exists public.flight_schedule (
  id        bigint generated always as identity primary key,
  svc_date  date not null,                 -- 運航日（出発の日本時間の日付）
  flight    text not null check (flight ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$'),
  dep       text not null check (dep ~ '^[A-Z]{3}$'),
  arr       text not null check (arr ~ '^[A-Z]{3}$'),
  std       timestamptz not null,          -- 出発の定刻
  sta       timestamptz not null,          -- 到着の定刻
  aircraft  text,
  source    text not null check (length(source) between 1 and 200),
  unique (svc_date, flight, dep)
);
create index if not exists flight_schedule_std on public.flight_schedule (std);

create table if not exists public.flight_watch (
  schedule_id bigint primary key references public.flight_schedule(id) on delete cascade,
  state       jsonb not null,
  updated_at  timestamptz not null default now()
);

create table if not exists public.flight_alerts (
  id          bigint generated always as identity primary key,
  schedule_id bigint references public.flight_schedule(id) on delete set null,
  kind        text not null check (kind in ('delay_dep','no_takeoff','delay_arr','divert','return','divert_landed')),
  flight      text not null,
  dep         text not null,
  arr         text not null,
  iata        text[] not null,             -- 関係する空港（その空港の画面・通知に出す）
  message     text not null check (length(message) <= 300),
  created_at  timestamptz not null default now()
);
create index if not exists flight_alerts_recent on public.flight_alerts (created_at desc);

create table if not exists public.push_subs (
  id         bigint generated always as identity primary key,
  endpoint   text not null unique check (endpoint ~ '^https://' and length(endpoint) <= 1000),
  p256dh     text not null check (length(p256dh) <= 200),
  auth       text not null check (length(auth) <= 100),
  airports   text[] not null default '{}',
  created_at timestamptz not null default now(),
  last_ok    timestamptz
);

-- 見張りの関数が最後に動いた時刻（何度呼ばれても、1分に1回しか機体を取りに行かない）
create table if not exists public.flight_watch_runs (
  id     int primary key default 1 check (id = 1),
  ran_at timestamptz not null default 'epoch'
);
insert into public.flight_watch_runs (id) values (1) on conflict do nothing;

alter table public.flight_schedule enable row level security;
alter table public.flight_watch enable row level security;
alter table public.flight_alerts enable row level security;
alter table public.push_subs enable row level security;
alter table public.flight_watch_runs enable row level security;
revoke all on public.flight_schedule, public.flight_watch, public.flight_alerts, public.push_subs, public.flight_watch_runs from public, anon, authenticated;

-- 利用者向け：直近12時間のお知らせ。p_iata を渡すと、その空港に関係するものだけ。ログインしていなくても読める
create or replace function public.flight_alerts(p_iata text default null) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'kind', a.kind, 'flight', a.flight, 'dep', a.dep, 'arr', a.arr,
           'iata', a.iata, 'message', a.message, 'at', a.created_at) order by a.created_at desc), '[]'::jsonb)
  from (select * from public.flight_alerts
        where created_at > now() - interval '12 hours' and (p_iata is null or upper(p_iata) = any(iata))
        order by created_at desc limit 100) a
$$;
revoke all on function public.flight_alerts(text) from public;
grant execute on function public.flight_alerts(text) to anon, authenticated;

-- 1分ごとに見張りの関数を呼ぶ（pg_cron と pg_net がある環境だけ。手元のテストでは何もしない）
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、便の見張りの定期実行は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('flight-watch', '* * * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/flight-watch',
        headers := '{"User-Agent": "soramemo (flight-watch)"}'::jsonb,
        timeout_milliseconds := 50000)
    $job$)
  $q$;
  -- お知らせと見張りの状態は、2日より古いものを毎日消す
  execute $q$
    select cron.schedule('flight-watch-cleanup', '20 19 * * *', $job$
      delete from public.flight_alerts where created_at < now() - interval '2 days';
      delete from public.flight_schedule where std < now() - interval '2 days';
    $job$)
  $q$;
end
$outer$;
