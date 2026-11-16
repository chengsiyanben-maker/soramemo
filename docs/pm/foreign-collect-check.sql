-- 海外の会社の便の実績（data/foreign-collect）：本番で SQL Editor に貼って流す「読むだけ」の SQL（書き換えなし・一時ファイルを使わない・20秒で止まる）
-- 前の日（日本時間）の全機の航跡（airport_tracks_all）から、海外の会社の便が何回出た・着いたかを数える。表の大きさの見込み（1年で何行）に使う。
-- 移行 171 の前に流せるように、日本の会社の呼び出し符号の記号はここに書いている（移行の airline_codes の japan と同じ）
set statement_timeout = '20s';

with aps as (
  select array_agg(distinct iata) as a from public.airports where iata ~ '^[A-Z]{3}$'
), t as (
  select t.iata, t.callsign, t.dep_here
    from public.airport_tracks_all t, aps
   where t.iata = any(aps.a) and t.day = (now() at time zone 'Asia/Tokyo')::date - 1
)
select case when left(callsign, 3) in ('ADO','AJX','AKX','ANA','APJ','FDA','HAC','IBX','JAC','JAL','JJP','JLJ','JTA','NCA','ORC','SFJ','SJO','SKY','SNJ')
            then '日本の会社' else '海外の会社など' end as 区分,
       count(*) as 回数,
       count(distinct callsign) as 便,
       count(*) filter (where dep_here = 1) as 出た,
       count(*) filter (where dep_here = 0) as 着いた,
       count(distinct iata) as 空港
  from t
 group by 1
 order by 1;
