-- エアライン経営 co-v3：ラウンジ・マイル制度・安全への投資と会社の出来事・借金（どれも格付け3から）
--   ラウンジ：空港に建てる（1〜3段、1段 40,000）。その空港の路線で仕事の客 +5%/段（LCC は半分）、満足度 +2/段（会社全体で最大 +6）
--     ゲームの計算では「仕事の客の割合 × 5% × 段」を収益に足す（上級席の埋まり方 +10%/段は、上級席の計算を分けるときに足す）
--   マイル制度：0（なし）・1〜3段。費用は収益の 2%・4%・6%。同じ路線にほかの会社がいるとき、仕事の客 +4%・+8%・+12%
--     続けた日数で効き目が増え、180日で1.5倍（やめると0日から）。満足度 +1〜+3（上級会員）
--   安全への投資：少なめ（費用 +0）・普通（運航の費用 +1ポイント）・手厚い（+3ポイント）。格付け1・2は「普通」扱いの費用なし（いままでどおり）
--   会社の出来事（悪いもの。毎朝4時に引く）：
--     乗員の飲酒問題：1年あたり 0.8回 × 乗員の不足（いる ÷ 要る の逆数）× 満足度（40未満なら1.5）× 安全（少なめ 1.5・普通 1・手厚い 0.4）
--       → 評判 −40、満足度 −10、3日間すべての路線の収益 −20%
--     整備のミス：1年あたり 0.6回 × 整備士の不足 × 古さ（機体の古さ 0〜−20% を 1〜1.5）× 安全
--       → その機種（いちばん多い機種）がすべて2日運休（予備機なし）、評判 −30
--     評判の減点は90日で消える
--   借金：会社の価値（借金を引いたもの）の半分まで。利息は30日ごとに借金の3%（毎朝、30日たった分を引く）。いつでも返せる
--     資金のマイナス・倒産は、まだ作らない（資金は0で止まるまま）

-- ラウンジ
create table if not exists public.co3_lounges (
  user_id uuid not null references auth.users (id) on delete cascade,
  iata text not null,
  level integer not null check (level between 1 and 3),
  built_at timestamptz not null default now(),
  primary key (user_id, iata)
);
alter table public.co3_lounges enable row level security;
revoke all on public.co3_lounges from public, anon, authenticated;
grant select on public.co3_lounges to authenticated;
drop policy if exists co3_lounges_own on public.co3_lounges;
create policy co3_lounges_own on public.co3_lounges for select to authenticated using (user_id = (select auth.uid()));

-- 会社の出来事
create table if not exists public.co3_events (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  day date not null,
  kind text not null check (kind in ('drink', 'maint')),
  until_day date not null,
  ac_type text,
  rep integer not null,
  created_at timestamptz not null default now(),
  unique (user_id, day, kind)
);
create index if not exists co3_events_user on public.co3_events (user_id, day desc);
alter table public.co3_events enable row level security;
revoke all on public.co3_events from public, anon, authenticated;
grant select on public.co3_events to authenticated;
drop policy if exists co3_events_own on public.co3_events;
create policy co3_events_own on public.co3_events for select to authenticated using (user_id = (select auth.uid()));

alter table public.companies add column if not exists miles smallint not null default 0 check (miles between 0 and 3);
alter table public.companies add column if not exists miles_since date;
alter table public.companies add column if not exists safety text not null default 'normal' check (safety in ('low', 'normal', 'high'));
alter table public.companies add column if not exists debt bigint not null default 0 check (debt >= 0);
alter table public.companies add column if not exists debt_at timestamptz;
alter table public.companies enable row level security;

alter table public.co3_news drop constraint if exists co3_news_kind_check;
alter table public.co3_news add constraint co3_news_kind_check check (kind in ('route', 'god', 'rating', 'value', 'slots', 'event'));
alter table public.co3_news enable row level security;

-- いちばん高いラウンジの段（路線の両端）
create or replace function public.co3_lounge_lv(p_uid uuid, p_a text, p_b text) returns integer
language sql stable security definer set search_path = public as $$
  select coalesce(max(level), 0)::int from co3_lounges where user_id = p_uid and iata in (p_a, p_b)
$$;
revoke all on function public.co3_lounge_lv(uuid, text, text) from public, anon, authenticated;

