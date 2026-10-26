-- エアライン経営 co-v3：地域航空の会社（仕様書 10/24〜25）
--   ・方針に「地域航空」（regional）。運賃は FSC の1.1倍、赤字の線50%。上級席なし
--   ・小型機6機種（セスナ172・アイランダー・キャラバン・PC-12・R44・H125）は見ていなくてもいつでも買える。
--     登録記号はゲーム用の「SM-」で始まる記号、値段は機種の表のまま（持っている機体1機ごとの +25% は 0.5機と数える）
--   ・仕事：路線に入れていない小型機・プロペラ機・ヘリを、もうかる仕事から自動で割り当てる
--       遊覧：本拠地の空港で、観光地の度合い × 6機まで。1機1日 席数 × 3.8 × 度合い
--       チャーター・撮影・測量：前の7日にチェックインした空港ごとに3件（1件で1機を7日使う）。1機1日 席数 × 4.3
--   ・定期便の補助（地域航空の会社の旅客の路線だけ）：
--       地方の路線は「搭乗率保証」：搭乗率60%を下回った分の運賃を自治体が払い、上回った分の稼ぎの半分を自治体に返す
--       離島の路線は「赤字の補填」：赤字を国と県が補う（赤字にはならないが、もうけも出ない）
--   ・観光地の度合い：仕様書に空港ごとの決め方がないので、はじめはリゾートの空港 1.5・ほかの離島 1.3・それ以外 1.0。運営が表で直す

alter table public.companies drop constraint if exists companies_policy_check;
alter table public.companies add constraint companies_policy_check check (policy in ('fsc', 'mcc', 'lcc', 'cargo', 'pj', 'regional'));

create or replace function co3.policy(p text,
  out fare_mult numeric, out breakeven numeric, out biz_mult numeric, out leisure_mult numeric, out premium_share numeric)
language sql immutable as $$
  select f, b, bz, ls, pr from (values
    ('fsc', 1.00, 0.50, 1.0, 0.85, 0.2),
    ('mcc', 0.85, 0.45, 1.1, 1.15, 0.1),
    ('lcc', 0.72, 0.40, 0.4, 1.70, 0.0),
    ('cargo', 1.00, 0.35, 0.0, 0.00, 0.0),
    ('pj', 1.00, 0.45, 0.0, 0.00, 0.0),
    ('regional', 1.10, 0.50, 1.0, 1.00, 0.0)
  ) t(k, f, b, bz, ls, pr) where k = p
$$;

create or replace function public.co3_set_policy(p_policy text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  if p_policy not in ('fsc', 'mcc', 'lcc', 'cargo', 'pj', 'regional') then raise exception 'invalid policy'; end if;
  perform co_check(uid);
  perform co_settle(uid);
  update companies set policy = p_policy,
         premium = case when premium is not null and co3.premium_ok(p_policy, premium) then premium end
   where user_id = uid;
  return co_state();
end;
$$;

-- 上級席は旅客の3方針だけ（貨物・プライベートジェット・地域航空は0%）
create or replace function co3.premium_ok(p_policy text, p_pct integer) returns boolean
language sql immutable as $$
  select case p_policy when 'fsc' then p_pct in (0, 10, 20, 30) when 'mcc' then p_pct in (0, 10) else p_pct = 0 end
$$;

-- 観光地の度合い（0.5〜1.5）。運営が直す表。ない空港は 1.0
create table if not exists public.co3_tourism (
  iata   text primary key check (iata ~ '^[A-Z]{3}$'),
  degree numeric not null check (degree between 0.5 and 1.5)
);
alter table public.co3_tourism enable row level security;
revoke all on public.co3_tourism from public, anon, authenticated;
grant select on public.co3_tourism to anon, authenticated;
drop policy if exists "tourism is public" on public.co3_tourism;
create policy "tourism is public" on public.co3_tourism for select to anon, authenticated using (true);
insert into public.co3_tourism (iata, degree)
select iata, case when co3.is_resort(iata) then 1.5 else 1.3 end from public.airports
 where iata ~ '^[A-Z]{3}$' and (co3.is_resort(iata) or co3.is_island(iata))
on conflict (iata) do nothing;

create or replace function public.co3_degree(p_iata text) returns numeric
language sql stable security definer set search_path = public as $$ select coalesce((select degree from co3_tourism where iata = p_iata), 1.0) $$;
revoke all on function public.co3_degree(text) from public, anon, authenticated;

-- 地域航空の仕事に使える機体：小型機・ヘリ・プロペラ機（騒音の区分が none か prop）
create or replace function public.co3_is_light(p_aircraft bigint) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select (co3_ac_spec(p_aircraft)).noise in ('none', 'prop')), false)
$$;
revoke all on function public.co3_is_light(bigint) from public, anon, authenticated;

-- 小型機を買う（見ていなくてもいつでも）
create or replace function public.co3_buy_small(p_code text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); t co3_types; price bigint; v_reg text;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into t from co3_types where code = p_code and kind in ('small', 'heli');
  if not found then raise exception 'not a small aircraft'; end if;
  price := round(t.price * (1 + 0.25 * (select coalesce(sum(co3.count_weight(coalesce(x.kind in ('small', 'heli'), a.type = 'prop'))), 0)
                                          from aircraft a left join co3_types x on x.code = a.co3_code where a.user_id = uid)))::bigint;
  update companies set cash = cash - price, bought = bought + 1 where user_id = uid and cash >= price;
  if not found then raise exception 'not enough cash'; end if;
  loop
    v_reg := 'SM-' || upper(substr(md5(gen_random_uuid()::text), 1, 4));
    exit when not exists (select 1 from aircraft a where a.reg = v_reg);
  end loop;
  insert into aircraft (user_id, type, reg, icao, paid, co3_code, seen) values (uid, 'prop', v_reg, left(coalesce(t.icao[1], t.code), 8), price, t.code, false);
  return co_state();
