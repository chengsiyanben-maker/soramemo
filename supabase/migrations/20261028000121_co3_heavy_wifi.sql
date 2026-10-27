-- エアライン経営 co-v3：C点検・重整備（自動）と機内Wi-Fi（仕様書「定期点検」「サービス」）
--   C点検：会社に入れてから（または前のC点検・重整備から）2年半（912日）か、飛んだ時間 7,500時間ごと
--     7日（中型以上 10日）運休。費用は機体の値段の3% × 1.3（整備場がないので、ゲームの整備会社）
--   重整備：8年（2,920日）ごと。21日運休、費用 10% × 1.3。古さが新品に戻る（会社に入れた日を、始めた日にする）
--   どちらも格付け3から（それまでは点検の費用は維持費に込み）。整備場を作るまでは自動で、時期は選べない
--   運休の間は、予備機（路線に入れていない旅客機）がいれば代わりに飛ぶ。いなければその路線は飛ばない（計画した運休なので、欠航・トラブル・定時率には数えない）
--   機内Wi-Fi（格付け4から・機体ごと）：付けるのに機体の値段の3%、維持費 +10%、その機体の路線で仕事の客 +8%（収益に 仕事の割合 × 8%）、
--     満足度 +（付けた機体の割合 × 6）

alter table public.aircraft add column if not exists wifi boolean not null default false;
alter table public.aircraft add column if not exists heavy_from date;     -- 前のC点検・重整備の終わった日（なければ会社に入れた日）
alter table public.aircraft add column if not exists heavy_min integer not null default 0;   -- 前のC点検のときの飛んだ時間
alter table public.aircraft enable row level security;

create table if not exists public.co3_heavy (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  aircraft_id bigint not null references public.aircraft (id) on delete cascade,
  kind text not null check (kind in ('c', 'heavy')),
  start_day date not null,
  end_day date not null,
  spare_id bigint references public.aircraft (id) on delete set null,
  cost numeric not null default 0,
  created_at timestamptz not null default now(),
  unique (aircraft_id, start_day)
);
create index if not exists co3_heavy_user on public.co3_heavy (user_id, end_day);
alter table public.co3_heavy enable row level security;
revoke all on public.co3_heavy from public, anon, authenticated;
grant select on public.co3_heavy to authenticated;
drop policy if exists co3_heavy_own on public.co3_heavy;
create policy co3_heavy_own on public.co3_heavy for select to authenticated using (user_id = (select auth.uid()));

-- その日、機体が点検で飛べないか（予備機が飛ぶなら false）
create or replace function public.co3_in_heavy(p_aircraft bigint, p_day date default null) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from co3_heavy h where h.aircraft_id = p_aircraft and h.spare_id is null
                    and coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date) between h.start_day and h.end_day)
$$;
revoke all on function public.co3_in_heavy(bigint, date) from public, anon, authenticated;

-- 毎晩：C点検・重整備を始める
create or replace function public.co3_heavy_run(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); a record; k text; len int; cst numeric; sp bigint; n int := 0;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for a in select x.*, r.min_size as r_min, r.intl as r_intl from aircraft x join companies c on c.user_id = x.user_id
             left join lateral (select y.min_size, y.intl from co_routes(x.user_id) y where y.route_key = x.route_key) r on true
            where coalesce(c.rating, 1) >= 3 and not x.lease
              and not exists (select 1 from co3_heavy h where h.aircraft_id = x.id and h.end_day >= d) loop
    k := case when d - coalesce(a.heavy_from, (a.bought_at at time zone 'Asia/Tokyo')::date) >= 2920 then 'heavy'
              when d - coalesce(a.heavy_from, (a.bought_at at time zone 'Asia/Tokyo')::date) >= 912 or a.fly_min - a.heavy_min >= 7500 * 60 then 'c' end;
    continue when k is null;
    len := case when k = 'heavy' then 21 when a.type in ('wb', 'lg') then 10 else 7 end;
    cst := ceil(greatest(a.paid, (ac_spec(a.type)).price) * case when k = 'heavy' then 0.10 else 0.03 end * 1.3);
    sp := null;
    if a.route_key is not null then
      select s.id into sp from aircraft s
       where s.user_id = a.user_id and s.route_key is null and not exists (select 1 from co3_sched q where q.aircraft_id = s.id)
         and not co3_is_freighter(s.id) and not co3_is_bizjet(s.id) and a.r_min >= (ac_spec(s.type)).min_size and (not a.r_intl or s.intl)
         and not exists (select 1 from co3_heavy h where (h.spare_id = s.id or h.aircraft_id = s.id) and h.end_day >= d)
         and not exists (select 1 from co3_breakdowns b where (b.spare_id = s.id or b.aircraft_id = s.id) and b.end_day >= d)
         and not exists (select 1 from co3_extra x where x.aircraft_id = s.id and d between x.start_day and x.end_day)
       order by s.id limit 1;
    end if;
    insert into co3_heavy (user_id, aircraft_id, kind, start_day, end_day, spare_id, cost) values (a.user_id, a.id, k, d, d + len - 1, sp, cst);
    update companies set cash = greatest(0, cash - cst) where user_id = a.user_id;
    update aircraft set heavy_from = d + len, heavy_min = fly_min, bought_at = case when k = 'heavy' then d::timestamp at time zone 'Asia/Tokyo' else bought_at end
     where id = a.id;
    n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_heavy_run(date) from public, anon, authenticated;