-- マイルの効き目（続けた日数で 1〜1.5倍）
create or replace function public.co3_miles_eff(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select case when c.miles = 0 or coalesce(c.rating, 1) < 3 then 0
                     else 0.04 * c.miles * (1 + 0.5 * least(1, greatest(0, (now() at time zone 'Asia/Tokyo')::date - coalesce(c.miles_since, (now() at time zone 'Asia/Tokyo')::date)) / 180.0)) end
                     from companies c where c.user_id = p_uid), 0)
$$;
revoke all on function public.co3_miles_eff(uuid) from public, anon, authenticated;

-- 収益にかける倍率：ラウンジ・マイル（効き目と費用）・飲酒問題の国の指導
create or replace function public.co3_extra_rev_mult(p_uid uuid, p_a text, p_b text, p_biz numeric, p_policy text, p_others integer) returns numeric
language sql stable security definer set search_path = public as $$
  select (1 + coalesce(p_biz, 0) * 0.05 * co3_lounge_lv(p_uid, p_a, p_b) * case when p_policy = 'lcc' then 0.5 else 1 end)
       * (1 + case when coalesce(p_others, 0) > 0 then coalesce(p_biz, 0) * co3_miles_eff(p_uid) else 0 end)
       * (1 - coalesce((select case when coalesce(c.rating, 1) >= 3 then 0.02 * c.miles else 0 end from companies c where c.user_id = p_uid), 0))
       * case when exists (select 1 from co3_events e where e.user_id = p_uid and e.kind = 'drink'
                             and (now() at time zone 'Asia/Tokyo')::date between e.day and e.until_day) then 0.8 else 1 end
$$;
revoke all on function public.co3_extra_rev_mult(uuid, text, text, numeric, text, integer) from public, anon, authenticated;

-- 安全への投資の費用（運航の費用の倍率。ポイントは機内食と同じ数え方）
create or replace function public.co3_safety_cost_mult(p_uid uuid, p_policy text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select case when coalesce(c.rating, 1) < 3 then 1
                               else 1 + case c.safety when 'normal' then 0.01 when 'high' then 0.03 else 0 end
                                        / case p_policy when 'lcc' then 0.57 when 'mcc' then 0.64 else 0.71 end end
                     from companies c where c.user_id = p_uid), 1)
$$;
revoke all on function public.co3_safety_cost_mult(uuid, text) from public, anon, authenticated;

-- 出来事の評判（90日で消える）
create or replace function public.co3_event_rep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select -coalesce(sum(rep), 0)::bigint from co3_events where user_id = p_uid and day > (now() at time zone 'Asia/Tokyo')::date - 90
$$;
revoke all on function public.co3_event_rep(uuid) from public, anon, authenticated;

-- 1年あたりの起きやすさ
create or replace function public.co3_event_rates(p_uid uuid, out drink numeric, out maint numeric)
language sql stable security definer set search_path = public as $$
  select 0.8 / greatest(0.2, co3_crew_ratio(p_uid)) * case when c.satisfaction < 40 then 1.5 else 1 end * s.m,
         0.6 * co3_mech_mult(p_uid)
             * (1 + least(0.5, greatest(0, (1 - coalesce((select avg(ac_age(a.bought_at)) from aircraft a where a.user_id = p_uid), 1)) / 0.2 * 0.5))) * s.m
    from companies c cross join lateral (select case c.safety when 'low' then 1.5 when 'high' then 0.4 else 1 end as m) s
   where c.user_id = p_uid
$$;
revoke all on function public.co3_event_rates(uuid) from public, anon, authenticated;

