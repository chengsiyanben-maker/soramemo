-- 読むだけ：古い記録をファイル置き場へ移すとき、1日分がどのくらいの大きさになるか（11/9 定期の手入れ）
--   前の日（日本時間）の1日分を、表ごとに行数と大きさで出す。どれも索引で引くので軽い（20秒で止まる）。何も書き換えない
--   SQL Editor に全部貼って Run。結果の表をそのまま貼ってください（自動翻訳は切ってから）
set statement_timeout = '20s';
with d as (select ((now() at time zone 'Asia/Tokyo')::date - 1) as day),
-- 全機の航跡は主キー (iata, day, …) なので、空港を1つずつ引いてからその日を読む
atl as (
  select a.iata from (
    with recursive r(iata) as (
      select min(iata) from public.airport_tracks_all
      union all
      select (select min(iata) from public.airport_tracks_all t where t.iata > r.iata) from r where r.iata is not null
    ) select iata from r where iata is not null
  ) a
)
select 'airport_tracks_all' as tbl, count(*) as rows, pg_size_pretty(coalesce(sum(pg_column_size(x)), 0)) as size,
       count(distinct x.iata) as airports, max(length(x.pts)) as max_pts
from d, atl join public.airport_tracks_all x on x.iata = atl.iata where x.day = d.day
union all
select 'reg_legs', count(*), pg_size_pretty(coalesce(sum(pg_column_size(x)), 0)), null, null
from d, public.reg_legs x where x.day = d.day
union all
select 'flight_history', count(*), pg_size_pretty(coalesce(sum(pg_column_size(x)), 0)), null, null
from d, public.flight_history x where x.svc_date = d.day
union all
select 'flight_tracks', count(*), pg_size_pretty(coalesce(sum(pg_column_size(x)), 0)), null, max(length(x.pts))
from d, public.flight_tracks x where x.svc_date = d.day;
