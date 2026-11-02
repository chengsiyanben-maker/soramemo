-- 撮影地の情報（撮る人の画面の「この撮影地の情報」）：開いている時間・行き方・駐車場・決まり・問い合わせ先・出典・確認日
--   ・名前はアプリの撮影地（OPS_SPOTS）と同じにする。はじめは羽田の6地点（2026-11-02 に公式の案内で確認）
--   ・公式に書いていないことは書かない（null のまま。アプリは「公式の案内に記載なし」と出す）
--   ・誰でも読める。書けるのは運営者だけ（spot_info_put。is_admin で確かめる）。表に直接は書けない
--   ・月に1回見直す（checked_on を更新する）
create table if not exists public.spot_info (
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  name       text not null check (length(name) between 1 and 60),
  open_kind  text not null default 'unknown' check (open_kind in ('always', 'hours', 'unknown')),
  open_from  time,                       -- 日本時間。open_kind = 'hours' のとき
  open_to    time,
  open_note  text check (length(open_note) <= 200),
  access     text check (length(access) <= 300),
  parking    text check (length(parking) <= 300),
  rules      text[] not null default '{}' check (cardinality(rules) <= 12),
  contact    text check (length(contact) <= 200),
  sources    jsonb not null default '[]'::jsonb check (jsonb_typeof(sources) = 'array' and jsonb_array_length(sources) <= 8),
  checked_on date not null,
  updated_at timestamptz not null default now(),
  primary key (iata, name),
  check (open_kind <> 'hours' or (open_from is not null and open_to is not null))
);
alter table public.spot_info enable row level security;
revoke all on public.spot_info from public, anon, authenticated;
grant select on public.spot_info to anon, authenticated;
drop policy if exists spot_info_read on public.spot_info;
create policy spot_info_read on public.spot_info for select to anon, authenticated using (true);

-- 運営者が足す・直す（運営コンソールから）。名前が同じなら置き換える
create or replace function public.spot_info_put(p jsonb) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'admin only'; end if;
  insert into public.spot_info (iata, name, open_kind, open_from, open_to, open_note, access, parking, rules, contact, sources, checked_on, updated_at)
  values (p ->> 'iata', p ->> 'name', coalesce(p ->> 'open_kind', 'unknown'), (p ->> 'open_from')::time, (p ->> 'open_to')::time, p ->> 'open_note',
          p ->> 'access', p ->> 'parking', coalesce(array(select jsonb_array_elements_text(p -> 'rules')), '{}'), p ->> 'contact',
          coalesce(p -> 'sources', '[]'::jsonb), coalesce((p ->> 'checked_on')::date, (now() at time zone 'Asia/Tokyo')::date), now())
  on conflict (iata, name) do update set open_kind = excluded.open_kind, open_from = excluded.open_from, open_to = excluded.open_to, open_note = excluded.open_note,
    access = excluded.access, parking = excluded.parking, rules = excluded.rules, contact = excluded.contact, sources = excluded.sources,
    checked_on = excluded.checked_on, updated_at = now();
end
$$;
revoke all on function public.spot_info_put(jsonb) from public, anon;
grant execute on function public.spot_info_put(jsonb) to authenticated;

-- はじめの6地点（羽田）。2026-11-02 に公式の案内で確認
insert into public.spot_info (iata, name, open_kind, open_from, open_to, open_note, access, parking, rules, contact, sources, checked_on) values
('HND', '第1ターミナル 展望デッキ', 'hours', '06:30', '22:00', '6階の展望デッキ（南・北）と屋上。天候や保安上の理由で閉まることがあります',
  '京急線・東京モノレールの第1ターミナルの駅から、ターミナルの6階へ', '空港の有料駐車場',
  array['個人の趣味の撮影は申請なしでできます（収益化する配信などは事前の申請が必要）', '移動しながら・後ずさりしながらの撮影と、機材を持って走るのは禁止', 'ほかの利用者や職員を無断で撮らない', '三脚・脚立の決まりは公式の案内に記載がありません。現地の掲示に従ってください'],
  '羽田空港ターミナルインフォメーション 03-5757-8111',
  '[{"title":"羽田空港 展望デッキ","url":"https://tokyo-haneda.com/text/service/facilities/observation_deck.html"},{"title":"第1・第2ターミナル内での一般のお客さまの撮影について","url":"https://tokyo-haneda.com/text/information/2024/detail_00066.html"}]', '2026-11-02'),
