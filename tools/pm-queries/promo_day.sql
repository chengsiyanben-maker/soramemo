-- ある1日（日本時間）の、ある航空会社の便の一覧（1便1行）。広報の動画の材料などに
--   変数：airline＝便名の頭の2文字（例 JL・NH・NU）、day＝日付（例 2026-11-20）
--   流し方：Actions の「PM の読むだけの問い合わせ」で query=promo_day.sql、params=airline=JL day=2026-11-20
--   登録記号・呼び出し符号が便の記録にないときは、全機の記録（reg_legs）から同じ日・同じ番号・同じ区間の機体を1つ探す
--   （呼び出し符号の頭は airline_codes の ICAO の3文字。共同運航の他社の便名は数えない）
with p as (select :'airline'::text as al, :'day'::date as d),
f as (
  select fh.*, ltrim(substr(fh.flight, 3), '0') as num
    from public.flight_history fh, p
   where fh.svc_date = p.d and fh.flight like p.al || '%'
)
select f.svc_date as day, f.flight, coalesce(f.reg, rl.reg) as reg, coalesce(f.type, rl.type) as type, f.aircraft as type_timetable,
       f.dep, f.arr, coalesce(f.callsign, rl.callsign) as callsign,
       to_char(f.std at time zone 'Asia/Tokyo', 'HH24:MI') as std_jst, to_char(f.sta at time zone 'Asia/Tokyo', 'HH24:MI') as sta_jst,
       to_char(f.atd at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as atd_jst, f.atd_src,
       to_char(f.ata at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI:SS') as ata_jst, f.ata_src,
       f.cancelled, f.diverted_to
  from f
  left join lateral (
    select r.reg, r.type, r.callsign
      from public.reg_legs r, p
     where (f.reg is null or f.callsign is null)
       and r.callsign in (select ac.icao || f.num from public.airline_codes ac where ac.iata = p.al)
       and r.day = p.d and (r.dep = f.dep or r.arr = f.arr)
     order by (r.dep = f.dep and r.arr = f.arr) desc, r.first_at
     limit 1) rl on true
 order by f.std, f.flight
