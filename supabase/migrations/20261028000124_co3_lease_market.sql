-- エアライン経営 co-v3：リースと中古機（仕様書5章「リース」「中古機」）
--   リース（格付け1から）：乗った・見た機体を、お金を払わずに借りる。毎日、機体の値段の0.15%（見ただけの旅客機は0.2%）を払う（維持費に足す）
--     値段は買うときと同じ計算（最初の1機の半額は使わない）。見ただけの旅客機の差（稼ぎ0.85〜・維持費+30%・1日3機・半分まで）はそのまま
--     借りられるのは「2機＋自社機2機ごとに1機」まで。いつでも返せる（お金は戻らない）。売ることはできない
--     リースの機体は、会社の価値と、値段の「持っている機体1機ごとに +25%」には数えない。格付けの機体の数には数える（仕様書）
--   中古機（格付け2から）：自社機を、いまの値段の30〜150%で売りに出す（7日間。売れなければ戻る）。売れたら値段の5%は手数料
--     買えるのは、その機種に乗った（見た）会社だけ。登録記号・古さ・特別塗装は引き継ぐ。1日1機、同じ相手との取引は30日に1回まで
--     売りに出している間も、売る人の機体として飛ぶ。売れたら路線とスケジュールから外れる
--   会社どうしのリース（貸す側）は格付け4から（あとで作る）

alter table public.aircraft add column if not exists lease boolean not null default false;
alter table public.aircraft add column if not exists lease_fee numeric not null default 0;
alter table public.aircraft enable row level security;

-- 表：中古機の売り場。売りに出ているものはだれでも見られる。自分の売り買いは自分で見られる。書くのは関数だけ
create table if not exists public.co3_market (
  id          bigint generated always as identity primary key,
  seller_id   uuid not null references auth.users(id) on delete cascade,
  aircraft_id bigint references public.aircraft(id) on delete set null,
  reg         text,
  code        text,
  type        text not null,
  price       bigint not null check (price > 0),
  value_at    bigint not null,
  listed_at   timestamptz not null default now(),
  expires_at  timestamptz not null,
  status      text not null default 'open' check (status in ('open', 'sold', 'cancelled')),
  buyer_id    uuid references auth.users(id) on delete set null,
  sold_at     timestamptz
);
create unique index if not exists co3_market_open on public.co3_market (aircraft_id) where status = 'open';
create index if not exists co3_market_list on public.co3_market (status, expires_at);
alter table public.co3_market enable row level security;
revoke all on public.co3_market from public, anon, authenticated;
grant select on public.co3_market to authenticated;
drop policy if exists "market open or mine" on public.co3_market;
create policy "market open or mine" on public.co3_market for select to authenticated
  using ((status = 'open' and expires_at > now()) or seller_id = auth.uid() or buyer_id = auth.uid());

-- 値段の +25% と会社の価値は、リースの機体を数えない
do $do$
declare src text;
begin
  select pg_get_functiondef('public.ac_price(uuid,text)'::regprocedure) into src;
  if position('not lease' in src) = 0 then
    if position('(select count(*) from aircraft where user_id = p_uid)' in src) = 0 then raise exception 'ac_price の形が変わっていて、リースを入れられない'; end if;
    src := replace(src, '(select count(*) from aircraft where user_id = p_uid)', '(select count(*) from aircraft where user_id = p_uid and not lease)');
    execute src;
  end if;
  select pg_get_functiondef('public.co_value(uuid)'::regprocedure) into src;
  if position('not lease' in src) = 0 then
    if position('from aircraft where user_id = p_uid), 0)::bigint' in src) = 0 then raise exception 'co_value の形が変わっていて、リースを入れられない'; end if;
    src := replace(src, 'from aircraft where user_id = p_uid), 0)::bigint', 'from aircraft where user_id = p_uid and not lease), 0)::bigint');
    execute src;
  end if;
  -- 売る：リースの機体は売れない。売りに出していたら取り下げる
  select pg_get_functiondef('public.co_sell(bigint)'::regprocedure) into src;
  if position('leased' in src) = 0 then
    if position('delete from aircraft where id = p_aircraft;' in src) = 0 then raise exception 'co_sell の形が変わっていて、リースを入れられない'; end if;
    src := replace(src, 'delete from aircraft where id = p_aircraft;',
      'if ac.lease then raise exception ''leased''; end if;' || chr(10) ||
      '  update co3_market set status = ''cancelled'' where aircraft_id = p_aircraft and status = ''open'';' || chr(10) ||
      '  delete from aircraft where id = p_aircraft;');
    execute src;
  end if;
  -- 維持費にリース料を足す
  select pg_get_functiondef('public.co3_ac_upkeep(bigint)'::regprocedure) into src;
  if position('lease_fee' in src) = 0 then
    if position('* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end' in src) = 0 then raise exception 'co3_ac_upkeep の形が変わっていて、リースを入れられない'; end if;
    src := replace(src, '* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end', '* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end + case when a.lease then a.lease_fee else 0 end');
    execute src;
  end if;
