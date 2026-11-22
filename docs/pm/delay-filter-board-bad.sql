-- 【案・移行ではない】運用の「遅れ」の専用ページの絞り込み（checkin/delay-filter）のために、airport_board に 'bad' を足す案
--   チェックイン担当が書いた下書き。移行にするか・形を変えるかはデータ担当が決める（表・列・RLS・権限は変えない。関数を同じ名前・引数・権限で置き換えるだけ）
--   元：supabase/migrations/20261113000165_ops_speed.sql の airport_board。変えたのは u と d に便の列を足したことと、返す形の 'bad' だけ
--   画面は 'bad' がないあいだ前の時間ごとの札のまま動くので、どちらが先に入っても壊れない
--   1便の形：{dir:'dep'|'arr', flight, other, sched, est, actual, late(分・欠航は null), cancelled, intl, aircraft}
create or replace function public.airport_board(p_iata text, p_kind text default 'all') returns jsonb
language sql stable security definer set search_path = public as $$
  with s as (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.etd, f.eta, f.atd, f.ata, f.aircraft, f.dep_status, f.arr_status,
      case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end as atd_inf,
      case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end as ata_inf,
      case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end as eta_inf,
      coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled,
      not exists (select 1 from public.airports a where a.iata = case when f.dep = p_iata then f.arr else f.dep end) as intl
    from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
    where (f.arr = p_iata or f.dep = p_iata) and f.std > now() - interval '8 days 6 hours' and f.std < now() + interval '6 hours'
  ), tx as (select public.taxi_out_min(p_iata) as m),
  dp as (
    -- 離陸の時刻：機体の位置で見つけた離陸、なければ出発（実際・見込み・定刻）＋地上走行
    select s.*, coalesce(atd_inf, coalesce(atd, etd, std) + make_interval(secs => tx.m * 60)) as tko, atd_inf is not null as tko_actual, tx.m as taxi
    from s, tx where dep = p_iata
  ), u as (
    -- この空港から見た1便（到着なら到着の時刻、出発なら出発の時刻）
    select flight, case when arr = p_iata then 'arr' else 'dep' end as dir, case when arr = p_iata then dep else arr end as other,
           case when arr = p_iata then eta else etd end as t_est, case when arr = p_iata then ata else atd end as t_act, intl, aircraft,
           case when arr = p_iata then sta else std end as t_sched,
           case when arr = p_iata then coalesce(ata, eta) else coalesce(atd, etd) end as t_off,
           cancelled
    from s
  ), d as (
    select (t_sched at time zone 'Asia/Tokyo')::date as day, extract(hour from t_sched at time zone 'Asia/Tokyo')::int as h,
           not cancelled and t_off is not null and t_off - t_sched >= interval '15 minutes' as late, cancelled, flight, dir, other, t_sched, t_est, t_act, intl, aircraft
    from u
  ), today as (select (now() at time zone 'Asia/Tokyo')::date as day)
  select jsonb_build_object(
    'iata', p_iata, 'now', now(),
    -- 足すもの（11/22 チェックイン担当からの依頼）：今日（日本時間）の15分以上の遅れと欠航の便。'hours' の late・cancel と同じ数え方なので、合計は hours と合う
    'bad', coalesce((select jsonb_agg(jsonb_build_object('dir', d.dir, 'flight', d.flight, 'other', d.other, 'sched', d.t_sched, 'est', d.t_est, 'actual', d.t_act,
               'late', case when d.cancelled then null else round(extract(epoch from (coalesce(d.t_act, d.t_est) - d.t_sched)) / 60) end,
               'cancelled', d.cancelled, 'intl', d.intl, 'aircraft', d.aircraft) order by d.t_sched)
      from d, today where d.day = today.day and (d.late or d.cancelled)), '[]'::jsonb),
    'next_arr', coalesce((select jsonb_agg(x order by x ->> 't') from (
      select jsonb_build_object('flight', flight, 'other', dep, 'sched', sta, 'est', eta, 'actual', ata, 'inferred', ata_inf, 'predicted', eta_inf,
               'aircraft', aircraft, 'intl', intl, 't', coalesce(ata, ata_inf, eta, eta_inf, sta)) as x
      from s where arr = p_iata and not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
        and coalesce(ata, ata_inf, eta, eta_inf, sta) between now() - interval '20 minutes' and now() + interval '3 hours'
        and sta > now() - interval '6 hours'
      order by coalesce(ata, ata_inf, eta, eta_inf, sta) limit 6) q), '[]'::jsonb),
    'next_dep', coalesce((select jsonb_agg(x order by x ->> 'takeoff') from (
      select jsonb_build_object('flight', flight, 'other', arr, 'sched', std, 'est', etd, 'actual', atd, 'inferred', atd_inf,
               'aircraft', aircraft, 'intl', intl, 't', coalesce(atd, atd_inf, etd, std),
               'takeoff', tko, 'takeoff_src', case when tko_actual then 'actual' else 'calc' end, 'taxi', round(taxi::numeric)) as x
      from dp where not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
        and tko between now() - interval '20 minutes' and now() + interval '3 hours'
        and std > now() - interval '6 hours'
      order by tko limit 6) q), '[]'::jsonb),
    -- 1時間ごとの数：前は 24時間 × 4つの数を、それぞれ便の表 d を読み直して数えていた（96回）。1回読んでまとめて数える（結果は同じ）
    'hours', (select jsonb_agg(jsonb_build_object('h', g.h, 'flights', coalesce(c.flights, 0), 'late', coalesce(c.late, 0), 'cancel', coalesce(c.cancel, 0),
        'ref', round(coalesce(c.bad7, 0) / 7.0, 1)) order by g.h)
      from generate_series(0, 23) as g(h)
      left join (select d.h,
          count(*) filter (where d.day = today.day) as flights,
          count(*) filter (where d.day = today.day and d.late) as late,
          count(*) filter (where d.day = today.day and d.cancelled) as cancel,
          count(*) filter (where d.day between today.day - 7 and today.day - 1 and (d.late or d.cancelled)) as bad7
        from d, today group by d.h) c on c.h = g.h)
  )
$$;
revoke all on function public.airport_board(text, text) from public;
grant execute on function public.airport_board(text, text) to anon, authenticated;
