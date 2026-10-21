-- 着陸する滑走路の学習用の記録：羽田・成田に着陸する機体（航空会社を問わない）の、来た方面・途中のルート・着陸した滑走路を残す。
-- ・arr_watch：近づいている機体の途中の位置（airport-traffic が30秒ごとに書く。30分で消す）
-- ・rwy_samples：着陸した滑走路が分かった機体1機ごとの記録（来た方面、120km・60km・30kmの円に入った方角、途中の点）。90日で消す
-- どちらも運営の分析用で、利用者からは読めない
create table if not exists public.arr_watch (
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  hex        text not null check (length(hex) <= 12),
  callsign   text check (length(callsign) <= 10),
  type       text check (length(type) <= 8),
  first_km   real,
  first_brg  smallint,
  ent120     smallint,
  ent60      smallint,
  ent30      smallint,
  pts        jsonb not null default '[]'::jsonb,   -- [[秒, 緯度, 経度, 高度ft], …] 1分に1点、40点まで
  updated_at timestamptz not null default now(),
  primary key (iata, hex)
);
create index if not exists arr_watch_updated on public.arr_watch (updated_at);
alter table public.arr_watch enable row level security;
revoke all on public.arr_watch from public, anon, authenticated;

create table if not exists public.rwy_samples (
  id        bigint generated always as identity primary key,
  iata      text not null check (iata ~ '^[A-Z]{3}$'),
  at        timestamptz not null,
  callsign  text check (length(callsign) <= 10),
  flight    text,
  type      text,
  rwy       text not null check (rwy ~ '^[0-9]{2}[LRC]?$'),
  first_km  real,
  first_brg smallint,
  ent120    smallint,
  ent60     smallint,
  ent30     smallint,
  pts       jsonb not null default '[]'::jsonb
);
create index if not exists rwy_samples_iata_at on public.rwy_samples (iata, at);
alter table public.rwy_samples enable row level security;
revoke all on public.rwy_samples from public, anon, authenticated;

-- 運営の分析用：集まった数（空港・滑走路ごと）。だれでも読めるのは数だけ
create or replace function public.rwy_sample_counts() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select iata || ':' || rwy as k, count(*) as n from public.rwy_samples group by 1) q
$$;
revoke all on function public.rwy_sample_counts() from public;
grant execute on function public.rwy_sample_counts() to anon, authenticated;

-- 学習した振り分けの確かめ用：その空港の最近の記録（来た方角と滑走路だけ。便名・位置は返さない）
create or replace function public.rwy_samples_recent(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_array(extract(epoch from at)::bigint, rwy, ent120, ent60, ent30, first_brg) order by at), '[]'::jsonb)
  from public.rwy_samples where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 14), 1), 90))
$$;
revoke all on function public.rwy_samples_recent(text, int) from public;
grant execute on function public.rwy_samples_recent(text, int) to anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('rwy-samples-cleanup', '23 19 * * *', $job$ delete from public.rwy_samples where at < now() - interval '90 days'; delete from public.arr_watch where updated_at < now() - interval '30 minutes' $job$) $q$;
end
$outer$;
