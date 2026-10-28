-- エアライン経営 co-v3：貨物の会社（仕様書 10/25〜26）
--   ・方針に「貨物」（cargo）を足す。貨物の会社は旅客を運ばない。旅客の会社の貨物機（機体の1割まで）は次の段階
--   ・貨物の路線：空港で見た貨物機が本物で飛んでいる区間（国際線も。海外の空港どうしは除く）と、自分が飛んだ区間
--   ・路線の貨物（1日・トン、両方向）：令和7年の空港管理状況調書の本物の量をそのまま使う
--       国内線：小さいほうの空港の国内の貨物 × 相手の大きさ ÷ その空港の本物の相手の大きさの合計 ÷ 365
--       国際線：日本の空港の国際の貨物 ÷ 365 × その区間の本物の便 ÷ その空港の国際線の本物の便（前の28日）
--     旅客の会社の床下が3割まで取るので、貨物機の分は7割。貨物の会社どうしは、その路線に貨物機を入れている会社の数で分ける
--   ・稼ぎ：運べる重さ（積める重さ × 便 × 85%まで）× 1トンの席分（国内2.5・国際線4）× 運賃 × はじめの上乗せ × 上乗せの3つの組
--     費用：積み込み率35%で赤字になる額。着陸料は重さの額（羽田の国際線は割高）。混雑料金は旅客と同じ
--   ・距離：国内線は空港の位置から。海外の空港は位置を持っていないので、本物の便の飛ぶ時間から（（飛ぶ時間 − 30分）× 時速820km）
--   まだ入れていないもの：混雑空港での貨物機の発着枠の分け方（今は混雑料金だけ）

alter table public.companies drop constraint if exists companies_policy_check;
alter table public.companies add constraint companies_policy_check check (policy in ('fsc', 'mcc', 'lcc', 'cargo'));

-- 方針の数字に貨物を足す（旅客の客は取らない、赤字の線は35%）
create or replace function co3.policy(p text,
  out fare_mult numeric, out breakeven numeric, out biz_mult numeric, out leisure_mult numeric, out premium_share numeric)
language sql immutable as $$
  select f, b, bz, ls, pr from (values
    ('fsc', 1.00, 0.50, 1.0, 0.85, 0.2),
    ('mcc', 0.85, 0.45, 1.1, 1.15, 0.1),
    ('lcc', 0.72, 0.40, 0.4, 1.70, 0.0),
    ('cargo', 1.00, 0.35, 0.0, 0.00, 0.0)
  ) t(k, f, b, bz, ls, pr) where k = p
$$;

create or replace function public.co3_set_policy(p_policy text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  if p_policy not in ('fsc', 'mcc', 'lcc', 'cargo') then raise exception 'invalid policy'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  update companies set policy = p_policy,
         premium = case when premium is not null and co3.premium_ok(p_policy, premium) then premium end
   where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co3_is_freighter(p_aircraft bigint) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select t.kind = 'freighter' from aircraft a join co3_types t on t.code = coalesce(a.co3_code, co3_type_of(a.icao)) where a.id = p_aircraft), false)
$$;
revoke all on function public.co3_is_freighter(bigint) from public, anon, authenticated;

-- 2つの空港の距離（km）。両方とも日本の空港なら位置から、海外の空港が入るなら本物の便の飛ぶ時間から
create or replace function public.co3_km(p_a text, p_b text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select round((6371 * 2 * asin(sqrt(power(sin(radians(y.lat - x.lat) / 2), 2)
                   + cos(radians(x.lat)) * cos(radians(y.lat)) * power(sin(radians(y.lon - x.lon) / 2), 2))))::numeric)
       from airports x, airports y where x.iata = p_a and y.iata = p_b limit 1),
    (select round(greatest(300, (extract(epoch from avg(h.sta - h.std)) / 60 - 30) / 60 * 820))::numeric
       from flight_history h where ((h.dep = p_a and h.arr = p_b) or (h.dep = p_b and h.arr = p_a))
        and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 60 and h.sta > h.std))
$$;
revoke all on function public.co3_km(text, text) from public, anon, authenticated;

-- 見た機体の、見たときの便すべて（co3_seen は登録記号ごとに1つにまとめたもの）
create or replace function public.co3_seen_flights(p_uid uuid)
returns table (reg text, code text, kind text, dep text, arr text, flight text, seen_at timestamptz)
language sql stable security definer set search_path = public as $$
  with ch as (
    select c.created_at, a.iata from checkins c join airports a on a.id = c.airport_id
     where c.user_id = p_uid and not ('impossible_speed' = any (c.flags)) and a.iata ~ '^[A-Z]{3}$'
     order by c.created_at desc limit 500
  )
  select h.reg, co3_seen_code(h.flight, h.type, h.aircraft), t.kind, h.dep, h.arr, h.flight, ch.created_at
    from ch join flight_history h
      on h.svc_date between (ch.created_at at time zone 'Asia/Tokyo')::date - 1 and (ch.created_at at time zone 'Asia/Tokyo')::date + 1
     and ((h.dep = ch.iata and coalesce(h.atd, h.std) between ch.created_at - interval '45 minutes' and ch.created_at + interval '45 minutes')
       or (h.arr = ch.iata and coalesce(h.ata, h.sta) between ch.created_at - interval '45 minutes' and ch.created_at + interval '45 minutes'))
    join co3_types t on t.code = co3_seen_code(h.flight, h.type, h.aircraft)
   where h.reg ~ '^[A-Z0-9-]{3,10}$' and not h.cancelled
