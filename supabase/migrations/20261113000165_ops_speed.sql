-- 運用を開いたときの速さ（11/13 4時 PM の指示「全体の見回りの直し」・本人「バグや反応しないところを直し、処理速度を早くして」）
--   見回り（kaizen/sweep-1113）で、運用を開くと airport_board 3.80秒・airport_ontime 3.38秒（アメリカから測った）。
-- 1. flight_schedule に「出発の空港・時刻」「到着の空港・時刻」の索引。airport_board と spot_departures は
--    「この空港の8日分」を引くのに、今は時刻の索引しかなく、全空港の8日分（約2万便）を読んでから空港で絞っていた。
--    時刻表は14日で消える表なので、索引は小さい（2つで数 MB 以下）
-- 2. airport_board の1時間ごとの数を、1回読んでまとめて数える形に（前は24時間×4つで96回読み直していた）。返す形・値は前と同じ
-- 3. flight_history に「出発の空港・運航日」の索引。airport_ontime（定時の見方。この空港を出た30日分）は、
--    今は (dep, arr, svc_date) の索引で「この空港を出た全部の日」を読んでから日で絞っていた。記録は消さない表なので年々重くなる
-- 表・列・RLS・権限は変えない（関数は同じ名前・同じ引数・同じ権限で置き換える）。記録は消さない
-- 影響：チェックイン（運用の案内板・定時が速くなるだけ。返す形は同じ）。エアライン経営は使わない
-- 索引は concurrently を使わない（移行は1つのトランザクションで流れるため）。時刻表は小さいので作るのは一瞬。
--   flight_history は大きくなっているかもしれないので、作るあいだ書き込みが待たされる（毎晩の記録の数秒。lock_timeout を付けて、待ちすぎたら移行ごと止める）
set lock_timeout = '10s';

create index if not exists flight_schedule_dep_std on public.flight_schedule (dep, std);
create index if not exists flight_schedule_arr_std on public.flight_schedule (arr, std);
create index if not exists flight_history_dep_day on public.flight_history (dep, svc_date);

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

reset lock_timeout;
