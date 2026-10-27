-- エアライン経営 co-v3：便ごとのトラブル（仕様書どおり「出発の3時間前に決める」形。10/27 の1日まとめを置きかえる）
--   15分ごとに、出発の3時間前になった自社の便（おまかせのスケジュール co3_route_legs）を決める：
--     本物の便（flight_schedule：ODPT の運航情報が5分ごとに入る）のうち、同じ区間・同じ向き・定刻が前後90分の便を見る
--     欠航：本物の欠航の割合で決める（会社・路線・便・日から作る決まった数で。同じ便はいつ見ても同じ結果）
--     遅れ：本物の便の遅れ（変更後の出発 − 定刻）の平均と、前の便から続いた遅れ（遅れ − 折り返しの余裕）の大きいほう。15分以上で「遅れ」
--     近くに本物の便がなければ「定時」（そのときは前からある実際の空の倍率で欠航の分を数える）
--   お金：欠航は収益0（その便の収益を引く）、遅れは −10%（その便の収益の10%を引く）
--     本物の便と照らして決めた路線は、実際の空の倍率から欠航の分を除く（二重に引かない）
--   欠航か1時間以上の遅れなら「対応してください」（co3_troubles）。夜22時〜朝7時に決まったものは朝7時から数える
--   カードが合うとき：振替の手配＝欠航、ホテルの手配＝19時より後の欠航、軽食とおわび＝2時間以上の遅れ
--   定時率（満足度・評判）は、会社のせいの遅れ（故障・人の不足）だけを数えるので、格付けと故障を作るまで0
--   毎朝の1日まとめ（co3_trouble_detect）は止める（関数は残す）

-- 表：便ごとの結果。自分の分だけ読める。書くのは関数だけ
create table if not exists public.co3_leg_status (
  user_id    uuid not null references auth.users(id) on delete cascade,
  day        date not null,
  route_key  text not null,
  leg        integer not null,
  dep        text not null,
  arr        text not null,
  dep_at     timestamptz not null,
  status     text not null check (status in ('ok', 'delay', 'cxl')),
  delay_min  integer not null default 0,
  carried    integer not null default 0,            -- 前の便から続いた遅れ
  real_n     integer not null default 0,
  real_cxl   integer not null default 0,
  real_delay integer,
  rev_flight numeric not null default 0,
  loss       numeric not null default 0,
  decided_at timestamptz not null default now(),
  primary key (user_id, day, route_key, leg)
);
alter table public.co3_leg_status enable row level security;
revoke all on public.co3_leg_status from public, anon, authenticated;
grant select on public.co3_leg_status to authenticated;
drop policy if exists "own leg status" on public.co3_leg_status;
create policy "own leg status" on public.co3_leg_status for select to authenticated using (user_id = auth.uid());

-- トラブルの表に、便・種類・遅れを足す（前の1日まとめの行は leg が空のまま残る）。RLS はそのまま
alter table public.co3_troubles add column if not exists leg integer;
alter table public.co3_troubles add column if not exists kind text not null default 'cxl' check (kind in ('cxl', 'delay'));
alter table public.co3_troubles add column if not exists delay_min integer not null default 0;
alter table public.co3_troubles add column if not exists dep_at timestamptz;
alter table public.co3_troubles add column if not exists dep text;
alter table public.co3_troubles add column if not exists arr text;
alter table public.co3_troubles drop constraint if exists co3_troubles_user_id_route_key_day_key;
create unique index if not exists co3_troubles_leg on public.co3_troubles (user_id, route_key, day, coalesce(leg, 0));
alter table public.co3_troubles drop constraint if exists co3_troubles_cancelled_check;
alter table public.co3_troubles add constraint co3_troubles_cancelled_check check (cancelled >= 0);
alter table public.co3_troubles enable row level security;

-- 前の1日まとめの関数は、行の重なりの決まりが変わったので on conflict を直す（試験と、もしものときのために残す）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_trouble_detect(timestamptz)'::regprocedure) into src;
  if position('on conflict (user_id, route_key, day) do nothing' in src) > 0 then
    src := replace(src, 'on conflict (user_id, route_key, day) do nothing', 'on conflict do nothing');
    execute src;
  end if;
end
$do$;

-- カードが合うか（種類・遅れ・出発の時刻〈日本時間の0時からの分〉）
create or replace function co3.card_fits2(p_card text, p_kind text, p_delay integer, p_dep_min integer) returns boolean
language sql immutable as $$
  select case p_card when 'transfer' then p_kind = 'cxl'
                     when 'hotel' then p_kind = 'cxl' and coalesce(p_dep_min, 0) >= 1140
                     when 'snack' then p_kind = 'delay' and coalesce(p_delay, 0) >= 120
                     else false end
$$;
revoke all on function co3.card_fits2(text, text, integer, integer) from public, anon, authenticated;

