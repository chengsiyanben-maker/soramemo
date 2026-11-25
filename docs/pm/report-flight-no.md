# 記録帳の便名と flight_lookup（データ担当）

PM の指示 11/26 1時30分（checkin/flight-suggest #239 の依頼 ①②）。ブランチ data/flight-no（main f18b2eb から）。main と本番には入れていない。

作業の前の3行：
- 変えるファイル：移行 202（列1つ・決まり1つ・列の権限・関数1つ）・テスト t140・読むだけの SQL docs/pm/flight-no-check.sql・この報告・帳面
- 手順：manual_flights に flight_no（text・任意）を足し、RLS は今のまま本人の行だけにする。flight_history から日付＋便名で便を返す読むだけの関数 flight_lookup を、flight_facts と同じ権限で作る
- 確かめ方：t140（本人だけ書ける・形の決まり・引ける便・おかしな入力・全部読みしない・形が変わらない）と、記録帳と flight_history に関係するテスト

## 1. 作ったもの（移行 202 `20261126000202_flight_no_lookup.sql`）
1. **manual_flights.flight_no**（text・任意）
   - 形は flight_history・intl_flights と同じ `^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$`（例 JL123）。小文字や空白は入らないので、画面は大文字にそろえて送る（#239 の `x.no` はこの形）
   - RLS の方針は変えない（本人の行だけ読む・足す・消す・直す）。本人はあとから便名を直せる（直せる列は fare・seat・airline・price に flight_no を足した）
   - 記録帳は今までどおり印・路線・経営の数に入らない。退会では行ごと消える。バックアップ（to_jsonb）には自動で入る
2. **flight_lookup(p_date date, p_flight text) → jsonb**
   - 返す形：`{date, flight, rows:[{flight, dep, arr, std, sta, atd, ata, atd_src, ata_src, dep_delay, arr_delay, cancelled, diverted_to, aircraft, type, reg, also, src}]}`。rows は定刻の順で最大6（経由便など同じ便名で区間が2つの日は全部）
   - 取り先：flight_history（約400日）。flight_history にまだない日（今日・前の日など）は時刻表 flight_schedule（14日）から返し、`src` が `schedule`（登録記号はない）。両方にある日は flight_history だけ
   - 便名は flight_facts と同じく前の 0 をそろえ（JL0123＝JL123）、小文字・前後の空白も受け、共同運航の便名（also）でも見つける
   - おかしな入力（形の違う便名・空・null）は rows が空
   - 権限は flight_facts と同じ：anon・authenticated が呼べ、表そのものは読めない。返すのは公開の運航の事実だけで、利用者の記録は返さない
   - 読み方：その日の行だけを flight_history の主キー（svc_date, flight, dep）と flight_schedule の一意の索引（svc_date, flight, dep）の先頭で読む（1日 数千行まで）
- 影響：**チェックイン**（記録帳で便名を残す・過去の便を補う）。**経営は関係しない**
- 索引は増やさない。記録は消さない

## 2. 確かめた結果
- t140：33項目すべて OK（本人だけ便名つきで足せて直せる／形の違う便名は入らない／他人の行は読めず直せない／ログインなしは何もできない／日付＋便名で時刻・機体が返る／前の 0・小文字・共同運航・経由便・日付違い／時刻表に回る日／おかしな入力は空／表は直接読めない／全部読みしない／列は flight_no だけ・RLS と索引の数は同じ・関数は1つだけ増える／2回流しても壊れない／後の移行も流せる）
- 関係するテスト：t01・t02・t07・t08・t23・t24・t26・t27 通過（残りは下の 5 に）
- `node tools/migrations.mjs check`：番号の重なりなし

## 3. 反映の順
番号 202・テスト t140。定期の手入れ #246（201・t139）とは重ならず、どちらが先でもよい（main に別の移行が先に入ったら `node tools/migrations.mjs rebase`）。**列を足すだけの移行**なので、11/20 の決まりでは PM の自動の反映でよい（入れたあと本人に知らせる）。チェックインの #239 より先でも後でもよい（画面は列がなければ便名を外して入れる形）。反映のあと `docs/pm/flight-no-check.sql` を1回。

## 4. チェックイン担当への依頼
- 記録帳：`flight_no` は大文字・空白なしの形（JL123）で送る。形が違うと入らない（今の「列がなければ外して入れ直す」は、決まりに当たったときも外して入れ直すので、そのままでも行は入る）
- 過去の便：`sb.rpc("flight_lookup", { p_date: "2026-11-01", p_flight: "JL123" })`。`rows` が2つ以上なら区間を選んでもらう。`src` が `schedule` の行は実際の時刻が ODPT の分だけで、登録記号はない。400日より前の日は空（ファイル置き場に移っている）

## 5. 本人に決めてほしいこと
- なし（PM のおすすめで決めた2つ：本人があとから便名を直せるようにした／flight_history にない日は時刻表から返す。要らなければ外す）
- 三沢・岩国の terminals の行は、本人の OK まで足していない（指示どおり）
