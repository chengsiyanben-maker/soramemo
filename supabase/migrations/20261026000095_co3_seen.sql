-- エアライン経営 co-v3：見た機体（仕様書「機体」の「見た機体」）
--   空港でチェックインしている間（前後45分）にその空港を発着した機体を、毎日の記録（flight_history）から見つける。
--   位置の偽装の印（impossible_speed）が付いたチェックインは数えない。
--   ・貨物機・ビジネスジェット：見ただけで乗ったのと同じ扱い（乗れないため）。値段は機種の表の1.5倍
--   ・旅客機：見ただけでも買えるが差がつく。値段1.3倍・維持費+30%・稼ぎ0.85（会社に入れて30日ごとに +0.05、最大0.95）・最初の半額は使えない。
--     足せるのは1日3機まで。会社の機体のうち見ただけの旅客機は半分まで（乗った機体がない最初のうちは2機まで）。後でその機体に乗ると差はなくなる
--   ・貨物機の見分け方：記号は旅客機と同じなので、貨物の専門の会社の便名（航空会社の記号）と、777F（B77L）の記号で見分ける

-- 見た機体の記録の印：s:登録記号
alter table public.aircraft drop constraint if exists aircraft_ride_check;
alter table public.aircraft add constraint aircraft_ride_check
  check (ride is null or ride ~ '^(r:[A-Z0-9-]{3,10}|s:[A-Z0-9-]{3,10}|f:[0-9]+|i:[0-9]+)$');
alter table public.aircraft add column if not exists co3_code text references public.co3_types(code);  -- 機種（見た機体は必ず入る）
alter table public.aircraft add column if not exists seen boolean not null default false;              -- 見ただけの旅客機（差つき）

-- 貨物の専門の会社（便名の航空会社の記号）
create or replace function co3.is_cargo_airline(p_flight text) returns boolean
language sql immutable as $$
  select left(upper(coalesce(p_flight, '')), 2) = any (array['KZ','FX','5X','CV','PO','K4','5Y','CK','3S','ES','QY','D0','RU','LD','O3','YG','Y8','CF','M3','NC'])
$$;

-- 見た機体の機種：貨物の会社の便なら貨物機の機種、そうでなければ記号で引いた機種
create or replace function public.co3_seen_code(p_flight text, p_type text, p_aircraft text) returns text
language sql stable security definer set search_path = public as $$
  select case
    when upper(coalesce(nullif(p_type, ''), '')) = 'B77L' then 'B77F'
    when co3.is_cargo_airline(p_flight) then
      case upper(coalesce(nullif(p_type, ''), p_aircraft, ''))
        when 'B738' then 'B738F' when 'B752' then 'B752F' when 'B763' then 'B763F' when '76F' then 'B763F'
        when 'A333' then 'A333F' when 'MD11' then 'MD11F' when 'B744' then 'B744F' when '74Y' then 'B744F'
        when 'B748' then 'B748F' when '74N' then 'B748F' when '77X' then 'B77F' end
    else co3_type_of(coalesce(nullif(p_type, ''), p_aircraft)) end
$$;
revoke all on function public.co3_seen_code(text, text, text) from public, anon, authenticated;

