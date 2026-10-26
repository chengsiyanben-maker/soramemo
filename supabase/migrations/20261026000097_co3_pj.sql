-- エアライン経営 co-v3：プライベートジェットの会社（仕様書 10/24〜25）
--   ・方針に「プライベートジェット」（pj）を足す。全席 VIP の貸し切り。機体はビジネスジェット（見た機体は乗ったのと同じ扱い）
--   ・路線は自分が飛んだ区間。ビジネスジェットは co_assign（旅客と同じ関数）で路線に入れる
--   ・路線の1日の VIP の客 ＝ その路線の客（1社のとき）× リゾート20%・国際線16%・大きい空港どうし8%・地方4%。
--     会社どうしは旅客と同じく、会社の数で客の総数が増えて分ける（2社で75%ずつ）
--   ・埋まり方 ＝ VIP の客 ÷（VIP 席 × 便）、上限はリゾート90%・国際線80%・大きい空港どうし50%・地方25%
--   ・稼ぎ ＝ VIP 席 × 25（普通席の席分）× 埋まり方 × 運賃 × はじめの上乗せ × 上乗せの3つの組。費用は埋まり方45%で赤字になる額
--   ・便数は、決めていなければ1日に飛べる便のうち、いちばんもうかる数（2便ずつ）

alter table public.companies drop constraint if exists companies_policy_check;
alter table public.companies add constraint companies_policy_check check (policy in ('fsc', 'mcc', 'lcc', 'cargo', 'pj'));

create or replace function co3.policy(p text,
  out fare_mult numeric, out breakeven numeric, out biz_mult numeric, out leisure_mult numeric, out premium_share numeric)
language sql immutable as $$
  select f, b, bz, ls, pr from (values
    ('fsc', 1.00, 0.50, 1.0, 0.85, 0.2),
    ('mcc', 0.85, 0.45, 1.1, 1.15, 0.1),
    ('lcc', 0.72, 0.40, 0.4, 1.70, 0.0),
    ('cargo', 1.00, 0.35, 0.0, 0.00, 0.0),
    ('pj', 1.00, 0.45, 0.0, 0.00, 0.0)
  ) t(k, f, b, bz, ls, pr) where k = p
$$;

create or replace function public.co3_set_policy(p_policy text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  if p_policy not in ('fsc', 'mcc', 'lcc', 'cargo', 'pj') then raise exception 'invalid policy'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  update companies set policy = p_policy,
         premium = case when premium is not null and co3.premium_ok(p_policy, premium) then premium end
   where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co3_is_bizjet(p_aircraft bigint) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select t.kind = 'bizjet' from aircraft a join co3_types t on t.code = coalesce(a.co3_code, co3_type_of(a.icao)) where a.id = p_aircraft), false)
$$;
revoke all on function public.co3_is_bizjet(bigint) from public, anon, authenticated;

-- 路線の客（1社のとき。本物の便か空港の旅客数から）。旅客の内わけと同じ式
create or replace function public.co3_route_pax(p_a text, p_b text, p_km numeric) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select co3.route_pax_real(flights, avg_seats) from co3_route_real where a = least(p_a, p_b) and b = greatest(p_a, p_b)),
    co3.route_pax_nodirect(coalesce((select dom_pax from co3_airport_stats where iata = p_a), 0),
                           coalesce((select dom_pax from co3_airport_stats where iata = p_b), 0),
                           (select sum(dom_pax) from co3_airport_stats), p_km))
$$;
revoke all on function public.co3_route_pax(text, text, numeric) from public, anon, authenticated;

-- プライベートジェットの路線ごとの1日の内わけ
create or replace function public.co3_pj_econ(p_uid uuid)
returns table (route_key text, a text, b text, km numeric, intl boolean, kind text, vip numeric, companies integer, flights integer,
               seats numeric, fill numeric, revenue numeric, cost numeric, landing numeric, congestion numeric, profit numeric, aircraft_id bigint)
