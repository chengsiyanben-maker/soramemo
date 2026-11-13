# 運用予想担当の帳面（チェックイン担当の下、11/6 新設）

## 持ち場
- 機体の運用予想を画面でどう見せるか：運用タブ・撮る人の「この機体の運用（推定）」、機体のくわしく、特別塗装機の今日の足あと・この先の便、予想の当たり具合の見せ方
- 予想の計算そのもの（rot_pairs・rot_eval・rot_predict・毎晩の rot-pairs／rot-eval）はデータ担当が持つ。計算を変えたいときはデータ担当の帳面に依頼を書く
- 触らないもの：運用タブの土台はチェックイン担当、撮る人の見方の中の並べ方は撮る人用担当。予想の部品（関数）をこの担当が作り、二つの担当が呼ぶ形にする
- 表・移行・RLS はデータ担当。経営のコードには触らない

## 守る決定
- 運航予想と運用予想は実績と分けて持ち、画面では「予想」と出し、保証しないと書く
- 登録記号の点の形（● 確認 ◐ 前の便から ○ 予想）は撮る人の画面の決めごとに合わせる

## いま持っている状況（11/6 夜、11/8 に足した）
- データ担当の移行 152 は11/6に main・本番に入った。毎晩 base・learn・learn_hi の3通りを rot_eval に採点している。画面はまだ変わらない
- 11/5 の確かめ（300便・21日）：learn は当たり率で base より上、出したうちの当たり率では下
- 11/6 棚卸し（PR #25 下書き・ブランチ yosoku/inventory・報告 docs/pm/report-yosoku-inventory.md）：
  - 予想の部品は loadPrediction（8720）・predictionHTML（8727）。呼ぶ所は specialHTML（8369）・spDetailHTML（9735）・openPlane／planeHTML／drawPlaneMap（8562〜）。撮る人の一覧の ● ◐ ○ は spot_regs（regLine 9700・spRegWhy 9383）
  - loadPrediction は predict_rotation（JAL・ANA の時刻表の作り・しきい値なし）→ 空なら predict_rotation_reg。採点されているのは predict_rotation_reg と同じ決め方（base）だけ。predict_rotation と spot_regs は採点外
  - predict_rotation_v2（learn）はどこからも呼ばれていない。そのままつなぐと src＝livery の便が「0%（null回）」になる
  - 画面の言い方は「推定」が多く、「保証しない」の文がない
- 11/13 の案：docs/pm/report-yosoku-1113.md（方式ごとの画面の違い・直す関数・デザイン担当への依頼文・当たり具合の1行の案）

## PM から積んだ次の仕事（11/8 16時、本人の依頼「塗装ごとの運用予想も出せるようにして」）
仕様（短く）
- 目的：特別塗装機ごとに、この先どの便に入りそうかを見られるようにする。撮る人が「いつ・どこで・どの便で会えるか」を先に知れる
- 画面：特別塗装機の画面の各機体に「この先の便（予想）」（今日と明日、便名・区間・時刻・● ◐ ○）。一覧のカードに「次は ◯◯ 便（予想）」を1行。空港ごとの「この空港に来る特別塗装機」にも予想の便。どれも「予想です。保証しません」
- 完了の条件：今日飛んでいる機体の予想が出る／出せない機体は「予想できません（最近の記録が足りない）」／当たり具合を1週間あとに数えられる（rot_eval で塗装機だけ）／画面のテストを足す
- 決まり：予想は実績と分けて持つ・保証しない。機体図鑑は特別塗装機だけ。画面はデザイン担当の案を本人に見せてから。作るのは 11/13 の方式の決定のあと
- 進み具合：1（見積もり）と 2（依頼文）は 11/8 に済み（下）。3（作る）は 11/13 のあと

## 11/8 にしたこと（塗装ごとの運用予想 その1・その2）
- ブランチ yosoku/livery-predict-plan・下書き PR #36・報告 docs/pm/report-livery-predict.md（PM の指示どおりの名前。先に出した yosoku/livery-estimate・PR #35 は閉じた）。src/index.html・移行は変えていない
- docs/pm/yosoku-livery-coverage.sql（読むだけ、[1]〜[5]）：前の30日に飛んだ日・今の予想の部品（loadPrediction と同じ順）と学ぶ予想で何機に出るか・前の14日の振り返り（base・learn の出た数と当たった数、機体ごと）。元は .tpl.sql、tools/yosoku_livery_sql.mjs が liveries.ts の特別塗装機を書き込む（一覧が変わったら流し直す）。tests/sql/t97 13項目通過
- 見込み：特別塗装機は95件、期間内93件（PM の「92件」と1件違い）。国内41・海外52。海外は reg_legs に日本に来た1便しか残らないので予想はほぼ出ない。ZIPAIR も同じ。JTA は南の円の記録が 11/7 からなので少ない。上限は国内およそ39機
- 気づいたこと：rot_predict の塗装機の予定の便は livery_sightings に名前が入っている機体だけ効く（データ担当に伝えた）

