-- エアライン経営 co-v3：機内食と預ける荷物（仕様書 第7章「サービス」）
--   機内食：無料・有料・なし（会社ごと）。無料は運航の費用 +2ポイント（搭乗率70%・普通の運賃の収益に対する割合で。
--           LCC 57%→59%・ミドルコスト 64%→66%・FSC など 71%→73%）、有料は収益 +3%
--   預ける荷物：無料・有料（会社ごと）。有料は収益 +4%（LCC は +6%）、旅行の客 −5%
--   満足度の目標値：機内食 無料 +8・有料 −3・なし −8、荷物 有料 −4（貨物の会社は客がいないので0）
--   はじめはどの会社も「機内食なし・荷物無料」（10/27 企画者が決定。方針の標準パックは作らない）
--   収益と費用に効くのは旅客の路線（co3_route_econ）だけ。いつでも変えられる

-- 表：会社に2つの列を足す。companies の RLS はそのまま（自分の会社だけ読める。書くのは関数だけ）
alter table public.companies add column if not exists meal text not null default 'none' check (meal in ('free', 'paid', 'none'));
alter table public.companies add column if not exists bag  text not null default 'free' check (bag in ('free', 'paid'));
alter table public.companies enable row level security;

create or replace function co3.meal_cost_mult(p_policy text, p_meal text) returns numeric
language sql immutable as $$
  select case when p_meal = 'free' then 1 + 0.02 / case p_policy when 'lcc' then 0.57 when 'mcc' then 0.64 else 0.71 end else 1 end::numeric
$$;
create or replace function co3.service_rev_mult(p_policy text, p_meal text, p_bag text) returns numeric
language sql immutable as $$
  select (case when p_meal = 'paid' then 1.03 else 1 end
        * case when p_bag = 'paid' then case when p_policy = 'lcc' then 1.06 else 1.04 end else 1 end)::numeric
$$;
create or replace function co3.service_sat(p_policy text, p_meal text, p_bag text, out meal numeric, out bag numeric)
language sql immutable as $$
  select case when p_policy = 'cargo' then 0 when p_meal = 'free' then 8 when p_meal = 'paid' then -3 else -8 end::numeric,
         case when p_policy = 'cargo' then 0 when p_bag = 'paid' then -4 else 0 end::numeric
$$;
revoke all on function co3.meal_cost_mult(text, text), co3.service_rev_mult(text, text, text), co3.service_sat(text, text, text) from public, anon, authenticated;

-- 機内食と荷物を決める
create or replace function public.co3_set_service(p_meal text, p_bag text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if p_meal not in ('free', 'paid', 'none') or p_bag not in ('free', 'paid') then raise exception 'invalid service'; end if;
  update companies set meal = p_meal, bag = p_bag where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_service(text, text) from public, anon;
grant execute on function public.co3_set_service(text, text) to authenticated;

-- 満足度の目標値に機内食と荷物を足す（中身の列が増えるので作り直す）
drop function if exists public.co3_satisfaction_parts(uuid);
create function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out meal numeric, out bag numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy, meal, bag from companies where user_id = p_uid),
  f as (select count(*) as n,
               count(*) filter (where bought_at > now() - interval '90 days') as fresh,
               avg(ac_age(bought_at)) as age
          from aircraft where user_id = p_uid),
  p as (
    select 50::numeric as base,
           case when c.policy = 'lcc' then -4 else 0 end::numeric as packed,
           round(case when f.n > 0 then 6.0 * f.fresh / f.n else 0 end, 2) as new_share,
           round(case when f.n > 0 then -8 * (1 - f.age) / 0.2 else 0 end, 2) as aging,
           case c.policy when 'fsc' then -5 when 'lcc' then 5 else 0 end::numeric as policy_adj,
           (co3.service_sat(c.policy, c.meal, c.bag)).meal as meal,
           (co3.service_sat(c.policy, c.meal, c.bag)).bag as bag
      from c cross join f)
  select p.base, p.packed, p.new_share, p.aging, p.policy_adj, p.meal, p.bag,
         greatest(0, least(100, p.base + p.packed + p.new_share + p.aging + p.policy_adj + p.meal + p.bag))
    from p
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

-- 路線の計算：機内食の費用、有料の収益、荷物有料の旅行の客 −5%
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('service_rev_mult' in src) = 0 then
    if position('c.policy, c.pct, c.day_no' in src) = 0
       or position('(1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl' in src) = 0
       or position('* co3.fare(k2.km) * k2.fm * k2.mult as rev' in src) = 0
       or position('k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) as cst' in src) = 0 then
      raise exception 'co3_route_econ の形が変わっていて、機内食と荷物を入れられない';
    end if;
    src := replace(src, 'c.policy, c.pct, c.day_no', 'c.policy, c.meal, c.bag, c.pct, c.day_no');
    src := replace(src, '(1 - g.biz) * (co3.policy(g.policy)).leisure_mult * g.sl',
                        '(1 - g.biz) * (co3.policy(g.policy)).leisure_mult * case when g.bag = ''paid'' then 0.95 else 1 end * g.sl');
    src := replace(src, '* co3.fare(k2.km) * k2.fm * k2.mult as rev', '* co3.fare(k2.km) * k2.fm * k2.mult * co3.service_rev_mult(k2.policy, k2.meal, k2.bag) as rev');
    src := replace(src, 'k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) as cst',
                        'k2.fl * co3.flight_cost(k2.policy, k2.seats_eq, k2.km) * co3.meal_cost_mult(k2.policy, k2.meal) as cst');
    execute src;
  end if;
end
$do$;

-- 会社の状態に meal・bag を足す（sat_parts には meal・bag が自然に入る）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''meal'', c.meal' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、機内食と荷物を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'meal', c.meal, 'bag', c.bag,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
