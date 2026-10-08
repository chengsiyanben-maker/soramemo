-- 運営画面の集計の起点（表示だけを変える。データは消さない）
-- 2026-10-09 05:47 JST（= 2026-10-08 20:47 UTC）から数えなおす。
-- 起点より前の行は残る。集計の関数だけが、起点より前を数えないようにする。
-- 元に戻すには、ops.flags の 'stats_since' を過去の日時に変えるか、行を消す。

insert into ops.flags (key, value) values ('stats_since', to_jsonb('2026-10-08T20:47:00+00:00'::text))
  on conflict (key) do update set value = excluded.value, updated_at = now();

create or replace function ops.stats_since() returns timestamptz
language sql stable security definer set search_path = ops as $$
  select coalesce((ops.flag('stats_since') #>> '{}')::timestamptz, '-infinity'::timestamptz)
$$;

-- 概要（登録者数・今日のチェックイン・全チェックイン・要確認）
create or replace function public.admin_stats() returns jsonb
language plpgsql stable security definer set search_path = ops, public, auth as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'users', (select count(*) from auth.users where created_at >= ops.stats_since()),
    'checkins_today', (select count(*) from public.checkins where created_at >= greatest(date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo', ops.stats_since())),
    'checkins_total', (select count(*) from public.checkins where created_at >= ops.stats_since()),
    'flagged', (select count(*) from public.checkins where flags <> '{}' and created_at >= ops.stats_since()),
    'plus', (select count(*) from public.subscriptions where status in ('active', 'trialing')),
    'verified', (select count(*) from public.flights where status = 'verified'),
    'flights', (select count(*) from public.flights));
end;
$$;

-- 使われ方（日別・直近の集計・人気の空港と路線）
create or replace function public.admin_metrics(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public, auth as $$
declare d integer := least(greatest(p_days, 7), 120);
        s timestamptz := ops.stats_since();
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'daily', (select coalesce(jsonb_agg(x order by x.day), '[]'::jsonb) from (
        select g.day::date as day,
               (select count(distinct user_id) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day and c.created_at >= s) as active,
               (select count(*) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day and c.created_at >= s) as checkins,
               (select count(*) from public.flights f where (f.arr_at at time zone 'Asia/Tokyo')::date = g.day) as flights,
               (select count(*) from auth.users u where (u.created_at at time zone 'Asia/Tokyo')::date = g.day and u.created_at >= s) as signups,
               (select count(distinct session) from ops.usage_events e where (e.created_at at time zone 'Asia/Tokyo')::date = g.day and e.event = 'open' and e.created_at >= s) as opens
          from generate_series((now() at time zone 'Asia/Tokyo')::date - (d - 1), (now() at time zone 'Asia/Tokyo')::date, interval '1 day') as g(day)) x),
    'active7',  (select count(distinct user_id) from public.checkins where created_at > greatest(now() - interval '7 days', s)),
    'active30', (select count(distinct user_id) from public.checkins where created_at > greatest(now() - interval '30 days', s)),
    -- 30日以上前に登録した人のうち、この30日にチェックインした人の割合（起点以降に登録した人だけ）
    'retention30', (select case when count(*) = 0 then null else round(100.0 * count(*) filter (where exists (
                        select 1 from public.checkins c where c.user_id = u.id and c.created_at > greatest(now() - interval '30 days', s))) / count(*), 1) end
                      from auth.users u where u.created_at < now() - interval '30 days' and u.created_at >= s),
    'top_airports', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select a.name, count(*) as checkins, count(distinct c.user_id) as users from public.checkins c join public.airports a on a.id = c.airport_id
         where c.created_at > greatest(now() - make_interval(days => d), s) group by a.name order by 2 desc limit 15) x),
    'top_routes', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select x1.name || ' ⇄ ' || x2.name as route, count(*) as flights from public.flights f
          join public.airports x1 on x1.id = least(f.from_airport, f.to_airport) join public.airports x2 on x2.id = greatest(f.from_airport, f.to_airport)
         where f.arr_at > now() - make_interval(days => d) group by 1 order by 2 desc limit 15) x),
    'plus', jsonb_build_object(
        'active', (select count(*) from public.subscriptions where status in ('active', 'trialing')),
        'canceled_30', (select count(*) from public.subscriptions where status = 'canceled' and updated_at > greatest(now() - interval '30 days', s))));
end;
$$;

-- 使われ方（操作の集計）
create or replace function public.admin_usage(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
declare since timestamptz := greatest(now() - make_interval(days => least(greatest(p_days, 1), 180)), ops.stats_since());
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'sessions', (select count(distinct session) from ops.usage_events where created_at > since),
    'events', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select event, prop, count(*) as n, count(distinct session) as sessions from ops.usage_events
         where created_at > since group by 1, 2 order by 3 desc limit 60) x),
    'platforms', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select coalesce(platform, '不明') as platform, count(distinct session) as sessions from ops.usage_events where created_at > since group by 1 order by 2 desc) x));
end;
$$;

-- エラーと、チェックイン拒否の集計
create or replace function public.admin_errors(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
declare since timestamptz := greatest(now() - make_interval(days => least(greatest(p_days, 1), 180)), ops.stats_since());
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'errors', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select kind, message, count(*) as n, count(distinct session) as sessions, max(created_at) as last, max(version) as version
          from ops.client_errors where created_at > since group by 1, 2 order by 3 desc limit 40) x),
    'rejections', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select reason, count(*) as n, count(*) filter (where queued) as queued from ops.checkin_rejections where created_at > since group by 1 order by 2 desc) x));
end;
$$;

-- 空港ごとの精度（起点以降のチェックインだけ）
create or replace function public.admin_quality(p_days integer default 90) returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
declare since timestamptz := greatest(now() - make_interval(days => least(greatest(p_days, 7), 365)), ops.stats_since());
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
           (select count(*) from ops.checkin_rejections r where r.airport_id = a.id and r.reason = 'out_of_range'
               and r.created_at > since and r.dist_km * 1000 <= a.radius_m + 1500) as near_miss
      from public.airports a
      left join public.checkins c on c.airport_id = a.id and c.created_at > since
     where a.game_target
     group by a.id
     having count(c.id) > 0 or (select count(*) from ops.checkin_rejections r where r.airport_id = a.id and r.created_at > since) > 0
  ) x);
end;
$$;