## ほかの担当への依頼
- データ担当へ（11/6、data.md に書いた）：predict_rotation の採点を足すか・predict_rotation_v2 に方式の引数・当たり具合を返す読む関数。どれも 11/13 の本人の決定しだい
- データ担当へ（11/8、data.md に書いた）：塗装機の便を毎晩の採点に必ず入れ、塗装機だけの当たり率を数えられるように。11/13 の決定のあと

## 11/13 にしたこと（全体の見回りの直し）→ 下書き PR #83（yosoku/fix-sweep-1113）・報告 docs/pm/report-yosoku-fix-sweep-1113.md
- 6項目とも作った：選んだ見方の分だけ読む（OPS_NEED・opsNeed。開いたときの通信 17→6〜9本）／livery_board は運用では飛んでいる特別塗装機の分を1回（loadSpbLive。全部の4回は「すべての特別塗装機」を開いたときだけ）／見方を変えても3分は読み直さない（OPS_LAZY・opsFresh）／ログインなし・デモは flight_alerts を読まずタイルとお知らせを出さない（fwOn）／風は届くまで「読み込み中」・札なし（OPS_WX_WAIT）／帯は左端から（opsViewsReveal）／案内板の2行と 44px／滑走路は先に中身を出し地図はあと
- 「中身のない丸いボタン」「名前のない小さいボタン」は閉じた details の中身（ほかの向き・この地図について）。開けば押せる。コードは変えず、見回りの道具の直しを改善担当へ（報告に書いた）
- テスト t130（43項目）・運用の e2e 15本・tests/ops 通過。全 e2e は報告に追記
- 本人に決めてほしいこと：ログインなしの人に遅れ・欠航を出さなくてよいか（1行の案内を出すか）／「気象通報なし（仮の表示）」の言い方／livery_board を「飛んでいる分だけ1回」にしたこと
- チェックイン担当へ：setViewsw の送り方を共通にするか（checkin.md の依頼に書いた）

## 11/13 夜にしたこと（画面の予想を v2 に切り替え）→ 下書き PR #86（yosoku/rot-v2）・報告 docs/pm/report-rot-v2.md
- loadPrediction を「predict_rotation → predict_rotation_v2 → predict_rotation_reg」に。v2 が null・失敗・空なら reg に戻す（predHasNext）
- src＝livery の便は「特別塗装機の予定の便から」／機体の1日は「予想・塗装機の予定」（predWhy・predTag）。learn は「前の42日」。書き方「推定です…」は今のまま
- 変えた関数：loadPrediction・predictionHTML・planeHTML（足した：predHasNext・predWhy・predTag）
- テスト t131（14項目）・t68・tests/ops 通過。全 e2e は t99・t105（経営・main でも落ちる）・t48（pdf417gen なし）以外通過
- 本人に決めてほしいこと：JAL・ANA でも v2 を先にするか（今は predict_rotation が先で learn_hi が出ない機体がある）／「保証しません」を画面の文に足すか／反映は data/rot-learn-hi のあと

## 次にやること
1. PR #86 は main に入った（11/13 20時14分）。本人の3つの決定（JAL・ANA の順番・「保証しません」・本番の反映は data/rot-learn-hi が先）を待つ
2. PR #83（見回りの直し）は 11/13 に main に入った。本人の3つの決定（ログインなしの遅れ・欠航／「気象通報なし（仮の表示）」／livery_board を飛んでいる分だけ）は、答えが来たら直す
3. PR #25・#36 のレビューに答える
4. 本人が docs/pm/yosoku-livery-coverage.sql を流した結果が来たら、report-livery-predict.md の見込みを本番の数に直す
5. 塗装ごとの運用予想（yosoku/livery-predict）：方式は learn_hi に決まったので、デザイン担当の画面案を待って作る。約4週間後（42日そろったら）の比べ直しの結果も見る

## PM から積んだ次の仕事（11/13 17時30分、画面の予想を v2 に切り替え）【済み・PR #86】
本人「切り替えて」（決定事項：運用予想の画面は learn_hi）。画面が今呼んでいる predict_rotation_reg を predict_rotation_v2 に替える（運用タブ・撮る人の「この機体の運用（推定）」・機体のくわしく・特別塗装機の この先の便など、予想を出す部品のすべて）。返す形は同じで、'estimate': true と便ごとの src が増える。見た目と「予想・保証しない」の書き方は変えないので画面案は要らない。v2 が null や空のときは今の predict_rotation_reg に戻す。データ担当が v2 を learn_hi にする移行を data/rot-learn-hi で作る。ブランチ yosoku/rot-v2、下書き PR。変えた関数の名前を報告に
