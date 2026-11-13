# 報告：画面の運用予想を学ぶ予想（predict_rotation_v2・learn_hi）に切り替え（運用予想担当・11/13）

ブランチ yosoku/rot-v2（main から）。下書きのプルリクエスト。main・本番には入れていない。

## 作ったもの
- 予想を読む部品 `loadPrediction` の順番を「時刻表の predict_rotation → **predict_rotation_v2** → predict_rotation_reg」に。v2 が null・失敗・「いまの便が分からない」・「この先の便が空」のときだけ、今までの predict_rotation_reg に戻す。どれも次の便がないときは、いまの便が分かる方で「予想できません」
- v2 の便ごとの `src` に合わせた小さい字
  - 特別塗装機の予定の便（src＝livery）は割合がないので「特別塗装機の予定の便から」（そのままだと「0%（null回）」と出ていた）
  - 学ぶ予想（src＝learn）は「前の42日で○%（○回）」、今までの決め方（src＝base）は今のまま「前の60日で…」
  - 機体の1日の札は「予想・66%」「予想・塗装機の予定」。注記に「特別塗装機は航空会社の運航情報にある予定の便も」
- 見た目と「推定です。…機体の入れ替えで違うことがあります」の書き方は変えていない（画面案なし）
- 予想を出す所はすべて `loadPrediction` を通るので、運用タブの特別塗装機・撮る人の「この機体の運用（推定）」・機体のくわしく（機体の1日）がまとめて切り替わる

### src/index.html で変えた関数
- 変えた：`loadPrediction`・`predictionHTML`・`planeHTML`
- 足した：`predHasNext`・`predWhy`・`predTag`
- web/index.html・web/sw.js は tools/build.mjs で作り直したもの

## 確かめた結果
- 新しいテスト tests/e2e/t131.py（14項目）通過：v2 を使う・v2 が空／null／404 なら reg・両方空・いまの便なし・塗装機の便に「0%」「null」が出ない・機体の1日の画面
- 今ある t68（機体の1日・予想）通過。tests/ops 通過
- 全部の画面テスト：t99・t105（経営の枠・台風。main でも同じく落ちる日付の問題）と t48（手元に pdf417gen がない）以外は通過。t13 は並べて流したときだけ時間切れ、単独で通過
- スマホ幅（390）の画面：docs/pm/shots-rot-v2/plane-390.png

## 本人に決めてほしいこと
1. **JAL・ANA の機体は、今も時刻表の predict_rotation が先に出ます**（採点されていない・しきい値なしの方式）。PM の指示どおり predict_rotation_reg の所だけ v2 に替えたので、JAL・ANA で predict_rotation が答えを返す機体には learn_hi が出ません。JAL・ANA も v2 を先にするか（predict_rotation を戻り先にする）を決めてほしい
2. 決定事項の「保証しないと書く」が、まだ画面の文にない（今は「推定です。…違うことがあります」）。今回は「書き方は変えない」の指示なので触っていない。「保証しません」を足すなら、デザイン担当の案と一緒に
3. 反映の順番：データ担当の data/rot-learn-hi（v2 を learn_hi にする移行）が先、この PR があと。この PR だけ先に入ると、v2 は今の learn で出る（しきい値が低い方）
