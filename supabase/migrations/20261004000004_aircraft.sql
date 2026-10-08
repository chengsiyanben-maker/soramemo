-- 会社経営（第2段）：機材の購入と路線への割り当て
-- アプリ側の ECON.aircraft と同じ値にすること。
--   prop プロペラ機          ×1.10  1,000万円  解放 0km       就航 規模1.5以上どうし
--   rj   リージョナルジェット ×1.25  2,500万円  解放 2,000km   就航 規模1.5以上どうし
--   nb   小型ジェット         ×1.50  5,000万円  解放 5,000km   就航 規模2以上どうし
--   wb   中型ジェット         ×1.90 15,000万円  解放 20,000km  就航 規模3どうし
--   lg   大型ジェット         ×2.30 40,000万円  解放 40,075km  就航 規模3どうし

create table public.aircraft (
  id        bigint generated always as identity primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  type      text not null check (type in ('prop', 'rj', 'nb', 'wb', 'lg')),
  route_key text check (route_key is null or route_key ~ '^[0-9]+-[0-9]+$'),
  bought_at timestamptz not null default now()
);
-- 1つの路線に割り当てられる機材は1機まで
create unique index aircraft_one_per_route on public.aircraft (user_id, route_key) where route_key is not null;

alter table public.aircraft enable row level security;
create policy "own aircraft" on public.aircraft for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.aircraft from anon, authenticated;

create or replace function public.ac_spec(p_type text, out mult numeric, out price bigint, out unlock_km numeric, out min_size numeric)
language sql immutable as $$
  select mult, price, unlock_km, min_size from (values
    ('prop', 1.10, 1000::bigint, 0::numeric, 1.5::numeric),
    ('rj',   1.25, 2500, 2000, 1.5),
    ('nb',   1.50, 5000, 5000, 2),
    ('wb',   1.90, 15000, 20000, 3),
    ('lg',   2.30, 40000, 40075, 3)
  ) as t(ty, mult, price, unlock_km, min_size) where ty = p_type
$$;

-- 路線一覧に、両端の小さいほうの空港規模と、割り当てた機材の倍率を加える
drop function if exists public.co_routes(uuid);
create or replace function public.co_routes(p_uid uuid)
returns table (route_key text, base bigint, level integer, min_size numeric, ac_type text, ac_mult numeric)
language sql stable security definer set search_path = public as $$
  with r as (
    select least(f.from_airport, f.to_airport) as a, greatest(f.from_airport, f.to_airport) as b, max(f.distance_km) as km
      from flights f where f.user_id = p_uid group by 1, 2
  )
  select r.a || '-' || r.b,
         round(sqrt(r.km::numeric) * (airport_size(x.radius_m) + airport_size(y.radius_m)) * 2)::bigint,
         coalesce(l.level, 1),
         least(airport_size(x.radius_m), airport_size(y.radius_m)),
         ac.type,
         coalesce((ac_spec(ac.type)).mult, 1)
    from r
    join airports x on x.id = r.a
    join airports y on y.id = r.b
    left join route_levels l on l.user_id = p_uid and l.route_key = r.a || '-' || r.b
    left join aircraft ac on ac.user_id = p_uid and ac.route_key = r.a || '-' || r.b
$$;
revoke all on function public.co_routes(uuid) from public, anon, authenticated;

create or replace function public.co_daily(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(round(sum(base * (1 + 0.25 * (level - 1)) * ac_mult) * (1 + co_bonus(p_uid))), 0)::bigint from co_routes(p_uid)
$$;
revoke all on function public.co_daily(uuid) from public, anon, authenticated;

create or replace function public.co_state() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  uid uuid := auth.uid(); c companies; d bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  insert into companies (user_id) values (uid) on conflict do nothing;
  select * into c from companies where user_id = uid;
  d := co_daily(uid);
  return jsonb_build_object(
    'name', c.name, 'cash', c.cash, 'last', c.last_collect, 'roles', c.roles, 'daily', d,
    'bonus', co_bonus(uid),
    'pending', floor(d * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400),
    'total_km', (select coalesce(sum(distance_km), 0) from flights where user_id = uid),
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', base * 3 * level,
                 'min_size', min_size, 'ac', ac_type, 'mult', ac_mult)), '[]'::jsonb) from co_routes(uid)),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key) order by id), '[]'::jsonb)
                from aircraft where user_id = uid));
end;
$$;

create or replace function public.co_buy(p_type text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); sp record; km numeric;
begin
  if uid is null then raise exception 'not signed in'; end if;
  select * into sp from ac_spec(p_type);
  if sp.price is null then raise exception 'invalid aircraft'; end if;
  perform co_state();
  perform 1 from companies where user_id = uid for update;
  select coalesce(sum(distance_km), 0) into km from flights where user_id = uid;
  if km < sp.unlock_km then raise exception 'aircraft locked'; end if;
  update companies set cash = cash - sp.price where user_id = uid and cash >= sp.price;
  if not found then raise exception 'not enough cash'; end if;
  insert into aircraft (user_id, type) values (uid, p_type);
  return co_state();
end;
$$;

create or replace function public.co_assign(p_aircraft bigint, p_route text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); ac aircraft; r record;
begin
  if uid is null then raise exception 'not signed in'; end if;
  select * into ac from aircraft where id = p_aircraft and user_id = uid for update;
  if not found then raise exception 'aircraft not found'; end if;
  if p_route is not null then
    select * into r from co_routes(uid) where route_key = p_route;
    if not found then raise exception 'route not found'; end if;
    if r.min_size < (ac_spec(ac.type)).min_size then raise exception 'airport too small'; end if;
    update aircraft set route_key = null where user_id = uid and route_key = p_route and id <> p_aircraft;  -- 前の機材は外す
  end if;
  update aircraft set route_key = p_route where id = p_aircraft;
  return co_state();
end;
$$;

revoke all on function public.co_buy(text), public.co_assign(bigint, text) from public, anon;
grant execute on function public.co_buy(text), public.co_assign(bigint, text) to authenticated;
