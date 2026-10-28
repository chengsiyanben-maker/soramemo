-- エアライン経営 co-v3：天気の備えと台風の計画欠航（仕様書「天気の備え」「台風の計画欠航」。格付けに関係なく、自分で入れられる）
--   天気：空港の気象通報（METAR。米国の航空気象センターの公開データ。運用の表示と同じ出どころ）を毎時 co3_wx に残す（関数 co3-weather）
--     雪・凍った雨（SN・FZRA・FZDZ・PL・GS）、強風（平均 25ノット以上か最大瞬間 35ノット以上）、霧（視程 800m 未満か FG）、雷（TS）
--   便の欠航・遅れ（本物の便から決めるもの）が、出発・到着の空港のその時間の天気に当たるとき、備えで減らす
--     防除氷の設備（空港・3段。5,000・12,000・30,000）：雪の欠航 −30%・−50%・−70%、雪の遅れは半分
--     横風・強風の訓練（会社の方針：なし・普通・手厚い。毎日 機体1機あたり 0・1・3）：強風の欠航 0・−20%・−40%
--     低い視界での運航（機体ごと。機体の値段の2%）：CAT III に対応した空港（co3_cat3_airports。国の資料で確かめた8空港を入れておく。運営が直せる）で霧の欠航 −80%
--     雷の作業の備え（空港・1段 8,000）：雷の遅れが半分
--     いくつもの天気が重なるときは、それぞれの減らし方をかける
--   台風：予報（co3_typhoon_fcst。台風の中心が明日その空港から300km以内に来そう）は運営が入れる（気象庁の情報の使い方を確かめてから自動にする）
--     予報があると、その空港を結ぶ自社の路線ごとに「計画欠航するか」を前の日に決める（決めなければ飛ばす）
--     計画欠航した：その日はその路線の便を出さない（収益0）、評判は下がらない
--     飛ばして、台風が来た（その日、その空港の本物の便の半分以上が欠航）：その日の収益0、次の日も収益が半分（台風の避難の備えがあれば足止めなし）、評判 −10
--     飛ばして、台風がそれた：その日の収益 +30%
--     台風の避難の備え（空港・2段。1段 20,000＝小型・中型の機体、2段 60,000＝大型も）
--   値段と上限は仕様書の「値段が決まっていない施設」の見直しで変えることがある

create table if not exists public.co3_wx (
  iata text not null,
  at timestamptz not null,           -- その時間（毎時0分にそろえる）
  snow boolean not null default false,
  wind boolean not null default false,
  fog boolean not null default false,
  ts boolean not null default false,
  raw text,
  primary key (iata, at)
);
alter table public.co3_wx enable row level security;
revoke all on public.co3_wx from public, anon, authenticated;

create table if not exists public.co3_cat3_airports (
  iata text primary key,
  note text
);
alter table public.co3_cat3_airports enable row level security;
revoke all on public.co3_cat3_airports from public, anon, authenticated;
grant select on public.co3_cat3_airports to authenticated;
drop policy if exists co3_cat3_read on public.co3_cat3_airports;
create policy co3_cat3_read on public.co3_cat3_airports for select to authenticated using (true);
-- 国の資料（令和5年4月1日現在）で CAT III に対応している8空港。公開の前に航空路誌（AIP）で確かめ直す。高松は運用が始まったら足す
insert into public.co3_cat3_airports (iata, note) values
  ('CTS', '国の資料 令和5年4月1日現在'), ('KUH', '国の資料 令和5年4月1日現在'), ('AOJ', '国の資料 令和5年4月1日現在'), ('NRT', '国の資料 令和5年4月1日現在'),
  ('HND', '国の資料 令和5年4月1日現在'), ('NGO', '国の資料 令和5年4月1日現在'), ('HIJ', '国の資料 令和5年4月1日現在'), ('KMJ', '国の資料 令和5年4月1日現在')
on conflict (iata) do nothing;

create table if not exists public.co3_wx_prep (
  user_id uuid not null references auth.users (id) on delete cascade,
  iata text not null,
  kind text not null check (kind in ('deice', 'typhoon', 'thunder')),
  level integer not null check (level between 1 and 3),
  built_at timestamptz not null default now(),
  primary key (user_id, iata, kind)
);
alter table public.co3_wx_prep enable row level security;
revoke all on public.co3_wx_prep from public, anon, authenticated;
grant select on public.co3_wx_prep to authenticated;
drop policy if exists co3_wx_prep_own on public.co3_wx_prep;
create policy co3_wx_prep_own on public.co3_wx_prep for select to authenticated using (user_id = (select auth.uid()));

