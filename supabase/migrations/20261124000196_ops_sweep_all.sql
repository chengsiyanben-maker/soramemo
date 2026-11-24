-- アプリ全体の見直し B の回（kaizen/sweep-all-b・report-sweep-all-b.md）のデータの分。PM の指示 11/24 14時30分
--   1. airport_board の next_arr・next_dep：「20分前から6便」をやめ、「今より先の便を12便まで」＋「過ぎた便（20分前まで）を2便まで」に分けて取る
--      （羽田の昼は6つの枠が過ぎた20分の便で埋まり、先の便が0〜1便になっていた）。1便の形・キー・名前・引数・権限は同じ
--   2. airport_board を軽くする：
--      ・hours の ref（前の7日の同じ時間の遅れ・欠航の平均）を、毎時まとめる表 airport_hour_bad から読む（前は毎回8日分の便を全部読んでいた）
--      ・便を読む幅を「8日6時間前から」→「今日（日本時間）の0時の20時間前から」に（今日の数・これからの便・飛んでいる長い国際線が入る幅）
--      ・まとめがまだない日（作った直後・毎時の仕事が止まった日）は、その日だけ前と同じく便の表から数える（答えは前と同じ）
--      hours・bad の値は前と同じ（テスト t134 で前の関数と比べる）
--   3. rwy_learned（撮る人の学んだ滑走路）：毎時まとめる表 rwy_learned_days から読み、今日の分だけ rwy_samples から数える
--      ・前は30日分の記録（羽田は約4万行・1行に途中の点）を毎回全部読んで 3〜4秒かかり、500 になっていた
--      ・幅は「今から p_days 日前まで」→「今日を入れて p_days 日（日本時間の暦の日）」。数は前とほぼ同じ（端の半日ぶんだけ違う）
--      ・まとめがまだない日は、その日だけ rwy_samples から数える
--   4. 知らせのピン止めをアカウントに残す表 user_pins（本人の行だけ読める・書ける）と、読む・書く関数 my_pins()・my_pins_put()
--   影響：チェックイン（運用タブの案内板・短冊・撮る人・遅れ、知らせのピン止め）。経営は関係しない
--   航路と機体の記録は消さない（まとめの表を足すだけ。rwy_samples・flight_schedule は変えない）
set lock_timeout = '5s';

-- ───────── 2. 前の日の時間ごとの遅れ・欠航のまとめ ─────────
-- 1行＝空港・日（日本時間）・時（0〜23）。bad は定刻から15分以上の遅れと欠航の便の数（airport_board の hours の late＋cancel と同じ数え方）。0 の時は行を作らない
create table if not exists public.airport_hour_bad (
  iata text not null check (iata ~ '^[A-Z0-9]{3}$'),
  day  date not null,
  h    smallint not null check (h between 0 and 23),
  bad  integer not null check (bad > 0),
  primary key (iata, day, h)
);
-- まとめ終わった日（この表にない日は、airport_board が便の表から数える）
create table if not exists public.airport_hour_bad_done (
  day     date primary key,
  made_at timestamptz not null default now()
);
alter table public.airport_hour_bad enable row level security;
alter table public.airport_hour_bad_done enable row level security;
revoke all on public.airport_hour_bad, public.airport_hour_bad_done from public, anon, authenticated;

-- 日本時間の p_from〜p_to の日をまとめ直す（今日より前の日だけ）。返すのは書いた行の数
create or replace function public.airport_hour_bad_roll(p_from date, p_to date) returns integer
language plpgsql security definer set search_path = public as $$
declare
  d0 date := p_from;
  d1 date := least(p_to, (now() at time zone 'Asia/Tokyo')::date - 1);
  v_rows int;
begin
  if d0 is null or d1 is null or d0 > d1 then return 0; end if;
  delete from public.airport_hour_bad where day between d0 and d1;
  insert into public.airport_hour_bad (iata, day, h, bad)
  select iata, (t_sched at time zone 'Asia/Tokyo')::date, extract(hour from t_sched at time zone 'Asia/Tokyo')::int, count(*)::int
  from (
    select f.arr as iata, f.sta as t_sched, coalesce(f.ata, f.eta) as t_off, coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled
    from public.flight_schedule f
    where f.std >= (d0::timestamp at time zone 'Asia/Tokyo') - interval '1 day' and f.std < ((d1 + 1)::timestamp at time zone 'Asia/Tokyo') + interval '6 hours'
    union all
    select f.dep, f.std, coalesce(f.atd, f.etd), coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false)
    from public.flight_schedule f
    where f.std >= (d0::timestamp at time zone 'Asia/Tokyo') and f.std < ((d1 + 1)::timestamp at time zone 'Asia/Tokyo')
  ) x
  where x.t_sched is not null and (x.t_sched at time zone 'Asia/Tokyo')::date between d0 and d1
    and (x.cancelled or (x.t_off is not null and x.t_off - x.t_sched >= interval '15 minutes'))
  group by 1, 2, 3;
  get diagnostics v_rows = row_count;
  insert into public.airport_hour_bad_done (day, made_at) select g::date, now() from generate_series(d0, d1, interval '1 day') g
  on conflict (day) do update set made_at = excluded.made_at;
  return v_rows;
