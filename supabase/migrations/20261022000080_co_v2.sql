-- エアライン経営のつくり直し（2026年10月）
--   ・機体は「自分が乗った機体」だけ。便名を入れたフライトを毎日の記録（flight_history）と照らして、登録記号ごとに買えるようになる。
--     登録記号が分からないフライトは、時刻表の機種で「名前のない機体」を1機（フライト1つにつき1機）買える
--   ・飛んだ距離での機体の解放はなくす。はじめの資金は 5,000、最初の1機は半額
--   ・機体のない路線は収益が半分（×0.5）。機体を入れると機体の倍率になる
--   ・機体の維持費（毎日、値段の0.1%）・古さ（会社に入れて90日ごとに −5%、最大 −20%）・売る（いまの値段の3割）
--   ・実際の空：前の日の実際の便の数（いつもの同じ曜日との比べ、±10%まで）と欠航（−10%まで）で、国内線の収益が ±20%まで上下
--   ・国際線の路線：便名を入れた国際線の記録から開く。入れられるのは国際線で乗った機体だけ。海外の空港は大きな空港として数える
--   ・会社の価値のランキング（全国・拠点の空港・友だち。出さない設定もできる）と、友だちの合言葉
--   ・直し：お金を使う・機体を入れるなどの前に、それまでの収益を確定する（後から倍率が上がって昔の分まで増える不具合）
--           役職のボーナスの階級は、チェックインの回数でなく、チェックインした日の数で数える

-- ---------- 機種の記号 → 機体の大きさ（ICAO の記号 B789 も、時刻表の記号 789・73H も） ----------
create or replace function public.ac_class(p text) returns text
language sql immutable as $$
  select case
    when p is null or btrim(p) = '' then null
    when upper(p) ~ '^(DH8|DHC|DH[0-9]|AT[0-9]|ATR|SF3|SB2|Q[0-9]|SW4|B35|BE[0-9]|D28|DO2|BN2|L4T)' then 'prop'
    when upper(p) ~ '^(E1[0-9]|E2[0-9]|E7|E9|ER[0-9J]|CR[0-9A-Z]|MRJ|M90)' then 'rj'
    when upper(p) ~ '^(B73|B3[0-9]M|7M[0-9]|73|A31[89]|A32|A2[01]N|31[89]|32|B75|75|BCS|CS[0-9]|22[0-9])' then 'nb'
    when upper(p) ~ '^(B76|B78|A33|A30|A310|76|78|33)' then 'wb'
    when upper(p) ~ '^(B77|B74|A35|A34|A38|77|74|35|34|38)' then 'lg'
    else null end
$$;

-- 機体の大きさごとの倍率・値段・維持費・就航できる空港の大きさ（距離での解放はなくした。unlock_km は互換のために残すが使わない）
create or replace function public.ac_spec(p_type text, out mult numeric, out price bigint, out unlock_km numeric, out min_size numeric)
language sql immutable as $$
  select mult, price, 0::numeric, min_size from (values
    ('prop', 1.10, 8000::bigint, 1.5::numeric),
    ('rj',   1.25, 15000, 1.5),
    ('nb',   1.50, 25000, 2),
    ('wb',   1.90, 50000, 3),
    ('lg',   2.30, 80000, 3)
  ) as t(ty, mult, price, min_size) where ty = p_type
$$;
create or replace function public.ac_upkeep(p_type text) returns bigint
language sql immutable as $$ select ((ac_spec(p_type)).price / 1000)::bigint $$;
-- 古さ：会社に入れて90日ごとに −5%（最大 −20%）
create or replace function public.ac_age(p_at timestamptz) returns numeric
language sql stable as $$ select greatest(0.8, 1 - 0.05 * floor(extract(epoch from (now() - p_at)) / 86400 / 90))::numeric $$;

