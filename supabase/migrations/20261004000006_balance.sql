-- 経済バランスの調整（2026年10月、4タイプの利用者で2年間をシミュレーションした結果）
-- 変更点（アプリ側の ECON も同じ値）：
--   増便の費用   基本収益 × 30 × 段階²（以前は ×3×段階）
--   機材の価格   10倍、さらに保有している機材1機ごとに +25%
--   施設の費用   30,000・80,000・200,000万円（以前の10倍）
--   評判の星     ★2:100 ★3:250 ★4:550 ★5:1000点（以前は 100・300・700・1500）

create or replace function public.fac_cost(p_level integer) returns bigint
language sql immutable as $$ select (array[30000, 80000, 200000])[p_level]::bigint $$;

create or replace function public.ac_spec(p_type text, out mult numeric, out price bigint, out unlock_km numeric, out min_size numeric)
language sql immutable as $$
  select mult, price, unlock_km, min_size from (values
    ('prop', 1.10, 10000::bigint, 0::numeric, 1.5::numeric),
    ('rj',   1.25, 25000, 2000, 1.5),
    ('nb',   1.50, 50000, 5000, 2),
    ('wb',   1.90, 150000, 20000, 3),
    ('lg',   2.30, 400000, 40075, 3)
  ) as t(ty, mult, price, unlock_km, min_size) where ty = p_type
$$;

create or replace function public.rep_stars(p bigint) returns integer
language sql immutable as $$
  select case when p >= 1000 then 5 when p >= 550 then 4 when p >= 250 then 3 when p >= 100 then 2 else 1 end
$$;

create or replace function public.up_cost(p_base bigint, p_level integer) returns bigint
language sql immutable as $$ select p_base * 30 * p_level * p_level $$;

create or replace function public.ac_price(p_uid uuid, p_type text) returns bigint
language sql stable security definer set search_path = public as $$
  select round((ac_spec(p_type)).price * (1 + 0.25 * (select count(*) from aircraft where user_id = p_uid)))::bigint
$$;
revoke all on function public.ac_price(uuid, text) from public, anon, authenticated;

create or replace function public.co_state() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  uid uuid := auth.uid(); c companies; d bigint; pts bigint; st integer;
begin
  if uid is null then raise exception 'not signed in'; end if;
  insert into companies (user_id) values (uid) on conflict do nothing;
  select * into c from companies where user_id = uid;
  d := co_daily(uid); pts := co_rep_points(uid); st := rep_stars(pts);
  return jsonb_build_object(
    'name', c.name, 'cash', c.cash, 'last', c.last_collect, 'roles', c.roles, 'daily', d,
    'bonus', co_bonus(uid), 'rep_points', pts, 'stars', st, 'rep_bonus', 0.05 * (st - 1),
    'pending', floor(d * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400),
    'total_km', (select coalesce(sum(distance_km), 0) from flights where user_id = uid),
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', up_cost(base, level),
                 'min_size', min_size, 'ac', ac_type, 'mult', ac_mult, 'hub', hub_mult)), '[]'::jsonb) from co_routes(uid)),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key) order by id), '[]'::jsonb)
                from aircraft where user_id = uid),
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid));
end;
$$;

create or replace function public.co_upgrade(p_route text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r record; cost bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  perform co_state();
  perform 1 from companies where user_id = uid for update;
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

create or replace function public.co_buy(p_type text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); sp record; km numeric; price bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  select * into sp from ac_spec(p_type);
  if sp.price is null then raise exception 'invalid aircraft'; end if;
  perform co_state();
  perform 1 from companies where user_id = uid for update;
  select coalesce(sum(distance_km), 0) into km from flights where user_id = uid;
  if km < sp.unlock_km then raise exception 'aircraft locked'; end if;
  price := ac_price(uid, p_type);
  update companies set cash = cash - price where user_id = uid and cash >= price;
  if not found then raise exception 'not enough cash'; end if;
  insert into aircraft (user_id, type) values (uid, p_type);
  return co_state();
end;
$$;
