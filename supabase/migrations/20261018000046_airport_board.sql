-- 運用タブの「これから着く便・出る便」と「今日の遅れ・欠航」（JAL・ANA グループの時刻表と運航情報から）
--   next_arr / next_dep：今から20分前〜3時間後の便を、実際・見込み・推定の早い順に6便まで（欠航は除く）
--   hours：今日（日本時間）の1時間ごとの便の数、15分以上の遅れの数、欠航の数と、
--          前の7日間の同じ時間の「遅れ＋欠航」の平均（くらべる目安）
--   遅れは航空会社の運航情報（実際の時刻、なければ見込み）だけで数える。機体の位置からの推定は数えない。
create or replace function public.airport_board(p_iata text) returns jsonb
language sql stable security definer set search_path = public as $$
  with s as (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.etd, f.eta, f.atd, f.ata, f.aircraft, f.dep_status, f.arr_status,
      case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end as atd_inf,
      case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end as ata_inf,
      case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end as eta_inf,
      coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled
    from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
    where (f.arr = p_iata or f.dep = p_iata) and f.std > now() - interval '8 days 6 hours' and f.std < now() + interval '6 hours'
  ), u as (
    -- この空港から見た1便（到着なら到着の時刻、出発なら出発の時刻）
    select case when arr = p_iata then sta else std end as t_sched,
           case when arr = p_iata then coalesce(ata, eta) else coalesce(atd, etd) end as t_off,
           cancelled
    from s
  ), d as (
    select (t_sched at time zone 'Asia/Tokyo')::date as day, extract(hour from t_sched at time zone 'Asia/Tokyo')::int as h,
           not cancelled and t_off is not null and t_off - t_sched >= interval '15 minutes' as late, cancelled
    from u
  ), today as (select (now() at time zone 'Asia/Tokyo')::date as day)
  select jsonb_build_object(
    'iata', p_iata, 'now', now(),
    'next_arr', coalesce((select jsonb_agg(x order by x ->> 't') from (
      select jsonb_build_object('flight', flight, 'other', dep, 'sched', sta, 'est', eta, 'actual', ata, 'inferred', ata_inf, 'predicted', eta_inf,
               'aircraft', aircraft, 't', coalesce(ata, ata_inf, eta, eta_inf, sta)) as x
      from s where arr = p_iata and not cancelled
        and coalesce(ata, ata_inf, eta, eta_inf, sta) between now() - interval '20 minutes' and now() + interval '3 hours'
        and sta > now() - interval '6 hours'
      order by coalesce(ata, ata_inf, eta, eta_inf, sta) limit 6) q), '[]'::jsonb),
    'next_dep', coalesce((select jsonb_agg(x order by x ->> 't') from (
      select jsonb_build_object('flight', flight, 'other', arr, 'sched', std, 'est', etd, 'actual', atd, 'inferred', atd_inf,
               'aircraft', aircraft, 't', coalesce(atd, atd_inf, etd, std)) as x
      from s where dep = p_iata and not cancelled
        and coalesce(atd, atd_inf, etd, std) between now() - interval '20 minutes' and now() + interval '3 hours'
        and std > now() - interval '6 hours'
      order by coalesce(atd, atd_inf, etd, std) limit 6) q), '[]'::jsonb),
    'hours', (select jsonb_agg(jsonb_build_object('h', g.h,
        'flights', (select count(*) from d, today where d.day = today.day and d.h = g.h),
        'late', (select count(*) from d, today where d.day = today.day and d.h = g.h and d.late),
        'cancel', (select count(*) from d, today where d.day = today.day and d.h = g.h and d.cancelled),
        'ref', (select round(count(*) filter (where d.late or d.cancelled) / 7.0, 1) from d, today
                where d.day between today.day - 7 and today.day - 1 and d.h = g.h)) order by g.h)
      from generate_series(0, 23) as g(h))
  )
$$;
revoke all on function public.airport_board(text) from public;
grant execute on function public.airport_board(text) to anon, authenticated;
