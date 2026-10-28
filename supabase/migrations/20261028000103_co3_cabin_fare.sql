-- エアライン経営 co-v3：上級席と、運賃での取り合い（仕様書 10/24〜26）
--   上級席：方針ごとに選べる割合（LCC 0%＝席を詰めて ×1.12、ミドルコスト 0・10%、FSC 0・10・20・30%）。
--           上級席1席は普通席2席分（中型以上は3席分）の場所を使い、運賃は普通席の4.5倍（中型以上5.6倍）。
--           上級席の客は仕事の客の 12%（大きい空港どうし・国際線）・6%（ほか）・2%（小規模の空港がからむ）
--   運賃での取り合い：同じ路線の会社のあいだで、仕事の客は 1/運賃、旅行の客は 1/運賃³ の割合で分ける。
--           客の総数は会社の数で増える（1＋0.5×(n−1)、最大3倍）。同じ方針どうしなら前と同じ（2社で75%ずつ）

alter table public.companies add column if not exists premium smallint check (premium in (0, 10, 20, 30));  -- null は方針のはじめの値

-- 方針ごとに選べる上級席の割合と、はじめの値（FSC 20%・ミドルコスト 10%・LCC 0%）
create or replace function co3.premium_ok(p_policy text, p_pct integer) returns boolean
language sql immutable as $$
  select case p_policy when 'lcc' then p_pct = 0 when 'mcc' then p_pct in (0, 10) else p_pct in (0, 10, 20, 30) end
$$;
create or replace function co3.premium_default(p_policy text) returns integer
language sql immutable as $$ select case p_policy when 'fsc' then 20 when 'mcc' then 10 else 0 end $$;

-- 席の配置：全席普通のときの席（機種の表）から、上級席と普通席の数。LCC は詰めて ×1.12
create or replace function co3.cabin(p_seats numeric, p_policy text, p_pct integer, p_wide boolean, out premium numeric, out economy numeric)
language sql immutable as $$
  select pr, s - k * pr from (
    select s, k, case when pct = 0 then 0 else floor(s * pct / (1 + (k - 1) * pct)) end as pr
      from (select p_seats * case when p_policy = 'lcc' then 1.12 else 1 end as s,
                   case when p_wide then 3 else 2 end as k, p_pct / 100.0 as pct) t) u
$$;

-- 上級席の客の割合（仕事の客のうち）
create or replace function co3.premium_share(p_kind text, p_intl boolean, p_small boolean) returns numeric
language sql immutable as $$ select case when p_small then 0.02 when p_intl or p_kind = 'big' then 0.12 else 0.06 end $$;

-- 上級席の運賃（普通席に対して）
create or replace function co3.premium_fare(p_wide boolean) returns numeric
language sql immutable as $$ select case when p_wide then 5.6 else 4.5 end $$;

create or replace function public.co3_set_premium(p_pct integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); pol text;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select policy into pol from companies where user_id = uid;
  if p_pct is not null and not co3.premium_ok(pol, p_pct) then raise exception 'premium not allowed'; end if;
  update companies set premium = p_pct where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_premium(integer) from public, anon;
grant execute on function public.co3_set_premium(integer) to authenticated;

