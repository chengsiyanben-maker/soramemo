# adsb.lol の出典をどこでも押せる形に（11/21 チェックイン担当）

ブランチ checkin/adsb-credit（main 8c39141 から）・下書きのプルリクエスト **#150**

## 作ったもの
- 共通の部品 `ADSB_A`（`<a class="adsbl" href="https://adsb.lol" target="_blank" rel="noopener">adsb.lol</a>`）を ODPT_CREDIT のすぐ下に足した。見える字は「adsb.lol」のままで、色は字の色のまま・下線だけ（CSS `a.adsbl`）
- チェックインの持ち場で字だけだった出典を、全部このリンクにした。形は「adsb.lol（ODbL）」、かっこの中のときは「（adsb.lol・ODbL）」（かっこが二重にならないように）
  - 運用：滑走路の向きの1行（hndOpsHTML）・ゴーアラウンドの箱・設定・一覧（renderGaBox・gaSetHTML・gaEvHTML）・あの日の航跡（renderThatDay）・傾向（trendHTML）・門限（curfewHTML）・海外の便（foreignHTML の凡例と「出典と注意」）・空の道すじ（renderArt）・ピン止めの注意（PIN_FOOT）
  - 空港の3D：「データの出典」の機体の位置（a3SrcHTML）。角の出典はボタンのまま（押すと1回で「データの出典」が開く。ボタンの中にリンクは置けない）
  - 乗る便：時刻表にない便の箱の1行（UL_SRC。撮る人の機体のくわしくでも同じ部品が出る）・「出典と注意」（renderRideIntl）
  - フライト：地図の角の「航跡：adsb.lol（ODbL）」（fbMapHTML）・便を選ぶ画面の注意（loadFlightCands）
  - 図鑑：機体図鑑の注意（renderFleetBook）・特別塗装機の図鑑の注意（renderLivBook）
- もとからリンクだった所：運用の地図の角（drawOpsMap）・専用ページの i（opsHubSrc）・機体の側の注意（#opsPNote）・空港のいま（now.html）
- 字は増やしていない（「ODbL」が無かった所だけ、決められた形にそろえるため「・ODbL」が付いた）
- 変えた関数（src/index.html）：hndOpsHTML・a3SrcHTML・UL_SRC・renderRideIntl・fbMapHTML・loadFlightCands・renderFleetBook・renderLivBook・renderThatDay・trendHTML・curfewHTML・foreignHTML・renderArt・PIN_FOOT・renderGaBox・gaSetHTML・gaEvHTML。足した：ADSB_A と CSS a.adsbl

## 確かめた結果
- 新しいテスト t153：src/index.html を読んで、チェックインの持ち場に字だけの adsb.lol が残っていないこと（下の担当の持ち場・経営・共有の絵の字・コメントは除く）、画面で乗る便の1行・ピン止め・3D の出典・ゴーアラウンドの設定にリンクがあり新しい窓で開くこと、色が字のままで下線、運用の専用ページで i が見えて1回でリンクが出ること → 成功
- 全体のテスト（run_all.py）：122 / 124 件成功（運営コンソールの4本は手元にないので飛ばす）。落ちた2本は今の main でも落ちるもの：t48 は手元に zxing がなかっただけ（入れて1本で流すと成功）、t72 は古いテスト（PR #148 の直したテストで流すと成功）
- tests/ops：すべて成功
- 写真（390 幅）：docs/pm/shots-adsb-credit/（01 ゴーアラウンドの設定の注意・02 運用の i・03 乗る便の1行とピン止めの注意）

## まだの所（ほかの担当の持ち場）
- 運用予想（yosoku.md）：specialHTML・spbListHTML・spbDetailHTML・planeHTML・PRED_NOTE の「adsb.lol」は字だけ。`${ADSB_A}` に替えてもらう依頼を帳面に書いた。とくに機体を選んだ画面（planeHTML）は上の i が隠れるので、ここの1行がリンクでないと1回では出典に行けない
- 撮る人用（satsuei.md）：spDetailHTML の注意・spRegWhy の「adsb.lol」も同じ依頼
- 経営の会社の機体の説明（index.html の 4004 行あたり）にも字だけの adsb.lol がある。経営の持ち場なので触っていない
- 共有の画像（あの日・空の道すじの絵）の「機体の位置：adsb.lol」は絵の字なので押せない。画面の下の1行がリンクなので、そのままにした

## 本人に決めてほしいこと
- なし（PM のおすすめどおり。経営の画面の1行を経営担当に頼むかだけ PM が決める）
