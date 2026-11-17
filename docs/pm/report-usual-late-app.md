# いつもより○分遅い（推定）の画面（チェックイン担当）

担当：チェックイン（checkin）　ブランチ：checkin/usual-late（main 32d923d から）　日付：2026-11-17（火）
PM の指示：11/17 12時20分（決定事項【11/17】案A・画面案 design/usual-late 2版）。本番には入れていない。

作業の前の3行
- 変えるファイル：src/index.html（と組み立てた web/）・tests/e2e/t139.py（新）・tests/e2e/t60.py
- 手順：乗る便のカードに見込みの箱と灰色の点線の札 → カードをシートの先頭へ → 案内板の「時刻表にない便」→ 機体のくわしくの着陸の箱 → テスト
- 確かめ方：t139（偽のサーバーで U1〜U5 の形）・tests/ops・tests/sql・e2e 全部、390×844／667 で撮る

## 1. 作ったもの
- **乗る便のカード（renderRideIntl）**：時刻表にない便（route_estimate の便、または見つからない JAL・ANA グループ以外の便）だけ、
  - 会社名＋灰色の札「時刻表にない便」
  - 見込みの箱：飛行中＝「羽田に着く見込み 20:07 ごろ　いつもは 19:35 ごろ」＋札「〜 いつもより32分遅い（推定）」（U1）／見込みが出せない＝「見込みはまだ出せません」＋いつもの時刻か「いつもの時刻はまだありません」（U1n）／出発前＝いつもの出る・着く時刻（U2。いつもの時刻がないときは今までの1行）／着陸＝着いた時刻と札／ダイバート＝「いつもと違う空港 成田　いつもは 羽田」（U2c）／引き返し
  - 箱の中に「推定・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）」の1行。ODPT の出典は出さない。長い説明は「出典と注意 ›」の中
  - 門限（伊丹21時・福岡22時。手元の CURFEW）の10分前より遅い見込みは灰色の箱（U2b）。赤は使わない
  - JAL・ANA の国際線（ODPT）は今までどおり
- **乗る便があるときはシートの先頭**：新しい欄 #rideTop（.sbody の先頭）へ #rideCard を移す。表示の編集で「乗る便」を隠しているとき・カードがないときは元の場所へ戻す。国内線の乗る便も同じ
- **案内板（foreignHTML）**：題を「時刻表にない便（いま近くにいる便）」に。題の下に凡例「点線の札はいつもの時刻との比べ（推定）。定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）」。点線の線と点、札「海外」「日本」（灰色）、着く見込み「20:07ごろ」、札（いつもより○分遅い／いつもどおり／いつもより○分早い）か「いつもの時刻はまだありません」。会社名は行から外した。長い説明は「出典と注意 ›」
- **機体のくわしく（spDetailHTML）**：時刻表にない便の到着だけ、上に「着陸の見込み」の箱（時刻・いつもは・札・出典の1行）と「いつもの時刻（推定）」のカード（いつも・数えた回数）。そのときは下の「着陸」のカードを出さない
- 札の決まり：15分以上遅い＝「いつもより○分遅い」・前後14分以内＝「いつもどおり」・15分以上早い＝「いつもより○分早い」。どれも灰色の点線＋波の印＋（推定）。夜（data-night・案内板の色）は点線を琥珀
- 曜日（dow）とばらつき（spread）は出していない（画面案 2版どおり）

### src/index.html で足した・変えた関数
- 足した：ulName・ulJP・ulMin・ulJstMin・ulDiff・ulTagText・ulTag・ulNorm・ulFromLate・ulFetch・ulCurfew・ulRideBox・rideTop・renderRide0（もとの renderRide の中身）・ulPlane・ulSpBox。定数 UL_JP・UL_ODPT・UL_WAVE・UL_I・UL_SRC・UL・UL_RPC
- 変えた：renderRideIntl・renderRide（renderRide0 を呼んでから rideTop）・applyLayout（最後に rideTop）・foreignHTML・spDetailHTML（ulSpBox を差し込むだけ）
- HTML：.sbody の先頭に `<div class="ridetop" id="rideTop" hidden>`。CSS：.ultag・.ulbox・.ulsrc・.ulcf・.ulmore・.ridecard.ul・#v-ops .bdseq.foreign ほか・.spcard.ulsp・.spcard.ulus

