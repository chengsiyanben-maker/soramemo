-- エアライン経営 co-v3：1日の収益を仕様書（10/26）の計算に切り替える
--   運営のスイッチ ops.flags の co_v3 が true のときだけ、co_gross（1日の収益）と co_state（会社の状態）が新しい計算を使う。
--   false（はじめ）のあいだは co-v2 のまま。画面の作りは変えず、co_state に 'v3' と 'econ'（路線ごとの内わけ）を足す。
--   新しい計算：路線の客（本物の便の数か、空港の旅客数）→ 方針の客の取り方 → 会社の数で取り合い → 地元の応援
--             → 運べる席まで → 運賃 × はじめの上乗せ × 上乗せの3つの組 × 実際の空（その日の便数・欠航）
--             − 運航の費用 − 着陸料 − 混雑料金
--   まだ入れていないもの（次の段階）：上級席・運賃を変えたときの取り合い・発着枠の申し込みの画面・貨物・プライベート・地域航空の仕事

-- ---------- 空港の統計（国土交通省「空港管理状況調書」、毎年入れ替える）----------
create table if not exists public.co3_airport_stats (
  iata         text primary key check (iata ~ '^[A-Z]{3}$'),
  year         integer not null,
  pax          bigint not null check (pax >= 0),        -- 乗降客数（国内＋国際、人/年）
  dom_pax      bigint not null check (dom_pax >= 0),    -- 乗降客数（国内）
  dom_cargo_t  bigint not null default 0,               -- 貨物（国内、積＋卸、トン/年）
  intl_cargo_t bigint not null default 0                -- 貨物（国際）
);
alter table public.co3_airport_stats enable row level security;
revoke all on public.co3_airport_stats from public, anon, authenticated;
grant select on public.co3_airport_stats to anon, authenticated;
drop policy if exists "airport stats are public" on public.co3_airport_stats;
create policy "airport stats are public" on public.co3_airport_stats for select to anon, authenticated using (true);