-- ---------- 表の変更 ----------
alter table public.companies alter column cash set default 5000;
alter table public.companies add column if not exists bought integer not null default 0;           -- これまでに買った機体の数（最初の1機を半額にする）
alter table public.companies add column if not exists hide_rank boolean not null default false;    -- ランキングに出さない（友だちには出る）
alter table public.companies add column if not exists friend_code text;
update public.companies set friend_code = upper(substr(md5(user_id::text || random()::text), 1, 8)) where friend_code is null;
alter table public.companies alter column friend_code set default upper(substr(md5(gen_random_uuid()::text), 1, 8));
create unique index if not exists companies_friend_code on public.companies (friend_code);

alter table public.aircraft add column if not exists reg text check (reg is null or reg ~ '^[A-Z0-9-]{3,10}$');
alter table public.aircraft add column if not exists icao text check (icao is null or length(icao) <= 8);
alter table public.aircraft add column if not exists ride text check (ride is null or ride ~ '^(r:[A-Z0-9-]{3,10}|f:[0-9]+|i:[0-9]+)$');
alter table public.aircraft add column if not exists intl boolean not null default false;
alter table public.aircraft add column if not exists paid bigint not null default 0;
alter table public.aircraft add column if not exists rode_on date;
alter table public.aircraft add column if not exists rode_flight text check (rode_flight is null or length(rode_flight) <= 10);
create unique index if not exists aircraft_ride on public.aircraft (user_id, ride) where ride is not null;
update public.aircraft set paid = (public.ac_spec(type)).price where paid = 0;
update public.companies c set bought = (select count(*) from public.aircraft a where a.user_id = c.user_id) where bought = 0;

-- 国際線の路線の記号（HND-ICN のように、アルファベット順の空港の記号2つ）
alter table public.aircraft drop constraint if exists aircraft_route_key_check;
alter table public.aircraft add constraint aircraft_route_key_check check (route_key is null or route_key ~ '^([0-9]+-[0-9]+|[A-Z]{3}-[A-Z]{3})$');
alter table public.route_levels drop constraint if exists route_levels_route_key_check;
alter table public.route_levels add constraint route_levels_route_key_check check (route_key ~ '^([0-9]+-[0-9]+|[A-Z]{3}-[A-Z]{3})$');

-- 実際の空：路線（国内線、空港の番号2つ）ごと・日ごとの、実際の便の数と欠航
create table if not exists public.co_sky (
  route_key text not null,
  day       date not null,
  n         integer not null,      -- 飛んだ便
  cxl       integer not null,      -- 欠航
  avg4      real,                  -- 前の4週の同じ曜日の平均（記録がなければ null）
  mult      numeric not null,
  primary key (route_key, day)
);
alter table public.co_sky enable row level security;
revoke all on public.co_sky from public, anon, authenticated;

-- 会社の価値の毎日の記録（ランキング用）
create table if not exists public.co_rank_days (
  day     date not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  value   bigint not null,
  home    integer,
  routes  integer not null,
  fleet   integer not null,
  primary key (day, user_id)
);
create index if not exists co_rank_days_user on public.co_rank_days (user_id, day desc);
alter table public.co_rank_days enable row level security;
revoke all on public.co_rank_days from public, anon, authenticated;

-- 友だち（合言葉を入れると、おたがいに友だちになる）
create table if not exists public.co_friends (
  user_id    uuid not null references auth.users(id) on delete cascade,
  friend_id  uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, friend_id),
  check (user_id <> friend_id)
);
alter table public.co_friends enable row level security;
revoke all on public.co_friends from public, anon, authenticated;

