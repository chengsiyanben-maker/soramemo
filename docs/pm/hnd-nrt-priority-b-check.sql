-- 羽田・成田を優先して取る＋滑走路の予想の当たり具合（data/hnd-nrt-priority・移行198）の確かめ。読むだけ
--   SQL Editor に1つずつ貼って流す。どれも索引で引く形で、一時ファイルは使わない
--   2・3 は移行198 を入れたあとに流す（入れる前は関数がないので止まる）

-- 1. いまある記録の量（前の60日）：運用の記録（5分ごと）と、実機で向きが決まった回・着陸の滑走路の記録
select o.iata, count(*) as rows_5min, count(*) filter (where o.obs_mode is not null and not o.obs_mixed) as judged,
       min(o.at) as first_at, max(o.at) as last_at
from public.ops_log o
where o.iata in ('HND', 'NRT') and o.at > now() - interval '60 days'
group by o.iata order by o.iata;

-- 2. 当たり具合（羽田・前の60日）。kind の番号の順に見る：
--    1＝いまの画面の推定／2＝実況の風（追い風7kt）／3＝いちばん良い組／4＝30組の並び（すべて・切り替わりの前後）／5＝TAF から（予報が入ってから）
select * from public.rwy_wx_eval('HND', 60);

-- 3. 当たり具合（成田・前の60日）。成田は 34 向き（b）と 16 向き（a）を当てる
select * from public.rwy_wx_eval('NRT', 60);

-- 4. 成田の時刻ごとの滑走路の使い分け（前の30日・日本時間）。A＝16R/34L、B＝16L/34R。着陸（arr）と離陸（dep）
select extract(hour from s.at at time zone 'Asia/Tokyo')::int as jst_hour, s.dir,
       count(*) filter (where s.rwy in ('16R', '34L')) as a_rwy,
       count(*) filter (where s.rwy in ('16L', '34R')) as b_rwy,
       count(*) filter (where s.rwy in ('16R', '16L')) as dir16,
       count(*) filter (where s.rwy in ('34L', '34R')) as dir34
from public.rwy_samples s
where s.iata = 'NRT' and s.at > now() - interval '30 days'
group by 1, 2 order by 1, 2;

-- 5. 移行198 を入れて1日たったら：TAF と羽田・成田の METAR が抜けずに入っているか
--    TAF は1日に4発表（＋修正）、METAR は30分ごとなので1日に48本前後（＋臨時の SPECI）
select 'taf' as what, t.icao, count(*) as n, max(t.issued_at) as newest from public.taf_obs t group by t.icao
union all
select 'metar_24h', w.icao, count(*), max(w.at) from public.wx_obs w where w.icao in ('RJTT', 'RJAA') and w.at > now() - interval '24 hours' group by w.icao
order by 1, 2;
