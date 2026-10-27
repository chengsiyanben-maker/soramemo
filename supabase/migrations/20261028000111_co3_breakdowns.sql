-- エアライン経営 co-v3：機体の故障と予備機（格付け3から。仕様書「欠航と遅れ」の表）
--   毎朝4時（日本時間）に、格付け3以上の会社の、路線に入っている機体ごとに故障を引く（会社・機体・日から作る決まった数で）
--     1年あたりの回数 ＝ 1 ＋ 世代（旧い 1.5・中くらい 0.75・新しい 0）＋ 古さ（会社の機体の古さ 0〜−20% を 0〜1.5 に）
--       → 新品の新世代で年1回、古い旧世代で年4回。役職「整備」がいれば ×0.7
--     故障したら1〜3日運休。点検（A点検）はまだないので「点検の後30日は半分」は点検を作るときに足す
--   予備機：路線に入れていない旅客機で、その路線に入れられる大きさ（国際線は国際線で乗った機体）なら代わりに飛ぶ
--     予備機が飛ぶ日は、その路線の便はいつもどおり（本物の便の欠航・遅れは同じように決める）
--     予備機がなければ、その路線の便は欠航（会社のせい。収益0）。対応してくださいは、その日のはじめの1便だけ
--   定時率（前の30日、会社のせいのものだけ ＝ 故障の欠航）：満足度の目標値 95%以上 +10・90% +5・80% 0・70% −8・それより下 −15、
--     自分のせいの欠航1便 −1（最大 −10）。評判は 90%以上 +20点・70%未満 −20点。どれも格付け3から（それまでは故障が起きないので数えない）
--   乗員の経験・人の不足は、乗員の仕組みを作るときに足す

create table if not exists public.co3_breakdowns (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  aircraft_id bigint not null references public.aircraft(id) on delete cascade,
  route_key   text not null,
  start_day   date not null,
  days        integer not null check (days between 1 and 3),
  end_day     date not null,
  spare_id    bigint references public.aircraft(id) on delete set null,
  created_at  timestamptz not null default now(),
  unique (aircraft_id, start_day)
);
create index if not exists co3_breakdowns_user on public.co3_breakdowns (user_id, end_day);
alter table public.co3_breakdowns enable row level security;
revoke all on public.co3_breakdowns from public, anon, authenticated;
grant select on public.co3_breakdowns to authenticated;
drop policy if exists "own breakdowns" on public.co3_breakdowns;
create policy "own breakdowns" on public.co3_breakdowns for select to authenticated using (user_id = auth.uid());

-- 便ごとの結果・トラブルに原因（real ＝ 本物の便から、breakdown ＝ 機体の故障）と予備機を足す。RLS はそのまま
alter table public.co3_leg_status add column if not exists cause text check (cause in ('real', 'breakdown'));
alter table public.co3_leg_status add column if not exists spare boolean not null default false;
alter table public.co3_leg_status enable row level security;
alter table public.co3_troubles add column if not exists cause text check (cause in ('real', 'breakdown'));
alter table public.co3_troubles enable row level security;

-- 1年あたりの故障の回数
create or replace function public.co3_breakdown_rate(p_aircraft bigint) returns numeric
language sql stable security definer set search_path = public as $$
  select (1 + case coalesce(t.gen, 'mid') when 'old' then 1.5 when 'mid' then 0.75 else 0 end
             + least(1.5, greatest(0, (1 - ac_age(a.bought_at)) / 0.2 * 1.5)))
         * case when c.roles ? 'maint' and c.roles->>'maint' ~ '^[0-9]+$' then 0.7 else 1 end
    from aircraft a join companies c on c.user_id = a.user_id
    left join co3_types t on t.code = coalesce(a.co3_code, co3_type_of(a.icao))
   where a.id = p_aircraft
$$;
revoke all on function public.co3_breakdown_rate(bigint) from public, anon, authenticated;

-- その日、その路線は飛べるか：'down'（故障・予備機なし）・'spare'（予備機が飛ぶ）・null（ふつう）
create or replace function public.co3_grounded(p_uid uuid, p_route text, p_day date) returns text
language sql stable security definer set search_path = public as $$
  select case when b.spare_id is null then 'down' else 'spare' end
    from co3_breakdowns b where b.user_id = p_uid and b.route_key = p_route and p_day between b.start_day and b.end_day
   order by b.spare_id nulls first limit 1
$$;
revoke all on function public.co3_grounded(uuid, text, date) from public, anon, authenticated;