end;
$$;
revoke all on function public.co3_buy_small(text) from public, anon;
grant execute on function public.co3_buy_small(text) to authenticated;

-- 仕事の割り当て：路線に入れていない軽い機体を、1機1日の稼ぎが大きい仕事から順に入れる
create or replace function public.co3_regional_jobs(p_uid uuid)
returns table (aircraft_id bigint, job text, airport text, seats numeric, earn numeric)
language plpgsql stable security definer set search_path = public as $$
#variable_conflict use_column
declare c record; home text; deg numeric; n_charter integer; mult numeric;
begin
  select co.*, (now() at time zone 'Asia/Tokyo')::date - (co.created_at at time zone 'Asia/Tokyo')::date + 1 as day_no into c
    from companies co where co.user_id = p_uid;
  if not found or c.policy <> 'regional' then return; end if;
  select iata into home from airports where id = c.home_airport;
  deg := co3_degree(home);
  select co3.charter_jobs_per_week(count(distinct ch.airport_id)::int) into n_charter
    from checkins ch where ch.user_id = p_uid and ch.created_at > now() - interval '7 days' and not ('impossible_speed' = any (ch.flags));
  mult := co3.newbie_mult(c.day_no);
  return query
  with ac as (
    select a.id, (co3_ac_spec(a.id)).seats as s, co3_ac_earn(a.id) as e
      from aircraft a where a.user_id = p_uid and a.route_key is null and co3_is_light(a.id)
  ), slots as (
    select 'sightseeing'::text as job, home as ap, g as no, 3.8 * least(1.5, greatest(0.5, deg)) as per_seat
      from generate_series(1, case when home is null then 0 else co3.sightseeing_cap(deg) end) g
    union all
    select 'charter', null, g, 4.3 from generate_series(1, coalesce(n_charter, 0)) g
  ), ac_r as (select ac.*, row_number() over (order by ac.s desc, ac.id) as rn from ac),
  sl_r as (select slots.*, row_number() over (order by per_seat desc, job, no) as rn from slots)
  -- 席の多い機体から、1席あたりの稼ぎが大きい仕事に入れる
  select ac_r.id, sl_r.job, sl_r.ap, ac_r.s, round(ac_r.s * sl_r.per_seat * ac_r.e * mult, 2)
    from ac_r join sl_r on sl_r.rn = ac_r.rn;
end;
$$;
revoke all on function public.co3_regional_jobs(uuid) from public, anon, authenticated;

-- 定期便の補助（地域航空の会社の旅客の路線）
create or replace function public.co3_regional_subsidy(p_uid uuid)
returns table (route_key text, kind text, load numeric, subsidy numeric)
language sql stable security definer set search_path = public as $$
  select e.route_key,
         case when co3.is_island(e.a) or co3.is_island(e.b) then 'island' else 'local' end,
         round(e.carried / nullif(e.flights * e.seats, 0), 3),
         round(case
           when co3.is_island(e.a) or co3.is_island(e.b) then greatest(0, -e.profit)
           when e.carried <= 0 then 0
           -- 搭乗率保証60%：下回った分の運賃をもらう、上回った分の稼ぎの半分を返す
           when e.carried < 0.6 * e.flights * e.seats then (0.6 * e.flights * e.seats - e.carried) * e.revenue / e.carried
           else -0.5 * (e.carried - 0.6 * e.flights * e.seats) * e.revenue / e.carried end, 2)
    from co3_route_econ(p_uid) e
   where e.flights > 0 and (select policy from companies where user_id = p_uid) = 'regional'
$$;
revoke all on function public.co3_regional_subsidy(uuid) from public, anon, authenticated;

create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select (coalesce((select round(sum(profit)) from co3_route_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_cargo_econ(p_uid)), 0)
        + coalesce((select round(sum(profit)) from co3_pj_econ(p_uid)), 0)
        + coalesce((select round(sum(earn)) from co3_regional_jobs(p_uid)), 0)
        + coalesce((select round(sum(subsidy)) from co3_regional_subsidy(p_uid)), 0))::bigint
$$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

-- 会社の状態に地域航空の仕事と補助を足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_regional_jobs' in src) = 0 then
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'jobs', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('ac_id', j.aircraft_id, 'job', j.job, 'airport', j.airport, 'seats', j.seats, 'earn', j.earn)), '[]'::jsonb) from co3_regional_jobs(uid) j) end,
    'subsidy', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('k', x.route_key, 'kind', x.kind, 'load', x.load, 'subsidy', x.subsidy)), '[]'::jsonb) from co3_regional_subsidy(uid) x) end,
    'satisfaction', c.satisfaction,$r$);
    if position('co3_regional_jobs' in src) = 0 then raise exception 'co_state の形が変わっていて、地域航空を入れられない'; end if;
    execute src;
  end if;
end
$do$;
