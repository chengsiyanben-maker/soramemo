-- 特別塗装機の「見た」（my_livery_seen）が日本時間の0時をまたぐと見えない件を直す（関数だけ。表は変えない）
--   前は便の日付（reg_legs.day）を「チェックインの日の前の日〜その日」で探していたので、
--   23時58分のチェックインと0時8分に着いた便（便の日付は次の日）のように、チェックインのあと日付が変わった便が見えなかった。
--   便の日付を「チェックインの日の前の日〜次の日」で探す（経営の co3_seen と同じ幅）。前後45分の決まりは変えない。
create or replace function public.my_livery_seen(p_regs text[]) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('reg', reg, 'iata', iata, 'at', at) order by at), '[]'::jsonb) from (
    select distinct on (l.reg, a.iata, (c.created_at at time zone 'Asia/Tokyo')::date) l.reg, a.iata, c.created_at as at
    from public.checkins c join public.airports a on a.id = c.airport_id
    join public.reg_legs l on l.reg = any(p_regs[1:100])
      and l.day between (c.created_at at time zone 'Asia/Tokyo')::date - 1 and (c.created_at at time zone 'Asia/Tokyo')::date + 1
      and ((l.arr = a.iata and abs(extract(epoch from (l.last_at - c.created_at))) <= 2700) or (l.dep = a.iata and abs(extract(epoch from (l.first_at - c.created_at))) <= 2700))
    where c.user_id = auth.uid()
    order by l.reg, a.iata, (c.created_at at time zone 'Asia/Tokyo')::date, c.created_at
  ) q
$$;
revoke all on function public.my_livery_seen(text[]) from public, anon;
grant execute on function public.my_livery_seen(text[]) to authenticated;
