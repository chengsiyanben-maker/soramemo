-- 見る・遊ぶの画面のための読み出し
--   my_livery_seen：特別塗装機の図鑑の「見た」。自分がチェックインした空港に、その前後45分で着いた・出た特別塗装機（reg_legs から）
--   airport_day   ：あの日の空。その日の空港のまとめ（airport_daily）と、滑走路ごとの着陸・離陸の数（rwy_samples）
--   airport_trend ：空港の傾向。風の向きごとの運用（ops_log）、時間帯ごとの着陸（rwy_samples）、ゴーアラウンド（ga_events）
create or replace function public.my_livery_seen(p_regs text[]) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('reg', reg, 'iata', iata, 'at', at) order by at), '[]'::jsonb) from (
    select distinct on (l.reg, a.iata, (c.created_at at time zone 'Asia/Tokyo')::date) l.reg, a.iata, c.created_at as at
    from public.checkins c join public.airports a on a.id = c.airport_id
    join public.reg_legs l on l.reg = any(p_regs[1:100]) and l.day between (c.created_at at time zone 'Asia/Tokyo')::date - 1 and (c.created_at at time zone 'Asia/Tokyo')::date
      and ((l.arr = a.iata and abs(extract(epoch from (l.last_at - c.created_at))) <= 2700) or (l.dep = a.iata and abs(extract(epoch from (l.first_at - c.created_at))) <= 2700))
    where c.user_id = auth.uid()
    order by l.reg, a.iata, (c.created_at at time zone 'Asia/Tokyo')::date, c.created_at
  ) q
$$;
revoke all on function public.my_livery_seen(text[]) from public, anon;
grant execute on function public.my_livery_seen(text[]) to authenticated;

create or replace function public.airport_day(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('iata', p_iata, 'day', p_day,
    'daily', (select jsonb_build_object('flights', flights, 'arr', arr, 'dep', dep, 'late', late, 'cancelled', cancelled, 'modes', modes, 'max_wind', max_wind)
              from public.airport_daily where iata = p_iata and day = p_day),
    'rwy', coalesce((select jsonb_object_agg(dir || ':' || rwy, n) from (
              select dir, rwy, count(*) as n from public.rwy_samples
              where iata = p_iata and (src = 'live' or iata not in ('HND', 'NRT')) and (at at time zone 'Asia/Tokyo')::date = p_day group by 1, 2) r), '{}'::jsonb),
    'ga', (select count(*) from public.ga_events where iata = p_iata and (at at time zone 'Asia/Tokyo')::date = p_day))
$$;
revoke all on function public.airport_day(text, date) from public;
grant execute on function public.airport_day(text, date) to anon, authenticated;

create or replace function public.airport_trend(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  with o as (
    select coalesce(obs_mode, est_mode) as mode,
      case when wspd is null or wspd < 5 or wdir is null then 'calm' else (array['N', 'E', 'S', 'W'])[((wdir + 45) % 360) / 90 + 1] end as sec
    from public.ops_log where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 3660))
  ), s as (
    select (at at time zone 'Asia/Tokyo') as t from public.rwy_samples
    where iata = p_iata and dir = 'arr' and (src = 'live' or iata not in ('HND', 'NRT')) and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 3660))
  )
  select jsonb_build_object('iata', p_iata, 'days', least(greatest(coalesce(p_days, 30), 1), 3660),
    'wind', coalesce((select jsonb_object_agg(sec, m) from (select sec, jsonb_object_agg(mode, n) as m from (select sec, mode, count(*) as n from o group by 1, 2) a group by sec) b), '{}'::jsonb),
    'hours', coalesce((select jsonb_object_agg(h, round(n::numeric / greatest(d, 1), 1)) from (
              select extract(hour from t)::int as h, count(*) as n, (select count(distinct t::date) from s) as d from s group by 1) c), '{}'::jsonb),
    'arr_days', (select count(distinct t::date) from s),
    'ga', (select jsonb_build_object('n', count(*), 'windy', count(*) filter (where coalesce((wx->>'wgst')::int, 0) >= 25 or coalesce((wx->>'wspd')::int, 0) >= 20),
              'low', count(*) filter (where coalesce(wx->>'raw', '') ~ '(BKN|OVC|VV)00[0-4]')) from public.ga_events
           where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 3660))))
$$;
revoke all on function public.airport_trend(text, int) from public;
grant execute on function public.airport_trend(text, int) to anon, authenticated;