-- 出どころ：国土交通省「令和7年（暦年）空港別順位表」https://www.mlit.go.jp/koku/content/002016479.xlsx
-- 統計の名前と空港の記号が合わなかったもの（アプリの空港の一覧にない）：調布・新島・神津島・米沢H・岡南・栃木H・奈良県H
insert into public.co3_airport_stats (iata, year, pax, dom_pax, dom_cargo_t, intl_cargo_t) values
('AGJ', 2025, 941, 941, 0, 0),
('AKJ', 2025, 1223151, 1160100, 4033, 0),
('AOJ', 2025, 1329031, 1241896, 566, 0),
('ASJ', 2025, 876044, 876044, 638, 0),
('AXJ', 2025, 35679, 35679, 0, 0),
('AXT', 2025, 1290305, 1257846, 562, 0),
('CTS', 2025, 25849752, 21493654, 147687, 9877),
('FKJ', 2025, 53, 53, 0, 0),
('FKS', 2025, 280420, 247189, 9, 0),
('FSZ', 2025, 734490, 467884, 86, 173),
('FUJ', 2025, 175098, 175098, 113, 0),
('FUK', 2025, 28396908, 19261948, 119503, 38022),
('GAJ', 2025, 368401, 368401, 7, 0),
('HAC', 2025, 214081, 214071, 796, 0),
('HIJ', 2025, 2933923, 2487401, 10037, 17),
('HKD', 2025, 2020921, 1844940, 3645, 0),
('HNA', 2025, 499766, 463021, 164, 0),
('HND', 2025, 91542534, 67213224, 476065, 742846),
('HSG', 2025, 628786, 471791, 222, 0),
('HTR', 2025, 964, 964, 0, 0),
('IBR', 2025, 828870, 737336, 11, 151),
('IEJ', 2025, 378, 378, 0, 0),
('IKI', 2025, 30859, 30859, 0, 0),
('ISG', 2025, 2871083, 2759714, 16945, 0),
('ITM', 2025, 16175048, 16175048, 92584, 0),
('IWJ', 2025, 145458, 145458, 0, 0),
('IWK', 2025, 543964, 543964, 304, 0),
('IZO', 2025, 1137979, 1136810, 410, 0),
('KCZ', 2025, 1634699, 1600105, 1931, 0),
('KIJ', 2025, 1143193, 1048306, 59, 4),
('KIX', 2025, 34062645, 6571307, 9034, 777780),
('KJP', 2025, 175, 175, 0, 0),
('KKJ', 2025, 1236950, 1113733, 32378, 10451),
('KKX', 2025, 83466, 83466, 91, 0),
('KMI', 2025, 3354099, 3276030, 3855, 0),
('KMJ', 2025, 3854269, 3211042, 7881, 98),
('KMQ', 2025, 1509415, 1256537, 806, 1875),
('KOJ', 2025, 5820535, 5599012, 16177, 424),
('KTD', 2025, 20243, 20243, 121, 0),
('KUH', 2025, 788641, 788641, 1471, 0),
('KUM', 2025, 202028, 202028, 72, 0),
('MBE', 2025, 75566, 75566, 1, 0),
('MMB', 2025, 843324, 843324, 772, 0),
('MMD', 2025, 38659, 38659, 253, 0),
('MMJ', 2025, 259841, 259244, 0, 0),
('MMY', 2025, 2023023, 2023023, 15506, 0),
('MSJ', 2025, 375049, 375049, 308, 0),
('MYE', 2025, 28408, 28408, 12, 0),
('MYJ', 2025, 3283785, 2898553, 5576, 0),
('NGO', 2025, 11643095, 6229794, 9776, 131444),
('NGS', 2025, 3215977, 3156063, 5667, 6),
('NKM', 2025, 918668, 918327, 0, 0),
('NRT', 2025, 41140408, 7185885, 23619, 2039731),
('NTQ', 2025, 122729, 122729, 4, 0),
('OBO', 2025, 694945, 669654, 485, 0),
('OGN', 2025, 117340, 117340, 397, 0),
('OIM', 2025, 25606, 25606, 0, 0),
('OIR', 2025, 15159, 15159, 0, 0),
('OIT', 2025, 1940837, 1843883, 2997, 0),
('OKA', 2025, 23174996, 19148883, 177597, 3207),
('OKD', 2025, 585892, 585892, 2, 0),
('OKE', 2025, 112068, 112068, 60, 0),
('OKI', 2025, 75915, 75915, 0, 0),
('OKJ', 2025, 1470690, 1179647, 3293, 0),
('ONJ', 2025, 199618, 199618, 115, 0),
('RIS', 2025, 60021, 60021, 0, 0),
('RNJ', 2025, 92980, 92980, 46, 0),
('SDJ', 2025, 3969910, 3341659, 1278, 7),
('SHB', 2025, 238339, 238339, 153, 0),
('SHI', 2025, 493544, 400048, 135, 0),
('SHM', 2025, 247604, 246313, 14, 0),
('SYO', 2025, 374368, 373704, 452, 0),
('TAK', 2025, 2238459, 1716722, 2704, 0),
('TJH', 2025, 39946, 39946, 0, 0),
('TKN', 2025, 199574, 199574, 119, 0),
('TKS', 2025, 1116425, 1057252, 1149, 0),
('TNE', 2025, 113312, 113312, 129, 0),
('TOY', 2025, 382610, 342458, 223, 0),
('TRA', 2025, 51153, 51153, 305, 0),
('TSJ', 2025, 244795, 244795, 120, 0),
('TTJ', 2025, 417082, 417082, 287, 0),
('UBJ', 2025, 886411, 878827, 1555, 0),
('UEO', 2025, 218936, 218936, 1179, 0),
('UKB', 2025, 4059867, 3654610, 0, 0),
('WKJ', 2025, 187273, 187273, 35, 0),
('YGJ', 2025, 735625, 621198, 570, 0)
on conflict (iata) do update set year = excluded.year, pax = excluded.pax, dom_pax = excluded.dom_pax,
  dom_cargo_t = excluded.dom_cargo_t, intl_cargo_t = excluded.intl_cargo_t;

-- ---------- 本物の便（前の28日、路線ごと）----------
--   ODPT・機体の位置の記録から作る数字なので、だれにも読ませない（生のデータを配らない決まり）
create table if not exists public.co3_route_real (
  a          text not null check (a ~ '^[A-Z]{3}$'),
  b          text not null check (b ~ '^[A-Z]{3}$' and b > a),
  flights    numeric not null,       -- 1日の便（両方向、欠航を除く）
  avg_seats  numeric not null,       -- 平均の座席（機種の大きさから）
  days       integer not null,
  updated_at timestamptz not null default now(),
  primary key (a, b)
);
alter table public.co3_route_real enable row level security;
revoke all on public.co3_route_real from public, anon, authenticated;

-- ---------- 会社：方針・本拠地 ----------
alter table public.companies add column if not exists policy text not null default 'fsc' check (policy in ('fsc', 'mcc', 'lcc'));
alter table public.companies add column if not exists home_airport integer references public.airports(id);
alter table public.companies add column if not exists home_since date;

