-- 読むだけ：まだ来ていない「実際の時刻」が flight_schedule に残っているか（PR #126 の前後で比べる）
-- 定刻（std の索引）で前の2日〜次の1日だけを見る。一時ファイルを使わない軽い形
set statement_timeout = '20s';
-- ① 数：最後に書いた時点で先の atd・ata（ahead）と、いまも先の atd・ata（future_now）
select count(*) as rows,
       count(*) filter (where atd > status_at + interval '1 minute') as atd_ahead,
       count(*) filter (where ata > status_at + interval '1 minute') as ata_ahead,
       count(*) filter (where atd > now()) as atd_future_now,
       count(*) filter (where ata > now()) as ata_future_now
from public.flight_schedule
where std >= now() - interval '2 days' and std < now() + interval '1 day';
-- ② 例：最後に書いた時点で先だった atd（20件まで）。会社ごとの出方を見る
select flight, dep, arr, std, atd, etd, status_at, round(extract(epoch from (atd - status_at)) / 60) as ahead_min, dep_status
from public.flight_schedule
where std >= now() - interval '2 days' and std < now() + interval '1 day'
  and atd > status_at + interval '1 minute'
order by std desc
limit 20;
