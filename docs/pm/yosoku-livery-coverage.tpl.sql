-- 特別塗装機ごとの運用予想：今の予想の部品で、何機に予想が出せるか（運用予想担当・11/8）
-- 読むだけ（select だけ。表は変えない）。本人が Supabase の SQL Editor で、[1]〜[5] を1つずつ選んで流す（Run selected）。
-- 登録記号の一覧は supabase/functions/_shared/liveries.ts の特別塗装機（kind が special のもの、/*COUNT*/ 件）を書き込んだもの。
--   今日の時点で塗装の期間（from〜until）に入っているものだけを数える。一覧が変わったら node tools/yosoku_livery_sql.mjs で作り直す
-- このファイルは docs/pm/yosoku-livery-coverage.tpl.sql から作る。直すときは .tpl.sql の方を直す
-- 使う関数：predict_rotation（時刻表と便の見張りから）・predict_rotation_reg（今の予想）・predict_rotation_v2 と rot_predict（学ぶ予想。移行 152）
--   rot_predict はつながり（rot_pairs）を読むので、[1] の「つながりを作った日」が少ないと [5] の数は小さめに出る

-- ===== [1] 前提：記録の新しさ・つながりを作った日数・数える塗装機の数
with lv(reg, name, airline, from_d, until_d) as (
/*LIVERIES*/
), p as (select (now() at time zone 'Asia/Tokyo')::date as today)
select (select max(day) from public.reg_legs) as "機体の便の記録の新しい日",
       (select count(*) from public.rot_pairs_days, p where day >= p.today - 60)::int as "つながりを作った日数（前の60日）",
       (select min(day) from public.rot_pairs_days) as "つながりの古い日",
       to_regprocedure('public.predict_rotation_v2(text)') is not null as "学ぶ予想の関数がある",
       (select count(*) from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today))::int as "数える塗装機",
       (select count(*) from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today) and reg like 'JA%')::int as "うち国内";

-- ===== [2] 機体ごと：前の30日に飛んだ日数・便の数・最後に見えた日（国内→海外、飛んだ日の多い順）
with lv(reg, name, airline, from_d, until_d) as (
/*LIVERIES*/
), p as (select (now() at time zone 'Asia/Tokyo')::date as today),
act as (select lv.* from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today)),
legs as (
  select l.reg, count(distinct l.day)::int as days, count(*)::int as legs, max(l.day) as last_day, bool_or(l.day >= p.today - 1) as recent
  from public.reg_legs l, p
  where l.reg in (select reg from act) and l.day between p.today - 30 and p.today
  group by l.reg
)
select case when a.reg like 'JA%' then '国内' else '海外' end as "区分", a.reg as "登録記号", a.name as "塗装", a.airline as "会社",
       coalesce(g.days, 0) as "飛んだ日（30日）", coalesce(g.legs, 0) as "便の数", g.last_day as "最後に見えた日", coalesce(g.recent, false) as "今日かきのう飛んだ"
from act a left join legs g on g.reg = a.reg
order by a.reg like 'JA%' desc, 5 desc, 2;

-- ===== [3] まとめ：区分ごとに、前の30日に飛んだ機体・10日以上飛んだ機体・今日かきのう飛んだ機体
with lv(reg, name, airline, from_d, until_d) as (
/*LIVERIES*/
), p as (select (now() at time zone 'Asia/Tokyo')::date as today),
act as (select lv.* from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today)),
legs as (
  select l.reg, count(distinct l.day)::int as days, bool_or(l.day >= p.today - 1) as recent
  from public.reg_legs l, p
  where l.reg in (select reg from act) and l.day between p.today - 30 and p.today
  group by l.reg
)
select * from (
select coalesce(case when a.reg like 'JA%' then '国内' else '海外' end, '合計') as "区分",
       count(*)::int as "塗装機", count(g.reg)::int as "30日に1回でも飛んだ", count(*) filter (where g.days >= 10)::int as "10日以上飛んだ",
       count(*) filter (where g.recent)::int as "今日かきのう飛んだ"
from act a left join legs g on g.reg = a.reg
group by rollup (case when a.reg like 'JA%' then '国内' else '海外' end)
) q order by "区分" = '合計', "区分" = '海外', "区分";

