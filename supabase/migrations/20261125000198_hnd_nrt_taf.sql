-- 羽田・成田の飛行場予報（TAF）を残す（PM の指示 11/25 18時45分「羽田・成田を優先して取る＋滑走路の予想の当たり具合」の2番）
--   本人「羽田、成田の滑走路の使い方を気象と関連付けて予想できそう？」→「羽田、成田は優先的に取って」
--   今は METAR（実況）だけを wx_obs に残していて、予報（TAF）は空港の今の画面のために edge_cache に上書きしているだけ（残らない）。
--   「数時間前の TAF から滑走路の使い方を当てられるか」を ops_log（実際の機体からの判定）と比べるため、TAF を残す
--   1. wx_taf：TAF の原文（発表ごとに1行。訂正（AMD）も別の行）
--   2. wx_taf_hours：その TAF の時間ごと（毎時0分）の風（向き・速さ・突風）・視程・TEMPO/PROB の風と、その風から推定した運用（est_mode）
--      est_mode は画面と同じ推定（_shared/ops_core.js の estimate。羽田は追い風7kt・都心ルート・深夜の時刻も使う）
--   出どころ：aviationweather.gov の Data API（米国の航空気象センター。パブリックドメイン。METAR と同じ所。User-Agent を付け、1分に100回より十分少なく）
--   取るのは wx-archive（毎時7分の今の回と、毎時41分の羽田・成田だけの回）。過去の TAF は date の指定で 10/15（ops_log の始まり）までさかのぼる
--   量：1回の TAF は30時間 → 30行。羽田・成田で1日およそ 8〜12回 → 1日 300行前後（1年で約11万行・十数MB）。ずっと残す（消さない）
--   RLS：有効にして方針は作らない（anon・authenticated は読めも書けもしない）。読み書きするのは関数（service_role）と本人の SQL Editor だけ
--   影響：チェックイン・経営のどちらの画面にも出さない（構想段階）。関数 wx-archive が書き足すだけ
set lock_timeout = '5s';

create table if not exists public.wx_taf (
  icao       text not null check (icao ~ '^[A-Z]{4}$'),
  issued     timestamptz not null,          -- 発表の時刻
  valid_from timestamptz not null,
  valid_to   timestamptz not null,
  raw        text not null check (length(raw) <= 2000),
  saved_at   timestamptz not null default now(),
  primary key (icao, issued),
  check (valid_from < valid_to)
);
comment on table public.wx_taf is '羽田・成田の飛行場予報（TAF）の原文。aviationweather.gov（パブリックドメイン）。wx-archive が書く。ずっと残す';

create table if not exists public.wx_taf_hours (
  icao     text not null check (icao ~ '^[A-Z]{4}$'),
  at       timestamptz not null,            -- 予報の時刻（毎時0分）
  issued   timestamptz not null,            -- どの TAF か
  lead_h   smallint not null,               -- 発表から何時間先か
  wdir     smallint,                        -- 風向（度）。VRB は null
  wspd     smallint,                        -- 風速（ノット）
  wgst     smallint,                        -- 突風（ノット）
  vrb      boolean not null default false,
  changing boolean not null default false,  -- BECMG の変わっている途中
  vis_m    integer,
  wx       text check (length(wx) <= 40),
  t_kind   text check (length(t_kind) <= 8),   -- TEMPO・PROB30 など（かかっていなければ null）
  t_wdir   smallint, t_wspd smallint, t_wgst smallint,
  est_mode text check (length(est_mode) <= 12),   -- その風から推定した運用（羽田 north・south・city・nightN・nightS、成田 a・b）
  primary key (icao, at, issued),
  foreign key (icao, issued) references public.wx_taf (icao, issued)
);
comment on table public.wx_taf_hours is 'TAF の時間ごとの風と推定の運用。「n時間前の TAF で当たるか」を ops_log と比べるため。ずっと残す';
-- 発表ごとに読む（作り直し・確かめ用）
create index if not exists wx_taf_hours_issued on public.wx_taf_hours (icao, issued);

alter table public.wx_taf enable row level security;
alter table public.wx_taf_hours enable row level security;
revoke all on public.wx_taf, public.wx_taf_hours from public, anon, authenticated;
grant all on public.wx_taf, public.wx_taf_hours to service_role;

-- 羽田・成田だけの回（毎時41分）：TAF（訂正を取りこぼさない）と METAR（直近6時間）、過去の TAF のさかのぼり（1回で1日ぶん）
--   今の wx-archive（毎時7分）でも TAF を取る。aviationweather.gov は TAF を発表の20分ほどあとに載せるので、41分の回で同じ時間のうちに拾える
--   呼ぶだけの仕事なので、上限は短く（関数の中の待ちは net.http_get の timeout で切る）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  if exists (select 1 from cron.job where jobname = 'wx-hnd-nrt') then perform cron.unschedule('wx-hnd-nrt'); end if;
  execute $q$ select cron.schedule('wx-hnd-nrt', '41 * * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s';
    select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/wx-archive?part=hnt', headers := '{"User-Agent": "soramemo (wx-archive)"}'::jsonb, timeout_milliseconds := 60000)
  $job$) $q$;
end
$outer$;
reset lock_timeout;