create table if not exists public.co3_typhoon_fcst (
  iata text not null,
  day date not null,
  note text,
  created_at timestamptz not null default now(),
  primary key (iata, day)
);
alter table public.co3_typhoon_fcst enable row level security;
revoke all on public.co3_typhoon_fcst from public, anon, authenticated;
grant select on public.co3_typhoon_fcst to authenticated;
drop policy if exists co3_typhoon_fcst_read on public.co3_typhoon_fcst;
create policy co3_typhoon_fcst_read on public.co3_typhoon_fcst for select to authenticated using (true);

-- 計画欠航の判断（路線ごと・日ごと）
create table if not exists public.co3_typhoon_plan (
  user_id uuid not null references auth.users (id) on delete cascade,
  route_key text not null,
  day date not null,
  iata text not null,
  cancel boolean not null,
  decided_at timestamptz not null default now(),
  primary key (user_id, route_key, day)
);
alter table public.co3_typhoon_plan enable row level security;
revoke all on public.co3_typhoon_plan from public, anon, authenticated;
grant select on public.co3_typhoon_plan to authenticated;
drop policy if exists co3_typhoon_plan_own on public.co3_typhoon_plan;
create policy co3_typhoon_plan_own on public.co3_typhoon_plan for select to authenticated using (user_id = (select auth.uid()));

alter table public.companies add column if not exists wind_training text not null default 'none' check (wind_training in ('none', 'normal', 'high'));
alter table public.companies enable row level security;
alter table public.aircraft add column if not exists cat3 boolean not null default false;
alter table public.aircraft enable row level security;

-- その時間の天気（出発・到着の空港のどちらか）
create or replace function public.co3_wx_at(p_a text, p_b text, p_at timestamptz, out snow_a boolean, out snow_b boolean, out wind boolean, out fog_a boolean, out fog_b boolean, out ts_a boolean, out ts_b boolean)
language sql stable security definer set search_path = public as $$
  select coalesce(bool_or(snow) filter (where iata = p_a), false), coalesce(bool_or(snow) filter (where iata = p_b), false),
         coalesce(bool_or(wind), false),
         coalesce(bool_or(fog) filter (where iata = p_a), false), coalesce(bool_or(fog) filter (where iata = p_b), false),
         coalesce(bool_or(ts) filter (where iata = p_a), false), coalesce(bool_or(ts) filter (where iata = p_b), false)
    from co3_wx where iata in (p_a, p_b) and at = date_trunc('hour', p_at)
$$;
revoke all on function public.co3_wx_at(text, text, timestamptz) from public, anon, authenticated;

create or replace function public.co3_prep_lv(p_uid uuid, p_iata text, p_kind text) returns integer
language sql stable security definer set search_path = public as $$ select coalesce((select level from co3_wx_prep where user_id = p_uid and iata = p_iata and kind = p_kind), 0) $$;
revoke all on function public.co3_prep_lv(uuid, text, text) from public, anon, authenticated;

-- 本物の便から決めた欠航の確率にかける倍率（その天気に当たっていなければ1）
create or replace function public.co3_wx_cxl_mult(p_uid uuid, p_a text, p_b text, p_aircraft bigint, p_at timestamptz) returns numeric
language sql stable security definer set search_path = public as $$
  with w as (select * from co3_wx_at(p_a, p_b, p_at)), d as (select x as iata, k from (values (p_a, 'a'), (p_b, 'b')) v(x, k))
  select (case when w.snow_a then 1 - (array[0, 0.3, 0.5, 0.7])[co3_prep_lv(p_uid, p_a, 'deice') + 1] else 1 end)
       * (case when w.snow_b then 1 - (array[0, 0.3, 0.5, 0.7])[co3_prep_lv(p_uid, p_b, 'deice') + 1] else 1 end)
       * (case when w.wind then 1 - coalesce((select case wind_training when 'normal' then 0.2 when 'high' then 0.4 else 0 end from companies where user_id = p_uid), 0) else 1 end)
       * (case when (w.fog_a and exists (select 1 from co3_cat3_airports where iata = p_a)) or (w.fog_b and exists (select 1 from co3_cat3_airports where iata = p_b))
               then case when coalesce((select cat3 from aircraft where id = p_aircraft), false) then 0.2 else 1 end else 1 end)
    from w
$$;
revoke all on function public.co3_wx_cxl_mult(uuid, text, text, bigint, timestamptz) from public, anon, authenticated;

