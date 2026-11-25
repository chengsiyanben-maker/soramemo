# データ担当の帳面

## いま持っている仕事
- **羽田・成田はいろいろなデータを細かく取る（PM の指示 11/25 18時50分。手動の呼び出しで data/hnd-nrt-more を指定された）**：ブランチ data/hnd-nrt-more（data/hnd-nrt-priority #227 の上）→ **下書き PR #230**（11/25 22時半 #227 が main に入ったので、向き先を main に直し main を取り込んだ（24407b4）。deno test 332本・t136・t137 通過。移行199 は main と重ならない）。報告 docs/pm/report-hnd-nrt-more.md（候補ごとの規約の一覧）。読むだけの SQL docs/pm/hnd-nrt-more-check.sql（5つ）。**移行199・テスト t137 を使った**
  - 規約：adsb.lol（ODbL）・ODPT（基本ライセンス・公開しない）・aviationweather.gov は「よい」。アメダスは商用可・出典要だが JSON の自動取得の頻度は書いていない（本人に）。空港会社のサイト（サイトポリシーは読めなかった）・SWIM の NOTAM（二次利用の条件が資料にない）・雷（有料）は「分からない」で使わない。FR24 は使わない
  - 移行199：ground_watch（見張り・6時間・毎日の cleanup 30秒）・ground_moves（着陸→スポット・動き出し→離陸・地上の時間。ずっと残す）・flight_changes とトリガー（羽田・成田の便のゲート・機材・状態・見込みの時刻5分以上）。RLS ON・方針なし
  - airport-traffic：recordGround（_shared/ground_moves.ts。止まっている機体は10分に1回・動いている機体は2分に1回か状態が変わったときだけ書く）。adsb.lol の回数は同じ
  - 確かめ：deno test 327本（ground_moves_test 5本）・deno check・t137・SQL のテスト全部 通過・migrations.mjs check 189件
  - 次の回の候補：進入の線・待機を rwy_samples.pts から数える／緊急の squawk だけ残す表／遅れの理由の文を flight_changes に（odpt-status の変更）／ターミナルの列
  - 本人待ち：反映（#227 のあと）・アメダス・空港会社のサイト・SWIM の規約・量（1年で百万行前後→半年で cold-archive の案）
- **羽田・成田を優先して取る＋滑走路の予想の当たり具合（PM の指示 11/25 18時45分。11/25 水曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/hnd-nrt-priority（main 4354656 から）→ **PR #227（11/25 22時39分 main に入った。本番の移行198 は PM の反映の流れで確かめる）**。報告 docs/pm/report-hnd-nrt-priority.md。本人用の読むだけの SQL docs/pm/hnd-nrt-priority-check.sql（7つ）。**移行198・テスト t136 を使った**
  - 調べた結果：羽田・成田はもともと同じ東の円で30秒ごと・track_points・ops_log・rwy_samples もそろっていた。違いは学習の半径だけ（羽田60・成田40海里）
  - airport-traffic：記録の処理だけ成田の学習を60海里に（LEARN_NM・LEARN_PLANES）。画面は40海里のまま。adsb.lol の回数は同じ（1日約8,640回）
  - 移行198：wx_taf（原文）・wx_taf_hours（毎時の風・TEMPO/PROB・est_mode＝画面と同じ推定）。RLS ON・方針なし。cron wx-hnd-nrt（毎時41分・30秒の上限）
  - wx-archive：7分の回でも TAF。41分の回（?part=hnt）で TAF・METAR 6時間・過去の TAF のさかのぼり（置き場 tafback:RJTT/RJAA、3時間ずつ8回＝1日ぶん、10/15 まで約41時間）。過去の TAF は date の指定で取れると確かめた
  - 規約：aviationweather.gov はパブリックドメイン・1分100回まで・User-Agent（API の案内で確かめた）
  - 確かめ：deno test 322本（taf_test 5本）・deno check・lint は前からの4件・t136・SQL のテスト全部 通過・migrations.mjs check 188件。t135 の「最後の移行」の確かめを「197番」に直した
  - 本人待ち（PM のおすすめで可）：反映・羽田の追い風の上限と粘りの合わせ込み（結果のあと。推定の式は画面と共通なのでチェックイン担当と）・成田の画面の半径を60にするか
- **羽田・成田を優先して取る＋当たり具合【別の回の案。#227 と同じ仕事】（PM の指示 11/25 18時45分。11/25 水曜に定期の回として呼ばれ、積んであったこの指示をした。同じ時刻に別のデータ担当の回が data/hnd-nrt-priority・PR #227 を先に仕上げていたのを、push のときに知った）**：ブランチ data/hnd-nrt-priority-b（main 4354656 から）→ **下書き PR #228**。報告 docs/pm/report-hnd-nrt-priority-b.md。本人用の読むだけの SQL docs/pm/hnd-nrt-priority-b-check.sql。**#227 と同じく移行198・テスト t136 を使っているので、両方は入れない**
  - おすすめ：#227 を本筋にし #228 は閉じる。#227 にない2つ（A：東の円が断られた回は同じ円を取り直さず新千歳・那覇を休む recordStep／B：追い風の上限×粘り×戻り幅の30組を切り替えを待つ動きで数える関数 rwy_wx_eval）は、PM が要ると決めたら #227 のあとに移行199・t137 で足す
  - 確かめ：t136 33項目・deno test 327本（taf_test 5本）・deno check・migrations.mjs check 188件・模擬90日で rwy_wx_eval 約4.3秒（PGlite）
  - 次の仕事 data/hnd-nrt-more（11/25 18時50分）は、#227 の回が続けて受け持っている見込みなので、この回では始めていない（重ねないため）
  - 11/25 18時58分にもう一度呼ばれた（同じ指示・data/hnd-nrt-priority で、と指定）：#227 がその名前のブランチで仕上がっているので、手元で確かめただけ（migrations.mjs check 188件・t136・t135・deno test 322本・deno check 通過）。#227 の回がまだ動いているかもしれないので、そのブランチには push していない
- **印を押すときのロードを短く（PM の最優先の指示 11/25 17時45分。11/25 水曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/stamp-fast（main 4354656 から）→ **下書き PR #225**。報告 docs/pm/report-stamp-fast.md。本人用の読むだけの SQL docs/pm/stamp-fast-check.sql。**移行・テスト番号は使っていない（表を変えていない）**
  - 調べた結果：データベース側に重い処理はない（checkins にトリガーなし・集計は保存の中で走らない・索引は足りている）。重いのは関数 checkin の待ち方（毎回 aviationweather.gov へ最大2.5秒・往復約9回が順番）
  - 直し：天気は 記憶 → edge_cache（now:wx）→ wx_obs（75分まで）で決め、決まらなければ空で記録して返したあとに書き足す（_shared/checkin_wx.ts）。前半の読み5つを同時に、ボーナスとフライトも同時に。ログ checkin_ms（read・total・wx）
  - 関数の名前・送る中身・戻り値・記録の中身・RLS は同じ
  - 確かめ：deno test 322本（新しい checkin_wx_test 5本）・deno check・deno lint・migrations.mjs check 187件
  - 本人待ち（PM のおすすめで可）：記録のない空港は天気が数秒あとに入る。さらに1往復減らすなら auth.getUser → getClaims（ログインの扱いの変更なので本人の OK が要る）
- **見直し 2回目のデータの分：特別塗装機の知らせを1便で1つに・夜の静かな時間（PM の指示 11/25 5時10分・report-sweep-1125.md の4番。11/25 水曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/sweep-1125（main 04d22af から）→ **PR #216（11/25 8時16分 main に入った。本番の移行197 は PM の反映の流れで確かめる。今いる購読ははじめ ON なので、チェックインの「夜は知らせない」の行が入るまで夜は止まる）**。報告 docs/pm/report-sweep-1125-data.md。**移行197・テスト t135 を使った**
  - tag はどれも `sp-便名`（_shared/livery_note.ts の liveryTag。予定は機体が分からないので便名だけ。便名がなければ `sp-登録記号`）。renotify つき。前の `plan-`・`spr-`・`sp-登録記号` はやめた
  - 移行197：push_subs.quiet_night（はじめ true）・livery_plans.quiet_push_at。夜（23〜7時）は特別塗装機・撮影・運用の知らせを quiet_night の人に送らない（awake()）。乗る便・空港の遅れは止めない。ga は ga_quiet のまま。夜に見つかった予定は7時すぎに静かな時間の人へ1回（odpt-status）
  - 運用の知らせは spot_notified の `ops-空港@分` で「前の知らせから60分」
  - push-subscribe：quiet_night を受け付ける（来なければ前の値のまま）
  - 確かめ：t135 21項目・deno test 317本・deno check・migrations.mjs check 187件
  - 本人待ち（PM のおすすめで可）：はじめ ON は今いる人にもすぐ効く（画面の行と一緒に入れるのがおすすめ）。通知の扱いの変更なので入れる前に本人に一言
- **見直し B の回のデータの分（PM の指示 11/24 14時30分・report-sweep-all-b.md の 1・2・7①・8番。11/24 火曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/sweep-all（main 8744f86 から）→ **PR #206（11/24 17時22分 main に入った。本番の移行196 は PM の反映の流れで確かめる。sweep-all-check.sql の 2〜4 を反映のあとに）**。報告 docs/pm/report-sweep-all-data.md。確かめの SQL docs/pm/sweep-all-check.sql。**移行196・テスト t134 を使った**
  - 移行196：airport_board の next_arr・next_dep を「先の便12便（3時間先まで）＋過ぎた便2便（20分前まで）」に。便を読む幅を「今日0時の20時間前から」に（前は8日6時間前から）。hours の ref はまとめ表 airport_hour_bad（空港・日・時の遅れ＋欠航）から、まとめがない日だけ便の表から。hours・bad は前と同じ
  - rwy_learned はまとめ表 rwy_learned_days ＋今日の分（rwy_samples）。幅は「今日を入れて p_days 日（暦の日）」。記録がファイル置き場に移った日は前のまとめを残す。毎時の仕事 board-bad-roll（7分）・rwy-learned-roll（37分）、前の日と前の前の日をまとめ直す、上限1分
  - user_pins（本人だけ・RLS・退会で消える）と rpc my_pins()・my_pins_put(p_pins, p_spot, p_rev)。20空港・4KB まで、形はトリガーで確かめる
  - 通知：_shared/push_text.ts の tidyPush を送る直前に通す（題の「そらメモ：」を外す・推定は推定のあった行の最後に「（推定）」1つ）。画面の文は変えない。spot_push.ts（撮る人用）は触らず送る直前でそろう
  - 確かめた結果：t134 56項目 OK・t22（まとめを作る1行を足した）ほか関係する SQL のテスト12本 通過・deno test 311本・deno check 通過・migrations.mjs check 186件・速さの目安（PGlite）airport_board 108→64ms・rwy_learned 41→16ms
  - 11/24 2回目の呼び出し（同じ指示）：main の #201（撮る人用のテストだけ）を取り込み 5c4c05d。t134・deno test 311本 もう一度通過。中身の変更なし
  - 本人待ち（PM のおすすめで可）：反映。user_pins は新しい利用者のデータなので「個人情報の扱いを変える」に当たるかを PM が判断（おすすめ：入れる前に本人に一言）。数字（12便・2便・毎時）
- **運用の「今日の遅れ」の bad と海外の塗装機の知らせの言い方（PM の指示 11/24 4時15分・sweep-1124。11/24 火曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/board-bad（main 32ea294 から）→ **PR #197（11/24 7時27分 main に入った。本番の移行195・airport-traffic の出し直しは PM の反映の流れで確かめる）**。報告 docs/pm/report-board-bad.md。**移行195・テスト t133 を使った**
  - 移行195 airport_board_bad：airport_board に今日（日本時間）の15分以上の遅れ・欠航の便 bad（チェックイン担当の下書き docs/pm/delay-filter-board-bad.sql のまま・lock_timeout 5秒）。表・列・RLS・権限は同じ。影響はチェックイン（#182 の絞り込み）だけ。経営は関係しない
  - inboundMessage：「…に向かっています。着くのは10時42分ごろ（推定）。」（推定は1回・見込みを外す・便名がなければ会社名だけ。jaTime を足した）
  - 確かめた結果：t133 24項目 OK・t22/t51/t105 通過・migrations.mjs check 185件で重なりなし・deno test 306本・deno check 通過
  - 本人待ち（PM のおすすめで可）：反映（PM が自動で入れてよい区分）。bad も hours と同じく定刻の出発が6時間後までの便しか見ない（今日の夜遅くの便は近づくまで数に入らない）。画面の「今日」の言い方でよいか
- **定期の手入れ 11/23（月曜の定期の回・PM の指示なし）**：ブランチ maint/2026-11-23（main 9a79def から）→ **PR #188（11/23 16時29分 main に入った。本番の移行194 は PM の反映の流れで確かめる）**。報告 docs/pm/maint/2026-11-23-report.md。確かめの SQL docs/pm/maint/2026-11-23-check.sql。**移行194・テスト t132 を使った**
  - 点検の結果がまだないので、模擬のデータベース（移行184本）で関数367個の where の列と索引の先頭の列を突き合わせ、全部読みを洗い出した（約130件、ほとんど小さな表）。効く3つを直した
  - ① airport_day：rwy_samples・ga_events の「(at の日本時間)::date = 日」を時刻の幅に（羽田は400日分を毎回全部読んでいた）② flights_track_todo_dep：flights (dep_at desc) where track is null and flight_no is not null（毎晩の flights_track_todo・archive_user_flights）③ rot_predict：livery_plans の日付を時刻の幅に（pg_get_functiondef の1か所だけ置き換え、1か所でなければ止まる）
  - 影響：チェックイン（空港ページ・便の航跡）と運用予想が速くなるだけ。経営は関係しない。表・列・RLS・権限は同じ
  - 確かめた結果：t132 18項目 OK・t27/t42/t90/t92/t106/t117/t122/t126/t128 通過・migrations.mjs check 184件で重なりなし
  - 本人待ち（PM のおすすめで可）：反映（索引を足す・関数の中身は同じ値なので、入れたあとに知らせる区分）・check.sql を反映の前と次の日に
  - 次の候補：atc_msgs(feeder) に索引がない（atc_my_feeders が1台ごとに全部読む）。管制の交信を使い始めるなら足す
- **AAL176（N791AN）とアメリカン航空のワンワールド塗装（11/23 月曜の定期の回として呼ばれたが、PM の積んだ依頼 11/23 があったのでこちらをした。定期の手入れは点検の結果がまだ来ていないので今回は見送り）**：ブランチ data/aal-oneworld（main 9a79def から）→ **PR #187（11/23 16時29分 main に入った。本番の関数の出し直しは PM の反映の流れで確かめる）**。報告 docs/pm/report-aal176.md。確かめの SQL docs/pm/aal176-check.sql。**移行・テストの番号は使っていない（表は変えない）**
  - liveries.ts の ALLIANCE に N791AN・N796AN（777-200ER、アメリカン航空、ワンワールド塗装・alliance＝知らせが出る）。出典 airportspotting（N791AN は World Airline News 2009 でも確認）。FR24 は不使用。737-800（N837NN・N919NN・N973AN）は日本に来ないので入れない
  - 確かめた結果：deno test 306本 通過（liveries_test に1本足した）・deno check 通過
  - live_positions は15分で消えるので、11/22 19:30〜21:30 は track_points（36時間で消える＝**11/24 朝8時半までに流す**）・reg_legs・foreign_legs・livery_notified で見る SQL にした
  - 本人待ち（PM のおすすめで可）：出典の強さ（airportspotting で可か）・反映（コードだけ）・aal176-check.sql の結果
- **行き先を便名で決めるのを本筋に（PM の指示 11/21 15時50分。土曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/livery-dest2（main 26804a8 から）→ **PR #167（11/21 19時43分 main に入った。本番の関数・移行192 は PM の反映の流れで確かめる。反映の後に livery-dest2-check.sql の 2、次の夜のあとに 3）**。報告 docs/pm/report-livery-dest2.md。確かめの SQL docs/pm/livery-dest2-check.sql。**移行192・テスト t131 を使った**
  - _shared/flight_dest.ts（1か所の判定）：呼び出し符号 → 便名（flightsOfCallsign。グループの別会社は親の便名でも：JAC→3X・JL、JTA→NU・JL）→ ①時刻表 flight_schedule（出発の定刻が20時間前〜1時間後の幅、出発〜到着＋6時間にいまが入る便）②いつもの時刻 foreign_usual（livery_inbound_usual。ふだんの到着がいまの前後2時間）③形の判定。束ねて1回ずつ・記憶10分・1.5秒で打ち切り
  - 使う所：運用タブの build（applyRoutes。行き先が違えば外す・この空港なら戻す・最終進入12km以内3,000ft以下はダイバートで残す・離陸は時刻表の出発地）／撮影の知らせ（build の答え）／nearAirports（便名をいつも先に）／notifyInbound（①時刻表 ②ふだん ③経路）
  - 会社を34社足した（PREFIX と airline_codes。トキエア BV・天草 MZ・エアロK・エアプレミア・貨物など）。移行192 は行を足すだけ（表の形・RLS は移行171 のまま）
  - 確かめた結果：flight_dest_test.ts 10本（本人の6件）・deno test 301本・deno check 通過・lint は前からの7件・t131 13項目・移行の番号の重なりなし
  - 本人待ち（PM のおすすめで可）：反映・数字（前後2時間・12km/3,000ft・1.5秒）・Air Japan の NQ を足すか・check.sql の 1 を反映前、2 を反映後、3 を次の夜のあと
- **特別塗装機の知らせの行き先の取り違え（急ぎ。PM の指示 11/21 14時40分。土曜で定期の回として呼ばれたが、PM の積んだ急ぎの指示があったのでこちらをした）**：ブランチ data/livery-dest（main 8ba15f6 から）→ **PR #165（11/21 15時37分 main に入った。本番の関数の出し直しは PM の反映の流れで確かめる。反映の後に livery-dest-check.sql の 4 を流してもらう）**。報告 docs/pm/report-livery-dest.md。確かめの SQL docs/pm/livery-dest-check.sql。**移行・テストの番号は使っていない（表は変えない）**
  - 原因：recordLiveries が空港ごとの答えを順に回して上書き。成田の答えの「ほかの空港へ向かう機体を除く」は機体から40km以内の空港しか比べていなかったので、羽田から40km以上離れた羽田行きが成田の「着陸」になっていた
  - 直し：_shared/arr_dest.ts（refinePhases：滑走路の向き・最終進入（横3km・手前25km・向き30°・高さ）・110km以内のほかの空港との比べで arr/dep を絞る。pickAirport：便名の行き先＞最終進入に乗っている近い方＞はっきり近い方（7割）・候補1つは50km以内。決められなければ知らせない）。airport-traffic の build で絞り込み（運用タブ・撮影の知らせ・ゴーアラウンドにも効く）、recordLiveries は nearAirports で1つに決める（必要な機体だけ flight_schedule を引く）
  - 確かめた結果：arr_dest_test.ts 9本・deno test 全部291本 通過・deno check 通過・lint は前からの4件
  - 残る弱いところ：時刻表にない便で、成田のすぐ東を低めに南西へ降りる羽田行きは形だけでは見分けられない（知らせは時刻表の行き先で止まる）
  - 本人待ち（PM のおすすめで可）：反映（関数の出し直しだけ）・数字（25km・3km・7割・50km）・SQL の 1〜3 を反映前、4 を反映後に
- **見回り 11/21 の直し（データの分。PM の指示 11/21 9時15分。土曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/sweep-1121（main 08e4b84 から）→ **PR #159（11/21 11時49分 main に入った。PM の反映 PR #163 と同じ流れ。本番の関数・移行191 の公開は PM の反映の流れで確かめる）**。報告 docs/pm/report-sweep-1121-data.md（改善担当の report-sweep-1121.md と名前が重ならないよう -data）。確かめの SQL docs/pm/sweep-1121-check.sql。**移行191・テスト t130 を使った**
  - 2：移行191 odpt_feed_at()（関数だけ。表と RLS は変えない）。返す形 {status_at, timetable_at}（運航情報・時刻表のいちばん新しい dc:date、なければ null）。anon・authenticated が呼べる・security invoker・上限2秒。画面（PR #107 の loadOdptAt）は今の呼び方のままで「○時○分時点」が出て 404 が消える。チェックインの直しは要らない
  - 7：airport-traffic（返す形は同じ）。置き場の答えが20〜60秒前なら待たせず返して裏で作り直す（_shared/traffic_view.ts の viewPlan）・見る人のしるし trafficseen:<空港>（入れ物ごとに1分に1回）が3分以内の空港だけ記録の処理が置き場を新しくする・見る人は線を書かない（記録が止まったときは書く）・記録の処理は入れ物の記憶を使わない・線は arr・dep の機体だけ・小数5けた。記録の処理の返り値に shared
  - 確かめた結果：t130 11項目・SQL 全部131本 通過・deno test 282本（traffic_view_test 3本を足した）・deno check 通過・deno lint は前からの4件
  - 本人待ち（PM のおすすめで可）：古い答えを返す幅60秒・見ているとみなす3分・反映（191 と airport-traffic は別々でも可）。起動の時間（web-push の読み込み）は測ってから
- **adsb.lol の続き：外に返す口の上限（11/21 の回・2つ目。PM の指示 11/21 2時20分。土曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/adsblol-key2（main 8c39141 から）→ **PR #153（11/21 6時17分 main に入った。PM の反映。本番の関数・移行190 の公開は PM の反映の流れで確かめる）**。報告 docs/pm/report-adsblol-key2.md。**移行190・テスト t129 を使った**
  - 移行190 track_quota（表＋RLS・方針なし）：airport_tracks は今日と前の7日はだれでも、それより前はログインした人だけ・1人1時間に空港×日60組（同じ組は数えない）。ログインなし {"error":"login_required"}・上限 {"error":"rate_limited","retry_after_min"}。中身は airport_tracks_raw（直接呼べない）に移し、airport_tracks は volatile・statement_timeout 8秒。運営の役は数えない。退会で消える。航跡の表と RLS は変えない
  - cold-tracks：ログインの鍵を getUser で確かめ、track_quota_take（service_role だけ）で同じ上限。401・429（Retry-After）。Cache-Control は private
  - t27 の「40日前を匿名で読む」を直した。deno の cold_test に bearerToken の1本
  - **反映はチェックイン担当の直し（ログインの鍵を付ける）と同時に**。今のアプリは anon の鍵で呼ぶので、先に入れるとログインした人も8日より前が見えなくなる
  - adsb.im の条件：この回も開けず（ページを開く許可の確認が時間切れ）。使えない条件なら経路の推定を止め、ODPT と reg_legs の区間だけにする案を報告に。確認表は書き換えていない
  - 確かめた結果：t129 25項目・SQL 全部128本（t49 が1回揺れて流し直しで通過。main でも通る）・deno test 273本・deno check 通過
  - 本人待ち（PM のおすすめで可）：上限の数（60組・前の7日）・adsb.im の2ページを開く・反映（チェックインの直しと一緒）
  - 11/21 2回目の呼び出し（同じ指示を手で・「main を取り込み直してから」）：PR #153 で済み。main は 8c39141 のままで取り込むものはなかった。PR #149（data/adsblol-key）とは変えるファイルが重ならず、合わせてもぶつからないことを確かめた（#149 が先に入っても rebase は要らない。移行の番号も #149 は使っていない）
  - 11/21 見張りの確認：main に PR #154（#149 adsb.lol の鍵・#146 の移行188・189）が入ったので取り込んだ。190 は付け直し不要。t122 が「188 のあとの移行ぜんぶ」で表の形を比べていて190で落ちたので、188 の直後と比べるように直した。SQL 130本・deno 279本 通過
