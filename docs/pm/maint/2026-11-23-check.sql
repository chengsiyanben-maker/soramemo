-- 定期の手入れ 11/23 の確かめ（読むだけ。統計と計画を見るだけで、表は読まない。一瞬で終わる）
-- 反映の前に1回、反映の次の日にもう1回流して、結果を docs/pm/maint/2026-11-23-result.csv に貼るか、データ担当の回に貼ってください。
set local statement_timeout = '20s';

-- ① 4つの表の「全部読み」と「索引で引いた」回数（統計を最後に消してからの合計）。反映のあと seq_tup_read の伸びが小さくなれば効いている
select relname as 表, n_live_tup as 行の見込み, pg_size_pretty(pg_total_relation_size(relid)) as 大きさ,
       seq_scan as 全部読みの回数, seq_tup_read as 全部読みで読んだ行, idx_scan as 索引で引いた回数,
       stats_reset_note.v as 統計の始まり
  from pg_stat_user_tables
  cross join lateral (select coalesce((select stats_reset::text from pg_stat_database where datname = current_database()), '') v) stats_reset_note
 where schemaname = 'public' and relname in ('rwy_samples', 'ga_events', 'flights', 'livery_plans')
 order by 1;

-- ② 空港ページの「あの日の空」の中の文が、どこまで索引で引けるか（計画だけ。実際には読まない）
--    反映の前は Index Cond に iata だけ、反映のあとは at の幅も入るはず
explain select dir, rwy, count(*) from public.rwy_samples
 where iata = 'HND' and (src = 'live' or iata not in ('HND', 'NRT'))
   and at >= ((current_date - 1)::timestamp at time zone 'Asia/Tokyo') and at < (current_date::timestamp at time zone 'Asia/Tokyo')
 group by 1, 2;

-- ③ 新しい索引ができたか・大きさ（反映のあと）
select indexrelname as 索引, pg_size_pretty(pg_relation_size(indexrelid)) as 大きさ, idx_scan as 使った回数
  from pg_stat_user_indexes where schemaname = 'public' and indexrelname in ('flights_track_todo_dep', 'rwy_samples_iata_at', 'ga_events_iata_at', 'livery_plans_std');

-- ④ 毎晩の仕事の前の7日（rot-eval は rot_predict を数千回呼ぶ。daily-archive は頼むだけなので秒は短いまま、失敗の数を見る）
select j.jobname as 仕事, count(*) as 回数, count(*) filter (where d.status <> 'succeeded') as 失敗,
       round(max(extract(epoch from d.end_time - d.start_time))::numeric, 1) as いちばん長い秒
  from cron.job_run_details d join cron.job j on j.jobid = d.jobid
 where j.jobname in ('daily-archive', 'rot-eval', 'rot-pairs') and d.start_time > now() - interval '7 days'
 group by 1 order by 1;
