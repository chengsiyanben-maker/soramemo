-- エアライン経営 co-v3：画面のための足し算（表は変えない。関数 co_state だけ）
--   fleet の各機体に kind（freighter・bizjet・light・pax）を足す（貨物の路線に入れる機体を選ぶため）
--   路線ごとに決めた便数（plans。決めていない路線は入らない）
--   地域航空の会社には、いま買える小型機の一覧と値段（small）を足す（co3_buy_small と同じ計算）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''kind'', case when co3_is_freighter(id)' in src) = 0 then
    if position($r$'rode_on', rode_on, 'flight', rode_flight) order by id)$r$ in src) = 0 then
      raise exception 'co_state の形が変わっていて、機体の種類を入れられない';
    end if;
    src := replace(src, $r$'rode_on', rode_on, 'flight', rode_flight) order by id)$r$,
      $r$'rode_on', rode_on, 'flight', rode_flight,
                 'kind', case when not v3 then null when co3_is_freighter(id) then 'freighter' when co3_is_bizjet(id) then 'bizjet' when co3_is_light(id) then 'light' else 'pax' end) order by id)$r$);
  end if;
  if position('''small'', case when v3' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、小型機の一覧を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'small', case when v3 and c.policy = 'regional' then (
        select coalesce(jsonb_agg(jsonb_build_object('code', t.code, 'name', t.name, 'kind', t.kind, 'seats', t.seats, 'range', t.range_km,
                 'price', round(t.price * (1 + 0.25 * w.n))) order by t.price), '[]'::jsonb)
          from co3_types t,
               (select coalesce(sum(co3.count_weight(coalesce(x.kind in ('small', 'heli'), a.type = 'prop'))), 0) as n
                  from aircraft a left join co3_types x on x.code = a.co3_code where a.user_id = uid) w
         where t.kind in ('small', 'heli')) end,
    'plans', case when v3 then (select coalesce(jsonb_object_agg(p.route_key, p.flights), '{}'::jsonb) from co3_plans p where p.user_id = uid) end,
    'satisfaction', c.satisfaction,$r$);
  end if;
  execute src;
end
$do$;
