-- 図鑑の1空港のデータ欄：供用開始の年と滑走路（11/10 1時 本人「すべてOK」・PM の指示。CLAUDE.md「図鑑のデータ」）
--   出典：国土交通省「空港一覧」（令和8年9月1日現在）の PDF（国管理・特定地方管理・地方管理・その他・共用の5つ）。
--         国交省サイトの利用ルールは公共データ利用規約（第1.0版、CC BY 4.0 互換）。和暦を西暦に直し、滑走路を数に直したので
--         画面には「出典：国土交通省『空港一覧』を加工して作成」と添える（国が作ったように見せない）
--   opened_year … 沿革のうち、空港として「供用開始」した最初の年（西暦）。画面では「開港」でなく「供用開始」と書く。
--                 滑走路やターミナルだけの供用開始は数えない。年のない行は前の行の年（波照間など、同じ年の続き）。
--                 空港としての供用開始の行がない空港（羽田・三沢・岩国）は null。
--                 「旧◯◯空港」「非公共用」「公共用として」の供用開始も最初の供用開始として数える（今の場所・形になった年とは限らない）
--   runways     … 今の滑走路の配列 [{name, length_m, width_m, note?}]。name は A・B など（1本だけの空港は null）。福岡の C・D は奈多地区のヘリポート（note に書く）
--   行があるのは国の一覧に載っていて番外編でない82空港。会社管理の4空港（成田・中部・関西・伊丹）・千歳（共用、一覧にない）・番外編は行を作らない
-- 読むのは誰でも（図鑑はログイン前のデモでも見る）。書くのは運営（service_role）だけ。
-- 影響：チェックイン（図鑑の1空港のデータ欄）だけ。エアライン経営は使わない。public.airports は変えない。

create table if not exists public.airport_facts (
  airport_id  integer  primary key references public.airports(id) on delete cascade,
  opened_year smallint check (opened_year between 1900 and 2100),
  runways     jsonb    not null default '[]'::jsonb check (
                jsonb_typeof(runways) = 'array' and jsonb_array_length(runways) <= 8
                and not jsonb_path_exists(runways, '$[*] ? (@.length_m.type() != "number" || @.width_m.type() != "number" || @.length_m < 1 || @.length_m > 6000 || @.width_m < 1 || @.width_m > 100)')
                and jsonb_array_length(runways) = jsonb_array_length(jsonb_path_query_array(runways, '$[*] ? (exists(@.length_m) && exists(@.width_m))'))),
  source      text     not null default 'mlit_airport_list' check (source in ('mlit_airport_list')),
  source_ref  text     not null check (char_length(source_ref) between 1 and 300),
  updated_at  timestamptz not null default now()
);
comment on table public.airport_facts is '図鑑の空港のデータ欄（供用開始の年・滑走路）。出典は国土交通省「空港一覧」。画面には「出典：国土交通省『空港一覧』を加工して作成」と出す';
comment on column public.airport_facts.opened_year is '空港として供用開始した最初の年（西暦）。「開港」とは書かない。行がない・null は出さない';

create or replace function public.airport_facts_touch() returns trigger language plpgsql set search_path = '' as $$
begin new.updated_at := now(); return new; end $$;
drop trigger if exists airport_facts_touch on public.airport_facts;
create trigger airport_facts_touch before update on public.airport_facts for each row execute function public.airport_facts_touch();

-- RLS：誰でも読める。書く権限は渡さない（service_role は RLS を通らない）
alter table public.airport_facts enable row level security;
drop policy if exists airport_facts_read on public.airport_facts;
create policy airport_facts_read on public.airport_facts for select to anon, authenticated using (true);
revoke all on public.airport_facts from anon, authenticated;
grant select on public.airport_facts to anon, authenticated;
grant all on public.airport_facts to service_role;

