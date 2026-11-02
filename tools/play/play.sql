-- そらメモ 試遊版（ブラウザの中のデータベース）だけで使う：見本の利用者と、本物そっくりの便の記録・1日進める仕組み
--   本番のデータベースには入れない（tools/build_play.mjs が、マイグレーションを流したあとの試遊用のデータベースにだけ流す）
--   便の記録は作り物（登録記号・便名・便数は本物に似せた見本。本物の運航の記録ではない）

create schema if not exists play;

-- 見本の路線（片道の1日の便数・航空会社ごとの機種）
create table play.routes (a text, b text, n int, jl text[], nh text[], km_base int);
insert into play.routes values
  ('HND','CTS',24,'{A359,B763,B738}','{B772,B789,B763}',500),
  ('HND','FUK',24,'{A359,B763,B738}','{B772,B789,B763}',300),
  ('HND','OKA',14,'{B763,B738}','{B772,B789}',900),
  ('HND','ITM',14,'{B763,A359}','{B772,B789}',100),
  ('HND','HIJ',8,'{B738,B763}','{B789,B763}',250),
  ('HND','KOJ',8,'{B738,B763}','{B763,A321}',640),
  ('HND','KMQ',5,'{B738}','{A321}',180),
  ('HND','HKD',4,'{B738}','{A321}',580),
  ('HND','NGS',6,'{B763,B738}','{B763}',660),
  ('HND','OIT',5,'{B738}','{A321}',790);

-- 登録記号の見本（航空会社・機種ごと）
create table play.regs (al text, icao text, reg text);
insert into play.regs
  select 'JL', 'A359', 'JA' || lpad(i::text, 2, '0') || 'XJ' from generate_series(1, 16) i union all
  select 'JL', 'B763', 'JA' || (600 + i) || 'J' from generate_series(1, 18) i union all
  select 'JL', 'B738', 'JA' || (300 + i) || 'J' from generate_series(1, 40) i union all
  select 'NH', 'B772', 'JA' || (740 + i) || 'A' from generate_series(1, 14) i union all
  select 'NH', 'B789', 'JA' || (830 + i) || 'A' from generate_series(1, 30) i union all
  select 'NH', 'B763', 'JA' || (601 + i) || 'A' from generate_series(1, 15) i union all
  select 'NH', 'A321', 'JA' || (130 + i) || 'A' from generate_series(1, 28) i;

-- 1日ぶんの便の記録を作る（その日の本物そっくりの便。欠航は1%くらい、ときどき天気の悪い日）
create or replace function play.make_day(p_day date) returns int
language plpgsql as $$
declare r record; d int; i int; v_al text; v_ty text; v_fno text; v_dep text; v_arr text; t0 timestamptz; dur interval; n int := 0; bad boolean;
begin
  for r in select * from play.routes loop
    bad := random() < 0.04;   -- ときどき、その路線の天気が悪い日
    for d in 0..1 loop
      v_dep := case d when 0 then r.a else r.b end; v_arr := case d when 0 then r.b else r.a end;
      dur := make_interval(mins => 70 + (r.km_base / 8));
      for i in 0..r.n - 1 loop
        v_al := case when i % 2 = 0 then 'JL' else 'NH' end;
        v_ty := case when v_al = 'JL' then r.jl[1 + (i / 2) % array_length(r.jl, 1)] else r.nh[1 + (i / 2) % array_length(r.nh, 1)] end;
        v_fno := v_al || (r.km_base + i * 2 + d)::text;
        t0 := (p_day::timestamp + make_interval(mins => 390 + (i * (840 / greatest(r.n, 1))) + d * 25)) at time zone 'Asia/Tokyo';
        insert into flight_history (svc_date, flight, dep, arr, std, sta, atd, ata, dep_delay, arr_delay, cancelled, aircraft, type, reg)
        select p_day, v_fno, v_dep, v_arr, t0, t0 + dur,
               case when c then null else t0 + make_interval(mins => dl) end, case when c then null else t0 + dur + make_interval(mins => dl) end,
               case when c then null else dl end, case when c then null else dl end, c, v_ty, v_ty,
               (select g.reg from play.regs g where g.al = v_al and g.icao = v_ty order by md5(g.reg || p_day::text || v_fno) limit 1)
          from (select (random() < case when bad then 0.25 else 0.01 end) as c, (case when random() < 0.2 then (random() * 40)::int else (random() * 8)::int end) as dl) x
        on conflict do nothing;
        n := n + 1;
      end loop;
    end loop;
  end loop;
  return n;