- **adsb.lol の鍵と使い方の守り（11/21 の回。PM の指示 11/21 1時10分。土曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/adsblol-key（main 8c39141 から）→ 下書き **PR #149**（見張りを始めた）。報告 docs/pm/report-adsblol-key.md。**移行・テストの番号は使っていない**（表・RLS は変えない）
  - _shared/adsblol.ts（新）：秘密の設定 ADSBLOL_API_KEY があれば api.adsb.lol に鍵を付ける（なければ今までどおり）。ヘッダー名は ADSBLOL_KEY_HEADER（既定 api-auth。**案内のページを開けず未確認**）。adsb.im には付けない
  - User-Agent を `soramemo (<関数名>; https://soramemo.jp/)` に（airport-traffic・flight-live・airport-foreign の5か所）。flight-live に Retry-After の守り（429・420 のあと最長5分止める）
  - adsb.im の条件はページを開けず未確認。Project の「外部データの利用規約の確認表」に adsb.im の行を足し、adsb.lol の行を返事に合わせて直した
  - 外に返す口：表はどれも閉じている。ログインなしで回せば大量に取れるのは airport_tracks（どの過去の日でも・回数の上限なし）と cold-tracks。上限の案1（ログインした人だけ＋1時間の日数の上限、ログインなしは前の7日）・案2（日付だけ）・案3（今のまま）を報告に。作っていない
  - 確かめた結果：deno test 278本・deno check 通過
  - 本人待ち（PM のおすすめで可）：鍵を取って入れる（ヘッダー名も確かめる）・adsb.im の条件を本人が開いて確かめる・外に返す口の案（おすすめ案1）
  - **11/21 2時46分（日本時間）PR #149 は main に入った**。鍵は本人が秘密の設定に入れるまで今までどおり鍵なしで動く。入れたら次の日にログの「adsb.lol 429」を見てもらう
  - 11/21 2回目の呼び出し（同じ指示を手で）：PR #149 で済み。data/redo-1120（PR #146）は作り終えて PM の反映待ちで、残りの仕事はない（main は 8c39141 のまま）。変えたものは帳面のこの行だけ
- **見落としの片付け 11/20（PM の指示 11/20 14時10分・overlooked-1120.md の A1・A2・A4。金曜の定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/redo-1120（main 8c39141 から）→ 下書き **PR #146**（見張りを始めた）。報告 docs/pm/report-redo-1120.md。**移行188・189、テスト t122（読み替え）・t127 を使った**
  - 移行188：定期の手入れ #111 の 183（索引8本だけ）を番号を付け直して入れた。今の main（184〜187）とぶつからないことを t122 で確かめた。**#111 は閉じてよい**（PM が閉じる）
  - 移行189：inbound_aircraft が前の便がないとき first_of_day を返す（reg：今日の登録記号＋前の日の最後の便がここに着いた・今日それより前の便なし → overnight も返す／history：前の60日で3日以上・7割以上）。関数の中身だけ・表と RLS は変えない
  - #81（data/speed-1113b）は main に全部入っている。**閉じてよい**
  - 確かめた結果：t122 16項目・t127 16項目・t29 通過・番号の重なりなし（179件）。SQL のテスト全部 129本 通過
  - 本人待ち（PM のおすすめで可）：history の線（3日以上・7割以上）でよいか・overnight を画面に出すか
  - **11/20 17時46分（UTC）PR #146 は main に入った（移行188・189）**。本番に出たかを Actions で確かめ、反映のあと 2026-11-16-2-check.sql で「索引で引いた回数」が増えたか見てもらう
- **フライトの実際の出発・到着と航跡（11/20 の回。PM の指示 11/20 1時55分。木曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）**：ブランチ data/flight-actual（main 3a71781 から）→ 下書き **PR #136**（見張りを始めた）。報告 docs/pm/report-flight-actual.md。**移行187・テスト t126 を使った**
  - 移行187：flights に act_dep_at・act_arr_at・act_src（odpt／adsb／timetable）。3つそろう決まり（flights_act_pair）・未来の時刻を空にする守り（trigger flights_act_guard）。RLS は今のまま（本人だけ読める・利用者は書けない）
  - flights_fill_actual(p_days, p_limit)：flight_history（400日）→ flight_schedule（14日、ODPT の実際の時刻）の順。同じ便名（0なし・共同運航も）・同じ区間・定刻が出発チェックインの2時間前〜到着チェックイン。欠航は使わない。実績と定刻はまぜない。確かな取り先になったときだけ書き直す。照合（8日分）と daily-archive（3日分）から呼ぶ。移行の中で400日分さかのぼる（時間切れなら止めて移行は通す）
  - flights_track_todo：31日前までの便に flight_tracks の航跡（adsb.lol）。daily-archive が1晩300便まで書く。**照合で OpenSky の航跡を取るのはやめた**（研究・非商用だけの条件）
  - 確かめた結果：t126 26項目・deno 272本・型の確かめ・番号の重なりなし。SQL のテスト全部 126/127 通過（落ちたのは main でも落ちる経営の t49）
  - 本人待ち（PM のおすすめで可）：「空の上」は ODPT のゲートの時刻の差でよいか・便名のない便を reg_legs で埋めるか・31日より前の航跡を cold-archive から埋めるか・照合を adsb に切り替えるか
  - 11/20 2回目の呼び出し（同じ指示）：新しい仕事はなし。main（863fb3d・PR #137）を取り込み、移行の番号の重なりなし（187 のまま）・deno 272本・t126 通過を確かめて push した
  - **11/20 3時18分（JST）PR #136 は main に入った（移行187）**。本番に出たかを Actions で確かめ、次の日に flight-actual-check.sql の ② と daily-archive の結果（actual・track_back）を見てもらう
  - 反映のあと：docs/pm/flight-actual-check.sql の ② で取り先ごとの数と航跡の数を見てもらう
- 未来の「実際の時刻」を見込みにする（11/18 朝の回。定期の回として呼ばれたが、PM の積んだ急ぎの指示 11/18 7時45分 があったのでこちらをした）：ブランチ data/atd-future（main 61ba9c7 から）→ 下書き **PR #126**（見張りを始めた）。報告 docs/pm/report-atd-future.md。**移行186・テスト t125 を使った**
  - _shared/odpt_status.ts の splitActual：実際の時刻が取り込んだ時刻より1分を超えて先なら atd／ata にせず etd／eta（お知らせも「見込み」の文）。odpt_fast.ts：未来の atd は出発前扱い
  - 移行186：apply_flight_status に同じ守り（未来の atd・ata は入れず etd・eta に、残っていた未来の値は次の書き直しで外す。lock_timeout 10s 付け直し）。表・RLS は変えない
  - 確かめた結果：deno 270本・t125 14項目・t18/t21/t23/t27/t51/t89/t105/t108/t117 通過
  - 11/18 8時16分の PM の指示（ブランチ名 data/odpt-future-actual・本人「進めて」）は、同じ中身なので PR #126 にまとめた（報告に対応を書いた）。本番を見る読むだけの SQL docs/pm/atd-future-check.sql（① 先の atd・ata の数 ② 例20件）を足した。反映の前と次の日に流してもらう
  - **11/19 3時55分（UTC）PR #126 は main に入った（移行186）**。本番に出たかを Actions で確かめ、次の日に docs/pm/atd-future-check.sql の ① future_now が 0 か見てもらう
  - 本人待ち：朝一番の便の言い方（案A：inbound_aircraft に first と前の日に着いた空港・時刻を足す／案B：画面の文だけ。おすすめ A）
- いつもより遅いの画面に要る関数（11/17 の回。PM の指示 11/17 12時20分。曜日は火曜で定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）：ブランチ data/usual-late-rpc（main 32d923d から）→ 下書き **PR #118**（見張りを始めた）。報告 docs/pm/report-usual-late-rpc.md。**移行185・テスト t124 を使った**
  - 移行185：読むだけの関数 usual_late(p_flight, p_reg, p_day, p_arr, p_land) だけ（表・RLS は変えない。anon・authenticated は実行だけ）。便名か登録記号（reg_legs のその日と前の日）から、いつもの到着（foreign_usual。dow・n・spread・weeks）・着く見込み（着陸。実績 foreign_legs → 画面が渡す flight-live の land_pred → foreign_watch.eta（10分以内）の順）・late_min と kind（late 15分以上・usual 前後14分・early）・event・divert_to・curfew_near・source・note。見込みがなければ eta null（U1n-v2）。ODPT の会社は reason odpt、知らない記号は unknown、形のちがう値は null
  - 約束：見張りの関数をつなぐとき、foreign_watch.eta は**着陸の見込み**で書き、門限は state.curfew_near（true／false）に入れる
  - 確かめた結果：t124 32項目・SQL のテスト全部125本 通過・番号の重なりなし
  - **11/17 15時18分 PR #118 は main に入った（PM の反映の PR #119 → 61ba9c7、移行185。チェックインの usual_late の取り込みと一緒）**。反映の Actions の結果と、次の日の報告の 7 の SQL の結果を見る
  - 本人待ち：案内板で選ばれていない飛行中の便にも見込みを出すか（出すなら live_positions に速さの列を足す案）・報告の 7 の SQL の結果
- 海外の会社の特別塗装機の続き（11/16 夜 PM の手で呼んだ回。11/16 14時の指示の 2・本人「おすすめ」）：ブランチ data/foreign-livery（main 4af96c8 から）→ 下書き **PR #102**（題を直した）。報告 docs/pm/report-foreign-livery.md の 7〜11。**移行184・テスト t123 を使った**
  - 移行184：表 livery_extra（本人が Table Editor で足す。src 必須・https・FR24 不可。誰でも select・書くのは service_role）・livery_inbound_usual（foreign_usual の到着。service_role だけ）
  - _shared/livery_extra.ts（新）・airport-traffic：一覧に表を合わせる（5分ためる）／海外の塗装機を日本のまわりで見たら行き先（①foreign_usual ②adsb.im routeset）と着く見込みを1回（livery_notified の（機体・空港）に入れて数分前の知らせと二重にしない。調べるのは便ごとに12時間に1回、分からなければ15分後）／アライアンス塗装は海外の会社だけ知らせる（案3-A）／アライアンス塗装のときは撮影の知らせの人にも空港の知らせを送る（spot_push が alliance を出さないため。撮る人用が直したら戻す）
  - liveries.ts：FR24 出典の32機 → B-16206・VT-ALJ・VT-ANU・C-GHLM は出典を差し替えて残し、28機を外した。B-17812・B-16715・G-YMMR を足した。N91007 の出典も差し替えた。G-YMMU は報道の出典がなく入れていない（本人の目撃で livery_extra に足せる）
  - 確かめた結果：t123 18項目・deno test 268本・deno check 通過。SQL のテスト全部は報告に書く
  - 本人待ち：「反映して」・外した28機の扱い・G-YMMU・特別塗装も早めの1回に替わってよいか（報告の 10）
- 定期の手入れ 11/16 の2回目（月曜の定期の回・17時台。PM の指示なし）：ブランチ maint/2026-11-16b（main 4af96c8 から）→ 下書き **PR #111**。報告 docs/pm/maint/2026-11-16-2-report.md・読むだけの SQL docs/pm/maint/2026-11-16-2-check.sql。**移行183・テスト t122 を使った**（ほかの回は 184・t123 から）
  - 移行183 maint_1116b：索引を8本足すだけ（aircraft(user_id)・flights の dep_checkin/arr_checkin 部分索引・経営の co3_market/co3_orders の aircraft_id・co3_breakdowns/co3_heavy の spare_id・co3_extra の aircraft_id）。模擬のデータベースで「外部キーなのに引く索引がない」28本から、小さな表と auth.users を指すものを除いた8本。aircraft は user_id で始まる索引が部分索引だけで、経営の約50か所が全部読みだった
  - 重なる索引は co3_events_user（一意の (user_id, day, kind) と重なる）1組だけ。経営の道なので消さない（本人に聞いている）
  - テスト t122（16項目）・SQL のテスト全部。経営・チェックインとも値は変わらない
  - 本人待ち：「反映して」・2026-11-16-2-check.sql の結果
- **11/16 17時26分 PR #104・#108 が main に入った（本人の反映の PR #109 → 4af96c8、移行171〜182）。反映の Actions（run 215＝43831221783、17時26分〜17時54分）はすべて成功（テスト・SQL を流す・関数の公開・アプリ）。本番に入った**
  - 次の日（11/17）に本人に流してもらう読むだけの SQL（重くしない）：
    - `select feed, dc_date at time zone 'Asia/Tokyo' dc, fetched_at at time zone 'Asia/Tokyo' f, n from public.odpt_feed_dates order by feed;`（redo-1116-check.sql の③）
    - `select j.jobname, count(*) n, count(*) filter (where d.status <> 'succeeded') ng, round(max(extract(epoch from d.end_time - d.start_time))::numeric, 1) max_s from cron.job_run_details d join cron.job j on j.jobid = d.jobid where j.jobname in ('foreign-legs','foreign-usual','foreign-watch-sync','ops-log-cleanup','eta-calib','taxi-out','flight-watch-cleanup') and d.start_time > now() - interval '1 day' group by 1 order by 1;`
    - `select day, count(*) from public.foreign_legs where day >= current_date - 2 group by 1 order by 1;`
  - redo-1116-check.sql の ①②（照合を adsb に切り替えるか）は本人待ちのまま。切り替えるまで照合は OpenSky のまま
  - 下の「見落としの片付け」「海外の便の見張りの続き」の行は本番に入った。古い PR #18・#33・#56・#58・#70・#103 は閉じてよい（本人へ）
- 海外の便の見張りの続き（11/16 14時 PM の指示の 1。11/16 15時台の回＝PM が「見落としの片付けを先に、時間があればこちら」と手で呼んだ回）：ブランチ data/foreign-collect（PR #104、**data/redo-1116＝#108 を取り込んだ**ので反映は #108 のあと）。報告 docs/pm/report-foreign-collect.md の 7
  - ① 171 を直した（まだ main にないので番号はそのまま）：airline_codes の japan → **odpt**（JAL・JLJ・JTA・JAC・HAC・ANA・AKX・AJX だけ true）。ODPT にない日本の会社（スカイマーク・ピーチ・ZIPAIR・春秋航空日本・日本貨物航空など）は JA の機体でも集める。表にない会社の JA の機体は入れない。t110（37項目）
  - ③ 移行181 foreign_cold：foreign_legs だけ180日より前を cold-archive へ（ほかの表は400日のまま）。cold_days の決まりに foreign_legs を足す。cold_done の lock_timeout 5s は残す。t120（14項目）。大きさは約85MB で頭打ちの見込み
  - ② 移行182 foreign_watch：乗る便に選んだ時刻表にない便を1便1行（いつもの到着空港・時刻つき）。foreign_watch_sync（cron 5分・30s）・foreign_watch_rows・foreign_watch_put（service_role だけ・RLS 有効）。t121（17項目）。**見張りの関数（flight-watch）へのつなぎはまだ**
  - t117 を「178 だけで比べ、あとの移行のあとも上限が残る」形に直した（181 が cold_done の中身を足すため）
  - 確かめた結果：SQL のテスト全部122本・deno test 262本 通過
  - 本人待ち：反映の順（#108 → #104）・「反映して」
  - 2 の data/foreign-livery の続き（livery_extra・日本行きの1回の知らせ・海外のアライアンス塗装・FR24 の出典の差し替え）は**まだ始めていない**
- 見落としの片付け（11/16 14時10分 PM の指示・本人「OK」。11/16 14時40分の回＝月曜の定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした）：ブランチ data/redo-1116（main 2ae2e1f から）→ main 向けの下書き PR #108（見張りを始めた）。報告 docs/pm/report-redo-1116.md（そのブランチ）
  - 1. 定期の手入れ6本を書いた順のまま付け直した：#18 153→**173**（t93→t112）・#33 155→**174**（t95→t113）・#56 158→**175**（t98→t114）・#58 161→**176**（t101→t115）・#70 162→**177**（t102→t116）・#103 170→**178**（t109→t117）。171（foreign-collect）・172（経営 keiei/redo-1116）・t110・t111 は飛ばした。main の 151〜169 が同じ関数・仕事を書き直していないのを確かめた。t113 は 175 の json に合わせて直した
  - 2. 移行179 odpt_feed_dates（RLS 誰でも select・書くのは odpt_feed_date_put＝service_role だけ・lock_timeout 5s）。odpt-status（4分の回）・timetable-sync・schedule-sync が dc:date を残す。airport-now は flights.dc_date を返す（足しただけ）。テスト t118・odpt_date_test
  - 3. OpenSky を今使っているのは毎晩の照合（verify-flights・tools/verify_flights.ts）だけと分かった。移行180 verify_arrivals（reg_legs から OpenSky と同じ形の到着の一覧。service_role だけ）。VERIFY_SOURCE=adsb のときだけ使う（未設定なら今までどおり）。テスト t119・verify_source_test
  - t108（海外の止まり具合）が日付に左右されて main でも落ちていたのを直した
  - 確かめた結果：SQL のテスト全部119本・deno test 262本・deno check 通過
  - 本人待ち：redo-1116-check.sql の ①②（adsb に切り替えるか）・「反映して」
  - 古い PR #18・#33・#56・#58・#70・#103 は**11/16 にすべて閉じられた**（入れ直しずみ）。下の行は次の回で消してよい
- 公式の便の情報の元（11/16 11時55分 PM の指示、11/16 13時台の回で済み）：報告 docs/pm/report-official-flight-sources.md（ブランチ data/foreign-collect・PR #104 に入る）。コード・表・移行なし
  - 分かったこと：一般の無料アプリに出してよいとはっきり書いた公式の元はなかった。FAA SWIM（SCDS）は無料・登録制で「運航に使わないアプリ」は可（受ける仕組みが Supabase に向かない）。ルフトハンザは無料の枠だが「ほかのデータと合わせない・渡さない」・商用は許可。スキポールは旅客を助ける用途だけ・保存24時間まで・商用は有料。BA は試用だけで商用不可。フランクフルトは公開の API なし・サイトから取るのも不可。エールフランス‐KLM は規約の原文を読めず（未確認）
  - 本人待ち：試すか（おすすめ ①FAA ②ルフトハンザ ③スキポール）・アカウントは本人（旅そら）・「商用」に当たるかの問い合わせをするか
- 海外の会社の便の実績を自分で集める（11/16 11時40分 PM の指示・本人「海外のデータも収集したい」）：ブランチ data/foreign-collect（main 2ae2e1f から）→ main 向けの下書き PR #104（見張りを始めた）。報告 docs/pm/report-foreign-collect.md（そのブランチ）
  - 分かったこと：reg_legs・airport_tracks_all は会社を問わず「英字3文字＋数字」の便を残していて、海外の会社の便も4つの円の中なら入っていた。海外の空港の側は円の外で分からない
  - 移行 171（foreign_legs）：表 airline_codes（86行・PREFIX と同じ＋NCA。誰でも select）・foreign_legs（実績。消さない。関数からだけ）・foreign_usual（前の8週の中央値。曜日ごと3回以上・曜日なし5回以上・ばらつき60分以下。関数からだけ）。関数 foreign_legs_build(日)・foreign_usual_build()（運営だけ・lock_timeout 5s）・foreign_late(便名, 日)（誰でも）。毎日の仕事 foreign-legs（45 */3）・foreign-usual（55 18 UTC）、上限つき。外への問い合わせは0回増
  - テスト t110（34項目 OK）。adsb.lol は ODbL 1.0（出典を関数の note に入れた）。adsb.im は使っていない
  - 本人待ち：表の大きさ（1年で約100〜140MB の見込み。foreign-collect-check.sql の結果で確かめる）・案A の見張りの表の持ち方（flight_schedule に推定の行／foreign_watch）・ODPT にない日本の会社（スカイマーク・ピーチなど）を入れるか・画面に出すならデザインの画面案から
- 定期の手入れ 6回目（11/16 月、PM の指示なしの回）：ブランチ maint/2026-11-16（main 2ae2e1f から）→ main 向けの下書き PR #103（見張りを始めた）。報告 docs/pm/maint/2026-11-16-report.md（そのブランチ）
  - 移行 170（maint_1116）：ops-log-cleanup に statement_timeout 2min・lock_timeout 5s／Edge Functions が service_role で呼ぶ書く関数12個に lock_timeout（毎晩 5s：archive_* 4つ・cold_done・airport_tracks_put・reg_legs_route・timetable_replace・world_status_put、毎分 10s：apply_flight_status・flight_alerts_put・reg_legs_touch）。表・索引・RLS・権限・本文は変えない。チェックイン・経営への影響なし
  - テスト t109（13項目 OK）。本物の Postgres 16 で関数の lock_timeout が効くのを確かめた。読むだけの docs/pm/maint/2026-11-16-check.sql（cron の仕事ごとの上限の有無・回数・失敗・最長秒と12関数の設定）
  - 反映の順：#18（153）→#33（155）→#56（158）→#58（161）→#70（162）→#103（170）。#33・#56・#58 の create or replace で関数の設定が消えるので 170 は最後。#18 は開いたままの下書き（11/16 2回目の回で確かめた）
  - 本人待ち：「反映して」・2026-11-16-check.sql の結果
  - 2回目の回（11/16 12時55分、月曜の定期の回・PM の指示なし）：今日の手入れは PR #103 で済みなので作り直さない。#103 は CI の実行・コメントとも まだなし。**#18（153）は下書きのまま開いている**のを確かめた（反映の順は上のまま）。点検の結果（result.csv）はまだ来ていない。変えたものは帳面のこの行だけ
  - 3回目の回（11/16 13時25分、月曜の定期の回・PM の指示なし）：今日の手入れは PR #103 で済み・PM の新しい指示もなし（最後は 11/16 11時55分で済み）。#103・#104 とも CI の実行・コメントはまだなし、main は 2ae2e1f のまま。点検の結果（result.csv）はまだ来ていない。変えたものは帳面のこの行だけ
  - この回では PM が 11/16 11時40分に積んだ「海外の会社の便を自分で集める」（data/foreign-collect）は始めていない（月曜の定期の回で PM の指示が付いていなかったため。指示の回で作る）