end $$;
revoke all on function public.airport_hour_bad_roll(date, date) from public, anon, authenticated;

-- ───────── 1・2. airport_board ─────────
create or replace function public.airport_board(p_iata text, p_kind text default 'all') returns jsonb
language sql stable security definer set search_path = public as $$
  with today as (select (now() at time zone 'Asia/Tokyo')::date as day, ((now() at time zone 'Asia/Tokyo')::date::timestamp at time zone 'Asia/Tokyo') as t0),
  s as (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.etd, f.eta, f.atd, f.ata, f.aircraft, f.dep_status, f.arr_status,
      case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end as atd_inf,
      case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end as ata_inf,
      case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end as eta_inf,
      coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled,
      not exists (select 1 from public.airports a where a.iata = case when f.dep = p_iata then f.arr else f.dep end) as intl
    from today, public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
    -- 今日の0時の20時間前から：今日着く長い国際線（前の日に出た便）と、いま飛んでいる便（到着の定刻が6時間前より後）が入る幅
    where (f.arr = p_iata or f.dep = p_iata) and f.std > today.t0 - interval '20 hours' and f.std < now() + interval '6 hours'
  ), tx as (select public.taxi_out_min(p_iata) as m),
  dp as (
    -- 離陸の時刻：機体の位置で見つけた離陸、なければ出発（実際・見込み・定刻）＋地上走行
    select s.*, coalesce(atd_inf, coalesce(atd, etd, std) + make_interval(secs => tx.m * 60)) as tko, atd_inf is not null as tko_actual, tx.m as taxi
    from s, tx where dep = p_iata
  ), ar as (
    select s.*, coalesce(ata, ata_inf, eta, eta_inf, sta) as t from s where arr = p_iata
  ), u as (
    -- この空港から見た1便（到着なら到着の時刻、出発なら出発の時刻）
    select flight, case when arr = p_iata then 'arr' else 'dep' end as dir, case when arr = p_iata then dep else arr end as other,
           case when arr = p_iata then eta else etd end as t_est, case when arr = p_iata then ata else atd end as t_act, intl, aircraft,
           case when arr = p_iata then sta else std end as t_sched,
           case when arr = p_iata then coalesce(ata, eta) else coalesce(atd, etd) end as t_off,
           cancelled
    from s
  ), d as (
    select (t_sched at time zone 'Asia/Tokyo')::date as day, extract(hour from t_sched at time zone 'Asia/Tokyo')::int as h,
           not cancelled and t_off is not null and t_off - t_sched >= interval '15 minutes' as late, cancelled, flight, dir, other, t_sched, t_est, t_act, intl, aircraft
    from u
  ),
  -- 前の7日のうち、まとめ（airport_hour_bad）がまだない日
  miss as (
    select g::date as day from today, generate_series(today.day - 7, today.day - 1, interval '1 day') g
    where not exists (select 1 from public.airport_hour_bad_done x where x.day = g::date)
  ),
  -- まとめがない日だけ、前と同じく便の表から数える（ない日がなければ読まない）
  miss_rows as (
    select extract(hour from t_sched at time zone 'Asia/Tokyo')::int as h, count(*)::int as bad
    from (
      select case when f.arr = p_iata then f.sta else f.std end as t_sched,
             case when f.arr = p_iata then coalesce(f.ata, f.eta) else coalesce(f.atd, f.etd) end as t_off,
             coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled
      from today, public.flight_schedule f
      where exists (select 1 from miss) and (f.arr = p_iata or f.dep = p_iata)
        and f.std > now() - interval '8 days 6 hours' and f.std < today.t0 + interval '6 hours'
    ) z
    where (t_sched at time zone 'Asia/Tokyo')::date in (select day from miss)
      and (cancelled or (t_off is not null and t_off - t_sched >= interval '15 minutes'))
    group by 1
  ),
  ref7 as (
    select h, sum(bad)::int as bad7 from (
      select b.h::int as h, b.bad from public.airport_hour_bad b, today
      where b.iata = p_iata and b.day between today.day - 7 and today.day - 1 and b.day not in (select day from miss)
      union all select h, bad from miss_rows
    ) r group by h
  )
  select jsonb_build_object(
    'iata', p_iata, 'now', now(),
    -- 今日（日本時間）の15分以上の遅れと欠航の便（移行 195）。'hours' の late・cancel と同じ数え方なので、合計は hours と合う
    'bad', coalesce((select jsonb_agg(jsonb_build_object('dir', d.dir, 'flight', d.flight, 'other', d.other, 'sched', d.t_sched, 'est', d.t_est, 'actual', d.t_act,
               'late', case when d.cancelled then null else round(extract(epoch from (coalesce(d.t_act, d.t_est) - d.t_sched)) / 60) end,
               'cancelled', d.cancelled, 'intl', d.intl, 'aircraft', d.aircraft) order by d.t_sched)
      from d, today where d.day = today.day and (d.late or d.cancelled)), '[]'::jsonb),
    -- これから着く便：今より先の便を3時間先まで12便＋過ぎた便を20分前まで2便（11/24 見直し B の1番）
    'next_arr', coalesce((select jsonb_agg(x order by x ->> 't') from (
      (select jsonb_build_object('flight', flight, 'other', dep, 'sched', sta, 'est', eta, 'actual', ata, 'inferred', ata_inf, 'predicted', eta_inf,
               'aircraft', aircraft, 'intl', intl, 't', t) as x
       from ar where not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
         and t >= now() and t <= now() + interval '3 hours' and sta > now() - interval '6 hours'
       order by t limit 12)
      union all
      (select jsonb_build_object('flight', flight, 'other', dep, 'sched', sta, 'est', eta, 'actual', ata, 'inferred', ata_inf, 'predicted', eta_inf,
               'aircraft', aircraft, 'intl', intl, 't', t) as x
       from ar where not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
         and t >= now() - interval '20 minutes' and t < now() and sta > now() - interval '6 hours'
       order by t desc limit 2)) q), '[]'::jsonb),
    'next_dep', coalesce((select jsonb_agg(x order by x ->> 'takeoff') from (
      (select jsonb_build_object('flight', flight, 'other', arr, 'sched', std, 'est', etd, 'actual', atd, 'inferred', atd_inf,
               'aircraft', aircraft, 'intl', intl, 't', coalesce(atd, atd_inf, etd, std),
               'takeoff', tko, 'takeoff_src', case when tko_actual then 'actual' else 'calc' end, 'taxi', round(taxi::numeric)) as x
       from dp where not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
         and tko >= now() and tko <= now() + interval '3 hours' and std > now() - interval '6 hours'
       order by tko limit 12)
      union all
      (select jsonb_build_object('flight', flight, 'other', arr, 'sched', std, 'est', etd, 'actual', atd, 'inferred', atd_inf,
               'aircraft', aircraft, 'intl', intl, 't', coalesce(atd, atd_inf, etd, std),
               'takeoff', tko, 'takeoff_src', case when tko_actual then 'actual' else 'calc' end, 'taxi', round(taxi::numeric)) as x
       from dp where not cancelled and (p_kind = 'all' or (p_kind = 'intl') = intl)
         and tko >= now() - interval '20 minutes' and tko < now() and std > now() - interval '6 hours'
       order by tko desc limit 2)) q), '[]'::jsonb),
    -- 1時間ごとの数。ref（前の7日の平均）はまとめの表から（まとめがない日だけ便の表から）
    'hours', (select jsonb_agg(jsonb_build_object('h', g.h, 'flights', coalesce(c.flights, 0), 'late', coalesce(c.late, 0), 'cancel', coalesce(c.cancel, 0),
        'ref', round(coalesce(r.bad7, 0) / 7.0, 1)) order by g.h)
      from generate_series(0, 23) as g(h)
      left join (select d.h,
          count(*) filter (where d.day = today.day) as flights,
          count(*) filter (where d.day = today.day and d.late) as late,
          count(*) filter (where d.day = today.day and d.cancelled) as cancel
        from d, today group by d.h) c on c.h = g.h
      left join ref7 r on r.h = g.h)
  )
