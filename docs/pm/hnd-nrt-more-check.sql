-- 羽田・成田の細かいデータのたまり具合（読むだけ。SQL Editor に貼って、1つずつ流す。移行199 の反映のあと）
--   PM の指示 11/25 18時50分（data/hnd-nrt-more）。どれも読むだけで、表を変えない。一時の表を作らない

-- 1. たまり具合（直近1日）：地上の動き・便の変わったこと・見張りの行の数
select 'ground_moves' as what, iata || ':' || kind as k, count(*) as n,
       round(100.0 * avg(lost::int), 1) as lost_pct, round(100.0 * avg((taxi_sec is not null)::int), 1) as with_taxi_pct
from public.ground_moves where saved_at > now() - interval '1 day' group by iata, kind
union all select 'flight_changes', field, count(*), null, null from public.flight_changes where at > now() - interval '1 day' group by field
union all select 'ground_watch', iata || ':' || mode, count(*), null, null from public.ground_watch group by iata, mode
order by 1, 2;

-- 2. 地上を走った時間（分）：空港・到着/出発・滑走路ごと（直近7日。中央値と9割の値）
select iata, kind, coalesce(rwy, '?') as rwy, count(*) as n,
       round((percentile_cont(0.5) within group (order by taxi_sec) / 60.0)::numeric, 1) as median_min,
       round((percentile_cont(0.9) within group (order by taxi_sec) / 60.0)::numeric, 1) as p90_min
from public.ground_moves where saved_at > now() - interval '7 days' and taxi_sec is not null and not lost
group by 1, 2, 3 order by 1, 2, 3;

-- 3. 地上を走った時間の時刻別（日本時間・直近7日・中央値の分）
select iata, kind, extract(hour from coalesce(t_block, t_rwy) at time zone 'Asia/Tokyo')::int as jst_h, count(*) as n,
       round((percentile_cont(0.5) within group (order by taxi_sec) / 60.0)::numeric, 1) as median_min
from public.ground_moves where saved_at > now() - interval '7 days' and taxi_sec is not null and not lost
group by 1, 2, 3 order by 1, 2, 3;

-- 4. ゲート・機材の変更（直近7日）：便の数と、その日のうちに2回以上変わった便
select dep || '→' || arr as route_side, field, count(*) as changes, count(distinct schedule_id) as flights,
       count(*) filter (where old_v is not null) as changed_after_set
from public.flight_changes where at > now() - interval '7 days' and field in ('dep_gate', 'arr_gate', 'aircraft')
  and (dep in ('HND', 'NRT') or arr in ('HND', 'NRT'))
group by 1, 2 order by changes desc limit 30;

-- 5. 続けて降りる間隔（すでに取っている rwy_samples から。直近7日・滑走路ごと・秒の中央値）。新しく取らなくても数えられる
with s as (
  select iata, rwy, at, extract(epoch from at - lag(at) over (partition by iata, rwy order by at)) as gap
  from public.rwy_samples where iata in ('HND', 'NRT') and at > now() - interval '7 days'
)
select iata, rwy, count(*) as n, round((percentile_cont(0.5) within group (order by gap))::numeric) as median_sec,
       round((percentile_cont(0.1) within group (order by gap))::numeric) as p10_sec
from s where gap between 30 and 1800 group by 1, 2 order by 1, 2;