- 海外の会社の特別塗装機が来るのも知らせる（11/16 10時55分 PM の指示・本人「海外の塗装機が来るのも通知に出したい」）：ブランチ data/foreign-livery（main 2ae2e1f から）→ main 向けの下書き PR #102（見張りを始めた）。報告 docs/pm/report-foreign-livery.md（そのブランチ）。コード・表は変えていない
  - 分かったこと：liveries.ts に海外の会社の機体はすでにある（特別塗装13機・アライアンス塗装約40機）。G-YMMU（BA の 777-200ER）は一覧になく、アライアンス塗装は「知らせない」決まり（kind !== "alliance" が airport-traffic・odpt-status・livery_push・spot_push の4か所）なので来なかった。今の知らせは運用タブの空港の近くで「着陸に向かっている」と分かったときだけ
  - **アライアンス塗装の31機の出典が Flightradar24 のブログ**で、決まり（FR24 は使わない）に合わない → 差し替えるか外す案
  - 案：1-A 表 livery_extra（本人が Table Editor で足せる。RLS は誰でも select・書くのは service_role）／2-A 今の adsb.lol の円＋adsb.im の経路で日本行きを見つけたら到着の見込みつきで1回（livery_notified の決まり）。2-B 離陸から見るなら /v2/reg/ を10分ごと（1日約7,200回。adsb.lol の作者に上限を聞いてから）／3-A 海外の会社のアライアンス塗装だけ知らせる
  - **11/16 23時20分 PR #102 が main に入った（報告だけ。コード・表は変わらない）**
  - 本人待ち：案1・2・3 と FR24 の出典の差し替え
- 海外の航空会社の便も遅れの通知の対象に（11/16 10時50分 PM の指示・本人「進める」）：ブランチ data/foreign-carriers（main 2ae2e1f から）→ main 向けの下書き PR #101（見張りを始めた）。報告 docs/pm/report-foreign-carriers.md（そのブランチ）
  - 結論：**ODPT の空港ビル会社のデータは本番に使えないので、取り込みは作っていない**（移行・表・RLS・関数は変えていない）。ODPT にある空港会社は東京国際空港ターミナル（羽田の国際線）の3件だけで、ライセンスは「公共交通オープンデータチャレンジ限定ライセンス」（【チャレンジ2026限定】・目的外の利用は禁止・2027年3月12日に終了して消す）。成田・羽田の国内線・関西などの空港会社は ODPT にない。成田の公開 API も見つからない
  - アプリ：ホームの便名入力で BA5 などは「いま飛んでいるときだけ」選べる。push-subscribe も受け取るが、通知の仕組みは flight_schedule の行から始まるので通知は出ない（困りごとの原因）。画面の直しは元が決まるまで要らない
  - 代わりの案（報告）：A 乗る便に選んだ海外の便だけ機体の位置で見張る（推定。門限の10分前より遅い見込み・ダイバート・引き返しだけ。定刻がないので遅れの分・0時前後・欠航は出せない。移行と RLS が要る）／B 旅そらから TIAT・成田に問い合わせ（文の下書きあり）／C ODPT 事務局にチャレンジ後も使える形の予定を聞く。チャレンジに応募して使う案は勧めない
  - 読めなかった：チャレンジ限定ライセンスの本文（developer.odpt.org/terms が JavaScript だけ）。本人にブラウザで目的と期間の条を見てもらう
  - 確かめた結果：報告の読むだけの SQL（選ばれた便のうち時刻表にない便の数）を手元の Postgres 16 で流して通った
  - 本人待ち：案A・B・C のどれをするか・SQL の結果
  - 2回目の回（11/16、PM が同じ指示を手で呼んだ）：PR #101（249728a）で済みだったので、PR #101 のコメント・CI（どちらもまだなし）と main（2ae2e1f のまま、rebase 不要）だけ見た。変えたものはなし
  - この回は定期の回（月曜・PM の指示なし）として呼ばれたが、PM が 11/16 10時50分・10時55分に積んだ指示があったので、その2つをした。定期の仕事（データの整理・圧縮）はこの回はしていない（次の月曜に）
- 門限ギリギリの知らせの幅を30分→10分に（11/15 19時25分 PM の指示・本人「門限ぎりぎりになるやつ」）：ブランチ data/curfew-10（main 754bca5 から）→ main 向けの下書き PR #100（見張りを始めた）。報告 docs/pm/report-curfew-10.md（そのブランチ）
  - alert_merge.ts の CURFEW_NEAR を 30→10（空港ごとの通知・乗る便の通知の両方がこの1か所を見る）。0時前後・欠航・ダイバート・引き返し・乗る便の15分は変えない。移行・表・RLS なし。影響はチェックイン（通知だけ）、経営なし
  - テスト：alert_merge_test に「幅は10分」（伊丹・福岡・成田で11分前は出ない・10分前と9分前は出る・過ぎたら出る・前の幅なら出た25分前は出ない・乗る便にも届く）。30分前提の古い例はまとめた。deno test 255本・型の確認 通過（Deno 2.5.6 を npm で入れられた）
  - 本人待ち：「反映して」（移行がないので rebase 不要、関数の公開だけ）
  - この回は定期の回（PM の指示なし・日曜）として呼ばれたが、PM が 11/15 19時25分に積んだ指示があったので、そちらをした
  - 2回目の回（11/15、PM が同じ指示を手で呼んだ）：PR #100（18fd97a）で済みだったので、PR #100 のコメント・CI（どちらもまだなし）と main（754bca5 のまま、rebase 不要）だけ見た。変えたものはなし
  - **11/15 21時52分 PR #100 が main に入った（本人が下書きを外して入れた）**。反映の Actions（run 214＝43716064808、11/15 21時52分〜22時18分）は成功。本番に入った。移行なし
- 海外の空港の止まり具合を作る（11/15 0時10分 PM の指示・本人「OK」：案1・2）：ブランチ data/world-ops → main 向けの下書き PR #93（見張りを始めた）。報告 docs/pm/report-world-ops.md（そのブランチ）
  - **11/15 14時59分 PR #93 が main に入った（反映の PR #97 → 754bca5、移行169。仕上げ a33a975 も一緒）。反映の Actions（run 213＝43683425961）はすべて成功（テスト・移行169の適用・関数の公開・アプリ。15時0分〜15時25分）。本番に入った**。次：明日、cron.job_run_details（world-status）と関数の返す rows・started・ms を本人に見てもらう
  - 移行 169 world_ops：表 world_airport_status（RLS 誰でも select・書くのは service_role。続いているものは空港・種類ごとに1行、なくなったら ended_at、3日で掃除）・world_status_put／world_status_rows（service_role）・world_status_now（10分より古い・終わったものは出さない）・world_flight_counts（JAL・ANA の国際線を海外の空港ごとに便・欠航・30分以上の遅れ）・world_airport_ops（画面用、note に出典の文）・alert_push_log に world と rank 0・alert_push_claim に「止まり具合がはじめて分かった・変わったら送り直す」。cron world-status（2分・10s）・world-status-cleanup（30s）。先頭に lock_timeout 10s。影響はチェックイン（運用・通知）、経営なし
  - 関数 world-status（config.toml に足した）・_shared/faa_nas.ts（XML の読み方・就航先 US_SERVED 24空港）。通知は alert_merge.ts の addWorld・worldLine・worldOnlyGroups（お知らせのない乗る便には止まり具合だけの rank 0）、alert_push.ts の notifyFlights(…, worldOnly)
  - 確かめた結果：t108（23）・t107・t15・t18・t01・t51 通過、番号の重なりなし（161件）。**この回は npm で Deno 2.5.6 を入れられた**（npm i -g deno@2.5.6）ので、本物の deno test 255本・型の確認が通過。SQL のテスト全部（111本）も通過
  - 未確認：FAA の XML の本物の形（この回も開く許可が下りず。昔からの AirportStatus の形に合わせ、<ARPT> を含むかたまりを広く拾う）
  - 本人待ち：「反映して」・US_SERVED を world-destinations.sql の結果で直すか・止まり具合だけの通知（rank 0）を入れてよいか・FAA の XML を1回分貼ってもらう（docs/pm/faa-sample.xml）
  - この回は定期の回（PM の指示なし）として呼ばれたが、PM が 11/15 0時10分に積んだ指示があったので、そちらをした
  - 2回目の回（11/14、PM が同じ指示を手で呼んだ）：PR #93 で済みだったので、PR #93 の CI・コメント（どちらもまだなし）と main（5a22d8e のまま、rebase 不要）だけ見た。変えたものはなし
  - **3回目の回（11/15 日曜・定期の回として呼ばれたが、PM の 11/15 12時40分の指示が残っていたのでそちらをした）→ PR #93 の a33a975**：移行169の中身を直した（番号はそのまま）。world_airport_ops に feed_at（全体と空港ごと）・空港ごとの note（FAA がある空港用／便の数だけの空港用、notes: {faa, count} も）・faa[] に label（閉鎖中・地上待機中・到着の間引き中・到着の遅れ・出発の遅れ・除氷中）と reason_ja。関数 world_reason_ja(text)（約60語の表。区切った言葉を全部引けたときだけ訳す・知らない言葉があれば原文）。gdp の通知の文も「到着の間引き中」に。t108 28項目・t107・deno test 255本 通過。報告 report-world-ops.md の 6。PR #93 のコメント・レビューはまだなし。main は 5a22d8e のまま（rebase 不要）
  - 4回目の回（11/15、PM が同じ仕上げの指示を手で呼んだ）：a33a975 で済みだったので、PR #93 のコメント（まだなし）と main（5a22d8e のまま、rebase 不要）だけ見た。変えたものはなし
  - 返す形はチェックイン担当の帳面（checkin.md）に書くよう PM に言われたが、ほかの担当の帳面は変えない決まりなので、下の「ほかの担当への依頼」に書いた。PM から checkin.md に写してほしい
- 海外の空港の止まり具合の元さがし（11/14 21時10分 PM の指示・本人「ヨーロッパとか日本から就航してる空港も欲しいね」）：ブランチ data/world-ops-sources → main 向けの下書き PR #92。報告 docs/pm/report-world-ops-sources.md・読むだけの docs/pm/world-destinations.sql（そのブランチ）。コード・表は変えていない
  - 結論：すぐ使えるのはアメリカの FAA NAS Status（https://nasstatus.faa.gov/api/airport-status-information 、公開の XML・1分ごと・登録なし。地上待機・出発の間引き・閉鎖・15分以上の遅れ・除氷。個別の規約の文は見つからず、米国政府の著作物の一般の決まりと FAA のデータの免責で「使える見込み」）。仁川（data.go.kr「航空機運航現況 詳細照会」、許諾「制限なし」、開発用1日500回）・台湾 TDX（政府資料開放授權條款 1.0）は旅そらで登録すれば使える見込み。香港は前の日の分だけ。EUROCONTROL は公開の画面に機械で読む口がなく条件不明・B2B は運航の組織だけ → 使わない。中国・東南アジア・中東・オセアニアは公開の公式の元なし → 使わない
  - 案（効き目の順）：1 FAA を2分ごと（1日720回）で読み、表 world_airport_status（移行と RLS をセットで）に。運用タブの札・乗る便の通知に1行・羽田／成田のお知らせ 2 今ある JAL・ANA の国際線の欠航・遅れを海外の空港ごとに数える（外へ問い合わせない） 3 仁川・台湾の便の一覧を数える 4 ヨーロッパは EUROCONTROL に問い合わせる案
  - 就航先の一覧はリポジトリになく、world-destinations.sql（7日・std の索引・20秒で止まる。手元の Postgres 16 で確かめた）で作る。報告には見込みの一覧を書いた
  - 読めなかった：XML の全部の項目（11/14 に開くと閉鎖だけ・Update_Time が 10-26 と出た。道具のためた答えかもしれない）・FAA の Disclaimer Statement の本文・data.go.kr の活用ガイド・TDX の項目表・EUROCONTROL の再利用の条件
  - 本人待ち：案1・2を作るか・出す所・仁川／台湾の登録・EUROCONTROL に聞くか・world-destinations.sql の結果・ブラウザで XML の Update_Time を見る
  - この回は定期の回（PM の指示なし）として呼ばれたが、PM が 11/14 21時10分に積んだ指示があったので、そちらをした
  - 2回目の回（11/14、PM が同じ指示を手で呼んだ）：PR #92 で済みだったので、読めなかった所のうち韓国の公共データポータルの方針を読んで報告に足した（第0類型＝商用可・出典は条件でない・加工可。「制限なし」がそれにあたるという読み）。PR #92 に新しいコメント・CI はなし
- 遅れの通知を1つにまとめて、すぐ知らせる（11/13 20時20分 PM の指示・本人「遅れが二重にくる時があるので、きちんとまとめて、遅れが発生次第通知が来るようにして」）：ブランチ data/alert-merge → main 向けの下書き PR #88（この回で見張りを始めた）。報告 docs/pm/report-alert-merge.md（そのブランチ）
  - 通知は「便名@運航日@出発空港」で1件（_shared/alert_merge.ts）。出発と到着・推定と運航情報・共同運航の2行（同じ出発・到着・定刻）・空港と乗る便の両方、のどれでも1件。送るのは はじめて／欠航・ダイバート・引き返しになった／運航情報がはじめて届いた／送った遅れから30分以上ふえた、だけ。tag は fw-便名@運航日@出発空港、renotify: true、urgency high
  - 乗る便（push_subs.flights）は15分から・空港は60分から。遅れのお知らせは15分から作る（推定の出発は離陸が定刻の30分後から、「まだ飛行中」は15分から30分ごとに出し直す）。画面の一覧 flight_alerts() は今までどおり60分以上だけ（返す形同じ）
  - odpt-status?fast=1 を毎分（cron odpt-status-fast）：乗る便の空港だけ ODPT に問い合わせ（1回6件まで・50秒に1回。_shared/odpt_fast.ts）。目安は今の回 1日約1,150件＋毎分の回 多くて1分6件
  - 移行 168 alert_merge：flight_alerts に late・official・updated_at、flight_alerts_put（推定で運航情報を上書きしない）、表 alert_push_log（RLS 有効・ポリシーなし・購読と一緒に消える・3日で掃除）、alert_push_claim（同時でも二重にしない）、odpt_status_runs の id 2、見張り（alert_watchdog）と flight-watch の安全装置は60分以上だけ数える。先頭に lock_timeout 10s。影響はチェックイン（通知だけ・画面は同じ）、経営なし
  - 確かめた結果：関数のテスト alert_merge_test（8）・odpt_fast_test（3）・odpt_status_test・flight_watch_test（15分に直した）通過、SQL t107（24）・t15・t18・t01・t51 通過、番号の重なりなし（160件）。**この回は Deno を入れられなかった（外のコードの入れ方を止められた）ので、Node で Deno.test を動かす代わりの道具（作業用の場所だけ）で流した。CI の deno test を見る**
  - 2回目の回（PM が手で呼んだ）：PM の追記（20時25分）を入れた（b4d9528）。空港ごとの通知は「60分以上の遅れ全部」をやめ、主要空港（羽田・成田・関西・伊丹・中部・新千歳・福岡・那覇）の便で、門限に間に合わないおそれ（伊丹21時・福岡22時・成田24時の30分前から。過ぎる見込みなら「引き返すか、ほかの空港へ（推定）」）・遅れで0時前後（23時30分〜翌1時、定刻は12時〜23時29分）に着く便（rank 2）と、欠航・ダイバート・引き返しだけ。乗る便は15分のまま。門限は 11/13 に原文で確かめた（伊丹：豊中市 令和8年度資料、福岡：国交省 令和8年9月、成田：千葉県 令和8年8月28日更新。URL は alert_merge.ts の CURFEW と報告）。コードの定数で持ち、表は作らない。alert_push_claim は rank 2 でも30分ふえたら送り直す。テスト alert_merge_test 11項目・t107 27項目に
  - **3回目の回（11/14 土、定期の回として呼ばれたが PM の 11/14 9時40分の指示があったのでそちら）**：本人「すべてOK」を受け、主要でない空港を選んだ人にも欠航・ダイバート・引き返し（rank 3 以上）を届けるように eligible を直した（遅れは主要空港の門限・0時前後だけのまま）。alert_merge_test 13項目（主要でない空港の欠航が届く形を足した）・t107 30項目 通過（c45147d、PR #88 に push）。Deno はこの回も入れられず、Node の代わりの道具（作業用の場所だけ）で流した
  - 決定済み（11/14）：毎分の回（odpt-status-fast）を入れる・主要8空港・門限の30分前から
  - 4回目の回（11/14、PM が同じ指示を手で呼んだ）：c45147d で済みだったので、PR #88 の CI（まだ実行なし）と main（4fb2f42 のまま、rebase 不要）だけ見た。変えたものはなし
  - **11/14 11時34分 PR #88 が main に入った（#91 pm/release-1114 → 5a22d8e、移行168）。反映の Actions（run 212）はすべて成功（deno test・データベースのテスト・移行168の適用・関数の公開・アプリ。11時35分〜12時0分）**
  - 本人待ち：docs/pm/alert-dup-check.sql（本人が月曜に流す）の結果・「反映して」
  - チェックインの renotify は PR #90 で済み（チェックインの帳面）
  - 1回目の回は定期の回（PM の指示なし）として呼ばれたが、PM が 20時20分に積んだ指示があったので、そちらをした。PR #88 の CI の実行・コメントは 3回目の回（11/14）の時点でもまだない
- 運用予想を learn_hi に（11/13 17時30分 PM の指示・本人「切り替えて」）：ブランチ data/rot-learn-hi → main 向けの下書き PR #85。報告 docs/pm/report-rot-learn-hi.md（そのブランチ）
  - 移行 166 rot_learn_hi：predict_rotation_v2 が rot_predict('learn_hi', …) を呼ぶ（返す形は今のまま、'method' だけ 'learn_hi'）。表・索引・RLS・採点（3通り）・権限は変えない。先頭に lock_timeout 10s。影響はチェックイン（運用予想の画面）だけ、経営なし。アプリはまだ v2 を呼んでいない
  - 確かめた結果：t106（10項目）・t90（33）・t91・t92（26）通過、番号の重なりなし（156件）
  - **11/13 20時14分 PR #85 が main に入った（4fb2f42）。反映の PR #87（4fb2f42）で main に入り、反映の Actions（run 43415418706、移行164〜167）は 11/13 20時39分に成功し、本番に入った（移行166）**
  - 本人待ち：反映のあとに報告の 3 の読むだけの SQL（method が learn_hi か）
  - この回は定期の回（PM の指示なし）として呼ばれたが、PM が同じ時刻に積んだ指示（11/13 17時30分）があったので、そちらをした
  - 2回目の回（PM が同じ指示を手で呼んだ）：済みだったので、PR #85 の CI・コメント（どちらもまだなし）と帳面の新しい動きだけ見た。変えたものはなし
- 全体の見回りの直し・データの分（11/13 4時 PM の指示・本人「バグや反応しないところを直し、処理速度を早くして」）：ブランチ data/speed-1113b（data/speed-1113 の上に積んだ）→ 下書き PR #81（向き先 data/speed-1113）。報告 docs/pm/report-sweep-1113-data.md（そのブランチ）
  - airport-traffic の見る人の呼び出しは置き場 edge_cache の「traffic:空港」（20秒）を1回読んで返す。前は毎回 位置・線を読んで書き戻していた（4.07秒）。置き場に入れるのは見る人の呼び出しで作った答えだけ（記録の処理の分まで入れると書き込みが倍）。作れないときは5分以内の答え（X-Stale）。Server-Timing に shared・put
  - airport-foreign は「foreign:空港」（60秒）。経路が取れない回は10分以内の答えを出し、取れなかった答えは入れない（_shared/foreign_cache.ts の pickForeign）
  - 移行 165 ops_speed：flight_schedule (dep, std)・(arr, std)、flight_history (dep, svc_date) の索引／airport_board の1時間ごとの数を1回で数える（返す形・値・権限は同じ）。先頭に lock_timeout 10s。表・RLS 変えない。影響はチェックインだけ、経営なし
  - 確かめた結果：t105（14項目、前の airport_board と21通り同じ答え・索引が使われる）、t01・t22・t23・t24・t26・t27・t38・t45・t46・t47・t51・t60・t89・t104 通過、supabase/tests 222本・型の確認 通過、番号の重なりなし（157件）。作り物で羽田 46.5→29.2ms
  - 見立て：app_status・airport_notices・current_events・special_now・ga_recent はデータベースの中は軽く、遅さは距離・順番待ち。airport_tracks は返す量が大きい見込み
  - **反映の PR #87（4fb2f42）で main に入り、反映の Actions（run 43415418706、移行164〜167）は 11/13 20時39分に成功し、本番に入った（移行165 ops_speed）**
  - 本人待ち：speed-check-1113b.sql を反映の後に（前の分はなし）・app_boot（開いた直後の3つを1回で）を作るか
  - この回は定期の回（PM の指示なし）として呼ばれたが、PM が1分前に積んだ指示（11/13 4時）があったので、そちらをした
  - 2回目の回（PM が手で同じ指示をもう一度呼んだ。新しい結果・レビューはなし）：済みだったので livery_board だけ読み直した。reg_legs の主キー（reg, day）で30日分を引き、時刻表・前の30日の埋めは前の日と今日の行だけ（中の条件で止まる）なので、データベースの中の直しはなし。1.5〜1.9秒×4 は同じ呼び出しの重なり（運用予想への依頼のとおり）
- 速さの見直し（11/13 3時15分 PM の指示・本人「処理速度を早くして」）：ブランチ data/speed-1113 → 下書き PR #79。報告 docs/pm/report-speed-1113.md（そのブランチ）
  - 移行 164 edge_cache（key・body jsonb・at。RLS 有効・ポリシーなし＝service_role だけ。上書きのみで約270行、fillfactor 70）。airport-now・metar が「記憶 → 置き場 → 配信元」の順に見る（入れ物ごとに記憶が消えて毎回 ODPT を最長8秒待っていたのを直す）。配信元が取れないときは置き場の古い値。Server-Timing に shared（metar は shared・upstream）。影響はチェックインだけ、経営なし
  - 確かめた結果：t104（27項目）・t01・t100・t103 通過、番号の重なりなし（156件）。supabase/tests 216本通過（edge_cache_test 9本）、全関数の型の確認も通過。読むだけの SQL docs/pm/speed-check-1113.sql の①〜④は手元の Postgres 16 で流れる（⑤は Logs Explorer 用・未確認）
  - 2回目の回（PM が同じ指示でもう一度呼んだ。新しい結果はなし）：airport-traffic の見る人の呼び出しにも Server-Timing（mem・live・adsb・trails）を足して PR #79 に積んだ。型の確認と supabase/tests 216本 通過
  - 見つけたこと（持ち場の外）：アプリ本体 web/index.html は 1.36MB（gzip 396KB）、うち CSS 約333KB。sw.js は本体をいつも網から先に取るので、電波が弱いと毎回待つ
  - **反映の PR #87（4fb2f42）で main に入り、反映の Actions（run 43415418706、移行164〜167）は 11/13 20時39分に成功し、本番に入った（移行164 edge_cache）。airport-now・metar・airport-traffic の Server-Timing が本番で見られる**
  - 本人待ち：speed-check-1113.sql の結果・アプリの開き方と CSS をチェックイン／デザインに回すか
