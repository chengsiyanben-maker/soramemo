-- 番外編の新しい種類「ヘリポート」（extra_kind = 'heli'）。11/11 23時42分 本人「ヘリポートも入れる」（近くの空港の並び）、PM の指示 11/11 23時45分
--   中身：国土交通省「公共用ヘリポート一覧」（令和8年9月1日現在）の公共用ヘリポート12か所。名前・所在地（都道府県）はその一覧から。
--         https://www.mlit.go.jp/koku/content/002021268.pdf （公共データ利用規約 第1.0版。名前の「ヘリポート」は付け足したので「加工して作成」）
--   位置：一覧には緯度経度がないので OurAirports（パブリックドメイン）の位置。所在地の住所と食い違いがないことは手で見た（報告の 3）
--   入れないもの：非公共用ヘリポート83か所（県警・病院・庁舎の屋上など。一般の人が近づく所ではないので）、自衛隊のヘリポート（基地は出さない決まり）。
--   ほかの番外編と同じく、全国制覇・86 の数には数えない。民間空港より優先度が低く、フライトにはしない（checkin 関数は extra_kind で番外編を見分ける）。
--   【注意】checkin 関数は extra_kind が空でない行を全部「番外編の印」にする。ヘリポートで印を押せるようにするかは本人の決定待ち。
--           押せないことにするなら、反映の前にチェックイン担当が checkin 関数の読み出しから 'heli' を外す（報告の 5）。
-- RLS：airports は今のまま（誰でも select・anon と authenticated は書けない）。airport_yomi も今のまま（誰でも select・書くのは service_role だけ）。
-- 影響：チェックイン（近くの空港の並び・番外編・図鑑の索引）。エアライン経営は使わない（経営の空港は game_target と iata で引くので、iata のないこの行は出ない）。

alter table public.airports drop constraint if exists airports_extra_kind_check;
alter table public.airports add constraint airports_extra_kind_check check (extra_kind in ('mil', 'glider', 'field', 'secret', 'heli'));

-- 印の半径：屋上でなく地上の施設なので 600m。広島ヘリポートは元の広島空港（滑走路 1,800m）なので 800m
insert into public.airports (id, name, icao, iata, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind) values
  (5001, '豊富ヘリポート',       null,   null, 'heliport', '北海道',   45.100430, 141.758930, 600, false, false, 'heli'),
  (5002, '米沢ヘリポート',       null,   null, 'heliport', '山形県',   37.912950, 140.166100, 600, false, false, 'heli'),
  (5003, '栃木ヘリポート',       null,   null, 'heliport', '栃木県',   36.559910, 140.006070, 600, false, false, 'heli'),
  (5004, '群馬ヘリポート',       null,   null, 'heliport', '群馬県',   36.317904, 139.106752, 600, false, false, 'heli'),
  (5005, '高崎ヘリポート',       null,   null, 'heliport', '群馬県',   36.324990, 138.993520, 600, false, false, 'heli'),
  (5006, '東京ヘリポート',       'RJTI', null, 'heliport', '東京都',   35.635924, 139.839475, 600, false, false, 'heli'),
  (5007, '静岡ヘリポート',       null,   null, 'heliport', '静岡県',   35.024410, 138.408770, 600, false, false, 'heli'),
  (5008, '若狭ヘリポート',       null,   null, 'heliport', '福井県',   35.490338, 135.785530, 600, false, false, 'heli'),
  (5009, '津市伊勢湾ヘリポート', null,   null, 'heliport', '三重県',   34.672773, 136.555810, 600, false, false, 'heli'),
  (5010, '奈良県ヘリポート',     null,   null, 'heliport', '奈良県',   34.656210, 135.884610, 600, false, false, 'heli'),
  (5011, '広島ヘリポート',       'RJBH', null, 'heliport', '広島県',   34.371451, 132.417666, 800, false, false, 'heli'),
  (5012, '枕崎ヘリポート',       null,   null, 'heliport', '鹿児島県', 31.268255, 130.357706, 600, false, false, 'heli')
on conflict (id) do nothing;

-- 図鑑の索引の読み（airports の全行に1行の決まり。手で付けた読み）
insert into public.airport_yomi (airport_id, yomi, index_yomi, alt_yomi) values
  (5001, 'とよとみへりぽーと', 'とよとみ', '{}'),
  (5002, 'よねざわへりぽーと', 'よねざわ', '{}'),
  (5003, 'とちぎへりぽーと', 'とちぎ', '{}'),
  (5004, 'ぐんまへりぽーと', 'ぐんま', '{}'),
  (5005, 'たかさきへりぽーと', 'たかさき', '{}'),
  (5006, 'とうきょうへりぽーと', 'とうきょう', array['しんきば']),
  (5007, 'しずおかへりぽーと', 'しずおか', '{}'),
  (5008, 'わかさへりぽーと', 'わかさ', '{}'),
  (5009, 'つしいせわんへりぽーと', 'つしいせわん', array['つ']),
  (5010, 'ならけんへりぽーと', 'ならけん', array['なら']),
  (5011, 'ひろしまへりぽーと', 'ひろしま', array['ひろしまにし']),
  (5012, 'まくらざきへりぽーと', 'まくらざき', '{}')
on conflict (airport_id) do update set yomi = excluded.yomi, index_yomi = excluded.index_yomi, alt_yomi = excluded.alt_yomi;