-- 遅れにかける倍率（雪は防除氷があれば半分、雷は備えがあれば半分）
create or replace function public.co3_wx_delay_mult(p_uid uuid, p_a text, p_b text, p_at timestamptz) returns numeric
language sql stable security definer set search_path = public as $$
  with w as (select * from co3_wx_at(p_a, p_b, p_at))
  select case when (w.snow_a and co3_prep_lv(p_uid, p_a, 'deice') > 0) or (w.snow_b and co3_prep_lv(p_uid, p_b, 'deice') > 0)
                or (w.ts_a and co3_prep_lv(p_uid, p_a, 'thunder') > 0) or (w.ts_b and co3_prep_lv(p_uid, p_b, 'thunder') > 0) then 0.5 else 1 end
    from w
$$;
revoke all on function public.co3_wx_delay_mult(uuid, text, text, timestamptz) from public, anon, authenticated;

-- 横風の訓練の費用（1日）
create or replace function public.co3_wx_cost(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select case c.wind_training when 'normal' then 1 when 'high' then 3 else 0 end * (select count(*) from aircraft a where a.user_id = p_uid)
                     from companies c where c.user_id = p_uid), 0)
$$;
revoke all on function public.co3_wx_cost(uuid) from public, anon, authenticated;

-- 台風：その日、その空港に台風が来たか（本物の便の半分以上が欠航）
create or replace function public.co3_typhoon_hit(p_iata text, p_day date) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select count(*) filter (where coalesce(fs.dep_status, '') ~* 'cancel' or coalesce(fs.arr_status, '') ~* 'cancel')::numeric / nullif(count(*), 0) >= 0.5
                     from flight_schedule fs where fs.svc_date = p_day and (fs.dep = p_iata or fs.arr = p_iata)), false)
$$;
revoke all on function public.co3_typhoon_hit(text, date) from public, anon, authenticated;

-- 台風の収益の倍率：計画欠航 0・飛ばして来た 0・それた 1.3・前の日に来て足止め 0.5（避難の備えがあれば1）
create or replace function public.co3_typhoon_mult(p_uid uuid, p_route text, p_a text, p_b text, p_aircraft bigint) returns numeric
language sql stable security definer set search_path = public as $$
  with d as (select co3.today() as d),
  f as (select x.iata, x.day from co3_typhoon_fcst x, d where x.iata in (p_a, p_b) and x.day in (d.d, d.d - 1))
  select coalesce((
    select case
      when exists (select 1 from co3_typhoon_plan p, d where p.user_id = p_uid and p.route_key = p_route and p.day = d.d and p.cancel) then 0
      when exists (select 1 from f, d where f.day = d.d) then
        case when bool_or(co3_typhoon_hit(f.iata, f.day)) filter (where f.day = (select d from d)) then 0 else 1.3 end
      when exists (select 1 from f, d where f.day = d.d - 1 and co3_typhoon_hit(f.iata, f.day)
                     and not exists (select 1 from co3_typhoon_plan p where p.user_id = p_uid and p.route_key = p_route and p.day = f.day and p.cancel)
                     and co3_prep_lv(p_uid, f.iata, 'typhoon') < case when (select type from aircraft where id = p_aircraft) in ('wb', 'lg') then 2 else 1 end) then 0.5
      else 1 end
    from f), 1)
$$;
revoke all on function public.co3_typhoon_mult(uuid, text, text, text, bigint) from public, anon, authenticated;

-- 計画欠航した路線（その日は便を出さない）
create or replace function public.co3_typhoon_planned(p_uid uuid, p_route text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from co3_typhoon_plan p where p.user_id = p_uid and p.route_key = p_route and p.day = co3.today() and p.cancel)
$$;
revoke all on function public.co3_typhoon_planned(uuid, text) from public, anon, authenticated;

-- 台風の評判：飛ばして来た −10（前の90日）
create or replace function public.co3_typhoon_rep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select -10 * count(distinct (x.route_key, x.day))::bigint
    from (select r.route_key, f.day, f.iata from co3_typhoon_fcst f
            join co_routes(p_uid) r on true
            join lateral (select a.iata as ia, b.iata as ib from airports a, airports b
                           where r.route_key ~ '^[0-9]+-[0-9]+$' and a.id = split_part(r.route_key, '-', 1)::int and b.id = split_part(r.route_key, '-', 2)::int) e on f.iata in (e.ia, e.ib)
           where f.day > (now() at time zone 'Asia/Tokyo')::date - 90 and f.day < co3.today() + 1
             and exists (select 1 from aircraft a where a.user_id = p_uid and a.route_key = r.route_key)) x
   where co3_typhoon_hit(x.iata, x.day)
     and not exists (select 1 from co3_typhoon_plan p where p.user_id = p_uid and p.route_key = x.route_key and p.day = x.day and p.cancel)
