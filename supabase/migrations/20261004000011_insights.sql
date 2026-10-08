-- 運営のための情報集め（個人を特定しない形）
--   使われ方の記録 usage_events：利用者IDは持たず、起動ごとの使い捨ての番号（session）だけ
--   エラーの報告   client_errors：同上。メッセージは300文字まで
--   断られたチェックイン checkin_rejections：checkin 関数が書く。利用者IDも座標も持たず、最寄り空港と距離・誤差の目安だけ
-- 使われ方とエラーは180日で消す（最後の cron の例）。アプリの設定で送らないようにもできる。

create table public.usage_events (
  id         bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  session    text not null,
  platform   text,
  version    text,
  event      text not null,
  prop       text
);
create index usage_events_time on public.usage_events (created_at);
create index usage_events_event on public.usage_events (event, created_at);

create table public.client_errors (
  id         bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  session    text not null,
  platform   text,
  version    text,
  kind       text not null,
  message    text not null,
  detail     jsonb
);
create index client_errors_time on public.client_errors (created_at);

create table public.checkin_rejections (
  id         bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  reason     text not null,
  airport_id integer references public.airports(id),
  dist_km    numeric(6,1),      -- 最寄り空港の基準点からの距離（0.1km単位）
  accuracy_m integer,           -- 誤差（10m単位に丸める）
  queued     boolean not null default false
);
create index checkin_rejections_time on public.checkin_rejections (created_at);

alter table public.usage_events       enable row level security;
alter table public.client_errors      enable row level security;
alter table public.checkin_rejections enable row level security;
revoke all on public.usage_events, public.client_errors, public.checkin_rejections from anon, authenticated;

-- ---------- アプリから送る（ログインしていなくても送れる） ----------
create or replace function public.log_events(p_session text, p_platform text, p_version text, p_events jsonb) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  if p_session !~ '^[a-z0-9]{8,32}$' then raise exception 'bad session'; end if;
  if jsonb_typeof(p_events) <> 'array' or jsonb_array_length(p_events) = 0 or jsonb_array_length(p_events) > 50 then raise exception 'bad events'; end if;
  -- 1つの起動から1日に送れるのは2,000件まで（いたずら防止）
  if (select count(*) from usage_events where session = p_session and created_at > now() - interval '1 day') > 2000 then return 0; end if;
  insert into usage_events (session, platform, version, event, prop)
  select p_session, left(p_platform, 12), left(p_version, 16), e->>'e', left(e->>'p', 60)
    from jsonb_array_elements(p_events) as e
   where (e->>'e') ~ '^[a-z][a-z0-9_:.-]{0,39}$';
  get diagnostics n = row_count;
  return n;
end;
$$;

create or replace function public.log_error(p_session text, p_platform text, p_version text, p_kind text, p_message text, p_detail jsonb) returns void
language plpgsql security definer set search_path = public as $$
begin
  if p_session !~ '^[a-z0-9]{8,32}$' or p_kind !~ '^[a-z_]{1,20}$' then raise exception 'bad input'; end if;
  if (select count(*) from client_errors where session = p_session and created_at > now() - interval '1 day') >= 50 then return; end if;
  insert into client_errors (session, platform, version, kind, message, detail)
  values (p_session, left(p_platform, 12), left(p_version, 16), p_kind, left(coalesce(p_message, ''), 300),
          case when p_detail is null or length(p_detail::text) > 1000 then null else p_detail end);
end;
$$;

revoke all on function public.log_events(text, text, text, jsonb), public.log_error(text, text, text, text, text, jsonb) from public;
grant execute on function public.log_events(text, text, text, jsonb), public.log_error(text, text, text, text, text, jsonb) to anon, authenticated;

-- ---------- 運営画面用（運営者だけ） ----------
create or replace function public.km_between(lat1 double precision, lon1 double precision, lat2 double precision, lon2 double precision) returns double precision
language sql immutable as $$
  select 2 * 6371 * asin(sqrt(power(sin(radians(lat2 - lat1) / 2), 2) + cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians(lon2 - lon1) / 2), 2)))
$$;