## 2. データの読み方（データ担当の data/usual-late-rpc がまだないため）
- まず `rpc/usual_late`（p_flight・p_day・p_reg）を呼ぶ。**404（関数がない）のときだけ**、その回から `foreign_late`（main にある。着いたあとの実績）に切り替える。関数が null を返したら「この便は分からない」として U1n の形
- 読める名前（ulNorm）：usual_arr（または usual）・usual_dep・usual_n・usual_iata・eta・late_min・event（'divert'・'return'）・arr_at・arr_iata。late_min がなければ eta（なければ flight-live の eta_pred）といつもの時刻から手元で出す
- 案内板・機体のくわしくは airport-foreign の planes の各行の `usual`（"HH:MM"）・`usual_n`・`eta`・`late_min` を読む。**`usual` のキーがない今の版では、前の出し方（状態の字と高度・距離）のまま**。着陸に向かう便の時刻は eta がなければ距離からの目安（撮る人の spEta と同じ）
- 今の本番の形のままだと：乗る便は飛行中でも「いつもの時刻はまだありません」（foreign_late は着いたあとの行しか返さない）、案内板は題・凡例・灰色の札だけ変わる

## 3. 確かめた結果
- t139（新・33項目）すべて OK：U1（札・いつもは・出典の1行・ODPT を出さない・点線の灰色）／シートの先頭（844・667 とも出典の1行の下の端 526／469 がタブ帯 758／581 より上）／隠すと戻る／やめると空く／usual_late がない（404）→ foreign_late・U1n／null → foreign_late を呼ばない／門限／ダイバート／出発前／ODPT の国際線は今までどおり／案内板 U3／機体のくわしく U4
- t59・t133 OK。t60 は「海外の航空会社・到着」の確かめを新しい形（時刻表にない便・海外の札・ごろ）に直して OK
- tests/ops（node tests/ops/ops.test.mjs）：すべて成功（手元は全体の playwright をつないで流した）
- tests/sql・e2e 全部：下の「4」に書く
- 写真 docs/pm/shots-usual-late/：t139_ride_844・t139_ride_667（U1）・t139_curfew（U2b）・t139_divert（U2c）・t139_before（U2）・t139_board（U3）

## 4. 全部のテスト
（このあと追記）

## 5. 本人に決めてほしいこと
1. 国内線の乗る便のカードも、シートの先頭に出してよいか（今は国内線・国際線とも先頭。決定事項は「乗る便があるとき」なのでそろえた）
2. ダイバートのとき「この便を国際線の記録に入れる」は、着いた空港を予定の空港（羽田）で記録する（flight-live の到着空港）。着いた空港（成田）で記録するか

## 6. ほかの担当への依頼
- データ担当：data/usual-late-rpc の関数は `usual_late(p_flight text, p_day date default null, p_reg text default null) returns jsonb`（anon・authenticated に実行だけ・security definer）の形だと、そのまま読める。返す形 `{ usual_arr:"HH:MM", usual_dep:"HH:MM", usual_n, usual_iata, eta, late_min, event, arr_at, arr_iata, note }`（分からない値は null、便ごと分からなければ null）。名前・形を変えるなら data.md に書いてもらえれば合わせる（ulNorm の1か所）。あわせて airport-foreign の planes の各行に `usual`・`usual_n`・`eta`・`late_min` を足してほしい（案内板・機体のくわしくの札）。足すまでは案内板の札は出ない
- 撮る人用・運用予想（PM から伝えてほしい）：決定事項【11/17】の U4 のため、spDetailHTML に ulSpBox を差し込んだ（時刻表にない便の到着だけ。その便の「着陸」のカードを出さない）。ほかの所は変えていない
- 改善担当：写真 shots-usual-late/ と iPhone の幅で、シートの先頭のカード（667 で半券が下に押される）と案内板の札が横に切れる所（「いつもどおり（推定）」が列の幅で切れる）を見てほしい
