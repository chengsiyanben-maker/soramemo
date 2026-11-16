-- 定期の手入れ 11/16 の2回目：本人が SQL Editor で流す「読むだけ」の SQL（データ担当）
-- 移行 183 で索引を足す8か所の表について、今どれだけ「全部読み」が起きているか・表の大きさを出す。
-- 統計の表（pg_stat_user_tables）と索引の一覧を読むだけ。表の中身は読まないので一瞬で終わる。一時ファイルも使わない
set statement_timeout = '20s';

select s.relname                                   as 表,
       s.n_live_tup                                as 行数の見込み,
       pg_size_pretty(pg_total_relation_size(s.relid)) as 大きさ,
       s.seq_scan                                  as 全部読みの回数,
       s.seq_tup_read                              as 全部読みで読んだ行,
       coalesce(s.idx_scan, 0)                     as 索引で引いた回数,
       (select string_agg(i.indexrelname, ', ' order by i.indexrelname)
          from pg_stat_user_indexes i where i.relid = s.relid
            and i.indexrelname in ('aircraft_user', 'flights_dep_checkin', 'flights_arr_checkin', 'co3_market_aircraft',
                                   'co3_orders_aircraft', 'co3_breakdowns_spare', 'co3_heavy_spare', 'co3_extra_aircraft')) as 足した索引_反映後に出る
from pg_stat_user_tables s
where s.schemaname = 'public'
  and s.relname in ('aircraft', 'flights', 'checkins', 'co3_market', 'co3_orders', 'co3_breakdowns', 'co3_heavy', 'co3_extra')
order by s.seq_tup_read desc;