-- 方針を変えたとき、その方針で選べない上級席の割合ははじめの値に戻す
create or replace function public.co3_set_policy(p_policy text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  if p_policy not in ('fsc', 'mcc', 'lcc') then raise exception 'invalid policy'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  update companies set policy = p_policy,
         premium = case when premium is not null and co3.premium_ok(p_policy, premium) then premium end
   where user_id = uid;
  return co_state();
end;
$$;

-- 路線ごとの内わけ（返す列が増えるので作り直す）
drop function if exists public.co3_route_econ(uuid);
create or replace function public.co3_route_econ(p_uid uuid)
returns table (route_key text, a text, b text, km numeric, intl boolean, kind text, real_flights numeric,
               demand numeric, companies integer, own_pax numeric, flights integer, seats numeric, carried numeric,
               revenue numeric, cost numeric, landing numeric, congestion numeric, profit numeric,
               premium_seats numeric, premium_pax numeric, economy_pax numeric)
language sql stable security definer set search_path = public, ops as $$
  with c as (
    select c.*, (now() at time zone 'Asia/Tokyo')::date - (c.created_at at time zone 'Asia/Tokyo')::date + 1 as day_no,
           ha.iata as home_iata, coalesce(c.premium, co3.premium_default(c.policy)) as pct
      from companies c left join airports ha on ha.id = c.home_airport where c.user_id = p_uid
  ), r as (
    select x.route_key, x.a, x.b, x.km, x.intl, x.ac_id, x.ac_type, x.sky, x.hub_mult,
           least(x.a, x.b) as la, greatest(x.a, x.b) as lb
      from co_routes(p_uid) x
  ), tot as (select sum(dom_pax)::numeric as t from co3_airport_stats),
  active as (select count(*)::int as n from companies where last_collect > now() - interval '30 days'),
  req as (
    select ap.iata, sum(coalesce(p.flights, co3.legs_per_day(coalesce(f.distance_km, 800)::numeric))) as total
      from aircraft ac
      join lateral (select split_part(ac.route_key, '-', 1) as x, split_part(ac.route_key, '-', 2) as y) k on true
      left join co3_plans p on p.user_id = ac.user_id and p.route_key = ac.route_key
      left join lateral (select max(distance_km) as distance_km from flights fl
                          where fl.user_id = ac.user_id and least(fl.from_airport, fl.to_airport) || '-' || greatest(fl.from_airport, fl.to_airport) = ac.route_key) f on true
      join airports ap on ap.iata in ('HND', 'NRT', 'KIX', 'ITM', 'FUK')
       and (ap.iata in (k.x, k.y) or (k.x ~ '^[0-9]+$' and ap.id in (k.x::int, nullif(k.y, '')::int)))
     where ac.route_key is not null
     group by ap.iata
  ), e as (
    select r.*,
           rr.flights as rf,
           case when r.la = c.home_iata or r.lb = c.home_iata then co3.size_of(c.home_iata) end as home_size,
           case when co3.is_resort(r.a) or co3.is_resort(r.b) then 'resort'
                when co3.size_of(r.a) in ('xl', 'hub') and co3.size_of(r.b) in ('xl', 'hub') then 'big' else 'local' end as kind,
           co3.size_of(r.a) = 'small' or co3.size_of(r.b) = 'small' as small_end,
           -- 同じ路線のほかの会社（機体を入れている会社）の数と、運賃の重み
           o.n_other, o.wb_other, o.wl_other,
           coalesce((co3.ac_class_spec(r.ac_type)).seats, 0) as raw_seats,
           r.ac_type in ('wb', 'lg') as wide,
           (co3.ac_class_spec(r.ac_type)).mtow as mtow, (co3.ac_class_spec(r.ac_type)).noise as noise,
           case when r.ac_id is null then 0
                else least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = r.route_key), 99), co3.legs_per_day(r.km)) end as fl0,
           case when rr.flights is not null then co3.route_pax_real(rr.flights, rr.avg_seats)
                else co3.route_pax_nodirect(coalesce(sa.dom_pax, 0), coalesce(sb.dom_pax, 0), (select t from tot), r.km) end as dem0,
           c.policy, c.pct, c.day_no, c.home_since, c.user_id,
           (co3.policy(c.policy)).fare_mult as fm
      from r cross join c
      left join co3_route_real rr on rr.a = r.la and rr.b = r.lb
      left join co3_airport_stats sa on sa.iata = r.a
      left join co3_airport_stats sb on sb.iata = r.b
      cross join lateral (
        select count(*)::int as n_other,
               coalesce(sum(co3.fare_weight((co3.policy(c2.policy)).fare_mult, true)), 0) as wb_other,
               coalesce(sum(co3.fare_weight((co3.policy(c2.policy)).fare_mult, false)), 0) as wl_other
          from (select distinct x.user_id from aircraft x where x.route_key = r.route_key and x.user_id <> p_uid) u
          join companies c2 on c2.user_id = u.user_id) o
  ), f as (
    select e.*,
           least(e.fl0,
                 coalesce((select min(co3.slot_allot(e.fl0, q.total::int, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active))))
                             from req q where q.iata in (e.a, e.b)), e.fl0)) as fl,
           coalesce((select sum(co3.congestion_rate(q.total, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active)),
                                                    q.iata = 'HND' and e.kind <> 'big'))
                       from req q where q.iata in (e.a, e.b)), 0) as cong_rate,
           case e.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end as biz,
           (co3.cabin(e.raw_seats, e.policy, e.pct, e.wide)).premium as p_seats,
           (co3.cabin(e.raw_seats, e.policy, e.pct, e.wide)).economy as e_seats
      from e
  ), g as (
    -- 客の総数を会社の数で増やし、仕事の客は 1/運賃、旅行の客は 1/運賃³ の割合で分ける
    select f.*,
           f.dem0 * co3.route_total_mult(f.n_other + 1) as pool,
           co3.fare_weight(f.fm, true) / (co3.fare_weight(f.fm, true) + f.wb_other) as sb,
           co3.fare_weight(f.fm, false) / (co3.fare_weight(f.fm, false) + f.wl_other) as sl
      from f
  ), g2 as (
    select g.*,
           g.pool * (g.biz * (co3.policy(g.policy)).biz_mult * g.sb + (1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl) as share_pax,
           g.pool * g.biz * (co3.policy(g.policy)).biz_mult * g.sb * co3.premium_share(g.kind, g.intl, g.small_end) as share_prem
      from g
  ), h as (
    select g2.*,
           case when g2.home_size is null then 1
                else co3.local_support(g2.home_size, g2.share_pax, g2.rf is not null,
                                       coalesce((now() at time zone 'Asia/Tokyo')::date - g2.home_since, 0)) / nullif(g2.share_pax, 0) end as boost,
           co3.bonus_mult(co_bonus(g2.user_id) + 0.05 * (rep_stars(co_rep_points(g2.user_id)) - 1), (g2.hub_mult - 1) * 0.6, 0)
             * co3.newbie_mult(g2.day_no) * g2.sky as mult
      from g2
  ), k as (
    select h.*,
           h.share_pax * coalesce(h.boost, 1) as own,
           least(h.share_prem * coalesce(h.boost, 1), h.fl * h.p_seats * 0.85) as car_p
      from h
  ), k2 as (
    select k.*, least(k.own - k.car_p, k.fl * k.e_seats * 0.85) as car_e,
           k.raw_seats * case when k.policy = 'lcc' then 1.12 else 1 end as seats_eq
      from k
  ), m as (
    select k2.*,
           (k2.car_e + k2.car_p * co3.premium_fare(k2.wide)) * co3.fare(k2.km) * k2.fm * k2.mult as rev,
           k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) as cst,
           case when k2.fl > 0 then k2.fl * co3.landing_fee(k2.intl, false, (k2.car_e + k2.car_p) / k2.fl, k2.noise, k2.mtow,
                                                          k2.intl and 'HND' in (k2.a, k2.b), co3.is_island(k2.a) or co3.is_island(k2.b)) else 0 end as lnd
      from k2
  )
  select m.route_key, m.a, m.b, m.km, m.intl, m.kind, round(m.rf::numeric, 1), round(m.dem0, 1), (m.n_other + 1)::int, round(m.own, 1), m.fl::int,
         m.seats_eq, round(m.car_e + m.car_p, 1),
         round(m.rev, 2), round(m.cst, 2), round(m.lnd, 2), round(m.rev * 0.5 * m.cong_rate, 2),
         round(m.rev * (1 - 0.5 * m.cong_rate) - m.cst - m.lnd, 2),
         m.p_seats, round(m.car_p, 1), round(m.car_e, 1)
    from m
