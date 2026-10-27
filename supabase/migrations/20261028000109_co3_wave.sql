-- エアライン経営 co-v3：朝のまとめの「遅れの波」
--   前の日に決まった便（co3_leg_status）を、路線（＝その路線の機体）ごとに並べて co3_morning の wave に入れる
--   便ごと：出発・到着（日本時間の0時からの分、到着は距離からの飛ぶ時間）・向き・定時／遅れ／欠航・遅れの分・前の便から続いた分
--   表は変えない（関数だけ）

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_morning(uuid)'::regprocedure) into src;
  if position('''wave''' in src) = 0 then
    if position($r$'open', $r$ in src) = 0 then raise exception 'co3_morning の形が変わっていて、遅れの波を入れられない'; end if;
    src := replace(src, $r$'open', $r$,
      $r$'wave', (select coalesce(jsonb_agg(jsonb_build_object('k', w.route_key,
                   'reg', (select a.reg from aircraft a where a.user_id = p_uid and a.route_key = w.route_key order by a.id limit 1),
                   'legs', w.legs) order by w.route_key), '[]'::jsonb)
                 from (select x.route_key, jsonb_agg(jsonb_build_object('n', x.leg, 'f', x.dep, 'to', x.arr,
                          't', (extract(hour from x.dep_at at time zone 'Asia/Tokyo') * 60 + extract(minute from x.dep_at at time zone 'Asia/Tokyo'))::int,
                          'blk', co3.leg_block_min(coalesce(co3_km(x.dep, x.arr), 0)),
                          's', x.status, 'd', x.delay_min, 'c', x.carried, 'rn', x.real_n) order by x.leg) as legs
                         from co3_leg_status x, t where x.user_id = p_uid and x.day = t.today - 1 group by x.route_key) w),
    'open', $r$);
    execute src;
  end if;
end
$do$;
