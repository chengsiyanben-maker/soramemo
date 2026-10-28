-- 特別塗装機の画面：機体ごとの「いま」「今日の足あと」「この30日に来た空港」をまとめて返す。
-- 足あとは reg_legs（機体ごとの便の記録。表はそのまま、読むだけ）。発着の空港が入っていない便（3時間ごとのまとめの前）は、
-- 便名から航空会社の時刻表（flight_schedule）で埋める。読めるのは特別塗装機として見えたことがある機体（livery_sightings）だけ。
-- 表を増やさないので RLS は変わらない（reg_legs・livery_sightings・live_positions・flight_schedule はどれも利用者から直接読めないまま）

-- 便名（呼び出し符号）→ 時刻表の便名（JAL113 → JL113）
create or replace function public.cs_flight(p_cs text) returns text
language sql immutable set search_path = public as $$
  select case when m is null then null else
    (case m[1] when 'JAL' then 'JL' when 'JLJ' then 'JL' when 'HAC' then 'JL' when 'JAC' then 'JL' when 'JTA' then 'NU'
       when 'ANA' then 'NH' when 'AKX' then 'NH' when 'AJX' then 'NH' when 'SKY' then 'BC' when 'ADO' then 'HD' when 'SNJ' then '6J'
       when 'SFJ' then '7G' when 'APJ' then 'MM' when 'JJP' then 'GK' when 'SJO' then 'IJ' when 'FDA' then 'JH' when 'ORC' then 'OC'
       when 'IBX' then 'FW' else null end) || ltrim(m[2], '0') end
  from (select regexp_match(upper(coalesce(p_cs, '')), '^([A-Z]{3})([0-9]{1,4})[A-Z]?$') as m) x
  where m is null or m[1] in ('JAL','JLJ','HAC','JAC','JTA','ANA','AKX','AJX','SKY','ADO','SNJ','SFJ','APJ','JJP','SJO','FDA','ORC','IBX')
$$;
revoke all on function public.cs_flight(text) from public;

create or replace function public.livery_board(p_regs text[]) returns jsonb
language sql stable security definer set search_path = public as $$
  with r as (
    select distinct s.reg from public.livery_sightings s
    where s.reg = any(p_regs[1:200])
  ), d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  legs as (
    select l.reg, l.callsign, l.day, l.first_at, l.last_at,
      coalesce(l.dep, f.dep) as dep, coalesce(l.arr, f.arr) as arr, f.std, f.sta,
      (l.dep is null or l.arr is null) and f.id is not null as by_schedule
    from public.reg_legs l join r on r.reg = l.reg cross join d
    left join lateral (
      select fs.id, fs.dep, fs.arr, fs.std, fs.sta from public.flight_schedule fs
      where fs.flight = public.cs_flight(l.callsign) and fs.std between l.first_at - interval '3 hours' and l.first_at + interval '1 hour'
      order by abs(extract(epoch from fs.std - l.first_at)) limit 1
    ) f on true
    where l.day >= d.today - 30
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'reg', r.reg,
    'now', (select jsonb_build_object('at', s.seen_at, 'lat', round(s.lat::numeric, 3), 'lon', round(s.lon::numeric, 3), 'alt_ft', s.alt_ft,
              'callsign', s.callsign, 'iata', s.iata, 'phase', s.phase, 'kt', p.kt)
            from public.livery_sightings s left join public.live_positions p on p.callsign = s.callsign
            where s.reg = r.reg and s.seen_at > now() - interval '15 minutes'),
    'today', coalesce((select jsonb_agg(jsonb_build_object('cs', g.callsign, 'dep', g.dep, 'arr', g.arr, 'first', g.first_at, 'last', g.last_at,
              'std', g.std, 'sta', g.sta, 'sch', g.by_schedule) order by g.first_at)
            from legs g cross join d where g.reg = r.reg and g.day = d.today), '[]'::jsonb),
    'last_day', (select max(g.day) from legs g where g.reg = r.reg),
    'arr30', coalesce((select jsonb_object_agg(a.arr, a.n) from (select g.arr, count(*) as n from legs g where g.reg = r.reg and g.arr is not null group by g.arr) a), '{}'::jsonb)
  )), '[]'::jsonb) from r
$$;
revoke all on function public.livery_board(text[]) from public;
grant execute on function public.livery_board(text[]) to anon, authenticated;

-- 機体ごとの通知：選んだ特別塗装機が新しい便で飛び始めたら知らせる（push-subscribe の sp_regs。どの空港でも、1便に1回）。
-- push_subs の RLS は今のまま（利用者からは読めない。書くのは push-subscribe だけ）
alter table public.push_subs add column if not exists sp_regs text[] not null default '{}';
alter table public.push_subs drop constraint if exists push_subs_sp_regs_check;
alter table public.push_subs add constraint push_subs_sp_regs_check check (cardinality(sp_regs) <= 20);
create index if not exists push_subs_sp_regs on public.push_subs using gin (sp_regs);