$$;
revoke all on function public.co3_route_econ(uuid) from public, anon, authenticated;

-- 会社の状態の econ に上級席の内わけと、premium（上級席の割合）を足す
create or replace function public.co_state() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare
  uid uuid := auth.uid(); c companies; d bigint; g bigint; u bigint; pts bigint; st integer; v3 boolean := coalesce((ops.flag('co_v3'))::boolean, false);
begin
  perform co_check(uid);
  select * into c from companies where user_id = uid;
  g := co_gross(uid); u := co_upkeep(uid); d := g - u; pts := co_rep_points(uid); st := rep_stars(pts);
  return jsonb_build_object(
    'name', c.name, 'cash', c.cash, 'last', c.last_collect, 'roles', c.roles, 'daily', d, 'gross', g, 'upkeep', u,
    'bonus', co_bonus(uid), 'rep_points', pts, 'stars', st, 'rep_bonus', 0.05 * (st - 1),
    'pending', floor(d * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400),
    'total_km', (select coalesce(sum(distance_km), 0) from flights where user_id = uid),
    'bought', c.bought, 'friend_code', c.friend_code, 'hide_rank', c.hide_rank, 'value', co_value(uid),
    'friends', (select count(*) from co_friends where user_id = uid),
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', up_cost(base, level),
                 'min_size', min_size, 'ac', ac_type, 'ac_id', ac_id, 'mult', ac_mult, 'hub', hub_mult, 'sky', sky, 'intl', intl, 'km', km, 'a', a, 'b', b,
                 'sa', size_a, 'sb', size_b)), '[]'::jsonb)
                 from co_routes(uid)),
    'sky', (select coalesce(jsonb_object_agg(s.route_key, jsonb_build_object('day', s.day, 'n', s.n, 'cxl', s.cxl, 'avg4', s.avg4, 'mult', s.mult)), '{}'::jsonb)
              from co_routes(uid) r
              join lateral (select * from co_sky x where x.route_key = r.route_key and x.day >= (now() at time zone 'Asia/Tokyo')::date - 3 order by x.day desc limit 1) s on true
             where not r.intl),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key, 'reg', reg, 'icao', icao, 'intl', intl,
                 'paid', paid, 'age', ac_age(bought_at), 'bought_at', bought_at, 'value', round(paid * ac_age(bought_at)),
                 'sell', round(paid * ac_age(bought_at) * 0.3), 'upkeep', ac_upkeep(type), 'rode_on', rode_on, 'flight', rode_flight) order by id), '[]'::jsonb)
                from aircraft where user_id = uid),
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid),
    'v3', v3, 'policy', c.policy, 'home', c.home_airport, 'home_since', c.home_since,
    'premium', coalesce(c.premium, co3.premium_default(c.policy)),
    'econ', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', e.route_key, 'kind', e.kind, 'real', e.real_flights, 'demand', e.demand,
                 'n', e.companies, 'own', e.own_pax, 'flights', e.flights, 'seats', e.seats, 'carried', e.carried, 'revenue', e.revenue,
                 'cost', e.cost, 'landing', e.landing, 'congestion', e.congestion, 'profit', e.profit,
                 'p_seats', e.premium_seats, 'p_pax', e.premium_pax, 'e_pax', e.economy_pax)), '[]'::jsonb) from co3_route_econ(uid) e) end);
end;
$$;
revoke all on function public.co_state() from public, anon;
grant execute on function public.co_state() to authenticated;