$$;
revoke all on function public.airport_board(text, text) from public;
grant execute on function public.airport_board(text, text) to anon, authenticated;

-- ───────── 3. 学んだ滑走路のまとめ ─────────
-- 1行＝空港・日（日本時間）・着陸か離陸・滑走路・方角の8つの区分（sec。方角が分からないときは -1）。羽田・成田は30秒ごとの見張り（src='live'）だけ数える（前と同じ）
create table if not exists public.rwy_learned_days (
  iata text not null check (iata ~ '^[A-Z]{3}$'),
  day  date not null,
  dir  text not null check (dir in ('arr', 'dep')),
  rwy  text not null check (rwy ~ '^[0-9]{2}[LRC]?$'),
  sec  smallint not null check (sec between -1 and 7),
  n    integer not null check (n > 0),
  primary key (iata, day, dir, rwy, sec)
);
create table if not exists public.rwy_learned_done (
  day     date primary key,
  made_at timestamptz not null default now()
);
alter table public.rwy_learned_days enable row level security;
alter table public.rwy_learned_done enable row level security;
revoke all on public.rwy_learned_days, public.rwy_learned_done from public, anon, authenticated;

-- 日本時間の p_from〜p_to の日をまとめ直す（今日より前の日だけ）。記録がファイル置き場に移った日（rwy_samples に1行もない日）は、前のまとめを残す
create or replace function public.rwy_learned_roll(p_from date, p_to date) returns integer
language plpgsql security definer set search_path = public as $$
declare
  d0 date := p_from;
  d1 date := least(p_to, (now() at time zone 'Asia/Tokyo')::date - 1);
  v_rows int;