$$;
revoke all on function public.co3_typhoon_rep(uuid) from public, anon, authenticated;

-- 操作
create or replace function public.co3_build_prep(p_kind text, p_iata text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); lv int; mx int; cst numeric;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if p_kind not in ('deice', 'typhoon', 'thunder') then raise exception 'invalid prep'; end if;
  if not exists (select 1 from checkins ch join airports a on a.id = ch.airport_id where ch.user_id = uid and a.iata = p_iata) then raise exception 'not visited'; end if;
  lv := co3_prep_lv(uid, p_iata, p_kind);
  mx := case p_kind when 'deice' then 3 when 'typhoon' then 2 else 1 end;
  if lv >= mx then raise exception 'prep max'; end if;
  cst := case p_kind when 'deice' then (array[5000, 12000, 30000])[lv + 1] when 'typhoon' then (array[20000, 60000])[lv + 1] else 8000 end;
  if (select cash from companies where user_id = uid) < cst then raise exception 'not enough cash'; end if;
  update companies set cash = cash - cst where user_id = uid;
  insert into co3_wx_prep (user_id, iata, kind, level) values (uid, p_iata, p_kind, 1) on conflict (user_id, iata, kind) do update set level = co3_wx_prep.level + 1;
  return co_state();
end;
$$;
revoke all on function public.co3_build_prep(text, text) from public, anon;
grant execute on function public.co3_build_prep(text, text) to authenticated;

