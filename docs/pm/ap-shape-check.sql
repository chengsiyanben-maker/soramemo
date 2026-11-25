-- 空港の形（data/ap-shape）の確かめ。本人が SQL Editor で流す読むだけの SQL（軽い。一時ファイルを使わない）

-- 1. 三沢・岩国で「範囲の外」と断った回数（前の90日）。dist_km は最寄り空港の点からの距離（km）。1.5〜2.5km に多ければ、ターミナルのあたりで断っている
select a.iata, r.reason, count(*) as n, min(r.dist_km) as min_km, max(r.dist_km) as max_km
from ops.checkin_rejections r join public.airports a on a.id = r.airport_id
where r.airport_id in (92, 96) and r.created_at > now() - interval '90 days'
group by 1, 2 order by 1, 2;

-- 2. どの空港でも「あと少しで範囲」の断りが多い所（前の90日・半径＋1km 以内の out_of_range）。上の15か所
select a.iata, a.name, a.radius_m, count(*) as near_miss, round(avg(r.dist_km), 1) as avg_km
from ops.checkin_rejections r join public.airports a on a.id = r.airport_id
where r.reason = 'out_of_range' and r.created_at > now() - interval '90 days' and r.dist_km * 1000 <= a.radius_m + 1000
group by 1, 2, 3 order by near_miss desc limit 15;