-- 対応する：合うかどうかを種類・時刻で見る（前の1日まとめの行は「欠航・時刻なし」）
create or replace function public.co3_trouble_do(p_uid uuid, p_id bigint, p_card text, p_auto boolean, p_at timestamptz default now()) returns text
language plpgsql security definer set search_path = public as $$
declare t co3_troubles; res text; c numeric; dm integer;
begin
  select * into t from co3_troubles where id = p_id and user_id = p_uid for update;
  if not found then raise exception 'trouble not found'; end if;
  if t.result is not null then raise exception 'already done'; end if;
  if p_card not in ('transfer', 'hotel', 'snack') then raise exception 'invalid card'; end if;
  if p_at > t.deadline then raise exception 'too late'; end if;
  c := round(co3.card_rate(p_card) * t.rev_flight * greatest(t.cancelled, 1), 2);
  update companies set cash = cash - ceil(c) where user_id = p_uid and cash >= ceil(c);
  if not found then raise exception 'not enough cash'; end if;
  dm := case when t.dep_at is null then null else extract(hour from t.dep_at at time zone 'Asia/Tokyo')::int * 60 + extract(minute from t.dep_at at time zone 'Asia/Tokyo')::int end;
  res := case when not p_auto and p_at <= t.god_until and co3.card_fits2(p_card, t.kind, t.delay_min, dm) then 'god' else 'normal' end;
  update co3_troubles set card = p_card, cost = c, result = res, auto = p_auto, done_at = p_at where id = p_id;
  if res = 'god' then perform co3_sat_bump(p_uid, 8); end if;
  return res;
end;
$$;
revoke all on function public.co3_trouble_do(uuid, bigint, text, boolean, timestamptz) from public, anon, authenticated;

-- 決まった数（0〜1）：会社・路線・便・日から
create or replace function co3.leg_draw(p_uid uuid, p_route text, p_leg integer, p_day date) returns numeric
language sql immutable as $$
  select (abs(('x' || substr(md5(p_uid::text || '|' || p_route || '|' || p_leg || '|' || p_day), 1, 8))::bit(32)::int) % 100000) / 100000.0
$$;
revoke all on function co3.leg_draw(uuid, text, integer, date) from public, anon, authenticated;

-- 15分ごと：出発の3時間前になった便を決める。p_at は試験用
create or replace function public.co3_legs_check(p_at timestamptz default now()) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare today date := (p_at at time zone 'Asia/Tokyo')::date; c record; l record; e record; pv record;
        dep_at timestamptz; rn int; rc int; rd numeric; inh int; dl int; st text; rev numeric; loss numeric; n int := 0;
        start_at timestamptz; h int; tid bigint; slack int;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for c in select user_id, auto_trouble from companies where policy in ('fsc', 'mcc', 'lcc', 'regional') loop
    for l in select x.*, lag(x.arr_min) over (partition by x.route_key order by x.leg) as prev_arr
               from co3_route_legs(c.user_id) x loop
      dep_at := (today + make_interval(mins => l.dep_min)) at time zone 'Asia/Tokyo';
      continue when dep_at - interval '3 hours' > p_at or dep_at <= p_at;    -- 3時間前になっていない・もう出た
      continue when exists (select 1 from co3_leg_status s where s.user_id = c.user_id and s.day = today and s.route_key = l.route_key and s.leg = l.leg);
      select * into e from co3_route_econ(c.user_id) r where r.route_key = l.route_key;
      continue when e.intl;
      rev := case when e.flights > 0 then e.revenue / e.flights else 0 end;
      -- 本物の便：同じ区間・同じ向き・定刻が前後90分
      select count(*)::int, count(*) filter (where coalesce(fs.dep_status, '') ~* 'cancel')::int,
             avg(greatest(0, extract(epoch from (fs.etd - fs.std)) / 60)) filter (where coalesce(fs.dep_status, '') !~* 'cancel' and fs.etd is not null)
        into rn, rc, rd
        from flight_schedule fs
       where fs.svc_date = today and fs.dep = l.dep and fs.arr = l.arr and abs(extract(epoch from (fs.std - dep_at))) <= 90 * 60;
      -- 前の便から続く遅れ
      select * into pv from co3_leg_status s where s.user_id = c.user_id and s.day = today and s.route_key = l.route_key and s.leg = l.leg - 1;
      slack := case when l.prev_arr is null then 0 else greatest(0, l.dep_min - l.prev_arr - 40) end;
      inh := case when pv is null or pv.status = 'cxl' then 0 else greatest(0, pv.delay_min - slack) end;
      if rn > 0 and co3.leg_draw(c.user_id, l.route_key, l.leg, today) < rc::numeric / rn then
        st := 'cxl'; dl := 0; loss := rev;
      else
        dl := greatest(coalesce(round(rd)::int, 0), inh);
        st := case when dl >= 15 then 'delay' else 'ok' end;
        loss := case when st = 'delay' then round(rev * 0.1, 2) else 0 end;
      end if;
      insert into co3_leg_status (user_id, day, route_key, leg, dep, arr, dep_at, status, delay_min, carried, real_n, real_cxl, real_delay, rev_flight, loss, decided_at)
      values (c.user_id, today, l.route_key, l.leg, l.dep, l.arr, dep_at, st, dl, inh, rn, rc, round(rd)::int, round(rev, 2), loss, p_at);
      n := n + 1;
      if loss > 0 then update companies set cash = greatest(0, cash - ceil(loss)) where user_id = c.user_id; end if;
      -- 欠航か1時間以上の遅れなら、対応してください
      if st = 'cxl' or dl >= 60 then
        h := extract(hour from p_at at time zone 'Asia/Tokyo')::int;
        start_at := case when h >= 22 then ((today + 1) + time '07:00') at time zone 'Asia/Tokyo'
                         when h < 7 then (today + time '07:00') at time zone 'Asia/Tokyo' else p_at end;
        insert into co3_troubles (user_id, route_key, day, leg, kind, delay_min, dep_at, dep, arr, flights, cancelled, real_n, real_cxl, rev_flight,
                                  created_at, god_until, deadline)
        values (c.user_id, l.route_key, today, l.leg, case when st = 'cxl' then 'cxl' else 'delay' end, dl, dep_at, l.dep, l.arr, e.flights,
                case when st = 'cxl' then 1 else 0 end, rn, rc, round(rev, 2), start_at, start_at + interval '1 hour', start_at + interval '6 hours')
        on conflict do nothing returning id into tid;
        if tid is not null and c.auto_trouble then
          begin perform co3_trouble_do(c.user_id, tid, case when st = 'cxl' then 'transfer' else 'snack' end, true, start_at);
          exception when others then null; end;
        end if;
        tid := null;
      end if;
    end loop;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_legs_check(timestamptz) from public, anon, authenticated;