create or replace function public.co3_set_wind_training(p_level text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if p_level not in ('none', 'normal', 'high') then raise exception 'invalid prep'; end if;
  update companies set wind_training = p_level where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_wind_training(text) from public, anon;
grant execute on function public.co3_set_wind_training(text) to authenticated;

create or replace function public.co3_set_cat3(p_aircraft bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); a record; cst numeric;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into a from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  if a.cat3 then raise exception 'prep max'; end if;
  cst := ceil(greatest(a.paid, (ac_spec(a.type)).price) * 0.02);
  if (select cash from companies where user_id = uid) < cst then raise exception 'not enough cash'; end if;
  update companies set cash = cash - cst where user_id = uid;
  update aircraft set cat3 = true where id = a.id;
  return co_state();
end;
$$;
revoke all on function public.co3_set_cat3(bigint) from public, anon;
grant execute on function public.co3_set_cat3(bigint) to authenticated;

-- 計画欠航するか（明日の分。予報のある空港を結ぶ自社の路線だけ）
create or replace function public.co3_typhoon_decide(p_route text, p_cancel boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); d date := co3.today() + 1; ap text;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select f.iata into ap from co3_typhoon_fcst f
    join airports a on a.iata = f.iata
   where f.day = d and p_route ~ '^[0-9]+-[0-9]+$' and a.id in (split_part(p_route, '-', 1)::int, split_part(p_route, '-', 2)::int) limit 1;
  if ap is null then raise exception 'no typhoon'; end if;
  if not exists (select 1 from aircraft x where x.user_id = uid and x.route_key = p_route) then raise exception 'route not found'; end if;
  insert into co3_typhoon_plan (user_id, route_key, day, iata, cancel) values (uid, p_route, d, ap, coalesce(p_cancel, false))
    on conflict (user_id, route_key, day) do update set cancel = excluded.cancel, decided_at = now();
  return co_state();
end;
$$;
revoke all on function public.co3_typhoon_decide(text, boolean) from public, anon;
grant execute on function public.co3_typhoon_decide(text, boolean) to authenticated;

-- 運営：台風の予報を入れる
create or replace function public.admin_co3_typhoon(p_iata text, p_day date, p_note text default null) returns integer
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  insert into co3_typhoon_fcst (iata, day, note) values (upper(p_iata), p_day, p_note) on conflict (iata, day) do update set note = excluded.note;
  return 1;
end;
$$;
revoke all on function public.admin_co3_typhoon(text, date, text) from public, anon;
grant execute on function public.admin_co3_typhoon(text, date, text) to authenticated;

do $do$
declare src text; n0 text;
begin
  -- 便ごとの欠航・遅れ：天気の備え
  select pg_get_functiondef('public.co3_legs_check(timestamptz)'::regprocedure) into src;
  if position('co3_wx_cxl_mult' in src) = 0 then
    n0 := src;
    src := replace(src, 'elsif rn > 0 and co3.leg_draw(c.user_id, l.route_key, l.leg, today) < rc::numeric / rn then',
                        'elsif rn > 0 and co3.leg_draw(c.user_id, l.route_key, l.leg, today) < rc::numeric / rn * co3_wx_cxl_mult(c.user_id, l.dep, l.arr, l.aircraft_id, dep_at) then');
    src := replace(src, 'dl := greatest(coalesce(round(rd)::int, 0), inh);', 'dl := greatest(coalesce(round(rd * co3_wx_delay_mult(c.user_id, l.dep, l.arr, dep_at))::int, 0), inh);');
    if position('co3_wx_cxl_mult' in src) = 0 or position('co3_wx_delay_mult' in src) = 0 then raise exception 'co3_legs_check の形が変わっていて、天気の備えを入れられない'; end if;
    execute src;
  end if;
  -- 収益：台風
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_typhoon_mult' in src) = 0 then
    n0 := src;
    src := replace(src, '* co3_wifi_mult(k2.ac_id, k2.biz) as rev,', '* co3_wifi_mult(k2.ac_id, k2.biz) * co3_typhoon_mult(p_uid, k2.route_key, k2.a, k2.b, k2.ac_id) as rev,');
    src := replace(src, 'case when co3_in_heavy(e.ac_id) then 0', 'case when co3_in_heavy(e.ac_id) or co3_typhoon_planned(p_uid, e.route_key) then 0');
    if src = n0 then raise exception 'co3_route_econ の形が変わっていて、台風を入れられない'; end if;
    execute src;
  end if;
  -- 評判
  select pg_get_functiondef('public.co_rep_points(uuid)'::regprocedure) into src;
  if position('co3_typhoon_rep' in src) = 0 then
    src := replace(src, '+ co3_event_rep(p_uid)', '+ co3_event_rep(p_uid)' || chr(10) || '       + co3_typhoon_rep(p_uid)');
    if position('co3_typhoon_rep' in src) = 0 then raise exception 'co_rep_points の形が変わっていて、台風を入れられない'; end if;
    execute src;
  end if;
  -- 維持費：横風の訓練
  select pg_get_functiondef('public.co_upkeep(uuid)'::regprocedure) into src;
  if position('co3_wx_cost' in src) = 0 then
    n0 := src;
    src := replace(src, 'round(co3_people_cost(p_uid))::bigint', 'round(co3_people_cost(p_uid) + co3_wx_cost(p_uid))::bigint');
    if src = n0 then raise exception 'co_upkeep の形が変わっていて、横風の訓練を入れられない'; end if;
    execute src;
  end if;
  -- 会社の状態
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_wx_prep' in src) = 0 then
    if position($r$'wifi', wifi,$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、天気の備えを入れられない'; end if;
    src := replace(src, $r$'wifi', wifi,$r$, $r$'wifi', wifi, 'cat3', cat3, 'cat3_cost', ceil(greatest(paid, (ac_spec(type)).price) * 0.02),$r$);
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'wx', case when v3 then jsonb_build_object(
        'prep', coalesce((select jsonb_agg(jsonb_build_object('iata', p.iata, 'kind', p.kind, 'level', p.level) order by p.iata, p.kind) from co3_wx_prep p where p.user_id = uid), '[]'::jsonb),
        'wind', c.wind_training, 'cat3_airports', coalesce((select jsonb_agg(iata order by iata) from co3_cat3_airports), '[]'::jsonb),
        'typhoon', coalesce((select jsonb_agg(jsonb_build_object('day', f.day, 'iata', f.iata, 'k', r.route_key,
                              'cancel', (select p.cancel from co3_typhoon_plan p where p.user_id = uid and p.route_key = r.route_key and p.day = f.day)) order by f.day, r.route_key)
                       from co3_typhoon_fcst f
                       join airports ap on ap.iata = f.iata
                       join (select distinct x.route_key from aircraft x where x.user_id = uid and x.route_key ~ '^[0-9]+-[0-9]+$') r
                         on ap.id in (split_part(r.route_key, '-', 1)::int, split_part(r.route_key, '-', 2)::int)
                      where f.day between co3.today() and co3.today() + 1), '[]'::jsonb)) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

-- 気象通報の記録は3日より古いものを消す
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') and exists (select 1 from pg_extension where extname = 'pg_net') then
    execute $q$ select cron.schedule('co3-weather', '2 * * * *', $job$
      select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/co3-weather', headers := '{"User-Agent": "soramemo (co3-weather)"}'::jsonb, timeout_milliseconds := 50000)
    $job$) $q$;
    execute $q$ select cron.schedule('co3-weather-cleanup', '40 19 * * *', $job$ delete from public.co3_wx where at < now() - interval '3 days' $job$) $q$;
  end if;
end
$$;
