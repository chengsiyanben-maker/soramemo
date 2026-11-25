-- 羽田・成田の滑走路の予想の当たり具合と、たまり具合（読むだけ。SQL Editor に貼って、1つずつ流す）
--   PM の指示 11/25 18時45分（data/hnd-nrt-priority）。どれも読むだけで、表を変えない。一時の表を作らない
--   見る日数は各文の「interval '60 days'」を変えると変わる（ops_log は 10/15 から、wx_taf は移行198 の反映のあと）
--   運用の向き：羽田 N＝北風（north・nightN）、S＝南風（south・city・nightS）。成田 a＝16運用（南東向き）、b＝34運用（北西向き）
--   「推定」は画面と同じ風からの推定（羽田は 34滑走路への追い風が7ktを超えたら南風）、「実機」は実際の機体からの判定（ops_log の obs_mode）

-- 1. たまり具合（移行198 のあと。wx_taf は2空港、過去の分は2日ほどで 10/15 までさかのぼる）
select 'wx_taf' as what, icao as k, count(*) as n, min(issued) as first, max(issued) as last from public.wx_taf group by icao
union all select 'wx_taf_hours', icao, count(*), min(at), max(at) from public.wx_taf_hours group by icao
union all select 'wx_obs 7日', icao, count(*), min(at), max(at) from public.wx_obs where icao in ('RJTT', 'RJAA') and at > now() - interval '7 days' group by icao
union all select 'ops_log 7日（実機あり）', iata, count(*), min(at), max(at) from public.ops_log where iata in ('HND', 'NRT') and at > now() - interval '7 days' and obs_mode is not null group by iata
union all select 'rwy_samples 7日', iata, count(*), min(at), max(at) from public.rwy_samples where iata in ('HND', 'NRT') and at > now() - interval '7 days' group by iata
order by 1, 2;

-- 2. 実況の風から当てる：時間帯別（深夜 23〜6時・南風の午後 15〜19時・朝 7〜11時半・そのほか）
--    agree_dir＝向き（N/S、a/b）が合った割合。agree_mode＝羽田の都心ルート・深夜まで合った割合
with o as (
  select iata, at, wspd, est_mode, obs_mode, est_unsure,
         extract(hour from at at time zone 'Asia/Tokyo') + extract(minute from at at time zone 'Asia/Tokyo') / 60.0 as h
  from public.ops_log
  where iata in ('HND', 'NRT') and at > now() - interval '60 days' and obs_mode is not null and not obs_mixed
), d as (
  select *, case when iata = 'NRT' then est_mode when est_mode in ('north', 'nightN') then 'N' else 'S' end as est_dir,
            case when iata = 'NRT' then obs_mode when obs_mode in ('north', 'nightN') then 'N' else 'S' end as obs_dir,
            case when h >= 23 or h < 6 then '1 深夜 23-6時' when h >= 15 and h < 19 then '3 午後 15-19時' when h >= 7 and h < 11.5 then '2 朝 7-11時半' else '4 そのほか' end as band
  from o
)
select iata, band, count(*) as n,
       round(100.0 * avg((est_dir = obs_dir)::int), 1) as agree_dir,
       round(100.0 * avg((est_mode = obs_mode)::int), 1) as agree_mode,
       round(100.0 * avg((obs_dir in ('S', 'a'))::int), 1) as obs_south_pct
from d group by iata, band order by iata, band;

-- 3. 実況の風から当てる：風の強さ別（ノット）
with d as (
  select iata, wspd,
         case when iata = 'NRT' then est_mode when est_mode in ('north', 'nightN') then 'N' else 'S' end as est_dir,
         case when iata = 'NRT' then obs_mode when obs_mode in ('north', 'nightN') then 'N' else 'S' end as obs_dir
  from public.ops_log
  where iata in ('HND', 'NRT') and at > now() - interval '60 days' and obs_mode is not null and not obs_mixed and wspd is not null
)
select iata, case when wspd < 5 then '0-4' when wspd < 10 then '5-9' when wspd < 15 then '10-14' when wspd < 20 then '15-19' else '20+' end as wind_kt,
       count(*) as n, round(100.0 * avg((est_dir = obs_dir)::int), 1) as agree_dir
from d group by 1, 2 order by 1, min(wspd);

