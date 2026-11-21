-- 行き先を便名で決める（11/21 data/livery-dest2）の確かめ。読むだけ。SQL Editor でそのまま流す（どれも索引で引く軽いもの）

-- 1. 本人の通知の6便が、時刻表（flight_schedule）といつもの時刻（foreign_usual）のどちらで行き先が分かるか
--    時刻表は JL・NH だけ（ODPT）。エア・ドゥ（HD）・スカイマーク（BC）・スクート（TR）・ZIPAIR（ZG）は foreign_usual に行があれば分かる
select 'schedule' as src, flight as key, dep, arr, to_char(std at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') as at_jst
from public.flight_schedule
where flight in ('JL500', 'JL140', 'HD14', 'BC4', 'TR866', 'ZG52')
  and std >= now() - interval '20 hours' and std <= now() + interval '1 hour'
union all
select 'usual', callsign, case when dep_here = 1 then iata end, case when dep_here = 0 then iata end,
       'dow ' || dow || ' ' || lpad((mins / 60)::text, 2, '0') || ':' || lpad((mins % 60)::text, 2, '0')
from public.foreign_usual
where callsign in ('ADO14', 'SKY4', 'TGW866', 'TZP52')
order by 1, 2;

-- 2. 反映のあと：今日（日本時間）知らせた（機体・空港）の数を空港ごとに（成田が急に減り、羽田が増えていれば直っている）
select iata, count(*) as n
from public.livery_notified
where notified_at >= (date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo')
  and iata ~ '^[A-Z]{3}$'
group by iata order by n desc;

-- 3. 反映の次の夜のあと：足した会社（トキエア・天草など）の便の実績が foreign_legs に入り始めたか
select airline, count(*) as legs
from public.foreign_legs
where day >= (now() at time zone 'Asia/Tokyo')::date - 1
  and airline in ('BV', 'MZ', 'RF', 'YP', 'HB', 'NX', '3U', 'ZH', 'GJ', 'Z2', 'XJ', 'SL', 'AE', 'AS', 'AM', 'VA', 'TN', 'SB', 'PX', 'HY', 'BI', 'IB', 'AZ', 'LO', 'WS', 'FX', '5X', 'CV', '5Y', 'PO', 'K4', 'CK', 'LD', 'O3')
group by airline order by legs desc;
