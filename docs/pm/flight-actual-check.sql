-- フライトの実際の出発・到着（data/flight-actual・移行187）の確かめ。読むだけ・軽い（flights は利用者のフライトだけの小さい表）
-- SQL Editor に全部貼って流す。反映の前は ① だけ（② は列がまだないのでエラーになる）。反映の後と次の日は ①② の両方

-- ① 反映の前：便名のあるフライトの数（いつごろの便か）と、航跡のある数
select case when arr_at >= now() - interval '14 days' then '1: 14日以内（時刻表もある）'
            when arr_at >= now() - interval '31 days' then '2: 31日以内（航跡のさかのぼりができる）'
            when arr_at >= now() - interval '400 days' then '3: 400日以内（毎日の記録がある）'
            else '4: それより前（入らない）' end as when_flown,
       count(*) as flights,
       count(*) filter (where flight_no is not null) as with_flight_no,
       count(*) filter (where track is not null) as with_track
  from public.flights
 group by 1 order by 1;

-- ② 反映の後：実際の時刻がどこから入ったか・「空の上」の合計がどれだけ変わるか（全員の合計。人ごとには出さない）
select coalesce(act_src, '（空）') as act_src,
       count(*) as flights,
       count(*) filter (where track is not null) as with_track,
       round(sum(extract(epoch from arr_at - dep_at)) / 3600) as checkin_hours,
       round(sum(extract(epoch from act_arr_at - act_dep_at)) / 3600) as actual_hours
  from public.flights
 where flight_no is not null
 group by 1 order by 1;
