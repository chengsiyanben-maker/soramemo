-- 乗る便の機体：ホームで便名だけを入れたときにも使えるように、出発空港を省けるようにする（今日・明日のこれから出る便から、いちばん早いもの）
create or replace function public.inbound_aircraft(p_flight text, p_dep text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  s record; p record; w jsonb; pw jsonb; turn int; arr_at timestamptz; arr_src text; ready timestamptz;
begin
  if p_flight is null or p_flight !~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$' or (p_dep is not null and p_dep !~ '^[A-Z]{3}$') then return null; end if;
  select f.*, fw.state as st into s
  from public.flight_schedule f left join public.flight_watch fw on fw.schedule_id = f.id
  where f.svc_date in (today, today + 1) and (p_dep is null or f.dep = p_dep) and public.flight_no_norm(f.flight) = public.flight_no_norm(p_flight)
    and f.std > now() - interval '3 hours'
  order by f.std limit 1;
  if s is null then return jsonb_build_object('flight', p_flight, 'found', false); end if;
  w := coalesce(s.st, '{}'::jsonb);

  -- 前の便の候補（前の60日の記録で多いもの）
  select q.flight, q.dep, q.arr, q.std, q.sta, q.atd, q.eta, q.ata, q.aircraft, q.cancelled, q.st, q.score, q.total into p
  from (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.atd, f.eta, f.ata, f.aircraft, fw.state as st,
           coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled,
           sum(case when extract(dow from o.svc_date) = extract(dow from s.svc_date) then 2 else 1 end) as score,
           (select sum(case when extract(dow from o2.svc_date) = extract(dow from s.svc_date) then 2 else 1 end)
              from public.rotation_obs o2 where o2.next_flight = s.flight and o2.svc_date >= today - 60) as total
    from public.rotation_obs o
    join public.flight_schedule f on f.flight = o.prev_flight and f.svc_date = s.svc_date and f.arr = s.dep
    left join public.flight_watch fw on fw.schedule_id = f.id
    where o.next_flight = s.flight and o.svc_date >= today - 60
      and f.sta between s.std - interval '6 hours' and s.std - interval '15 minutes'
    group by f.flight, f.dep, f.arr, f.std, f.sta, f.atd, f.eta, f.ata, f.aircraft, fw.state, f.dep_status, f.arr_status
    order by score desc, f.sta desc limit 1
  ) q;

  if p is null then
    return jsonb_build_object('flight', s.flight, 'found', true, 'dep', s.dep, 'arr', s.arr, 'std', s.std, 'etd', s.etd, 'atd', s.atd,
      'reg', w ->> 'reg', 'phase', w ->> 'phase', 'inbound', null);
  end if;
  pw := coalesce(p.st, '{}'::jsonb);
  turn := case when coalesce(p.aircraft, s.aircraft, '') ~* '^(7[6-8]|77|78|35|B7[678]|A35|A33)' then 45 else 35 end;
  if p.ata is not null then arr_at := p.ata; arr_src := 'actual';
  elsif p.eta is not null then arr_at := p.eta; arr_src := 'est';
  elsif pw ->> 'landed_iata' = p.arr and public.inferred_time(pw, 'landed_at') is not null then arr_at := public.inferred_time(pw, 'landed_at'); arr_src := 'landed';
  elsif pw ->> 'phase' = 'air' and public.inferred_time(pw, 'eta') is not null then arr_at := public.inferred_time(pw, 'eta'); arr_src := 'predicted';
  else arr_at := p.sta; arr_src := 'sched';
  end if;
  ready := greatest(s.std, arr_at + make_interval(mins => turn));
  return jsonb_build_object('flight', s.flight, 'found', true, 'dep', s.dep, 'arr', s.arr, 'std', s.std, 'etd', s.etd, 'atd', s.atd,
    'reg', coalesce(w ->> 'reg', pw ->> 'reg'), 'phase', w ->> 'phase',
    'inbound', jsonb_build_object('flight', p.flight, 'dep', p.dep, 'arr', p.arr, 'std', p.std, 'sta', p.sta, 'atd', p.atd, 'eta', p.eta, 'ata', p.ata,
      'cancelled', p.cancelled, 'phase', pw ->> 'phase', 'reg', pw ->> 'reg', 'type', pw ->> 'type',
      'takeoff', case when coalesce((pw ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(pw, 'takeoff_at') end,
      'pos', case when pw ->> 'phase' = 'air' and pw -> 'last' is not null then jsonb_build_object('lat', pw -> 'last' -> 'lat', 'lon', pw -> 'last' -> 'lon', 'alt', pw -> 'last' -> 'alt_ft',
               'at', public.inferred_time(pw -> 'last', 'at')) end,
      'share', round(p.score::numeric / greatest(p.total, 1), 2), 'seen', p.score),
    'arr_at', arr_at, 'arr_src', arr_src, 'turn', turn, 'ready', ready,
    'late', greatest(0, round(extract(epoch from (ready - s.std)) / 60)));
end
$$;
revoke all on function public.inbound_aircraft(text, text) from public;
grant execute on function public.inbound_aircraft(text, text) to anon, authenticated;
