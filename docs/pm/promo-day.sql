-- 広報の動画の材料：ある1日（日本時間）の日本航空の便と、その機体の航跡の点（読むだけ・一時ファイルなし）
--   本人が Supabase の SQL Editor に貼って流し、結果を CSV で保存する（結果の右上の「Download CSV」など）。
--   記録は消さない・変えない（select だけ）。表は使う日の分だけ、主キーと索引で引く。
--   使い方：下の 3 つのうち要るものを1つずつ流す。日付は各文の頭の date '2026-11-25' を書き換える。
--     ① 便の一覧（1便1行）             … どの日でも（flight_history は約400日分ある）
--     ② 航跡の点（1機1分に1点）         … 生の点は36時間で消えるので、「今日」か「前の日」だけ。前の日の分は翌日の11時ごろまでに流す
--     ③ 古い日の航跡の線（1便1行）      … ② が間に合わなかった日。線の点には時刻がないので、docs/pm/promo-expand.py で
--                                         出発〜到着の間に時刻を割り振った点の CSV にする（時刻は推定）
--   対象：日本航空の便名（JL）と、日本トランスオーシャン航空などの NU（日本航空のグループ）。JL だけにするなら各文の
--         「flight like 'NU%'」の行を消す。共同運航の他社の便名（also）は数えない（実際に飛んだ1便は1行）。
--   出典（動画に入れる文）は docs/pm/report-promo-data.md の 3。

set statement_timeout = '60s';

-- ① 便の一覧（1便1行）
with p as (select date '2026-11-25' as d),
f as (
  select fh.*, ltrim(substr(fh.flight, 3), '0') as num
    from public.flight_history fh, p
   where fh.svc_date = p.d and (fh.flight like 'JL%'
      or fh.flight like 'NU%')
)
select f.svc_date as day, f.flight, coalesce(f.reg, rl.reg) as reg, coalesce(f.type, rl.type) as type, f.aircraft as type_timetable,
       f.dep, f.arr, coalesce(f.callsign, rl.callsign) as callsign,
       to_char(f.std at time zone 'Asia/Tokyo', 'HH24:MI') as std_jst, to_char(f.sta at time zone 'Asia/Tokyo', 'HH24:MI') as sta_jst,
       to_char(f.atd at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as atd_jst, f.atd_src,
       to_char(f.ata at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as ata_jst, f.ata_src,
       f.cancelled, f.diverted_to
  from f
  left join lateral (
    -- 便の記録に登録記号・呼び出し符号がないときは、全機の記録（reg_legs）から同じ日・同じ番号・同じ区間の機体を1つ
    select r.reg, r.type, r.callsign from public.reg_legs r, p
     where (f.reg is null or f.callsign is null)
       and r.callsign = any (case when f.flight like 'NU%' then array['JTA' || f.num, 'RAC' || f.num]
                                  else array['JAL' || f.num, 'JLJ' || f.num, 'JTA' || f.num, 'JAC' || f.num, 'HAC' || f.num] end)
       and r.day = p.d and (r.dep = f.dep or r.arr = f.arr)
     order by (r.dep = f.dep and r.arr = f.arr) desc, r.first_at
     limit 1) rl on true
 order by f.std, f.flight;

-- ② 航跡の点（1機1分に1点。今日か前の日だけ）
--    1行＝1点。時刻は日本時間・高度はフィート（記録は百フィート単位）。点は出発の20分前〜到着の20分後（実績がなければ定刻）
--    行が多すぎて保存できないときは、下の「時間で分ける」の2行を使って、例えば 0〜11時・12〜23時の2回に分ける
with p as (select date '2026-11-25' as d),
f as (
  select fh.*, ltrim(substr(fh.flight, 3), '0') as num
    from public.flight_history fh, p
   where fh.svc_date = p.d and not fh.cancelled and (fh.flight like 'JL%'
      or fh.flight like 'NU%')
),
fc as (
  select f.flight, f.dep, f.arr, coalesce(f.reg, rl.reg) as reg, coalesce(f.callsign, rl.callsign) as cs,
         coalesce(f.atd, f.std) - interval '20 minutes' as t0, coalesce(f.ata, f.sta) + interval '20 minutes' as t1
    from f
    left join lateral (
      select r.reg, r.callsign from public.reg_legs r, p
       where (f.reg is null or f.callsign is null)
         and r.callsign = any (case when f.flight like 'NU%' then array['JTA' || f.num, 'RAC' || f.num]
                                    else array['JAL' || f.num, 'JLJ' || f.num, 'JTA' || f.num, 'JAC' || f.num, 'HAC' || f.num] end)
         and r.day = p.d and (r.dep = f.dep or r.arr = f.arr)
       order by (r.dep = f.dep and r.arr = f.arr) desc, r.first_at
       limit 1) rl on true
)
select fc.flight, fc.reg, fc.dep, fc.arr, to_char(pt.t at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as t_jst,
       round(pt.lat::numeric, 4) as lat, round(pt.lon::numeric, 4) as lon, pt.alt * 100 as alt_ft
  from fc
  cross join lateral (
    select distinct on (date_trunc('minute', tp.t)) tp.t, tp.lat, tp.lon, tp.alt
      from public.track_points tp
     where tp.callsign = fc.cs and tp.t >= fc.t0 and tp.t <= fc.t1
     order by date_trunc('minute', tp.t), tp.t) pt
 where fc.cs is not null
   -- 時間で分ける（使うときは先頭の -- を外す）：
   -- and pt.t >= (date '2026-11-25' + time '00:00') at time zone 'Asia/Tokyo'
   -- and pt.t <  (date '2026-11-25' + time '12:00') at time zone 'Asia/Tokyo'
 order by fc.flight, fc.dep, pt.t;

-- ③ 古い日の航跡の線（1便1行。② が間に合わなかった日）
--    pts は Google の polyline（小数4桁）、alts は点ごとの高度（百フィート）。線は曲がらない所の点を省いてあり、点ごとの時刻はない
--    docs/pm/promo-expand.py に CSV を渡すと、出発〜到着の間に道のりの割合で時刻を割り振った点（推定）にする
with p as (select date '2026-11-25' as d)
select fh.svc_date as day, fh.flight, fh.reg, fh.dep, fh.arr,
       to_char(coalesce(fh.atd, fh.std) at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as dep_jst,
       to_char(coalesce(fh.ata, fh.sta) at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as arr_jst,
       (fh.atd is null or fh.ata is null) as time_is_schedule, ft.pts, array_to_string(ft.alts, ' ') as alts
  from public.flight_history fh
  join p on fh.svc_date = p.d
  join public.flight_tracks ft on ft.svc_date = fh.svc_date and ft.flight = fh.flight and ft.dep = fh.dep
 where not fh.cancelled and (fh.flight like 'JL%'
    or fh.flight like 'NU%')
 order by fh.std, fh.flight;
