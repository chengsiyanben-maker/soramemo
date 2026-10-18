-- 毎日の飛行機の記録
--   flight_history：便ごとの実績（定刻・実際の出発到着・遅れ・欠航・ダイバート・機種・登録記号）。400日残す
--   flight_tracks ：便ごとの航跡（上昇・降下中の部分を間引いて polyline で）。31日残す
--   airport_daily ：空港ごとの1日のまとめ（便の数・遅れ・欠航・平均の遅れ・運用・風）。ずっと残す
--   track_points  ：航跡の元になる点（airport-traffic が1分に1回残す）。36時間で消す
-- 書くのは daily-archive（service_role）と airport-traffic だけ。読むのは下の関数から。
alter table public.live_positions add column if not exists reg text check (length(reg) <= 10);

create table if not exists public.track_points (
  callsign text not null check (length(callsign) <= 10),
  t        timestamptz not null,
  lat      real not null,
  lon      real not null,
  alt      smallint            -- 百フィート単位
);
create index if not exists track_points_cs_t on public.track_points (callsign, t);
create index if not exists track_points_t on public.track_points (t);

create table if not exists public.flight_history (
  svc_date    date not null,
  flight      text not null check (flight ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$'),
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$'),
  std         timestamptz not null,
  sta         timestamptz not null,
  atd         timestamptz,
  ata         timestamptz,
  atd_src     text check (atd_src in ('odpt', 'adsb')),   -- odpt＝航空会社の運航情報、adsb＝機体の位置からの推定
  ata_src     text check (ata_src in ('odpt', 'adsb')),
  dep_delay   smallint,
  arr_delay   smallint,
  cancelled   boolean not null default false,
  diverted_to text check (diverted_to ~ '^[A-Z]{3}$'),
  aircraft    text check (length(aircraft) <= 20),        -- 時刻表の機種
  type        text check (length(type) <= 8),             -- 機体の位置の情報の機種（ICAO の記号）
  reg         text check (length(reg) <= 10),
  callsign    text check (length(callsign) <= 10),
  also        text[] not null default '{}',               -- 同じ便のほかの便名（共同運航）
  primary key (svc_date, flight, dep)
);
create index if not exists flight_history_reg on public.flight_history (reg, svc_date) where reg is not null;
create index if not exists flight_history_route on public.flight_history (dep, arr, svc_date);

create table if not exists public.flight_tracks (
  svc_date date not null,
  flight   text not null,
  dep      text not null,
  pts      text not null check (length(pts) <= 20000),    -- polyline（小数4桁）
  alts     smallint[] not null default '{}',              -- 点ごとの高度（百フィート）
  primary key (svc_date, flight, dep)
);

create table if not exists public.airport_daily (
  day        date not null,
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  flights    integer not null default 0,
  arr        integer not null default 0,
  dep        integer not null default 0,
  late       integer not null default 0,     -- 15分以上の遅れ（航空会社の運航情報か、機体の位置からの推定）
  cancelled  integer not null default 0,
  diverted   integer not null default 0,
  avg_delay  real,                           -- 遅れた便の平均（分）
  modes      jsonb,                          -- 運用ごとの分数（ops_log。運用タブの14空港だけ）
  max_wind   smallint,                       -- 気象通報の最大の風速（ノット）
  primary key (day, iata)
);

create table if not exists public.archive_runs (
  day    date primary key,
  ran_at timestamptz not null default now(),
  result jsonb
);

alter table public.track_points enable row level security;
alter table public.flight_history enable row level security;
alter table public.flight_tracks enable row level security;
alter table public.airport_daily enable row level security;
alter table public.archive_runs enable row level security;
revoke all on public.track_points, public.flight_history, public.flight_tracks, public.airport_daily, public.archive_runs from public, anon, authenticated;

-- 航跡の点を便ごとに集める（見張りで見つけた呼び出し符号と、出発の少し前〜到着の少し後の時間で結ぶ）
create or replace function public.archive_track_points(p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', f.flight, 'dep', f.dep, 'pts', p.pts)), '[]'::jsonb)
  from public.flight_schedule f
  join public.flight_watch w on w.schedule_id = f.id and w.state ? 'cs'
  cross join lateral (
    select jsonb_agg(jsonb_build_array(tp.lat, tp.lon, tp.alt) order by tp.t) as pts
    from public.track_points tp
    where tp.callsign = w.state ->> 'cs'
      and tp.t between coalesce(f.atd, f.std) - interval '25 minutes' and coalesce(f.ata, f.sta) + interval '25 minutes'
  ) p
  where f.svc_date = p_day and p.pts is not null
$$;
revoke all on function public.archive_track_points(date) from public, anon, authenticated;

-- 空港ごとの1日のまとめを作り直す（flight_history と ops_log から）
create or replace function public.archive_airport_daily(p_day date) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  delete from public.airport_daily where day = p_day;
  with u as (
    select arr as iata, 'arr' as dir, arr_delay as d, cancelled, diverted_to is not null as div from public.flight_history where svc_date = p_day
    union all
    select dep, 'dep', dep_delay, cancelled, false from public.flight_history where svc_date = p_day
  ), o as (
    select iata, jsonb_object_agg(mode, cnt * 5) as modes, max(wmax) as max_wind from (
      select iata, coalesce(obs_mode, est_mode) as mode, count(*) as cnt, max(wspd) as wmax
      from public.ops_log where (at at time zone 'Asia/Tokyo')::date = p_day group by 1, 2) x group by iata
  )
  insert into public.airport_daily (day, iata, flights, arr, dep, late, cancelled, diverted, avg_delay, modes, max_wind)
  select p_day, u.iata, count(*), count(*) filter (where dir = 'arr'), count(*) filter (where dir = 'dep'),
         count(*) filter (where not cancelled and d >= 15), count(*) filter (where cancelled), count(*) filter (where div),
         round(avg(d) filter (where not cancelled and d >= 15), 1), o.modes, o.max_wind
  from u left join o on o.iata = u.iata
  group by u.iata, o.modes, o.max_wind;
  get diagnostics n = row_count;
  return n;
end
$$;
revoke all on function public.archive_airport_daily(date) from public, anon, authenticated;

-- 機体のつながり（運用の予想に使う）：同じ登録記号の機体が、その日に続けて飛んだ2つの便（前の便の到着空港＝次の便の出発空港）。60日残す
create table if not exists public.rotation_obs (
  svc_date    date not null,
  reg         text not null check (length(reg) <= 10),
  prev_flight text not null,
  next_flight text not null,
  iata        text not null check (iata ~ '^[A-Z]{3}$'),
  turn_min    smallint,                     -- 前の便の到着から次の便の出発までの分（定刻）
  primary key (svc_date, reg, prev_flight)
);
create index if not exists rotation_obs_prev on public.rotation_obs (prev_flight, svc_date);
alter table public.rotation_obs enable row level security;
revoke all on public.rotation_obs from public, anon, authenticated;

create or replace function public.archive_rotations(p_day date) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  delete from public.rotation_obs where svc_date = p_day;
  insert into public.rotation_obs (svc_date, reg, prev_flight, next_flight, iata, turn_min)
  select p_day, reg, flight, nf, arr, round(extract(epoch from (nstd - sta)) / 60)::smallint
  from (
    select reg, flight, arr, sta, cancelled,
           lead(flight) over w as nf, lead(dep) over w as ndep, lead(std) over w as nstd
    from public.flight_history where svc_date = p_day and reg is not null and not cancelled
    window w as (partition by reg order by std)
  ) x
  where nf is not null and ndep = arr and nstd > sta and nstd - sta < interval '6 hours'
  on conflict do nothing;
  get diagnostics n = row_count;
  return n;
end
$$;
revoke all on function public.archive_rotations(date) from public, anon, authenticated;

-- 運用の予想（推定）：機体（登録記号）の今日の最後に分かった便から、よく続く便を4つまでたどる。
-- 「よく続く」は前の60日の記録で、同じ曜日を2倍に数える。今日の時刻表にない便・時刻が合わない便は出さない
create or replace function public.predict_rotation(p_reg text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  cur record; nxt record; steps jsonb := '[]'::jsonb; i int := 0; last_sta timestamptz; last_arr text;
begin
  if p_reg is null or p_reg !~ '^[A-Z0-9-]{2,10}$' then return null; end if;
  -- 今日、その機体を見つけた便のうち、いちばん新しいもの
  select f.flight, f.dep, f.arr, f.std, f.sta, w.state ->> 'phase' as phase into cur
  from public.flight_schedule f join public.flight_watch w on w.schedule_id = f.id
  where f.svc_date = today and w.state ->> 'reg' = p_reg
  order by f.std desc limit 1;
  if cur is null then return jsonb_build_object('reg', p_reg, 'known', null, 'next', '[]'::jsonb); end if;
  last_sta := cur.sta; last_arr := cur.arr;
  declare prevf text := cur.flight;
  begin
    while i < 4 loop
      select o.next_flight, s.dep, s.arr, s.std, s.sta, s.aircraft,
             sum(case when extract(dow from o.svc_date) = extract(dow from today) then 2 else 1 end) as score,
             (select sum(case when extract(dow from o2.svc_date) = extract(dow from today) then 2 else 1 end) from public.rotation_obs o2
               where o2.prev_flight = prevf and o2.svc_date >= today - 60) as total
        into nxt
      from public.rotation_obs o
      join public.flight_schedule s on s.flight = o.next_flight and s.svc_date = today and s.dep = last_arr
      where o.prev_flight = prevf and o.svc_date >= today - 60 and s.std > last_sta + interval '20 minutes'
      group by o.next_flight, s.dep, s.arr, s.std, s.sta, s.aircraft
      order by score desc, s.std limit 1;
      exit when nxt is null;
      steps := steps || jsonb_build_object('flight', nxt.next_flight, 'dep', nxt.dep, 'arr', nxt.arr, 'std', nxt.std, 'sta', nxt.sta,
        'aircraft', nxt.aircraft, 'seen', nxt.score, 'of', nxt.total, 'share', round(nxt.score::numeric / greatest(nxt.total, 1), 2));
      prevf := nxt.next_flight; last_sta := nxt.sta; last_arr := nxt.arr; i := i + 1;
    end loop;
  end;
  return jsonb_build_object('reg', p_reg,
    'known', jsonb_build_object('flight', cur.flight, 'dep', cur.dep, 'arr', cur.arr, 'std', cur.std, 'sta', cur.sta, 'phase', cur.phase),
    'next', steps);
end
$$;
revoke all on function public.predict_rotation(text) from public;
grant execute on function public.predict_rotation(text) to anon, authenticated;

-- 毎晩：前の日の記録を作る（日本時間 4:50。時刻表は14日残しているので、遅れて届いた実際の時刻も2日前まで取り直す）。古いものを消す
do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、毎日の記録の定期実行は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('daily-archive', '50 19 * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/daily-archive',
        headers := '{"User-Agent": "soramemo (daily-archive)"}'::jsonb,
        timeout_milliseconds := 120000)
    $job$)
  $q$;
  execute $q$
    select cron.schedule('archive-cleanup', '*/30 * * * *', $job$
      delete from public.track_points where t < now() - interval '36 hours';
    $job$)
  $q$;
  execute $q$
    select cron.schedule('archive-cleanup-daily', '40 20 * * *', $job$
      delete from public.flight_tracks where svc_date < (now() at time zone 'Asia/Tokyo')::date - 31;
      delete from public.flight_history where svc_date < (now() at time zone 'Asia/Tokyo')::date - 400;
      delete from public.archive_runs where day < (now() at time zone 'Asia/Tokyo')::date - 400;
      delete from public.rotation_obs where svc_date < (now() at time zone 'Asia/Tokyo')::date - 60;
    $job$)
  $q$;
end
$outer$;
