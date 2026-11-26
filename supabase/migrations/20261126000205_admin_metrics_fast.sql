-- 定期の手入れ 11/26 の4回目：admin_metrics（管理の画面の「使われ方」）の日別の数え方を速くする
--   前（20261009000018）：日ごと（最大120日）に checkins・flights・auth.users・ops.usage_events を
--     「(created_at at time zone 'Asia/Tokyo')::date = その日」で数えていたので、索引が効かず、
--     1回呼ぶと 120日 × 5 回、表をまるごと読んでいた（記録が増えるほど遅くなる）
--   後：見る期間（日本時間の d0 の0時〜今日の次の0時）で1回だけ読み、日ごとにまとめてから日の並びにつなぐ
--     ops.usage_events は created_at の索引（usage_events_time・usage_events_event）で範囲を引ける
--   返す形・数え方（起点 stats_since・日本時間の日付・0 の日も出す）は前と同じ。日別以外の項目は1文字も変えない
--   表・RLS・権限は変えない（create or replace なので権限はそのまま：authenticated だけ・中で is_admin）
--   影響：チェックイン・経営とも関係しない（管理者の画面だけ）

create or replace function public.admin_metrics(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public, auth as $$
declare d integer := least(greatest(p_days, 7), 120);
        s timestamptz := ops.stats_since();
        d1 date := (now() at time zone 'Asia/Tokyo')::date;
        d0 date := (now() at time zone 'Asia/Tokyo')::date - (least(greatest(p_days, 7), 120) - 1);
        t0 timestamptz := (((now() at time zone 'Asia/Tokyo')::date - (least(greatest(p_days, 7), 120) - 1))::timestamp at time zone 'Asia/Tokyo');
        t1 timestamptz := (((now() at time zone 'Asia/Tokyo')::date + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'daily', (select coalesce(jsonb_agg(x order by x.day), '[]'::jsonb) from (
        select g.day::date as day,
               coalesce(ck.active, 0) as active,
               coalesce(ck.checkins, 0) as checkins,
               coalesce(fl.flights, 0) as flights,
               coalesce(su.signups, 0) as signups,
               coalesce(op.opens, 0) as opens
          from generate_series(d0, d1, interval '1 day') as g(day)
          left join (select (c.created_at at time zone 'Asia/Tokyo')::date as day, count(distinct c.user_id) as active, count(*) as checkins
                       from public.checkins c where c.created_at >= greatest(t0, s) and c.created_at < t1 group by 1) ck on ck.day = g.day::date
          left join (select (f.arr_at at time zone 'Asia/Tokyo')::date as day, count(*) as flights
                       from public.flights f where f.arr_at >= t0 and f.arr_at < t1 group by 1) fl on fl.day = g.day::date
          left join (select (u.created_at at time zone 'Asia/Tokyo')::date as day, count(*) as signups
                       from auth.users u where u.created_at >= greatest(t0, s) and u.created_at < t1 group by 1) su on su.day = g.day::date
          left join (select (e.created_at at time zone 'Asia/Tokyo')::date as day, count(distinct e.session) as opens
                       from ops.usage_events e where e.event = 'open' and e.created_at >= greatest(t0, s) and e.created_at < t1 group by 1) op on op.day = g.day::date
       ) x),
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