begin
  if d0 is null or d1 is null or d0 > d1 then return 0; end if;
  create temp table if not exists rwy_roll_tmp (iata text, day date, dir text, rwy text, sec smallint, n int) on commit drop;
  truncate rwy_roll_tmp;
  insert into rwy_roll_tmp
  select iata, day, dir, rwy, case when b is null then -1 else (((b + 22) % 360) / 45)::int end, count(*)::int
  from (select iata, (at at time zone 'Asia/Tokyo')::date as day, dir, rwy,
               case when dir = 'arr' then coalesce(ent60, ent30, ent120, first_brg) else coalesce(ex60, ex30) end as b
        from public.rwy_samples
        where at >= (d0::timestamp at time zone 'Asia/Tokyo') and at < ((d1 + 1)::timestamp at time zone 'Asia/Tokyo')
          and (src = 'live' or iata not in ('HND', 'NRT'))) s
  group by 1, 2, 3, 4, 5;
  -- 記録のある日だけ入れ替える
  delete from public.rwy_learned_days k where k.day between d0 and d1 and k.day in (select distinct day from rwy_roll_tmp);
  insert into public.rwy_learned_days (iata, day, dir, rwy, sec, n) select iata, day, dir, rwy, sec, n from rwy_roll_tmp;
  get diagnostics v_rows = row_count;
  insert into public.rwy_learned_done (day, made_at) select g::date, now() from generate_series(d0, d1, interval '1 day') g
  on conflict (day) do update set made_at = excluded.made_at;
  return v_rows;
end $$;
revoke all on function public.rwy_learned_roll(date, date) from public, anon, authenticated;

