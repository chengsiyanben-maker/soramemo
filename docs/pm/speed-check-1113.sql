-- 速さの見直し（11/13）：本人が Supabase の SQL Editor に貼って流す「読むだけ」の SQL。表は変えない
-- 4つに分けてある。1つずつ選んで流し、結果を docs/pm/speed-1113-result.csv に貼るか、そのまま貼ってください
-- どれも小さい表（統計の表）を読むだけで、大きな並べ替え・一時ファイルは使わない

-- ① 遅い文の上位15（pg_stat_statements。1回あたりの時間の長い順。20回以上呼ばれたものだけ）
select left(regexp_replace(query, '\s+', ' ', 'g'), 160) as 文,
       calls as 回数,
       round(mean_exec_time::numeric, 1) as 平均ms,
       round(max_exec_time::numeric) as 最長ms,
       round((total_exec_time / 1000 / 60)::numeric, 1) as 合計分,
       temp_blks_written as 一時ファイル
from extensions.pg_stat_statements
where calls >= 20
order by mean_exec_time desc
limit 15;

-- ② 毎分・毎晩の処理の時間（前の7日。仕事ごとに回数・失敗・平均・最長）
select j.jobname as 仕事,
       count(*) as 回数,
       count(*) filter (where d.status <> 'succeeded') as 失敗,
       round(avg(extract(epoch from d.end_time - d.start_time))::numeric, 2) as 平均秒,
       round(max(extract(epoch from d.end_time - d.start_time))::numeric, 1) as 最長秒,
       round(avg(extract(epoch from d.end_time - d.start_time)) filter (where d.start_time > now() - interval '1 day')::numeric, 2) as 前の1日の平均秒
from cron.job_run_details d
join cron.job j on j.jobid = d.jobid
where d.start_time > now() - interval '7 days'
group by j.jobname
order by max(extract(epoch from d.end_time - d.start_time)) desc nulls last;

-- ③ 索引を使わずに全部読んでいる表（読んだ行の多い順10。索引の足りない所の候補）
select relname as 表,
       seq_scan as 全部読んだ回数,
       seq_tup_read as 全部読みで読んだ行,
       idx_scan as 索引で引いた回数,
       n_live_tup as 行の見込み,
       pg_size_pretty(pg_total_relation_size(relid)) as 大きさ
from pg_stat_user_tables
where schemaname = 'public'
order by seq_tup_read desc
limit 10;

-- ④ 使っていない索引（統計を取り始めてから1回も使われていない・主キーと一意は除く。大きい順10）
select s.relname as 表, s.indexrelname as 索引, pg_size_pretty(pg_relation_size(s.indexrelid)) as 大きさ
from pg_stat_user_indexes s
join pg_index i on i.indexrelid = s.indexrelid
where s.schemaname = 'public' and s.idx_scan = 0 and not i.indisunique and not i.indisprimary
order by pg_relation_size(s.indexrelid) desc
limit 10;

-- ⑤ 【SQL Editor ではなく「Logs Explorer」に貼る】関数ごとの時間（前の24時間。左上の時間の幅を「Last 24 hours」に）
--    動かなければ（列の名前が違うなど）、そのまま教えてください
-- select regexp_extract(request.url, r'functions/v1/([a-z0-9-]+)') as fn,
--        count(*) as n,
--        round(avg(m.execution_time_ms)) as avg_ms,
--        max(m.execution_time_ms) as max_ms,
--        countif(response.status_code >= 500) as errors
-- from function_edge_logs
--   cross join unnest(metadata) as m
--   cross join unnest(m.response) as response
--   cross join unnest(m.request) as request
-- group by fn
-- order by avg_ms desc
-- limit 20
