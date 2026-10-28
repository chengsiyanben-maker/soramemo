-- エアライン経営 co-v3：自分で組むスケジュール（格付け2から。仕様書「スケジュールの組み方」「機体の1日のスケジュール」）
--   機体ごとに、時刻つきの1日の便の並びを決める（いくつもの路線をまたいでよい・毎日同じ）。決めた機体は「自分で組む」、ほかは今までの「おまかせ」
--   決まり：便はつながっていること（着いた空港から次が出る）、1日の最後は最初の便が出る空港に着く（そこに泊まる）
--     飛ぶ時間 ＝ 距離 ÷ 速さ（プロペラ 450km/h・リージョナル 750km/h・ジェット 820km/h）＋ 20分
--     折り返しの最短：プロペラ・小型機 20分、リージョナル・中小のジェット 35分（LCC は25分）、大型 60分
--     空港の運用時間：羽田・関西 24時間、成田 6〜24時、伊丹 7〜21時、福岡 7〜22時、ほかは 8〜20時（便は出発から到着まで中に入ること）
--     路線は自社の路線だけ（国際線は国際線で乗った機体）、空港の大きさが合うこと、1日16便まで
--   路線の計算：おまかせの便＋自分で組んだ便が、その路線の1日の便数。席は機体ごとの席の平均で数える
--   便ごとの客・トラブル・故障・遅れの続き方（同じ機体の前の便から）も、自分で組んだ便で数える
--   夏ダイヤ・冬ダイヤ、便名（SORAM 101 など）は、ダイヤ改正を作るときに足す

create table if not exists public.co3_sched (
  user_id     uuid not null references auth.users(id) on delete cascade,
  aircraft_id bigint not null references public.aircraft(id) on delete cascade,
  seq         integer not null check (seq between 1 and 16),
  route_key   text not null,
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$'),
  dep_min     integer not null check (dep_min between 0 and 1439),
  arr_min     integer not null check (arr_min between 1 and 1440),
  primary key (aircraft_id, seq)
);
create index if not exists co3_sched_route on public.co3_sched (user_id, route_key);
alter table public.co3_sched enable row level security;
revoke all on public.co3_sched from public, anon, authenticated;
grant select on public.co3_sched to authenticated;
drop policy if exists "own schedule" on public.co3_sched;
create policy "own schedule" on public.co3_sched for select to authenticated using (user_id = auth.uid());

-- 便ごとの結果に機体を足す（遅れの続き方を機体ごとに見る）。RLS はそのまま
alter table public.co3_leg_status add column if not exists aircraft_id bigint;
alter table public.co3_leg_status enable row level security;

create or replace function co3.speed_kmh(p_type text) returns integer
language sql immutable as $$ select case p_type when 'prop' then 450 when 'rj' then 750 else 820 end $$;
create or replace function co3.turn_min(p_type text, p_policy text) returns integer
language sql immutable as $$ select case when p_type = 'prop' then 20 when p_type in ('wb', 'lg') then 60 when p_policy = 'lcc' then 25 else 35 end $$;
create or replace function co3.sched_block(p_km numeric, p_type text) returns integer
language sql immutable as $$ select (round(p_km / co3.speed_kmh(p_type) * 60) + 20)::int $$;
create or replace function co3.ap_open(p_iata text) returns integer
language sql immutable as $$ select case p_iata when 'HND' then 0 when 'KIX' then 0 when 'NRT' then 360 when 'ITM' then 420 when 'FUK' then 420 else 480 end $$;
create or replace function co3.ap_close(p_iata text) returns integer
language sql immutable as $$ select case p_iata when 'HND' then 1440 when 'KIX' then 1440 when 'NRT' then 1440 when 'ITM' then 1260 when 'FUK' then 1320 else 1200 end $$;
revoke all on function co3.speed_kmh(text), co3.turn_min(text, text), co3.sched_block(numeric, text), co3.ap_open(text), co3.ap_close(text) from public, anon, authenticated;

-- 路線に「おまかせ」で入っている機体・その便数、自分で組んだ便の数と平均の席
create or replace function public.co3_assigned_ac(p_uid uuid, p_route text) returns bigint
language sql stable security definer set search_path = public as $$
  select id from aircraft where user_id = p_uid and route_key = p_route order by id limit 1
