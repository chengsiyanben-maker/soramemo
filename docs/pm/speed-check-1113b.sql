-- 全体の見回りの直し（11/13 データ担当）：本人が Supabase の SQL Editor に貼って流す「読むだけ」の SQL。表は変えない
-- 1つずつ選んで流し、結果をそのまま貼ってください。どれも 20秒で止まる・一時ファイルを使わない形
-- 移行 165 を反映する「前」と「後」に同じものを流すと、効き目が比べられる
set statement_timeout = '20s';

-- ① 運用を開いたときに呼ばれる関数の、データベースの中の時間（pg_stat_statements。統計を取り始めてから）
--    平均ms が小さい（数十ms 以下）なら、画面で測った 1〜4秒の大部分はデータベースの外（距離・同時に14本の呼び出し・返す量）
select left(regexp_replace(query, '\s+', ' ', 'g'), 120) as 文,
       calls as 回数,
       round(mean_exec_time::numeric, 1) as 平均ms,
       round(max_exec_time::numeric) as 最長ms,
       round((shared_blks_hit + shared_blks_read)::numeric / greatest(calls, 1)) as 読んだページ_1回あたり
from extensions.pg_stat_statements
where query ~ '(airport_board|airport_ontime|airport_tracks|special_now|ga_recent|livery_board|flight_alerts|app_status|airport_notices|current_events)\('
order by mean_exec_time desc
limit 15;

-- ② 羽田の案内板が時刻表をどう引いているか（反映の前は flight_schedule_std で全空港の8日分を読む、
--    後は flight_schedule_dep_std と flight_schedule_arr_std の BitmapOr になるはず）。行数と時間も出る
explain (analyze, buffers, costs off)
select count(*) from public.flight_schedule f
where (f.arr = 'HND' or f.dep = 'HND') and f.std > now() - interval '8 days 6 hours' and f.std < now() + interval '6 hours';

-- ③ 定時の見方（羽田を出た30日分）。反映の前は flight_history_route を全部の日について読む、後は flight_history_dep_day
explain (analyze, buffers, costs off)
select count(*) from public.flight_history h
where h.dep = 'HND' and h.svc_date >= (now() at time zone 'Asia/Tokyo')::date - 30 and h.svc_date < (now() at time zone 'Asia/Tokyo')::date;

-- ④ 空の道すじ（airport_tracks）が今日の羽田で返す量。大きければ（数百KB〜MB）、遅さの主な原因は返す量
select pg_size_pretty(octet_length(t::text)::bigint) as 返す量, jsonb_array_length(t) as 線の数
from (select public.airport_tracks('HND', (now() at time zone 'Asia/Tokyo')::date) as t) x;

-- ⑤ 関数どうしの置き場（移行 164 を反映したあと）：鍵ごとの数と、いちばん古い・新しい行
select split_part(key, ':', 1) as 種類, count(*) as 行, min(at) as いちばん古い, max(at) as いちばん新しい,
       pg_size_pretty(sum(pg_column_size(body))::bigint) as 中身の大きさ
from public.edge_cache group by 1 order by 1;

reset statement_timeout;