- ヘリポートの種類（11/11 23時45分 PM の指示・本人「ヘリポートも入れる」）：ブランチ data/heliports → 下書き PR #74。報告 docs/pm/report-heliports.md。**11/12 16時32分、移行163とテスト t103 は同じ中身のまま PR #75（チェックイン担当の近くの空港）と一緒に main に入った（3ac3d91）。PR #74 はそれで閉じられた（マージなし）。反映の Actions（run 43176007239）は 17時05分に成功し、本番に入った**。本人の決定：近くの空港と一緒に反映・図鑑は「飛行場・滑空場・ヘリポートの図鑑」に入れる（86 に数えない）
  - 移行 163（airports の extra_kind の決まりに 'heli'、国交省「公共用ヘリポート一覧」（令和8年9月1日現在、002021268.pdf）の公共用12か所を id 5001〜5012・分類 heliport・半径 600m（広島 800m）・ICAO は東京 RJTI と広島 RJBH だけ。位置は OurAirports。airport_yomi に12行）。RLS は今のまま。影響はチェックインだけ、経営なし
  - 国の一覧は公共用12・非公共用83（屋上・病院・県警が大半なので入れない案）・非公共用飛行場3（番外編に入り済み）。一覧に緯度経度はない
  - 確かめた結果：t103（23項目、印の円がほかの194行と重ならない・RLS）・t99・t100・t48・t01 通過、番号の重なりなし（155件）
  - 注意：checkin 関数は extra_kind が空でない行を全部番外編の印にするので、反映するとヘリポートで印が押せる
  - 本人待ち（残り）：非公共用を入れない案でよいか（図鑑に入れると決まったので、印は案A＝押せる、のまま入った）
  - この回は定期の回（PM の指示なし）として呼ばれたが、同じ日の定期の手入れは済み（PR #70）で、PM が1分前に積んだ指示があったので、そちらをした
- 開港（供用開始）と滑走路の表（11/10 1時 PM の指示・本人「すべてOK」）：ブランチ data/airport-facts → PR #59。報告 docs/pm/report-airport-facts.md。**11/10 15時49分 本人が main に入れた（6eebfd4）。同じ時に PR #60（図鑑の作り直し・移行159 airport_yomi）も入り、反映の Actions が 159 → 160 の順に動き、どちらも成功（run 42771079841・42771136800）。airport_yomi と airport_facts は本番に入った**
  - 移行 160（airport_facts：airport_id・opened_year・runways の JSON［name・length_m・width_m・note］・source 'mlit_airport_list'・source_ref（PDF の URL と基準日）・updated_at。RLS は誰でも select、書くのは service_role だけ。airports を cascade）。影響はチェックイン（図鑑の1空港のデータ欄）だけ、経営なし
  - 中身は国交省「空港一覧」（令和8年9月1日現在）の PDF 5つから82空港。年は「空港としての供用開始」の最初の年（滑走路・ターミナルだけの供用開始は数えない。年のない行は前の行の年）。null は羽田・三沢・岩国。行なしは成田・中部・関西・伊丹・千歳（id 91）・番外編
  - 確かめた結果：t100（16項目）・t01・t08 通過、番号の重なりなし。PDF を別の読み方で取り直して92空港の滑走路が全部合った。SQL のテスト全部は報告の 4
  - 本人待ち：「反映して」・羽田の年（案A null のまま／案B「開設 1931年」を別の列で）・国の一覧に載っている番外編の10空港（礼文・福井・小値賀・上五島・慶良間・伊江島・波照間・岡南・大分県央・八尾）を入れるか（10行の値は報告の 6 に書いた）
- 空港の3Dのためのデータ調べ（11/11 18時35分 PM の指示。報告だけ）：ブランチ data/airport-3d-data → 下書き PR #72。報告 docs/pm/report-airport-3d-data.md。表・コードは変えていない
  - 羽田の形：OSM（形。羽田の分を切り出したファイルは派生データベースなので ODbL で公開）＋ PLATEAU（建物の高さ。公共データ利用規約 1.0）。滑走路の端は ops_core の HND_RWY（AIP）を正に。管制塔 115.7m（位置は OSM か AIP の図で）。基盤地図情報は高さなし・承認の要否が不明なので使わない。AIP は二次の資料で「目的を問わず可・AIP は出典不要・運航に使えないと書く」、原文（SWIM）は未読
  - 機体：案A＝airport-traffic に ?view=3d（30km・1万フィート以下と地上、adsb.lol に問い合わせない、要る項目だけ）。画面は45〜60秒遅らせて2つの位置の間をつなぐ。1回 3〜6KB、1人10分で約250KB、データベースは20秒に1回。案B（track_points の再生）は1分に1点で粗い
  - 空：raw に雲量・雲の高さ・気温があり足りる（列は足さない）。日の出入り・薄明は手元で計算（SunCalc は BSD）
  - 機種：FAA Aircraft Characteristics Database（翼の幅・長さ・尾翼の高さ、米国政府のデータ）から羽田の約30機種を手で表に。ダウンロードの中身は未確認
  - 読めなかった：Overpass（羽田の OSM の件数。許可が取れず）・SWIM の原文・FAA のダウンロード
  - 本人待ち：OSM＋PLATEAU でよいか・遅れ約1分でよいか・機種の表の作り方・報告の 5 の SQL（羽田のまわりの機体の数・7日の機種）を流してもらう
- 定期の手入れ 5回目（11/11 水、PM の指示なしの回）：ブランチ maint/2026-11-11 → main 向けの下書き PR #70。報告 docs/pm/maint/2026-11-11-report.md（そのブランチ）
  - 移行 162（maint_1111）：部分索引 flight_history_arr_eta（arr, svc_date。eta30・ata あり・欠航とダイバートでない便）／eta-calib・taxi-out（2分）・flight-watch-cleanup（3分）の仕事の先頭に statement_timeout と lock_timeout。表・関数の中身・RLS・権限は変えない。影響はチェックイン（到着予想・ずれのグラフが速くなるだけ）、経営なし
  - 効き目（本物の Postgres 16・26万4千便）：refresh_eta_calib 約400ms → 約52ms、eta_daily（60日）5〜25ms → 約2ms。索引は1年で約6MB
  - 試してやめた：refresh_eta_calib を1回読むだけに書き直す案（索引があると前の作りの方が速い）
  - flight-watch（1分ごと）は校正をまとめて読み直し、どの読み方も索引に乗っていたので変えない。taxi-out は14日で消える表なので変えない
  - 確かめた結果：t102（11項目）・t38・t45・t46・t51 ほか、SQL のテスト全部（105本）通過、番号の重なりなし（155件）
  - 本人待ち：「反映して」・点検の SQL（5回続けて未着）
- 定期の手入れ 4回目（11/10 月 1時、PM の指示なしの回）：ブランチ maint/2026-11-10 → main 向けの下書き PR #58。報告 docs/pm/maint/2026-11-10-report.md
  - 移行 161（maint_1110）：archive_airport_daily は ops_log をその日の範囲で引く（索引 ops_log_at。2日分 384ms → 19ms・1日 14,611 → 135 ページ）／airport_tracks_put は一時の表と総当たりをなくし1つの文に（入れ替え 7.6s → 2.5s・システムの表の書き込み 0）／rwy_learn_points は json で組み立てる（返す型 jsonb → json。36時間1回で 6.0s・約976MB → 3.3s・約370MB。いつもの5時間を8つに分けた回では効き目は小さい）。表・索引・RLS・権限は変えない。チェックイン・経営への影響なし
  - 確かめた結果：t101（11項目、前の作りと同じ行・値）・t23・t39・t43 通過、番号の重なりなし（153件）。SQL のテスト全部は報告の 3
  - 番号は 161・t101（160・t100 は開港と滑走路の表のために空けた）
  - 案（入れていない）：rwy-learn の8つが同じ5時間を8回読んでいるのを1回にする（点検の結果で rwy-learn が遅ければ）
  - 本人待ち：「反映して」・点検の SQL（4回続けて未着）
  - この回では、PM が 11/10 1時に積んだ「開港と滑走路の表」（data/airport-facts）は始めていない（月曜の定期の回で、PM の指示が付いていなかったため。指示の回で作る）
- 図鑑のための表（11/9 22時50分 PM の指示・本人の図鑑の形の決定）：ブランチ data/zukan-yomi → PR #57。報告 docs/pm/report-zukan-data.md。**11/10 15時49分 main に入った（本人がマージ、550fbda「反映：図鑑の作り直し（PR #60）…索引と読みの表（移行159）」）。本番の Actions の結果はまだ見ていない**
  - 移行 159（airport_yomi：airports の全182行に yomi・index_yomi・alt_yomi・source（official／manual）・source_ref・updated_at。RLS は誰でも select、書くのは service_role だけ。ひらがなと長音だけの決まり、airports を cascade）。影響はチェックイン（図鑑の索引・探す欄）だけ、経営なし
  - 読みは全部手で付けた（国交省の空港一覧・国土数値情報に読みの欄がない）。索引の頭はふだん呼ぶ名前（羽田→は・伊丹→い・小牧→こ・丘珠→お）。公式キャラの名前を含む愛称は alt_yomi に入れない
  - 確かめた結果：t99（26項目）通過、t01・t48・t87・t89・t90・t97 通過、番号の重なりなし。SQL のテスト全部（103本）通過
  - 出典さがし：国交省「空港一覧」の PDF（令和8年9月1日現在。国管理・特定地方管理・地方管理・その他・共用）に滑走路の長さ×幅と沿革（供用開始の年・和暦）。国交省サイトは公共データ利用規約 1.0（CC BY 4.0 互換）＝出典と「加工して作成」を書けばよい。会社管理の4空港（成田・中部・関西・伊丹）と番外編は載っていない。国土数値情報 C28 は滑走路だけで年なし・約款未読。AIP は SWIM 未読のまま
  - 見方の帯の移し方の案：id は今のまま（region＝地方別・map・chron＝行った順）、off.book から tiles・signs・region を外す、選んでいる見方は tiles・signs → region。アプリで読むときに直して fmt 3 で書く（サーバーの行は移行で書き換えない）。数は docs/pm/zukan-view-prefs-check.sql
  - 11/9 2回目の回（PM が同じ指示をもう一度）：済みだったので、出典さがしの残りだけ進めた。その他の空港の PDF は滑走路と供用開始あり（ただし調布 平成13年・名古屋 平成17年のように今の形になった年）→ 画面では「供用開始（国の空港一覧）」と書く案。ヘリポート・飛行場の一覧は名称・所在地・設置管理者だけ → 番外編の公的な出典はなし
  - 本人待ち：「反映して」・索引の頭の字・開港の年を沿革の最初の供用開始にしてよいか（「供用開始」と書く案）・会社管理の4空港と番外編・見方の id の案
- 定期の手入れ 3回目（11/9 月、PM の指示なしの回）：ブランチ maint/2026-11-09 → main 向けの下書き PR #56。報告 docs/pm/maint/2026-11-09-report.md
  - 移行 158（maint_1109）：cold_done は数えるだけ（新しい関数 cold_count、運営だけ）・消した数が控えと違えば全部取り消す／cold_rows は json で組み立てる（返す型 jsonb → json、中身は同じ）。表・索引・RLS・権限は変えない。チェックイン・経営への影響なし
  - 確かめた結果：t98（10項目）・t41・SQL のテスト103本すべて通過、番号の重なりなし（153件）。本物の Postgres 16（全機の航跡1日2万行）で消す前の確かめ 207〜376ms → 18〜22ms・最大メモリ約 213〜242MB → 約 68MB、cold_rows は約 184MB に
  - 実際に移しはじめるのは記録の始まりから400日後（2027年11月ごろ）。今回は先回り
  - 読むだけの docs/pm/maint/cold-day-size.sql（前の日1日の大きさ。索引で引く）
  - 案（入れていない）：全機の航跡のファイルを空港ごとに分ける（cold-tracks の読み出しと cold-archive の作業メモリが小さくなる。2027年11月までに）
  - 本人待ち：「反映して」・案を作るか・cold-day-size.sql を流してもらう
- 表示の設定をサーバーに保存する表（11/8 16時15分 PM の指示・本人の決定「全部乗せ＋自分で隠す」）：ブランチ data/view-prefs → PR #37。報告 docs/pm/report-view-prefs.md。**11/8 18時34分 main に入った（本人がマージ）。11/9 11時45分の「反映」の Re-run（run 42467712581 の4回目）が成功し、本番に入った**
  - 移行 157 user_view_prefs（1人1行・prefs は JSON のもの 16KB まで・fmt・suggest_shown_at・rev・updated_at。RLS は本人だけ select・insert・update・delete、書ける列は prefs・fmt だけ、rev と日時はトリガー、auth.users を cascade で退会で消える）／view_prefs_claim_suggest()（提案を1回だけ。別の端末でも。rev は変えない）
  - delete-account は説明の行だけ（cascade で消える）。admin_backup には足していない（PR #32 の 154 も同じ関数を直すため）
  - 確かめた結果：t97（38項目）・t01・t31・t33・t85・t87・t89・t96 通過、番号の重なりなし
  - 本人待ち：「反映して」（画面の OK のあとでよい）・admin_backup に足すか・上限 16KB でよいか
- 全体のデバッグ（11/7 22時20分 PM の指示）：ブランチ data/debug-1107 → PR #34。報告 docs/pm/report-debug-1107.md。**main に入った（bb23fc5「反映：全体のデバッグ 11/7」、11/8 の回で確認）**。本番の動きは health-check.sql の結果で確かめる
  - **11/9 11時45分の Re-run（run 42467712581 の4回目、main b9fc432）で反映は成功。移行156・関数・アプリは本番に入った**（11/8 16:32 の1回目は SUPABASE_ACCESS_TOKEN の鍵が古くて失敗、本人が差し替えた）
  - adsb.lol の 429：見る人の airport-traffic は live_positions（75秒以内）から作る（移行 156：live_positions に trk を足す。列だけ・RLS 今のまま）。記録の処理は 429・420 で1回だけ待って取り直す（最長5秒）
  - 見つけた抜け：航跡の点と reg_legs を「偶数の30秒の回」だけで残していたので、後半の回にしか取らない南の円（沖縄・奄美・宮古・石垣）がほとんど残っていない見込み → recordPlan（_shared/traffic.ts）で円ごとに決める。本番の数は health-check.sql の「3」で確かめる
  - airport-now：待つ上限（ODPT 8秒・天気5秒・気象庁4秒）・Server-Timing・wx_obs からの代わり。遅さの主な原因は aviationweather.gov の「ためた答えがない1回目が 4〜20秒、ときどき 504」（外から測った）
  - metar：取り直し1回 → 古い通報 → wx_obs（3時間以内）、stale を付ける
  - 長崎・鹿児島の METAR：1時間ごとの発表・夜は出ない（取り込みの抜けではない）
  - 健康診断 docs/pm/health-check.sql（月曜に本人が流す。1つの表、20秒で止まる）
  - 確かめた結果：関数のテスト207本・t96（7項目）・t41・t16・t44 通過。本物の Edge Functions では未確認
  - 本人待ち：「反映して」・便名のない機体が地図から消えてよいか・案A（天気を5分ごとにまとめて取って表に置く）・案B（airport-now の便を flight_schedule から作る）・南の円の抜けを health-check で確かめる
- 撮影記録の表と関数（11/6 22時45分 PM の指示・撮る人用担当の依頼 9-2）：ブランチ data/photo-log → main 向けの下書き PR #32。報告 docs/pm/report-photo-log.md
  - 移行 154（photo_log と RLS：本人だけ select・insert・delete、update なし、auth.users を cascade、unique (user_id, reg, taken_at)、トリガーで分に丸め・未来を断る・1日200行（足した日・日本時間）、created_at は今に固定／photo_candidates(p_iata, p_at)：authenticated だけ、airport_tracks_all＋reg_legs、36時間以内は track_points からも作る（22km 以内のいちばん近い点・6,000ft より下・高さで arr／dep・全機の航跡と30分以内で重なれば外す）、前後20分・20件・登録記号なしは返さない、断る文は not recorded／too old／future／login required／admin_backup に photo_log を1行）
  - テスト t94（38項目）通過。t31・t33・t36・t39・t40・t41・t43・t47・t85 も通過。番号は151件で重なりなし
  - 本人待ち：「反映して」・1日200行を足した日で数えてよいか。仕様との違いは「36時間の境目で両方を見る」だけ（撮る人用担当に伝える）
- 修行担当の依頼（checkin.md の依頼欄）：ANA の時刻表が12月以降も入っているか。timetable-sync を読んだ：日付で絞らず ODPT の期間をそのまま毎日入れる。誤りは前のまま残し result に ANA_error、1,000件ちょうどなら ANA_truncated。判定の表と、短い読むだけの SQL は report-photo-log.md の 4。本人が shugyo-timetable-check.sql（PR #26）を流した結果が来たら、その表で判定して修行担当に返す
- ストアに出す前の外部データの利用条件の見直し（11/6 PM の指示）：ブランチ data/store-terms → 下書き PR #22。文書 docs/pm/store-terms.md（コードは変えていない）
  - 判定：ODPT よい（dc:date の表示がまだ）／adsb.lol よい（作者への連絡が要る。送る文の案あり）／**OpenSky はストアの前に要対応**（研究・非商用向け。おすすめは毎晩の照合を adsb.lol の reg_legs・flight_history に置き換え）／地理院よい（その場で読み込むなら申請不要。地図をアプリに入れたり端末に保存したりしない。配色を変えた旨・淡色地図ズーム5〜8の海岸線の出所を足す）／aviationweather.gov・気象庁よい／AIP はたぶんよい（SWIM のサービス説明書は未読）／特別塗装機よい（planespotters の規約は開けず）
  - 読めなかったページ：ODPT の規約（スクリプトで描くページ）・OpenSky の利用規約・SWIM ポータル・planespotters の規約。ODPT は 11/4 の記録で判定
  - 本人待ち：adsb.lol へのメール・OpenSky をどうするか・ODPT と OpenSky の規約の改定日をブラウザで確かめる・SWIM のサービス説明書を読む・ODPT 第13条3 の扱い（11/4 から）
  - 次の回で読む：adsb.im（海外の便の経路）の条件
- 定期の手入れ 2回目（11/7 土、PM の指示なしの回）：ブランチ maint/2026-11-07 → PR #33 は **11/16 17:54 に閉じられた（マージなし）**。中身は data/redo-1116（PR #108）の移行 174・t113 に入っている。報告 docs/pm/maint/2026-11-07-report.md
  - 移行 155（maint_1107）：cold_candidates を「表ごとに古い方から次の日を索引で1件ずつ引く」形に（新しい関数 cold_days_of、運営だけ）。全機の航跡・ゴーアラウンドは空港ごと、滑走路の記録は取り先ごと。表・索引・RLS・権限は変えない。結果は前と同じ（同じ日・同じ順位は表の名前の順にそろえた）
  - 確かめた結果：t95（10項目、49通りで前と同じ）・SQL のテスト101本すべて通過（t49 も通った）。本物の Postgres 16（64kB・約1.4GB）：古い日200日で 897ms・一時ファイル 10.7MB → 24ms・0。古い日がない今の形でも、前は全機の航跡を丸ごと読んでいた（214ms・約3万ページ）→ 4ms
  - 本人待ち：「反映して」（153 とは別々に入れられる）
- 定期の手入れ（初回・11/6 金、PM の指示なしの回）：ブランチ maint/2026-11-06 → main 向けの下書き PR #18。報告 docs/pm/maint/2026-11-06-report.md
  - 点検の SQL docs/pm/maint/weekly-check.sql（読むだけ・1つの表で出る・20秒で止まる）。本人はまだ流していない（result.csv なし）
  - 移行 153（maint_1106）：データ担当の毎日の処理11本に statement_timeout（30秒〜3分）と lock_timeout 5s（時刻・中身は今のまま、cron の記録だけ 1日→8日）／BRIN 索引4つ（airport_tracks_all.day・rwy_samples.at・ga_events.at・atc_msgs.at）／track_points・live_positions の自動掃除を 2%＋1000行で。表・RLS・権限は変えない
  - 確かめた結果：SQL のテスト101本すべて通過（t93 は29項目。今回は t49 も通った）。本物の Postgres 16（2.1GB の作り物の全機の航跡）で、上限は効いて次のつながりに持ち越さない・移す日の読み出しが 10,137 → 1,170 ページ・候補探しは変わらない（今も主キーの索引だけ読む）・BRIN は 200kB・作るのに1秒未満
  - 見つけたこと：cold_candidates が一時ファイルを使う → 11/7 の回で直した（PR #33）
  - insights-cleanup は移行ではコメントの例だけ。本番にあるかは点検で見る
  - 本人待ち：点検の SQL を流してもらう → eta-calib・taxi-out・archive-cleanup の最長が上限の3分の1以下なら「反映して」をもらう。cron の記録を8日残してよいか
