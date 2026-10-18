-- 運用タブの「昨日の〇〇」：前の日の空港のまとめ（airport_daily）と、その前の7日の平均（くらべる目安）
create or replace function public.airport_yesterday(p_iata text) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date - 1 as y)
  select case when a.iata is null then null else jsonb_build_object(
    'day', a.day, 'flights', a.flights, 'arr', a.arr, 'dep', a.dep, 'late', a.late, 'cancelled', a.cancelled, 'diverted', a.diverted,
    'avg_delay', a.avg_delay, 'modes', a.modes, 'max_wind', a.max_wind,
    'ref', (select jsonb_build_object('days', count(*), 'late', round(avg(late), 1), 'cancelled', round(avg(cancelled), 1), 'flights', round(avg(flights)))
            from public.airport_daily r where r.iata = p_iata and r.day between d.y - 7 and d.y - 1)) end
  from d left join public.airport_daily a on a.iata = p_iata and a.day = d.y
$$;
revoke all on function public.airport_yesterday(text) from public;
grant execute on function public.airport_yesterday(text) to anon, authenticated;