-- 機内Wi-Fi を付ける・外す（外してもお金は戻らない）
create or replace function public.co3_set_wifi(p_aircraft bigint, p_on boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); a record; cst numeric;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 4 then raise exception 'rating required 4'; end if;
  select * into a from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  if co3_is_freighter(a.id) then raise exception 'not a passenger aircraft'; end if;
  if p_on and not a.wifi then
    cst := ceil(greatest(a.paid, (ac_spec(a.type)).price) * 0.03);
    if (select cash from companies where user_id = uid) < cst then raise exception 'not enough cash'; end if;
    update companies set cash = cash - cst where user_id = uid;
  end if;
  update aircraft set wifi = coalesce(p_on, false) where id = a.id;
  return co_state();
end;
$$;
revoke all on function public.co3_set_wifi(bigint, boolean) from public, anon;
grant execute on function public.co3_set_wifi(bigint, boolean) to authenticated;

-- 収益の倍率に Wi-Fi を足す（路線の機体に付いていれば 仕事の割合 × 8%）
create or replace function public.co3_wifi_mult(p_aircraft bigint, p_biz numeric) returns numeric
language sql stable security definer set search_path = public as $$
  select case when coalesce((select a.wifi from aircraft a join companies c on c.user_id = a.user_id where a.id = p_aircraft and coalesce(c.rating, 1) >= 4), false)
              then 1 + coalesce(p_biz, 0) * 0.08 else 1 end
$$;
revoke all on function public.co3_wifi_mult(bigint, numeric) from public, anon, authenticated;

-- 満足度の内わけ：Wi-Fi を足す（列が増えるので作り直す）
drop function if exists public.co3_satisfaction_parts(uuid);
create function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out meal numeric, out bag numeric,
  out response numeric, out ontime numeric, out own_cxl numeric, out ontime_rate numeric, out lounge numeric, out miles numeric, out wifi numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy, meal, bag, rating, miles from companies where user_id = p_uid),
  f as (select count(*) as n,
               count(*) filter (where bought_at > now() - interval '90 days') as fresh,
               count(*) filter (where wifi) as wf,
               avg(ac_age(bought_at)) as age
          from aircraft where user_id = p_uid),
  t as (select count(*) filter (where result = 'god') as god, count(*) filter (where result = 'none') as none
          from co3_troubles where user_id = p_uid and created_at > now() - interval '30 days'),
  o as (select * from co3_ontime(p_uid)),
  p as (
    select 50::numeric as base,
           case when c.policy = 'lcc' then -4 else 0 end::numeric as packed,
           round(case when f.n > 0 then 6.0 * f.fresh / f.n else 0 end, 2) as new_share,
           round(case when f.n > 0 then -8 * (1 - f.age) / 0.2 else 0 end, 2) as aging,
           case c.policy when 'fsc' then -5 when 'lcc' then 5 else 0 end::numeric as policy_adj,
           (co3.service_sat(c.policy, c.meal, c.bag)).meal as meal,
           (co3.service_sat(c.policy, c.meal, c.bag)).bag as bag,
           (least(9, 3 * t.god) - 2 * t.none)::numeric as response,
           case when c.rating >= 3 and c.policy <> 'cargo' then co3.ontime_points(o.rate) else 0 end as ontime,
           case when c.rating >= 3 and c.policy <> 'cargo' then -least(10, o.own_cxl)::numeric else 0 end as own_cxl,
           case when c.rating >= 3 then o.rate end as ontime_rate,
           case when c.rating >= 3 then least(6, 2 * coalesce((select sum(level) from co3_lounges where user_id = p_uid), 0)) else 0 end::numeric as lounge,
           case when c.rating >= 3 then c.miles else 0 end::numeric as miles,
           round(case when c.rating >= 4 and f.n > 0 then 6.0 * f.wf / f.n else 0 end, 2) as wifi
      from c cross join f cross join t cross join o)
  select p.base, p.packed, p.new_share, p.aging, p.policy_adj, p.meal, p.bag, p.response, p.ontime, p.own_cxl, p.ontime_rate, p.lounge, p.miles, p.wifi,
         greatest(0, least(100, p.base + p.packed + p.new_share + p.aging + p.policy_adj + p.meal + p.bag + p.response + p.ontime + p.own_cxl + p.lounge + p.miles + p.wifi))
    from p
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