$$;
revoke all on function public.co3_seen_flights(uuid) from public, anon, authenticated;

-- 貨物の路線：見た貨物機の区間（海外の空港どうしは除く）と、自分が飛んだ区間
create or replace function public.co3_cargo_routes(p_uid uuid)
returns table (route_key text, a text, b text, intl boolean, km numeric, seen boolean)
language sql stable security definer set search_path = public as $$
  with s as (
    select distinct least(f.dep, f.arr) as a, greatest(f.dep, f.arr) as b
      from co3_seen_flights(p_uid) f
     where f.kind = 'freighter' and (exists (select 1 from airports where iata = f.dep) or exists (select 1 from airports where iata = f.arr))
  ), sk as (
    select case when xa.id is not null and ya.id is not null then least(xa.id, ya.id) || '-' || greatest(xa.id, ya.id) else s.a || '-' || s.b end as k,
           s.a, s.b, (xa.id is null or ya.id is null) as intl
      from s
      left join lateral (select id from airports where iata = s.a order by id limit 1) xa on true
      left join lateral (select id from airports where iata = s.b order by id limit 1) ya on true
  ), f as (select r.route_key, least(r.a, r.b) as a, greatest(r.a, r.b) as b, r.intl, r.km from co_routes(p_uid) r)
  select distinct on (k) k, a, b, intl, km, seen from (
    select sk.k, sk.a, sk.b, sk.intl, co3_km(sk.a, sk.b) as km, true as seen from sk
    union all
    select f.route_key, f.a, f.b, f.intl, f.km, false from f
  ) u where km is not null
  order by k, seen
$$;
revoke all on function public.co3_cargo_routes(uuid) from public, anon, authenticated;

-- 路線の貨物（1日・トン、両方向、床下を含む全部）
create or replace function public.co3_cargo_tons(p_a text, p_b text) returns numeric
language sql stable security definer set search_path = public as $$
  with j as (select iata, dom_cargo_t, intl_cargo_t from co3_airport_stats),
  dom as (
    -- 小さいほうの空港と、その空港の本物の国内線の相手
    select s.iata as small, l.iata as large, s.dom_cargo_t as st, l.dom_cargo_t as lt
      from j s, j l
     where s.iata in (p_a, p_b) and l.iata in (p_a, p_b) and s.iata <> l.iata
       and (s.dom_cargo_t < l.dom_cargo_t or (s.dom_cargo_t = l.dom_cargo_t and s.iata < l.iata))
  )
  select case
    when exists (select 1 from airports where iata = p_a) and exists (select 1 from airports where iata = p_b) then
      (select case when d.st = 0 or d.lt = 0 then 0
                   else co3.cargo_dom_route(d.st, d.lt, greatest(d.lt,
                          (select coalesce(sum(p.dom_cargo_t), 0) from co3_route_real r join j p on p.iata = case when r.a = d.small then r.b else r.a end
                            where d.small in (r.a, r.b) and exists (select 1 from airports where iata = r.a) and exists (select 1 from airports where iata = r.b)))) end
         from dom d)
    else
      (select co3.cargo_intl_route(jj.intl_cargo_t,
                coalesce((select flights from co3_route_real where a = least(p_a, p_b) and b = greatest(p_a, p_b)), 0),
                (select sum(r.flights) from co3_route_real r
                  where jj.iata in (r.a, r.b) and not exists (select 1 from airports where iata = case when r.a = jj.iata then r.b else r.a end)))
         from j jj where jj.iata in (p_a, p_b) limit 1)
  end
$$;
revoke all on function public.co3_cargo_tons(text, text) from public, anon, authenticated;

