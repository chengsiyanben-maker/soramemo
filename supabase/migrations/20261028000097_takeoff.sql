-- 離陸の時刻（撮る人の一覧・離陸の知らせ）：出発（搭乗口を離れる時刻）に、空港ごとの地上走行の時間（出発→離陸）を足す
--   ・eta_calib.taxi_out：出発から離陸までの分。毎晩、この14日の便のうち、運航情報の出発の時刻と、機体の位置で見つけた離陸の時刻の
--     両方がある便（10便以上）の差の中央値で決め直す（2〜45分の便だけ）。少なければ前の値のまま
--   ・airport_board の next_dep に takeoff（離陸の時刻）・takeoff_src（actual＝機体の位置で見つけた / calc＝出発＋地上走行）・taxi（分）を足す。
--     これまでの 't'（出発の時刻）はそのまま。並びと「これから」の判断は離陸の時刻で（出発してまだ離陸していない便も出る）
--   ・撮影の知らせに 'dep'（離陸も知らせる）を足す
-- 表の守りは今のまま：eta_calib・push_subs は RLS を有効にしたうえで、public・anon・authenticated からはすべて取り上げている
alter table public.eta_calib add column if not exists taxi_out real check (taxi_out between 0 and 40);
alter table public.eta_calib add column if not exists n_out int not null default 0;
alter table public.eta_calib enable row level security;
revoke all on public.eta_calib from public, anon, authenticated;
-- はじめの値（大きな空港ほど長い。記録がたまれば毎晩決め直す）
insert into public.eta_calib (iata, taxi_out) values
  ('HND', 16), ('NRT', 15), ('KIX', 11), ('ITM', 9), ('CTS', 11), ('FUK', 11), ('OKA', 11), ('NGO', 9), ('NGS', 8), ('SDJ', 8),
  ('KMJ', 8), ('KOJ', 8), ('HIJ', 8), ('KMI', 7), ('HKD', 7), ('AKJ', 7), ('UKB', 8), ('MYJ', 8)
on conflict (iata) do update set taxi_out = coalesce(public.eta_calib.taxi_out, excluded.taxi_out);

-- 空港の地上走行（出発→離陸）の分。分からない空港は8分
create or replace function public.taxi_out_min(p_iata text) returns real
language sql stable security definer set search_path = public as $$
  select coalesce((select taxi_out from public.eta_calib where iata = p_iata), 8)::real
$$;
revoke all on function public.taxi_out_min(text) from public, anon, authenticated;

create or replace function public.refresh_taxi_out() returns int
language plpgsql security definer set search_path = public as $$
declare r record; n int := 0;
begin
  for r in
    select f.dep as iata, percentile_cont(0.5) within group (order by extract(epoch from (public.inferred_time(w.state, 'takeoff_at') - f.atd)) / 60) as med, count(*)::int as cnt
    from public.flight_schedule f join public.flight_watch w on w.schedule_id = f.id
    where f.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and f.atd is not null
      and coalesce((w.state ->> 'takeoff_est')::boolean, true) = false
      and public.inferred_time(w.state, 'takeoff_at') - f.atd between interval '2 minutes' and interval '45 minutes'
    group by f.dep having count(*) >= 10
  loop
    insert into public.eta_calib (iata, taxi_out, n_out) values (r.iata, round(r.med::numeric, 1), r.cnt)
    on conflict (iata) do update set taxi_out = excluded.taxi_out, n_out = excluded.n_out, updated_at = now();
    n := n + 1;
  end loop;
  return n;
end
$$;
revoke all on function public.refresh_taxi_out() from public, anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 到着予想の学習（20:35 UTC）の後に
  execute $q$ select cron.schedule('taxi-out', '40 20 * * *', $job$ select public.refresh_taxi_out() $job$) $q$;
end
$outer$;

-- 撮影の知らせ：「離陸も知らせる」（dep）を足す
alter table public.push_subs drop constraint if exists push_subs_spot_check;
alter table public.push_subs add constraint push_subs_spot_check check (
  spot_lead in (3, 5, 10) and cardinality(spot_kinds) <= 6 and cardinality(spot_regs) <= 10 and cardinality(spot_flights) <= 10
  and spot_kinds <@ array['special', 'big', 'foreign', 'reg', 'ops', 'dep']::text[]);
alter table public.push_subs enable row level security;
revoke all on public.push_subs from public, anon, authenticated;

-- 運用タブの「これから着く便・出る便」：出る便に離陸の時刻を足す（ほかは 20261020000059_board_intl.sql と同じ）
drop function if exists public.airport_board(text, text);
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
    'hours', (select jsonb_agg(jsonb_build_object('h', g.h,
        'flights', (select count(*) from d, today where d.day = today.day and d.h = g.h),
        'late', (select count(*) from d, today where d.day = today.day and d.h = g.h and d.late),
        'cancel', (select count(*) from d, today where d.day = today.day and d.h = g.h and d.cancelled),
        'ref', (select round(count(*) filter (where d.late or d.cancelled) / 7.0, 1) from d, today
                where d.day between today.day - 7 and today.day - 1 and d.h = g.h)) order by g.h)
      from generate_series(0, 23) as g(h))
  )
$$;
revoke all on function public.airport_board(text, text) from public;
grant execute on function public.airport_board(text, text) to anon, authenticated;

-- 撮影の知らせ（離陸）用：その空港をこれから離陸する便（service_role だけ。airport-traffic が使う）
create or replace function public.spot_departures(p_iatas text[]) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', f.flight, 'dep', f.dep, 'arr', f.arr, 'svc_date', f.svc_date, 'aircraft', f.aircraft,
           'reg', w.state ->> 'reg', 'livery', lp.livery, 'gate_actual', f.atd is not null,
           'takeoff', coalesce(f.atd, f.etd, f.std) + make_interval(secs => public.taxi_out_min(f.dep) * 60))), '[]'::jsonb)
  from public.flight_schedule f
  left join public.flight_watch w on w.schedule_id = f.id
  left join public.livery_plans lp on lp.schedule_id = f.id
  where f.dep = any(p_iatas) and f.std between now() - interval '2 hours' and now() + interval '2 hours'
    and not coalesce(f.dep_status ~* 'cancel', false)
    and not (coalesce((w.state ->> 'takeoff_est')::boolean, true) = false and public.inferred_time(w.state, 'takeoff_at') is not null)
    and coalesce(f.atd, f.etd, f.std) + make_interval(secs => public.taxi_out_min(f.dep) * 60) between now() and now() + interval '15 minutes'
$$;
revoke all on function public.spot_departures(text[]) from public, anon, authenticated;
grant execute on function public.spot_departures(text[]) to service_role;