$$;
create or replace function public.co3_sched_ac(p_uid uuid, p_route text) returns bigint
language sql stable security definer set search_path = public as $$
  select aircraft_id from co3_sched where user_id = p_uid and route_key = p_route order by aircraft_id limit 1
$$;
create or replace function public.co3_auto_fl(p_uid uuid, p_route text, p_km numeric, p_policy text) returns integer
language sql stable security definer set search_path = public as $$
  select case when a.id is null or co3_is_freighter(a.id) or co3_is_bizjet(a.id) or p_policy in ('cargo', 'pj') then 0
              else least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = p_route), 99), co3.legs_per_day(p_km)) end
    from (select co3_assigned_ac(p_uid, p_route) as id) a
$$;
create or replace function public.co3_custom(p_uid uuid, p_route text, out n integer, out seats numeric)
language sql stable security definer set search_path = public as $$
  select count(*)::int, coalesce(avg((co3_ac_spec(s.aircraft_id)).seats), 0)
    from co3_sched s where s.user_id = p_uid and s.route_key = p_route
$$;
revoke all on function public.co3_assigned_ac(uuid, text), public.co3_sched_ac(uuid, text), public.co3_auto_fl(uuid, text, numeric, text), public.co3_custom(uuid, text) from public, anon, authenticated;

-- 自分で組むスケジュールを決める。p_legs ＝ [{dep, arr, t（出発の分）}, …]
create or replace function public.co3_set_schedule(p_aircraft bigint, p_legs jsonb) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); ac aircraft; pol text; n int; i int; l jsonb; prev_arr text; prev_t int; r record;
        v_dep text; v_arr text; t int; blk int; first_dep text; turn int; ms int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 2 then raise exception 'rating required 2'; end if;
  select * into ac from aircraft where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  select policy into pol from companies where user_id = uid;
  if pol in ('cargo', 'pj') or co3_is_freighter(ac.id) or co3_is_bizjet(ac.id) then raise exception 'not a passenger aircraft'; end if;
  n := coalesce(jsonb_array_length(p_legs), 0);
  if n < 1 or n > 16 then raise exception 'legs 1 to 16'; end if;
  turn := co3.turn_min(ac.type, pol);
  ms := (ac_spec(ac.type)).min_size;
  delete from co3_sched where aircraft_id = ac.id;
  for i in 0..n - 1 loop
    l := p_legs->i; v_dep := upper(l->>'dep'); v_arr := upper(l->>'arr'); t := (l->>'t')::int;
    select * into r from co_routes(uid) x where (x.a = v_dep and x.b = v_arr) or (x.a = v_arr and x.b = v_dep) limit 1;
    if not found then raise exception 'route not found %-%', v_dep, v_arr; end if;
    if r.min_size < ms then raise exception 'airport too small %-%', v_dep, v_arr; end if;
    if r.intl and not ac.intl then raise exception 'not intl'; end if;
    blk := co3.sched_block(r.km, ac.type);
    if i = 0 then first_dep := v_dep; end if;
    if i > 0 and v_dep <> prev_arr then raise exception 'not connected at %', i + 1; end if;
    if i > 0 and t < prev_t + turn then raise exception 'turn too short at %', i + 1; end if;
    if t < co3.ap_open(v_dep) or t + blk > co3.ap_close(v_arr) or t + blk > 1440 then raise exception 'outside hours at %', i + 1; end if;
    insert into co3_sched (user_id, aircraft_id, seq, route_key, dep, arr, dep_min, arr_min) values (uid, ac.id, i + 1, r.route_key, v_dep, v_arr, t, t + blk);
    prev_arr := v_arr; prev_t := t + blk;
  end loop;
  if prev_arr <> first_dep then raise exception 'must end at %', first_dep; end if;
  update aircraft set route_key = null where id = ac.id;    -- おまかせの路線からは外す
  return co_state();
end;
$$;
revoke all on function public.co3_set_schedule(bigint, jsonb) from public, anon;
grant execute on function public.co3_set_schedule(bigint, jsonb) to authenticated;