-- ---------- 乗った機体 ----------
-- 便名を入れたフライト（チェックインのフライト・国際線の記録）を、毎日の記録と照らす。
--   ride：r:登録記号（登録記号が分かったもの、何回乗っても1つ）／f:フライトの番号・i:国際線の記録の番号（登録記号が分からず、機種だけ分かったもの）
create or replace function public.co_rides(p_uid uuid)
returns table (ride text, reg text, icao text, cls text, intl boolean, rode_on date, flight text, n integer)
language sql stable security definer set search_path = public as $$
  with fl as (
    (select 'f:' || f.id as fkey, (f.dep_at at time zone 'Asia/Tokyo')::date as d,
            case when f.flight_no ~ '^[0-9]' and f.airline ~ '^[A-Z0-9]{2}$' then f.airline || f.flight_no else f.flight_no end as fno,
            a.iata, false as intl
       from flights f join airports a on a.id = f.from_airport
      where f.user_id = p_uid and f.flight_no is not null and a.iata ~ '^[A-Z]{3}$'
      order by f.dep_at desc limit 500)
    union all
    (select 'i:' || i.id, i.flown_on, i.flight_no, i.dep, true
       from intl_flights i where i.user_id = p_uid and i.flight_no is not null
      order by i.flown_on desc limit 200)
  ), m as (
    select x.fkey, x.d, x.fno, x.intl, h.reg, coalesce(nullif(h.type, ''), h.aircraft) as icao
      from fl x
      join lateral (
        select h.reg, h.type, h.aircraft from flight_history h
         where h.svc_date = x.d and h.dep = x.iata
           and (flight_no_norm(h.flight) = flight_no_norm(x.fno) or exists (select 1 from unnest(h.also) o where flight_no_norm(o) = flight_no_norm(x.fno)))
         order by (flight_no_norm(h.flight) = flight_no_norm(x.fno)) desc limit 1) h on true
     where ac_class(coalesce(nullif(h.type, ''), h.aircraft)) is not null
  )
  select 'r:' || m.reg, m.reg, max(m.icao), ac_class(max(m.icao)), bool_or(m.intl), max(m.d), (array_agg(m.fno order by m.d desc))[1], count(*)::int
    from m where m.reg ~ '^[A-Z0-9-]{3,10}$' group by m.reg
  union all
  select m.fkey, null, m.icao, ac_class(m.icao), m.intl, m.d, m.fno, 1
    from m where m.reg is null or m.reg !~ '^[A-Z0-9-]{3,10}$'
$$;
revoke all on function public.co_rides(uuid) from public, anon, authenticated;

-- 機体の値段：大きさの値段 ×（1＋持っている機体1機ごとに 25%）。会社で最初の1機は半額
create or replace function public.ac_price(p_uid uuid, p_type text) returns bigint
language sql stable security definer set search_path = public as $$
  select round((ac_spec(p_type)).price * (1 + 0.25 * (select count(*) from aircraft where user_id = p_uid))
               * case when coalesce((select bought from companies where user_id = p_uid), 0) = 0 then 0.5 else 1 end)::bigint
$$;
revoke all on function public.ac_price(uuid, text) from public, anon, authenticated;

-- ---------- 実際の空 ----------
create or replace function public.co_sky_refresh(p_day date default null) returns integer
language plpgsql security definer set search_path = public as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date - 1); weeks integer; cnt integer;
begin
  select count(distinct svc_date) into weeks from flight_history where svc_date in (d - 7, d - 14, d - 21, d - 28);
  with ap as (select distinct on (iata) iata, id from airports where iata ~ '^[A-Z]{3}$' order by iata, id),
  h as (
    select least(a.id, b.id) || '-' || greatest(a.id, b.id) as k, x.svc_date, x.cancelled
      from flight_history x join ap a on a.iata = x.dep join ap b on b.iata = x.arr
     where x.svc_date in (d, d - 7, d - 14, d - 21, d - 28)
  ), g as (
    select k, count(*) filter (where svc_date = d and not cancelled)::int as n, count(*) filter (where svc_date = d and cancelled)::int as cxl,
           case when weeks > 0 then (count(*) filter (where svc_date < d and not cancelled))::real / weeks end as avg4
      from h group by k
  )
  insert into co_sky (route_key, day, n, cxl, avg4, mult)
  select k, d, n, cxl, avg4,
         round(1 + case when avg4 > 0 then greatest(-0.10, least(0.10, (n / avg4 - 1)::numeric)) else 0 end
                 - least(0.10, cxl::numeric / greatest(1, n + cxl)), 3)
    from g where n + cxl > 0
  on conflict (route_key, day) do update set n = excluded.n, cxl = excluded.cxl, avg4 = excluded.avg4, mult = excluded.mult;
  get diagnostics cnt = row_count;
  return cnt;
