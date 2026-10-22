-- 地上走行の目安を空港ごとの記録から見直す（_shared/flight_watch.ts の TAXI_IN と同じ値）
create or replace function public.taxi_in_min(p_iata text) returns int language sql immutable as $$
  select case p_iata when 'HND' then 10 when 'NRT' then 10 when 'KIX' then 7 when 'ITM' then 5 when 'CTS' then 8 when 'FUK' then 6 when 'OKA' then 6
    when 'NGO' then 3 when 'SDJ' then 4 when 'KMJ' then 4 when 'KOJ' then 4 when 'HIJ' then 3 when 'KMI' then 2 when 'HKD' then 3 when 'AKJ' then 3 when 'UKB' then 4 else 4 end
$$;
