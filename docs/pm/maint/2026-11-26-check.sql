-- 定期の手入れ 11/26 の確かめ（読むだけ。統計・権限・計画を見るだけで、大きな表は読まない。一瞬で終わる）
-- 反映の前に1回、反映の次の日にもう1回流して、結果を docs/pm/maint/2026-11-26-result.csv に貼るか、データ担当の回に貼ってください。
set local statement_timeout = '20s';

-- ① rwy_sample_counts をだれが呼べるか（反映の前は anon・authenticated が t、反映のあとは f。service_role は t のまま）
select r as 役割, has_function_privilege(r, 'public.rwy_sample_counts()', 'execute') as 呼べる
  from unnest(array['anon', 'authenticated', 'service_role']) r;

-- ② rwy_samples と airports の「全部読み」の回数（統計を最後に消してからの合計）。反映のあと airports の全部読みの伸びが小さくなれば効いている
select relname as 表, n_live_tup as 行の見込み, pg_size_pretty(pg_total_relation_size(relid)) as 大きさ,
       seq_scan as 全部読みの回数, seq_tup_read as 全部読みで読んだ行, idx_scan as 索引で引いた回数
  from pg_stat_user_tables
 where schemaname = 'public' and relname in ('rwy_samples', 'airports')
 order by 1;

-- ③ 新しい索引ができたか・大きさ・使った回数（反映のあと）
select indexrelname as 索引, pg_size_pretty(pg_relation_size(indexrelid)) as 大きさ, idx_scan as 使った回数
  from pg_stat_user_indexes where schemaname = 'public' and indexrelname = 'airports_iata';

-- ④ データベース全体の大きさ（無料枠・プランの上限までの見込みに使う）と、大きい表の上位10
select pg_size_pretty(pg_database_size(current_database())) as データベースの大きさ;
select relname as 表, pg_size_pretty(pg_total_relation_size(relid)) as 大きさ, n_live_tup as 行の見込み, n_dead_tup as 死んだ行
  from pg_stat_user_tables where schemaname = 'public'
 order by pg_total_relation_size(relid) desc limit 10;