- 運用予想の強化（ブランチ data/rotation-predict → main 向けの下書き PR #6）。報告 docs/pm/report-rotation-predict.md
  - 11/5 夜：main（17b584e）を取り込み、移行を 20261105000152_rotation_predict.sql、テストを t90_rotation_predict.mjs に付け直した。番号の重なりなし（150件）、SQL のテスト98本すべて通過（t90 は28項目）
  - 11/5 夜その2（PM の急ぎの指示）：本番で rotation-backtest.sql を3日分で流したら「53100 No space left on device」で止まった（一時ファイルが入りきらない。データは無事）。軽い版 docs/pm/rotation-backtest-lite.sql を作った（1日・300便・21日・会社で絞れる carrier・先頭に「自動翻訳を切る」と下げ方）。テスト t91（20項目）：60日・42日にすれば今の版と全部の行が同じ数、作業メモリ 64kB の EXPLAIN で一時ファイル 51,537 ブロック → 0
  - 11/5 23時：本人が軽い版を本番で流した（結果は下の節）。learn は当たり率で上、出したうちの当たり率で下
  - 11/6（PM の案への準備）：移行 152 に learn_hi（学んだ便を出すしきい値を3回以上・4割以上に上げたもの）を足し、毎晩 base・learn・learn_hi の3通りを rot_eval に採点するようにした。毎晩の採点は1日500便に下げた。読むだけの docs/pm/rotation-eval-view.sql で3方式を並べて見られる。t90 は33項目・SQL のテスト99本すべて通過。コミット 2955925（PR #6 に push 済み）
  - 11/6 その2（PM の指示：本番に入れる前に毎晩の処理を軽くする）：rot_pairs は前の日の分だけ足す（新しい表 rot_pairs_days に作った日を残し、まだない古い日は60秒の上限の中で新しい日から埋める。移行ではまとめて作らない）。つながりは便ごとに主キーで次の便を1件引く。採点は前の日の300便（rot_eval_nightly(300)）を1便ずつ引いて足す・4分で止める。pg_cron は rot-pairs（日本時間 6:33・statement_timeout 3min）と rot-eval（6:48・5min）に分け、どちらも lock_timeout 5s。rot-learn は外す。しきい値2通り（learn 2回3割・learn_hi 3回4割）と base を同じ便で採点
    - 確かめた結果：新しいテスト t92（25項目、作り物の便9万件・作業メモリ 64kB）で一時ファイル 0（前の作り方は1日で 131,072 バイト）、採点 300便×3通りも 0、前の作り方と同じ行、t90（33項目）・t91（20項目）も通過、SQL のテスト100本すべて通過。コミット e83114a（PR #6 に push 済み）
  - 11/6 その3（PM の指示：時間の上限）：関数に statement_timeout を付ける案は入れなかった（関数の設定は効かない。本物の Postgres 16 で確かめた）。上限は今のとおり仕事の文の先頭（rot-pairs 3分・rot-eval 5分）。本物の Postgres 16（手元・全部の移行を流した上で 400機×5便×45日）で、つながり43日分が約2秒、採点300便×3通りが約79秒（1便約0.26秒、ほとんど rot_predict）。上限で止めると、採点はそこまでの便を残し、つながりは "stopped":"timeout" と残りの日数を返して、どちらもエラーにならない。報告の確かめの SQL を直した（cron.job_run_details に jobname の列はないので cron.job とつなぐ。記録は1日で消える）。t92 に1項目（26項目）。SQL のテスト100本のうち98本は1回目で通過、t42 は流し直して通過（時刻で変わる）、t49 は main でも落ちる（関係なし）。コミット 43228fd（PR #6 に push 済み）
    - 手元の本物の Postgres の立て方：/var/lib/postgresql/t に postgres ユーザーで initdb（scratchpad は権限が戻されるので使えない）。tests/sql の前置き（役割・auth）＋全部の移行を psql で流せる
  - 本人待ち：移行 152 を反映するか（画面は変わらない）。反映した次の朝（記録は1日で消えるのでその日のうち）に、報告の「11/6 その3」の読むだけの SQL を流してもらう。7日たったら rotation-eval-view.sql を流して結果を貼ってもらい、learn／learn_hi／今のままのどれを画面に使うか決める
- 特別塗装機の予定の便を残す（151）・毎日の新規登録の数（150）・退会の精算の支え（147〜149・delete-account）：11/5 21時 main 17b584e に入り、本番に流した（Actions 成功）
  - 本人の判断待ち（残り）：livery_plans を admin_backup に入れるか・確認表の ODPT の行に第13条3を書き足すか／登録数の画面は ops-console/ がリポジトリにないので未（当面は SQL Editor か rpc）
  - PR #9（co/leave-handling 向け）は中身が main に入り済みで開いたまま。閉じるかは本人か経営の判断
- プロフィールの表（data/signup-profile）：本番に反映済み（11/5 17:45）。data/profiles は使わない（消さない）

## 11/6 の分け方の変更
- 運用予想の画面での見せ方は、新しい運用予想担当（yosoku.md）が持つ。予想の計算（rot_*・毎晩の処理・採点）は今までどおりデータ担当

## PM から積んだ次の仕事（11/6 22時半）
- （済み・11/6 22時45分の回）管制の交信の同意の記録・7日で消す作りの見直し：ブランチ data/atc-review → 下書き PR #27。文書 docs/pm/report-atc-data-review.md（report-atc-review.md がまだどこにもないので別のファイル。撮る人用担当がまとめるときに移す）、読むだけの docs/pm/atc-retention-check.sql（手元の Postgres 16 で17行出ることを確かめた）。コード・表は変えていない
  - 結論：7日で消すはおおむね足りる（ただし掃除が1日1回で最長約8日・止まっても気づけない）。同意は足りない：版が残らない・合言葉に期限なし・やめると同意の跡が消え交信は7日まで画面に出る・地域の人数が1人でも見える
  - 案：A1 同意の版（terms_versions に kind 'atc'）と取り直し／A2 やめた記録を8日残す／A3 やめた人・退会した人の交信（heard=1）を消す／A4 地域は3人以上だけ出す／B1 掃除を1時間ごと／B2 出さなかった交信は1日・英語の文字は10分で空に／C 管制だけ止める ops.flags の atc_enabled。おすすめはストアの前に A1・A3・A4・C
  - 本人待ち：どの案を入れるか・やめた人の交信をすぐ消すか・英語の文字を何日残すか・ポリシーにバックアップの残り方を書くか・SQL を流してもらう
- adsb.lol の作者には 11/6 22:24 に旅そらのアカウントから連絡済み。返事が来たら本人から渡す

## PM から積んだ次の仕事（11/8 16時15分）
- （済み・11/8 16時15分の回）表示の設定の表 → PR #37（上の節）


## PM から積んだ次の仕事（11/18 7時45分・本人の実地の報告。急ぎ）【(2) 取り込み側は済み：PR #126・report-atd-future.md。(1) 表示側はチェックイン担当へ依頼・朝一番は本人の答え待ち】
- 乗る便 JL661（羽田 8:05 発）で、7:34 に「出発しました（08:08）」と出た。まだ出発していない。乗る便のカードは renderRide0 の `if(d.atd)` で出していて、atd は inbound_aircraft → flight_schedule.atd → _shared/odpt_status.ts の odpt:actualDepartureTime から来る。未来の時刻が atd に入っている（ODPT の値が見込みなのか、別の日の便に合わせてしまったのかを調べる）
- 11/18 8時15分 本人の確認：実際の出発は 8:08 で、表示の時刻と同じだった。JAL の運航情報は、出発の前から「実際の出発時刻」の欄に見込みの時刻を入れることがある、と考えられる（だから時刻は正しく、「出発しました」の言い方だけがまちがい）
- 直し方の案：(1) 表示側：atd が今より後なら「出発しました」にせず、見込みとして「出発の見込み 08:08」と出す（checkin）。(2) 取り込み側：actualDepartureTime／actualArrivalTime が取り込んだ時刻より後なら atd／ata に入れず etd／eta にする（data）。通知（遅れ・出発）も同じ値を使っていないか確かめる。テストを足す
- ついでに：朝一番の便で前の便がないときの「この便の前に同じ機体が飛ぶ便は、まだ記録が足りず分かりません」は、前の日の夜に着いた機体なら「朝一番の便（前の便はありません）」と出せないか
## 守る決定
- 表を変えるときは移行と RLS をセット／本番への適用は本人の「反映して」のあと
- 航路と機体の記録は消さない／退会では本人の記録を消し、全機の記録は残す
- 外部データは規約の範囲を確かめてから。鍵は直書きしない
- あなたは本番のデータベースにつなげない。本番の数字が要るときは、本人が流す読むだけの SQL を書く
- 本人の決定：規約を改定するときは「terms_versions に1行足す → アプリの定数を変える」の順

## 移行とテストの番号
- main の最新は 160（159 airport_yomi・160 airport_facts は 11/10 本番に入った）。156・157 は 11/9 本番に入った。**maint/2026-11-09 の 158 は main の 159 より前になったので、反映の前に migrations.mjs rebase が要る**。maint/2026-11-06 は 153・テスト t93（fix/co-tests の経営の移行も 153 なので、反映の前に rebase）、data/photo-log は 154・テスト t94、maint/2026-11-07 は 155・テスト t95、data/debug-1107 は 156・テスト t96（関数のテストは supabase/tests/live_view_test.ts。main に反映済み）、data/view-prefs は 157・テスト t97、maint/2026-11-09 は 158・テスト t98、maint/2026-11-10 は 161・テスト t101。data/airport-facts は 160・テスト t100。そのほか次に新しく作るものは 162 以降・テストは t102 以降。**maint/2026-11-11 は 162・テスト t102**（161 の maint/2026-11-10 より後。反映の順が変わったら rebase）。**data/heliports の 163・t103 は 11/12 main に入った（PR #75 と一緒）**。**data/speed-1113 は 164・テスト t104**。**data/speed-1113b は 165・テスト t105**（164 の上）。**data/rot-learn-hi は 166・テスト t106**（関数1つだけなので 164・165 と順番が入れ替わってもよい）。（164〜167 は 11/13 に main に入った。166 は経営の co_cron_timeout、learn_hi は 167 に付け直し）。**data/alert-merge は 168・テスト t107**（11/14 main に入った）。**data/world-ops は 169・テスト t108**。**maint/2026-11-16 は 170・テスト t109**。**data/foreign-collect は 171・テスト t110**（170 と別の関数なので順番は入れ替わってもよい）。（11/16 data/redo-1116 で手入れ6本を 173〜178・t112〜t117 に付け直し、179 odpt_feed_dates・t118、180 verify_arrivals・t119。172・t111 は経営の keiei/redo-1116）。**data/foreign-collect は 181 foreign_cold・t120、182 foreign_watch・t121**。（171〜182 は 11/16 本番に入った。経営の t128 も main にある）。**maint/2026-11-16b は 183・テスト t122**。**data/foreign-livery は 184・テスト t123**。**data/usual-late-rpc は 185・テスト t124**（183 とは別の関数なのでどちらが先でもよい）。data/atd-future は 186・テスト t125。**data/flight-actual は 187・テスト t126**。**data/redo-1120 は 188（maint_1116b の付け直し・テスト t122）・189（inbound_first_of_day・テスト t127）**。**data/adsblol-key2 は 190 track_quota・テスト t129**。**data/sweep-1121 は 191 odpt_feed_at・テスト t130**。**data/livery-dest2 は 192 airline_codes_more・テスト t131**。**193 livery_seen_midnight は main にある。maint/2026-11-23 は 194・テスト t132**。**data/board-bad は 195・テスト t133**。**次に新しく作るものは 196 以降・テストは t134 以降**（t128 は経営が使った。maint/2026-11-16b の 183 は使わない）（data/foreign-carriers・data/foreign-livery は報告だけで番号を使っていない）
- 11/24：data/sweep-all（PR #206）が移行196・テスト t134
- 11/25：data/sweep-1125（PR #216）が移行197・テスト t135（data/stamp-fast #225 は移行なし）
- 11/25：data/hnd-nrt-priority（#227）と data/hnd-nrt-priority-b（#228・別の回の案）がどちらも移行198・t136。入れるのは片方だけ。#228 の A・B を足すなら199・t137
- data/hnd-nrt-more（PR #230）が移行199・テスト t137。次は200・t138 から（#228 の A・B を足すなら200 以降に付け直す）
- main に別の移行が先に入ったら、反映の前にもう一度 `node tools/migrations.mjs rebase`
- 本番は小さいプランで一時ファイルの余裕がない。本人に流してもらう SQL は、大きな中間の表・自己結合・大きな並べ替えを避け、索引で引く形にする
- SQL のテストは全部で約35分かかる（手元で流すときは裏で流してログを見る。t92 だけで約4分。同じログに2回流すと混ざるので、ログの名前を分ける）

## 次にやること
- 羽田・成田の細かいデータ（PR #230・移行199・t137）：向き先は main に直した。反映の前に main に別の移行が先なら rebase。反映のあと hnd-nrt-more-check.sql の 1（次の日）で ground_moves の lost の割合・with_taxi の割合を見て、判定の幅（15kt・2回・5分）を直す。本人の答えでアメダス（よければ表と取り込み・移行200）。次の回の候補は帳面の上の「次の回の候補」
- 羽田・成田の優先（PR #227・移行198・t136）：CI とレビューに答える。反映の前に main に別の移行が先なら rebase。反映のあと hnd-nrt-priority-check.sql の 1 で wx_taf が増え、さかのぼりが 10/15 まで来たか（2日後）。2〜5（実況）と 7（TAF）の結果で、羽田の追い風の上限・粘りの案を PM に。次は data/hnd-nrt-more（PM の指示 11/25 18時50分。一覧 report-hnd-nrt-more.md から。wx_taf はできたので SPECI・アメダス・NOTAM・ODPT のゲート・地上の動きの候補を調べる）
- 羽田・成田（#227／#228）：PM がどちらを本筋にするか決めたら、もう片方を閉じる。#228 の A・B を足すと決まれば #227 の上に移行199 で。当たり具合の結果（check.sql）が貼られたら、羽田の追い風の上限と粘りの案をまとめる
- 印の速さ（PR #225）：反映のあと、本人に stamp-fast-check.sql の 1・2 と Edge Functions の checkin のログ「checkin_ms」を見てもらい、まだ遅ければ getClaims（本人の OK のあと）と初訪問の数の2本を1本にまとめる案を見る
- 見直し B のデータの分（PR #206・移行196・t134）：CI とレビューに答える。反映の前に main に別の移行が先なら rebase。sweep-all-check.sql の 1 を反映の前、2〜4 を反映のあと、4 を次の日（毎時の仕事の時間・失敗）。反映のあと羽田の昼に案内板・短冊・撮る人で先の便が出るか、運用を開いたときの 500（57014）が減ったかを PM に見てもらう。まだ時間切れが出るなら、airport_board の残り（flight_watch の結合・taxi_out_min）を見る
- 今日の遅れの bad（PR #197・移行195・t133。main に入った）：反映の Actions の結果を見る。反映のあと、本番の運用タブで「遅れ」の絞り込みが出るかを PM に見てもらう。本人が「今日」を一日中にすると決めたら見る幅を広げる（hours も変わる）
- AAL176（PR #187）：aal176-check.sql の結果（①航跡 ②reg_legs ③foreign_legs ④livery_notified）を報告に足す。① が 0 件で ③ にあれば、track_points が先に消えた／呼び出し符号が違う（AAL176 以外）かを見る。CI とレビューに答える。公式・報道でアメリカン航空のワンワールド塗装機の一覧が見つかれば出典を差し替える
- 定期の手入れ 11/23（PR #188・移行194・t132）：CI とレビューに答える。反映の前に main に別の移行が先なら rebase。2026-11-23-check.sql の結果（反映の前・次の日）で rwy_samples の全部読みで読んだ行の伸びが止まったか見る。次の月曜の回：結果（*-result.csv）があれば死んだ行・使われていない索引。なければ洗い出しの残り（admin_* の日付の ::date 絞り込み・atc_msgs(feeder)）か、cold-archive の1日の大きさ
- 行き先を便名で（PR #167）：CI とレビューに答える。反映の前に main に別の移行が先なら rebase。反映のあと livery-dest2-check.sql の 2（成田が減り羽田が増えたか）、次の夜のあと 3 を見てもらう。foreign_usual にない便（エア・ドゥ・スカイマークの少ない便）が多ければ、全機の記録の reg_legs から当日の行き先を引く案。Air Japan の NQ は本人の答えで
- 見回り 11/21 の直し（PR #159・main に入った）：反映の Actions の結果を見る。反映のあと（前の値は取れていない）に sweep-1121-check.sql を流してもらい、①で dc:date が入っているか・②の答え・③の traffic の bytes が減ったかを見る。運用を開いたときの Server-Timing（shared・shared-stale・shared-miss）を PM に見てもらい、まだ遅ければ起動の時間を測る案（記録の処理と見る人の関数を分ける。画面の URL が変わるのでチェックイン担当と一緒に）
- 外に返す口の上限（PR #153・main に入った）：チェックイン担当の直し（checkin/track-quota・t155、ログインの鍵を付けて読む）も同じ反映（PR #158）で入ったことを確かめた。あとは本番で空の道すじの古い日がログインして見られるかを PM に見てもらう。adsb.im の条件が分かったら確認表を直し、使えなければ経路の推定を止める案を作る
00000000000000000000000000. adsb.lol の鍵（PR #149）：CI とレビューに答える。本人が鍵を入れたら、ログの「adsb.lol 429」「retry ok」が減ったかを見てもらう。ヘッダー名が違うと分かったら既定を直す。外に返す口の案が決まったら、案1なら移行（airport_tracks の grant・数える小さな表＋RLS・テスト。190 以降・t129 以降）とチェックイン担当への依頼（ログインの鍵を付けて呼ぶ）。adsb.im の条件が合わなければ、行き先を foreign_usual だけにする案
0000000000000000000000000. 見落としの片付け 11/20（PR #146）：CI とレビューに答える。PM が反映するとき main に別の移行が先なら rebase。反映のあと 2026-11-16-2-check.sql で「索引で引いた回数」が増えたか見てもらう。本人が history の線や overnight を決めたら直す
000000000000000000000000. 実際の出発・到着（PR #136）：CI とレビューに答える。「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）、反映の前後に flight-actual-check.sql を流してもらう。本人が決めたら、便名のない便を reg_legs で埋める・31日より前の航跡を cold-archive から埋める（188 以降・t127 以降）
00000000000000000000000. 未来の実際の時刻（PR #126・main に入った）：反映の Actions の結果と、atd-future-check.sql の結果を見る。本人が朝一番の案A を選んだら inbound_aircraft を作り直す（読むだけ。187・t126）
0000000000000000000000. いつもより遅いの関数（PR #118）：CI とレビューに答える。「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）。本人が案内板にも見込みを出すと決めたら live_positions に kt を足す案（移行と RLS・airport-traffic の書き込み）を作る。見張りの関数をつなぐ（0000000000000000000a）ときは eta を着陸の見込み・state.curfew_near で書く
000000000000000000000. 定期の手入れ 11/16 の2回目（PR #111）：2026-11-16-2-check.sql の結果で aircraft・flights の全部読みの回数を見る。「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）、反映後にもう一度流して「索引で引いた回数」が増えたか見る。CI とレビューに答える。次の定期の回の候補：結果が来たら死んだ行・使われていない索引。来なければ、関数の中の「表を全部読む文」（索引のない where）を模擬のデータベースの explain で洗い出す
00000000000000000000. 見落としの片付け（PR #108）：redo-1116-check.sql の ①② が来たら、adsb で確かめられる便の割合を報告に足し、切り替えの案を出す（切り替えるなら VERIFY_SOURCE を設定・照合を pg_cron に戻す移行・出典の一覧から OpenSky を外す依頼）。「反映して」が出たら番号を確かめ、次の日に ③（odpt_feed_dates）を見てもらう。CI とレビューに答える
0000000000000000000a. 海外の便の見張り（PR #104）：flight-watch に foreign_watch をつなぐ（foreign_watch_rows → live_positions の呼び出し符号 → いつもの到着時刻とのずれ15分から・門限の10分前（CURFEW・CURFEW_NEAR）・ダイバート・引き返し → foreign_watch_put → alert_push_claim。gkey は 便名@運航日@出発空港、分からなければ '---'。本文に「（推定）」。出発前の遅れ・欠航は出さない。純粋な関数 _shared/foreign_watch.ts と deno のテスト）
0000000000000000000b. 海外の会社の特別塗装機（PR #102・移行184・t123、作った）：「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）、次の日に livery_notified の I:・Q: の行の数と外への routeset の回数（ログの livery routeset）を見てもらう。本人が外した28機を探し直すと決めたらコモンズの分類で。撮る人用が spot_push を直したら notifyLivery の alliance の例外を戻す。CI とレビューに答える
000000000000000000. 海外の会社の便の実績（PR #104）：foreign-collect-check.sql の結果で1日の回数を見て、多ければ 400日より前を cold-archive に移す案（cold_candidates・cold_rows・cold_done に foreign_legs を足す。消さない）。本人が案A の表の持ち方を決めたら見張り（flight-watch の続き、172 以降・t111 以降）を作る。「反映して」が出たら番号を確かめ、次の日に cron.job_run_details（foreign-legs・foreign-usual）と foreign_legs の行数を見てもらう。CI とレビューに答える
0000000000000000000. 公式の便の情報の元（report-official-flight-sources.md）：本人が試す元を決めたら、その元の一般条件の原文を読み直し、合わせない・長く残さない形で案を作る（表なら 172 以降・t111 以降）。問い合わせると決まったら、ルフトハンザ・スキポールへの文（差出人は旅そら）を書く
00000000000000000. 定期の手入れ 11/16（PR #103）：2026-11-16-check.sql の結果で has_timeout が f の仕事が本番に残っていないか・最長の仕事を見て上限を直す。「反映して」が出たら上の順で rebase。CI とレビューに答える。海外の便の記録は PR #104（171・t110）で作った。PR #101・#102 の案A は 172 以降に読み替え
0000000000000000. 海外の会社の特別塗装機（PR #102）：本人が案を選んだら作る。表なら移行（170 以降）と RLS・テスト（t109 以降）。FR24 の出典の31機は公式・報道・コモンズで探し直す。G-YMMU の公式・報道の出典を探す。撮る人用担当への依頼（spot_push の alliance の扱い）は案3が決まったら
000000000000000. 海外の航空会社の便（PR #101）：本人が案を選んだら作る。案A なら移行170・テスト t109 から（乗る便に選んだ海外の便を adsb.lol で見張る推定の行。RLS つき）。案B・C なら問い合わせ文を直して渡し、返事の条件を原文で読んでから取り込みを作る。SQL の結果が来たら、時刻表にない便の多い会社を報告に足す
00000000000000. 門限の幅10分（PR #100）：11/15 反映の Actions 成功で済み
0000000000000. 海外の止まり具合を作る（PR #93）：本人が FAA の XML を貼ったら faa_nas_test に本物の形を足して読み方を直し、本物の reason で world_reason_ja の表に言葉を足す。world-destinations.sql の結果で US_SERVED を直す。「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）、次の日に cron.job_run_details（world-status）と関数の返す ms・rows・started を見てもらう。CI とレビューに答える
000000000000. 海外の止まり具合の元（PR #92）：仁川・台湾の鍵が来たら活用ガイドの状態の値を読んでから、案3（便の一覧を数える）を作る。ヨーロッパは本人が決めたら EUROCONTROL への問い合わせ文
00000000000. 遅れの通知（PR #88、11/14 の決定も入れ済み）：月曜に本人が流す alert-dup-check.sql の結果で①〜④のどれが多いかを見て、まとめ方を確かめる（③④が0でも害はない）。CI の deno test が落ちたら直す（手元は代わりの道具で流した）。「反映して」が出たら番号を確かめ、次の日に cron.job_run_details（odpt-status-fast・odpt-status・flight-watch）を見てもらい、毎分の回が詰まっていないか・ODPT の問い合わせ数を見る。チェックインの sw.js（renotify）が入ったか確かめる
0000000000. 運用予想 learn_hi（PR #85）：「反映して」が出たら番号を確かめ（main に別の移行が先なら rebase）、反映のあとの SQL の結果を読む。約4週間後（12月中旬、記録が42日そろったら）rotation-eval-view.sql で learn・learn_hi・base を比べ直し、PM に案を出す。運用予想担当の依頼 (1)（predict_rotation を4つ目の方式として採点）・(3)（rot_eval_summary）は本人が決めたら作る。CI とレビューに答える
000000000. 全体の見回りの直し（PR #81）：speed-check-1113b.sql の結果で、①の平均ms が大きい関数があれば索引・まとめ表の直し（166 以降）。④で airport_tracks が大きければ、運用予想担当と返し方（間引く・時間で分ける）の案を作る。app_boot を作ると決まったら関数（テスト付き）を作り、チェックインに依頼。CI とレビューに答える
00000000. 速さの見直し（PR #79・#81、11/13 本番に入った）：speed-check-1113.sql の結果が来たら、遅い文・全部読みの多い表から索引の直し（165 以降）を作る。⑤（Logs Explorer）が動かなければ直す。反映後に airport-now の Server-Timing で shared が数十ミリ秒に収まるか見る。CI とレビューに答える
0000000. ヘリポート（移行163・11/12 本番に入った）：非公共用の地上の数か所を入れると決まったら、新しい移行（164 以降）で足し、印の円の重なりを t103 で見る。**161（maint/2026-11-10）・162（maint/2026-11-11）は main の 163 より前になったので、反映の前に migrations.mjs rebase が要る**
000000. 空港の3D（PR #72）：本人が形・遅れ・機種の表を決め「作って」となったら、Overpass で羽田の OSM の件数を数え、切り出しの手順（ODbL のファイル）と airport-traffic の ?view=3d（テスト付き）を作る。報告の 5 の SQL の結果が来たら読み取りの量を直す。機種の表をデータベースに置くなら移行と RLS をセットで
00000. 開港と滑走路の表（PR #59・11/10 本番に入った）：本人が羽田の年・番外編の10空港を決めたら、新しい移行（162 以降）で直す
0000. 図鑑の表（PR #57）：会社管理の4空港の公的な出典をさがす（国土数値情報の利用約款もまだ）。zukan-view-prefs-check.sql の結果が来たら読む。CI とレビューに答える
000. 表示の設定（PR #37・11/9 本番に入った）：チェックイン担当が prefs の形を決めたら、fmt と上限が合うか見る。「反映して」が出たら migrations.mjs rebase。admin_backup に足すと決まったら PR #32 と順番をそろえて足す
00. 全体のデバッグ（PR #34・11/9 本番に入った）：本人の health-check.sql の結果を読む（南の円の抜け・429 の回数・cron の失敗）。反映されたら、Server-Timing で airport-now のどこが遅いかを PM に測ってもらい、案A／案B を出し直す。adsb.lol の作者の返事が来たら、上限に合わせて記録の間隔を見直す。CI とレビューに答える
0. ストアの見直し（PR #22）：本人が OpenSky を「置き換え」に決めたら、verify_io.ts の取り先を adsb.lol の記録に差し替える案（移行が要らない形）とテストを作る。SWIM のサービス説明書の文が来たら AIP の判定を書き直す。adsb.im の条件を読む
1. 運用予想：本人の「反映して」を待つ（移行 152 だけ。画面はまだ）。反映されたら、次の朝に cron.job_run_details（rot-pairs・rot-eval）の結果をもらい、古い日がどこまで埋まったか・かかった時間を見る。時間がかかりすぎ（採点の legs が300に届かない）なら、rot_eval_nightly の便の数を 200 に下げる案を出す。bgw が on なら、仕事の文の set が効いているかも結果から確かめる
2. 7日分たまったら rotation-eval-view.sql の結果を読み（「記録がそろった日数」を見て、そろった日だけで比べる）、learn と learn_hi のどちらを画面に使うかの案を PM に出す。決まったらチェックイン担当への依頼文（報告の7節）を、使う方式に合わせて直す
3. PR #6 の CI とレビューに答える（11/6 2時の回で確認：CI の実行もレビューもコメントもまだない）
4. 定期の手入れ（PR #18・PR #33・PR #56・PR #58・PR #70）：本人の点検の結果（docs/pm/maint/2026-11-06-result.csv か貼ったもの）が来たら読む。所要時間を見て上限を直すか決める・経営の処理の上限の案（最長の3倍・最小30秒）を作って経営担当への依頼文に入れる・無料枠／プランまでの見込みを出す。CI とレビューに答える
5. 撮影記録（PR #32）：CI とレビューに答える。「反映して」が出たら番号を rebase。撮る人用担当の画面が photo_candidates の断る文を使うか確かめる
6. 時刻表：shugyo-timetable-check.sql の結果が来たら report-photo-log.md の 4 の表で判定（ANA_truncated があれば問い合わせを分ける直しを作る）
7. 管制の交信（PR #27）：本人が案を選んだら、移行 155 以降・テスト t95 以降で作る（migrations.mjs rebase を忘れない）。atc-retention-check.sql の結果が来たら読む
8. それ以外は PM の指示を待つ（勝手に新しい機能は始めない）。毎週月曜の昼の回は、下の「定期の仕事」（次の候補：点検の結果が来たら、死んだ行や使われていない索引の整理・遅い処理。cold-day-size.sql の結果で全機の航跡の1日が 20MB を超えるなら、ファイルを空港ごとに分ける案を作る。rwy-learn と daily-archive は 11/10 に見た（PR #58）。eta-calib・taxi-out・flight-watch は 11/11 に見た（PR #70）。結果がないまま次の回が来たら、ほかの毎晩・裏の処理（timetable-sync・schedule-sync・odpt-status・co3 の SQL の文）を同じ目で見て、時間の上限のない仕事の一覧を作る）