-- ---------- 路線の1日の便数（会社が決める。決めていなければ機体が1日に飛べるだけ）----------
create table if not exists public.co3_plans (
  user_id    uuid not null references auth.users(id) on delete cascade,
  route_key  text not null check (route_key ~ '^([0-9]+-[0-9]+|[A-Z]{3}-[A-Z]{3})$'),
  flights    integer not null check (flights between 0 and 40 and flights % 2 = 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, route_key)
);
alter table public.co3_plans enable row level security;
revoke all on public.co3_plans from public, anon, authenticated;
grant select on public.co3_plans to authenticated;
drop policy if exists "own plans" on public.co3_plans;
create policy "own plans" on public.co3_plans for select to authenticated using (user_id = auth.uid());

insert into ops.flags (key, value) values ('co_v3', 'false') on conflict (key) do nothing;

-- ---------- 機体の大きさごとの数字（作るときに機種の表へ置き換える）----------
--   席・最大の重さ（トン）・騒音の区分・翼の幅の区分
create or replace function co3.ac_class_spec(p_cls text, out seats numeric, out mtow numeric, out noise text, out wing text)
language sql immutable as $$
  select s, m, n, w from (values
    ('prop',  70,  23, 'prop', 'C'),
    ('rj',    90,  45, 'jet',  'C'),
    ('nb',   170,  79, 'jet',  'C'),
    ('wb',   260, 190, 'wide', 'E'),
    ('lg',   350, 300, 'wide', 'E')
  ) t(c, s, m, n, w) where c = p_cls
$$;

-- 離島の空港（着陸料が半分）と、リゾートの空港（旅行の客が多い）
create or replace function co3.is_island(p_iata text) returns boolean
language sql immutable as $$
  select p_iata = any (array['RIS','RBJ','OIR','OIM','MYE','HAC','SDS','OKI','TSJ','FUJ','IKI','TNE','KUM','ASJ','KKX','TKN','OKE','RNJ',
                             'AGJ','UEO','KJP','MMD','KTD','IEJ','MMY','SHI','TRA','ISG','HTR','OGN'])
$$;
create or replace function co3.is_resort(p_iata text) returns boolean
language sql immutable as $$ select p_iata = any (array['OKA','ISG','MMY','SHI','ASJ','HAC','UEO','KUM','OGN','TNE']) $$;

-- 混雑空港の時間値と運用時間（伊丹は1日370回の上限から）
create or replace function co3.slot_hourly(p_iata text) returns numeric
language sql immutable as $$ select case p_iata when 'HND' then 80 when 'NRT' then 72 when 'KIX' then 60 when 'FUK' then 40 when 'ITM' then 370 / 14.0 end $$;
create or replace function co3.slot_hours(p_iata text) returns numeric
language sql immutable as $$ select case p_iata when 'HND' then 17 when 'NRT' then 17 when 'KIX' then 24 when 'FUK' then 15 when 'ITM' then 14 end $$;

-- 空港の大きさ（統計の1日の乗降客数。日本にない空港は拠点）
create or replace function co3.size_of(p_iata text) returns text
language sql stable security definer set search_path = public as $$
  select case when exists (select 1 from airports where iata = p_iata)
              then co3.airport_size(coalesce((select pax from co3_airport_stats where iata = p_iata), 0) / 365.0)
              else 'hub' end
$$;

-- 機体が1日に飛べる便（飛ぶ時間＋折り返し60分で、6〜23時。2〜8便、往復の数）
create or replace function co3.legs_per_day(p_km numeric) returns integer
language sql immutable as $$ select greatest(2, least(8, (floor(17 / (p_km / 820 + 1.33))::int / 2) * 2)) $$;

-- ---------- 毎日の処理：本物の便（前の28日）----------
create or replace function public.co3_route_real_refresh() returns integer
language plpgsql security definer set search_path = public as $$
declare d date := (now() at time zone 'Asia/Tokyo')::date; cnt integer;
begin
  with h as (
    select least(dep, arr) as a, greatest(dep, arr) as b, svc_date,
           coalesce((co3.ac_class_spec(ac_class(coalesce(nullif(type, ''), aircraft)))).seats, 170) as seats
      from flight_history where svc_date >= d - 28 and svc_date < d and not cancelled and dep <> arr
  ), g as (select a, b, round(count(*)::numeric / 28, 2) as flights, round(avg(seats), 1) as seats, count(distinct svc_date)::int as days from h group by a, b)
  insert into co3_route_real (a, b, flights, avg_seats, days, updated_at)
  select a, b, flights, seats, days, now() from g
  on conflict (a, b) do update set flights = excluded.flights, avg_seats = excluded.avg_seats, days = excluded.days, updated_at = now();
  get diagnostics cnt = row_count;
  -- データが止まって30日を超えた路線は消す（本物の便がない路線の式に切り替わる）
  delete from co3_route_real where updated_at < now() - interval '30 days';
  return cnt;
