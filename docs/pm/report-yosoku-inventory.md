# 運用予想の棚卸し（11/6・運用予想担当）

- 変えるファイル：この報告と docs/pm/report-yosoku-1113.md だけ（コードは変えない）
- 手順：main（14916e9）の src/index.html・移行・テストを読み、予想が出る所・呼ぶ関数・採点との関係を書き出す
- 確かめ方：関数の名前と行は main の 14916e9 で grep して照らした

## 1. 予想が画面に出ている所（5か所）

| # | 画面 | 関数（src/index.html） | 呼ぶサーバーの関数 | 画面の言い方 |
|---|---|---|---|---|
| 1 | 運用タブ「特別塗装機」の一覧の「この先の便（推定）」 | specialHTML（8369）→ クリックで predictionHTML（8727） | loadPrediction（8720）：predict_rotation → だめなら predict_rotation_reg | 「推定です。…機体の入れ替えで違うことがあります」 |
| 2 | 撮る人の便のくわしく「この機体の運用（推定）」→「この先の便を見る」 | spDetailHTML（9735）→ predictionHTML | 同じ loadPrediction | 同じ |
| 3 | 機体の1日（登録記号で探す） | openPlane（8562）・planeHTML（8569）・drawPlaneMap（8587） | reg_history ＋ loadPrediction | 「この先の便（予想）」。地図は橙の点線 |
| 4 | 撮る人の一覧の登録記号（● 確認 ◐ 前の便から ○ 予想） | spItems（9507）・regLine（9700）・spRegHTML（9377）・spRegWhy（9383） | spot_regs（移行 098） | ○は「2つ先の便までたどった予想（○%）」 |
| 5 | 乗る便の機体はいまどこ（推定） | 3515〜3600 あたり（ride の画面） | inbound_aircraft | 「到着予想（推定）」など。※運用予想とは別の作り（前の便の機体を探す） |

- 特別塗装機の画面（spbDetailHTML・8464）の「今日の足あと」には、この先の便は出ていない（一覧の #1 と機体の1日 #3 にだけ出る）
- 予想の当たり具合を見せる所は、どの画面にもない

## 2. いま使われている予想の作りは3通り、そのうち採点されているのは1通りだけ

| 作り | 中身 | しきい値 | 使っている画面 | rot_eval で採点 |
|---|---|---|---|---|
| predict_rotation（移行 047） | JAL・ANA の時刻表＋rotation_obs（前の60日・同じ曜日2倍）。今日 flight_watch で見つけた機体だけ | **なし**（いちばん多い便をそのまま出す） | #1〜#3 の**最初に**呼ぶ | されていない |
| predict_rotation_reg（移行 076） | reg_legs の全機の記録（前の60日・同じ曜日2倍） | 3回以上・4割以上 | #1〜#3 で、上が空のときだけ | base として採点（同じ決め方を rot_pairs で） |
| spot_regs（移行 098） | rotation_obs で前の便から1つ／2つたどる | 3回以上・4割以上（2つは掛け算で4割） | #4 | されていない |
| predict_rotation_v2（移行 152） | rot_predict('learn')。特別塗装の予定 → 学ぶ → base に戻る | 2回3割（学ぶ）／3回4割（戻り先） | **どこからも呼ばれていない** | learn として採点 |

気づいたこと
- 11/13 に比べる base・learn・learn_hi は、全機の記録（reg_legs）の作り同士の比べ。JAL・ANA の機体で画面に最初に出る predict_rotation と、撮る人の一覧の ○（spot_regs）は採点に入っていない。11/13 に「learn にする」と決めても、predict_rotation_reg の所を差し替えるだけでは、JAL・ANA の多くの機体の画面は変わらない
- predict_rotation はしきい値がないので、記録が1回だけの便でも出る。「出したうちの当たり率」は base より低い見込みだが、数字はない

## 3. predict_rotation_v2 をそのまま画面につなぐと困る所

- 特別塗装の予定から出した便（src＝livery）は seen と share が空。predictionHTML は「前の60日で0%（null回）」と出してしまう
- 学ぶ予想は前の42日・新しい日ほど重いので、「前の60日で○%」の言い方が合わない（planeHTML の注の「前の60日の記録からの推定」も）
- 便ごとの src（livery・learn・base）が返るが、今の画面は使っていない

## 4. 「予想」「保証しない」の決まりとのずれ

- #1〜#3 は「推定」と出していて「予想」の語が見出しにない所がある（#1 のボタン・#2 の見出し）。「保証しない」とは書いていない（「違うことがあります」まで）
- #4 は「予想」の語を使っている（決まりどおり）
- 直すのは画面の言い方なので、デザイン担当の案を待つ（11/13 の決定と一緒に直すのがよい）

## 5. テスト

- 画面：tests/e2e/t63.py（spot_regs の作り物・predictionHTML の reg の形）、tests/e2e/t68.py（機体の1日。predict_rotation は空、predict_rotation_reg を返す）
- SQL：t23（predict_rotation）、t40（predict_rotation_reg）、t49（spot_regs）、t90・t92（rot_predict・rot_eval・predict_rotation_v2）、t32（撮る人の知らせ）
- predict_rotation_v2 の返事（src＝livery で seen が空）を画面に通すテストはない

## 本人に決めてほしいこと

1. 11/13 の比べに、JAL・ANA の時刻表の作り（predict_rotation）も入れるか。入れるならデータ担当に「rot_eval に4つ目の方式として採点を足す」を頼む（下書きを data.md に書いた）
2. 撮る人の一覧の ○（spot_regs）も、11/13 に決める方式にそろえるか、今のままにするか