## ほかの担当への依頼
- チェックイン担当（checkin/stamp-fast）へ（11/25）：関数 checkin の名前・送る中身・戻り値は変えていない（PR #225）。画面側の待ち（位置の取得の最大12秒など）はそちらで。反映のあと、印の時間は Edge Functions の checkin のログ「checkin_ms」で見られる
- チェックインへ（11/25 夜の静かな時間・PR #216。PM から checkin.md に写してほしい）：知らせの設定に「夜は知らせない（23時〜7時）」の ON／OFF を1行（はじめ ON）。push-subscribe に `quiet_night: true|false` を付けて送る。文の例「特別塗装機・撮影・運用の知らせを、夜は止めます。乗る便の遅れは届きます」。ゴーアラウンドの「知らせない時間」は別のまま
- チェックインへ（11/24 ピン止めの保存・PR #206。PM から checkin.md に写してほしい）：ログインしているときは rpc('my_pins') で読み、変えたら rpc('my_pins_put', { p_pins, p_spot, p_rev }) で書く（返り値 {ok, rev} か {conflict, pins, spot, rev}）。localStorage はログインしていないときとデモの置き場のまま。はじめてログインしたとき端末にあってサーバーが null なら上げる。「アカウントへの保存は準備中」の文を外す（文はデザイン担当と）。運用の関数が失敗したときの「読み込めませんでした・もう一度」も引き続き要る
- 撮る人用へ（11/24・急がない）：spot_push.ts の題の「そらメモ：」と「（機体の位置からの推定）」は送る直前（tidyPush）でそろうので、そのままでよい。手を入れるときに元の文も「（推定）」にそろえてよい
- チェックインへ（11/21 空の道すじの上限・PR #153。PM から checkin.md に写してほしい）：loadArt の airport_tracks（rpcPost）と cold-tracks の fetch で、ログインしているときは Authorization: Bearer <session の access_token> を付ける（今は anon の鍵）。返り値が配列でないとき、error が login_required なら「8日より前の空の道すじはログインすると見られます」、rate_limited なら「たくさん読んだので、○分（retry_after_min）ほどあとでまた見られます」を小さく出す。未ログインとデモの日付は前の7日までにしてよい。データ側（移行190）と同時に反映する
- チェックインへ（11/20 朝一番の便・PR #146。PM から checkin.md に写してほしい）：inbound_aircraft が first_of_day（true／false）を返すようになった（移行189）。PR #128 の作りのまま読める。first_src（reg・history・null）と、reg のときだけ overnight（前の日に泊まった便：flight・dep・arr・arr_at・arr_src・reg）も返す。出すかは画面案しだい
- チェックインへ（11/20 実際の出発・到着・PR #136。PM から checkin.md に写してほしい）：flights の act_dep_at・act_arr_at・act_src（odpt・adsb・timetable・空）を select に足す。「空の上」は act_src があれば act_arr_at − act_dep_at、なければ今までどおり arr_at − dep_at。adsb・timetable を含むときは「推定を含む」の小さい注記。地図は track があればその線、なければ大圏の線（出典 adsb.lol・ODbL）。画面の形が変わるなら先にデザイン担当の画面案
- チェックイン（11/18・PR #126）：renderRide0 の `if(d.atd)` を「atd が今より後なら『出発の見込み 08:08』」にしてほしい（データ側で未来の atd は来なくなるが念のため）。前の便の行の ib.atd も同じ。朝一番の便の言い方は本人の答えのあと
- チェックインへ（11/17 いつもより遅い・PR #118。PM から checkin.md に写してほしい）：rpc('usual_late', { p_flight, p_land })（登録記号なら p_reg、空港を決めるなら p_arr）。乗る便のカードは flight-live の **land_pred**（eta_pred ではない）を p_land に渡す。返す形と画面の値の対応は docs/pm/report-usual-late-rpc.md の 2。eta が null なら U1n-v2、usual が null なら「いつもの時刻はまだありません」、event があれば札を出さずダイバート・引き返し。出典の1行は note・source をそのまま（時刻表にない便では ODPT を外す）
- 撮る人用へ（11/16 海外の塗装機・PR #102。PM から satsuei.md に写してほしい）：spot_push.ts 48行目の `livery.kind !== "alliance"` を、海外の会社のアライアンス塗装は通すように（`|| !/^JA/.test(livery.reg)`、または _shared/livery_extra.ts の wantsLiveryPush）。直ったらデータ担当が airport-traffic の notifyLivery の例外を戻す
- チェックインへ（11/16 同上）：特別塗装機の知らせの説明に「海外の会社の塗装機は日本のまわりで見えたときに行き先と着く見込み（推定）を1回」を足すか（デザイン担当の画面案のあと）。返す形は変えていない
- チェックインへ（11/16 見落としの片付け・PR #108。PM から checkin.md に写してほしい）：ODPT の便を出す所（空港ページ・運用タブの案内板など）に「ODPT のデータ ○時○分 時点」を出す。空港ページは airport-now の flights.dc_date、ほかは odpt_feed_dates を select（feed は FlightInformationDeparture:JAL・FlightInformationArrival:ANA・FlightSchedule:JAL など。いちばん新しい dc_date）。null なら出さない。画面案はデザイン担当から
- 経営へ（11/16 定期の手入れ・PR #103）：毎日の co3-trouble-detect（20261028000116）に時間の上限がない（166 の co_cron_timeout から漏れた）。経営の移行で `set statement_timeout = '3min'; set lock_timeout = '5s'; select public.co3_trouble_detect()` の形にしてほしい
- チェックインへ（11/15 海外の止まり具合の仕上げ・PR #93 の a33a975。PM から checkin.md に写してほしい）：rpc('world_airport_ops', { p_iata }) の返す形は { source, feed_at, note, notes: {faa, count}, airports: [{ iata, note, feed_at, faa: [{kind, label, reason, reason_ja, starts, ends, avg_delay, max_delay, trend, since}], flights, cancelled, late30 }] }。札とくわしくの言葉は label をそのまま（gdp は「到着の間引き中」）。わけは reason_ja を出し、reason（原文）を小さく添える。出典の文は空港ごとの note を出す（仁川などは FAA の字が出ない）。「○時○分 更新」は feed_at（null なら出さない）。くわしくは report-world-ops.md の 6
- デザインへ（11/15 同上）：feed_at・空港ごとの note・reason_ja・label を足した（W1〜W3 の依頼の分）。描き直しは要らない見込み
- デザインへ（11/14 海外の止まり具合・PR #93）：運用タブの海外の便の札・空港のお知らせの画面案。中身は world_airport_ops の返す形（report-world-ops.md の 1）。出典の文（note）を必ず出す
- チェックインへ（11/14 海外の止まり具合・PR #93）：画面案のあと rpc('world_airport_ops', { p_iata })。出すのは faa が空でないか cancelled・late30 が1以上の空港だけ、の案。乗る便の通知の本文に改行（\n）が入るようになる（sw.js の表示を確かめてほしい）
- チェックインへ（11/13 遅れの通知・PR #88）：renotify は PR #90 で済み。通知の説明の文（乗る便は15分から、空港ごとの遅れは主要空港の門限・0時前後の便だけ、欠航・ダイバート・引き返しはどの空港でも（11/14））が要るかはデザイン担当の画面案で
- 運用予想へ（11/13 learn_hi・PR #85）：predict_rotation_v2 は learn_hi で答える形になった（未反映）。返す形は同じ、'method' だけ 'learn_hi'。画面は今までどおり estimate・next[].src を使い、「予想・保証しない」の書き方は変えない。依頼 (2) の p_mode 引数は、learn_hi に決まったので作らず v2 の中身を替えた
- 運用予想へ（11/13 全体の見回り・PR #81）：(1) livery_board の同じ呼び出し4回を1回に (2) 定時・空の道すじ・ゴーアラウンドは選んだときだけ取る (3) 見方を変えても数分は持っている案内板・お知らせを使う (4) flight_alerts はログインしていない・デモでは呼ばない。案内板と海外の便はサーバー側で速くなる（返す形は同じ）
- チェックインへ（11/13 全体の見回り）：デモでも push-subscribe が呼ばれている。app_boot を作ると決まったら、開いた直後の app_status・airport_notices・current_events を1つの呼び出しに
- チェックインへ（11/13 速さの見直し・PR #79）：src/sw.js の networkFirst（アプリ本体）を、保存した版を先に出して裏で更新する形（または網を3秒だけ待つ）にする案。電波の弱い所で開くのが速くなる。PR #79 が入っても空港の今・metar の返す形は変わらない
- デザインへ（11/13 速さの見直し）：src/index.html の CSS（約333KB・本体の約4分の1）で使っていない決まりの洗い出し
- チェックインへ（11/11 ヘリポート・PR #74）：番外編に種類 heli の12か所ができた（未反映）。EXTRA_RAW に足す12行（3つ目は ICAO がなければ「ヘリポート」）は docs/pm/report-heliports.md の 6。札・色（XKIND・XCOL・--heli）はデザイン担当の画面案で。パタパタは ICAO のない10か所を滑空場・飛行場と同じ扱いに。本人が「印は押せない」（案B）に決めたら checkin 関数の airports の読み出しで heli を外す。出典「国土交通省『公共用ヘリポート一覧』を加工して作成」を出典の一覧に
- デザインへ（11/11 ヘリポート）：近くの空港の並びと番外編の図鑑で使う「ヘリポート」の札と色（昼・夜）
- チェックインへ（11/10 開港と滑走路の表・PR #59）：airport_facts ができた（未反映）。82行を select して手元に持ち、airport_id でつなぐ。年は「供用開始 1988年」と書く（「開港」とは書かない）。opened_year が null か行がない空港（成田・中部・関西・伊丹・千歳・番外編・羽田・三沢・岩国の年）は欄を出さない。滑走路は「A 3,000m×60m」、name が null なら記号なし、note があれば添える（福岡の C・D は奈多地区のヘリポート）。データ欄の下に「出典：国土交通省『空港一覧』を加工して作成」（source_ref の URL へのリンクにしてよい）。くわしくは docs/pm/report-airport-facts.md の 5
- チェックインへ（11/9 図鑑の表・PR #57）：airport_yomi ができた（未反映）。182行を1回 select して手元に持ち、索引は index_yomi を localeCompare(…, "ja") で並べる。探す欄はカタカナをひらがなにしてから、yomi の部分一致・index_yomi と alt_yomi の前方一致。見方の帯は id を今のまま（region＝地方別・map＝地図・chron＝行った順）にし、読むとき off.book から tiles・signs・region を外し、選んでいる見方の tiles・signs は region に、構成 casual と「隠しますか」の提案も合わせる案。くわしくは docs/pm/report-zukan-data.md の 3
- チェックインへ（11/8 表示の設定・PR #37）：user_view_prefs ができた（未反映）。読む＝select maybeSingle（行がない＝全部乗せ）、保存＝upsert({user_id, prefs, fmt})、ぶつかりを見るなら update … where rev = 前の値。提案は rpc('view_prefs_claim_suggest') が true のときだけ出す。「全部乗せに戻す」は行を消さず prefs = '{}' に（消すと提案がもう一度出る）。今ひな形を使っている人は、サーバーに行がなければ端末の見え方を1回だけ上げる案。くわしくは docs/pm/report-view-prefs.md
- チェックインへ（11/7 全体のデバッグ・PR #34）：(1) 運用の画面で metar を待つときに上限（例 8秒）を付け、超えたら「いまは読めません」に切り替えて、ほかは先に出す（11/6 のデモで「気象通報を読み込んでいます…」のまま止まった件）。`stale: true` なら「◯分前の通報」 (2) 長崎・鹿児島など1時間ごと・夜は発表のない空港の出し方 (3) 本人が決めたら、airport-traffic の地図から便名のない機体が消える
- 撮る人用・運用予想へ（11/7）：PR #34 が入ると reg_legs に南の円（那覇・宮古・石垣など）の機体が入り始める。予想の当たり率の比べ方が変わる可能性がある
- 撮る人用へ（11/6 撮影記録・PR #32）：photo_log と photo_candidates ができた（未反映）。候補は上の3件を出し、「ほかの機体」は最大20件。断る文は 'not recorded'（14空港の外）・'too old'（31日より前）・'future'・'login required'。登録記号のない便は返さないので、どれでもないときは手で入れる。仕様との違いは「36時間の境目で両方の元を見る」だけ
- 撮る人用へ（11/6 管制の見直し）：report-atc-review.md をまとめるとき、docs/pm/report-atc-data-review.md（PR #27）の中身を「データの節」として入れてほしい。案 A1 を入れるなら、画面に「同意を取り直す」案内（atc-ingest が 403 reconsent を返したとき）が要る
- チェックインへ（11/6 ストアの見直し）：ODPT のデータを出す所に dc:date を出す（ストアの前に）／地図の出典を全部の地図で地理院タイル一覧へのリンクにそろえ、「配色を変えて表示」を足す
- デザインへ（11/6 ストアの見直し）：アプリの中の「データの出典」の一覧の画面案（文はデータ担当が用意）
- 経営へ（11/6 定期の手入れ）：co-rank・co-size・co-sky と SQL で動く co3-* 15本に時間の上限がない。点検の結果で最長の時間が分かったらデータ担当が上限の案を出すので、経営の移行で `set statement_timeout = '…'; set lock_timeout = '5s'; select …` の形に直してほしい（co3-weather-cleanup も）。月の締め（co3-month-close・co3-season-close）は上限を長め（10分）にするか、失敗したら翌日もう一度動くようにするか決めてほしい
- 経営へ：co3_cs_pay_block で paid_amount に払った額を書き、退会の返金をそちらで計算するよう直す（空の行はいまの計算のまま）。t86 の1行の直しを確かめる。新聞で種類 partner の知らせが出るか確かめる
- 経営へ：tests/sql/t49_co3_seen.mjs の「乗った機体（JA731J）は見た機体の一覧から外れる」が main でも落ちる（11/6 日本時間2時ごろに流した。時刻で変わるテストかもしれない）。確かめてほしい
- 広告へ：登録数は admin_signups_daily（本番に入った）か docs/pm/signups-daily.sql で見られる
- 運用予想から（11/6・急がない。11/13 の本人の決定しだい）：(1) JAL・ANA の機体で画面に最初に出る predict_rotation（しきい値なし）と撮る人の一覧の spot_regs は rot_eval で採点されていない。11/13 の比べに入れるか本人が決めたら、predict_rotation を4つ目の方式として採点に足せるか見てほしい (2) learn_hi に決まったら、predict_rotation_v2 に方式を選ぶ引数（p_mode、既定 learn）を足してほしい (3) 当たり具合を画面に出すと決まったら、rot_eval をまとめて返すだけの読む関数（例：rot_eval_summary(p_days)。1〜4便先の当たり率と日数、方式は画面に使うもの1つ、anon にも実行を許す）を。くわしくは docs/pm/report-yosoku-inventory.md と report-yosoku-1113.md（PR #25）
- 運用予想から（11/8・急がない。11/13 の本人の決定のあと）：塗装ごとの運用予想（本人の依頼）で、1週間あとに「塗装機だけの当たり率」を数えたい。いまの毎晩の採点は前の日の300便をくじで選ぶので、特別塗装機は数便しか入らない。(1) 塗装機の便を必ず採点に入れ（くじとは別に上乗せ）、rot_eval で塗装機の分を分けて数えられるようにしてほしい（印の列か別の小さな表か。登録記号の一覧は liveries.ts にしかなく、livery_sightings は見えた国内の機体だけ）(2) 気づいたこと：rot_predict の「塗装機の予定の便」は、その機体が livery_sightings に一度でも見えて名前が入っているときだけ効く。くわしくは docs/pm/report-livery-predict.md（PR #36）
- 運用予想から（11/15・急がない。本人の決定しだい。PR #95 yosoku/rotation-view-a）：案A の画面は「12回中11回」の形だが、predict_rotation_v2（rot_predict）は便ごとに見た回数 seen と重みつきの割合 share しか返さないので、今は「11回見た」と出している。本人が「12回中11回」にすると決めたら、v2 の next[] に分母（前の便のあとを見た回数。重みなし）を足してほしい。あわせて predict_rotation（時刻表のある JAL・ANA）の seen・of は同じ曜日を2回と数えた点数なので、重みなしの回数も返せると画面の「5回以上」をそろえられる。くわしくは docs/pm/report-rotation-view-a.md の「本人に決めてほしいこと」1・2

## 11/5 23時 本番での比べた結果（軽い版、前の日1日・300便・見る日数21日）
- 当たり率（当たり÷基準の数）：learn が base を全部の段で上回った。1便先 84.7 / 83.3、2便先 68.6 / 65.4、3便先 70.9 / 63.8、4便先 60.8 / 54.4
- 出したうちの当たり率は learn が下がった：1便先 89.1 / 91.6、2便先 74.3 / 80.7、3便先 75.6 / 79.4、4便先 66.7 / 70.5（予想を出す数が増えたぶん外れも増えた）
- ANA の2〜3便先で差が大きい（2便先 66.7 / 55.6）。JAL はほぼ同じ。特別塗装機の予定の便は1件で当たり
- learn が今の仕組みに戻した便（src=base）の出したうちの当たり率は1便先 82.4%（base 自身の 91.6% より低い＝難しい便）
- PM の案：移行（rot_pairs・rot_eval・毎晩の採点）だけ先に反映し、画面は今のまま。本当の日数（60・42）で7日分の rot_eval がたまってから画面を切り替えるか決める。あわせて、learn だけで出す便のしきい値（2回以上・3割以上）を上げると出したうちの当たり率が戻るかを、rot_eval で見られるようにする

