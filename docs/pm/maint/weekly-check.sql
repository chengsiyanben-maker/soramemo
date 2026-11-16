-- そらメモ 週に1回の点検（読むだけ。データは何も変えない）
--   Supabase の SQL Editor に貼って流す。結果は1つの表で出るので、右上の「CSV」で保存して
--   docs/pm/maint/<日付>-result.csv に置く（またはデータ担当の回に貼る）。
--   重くしない作り：統計の表（pg_stat_*・pg_class）と、短い cron の記録だけを読む。表の中身は数えない（行数は見込み）。
--   並べ替えは小さい集まり（表の数・処理の数）だけなので、一時ファイルは使わない。
--   止め方の目安：10秒たっても終わらなければ止めてデータ担当に知らせる（下の statement_timeout で20秒で自動で止まる）。
--   ※ 先頭の2行は、この SQL Editor の画面の中だけで効く設定（本番の設定は変わらない）
set statement_timeout = '20s';
set lock_timeout = '2s';

-- ===== 1本目（必ず） =====
with
-- データベース全体と、統計を取り始めた時刻（「伸び」はここからの数）
db as (
  select 'db' as kind, current_database() as name,
         pg_database_size(current_database())::bigint as size_b,
         null::bigint as rows_est, null::bigint as dead, null::bigint as ins, null::bigint as upd_del,
         (select stats_reset::text from pg_stat_database where datname = current_database()) as note
),
-- 表ごとの大きさ（索引・TOAST を含む）・行数の見込み・死んだ行・足した行と直した／消した行・最後の自動掃除
tbl as (
  select 'table' as kind, s.schemaname || '.' || s.relname as name,
         pg_total_relation_size(s.relid)::bigint as size_b,
         greatest(c.reltuples, 0)::bigint as rows_est,
         s.n_dead_tup as dead, s.n_tup_ins as ins, (s.n_tup_upd + s.n_tup_del) as upd_del,
         'idx=' || pg_size_pretty(pg_indexes_size(s.relid)) ||
         ' toast=' || pg_size_pretty(coalesce(pg_total_relation_size(nullif(c.reltoastrelid, 0)), 0)) ||
         ' vac=' || coalesce(to_char(greatest(s.last_autovacuum, s.last_vacuum) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI'), '-') ||
         ' seq=' || coalesce(s.seq_scan, 0) || ' seq_rows=' || coalesce(s.seq_tup_read, 0) as note
  from pg_stat_user_tables s join pg_class c on c.oid = s.relid
  where s.schemaname in ('public', 'ops', 'cron', 'storage', 'auth')
  order by pg_total_relation_size(s.relid) desc
  limit 40
),
-- 使われていない索引（主キー・一意の索引は除く）。統計を取り始めてから1度も使われていないもの
idx as (
  select 'unused_index' as kind, s.schemaname || '.' || s.indexrelname as name,
         pg_relation_size(s.indexrelid)::bigint as size_b,
         null::bigint as rows_est, null::bigint as dead, s.idx_scan as ins, null::bigint as upd_del,
         'on ' || s.relname as note
  from pg_stat_user_indexes s join pg_index i on i.indexrelid = s.indexrelid
  where s.schemaname in ('public', 'ops') and s.idx_scan = 0 and not i.indisunique and not i.indisprimary
  order by pg_relation_size(s.indexrelid) desc
  limit 20
),
-- 毎日の処理（pg_cron）：残っている記録（cron-history-cleanup が消すまでの分）の回数・失敗・かかった時間
cr as (
  select 'cron' as kind, j.jobname as name,
         null::bigint as size_b,
         count(*)::bigint as rows_est,
         count(*) filter (where d.status <> 'succeeded')::bigint as dead,
         round(avg(extract(epoch from (d.end_time - d.start_time))) * 1000)::bigint as ins,
         round(max(extract(epoch from (d.end_time - d.start_time))) * 1000)::bigint as upd_del,
         'from=' || to_char(min(d.start_time) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') ||
         ' last=' || coalesce((array_agg(d.status order by d.start_time desc))[1], '-') ||
         coalesce(' err=' || left((array_agg(d.return_message order by d.start_time desc) filter (where d.status <> 'succeeded'))[1], 120), '') as note
  from cron.job j join cron.job_run_details d on d.jobid = j.jobid
  where d.start_time > now() - interval '8 days'
  group by j.jobname
),
-- 一度も記録がない（または記録が消えた）処理も出す
cr_none as (
  select 'cron_norun' as kind, j.jobname as name, null::bigint, null::bigint, null::bigint, null::bigint, null::bigint,
         j.schedule || ' active=' || j.active as note
  from cron.job j
  where not exists (select 1 from cron.job_run_details d where d.jobid = j.jobid and d.start_time > now() - interval '8 days')
),
-- ファイル置き場（バケットごとの大きさ。cold は古い記録の置き場）
st as (
  select 'storage' as kind, bucket_id as name,
         coalesce(sum((metadata->>'size')::bigint), 0)::bigint as size_b, count(*)::bigint as rows_est,
         null::bigint, null::bigint, null::bigint, null::text
  from storage.objects group by bucket_id
)
select kind as "区分", name as "名前",
       size_b as "大きさ_バイト", pg_size_pretty(size_b) as "大きさ",
       rows_est as "行数_見込み／回数",
       dead as "死んだ行／失敗",
       ins as "足した行／平均ミリ秒",
       upd_del as "直し消した行／最長ミリ秒",
       note as "メモ"
from (
  select * from db
  union all select * from tbl
  union all select * from idx
  union all select * from cr
  union all select * from cr_none
  union all select * from st
) x
order by case kind when 'db' then 0 when 'table' then 1 when 'unused_index' then 2 when 'cron' then 3 when 'cron_norun' then 4 else 5 end,
         size_b desc nulls last, ins desc nulls last;

-- ===== 2本目（あれば。遅い文の上位10） =====
--   pg_stat_statements が入っていないとエラーになる。そのときは飛ばしてよい。
--   流すときは、下の select から最後の行までを選んで「Run selected」。
-- select left(regexp_replace(query, '\s+', ' ', 'g'), 160) as "文",
--        calls as "回数",
--        round(total_exec_time)::bigint as "合計ミリ秒",
--        round(mean_exec_time)::bigint as "平均ミリ秒",
--        round(max_exec_time)::bigint as "最長ミリ秒",
--        temp_blks_written as "一時ファイルのブロック",
--        rows as "行"
-- from extensions.pg_stat_statements
-- where dbid = (select oid from pg_database where datname = current_database())
-- order by total_exec_time desc
-- limit 10;
