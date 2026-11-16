# 見落としの片付け（データ担当・11/16）

PM の指示（11/16 14時10分、本人「OK」・docs/pm/board/overlooked-1116.md）。ブランチ data/redo-1116（main 2ae2e1f から）→ main 向けの下書き PR。本番には入れていない。

## 作ったもの

### 1. 定期の手入れ6本を今の main の次の番号に付け直して1本に
書いた順のまま、最後に 11/16 の中身（関数の lock_timeout）。中身は前の PR と同じ（コミットをそのまま取り込んだ）。

| もとの PR | もとの番号・テスト | 新しい番号・テスト | 中身 |
|---|---|---|---|
| #18 | 153・t93 | **173**・t112 | 毎日の処理に時間の上限・BRIN 索引・自動掃除を早める・週の点検の SQL |
| #33 | 155・t95 | **174**・t113 | 古い記録を移す日の候補を索引で1件ずつ引く |
| #56 | 158・t98 | **175**・t114 | 古い記録を移す処理を軽く・安全に |
| #58 | 161・t101 | **176**・t115 | 毎晩・3時間ごとの記録の処理を軽く |
| #70 | 162・t102 | **177**・t116 | 到着空港の部分索引・毎晩の3つの仕事に上限 |
| #103 | 170・t109 | **178**・t117 | 裏の処理が呼ぶ書く関数12個に lock_timeout・ops-log-cleanup に上限 |

- 171（data/foreign-collect）・172（経営 keiei/redo-1116 の #21 の入れ直し）とテスト t110・t111 はほかのブランチが使っているので飛ばした。170 は空き番になる（#103 を閉じれば問題なし）
- 確かめたこと：main の 151〜169 のどれも、この6本が書き直す関数・仕事（cold_*・archive_airport_daily・airport_tracks_put・rwy_learn_points・archive-cleanup など11の仕事）を書き直していない（＝古い中身で新しい直しを戻してしまうことはない）。168・169 の flight_alerts_put・world_status_put は 178 が設定を足すだけ（中身は変えない）
- テストの直し：t113（もと t95）は 175 で cold_rows が json を返すようになったのを知らずに jsonb の関数で数えていたので、どちらでも通る形にした。t116・t117 のファイル名の参照を新しい番号に

### 2. ODPT のデータの時刻（dc:date）— 移行 179・テスト t118
- 表 odpt_feed_dates（種類と航空会社ごとに1行：feed＝FlightInformationDeparture:JAL など・dc_date・fetched_at・n）。上書きだけで行は増えない。RLS：誰でも select、書くのは関数 odpt_feed_date_put（service_role だけ・lock_timeout 5s。dc:date は前より古くしない）
- 取り込みの関数 odpt-status（4分ごとの回）・timetable-sync・schedule-sync が、取るたびに残す（失敗しても取り込みは止めない）
- airport-now は返す flights に dc_date（その空港の便のいちばん新しい dc:date、なければ null）を足した（足しただけで、ほかの形は同じ）
- 影響：チェックイン（出典の表示に使える。今の画面は変わらない）。経営は使わない
- **チェックイン担当への依頼**：ODPT の便を出す所（空港ページ・運用タブの案内板など）に「ODPT のデータ ○時○分 時点」を出す。空港ページは airport-now の flights.dc_date、そのほかは odpt_feed_dates を select（FlightInformationDeparture:JAL などのいちばん新しいもの）。null なら出さない。画面案はデザイン担当から

### 3. OpenSky の置き換え — 移行 180・テスト t119（できたところまで）
- 調べた結果：**今 OpenSky に問い合わせているのは毎晩の照合（verify-flights・tools/verify_flights.ts の /flights/arrival と /tracks/all）だけ**だった。airport-traffic は「OpenSky は使わない」と書いてあり、traffic.ts・track.ts は OpenSky の形を名前に残しているだけ（問い合わせない）。daily-archive は照合で航跡が取れなかった便に全機の記録から航跡を付ける側
- 作ったもの：読む関数 verify_arrivals(到着の ICAO, 始め, 終わり)。全機の記録（reg_legs。adsb.lol・ODbL）から OpenSky の /flights/arrival と同じ形の一覧を返す（登録記号を icao24 の代わりに・出発は ICAO に直す・窓は2日まで・service_role だけ）。照合の決まり（verify.ts の match）は変えない
- 切り替え：秘密の設定 VERIFY_SOURCE=adsb のときだけ使う（Supabase の関数の秘密の設定、または GitHub のリポジトリの変数 VERIFY_SOURCE）。**設定しなければ今までどおり OpenSky**。adsb のときは OpenSky の鍵が要らず、航跡は daily-archive が付ける
- 限り：reg_legs は4つの円の中で見えた機体だけ。出発か到着が円の外の便は「到着記録なし」になる（そのときは今までどおり航空会社の運航情報で確かめる）。OpenSky より確かめられる便が減るかは、redo-1116-check.sql の ①② で見積もれる
- 残り（本人が「置き換え」に決めたら）：①の結果を見て切り替える／照合を GitHub から Supabase の pg_cron に戻す（OpenSky が届かないので GitHub に置いていた）／ストアの出典の一覧から OpenSky を外す

## 確かめた結果
- 新しいテスト t118（19項目）・t119（11項目）、付け直した t112〜t117：すべて通過
- 関数のテスト（deno test supabase/tests/）262本 通過（odpt_date_test 4本・verify_source_test 3本を足した）。型の確認（deno check）通過
- SQL のテスト全部（119本）：通過。1回目の通しで t108 だけ落ち（下の日付の件）、直したあと流し直して通過。t118・t119 は別に流して通過
- 番号の重なりなし（node tools/migrations.mjs check）
- t108（データ担当の海外の止まり具合のテスト）が **main でも落ちていた**：日付が 11/15 のとき前提の書き方だった。今日の便を1つ足して、日付に左右されないように直した
- redo-1116-check.sql は手元の Postgres（PGlite）で通ることを確かめた

## 本人に決めてほしいこと
1. 「反映して」の前に：古い PR **#18・#33・#56・#58・#70・#103 は入れ直したので閉じてよい**（このブランチが代わり）
2. ODPT のデータの時刻：このまま反映してよいか（画面はチェックイン担当が出す）
3. OpenSky：redo-1116-check.sql の ①② を流して貼ってもらい、adsb に切り替えるか（切り替えは設定1つ。コードの直しは要らない）
4. 反映するときの順：経営の 172（#21 の入れ直し）とこのブランチの 173〜180 は別の関数なので、どちらが先でもよい。171（海外の便）も同じ
