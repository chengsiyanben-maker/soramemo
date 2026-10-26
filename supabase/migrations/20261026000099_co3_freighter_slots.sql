-- エアライン経営 co-v3：旅客の会社の貨物機と、混雑空港の発着枠のそろえ直し
--   ・FSC とミドルコストは、機体の1割まで貨物機を持てる（JAL の 767 貨物機型。10機で1機）。LCC・プライベートジェット・地域航空は持てない。
--     貨物の会社は上限なし。持った貨物機は co3_cargo_assign で貨物の路線に入れる（稼ぎは貨物の会社と同じ計算）
--   ・混雑空港の「申し込み」（全社の1日の便）の数え方を1つにそろえる（co3_slot_totals）。
--     便数を決めていない機体は、その路線の距離で1日に飛べる便。旅客・貨物・プライベートジェットの便をすべて数える
--   ・貨物機とビジネスジェットの便も、申し込みが枠を超えたら申し込みの割合で分ける（最低4便）

-- 全社の、混雑空港ごとの1日の便（申し込み）
create or replace function public.co3_slot_totals() returns table (iata text, total numeric)
language sql stable security definer set search_path = public as $$
  with k as (
    select ac.user_id, ac.route_key,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 1)::int) else split_part(ac.route_key, '-', 1) end as a,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 2)::int) else split_part(ac.route_key, '-', 2) end as b
      from aircraft ac where ac.route_key is not null
  ), f as (
    select k.a, k.b, coalesce(p.flights, co3.legs_per_day(coalesce(co3_km(k.a, k.b), 800))) as fl
      from k left join co3_plans p on p.user_id = k.user_id and p.route_key = k.route_key
  )
  select ap, sum(fl) from (select a as ap, fl from f union all select b, fl from f) u
   where ap in ('HND', 'NRT', 'KIX', 'ITM', 'FUK') group by ap
$$;
revoke all on function public.co3_slot_totals() from public, anon, authenticated;

-- 申し込んだ便を、混雑空港の枠で分けたあとの便（両端の小さいほう。混雑空港でなければそのまま）
create or replace function public.co3_slot_cap(p_flights integer, p_a text, p_b text) returns integer
language sql stable security definer set search_path = public as $$
  select least(p_flights, coalesce(
    (select min(co3.slot_allot(p_flights, q.total::int,
               co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata),
                                 (select count(*)::int from companies where last_collect > now() - interval '30 days'))))
       from co3_slot_totals() q where q.iata in (p_a, p_b)), p_flights))
$$;
revoke all on function public.co3_slot_cap(integer, text, text) from public, anon, authenticated;

-- 3つの内わけの「req」を、そろえた数え方に置き換える
do $do$
declare fn text; src text; n0 text;
begin
  foreach fn in array array['public.co3_route_econ(uuid)', 'public.co3_cargo_econ(uuid)', 'public.co3_pj_econ(uuid)'] loop
    select pg_get_functiondef(fn::regprocedure) into src;
    n0 := src;
    src := regexp_replace(src, 'req as \(.*?group by ap\.iata\s*\)', 'req as (select st.iata, st.total from co3_slot_totals() st)');
    if src = n0 then raise exception '% の形が変わっていて、発着枠の数え方をそろえられない', fn; end if;
    execute src;
  end loop;
end
$do$;

-- 貨物機の便も発着枠で分ける
do $do$
declare src text; n0 text;
begin
  select pg_get_functiondef('public.co3_cargo_econ(uuid)'::regprocedure) into src;
  n0 := src;
  src := replace(src,
    'least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = cr.route_key), 99), co3.legs_per_day(cr.km)) as fl,',
    'co3_slot_cap(least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = cr.route_key), 99), co3.legs_per_day(cr.km)), cr.a, cr.b) as fl,');
  if src = n0 then raise exception 'co3_cargo_econ の形が変わっていて、発着枠を入れられない'; end if;
  execute src;

  select pg_get_functiondef('public.co3_pj_econ(uuid)'::regprocedure) into src;
  n0 := src;
  src := replace(src, 'select g as fl from generate_series(2, co3.legs_per_day(v.km), 2) g',
                      'select g as fl from generate_series(2, co3_slot_cap(co3.legs_per_day(v.km), v.a, v.b), 2) g');
  src := replace(src, 'where v.plan is null or g = least(v.plan, co3.legs_per_day(v.km))',
                      'where v.plan is null or g = co3_slot_cap(least(v.plan, co3.legs_per_day(v.km)), v.a, v.b)');
  if src = n0 then raise exception 'co3_pj_econ の形が変わっていて、発着枠を入れられない'; end if;
  execute src;
end
$do$;

-- 見た機体を買う：旅客の会社の貨物機は機体の1割まで（FSC・ミドルコスト）。LCC・プライベートジェット・地域航空は貨物機を持てない
do $do$
declare src text; n0 text;
begin
  select pg_get_functiondef('public.co3_buy_seen(text)'::regprocedure) into src;
  n0 := src;
  src := replace(src, '  price := co3_seen_price(uid, s.code);',
$r$  if t.kind = 'freighter' then
    if (select policy from companies where user_id = uid) in ('lcc', 'pj', 'regional') then raise exception 'policy cannot own freighters'; end if;
    if (select policy from companies where user_id = uid) in ('fsc', 'mcc')
       and (select count(*) filter (where co3_is_freighter(id)) + 1 from aircraft where user_id = uid)
           > (select (count(*) + 1) / 10 from aircraft where user_id = uid) then
      raise exception 'freighters up to 10 percent';
    end if;
  end if;
  price := co3_seen_price(uid, s.code);$r$);
  if src = n0 then raise exception 'co3_buy_seen の形が変わっていて、貨物機の上限を入れられない'; end if;
  execute src;
end
$do$;
