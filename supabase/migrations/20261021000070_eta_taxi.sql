-- 到着予想の当たり具合：空港ごとのまとめ（by_arr）を足し、運航情報（搭乗口に着いた時刻）とくらべるときは地上走行の目安を足した値でもくらべる
--   flight_history.eta30 は着陸の予想（_shared/flight_watch.ts の predictEta）。taxi_in_min は _shared/flight_watch.ts の TAXI_IN と同じ値
create or replace function public.taxi_in_min(p_iata text) returns int language sql immutable as $$
  select case p_iata when 'HND' then 9 when 'NRT' then 10 when 'KIX' then 7 when 'ITM' then 6 when 'CTS' then 7 when 'FUK' then 6 when 'OKA' then 7 when 'NGO' then 6 else 4 end
$$;
create or replace function public.eta_accuracy(p_days int default 7) returns jsonb
language sql stable security definer set search_path = public as $$
  with x as (
    select coalesce(type, aircraft, '?') as type, arr, ata_src as src,
           extract(epoch from (eta30 - ata)) / 60 as diff,
           extract(epoch from (eta30 - ata)) / 60 + case when ata_src = 'odpt' then public.taxi_in_min(arr) else 0 end as diff_adj
    from public.flight_history
    where svc_date >= (now() at time zone 'Asia/Tokyo')::date - least(greatest(p_days, 1), 60)
      and eta30 is not null and ata is not null and not cancelled and diverted_to is null
  )
  select jsonb_build_object('days', least(greatest(p_days, 1), 60),
    'by_type', coalesce((
      select jsonb_agg(jsonb_build_object('type', type, 'src', src, 'n', n, 'mean', mean, 'median', med, 'p90_abs', p90, 'median_adj', med_adj) order by n desc)
      from (
        select type, src, count(*) as n, round(avg(diff)::numeric, 1) as mean,
               round((percentile_cont(0.5) within group (order by diff))::numeric, 1) as med,
               round((percentile_cont(0.9) within group (order by abs(diff)))::numeric, 1) as p90,
               round((percentile_cont(0.5) within group (order by diff_adj))::numeric, 1) as med_adj
        from x group by type, src having count(*) >= 3
      ) t), '[]'::jsonb),
    -- 空港ごと：運航情報（搭乗口）と機体の位置（着陸）の差の中央値の差が、その空港の地上走行の目安になる
    'by_arr', coalesce((
      select jsonb_agg(jsonb_build_object('arr', arr, 'src', src, 'n', n, 'median', med, 'median_adj', med_adj, 'taxi', public.taxi_in_min(arr)) order by arr, src)
      from (
        select arr, src, count(*) as n,
               round((percentile_cont(0.5) within group (order by diff))::numeric, 1) as med,
               round((percentile_cont(0.5) within group (order by diff_adj))::numeric, 1) as med_adj
        from x group by arr, src having count(*) >= 5
      ) a), '[]'::jsonb))
$$;
revoke all on function public.eta_accuracy(int) from public;
grant execute on function public.eta_accuracy(int) to anon, authenticated;
