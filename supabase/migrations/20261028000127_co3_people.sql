-- エアライン経営 co-v3：乗員・整備士と地上の仕事（仕様書「乗員と整備士」「地上の仕事」。格付け3から）
--   人数は「機体何機分」で数える。飛んでいる機体（路線に入れた・自分で組んだ）1機ごとに 1機分、中型以上（wb・lg）は 2機分
--   いる人：はじめから 3機分（給料は運航の費用に込み）＋ 役職「乗員」「整備」（守り神の階級 +1 ごとに +1機分）＋ 雇った分
--   雇う：乗員1組（1機分） 採用費 2,000・給料 20/日、整備士1機分 採用費 1,500・給料 15/日。いつでも減らせる（採用費は戻らない）
--   足りないとき（格付け3から。格付け1・2は人の不足は起きない）
--     乗員：いる ÷ 要る の割合まで、その日の便が飛ぶ（超えた分の便は運休）
--     整備士：故障が 要る ÷ いる 倍に増える（上限3倍）
--   地上の仕事：格付け1・2は委託（運航の費用に込み、運航の費用の約1割）。格付け3から「自社」を選べる
--     自社：拠点の空港を発着する便の運航の費用 −3%（地上の仕事の分が3割安い）。拠点ごとに毎日の人件費 30
--     折り返しの5分短縮・飛行学校・整備場・地上の会社・乗員の資格と拠点・経験は、あとで足す

alter table public.companies add column if not exists crew_hired integer not null default 0 check (crew_hired between 0 and 500);
alter table public.companies add column if not exists mech_hired integer not null default 0 check (mech_hired between 0 and 500);
alter table public.companies add column if not exists ground text not null default 'outsource' check (ground in ('outsource', 'self'));
alter table public.companies enable row level security;

-- 要る人（機体何機分）
create or replace function public.co3_people_need(p_uid uuid) returns integer
language sql stable security definer set search_path = public as $$
  select coalesce(sum(case when a.type in ('wb', 'lg') then 2 else 1 end), 0)::int
    from aircraft a where a.user_id = p_uid and (a.route_key is not null or exists (select 1 from co3_sched s where s.aircraft_id = a.id))
$$;
revoke all on function public.co3_people_need(uuid) from public, anon, authenticated;

-- いる人（乗員・整備士）
create or replace function public.co3_people_have(p_uid uuid, out crew integer, out mech integer)
language sql stable security definer set search_path = public as $$
  select 3 + c.crew_hired + coalesce((select 1 + rank_tier(count(distinct (ch.created_at at time zone 'Asia/Tokyo')::date))
                                         from checkins ch where c.roles->>'crew' ~ '^[0-9]+$' and ch.user_id = p_uid and ch.airport_id = (c.roles->>'crew')::int
                                        having count(*) > 0), 0),
         3 + c.mech_hired + coalesce((select 1 + rank_tier(count(distinct (ch.created_at at time zone 'Asia/Tokyo')::date))
                                         from checkins ch where c.roles->>'maint' ~ '^[0-9]+$' and ch.user_id = p_uid and ch.airport_id = (c.roles->>'maint')::int
                                        having count(*) > 0), 0)
    from companies c where c.user_id = p_uid
$$;
revoke all on function public.co3_people_have(uuid) from public, anon, authenticated;

-- 乗員の割合（1を超えない。格付け1・2はいつも1）
create or replace function public.co3_crew_ratio(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select case when coalesce(co3_rating_need(p_uid), 1) < 3 then 1
              else least(1, (select crew from co3_people_have(p_uid))::numeric / greatest(1, co3_people_need(p_uid))) end
$$;
revoke all on function public.co3_crew_ratio(uuid) from public, anon, authenticated;

-- 整備士の不足で増える故障（1〜3倍）
create or replace function public.co3_mech_mult(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select case when coalesce(co3_rating_need(p_uid), 1) < 3 then 1
              else least(3, greatest(1, co3_people_need(p_uid)::numeric / greatest(1, (select mech from co3_people_have(p_uid))))) end
$$;
revoke all on function public.co3_mech_mult(uuid) from public, anon, authenticated;

-- 発着枠と乗員で決まる、その日に飛べる便
create or replace function public.co3_people_fl(p_uid uuid, p_fl integer, p_a text, p_b text) returns integer
language sql stable security definer set search_path = public as $$ select floor(co3_slot_fl(p_uid, p_fl, p_a, p_b) * co3_crew_ratio(p_uid))::int $$;
revoke all on function public.co3_people_fl(uuid, integer, text, text) from public, anon, authenticated;

-- 地上の仕事：自社なら拠点の空港を発着する便の運航の費用 −3%
create or replace function public.co3_ground_mult(p_uid uuid, p_a text, p_b text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select 0.97 from companies c join airports h on h.id = c.home_airport
                    where c.user_id = p_uid and c.ground = 'self' and coalesce(c.rating, 1) >= 3 and h.iata in (p_a, p_b)), 1)
$$;
revoke all on function public.co3_ground_mult(uuid, text, text) from public, anon, authenticated;

-- 人の給料（1日）：雇った乗員 20・整備士 15、地上の仕事を自社にしたら拠点ごとに 30
create or replace function public.co3_people_cost(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select c.crew_hired * 20 + c.mech_hired * 15
                          + case when c.ground = 'self' and c.home_airport is not null and coalesce(c.rating, 1) >= 3 then 30 else 0 end
                     from companies c where c.user_id = p_uid), 0)