## 定期の仕事（毎週月曜の昼の回。PM の指示が付いていない回はこれをする）
本人の依頼（11/6）：定期的にデータの整理と圧縮、処理の高速化をしてほしい
1. 見る：本人が SQL Editor で流す読むだけの SQL は docs/pm/maint/weekly-check.sql（11/6 に作った。今は maint/2026-11-06 にある。足りない項目があれば直す）。中身：表ごとの大きさ・行数の見込み・伸び、使われていない索引、死んだ行の多い表、pg_cron の各処理の所要時間と失敗（cron.job_run_details の前の7日）、pg_stat_statements があれば遅い文の上位10。重くしない（一時ファイルを使わない形）
2. 本人がその週の結果を docs/pm/maint/<日付>-result.csv に貼っていれば、それを読む。なければ前の週の結果と、リポジトリの移行・関数を読んで判断する
3. 直す案を3つまで選ぶ（効き目の大きい順）：
   - 整理：使われていない索引・重複した列や表・古い作りの残り
   - 圧縮：型を詰める・同じ値をまとめる・古い日を cold-archive に早めに移す（ファイル置き場に移して読めるようにする。**記録は消さない**。「航路と機体の記録は消さない」を守る）
   - 高速化：遅い関数・毎晩の処理の索引・まとめ表・一時ファイルを使わない書き方
4. ブランチ maint/<日付> に移行（RLS もセット）とテストを置く。main と本番には入れない
5. 報告は docs/pm/maint/<日付>-report.md：先週と比べた大きさ・遅い処理・直す案（効き目と危なさ）・本人に流してほしい SQL
6. Supabase の無料枠・今のプランの上限まで、あとどのくらいで届くかの見込みも毎回書く

## 11/6 10:20 反映済み（main 15b2174）
- data/rotation-predict（移行 152：rot_pairs・rot_pairs_days・rot_eval、毎晩の rot-pairs 6:33・rot-eval 6:48、日本時間）を本番に流した。Actions はすべて成功。画面は変わらない
- 次：11/7 の朝に本人が cron.job_run_details を見る SQL を流して貼る → 初めの夜が動いたか確かめる。11/13 ごろに docs/pm/rotation-eval-view.sql で7日分を比べ、画面に learn・learn_hi・今のままのどれを使うか決める

## PM から（11/9 15時40分）
- #34 の航跡の直しは本番で確かめた：11:50〜15:37 の約227分で、点のある分は 北226・南225・東227・西227。沖縄と北海道の抜けは直った。来週月曜の health-check で 24時間の「3 抜け」が「よい」になるかをもう一度見る

## PM から積んだ次の仕事（11/9 22時50分、図鑑のための表）
（済み・11/9 22時50分の回 → PR #57。上の節）本人が図鑑の形を決めた（CLAUDE.md「11/9 の決定」の図鑑の形）。表を作る前に移行と RLS をセットで、ブランチで止まる
1. 86空港と番外編の「名前の読み」（ひらがな）の表。索引の50音順と、探す欄の読みで当たるのに使う。出典（国土交通省の空港一覧など）と、手で付けた読みかを列で分ける
2. 開港の年・滑走路の本数と長さの出典さがし：使える公的な一覧と利用条件（転載・加工してよいか）を外部データの確認表の形で調べて報告（表はまだ作らない。本人が出すと決めるまで画面には出さない）
3. 11/8 の user_view_prefs で、見方の帯の ON／OFF（タイル・案内標・地方・年代記）を保存している人の設定を、新しい3つ（地方別・地図・行った順）へ移す方法の案（年代記→行った順、タイル・地方・案内標→地方別はいつもなので消す、など）。チェックイン担当が作るときに使う

## PM から積んだ次の仕事（11/10 1時、開港と滑走路の表）
（済み・11/10 の回 → PR #59。上の節）
本人「すべてOK」：開港と滑走路を出してよい（CLAUDE.md「図鑑のデータ」）。data/zukan-yomi とは別のブランチ data/airport-facts で
- 表 airport_facts（airport_id・opened_year（供用開始の西暦）・runways の JSON（名前・長さ・幅）・source・source_ref（PDF の URL と基準日）・updated_at）を移行と RLS（誰でも select、書くのは service_role だけ）とセットで
- 中身は国土交通省「空港一覧」（令和8年9月1日現在）の PDF から。和暦を西暦に。会社管理の4空港（成田・中部・関西・伊丹）と番外編は空欄（行を作らないか null）
- 画面の出典の文「出典：国土交通省『空港一覧』を加工して作成」をチェックイン担当へ帳面で伝える
- テストを足す。下書き PR で止める

## PM から積んだ次の仕事（11/11 18時35分、空港の3Dのためのデータ調べ）
（済み・11/11 の2回目の回 → PR #72。上の節）
本人の決定「空港の3D」（CLAUDE.md）。まず調べて報告だけ（表はまだ作らない）。docs/pm/report-airport-3d-data.md
1. 羽田の形の出どころ：滑走路（今の OPS_AIRPORTS の rwy）・誘導路・エプロン・ターミナル・管制塔の位置と高さ。候補は OpenStreetMap（ODbL：出典の表示と、加工したデータを配るときの決まり）、国土地理院の基盤地図情報、AIP（転載の可否）。それぞれ「使ってよい形・出典の書き方・注意」を外部データの確認表の形で
2. 機体：live_positions／track_points から羽田のまわり（半径30km・高さ1万フィート以下など）を少し遅らせて出す読み方の案と、1人が開いたときの読み取りの量（今の adsb.lol の利用の範囲で、新しく外へ問い合わせないこと）
3. 空：今の wx_obs／metar の値で足りるか（雲量・視程・霧・風）。日の出入りの計算は手元でできるか
4. 3D の機種の形を作るのに要る情報（機種ごとの大まかな長さ・翼の幅）を、どこから取るか（公的・自由に使えるもの）

## PM から積んだ次の仕事（11/11 23時45分、ヘリポートの種類）
（済み・11/11 23時45分の回 → PR #74。上の節）
本人「ヘリポートも入れる」（近くの空港の並び。CLAUDE.md「近くの空港の細かい所」）。番外編（XA）にヘリポートの種類を足す案：出どころ（国土交通省の空港等一覧の「ヘリポート」・公共用ヘリポート）と規約、何か所あるか、今の kind（mil・secret など）にどう足すか。表を変えるなら移行と RLS をセットで、ブランチ data/heliports、下書き PR で止める

## PM から積んだ次の仕事（11/13 3時15分、速さの見直し）
（済み・11/12 の回 → PR #79。上の節）
本人「処理速度を早くして」。調べて案（直すのはブランチと下書き PR、本番は「反映して」のあと）。報告 docs/pm/report-speed-1113.md
- Edge Functions（airport-now・airport-traffic・metar など）の Server-Timing と、遅い問い合わせの候補（EXPLAIN できる範囲で、本人に流してもらう読むだけの SQL も）
- 毎晩・毎分の処理（pg_cron）の時間の伸び方。索引の足りない所、使っていない索引
- アプリが最初に読むデータの量（図鑑・近くの空港・ヘリポートを足して増えた分）。小さくできる所
- 効き目の大きい順に、直し方と危なさを並べる

## PM から積んだ次の仕事（11/13 4時、全体の見回りの直し）
（済み・11/12 の回 → PR #81。上の節）
報告の元：kaizen/sweep-1113 の docs/pm/report-sweep-1113.md（写真は docs/pm/report-sweep-1113-shots/）と data/speed-1113 の docs/pm/report-speed-1113.md。本人「一度すべてを見てバグや反応しないところを直し、処理速度を早くして」。不具合の直しなので画面案は要らない。見た目が変わるもの（大きさ・並び）は最小にし、変わる所は写真を報告に貼る。ブランチと下書き PR、main と本番には入れない。速さの見直し（data/speed-1113）の続き。同じブランチか data/speed-1113b
- 運用を開いたときに遅いもの：airport-traffic 4.07秒・airport-foreign 3.85秒・airport_board 3.80秒・airport_ontime 3.38秒・airport_tracks 3.24秒・special_now 2.99秒・ga_recent 2.31秒・livery_board 1.5〜1.9秒。edge_cache（移行164）を使える所は使い、RPC は索引と問い合わせの見直し（読むだけの SQL で本番の EXPLAIN を本人に頼む形）
- 開いた直後の app_status・airport_notices・current_events がそれぞれ 1.0〜1.6 秒。小さい表のはずなので原因を
- 測ったのはアメリカから。日本からの時間は短い見込み。直す前と後を同じ場所で比べる

## PM から積んだ次の仕事（11/13 17時30分、運用予想を learn_hi に）
（済み・11/13 17時30分の回 → PR #85。上の節）
本人「切り替えて」。predict_rotation_v2 は今 rot_predict('learn', …) を呼んでいる。'learn_hi' にする移行を（返す形は同じ、'method' も 'learn_hi' に）。表は変えないので RLS の変更はなし（関数の権限は今のまま anon・authenticated に実行だけ）。テストを足す。ブランチ data/rot-learn-hi、下書き PR。運用予想担当が画面の呼び出しを v2 に替える（yosoku.md）。約4週間後（記録が42日そろったら）に rotation-eval-view.sql で比べ直す

## PM から積んだ次の仕事（11/13 20時20分、遅れの通知を1つにまとめて、すぐ知らせる）
（済み・11/13 の回 → PR #88。上の節）
本人「飛行機の遅れが二重にくる時があるので、きちんとまとめて、遅れが発生次第通知が来るようにして」。決定事項（11/13 遅れの通知）に従う。通知の送り手（alert_push.ts・flight-watch・odpt-status・flight_alerts）はデータ担当の持ち場。ブランチ data/alert-merge、下書き PR、本番には入れない。
二重になりうる所（PM が読んだ見当。まず本番の flight_alerts の重なりを読むだけの SQL で確かめて報告に）
- delay_dep と delay_arr が別の種類なので、1つの遅れで2回届く
- flight-watch の推定の遅れのあとに odpt-status の公式の遅れが来ると、両方届く（official のときだけ推定を止めている）
- 同じ便が flight_schedule に複数行（共同運航・時刻表と運航情報のずれ）あると schedule_id ごとに届く
- tag が `fw-便名` で日付がないので、端末によっては重なって鳴る
直し方
1. 通知の単位を「便名＋運航日」の1件にまとめる（共同運航は運航する便に寄せる）。種類が違っても、同じ便の遅れは1つの通知。新しく分かったこと（公式の時刻・遅れが30分以上ふえた・欠航・ダイバート）だけ、同じ tag で上書きして知らせる。それ以外の小さい変化では鳴らさない
2. 目安：「この便に乗る」（push_subs.flights）の人は15分から、空港（push_subs.airports）の人は60分から。今は両方60分
3. すぐ知らせる：odpt-status は5分ごと。乗る便に選ばれた便だけ毎分見るなど、出てから知らせるまでを短く（ODPT の利用の範囲で。呼ぶ回数の目安を報告に）
4. 送った記録（どの購読に・どの便の・どの中身を送ったか）を残し、同じ中身を二度送らない。表を足すなら移行と RLS をセットで（読めるのは関数だけ）
5. テスト：推定→公式、出発→到着、共同運航2行、同じ遅れの繰り返し、15分と60分の分かれ目、遅れが30分ふえたときの上書き
影響：チェックイン（通知を受ける側の画面は変えない。乗る便の目安15分の一文がアプリに要るなら checkin.md に依頼）。経営は関係なし

### PM の追記（11/13 20時25分、空港ごとの通知の中身）※data/alert-merge の続きで必ず入れる
（済み・2回目の回 → PR #88 の b4d9528。上の節）
本人「通知がくるのは主要空港がいいな、門限ギリギリになりそうな便とか0時に着くような便とか」。空港ごとの通知（push_subs.airports）は「60分以上の遅れ全部」をやめて、次に絞る（乗る便の15分はそのまま）
- 対象の空港：主要空港（案：羽田・成田・関西・伊丹・中部・新千歳・福岡・那覇）。選んでいない空港・主要でない空港の便は、乗る便に選んだときだけ
- 門限ギリギリ：着く空港の運用時間の終わり（例：伊丹・福岡など）に対して、見込みの到着が終わりの30分前より遅い便。間に合わないと出発空港へ引き返し・ほかの空港へ回る、まで書けるなら書く（推定と書く）。運用時間は空港の公式・国交省の原文を開いて確かめ、URL と日付を残す。表で持つなら移行と RLS をセットで
- 0時前後に着く便：遅れのせいで、見込みの到着が 23時30分〜翌1時に入った便（定刻なら0時より前だった便）
- 1つの便は1つの通知にまとめる決まり（決定事項）はそのまま。文の例：「伊丹の門限（21時）に間に合わないおそれ：JL○○ 羽田→伊丹、到着の見込み 20時52分（約65分遅れ）」

## PM から積んだ次の仕事（11/14 9時40分、遅れの通知の仕上げ）
（済み・11/14 の回 → PR #88 の c45147d。上の節）
本人「すべてOK」：①毎分の回（odpt-status-fast）を入れる ②主要でない空港を選んだ人にも、欠航・ダイバート・引き返しは届ける（今の下書きは主要空港だけ。ここを直す。遅れは主要空港の門限・0時前後だけのまま）③主要8空港・門限の30分前からでよい。data/alert-merge に足し、テスト（t107・alert_merge_test）に主要でない空港の欠航が届く形を足す。SQL の重なり確認は本人が月曜に流す

## PM から積んだ次の仕事（11/14 21時10分、海外の空港の地上待機・止まっている情報）
（済み・11/14 の回 → PR #92。上の節）
本人「いいねぇ、ヨーロッパとか日本から就航してる空港も欲しいね」。11/14 朝（日本時間）の全米の地上待機（FAA）をそらメモが拾えなかった。今回は調べて案まで（取り込みのコードはまだ作らない。画面はあとでデザイン担当）。報告 docs/pm/report-world-ops-sources.md（ブランチ data/world-ops-sources、下書き PR）
- 対象：日本から直行便のある海外の空港（アメリカ・ヨーロッパ・韓国・台湾・中国・香港・東南アジア・オセアニア・中東など）。world_airports.ts と今の海外の便の取り込みから、就航している空港の一覧を作る
- 地域ごとに、空港の止まり具合（地上待機・出発の間引き・閉鎖・大きな遅れ）を出している公式の元を探す。例：アメリカ FAA の NAS Status（nasstatus.faa.gov）、ヨーロッパ EUROCONTROL（Network Manager の公開の情報）、各国の航空局・空港会社の公開の情報、NOTAM
- 元ごとに：取れる中身・更新の間隔・取り方（公開の API か、画面か）・利用規約（アプリに出してよいか・出どころの書き方・商用・回数の制限）を原文で確かめ、URL と調べた日を書く。規約で使えないもの・画面を自動で読むしかないものは「使わない」と書く
- 使えるものから、どう出すか（運用タブの海外の便・空港のお知らせ・乗る便の通知に「アメリカで地上待機中（FAA）」など）の案と、取り込みの手間・回数の目安を、効き目の大きい順に

## PM から積んだ次の仕事（11/15 0時10分、海外の空港の止まり具合を作る）
（済み・11/14 の回 → PR #93。上の節）
本人「OK」（report-world-ops-sources の案1・2。決定事項【11/15】）。ブランチ data/world-ops、下書き PR、本番には入れない
1. FAA NAS Status（https://nasstatus.faa.gov/api/airport-status-information）を2分に1回読み、日本から直行便のあるアメリカの空港だけ残す。表 world_airport_status（iata・source・kind・reason・starts・ends・avg_delay・fetched_at）を移行と RLS（誰でも select、書くのは service_role）で。終わったものは数日で消す。取れないとき・古いとき（Update_Time が10分より前）は出さない
2. 乗る便の通知（alert_merge）：着く空港か出る空港が地上待機・閉鎖・出発の間引きなら、1つの便の1つの通知に1行足す（「到着地ロサンゼルスで地上待機中（FAA・○時まで見込み）」）。はじめて分かったときは上書きで知らせる。新しい通知は増やさない
3. 今ある JAL・ANA の国際線（flight_schedule・odpt-status）を、海外の空港ごとに「今日の欠航○便・30分以上の遅れ○便」に数える関数（anon・authenticated に実行だけ）
4. 画面で使う関数（空港ごとの止まり具合を返す）を用意。画面はデザイン担当の案のあと、チェックイン担当が作る
5. 出典の書き方「出典：FAA NAS Status。運航の判断には使えません。遅れることがあります」を返す中身に入れる。テストを足す。影響：チェックイン（運用・通知）。経営は使わない

## PM から積んだ次の仕事（11/15 12時40分、海外の止まり具合の仕上げ）
（済み・11/15 の回 → PR #93 の a33a975。上の節）
本人「A」（決定事項【11/15】見せ方は案A）。data/world-ops（#93）に足す：①world_airport_ops に feed_at（FAA の発表の時刻）②note を「FAA がある空港用」と「便の数だけの空港用」に分ける ③FAA の reason の日本語の表（例 WEATHER / LOW CEILINGS → 天候（低い雲）。ないものは原文）④gdp の言葉は「到着の間引き中」（通知の文も）。チェックイン担当が画面を作るので、返す形が決まったら checkin.md に書く

## PM から積んだ次の仕事（11/15 19時25分、門限ギリギリの幅を10分に）
（済み・11/15 の回 → PR #100。上の節）
本人「遅れの通知は着く10分前から通知して」→「門限ぎりぎりになるやつ」。門限ギリギリの知らせの幅を「見込みの到着が門限の30分前より遅い」から「門限の10分前より遅い」に変える（主要8空港・空港ごとの通知と乗る便の通知の両方。0時前後・欠航・ダイバートはそのまま）。定数を1か所にし、テスト（門限の11分前は出ない・9分前は出る・過ぎたら出る）を直す。ブランチ data/curfew-10、下書き PR、本番には入れない

## PM から積んだ次の仕事（11/16 10時50分、海外の航空会社の便も遅れの通知の対象に）
（済み・11/16 の回 → PR #101。ODPT の空港会社のデータはチャレンジ限定で使えないので取り込みは作らず、案を報告。上の節）
本人「進める」。今の schedule-sync は OPERATORS = ["JAL","ANA"] だけなので、BA5・LH716 など海外の航空会社が運航する羽田・成田の便は flight_schedule に入らず、乗る便の通知も門限・0時前後・欠航の知らせも出ない（11/16 朝 BA5 は約38分遅れ、LH716 はゴーアラウンドらしい動き）。
- ODPT の空港ビル会社の発着情報（羽田の国際線・成田など、全航空会社の便。事業者の名前と中身は ODPT の一覧で確かめる）を取り込み、海外の航空会社の便も flight_schedule・odpt-status に入れる。共同運航は運航する会社の便に寄せる（alert_merge の決まりのまま）
- まず ODPT の利用の範囲（その事業者のデータの条件・出典の書き方・回数）を原文で確かめて報告に。使えないものは使わない
- 乗る便に選べるか（アプリの便の検索で海外の航空会社の便が出るか）を確かめ、画面側が要るなら checkin.md に依頼
- 表を変えるなら移行と RLS をセットで。テストを足す。ブランチ data/foreign-carriers、下書き PR、本番には入れない

## PM から積んだ次の仕事（11/16 10時55分、海外の航空会社の特別塗装機が来るのも知らせる）※海外の航空会社の便の取り込みの次に
（済み・11/16 の回 → PR #102。案を報告。上の節）
本人「海外の塗装機が来るのも通知に出したい」（例：11/16 BA5 G-YMMU ワンワールド塗装）。今の特別塗装機の知らせ（livery_sightings・livery_notified・livery_plans、odpt-status の「〇〇で運航いたします」）は国内の会社の機体だけ。
- 日本に来る海外の会社の特別塗装機（アライアンス塗装・記念塗装など）の一覧の元を探す。登録記号ごとに持てる、規約で使える元だけ（Flightradar24 の画面やデータは使わない。会社の公式の発表・ウィキメディアなど条件の分かるもの・本人が手で足す表）。一覧の持ち方（表・移行と RLS）を案に
- 来るのを見つける：adsb.lol の全機の記録（reg_legs）で、一覧の登録記号が日本の空港へ向かっているときに、その空港の特別塗装機の通知を申し込んでいる人へ1回（今の livery_notified の決まりに合わせ、二重にしない）。到着の見込みの時刻も
- 撮る人の「つぎに来る注目の機体」・特別塗装機の欄にも出すなら、撮る人用担当（satsuei.md）への依頼を書く
- まず調べて案（元と規約・手間）を報告に。ブランチ data/foreign-livery、下書き PR、本番には入れない

## PM から積んだ次の仕事（11/16 11時40分、海外の航空会社の便のデータを自分で集める）
本人「海外のデータも収集したい」。report-foreign-carriers の続き。正式な元（TIAT・成田）が使えないので、今使ってよい元（adsb.lol の全機の記録・adsb.im の経路）から、日本の空港に発着する海外の会社の便を自分で集めて残す案と、作れるところまで。ブランチ data/foreign-collect、下書き PR、本番には入れない
- 集めるもの：便名（コールサインから）・登録記号・機種・出発／到着の空港・実際の離陸／着陸の時刻（位置から推定）・ダイバート・引き返し。reg_legs と同じ考えで、海外の会社の分も漏れなく残す（今 reg_legs に入っている範囲・入っていない範囲をまず確かめる）
- 集めた実績から「いつもの時刻」（曜日ごとの便名の到着・出発の時刻の中央値）を毎晩作り、定刻の代わりの「いつもより○分遅い（推定）」を出せるようにする。記録が少ない便は出さない
- 乗る便に選んだ海外の便の見張り（report-foreign-carriers の案A：門限ギリギリ・ダイバート・引き返し）も、この記録の上に作る
- 表を足すなら移行と RLS をセット（誰でも select でよいか、関数だけか）。航路と機体の記録は消さない。adsb.lol・adsb.im の規約と回数の範囲を報告に（adsb.lol の作者への連絡が要るならその文案）
- 影響：チェックイン（乗る便・運用の海外の便）・撮る人（海外の塗装機）。経営は使わない

