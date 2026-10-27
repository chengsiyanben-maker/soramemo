-- 撮る人の一覧の登録記号：空港にこれから来る（この3時間半の）JAL・ANA の便ごとに、機体の登録記号と、その決め方を返す。
--   live：その便そのものを機体の位置で見つけた（見張りが登録記号を残した）＝「確認」
--   prev：今日、機体が分かった便の次に、その便がよく続く（前の60日の機体のつながり。同じ曜日は2倍）＝「前の便から」
--   pred：前の便のさらに前の便から2つたどった＝「予想」
--   prev・pred は、3回以上見ていて、つながりの割合（2つたどるときは掛けたもの）が4割以上のときだけ。
--   機体は、今日いちばん新しく分かった便から先だけをたどる（もう別の便で見つかった機体を、前の便から予想しない）。
-- 表は足さない。表には直接さわらせず、この関数（security definer）からだけ読む。今ある表の RLS はそのまま。
create or replace function public.spot_regs(p_iata text) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  -- その空港にこれから来る便（着陸と離陸）
  target as (
    select f.id, f.flight, f.dep, f.arr, f.std, f.sta, case when f.arr = p_iata then 'arr' else 'dep' end as dir
    from public.flight_schedule f, d
    where p_iata ~ '^[A-Z]{3}$' and f.svc_date between d.today - 1 and d.today
      and ((f.arr = p_iata and f.sta between now() - interval '30 minutes' and now() + interval '3 hours 30 minutes')
        or (f.dep = p_iata and f.std between now() - interval '30 minutes' and now() + interval '3 hours 30 minutes'))
    limit 300
  ),
  -- 今日、機体（登録記号）が分かった便
  seen as (
    select f.id, f.flight, f.dep, f.arr, f.std, f.sta, w.state ->> 'reg' as reg
    from public.flight_schedule f join public.flight_watch w on w.schedule_id = f.id, d
    where f.svc_date between d.today - 1 and d.today and f.std > now() - interval '20 hours'
      and (w.state ->> 'reg') ~ '^[A-Z0-9-]{2,10}$'
  ),
  -- 機体ごとに、いちばん新しく分かった便だけ
  last_seen as (select distinct on (reg) * from seen order by reg, std desc),
  obs as (
    select prev_flight, next_flight, sum(case when extract(dow from o.svc_date) = extract(dow from d.today) then 2 else 1 end) as sc,
           count(*) as n
    from public.rotation_obs o, d where o.svc_date >= d.today - 60 group by 1, 2
  ),
  tot as (select prev_flight, sum(sc) as total from obs group by 1),
  live as (select t.id, s.reg from target t join seen s on s.id = t.id),
  prev as (
    select distinct on (t.id) t.id, l.reg, l.flight as via, round(o.sc::numeric / tt.total, 2) as share
    from target t
    join obs o on o.next_flight = t.flight
    join tot tt on tt.prev_flight = o.prev_flight
    join last_seen l on l.flight = o.prev_flight and l.arr = t.dep and l.sta < t.std
    where o.n >= 3 and o.sc::numeric / tt.total >= 0.4
    order by t.id, o.sc::numeric / tt.total desc, l.sta desc
  ),
  pred as (
    select distinct on (t.id) t.id, l.reg, l.flight as via, round((o1.sc::numeric / t1.total) * (o2.sc::numeric / t2.total), 2) as share
    from target t
    join obs o2 on o2.next_flight = t.flight
    join tot t2 on t2.prev_flight = o2.prev_flight
    join public.flight_schedule m on m.flight = o2.prev_flight and m.svc_date between (select today from d) - 1 and (select today from d) and m.std > now() - interval '20 hours' and m.arr = t.dep and m.sta < t.std
    join obs o1 on o1.next_flight = m.flight
    join tot t1 on t1.prev_flight = o1.prev_flight
    join last_seen l on l.flight = o1.prev_flight and l.arr = m.dep and l.sta < m.std
    where o1.n >= 3 and o2.n >= 3 and (o1.sc::numeric / t1.total) * (o2.sc::numeric / t2.total) >= 0.4
    order by t.id, (o1.sc::numeric / t1.total) * (o2.sc::numeric / t2.total) desc, l.sta desc
  )
  select coalesce(jsonb_agg(jsonb_build_object('flight', t.flight, 'dir', t.dir,
           'reg', coalesce(lv.reg, pv.reg, pd.reg),
           'src', case when lv.reg is not null then 'live' when pv.reg is not null then 'prev' else 'pred' end,
           'via', case when lv.reg is not null then null when pv.reg is not null then pv.via else pd.via end,
           'share', case when lv.reg is not null then null when pv.reg is not null then pv.share else pd.share end)
         order by case when t.dir = 'arr' then t.sta else t.std end), '[]'::jsonb)
  from target t left join live lv on lv.id = t.id left join prev pv on pv.id = t.id left join pred pd on pd.id = t.id
  where coalesce(lv.reg, pv.reg, pd.reg) is not null
$$;
revoke all on function public.spot_regs(text) from public;
grant execute on function public.spot_regs(text) to anon, authenticated;