-- 毎朝：出来事を引く（会社・日・種類から作る決まった数で）・借金の利息。p_force は試験用（'drink' か 'maint' を必ず起こす）
create or replace function public.co3_events_draw(p_day date default null, p_force text default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); c record; r record; u numeric; t text; n int := 0; k text;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  -- 借金の利息（30日たった分）
  update companies set cash = greatest(0, cash - ceil(debt * 0.03)), debt_at = debt_at + interval '30 days'
   where debt > 0 and debt_at <= now() - interval '30 days';
  for c in select x.user_id, x.policy from companies x where coalesce(x.rating, 1) >= 3 and x.policy <> 'cargo'
             and exists (select 1 from aircraft a where a.user_id = x.user_id and a.route_key is not null) loop
    select * into r from co3_event_rates(c.user_id);
    foreach k in array array['drink', 'maint'] loop
      u := abs(hashtext(c.user_id::text || d::text || k)) / 2147483647.0;
      if not (p_force = k or (p_force is null and u < case k when 'drink' then r.drink else r.maint end / 365.0)) then continue; end if;
      if k = 'drink' then
        insert into co3_events (user_id, day, kind, until_day, rep) values (c.user_id, d, 'drink', d + 2, 40) on conflict do nothing;
        if found then
          perform co3_sat_bump(c.user_id, -10);
          perform co3_news_add(c.user_id, 'event', d::text || 'drink', '乗員の飲酒問題で国の指導', '評判 −40・満足度 −10・3日間 収益 −20%');
          n := n + 1;
        end if;
      else
        select a.type into t from aircraft a where a.user_id = c.user_id and a.route_key is not null group by a.type order by count(*) desc, a.type limit 1;
        insert into co3_events (user_id, day, kind, until_day, ac_type, rep) values (c.user_id, d, 'maint', d + 1, t, 30) on conflict do nothing;
        if found then
          insert into co3_breakdowns (user_id, aircraft_id, route_key, start_day, days, end_day)
            select a.user_id, a.id, a.route_key, d, 2, d + 1 from aircraft a where a.user_id = c.user_id and a.type = t and a.route_key is not null
            on conflict do nothing;
          perform co3_news_add(c.user_id, 'event', d::text || 'maint', '整備のミスで同じ機種がすべて2日運休', '評判 −30');
          n := n + 1;
        end if;
      end if;
    end loop;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_events_draw(date, text) from public, anon, authenticated;

-- 操作：ラウンジを建てる・上げる（拠点の空港か、訪れた混雑空港・拠点以上の空港）
create or replace function public.co3_build_lounge(p_iata text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); lv int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if not exists (select 1 from checkins ch join airports a on a.id = ch.airport_id where ch.user_id = uid and a.iata = p_iata) then raise exception 'not visited'; end if;
  select level into lv from co3_lounges where user_id = uid and iata = p_iata;
  if coalesce(lv, 0) >= 3 then raise exception 'lounge max'; end if;
  if (select cash from companies where user_id = uid) < 40000 then raise exception 'not enough cash'; end if;
  update companies set cash = cash - 40000 where user_id = uid;
  insert into co3_lounges (user_id, iata, level) values (uid, p_iata, 1) on conflict (user_id, iata) do update set level = co3_lounges.level + 1;
  return co_state();
end;
$$;
revoke all on function public.co3_build_lounge(text) from public, anon;
grant execute on function public.co3_build_lounge(text) to authenticated;

create or replace function public.co3_set_miles(p_level integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); cur int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_level not between 0 and 3 then raise exception 'invalid miles'; end if;
  select miles into cur from companies where user_id = uid;
  update companies set miles = p_level,
         miles_since = case when p_level = 0 then null when cur = 0 then (now() at time zone 'Asia/Tokyo')::date else miles_since end
   where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_miles(integer) from public, anon;
grant execute on function public.co3_set_miles(integer) to authenticated;

