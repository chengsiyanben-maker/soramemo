-- 会社経営（第1段）：資金・増便・役職・収益の受け取りをサーバーで計算する
-- 利用者は表を直接書き換えられない。操作はすべて下の関数（本人の会社だけに作用）を通す。
-- 数値はアプリ側の ECON と同じ：
--   空港の規模 大規模3・中規模2・離島1.5（判定半径で区別）
--   路線の1日の基本収益 = round(sqrt(距離km) × (規模1 + 規模2) × 2) 万円
--   便数レベル 1〜5、1段ごとに +25%。増便の費用 = 基本収益 × 3 × 今のレベル
--   役職 乗員+10%・整備+5%・営業+15%、守り神の階級1つごとに +2%
--   収益は7日分まで貯まる

create table public.companies (
  user_id      uuid primary key references auth.users(id) on delete cascade,
  name         text not null default 'そらメモ航空' check (char_length(name) between 1 and 20),
  cash         bigint not null default 0 check (cash >= 0),
  last_collect timestamptz not null default now(),
  roles        jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now()
);

create table public.route_levels (
  user_id   uuid not null references auth.users(id) on delete cascade,
  route_key text not null check (route_key ~ '^[0-9]+-[0-9]+$'),
  level     integer not null default 1 check (level between 1 and 5),
  primary key (user_id, route_key)
);

alter table public.companies    enable row level security;
alter table public.route_levels enable row level security;
create policy "own company"      on public.companies    for select to authenticated using (user_id = auth.uid());
create policy "own route levels" on public.route_levels for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.companies, public.route_levels from anon, authenticated;

-- ---------- 計算用の内部関数（利用者からは呼べない） ----------
create or replace function public.rank_tier(n bigint) returns integer
language sql immutable as $$
  select case when n >= 365 then 5 when n >= 100 then 4 when n >= 20 then 3 when n >= 5 then 2 when n >= 3 then 1 else 0 end
$$;

create or replace function public.airport_size(radius integer) returns numeric
language sql immutable as $$
  select case when radius >= 2000 then 3 when radius >= 1500 then 2 else 1.5 end
$$;

create or replace function public.co_routes(p_uid uuid)
returns table (route_key text, base bigint, level integer)
language sql stable security definer set search_path = public as $$
  with r as (
    select least(f.from_airport, f.to_airport) as a, greatest(f.from_airport, f.to_airport) as b, max(f.distance_km) as km
      from flights f where f.user_id = p_uid group by 1, 2
  )
  select r.a || '-' || r.b,
         round(sqrt(r.km::numeric) * (airport_size(x.radius_m) + airport_size(y.radius_m)) * 2)::bigint,
         coalesce(l.level, 1)
    from r
    join airports x on x.id = r.a
    join airports y on y.id = r.b
    left join route_levels l on l.user_id = p_uid and l.route_key = r.a || '-' || r.b
$$;

create or replace function public.co_bonus(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(sum(
           case r.k when 'crew' then 0.10 when 'maint' then 0.05 when 'sales' then 0.15 else 0 end
           + 0.02 * rank_tier(x.cnt)), 0)
    from companies c
    cross join lateral jsonb_each_text(c.roles) as r(k, v)
    cross join lateral (select count(*) as cnt from checkins ch
                         where ch.user_id = p_uid and r.v ~ '^[0-9]+$' and ch.airport_id = r.v::integer) x
   where c.user_id = p_uid and x.cnt > 0
$$;

create or replace function public.co_daily(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(round(sum(base * (1 + 0.25 * (level - 1))) * (1 + co_bonus(p_uid))), 0)::bigint from co_routes(p_uid)
$$;

revoke all on function public.co_routes(uuid), public.co_bonus(uuid), public.co_daily(uuid) from public, anon, authenticated;

-- ---------- 利用者が呼ぶ関数 ----------
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
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', base * 3 * level)), '[]'::jsonb)
                 from co_routes(uid)));
end;
$$;

create or replace function public.co_collect() returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); c companies; pend bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  perform co_state();
  select * into c from companies where user_id = uid for update;
  pend := floor(co_daily(uid) * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400);
  update companies set cash = cash + greatest(pend, 0), last_collect = now() where user_id = uid;
  return co_state();
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
  cost := r.base * 3 * r.level;
  update companies set cash = cash - cost where user_id = uid and cash >= cost;
  if not found then raise exception 'not enough cash'; end if;
  insert into route_levels (user_id, route_key, level) values (uid, p_route, r.level + 1)
    on conflict (user_id, route_key) do update set level = excluded.level;
  return co_state();
end;
$$;

create or replace function public.co_set_role(p_role text, p_airport integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not signed in'; end if;
  if p_role not in ('crew', 'maint', 'sales') then raise exception 'invalid role'; end if;
  perform co_state();
  if p_airport is not null and not exists (select 1 from checkins where user_id = uid and airport_id = p_airport) then
    raise exception 'guardian not met';
  end if;
  -- 1体の守り神は1つの役職まで
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
  if uid is null then raise exception 'not signed in'; end if;
  if char_length(n) < 1 or char_length(n) > 20 then raise exception 'invalid name'; end if;
  perform co_state();
  update companies set name = n where user_id = uid;
  return co_state();
end;
$$;

revoke all on function public.co_state(), public.co_collect(), public.co_upgrade(text), public.co_set_role(text, integer), public.co_rename(text) from public, anon;
grant execute on function public.co_state(), public.co_collect(), public.co_upgrade(text), public.co_set_role(text, integer), public.co_rename(text) to authenticated;
