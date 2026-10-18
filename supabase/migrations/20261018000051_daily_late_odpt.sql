-- 空港ごとの1日のまとめの「15分以上の遅れ」は、航空会社の運航情報（実際の時刻）がある便だけで数える。
-- 機体の位置からの推定は、出発が「離陸の時刻」（搭乗口を離れる定刻より地上走行のぶん遅い）、到着が「着陸の時刻」になり、
-- 遅れを多めに・少なめに見てしまうため
create or replace function public.archive_airport_daily(p_day date) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  delete from public.airport_daily where day = p_day;
  with u as (
    select arr as iata, 'arr' as dir, case when ata_src = 'odpt' then arr_delay end as d, cancelled, diverted_to is not null as div
    from public.flight_history where svc_date = p_day
    union all
    select dep, 'dep', case when atd_src = 'odpt' then dep_delay end, cancelled, false from public.flight_history where svc_date = p_day
  ), o as (
    select iata, jsonb_object_agg(mode, cnt * 5) as modes, max(wmax) as max_wind from (
      select iata, coalesce(obs_mode, est_mode) as mode, count(*) as cnt, max(wspd) as wmax
      from public.ops_log where (at at time zone 'Asia/Tokyo')::date = p_day group by 1, 2) x group by iata
  )
  insert into public.airport_daily (day, iata, flights, arr, dep, late, cancelled, diverted, avg_delay, modes, max_wind)
  select p_day, u.iata, count(*), count(*) filter (where dir = 'arr'), count(*) filter (where dir = 'dep'),
         count(*) filter (where not cancelled and d >= 15), count(*) filter (where cancelled), count(*) filter (where div),
         round(avg(d) filter (where not cancelled and d >= 15), 1), o.modes, o.max_wind
  from u left join o on o.iata = u.iata
  group by u.iata, o.modes, o.max_wind;
  get diagnostics n = row_count;
  return n;
end
$$;
revoke all on function public.archive_airport_daily(date) from public, anon, authenticated;
