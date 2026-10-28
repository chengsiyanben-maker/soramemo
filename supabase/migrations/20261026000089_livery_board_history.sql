-- 特別塗装機の画面：時刻表にない便の発着を、同じ便名の前の30日の路線で埋める（埋めたものは hist: true。画面では「いつもの路線から」と出す）。
-- 表と RLS は変えない（reg_legs は利用者から直接読めないまま）

create or replace function public.livery_board(p_regs text[]) returns jsonb
language sql stable security definer set search_path = public as $$
  with r as (
    select distinct s.reg from public.livery_sightings s
    where s.reg = any(p_regs[1:200])
  ), d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  legs as (
    select l.reg, l.callsign, l.day, l.first_at, l.last_at,
      coalesce(l.dep, f.dep, h.dep) as dep, coalesce(l.arr, f.arr, h.arr) as arr, f.std, f.sta,
      (l.dep is null or l.arr is null) and f.id is not null as by_schedule,
      (l.dep is null or l.arr is null) and f.id is null and h.dep is not null as by_history
    from public.reg_legs l join r on r.reg = l.reg cross join d
    left join lateral (
      select fs.id, fs.dep, fs.arr, fs.std, fs.sta from public.flight_schedule fs
      where l.day >= d.today - 1 and fs.flight = public.cs_flight(l.callsign) and fs.std between l.first_at - interval '3 hours' and l.first_at + interval '1 hour'
      order by abs(extract(epoch from fs.std - l.first_at)) limit 1
    ) f on true
    -- 時刻表にない便（ODPT にない会社・空港）は、同じ便名の前の30日にいちばん多かった路線で埋める（便名の路線はふつう変わらない）
    left join lateral (
      select hh.dep, hh.arr from public.reg_legs hh
      where l.day >= d.today - 1 and (l.dep is null or l.arr is null) and f.id is null
        and hh.callsign = l.callsign and hh.day between d.today - 30 and d.today - 1 and hh.dep is not null and hh.arr is not null
        and (l.dep is null or hh.dep = l.dep) and (l.arr is null or hh.arr = l.arr)
      group by hh.dep, hh.arr order by count(*) desc limit 1
    ) h on true
    where l.day >= d.today - 30
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'reg', r.reg,
    'now', (select jsonb_build_object('at', s.seen_at, 'lat', round(s.lat::numeric, 3), 'lon', round(s.lon::numeric, 3), 'alt_ft', s.alt_ft,
              'callsign', s.callsign, 'iata', s.iata, 'phase', s.phase, 'kt', p.kt)
            from public.livery_sightings s left join public.live_positions p on p.callsign = s.callsign
            where s.reg = r.reg and s.seen_at > now() - interval '15 minutes'),
    'today', coalesce((select jsonb_agg(jsonb_build_object('cs', g.callsign, 'dep', g.dep, 'arr', g.arr, 'first', g.first_at, 'last', g.last_at,
              'std', g.std, 'sta', g.sta, 'sch', g.by_schedule, 'hist', g.by_history) order by g.first_at)
            from legs g cross join d where g.reg = r.reg and g.day = d.today), '[]'::jsonb),
    'last_day', (select max(g.day) from legs g where g.reg = r.reg),
    'arr30', coalesce((select jsonb_object_agg(a.arr, a.n) from (select g.arr, count(*) as n from legs g where g.reg = r.reg and g.arr is not null group by g.arr) a), '{}'::jsonb)
  )), '[]'::jsonb) from r
$$;
revoke all on function public.livery_board(text[]) from public;
grant execute on function public.livery_board(text[]) to anon, authenticated;