end;
$$;
revoke all on function public.co_sky_refresh(date) from public, anon, authenticated;

-- ---------- 路線 ----------
drop function if exists public.co_routes(uuid);
create or replace function public.co_routes(p_uid uuid)
returns table (route_key text, base bigint, level integer, min_size numeric, ac_type text, ac_mult numeric, hub_mult numeric,
               ac_id bigint, sky numeric, intl boolean, km numeric, a text, b text)
language sql stable security definer set search_path = public as $$
  with dom as (
    select least(f.from_airport, f.to_airport) as x, greatest(f.from_airport, f.to_airport) as y, max(f.distance_km)::numeric as km
      from flights f where f.user_id = p_uid group by 1, 2
  ), itl as (
    select least(i.dep, i.arr) as x, greatest(i.dep, i.arr) as y, max(i.distance_km)::numeric as km
      from intl_flights i where i.user_id = p_uid and i.flight_no is not null and i.distance_km > 0 group by 1, 2
  ), r as (
    select d.x || '-' || d.y as k, d.km, false as intl, xa.id as ida, ya.id as idb, airport_size(xa.radius_m) as sa, airport_size(ya.radius_m) as sb,
           xa.iata as a, ya.iata as b
      from dom d join airports xa on xa.id = d.x join airports ya on ya.id = d.y
    union all
    select i.x || '-' || i.y, i.km, true, ja.id, null, airport_size(ja.radius_m), 3::numeric, i.x, i.y
      from itl i join lateral (select id, radius_m from airports where iata in (i.x, i.y) order by id limit 1) ja on true
  )
  select r.k,
         round(sqrt(r.km) * (r.sa + r.sb) * 2)::bigint,
         coalesce(l.level, 1),
         least(r.sa, r.sb),
         ac.type,
         case when ac.id is null then 0.5 else round((ac_spec(ac.type)).mult * ac_age(ac.bought_at), 3) end,
         1 + 0.10 * coalesce(fa.level, 0) + 0.10 * coalesce(fb.level, 0),
         ac.id,
         case when r.intl then 1 else coalesce((select s.mult from co_sky s where s.route_key = r.k and s.day >= (now() at time zone 'Asia/Tokyo')::date - 3
                                                 order by s.day desc limit 1), 1) end,
         r.intl, round(r.km), r.a, r.b
    from r
    left join route_levels l on l.user_id = p_uid and l.route_key = r.k
    left join aircraft ac on ac.user_id = p_uid and ac.route_key = r.k
    left join facilities fa on fa.user_id = p_uid and fa.airport_id = r.ida
    left join facilities fb on fb.user_id = p_uid and fb.airport_id = r.idb
$$;
revoke all on function public.co_routes(uuid) from public, anon, authenticated;