-- 貨物の路線ごとの1日の内わけ（貨物機を入れた路線）
create or replace function public.co3_cargo_econ(p_uid uuid)
returns table (route_key text, a text, b text, km numeric, intl boolean, tons numeric, companies integer, flights integer,
               payload numeric, carried numeric, revenue numeric, cost numeric, landing numeric, congestion numeric, profit numeric, aircraft_id bigint)
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
    select cr.*, ac.id as ac_id, (co3_ac_spec(ac.id)).seats as payload, (co3_ac_spec(ac.id)).mtow as mtow, (co3_ac_spec(ac.id)).noise as noise,
           co3_cargo_tons(cr.a, cr.b) * 0.7 as t70,
           (select count(distinct x.user_id) from aircraft x where x.route_key = cr.route_key and co3_is_freighter(x.id))::int as n,
           least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = cr.route_key), 99), co3.legs_per_day(cr.km)) as fl,
           coalesce((select sum(co3.congestion_rate(q.total, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active)), false))
                       from req q where q.iata in (cr.a, cr.b)), 0) as cong_rate,
           co3.bonus_mult(co_bonus(p_uid) + 0.05 * (rep_stars(co_rep_points(p_uid)) - 1), 0, 0) * co3.newbie_mult(c.day_no) * co3_ac_earn(ac.id) as mult
      from co3_cargo_routes(p_uid) cr
      join aircraft ac on ac.user_id = p_uid and ac.route_key = cr.route_key and co3_is_freighter(ac.id)
      cross join c
  ), k as (
    select r.*, least(r.t70 / greatest(r.n, 1), r.fl * r.payload * 0.85) as car, co3.cargo_seat_eq(r.intl) as eq from r
  ), m as (
    select k.*,
           k.car * k.eq * co3.fare(k.km) * k.mult as rev,
           k.fl * k.payload * k.eq * 0.35 * co3.fare(k.km) as cst,
           k.fl * co3.landing_fee(k.intl, true, 0, k.noise, k.mtow, k.intl and 'HND' in (k.a, k.b), co3.is_island(k.a) or co3.is_island(k.b)) as lnd
      from k
  )
  select m.route_key, m.a, m.b, m.km, m.intl, round(m.t70, 1), m.n, m.fl, m.payload, round(m.car, 1),
         round(m.rev, 2), round(m.cst, 2), round(m.lnd, 2), round(m.rev * 0.5 * m.cong_rate, 2),
         round(m.rev * (1 - 0.5 * m.cong_rate) - m.cst - m.lnd, 2), m.ac_id
    from m
$$;
revoke all on function public.co3_cargo_econ(uuid) from public, anon, authenticated;

-- 1日の収益：旅客の路線と貨物の路線の合計
create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select (coalesce((select round(sum(profit)) from co3_route_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_cargo_econ(p_uid)), 0))::bigint
$$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

-- 旅客の路線では、貨物機と、貨物の会社の機体は飛ばない
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_is_freighter' in src) = 0 then
    src := replace(src, 'case when r.ac_id is null then 0', 'case when r.ac_id is null or co3_is_freighter(r.ac_id) or c.policy = ''cargo'' then 0');
    if position('co3_is_freighter' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、貨物機を外せない'; end if;
    execute src;
  end if;
end
$do$;

-- 貨物機を貨物の路線に入れる（null で外す）
create or replace function public.co3_cargo_assign(p_aircraft bigint, p_route text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); r record; t co3_types;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not co3_is_freighter(p_aircraft) or not exists (select 1 from aircraft where id = p_aircraft and user_id = uid) then raise exception 'not a freighter'; end if;
  if p_route is not null then
    select * into r from co3_cargo_routes(uid) where route_key = p_route;
    if not found then raise exception 'route not found'; end if;
    select x.* into t from aircraft a join co3_types x on x.code = coalesce(a.co3_code, co3_type_of(a.icao)) where a.id = p_aircraft;
    if r.km > t.range_km then raise exception 'too far'; end if;
    update aircraft set route_key = null where user_id = uid and route_key = p_route and id <> p_aircraft;
  end if;
  update aircraft set route_key = p_route where id = p_aircraft;
  return co_state();
end;
$$;
revoke all on function public.co3_cargo_assign(bigint, text) from public, anon;
grant execute on function public.co3_cargo_assign(bigint, text) to authenticated;

-- 会社の状態に貨物の路線と内わけを足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_cargo_econ' in src) = 0 then
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'cargo_routes', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', x.route_key, 'a', x.a, 'b', x.b, 'intl', x.intl, 'km', x.km, 'seen', x.seen)), '[]'::jsonb) from co3_cargo_routes(uid) x) end,
    'cargo', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', e.route_key, 'a', e.a, 'b', e.b, 'km', e.km, 'intl', e.intl, 'tons', e.tons,
                 'n', e.companies, 'flights', e.flights, 'payload', e.payload, 'carried', e.carried, 'revenue', e.revenue, 'cost', e.cost,
                 'landing', e.landing, 'congestion', e.congestion, 'profit', e.profit, 'ac_id', e.aircraft_id)), '[]'::jsonb) from co3_cargo_econ(uid) e) end,
    'satisfaction', c.satisfaction,$r$);
    if position('co3_cargo_econ' in src) = 0 then raise exception 'co_state の形が変わっていて、貨物を入れられない'; end if;
    execute src;
  end if;
end
$do$;
