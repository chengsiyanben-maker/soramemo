-- 特別塗装機の知らせの行き先の確かめ（11/21 急ぎ・data/livery-dest）。読むだけ。SQL Editor でそのまま流す（どれも軽い）
-- livery_notified は（機体・空港）ごとに最後に知らせた時刻だけを持つ（同じ組は上書き）。'I:'・'Q:' で始まる行は海外の塗装機の早めの知らせのしるし

-- 1. 今日（日本時間）知らせた（機体・空港）の数を空港ごとに
select iata, count(*) as n
from public.livery_notified
where notified_at >= (date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo')
  and iata ~ '^[A-Z]{3}$'
group by iata order by n desc;

-- 2. 今日の成田（NRT）の行：どの機体を何時に。羽田行きの便が混じっていないかを見る
select n.reg, l.name, l.callsign, to_char(n.notified_at at time zone 'Asia/Tokyo', 'HH24:MI') as jst
from public.livery_notified n
left join public.livery_sightings l on l.reg = n.reg
where n.iata = 'NRT'
  and n.notified_at >= (date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo')
order by n.notified_at;

-- 3. 2 の機体の便名の、今日の時刻表の行き先（arr が HND なら取り違え）
select n.reg, l.callsign, s.flight, s.dep, s.arr, to_char(s.std at time zone 'Asia/Tokyo', 'HH24:MI') as std_jst
from public.livery_notified n
join public.livery_sightings l on l.reg = n.reg
join public.flight_schedule s
  on s.std >= now() - interval '24 hours' and s.std <= now() + interval '2 hours'
 and s.flight = regexp_replace(l.callsign, '^(JAL|JTA|JAC|HAC|JLJ)0*', 'JL')
 and l.callsign ~ '^(JAL|JTA|JAC|HAC|JLJ)'
where n.iata = 'NRT'
  and n.notified_at >= (date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo')
union all
select n.reg, l.callsign, s.flight, s.dep, s.arr, to_char(s.std at time zone 'Asia/Tokyo', 'HH24:MI')
from public.livery_notified n
join public.livery_sightings l on l.reg = n.reg
join public.flight_schedule s
  on s.std >= now() - interval '24 hours' and s.std <= now() + interval '2 hours'
 and s.flight = regexp_replace(regexp_replace(regexp_replace(l.callsign, '^ADO0*', 'HD'), '^SKY0*', 'BC'), '^(ANA|AKX|AJX)0*', 'NH')
 and l.callsign ~ '^(ADO|SKY|ANA|AKX|AJX)'
where n.iata = 'NRT'
  and n.notified_at >= (date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo');

-- 4. 反映のあと：いま成田の「着陸・離陸中」とされている特別塗装機（羽田行きが出なくなったか）
select reg, name, callsign, phase, alt_ft, to_char(seen_at at time zone 'Asia/Tokyo', 'HH24:MI:SS') as jst
from public.livery_sightings
where iata = 'NRT' and seen_at > now() - interval '2 hours'
order by seen_at desc;
