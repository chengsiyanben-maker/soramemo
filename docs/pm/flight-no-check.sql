-- 記録帳の便名と flight_lookup（移行 202）の確かめ（読むだけ。一瞬で終わる）
-- 反映のあとに1回流して、結果をデータ担当の回に貼ってください。
set local statement_timeout = '20s';

-- ① 列と決まりができたか・本人が直せる列
select column_name as 列, data_type as 型 from information_schema.columns where table_schema = 'public' and table_name = 'manual_flights' and column_name = 'flight_no';
select string_agg(column_name, '・' order by column_name) as 本人が直せる列
  from information_schema.column_privileges where table_schema = 'public' and table_name = 'manual_flights' and grantee = 'authenticated' and privilege_type = 'UPDATE';

-- ② flight_lookup をだれが呼べるか（anon・authenticated が t）
select r as 役割, has_function_privilege(r, 'public.flight_lookup(date, text)', 'execute') as 呼べる from unnest(array['anon', 'authenticated']) r;

-- ③ 前の日の1便で試す（その日の flight_history のいちばん早い便。その日の行だけを主キーで読む）
select public.flight_lookup(d, (select flight from public.flight_history where svc_date = d order by std limit 1)) as 試し
  from (select (now() at time zone 'Asia/Tokyo')::date - 1 as d) x;

-- ④ 今日の分（時刻表から返るはず。src = schedule）
select public.flight_lookup(d, (select flight from public.flight_schedule where svc_date = d order by std limit 1)) as 今日の試し
  from (select (now() at time zone 'Asia/Tokyo')::date as d) x;