$$;
revoke all on function public.co3_people_cost(uuid) from public, anon, authenticated;

-- 雇う・減らす（p_delta が正なら雇う、負なら減らす）
create or replace function public.co3_hire(p_kind text, p_delta integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); fee numeric; cur int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_kind not in ('crew', 'mech') or p_delta is null or p_delta = 0 or abs(p_delta) > 50 then raise exception 'invalid hire'; end if;
  select case when p_kind = 'crew' then crew_hired else mech_hired end into cur from companies where user_id = uid;
  if cur + p_delta < 0 then raise exception 'invalid hire'; end if;
  if p_delta > 0 then
    fee := p_delta * case when p_kind = 'crew' then 2000 else 1500 end;
    if (select cash from companies where user_id = uid) < fee then raise exception 'not enough cash'; end if;
    update companies set cash = cash - fee where user_id = uid;
  end if;
  if p_kind = 'crew' then update companies set crew_hired = crew_hired + p_delta where user_id = uid;
  else update companies set mech_hired = mech_hired + p_delta where user_id = uid; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_hire(text, integer) from public, anon;
grant execute on function public.co3_hire(text, integer) to authenticated;

create or replace function public.co3_set_ground(p_mode text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_mode not in ('outsource', 'self') then raise exception 'invalid mode'; end if;
  if p_mode = 'self' and (select home_airport from companies where user_id = uid) is null then raise exception 'no home airport'; end if;
  update companies set ground = p_mode where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_ground(text) from public, anon;
grant execute on function public.co3_set_ground(text) to authenticated;

do $do$
declare src text; n0 text;
begin
  -- 旅客の便：乗員の割合まで・地上の仕事
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_people_fl' in src) = 0 then
    n0 := src;
    src := replace(src, 'co3_slot_fl(p_uid, e.fl0, e.a, e.b) as fl,', 'co3_people_fl(p_uid, e.fl0, e.a, e.b) as fl,');
    src := replace(src, 'k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) * co3.meal_cost_mult(k2.policy, k2.meal) as cst,',
                        'k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) * co3.meal_cost_mult(k2.policy, k2.meal) * co3_ground_mult(p_uid, k2.a, k2.b) as cst,');
    if src = n0 or position('co3_ground_mult' in src) = 0 or position('co3_people_fl' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、乗員と地上の仕事を入れられない'; end if;
    execute src;
  end if;
  -- 貨物機の便
  select pg_get_functiondef('public.co3_cargo_econ(uuid)'::regprocedure) into src;
  if position('co3_people_fl' in src) = 0 then
    n0 := src;
    src := replace(src, 'co3_slot_fl(p_uid, least(', 'co3_people_fl(p_uid, least(');
    src := replace(src, 'k.fl * k.payload * k.eq * 0.35 * co3.fare(k.km) as cst,', 'k.fl * k.payload * k.eq * 0.35 * co3.fare(k.km) * co3_ground_mult(p_uid, k.a, k.b) as cst,');
    if src = n0 or position('co3_ground_mult' in src) = 0 then raise exception 'co3_cargo_econ の形が変わっていて、乗員と地上の仕事を入れられない'; end if;
    execute src;
  end if;
  -- 整備士の不足で故障が増える
  select pg_get_functiondef('public.co3_breakdown_rate(bigint)'::regprocedure) into src;
  if position('co3_mech_mult' in src) = 0 then
    if position($r$* case when c.roles ? 'maint'$r$ in src) = 0 then raise exception 'co3_breakdown_rate の形が変わっていて、整備士を入れられない'; end if;
    src := replace(src, $r$* case when c.roles ? 'maint'$r$, $r$* co3_mech_mult(a.user_id)
         * case when c.roles ? 'maint'$r$);
    execute src;
  end if;
  -- 維持費に人の給料を足す
  select pg_get_functiondef('public.co_upkeep(uuid)'::regprocedure) into src;
  if position('co3_people_cost' in src) = 0 then
    n0 := src;
    src := replace(src, 'then coalesce(round(sum(co3_ac_upkeep(id))), 0)::bigint', 'then coalesce(round(sum(co3_ac_upkeep(id))), 0)::bigint + round(co3_people_cost(p_uid))::bigint');
    if src = n0 then raise exception 'co_upkeep の形が変わっていて、人の給料を入れられない'; end if;
    execute src;
  end if;
  -- 会社の状態：人
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_people_need' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、人を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'people', case when v3 then (select jsonb_build_object('need', co3_people_need(uid), 'crew', h.crew, 'mech', h.mech,
        'crew_hired', c.crew_hired, 'mech_hired', c.mech_hired, 'ground', c.ground, 'cost', co3_people_cost(uid),
        'crew_ratio', co3_crew_ratio(uid), 'mech_mult', co3_mech_mult(uid)) from co3_people_have(uid) h) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
