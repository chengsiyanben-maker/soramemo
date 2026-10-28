-- エアライン経営：空港の大きさを実際の便の数で決める（2026年10月）
--   以前は滑走路まわりの広さだけで3段階（大規模に28空港。羽田と青森が同じ扱い）だった。
--   これからは、毎日の記録（airport_daily）の1日の発着便数の、前の28日の平均で5段階にする。
--     超大規模 6（800便以上）・拠点 4.5（250便以上）・大規模 3（80便以上）・中規模 2（25便以上）・小規模 1.5
--   記録が14日分ない空港は、主な空港の一覧（羽田は超大規模、成田・関西・伊丹・中部・新千歳・福岡・那覇は拠点）か、広さで決める（大規模まで）。
--   海外の空港は拠点（4.5）として数える。
--   基本収益は √距離 × √（大きさ×大きさ）× 4（大規模どうしは以前と同じ値。小さいほうの空港に引っぱられる）
--   機体：大型ジェットは拠点以上どうし、中型ジェットは大規模以上どうし、小型ジェットは中規模以上どうし

create table if not exists public.co_ap_size (
  iata       text primary key check (iata ~ '^[A-Z]{3}$'),
  flights    real not null,          -- 1日の発着便数（前の28日の平均）
  days       integer not null,       -- 数えた日数
  size       numeric not null,
  updated_at timestamptz not null default now()
);
alter table public.co_ap_size enable row level security;
revoke all on public.co_ap_size from public, anon, authenticated;
grant select on public.co_ap_size to anon, authenticated;
drop policy if exists "airport sizes are public" on public.co_ap_size;
create policy "airport sizes are public" on public.co_ap_size for select to anon, authenticated using (true);

create or replace function public.co_size_of_flights(p real) returns numeric
language sql immutable as $$ select case when p >= 800 then 6 when p >= 250 then 4.5 when p >= 80 then 3 when p >= 25 then 2 else 1.5 end::numeric $$;

-- 空港の大きさ（記録があれば便の数、なければ主な空港の一覧か広さ）
create or replace function public.co_size(p_iata text, p_radius integer) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select size from co_ap_size where iata = p_iata and days >= 14),
    case when p_iata = 'HND' then 6 when p_iata in ('NRT', 'KIX', 'ITM', 'NGO', 'CTS', 'FUK', 'OKA') then 4.5 end,
    airport_size(coalesce(p_radius, 0)))
$$;

create or replace function public.co_size_refresh() returns integer
language plpgsql security definer set search_path = public as $$
declare cnt integer; d date := (now() at time zone 'Asia/Tokyo')::date;
begin
  insert into co_ap_size (iata, flights, days, size, updated_at)
  select iata, avg(flights)::real, count(*)::int, co_size_of_flights(avg(flights)::real), now()
    from airport_daily where day >= d - 28 and day < d group by iata
  on conflict (iata) do update set flights = excluded.flights, days = excluded.days, size = excluded.size, updated_at = now();
  get diagnostics cnt = row_count;
  return cnt;
end;
$$;
revoke all on function public.co_size_refresh() from public, anon, authenticated;
select public.co_size_refresh();

-- だれでも読める：空港ごとの大きさ（アプリのお試し版と、路線の内わけの表示に使う）
create or replace function public.co_sizes() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_object_agg(iata, jsonb_build_object('size', size, 'flights', round(flights))), '{}'::jsonb) from co_ap_size where days >= 14
$$;
revoke all on function public.co_sizes() from public;
grant execute on function public.co_sizes() to anon, authenticated;

create or replace function public.ac_spec(p_type text, out mult numeric, out price bigint, out unlock_km numeric, out min_size numeric)
language sql immutable as $$
  select mult, price, 0::numeric, min_size from (values
    ('prop', 1.10, 8000::bigint, 1.5::numeric),
    ('rj',   1.25, 15000, 1.5),
    ('nb',   1.50, 25000, 2),
    ('wb',   1.90, 50000, 3),
    ('lg',   2.30, 80000, 4.5)
  ) as t(ty, mult, price, min_size) where ty = p_type
