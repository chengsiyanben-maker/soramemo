-- 見落としの片付け（data/redo-1116）の確かめ。本人が SQL Editor で流す読むだけの SQL（書き換えない・一時ファイルを使わない形）
-- ① と ② はいつ流してもよい（反映の前に流すと、照合を adsb に切り替えたときの見込みが分かる）。③ は反映のあとに流す

-- ① 照合の取り先を adsb（全機の記録 reg_legs）にしたら、前の7日に OpenSky で「確認済み」になった便のうち何便が同じく確かめられるか
--    （便名のある便だけ。到着空港・便名・時間帯で reg_legs を1件ずつ索引で引く。最大200便）
with f as (
  select f.id, f.flight_no, f.dep_at, f.arr_at, a1.iata dep, a2.iata arr
    from public.flights f
    join public.airports a1 on a1.id = f.from_airport
    join public.airports a2 on a2.id = f.to_airport
   where f.status = 'verified' and f.arr_at >= now() - interval '7 days' and f.flight_no ~ '^[A-Z0-9]{2}[0-9]{1,4}$'
   order by f.arr_at desc limit 200
)
select count(*) as verified_7d,
       count(*) filter (where exists (
         select 1 from public.reg_legs l
          where l.day between (f.dep_at at time zone 'Asia/Tokyo')::date - 1 and (f.arr_at at time zone 'Asia/Tokyo')::date
            and l.arr = f.arr and l.dep = f.dep
            and l.last_at between f.dep_at - interval '30 minutes' and f.arr_at + interval '20 minutes'
       )) as adsb_same_route_time
  from f;

-- ② 照合を待っている便（未確認・前の7日）の数と、そのうち到着空港が全機の記録の円の中にある便の数（円の外は adsb でも確かめられない）
select count(*) as waiting_7d,
       count(*) filter (where exists (select 1 from public.reg_legs l where l.day = (f.arr_at at time zone 'Asia/Tokyo')::date and l.arr = a2.iata limit 1)) as arr_seen_that_day
  from public.flights f join public.airports a2 on a2.id = f.to_airport
 where f.status in ('provisional', 'with_flight_no') and f.arr_at >= now() - interval '7 days';

-- ③ 反映のあと：ODPT のデータの時刻（種類・航空会社ごと。dc_date が null の行は ODPT が dc:date を返していない）
select feed, dc_date at time zone 'Asia/Tokyo' as dc_date_jst, fetched_at at time zone 'Asia/Tokyo' as fetched_jst, n
  from public.odpt_feed_dates order by feed;
