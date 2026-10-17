-- 機体の位置から推定した離陸・着陸の時刻（flight-watch が flight_watch.state に残しているもの）を、
-- 門限チャレンジ（curfew_flights）と、フライトの記録で選ぶ便の候補（flight_candidates）でも返す。
-- 航空会社の運航情報（atd・ata）がない便（共同運航便・ほかの会社の便）に使う。画面では「推定」と明記する。
--   離陸：出発空港の40km以内・8,000ft以下で最初に飛んでいるのを見た時刻（takeoff_est が false のときだけ）
--   着陸：到着空港の近くで最後に見た時刻（landed_iata が到着空港のときだけ）
create or replace function public.inferred_time(st jsonb, k text) returns timestamptz
language sql immutable set search_path = public as $$
  select case when st ? k and jsonb_typeof(st -> k) = 'number' then to_timestamp((st ->> k)::double precision / 1000) end
$$;
revoke all on function public.inferred_time(jsonb, text) from public, anon, authenticated;

create or replace function public.curfew_flights(p_iata text) returns jsonb
language sql stable security definer set search_path = public as $$
  with c as (
    select p_iata as iata,
      ((((now() at time zone 'Asia/Tokyo') - interval '5 hours')::date + make_interval(hours => h)) at time zone 'Asia/Tokyo') as close_at
    from (select case p_iata when 'ITM' then 21 when 'FUK' then 22 end as h) x where h is not null
  ), s as (
    select f.*,
      case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end as atd_inf,
      case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end as ata_inf
    from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id, c
    where (f.arr = c.iata or f.dep = c.iata)
      and coalesce(f.std, f.sta) between c.close_at - interval '8 hours' and c.close_at + interval '30 minutes'
  )
  select jsonb_build_object('iata', c.iata, 'close_at', c.close_at, 'flights', coalesce((
    select jsonb_agg(f order by f->>'t') from (
      select jsonb_build_object('dir', 'arr', 'flight', s.flight, 'other', s.dep, 'sched', s.sta, 'est', s.eta, 'actual', s.ata, 'inferred', s.ata_inf,
               'status', s.arr_status, 'cancelled', coalesce(s.arr_status ~* 'cancel' or s.dep_status ~* 'cancel', false),
               'dep_actual', coalesce(s.atd, s.atd_inf), 'source', s.source, 't', coalesce(s.ata, s.ata_inf, s.eta, s.sta)) f
      from s
      where s.arr = c.iata and coalesce(s.ata, s.ata_inf, s.eta, s.sta) between c.close_at - interval '90 minutes' and c.close_at + interval '90 minutes'
        and s.sta between c.close_at - interval '6 hours' and c.close_at + interval '30 minutes'
      union all
      select jsonb_build_object('dir', 'dep', 'flight', s.flight, 'other', s.arr, 'sched', s.std, 'est', s.etd, 'actual', s.atd, 'inferred', s.atd_inf,
               'status', s.dep_status, 'cancelled', coalesce(s.dep_status ~* 'cancel', false),
               'dep_actual', coalesce(s.atd, s.atd_inf), 'source', s.source, 't', coalesce(s.atd, s.atd_inf, s.etd, s.std))
      from s
      where s.dep = c.iata and coalesce(s.atd, s.atd_inf, s.etd, s.std) between c.close_at - interval '90 minutes' and c.close_at + interval '90 minutes'
        and s.std between c.close_at - interval '6 hours' and c.close_at + interval '30 minutes'
      limit 60
    ) q), '[]'::jsonb))
  from c
$$;
revoke all on function public.curfew_flights(text) from public;
grant execute on function public.curfew_flights(text) to anon, authenticated;

create or replace function public.flight_candidates(p_dep text, p_arr text, p_dep_at timestamptz, p_arr_at timestamptz)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', flight, 'std', std, 'sta', sta, 'aircraft', aircraft, 'source', source, 'diff_min', diff,
           'atd', atd, 'ata', ata, 'atd_est', atd_inf, 'ata_est', ata_inf, 'cancelled', coalesce(dep_status ~* 'cancel' or arr_status ~* 'cancel', false)) order by diff, std), '[]'::jsonb)
  from (
    select f.flight, f.std, f.sta, f.aircraft, f.source, f.atd, f.ata, f.dep_status, f.arr_status, i.atd_inf, i.ata_inf,
           round((abs(extract(epoch from (coalesce(f.atd, i.atd_inf, f.std) - p_dep_at))) + abs(extract(epoch from (coalesce(f.ata, i.ata_inf, f.sta) - p_arr_at)))) / 60)::int as diff
    from public.flight_schedule f
    left join public.flight_watch w on w.schedule_id = f.id
    cross join lateral (select
      case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end as atd_inf,
      case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end as ata_inf) i
    where p_dep ~ '^[A-Z]{3}$' and p_arr ~ '^[A-Z]{3}$'
      and p_arr_at > p_dep_at and p_arr_at - p_dep_at < interval '24 hours'
      and f.dep = p_dep and f.arr = p_arr
      and f.std between p_dep_at - interval '3 hours' and p_arr_at
      and f.sta between p_dep_at and p_arr_at + interval '3 hours'
    order by diff, f.std
    limit 5
  ) c
$$;
revoke all on function public.flight_candidates(text, text, timestamptz, timestamptz) from public;
grant execute on function public.flight_candidates(text, text, timestamptz, timestamptz) to anon, authenticated;