-- ===== [4] 今の予想が出るか：今日かきのう飛んだ塗装機だけ、いまの画面の部品（loadPrediction）と学ぶ予想を呼ぶ
--   「画面」：loadPrediction と同じく、predict_rotation で今の便が分かればそれ、分からなければ predict_rotation_reg
--   最後の行（登録記号が「合計」）は、それぞれ1便でも予想が出た機体の数
with lv(reg, name, airline, from_d, until_d) as (
/*LIVERIES*/
), p as (select (now() at time zone 'Asia/Tokyo')::date as today),
act as (select lv.* from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today)),
r as (select distinct l.reg from public.reg_legs l, p where l.reg in (select reg from act) and l.day >= p.today - 1),
x as (select r.reg, public.predict_rotation(r.reg) as a, public.predict_rotation_reg(r.reg) as b, public.predict_rotation_v2(r.reg) as c from r),
y as (
  select x.reg, act.name,
         jsonb_typeof(a -> 'known') = 'object' as tt_known,
         coalesce(jsonb_array_length(a -> 'next'), 0) as tt_n,
         coalesce(jsonb_array_length(b -> 'next'), 0) as base_n,
         coalesce(jsonb_array_length(c -> 'next'), 0) as learn_n,
         c -> 'next' -> 0 ->> 'callsign' as learn_first, c -> 'next' -> 0 ->> 'src' as learn_src
  from x join act on act.reg = x.reg
), z as (select y.*, case when tt_known then tt_n else base_n end as screen_n from y)
select * from (
select reg as "登録記号", name as "塗装", tt_known::text as "時刻表で今の便が分かる", screen_n as "画面の予想（便の数）",
       base_n as "今の予想（便の数）", learn_n as "学ぶ予想（便の数）", learn_first as "学ぶ予想の次の便", learn_src as "その出どころ"
from z
union all
select '合計', count(*)::text || ' 機', count(*) filter (where tt_known)::text, count(*) filter (where screen_n > 0)::int,
       count(*) filter (where base_n > 0)::int, count(*) filter (where learn_n > 0)::int, null, null
from z
) q order by "登録記号" = '合計', "登録記号";

-- ===== [5] 前の14日を振り返る：塗装機の便（次の便があったもの）を最大400便えらび、その日の前の夜の時点の記録だけで「次の1便」を予想して、実際と比べる
--   今の予想（base）と学ぶ予想（learn）の2通り。区分ごと・機体ごとに、予想が出た便・当たった便。時間切れになるときは 400 を 200 に下げる
--   （1便あたり 0.1〜0.2 秒の見込み。データ担当の確かめでは、3通りで1便約0.26秒）
set statement_timeout = '170s';
with lv(reg, name, airline, from_d, until_d) as (
/*LIVERIES*/
), p as (select (now() at time zone 'Asia/Tokyo')::date as today, 14 as days, 400 as max_legs),
act as (select lv.* from lv, p where (from_d is null or from_d <= p.today) and (until_d is null or until_d >= p.today)),
s as (
  select l.reg, l.day, l.callsign as cs, l.arr, l.first_at, nl.callsign as next_cs
  from public.reg_legs l cross join p
  cross join lateral (select b.callsign from public.reg_legs b
                      where b.reg = l.reg and b.day = l.day and (b.first_at, b.callsign) > (l.first_at, l.callsign)
                      order by b.first_at, b.callsign limit 1) nl
  where l.reg in (select reg from act) and l.day between p.today - p.days and p.today - 1
  order by md5(l.reg || ':' || l.day || ':' || l.callsign)
  limit (select max_legs from p)
), e as (
  select s.*, case when s.reg like 'JA%' then '国内' else '海外' end as grp,
         public.rot_predict('base',  s.reg, s.day, s.cs, s.arr, (s.first_at at time zone 'Asia/Tokyo')::time, 1) -> 0 as pb,
         public.rot_predict('learn', s.reg, s.day, s.cs, s.arr, (s.first_at at time zone 'Asia/Tokyo')::time, 1) -> 0 as pl
  from s
)
select coalesce(grp, '合計') as "区分", coalesce(reg, case when grp is null then '' else '（区分の計）' end) as "登録記号",
       count(*)::int as "便", count(distinct reg || day)::int as "機体×日",
       count(pb)::int as "今の予想が出た", count(*) filter (where pb ->> 'callsign' = next_cs)::int as "今の予想が当たった",
       count(pl)::int as "学ぶ予想が出た", count(*) filter (where pl ->> 'callsign' = next_cs)::int as "学ぶ予想が当たった",
       count(*) filter (where pl ->> 'src' = 'livery')::int as "うち塗装機の予定の便から",
       count(distinct reg) filter (where pl is not null)::int as "学ぶ予想が1回でも出た機体"
from e
group by grouping sets ((grp, reg), (grp), ())
order by grp is null, grp = '海外', reg is null desc, reg;
