-- 空の道：全機の航跡（airport_tracks_all）に、JAL・ANA の便の航跡（flight_tracks）のうち全機の航跡にない便を足して出す（10/27）。
-- 全機の航跡は低い高度が地上で受信できないと残らず、松山（10/23 から1日0〜3本）・仙台・那覇などで少なかった。
-- 前は全機の航跡が1本でもあると JAL・ANA の航跡を使わなかったので、少しだけ取れた日はかえって少なくなっていた。
-- 同じ便は便名（呼び出し符号）で1本にまとめる。JAL・ANA の航跡は次の日にまとめるので、今日の分は全機の航跡だけ。表と RLS は変えない
create or replace function public.airport_tracks(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  a as (
    select callsign, dep_here, pts, extract(hour from at at time zone 'Asia/Tokyo')::int as h, at
    from public.airport_tracks_all, d where iata = p_iata and day = p_day and p_day <= d.today order by at limit 3000
  ),
  b as (
    select case when h.dep = p_iata then 1 else 0 end as dep_here, t.pts,
           extract(hour from (case when h.dep = p_iata then coalesce(h.atd, h.std) else coalesce(h.ata, h.sta) end) at time zone 'Asia/Tokyo')::int as hr,
           case when h.dep = p_iata then coalesce(h.atd, h.std) else coalesce(h.ata, h.sta) end as at
    from d, public.flight_history h join public.flight_tracks t on t.svc_date = h.svc_date and t.flight = h.flight and t.dep = h.dep
    where h.svc_date = p_day and p_day < d.today and (h.dep = p_iata or h.arr = p_iata) and not h.cancelled
      and (case when h.callsign is null then not exists (select 1 from a) else not exists (select 1 from a where a.callsign = upper(h.callsign)) end)
    order by h.std limit 2000
  )
  select coalesce((select jsonb_agg(x.j order by x.at) from (
    select jsonb_build_object('d', dep_here, 'p', pts, 'h', h) as j, at from a
    union all
    select jsonb_build_object('d', dep_here, 'p', pts, 'h', hr), at from b
  ) x), '[]'::jsonb)
$$;
revoke all on function public.airport_tracks(text, date) from public;
grant execute on function public.airport_tracks(text, date) to anon, authenticated;
