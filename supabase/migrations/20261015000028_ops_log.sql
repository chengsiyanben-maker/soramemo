-- 運用の判定の記録：14空港の「風からの推定」と「実際の機体からの判定」を5分ごとに残し、外れ（食い違い）を後から拾えるようにする。
-- 書くのは airport-traffic（記録用の呼び出し）だけ。読むのは運営者の道具（tools/ops_report.mjs、service_role）だけ。
create table if not exists public.ops_log (
  id          bigint generated always as identity primary key,
  at          timestamptz not null default now(),
  iata        text not null check (iata ~ '^[A-Z]{3}$'),
  wdir        smallint,                    -- 気象通報の風向（度。VRB は null）
  wspd        smallint,                    -- 風速（ノット）
  metar_at    timestamptz,                 -- 気象通報の時刻
  est_mode    text not null,               -- 風からの推定の運用（modes のキー）
  est_unsure  boolean not null default false,
  obs_mode    text,                        -- 実際の機体からの判定（判定できなければ null）
  obs_mixed   boolean not null default false,
  obs_arr     smallint not null default 0, -- 判定に使った着陸機の数
  obs_dep     smallint not null default 0, -- 判定に使った離陸機の数
  planes      smallint not null default 0  -- この空港の着陸・離陸の機体の数
);
create index if not exists ops_log_iata_at on public.ops_log (iata, at desc);
create index if not exists ops_log_at on public.ops_log (at);

alter table public.ops_log enable row level security;
revoke all on public.ops_log from public, anon, authenticated;

-- 空港ごとのまとめ（直近 p_days 日）：記録の数、実機で判定できた数、推定と一致・食い違い、分かれていた数
create or replace function public.ops_log_summary(p_days int default 7) returns table (
  iata text, samples bigint, observed bigint, agree bigint, disagree bigint, mixed bigint, unsure bigint
) language sql stable security definer set search_path = public as $$
  select iata, count(*),
         count(*) filter (where obs_mode is not null),
         count(*) filter (where obs_mode is not null and not est_unsure and obs_mode = est_mode),
         count(*) filter (where obs_mode is not null and not est_unsure and obs_mode <> est_mode),
         count(*) filter (where obs_mixed),
         count(*) filter (where est_unsure)
  from public.ops_log where at > now() - make_interval(days => greatest(1, least(p_days, 90)))
  group by iata order by iata
$$;
revoke all on function public.ops_log_summary(int) from public, anon, authenticated;
grant execute on function public.ops_log_summary(int) to service_role;

-- 90日より古い記録は毎日消す（pg_cron がある環境だけ）
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron') then
    raise notice 'pg_cron がないため、運用の記録の掃除は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_cron';
  execute $q$ select cron.schedule('ops-log-cleanup', '35 19 * * *', $job$ delete from public.ops_log where at < now() - interval '90 days' $job$) $q$;
end
$outer$;