end;
$$;

-- 見本の利用者と、1年ぶんのフライト（羽田から各地へ。便名が分かり、乗った機体が記録にある）
create or replace function play.seed(p_uid uuid) returns void
language plpgsql as $$
declare r record; k int := 0; d date; today date := (now() at time zone 'Asia/Tokyo')::date; h record; ida int; idb int; c1 bigint; c2 bigint; v_dep text; v_arr text;
begin
  insert into auth.users (id, email) values (p_uid, 'play@example.com') on conflict do nothing;
  -- 前の29日と今日の、本物そっくりの便
  for d in select generate_series(today - 29, today, interval '1 day')::date loop perform play.make_day(d); end loop;
  -- 1年ぶんの自分のフライト：路線ごとに往復を数回
  for r in select * from play.routes, generate_series(1, case when n >= 14 then 3 when n >= 6 then 2 else 1 end) rep order by n desc, rep loop
    k := k + 1;
    for v_dep, v_arr in select x, y from (values (r.a, r.b, 0), (r.b, r.a, 1)) v(x, y, o) order by o loop
      d := today - 360 + k * 11 + case when v_dep = r.a then 0 else 2 end;
      if d > today - 31 then d := today - 31 - k; end if;
      -- その日の便の記録（自分の便と、前後の便）
      if not exists (select 1 from flight_history x where x.svc_date = d) then perform play.make_day(d); end if;
      select * into h from flight_history x where x.svc_date = d and x.dep = v_dep and x.arr = v_arr and not x.cancelled order by x.std offset (k % 4) limit 1;
      if not found then continue; end if;
      select id into ida from airports where iata = v_dep; select id into idb from airports where iata = v_arr;
      insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at)
        select p_uid, a.id, a.lat, a.lon, 12, h.std - interval '50 minutes', h.std - interval '50 minutes' from airports a where a.id = ida returning id into c1;
      insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at)
        select p_uid, a.id, a.lat, a.lon, 12, h.sta + interval '10 minutes', h.sta + interval '10 minutes' from airports a where a.id = idb returning id into c2;
      insert into flights (user_id, from_airport, to_airport, dep_checkin, arr_checkin, dep_at, arr_at, distance_km, status, flight_no, airline)
        select p_uid, ida, idb, c1, c2, h.std, h.sta, greatest(1, round((6371 * acos(least(1, sin(radians(a.lat)) * sin(radians(b.lat)) + cos(radians(a.lat)) * cos(radians(b.lat)) * cos(radians(b.lon - a.lon)))))::numeric, 1)),
               'verified', substr(h.flight, 3), substr(h.flight, 1, 2)
          from airports a, airports b where a.id = ida and b.id = idb;
    end loop;
  end loop;
end;
$$;

-- 1日進める：その日の終わりの記録 → すべての日時を1日前へずらす（＝時間が1日進む） → 新しい日の便 → 毎日の処理（本番の毎日の処理と同じ順）
create table play.state (k text primary key, v text);
create table play.job_errors (at timestamptz default now(), job text, err text);   -- 毎日の処理で止まったもの（調べるとき用）
insert into play.state values ('day', '0');

