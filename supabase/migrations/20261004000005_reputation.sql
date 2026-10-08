-- 会社経営（第3段）：評判と施設（拠点）
-- アプリ側の ECON.rep / ECON.facility と同じ値にすること。
--   評判の点数 = 就航地×10 + 路線×20 + 増便の段数×5 + 機材×15 + 施設の段数×10 + 役職に就いた守り神×10
--   星 ★1:0点 ★2:100 ★3:300 ★4:700 ★5:1500。★1つごとに収益+5%（★1は0%、★5で+20%）。建てられる施設の数＝星の数
--   施設（拠点）は訪れた空港に建てる。段階1〜3、費用 3,000・8,000・20,000万円、その空港を発着する路線の収益が1段ごとに+10%

create table public.facilities (
  user_id    uuid not null references auth.users(id) on delete cascade,
  airport_id integer not null references public.airports(id),
  level      integer not null default 1 check (level between 1 and 3),
  built_at   timestamptz not null default now(),
  primary key (user_id, airport_id)
);
alter table public.facilities enable row level security;
create policy "own facilities" on public.facilities for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.facilities from anon, authenticated;

create or replace function public.fac_cost(p_level integer) returns bigint
language sql immutable as $$ select (array[3000, 8000, 20000])[p_level]::bigint $$;

-- 路線一覧に拠点の倍率を加える
drop function if exists public.co_routes(uuid);
create or replace function public.co_routes(p_uid uuid)
returns table (route_key text, base bigint, level integer, min_size numeric, ac_type text, ac_mult numeric, hub_mult numeric)
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
         coalesce((ac_spec(ac.type)).mult, 1),
         1 + 0.10 * coalesce(fa.level, 0) + 0.10 * coalesce(fb.level, 0)
    from r
    join airports x on x.id = r.a
    join airports y on y.id = r.b
    left join route_levels l on l.user_id = p_uid and l.route_key = r.a || '-' || r.b
    left join aircraft ac on ac.user_id = p_uid and ac.route_key = r.a || '-' || r.b
    left join facilities fa on fa.user_id = p_uid and fa.airport_id = r.a
    left join facilities fb on fb.user_id = p_uid and fb.airport_id = r.b
$$;

create or replace function public.co_rep_points(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select (select count(distinct airport_id) from checkins where user_id = p_uid) * 10
       + (select count(*) from co_routes(p_uid)) * 20
       + (select coalesce(sum(level - 1), 0) from route_levels where user_id = p_uid) * 5
       + (select count(*) from aircraft where user_id = p_uid) * 15
       + (select coalesce(sum(level), 0) from facilities where user_id = p_uid) * 10
       + (select count(*) from companies c cross join lateral jsonb_each_text(c.roles) as e(k, v)
           where c.user_id = p_uid and e.v ~ '^[0-9]+$'
             and exists (select 1 from checkins ch where ch.user_id = p_uid and ch.airport_id = e.v::integer)) * 10
$$;

create or replace function public.rep_stars(p bigint) returns integer
language sql immutable as $$
  select case when p >= 1500 then 5 when p >= 700 then 4 when p >= 300 then 3 when p >= 100 then 2 else 1 end
$$;

create or replace function public.co_daily(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce(round(sum(base * (1 + 0.25 * (level - 1)) * ac_mult * hub_mult)
                        * (1 + co_bonus(p_uid) + 0.05 * (rep_stars(co_rep_points(p_uid)) - 1))), 0)::bigint
    from co_routes(p_uid)
$$;

revoke all on function public.co_routes(uuid), public.co_rep_points(uuid), public.co_daily(uuid) from public, anon, authenticated;

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
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', base * 3 * level,
                 'min_size', min_size, 'ac', ac_type, 'mult', ac_mult, 'hub', hub_mult)), '[]'::jsonb) from co_routes(uid)),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key) order by id), '[]'::jsonb)
                from aircraft where user_id = uid),
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid));
end;
$$;

create or replace function public.co_build(p_airport integer) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); cur integer; n integer; slots integer; cost bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  perform co_state();
  perform 1 from companies where user_id = uid for update;
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

revoke all on function public.co_build(integer) from public, anon;
grant execute on function public.co_build(integer) to authenticated;
