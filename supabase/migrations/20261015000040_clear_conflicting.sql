-- 航空会社の運航情報で欠航の便に出ていた、推定の遅れ・飛行中のお知らせを消す（別の機体と取り違えたもの。2026-10-15）
delete from public.flight_alerts a using public.flight_alerts c
 where c.kind = 'cancel' and a.schedule_id = c.schedule_id and a.kind in ('delay_dep', 'delay_arr', 'no_takeoff');
-- 航空会社の運航情報がある便の、推定の遅れのお知らせも消す（遅れは航空会社の運航情報のほうで出す）
delete from public.flight_alerts a using public.flight_schedule s
 where a.schedule_id = s.id and a.kind in ('delay_dep', 'delay_arr') and a.message like '%推定%'
   and (s.dep_status is not null or s.arr_status is not null);
