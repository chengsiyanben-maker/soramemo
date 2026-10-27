-- エアライン経営 co-v3：臨時便（仕様書「臨時便」。格付け3から）
--   全国の繁忙期（旅行の客が増える時期：年末年始・GW・お盆・夏休み・春休み）のあいだだけ、予備機（路線に入れていない旅客機）に
--   自社の路線の臨時便を組める。期間はその繁忙期の終わりまで（終わると自動で予備機に戻る）。1機1路線、1日2〜8便（往復の数）
--   臨時便の客は「繁忙期で増えた旅行の客」だけ：その路線の客（前の28日の本物の便から。econ の demand）× 旅行の割合 ×（旅行の倍率 − 1）
--     × 自社の取り分（いまの自社の客 ÷ 路線の客）。席の85%まで
--   収益は運賃 × 方針の運賃 × 繁忙期の運賃。費用は運航の費用と着陸料（いつもの便と同じ計算）
--   混雑空港の便は、その月の自社の発着枠に数えない（ゲームを軽くするため。あとで見直す）
--   臨時便の間は、その機体は故障の代わり（予備機）には飛べない
--   「繁忙期に帰省客を運びきった」（臨時便を出した繁忙期に欠航がなかった）は、出来事の仕組みでよい出来事を作るときに足す

create table if not exists public.co3_extra (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  aircraft_id bigint not null references public.aircraft (id) on delete cascade,
  route_key text not null,
  flights integer not null check (flights in (2, 4, 6, 8)),
  start_day date not null,
  end_day date not null,
  created_at timestamptz not null default now(),
  check (end_day >= start_day)
);
create index if not exists co3_extra_user on public.co3_extra (user_id, end_day);
alter table public.co3_extra enable row level security;
revoke all on public.co3_extra from public, anon, authenticated;
grant select on public.co3_extra to authenticated;
drop policy if exists co3_extra_own on public.co3_extra;
create policy co3_extra_own on public.co3_extra for select to authenticated using (user_id = (select auth.uid()));

-- いまの繁忙期の最後の日（繁忙期でなければ null）
create or replace function co3.peak_end(p_day date) returns date
language sql stable as $$
  select case when (co3.season_nat(p_day)).lei > 1 then
    (select max(g::date) from generate_series(p_day, p_day + 60, interval '1 day') g
      where (co3.season_nat(g::date)).name = (co3.season_nat(p_day)).name
        and not exists (select 1 from generate_series(p_day, g::date, interval '1 day') h where (co3.season_nat(h::date)).name is distinct from (co3.season_nat(p_day)).name)) end
$$;
revoke all on function co3.peak_end(date) from public, anon, authenticated;

create or replace function co3.today() returns date
language sql stable as $$ select coalesce(nullif(current_setting('co3.season_day', true), '')::date, (now() at time zone 'Asia/Tokyo')::date) $$;
revoke all on function co3.today() from public, anon, authenticated;

-- 臨時便の稼ぎ（その日に飛んでいるもの）
create or replace function public.co3_extra_econ(p_uid uuid)
returns table (id bigint, aircraft_id bigint, route_key text, flights integer, end_day date, pax numeric, revenue numeric, cost numeric, landing numeric, profit numeric)
language sql stable security definer set search_path = public as $$
  with x as (
    select x.*, e.a, e.b, e.km, e.kind, e.demand, e.carried, e.intl, c.policy,
           (co3_ac_spec(x.aircraft_id)).seats as seats, (co3_ac_spec(x.aircraft_id)).noise as noise, (co3_ac_spec(x.aircraft_id)).mtow as mtow,
           case e.kind when 'big' then 0.60 when 'resort' then 0.12 else 0.45 end as biz0,
           (co3.season(e.a, e.b, co3.today())).lei as lei, (co3.season(e.a, e.b, co3.today())).fare as sfare
      from co3_extra x
      join co3_route_econ(p_uid) e on e.route_key = x.route_key
      join companies c on c.user_id = x.user_id
     where x.user_id = p_uid and co3.today() between x.start_day and x.end_day
  ), p as (
    select x.*, least(x.flights * x.seats * 0.85,
                      greatest(0, x.demand * (1 - x.biz0) * (x.lei - 1) * least(1, x.carried / nullif(x.demand, 0)))) as pax
      from x
  )
  select p.id, p.aircraft_id, p.route_key, p.flights, p.end_day, round(p.pax, 1),
         round(p.pax * co3.fare(p.km) * (co3.policy(p.policy)).fare_mult * p.sfare, 2),
         round(p.flights * co3.flight_cost(p.policy, p.seats, p.km), 2),
         round(case when p.flights > 0 then p.flights * co3.landing_fee(p.intl, false, p.pax / p.flights, p.noise, p.mtow, false, co3.is_island(p.a) or co3.is_island(p.b)) else 0 end, 2),
         round(p.pax * co3.fare(p.km) * (co3.policy(p.policy)).fare_mult * p.sfare - p.flights * co3.flight_cost(p.policy, p.seats, p.km)
               - case when p.flights > 0 then p.flights * co3.landing_fee(p.intl, false, p.pax / p.flights, p.noise, p.mtow, false, co3.is_island(p.a) or co3.is_island(p.b)) else 0 end, 2)
    from p