('HND', '第2ターミナル 展望デッキ', 'hours', '06:30', '22:00', '5階。屋内の展望フロア「FLIGHT DECK TOKYO」は 5:00〜23:00。天候や保安上の理由で閉まることがあります',
  '京急線・東京モノレールの第2ターミナルの駅から、ターミナルの5階へ', '空港の有料駐車場',
  array['個人の趣味の撮影は申請なしでできます（収益化する配信などは事前の申請が必要）', '移動しながら・後ずさりしながらの撮影と、機材を持って走るのは禁止', 'ほかの利用者や職員を無断で撮らない', '三脚・脚立の決まりは公式の案内に記載がありません。現地の掲示に従ってください'],
  '羽田空港ターミナルインフォメーション 03-5757-8111',
  '[{"title":"羽田空港 展望デッキ","url":"https://tokyo-haneda.com/text/service/facilities/observation_deck.html"},{"title":"第1・第2ターミナル内での一般のお客さまの撮影について","url":"https://tokyo-haneda.com/text/information/2024/detail_00066.html"}]', '2026-11-02'),
('HND', '第3ターミナル 展望デッキ', 'always', null, null, '5階。天候や保安上の理由で閉まることがあります',
  '京急線・東京モノレールの第3ターミナル駅から、ターミナルの5階へ', '空港の有料駐車場',
  array['撮影の決まりは公式の案内に記載がありません。現地の掲示に従ってください'],
  '羽田空港ターミナルインフォメーション 03-5757-8111',
  '[{"title":"羽田空港 展望デッキ","url":"https://tokyo-haneda.com/text/service/facilities/observation_deck.html"}]', '2026-11-02'),
('HND', '城南島海浜公園', 'unknown', null, null, '公園の開園時間は公式の案内に記載がありません。駐車場は 7:30〜21:00',
  'JR大森駅東口などから京急バス 森32（城南島循環）「城南島四丁目」下車、歩いて3分',
  '第1駐車場 83台・第2駐車場 184台。7:30〜21:00、1時間300円（以降30分ごとに100円）',
  array['ドローン・ラジコンは禁止（海上公園条例）', '火気（たばこ・電子たばこを含む）はキャンプ場のほかでは禁止'],
  '城南島海浜公園 管理事務所 03-3799-6402（9:00〜17:00、水曜休み）',
  '[{"title":"城南島海浜公園（東京都立海上公園 南部地区）","url":"https://tokyo-south-seaside-parks.com/jonanjima/"},{"title":"城南島海浜公園 アクセス","url":"https://tokyo-south-seaside-parks.com/jonanjima-access/"}]', '2026-11-02'),
('HND', '京浜島つばさ公園', 'always', null, null, '24時間・無料',
  null, '有料駐車場あり',
  array['公園内は全面禁煙（電子たばこを含む）', 'ドローン・ラジコンは禁止（海上公園条例）'],
  '大井ふ頭中央海浜公園 管理事務所 03-3790-2378',
  '[{"title":"その他公園・緑道（東京都立海上公園 南部地区）","url":"https://tokyo-south-seaside-parks.com/other-parks/"}]', '2026-11-02'),
('HND', '浮島町公園', 'unknown', null, null, '開園時間は公式の案内に記載がありません',
  'JR川崎駅東口から臨港バス 川03（浮島バスターミナル行き）「浮島町公園入口」下車、歩いて2分', '公園の駐車場はありません',
  '{}',
  '川崎区役所道路公園センター 044-244-3206',
  '[{"title":"川崎市 浮島町公園","url":"https://www.city.kawasaki.jp/530/page/0000028068.html"},{"title":"かわさき観光 浮島町公園","url":"https://www.k-kankou.jp/spot/play/detail.html?CN=53743"}]', '2026-11-02')
on conflict (iata, name) do nothing;
