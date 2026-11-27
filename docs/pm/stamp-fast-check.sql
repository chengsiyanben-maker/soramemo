-- 印を押すときの重さを見る（読むだけ・data/stamp-fast）。SQL Editor で 1 から順に1つずつ流してください。
-- どれも統計の表を読むだけで、一時ファイルを使う大きな並べ替えや結合はしません。

-- 1) 印の保存まわりの文の平均・最大の時間（pg_stat_statements。なければ 2 へ）
select left(regexp_replace(query, '\s+', ' ', 'g'), 120) as 文,
       calls as 回数, round(mean_exec_time::numeric, 1) as 平均ms, round(max_exec_time::numeric, 1) as 最大ms,
       round(total_exec_time::numeric / 1000, 1) as 合計秒
from extensions.pg_stat_statements
where query ilike any (array['%checkins%', '%grant_event_bonus%', '%rl_take%', '%rl_check%', '%checkin_allowed%', '%insert into "public"."flights"%', '%wx_obs%', '%edge_cache%', '%ops_log%'])
  and query not ilike '%pg_stat_statements%'
order by mean_exec_time desc
limit 15;

-- 2) checkins・flights・event_bonuses の大きさと索引の使われ方（行数は見込み）
select c.relname as 表, c.reltuples::bigint as 行数の見込み, pg_size_pretty(pg_total_relation_size(c.oid)) as 大きさ,
       s.seq_scan as 全部読んだ回数, s.idx_scan as 索引で読んだ回数, s.n_dead_tup as 死んだ行
from pg_class c join pg_stat_user_tables s on s.relid = c.oid
where c.relname in ('checkins', 'flights', 'event_bonuses', 'wx_obs', 'edge_cache', 'ops_log')
order by c.relname;

-- 3) 前の7日の 印の時間（Edge Function のログ）は SQL では見られません。
--    ダッシュボードの Edge Functions → checkin → Logs で「checkin_ms」を検索すると、1回ごとに
--    read（判定まで）・total（記録まで）・wx（db＝データベースで天気が決まった／later＝あとで書き足した）が出ます。