$$;
revoke all on function public.co3_extra_econ(uuid) from public, anon, authenticated;

-- 臨時便を組む
create or replace function public.co3_set_extra(p_aircraft bigint, p_route text, p_flights integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); d date := co3.today(); pe date; ac record; r record;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  pe := co3.peak_end(d);
  if pe is null then raise exception 'not peak'; end if;
  if p_flights not in (2, 4, 6, 8) then raise exception 'invalid flights'; end if;
  select * into ac from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  if ac.route_key is not null or exists (select 1 from co3_sched s where s.aircraft_id = ac.id) or co3_is_freighter(ac.id) or co3_is_bizjet(ac.id) then raise exception 'not a spare'; end if;
  if exists (select 1 from co3_extra x where x.aircraft_id = ac.id and x.end_day >= d) then raise exception 'already extra'; end if;
  if exists (select 1 from co3_breakdowns b where (b.aircraft_id = ac.id or b.spare_id = ac.id) and b.end_day >= d) then raise exception 'not a spare'; end if;
  select * into r from co_routes(uid) x where x.route_key = p_route;
  if not found then raise exception 'route not found'; end if;
  if r.min_size < (ac_spec(ac.type)).min_size then raise exception 'too small'; end if;
  if r.intl and not ac.intl then raise exception 'not intl'; end if;
  insert into co3_extra (user_id, aircraft_id, route_key, flights, start_day, end_day) values (uid, ac.id, p_route, p_flights, d, pe);
  return co_state();
end;
$$;
revoke all on function public.co3_set_extra(bigint, text, integer) from public, anon;
grant execute on function public.co3_set_extra(bigint, text, integer) to authenticated;

-- 途中でやめる（その日から予備機に戻る）
create or replace function public.co3_stop_extra(p_id bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  delete from co3_extra where id = p_id and user_id = uid and start_day >= co3.today();
  update co3_extra set end_day = co3.today() - 1 where id = p_id and user_id = uid and end_day >= co3.today();
  return co_state();
end;
$$;
revoke all on function public.co3_stop_extra(bigint) from public, anon;
grant execute on function public.co3_stop_extra(bigint) to authenticated;

-- 1日の稼ぎに臨時便を足す
create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select (coalesce((select round(sum(profit)) from co3_route_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_cargo_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_pj_econ(p_uid)), 0)
        + coalesce((select round(sum(earn)) from co3_regional_jobs(p_uid)), 0)
        + coalesce((select round(sum(subsidy)) from co3_regional_subsidy(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_extra_econ(p_uid)), 0))::bigint
$$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

do $do$
declare src text; n0 text;
begin
  -- 臨時便の機体は予備機にならない
  select pg_get_functiondef('public.co3_breakdown_draw(date)'::regprocedure) into src;
  if position('co3_extra' in src) = 0 then
    n0 := src;
    src := replace(src, 'and not exists (select 1 from co3_breakdowns b where b.spare_id = s.id and b.end_day >= d)',
                        'and not exists (select 1 from co3_breakdowns b where b.spare_id = s.id and b.end_day >= d)' || chr(10) ||
                        '       and not exists (select 1 from co3_extra x where x.aircraft_id = s.id and d between x.start_day and x.end_day)');
    if src = n0 then raise exception 'co3_breakdown_draw の形が変わっていて、臨時便を入れられない'; end if;
    execute src;
  end if;
  -- 会社の状態
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_extra_econ' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、臨時便を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'extra', case when v3 then jsonb_build_object('peak_end', co3.peak_end(co3.today()),
        'list', coalesce((select jsonb_agg(jsonb_build_object('id', x.id, 'ac_id', x.aircraft_id, 'k', x.route_key, 'flights', x.flights, 'end', x.end_day,
                                                              'pax', x.pax, 'revenue', x.revenue, 'cost', x.cost, 'landing', x.landing, 'profit', x.profit))
                            from co3_extra_econ(uid) x), '[]'::jsonb)) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