-- 毎朝：故障を引く。p_day は試験用
create or replace function public.co3_breakdown_draw(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); a record; p numeric; x numeric; nd int; sp bigint; n int := 0;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for a in select ac.id, ac.user_id, ac.route_key, r.min_size, r.intl
             from aircraft ac join companies c on c.user_id = ac.user_id
             cross join lateral (select x.min_size, x.intl from co_routes(ac.user_id) x where x.route_key = ac.route_key) r
            where ac.route_key is not null and c.rating >= 3 and c.policy in ('fsc', 'mcc', 'lcc', 'regional')
              and not co3_is_freighter(ac.id) and not co3_is_bizjet(ac.id)
              and not exists (select 1 from co3_breakdowns b where b.aircraft_id = ac.id and d between b.start_day and b.end_day)
  loop
    p := co3_breakdown_rate(a.id) / 365;
    x := co3.leg_draw(a.user_id, 'brk:' || a.id, 0, d);
    continue when x >= p;
    nd := 1 + floor(co3.leg_draw(a.user_id, 'brkdays:' || a.id, 0, d) * 3)::int;
    -- 予備機：路線に入れていない旅客機・大きさが合う・国際線なら国際線で乗った機体・ほかで予備機をしていない・故障していない
    select s.id into sp from aircraft s
     where s.user_id = a.user_id and s.route_key is null and not co3_is_freighter(s.id) and not co3_is_bizjet(s.id)
       and a.min_size >= (ac_spec(s.type)).min_size and (not a.intl or s.intl)
       and not exists (select 1 from co3_breakdowns b where b.spare_id = s.id and b.end_day >= d)
       and not exists (select 1 from co3_breakdowns b where b.aircraft_id = s.id and b.end_day >= d)
     order by s.id limit 1;
    insert into co3_breakdowns (user_id, aircraft_id, route_key, start_day, days, end_day, spare_id)
    values (a.user_id, a.id, a.route_key, d, nd, d + nd - 1, sp) on conflict do nothing;
    sp := null; n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_breakdown_draw(date) from public, anon, authenticated;

create or replace function public.co3_legs_check(p_at timestamptz default now()) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare today date := (p_at at time zone 'Asia/Tokyo')::date; c record; l record; e record; pv record;
        dep_at timestamptz; rn int; rc int; rd numeric; inh int; dl int; st text; rev numeric; loss numeric; n int := 0;
        start_at timestamptz; h int; tid bigint; slack int; g text; cs text; brk_first boolean;
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
      g := co3_grounded(c.user_id, l.route_key, today);
      cs := null;
      if g = 'down' then
        st := 'cxl'; dl := 0; loss := rev; cs := 'breakdown';                 -- 機体の故障・予備機なし（会社のせい）
      elsif rn > 0 and co3.leg_draw(c.user_id, l.route_key, l.leg, today) < rc::numeric / rn then
        st := 'cxl'; dl := 0; loss := rev; cs := 'real';
      else
        dl := greatest(coalesce(round(rd)::int, 0), inh);
        st := case when dl >= 15 then 'delay' else 'ok' end;
        loss := case when st = 'delay' then round(rev * 0.1, 2) else 0 end;
        cs := case when st = 'delay' then 'real' end;
      end if;
      insert into co3_leg_status (user_id, day, route_key, leg, dep, arr, dep_at, status, delay_min, carried, real_n, real_cxl, real_delay, rev_flight, loss, decided_at, cause, spare)
      values (c.user_id, today, l.route_key, l.leg, l.dep, l.arr, dep_at, st, dl, inh, rn, rc, round(rd)::int, round(rev, 2), loss, p_at, cs, coalesce(g = 'spare', false));
      n := n + 1;
      if loss > 0 then update companies set cash = greatest(0, cash - ceil(loss)) where user_id = c.user_id; end if;
      -- 欠航か1時間以上の遅れなら、対応してください
      -- 故障の欠航は、その日のその路線のはじめの1便だけ「対応してください」
      brk_first := cs is distinct from 'breakdown' or not exists (select 1 from co3_troubles t where t.user_id = c.user_id and t.route_key = l.route_key and t.day = today and t.cause = 'breakdown');
      if (st = 'cxl' or dl >= 60) and brk_first then
        h := extract(hour from p_at at time zone 'Asia/Tokyo')::int;
        start_at := case when h >= 22 then ((today + 1) + time '07:00') at time zone 'Asia/Tokyo'
                         when h < 7 then (today + time '07:00') at time zone 'Asia/Tokyo' else p_at end;
        insert into co3_troubles (user_id, route_key, day, leg, kind, delay_min, dep_at, dep, arr, flights, cancelled, real_n, real_cxl, rev_flight,
                                  created_at, god_until, deadline, cause)
        values (c.user_id, l.route_key, today, l.leg, case when st = 'cxl' then 'cxl' else 'delay' end, dl, dep_at, l.dep, l.arr, e.flights,
                case when st = 'cxl' then 1 else 0 end, rn, rc, round(rev, 2), start_at, start_at + interval '1 hour', start_at + interval '6 hours', cs)
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

