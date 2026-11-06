-- 修行の計画：時刻表（ODPT）の更新が来ているかを確かめる（読むだけ。本人が SQL Editor で流す）
-- 10/28 時点では ANA は 11月30日まで、JAL は 1月4日まで。12月の計画を作るには、ANA の 12月以降の時刻表が要る。

-- 1) 航空会社ごとの、時刻表が出ている最後の日（アプリの「◯/◯まで」と同じ値）と、最後に取り込んだ時刻
select operator,
       max(valid_to)   as 最後の日,
       min(valid_from) as 最初の日,
       count(*)        as 行の数,
       max(synced_at)  as 最後に取り込んだ時刻
from public.timetable
group by operator
order by operator;

-- 2) 12月の日ごとに、その日に飛ぶ便の数（0 の日があれば、その日の計画は作れない）
select d::date as 日,
       count(*) filter (where t.operator = 'ANA') as ANA,
       count(*) filter (where t.operator = 'JAL') as JAL
from generate_series(date '2026-12-01', date '2027-01-10', interval '1 day') as d
left join public.timetable t
  on t.valid_from <= d::date and t.valid_to >= d::date
 and (t.days & (1 << extract(dow from d)::int)) <> 0   -- 日曜=1 … 土曜=64
group by d
order by d;

-- 3) 取り込みの処理（timetable-sync）が毎日動いているか：空港ごとの最後の実行と結果
select iata, ran_at, result
from public.timetable_sync_runs
order by ran_at desc
limit 30;