-- 見た機体の一覧（登録記号ごとに1つ。いちばん新しく見たとき）
create or replace function public.co3_seen(p_uid uuid)
returns table (reg text, code text, kind text, airport text, seen_at timestamptz, flight text, dep text, arr text)
language sql stable security definer set search_path = public as $$
  with ch as (
    select c.created_at, a.iata from checkins c join airports a on a.id = c.airport_id
     where c.user_id = p_uid and not ('impossible_speed' = any (c.flags)) and a.iata ~ '^[A-Z]{3}$'
     order by c.created_at desc limit 500
  ), m as (
    select h.reg, co3_seen_code(h.flight, h.type, h.aircraft) as code, ch.iata, ch.created_at, h.flight, h.dep, h.arr
      from ch join flight_history h
        on h.svc_date between (ch.created_at at time zone 'Asia/Tokyo')::date - 1 and (ch.created_at at time zone 'Asia/Tokyo')::date + 1
       and ((h.dep = ch.iata and coalesce(h.atd, h.std) between ch.created_at - interval '45 minutes' and ch.created_at + interval '45 minutes')
         or (h.arr = ch.iata and coalesce(h.ata, h.sta) between ch.created_at - interval '45 minutes' and ch.created_at + interval '45 minutes'))
     where h.reg ~ '^[A-Z0-9-]{3,10}$' and not h.cancelled
  )
  select distinct on (m.reg) m.reg, m.code, t.kind, m.iata, m.created_at, m.flight, m.dep, m.arr
    from m join co3_types t on t.code = m.code
   order by m.reg, m.created_at desc
$$;
revoke all on function public.co3_seen(uuid) from public, anon, authenticated;

-- 見た機体の値段：機種の表 ×（貨物機・ビジネスジェット 1.5、旅客機 1.3）×（1＋持っている機体1機ごとに 25%）。半額なし
create or replace function public.co3_seen_price(p_uid uuid, p_code text) returns bigint
language sql stable security definer set search_path = public as $$
  select round(t.price * case when t.kind in ('freighter', 'bizjet') then 1.5 else 1.3 end
               * (1 + 0.25 * (select coalesce(sum(co3.count_weight(coalesce(x.kind in ('small', 'heli'), a.type = 'prop'))), 0)
                                from aircraft a left join co3_types x on x.code = a.co3_code where a.user_id = p_uid)))::bigint
    from co3_types t where t.code = p_code
$$;
revoke all on function public.co3_seen_price(uuid, text) from public, anon, authenticated;

-- 見た機体の一覧（画面用）
create or replace function public.co3_seen_list() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  return (select coalesce(jsonb_agg(jsonb_build_object('reg', s.reg, 'code', s.code, 'name', t.name, 'kind', s.kind, 'airport', s.airport,
            'seen_at', s.seen_at, 'flight', s.flight, 'dep', s.dep, 'arr', s.arr,
            'owned', a.id, 'price', co3_seen_price(uid, s.code), 'as_ridden', s.kind in ('freighter', 'bizjet'))
            order by s.seen_at desc), '[]'::jsonb)
    from co3_seen(uid) s join co3_types t on t.code = s.code
    left join aircraft a on a.user_id = uid and a.reg = s.reg);
end;
$$;

-- 見た機体を買う
create or replace function public.co3_buy_seen(p_reg text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); s record; t co3_types; price bigint; is_pax boolean; n_seen integer; n_all integer; n_today integer;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into s from co3_seen(uid) where reg = upper(btrim(p_reg));
  if not found then raise exception 'not seen'; end if;
  if exists (select 1 from aircraft where user_id = uid and reg = s.reg) then raise exception 'already owned'; end if;
  select * into t from co3_types where code = s.code;
  is_pax := t.kind not in ('freighter', 'bizjet');
  if is_pax then
    -- 乗ったことがある機体なら、乗った機体として買う（co_buy）
    if exists (select 1 from co_rides(uid) r where r.reg = s.reg) then raise exception 'ridden: use co_buy'; end if;
    select count(*) filter (where seen), count(*), count(*) filter (where seen and bought_at > now() - interval '1 day')
      into n_seen, n_all, n_today from aircraft where user_id = uid;
    if n_today >= 3 then raise exception 'seen limit per day'; end if;
    if n_seen + 1 > greatest(2, (n_all + 1) / 2) then raise exception 'too many seen aircraft'; end if;
  end if;
  price := co3_seen_price(uid, s.code);
  update companies set cash = cash - price, bought = bought + 1 where user_id = uid and cash >= price;
  if not found then raise exception 'not enough cash'; end if;
  insert into aircraft (user_id, type, reg, icao, ride, intl, paid, co3_code, seen)
  values (uid,
          coalesce(ac_class(t.icao[1]), case when t.wing >= 'E' then 'lg' when t.wing = 'D' then 'wb' when t.kind in ('small', 'heli') then 'prop' else 'nb' end),
          s.reg, left(coalesce(t.icao[1], t.code), 8), 's:' || s.reg,
          s.dep is null or s.arr is null or not exists (select 1 from airports where iata = s.dep) or not exists (select 1 from airports where iata = s.arr),
          price, s.code, is_pax);
  return co_state();