create or replace function public.co3_set_safety(p_level text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_level not in ('low', 'normal', 'high') then raise exception 'invalid safety'; end if;
  update companies set safety = p_level where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_safety(text) from public, anon;
grant execute on function public.co3_set_safety(text) to authenticated;

-- 借りられる残り（借金を引いた会社の価値の半分 − いまの借金）
create or replace function public.co3_debt_room(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select greatest(0, floor(co_value(p_uid) * 0.5) - (select debt from companies where user_id = p_uid))::bigint
$$;
revoke all on function public.co3_debt_room(uuid) from public, anon, authenticated;

-- 借りる（正）・返す（負）
create or replace function public.co3_borrow(p_amount bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); c record;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_amount is null or p_amount = 0 then raise exception 'invalid amount'; end if;
  select * into c from companies where user_id = uid;
  if p_amount > 0 then
    if p_amount > co3_debt_room(uid) then raise exception 'debt limit'; end if;
    update companies set cash = cash + p_amount, debt = debt + p_amount, debt_at = coalesce(case when debt > 0 then debt_at end, now()) where user_id = uid;
  else
    if -p_amount > c.debt then raise exception 'invalid amount'; end if;
    if -p_amount > c.cash then raise exception 'not enough cash'; end if;
    update companies set cash = cash + p_amount, debt = debt + p_amount, debt_at = case when debt + p_amount = 0 then null else debt_at end where user_id = uid;
  end if;
  return co_state();
end;
$$;
revoke all on function public.co3_borrow(bigint) from public, anon;
grant execute on function public.co3_borrow(bigint) to authenticated;

-- 満足度の内わけ：ラウンジ・マイルを足す（列が増えるので作り直す）
drop function if exists public.co3_satisfaction_parts(uuid);
create function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out meal numeric, out bag numeric,
  out response numeric, out ontime numeric, out own_cxl numeric, out ontime_rate numeric, out lounge numeric, out miles numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy, meal, bag, rating, miles from companies where user_id = p_uid),
  f as (select count(*) as n,
               count(*) filter (where bought_at > now() - interval '90 days') as fresh,
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
           case when c.rating >= 3 then c.miles else 0 end::numeric as miles
      from c cross join f cross join t cross join o)
  select p.base, p.packed, p.new_share, p.aging, p.policy_adj, p.meal, p.bag, p.response, p.ontime, p.own_cxl, p.ontime_rate, p.lounge, p.miles,
         greatest(0, least(100, p.base + p.packed + p.new_share + p.aging + p.policy_adj + p.meal + p.bag + p.response + p.ontime + p.own_cxl + p.lounge + p.miles))
    from p
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

do $do$
declare src text; n0 text;
begin
  -- 旅客の収益と費用
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_extra_rev_mult' in src) = 0 then
    n0 := src;
    src := replace(src, '* co3.service_rev_mult(k2.policy, k2.meal, k2.bag) as rev,',
                        '* co3.service_rev_mult(k2.policy, k2.meal, k2.bag) * co3_extra_rev_mult(p_uid, k2.a, k2.b, k2.biz, k2.policy, k2.n_other) as rev,');
    src := replace(src, '* co3_ground_mult(p_uid, k2.a, k2.b) as cst,', '* co3_ground_mult(p_uid, k2.a, k2.b) * co3_safety_cost_mult(p_uid, k2.policy) as cst,');
    if position('co3_extra_rev_mult' in src) = 0 or position('co3_safety_cost_mult' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、ラウンジ・マイル・安全を入れられない'; end if;
    execute src;
  end if;
  -- 評判に出来事を足す
  select pg_get_functiondef('public.co_rep_points(uuid)'::regprocedure) into src;
  if position('co3_event_rep' in src) = 0 then
    if position('+ co3_ontime_rep(p_uid)' in src) = 0 then raise exception 'co_rep_points の形が変わっていて、出来事を入れられない'; end if;
    src := replace(src, '+ co3_ontime_rep(p_uid)', '+ co3_ontime_rep(p_uid)' || chr(10) || '       + co3_event_rep(p_uid)');
    execute src;
  end if;
  -- 会社の価値から借金を引く
  select pg_get_functiondef('public.co_value(uuid)'::regprocedure) into src;
  if position('debt' in src) = 0 then
    if position('+ greatest(co_daily(p_uid), 0) * 30' in src) = 0 then raise exception 'co_value の形が変わっていて、借金を入れられない'; end if;
    src := replace(src, '+ greatest(co_daily(p_uid), 0) * 30', '+ greatest(co_daily(p_uid), 0) * 30' || chr(10) || '       - coalesce((select debt from companies where user_id = p_uid), 0)');
    execute src;
  end if;
  -- 会社の状態
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_debt_room' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、ラウンジ・マイル・借金を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'money3', case when v3 then jsonb_build_object(
        'lounges', coalesce((select jsonb_agg(jsonb_build_object('iata', l.iata, 'level', l.level) order by l.iata) from co3_lounges l where l.user_id = uid), '[]'::jsonb),
        'miles', c.miles, 'miles_since', c.miles_since, 'miles_eff', co3_miles_eff(uid), 'safety', c.safety,
        'debt', c.debt, 'debt_room', co3_debt_room(uid), 'debt_next', case when c.debt > 0 then c.debt_at + interval '30 days' end,
        'rates', (select to_jsonb(r) from co3_event_rates(uid) r),
        'events', coalesce((select jsonb_agg(jsonb_build_object('day', e.day, 'kind', e.kind, 'until', e.until_day, 'type', e.ac_type) order by e.day desc)
                              from co3_events e where e.user_id = uid and e.day > (now() at time zone 'Asia/Tokyo')::date - 90), '[]'::jsonb)) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-events', '5 19 * * *', $job$ select public.co3_events_draw() $job$) $q$;
  end if;
end
$$;