-- 中身（82行）。もう一度流しても同じになる。airports にない番号は入れない（手元の作り直しで落ちないように）
insert into public.airport_facts (airport_id, opened_year, runways, source_ref)
select v.id, v.y, v.rw::jsonb, 'https://www.mlit.go.jp/koku/content/' || v.pdf || '.pdf（令和8年9月1日現在）'
from (values
  (5, null, '[{"name":"A","length_m":3000,"width_m":60},{"name":"B","length_m":2500,"width_m":60},{"name":"C","length_m":3360,"width_m":60},{"name":"D","length_m":2500,"width_m":60}]', '002021263'),  -- 東京国際空港（空港としての供用開始の行がない）
  (6, 1988, '[{"name":"A","length_m":3000,"width_m":60},{"name":"B","length_m":3000,"width_m":60}]', '002021263'),  -- 新千歳空港
  (7, 1960, '[{"name":null,"length_m":2200,"width_m":45}]', '002021263'),  -- 稚内空港
  (8, 1961, '[{"name":null,"length_m":2500,"width_m":45}]', '002021263'),  -- 釧路空港
  (9, 1961, '[{"name":null,"length_m":3000,"width_m":45}]', '002021263'),  -- 函館空港
  (10, 1964, '[{"name":"A","length_m":1200,"width_m":45},{"name":"B","length_m":3000,"width_m":45}]', '002021263'),  -- 仙台空港
  (11, 1960, '[{"name":"A","length_m":1314,"width_m":45},{"name":"B","length_m":2500,"width_m":45}]', '002021263'),  -- 新潟空港
  (12, 1961, '[{"name":null,"length_m":3000,"width_m":60}]', '002021263'),  -- 広島空港
  (13, 1958, '[{"name":null,"length_m":2500,"width_m":60}]', '002021263'),  -- 高松空港
  (14, 1960, '[{"name":null,"length_m":2500,"width_m":45}]', '002021263'),  -- 松山空港
  (15, 1960, '[{"name":null,"length_m":2500,"width_m":45}]', '002021263'),  -- 高知空港
  (16, 1972, '[{"name":"A","length_m":2800,"width_m":60},{"name":"B","length_m":2500,"width_m":60},{"name":"C","length_m":35,"width_m":30,"note":"奈多地区（ヘリポート）"},{"name":"D","length_m":35,"width_m":30,"note":"奈多地区（ヘリポート）"}]', '002021263'),  -- 福岡空港
  (17, 1961, '[{"name":null,"length_m":2500,"width_m":60}]', '002021263'),  -- 北九州空港
  (18, 1960, '[{"name":null,"length_m":3000,"width_m":60}]', '002021263'),  -- 長崎空港
  (19, 1960, '[{"name":null,"length_m":3000,"width_m":45}]', '002021263'),  -- 熊本空港
  (20, 1957, '[{"name":null,"length_m":3000,"width_m":45}]', '002021263'),  -- 大分空港
  (21, 1957, '[{"name":null,"length_m":2500,"width_m":45}]', '002021263'),  -- 宮崎空港
  (22, 1958, '[{"name":null,"length_m":3000,"width_m":45}]', '002021263'),  -- 鹿児島空港
  (23, 1972, '[{"name":"A","length_m":3000,"width_m":45},{"name":"B","length_m":2700,"width_m":60}]', '002021263'),  -- 那覇空港
  (24, 1966, '[{"name":null,"length_m":2500,"width_m":60}]', '002021264'),  -- 旭川空港
  (25, 1964, '[{"name":null,"length_m":2500,"width_m":45}]', '002021264'),  -- 帯広空港
  (26, 1961, '[{"name":null,"length_m":2500,"width_m":60}]', '002021264'),  -- 秋田空港
  (27, 1964, '[{"name":null,"length_m":2000,"width_m":45}]', '002021264'),  -- 山形空港
  (28, 1966, '[{"name":null,"length_m":2500,"width_m":45}]', '002021264'),  -- 山口宇部空港
  (29, 1962, '[{"name":null,"length_m":1800,"width_m":45}]', '002021265'),  -- 利尻空港
  (31, 1974, '[{"name":null,"length_m":1500,"width_m":45}]', '002021265'),  -- 奥尻空港
  (32, 1965, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 中標津空港
  (33, 1966, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 紋別空港
  (34, 1963, '[{"name":null,"length_m":2500,"width_m":45}]', '002021265'),  -- 女満別空港
  (35, 1964, '[{"name":null,"length_m":3000,"width_m":60}]', '002021265'),  -- 青森空港
  (36, 1964, '[{"name":null,"length_m":2500,"width_m":45}]', '002021265'),  -- 花巻空港
  (37, 1998, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 大館能代空港
  (38, 1991, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 庄内空港
  (39, 1993, '[{"name":null,"length_m":2500,"width_m":60}]', '002021265'),  -- 福島空港
  (40, 1964, '[{"name":null,"length_m":1800,"width_m":45}]', '002021265'),  -- 大島空港
  (41, 1987, '[{"name":null,"length_m":800,"width_m":25}]', '002021265'),  -- 新島空港
  (42, 1992, '[{"name":null,"length_m":800,"width_m":25}]', '002021265'),  -- 神津島空港
  (43, 1966, '[{"name":null,"length_m":1200,"width_m":30}]', '002021265'),  -- 三宅島空港
  (44, 1962, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 八丈島空港
  (45, 1971, '[{"name":null,"length_m":890,"width_m":25}]', '002021265'),  -- 佐渡空港
  (46, 1963, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 富山空港
  (47, 2003, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 能登空港
  (49, 1965, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 松本空港
  (50, 2009, '[{"name":null,"length_m":2500,"width_m":60}]', '002021265'),  -- 静岡空港
  (51, 2006, '[{"name":null,"length_m":2500,"width_m":60}]', '002021265'),  -- 神戸空港
  (52, 1968, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 南紀白浜空港
  (53, 1967, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 鳥取空港
  (54, 1968, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 隠岐空港
  (55, 1966, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 出雲空港
  (56, 1993, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 石見空港
  (57, 1962, '[{"name":null,"length_m":3000,"width_m":45}]', '002021265'),  -- 岡山空港
  (58, 1998, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 佐賀空港
  (59, 1964, '[{"name":null,"length_m":1900,"width_m":45}]', '002021265'),  -- 対馬空港
  (61, 1963, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 福江空港
  (63, 1966, '[{"name":null,"length_m":1200,"width_m":30}]', '002021265'),  -- 壱岐空港
  (64, 1962, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 種子島空港
  (65, 1963, '[{"name":null,"length_m":1500,"width_m":45}]', '002021265'),  -- 屋久島空港
  (66, 1964, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 奄美空港
  (67, 1968, '[{"name":null,"length_m":1200,"width_m":30}]', '002021265'),  -- 喜界空港
  (68, 1962, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 徳之島空港
  (69, 1969, '[{"name":null,"length_m":1350,"width_m":45}]', '002021265'),  -- 沖永良部空港
  (70, 1976, '[{"name":null,"length_m":1200,"width_m":30}]', '002021265'),  -- 与論空港
  (71, 1978, '[{"name":null,"length_m":800,"width_m":25}]', '002021265'),  -- 粟国空港
  (72, 1972, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 久米島空港
  (74, 1972, '[{"name":null,"length_m":1500,"width_m":45}]', '002021265'),  -- 南大東空港
  (75, 1972, '[{"name":null,"length_m":1500,"width_m":45}]', '002021265'),  -- 北大東空港
  (77, 1972, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 宮古空港
  (78, 1979, '[{"name":null,"length_m":3000,"width_m":60}]', '002021265'),  -- 下地島空港
  (79, 1972, '[{"name":null,"length_m":1500,"width_m":45}]', '002021265'),  -- 多良間空港
  (80, 1972, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 石垣空港
  (82, 1972, '[{"name":null,"length_m":2000,"width_m":45}]', '002021265'),  -- 与那国空港
  (83, 2001, '[{"name":null,"length_m":800,"width_m":30}]', '002021266'),  -- 調布飛行場
  (84, 2005, '[{"name":null,"length_m":2740,"width_m":45}]', '002021266'),  -- 名古屋飛行場
  (85, 1994, '[{"name":null,"length_m":1200,"width_m":30}]', '002021266'),  -- 但馬飛行場
  (87, 2000, '[{"name":null,"length_m":1000,"width_m":30}]', '002021266'),  -- 天草飛行場
  (90, 1961, '[{"name":null,"length_m":1500,"width_m":45}]', '002021267'),  -- 札幌飛行場
  (92, null, '[{"name":null,"length_m":3050,"width_m":45}]', '002021267'),  -- 三沢飛行場（空港としての供用開始の行がない）
  (93, 2010, '[{"name":"A","length_m":2700,"width_m":45},{"name":"B","length_m":2700,"width_m":45}]', '002021267'),  -- 百里飛行場
  (94, 1961, '[{"name":null,"length_m":2700,"width_m":45}]', '002021267'),  -- 小松飛行場
  (95, 1969, '[{"name":null,"length_m":2500,"width_m":45}]', '002021267'),  -- 美保飛行場
  (96, null, '[{"name":null,"length_m":2440,"width_m":60}]', '002021267'),  -- 岩国飛行場（空港としての供用開始の行がない）
  (97, 1962, '[{"name":null,"length_m":2500,"width_m":45}]', '002021267')   -- 徳島飛行場
) as v(id, y, rw, pdf)
where exists (select 1 from public.airports a where a.id = v.id)
on conflict (airport_id) do update set opened_year = excluded.opened_year, runways = excluded.runways, source_ref = excluded.source_ref;