end;
$$;
revoke all on function public.co3_seen_list(), public.co3_buy_seen(text) from public, anon;
grant execute on function public.co3_seen_list(), public.co3_buy_seen(text) to authenticated;

-- 見ただけの旅客機の稼ぎ：0.85、会社に入れて30日ごとに +0.05、最大0.95。あとで乗ったら1.0
create or replace function public.co3_ac_earn(p_aircraft bigint) returns numeric
language sql stable security definer set search_path = public as $$
  select case when a.id is null or not a.seen then 1
              when a.reg is not null and exists (select 1 from co_rides(a.user_id) r where r.reg = a.reg) then 1
              else least(0.95, 0.85 + 0.05 * floor(extract(epoch from (now() - a.bought_at)) / 86400 / 30)) end
    from (select 1) one left join aircraft a on a.id = p_aircraft
$$;
revoke all on function public.co3_ac_earn(bigint) from public, anon, authenticated;

-- 機種の表の維持費（見ただけの旅客機は +30%。あとで乗ったら差なし）。機種がなければ co-v2 の大きさの維持費
create or replace function public.co3_ac_upkeep(p_aircraft bigint) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(t.upkeep, ac_upkeep(a.type))
         * case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end
    from aircraft a left join co3_types t on t.code = coalesce(a.co3_code, co3_type_of(a.icao))
   where a.id = p_aircraft
$$;
revoke all on function public.co3_ac_upkeep(bigint) from public, anon, authenticated;

-- 切り替え：スイッチがオンなら維持費も機種の表で数える
create or replace function public.co_upkeep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public, ops as $$
  select case when coalesce((ops.flag('co_v3'))::boolean, false)
    then coalesce(round(sum(co3_ac_upkeep(id))), 0)::bigint
    else coalesce(sum(ac_upkeep(type)), 0)::bigint end
    from aircraft where user_id = p_uid
$$;
revoke all on function public.co_upkeep(uuid) from public, anon, authenticated;

-- 機体の数字は、見た機体の機種（co3_code）を先に使う
create or replace function public.co3_ac_spec(p_aircraft bigint, out code text, out seats numeric, out mtow numeric, out noise text, out wing text, out wide boolean)
language sql stable security definer set search_path = public as $$
  select t.code,
         coalesce(t.seats, (co3.ac_class_spec(a.type)).seats),
         coalesce(t.mtow, (co3.ac_class_spec(a.type)).mtow),
         coalesce(t.noise, (co3.ac_class_spec(a.type)).noise),
         coalesce(t.wing, (co3.ac_class_spec(a.type)).wing),
         coalesce(t.wing >= 'D', a.type in ('wb', 'lg'))
    from aircraft a left join co3_types t on t.code = coalesce(a.co3_code, co3_type_of(a.icao))
   where a.id = p_aircraft
$$;

-- 路線ごとの内わけの稼ぎに、見ただけの旅客機の 0.85〜0.95 を掛ける
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_ac_earn' in src) = 0 then
    src := replace(src, '* co3.newbie_mult(g2.day_no) * g2.sky as mult', '* co3.newbie_mult(g2.day_no) * g2.sky * co3_ac_earn(g2.ac_id) as mult');
    if position('co3_ac_earn' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、見た機体の稼ぎを入れられない'; end if;
    execute src;
  end if;
end
$do$;