end
$do$;

-- 借りられる数
create or replace function public.co3_lease_room(p_uid uuid) returns integer
language sql stable security definer set search_path = public as $$
  select (2 + floor((select count(*) from aircraft where user_id = p_uid and not lease) / 2.0))::int
         - (select count(*) from aircraft where user_id = p_uid and lease)::int
$$;
revoke all on function public.co3_lease_room(uuid) from public, anon, authenticated;

-- リースで借りる：p_kind 'ride'（乗った機体。p_key は co_hangar の ride）・'seen'（見た機体。p_key は登録記号）
create or replace function public.co3_lease(p_kind text, p_key text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); c0 companies; id0 bigint; ac aircraft; base numeric;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if co3_lease_room(uid) < 1 then raise exception 'lease limit'; end if;
  select * into c0 from companies where user_id = uid;
  -- 一時的にお金を足して、買うときと同じ確かめ方で機体を作り、あとでお金と「買った数」を戻す
  update companies set cash = cash + 100000000 where user_id = uid;
  select coalesce(max(id), 0) into id0 from aircraft where user_id = uid;
  if p_kind = 'ride' then perform co_buy(p_key);
  elsif p_kind = 'seen' then perform co3_buy_seen(p_key);
  else raise exception 'invalid lease'; end if;
  select * into ac from aircraft where user_id = uid and id > id0 order by id desc limit 1;
  if not found then raise exception 'lease failed'; end if;
  base := case when p_kind = 'ride' then (ac_spec(ac.type)).price * (1 + 0.25 * (select count(*) from aircraft where user_id = uid and not lease and id <> ac.id))
               else ac.paid end;
  update aircraft set lease = true, paid = round(base), lease_fee = round(base * case when p_kind = 'seen' and ac.seen and co3_ac_earn(ac.id) < 1 then 0.002 else 0.0015 end, 2)
   where id = ac.id;
  update companies set cash = c0.cash, bought = c0.bought where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_lease(text, text) from public, anon;
grant execute on function public.co3_lease(text, text) to authenticated;

