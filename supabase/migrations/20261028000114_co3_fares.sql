-- エアライン経営 co-v3：運賃の5段階（仕様書「同じ路線の競争と運賃」）
--   とても安い ×0.7・安い ×0.85・普通 ×1.0・高い ×1.2・とても高い ×1.4。決めなければ普通。変えられるのは1日1回（日本時間）
--   方針の運賃にかけ合わせる（収益も、取り合いの運賃の重みも）。旅客の路線だけ（貨物・プライベートジェットには効かない）
--   同じ路線のほかの会社の段は co_state の fares で見える（会社名は出さない）

-- 表：路線ごとの運賃の段。自分の分だけ読める。書くのは関数 co3_set_fare だけ
create table if not exists public.co3_fares (
  user_id    uuid not null references auth.users(id) on delete cascade,
  route_key  text not null check (route_key ~ '^([0-9]+-[0-9]+|[A-Z]{3}-[A-Z]{3})$'),
  level      smallint not null check (level between -2 and 2),
  set_on     date not null default ((now() at time zone 'Asia/Tokyo')::date),
  primary key (user_id, route_key)
);
create index if not exists co3_fares_route on public.co3_fares (route_key);
alter table public.co3_fares enable row level security;
revoke all on public.co3_fares from public, anon, authenticated;
grant select on public.co3_fares to authenticated;
drop policy if exists "own fares" on public.co3_fares;
create policy "own fares" on public.co3_fares for select to authenticated using (user_id = auth.uid());

create or replace function co3.fare_level_mult(p_level integer) returns numeric
language sql immutable as $$
  select case coalesce(p_level, 0) when -2 then 0.7 when -1 then 0.85 when 1 then 1.2 when 2 then 1.4 else 1.0 end::numeric
$$;
revoke all on function co3.fare_level_mult(integer) from public, anon, authenticated;

create or replace function public.co3_fare_level(p_uid uuid, p_route text) returns integer
language sql stable security definer set search_path = public as $$
  select coalesce((select level from co3_fares where user_id = p_uid and route_key = p_route), 0)::int
$$;
revoke all on function public.co3_fare_level(uuid, text) from public, anon, authenticated;

-- 運賃の段を決める（1日1回。同じ段にするのは回数に数えない）
create or replace function public.co3_set_fare(p_route text, p_level integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); cur record; today date := (now() at time zone 'Asia/Tokyo')::date;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if p_level is null or p_level < -2 or p_level > 2 then raise exception 'invalid fare'; end if;
  if not exists (select 1 from co_routes(uid) where route_key = p_route) then raise exception 'route not found'; end if;
  select * into cur from co3_fares where user_id = uid and route_key = p_route;
  if found and cur.level = p_level then return co_state(); end if;
  if found and cur.set_on = today then raise exception 'fare once a day'; end if;
  insert into co3_fares (user_id, route_key, level, set_on) values (uid, p_route, p_level, today)
    on conflict (user_id, route_key) do update set level = excluded.level, set_on = excluded.set_on;
  return co_state();
end;
$$;
revoke all on function public.co3_set_fare(text, integer) from public, anon;
grant execute on function public.co3_set_fare(text, integer) to authenticated;

-- 路線の計算：自社の運賃 ×段、ほかの会社の運賃の重みも ×段
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('fare_level_mult' in src) = 0 then
    if position('(co3.policy(c.policy)).fare_mult as fm' in src) = 0
       or position('co3.fare_weight((co3.policy(c2.policy)).fare_mult, true)' in src) = 0
       or position('co3.fare_weight((co3.policy(c2.policy)).fare_mult, false)' in src) = 0 then
      raise exception 'co3_route_econ の形が変わっていて、運賃の段を入れられない';
    end if;
    src := replace(src, '(co3.policy(c.policy)).fare_mult as fm',
                        '(co3.policy(c.policy)).fare_mult * co3.fare_level_mult(co3_fare_level(p_uid, r.route_key)) as fm');
    src := replace(src, 'co3.fare_weight((co3.policy(c2.policy)).fare_mult, true)',
                        'co3.fare_weight((co3.policy(c2.policy)).fare_mult * co3.fare_level_mult(co3_fare_level(c2.user_id, r.route_key)), true)');
    src := replace(src, 'co3.fare_weight((co3.policy(c2.policy)).fare_mult, false)',
                        'co3.fare_weight((co3.policy(c2.policy)).fare_mult * co3.fare_level_mult(co3_fare_level(c2.user_id, r.route_key)), false)');
    execute src;
  end if;
end
$do$;

-- 会社の状態に運賃の段を足す：fares = {路線: {level, set_on, others: [ほかの会社の段…]}}（旅客の路線だけ）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''fares'', case when v3' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、運賃の段を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'fares', case when v3 then (
        select coalesce(jsonb_object_agg(r.route_key, jsonb_build_object(
                 'level', co3_fare_level(uid, r.route_key),
                 'set_on', (select f.set_on from co3_fares f where f.user_id = uid and f.route_key = r.route_key),
                 'others', (select coalesce(jsonb_agg(co3_fare_level(u.user_id, r.route_key) order by co3_fare_level(u.user_id, r.route_key)), '[]'::jsonb)
                              from (select distinct x.user_id from aircraft x where x.route_key = r.route_key and x.user_id <> uid) u))), '{}'::jsonb)
          from co_routes(uid) r) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