language sql stable security definer set search_path = public, ops as $$
  with c as (
    select c.*, (now() at time zone 'Asia/Tokyo')::date - (c.created_at at time zone 'Asia/Tokyo')::date + 1 as day_no
      from companies c where c.user_id = p_uid
  ), active as (select count(*)::int as n from companies where last_collect > now() - interval '30 days'),
  req as (
    select ap.iata, sum(coalesce(p.flights, 4)) as total
      from aircraft ac
      join lateral (select split_part(ac.route_key, '-', 1) as x, split_part(ac.route_key, '-', 2) as y) k on true
      left join co3_plans p on p.user_id = ac.user_id and p.route_key = ac.route_key
      join airports ap on ap.iata in ('HND', 'NRT', 'KIX', 'ITM', 'FUK')
       and (ap.iata in (k.x, k.y) or (k.x ~ '^[0-9]+$' and ap.id in (k.x::int, nullif(k.y, '')::int)))
     where ac.route_key is not null
     group by ap.iata
  ), r as (
    select x.route_key, x.a, x.b, x.km, x.intl, x.hub_mult, ac.id as ac_id,
           (co3_ac_spec(ac.id)).seats as seats, (co3_ac_spec(ac.id)).mtow as mtow, (co3_ac_spec(ac.id)).noise as noise,
           case when x.intl then 'intl' when co3.is_resort(x.a) or co3.is_resort(x.b) then 'resort'
                when co3.size_of(x.a) in ('xl', 'hub') and co3.size_of(x.b) in ('xl', 'hub') then 'big' else 'local' end as kind,
           ((select count(distinct y.user_id) from aircraft y where y.route_key = x.route_key and y.user_id <> p_uid and co3_is_bizjet(y.id)) + 1)::int as n,
           (select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = x.route_key) as plan,
           coalesce((select sum(co3.congestion_rate(q.total, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active)), false))
                       from req q where q.iata in (x.a, x.b)), 0) as cong_rate,
           co3.bonus_mult(co_bonus(p_uid) + 0.05 * (rep_stars(co_rep_points(p_uid)) - 1), (x.hub_mult - 1) * 0.6, 0)
             * co3.newbie_mult(c.day_no) * co3_ac_earn(ac.id) * co3_sat_mult(p_uid) * x.sky as mult
      from co_routes(p_uid) x
      join aircraft ac on ac.user_id = p_uid and ac.route_key = x.route_key and co3_is_bizjet(ac.id)
      cross join c
     where c.policy = 'pj'
  ), v as (
    select r.*, co3.vip_pax(co3_route_pax(r.a, r.b, r.km), r.kind) * co3.route_share(r.n) as vip_pax, co3.vip_fill_cap(r.kind) as cap from r
  ), opt as (
    -- 便数：決めていればその数（飛べる数まで）、なければいちばんもうかる数
    select v.*, f.fl,
           least(v.cap, v.vip_pax / nullif(v.seats * f.fl, 0)) as fl_fill
      from v
      cross join lateral (
        select g as fl from generate_series(2, co3.legs_per_day(v.km), 2) g
         where v.plan is null or g = least(v.plan, co3.legs_per_day(v.km))
         order by g * v.seats * co3.vip_seat_eq() * co3.fare(v.km)
                  * (least(v.cap, v.vip_pax / nullif(v.seats * g, 0)) * v.mult - (co3.policy('pj')).breakeven) desc
         limit 1) f
  ), m as (
    select o.*,
           o.fl * o.seats * co3.vip_seat_eq() * o.fl_fill * co3.fare(o.km) * o.mult as rev,
           o.fl * o.seats * co3.vip_seat_eq() * (co3.policy('pj')).breakeven * co3.fare(o.km) as cst,
           o.fl * co3.landing_fee(o.intl, false, o.seats * o.fl_fill, o.noise, o.mtow, o.intl and 'HND' in (o.a, o.b), co3.is_island(o.a) or co3.is_island(o.b)) as lnd
      from opt o
  )
  select m.route_key, m.a, m.b, m.km, m.intl, m.kind, round(m.vip_pax, 1), m.n, m.fl, m.seats, round(m.fl_fill, 3),
         round(m.rev, 2), round(m.cst, 2), round(m.lnd, 2), round(m.rev * 0.5 * m.cong_rate, 2),
         round(m.rev * (1 - 0.5 * m.cong_rate) - m.cst - m.lnd, 2), m.ac_id
    from m
$$;
revoke all on function public.co3_pj_econ(uuid) from public, anon, authenticated;

create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select (coalesce((select round(sum(profit)) from co3_route_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_cargo_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_pj_econ(p_uid)), 0))::bigint
$$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

-- 旅客の路線では、ビジネスジェットと、プライベートジェットの会社の機体は飛ばない
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_is_bizjet' in src) = 0 then
    src := replace(src, 'case when r.ac_id is null or co3_is_freighter(r.ac_id) or c.policy = ''cargo'' then 0',
                        'case when r.ac_id is null or co3_is_freighter(r.ac_id) or co3_is_bizjet(r.ac_id) or c.policy in (''cargo'', ''pj'') then 0');
    if position('co3_is_bizjet' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、ビジネスジェットを外せない'; end if;
    execute src;
  end if;
end
$do$;

-- 会社の状態にプライベートジェットの内わけを足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_pj_econ' in src) = 0 then
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'pj', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', e.route_key, 'a', e.a, 'b', e.b, 'km', e.km, 'intl', e.intl, 'kind', e.kind,
                 'vip', e.vip, 'n', e.companies, 'flights', e.flights, 'seats', e.seats, 'fill', e.fill, 'revenue', e.revenue, 'cost', e.cost,
                 'landing', e.landing, 'congestion', e.congestion, 'profit', e.profit, 'ac_id', e.aircraft_id)), '[]'::jsonb) from co3_pj_econ(uid) e) end,
    'satisfaction', c.satisfaction,$r$);
    if position('co3_pj_econ' in src) = 0 then raise exception 'co_state の形が変わっていて、プライベートジェットを入れられない'; end if;
    execute src;
  end if;
end
$do$;