create or replace function public.co3_lease_return(p_aircraft bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not exists (select 1 from aircraft where id = p_aircraft and user_id = uid and lease) then raise exception 'not leased'; end if;
  delete from aircraft where id = p_aircraft;
  return co_state();
end;
$$;
revoke all on function public.co3_lease_return(bigint) from public, anon;
grant execute on function public.co3_lease_return(bigint) to authenticated;

-- 中古機：その機種に乗った（見た）か
create or replace function public.co3_knows_type(p_uid uuid, p_code text) returns boolean
language sql stable security definer set search_path = public as $$
  select p_code is not null and (
       exists (select 1 from co_rides(p_uid) r where co3_type_of(r.icao) = p_code)
    or exists (select 1 from co3_seen(p_uid) s where s.code = p_code)
    or exists (select 1 from aircraft a where a.user_id = p_uid and coalesce(a.co3_code, co3_type_of(a.icao)) = p_code))
$$;
revoke all on function public.co3_knows_type(uuid, text) from public, anon, authenticated;

create or replace function public.co3_market_list(p_aircraft bigint, p_pct integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); ac aircraft; v bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 2 then raise exception 'rating required 2'; end if;
  select * into ac from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  if ac.lease then raise exception 'leased'; end if;
  if p_pct is null or p_pct < 30 or p_pct > 150 then raise exception 'invalid price'; end if;
  if exists (select 1 from co3_market where aircraft_id = ac.id and status = 'open' and expires_at > now()) then raise exception 'already listed'; end if;
  update co3_market set status = 'cancelled' where aircraft_id = ac.id and status = 'open';
  v := round(ac.paid * ac_age(ac.bought_at));
  insert into co3_market (seller_id, aircraft_id, reg, code, type, price, value_at, expires_at)
  values (uid, ac.id, ac.reg, coalesce(ac.co3_code, co3_type_of(ac.icao)), ac.type, greatest(1, round(v * p_pct / 100.0)), v, now() + interval '7 days');
  return co_state();
end;
$$;
revoke all on function public.co3_market_list(bigint, integer) from public, anon;
grant execute on function public.co3_market_list(bigint, integer) to authenticated;

create or replace function public.co3_market_cancel(p_listing bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  update co3_market set status = 'cancelled' where id = p_listing and seller_id = uid and status = 'open';
  if not found then raise exception 'listing not found'; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_market_cancel(bigint) from public, anon;
grant execute on function public.co3_market_cancel(bigint) to authenticated;

create or replace function public.co3_market_buy(p_listing bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); m co3_market; ac aircraft; today_start timestamptz := ((now() at time zone 'Asia/Tokyo')::date)::timestamp at time zone 'Asia/Tokyo';   -- 日本時間のきょうの0時（date のままだと接続の時間帯で18時になる）
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 2 then raise exception 'rating required 2'; end if;
  select * into m from co3_market where id = p_listing for update;
  if not found or m.status <> 'open' or m.expires_at <= now() then raise exception 'listing not found'; end if;
  if m.seller_id = uid then raise exception 'own listing'; end if;
  select * into ac from aircraft where id = m.aircraft_id and user_id = m.seller_id for update;
  if not found then raise exception 'listing not found'; end if;
  if not co3_knows_type(uid, m.code) then raise exception 'type not known'; end if;
  if exists (select 1 from co3_market x where x.buyer_id = uid and x.sold_at >= today_start) then raise exception 'one per day'; end if;
  if exists (select 1 from co3_market x where x.status = 'sold' and x.sold_at > now() - interval '30 days'
               and ((x.buyer_id = uid and x.seller_id = m.seller_id) or (x.buyer_id = m.seller_id and x.seller_id = uid))) then raise exception 'same partner'; end if;
  update companies set cash = cash - m.price where user_id = uid and cash >= m.price;
  if not found then raise exception 'not enough cash'; end if;
  perform co_settle(m.seller_id);
  update companies set cash = cash + floor(m.price * 0.95) where user_id = m.seller_id;
  delete from co3_sched where aircraft_id = ac.id;
  -- 乗った機体でなければ「見ただけ」の差がつく（あとで乗れば消える）
  update aircraft set user_id = uid, route_key = null,
         seen = not exists (select 1 from co_rides(uid) r where co3_type_of(r.icao) = m.code or (ac.reg is not null and r.reg = ac.reg))
   where id = ac.id;
  update co3_market set status = 'sold', buyer_id = uid, sold_at = now() where id = m.id;
  return co_state();
end;
$$;
revoke all on function public.co3_market_buy(bigint) from public, anon;
grant execute on function public.co3_market_buy(bigint) to authenticated;

-- 会社の状態：機体のリース・売りに出している値段、売り場（自分のでないもの）、借りられる数
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''market''' in src) = 0 then
    if position($r$'rode_on', rode_on, 'flight', rode_flight,$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then
      raise exception 'co_state の形が変わっていて、リースと中古機を入れられない';
    end if;
    src := replace(src, $r$'rode_on', rode_on, 'flight', rode_flight,$r$,
      $r$'rode_on', rode_on, 'flight', rode_flight, 'lease', lease, 'lease_fee', lease_fee,
                 'listed', (select jsonb_build_object('id', m.id, 'price', m.price, 'expires', m.expires_at) from co3_market m where m.aircraft_id = aircraft.id and m.status = 'open' and m.expires_at > now() limit 1),$r$);
    -- jsonb_build_object は100個までなので、ここから先は2つ目の object にして || でつなぐ
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'_part1', true) || jsonb_build_object('market', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('id', m.id, 'reg', m.reg, 'code', m.code, 'name', t.name, 'type', m.type,
                 'price', m.price, 'value', m.value_at, 'age', (select ac_age(a.bought_at) from aircraft a where a.id = m.aircraft_id),
                 'seller', (select s.name from companies s where s.user_id = m.seller_id), 'expires', m.expires_at, 'can_buy', co3_knows_type(uid, m.code))
                 order by m.listed_at desc), '[]'::jsonb)
                 from co3_market m left join co3_types t on t.code = m.code
                where m.status = 'open' and m.expires_at > now() and m.seller_id <> uid) end,
    'lease_room', case when v3 then co3_lease_room(uid) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
