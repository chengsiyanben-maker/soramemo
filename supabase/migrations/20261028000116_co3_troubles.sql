-- エアライン経営 co-v3：トラブルの対応と「神対応」（1日まとめの形。10/27 企画者が決定）
--   仕様書は「便ごとに出発の3時間前に決める」形だが、co-v3 はまだ便の時刻を持たないので、まず1日まとめで作る：
--   毎朝7時（日本時間）に、前の日の本物の欠航の割合（co_sky、国内線）から、自社の路線で欠航した便の数を決める
--     欠航した便 ＝ 四捨五入（自社の1日の便数 × 本物の欠航 ÷（本物の飛んだ便 ＋ 欠航））。1便以上ならトラブル
--   対応できるのは6時間（13時まで）。はじめの1時間（8時まで）に合うカードを使うと「神対応」
--   カード：振替の手配（欠航に合う、その便の収益の20%）・ホテルの手配（30%）・軽食とおわび（10%）。
--     1日まとめでは欠航の時刻と原因が分からないので、合うのは振替の手配だけ（ほかは「ふつうの対応」）
--   結果：神対応 ＝ 満足度その日 +8・評判 +15（7日で +30まで）／ふつう ＝ 変わらない／対応なし ＝ 満足度 −2・評判 −5
--   満足度の目標値「対応（前の30日）」：神対応1回 +3（最大 +9）、対応なし −2/回
--   欠航した便の収益は、前からある「実際の空」（co_sky の倍率）で減っているので、ここでは引かない（カードの費用は引く）
--   「自動で対応する」をオンにすると、トラブルが決まったときに振替の手配でふつうの対応をする（神対応にはならない）
--   遅れ・機体の故障・定時率は、便の時刻を作るときに足す

alter table public.companies add column if not exists auto_trouble boolean not null default false;
alter table public.companies enable row level security;

-- 表：トラブル。自分の分だけ読める。書くのは関数だけ
create table if not exists public.co3_troubles (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  route_key   text not null,
  day         date not null,                     -- 欠航した日（前の日）
  flights     integer not null,                  -- 自社のその日の便数
  cancelled   integer not null check (cancelled >= 1),
  real_n      integer not null,                  -- 本物の飛んだ便
  real_cxl    integer not null,                  -- 本物の欠航
  rev_flight  numeric not null,                  -- 1便あたりの収益（カードの費用の元）
  created_at  timestamptz not null default now(),
  god_until   timestamptz not null,
  deadline    timestamptz not null,
  card        text check (card in ('transfer', 'hotel', 'snack')),
  cost        numeric,
  result      text check (result in ('god', 'normal', 'none')),
  auto        boolean not null default false,
  done_at     timestamptz,
  unique (user_id, route_key, day)
);
create index if not exists co3_troubles_user on public.co3_troubles (user_id, created_at desc);
alter table public.co3_troubles enable row level security;
revoke all on public.co3_troubles from public, anon, authenticated;
grant select on public.co3_troubles to authenticated;
drop policy if exists "own troubles" on public.co3_troubles;
create policy "own troubles" on public.co3_troubles for select to authenticated using (user_id = auth.uid());

create or replace function co3.card_rate(p_card text) returns numeric
language sql immutable as $$ select case p_card when 'transfer' then 0.20 when 'hotel' then 0.30 when 'snack' then 0.10 end::numeric $$;
create or replace function co3.card_fits(p_card text) returns boolean
language sql immutable as $$ select p_card = 'transfer' $$;
revoke all on function co3.card_rate(text), co3.card_fits(text) from public, anon, authenticated;

-- 満足度をその場で動かす（0〜100）
create or replace function public.co3_sat_bump(p_uid uuid, p_delta numeric) returns void
language sql security definer set search_path = public as $$
  update companies set satisfaction = greatest(0, least(100, satisfaction + p_delta)) where user_id = p_uid
$$;
revoke all on function public.co3_sat_bump(uuid, numeric) from public, anon, authenticated;

