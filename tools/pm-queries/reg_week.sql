-- ある機体（登録記号）の、ある期間（日本時間の日付・両端を含む・31日まで）の飛んだ区間
--   変数：reg＝登録記号（例 JA8089）、from・to＝日付（例 from=2026-11-14 to=2026-11-20）
--   流し方：Actions の「PM の読むだけの問い合わせ」で query=reg_week.sql、params=reg=JA8089 from=2026-11-14 to=2026-11-20
--   src：便＝ODPT の便の記録（flight_history）に登録記号が付いた便、全機＝全機の記録（reg_legs）だけにある区間
--   （同じ日・同じ区間が両方にあれば便の方だけ出す）
with p as (
  select upper(:'reg'::text) as reg, :'from'::date as d0, least(:'to'::date, :'from'::date + 30) as d1
),
fh as (
  select f.svc_date as day, f.flight, f.callsign, f.dep, f.arr, f.type,
         coalesce(f.atd, f.std) as t_dep, coalesce(f.ata, f.sta) as t_arr, f.cancelled, f.diverted_to
    from public.flight_history f, p
   where f.svc_date between p.d0 and p.d1 and f.reg = p.reg
),
rl as (
  select r.day, null::text as flight, r.callsign, r.dep, r.arr, r.type, r.first_at as t_dep, r.last_at as t_arr
    from public.reg_legs r, p
   where r.reg = p.reg and r.day between p.d0 and p.d1
)
select day, '便' as src, flight, callsign, dep, arr, type,
       to_char(t_dep at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI') as dep_jst,
       to_char(t_arr at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI') as arr_jst, cancelled, diverted_to
  from fh
union all
select rl.day, '全機', rl.flight, rl.callsign, rl.dep, rl.arr, rl.type,
       to_char(rl.t_dep at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI'),
       to_char(rl.t_arr at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI'), null, null
  from rl
 where not exists (select 1 from fh where fh.day = rl.day and fh.dep is not distinct from rl.dep and fh.arr is not distinct from rl.arr)
 order by 8, 2