create or replace function public.co3_clear_schedule(p_aircraft bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  delete from co3_sched where aircraft_id = p_aircraft and user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_clear_schedule(bigint) from public, anon;
grant execute on function public.co3_clear_schedule(bigint) to authenticated;

-- 路線の計算：便数 ＝ おまかせ ＋ 自分で組んだ便、席は平均。自分で組んだ便だけの路線も飛ぶ
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_custom' in src) = 0 then
    if position('x.ac_id, x.ac_type' in src) = 0 or position('coalesce((co3_ac_spec(r.ac_id)).seats, 0) as raw_seats' in src) = 0
       or position('left join co3_airport_stats sb on sb.iata = r.b' in src) = 0 or src !~ 'case when r\.ac_id is null or co3_is_freighter\(r\.ac_id\).*? end as fl0' then
      raise exception 'co3_route_econ の形が変わっていて、自分で組むスケジュールを入れられない';
    end if;
    src := replace(src, 'x.ac_id, x.ac_type', 'coalesce(x.ac_id, co3_sched_ac(p_uid, x.route_key)) as ac_id, x.ac_type');
    src := replace(src, 'coalesce((co3_ac_spec(r.ac_id)).seats, 0) as raw_seats',
      'case when cu.n = 0 then coalesce((co3_ac_spec(co3_assigned_ac(p_uid, r.route_key))).seats, 0)
                else (co3_auto_fl(p_uid, r.route_key, r.km, c.policy) * coalesce((co3_ac_spec(co3_assigned_ac(p_uid, r.route_key))).seats, 0) + cu.n * cu.seats)
                     / nullif(co3_auto_fl(p_uid, r.route_key, r.km, c.policy) + cu.n, 0) end as raw_seats');
    src := regexp_replace(src, 'case when r\.ac_id is null or co3_is_freighter\(r\.ac_id\).*? end as fl0',
      'case when c.policy in (''cargo'', ''pj'') then 0 else co3_auto_fl(p_uid, r.route_key, r.km, c.policy) + cu.n end as fl0');
    src := replace(src, 'left join co3_airport_stats sb on sb.iata = r.b', 'left join co3_airport_stats sb on sb.iata = r.b' || chr(10) || '      cross join lateral co3_custom(p_uid, r.route_key) cu');
    execute src;
  end if;
end
$do$;

-- 発着枠の申し込みの数え方に、自分で組んだ便を足す（1便で出発と到着の空港に1つずつ）
create or replace function public.co3_slot_totals() returns table (iata text, total numeric)
language sql stable security definer set search_path = public as $$
  with k as (
    select ac.user_id, ac.route_key,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 1)::int) else split_part(ac.route_key, '-', 1) end as a,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 2)::int) else split_part(ac.route_key, '-', 2) end as b
      from aircraft ac where ac.route_key is not null
  ), f as (
    select k.a, k.b, coalesce(p.flights, co3.legs_per_day(coalesce(co3_km(k.a, k.b), 800))) as fl
      from k left join co3_plans p on p.user_id = k.user_id and p.route_key = k.route_key
  )
  select ap, sum(fl) from (
    select a as ap, fl from f union all select b, fl from f
    union all select s.dep, 1 from co3_sched s union all select s.arr, 1 from co3_sched s) u
   where ap in ('HND', 'NRT', 'KIX', 'ITM', 'FUK') group by ap
$$;
revoke all on function public.co3_slot_totals() from public, anon, authenticated;

-- 便ごと：おまかせの便（今までどおり並べる）と、自分で組んだ便。機体の列を足す（列が増えるので作り直す）
drop function if exists public.co3_route_legs(uuid);
create function public.co3_route_legs(p_uid uuid)
returns table (route_key text, leg integer, dep_min integer, arr_min integer, dep text, arr text, seats numeric, biz numeric, leisure numeric, aircraft_id bigint)
language plpgsql stable security definer set search_path = public as $$
declare e record; home text; blk int; gap int; n int; na int; i int; it int; aa bigint;
        d int[]; ta int[]; f text[]; t text[]; acs bigint[]; cap numeric[]; b numeric[]; l numeric[]; w numeric[]; act boolean[]; rest numeric; sw numeric; ord int[];
        s record;