$$;

drop function if exists public.co_routes(uuid);
create or replace function public.co_routes(p_uid uuid)
returns table (route_key text, base bigint, level integer, min_size numeric, ac_type text, ac_mult numeric, hub_mult numeric,
               ac_id bigint, sky numeric, intl boolean, km numeric, a text, b text, size_a numeric, size_b numeric)
language sql stable security definer set search_path = public as $$
  with dom as (
    select least(f.from_airport, f.to_airport) as x, greatest(f.from_airport, f.to_airport) as y, max(f.distance_km)::numeric as km
      from flights f where f.user_id = p_uid group by 1, 2
  ), itl as (
    select least(i.dep, i.arr) as x, greatest(i.dep, i.arr) as y, max(i.distance_km)::numeric as km
      from intl_flights i where i.user_id = p_uid and i.flight_no is not null and i.distance_km > 0 group by 1, 2
  ), r as (
    select d.x || '-' || d.y as k, d.km, false as intl, xa.id as ida, ya.id as idb, co_size(xa.iata, xa.radius_m) as sa, co_size(ya.iata, ya.radius_m) as sb,
           xa.iata as a, ya.iata as b
      from dom d join airports xa on xa.id = d.x join airports ya on ya.id = d.y
    union all
    -- 国際線：日本の空港はその大きさ、海外の空港は拠点（4.5）
    select i.x || '-' || i.y, i.km, true, ja.id, null,
           case when ja.iata = i.x then co_size(ja.iata, ja.radius_m) else 4.5 end, case when ja.iata = i.y then co_size(ja.iata, ja.radius_m) else 4.5 end, i.x, i.y
      from itl i join lateral (select id, iata, radius_m from airports where iata in (i.x, i.y) order by id limit 1) ja on true
  )
  select r.k,
         round(sqrt(r.km) * sqrt(r.sa * r.sb) * 4)::bigint,
         coalesce(l.level, 1),
         least(r.sa, r.sb),
         ac.type,
         case when ac.id is null then 0.5 else round((ac_spec(ac.type)).mult * ac_age(ac.bought_at), 3) end,
         1 + 0.10 * coalesce(fa.level, 0) + 0.10 * coalesce(fb.level, 0),
         ac.id,
         case when r.intl then 1 else coalesce((select s.mult from co_sky s where s.route_key = r.k and s.day >= (now() at time zone 'Asia/Tokyo')::date - 3
                                                 order by s.day desc limit 1), 1) end,
         r.intl, round(r.km), r.a, r.b, r.sa, r.sb
    from r
    left join route_levels l on l.user_id = p_uid and l.route_key = r.k
    left join aircraft ac on ac.user_id = p_uid and ac.route_key = r.k
    left join facilities fa on fa.user_id = p_uid and fa.airport_id = r.ida
    left join facilities fb on fb.user_id = p_uid and fb.airport_id = r.idb
$$;
revoke all on function public.co_routes(uuid) from public, anon, authenticated;

-- すでに入っている機体のうち、入れられなくなった路線（大型ジェットの拠点以外）からは外す
update public.aircraft a set route_key = null
 where a.route_key is not null and a.type = 'lg'
   and not exists (select 1 from public.co_routes(a.user_id) r where r.route_key = a.route_key and r.min_size >= 4.5);

-- 会社の状態に、路線の両端の大きさを足す（ほかは 20261028000099_co_v2.sql と同じ）
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
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid));
end;
$$;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎日の記録（19:50 UTC）の後に、空港の大きさ（05:15 日本時間）
  execute $q$ select cron.schedule('co-size', '15 20 * * *', $job$ select public.co_size_refresh() $job$) $q$;
end
$outer$;
