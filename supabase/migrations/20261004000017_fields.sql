-- 番外編の3つ目「飛行場」：定期便のない公共用の空港と、民間の飛行場（小型機・農道空港など）
-- 番外編かどうかを extra_kind で持つ（mil＝自衛隊・米軍の飛行場、glider＝滑空場、field＝飛行場）。checkin 関数はこの欄で番外編を見分ける。
-- 位置は国土交通省の空港一覧（既存の行）と OurAirports（パブリックドメイン）。千歳空港（id 91、RJCJ）は千歳基地（1001）と同じ場所なので番外編に入れない。
alter table public.airports add column if not exists extra_kind text check (extra_kind in ('mil', 'glider', 'field'));
update public.airports set extra_kind = 'mil'    where category = 'military';
update public.airports set extra_kind = 'glider' where category = 'glider';
-- 定期便のない公共用の空港（すでに表にあり、ゲームの対象外だったもの）
update public.airports set extra_kind = 'field' where id in (30, 48, 60, 62, 73, 76, 81, 86, 88, 89) and not game_target;
-- 民間の飛行場
insert into public.airports (id, name, icao, iata, category, prefecture, lat, lon, radius_m, rare, game_target, extra_kind) values
  (3001, '大樹町多目的航空公園', null, null, '民間の飛行場', '北海道', 42.499971, 143.441759, 800, false, false, 'field'),
  (3002, 'ホンダエアポート', null, null, '民間の飛行場', '埼玉県', 35.97633, 139.524125, 800, false, false, 'field'),
  (3003, '大利根飛行場', null, null, '民間の飛行場', '茨城県', 35.85937, 140.241219, 800, false, false, 'field'),
  (3004, '竜ヶ崎飛行場', null, null, '民間の飛行場', '茨城県', 35.906276, 140.242152, 800, false, false, 'field'),
  (3005, '福島スカイパーク', null, null, '民間の飛行場', '福島県', 37.82322, 140.38767, 800, false, false, 'field'),
  (3006, '笠岡ふれあい空港', null, null, '民間の飛行場', '岡山県', 34.476022, 133.488961, 800, false, false, 'field'),
  (3007, '飛騨エアパーク', null, null, '民間の飛行場', '岐阜県', 36.17939, 137.313573, 800, false, false, 'field'),
  (3008, 'スカイポート美唄', null, null, '民間の飛行場', '北海道', 43.38992, 141.85892, 800, false, false, 'field'),
  (3009, 'スカイポート北見', null, null, '民間の飛行場', '北海道', 43.77998, 143.73064, 800, false, false, 'field'),
  (3010, 'アップルポート余市', null, null, '民間の飛行場', '北海道', 43.17089, 140.80753, 800, false, false, 'field'),
  (3011, '新得農道空港', null, null, '民間の飛行場', '北海道', 43.07622, 142.87658, 800, false, false, 'field'),
  (3012, '滝川スカイパーク', null, null, '民間の飛行場', '北海道', 43.549349, 141.894103, 800, false, false, 'field'),
  (3013, '別海フライトパーク', null, null, '民間の飛行場', '北海道', 43.47484, 144.78309, 800, false, false, 'field'),
  (3014, '美幌エアパーク', null, null, '民間の飛行場', '北海道', 43.81589, 144.07879, 800, false, false, 'field'),
  (3015, '上士幌航空公園', null, null, '民間の飛行場', '北海道', 43.244787, 143.277673, 800, false, false, 'field'),
  (3016, '厚真スカイパーク', null, null, '民間の飛行場', '北海道', 42.64362, 141.87865, 800, false, false, 'field'),
  (3017, '鹿部飛行場', null, null, '民間の飛行場', '北海道', 42.045033, 140.793293, 800, false, false, 'field'),
  (3018, '白鷹エアロパーク', null, null, '民間の飛行場', '山形県', 38.16359, 140.0619, 800, false, false, 'field'),
  (3019, '諏訪之瀬島飛行場', null, null, '民間の飛行場', '鹿児島県', 29.60624, 129.70221, 800, false, false, 'field'),
  (3020, '薩摩硫黄島飛行場', null, null, '民間の飛行場', '鹿児島県', 30.784722, 130.270556, 800, false, false, 'field')
on conflict (id) do nothing;
create index if not exists airports_extra on public.airports (extra_kind) where extra_kind is not null;
