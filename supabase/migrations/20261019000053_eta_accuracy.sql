-- 到着予想の当たり具合（運営者の確認用。便ごとではなく、機種ごとのまとめだけを返す）
--   到着の30分前ごろの予想（eta30）と、実際の到着（航空会社の運航情報＝搭乗口に着いた時刻 ／ 機体の位置＝着陸の時刻）の差（分）
create or replace function public.eta_accuracy(p_days int default 7) returns jsonb
language sql stable security definer set search_path = public as $$
  with x as (
    select coalesce(type, aircraft, '?') as type, ata_src as src,
           extract(epoch from (eta30 - ata)) / 60 as diff
    from public.flight_history
    where svc_date >= (now() at time zone 'Asia/Tokyo')::date - least(greatest(p_days, 1), 60)
      and eta30 is not null and ata is not null and not cancelled and diverted_to is null
  )
  select jsonb_build_object('days', least(greatest(p_days, 1), 60), 'by_type', coalesce((
    select jsonb_agg(jsonb_build_object('type', type, 'src', src, 'n', n, 'mean', mean, 'median', med, 'p90_abs', p90) order by n desc)
    from (
      select type, src, count(*) as n, round(avg(diff)::numeric, 1) as mean,
             round((percentile_cont(0.5) within group (order by diff))::numeric, 1) as med,
             round((percentile_cont(0.9) within group (order by abs(diff)))::numeric, 1) as p90
      from x group by type, src having count(*) >= 3
    ) t), '[]'::jsonb))
$$;
revoke all on function public.eta_accuracy(int) from public;
grant execute on function public.eta_accuracy(int) to anon, authenticated;