do $do$
declare src text; n0 text;
begin
  -- 旅客：点検中（予備機なし）の機体の路線は飛ばない・Wi-Fi
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_in_heavy' in src) = 0 then
    n0 := src;
    src := replace(src, 'co3_people_fl(p_uid, e.fl0, e.a, e.b) as fl,', 'case when co3_in_heavy(e.ac_id) then 0 else co3_people_fl(p_uid, e.fl0, e.a, e.b) end as fl,');
    src := replace(src, '* co3.season_fare(k2.a, k2.b) as rev,', '* co3.season_fare(k2.a, k2.b) * co3_wifi_mult(k2.ac_id, k2.biz) as rev,');
    if position('co3_in_heavy' in src) = 0 or position('co3_wifi_mult' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、C点検と Wi-Fi を入れられない'; end if;
    execute src;
  end if;
  -- 維持費：Wi-Fi +10%
  select pg_get_functiondef('public.co3_ac_upkeep(bigint)'::regprocedure) into src;
  if position('a.wifi' in src) = 0 then
    if position('* case when coalesce(co3_rating_need(a.user_id), 1) < 3 then 1.1 else 1 end' in src) = 0 then raise exception 'co3_ac_upkeep の形が変わっていて、Wi-Fi を入れられない'; end if;
    src := replace(src, '* case when coalesce(co3_rating_need(a.user_id), 1) < 3 then 1.1 else 1 end',
                        '* case when coalesce(co3_rating_need(a.user_id), 1) < 3 then 1.1 else 1 end * case when a.wifi then 1.1 else 1 end');
    execute src;
  end if;
  -- 会社の状態：機体に Wi-Fi と点検の予定、点検の一覧
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_heavy' in src) = 0 then
    if position($r$'check_cost', co3_check_cost(id),$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、C点検を入れられない'; end if;
    src := replace(src, $r$'check_cost', co3_check_cost(id),$r$, $r$'check_cost', co3_check_cost(id), 'wifi', wifi, 'wifi_cost', ceil(greatest(paid, (ac_spec(type)).price) * 0.03),
                 'heavy_next', coalesce(heavy_from, (bought_at at time zone 'Asia/Tokyo')::date) + 912,$r$);
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'heavy', case when v3 then coalesce((select jsonb_agg(jsonb_build_object('ac_id', h.aircraft_id, 'kind', h.kind, 'start', h.start_day, 'end', h.end_day,
        'spare_reg', s.reg, 'cost', h.cost) order by h.start_day) from co3_heavy h left join aircraft s on s.id = h.spare_id
        where h.user_id = uid and h.end_day >= (now() at time zone 'Asia/Tokyo')::date), '[]'::jsonb) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-heavy', '35 15 * * *', $job$ select public.co3_heavy_run() $job$) $q$;
  end if;
end
$$;