-- 学んだ滑走路の数（返す形は前と同じ：{iata, n, rows:[{dir, rwy, sec, n}]}、rows は dir・rwy・sec の順）
create or replace function public.rwy_learned(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  with p as (
    select least(greatest(coalesce(p_days, 30), 1), 3660) as days, (now() at time zone 'Asia/Tokyo')::date as today,
           ((now() at time zone 'Asia/Tokyo')::date::timestamp at time zone 'Asia/Tokyo') as t0
  ), first as (select min(day) as d from public.rwy_learned_done),
  -- まとめがまだない日（まとめを始めた日より前は、記録がないので数えない）
  miss as (
    select g::date as day from p, first, generate_series(greatest(p.today - p.days + 1, coalesce(first.d, p.today)), p.today - 1, interval '1 day') g
    where not exists (select 1 from public.rwy_learned_done x where x.day = g::date)
  ),
  raw as (
    -- 今日の分と、まとめがない日の分は rwy_samples から（前と同じ数え方）。2つに分けて、どちらも (iata, at) の索引の幅で読む
    select dir, rwy, case when b is null then -1 else (((b + 22) % 360) / 45)::int end as sec, count(*)::int as n
    from (select r.dir, r.rwy, case when r.dir = 'arr' then coalesce(r.ent60, r.ent30, r.ent120, r.first_brg) else coalesce(r.ex60, r.ex30) end as b
          from p, public.rwy_samples r
          where r.iata = p_iata and (r.src = 'live' or p_iata not in ('HND', 'NRT')) and r.at >= p.t0
          union all
          select r.dir, r.rwy, case when r.dir = 'arr' then coalesce(r.ent60, r.ent30, r.ent120, r.first_brg) else coalesce(r.ex60, r.ex30) end
          from p, public.rwy_samples r
          where exists (select 1 from miss) and r.iata = p_iata and (r.src = 'live' or p_iata not in ('HND', 'NRT'))
            and r.at >= ((select min(day) from miss)::timestamp at time zone 'Asia/Tokyo') and r.at < p.t0
            and (r.at at time zone 'Asia/Tokyo')::date in (select day from miss)) s
    group by 1, 2, 3
  ), sum_rows as (
    select dir, rwy, sec::int as sec, n from raw
    union all
    select k.dir, k.rwy, k.sec::int, k.n from p, public.rwy_learned_days k
    where k.iata = p_iata and k.day between p.today - p.days + 1 and p.today - 1 and k.day not in (select day from miss)
  ), q as (
    select dir, rwy, case when sec < 0 then null else sec end as sec, sum(n)::bigint as n from sum_rows group by 1, 2, 3
  )
  select jsonb_build_object('iata', p_iata, 'n', coalesce(sum(n), 0), 'rows', coalesce(jsonb_agg(jsonb_build_object('dir', dir, 'rwy', rwy, 'sec', sec, 'n', n) order by dir, rwy, sec), '[]'::jsonb))
  from q
$$;
revoke all on function public.rwy_learned(text, int) from public;
grant execute on function public.rwy_learned(text, int) to anon, authenticated;

-- ───────── 4. 知らせのピン止め（アカウントに残す） ─────────
-- 1人1行。pins はアプリのピン止めの並び（[{k:"HND", sp:true, dl:false, ga:false}, …]。k は3レターか "#番号"）
--   ・上限は20空港（新しく足せるのは12空港まで。前から13〜14空港を申し込んでいた人がそのまま入る幅）・大きさは 4KB まで
--   ・spot は撮影の知らせの空港（1つだけ。なければ null）
--   ・本人だけが読める・作れる・直せる・消せる。rev は直すたびにサーバーが1つ上げる（別の端末の保存とぶつかったかを見る）
--   ・退会（delete-account → auth.users の削除）で一緒に消える（on delete cascade）
create table if not exists public.user_pins (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  pins       jsonb not null default '[]'::jsonb
             check (jsonb_typeof(pins) = 'array' and jsonb_array_length(pins) <= 20 and octet_length(pins::text) <= 4096),
  spot       text check (spot ~ '^[A-Z]{3}$'),
  rev        integer not null default 1,
  updated_at timestamptz not null default now()
);
alter table public.user_pins enable row level security;
revoke all on public.user_pins from public, anon, authenticated;
grant select, delete on public.user_pins to authenticated;
grant insert (user_id, pins, spot) on public.user_pins to authenticated;
grant update (pins, spot) on public.user_pins to authenticated;
drop policy if exists user_pins_own_read on public.user_pins;
create policy user_pins_own_read on public.user_pins for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists user_pins_own_insert on public.user_pins;
create policy user_pins_own_insert on public.user_pins for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists user_pins_own_update on public.user_pins;
create policy user_pins_own_update on public.user_pins for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
drop policy if exists user_pins_own_delete on public.user_pins;
create policy user_pins_own_delete on public.user_pins for delete to authenticated using (user_id = (select auth.uid()));

-- 1つのピン止めの形：{k: 3レターか "#数字"、sp・dl・ga は true／false（なくてもよい）}。ほかの鍵は入れない。同じ k は2回入れない
create or replace function public.user_pins_ok(p jsonb) returns boolean
language plpgsql immutable set search_path = '' as $$
declare e jsonb; kv record; seen text[] := '{}';
begin
  if p is null or jsonb_typeof(p) <> 'array' then return false; end if;
  for e in select x from jsonb_array_elements(p) x loop
    if jsonb_typeof(e) <> 'object' or jsonb_typeof(e -> 'k') is distinct from 'string' then return false; end if;
    if not ((e ->> 'k') ~ '^([A-Z]{3}|#[0-9]{1,6})$') or (e ->> 'k') = any (seen) then return false; end if;
    seen := seen || (e ->> 'k');
    for kv in select * from jsonb_each(e) loop
      if kv.key not in ('k', 'sp', 'dl', 'ga') then return false; end if;
      if kv.key <> 'k' and jsonb_typeof(kv.value) <> 'boolean' then return false; end if;
    end loop;
  end loop;
  return true;
end $$;
revoke all on function public.user_pins_ok(jsonb) from public, anon;
grant execute on function public.user_pins_ok(jsonb) to authenticated;   -- 本人が書くときのトリガーから呼ぶ
create or replace function public.user_pins_touch() returns trigger
language plpgsql set search_path = '' as $$
begin
  if not public.user_pins_ok(new.pins) then raise exception 'bad pins' using errcode = '22023'; end if;
  if tg_op = 'INSERT' then new.rev := 1;
  else new.user_id := old.user_id; new.rev := old.rev + 1; end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists user_pins_touch on public.user_pins;
create trigger user_pins_touch before insert or update on public.user_pins for each row execute function public.user_pins_touch();
revoke all on function public.user_pins_touch() from public, anon, authenticated;

-- 読む：{pins, spot, rev, updated_at}。まだ保存していなければ null。ログインしていなければ null
create or replace function public.my_pins() returns jsonb
language sql stable security invoker set search_path = '' as $$
  select jsonb_build_object('pins', p.pins, 'spot', p.spot, 'rev', p.rev, 'updated_at', p.updated_at)
  from public.user_pins p where p.user_id = (select auth.uid())
$$;
revoke all on function public.my_pins() from public, anon;
grant execute on function public.my_pins() to authenticated;

-- 書く：p_rev に前に読んだ rev を渡すと、別の端末が先に直していたら書かずに {conflict:true, pins, spot, rev} を返す（p_rev が null なら上書き）
--   書けたら {ok:true, rev}。形が違えば 22023（bad pins）
create or replace function public.my_pins_put(p_pins jsonb, p_spot text default null, p_rev integer default null) returns jsonb
language plpgsql security invoker set search_path = '' as $$
declare uid uuid := auth.uid(); cur public.user_pins; r int;
begin
  if uid is null then raise exception 'login required' using errcode = '28000'; end if;
  select * into cur from public.user_pins where user_id = uid for update;
  if not found then
    insert into public.user_pins (user_id, pins, spot) values (uid, coalesce(p_pins, '[]'::jsonb), p_spot) returning rev into r;
    return jsonb_build_object('ok', true, 'rev', r);
  end if;
  if p_rev is not null and p_rev <> cur.rev then
    return jsonb_build_object('conflict', true, 'pins', cur.pins, 'spot', cur.spot, 'rev', cur.rev);
  end if;
  update public.user_pins set pins = coalesce(p_pins, '[]'::jsonb), spot = p_spot where user_id = uid returning rev into r;
  return jsonb_build_object('ok', true, 'rev', r);
end $$;
revoke all on function public.my_pins_put(jsonb, text, integer) from public, anon;
grant execute on function public.my_pins_put(jsonb, text, integer) to authenticated;

-- ───────── まとめの最初の作り（前の8日・記録のある日すべて）と毎時の仕事 ─────────
set statement_timeout = '5min';
select public.airport_hour_bad_roll((now() at time zone 'Asia/Tokyo')::date - 8, (now() at time zone 'Asia/Tokyo')::date - 1);
select public.rwy_learned_roll(coalesce((select (min(at) at time zone 'Asia/Tokyo')::date from public.rwy_samples), (now() at time zone 'Asia/Tokyo')::date - 1),
                               (now() at time zone 'Asia/Tokyo')::date - 1);
reset statement_timeout;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎時：前の日と前の前の日をまとめ直す（遅れて入る実際の時刻・3時間ごとの rwy-learn の記録を拾う）。上限1分
  execute $q$ select cron.schedule('board-bad-roll', '7 * * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; select public.airport_hour_bad_roll((now() at time zone 'Asia/Tokyo')::date - 2, (now() at time zone 'Asia/Tokyo')::date - 1) $job$) $q$;
  execute $q$ select cron.schedule('rwy-learned-roll', '37 * * * *', $job$ set statement_timeout = '1min'; set lock_timeout = '5s'; select public.rwy_learned_roll((now() at time zone 'Asia/Tokyo')::date - 2, (now() at time zone 'Asia/Tokyo')::date - 1) $job$) $q$;
end
$outer$;
reset lock_timeout;
