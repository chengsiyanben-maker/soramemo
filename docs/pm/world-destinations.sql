-- 日本から直行便のある海外の空港の一覧（読むだけ。SQL Editor に貼って流す）
-- flight_schedule（JAL・ANA の時刻表）の、これから7日の便のうち、片方が日本の空港表にない便を数える。
-- 海外の航空会社の便は時刻表に入っていないので、この一覧は JAL・ANA の分だけ（海外の会社の分は airport-foreign の記録で補う）。
-- 索引 flight_schedule_std（std）で7日分だけ引く。大きな並べ替え・一時の表は使わない。20秒で止まる。
set statement_timeout = '20s';
with jp as (select iata from public.airports where iata is not null),
     f as (select flight, dep, arr from public.flight_schedule
           where std >= now() and std < now() + interval '7 days'),
     x as (
       select arr as apt, 1 as out_n, 0 as in_n, flight from f where arr not in (select iata from jp)
       union all
       select dep as apt, 0, 1, flight from f where dep not in (select iata from jp)
     )
select apt as "海外の空港", sum(out_n) as "日本から（7日）", sum(in_n) as "日本へ（7日）",
       count(distinct flight) as "便名の数"
from x group by apt order by sum(out_n) + sum(in_n) desc;