create or replace function play.shift_all(p_days int) returns void
language plpgsql as $$
declare t record; sets text;
begin
  set local session_replication_role = replica;   -- 書き換えの決まり（記録を消さない・変えない）と、表どうしのつながりの確かめを、ずらす間だけ止める
  for t in
    select c.table_schema s, c.table_name n, string_agg(format('%I = %I - %L::interval', c.column_name, c.column_name, '%s'), ', ') cols
      from information_schema.columns c
      join information_schema.tables x on x.table_schema = c.table_schema and x.table_name = c.table_name and x.table_type = 'BASE TABLE'
     where c.table_schema in ('public', 'ops', 'auth')
       and c.data_type in ('date', 'timestamp with time zone', 'timestamp without time zone')
       and (c.table_schema, c.table_name) not in (('ops', 'flags'), ('public', 'game_events'))
     group by 1, 2
  loop
    -- 主キーに日付がある表があるので、いったん遠くへずらしてから戻す（途中で重ならないように）
    execute format('update %I.%I set ' || replace(t.cols, '''%s''', quote_literal((p_days + 2000) || ' days')), t.s, t.n);
    execute format('update %I.%I set ' || replace(replace(t.cols, ' - ', ' + '), '''%s''', quote_literal('2000 days')), t.s, t.n);
  end loop;
  perform set_config('session_replication_role', 'origin', true);
end;
$$;

create or replace function play.run_daily() returns void
language plpgsql as $$
declare j text;
begin
  foreach j in array array[
    'select public.co3_checks_run()', 'select public.co3_heavy_run()', 'select public.co3_satisfaction_refresh()', 'select public.co3_slots_decide()',
    'select public.co3_breakdown_draw()', 'select public.co3_events_draw()', 'select public.co3_orders_deliver()', 'select public.co3_cs_daily()', 'select public.co3_ally_daily()',
    'select public.co_size_refresh()', 'select public.co_sky_refresh()', 'select public.co3_route_real_refresh()', 'select public.co_rank_refresh()',
    'select public.co3_season_close() where extract(day from (now() at time zone ''Asia/Tokyo'')) = 1 and extract(month from (now() at time zone ''Asia/Tokyo'')) in (1, 4, 7, 10)',
    'select public.co3_month_close() where extract(day from (now() at time zone ''Asia/Tokyo'')) = 1',
    'select public.co3_trouble_detect()', 'select public.co3_trouble_expire()', 'select public.co3_legs_check()']
  loop
    begin execute j; exception when others then raise notice '% : %', j, sqlerrm; insert into play.job_errors (job, err) values (j, sqlerrm); end;
  end loop;
end;
$$;

create or replace function play.advance(p_days int default 1) returns jsonb
language plpgsql as $$
declare i int; today date;
begin
  for i in 1..greatest(1, least(p_days, 31)) loop
    begin perform public.co3_daily_record(); exception when others then raise notice 'daily_record: %', sqlerrm; insert into play.job_errors (job, err) values ('co3_daily_record', sqlerrm); end;
    perform play.shift_all(1);
    today := (now() at time zone 'Asia/Tokyo')::date;
    perform play.make_day(today);
    delete from flight_history where svc_date < today - 60 and not exists (select 1 from flights f where (f.dep_at at time zone 'Asia/Tokyo')::date = flight_history.svc_date);
    perform play.run_daily();
    update play.state set v = (v::int + 1)::text where k = 'day';
  end loop;
  return jsonb_build_object('day', (select v::int from play.state where k = 'day'));
end;
$$;

-- 開いた日に合わせる：作ったとき（または前に開いたとき）から日がたっていれば、その日数ぶんの便の記録を足して毎日の処理を流す
--   （時間は本物の時計で進む。何日も開かなかったときは、そのあいだの稼ぎも本番と同じように貯まる）
create or replace function play.catch_up() returns int
language plpgsql as $$
declare last date; today date := (now() at time zone 'Asia/Tokyo')::date; d date; n int := 0;
begin
  select max(svc_date) into last from flight_history;
  if last is null or last >= today then return 0; end if;
  for d in select generate_series(last + 1, today, interval '1 day')::date loop
    perform play.make_day(d); n := n + 1;
  end loop;
  perform play.run_daily();
  return n;
end;
$$;
