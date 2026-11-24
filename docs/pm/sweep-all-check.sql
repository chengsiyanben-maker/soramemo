-- 見直し B の回のデータの分（移行 196）の確かめ。本人が SQL Editor で流す読むだけの SQL（書き換えなし・一時ファイルを使わない形）
-- 反映の前に 1、反映のあとに 2〜4、次の日に 4 をもう一度

-- 1.（反映の前・あと）airport_board がいま読む便の数：前は「8日6時間前から」、移行196 からは「今日0時の20時間前から」
select p.iata,
  (select count(*) from public.flight_schedule f where (f.arr = p.iata or f.dep = p.iata)
     and f.std > now() - interval '8 days 6 hours' and f.std < now() + interval '6 hours') as rows_before,
  (select count(*) from public.flight_schedule f where (f.arr = p.iata or f.dep = p.iata)
     and f.std > (((now() at time zone 'Asia/Tokyo')::date)::timestamp at time zone 'Asia/Tokyo') - interval '20 hours' and f.std < now() + interval '6 hours') as rows_after
from (values ('HND'), ('ITM'), ('CTS'), ('FUK')) p(iata);

-- 2.（反映のあと）羽田の「これから着く便・出る便」：先の便（t が今より後）が12便まで出ているか
with b as (select public.airport_board('HND') as j)
select (select count(*) from b, jsonb_array_elements(b.j -> 'next_arr') x where (x ->> 't')::timestamptz >= now()) as arr_future,
       (select count(*) from b, jsonb_array_elements(b.j -> 'next_arr') x where (x ->> 't')::timestamptz < now()) as arr_past,
       (select count(*) from b, jsonb_array_elements(b.j -> 'next_dep') x where (x ->> 'takeoff')::timestamptz >= now()) as dep_future,
       (select count(*) from b, jsonb_array_elements(b.j -> 'next_dep') x where (x ->> 'takeoff')::timestamptz < now()) as dep_past;

-- 3.（反映のあと）まとめの表の大きさと、まとめた日
select 'airport_hour_bad' as t, count(*) as n_rows, min(day)::text as first_day, max(day)::text as last_day, pg_size_pretty(pg_total_relation_size('public.airport_hour_bad')) as size from public.airport_hour_bad
union all select 'rwy_learned_days', count(*), min(day)::text, max(day)::text, pg_size_pretty(pg_total_relation_size('public.rwy_learned_days')) from public.rwy_learned_days
union all select 'user_pins', count(*), null, null, pg_size_pretty(pg_total_relation_size('public.user_pins')) from public.user_pins;

-- 4.（反映のあと・次の日）毎時の仕事（board-bad-roll・rwy-learned-roll）の結果と時間
select j.jobname, d.status, count(*) as runs, round(avg(extract(epoch from d.end_time - d.start_time))::numeric, 2) as avg_sec,
       round(max(extract(epoch from d.end_time - d.start_time))::numeric, 2) as max_sec, max(d.start_time) as last_run
from cron.job j join cron.job_run_details d on d.jobid = j.jobid
where j.jobname in ('board-bad-roll', 'rwy-learned-roll') and d.start_time > now() - interval '2 days'
group by 1, 2 order by 1, 2;