-- 対応する（本人）。p_at は試験用（本番は now()）
create or replace function public.co3_trouble_do(p_uid uuid, p_id bigint, p_card text, p_auto boolean, p_at timestamptz default now()) returns text
language plpgsql security definer set search_path = public as $$
declare t co3_troubles; res text; c numeric;
begin
  select * into t from co3_troubles where id = p_id and user_id = p_uid for update;
  if not found then raise exception 'trouble not found'; end if;
  if t.result is not null then raise exception 'already done'; end if;
  if p_card not in ('transfer', 'hotel', 'snack') then raise exception 'invalid card'; end if;
  if p_at > t.deadline then raise exception 'too late'; end if;
  c := round(co3.card_rate(p_card) * t.rev_flight * t.cancelled, 2);
  update companies set cash = cash - ceil(c) where user_id = p_uid and cash >= ceil(c);
  if not found then raise exception 'not enough cash'; end if;
  res := case when not p_auto and p_at <= t.god_until and co3.card_fits(p_card) then 'god' else 'normal' end;
  update co3_troubles set card = p_card, cost = c, result = res, auto = p_auto, done_at = p_at where id = p_id;
  if res = 'god' then perform co3_sat_bump(p_uid, 8); end if;
  return res;
end;
$$;
revoke all on function public.co3_trouble_do(uuid, bigint, text, boolean, timestamptz) from public, anon, authenticated;