end;
$$;
revoke all on function public.co3_route_real_refresh() from public, anon, authenticated;

-- ---------- 路線ごとの1日の内わけ ----------
create or replace function public.co3_route_econ(p_uid uuid)
returns table (route_key text, a text, b text, km numeric, intl boolean, kind text, real_flights numeric,
               demand numeric, companies integer, own_pax numeric, flights integer, seats numeric, carried numeric,
               revenue numeric, cost numeric, landing numeric, congestion numeric, profit numeric)
language sql stable security definer set search_path = public, ops as $$
  with c as (
    select c.*, (now() at time zone 'Asia/Tokyo')::date - (c.created_at at time zone 'Asia/Tokyo')::date + 1 as day_no,
           ha.iata as home_iata
      from companies c left join airports ha on ha.id = c.home_airport where c.user_id = p_uid
  ), r as (
    select x.route_key, x.a, x.b, x.km, x.intl, x.ac_id, x.ac_type, x.sky, x.hub_mult,
           least(x.a, x.b) as la, greatest(x.a, x.b) as lb
      from co_routes(p_uid) x
  ), tot as (select sum(dom_pax)::numeric as t from co3_airport_stats),
  active as (select count(*)::int as n from companies where last_collect > now() - interval '30 days'),
  -- 混雑空港の、全社の1日の便（申し込み＝スケジュールの便）
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
           ((select count(distinct x.user_id) from aircraft x where x.route_key = r.route_key and x.user_id <> p_uid) + 1)::int as n,
           coalesce((co3.ac_class_spec(r.ac_type)).seats, 0) as seats,
           (co3.ac_class_spec(r.ac_type)).mtow as mtow, (co3.ac_class_spec(r.ac_type)).noise as noise,
           case when r.ac_id is null then 0
                else least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = r.route_key), 99), co3.legs_per_day(r.km)) end as fl0,
           case when rr.flights is not null then co3.route_pax_real(rr.flights, rr.avg_seats)
                else co3.route_pax_nodirect(coalesce(sa.dom_pax, 0), coalesce(sb.dom_pax, 0), (select t from tot), r.km) end as dem0,
           c.policy, c.day_no, c.home_since, c.user_id
      from r cross join c
      left join co3_route_real rr on rr.a = r.la and rr.b = r.lb
      left join co3_airport_stats sa on sa.iata = r.a
      left join co3_airport_stats sb on sb.iata = r.b
  ), f as (
    -- 混雑空港の発着枠：申し込みが枠を超えたら申し込みの割合で分ける（最低4便）
    select e.*,
           least(e.fl0,
                 coalesce((select min(co3.slot_allot(e.fl0, q.total::int, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active))))
                             from req q where q.iata in (e.a, e.b)), e.fl0)) as fl,
           coalesce((select sum(co3.congestion_rate(q.total, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active)),
                                                    q.iata = 'HND' and e.kind <> 'big'))
                       from req q where q.iata in (e.a, e.b)), 0) as cong_rate
      from e
  ), g as (
    select f.*,
           f.dem0 * (case f.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end * (co3.policy(f.policy)).biz_mult
                     + (1 - case f.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end) * (co3.policy(f.policy)).leisure_mult)
             * co3.route_share(f.n) as share_pax
      from f
  ), h as (
    select g.*,
           case when g.home_size is null then g.share_pax
                else co3.local_support(g.home_size, g.share_pax, g.rf is not null,
                                       coalesce((now() at time zone 'Asia/Tokyo')::date - g.home_since, 0)) end as own,
           co3.bonus_mult(co_bonus(g.user_id) + 0.05 * (rep_stars(co_rep_points(g.user_id)) - 1), (g.hub_mult - 1) * 0.6, 0) * co3.newbie_mult(g.day_no) * g.sky as mult
      from g
  ), k as (
    select h.*, least(h.own, h.fl * h.seats * 0.85) as car from h
  )
  select k.route_key, k.a, k.b, k.km, k.intl, k.kind, round(k.rf::numeric, 1), round(k.dem0, 1), k.n::int, round(k.own, 1), k.fl::int, k.seats, round(k.car, 1),
         round(k.car * co3.fare(k.km) * (co3.policy(k.policy)).fare_mult * k.mult, 2) as revenue,
         round(k.fl * co3.flight_cost(k.policy, k.seats, k.km), 2) as cost,
         round(case when k.fl > 0 then k.fl * co3.landing_fee(k.intl, false, k.car / k.fl, k.noise, k.mtow,
                                                              k.intl and 'HND' in (k.a, k.b), co3.is_island(k.a) or co3.is_island(k.b)) else 0 end, 2) as landing,
         round(k.car * co3.fare(k.km) * (co3.policy(k.policy)).fare_mult * k.mult * 0.5 * k.cong_rate, 2) as congestion,
         round(k.car * co3.fare(k.km) * (co3.policy(k.policy)).fare_mult * k.mult * (1 - 0.5 * k.cong_rate)
               - k.fl * co3.flight_cost(k.policy, k.seats, k.km)
               - case when k.fl > 0 then k.fl * co3.landing_fee(k.intl, false, k.car / k.fl, k.noise, k.mtow,
                                                               k.intl and 'HND' in (k.a, k.b), co3.is_island(k.a) or co3.is_island(k.b)) else 0 end, 2) as profit
    from k
