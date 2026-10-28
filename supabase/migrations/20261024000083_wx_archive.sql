-- 天気の記録（ずっと残す）：空港の気象通報（METAR）の原文と、気象庁の台風情報
--   欠航や遅れの原因（強風・雪・台風）をあとから調べられるようにする。いまの運用の記録（ops_log）は風だけで、天気の現象と台風の位置がない
--   METAR：aviationweather.gov（パブリックドメイン）。台風：気象庁（出どころを書いて使う）。どちらも利用者の情報は含まない
create table if not exists public.wx_obs (
  icao  text not null check (icao ~ '^[A-Z]{4}$'),
  at    timestamptz not null,           -- 観測の時刻
  raw   text not null check (length(raw) <= 400),
  wx    text,                           -- 天気の現象（例：-SHRA、+TSRA、SN、FZRA、BR）
  wdir  smallint, wspd smallint, wgst smallint,   -- 風向（度）・風速・最大瞬間（ノット）
  vis_m integer,
  primary key (icao, at)
);
alter table public.wx_obs enable row level security;
revoke all on public.wx_obs from public, anon, authenticated;

create table if not exists public.typhoon_snap (
  tc_id    text not null check (tc_id ~ '^TC\d{4}$'),
  issue    timestamptz not null,        -- 気象庁の発表の時刻
  number   text,                        -- 台風の番号（例：2630）。番号がつく前は記号
  category text,                        -- TY・STS・TS・TD など
  spec     jsonb,                       -- specifications.json（その時刻の位置・中心気圧・風・暴風域）
  forecast jsonb,                       -- forecast.json（予報円）
  saved_at timestamptz not null default now(),
  primary key (tc_id, issue)
);
alter table public.typhoon_snap enable row level security;
revoke all on public.typhoon_snap from public, anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 1時間ごと（毎時7分）。METAR は直近3時間ぶんを取るので、1回とんでも抜けない
  execute $q$ select cron.schedule('wx-archive', '7 * * * *', $job$
    select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/wx-archive', headers := '{"User-Agent": "soramemo (wx-archive)"}'::jsonb, timeout_milliseconds := 60000)
  $job$) $q$;
end
$outer$;