begin
  select a.iata into home from companies c left join airports a on a.id = c.home_airport where c.user_id = p_uid;
  for e in select * from co3_route_econ(p_uid) r where r.flights > 0 loop
    d := array[]::int[]; ta := array[]::int[]; f := array[]::text[]; t := array[]::text[]; acs := array[]::bigint[]; cap := array[]::numeric[];
    -- 自分で組んだ便
    for s in select x.* from co3_sched x where x.user_id = p_uid and x.route_key = e.route_key order by x.dep_min loop
      d := d || s.dep_min; ta := ta || s.arr_min; f := f || s.dep; t := t || s.arr; acs := acs || s.aircraft_id; cap := cap || coalesce((co3_ac_spec(s.aircraft_id)).seats, e.seats);
    end loop;
    -- おまかせの便（残りの便数を 6:30〜23:30 に並べる）
    na := e.flights - coalesce(array_length(d, 1), 0); aa := co3_assigned_ac(p_uid, e.route_key);
    if na > 0 then
      blk := co3.leg_block_min(e.km);
      gap := case when na > 1 then greatest(blk + 40, ((1020 - blk) / (na - 1) / 5) * 5) else 0 end;
      for i in 1..na loop
        d := d || (390 + (i - 1) * gap); ta := ta || (390 + (i - 1) * gap + blk);
        if home is not null and home = e.b then
          f := f || case when i % 2 = 1 then e.b else e.a end; t := t || case when i % 2 = 1 then e.a else e.b end;
        else
          f := f || case when i % 2 = 1 then e.a else e.b end; t := t || case when i % 2 = 1 then e.b else e.a end;
        end if;
        acs := acs || aa; cap := cap || coalesce((co3_ac_spec(aa)).seats, e.seats);
      end loop;
    end if;
    n := array_length(d, 1);
    continue when n is null or n = 0;
    -- 仕事の客 → 旅行の客の順に、重みで分けて満席を超えた分を回す（5回まで）
    b := array_fill(0::numeric, array[n]); l := array_fill(0::numeric, array[n]);
    for it in 1..2 loop
      rest := case when it = 1 then coalesce(e.biz_pax, 0) else greatest(0, e.carried - coalesce(e.biz_pax, 0)) end;
      w := array[]::numeric[]; act := array[]::boolean[];
      for i in 1..n loop
        w := w || case when it = 1 then co3.biz_weight(d[i]) else co3.leisure_weight(d[i]) end; act := act || true;
      end loop;
      for x in 1..5 loop
        exit when rest <= 0.001;
        sw := 0; for i in 1..n loop if act[i] then sw := sw + w[i]; end if; end loop;
        exit when sw = 0;
        declare give numeric := rest; add numeric; room numeric;
        begin
          for i in 1..n loop
            continue when not act[i];
            room := cap[i] - b[i] - l[i];
            add := least(room, give * w[i] / sw);
            if it = 1 then b[i] := b[i] + add; else l[i] := l[i] + add; end if;
            rest := rest - add;
            if add >= room - 0.001 then act[i] := false; end if;
          end loop;
        end;
      end loop;
    end loop;
    -- 出発の早い順に番号をつける
    select array_agg(k order by d[k], k) into ord from generate_series(1, n) k;
    for i in 1..n loop
      route_key := e.route_key; leg := i; dep_min := d[ord[i]]; arr_min := ta[ord[i]]; dep := f[ord[i]]; arr := t[ord[i]];
      seats := cap[ord[i]]; biz := round(b[ord[i]], 1); leisure := round(l[ord[i]], 1); aircraft_id := acs[ord[i]];
      return next;
    end loop;
  end loop;
end;
$$;
revoke all on function public.co3_route_legs(uuid) from public, anon, authenticated;

create or replace function public.co3_ac_grounded(p_aircraft bigint, p_day date) returns text
language sql stable security definer set search_path = public as $$
  select case when b.spare_id is null then 'down' else 'spare' end
    from co3_breakdowns b where b.aircraft_id = p_aircraft and p_day between b.start_day and b.end_day limit 1
$$;
revoke all on function public.co3_ac_grounded(bigint, date) from public, anon, authenticated;