$$;
revoke all on function public.co3_route_econ(uuid) from public, anon, authenticated;

create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(round(sum(profit)), 0)::bigint from co3_route_econ(p_uid)
$$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

-- ---------- 切り替え：1日の収益 ----------
--   スイッチがオフなら co-v2 の式（20261028000099_co_v2.sql と同じ）
create or replace function public.co_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public, ops as $$
  select case when coalesce((ops.flag('co_v3'))::boolean, false) then co3_gross(p_uid)
    else (select coalesce(round(sum(base * (1 + 0.25 * (level - 1)) * ac_mult * hub_mult * sky)
                        * (1 + co_bonus(p_uid) + 0.05 * (rep_stars(co_rep_points(p_uid)) - 1))), 0)::bigint
            from co_routes(p_uid)) end
$$;
revoke all on function public.co_gross(uuid) from public, anon, authenticated;

-- ---------- 会社が決めること：方針・本拠地・路線の便数 ----------
create or replace function public.co3_set_policy(p_policy text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  if p_policy not in ('fsc', 'mcc', 'lcc') then raise exception 'invalid policy'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  update companies set policy = p_policy where user_id = uid;
  return co_state();
end;
$$;

-- 本拠地はチェックインしたことがある空港だけ。変えると、地元の応援は30日たってから効く
create or replace function public.co3_set_home(p_airport integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not exists (select 1 from checkins where user_id = uid and airport_id = p_airport) then raise exception 'airport not visited'; end if;
  update companies set home_airport = p_airport, home_since = (now() at time zone 'Asia/Tokyo')::date
   where user_id = uid and home_airport is distinct from p_airport;
  return co_state();
end;
$$;

-- 路線の1日の便数（往復の数、0〜40）。持っている路線だけ。null で「機体が飛べるだけ」に戻す
create or replace function public.co3_set_flights(p_route text, p_flights integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not exists (select 1 from co_routes(uid) where route_key = p_route) then raise exception 'route not found'; end if;
  if p_flights is null then
    delete from co3_plans where user_id = uid and route_key = p_route;
  else
    if p_flights < 0 or p_flights > 40 or p_flights % 2 <> 0 then raise exception 'invalid flights'; end if;
    insert into co3_plans (user_id, route_key, flights) values (uid, p_route, p_flights)
      on conflict (user_id, route_key) do update set flights = excluded.flights, updated_at = now();
  end if;
  return co_state();
end;
$$;

-- ---------- 会社の状態（20261028000100_co_airport_size.sql の co_state に 'v3' と 'econ' を足す）----------
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
    'econ', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', e.route_key, 'kind', e.kind, 'real', e.real_flights, 'demand', e.demand,
                 'n', e.companies, 'own', e.own_pax, 'flights', e.flights, 'seats', e.seats, 'carried', e.carried, 'revenue', e.revenue,
                 'cost', e.cost, 'landing', e.landing, 'congestion', e.congestion, 'profit', e.profit)), '[]'::jsonb) from co3_route_econ(uid) e) end);
end;
$$;

revoke all on function public.co3_set_policy(text), public.co3_set_home(integer), public.co3_set_flights(text, integer), public.co_state() from public, anon;
grant execute on function public.co3_set_policy(text), public.co3_set_home(integer), public.co3_set_flights(text, integer), public.co_state() to authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎日の記録（19:50 UTC）の後に、本物の便（05:25 日本時間）
  execute $q$ select cron.schedule('co3-route-real', '25 20 * * *', $job$ select public.co3_route_real_refresh() $job$) $q$;
end
$outer$;