create or replace function public.co3_trouble_respond(p_id bigint, p_card text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  perform co3_trouble_do(uid, p_id, p_card, false);
  return co_state();
end;
$$;
revoke all on function public.co3_trouble_respond(bigint, text) from public, anon;
grant execute on function public.co3_trouble_respond(bigint, text) to authenticated;

create or replace function public.co3_set_auto_trouble(p_on boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  update companies set auto_trouble = coalesce(p_on, false) where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_auto_trouble(boolean) from public, anon;
grant execute on function public.co3_set_auto_trouble(boolean) to authenticated;

-- 毎朝：前の日の本物の欠航から、自社の路線のトラブルを決める。p_at は試験用
create or replace function public.co3_trouble_detect(p_at timestamptz default now()) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := (p_at at time zone 'Asia/Tokyo')::date - 1; r record; tid bigint; n integer := 0;
        start_at timestamptz := greatest(p_at, ((p_at at time zone 'Asia/Tokyo')::date + time '07:00') at time zone 'Asia/Tokyo');
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for r in
    select c.user_id, c.auto_trouble, e.route_key, e.flights, e.revenue, s.n as real_n, s.cxl as real_cxl,
           round(e.flights * s.cxl::numeric / nullif(s.n + s.cxl, 0))::int as cxl_fl
      from companies c
      cross join lateral co3_route_econ(c.user_id) e
      join co_sky s on s.route_key = e.route_key and s.day = d
     where c.policy in ('fsc', 'mcc', 'lcc', 'regional') and not e.intl and e.flights > 0 and s.cxl > 0
  loop
    continue when r.cxl_fl < 1;
    insert into co3_troubles (user_id, route_key, day, flights, cancelled, real_n, real_cxl, rev_flight, created_at, god_until, deadline)
    values (r.user_id, r.route_key, d, r.flights, least(r.cxl_fl, r.flights), r.real_n, r.real_cxl, round(r.revenue / r.flights, 2),
            start_at, start_at + interval '1 hour', start_at + interval '6 hours')
    on conflict (user_id, route_key, day) do nothing
    returning id into tid;
    if tid is null then continue; end if;
    n := n + 1;
    if r.auto_trouble then
      begin perform co3_trouble_do(r.user_id, tid, 'transfer', true, start_at); exception when others then null; end;
    end if;
    tid := null;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_trouble_detect(timestamptz) from public, anon, authenticated;

-- 毎時：締め切りを過ぎて対応していないトラブルを「対応なし」に（満足度 −2）
create or replace function public.co3_trouble_expire(p_at timestamptz default now()) returns integer
language plpgsql security definer set search_path = public as $$
declare r record; n integer := 0;
begin
  for r in update co3_troubles set result = 'none', done_at = deadline
            where result is null and deadline < p_at returning user_id
  loop
    perform co3_sat_bump(r.user_id, -2); n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_trouble_expire(timestamptz) from public, anon, authenticated;

-- 評判：神対応 +15（7日ごとに +30まで）、対応なし −5
create or replace function public.co3_trouble_rep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select coalesce((select sum(least(30, 15 * g)) from (
           select count(*) filter (where result = 'god') as g from co3_troubles where user_id = p_uid
            group by floor(extract(epoch from created_at) / (7 * 86400))) w), 0)::bigint
       - 5 * (select count(*) from co3_troubles where user_id = p_uid and result = 'none')
$$;
revoke all on function public.co3_trouble_rep(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_rep_points(uuid)'::regprocedure) into src;
  if position('co3_trouble_rep' in src) = 0 then
    -- 本番の関数の文は、改行の文字などが手元と違うことがある（10/29 の反映で止まった）ので、終わりの形を広く見る
    if src ~ '\* 10\s*\$function\$' then
      src := regexp_replace(src, '\* 10\s*\$function\$', '* 10' || chr(10) || '       + co3_trouble_rep(p_uid)' || chr(10) || '$function$');
      execute src;
    else
      -- それでも合わなければ、もとの関数を co_rep_points_base に残し、その上に足す形で作り直す
      execute 'alter function public.co_rep_points(uuid) rename to co_rep_points_base';
      execute $f$create function public.co_rep_points(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $b$
  select co_rep_points_base(p_uid)
       + co3_trouble_rep(p_uid)
$b$$f$;
      execute 'revoke all on function public.co_rep_points_base(uuid) from public, anon, authenticated';
      execute 'revoke all on function public.co_rep_points(uuid) from public, anon, authenticated';
    end if;
  end if;
end
$do$;

-- 満足度の目標値に「対応（前の30日）」を足す（列が増えるので作り直す）
drop function if exists public.co3_satisfaction_parts(uuid);
create function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out meal numeric, out bag numeric,
  out response numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy, meal, bag from companies where user_id = p_uid),
  f as (select count(*) as n,
               count(*) filter (where bought_at > now() - interval '90 days') as fresh,
               avg(ac_age(bought_at)) as age
          from aircraft where user_id = p_uid),
  t as (select count(*) filter (where result = 'god') as god, count(*) filter (where result = 'none') as none
          from co3_troubles where user_id = p_uid and created_at > now() - interval '30 days'),
  p as (
    select 50::numeric as base,
           case when c.policy = 'lcc' then -4 else 0 end::numeric as packed,
           round(case when f.n > 0 then 6.0 * f.fresh / f.n else 0 end, 2) as new_share,
           round(case when f.n > 0 then -8 * (1 - f.age) / 0.2 else 0 end, 2) as aging,
           case c.policy when 'fsc' then -5 when 'lcc' then 5 else 0 end::numeric as policy_adj,
           (co3.service_sat(c.policy, c.meal, c.bag)).meal as meal,
           (co3.service_sat(c.policy, c.meal, c.bag)).bag as bag,
           (least(9, 3 * t.god) - 2 * t.none)::numeric as response
      from c cross join f cross join t)
  select p.base, p.packed, p.new_share, p.aging, p.policy_adj, p.meal, p.bag, p.response,
         greatest(0, least(100, p.base + p.packed + p.new_share + p.aging + p.policy_adj + p.meal + p.bag + p.response))
    from p
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

-- 会社の状態に、前の7日のトラブルと「自動で対応する」を足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''troubles'', case when v3' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、トラブルを入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'troubles', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('id', t.id, 'k', t.route_key, 'day', t.day, 'flights', t.flights,
                 'cancelled', t.cancelled, 'real_n', t.real_n, 'real_cxl', t.real_cxl, 'rev_flight', t.rev_flight,
                 'created_at', t.created_at, 'god_until', t.god_until, 'deadline', t.deadline,
                 'card', t.card, 'cost', t.cost, 'auto', t.auto, 'done_at', t.done_at,
                 'result', coalesce(t.result, case when t.deadline < now() then 'none' end)) order by t.created_at desc), '[]'::jsonb)
                 from co3_troubles t where t.user_id = uid and t.created_at > now() - interval '7 days') end,
    'auto_trouble', c.auto_trouble,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-trouble-detect', '0 22 * * *', $job$ select public.co3_trouble_detect() $job$) $q$;
    execute $q$ select cron.schedule('co3-trouble-expire', '5 * * * *', $job$ select public.co3_trouble_expire() $job$) $q$;
  end if;
end
$$;