-- 役職のボーナス：守り神の階級は、その空港でチェックインした日（日本時間）の数で数える
create or replace function public.co_bonus(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(sum(
           case r.k when 'crew' then 0.10 when 'maint' then 0.05 when 'sales' then 0.15 else 0 end
           + 0.02 * rank_tier(x.days)), 0)
    from companies c
    cross join lateral jsonb_each_text(c.roles) as r(k, v)
    cross join lateral (select count(distinct (ch.created_at at time zone 'Asia/Tokyo')::date) as days from checkins ch
                         where ch.user_id = p_uid and r.v ~ '^[0-9]+$' and ch.airport_id = r.v::integer) x
   where c.user_id = p_uid and x.days > 0
$$;

-- 1日の収益（維持費を引く前）・維持費・差し引き
create or replace function public.co_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(round(sum(base * (1 + 0.25 * (level - 1)) * ac_mult * hub_mult * sky)
                        * (1 + co_bonus(p_uid) + 0.05 * (rep_stars(co_rep_points(p_uid)) - 1))), 0)::bigint
    from co_routes(p_uid)
$$;
create or replace function public.co_upkeep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(sum(ac_upkeep(type)), 0)::bigint from aircraft where user_id = p_uid
$$;
create or replace function public.co_daily(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$ select co_gross(p_uid) - co_upkeep(p_uid) $$;

-- 会社の価値＝資金＋機体のいまの値段＋施設に使ったお金＋1日の収益×30日
create or replace function public.co_value(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce((select cash from companies where user_id = p_uid), 0)
       + coalesce((select sum(round(paid * ac_age(bought_at))) from aircraft where user_id = p_uid), 0)::bigint
       + coalesce((select sum(case level when 1 then 30000 when 2 then 110000 else 310000 end) from facilities where user_id = p_uid), 0)::bigint
       + greatest(co_daily(p_uid), 0) * 30
$$;
-- 拠点の空港：チェックインした日がいちばん多い空港
create or replace function public.co_home(p_uid uuid) returns integer
language sql stable security definer set search_path = public as $$
  select airport_id from checkins where user_id = p_uid
   group by airport_id order by count(distinct (created_at at time zone 'Asia/Tokyo')::date) desc, max(created_at) desc limit 1
$$;
revoke all on function public.co_bonus(uuid), public.co_gross(uuid), public.co_upkeep(uuid), public.co_daily(uuid), public.co_value(uuid), public.co_home(uuid)
  from public, anon, authenticated;

-- ---------- 公開の確かめ・会社を作る・収益の確定 ----------
create or replace function public.co_check(p_uid uuid) returns void
language plpgsql security definer set search_path = public, ops as $$
begin
  if p_uid is null then raise exception 'not signed in'; end if;
  if not coalesce((ops.flag('game_released'))::boolean, false) and not public.admin_registered() then raise exception 'game not released'; end if;
  insert into companies (user_id) values (p_uid) on conflict do nothing;
end;
$$;
-- それまでの収益（7日分まで）を資金に入れて、数えはじめを今にする。倍率が変わる操作の前に必ず呼ぶ
create or replace function public.co_settle(p_uid uuid) returns bigint
language plpgsql security definer set search_path = public as $$
declare c companies; pend bigint;
begin
  select * into c from companies where user_id = p_uid for update;
  pend := floor(co_daily(p_uid) * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400);
  update companies set cash = greatest(0, cash + pend), last_collect = now() where user_id = p_uid;
  return pend;
end;
$$;
revoke all on function public.co_check(uuid), public.co_settle(uuid) from public, anon, authenticated;

-- ---------- 会社の状態 ----------
create or replace function public.co_state() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare
  uid uuid := auth.uid(); c companies; d bigint; g bigint; u bigint; pts bigint; st integer;
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
                 'min_size', min_size, 'ac', ac_type, 'ac_id', ac_id, 'mult', ac_mult, 'hub', hub_mult, 'sky', sky, 'intl', intl, 'km', km, 'a', a, 'b', b)), '[]'::jsonb)
                 from co_routes(uid)),
    'sky', (select coalesce(jsonb_object_agg(s.route_key, jsonb_build_object('day', s.day, 'n', s.n, 'cxl', s.cxl, 'avg4', s.avg4, 'mult', s.mult)), '{}'::jsonb)
              from co_routes(uid) r
              join lateral (select * from co_sky x where x.route_key = r.route_key and x.day >= (now() at time zone 'Asia/Tokyo')::date - 3 order by x.day desc limit 1) s on true
             where not r.intl),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key, 'reg', reg, 'icao', icao, 'intl', intl,
                 'paid', paid, 'age', ac_age(bought_at), 'bought_at', bought_at, 'value', round(paid * ac_age(bought_at)),
                 'sell', round(paid * ac_age(bought_at) * 0.3), 'upkeep', ac_upkeep(type), 'rode_on', rode_on, 'flight', rode_flight) order by id), '[]'::jsonb)
                from aircraft where user_id = uid),
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid));
end;
$$;