-- 4. 切り替わりの前後：実機の向きが変わってから何分たったか（since）と、次に変わるまで何分あるか（until）ごとの当たり具合
with d as (
  select iata, at,
         case when iata = 'NRT' then est_mode when est_mode in ('north', 'nightN') then 'N' else 'S' end as est_dir,
         case when iata = 'NRT' then obs_mode when obs_mode in ('north', 'nightN') then 'N' else 'S' end as obs_dir
  from public.ops_log
  where iata in ('HND', 'NRT') and at > now() - interval '60 days' and obs_mode is not null and not obs_mixed
), g as (
  select *, sum(chg) over (partition by iata order by at) as grp
  from (select *, (lag(obs_dir) over (partition by iata order by at) is distinct from obs_dir)::int as chg from d) x
), s as (
  select *, extract(epoch from at - min(at) over (partition by iata, grp)) / 60 as since,
            extract(epoch from max(at) over (partition by iata, grp) - at) / 60 as until
  from g
)
select iata, kind, bucket, count(*) as n, round(100.0 * avg((est_dir = obs_dir)::int), 1) as agree_dir from (
  select iata, est_dir, obs_dir, 'since' as kind,
         case when since < 15 then '0-15分' when since < 30 then '15-30分' when since < 60 then '30-60分' when since < 120 then '1-2時間' else '2時間-' end as bucket, since as ord from s
  union all
  select iata, est_dir, obs_dir, 'until',
         case when until < 15 then '0-15分' when until < 30 then '15-30分' when until < 60 then '30-60分' when until < 120 then '1-2時間' else '2時間-' end, until from s
) q group by iata, kind, bucket order by iata, kind, min(ord);

-- 5. 羽田の追い風の上限と粘り：34滑走路への追い風（ノット、1kt ごと）で、実機が南風だった割合。
--    prev＝ひとつ前（5分前）の実機の向き。N の行と S の行で南風になる割合の変わり目がずれていれば「すぐ切り替えない粘り」がある
with d as (
  select at, round(-wspd * cos(radians(wdir - 330)))::int as tail34,
         case when obs_mode in ('north', 'nightN') then 'N' else 'S' end as obs_dir,
         extract(hour from at at time zone 'Asia/Tokyo') as h
  from public.ops_log
  where iata = 'HND' and at > now() - interval '60 days' and obs_mode is not null and not obs_mixed and wdir is not null and wspd is not null
), p as (select *, lag(obs_dir) over (order by at) as prev from d)
select case when h >= 23 or h < 6 then '深夜' else '昼' end as band, prev, greatest(-10, least(20, tail34)) as tail34_kt,
       count(*) as n, round(100.0 * avg((obs_dir = 'S')::int), 1) as south_pct
from p where prev is not null group by 1, 2, 3 order by 1, 2, 3;

-- 6. 成田の A/B 滑走路の使い分け：着陸した滑走路（rwy_samples）を日本時間の時刻ごとに
--    A＝16R/34L、B＝16L/34R。0〜6時は運用していない。23時台は A だけのはず
select extract(hour from at at time zone 'Asia/Tokyo')::int as jst_h, count(*) as n,
       round(100.0 * avg((rwy in ('16R', '34L'))::int), 1) as a_pct,
       round(100.0 * avg((rwy in ('16R', '16L'))::int), 1) as dir16_pct
from public.rwy_samples where iata = 'NRT' and at > now() - interval '60 days'
group by 1 order by 1;

-- 7. 数時間前の TAF から当てる（移行198 のあと。過去の TAF がさかのぼって入れば、10/15 からの日で比べられる）
--    TAF の時間ごとの推定（wx_taf_hours.est_mode）と、その時間の実機（ops_log の5分ごと）を比べる。lead＝発表から何時間先か
--    同じ時刻を、発表の違う TAF で何回か数える（lead の区切りごとに見るので、ほとんど重ならない）
with o as (
  select iata, at, case iata when 'HND' then 'RJTT' else 'RJAA' end as icao,
         case when iata = 'NRT' then obs_mode when obs_mode in ('north', 'nightN') then 'N' else 'S' end as obs_dir, obs_mode
  from public.ops_log
  where iata in ('HND', 'NRT') and at > now() - interval '60 days' and obs_mode is not null and not obs_mixed
)
select o.iata, case when h.lead_h <= 3 then '1 1-3時間前' when h.lead_h <= 6 then '2 4-6時間前' when h.lead_h <= 12 then '3 7-12時間前' else '4 13-30時間前' end as lead,
       count(*) as n,
       round(100.0 * avg(((case when o.iata = 'NRT' then h.est_mode when h.est_mode in ('north', 'nightN') then 'N' else 'S' end) = o.obs_dir)::int), 1) as agree_dir,
       round(100.0 * avg((h.est_mode = o.obs_mode)::int), 1) as agree_mode,
       round(100.0 * avg((h.changing or h.t_kind is not null)::int), 1) as unsure_pct
from o join public.wx_taf_hours h on h.icao = o.icao and h.at = date_trunc('hour', o.at) and h.issued <= o.at and h.est_mode is not null
group by 1, 2 order by 1, 2;