## PM から積んだ次の仕事（11/16 11時55分、アメリカ・ヨーロッパの公式の便の情報の元）※data/foreign-collect と一緒に【済み：report-official-flight-sources.md】
本人「アメリカとか、ヨーロッパの公式の情報サイトないの？」。空港の止まり具合ではなく、便ごと（定刻・変更時刻・状態）の公式の元を、規約の原文で確かめる。報告に1表（元・中身・登録の要否・無料か・アプリに出してよいか・出典の書き方・回数）
- アメリカ：FAA SWIM（SCDS。登録すれば無料。TFMS の便の情報＝アメリカの空の便の計画と到着の見込み。日本行き・日本発の便がどこまで入るか、一般のアプリで使ってよいか）
- 航空会社の公式 API：Lufthansa Open API（便の状態・時刻表。LH716 など）、Air France-KLM の開発者 API、British Airways・ほかの会社にあるか。日本に来る主な会社から
- 空港の公式 API：アムステルダム・スキポールの Flight API（登録して使う。条件の頁あり）、フランクフルト・ほかの空港
- 使えるものは、アカウントを作るのは本人（旅そら）。鍵は Supabase の秘密の設定に本人が入れる（コードに書かない）

## PM から積んだ次の仕事（11/16 14時、海外の便の見張りと特別塗装機。本人「おすすめ」）【1 は PR #104 に表まで（見張りの関数へのつなぎは次）・2 はまだ】
決定事項【11/16】の2つ。本番の数（本人が流した SQL、11/16）：海外の会社など 1日 1,552回・1,346便・29空港（日本の会社 3,723回）。ゴーアラウンドは LH716 を 10:24 に見つけている（34L・375ft、10:50 に降り直し）。push_subs は全部で1件（空港1・乗る便0）。flight_alerts の「出発と到着の両方」634 は案内の記録で、通知は alert_push_log で1便1件。経営の夜の処理はいちばん長くて co3-legs-check 34秒（上限の中）。毎分・2分ごとの回はすべて succeeded。
1. data/foreign-collect の続き：①ODPT にない日本の会社も入れる（japan の見分けを「ODPT の会社か」に）②乗る便の見張りは小さな表 foreign_watch（移行と RLS）で、alert_merge・alert_push_log の決まり（1便1件・上書き）に合わせる ③表の大きさ：1年約140MB の見込みなので、foreign_legs は180日より前をファイル置き場に移す（消さない・読めるように）案を入れる
2. data/foreign-livery の続き：案1-A（表 livery_extra、本人が Table Editor で足せる。移行と RLS）・案2-A（日本のまわりで見えたら行き先と着く見込みを1回知らせる）・案3-A（海外の会社のアライアンス塗装だけ知らせる）・FR24 出典の31機の差し替え（見つからないものは外す）。撮る人用担当への依頼（spot_push の kind !== "alliance"）は satsuei.md に書く
どちらも下書き PR、本番には入れない。公式の元の表（report-official-flight-sources）が先でよい

## PM から積んだ次の仕事（11/16 14時10分、見落としの片付け。本人「OK」）【済み：PR #108・report-redo-1116.md】
一覧は docs/pm/board/overlooked-1116.md。作ったのに main に入っていない直しを、今の main に取り込み直して（番号・テストの名前のぶつかりも直して）、新しいブランチの下書き PR に。本番には入れない。古い PR は「入れ直したので閉じてよい」と報告に書く。ブランチ data/redo-1116
1. 定期の手入れ6本（#18 153・#33 155・#56 158・#58 161・#70 162・#103 170）を、今の main の次の番号に付け直して1本のブランチに（書いた順のまま。create or replace で関数の設定が消えないよう最後に 170 の中身）。#21 も 153 を使っているので経営担当と番号を分ける
2. ODPT の dc:date：取り込むたびにデータの時刻を残し、画面が読める形で返す（チェックイン担当が出す）
3. OpenSky の置き換え（ストアの前に要る）：track・traffic・verify・daily-archive で使っている所を adsb.lol（reg_legs・flight_history）に置き換える案と、できるところまで

## PM から積んだ次の仕事（11/17 12時20分、いつもより遅いの画面に要る関数）【済み：PR #118・report-usual-late-rpc.md】
本人「OK」（決定事項【11/17】いつもより遅い）。design/usual-late の report（1版・2版の「データ担当へ」）のとおり、飛行中の見込みを画面から読める関数（便名・登録記号から「いつもの到着」「見込みの到着」「いつもより○分」「出典」「dow と spread」）を anon・authenticated に実行だけで。読めないときは U1n-v2 の形で出せるよう null を返す。ブランチ data/usual-late-rpc、下書き PR、本番には入れない。返す形が決まったら checkin.md に書く

## PM から積んだ次の仕事（11/20 1時55分、フライトの「空の上」を実際の飛行時間に・地図に実際の飛行ルート）※data/flight-actual で作る【済み：PR #136・report-flight-actual.md】
- 本人の声：「空の上の時間はチェックイン時間ではなく、実際に運航した便の飛行時間を積算すること、地図もできれば飛行ルートを反映してほしい」
- 今：flights.dep_at・arr_at はチェックインの時刻で、画面の「空の上」は arr_at − dep_at の合計。地図は flights.track（20261012000021、OpenSky の航跡）があれば描くが、ほとんど空。
- やること：
  1. flights に「実際の出発・到着」（act_dep_at・act_arr_at、どこから取ったか act_src：odpt／時刻表）を足す。移行と RLS をセットで（書くのは照合のサーバーだけ、読むのは本人の分だけ。今の flights の決まりに合わせる）。
  2. 照合（verify-flights）で便名が分かった便に、ODPT の実際の出発・到着の時刻を入れる（未来の時刻は入れない：atd-future と同じ守り）。実績がなければ時刻表の時刻、それもなければ空のまま。今までの便にもさかのぼって入れる（入れられる分だけ）。
  3. 航跡：flights.track を adsb.lol（ODbL、運用で使っている）の航跡から埋められるか確かめる。OpenSky は利用規約の確認表（plans/そらメモ_外部データの利用規約の確認表）で、有料の機能があるアプリで使ってよいか確かめてから。だめなら adsb.lol だけにする。取れない便は今のまま（画面は大圏の線）。
- テスト（tests/sql）：本人以外は読めない・未来の時刻は入らない・さかのぼりの数。本番の Supabase には PM の反映まで適用しない。
- 終わったらチェックイン担当（checkin.md）に、画面で使う列の名前を渡す。

## PM から積んだ次の仕事（11/20 14時10分、見落としの片付け・overlooked-1120.md の A1・A2・A4）※data/redo-1120 で【済み：PR #146・report-redo-1120.md】
1. 定期の手入れ #111（移行183）が main に入っていない（main は 182→184）。番号を今の次（188〜）に付け直して入れられる形にする。中身が今の main とぶつからないか確かめる
2. inbound_aircraft：前の便がないとき、その機体が前の日の夜に着いて泊まった（この日の最初の便）なら first_of_day を返す（11/19 の依頼、checkin.md の「データ担当（11/19・PR #128）」）
3. #81（data/speed-1113b）が今の main で済んでいるか確かめる。済んでいれば「閉じてよい」と報告に（PR は PM が閉じる）
- 移行は RLS とセットで。テストを足す。仕上がったら PM が自動で反映する

## PM から積んだ次の仕事（11/21 1時10分、adsb.lol の鍵と使い方の守り）※data/adsblol-key で【済み：PR #149・report-adsblol-key.md】
- adsb.lol から返事があった（11/6、本人の旅そらのメールに。定型文）。要点：使うなら鍵を取る（匿名の鍵＝試し用で1か月ごと・受信機の鍵・adhoc の鍵＝申し込みを人が読む）。共有の IP（Supabase の関数も当たりうる）は 429 になりやすく、鍵があると自分の枠になる。User-Agent で名乗り、Retry-After を守る。大量のデータを配り直さない・競合の追跡 API を作らない（自分のアプリで位置を見せるのはよい）。お金を得るなら sponsor で費用の分を返すのが期待。
- 今のコード：User-Agent「soramemo (…)」と Retry-After は済み（airport-traffic）。鍵はまだない。
- やること：
  1. adsb.lol に問い合わせる所（airport-traffic・flight_live・foreign_now など全部）で、Supabase の秘密の設定 ADSBLOL_API_KEY があればそれを付ける形に（ヘッダーの名前は adsb.lol の案内 https://www.adsb.lol/mmb・api.adsb.lol/docs で確かめる）。鍵がなければ今のまま動く。鍵はコードに書かない
  2. User-Agent に連絡先（https://soramemo.jp/）を足す
  3. adsb.im（経路の routeset）の利用条件を確かめて、利用規約の確認表に書く
  4. 外にデータをまとめて返す口（ログインなしで live_positions・reg_legs をそのまま大量に返す関数）がないか確かめ、あれば上限を付ける案を報告に
- 仕上がったら PM が自動で反映する（鍵は本人が秘密の設定に入れる）

## PM から積んだ次の仕事（11/21 2時20分、adsb.lol の続き。report-adsblol-key の 2・3 を PM のおすすめで決めた）※data/adsblol-key2 で【済み：PR #153・report-adsblol-key2.md。adsb.im は開けず未確認】
- 外に返す口の上限は案1（おすすめ）で作る
- adsb.im の条件（https://adsb.im/ と vradarserver/standing-data の LICENSE）を WebFetch で開いて確かめ、利用規約の確認表に書く。使えない条件なら経路の推定を止める案を報告に
- first_of_day の線（3日以上・7割以上）はこのまま。overnight は今は画面に出さない
- 本人は adhoc の鍵を申し込み済み（11/21 1時）。届いたら本人が ADSBLOL_API_KEY に入れる

## PM から積んだ次の仕事（11/21 9時15分、改善担当の見回りの指摘）※data/sweep-1121 で （report-sweep-1121.md・kaizen/sweep-1121 の指摘。PM のおすすめどおりに直す。仕上がったら PM が自動で反映）【済み：PR #159・report-sweep-1121-data.md】
- 2 odpt_feed_at（ODPT のデータの時刻）をサーバーから返す。画面の「○時○分時点」と毎回の 404 が消えるように。チェックイン担当に名前を渡す
- 7 運用を開いたときの機体の位置が 3.7秒：airport-traffic の返す量と待ち時間を見直す（ほかの処理を巻き込まない）

## PM から積んだ急ぎの仕事（11/21 14時40分、特別塗装機の知らせが羽田行きを「成田に着陸に向かっています」と送る）※data/livery-dest で。仕上がったら PM が自動で反映【済み：PR #165・report-livery-dest.md】
- 本人の iPhone の通知（11/21 午前）：ロコンジェット ADO14・ピカチュウジェットBC2 SKY004・A350 1号機 JAL500・JAL Jubilee Express JAL140 がどれも「成田に着陸に向かっています（推定）」。どれも羽田行きの便。本人「成田にそんなに行ってるわけないよ」
- PM が見た原因の見当：airport-traffic の recordLiveries で、空港ごとの答え（bodies）を順に回して near.set(reg, {iata, phase}) を上書きしている。羽田に降りる機体が成田の円の中でも高度を下げているので、成田の答えでも phase="arr" になり、後から回る成田で上書きされる → notifyLivery が成田を選ぶ人に「成田に…」と送る
- 直すこと：
  1. 1機が2つ以上の空港で arr になったら、本当の行き先を1つに決める（便名の行き先（ODPT・時刻表）＞滑走路の向きに合っていて近い方＞近い方）。決められないときは知らせない
  2. 各空港の答えの arr/dep の見分けも、その空港の滑走路の向きと距離（最終進入の範囲）で絞る。成田の運用タブに羽田行きが「着陸」と出ていないかも確かめて直す
  3. テスト：羽田に降りる機体が成田の円にも入る場面で、知らせは羽田だけ・成田の一覧に「着陸」と出ない
- 本番の送られ方の確かめ：livery_notified の今日の成田（NRT）の行を数える読むだけの SQL を報告に（本人が流す）
- 追記（11/21 14時48分、本人）：「便の名前から行き先を判別して、判定を強化して」。行き先は便名で決めるのを本筋にする：
  - 機体の呼び出し符号（ADO14・SKY004・JAL500・TGW866 など）を便名に直し（ICAO の3文字→IATA の2文字：ADO→HD、SKY→BC、JAL→JL、ANA→NH、SNJ→6J、SFJ→7G、APJ→MM、TGW→TR、TZP→ZG など。表にして足せる形）、今日の時刻表（timetable・ODPT）からその便の到着の空港を引く。日付の境目（深夜便・遅れて日をまたぐ便）も見る
  - 便名で行き先が分かったら、それを必ず使う（形の判定より優先）。分からないときだけ滑走路の向きと距離で、それでも1つに決まらなければ知らせない
  - 同じ行き先の判定を、特別塗装機の知らせ・空港の近くの知らせ（notifyInbound）・運用タブの着陸の一覧のすべてで使う（1か所の関数にまとめる）
  - テスト：ADO14→羽田、SKY004→羽田、JAL500→羽田、JAL140→羽田、TGW866→成田、TZP52→成田（11/21 の本人の通知と同じ並び）が正しく出る

## PM から積んだ次の仕事（11/21 15時50分、行き先を便名で決めるのを本筋に。data/livery-dest #166 は急ぎで反映した。その続き）※data/livery-dest2 で【済み：PR #167・report-livery-dest2.md】
- 本人の追記（14時48分）が #165 に入りきっていない：今は便名（flight_schedule）を引くのが「候補が2つ以上か最終進入の外」のときだけ。本人の決めは「便名から行き先を判別して、判定を強化」
- やること：
  1. 便名が分かる機体は、いつも便名の行き先を先に使う（形の判定はその次）。flightOfCallsign の対応（ICAO 3文字→IATA 2文字）に抜けがないか、日本の会社と日本に来る海外の会社で確かめて足す
  2. 海外の便など時刻表にない便は、ODPT の国際線の出発到着・foreign_usual・経路のデータで行き先を引く
  3. 同じ判定を notifyInbound（海外の塗装機の早めの知らせ）・撮影の知らせ・運用タブの着陸の一覧でも使う（1つの関数に）
  4. テストに本人の通知の6件を呼び出し符号のまま：ADO14・SKY004・JAL500・JAL140 → 羽田、TGW866・TZP52 → 成田
  5. 決めにくいときの重い問い合わせが増えないように（1回の処理で引く便名は束ねて1回）
- 仕上がったら PM が自動で反映する

## 【11/23 PM から・依頼】AAL176（N791AN、アメリカン航空のワンワールド塗装）【済み：PR #187・report-aal176.md。SQL の結果待ち】
- 本人から「11/22 20:35ごろ羽田発 AAL176（N791AN）は見えてた？」と質問。塗装の一覧（_shared/liveries.ts）にアメリカン航空の機体が1機もなく、通知は出ていないはず。
- やること1（読むだけ）：11/22 19:30〜21:30 の live_positions／運用の記録に AAL176・N791AN が載っていたかを読み取りだけの SQL で確かめ、結果を報告に書く（書き換えなし）。
- やること2：N791AN をワンワールド塗装として ALLIANCE に追加。出典はアメリカン航空の公式発表か航空専門メディア。Flightradar24 は使わない。アメリカン航空のほかのワンワールド塗装機も、出典が取れるものは一緒に。
- テスト：既存の塗装テストが通ること。

## PM から積んだ次の仕事（11/24 4時15分、改善担当の見回り sweep-1124 から）※data/board-bad で。テストが通れば PM が自動で反映【済み：PR #197・report-board-bad.md】
- 【大】運用の「今日の遅れ」の絞り込み（#182）が本番で出ない。本番の airport_board が `bad` を返していないため。チェックイン担当の案 docs/pm/delay-filter-board-bad.sql（関数に今日の遅れ・欠航の便 `bad` を足すだけ。表・列・RLS・権限は変えない）を移行として出す。確かめ方：作り物の時刻表で bad の数が hours の遅れ＋欠航と同じ（report-delay-filter.md のとおり）。テストを足す
- 【小】supabase/functions/_shared/livery_extra.ts の inboundMessage：「（推定）」が2回と「見込み」が重なる。「○○（会社・便名）が羽田に向かっています。着くのは10時20分ごろ（推定）。」のように最後に1回。近くなったときの文と言い方をそろえる

## PM から積んだ次の仕事（11/24 14時30分、アプリ全体の見直し B の回から。ブランチ kaizen/sweep-all-b の docs/pm/report-sweep-all-b.md）※data/sweep-all で。運用の土台なので今の仕事より先に。テストが通れば PM が自動で反映【済み：PR #206・report-sweep-all-data.md】
- 【大】airport_board の next_arr・next_dep を「今より先の便を12便＋過ぎた便を2便まで」に分けて取る（今は「20分前から6便」で羽田の昼は先の便が0〜1便）。表・RLS・名前・引数は変えない（B の1番）
- 【大】airport_board を8本同時に呼ぶと5本が4.1秒で時間切れ（57014）、rwy_learned（p_days 30）は1本でも3〜4秒で 500 が出る。rwy_learned は rwy-learn の毎晩の処理で集めた表を読むだけに、airport_board は8日分の範囲と bad の作り方を軽く（索引・まとめた表）。速さを測って報告に（B の2番）
- 【中】知らせのピン止めをアカウントに保存する（今は端末だけ）。表を足すなら移行と RLS をセットで、自分の行だけ読める・書ける形に。チェックイン担当が画面から読めるよう関数の名前を報告に（B の7番）
- 【小】通知の題から「そらメモ：」を外し、推定は本文の最後に「（推定）」1つにそろえる（B の8番）

## PM から積んだ次の仕事（11/25 5時10分、アプリ全体の見直し 2回目から。ブランチ kaizen/sweep-1125 の docs/pm/report-sweep-1125.md）※data/sweep-1125 で。テストが通れば PM が自動で反映【4番は済み：PR #216・report-sweep-1125-data.md。2番は本人の確認待ち】
- 【中】特別塗装機の知らせを1機・1便で1つの tag にまとめ、予定 → 飛んでいる → 着陸に向かっている を同じ通知の書き換えにする。夜の静かな時間（23〜7時）をゴーアラウンド以外にも選べるように（はじめ ON）。運用が変わった知らせは「前の知らせから60分」で数える。設定を足すなら移行と RLS をセットで（4番）
- 「空の上」を adsb の離陸〜着陸にする件（2番）は本人の決定で「やらない」（出発〜到着のまま・11/25）

## PM から積んだ最優先の仕事（11/25 17時45分、印を押すときロードが長い。本人の声）※data/stamp-fast で。テストが通れば PM がすぐ反映【済み：PR #225・report-stamp-fast.md】
- 印を記録する関数（checkin の保存・その後の集計やトリガー）の重さを調べる。トリガーで重い集計（成績・図鑑・経営など）を同じ処理の中で走らせていないか、索引が足りているか。読むだけの SQL で本番の時間を測れるなら本人用に用意（EXPLAIN は書かずに pg_stat_statements の読むだけ）
- 重い集計は保存と切り離す（あとで回す・軽くする）。記録の中身と RLS は変えない。表を変えるなら移行と RLS をセットで
- チェックイン担当（checkin/stamp-fast）が画面側を直すので、関数の名前と戻り値は変えない

## PM から積んだ次の仕事（11/25 18時45分、羽田・成田を優先して取る＋滑走路の予想の当たり具合。本人「羽田、成田の滑走路の使い方を気象と関連付けて予想できそう？」→「羽田、成田は優先的に取って」）※data/hnd-nrt-priority で。表を足すだけなら PM が自動で反映（足した後に本人へ報告）。画面には出さない（構想段階）【済み：PR #227・report-hnd-nrt-priority.md】
- 1. 成田（RJAA）も羽田と同じ細かさで機体の位置を取る（traffic-record-hnd と同じ形。track_points・rwy_samples・ops_log・arr_watch）。adsb.lol の回数の上限（track_quota・ADSBLOL_API_KEY の有無）に収まるよう、ほかの空港の間隔を延ばして割り振る。1日の回数の見積もりを表で
- 2. 羽田・成田の TAF（aviationweather.gov。今 METAR を取っているのと同じ所）を1時間ごとに取り込んで残す（原文と、時間ごとの風向・風速・突風に分けた形）。METAR も2空港は取りこぼさないように。規約の確認を report に一行
- 3. 当たり具合を測る：ops_log（推定と実機）と wx_obs（METAR）・TAF で、「その時刻の風（実況）から滑走路を当てる」「数時間前の TAF から当てる」の2つを、過去の日で何％当たるか。時刻別（深夜・南風の午後 15〜19時を分ける）・風の強さ別・切り替わりの前後の表。羽田は追い風の上限と「すぐ切り替えない粘り」を合わせ込む。成田は運用時間と A/B 滑走路の使い分け
- 運用を集める印・バッジにはしない（却下済み）。予想は「予想」と出す前提で、表示はまだ作らない
- 記録は消さない。表を足すときは移行と RLS をセット（読むのはサーバーの関数だけ＝方針0でよい）

## PM から積んだ次の仕事（11/25 18時50分、羽田・成田はいろいろなデータを細かく取る。本人「なんなら羽田と成田のデータは細かくいろんなデータを取ってほしい」）※data/hnd-nrt-more で（data/hnd-nrt-priority のあと、またはその上に）。表を足すだけなら PM が自動で反映（足した後に本人へ報告）。画面には出さない【一覧と1回目は済み：PR #230・report-hnd-nrt-more.md】
- まず一覧（docs/pm/report-hnd-nrt-more.md）：候補ごとに「何が取れるか・出どころ・回数と量・規約の一文（原文の URL）・使ってよいか（よい／分からない／だめ）・使い道」。規約が分からない・契約が要るものは「本人に決めてほしいこと」へ。Flightradar24 は使わない
- 候補：
  1. adsb.lol（今の取り込みに足す）：地上の動き（誘導路の道すじ・止まったスポット・止まっていた時間）、進入の線（何マイル手前から乗ったか）、待機（ぐるぐる）、滑走路を使っていた時間（着陸してから出るまで）、続けて降りる間隔、地上を走る時間（出発・到着）、高さ・速さ・上り下りの速さ・squawk
  2. ODPT：羽田・成田のゲート・ターミナル・機材の変更・遅れの理由（出ていれば）。成田の出どころ（NAA）があるか
  3. 天気：METAR・TAF・SPECI を2空港は取りこぼさない、空港の近くのアメダスの風・雷の情報（気象庁。規約を確かめる）
  4. 運用の知らせ：滑走路の閉鎖など（NOTAM。出どころと規約を確かめる。分からなければ本人に）
- 使ってよいものから、今ある取り込みに足すだけで済むものを先に入れる。adsb.lol の回数の上限に収まるか（hnd-nrt-priority の見積もりと合わせて）
- 記録は消さない（生の点は短く置き、まとめて長く残す形）。表を足すときは移行と RLS をセット（方針0）。毎晩の処理には statement_timeout
- たまり具合を見る読むだけの SQL を本人用に
