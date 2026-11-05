-- 運用予想の毎晩の採点（rot_eval）を見る（読むだけ。表も関数も作らず、書き込みもしません）
-- 貼る前に、ブラウザの自動翻訳を切ってください（SQL が書き換わって動かなくなります）
-- 使える日：移行 152（rot_pairs・rot_eval・毎晩の採点 rot-learn）を反映した次の日から。毎晩 日本時間 4:55 に前の日の分が1日ぶん増えます
--
-- 先頭の p で変えられるもの
--   d_from：何日前から見るか（初めは7日）
--   carrier：会社で絞る（'JAL'・'ANA' など。null なら絞らない）
-- 方式：base＝今の予想、learn＝学ぶ予想（学んだ便は2回以上・3割以上で出す）、learn_hi＝学ぶ予想で、しきい値を3回以上・4割以上に上げたもの
-- 列：当たり率＝当たり÷基準の数、出したうちの当たり率＝当たり÷予想を出した数
-- 判断の目安：learn_hi の「出したうちの当たり率」が base 並みに戻り、「当たり率」が base より上なら、しきい値を上げる価値あり
with p as (
  select (now() at time zone 'Asia/Tokyo')::date - 7 as d_from, null::text as carrier
), e as (
  select r.* from public.rot_eval r, p
  where r.day >= p.d_from and (p.carrier is null or r.carrier = p.carrier)
), g as (
  select '全体' as kubun, '' as val, method, k, sum(n) as n, sum(predicted) as pr, sum(hit) as hit from e group by method, k
  union all
  select '会社', carrier, method, k, sum(n), sum(predicted), sum(hit) from e group by carrier, method, k having sum(n) >= 20
  union all
  select '羽田発着', case when hnd then '羽田' else '羽田以外' end, method, k, sum(n), sum(predicted), sum(hit) from e group by hnd, method, k
  union all
  select '出どころ', src, method, k, sum(n), sum(predicted), sum(hit) from e group by src, method, k
)
select g.kubun as "区分", g.val as "値", g.method as "方式", g.k as "何便先",
       g.n as "基準の数", g.pr as "予想を出した数", g.hit as "当たり",
       round(100.0 * g.hit / nullif(g.n, 0), 1) as "当たり率",
       round(100.0 * g.hit / nullif(g.pr, 0), 1) as "出したうちの当たり率",
       (select count(distinct day) from e) as "日数"
from g
order by case g.kubun when '全体' then 1 when '会社' then 2 when '羽田発着' then 3 else 4 end, g.val, g.k,
         case g.method when 'base' then 1 when 'learn' then 2 else 3 end