-- 乗った機体の一覧（持っている・買える）。照らし合わせに時間がかかるので、機体の画面を開いたときだけ呼ぶ
create or replace function public.co_hangar() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  return (select coalesce(jsonb_agg(jsonb_build_object('ride', r.ride, 'reg', r.reg, 'icao', r.icao, 'cls', r.cls, 'intl', r.intl,
            'rode_on', r.rode_on, 'flight', r.flight, 'n', r.n, 'owned', a.id, 'price', ac_price(uid, r.cls), 'upkeep', ac_upkeep(r.cls))
            order by (a.id is not null) desc, r.rode_on desc), '[]'::jsonb)
    from co_rides(uid) r left join aircraft a on a.user_id = uid and a.ride = r.ride);
end;
$$;

-- ---------- 操作（どれも先に収益を確定する） ----------
create or replace function public.co_collect() returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); bon bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  with b as (update event_bonuses set credited_at = now() where user_id = uid and credited_at is null returning amount)
  select coalesce(sum(amount), 0) into bon from b;
  update companies set cash = cash + bon where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co_upgrade(p_route text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r record; cost bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into r from co_routes(uid) where route_key = p_route;
  if not found then raise exception 'route not found'; end if;
  if r.level >= 5 then raise exception 'max level'; end if;
  cost := up_cost(r.base, r.level);
  update companies set cash = cash - cost where user_id = uid and cash >= cost;
  if not found then raise exception 'not enough cash'; end if;
  insert into route_levels (user_id, route_key, level) values (uid, p_route, r.level + 1)
    on conflict (user_id, route_key) do update set level = excluded.level;
  return co_state();
end;
$$;

drop function if exists public.co_buy(text);
create or replace function public.co_buy(p_ride text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r record; price bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into r from co_rides(uid) where ride = p_ride;
  if not found then raise exception 'not ridden'; end if;
  if exists (select 1 from aircraft where user_id = uid and ride = p_ride) then raise exception 'already owned'; end if;
  price := ac_price(uid, r.cls);
  update companies set cash = cash - price, bought = bought + 1 where user_id = uid and cash >= price;
  if not found then raise exception 'not enough cash'; end if;
  insert into aircraft (user_id, type, reg, icao, ride, intl, paid, rode_on, rode_flight)
  values (uid, r.cls, r.reg, left(r.icao, 8), p_ride, r.intl, price, r.rode_on, left(r.flight, 10));
  return co_state();
end;
$$;

create or replace function public.co_assign(p_aircraft bigint, p_route text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); ac aircraft; r record;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into ac from aircraft where id = p_aircraft and user_id = uid for update;
  if not found then raise exception 'aircraft not found'; end if;
  if p_route is not null then
    select * into r from co_routes(uid) where route_key = p_route;
    if not found then raise exception 'route not found'; end if;
    if r.min_size < (ac_spec(ac.type)).min_size then raise exception 'airport too small'; end if;
    if r.intl and not ac.intl then raise exception 'not intl aircraft'; end if;
    update aircraft set route_key = null where user_id = uid and route_key = p_route and id <> p_aircraft;  -- 前の機体は外す
  end if;
  update aircraft set route_key = p_route where id = p_aircraft;
  return co_state();
end;
$$;

-- 売る：いまの値段（古さを入れた値段）の3割。売った機体は、また買える（最初の半額にはならない）
create or replace function public.co_sell(p_aircraft bigint) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); ac aircraft;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into ac from aircraft where id = p_aircraft and user_id = uid for update;
  if not found then raise exception 'aircraft not found'; end if;
  delete from aircraft where id = p_aircraft;
  update companies set cash = cash + round(ac.paid * ac_age(ac.bought_at) * 0.3) where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co_build(p_airport integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); cur integer; n integer; slots integer; cost bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not exists (select 1 from checkins where user_id = uid and airport_id = p_airport) then raise exception 'airport not visited'; end if;
  select level into cur from facilities where user_id = uid and airport_id = p_airport;
  if cur is null then
    select count(*) into n from facilities where user_id = uid;
    slots := rep_stars(co_rep_points(uid));
    if n >= slots then raise exception 'no free slot'; end if;
    cost := fac_cost(1);
  elsif cur >= 3 then raise exception 'max level';
  else cost := fac_cost(cur + 1);
  end if;
  update companies set cash = cash - cost where user_id = uid and cash >= cost;
  if not found then raise exception 'not enough cash'; end if;
  insert into facilities (user_id, airport_id, level) values (uid, p_airport, 1)
    on conflict (user_id, airport_id) do update set level = facilities.level + 1;
  return co_state();
end;
$$;

create or replace function public.co_set_role(p_role text, p_airport integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if p_role not in ('crew', 'maint', 'sales') then raise exception 'invalid role'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  if p_airport is not null and not exists (select 1 from checkins where user_id = uid and airport_id = p_airport) then
    raise exception 'guardian not met';
  end if;
  update companies set roles = (
      select coalesce(jsonb_object_agg(k, case when k <> p_role and v = to_jsonb(p_airport) then 'null'::jsonb else v end), '{}'::jsonb)
        from jsonb_each(roles) as e(k, v)
    ) || jsonb_build_object(p_role, p_airport)
   where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co_rename(p_name text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); n text := btrim(coalesce(p_name, ''));
begin
  perform co_check(uid);
  if char_length(n) < 1 or char_length(n) > 20 then raise exception 'invalid name'; end if;
  update companies set name = n where user_id = uid;
  return co_state();
end;
$$;

-- ---------- ランキングと友だち ----------
create or replace function public.co_set_hide(p_hide boolean) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  update companies set hide_rank = coalesce(p_hide, false) where user_id = uid;
  return co_state();
end;
$$;

create or replace function public.co_add_friend(p_code text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); f uuid;
begin
  perform co_check(uid);
  select user_id into f from companies where friend_code = upper(btrim(coalesce(p_code, '')));
  if f is null then raise exception 'code not found'; end if;
  if f = uid then raise exception 'own code'; end if;
  if (select count(*) from co_friends where user_id = uid) >= 100 then raise exception 'too many friends'; end if;
  insert into co_friends (user_id, friend_id) values (uid, f), (f, uid) on conflict do nothing;
  return jsonb_build_object('name', (select name from companies where user_id = f));
end;
$$;

create or replace function public.co_remove_friend(p_code text) returns void
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); f uuid;
begin
  perform co_check(uid);
  select user_id into f from companies where friend_code = upper(btrim(coalesce(p_code, '')));
  delete from co_friends where (user_id = uid and friend_id = f) or (user_id = f and friend_id = uid);
end;
$$;

-- 毎日の記録（日本時間の朝）：会社ごとの価値・拠点・路線と機体の数
create or replace function public.co_rank_refresh() returns integer
language plpgsql security definer set search_path = public as $$
declare d date := (now() at time zone 'Asia/Tokyo')::date; cnt integer;
begin
  insert into co_rank_days (day, user_id, value, home, routes, fleet)
  select d, c.user_id, co_value(c.user_id), co_home(c.user_id), (select count(*) from co_routes(c.user_id)), (select count(*) from aircraft a where a.user_id = c.user_id)
    from companies c
  on conflict (day, user_id) do update set value = excluded.value, home = excluded.home, routes = excluded.routes, fleet = excluded.fleet;
  get diagnostics cnt = row_count;
  return cnt;
end;
$$;
revoke all on function public.co_rank_refresh() from public, anon, authenticated;

-- ランキング：p_scope は all（全国）・home（拠点が同じ）・friends（友だち）。
--   ほかの会社は毎朝の記録、自分はいまの価値で並べる。出さない設定の会社は、全国と拠点には出ない（友だちには出る）。
--   名前は会社の名前だけ。上から20社と、自分の前後2社を返す
create or replace function public.co_ranking(p_scope text default 'all') returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); d date; me_v bigint; me_home integer; out jsonb; prev integer; me_rank integer; total integer; pv bigint;
begin
  perform co_check(uid);
  if p_scope not in ('all', 'home', 'friends') then raise exception 'bad scope'; end if;
  select max(day) into d from co_rank_days;
  me_v := co_value(uid); me_home := co_home(uid);
  with o as (
    select r.user_id, c.name, r.value, r.routes, r.fleet, false as me, case when p_scope = 'friends' then c.friend_code end as code
      from co_rank_days r join companies c on c.user_id = r.user_id
     where r.day = d and r.user_id <> uid
       and case p_scope
             when 'all' then not c.hide_rank
             when 'home' then not c.hide_rank and me_home is not null and r.home = me_home
             else exists (select 1 from co_friends f where f.user_id = uid and f.friend_id = r.user_id) end
    union all
    select uid, c.name, me_v, (select count(*) from co_routes(uid))::int, (select count(*) from aircraft where user_id = uid)::int, true, null
      from companies c where c.user_id = uid
  ), x as (select *, rank() over (order by value desc, me desc) as no from o)
  select (select no from x where me), (select count(*) from x),
         coalesce(jsonb_agg(jsonb_build_object('no', no, 'name', name, 'value', value, 'routes', routes, 'fleet', fleet, 'me', me, 'code', code) order by no, me desc)
                  filter (where no <= 20 or abs(no - (select no from x where me)) <= 2), '[]'::jsonb)
    into me_rank, total, out from x;
  -- 先週の順位（同じ並べ方で、7日前の記録どうし）
  select value into pv from co_rank_days where day = d - 7 and user_id = uid;
  if pv is not null then
    select 1 + count(*) into prev from co_rank_days r join companies c on c.user_id = r.user_id
     where r.day = d - 7 and r.user_id <> uid and r.value > pv
       and case p_scope when 'all' then not c.hide_rank
                        when 'home' then not c.hide_rank and r.home = me_home
                        else exists (select 1 from co_friends f where f.user_id = uid and f.friend_id = r.user_id) end;
  end if;
  return jsonb_build_object('scope', p_scope, 'day', d, 'rank', me_rank, 'total', total, 'value', me_v, 'prev', prev, 'home', me_home,
                            'hidden', (select hide_rank from companies where user_id = uid), 'rows', out);
end;
$$;

revoke all on function public.co_state(), public.co_hangar(), public.co_collect(), public.co_upgrade(text), public.co_buy(text), public.co_assign(bigint, text),
  public.co_sell(bigint), public.co_build(integer), public.co_set_role(text, integer), public.co_rename(text), public.co_set_hide(boolean),
  public.co_add_friend(text), public.co_remove_friend(text), public.co_ranking(text) from public, anon;
grant execute on function public.co_state(), public.co_hangar(), public.co_collect(), public.co_upgrade(text), public.co_buy(text), public.co_assign(bigint, text),
  public.co_sell(bigint), public.co_build(integer), public.co_set_role(text, integer), public.co_rename(text), public.co_set_hide(boolean),
  public.co_add_friend(text), public.co_remove_friend(text), public.co_ranking(text) to authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎日の記録（19:50 UTC）の後に、実際の空（05:20 日本時間）と会社の価値（05:45）
  execute $q$ select cron.schedule('co-sky', '20 20 * * *', $job$ select public.co_sky_refresh() $job$) $q$;
  execute $q$ select cron.schedule('co-rank', '45 20 * * *', $job$ select public.co_rank_refresh() $job$) $q$;
end
$outer$;