-- 本物の便と照らして決めた路線は、実際の空の倍率から欠航の分を除く
create or replace function public.co3_sky_cxl_back(p_uid uuid, p_route text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((
    select least(0.10, s.cxl::numeric / greatest(1, s.n + s.cxl))
      from co_sky s
     where s.route_key = p_route and s.day >= (now() at time zone 'Asia/Tokyo')::date - 3
       and exists (select 1 from co3_leg_status x where x.user_id = p_uid and x.route_key = p_route and x.day = s.day and x.real_n > 0)
     order by s.day desc limit 1), 0)
$$;
revoke all on function public.co3_sky_cxl_back(uuid, text) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_sky_cxl_back' in src) = 0 then
    if position('* g2.sky *' in src) = 0 then raise exception 'co3_route_econ の形が変わっていて、実際の空を直せない'; end if;
    src := replace(src, '* g2.sky *', '* (g2.sky + co3_sky_cxl_back(g2.user_id, g2.route_key)) *');
    execute src;
  end if;
end
$do$;

-- 会社の状態のトラブルに、便・種類・遅れ・合うカードを足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''fits''' in src) = 0 then
    if position($r$'card', t.card, 'cost', t.cost,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、便ごとのトラブルを入れられない'; end if;
    src := replace(src, $r$'card', t.card, 'cost', t.cost,$r$,
      $r$'leg', t.leg, 'kind', t.kind, 'delay_min', t.delay_min, 'dep_at', t.dep_at, 'dep', t.dep, 'arr', t.arr,
                 'fits', (select coalesce(jsonb_agg(k), '[]'::jsonb) from unnest(array['transfer', 'hotel', 'snack']) k
                           where co3.card_fits2(k, t.kind, t.delay_min,
                                   case when t.dep_at is null then null else (extract(hour from t.dep_at at time zone 'Asia/Tokyo') * 60 + extract(minute from t.dep_at at time zone 'Asia/Tokyo'))::int end)),
                 'card', t.card, 'cost', t.cost,$r$);
    execute src;
  end if;
end
$do$;

-- 朝のまとめ：前の日の遅れの便の数も出す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_morning(uuid)'::regprocedure) into src;
  if position('delayed' in src) = 0 then
    if position($r$'open', $r$ in src) = 0 then raise exception 'co3_morning の形が変わっていて、遅れを入れられない'; end if;
    src := replace(src, $r$'open', $r$,
      $r$'delayed', (select count(*) from co3_leg_status x, t where x.user_id = p_uid and x.day = t.today - 1 and x.status = 'delay'),
    'legs_done', (select count(*) from co3_leg_status x, t where x.user_id = p_uid and x.day = t.today - 1),
    'cxl_legs', (select count(*) from co3_leg_status x, t where x.user_id = p_uid and x.day = t.today - 1 and x.status = 'cxl'),
    'open', $r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    begin execute $q$ select cron.unschedule('co3-trouble-detect') $q$; exception when others then null; end;
    execute $q$ select cron.schedule('co3-legs-check', '*/15 * * * *', $job$ select public.co3_legs_check() $job$) $q$;
  end if;
end
$$;