create or replace function public.co3_breakdown_draw(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); a record; p numeric; x numeric; nd int; sp bigint; n int := 0;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for a in select ac.id, ac.user_id, coalesce(ac.route_key, sr.route_key) as route_key, r.min_size, r.intl
             from aircraft ac join companies c on c.user_id = ac.user_id
             left join lateral (select s.route_key from co3_sched s where s.aircraft_id = ac.id order by s.seq limit 1) sr on true
             cross join lateral (select x.min_size, x.intl from co_routes(ac.user_id) x where x.route_key = coalesce(ac.route_key, sr.route_key)) r
            where coalesce(ac.route_key, sr.route_key) is not null and c.rating >= 3 and c.policy in ('fsc', 'mcc', 'lcc', 'regional')
              and not co3_is_freighter(ac.id) and not co3_is_bizjet(ac.id)
              and not exists (select 1 from co3_breakdowns b where b.aircraft_id = ac.id and d between b.start_day and b.end_day)
  loop
    p := co3_breakdown_rate(a.id) / 365;
    x := co3.leg_draw(a.user_id, 'brk:' || a.id, 0, d);
    continue when x >= p;
    nd := 1 + floor(co3.leg_draw(a.user_id, 'brkdays:' || a.id, 0, d) * 3)::int;
    -- 予備機：路線に入れていない旅客機・大きさが合う・国際線なら国際線で乗った機体・ほかで予備機をしていない・故障していない
    select s.id into sp from aircraft s
     where s.user_id = a.user_id and s.route_key is null and not exists (select 1 from co3_sched q where q.aircraft_id = s.id) and not co3_is_freighter(s.id) and not co3_is_bizjet(s.id)
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
#variable_conflict use_variable
declare today date := (p_at at time zone 'Asia/Tokyo')::date; c record; l record; e record; pv record;
        dep_at timestamptz; rn int; rc int; rd numeric; inh int; dl int; st text; rev numeric; loss numeric; n int := 0;
        start_at timestamptz; h int; tid bigint; slack int; g text; cs text; brk_first boolean;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  for c in select user_id, auto_trouble from companies where policy in ('fsc', 'mcc', 'lcc', 'regional') loop
    for l in select x.*, lag(x.arr_min) over (partition by coalesce(x.aircraft_id, 0), x.route_key is null order by x.dep_min) as prev_arr
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
      select * into pv from co3_leg_status s where s.user_id = c.user_id and s.day = today and s.aircraft_id is not distinct from l.aircraft_id and s.dep_at < dep_at order by s.dep_at desc limit 1;
      slack := case when l.prev_arr is null then 0 else greatest(0, l.dep_min - l.prev_arr - 40) end;
      inh := case when pv is null or pv.status = 'cxl' then 0 else greatest(0, pv.delay_min - slack) end;
      g := case when l.aircraft_id is not null then co3_ac_grounded(l.aircraft_id, today) else co3_grounded(c.user_id, l.route_key, today) end;
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
      insert into co3_leg_status (user_id, day, route_key, leg, dep, arr, dep_at, status, delay_min, carried, real_n, real_cxl, real_delay, rev_flight, loss, decided_at, cause, spare, aircraft_id)
      values (c.user_id, today, l.route_key, l.leg, l.dep, l.arr, dep_at, st, dl, inh, rn, rc, round(rd)::int, round(rev, 2), loss, p_at, cs, coalesce(g = 'spare', false), l.aircraft_id);
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

-- 会社の状態：自分で組んだスケジュール（機体ごと）と、便ごとの機体
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''scheds''' in src) = 0 then
    if position($r$'seats', x.seats, 'biz', x.biz, 'lei', x.leisure)$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then
      raise exception 'co_state の形が変わっていて、スケジュールを入れられない';
    end if;
    src := replace(src, $r$'seats', x.seats, 'biz', x.biz, 'lei', x.leisure)$r$, $r$'seats', x.seats, 'biz', x.biz, 'lei', x.leisure, 'ac', x.aircraft_id)$r$);
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'scheds', case when v3 then (select coalesce(jsonb_object_agg(g.aircraft_id, g.legs), '{}'::jsonb) from (
          select s.aircraft_id, jsonb_agg(jsonb_build_object('n', s.seq, 'k', s.route_key, 'f', s.dep, 'to', s.arr, 't', s.dep_min, 'ta', s.arr_min) order by s.seq) as legs
            from co3_sched s where s.user_id = uid group by s.aircraft_id) g) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