-- 利用状況：日ごとの推移と、続けて使っている人の割合
create or replace function public.admin_metrics(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = public, auth as $$
declare d integer := least(greatest(p_days, 7), 120);
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'daily', (select coalesce(jsonb_agg(x order by x.day), '[]'::jsonb) from (
        select g.day::date as day,
               (select count(distinct user_id) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day) as active,
               (select count(*) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day) as checkins,
               (select count(*) from public.flights f where (f.arr_at at time zone 'Asia/Tokyo')::date = g.day) as flights,
               (select count(*) from auth.users u where (u.created_at at time zone 'Asia/Tokyo')::date = g.day) as signups,
               (select count(distinct session) from public.usage_events e where (e.created_at at time zone 'Asia/Tokyo')::date = g.day and e.event = 'open') as opens
          from generate_series((now() at time zone 'Asia/Tokyo')::date - (d - 1), (now() at time zone 'Asia/Tokyo')::date, interval '1 day') as g(day)) x),
    'active7',  (select count(distinct user_id) from public.checkins where created_at > now() - interval '7 days'),
    'active30', (select count(distinct user_id) from public.checkins where created_at > now() - interval '30 days'),
    -- 30日以上前に登録した人のうち、この30日にチェックインした人の割合
    'retention30', (select case when count(*) = 0 then null else round(100.0 * count(*) filter (where exists (
                        select 1 from public.checkins c where c.user_id = u.id and c.created_at > now() - interval '30 days')) / count(*), 1) end
                      from auth.users u where u.created_at < now() - interval '30 days'),
    'top_airports', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select a.name, count(*) as checkins, count(distinct c.user_id) as users from public.checkins c join public.airports a on a.id = c.airport_id
         where c.created_at > now() - make_interval(days => d) group by a.name order by 2 desc limit 15) x),
    'top_routes', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select x1.name || ' ⇄ ' || x2.name as route, count(*) as flights from public.flights f
          join public.airports x1 on x1.id = least(f.from_airport, f.to_airport) join public.airports x2 on x2.id = greatest(f.from_airport, f.to_airport)
         where f.arr_at > now() - make_interval(days => d) group by 1 order by 2 desc limit 15) x),
    'plus', jsonb_build_object(
        'active', (select count(*) from public.subscriptions where status in ('active', 'trialing')),
        'canceled_30', (select count(*) from public.subscriptions where status = 'canceled' and updated_at > now() - interval '30 days')));
end;
$$;

-- 使われ方：イベントの回数、タブ・機能・端末ごと
create or replace function public.admin_usage(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare since timestamptz := now() - make_interval(days => least(greatest(p_days, 1), 180));
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'sessions', (select count(distinct session) from usage_events where created_at > since),
    'events', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select event, prop, count(*) as n, count(distinct session) as sessions from usage_events
         where created_at > since group by 1, 2 order by 3 desc limit 60) x),
    'platforms', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select coalesce(platform, '不明') as platform, count(distinct session) as sessions from usage_events where created_at > since group by 1 order by 2 desc) x));
end;
$$;

-- エラー：多いメッセージと、チェックインが断られた理由
create or replace function public.admin_errors(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare since timestamptz := now() - make_interval(days => least(greatest(p_days, 1), 180));
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'errors', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select kind, message, count(*) as n, count(distinct session) as sessions, max(created_at) as last, max(version) as version
          from client_errors where created_at > since group by 1, 2 order by 3 desc limit 40) x),
    'rejections', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select reason, count(*) as n, count(*) filter (where queued) as queued from checkin_rejections where created_at > since group by 1 order by 2 desc) x));
end;
$$;

-- 判定ルールの見直し：空港ごとの、チェックイン地点の距離の分布と誤差、範囲外で惜しくも断られた回数
create or replace function public.admin_quality(p_days integer default 90) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare since timestamptz := now() - make_interval(days => least(greatest(p_days, 7), 365));
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return (select coalesce(jsonb_agg(x order by x.near_miss desc, x.checkins desc), '[]'::jsonb) from (
    select a.id, a.name, a.radius_m,
           count(c.id) as checkins,
           round(percentile_cont(0.5) within group (order by km_between(c.lat, c.lon, a.lat, a.lon))::numeric * 1000) as p50_m,
           round(percentile_cont(0.9) within group (order by km_between(c.lat, c.lon, a.lat, a.lon))::numeric * 1000) as p90_m,
           round(max(km_between(c.lat, c.lon, a.lat, a.lon))::numeric * 1000) as max_m,
           round(percentile_cont(0.5) within group (order by c.accuracy_m)::numeric) as acc_p50_m,
           round(100.0 * count(c.terminal_id) / nullif(count(c.id), 0), 1) as terminal_pct,
           (select count(*) from checkin_rejections r where r.airport_id = a.id and r.reason = 'out_of_range'
               and r.created_at > since and r.dist_km * 1000 <= a.radius_m + 1500) as near_miss
      from airports a
      left join checkins c on c.airport_id = a.id and c.created_at > since
     where a.game_target
     group by a.id
    having count(c.id) > 0 or (select count(*) from checkin_rejections r where r.airport_id = a.id and r.created_at > since) > 0
  ) x);
end;
$$;

revoke all on function public.admin_metrics(integer), public.admin_usage(integer), public.admin_errors(integer), public.admin_quality(integer) from public, anon;
grant execute on function public.admin_metrics(integer), public.admin_usage(integer), public.admin_errors(integer), public.admin_quality(integer) to authenticated;

-- 使われ方とエラーを180日で消す
create or replace function public.insights_cleanup() returns void
language sql security definer set search_path = public as $$
  delete from usage_events where created_at < now() - interval '180 days';
  delete from client_errors where created_at < now() - interval '180 days';
  delete from checkin_rejections where created_at < now() - interval '365 days';
$$;
revoke all on function public.insights_cleanup() from public, anon, authenticated;
-- 定期実行の例（pg_cron を有効にしてから）：
-- select cron.schedule('insights-cleanup', '0 19 * * *', $$ select public.insights_cleanup() $$);
