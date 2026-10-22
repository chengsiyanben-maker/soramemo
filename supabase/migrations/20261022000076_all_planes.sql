-- 全機の記録：
--   ・airport_tracks_all：空港ごと・日ごとの、全航空会社の機体の上昇・降下の航跡（毎晩 rwy-learn が track_points から作る）。31日残す
--   ・reg_legs：機体（登録記号）ごとの、その日に飛んだ便（呼び出し符号）・時刻・出発と到着の空港。airport-traffic が2分ごとに足し、
--     rwy-learn が出発・到着の空港を入れる。400日残す。航空会社の便（呼び出し符号が「英字3文字＋数字」）だけで、自家用機などは記録しない
--   ・predict_rotation：時刻表のある JAL・ANA の便はこれまでどおり。ない機体は reg_legs の「この便のあとによく続く便」から予想する
create table if not exists public.airport_tracks_all (
  iata     text not null check (iata ~ '^[A-Z]{3}$'),
  day      date not null,
  callsign text not null check (callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  at       timestamptz not null,      -- 空港のいちばん近くにいた時刻
  dep_here smallint not null check (dep_here in (0, 1)),
  pts      text not null check (length(pts) <= 4000),
  primary key (iata, day, callsign, at)
);
alter table public.airport_tracks_all enable row level security;
revoke all on public.airport_tracks_all from public, anon, authenticated;

create table if not exists public.reg_legs (
  reg      text not null check (reg ~ '^[A-Z0-9-]{2,10}$'),
  callsign text not null check (callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  day      date not null,
  type     text check (length(type) <= 8),
  first_at timestamptz not null,
  last_at  timestamptz not null,
  dep      text check (dep ~ '^[A-Z]{3}$'),
  arr      text check (arr ~ '^[A-Z]{3}$'),
  primary key (reg, day, callsign)
);
create index if not exists reg_legs_cs on public.reg_legs (callsign, day);
create index if not exists reg_legs_day on public.reg_legs (day);
alter table public.reg_legs enable row level security;
revoke all on public.reg_legs from public, anon, authenticated;

-- airport-traffic から（service_role）：見えた機体をまとめて足す。[{reg, cs, type, at}]
create or replace function public.reg_legs_touch(p_rows jsonb) returns int
language sql security definer set search_path = public as $$
  with r as (
    select x->>'reg' as reg, x->>'cs' as cs, nullif(x->>'type', '') as type, (x->>'at')::timestamptz as at
    from jsonb_array_elements(p_rows) x
    where x->>'reg' ~ '^[A-Z0-9-]{2,10}$' and x->>'cs' ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and (x->>'at') is not null
  ), ins as (
    insert into public.reg_legs (reg, callsign, day, type, first_at, last_at)
    -- 同じ便が1回の中に2回あってもよいように、まとめてから
    select reg, cs, (at at time zone 'Asia/Tokyo')::date, left(max(type), 8), min(at), max(at) from r group by 1, 2, 3
    on conflict (reg, day, callsign) do update set last_at = greatest(reg_legs.last_at, excluded.last_at), first_at = least(reg_legs.first_at, excluded.first_at),
      type = coalesce(excluded.type, reg_legs.type)
    returning 1
  ) select count(*)::int from ins
$$;
revoke all on function public.reg_legs_touch(jsonb) from public, anon, authenticated;

-- rwy-learn から（service_role）：出発・到着の空港を入れる。[{cs, dir:'arr'|'dep', iata, at}]
create or replace function public.reg_legs_route(p_rows jsonb) returns int
language plpgsql security definer set search_path = public as $$
declare x jsonb; n int := 0; t timestamptz; c int;
begin
  for x in select * from jsonb_array_elements(p_rows) loop
    t := (x->>'at')::timestamptz;
    if x->>'dir' = 'arr' then
      update public.reg_legs set arr = x->>'iata' where callsign = x->>'cs' and day between (t at time zone 'Asia/Tokyo')::date - 1 and (t at time zone 'Asia/Tokyo')::date
        and first_at <= t + interval '10 minutes' and last_at >= t - interval '40 minutes';
    else
      update public.reg_legs set dep = x->>'iata' where callsign = x->>'cs' and day between (t at time zone 'Asia/Tokyo')::date - 1 and (t at time zone 'Asia/Tokyo')::date
        and first_at <= t + interval '40 minutes' and last_at >= t - interval '10 minutes';
    end if;
    get diagnostics c = row_count; n := n + c;
  end loop;
  return n;
end $$;
revoke all on function public.reg_legs_route(jsonb) from public, anon, authenticated;

-- 空の道すじ：全機の航跡があればそれを、なければこれまでの JAL・ANA の便の航跡を
create or replace function public.airport_tracks(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  a as (select dep_here, pts from public.airport_tracks_all, d where iata = p_iata and day = p_day and p_day < d.today and p_day >= d.today - 30 order by at limit 3000)
  select case when exists (select 1 from a) then (select jsonb_agg(jsonb_build_object('d', dep_here, 'p', pts)) from a)
  else coalesce((select jsonb_agg(jsonb_build_object('d', q.dep_here, 'p', q.pts)) from (
    select case when h.dep = p_iata then 1 else 0 end as dep_here, t.pts
    from d, public.flight_history h join public.flight_tracks t on t.svc_date = h.svc_date and t.flight = h.flight and t.dep = h.dep
    where h.svc_date = p_day and p_day < d.today and p_day >= d.today - 30 and (h.dep = p_iata or h.arr = p_iata)
    order by h.std limit 2000) q), '[]'::jsonb) end
$$;
revoke all on function public.airport_tracks(text, date) from public;
grant execute on function public.airport_tracks(text, date) to anon, authenticated;

-- 機体の運用の予想（全機）：今日いちばん新しい便から、前の60日で「その便のあとに同じ機体が飛んだ便」をたどる（同じ曜日は2倍に数える）。
--   3回以上見ていて、4割以上のときだけ出す。時刻は、その便が前に見えはじめた時刻（日本時間）の中央値
create or replace function public.predict_rotation_reg(p_reg text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare today date := (now() at time zone 'Asia/Tokyo')::date; cur record; nxt record; steps jsonb := '[]'::jsonb; i int := 0; prev text; seen_cs text[] := '{}';
begin
  if p_reg is null or p_reg !~ '^[A-Z0-9-]{2,10}$' then return null; end if;
  select callsign, dep, arr, first_at, last_at, type into cur from public.reg_legs where reg = p_reg and day >= today - 1 order by last_at desc limit 1;
  if cur is null then return jsonb_build_object('reg', p_reg, 'known', null, 'next', '[]'::jsonb, 'src', 'reg'); end if;
  prev := cur.callsign; seen_cs := array[prev];
  while i < 4 loop
    with seq as (
      select reg, day, callsign, lead(callsign) over (partition by reg, day order by first_at) as nx
      from public.reg_legs l
      where (l.reg, l.day) in (select reg, day from public.reg_legs where callsign = prev and day >= today - 60 and day < today)
    ), c as (
      select nx, sum(case when extract(dow from day) = extract(dow from today) then 2 else 1 end) as score, count(*) as n
      from seq where callsign = prev and nx is not null group by nx
    ), t as (select sum(score) as total from c)
    select c.nx, c.score, c.n, t.total,
      (select percentile_disc(0.5) within group (order by (first_at at time zone 'Asia/Tokyo')::time) from public.reg_legs r where r.callsign = c.nx and r.day >= today - 60) as tm,
      (select mode() within group (order by dep) from public.reg_legs r where r.callsign = c.nx and r.day >= today - 60 and dep is not null) as dep,
      (select mode() within group (order by arr) from public.reg_legs r where r.callsign = c.nx and r.day >= today - 60 and arr is not null) as arr
    into nxt from c, t order by c.score desc limit 1;
    exit when nxt is null or nxt.n < 3 or nxt.score::numeric / greatest(nxt.total, 1) < 0.4 or nxt.nx = any(seen_cs);
    steps := steps || jsonb_build_object('callsign', nxt.nx, 'dep', nxt.dep, 'arr', nxt.arr, 'time', to_char(nxt.tm, 'HH24:MI'), 'seen', nxt.n,
      'share', round(nxt.score::numeric / greatest(nxt.total, 1), 2));
    prev := nxt.nx; seen_cs := seen_cs || prev; i := i + 1;
  end loop;
  return jsonb_build_object('reg', p_reg, 'src', 'reg', 'type', cur.type,
    'known', jsonb_build_object('callsign', cur.callsign, 'dep', cur.dep, 'arr', cur.arr, 'first', cur.first_at, 'last', cur.last_at), 'next', steps);
end $$;
revoke all on function public.predict_rotation_reg(text) from public;
grant execute on function public.predict_rotation_reg(text) to anon, authenticated;

-- 機体の今日と前の日の便（登録記号で）
create or replace function public.reg_history(p_reg text, p_days int default 7) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('day', day, 'callsign', callsign, 'dep', dep, 'arr', arr, 'first', first_at, 'last', last_at, 'type', type) order by first_at desc), '[]'::jsonb)
  from (select * from public.reg_legs where reg = p_reg and day >= (now() at time zone 'Asia/Tokyo')::date - least(greatest(coalesce(p_days, 7), 1), 30) order by first_at desc limit 80) q
$$;
revoke all on function public.reg_history(text, int) from public;
grant execute on function public.reg_history(text, int) to anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('all-planes-cleanup', '27 19 * * *', $job$
    delete from public.airport_tracks_all where day < (now() at time zone 'Asia/Tokyo')::date - 31;
    delete from public.reg_legs where day < (now() at time zone 'Asia/Tokyo')::date - 400
  $job$) $q$;
end
$outer$;
