-- 図鑑の見方の帯を新しい3つ（地方別・地図・行った順）にする前に、今の保存の数を見る（読むだけ・1つの表で出る）
-- 使い方：Supabase の SQL Editor に貼って Run。表 user_view_prefs は1人1行なので軽い（索引も一時ファイルも要らない大きさ）
-- 中身の形（fmt 2）：{} ＝全部乗せのまま／{ base:構成, layout:{ off:{ book:[隠した見方], … }, order:{…}, tabs:[…] } }
-- 図鑑の見方の id：map＝地図、signs＝案内標、tiles＝タイル、chron＝年代記、region＝地方
-- ※ ブラウザの自動翻訳は切って貼る。20秒で止まる（この画面の中だけの設定）
set statement_timeout = '20s';
with p as (
  select fmt, prefs,
         prefs->>'base' as base,
         case when jsonb_typeof(prefs->'layout'->'off'->'book') = 'array' then prefs->'layout'->'off'->'book' end as off_book,
         prefs->'layout'->'order'->'book' as order_book
  from public.user_view_prefs
)
select '1 行の数（全部）' as what, count(*)::text as n from p
union all select '2 fmt ごと', coalesce(string_agg(fmt::text || '：' || c, '、' order by fmt), 'なし') from (select fmt, count(*) c from p group by fmt) x
union all select '3 全部乗せのまま（{}）', count(*)::text from p where prefs = '{}'::jsonb
union all select '4 構成（base）ごと（全部乗せのまま以外）', coalesce(string_agg(coalesce(base, '（なし）') || '：' || c, '、' order by base), 'なし') from (select base, count(*) c from p where prefs <> '{}'::jsonb group by base) x
union all select '5 図鑑の見方を自分で変えた人（off.book がある）', count(*)::text from p where off_book is not null
union all select '6 隠している見方ごとの人数', coalesce(string_agg(v || '：' || c, '、' order by v), 'なし') from (select v, count(*) c from p, jsonb_array_elements_text(off_book) v group by v) x
union all select '7 地図だけ出している人（地方別がいつも出るので変わらない）', count(*)::text from p where off_book @> '["signs","tiles","chron","region"]'::jsonb
union all select '8 年代記を隠していない人（行った順が出る）', count(*)::text from p where off_book is not null and not off_book ? 'chron'
union all select '9 図鑑の見方の並び（order.book）を持っている人', count(*)::text from p where order_book is not null
union all select '10 知らない id（5つ以外）', coalesce(string_agg(distinct v, '、'), 'なし') from p, jsonb_array_elements_text(off_book) v where v not in ('map','signs','tiles','chron','region');