-- 定時率（前の30日、会社のせいの欠航だけ）
create or replace function public.co3_ontime(p_uid uuid, out legs integer, out own_cxl integer, out rate numeric)
language sql stable security definer set search_path = public as $$
  select count(*)::int, count(*) filter (where status = 'cxl' and cause = 'breakdown')::int,
         case when count(*) > 0 then round(1 - count(*) filter (where status = 'cxl' and cause = 'breakdown')::numeric / count(*), 4) end
    from co3_leg_status where user_id = p_uid and day > (now() at time zone 'Asia/Tokyo')::date - 30
$$;
revoke all on function public.co3_ontime(uuid) from public, anon, authenticated;

create or replace function co3.ontime_points(p_rate numeric) returns numeric
language sql immutable as $$
  select case when p_rate is null then 0 when p_rate >= 0.95 then 10 when p_rate >= 0.90 then 5 when p_rate >= 0.80 then 0 when p_rate >= 0.70 then -8 else -15 end::numeric
$$;
revoke all on function co3.ontime_points(numeric) from public, anon, authenticated;

-- 満足度の目標値に「定時率」「自分のせいの欠航」を足す（格付け3から。列が増えるので作り直す）
drop function if exists public.co3_satisfaction_parts(uuid);
create function public.co3_satisfaction_parts(p_uid uuid,
  out base numeric, out packed numeric, out new_share numeric, out aging numeric, out policy_adj numeric, out meal numeric, out bag numeric,
  out response numeric, out ontime numeric, out own_cxl numeric, out ontime_rate numeric, out target numeric)
language sql stable security definer set search_path = public as $$
  with c as (select policy, meal, bag, rating from companies where user_id = p_uid),
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
           case when c.rating >= 3 then o.rate end as ontime_rate
      from c cross join f cross join t cross join o)
  select p.base, p.packed, p.new_share, p.aging, p.policy_adj, p.meal, p.bag, p.response, p.ontime, p.own_cxl, p.ontime_rate,
         greatest(0, least(100, p.base + p.packed + p.new_share + p.aging + p.policy_adj + p.meal + p.bag + p.response + p.ontime + p.own_cxl))
    from p
$$;
revoke all on function public.co3_satisfaction_parts(uuid) from public, anon, authenticated;

-- 評判：定時率 90%以上 +20点・70%未満 −20点（格付け3から）
create or replace function public.co3_ontime_rep(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$
  select case when (select rating from companies where user_id = p_uid) < 3 then 0
              when o.rate is null then 0 when o.rate >= 0.90 then 20 when o.rate < 0.70 then -20 else 0 end::bigint
    from co3_ontime(p_uid) o
$$;
revoke all on function public.co3_ontime_rep(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_rep_points(uuid)'::regprocedure) into src;
  if position('co3_ontime_rep' in src) = 0 then
    if position('+ co3_trouble_rep(p_uid)' in src) = 0 then raise exception 'co_rep_points の形が変わっていて、定時率の評判を入れられない'; end if;
    src := replace(src, '+ co3_trouble_rep(p_uid)', '+ co3_trouble_rep(p_uid)' || chr(10) || '       + co3_ontime_rep(p_uid)');
    execute src;
  end if;
end
$do$;

-- 会社の状態：いまの故障（運休中・予備機）と、トラブルの原因
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''breakdowns''' in src) = 0 then
    if position($r$'leg', t.leg, 'kind', t.kind,$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then
      raise exception 'co_state の形が変わっていて、故障を入れられない';
    end if;
    src := replace(src, $r$'leg', t.leg, 'kind', t.kind,$r$, $r$'leg', t.leg, 'kind', t.kind, 'cause', t.cause,$r$);
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'breakdowns', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('id', b.id, 'ac_id', b.aircraft_id, 'reg', a.reg, 'k', b.route_key,
                 'start', b.start_day, 'end', b.end_day, 'days', b.days, 'spare_id', b.spare_id, 'spare_reg', s.reg) order by b.start_day desc), '[]'::jsonb)
                 from co3_breakdowns b join aircraft a on a.id = b.aircraft_id left join aircraft s on s.id = b.spare_id
                where b.user_id = uid and b.end_day >= (now() at time zone 'Asia/Tokyo')::date - 1) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

-- 朝のまとめの遅れの波に、原因と予備機を足す
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_morning(uuid)'::regprocedure) into src;
  if position($r$'why', x.cause$r$ in src) = 0 then
    if position($r$'rn', x.real_n)$r$ in src) = 0 then raise exception 'co3_morning の形が変わっていて、原因を入れられない'; end if;
    src := replace(src, $r$'rn', x.real_n)$r$, $r$'rn', x.real_n, 'why', x.cause, 'spare', x.spare)$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-breakdown', '0 19 * * *', $job$ select public.co3_breakdown_draw() $job$) $q$;
  end if;
end
$$;
