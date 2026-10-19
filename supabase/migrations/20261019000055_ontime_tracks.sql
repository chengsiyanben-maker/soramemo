-- 路線・空港ごとの定時率と、空港の航跡（毎日の記録から）
--   定時：出発の定刻から15分未満に出発した便（国土交通省の定時運航率と同じ考え方）。
--         航空会社の運航情報の実際の出発時刻（atd_src = 'odpt'）がある便だけで数える。機体の位置からの推定（離陸の時刻）は数えない。
--   欠航は別に数え、定時率の分母には入れない。
create or replace function public.route_ontime(p_dep text, p_arr text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today, least(greatest(coalesce(p_days, 30), 7), 365) as n),
  h as (
    select h.* from public.flight_history h, d
    where h.dep = p_dep and h.arr = p_arr and h.svc_date >= d.today - d.n and h.svc_date < d.today
  )
  select jsonb_build_object('dep', p_dep, 'arr', p_arr, 'days', (select n from d),
    'from', (select min(svc_date) from h), 'to', (select max(svc_date) from h),
    'flights', count(*), 'cancelled', count(*) filter (where cancelled),
    'measured', count(*) filter (where not cancelled and atd_src = 'odpt'),
    'ontime', count(*) filter (where not cancelled and atd_src = 'odpt' and dep_delay < 15),
    'avg_late', round(avg(dep_delay) filter (where not cancelled and atd_src = 'odpt' and dep_delay >= 15)))
  from h
$$;
revoke all on function public.route_ontime(text, text, int) from public;
grant execute on function public.route_ontime(text, text, int) to anon, authenticated;

-- 空港から出る路線ごとの定時率（数えられた便が5便以上の路線を、便の多い順に12路線まで）と、空港全体の出発の定時率
create or replace function public.airport_ontime(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today, least(greatest(coalesce(p_days, 30), 7), 365) as n),
  h as (
    select h.arr, h.cancelled, h.svc_date, (not h.cancelled and h.atd_src = 'odpt') as m, (not h.cancelled and h.atd_src = 'odpt' and h.dep_delay < 15) as ok
    from public.flight_history h, d
    where h.dep = p_iata and h.svc_date >= d.today - d.n and h.svc_date < d.today
  ), r as (
    select arr, count(*) as flights, count(*) filter (where m) as measured, count(*) filter (where ok) as ontime, count(*) filter (where cancelled) as cancelled
    from h group by arr
  )
  select jsonb_build_object('iata', p_iata, 'days', (select n from d), 'from', (select min(svc_date) from h), 'to', (select max(svc_date) from h),
    'flights', (select count(*) from h), 'measured', (select count(*) filter (where m) from h), 'ontime', (select count(*) filter (where ok) from h),
    'cancelled', (select count(*) filter (where cancelled) from h),
    'routes', coalesce((select jsonb_agg(jsonb_build_object('arr', arr, 'flights', flights, 'measured', measured, 'ontime', ontime, 'cancelled', cancelled) order by flights desc, arr)
                        from (select * from r where measured >= 5 order by flights desc, arr limit 12) q), '[]'::jsonb))
$$;
revoke all on function public.airport_ontime(text, int) from public;
grant execute on function public.airport_ontime(text, int) to anon, authenticated;

-- 空港の航跡アート用：その日にその空港を出た・着いた便の航跡（上昇・降下中の部分。便名は返さない）。
-- 前の日から30日前までの日だけ（航跡は31日で消える）。1日2000便まで
create or replace function public.airport_tracks(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today)
  select coalesce(jsonb_agg(jsonb_build_object('d', case when h.dep = p_iata then 1 else 0 end, 'p', t.pts, 'a', t.alts)), '[]'::jsonb)
  from d, (
    select t.pts, t.alts, t.svc_date, t.flight, t.dep from public.flight_tracks t, d
    where t.svc_date = p_day and p_day < d.today and p_day >= d.today - 30
    order by t.flight limit 2000
  ) t
  join public.flight_history h on h.svc_date = t.svc_date and h.flight = t.flight and h.dep = t.dep
  where h.dep = p_iata or h.arr = p_iata
$$;
revoke all on function public.airport_tracks(text, date) from public;
grant execute on function public.airport_tracks(text, date) to anon, authenticated;

-- 利用者のフライトに航跡を付ける（daily-archive から。照合で OpenSky の航跡が取れなかった便だけ）：
-- その日（日本時間）に出発し、便名（0を取ってくらべる）と出発空港が毎日の記録と一致するフライト
create or replace function public.archive_user_flights(p_day date) returns table (id bigint, flight text, dep text)
language sql stable security definer set search_path = public as $$
  select f.id, public.flight_no_norm(f.flight_no), a.iata
  from public.flights f join public.airports a on a.id = f.from_airport
  where f.track is null and f.flight_no is not null and a.iata ~ '^[A-Z]{3}$'
    and f.dep_at >= (p_day::timestamp at time zone 'Asia/Tokyo')
    and f.dep_at < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')
$$;
revoke all on function public.archive_user_flights(date) from public, anon, authenticated;
