# チェックイン担当の帳面

## いま持っている仕事
- 11/21 手動の回（PM が同じ「改善担当の見回りの指摘」を指示）：直前の回で PR #161（checkin/sweep-1121・3a9a3ad）として済み。main は 08e4b84 のままで取り込み済み、作り直しは不要だった。PM の自動の反映を待つ
- 11/21 昼の定時の回（PM 11/21 9時15分「改善担当の見回りの指摘」）：ブランチ checkin/sweep-1121（main 08e4b84 から）・下書き **PR #161**（925a8fe）・報告 docs/pm/report-checkin-sweep-1121.md・写真 docs/pm/shots-sweep-1121/。PR #161 の動きはこの回の会話で見張りを付けた
  - 1 運用「遅れ」の専用ページの頭に「今日の遅れ・欠航」の1枚（#opsLate。カードと同じ数＝案内板の hours の今日の遅れ＋欠航・時間ごとの札・0便は「いま遅れ・欠航の便はありません」・未ログインは「ログインすると見られます」の1行）
  - 3 ホームの「マイページ」を1行（nowrap・絵 18px・切り替えのピルの余白 10px）／4 地図カードは位置が届くまで「—」（TRAFFIC_GOT）・地図の凡例の数は「この範囲に ○機」だけ／7 地図カードの前の数を10分まで「約○分前」（localStorage soramemo.ops.mapn・数と時刻だけ）
  - 8 3D の全体の視点を約12km（R 10000・高さ 7000・見る点は1km 北）＋景色の外の空の機体は端に矢印の札（.a3tag.edge・3機まで・全体の視点だけ）。t142 の名札の確かめを合わせた
  - 9 #opsMap の ＋− 44・.artnav ◀ ▶ と .artdate 高さ44・出典の「くわしく」を上下に広げた（マイページ・終了・見方のピル・案内板のピルは前から ::after で 44 あった）
  - 5（土台の側）特別塗装機のカードから開いたら details.spnow を開く（renderOpsPside）。撮る人の PR #162 も spnow のまま1〜3機なら開く形で重ねても動く
  - PR #162（撮る人）・yosoku/sweep-1121 と重ねると src は自動でまとまり、ぶつかるのは web/index.html・web/sw.js だけ（あとから入る方で組み立て直す）
  - 変えた関数：opsLateHTML・renderOpsLate・ohMapKeep・ohMapPrev（新）、renderOpsAlerts・renderBoard・opsHubApply・ohCardHTML・loadTraffic・setOpsAirport・trafficNoteDraw・renderOpsPside・a3Camera・a3Labels
  - テスト：t159（新・26項目。撮る人・運用予想も t156 を足したので番号を分けた）・t142・tests/ops 成功・e2e 全体 127／127（3a9a3ad）
- 11/21 昼：PR #157（空の道すじの上限）は #153 と一緒に PR #158（pm/release-1121c）で main に入った（08e4b84）。本番の反映（Actions）の成否はまだ見ていない
- 11/21 6時17分（日本時間）：PR #157（空の道すじの上限）が main に入った。#153（移行190）と一緒に入ったか・本番の反映（Actions）が成功したかは次の回で確かめる。直しは main から新しいブランチで
- 11/21 手動の回（PM が同じ「空の道すじの上限に合わせる」を指示）：前の回で PR #157 として済み。この回は main（#156 まで）と data/adsblol-key2（5dce3ac・t122 の直し）を取り込み直して push（d8a9a18）。src/・web/ の変化はなし（関数は変えていない）。t155・t55 成功
- 11/21 4時台（日本時間）の定時の回（PM 11/21 4時「空の道すじの上限に合わせる」）：ブランチ checkin/track-quota（main 17d48db ＋ data/adsblol-key2 を取り込み）・下書き **PR #157**（af801d6）・報告 docs/pm/report-track-quota.md・写真 docs/pm/shots-track-quota/
  - airport_tracks・cold-tracks をログイン中はログインの鍵（access_token）で読む。login_required／rate_limited（cold は 401／429）で日付の下に小さな一文。未ログイン・デモは前の7日まで（端で「ログインすると見られます」の1行）。あの日の空も同じ一文。空の道の下の注に「（8日より前はログインした人だけ）」
  - 変えた関数：loadArt・renderArt・renderThatDay（足した：ART_FREE_DAYS・artLoggedIn・artMinDay・artToken・artErrOf・artErrText）。rpcPost は変えていない
  - tests/e2e/fake_sb.js のログインに access_token:'tok-u1' を足した
  - テスト：t155（新・16項目）成功・全体 126／126（t48 は pdf417gen・segno を pip で入れて流し直し）・tests/ops 成功
  - PR #157 の動き（コメント・CI）はこの回の会話で見張りを付けた
- 11/21 2時46分（日本時間）：PR #148・#150 は PR #154（反映 11/21）で main に入り、反映の Actions 225 は成功（11/21 3時23分）→ 本番に出た。出典のテストは main で t154 に付け直された
- 11/21 手動の回（PM が同じ「adsb.lol の出典をどこでも押せる形に」を指示）：直前の回で PR #150 として済み。main は 8c39141 のままで作り直しは不要だった。前の仕事 checkin/test-fix-1120 も PR #148 として済み（main に入るのを待つだけ）
- 11/21 1時台（日本時間）の定時の回（PM 11/21 1時10分「adsb.lol の出典をどこでも押せる形に」）：ブランチ checkin/adsb-credit（main 8c39141 から）・下書き **PR #150**（0eaee2f・3278382）・報告 docs/pm/report-adsb-credit.md・写真 docs/pm/shots-adsb-credit/
  - 共通の部品 ADSB_A（新しい窓・noopener）と CSS a.adsbl（字の色のまま下線）を足し、チェックインの持ち場の字だけの出典を全部リンクに。形は「adsb.lol（ODbL）」、かっこの中は「（adsb.lol・ODbL）」
  - 変えた関数：hndOpsHTML・a3SrcHTML・UL_SRC・renderRideIntl・fbMapHTML・loadFlightCands・renderFleetBook・renderLivBook・renderThatDay・trendHTML・curfewHTML・foreignHTML・renderArt・PIN_FOOT・renderGaBox・gaSetHTML・gaEvHTML（足した：ADSB_A）
  - 空港の3D の角の出典はボタンのまま（押すと「データの出典」が開き、そこがリンク）。共有の絵の字は押せないのでそのまま
  - テスト：t153（新）成功・全体 122 / 124（t48 は zxing がなかっただけ、t72 は #148 の直したテストで成功）・tests/ops 成功
  - 下の担当（運用予想・撮る人用）の字だけの adsb.lol は変えていない → 依頼を「ほかの担当への依頼」に。経営の会社の機体の説明（4004 行あたり）も字だけ（経営の持ち場）
- 11/20 手動の回（PM が同じ「毎回落ちるテストの直し」を指示）：前の回で PR #148 として済み。main は 8c39141 のままで、#148 は取り込み済みなので作り直しは不要だった。修行のコードには触っていない
- 11/20 午後の定時の回（PM 14時10分「毎回落ちるテストの直し」）：ブランチ checkin/test-fix-1120（main 8c39141 から）・下書き **PR #148**（caf39d0）・報告 docs/pm/report-test-fix-1120.md。テストだけの直しで src/・web/ は変えていない（変えた関数なし）
  - t48：web/config.js でサーバー版になり、ログインなしでは便に付かなかった → デモに入ってから試す・zxing は /tmp/build → 作業用フォルダの順に探し、なければ npm で入れる・成否の確かめを足した
  - t72：運用タブが一覧＋専用ページになり、特別塗装機の欄は「撮る人」のページの中 → opsHubOpen('photo') してから押す。1本だけ流すときは run_all.py から（サーバー版のコピーを作るため）
  - t123：「共有する」のあと固定 600ms → 共有の窓が開くまで evaluate を繰り返して待つ（wait_for_function は CSP の unsafe-eval に引っかかる）
  - t147：指の時刻（CDP の timestamp → e.timeStamp）をテストで決めて渡す。重い状態で直す前は落ち、直したあとは成功
  - run_all.py で 123 / 123 件成功（運営コンソールの4本は手元にないので飛ばす）
  - 本番の反映（Actions）は #142・#144・#145 とも成功を確かめた（#141・#143 は本番に入っている）
  - テストを流すには pip の pdf417gen・segno・brotli と、zxing（@zxing/library@0.21.3）が要る
  - 修行担当への「年の区切りを日本時間に」は、PM がすでに shugyo.md に積んでいた（書き足していない）
- 11/20 11時26分（日本時間）：PR #143（日誌の1行と共有の画像も実際の時刻に）が main に入った。本番の反映（Actions）が成功したかは次の回で確かめる。直しは main から新しいブランチで
- 11/20 8時42分（日本時間）：PR #141（図鑑の「まだ」を5行に畳む・フライトのくわしくを実際の時刻に）が main に入った。本番の反映（Actions）が成功したかは次の回で確かめる。直しは main から新しいブランチで
- 11/20 手動の回（PM が同じ「日誌の1行と共有の画像も実際の時刻に」を指示）：前の回で PR #143 として済み。main は 642840b のまま、#141 もまだ main に入っていない。#143 は #141 と main を取り込み済みなので作り直しは不要だった
- 11/20 8時台（日本時間）の定時の回（PM 8時5分「日誌の1行と共有の画像も実際の時刻に」）：ブランチ checkin/actual-share（#141 の checkin/small-1120 の上に重ねた）・下書き **PR #143**（3051709）・報告 docs/pm/report-actual-share.md・写真 docs/pm/shots-actual-share/
  - 実際の時刻がある便は、日誌の1行の「○:○○ 発」と共有の画像の「出発」を実際の時刻に。ない便は今までどおり。共有の画像にチェックインの時刻は出さない
  - 変えた関数：新 fbDepAt・fbRowHTML・fbPassCard・fbOpenView
  - テスト：t152（新）・t151・t150・t149・t127・t123・t116・t118・t60・t47・t61 成功
  - 日付は今までどおりチェックインの日（0時をまたぐ便だけずれて見えるおそれ。まれなので今はそのまま）
  - #141 はまだ main に入っていない。#141 が入ったら #143 に main を取り込み、web/ を作り直して t152 を流し直す
  - 組み立て（tools/build.mjs）にはフォントのために python の brotli が要る（入っていないと止まる）
- 11/20 6時（日本時間）：#138・#139 が main に入って（PR #142・642840b）#141 がぶつかった → main を取り込んだ（db2be80。src は自動で重なり、web/ だけ作り直し）。t151・t149・t150 成功。#141 は図鑑とフライトの小さい直しだけになった（上の「本人の答え」の3つは PM のおすすめで決まり、#141 に入っている）
- 11/20 6時4分（日本時間）：PR #138（図鑑の絞り込みと県名）と #139（フライトの実際の時刻と航跡）が main に入った。本番の反映（Actions）が成功したかは次の回で確かめる。直しは main から新しいブランチで。本人の答え（図鑑の地図の「まだ」の一覧・くわしくの出発と到着を実際の時刻にするか・航跡が何本もあるとき）を待つ
- 11/20 手動の回（PM が同じ「小さい直し」を指示）：前の回で PR #141 として済み。main は f684e9e のまま（#138・#139 はまだ入っていない）、#141 は main・#138・#139 を全部取り込み済みなので、作り直しは不要だった
- 11/20 定時の回（PM 5時30分「図鑑とフライトの小さい直し」）：ブランチ checkin/small-1120（main f684e9e に #138・#139 を重ねてから）・下書き **PR #141**（c711bfe）・報告 docs/pm/report-small-1120.md・写真 docs/pm/shots-small-1120/
  - 図鑑：地図の見方の「まだ」の一覧は5行＋「残り○か所 ›」（48px のピル）。押すと全部・6行目に移る。種類・見方を変えたら畳み直す（端末に覚えない）。沖縄・南の島は今のまま
  - フライト：実際の時刻がある便は、くわしくの出発・到着を実際の時刻に。下に12pxで「チェックイン ○:○○〜○:○○」1行（取り先は空の上の箱にあるので重ねない）。航跡は最新1本・出典そのまま
  - 変えた関数：zkAirBookHTML・図鑑のピルと見方の click・fbOpenView、新 ZKX_YET_N・ZKX_YET_OPEN・「残り」の click。CSS #v-book .zx-list .more・dialog.fbx .fvhead .fvsrc
  - テスト：t151（新）・t149（5行に直した）・t150・t127・t116・t118・t60・t47・t61・t123 成功（t123 はこの回は通った）
  - 本人に決めてほしいこと：日誌の1行の出発時刻と共有の画像も実際の時刻にそろえるか
- 11/20 3時19分（日本時間）に PR #140（運用の一覧 #134・data/flight-actual 移行187）が main に入り、#138・#139 がぶつかった → 両方に main を取り込んだ（#138 07eb3db・#139 281a9fe。src は自動で重なり、web/ だけ作り直し）。t149・t127・t148・t150・t47・t61 成功、t123 は前からの失敗
- 11/20 3時台の手動の回（PM が同じ2つを指示）：どちらも前の回で済み（PR #138・#139）。main は 863fb3d のままで、data/flight-actual はまだ main に入っていないので取り込み直しは不要だった。#136 が main に入ったら #139 に main を取り込み、t150 を流し直す
- 11/20 3時台（日本時間）の定時の回（PM 2時45分の2つ）：どちらも作って下書きにした
  - 図鑑の絞り込みと県名（design/zukan-filter 1版 F1〜F3）：ブランチ checkin/zukan-filter（main 863fb3d から）・下書き **PR #138**（07d7cc0）・報告 docs/pm/report-zukan-filter-app.md・写真 docs/pm/shots-zukan-filter/
    - 見方の帯「地方別・地図」・ピル「すべて 75・飛行場 30・滑空場 33・ヘリポート 12」（localStorage soramemo.zkx.kind・soramemo.zkx.view、DEMO_LO_KEYS にも足した）・全部の枠に県名13px・1つに絞ると種類の札を外す・地図の見方（点と「まだ」の一覧）
    - 変えた関数：zkxTile・zkAirBookHTML・DEMO_LO_KEYS、新 zkxGet・zkxKind・zkxView・zkxSet・zkxBigMapSVG・ピルと見方の click
    - t149（新）・t127（見方の帯の押す所を44pxに）・t116・t118・t122・t124・t126・t60・t7系 成功（t72 は前から）
    - 本人に決めてほしいこと：地図の「まだ」の一覧を全部出すか畳むか・地図に沖縄と南の島が入らない
  - フライトの「空の上」と航跡（data/flight-actual・PR #136 の列）：ブランチ checkin/flight-actual（main 863fb3d から）・下書き **PR #139**（7d61b8a→b37dc33）・報告 docs/pm/report-flight-actual-app.md・写真 docs/pm/shots-flight-actual/
    - select に act_dep_at・act_arr_at・act_src（エラーなら前の列で読み直す）・空の上は fbMin（実際の時刻があればその差）・1行に「目安」・年の帯と年のまとめに「（推定を含む）」・くわしくに取り先の説明・地図は区間のいちばん新しい航跡（fbTrackOf）・出典「航跡：adsb.lol（ODbL）」
    - 変えた関数：読み込み（fetchAll("flights")・S.flights）・fbEntries・fbSum・fbYrHTML・fbRowHTML・fbYearHTML・便のくわしく・fbMapHTML・fbMapSVG・renderFlightMap・共有の画像、新 fbActOf・fbMin・FB_SRC_TXT・fbTrackOf。tests/e2e/fake_sb.js に window.__flightsAct
    - t150（新）成功・関係する e2e 51本中50本成功（t72 は前から）
    - 本人に決めてほしいこと：くわしくの出発・到着も実際の時刻にするか・1区間に航跡が何本もあるときの描き方・出典の言い方
- 11/20 2時半（日本時間）：PR #137 で checkin/ios-app と checkin/tear-finger（PR #133）が main に入った（863fb3d）。PR #134（運用の一覧）に main を取り込んだ（e3dd9f8・src は自動で重なり、web/ だけ作り直し）。t148・t146・t147・t143・t74・t138・t130・tests/ops 成功
- PR #130（ピン止め）：11/20 2時29分（日本時間）に main に入った。本番の反映（Actions）が成功したかは次の回で確かめる。iPhone で Safari →ホーム画面にピン止めが移るか（報告 report-pin-app.md の手順）は本人の結果待ち。直しは main から新しいブランチで
- 11/20 1時台の定時の回（PM 1時10分「運用の地図の数をそろえる」）：PR #134（checkin/ops-hub）に足した（21180c2）。報告 docs/pm/report-ops-hub-app.md の「追記2」・写真 docs/pm/shots-ops-hub/t148_map_legend_844・t148_map_wide_844・t148_list_844
  - 地図カードの数は着陸・離陸の機体だけ（上空通過は数えない）。凡例に「この範囲に ○機」（地図を動かすと数え直す）と、空港のまわりで外に機体がいるとき「ほかの○機は『経路の全体』で見られます ›」（押すと経路の全体）
  - 経路の全体の合わせ（opsFit・renderOps の中・loadTraffic の最初の合わせ）に機体の今の位置を入れた。凡例の時点の字を13pxに
  - 変えた関数：ohCardHTML・loadTraffic・trafficNoteDraw（新）・trafficInView（新）・TRAFFIC_LAST（新）・opsFit・renderOps の経路の全体の合わせ・CSS .opsstat
  - t148（43）・tests/ops・前の形の e2e 17本 成功。本番の羽田は夜中で1機だけだったので、本番のデータでの撮り直しは昼の回に
- 11/19 23時前後の回（PM 22時45分の急ぎ「運用の地図に機体が映っていない」）：PR #134（checkin/ops-hub）に足した（92a0a34）。報告 docs/pm/report-ops-hub-app.md の「追記」・写真 docs/pm/shots-ops-hub/real_hnd_*・t148_list_844・t148_map_844
  - 地図カードの絵に今の機体の印（ohMapPlanes・OH_MAP_KM＝外の輪74を約15km）。着陸・離陸の機体だけ・近い順に最大12機・絵の外は描かない。ohCardHTML の地図の svg に入れた
  - 専用ページで出なかったのは t148 の作り物の機体が「空港のまわり」の範囲の外にいただけ（アプリの直しなし）。作り物を羽田の南の進入5機＋遠くの出発機1機に置き直し、カードの印5機・地図の中に5機の確かめを足した
  - 本番の羽田（11/19 22時45分の adsb.lol 23機、airport-traffic を読むだけ）を偽のサーバーから出して撮った：カードに7機・空港のまわりに2機・経路の全体で広く
  - t148・tests/ops・前の形の e2e 17本 成功
  - 本人に決めてほしいこと（追加）：カードの数（上空通過も数える 23機）を地図と同じ着陸・離陸（14機）にそろえるか／「空港のまわり」で凡例の数より見える機体が少ないこと（「この範囲に ○機」を足すか、「経路の全体」へ誘う1行を出すか）
- 11/19 夜の回（PM の指示：1 アプリだけの画面 2 運用の一覧 3 半券の指）：1 と 3 は前の回で済み（PR #125・#133）。2 を作った
  - 運用タブを一覧＋専用ページに（PM 11/19 15時・design/ops-hub 1版 案A）：ブランチ checkin/ops-hub（main 3a71781 から）・下書き **PR #134**（8f80885→92a0a34・見張り中）・報告 docs/pm/report-ops-hub-app.md・写真 docs/pm/shots-ops-hub/
    - #opsHubList（カード10枚 OH_CARDS）・#v-ops[data-hub="list"|"page"]・[data-page]。専用ページは今の見方の中身をそのまま（滑走路は地図を隠す・地図は運用の箱を隠す・遅れは #opsAlerts・特別塗装機は機体の側の special・検索窓からは page="plane"）
    - 動きは clip-path（開く 460ms・戻る 380ms・reduce で動きなし）。左端 24px から引いて戻る（touch と mouse）。i は #dOpsSrc。opsNeed は一覧で board・special・traffic だけ
    - 試験用の切り替え localStorage soramemo.ops.hub="0" で前の形。前の形を前提にした e2e 17本（t113・t124・t128・t130・t133・t138・t139・t53・t55・t59・t60・t61・t63・t65・t66・t68・t71）に付けた
    - t148（新）・tests/ops・上の17本 成功。e2e 全体 112／115（t48・t72・t123 は main でも落ちる）
    - 本人に決めてほしいこと：並べ替え（今は隠す・出すだけ）・遅れと定時のカードの数の意味・専用ページの共有のボタン
- 11/19 夕方の定時の回（PM の指示なし・帳面の積んだ順）：2つ済み
  - iPhone のアプリだけの画面（PM 11/19 11時55分・design/ios-app 2版）：PR #125（checkin/ios-app）に足した（5ac9b45・報告の追記 90ac1ab）。報告 docs/pm/report-ios-app-screens.md・写真 docs/pm/shots-ios-app/t146_*
    - I1 位置の説明（#dLocWhy・ログインかデモのあとホームで1回・「次へ」で requestPermissions・答え済みには出さない・登録の流れの位置の段もアプリでは同じ文と「次へ」）・I1c（#nvLocOff が半券の代わり・bpass.dataset.nvHide）・I1e（#dNvSheet）・I4c（startCamera の前に nvPermWhy("cam")）・I2／I5／I5z（#nvNetHome／Ops／Book／Log・最後に読んだ時刻は localStorage soramemo.native.lastread）・I3（renderInstall／doInstall・保存・位置・カメラの文、PUSH_NG_TXT／MIC_NG_TXT）・homeLocStart は geoPermState（アプリは checkPermissions）・Info.plist の文と iPad 縦だけ
    - 「設定を開く」は window.location = "app-settings:"（Capacitor が iOS に渡す前提・Mac で未確認）
    - t146（新・36項目）成功・e2e 全体 114／116（t48・t72 は前から）・tests/ops 成功
    - 本人に決めてほしいこと：位置の説明をデモの人にも出すか／運用のカードごとの「読み込めませんでした」は ops-hub のときでよいか
  - 半券が指で切れない（PM 11/19 14時05分）：ブランチ checkin/tear-finger（main 3a71781 から）・下書き **PR #133**（5e59764・見張り中）・報告 docs/pm/report-tear-finger.md
    - 切れる長さ tearAt（端までの残りの半分・28〜56px）・はじき（0.5px/ms・20px・e.timeStamp で数える）・縦横は 10px で決めて 0.6 倍。押すだけは今のまま
    - t147（新・CDP の指の操作・3つの幅で28項目）成功。t74 の「真ん中から40pxで切れない」を「18px」に直した（新しい決まりでは真ん中は33pxで切れる）。半券のテスト40本 40／40
    - 本人に決めてほしいこと：はじきの速さ 0.5px/ms と縦横 0.6 でよいか。本人の iPhone で試してもらう
- PR #130：11/19 12時55分の main（3a71781・PR #131 の反映）とぶつかったので取り込んだ（7568d8f）。main に別の t140 が入ったので、ピン止めのテストは **t145** に名前を変えた（帳面と報告の t140 は t145 と読む）。取り込み後に t145・t116・t118・t119・t124・t127・t140・t141・t142・t144・t74・t7 成功
- PM の指示 11/19 11時（ピン止めを checkin/pin で・データ担当への依頼を data.md に・iPhone の手順を報告に）：ピン止めと iPhone の手順は PR #130（9d21a37）で済んでいた。data.md はほかの帳面を変えない決まりに当たるので書かず、依頼は下の「ほかの担当への依頼」（11/19・PR #130）のまま。**PM から data.md へ写してほしい**。PR #128 は閉じてよい（PM に任せる）
- PM から積んだ仕事（11/19 9時50分・決定事項【11/19】ピン止めは4版）：1回目済み。ブランチ checkin/pin（main 61ba9c7 から）・下書き **PR #130**（9d21a37・見張り中）・報告 docs/pm/report-pin-app.md・写真 docs/pm/shots-pin/
  - 作った：K1（黒いカードの札 #nearPin）・K1o（一覧の丸 .nrpin、nearRowHTML を .nrw で包んだ）・K4／K4t／K4u（シート・帯・元に戻す）・K0（許可を聞く）・K1s／K6（4つの ON／OFF・出せない知らせは理由）・K2（空港のページ pinApHTML）・K7（pushButtonHTML・spPushHTML の中身を pinLineHTML に。古い形は *Old に残した）・K8（空港を選ぶシートの先頭）・K5（#dPins・マイページの「知らせ」）・K1h（LO_BLOCKS.home に pins・#pinHome）・K9（はじめて開いたとき今の申し込みをそのまま移す・12超えもそのまま）
  - 表は変えていない。ピン止めは localStorage soramemo.pins（[{k,sp,dl,ga}]、k は3レターか "#番号"）。撮影は pushSpot().iata で持つ。pinSync が今の syncPush に airports・sp_airports・ga・spot を作って送る。運用のゴーアラウンドの保存で pinFromGa
  - テスト：t140（新・約60項目）成功。ホームのかたまりが1つ増えた分を t118（35／42／29）・t119（5/5）・t124（42）・t127（/5）で直した。t116 のため黒いカードの札は字 13px・押す所 44px。全体 102／110（t48・t72・t123 は main でも落ちる、残り5本は直して成功）
  - 本人に決めてほしいこと：アカウントに残す表を作るか・撮影をまだ作っていない人が ON にしたら撮る人の設定を開く形でよいか・並べ替えは要るか。iPhone で Safari →ホーム画面にピン止めが移るかの手順は報告に書いた（本番に出たあとでないと確かめられない）
- PM の指示 11/19 9時50分（本人承認）：乗る便の「出発の見込み」と押せなかった半券を checkin/ride-stub-fix（main 61ba9c7 から）で直した。下書き **PR #129**（6899e3f・見張り中）・報告 docs/pm/report-ride-stub-fix.md・写真 docs/pm/shots-ride-stub-fix/。中身は下の PR #128 と同じに、前の便がないときの1行「見つかりませんでした（朝一番の便なら、前の便はありません）」を足した版。**#129 が正、#128 は閉じてよい**（PM に任せる）
  - e2e 全体 108／111（t48・t72・t123 は main でも落ちる）・tests/ops 成功・checkin/ios-app と重ねた版で t143・t144・t74 成功（src は自動で重なり、web/ だけ作り直し）
- 乗る便の「出発しました」の直し＋押せなかった半券（11/19 定時の回・PM から積んだ 11/18 7時45分と 11/19 9時45分）：済み。ブランチ checkin/atd-ticket（main 61ba9c7 から）・下書き **PR #128**（a1f0ca4・見張り中）、報告 docs/pm/report-atd-ticket.md
  - renderRide0：atd が今より後（1分の余裕）なら「出発の見込み HH:MM（航空会社の運航情報）」。前の便の ata・atd・takeoff も未来なら「到着しました／出発しました」にしない。arr_src＝actual でも未来なら「到着の見込み」。first_of_day が来たら「朝一番の便です（この日、この機体の前の便はありません）。」
  - 半券：tear は調べている間は引いた所で待ち、押せたときだけ飛ぶ。押せなかったら戻して揺らす（.bpass.no・stubNo）＋理由を #stubMsg（ckNote・8秒）。キーボードの $("checkin").onclick も同じ
  - src/index.html 変えた：renderRide0・tear・$("checkin").onclick。足した：ckNote・CK_NOTE_T・#stubMsg・CSS .stubmsg
  - t144（新・23項目）OK。関連40本で 39／40（t72 は main でも落ちる）。指で引く形は本人の iPhone で
  - 本人に決めてほしいこと：理由のカードの8秒と場所（667 では今日の数字が一時的に下へ）・「出発の見込み」の言い方
- PM の指示 11/18 5時50分（本人「全てOK、iPhone は自分用から試してみよう」）：1 シークレットの直しは PR #122（673e278）で済みだった。2 iPhone の土台は PR #125 で済みだったので、Mac で動かす手順（1行ずつ・Xcode でチームを選んで ▶・うまくいかないときの表）を docs/pm/report-ios-app.md に足した（PR #125 の追いのコミット）。デザイン担当への依頼は指示どおり design.md の末尾に「チェックイン担当からの依頼」として書いた（ほかの帳面を変えない決まりの例外。PM の指示のため）
- iPhone のアプリの土台（11/18 6時の定時の回・PM の指示なし。帳面の「次にやること」の1つめ＝決定事項【11/18】作り方 A で本人の答えが出たため）：1回目済み。ブランチ checkin/ios-app（main 61ba9c7 から）・下書き **PR #125**（06e603f・見張り中）、報告 docs/pm/report-ios-app-base.md、写真 docs/pm/shots-ios-app/、Mac の手順 ios-app/README.md
  - ios-app/（Capacitor 8.6.0・geolocation 8.2.4・share 8.0.3・browser 8.0.5・SPM・iOS 15 以上・appId jp.soramemo.app）。server.url は使わず、build_www.mjs で web/ を www/ に写し capacitor.js を config.js の前に足す（sw.js・now*.html・og は入れない）。Info.plist：ja・縦だけ・位置（使用中のみ）／カメラ／マイクの理由の文・暗号の申告。アイコンは web/icon.svg を角なし 1024px
  - src/index.html 足した：NATIVE・capPlugin・capGeoErr・capGeoPos・capGeoOpts・capGeoInstall・capShareInstall・capOpenUrl・capLinkInstall・CAP_ON。変えた：captchaOn・pushOK・pushButtonHTML・renderPlusSettings・サービスワーカーの登録。html に data-native="ios"
  - 位置は navigator.geolocation の中身だけ差し替え（呼ぶ所・下の担当のコードは変えない）。共有は字と URL だけネイティブ、画像つきは WebView のまま。外のリンクは @capacitor/browser
  - アプリの中ではロボット除け・Web Push（「アプリの通知は準備中です。」）・そらメモ＋の申し込みと解約のボタン・サービスワーカーを使わない
  - テスト t143（新・18項目）OK。tests/ops 成功。e2e 109／111（t48・t72 は main でも落ちる。t123 は通った）。追いのコミット 報告だけ。Xcode のビルドと iPhone の動きは未確認（Mac がない）
  - 本人に決めてほしいこと：本番の CAPTCHA が ON ならアプリの中ではログインのコードを送れない（自分用はデモで見るか、別の確かめ方を決めるか）／縦だけでよいか／マイクの理由の文
- iPhone のアプリにする計画（PM 11/17 20時30分・11/18 0時15分の指示）：済み。ブランチ checkin/ios-plan（main 61ba9c7 から）・下書き **PR #124**（f0aab2d）、報告 docs/pm/report-ios-app-plan.md。コードは変えていない
  - おすすめは Capacitor 8（Node 22 以上・Xcode 26 以上・iOS 15 以上・SPM）で今の web を包み、位置・通知（APNs）・カメラ・共有だけネイティブの部品。server.url で本番を読むだけの形はやめる
  - 審査：4.2・位置は「使用中のみ」と理由の文・非公式の書き方・出典・有料はスマホ新法（2025/12/18）も含めて申請前に確かめる。登録は個人だと本名が販売元に出る、組織は法人と D-U-N-S
  - 本人が Mac で貼る手順（Xcode・シミュレーター・node の確かめ）を報告の6に書いた
  - 本人に決めてほしいこと：作り方 A でよいか／個人か組織か／そらメモ＋をアプリで売るか／Turnstile をアプリで使うか
- 11/18 の2回目の回（PM の指示の続き「3 空港の3D・4 iPhone の計画」）：3 は PR #123 で済みだったので data/airport-3d-data（PR #72・報告だけ）を checkin/airport-3d に取り込んだ（push 済み）。4 を PR #124 で作った。指示の文に「基地の名前・秘境の見出しは確認中なので変えない」とあったが、帳面の決定事項（11/18 0時15分「基地」のまま・「シークレット」で隠す）が先に入っていて、PR #122 に入れ済み（673e278）。違っていたら PM が戻す指示を
- 空港の3D（11/17 18時05分の PM の指示の3つめ・決定事項【11/17】）：1回目済み。ブランチ checkin/airport-3d（main 61ba9c7 から）・下書き **PR #123**（c69545b・見張り中）、報告 docs/pm/report-airport-3d-app.md、写真 docs/pm/shots-airport-3d/
  - 入口：羽田の空港ページの数字のカードの下に小さな「3Dで見る ›」（押すと直接開く）＋「空港の今」の見出しの下に見本の絵（SVG・何も読まない）。字は「押すと読み込みます（約0.2MB）」
  - 押したときだけ three.js 0.160.0（jsdelivr の three.module.min.js）を import。全体（北の上空から南・指で左右に回す・空の機体は8倍）／管制塔（約116m・はじめ南）／機体のうしろ。名札は空の機体だけ（高さつき・端で切れない）。一覧・カード・出典のシート・軽い表示（電池20%以下で自動・「ふつうに」）・尾翼は昼だけ金・夜は灯り
  - 機体は airport-traffic を20秒ごと、1分前の時刻を2つの答えの間でつなぐ（a3Planes・a3Lerp・a3Ahead）。今の airport-traffic は地上の機体を返さない（一覧に「地上の機体はまだ出ません」）
  - 空港の形は仮（HND_RWY と T1〜T3 の位置から作った島と箱。管制塔の位置はおおよそ）。データ担当の形のファイル・?view=3d・FAA の大きさの表が来たら差し替え（出典の文も）
  - 変えた関数：openAirport・renderNow。足した：ap3dPillHTML・ap3dCardHTML・openAp3d・closeAp3d・a3*（報告に一覧）
  - テスト t142（新・40項目）OK。tests/ops 成功。e2e 108／111（t123・t48・t72 は前から）。追いのコミットは報告だけ
  - 本人に決めてほしいこと：入口の字の大きさ（約0.2MB）／全体の視点の引き具合／カードを開いた写真の上が平らな水色に写る件（ヘッドレスだけか iPhone で）
- 図鑑の飛行場・滑空場の2回目（PM 11/18 0時15分・本人の決定）：済み。PR #122 に足した（673e278）。報告 report-zukan-airfields-app.md の2回目
  - 実績の見出しを「シークレット」（ACH の sc1 の cat）・取るまで「？？？」と「取ると中身が見られます」。基地の図鑑の秘密の枠も見出し「シークレット」で押すまで数を出さない・開いても「？？？」1枠・場所も「？」（extraBook・extraGrid）。ほかの図鑑・実績の「基地」の数は押した分だけ（renderZkOthers）
  - t70・t141 を直して足した。t70・t141・t127 成功
- 図鑑の飛行場・滑空場（11/17 18時05分の PM の指示の2つめ・決定事項【11/17】）：済み。ブランチ checkin/zukan-airfields（main 61ba9c7 から）・下書き **PR #122**（f6198d9・見張り中）、報告 docs/pm/report-zukan-airfields-app.md、写真 docs/pm/shots-zukan-airfields/
  - 入口・ほかの図鑑・実績の行・ヘリポートの札（データが入ったので出す）は PR #75 のまま。足したのは2つ
  - 「番外編」の言葉をやめた：基地の図鑑の題と行は「基地」（renderBook・renderZkOthers・#bookExtra の題）、印の説明の見出し（showStamp）・空港ページの名前の下（openAirport）・選ぶ欄（fillSelects）・実績の見出し（ACH・renderAch の AIR_CATS。id は不変。秘密の見出しは「一般の人が行けない飛行場」）
  - 夜の小さな地図で滑空場は四角（zkxDot・zkxMapSVG。.zxmap .zn／.zd で昼夜を出し分け）。夜の凡例も出す（zkAirEntryHTML の i に k-種類）
  - テスト t141（13項目）OK・tests/ops 成功・e2e 108／111（t123・t48・t72 は前から）
  - PR #121 と夜の図鑑の CSS の行（.zx-k・.zx-kd i）がぶつかる。両方の行を残せばよい（PR に書いた）。先に入った方のあとで、もう一方に main を取り込み直す
  - 本人に決めてほしいこと：基地の図鑑の名前「基地」でよいか（一般の人が行けない飛行場も入る）／秘密の実績の見出し
- 近くの空港の小さな直し3つ（11/17 18時05分の PM の指示の1つめ）：済み。ブランチ checkin/near-fix（main 61ba9c7 から）・下書き **PR #121**（2fc3afc・見張り中）、報告 docs/pm/report-near-fix.md、写真 docs/pm/shots-near-fix/
  - 大利根が二つ：同じ短い名前が2つのときだけ正式な名前（zkxCut・ZKX_DUP・zkxShort）。「大利根／滑空場」で折る（zkxBreak）
  - 東京ヘリポートの名札：いまここへの点線にかからない側に置く（renderHomeMap の最後・homeSegHit）。点線が縦（加須・八尾）は今のまま
  - 夜の札：[data-night="on"] #v-book .zx-k と .nrow2 .t を #141B24／#BCC6D1（5版の夜の色）。1.1〜1.3 → 10。.zx-dtag と #v-home .ktag は前のまま
  - テスト t140（17項目）OK（main の版では9項目 NG）。tests/ops 成功・e2e 108／111（t123・t48・t72 は前から）・tests/sql は SQL 不変（t92 だけ手元で時間切れ）
- いつもより○分遅いの画面（11/17 12時20分の PM の指示・本人「OK」）：済み。ブランチ checkin/usual-late（main 32d923d から）・下書き **PR #117**（0f76975・見張り中）、報告 docs/pm/report-usual-late-app.md、写真 docs/pm/shots-usual-late/
  - 乗る便のカード（renderRideIntl）：時刻表にない便だけ見込みの箱（U1・U1n・U2・U2b 門限・U2c ダイバート・引き返し）・灰色の点線の札・箱の中の出典の1行。ODPT の出典は外した。長い説明は「出典と注意 ›」
  - 乗る便があるときはシートの先頭（#rideTop へ #rideCard を移す。rideTop・renderRide0。表示の編集で隠しているときは戻す。国内線も同じ）
  - 案内板（foreignHTML・ulPlane）：題「時刻表にない便（いま近くにいる便）」・凡例・点線・札「海外」「日本」。airport-foreign の planes に usual のキーがない今の版では札は出さず前の字のまま
  - 機体のくわしく（spDetailHTML に ulSpBox を差し込んだだけ。撮る人用・運用予想の持ち場なので依頼に書いた）
  - データ：回の途中でデータ担当の PR #118（移行185 usual_late）が出たので取り込み（マージ）、本物の返す形（usual・eta の入れ子・reason・divert_to・curfew_near）に合わせた（8378c0a まで）。p_arr・p_land も渡す。404 のときだけ foreign_late に切り替え（ulFetch・ulNorm）。usual_late は「いつもの出発」を返さないので出発前（U2）は着く時刻だけ
  - 足した関数：ulName・ulJP・ulMin・ulJstMin・ulDiff・ulTagText・ulTag・ulNorm・ulFromLate・ulFetch・ulCurfew・ulRideBox・rideTop・renderRide0・ulPlane・ulSpBox。変えた：renderRideIntl・renderRide・applyLayout・foreignHTML・spDetailHTML
  - テスト t139（新・33項目）OK、t60 を新しい形に直した。tests/ops すべて成功・tests/sql 124本成功・e2e 107／110（t123・t48・t72 は main でも落ちる。t72 は #opsSpecial の開くボタンが運用タブを分けたあと見つからない）。追いのコミット bedd649（報告）
  - 本人に決めてほしいこと：国内線の乗る便も先頭でよいか／ダイバートのときの国際線の記録の到着空港
  - 2回目の回（11/17、PM が同じ指示を手で呼んだ）：PR #117 で済みだった。main は 32d923d のまま、#118 の最新は取り込み済み、PR のコメント・CI はまだなし。変えたものはなし
- #113 の反映がテストで止まった件（11/16 23時55分の PM の急ぎ）：済み。ブランチ checkin/fix-ops-test（main b9f59f2 から）・下書き PR #114（4391d34・見張り中）、報告 docs/pm/report-fix-ops-test.md。変えたのは tests/ops/ops.test.mjs だけ（src/index.html の関数は変えていない）
  - 画面案 2版（A1-v2 滑走路に特別塗装機の欄なし・Q1-v2 撮る人に出る）どおりなので①テストを直した：羽田は滑走路で「欄なし・名札あり」、撮る人の見方を押して「羽田に来る特別塗装機」とエラーなし。ops.test.mjs はすべて成功（2回）
  - 地図の★：滑走路は特別塗装機を読まない（t130）ので★が付かない。撮る人には地図がない。戻すか本人の答え待ち（戻すなら滑走路で special_now だけ読み、t130 を合わせる）
  - tests/sql の t111（経営の返金）が 11/17 日本時間に手元で2件 NG（12345×月の残りの比が割り切れる日に JS と SQL の切り上げが1円ずれる）。持ち場の外なので依頼に書いた。今日やり直すと SQL のテストで止まるかもしれない
  - 2回目の回（11/17 0時台、PM が同じ指示を手で呼んだ）：PR #114 で済みだった。main は b9f59f2 のまま、変えたものはなし
  - Actions：#109（4af96c8）の反映は成功 → PR #107 と #96・#90・#84 は本番に出た。#113（b9f59f2）は失敗（tests/ops の2件だけ）
- 11/16 23時20分（日本時間）PR #112（運用タブの空港と機体）が main に入った。本番に出たかは次の回に Actions で確かめる。本人の答え3つ（「近く」・A2e の入口タイル・運用タブの外の機体）はまだ
- 運用タブを空港と機体に分ける（11/16 15時50分の PM の指示・本人「OK」）：済み。ブランチ checkin/ops-split（main 4af96c8 から）・下書き PR #112（361bb78・見張り中）、報告 docs/pm/report-ops-split-app.md、写真 docs/pm/shots-ops-split/
  - 上を1行（空港｜機体＋空港のピル＋ⓘ＋共有／探す欄＋ⓘ／戻る＋登録記号＋共有）。空港のピルの「近く」は外した
  - 空港の側は見方7つ（撮る人も・案2）。特別塗装機のかたまり（opsb:special）は外し、OPS_NEED.special は撮る人だけ
  - 機体の側（VIEWS.opsp：recent・special）。最近見たは端末だけ（soramemo.ops.recent・8機）。運用タブを見ているときの openPlane はタブの中（opsPlOpen）、ほかはシート
  - 「機体」を出す OFF は layout.opsPlane = 0。表示の編集は運用（空港）／運用（機体）。数 39→41
  - 足した関数：opsPlaneOn・opsPlaneSet・opsSide・opsSideSet・vsName・opsRecent・opsRecentAdd・opsPlaneInTab・opsFlying・opsPlRow・opsRecentHTML・renderOpsPside・applyOpsSide・opsSideRefresh・opsPlHead・opsPlOpen。変えた：applyOpsView・VIEW_RENDER.ops・opsNeed・renderSpecial・openPlane・renderOpsApPicker・vsHTML・loItems・loSecDef・loSecIds・loSecHTML・opsShare ほか（報告に一覧）
  - テスト t138 を足した。t118・t124・t130 を直した。全体は t123・t48・運営コンソールのもの以外成功
  - 2回目の回（11/16、PM が同じ指示を手で呼んだ）：PR #112 で済みだった。main は 4af96c8（#109）のままで取り込み済み、PR のコメント・CI はまだなし。変えたものはなし
  - 本人に決めてほしいこと：「近く」を外してよいか／A2e の入口タイル（羽田に来る機体・乗った機体）を入れるか／運用タブの外で機体を押したときもタブへ移すか
- 11/16 17時26分（日本時間）PR #107（見落としの片付け）が main に入った。本番に出たかは次の回に Actions で確かめる。ODPT の時刻はデータ担当の odpt_feed_at が入るまで今までの文のまま
- 見落としの片付け（11/16 14時10分の PM の指示・本人「OK」）：済み。ブランチ checkin/redo-1116（main 2ae2e1f から）・下書き PR #107（062e504・見張り中）、報告 docs/pm/report-redo-1116.md、写真 docs/pm/shots-redo-1116/
  - 1 運用タブの遅れのカードを1便1枚（fix/fw-merge の入れ直し）：通知のまとめ方にそろえ、便名の0をそろえる・共同運航（出発・到着・出発の定刻が同じ。std を返せばそれ）を1枚・便名は運航情報 → JAL・ANA。足した fwMerge・fwNo（FW_RANK）／変えた fwCard・fwHTML・delayTileHTML。t135
  - 2 送れないときの言い方（#15 の入れ直し）：変えた auSendErr・auSend。t115
  - 3 ホームのメールのログイン欄を消す（#23 の入れ直し。main にまだあった）：#loginBox ほかと initCaptcha・resetCaptcha・CAPTCHA を消した。変えた updateAuthUI
  - 4 揺れるテスト（#20 の入れ直し）：keepls.py・t117。t17・t19・t37・t62 は4回くり返して成功
  - 5 ODPT の dc:date：出典に「運航情報 ○時○分・時刻表 ○月○日時点」。足した odptAtText・odptCredit・setOdptAt・loadOdptAt・loadOdptAtSoon（ODPT_AT）、ODPT_CREDIT を let に。変えた loadFlightAlerts・renderOpsAlerts。rpc/odpt_feed_at（データ担当に依頼中・まだない）を運用タブと空港の今を開いて8秒あとに読む（t130 の本数を守るため）。t136
  - テスト全体 102/107（t123 は main でも落ちる・t99・t105・t48 は前から）
  - 本人に決めてほしいこと：時刻の書き方／別の1本で読むか、今ある返す形に入れてもらうか
  - #15・#20・#23 は「入れ直したので閉じてよい」と報告に書いた。fix/fw-merge は PR がなかった
  - 2回目の回（11/16、PM が同じ指示を手で呼んだ）：PR #107 で済みだったので、main（2ae2e1f のまま）・data/redo-1116（まだない）・PR #107 のコメント（まだなし）だけ見た。変えたものはなし
- 11/15 15時ごろ（日本時間）PR #96（海外の止まり具合の画面）が main に入った（PM のまとめ PR #97・754bca5。運用予想の案A と一緒。運用予想のテストは t134 に番号を変えた）。本番に出たかは次の回に Actions で確かめる。データ担当の #93（移行169）が本番に入っていないと画面には何も出ない（取れないときは出さない作り）
- 海外の空港の止まり具合の画面（11/15 12時40分の PM の指示・本人「A」）：済み。ブランチ checkin/world-ops（main 5a22d8e＋data/world-ops 664e5dd）・下書き PR #96（9f601cc・見張り中）、報告 docs/pm/report-world-ops-app.md、写真 docs/pm/shots-world-ops/
  - 案内板の国際線の便にピンの札（FAA のいちばん重いもの1つ・出発前／到着前だけ・便の数の札は列に出さない）＋ピンの説明の1行。海外の航空会社の上に「行き先の海外の空港のいま」の欄（案内板の便の行き先・出発地のうち FAA があるか欠航・30分以上の遅れがある空港だけ・断り書きは太字・note）。押すとくわしく（#dWorldAp）。乗る便のカード（国際線）に1行（FAA・便の数）と出典の断り
  - 読むのは rpc('world_airport_ops', { p_iata:null }) を1回。案内板の見方で国内線以外・乗る便が国際線のときだけ。2分（見方を変えたときは3分）は取れなかったときも読み直さない
  - データ担当の仕上げ（PR #93 の a33a975）の返す形に合わせた：札とくわしくは label、わけは reason_ja（下に原文）、出典は空港ごとの note、「○時○分 更新」は feed_at（足した関数 woLabel・t133 は44項目）
  - 関数：足した loadWorldOps・woAp・woFaa・woShow・woHM・woLocal・woFeedAt・woNote・woTag・woCountTag・woSub・woRowTag・worldOpsHTML・worldApSheet・worldRideHTML（WO_KIND・WO_ORDER・WO_TREND・WOPS）／変えた boardHTML・renderBoard・renderRideIntl。dialog#dWorldAp と CSS（.wotag・.wopin・#v-ops .wobox ほか・.ridecard .woline・dialog.wodlg）
  - テスト：t133（新・41項目）成功。t130・t60・t128・t132 成功。全体 92/102（t19・t27・t34・t37・t47 は流し直して成功、t17 は揺れ、t62 は main でも落ちる、残りは前からの t105・t99・t48）
  - 本人に決めてほしいこと：欄を案内板の便の行き先だけに絞った形でよいか／乗る便の1行を押すとくわしくが開く形
  - 2回目の回（11/15、PM が同じ指示を手で呼んだ）：PR #96 で済みだったので、data/world-ops（a33a975 のまま・取り込み済み）・main（5a22d8e のまま）・PR #96 のコメントと CI（どちらもまだなし）だけ見た。変えたものはなし
- 遅れの通知の受け取り（11/13 21時20分の PM の指示・データ担当 data/alert-merge の依頼）：済み。ブランチ checkin/push-renotify（main 4fb2f42 から）・下書き PR #90（016bba9・bcbb90a）、報告 docs/pm/report-push-renotify.md
  - src/sw.js の push の受け取りで showNotification に `renotify: !!(d.tag && d.renotify)` を渡す（tag がないときは立てない）。web/sw.js を組み立て直した（1行だけ）。画面と src/index.html は変えていない（変えた関数なし）
  - テスト：t132 を足した（sw.js を node の vm で読み push を5件送る・9項目成功）。t128・t60 成功。全体 93/101（t123・t17・t47・t62・t19 は流し直して成功、残りは前からの t105・t99・t48）
  - 本人に決めてほしいこと：なし。data/alert-merge と一緒に反映
- 全体の見回りの直し（11/13 4時の PM の指示・report-sweep-1113／report-speed-1113）：済み。ブランチ checkin/fix-sweep-1113（main 3ac3d91 から）・下書き PR #84（91a8a4e・2d63304）、報告 docs/pm/report-fix-sweep-1113.md、写真 docs/pm/shots-fix-sweep-1113/。11/13 20時、PM のまとめの PR #87（pm/release-1113）で main に入った（4fb2f42）
  - 1 図鑑のツメをデモの帯の下に（667 はすき間 0 の .tight）／2 ホームの MAIN.wrap・上の段の透明な所は pointer-events:none／3 乗る便のカード（国際線）は前の日に出た便まで出す・t60 は「今」と「日本時間 1:30」（clock.set_system_time）の2回／4 フライトの地図は淡色地図（画像）を敷く（maplibre は使わない）／5 ログインの「デモで試す」は新規登録の下に高さ 44px・700px 未満は上を詰める／6 図鑑の scroll-padding-bottom／7 見方の帯・上の段・デモの「終了」・シートのつまみは ::after で押せる範囲 44px 以上（div.viewsw の下の線は背景に）／8 sw.js は staleWhileRevalidate・supabase-js を head で先読み（#sbPreload）・mapBase は部品が届くまで淡色地図・3つの rpc は前から並べて呼んでいた／9 デモの便は今日0時から数えた決まった時刻・loadPushKey はデモでは呼ばない・authCapOff で turnstile.remove()／ついで setViewsw は選んだ見方が見えていれば左端から（見回り #3）
  - 関数：変えた zkTsumeSync・renderRideIntl・renderFlightMap・mapBase・authRender・authClose・setViewsw・demoSeed・loadPushKey／足した authCapOff。fake_turnstile.js に remove
  - テスト：t128（54項目）すべて成功。全体 89/97（t123・t17・t27・t34・t62 は流し直して成功、残りは前からの t105・t99・t48）
  - 本人に決めてほしいこと：サービスワーカーで配った直後の1回目は前の版が出る形でよいか／デモの便の日付も固定するか／ログインの「デモで試す」をボタンにした形
- 図鑑の題を「飛行場・滑空場・ヘリポートの図鑑」にそろえる（11/12 14時50分の PM の指示・本人「A」）：済み。PR #75 に足した（7a901bd）、報告 docs/pm/report-zukan-heli-title.md、写真 shots-near-airfields/10-zukan-entry-844／667・11-airbook-844／667・12-airbook-kanto-844・14-others-844／667
  - 題は定数 ZKX_TITLE／ZKX_TITLE_BR（NEAR_KM の前）。入口のカード（題・読み上げ）・図鑑の題・扉の札「飛行場・滑空場・ヘリポート」・ほかの図鑑・実績の行・ホームの「…の図鑑に入ります」・ヘリポートの説明・小さな地図の読み上げ
  - 題は「飛行場・／滑空場・／ヘリポートの図鑑」のかたまりで折る（.nw）。扉の札は北海道で切れて上へのボタンが隠れたので、入らないときは2行（12px）。関東も2行になる
  - 「飛行場・滑空場の実績」の見出しは変えていない（実績は滑空場・飛行場の2つだけでヘリポートの実績がないため）
  - 関数：足した ZKX_TITLE・ZKX_TITLE_BR／変えた nearRowHTML・showStamp・zkxMapSVG・zkAirEntryHTML・zkAirBookHTML・renderZkOthers・#bookAir のもとの題・CSS #v-book .zx-dtag
  - テスト：t127 に題・折れ・扉のはみ出し・ほかの図鑑・実績の確かめを足してすべて成功。全体 90/96（t61・t19・t62 は流し直して成功、残りは前からの t105・t99・t48）
  - 改善担当は review-app-2 で「反映してよい（題を先に）」。題が入ったので、あとは本人の「反映して」待ち
  - 本人に決めてほしいこと：扉の札を2行のままにするか、短くする（外す・「飛行場など」）か
- 近くの空港の反映の前の直し（11/12 13時30分の PM の指示・review-app-1）：済み。PR #75 に足した（6a3b6e7・5685a10）、報告 docs/pm/report-near-airfields-fix1.md、写真 shots-near-airfields/02-kazo-full-844／740／667・05b-tokyo-full-844・03・06・08
  - 1 引き上げたとき地図を「いまここ」と先頭が両方入るよう寄せ直す（閉じたら元へ）／2 一覧は民間空港の行も入れて 844 は3行・760 未満は2行（844 の下のすき間 55px）。引き上げた位置では続きを画面の下の端より下から始める（今日の数字がのぞかない・送ると丸ごと見える）／3 一覧とすべては短い名前（羽田空港・伊丹空港・成田空港・関西空港、ほかはかっこを外す）で2行まで／4 「飛行場・滑空場・／ヘリポートも出す」で折る・OFF の補足「近くは民間空港だけ」／ついでに7 引き上げた位置で ＋− を隠す
  - 関数：変えた renderHomeMap・homeMapPad・homeEdge・initSheet の go・nearRowHTML・renderNearList・loSecDef（ホーム）・loRowHTML（labelHTML）・heNearxHTML／足した NEAR_SHORT・nearShort・nearGapSync・NEARX_H
  - テスト：t127 に確かめを足してすべて成功。全体 91/96（t61 は流し直して成功、t17 は3回目に成功、残りは前からの t105・t99・t48）
  - 本人に決めてほしいこと：短い名前の決め方でよいか（ほかは前と同じ：ヘリポートの印・図鑑／東京駅で先頭がヘリポート）
- 近くの空港と図鑑の飛行場・滑空場（11/12 10時25分の PM の指示・本人「1.2はOK」）：ブランチ feat/near-airfields（main e443373＋data/heliports を取り込み）・下書き PR #75（d821406）、報告 docs/pm/report-near-airfields-app.md、写真 docs/pm/shots-near-airfields/（01〜13）
  - 近くの空港：民間空港・飛行場・滑空場・ヘリポートを近い順（基地は出さない・判定は nearestBase のまま）。半券は「いちばん近い」・パタパタは先頭が民間空港でコードがあるときだけ・ほかは種類の札・ピル「ほか○つ ›」（20km）／「近くの民間空港 ›」／引き上げた位置で「閉じる ⌄」。引き上げた位置の一覧（見出し「ほかに 20km 以内 ○つ」・844 は3行、760 未満は1行・民間空港の行は2段目に「民間空港でいちばん近い」）と「すべて」のシート（#dNear）。範囲の中は「飛行場・滑空場の図鑑に入ります」。667 の一覧の下とタブ帯のあいだ約17px
  - 「飛行場・滑空場・ヘリポートも出す」（はじめ ON・LAYOUT.nearx＝0 で OFF）：ホームに出すものの半券の下の枝の行と表示の編集のホームのカード。○/4 の数に入れない
  - ヘリポート12か所を EXTRA_RAW に（heli・札「ヘリポート」・昼は土色）。印は今の checkin 関数のまま押せる（本人の答え待ち）
  - 図鑑：地方別の黒いカードの下に入口（3 / 75・小さな地図・重なる行った丸は数の入った1つ・667 は1行）。飛行場・滑空場の図鑑はツメ＋扉＋枠（#bookAir・#zkxTsume・四国は押せない）。ヘリポートもこの図鑑に入れた（75）
  - 関数：足した nearX・nearKind・nearMoreSync・nearRowHTML・renderNearList・openNearAll・nearxSet・heNearxHTML・zkxList・zkxShort・zkxBreak・zkxCounts・zkxMapSVG・zkAirEntryHTML・zkxTile・zkAirBookHTML／変えた nearest・showNearest・sheetTop・initSheet の go・renderHomeMap・enqueue（nearestBase）・heHTML・loSecDef・loSecCount・loRowHTML・loSecHTML・renderBook・zkRegionHTML・zkJump・zkTsumeSync・renderZkOthers・showStamp・印の色
  - テスト：t127（新）すべて成功。t119 はホームに出すもののスイッチの数を直して成功。全体 87/96 → t13・t17・t19・t37・t62 は流し直して成功、残りは前からの t105・t99・t48
  - 本人に決めてほしいこと：ヘリポートで印を押せるか・同じ図鑑か（今は押せる・75）／東京駅で先頭がヘリポートになる／入口を地図・行った順にも出すか／飛行場の図鑑の戻る先
  - main には入れていない
- 見方の設定の反映の前の直し（11/11 17時20分の PM の指示・review-app-1）：済み。PR #68 に足した（c837993）、報告 docs/pm/report-view-settings-fix1.md、写真 shots-view-settings/20-844-top-44px・21-667-close-44px（10〜15 も撮り直し）
  - 1 表示の編集の上の「‹ マイページ」「閉じる」「すべて」「隠しているもの」を 44px（CSS だけ）
  - 2 タブを全部出していて成績のタブがないとき、タブのカードの補足を「成績はマイページから」（指摘の長い文は 390 幅で切れた）
  - 3 デモで変えた表示は終えると戻す（demoLoSave・demoLoRestore・demoLoReload・soramemo.demo.lobak。開き直してデモが終わったときも読み込みのはじめに戻す）
  - 4 LO_EXT.sg がない間は1枚の下に「修行の見方は、修行の画面の鉛筆から変えます。」
  - 関数：変えた loSecDef・layoutHTML・toggleDemo の処理／足した demoLoSave・demoLoRestore・demoLoReload
  - テスト：t126（新）17項目成功。t124・t118・t122 成功。全体 88/95（前からの t105・t99・t48・t62。t62 は直す前の版でも落ちる）
- 11/11 19時ごろ（日本時間）PR #68（すべての見方の設定）が main に入った（本人が下書きを外してマージ）。その前に main（修行 #64 入り）を取り込み、web/ を組み立て直した（5f8f31f・関係するテスト8本成功）。本番に出たかは次の回に Actions で確かめる
- すべての見方の設定（11/11 13時5分の PM の指示・本人「すべてよい」）：ブランチ feat/view-settings・下書き PR #68（8d52a1c）、報告 docs/pm/report-view-settings-app.md、写真 docs/pm/shots-view-settings/（01〜04・10〜15）
  - 案A：地方別・日誌も OFF にでき、最後の1つだけ残る（loToggleOff）。案A で保存すると layout に vA:1。vA のない古い保存は zkFixLayout が前どおり地方別・日誌を出す。fmt 3 のまま
  - 鉛筆のシート（vsHTML）：全部の行に説明（VIEW_DESC・vwDesc）、OFF でも説明は残す、「最後の1つ」の札＋行の下に理由。見方が1つでも帯に名前と鉛筆を残す（setViewsw の .vwone）
  - 表示の編集の1枚（layoutHTML・openLayout）：畳んだカード（tabs・home・book・log・ops・stats・aps）、ON／OFF、「すべて｜隠しているもの N」と「32このうち」、行き先の字、鉛筆から来たらそのカードだけ開いて光る（LO_OPEN・LO_RING・loScrollTo）、5つのときタブを ON → タブを選ぶの入れ替え。元に戻すの帯は下に止まる
  - 修行のカードは LO_EXT.sg（groups()・toggle(id)）を修行担当が足すと出る。shugyo.md に書いた
  - 消した：loPill・LO_CHECK・LO_LOCK、ピルの CSS（.lohero・.lolegend・.logrp・.lopill・.lolock）
  - テスト：t124（新）30項目成功。t118・t122・t120・t71・t79 を直した。全体 82/93（前からの t105・t99・t48・t57、main でも落ちる t61・t73、開き直しの揺れ t27 は 5/7）
  - 夜：アプリに夜の画面（シートの地）がないので夜の写真は撮っていない。夜の光る縁は白の CSS だけ
  - 本人に決めてほしいこと：ホームのカードの数（4/4、画面案は 7/7）／タブのカードの成績の行（隠しているものに数えない）／「全部を見直す」のタイルの名前
- 11/11 14時40分（日本時間）PR #65（フライトの作り直し）が main に入った（2344c44「反映：フライトの作り直し（PR #65）…」）。下の PR #65 の項目はこれで済み。次の「すべての見方の設定」は main から始めてよい。本番に出たかは次の回に Actions で確かめる
- フライトの反映の前の直し（11/11 13時の PM の指示・review-app-1 の1〜3）：済み。feat/flight-book・PR #65 に足した（bb1d639）、報告 docs/pm/report-flight-book-fix1.md、写真 shots-flight-book/40-844・40-667・41-844・41-667
  - 1 statusRows で isCar(f) の便を飛ばす（成績の目安も修行も直る）。デモで JAL 15便 15,064 FOP → 14便 14,116 FOP
  - 2 大きい年のカードは止めない。年の字が上へ隠れたら、年の字と ‹ › だけの細い帯（#fbMini／#fbMiniBar・48px・高さ0の入れ物で下の便は動かない）を上に止める
  - 3 凡例の車などの点線が .lgrow i に負けていた → .fblg .lgrow i.dash をあとに足した
  - 関数：変えた statusRows・renderLog・fbGoYear・日誌のスクロールの処理／足した fbMiniSync
  - テスト：t123 に5つ足して成功。全体 84/92 → 流し直して t19・t61 成功。残りは前と同じ（t105・t99・t48・t57・揺れの t31・修行の t73）
  - 残り（指示待ち）：review-app-1 の4 共有を1つに・5 667 で共有のボタンの段・6 デモの時刻と便名・7 読み取りの行 44px・8 夜
- フライトの作り直し（11/11 9時10分の PM の指示・本人「すべてOK」）：ブランチ feat/flight-book・下書き PR #65（3cd5ad2）、報告 docs/pm/report-flight-book-app.md、写真 docs/pm/shots-flight-book/（844・667・昼夜）
  - シートをやめ上の段つきの1画面。見方は日誌（diary・いつも）・地図（map）・年のまとめ（year）。古い id（sg・pass・board・text・cal・route→diary、month・alt→year）は読むときに直す（FB_VIEW_MAP・viewOf・zkFixLayout）
  - 日誌：年のカード（日誌だけ上に止まる・年の帯が来ると年が変わる）・月の見出し・1便1行・年の帯・「○年の便はここまで」・年を選ぶとその年の頭へ（いちばん古い年は下に余白を足す）
  - 1便（dFbView）：共有・✎（今の便の窓）・機体は毎日の記録・この区間の便。画像で共有（dFbShare）：登録記号はじめ ON・座席はじめ OFF・券の下3段・入らないときは座席→登録記号の順に外す
  - 年のまとめ：4つの数・月ごとの便の数・いちばん長かった月・よく乗った路線・下にそらメモ＋の年のまとめ（共有はそらメモ＋の人だけ。前と同じ）
  - 地図：カードの中に別の地図（FB_MAP）、読めないときは SVG。太さ＝回数（10回で止める）・1色・区間を押すとその区間
  - 車など：isCar・setCar・flyOnly（この端末に覚える soramemo.car。f.mode === "car" も見る）。便・空の上・距離・路線（routes・focusKm・ホームの便の数・yearStats）に入れない。デモは長崎→福岡
  - 気軽にの構成は日誌と地図（年のまとめを隠す）。隠す提案：気軽に 6こ・撮る人 2こ
  - main（#48・#63 の入った版）は取り込み済み（24b326d）。表示の編集 32こ、見方のシートの日誌は「いつも」
  - 関数：足した fb*（fbEntries・fbDiaryHTML・fbYearHTML・fbMapHTML・fbMapSVG・fbGoYear・fbOpenView・fbOpenShare・fbPassCard ほか）・isCar・setCar・flyOnly／書き直した renderLog・setLogSeg・renderFlightMap・VIEWS.log・VIEW_DEF・PERSONAS・HS・routes・focusKm・openFlight・demoSeed・goTab・yearStats・loToggleOff ほか／消した logViewHTML・renderMap・drawRoutes・FMAP_COL
  - テスト：t123（新）成功、17本を直した。全体 81/92 → 流し直して t118・t119・t19・t61 成功。残りは前からの t105・t99・t48・t57、揺れの t17・t31（main でも同じ）、修行の t73
  - 本人に決めてほしいこと：車などの印をこの端末だけで覚える形でよいか（サーバーの列はデータ担当へ）／年のまとめの共有をみんなに出すか／気軽には日誌と地図でよいか／前の「年ごと」の全体の記録をフライトから外してよいか
- 11/11 9時半ごろ（日本時間）PR #48（全部乗せ 案3「タブから選ぶ」・出す隠すは ON／OFF）が main に入った（771e96b「反映：…（PR #48）」）。下の PR #48 の項目はこれで済み。本番に出たかは次の回に Actions で確かめる
- 反映の前の小さい直し（11/10 20時の PM の指示）：2つとも済んだ（11/10 夜の定時の回）
  - feat/zukan-facts・PR #63（7c67543・報告 eb1413d）：review-facts-1 の1〜5。データ欄と出典は押した記録とターミナルの下・前／次の上へ／出典 13px・リンクの押せる高さ 44px／福岡は A・B と「ほかにヘリポート 2（奈多地区）」／1本の空港はカードの中に長さ×幅／図鑑の上の「索引」「ほかの図鑑・実績」はツメの左で止める（main と同じ問題だったもの）。関数：変えた zkFactsHTML・openAirport、CSS #v-book .zk-ttl。t121 に5項目足して成功・全体 84/89（前からの t105・t99・t48・t57、t47 は流し直して成功）。写真 05a・07 が新しい
  - feat/all-in-tabs・PR #48（ae6e870）：review-c5 の1・2。見方の帯の鉛筆は、その画面の見方だけの小さいシート（#dViews。題・数・完了は固定、ON／OFF、図鑑の地方別は「いつも」、1つ以上、元に戻す、下に「表示の編集をすべて見る ›」）。鉛筆の押せる所 44×44。マイページの「全部を見直す」の1枚は題と閉じるを上に固定。関数：足した vsHTML・vsRender・openViewSheet・VS／変えた vwEditBtn。t122（新）成功、t118・t71 は鉛筆の行き先を直して成功。全体 82/90（t19・t27・t62 は流し直して成功、t31 は待ち方を CSP で止まらない形に直して成功 3a044d5、残りは前からの t105・t99・t48・t57）。報告 docs/pm/report-all-in-tabs-c5.md、写真 shots-all-in-tabs/30〜33
  - 本人に決めてほしいこと：「全部を見直す」の1枚の部品（今も ✓ のピル）を ON／OFF にそろえるか、1枚ごとやめるか（1月の公開の前）
- 図鑑のデータ欄（11/10 16時の PM の指示）：ブランチ feat/zukan-facts・下書き PR #63（b955478）、報告 docs/pm/report-zukan-facts.md、写真 docs/pm/shots-zukan-facts/
  - 空港ページの押した回数の下に「供用開始 ○年」「滑走路 ○本」のカード・滑走路ごとの「A 3,000m×60m」・出典の1行（国交省の PDF へのリンク）
  - 値は tools/build.mjs の airportFacts が移行160から入れ（AIRPORT_FACTS）、サーバーの表があれば zkLoadFacts で上書き
  - 会社管理の4空港・番外編は欄ごと出さない／羽田・三沢・岩国は年なしで滑走路だけ（横いっぱい）／福岡の C・D（ヘリポート）は補足つきで本数に数えない／まだの空港にも出す
  - 関数：足した zkLoadFacts・zkFactsHTML・AIRPORT_FACTS／変えた openAirport
  - t121（新）すべて成功・t120 は1項目を直して成功。全体 85/89（前からの t105・t99・t48・t57）。t13・t47・t61 は作業用フォルダ（/tmp/soramemo-e2e）が汚れていると落ちる。新しいフォルダ（SORAMEMO_TEST_WORK）で流し直すと成功
  - 本人に決めてほしいこと：まだの空港にも出すか／福岡のヘリポートを数えない形／羽田の年（案A のまま）／デザイン担当の画面案（review-4 の3）が出たら合わせる
  - main には入れていない
- PR #48（タブから選ぶ・ON／OFF）に main（図鑑の入った版）を取り込み直した（cf47306）：表示の編集の数 40→38、t118 の提案の数 15→13・25/38。t118・t119・t120 成功。本人の「反映して」待ち
- 図鑑の作り直し（11/10 1時の PM の指示）：ブランチ feat/zukan-book・下書き PR #60（644ff6e）、報告 docs/pm/report-zukan-book-app.md、写真 docs/pm/shots-zukan-book/
  - 見方は地方別（region・いつも）・地図・行った順（chron）。ツメ・1行の扉（上に止まる）・枠104・ターミナル6空港14こ（「新千歳 国内」）・0の人・行った順は月の見出しと「計」
  - 空港ページ（今の dAirport に足した）：コード・回数・はじめて押した日・記録3回＋すべて見る・ターミナル・前／次・はらう。まだの空港は「ここでチェックインすると印が付きます」。開港・滑走路は airport_facts 待ち
  - 索引（探す欄・ABC・50音）。読みは PR #57 を取り込み、tools/build.mjs が移行の読みをアプリに入れる（表があれば上書き）
  - ほかの図鑑・実績（4冊）・記号の意味・はじめの案内の文（大きな6空港はターミナルにも印）も済み
  - 見方の保存は読むときに直す（zkFixLayout・viewOf・vpApply）、VP_FMT=3。off.book の空の配列は消さない（消すと構成のはじめの値に戻る）
  - review-3 の指摘1〜8 は作る側で入れた
  - t120（49項目）成功・直したテスト12本。全体 80/88（t34・t37 は流し直して成功、残りは前からの t105・t99・t48・t57・t60・t62）
  - 本人に決めてほしいこと：空港ページを今の画面に足す形でよいか／読みを組み立てで入れる形でよいか
  - 2回目（11/10 PM の再指示）：画面案 4版（31959a1）に合わせた（7c2ba2e）。ターミナルは「羽田 第1」・止まった扉に「図鑑の上へ」・いちばん近い › は地方へ飛んで枠を光らせる・まだの空港に「いまの場所から ○km」・行った順は ✓ なし・ほかの図鑑に「もどる」のカード。ターミナルの数え方の文は本番どおり（ターミナルで押した回も空港の回数に入る）に直した。03 の「小さな地図と最後に押した」の行は後回し
  - t120 は56項目成功。全体 80/88（t31 は流し直して成功、t19・t61 は reload の揺れ、残りは前からの t105・t99・t48・t57・t60）
  - 本人に決めてほしいこと（足した分）：まだの空港に「いまの場所から ○km」を出すか／ターミナルの数え方の文
  - 3回目（11/10 6時35分の PM の指示・review-app-1）：292997d。844 で沖縄の扉も上に止まる（.zk-rg:last-of-type の min-height）・コードのない空港は大きい字に「神津島」などの名前＋2行目「コードなし」・前／次でコードを2回出さない・空港名は「（」の前で折る・ターミナルの印は「羽田 第1」「まだ」「年月日」・まだの空港は「閉じる」だけ・「すべて見る（28回）」と点なし・ほかの図鑑の下の行は「ターミナル 3/14」。写真 03-844-okinawa・03-844-kanto・04-844-hnd・04c-844-nrt。関数：zkTile・openAirport・renderZkOthers
  - 3回目で残したもの：8 見方の帯が下線のタブ（共通の部品 setViewsw なので PM の判断）・5 夜（土台待ち）・印の絵の中の日付 2025/12/14（共有の画像と共通なので変えていない。本人に聞く）
  - t120 は62項目成功。全体 83/88（t120 の1項目と t61 は流し直して成功。残りは前からの t105・t99・t48・t57 と reload の t62）
  - main には入れていない
- review-c4 の小さい所（11/9 5時40分の PM の指示・本人が ON／OFF に決めたあと）：同じブランチ feat/all-in-tabs・PR #48 に足した（029d4c6）、報告 docs/pm/report-all-in-tabs-c4.md、写真 docs/pm/shots-all-in-tabs/15・16・18・21 を撮り直し 22（夜の入れ替えの帯）を足した
  - 1 667 で元に戻すの帯が最後の行を隠す：帯は一覧と重ならない作り（一覧が縮む）なので余白では直らない。帯が出て最後の行が見えなくなったら、押した行が隠れない範囲で一覧を送って最後の行も見せる（tpKeep）
  - 2 全部乗せのときは押せない薄い「全部乗せに戻す」をやめ、理由の字「いまは全部乗せです」（#6B7280）。外れたときは紺のボタン
  - 3 夜（data-night="on"）は入れ替えの帯を地 #141B24・縁 2px rgba(220,227,234,.72)・ピルも縁だけ（07c の値）。昼は薄い黄色のまま
  - 「−／＋」の名残の CSS（.tpminus・.hex・.heon・.tpadd・.tpsec・.tpfoot・.hesec・.hetray・.tprow.away）と変数 tray を片づけた
  - 関数：変えた tpHTML・tpKeep・heHTML
  - t119 に3項目を足してすべて成功・t118 成功。全体 84/88（前からの t105・t99・t48・t57。揺れた t31・t62 は流し直して成功。t60 は今回は通った）
  - 本人に決めてほしいこと：全部乗せのときに「いまは全部乗せです」と字で出す形でよいか
  - main には入れていない
  - 組み立て（tools/build.mjs）には python の brotli が要る（この環境では pip で入れた）
- review-c3 の直し（11/9 3時35分の PM の指示）：同じブランチ feat/all-in-tabs・PR #48 に足した（0999d3c・8ec8a86）、報告 docs/pm/report-all-in-tabs-c3.md、写真 docs/pm/shots-all-in-tabs/15〜21
  - 1 タブを選ぶ：題・数「4/5・5つまで」・完了・説明文1行「OFF で隠れます。≡ で並べ替え。」を上に固定し、送るのは一覧（.tpscroll）だけ。元に戻すのトーストと入れ替えの質問は下（.tpbot）に固定。トーストで送らず、押した行が陰に入ったときだけ一覧を送る（tpKeep）
  - 2 OFF の縁とつまみの縁：次の回（PM の再指示）でデザイン担当の 4版（PR #49・5937ded の tokens.md）に合わせた（2e57613）。昼は地 #E5E8EE・縁 #768090（白と 3.99:1）、夜は縁 #66778C・字 #AEB9C6。写真 15〜21 を撮り直した
  - 3 OFF の補足は「マイページから開けます」の1行。行の高さは全部 62px
  - 4 5/5 のとき OFF の補足は「ON にすると外すタブを選びます」（2行に折れるが高さは同じ）。写真 21（入れ替え・667）
  - 5 ホームに出すもの：トーストは見本のすぐ下（下に貼りつけない）。667 でいちばん下の行を OFF にしたら見える所まで送る（heKeep）
  - 6 半券を薄い地（.hepc.fix）・≡ を3本線・写真 17 と 20 を同じ状態で
  - 関数：足した tpKeep・heKeep／変えた tpHTML・tpRender・tpSet・heHTML・heSet・クリックの処理（ON にする・入れ替え）
  - t119 に12項目を足してすべて成功・t118 成功。全体 82/88（前からの t105・t99・t48・t57・t60、揺れた t27 は流し直して成功）
  - 本人に決めてほしいこと：「−」か ON／OFF か／題の横の数の形／5/5 の補足が2行に折れる（短くするか）
  - main には入れていない（本人が写真を見て決めるまで）
- ON／OFF を試す（11/9 1時20分の PM の指示・本人「ON OFFにしてみて」）：同じブランチ feat/all-in-tabs・PR #48 に足した（3281874）、報告 docs/pm/report-all-in-tabs-c1.md の「追加（11/9 1時20分）」、写真 docs/pm/shots-all-in-tabs/15〜20
  - タブを選ぶ・ホームに出すものの各行を ON／OFF のスイッチに（字の札・role=switch・72×44px・色だけに頼らない）。OFF の行はその場に残す（「タブにないもの」「外したもの」の列はなくした）。ON にするとその行の場所でタブに戻る。≡ は OFF の行も動かせ、タブの順は ON の行だけ
  - ホームの半券・今日の数字は「いつも」。2つのときは ON を押せない＋「2つより減らせません」。はらって隠すのは ON の行だけ残した。トーストはそのまま（667 では見える所まで送る）
  - 文は「OFF にすると隠れます」（タブを選ぶ・ホーム・マイページのタイル）
  - 夜の色：アプリに夜の画面がまだないので、色を変数（--sw-*）にし :root[data-night="on"] で design/night 2版の tokens に替わる形だけ用意
  - 関数：足した tpOrder・loSw・tpReorder／変えた tpHTML・heHTML・tpSet・openTabPicker・クリックの処理（ON・入れ替え）・矢印のキーと ≡・はらう処理
  - t119 を直してすべて成功・t118 成功。全体 79/88（前からの t105・t99・t48・t57・t60。揺れた t13・t31・t47・t62 は流し直して成功）
  - 本人に決めてほしいこと：「−／＋ 出す」と ON／OFF のどちらか（写真 15〜19 と 09〜12）／OFF の行をその場に残す形でよいか／667 で OFF にすると「完了」が上に隠れる
  - 11/9 の PM の再指示で、スイッチの色の変数と大きさをデザイン担当の画面案（design/night の 07-tabs-v3-onoff・PR #49）に合わせた（811a2ef）。写真 15〜20 を撮り直し、t119・t118 成功。デザイン案は OFF のタブを一覧の下に置くが、アプリは PM の指示どおりその場に残す（本人が置き場所を決めたら合わせる）
  - 試しの形。本人が写真を見て決めるまで main には入れない
- 全部乗せ 案3の仕上げ（11/9 0時40分の PM の指示・改善担当の review-c2）：同じブランチ feat/all-in-tabs・PR #48 に足した（a245503）、報告 docs/pm/report-all-in-tabs-c1.md の「追加（11/9 0時40分）」
  - 1 マイページのタイルの「× で外し、＋ で戻す」を「「−」で外し、「＋」で戻す」に。t119 に「画面の文に『× で外し』がない」
  - 2 写真 01〜04・06・07・08・11・12・13 を撮り直した。667 で元に戻すのトーストが「タブにないもの」の行に重なっていたので、トーストを並べる行のすぐ下に出す形にした（下に貼りつけるのをやめた）。t119 に重ならないことを足した
  - 3 吹き出しはログインしていない人には出さない（ログイン・登録｜デモで試すを隠さない）。ログインしたあとの reload から出る
  - 4 全部乗せに戻すの表の左の欄が折れない・「そのまま」→「外しているものなし」（順番の行は「元の順のまま」）・トーストは「タブ4つ・かたまり1つ」の形
  - 関数：足した loOffText／変えた tpHTML・tpTipMaybe・rsHTML・クリックの処理（全部乗せに戻す・ホームを全部出す・1版の全部乗せに戻す）
  - 本人に決めてほしいこと：吹き出しをログインしたあとに出す形でよいか（前からの3つ：吹き出しを見たことは端末だけ／今日の数字は「いつも」／ホームのページから全部乗せに戻すを外した）
  - t119 すべて成功。t118 を新しい文に合わせて直した（4e12bcb）。全体 80/88（前からの t105・t99・t48・t57、揺れる t34・t62、t60 は変える前の版でも落ちる）
  - 11/9 の PM の再指示（同じ仕事）で review-c2.md を読み直し、4つと古い写真がすべて済んでいるのを確かめた。残っていたテストの説明の「×」も「−」にした（532e2f4）
  - 本人の「反映して」待ち。main には入れていない
- 全部乗せ 案3に改善担当の review-c1 の5つを入れた（11/8 夜の定時の回・PM の指示なし、帳面の「次にやること」から）：同じブランチ feat/all-in-tabs・PR #48 に足した（bd18ebc）、報告 docs/pm/report-all-in-tabs-c1.md、写真 docs/pm/shots-all-in-tabs/09〜12
  - 1 長押しの吹き出し（はじめてタブ帯が見えたとき1回・触ると消える・押せる物をさえぎらない・デモ中は出さない・端末の soramemo.tpTaught）。タブ帯の字は選ばれない
  - 2 外した直後のトーストに行き先「マイページから開けます」（開いていた画面ならホームへ移ったことも）。タブにないものの行に「・マイページから」
  - 3 外すのは見える丸い「−」（C1・C2 とも。2つのときは出さない）、戻すのは白いピル「＋ 出す」。はらうのはおまけで残した
  - 4 ホームの見本は灰色の枠と「見本」の札・左上は「‹ 戻る」
  - 5 ホームに出すものの「全部乗せに戻す」をやめ「ホームを全部出す」（ホームだけ・元に戻す）。C3 に「タブの順番」の行
  - 関数：足した tpOffText・tpTaught・tpTipDone・tpTipMaybe／変えた tpHTML・heHTML・rsHTML・reload（最後に吹き出し）・長押しの処理
  - t119 は59項目すべて成功。全体 81/88（前からの t105・t48・t57、揺れる t19・t34・t62。t62 は file:// の開き直しの問題で4回に1回）
  - 11/8 22時45分の PM の指示（review-c1 の5つ）に合わせ直した（bba5ae5）：トーストを「マイページの『運用』のタイルから開けます」と場所まで言う形に。全部乗せに戻したあとの元に戻すを t119 で確かめた（64項目すべて成功）。外すボタンは PM の文の「×」ではなく review-c1 のとおり「−」にした（× は本番で「閉じる」のため）。× がよければ直す
  - 本人に決めてほしいこと：吹き出しを見たことは端末だけ（別の端末でもう1回出る）でよいか／今日の数字は「いつも」のまま／ホームのページから全部乗せに戻すを外した
- 全部乗せを案3「タブから選ぶ」に作り直す（11/8 夜の定時の回・PM の 11/8 21時半の仕事）：ブランチ feat/all-in-tabs、下書き PR #48、報告 docs/pm/report-all-in-tabs.md、写真 docs/pm/shots-all-in-tabs/
  - C1 タブ帯の長押し（約0.55秒・スタンプラリーのときだけ）で「タブを選ぶ」（dTabs）。≡ で並べ替え（矢印のキーでも）・左へはらって外す（元に戻すつき）・5つあるとき6つ目は入れ替えを聞く・2つより減らせない。マイページからも開く
  - C2 ホームに出すもの（dHomeEd）：× で外し ＋ で戻す。半券と今日の数字は「いつも」。入口はホームのシートの下の1行・タブを選ぶ・マイページ
  - C3 全部乗せに戻す（dReset）：戻したあとのタブ帯と、タブ・見方・かたまりの戻るものを見せる
  - C4 提案は2本のタブ帯（hsHTML を作り直した。1つずつ残すピルはなくした）。長押しを教えた印 soramemo.tpTaught
  - マイページはタイル3枚（タブを選ぶ・ホームに出すもの・全部を見直す＝1版の1枚の画面）。見方は今までどおり各画面の鉛筆から
  - t119（41項目）を足し、t118 を直した。全体 81/88（前からの t105・t48・t57、揺れる t17・t19・t34）
  - 本人に決めてほしいこと：1版の1枚の画面を「全部を見直す」で残すか／今日の数字を外せるようにするか／長押し中の金の縁はシートの中の見本にした／画面ごとの「○○に出すもの」は作っていない
- 全部乗せ＋フィルター（11/8 夜の定時の回・PM の 11/8 16時15分の仕事、本人の「おけ」のあと）：ブランチ feat/all-in-filter、下書き PR #39、報告 docs/pm/report-all-in-filter-app.md、写真 docs/pm/shots-all-in-filter/
  - はじめての端末は全部乗せ（PERSONAS に all。タブ：ホーム・図鑑・フライト・運用・修行）。端末に使った跡（soramemo.usage・soramemo.onboarded・soramemo.layout）があれば前からの人として今の見え方（気軽に）のまま
  - 表示の編集を1枚のピルの画面に（しぼりこみ「すべて／隠しているもの」・元に戻す・全部乗せに戻すは戻る数を見せる）。ひな形の選ぶ所と並べ替えはなくした。マイページの「構成」は「表示の編集」のタイル＋タブにない画面を開くボタン
  - 保存は user_view_prefs（データの PR #37）。fmt 2：全部乗せ＝{}、ほか＝{base, layout}。upsert は使わず update／insert。表がないときは端末だけ・全部乗せの人は古い答えで変えない。行がない人は前の答えのまま上げる
  - 新規登録の答えで構成は変えない。view_prefs_claim_suggest が true のときだけ「隠しておきたいものはありますか？」（気軽からは「これから乗る便」を外した）。断った人・あとで決める人には「全部の機能を出しています」の1枚
  - t118（44項目）を足し、t62（setPersona で構成を変える形）・t71・t114 を直した。全体 79/87（前からの4本と揺れる4本。t62 は PR #20 と重ねて 3/3）
  - 本人の「反映して」待ち（PR #37 と一緒に）。決めてほしいこと：「これから乗る便」を外したこと／前からの人の見分け方／ようこそと1枚が2枚並ぶこと
  - 2回目（11/8 PM の指示 17時5分・本人「作ってみて」）：data/view-prefs を取り込んだ（t97 OK）。全部乗せの人だけ、空のかたまり（これまでの記録・最近の印・イベントのお知らせ）を「まだ中身のないもの N」に畳む（homeFold。印が入ると外に出る）。マイページはタブにない画面をタイル（.mptile、成績はいつも）。はじめの1枚は今日の数字の下へ。t118 は49項目、t62・t71 はタイルに合わせて直した。全体 78/87（前からの4本と揺れる4本）
- ホームのメールのログイン欄を消す（11/6 夜・PM の指示）：ブランチ fix/remove-home-login、下書き PR #23、報告 docs/pm/report-remove-home-login.md、写真 docs/pm/shots-remove-home-login/
  - ログインの入口は右上の「ログイン」とシートの「ログイン・登録」（どちらもログインの画面 dAuth）だけ。欄だけに使っていた処理（sendLink・verifyCode・欄用のロボット除け）と .login の見た目も消した。LOGIN_GUARD と captchaOn は残す
  - t7・t43・t44・t114 をログインの画面から入る形に直した。t114 の新規登録の流れは変わらない。全体 78/86（前からの4本と、#20 で直る揺れ4本）。#20 と重ねると 9/9
  - 本人の「反映して」待ち。#20 と #23 はどちらも t44 を変えているが、変えた所が別なのでぶつからない
- 新しいホーム（改善案の3版目）：ブランチ feat/home-v3、下書き PR #16、報告 docs/pm/report-home-v3.md、写真 docs/pm/shots-home-v3/。11/6 18時ごろ（日本時間）main に入った（PR #16 がマージされた）
  - 上を1段・航空図風の地図（地理院の地図に色を重ねる）・状態の出し分け（ログインしていない＞範囲の外＞中）・半券は右へ引くだけ（押すと確かめ）・シートは2段
  - ログインしていないとき、右上は「ログイン」（押すとログインの画面）。「エアライン経営」もログインの画面。マイページを直接開く関数は openMyPage()（テストのデモの始め方もこれに変えた）
  - 改善担当の指摘（docs/pm/review-home-v3.md）のうち、1（送ってから下げるとシートが消える）・2（図鑑のピルの色）・4（最近の印の並び）・8（字の選択）を直した（2a39baa）
  - 11/6 定時の回：指摘9（タブ帯の上の線。CSS の圧縮で前の線の指定が残っていた）を直し、t116 に「図鑑へ行って戻っても最初の位置」「線がない」を足した（5a73de6）。写真 06〜08（-375 も）を足した。改善担当の「直してから見せる3つ」はすべて済み。改善担当が指で確かめ直したら本人に見せてよい
  - PM の指示「新しいホームを1回直す」（必ず3つ・小8・9・4つの状態の撮り直し）はすべて済み。写真 01〜05 を撮り直し、報告に指示との対応表を足した
  - 本人に決めてほしいこと：右上「ログイン」の行き先でよいか／引き上げたときに前の「空港・路線・飛行距離」のカードが残ってよいか（メールのログイン欄は 11/6 に「消す」と決まった → PR #23）
- 揺れるテストを直す（11/6 夜の定時の回・PM の指示なし、帳面の「次にやること」から）：ブランチ checkin/test-waits、下書き PR #20、報告 docs/pm/report-test-waits.md。テストだけの変更
  - 元：file:// のページを読み込み直すと、Chromium が直前に書いた localStorage をときどき落とす（空の html でも。http では起きない）
  - tests/e2e/keepls.py の goto_http で、reload する16本を手元の http（127.0.0.1）から開く形にした。sw.js は返さない。t117 を足した
  - 全体 83/87（落ちたのは前からの t99・t105・t48・t57 だけ）。揺れる7本はすべて通った
  - これから reload するテストを書くときは goto_http と reload_keep を使う
- 送れないときの言い方（広告担当の依頼 2）：ブランチ checkin/send-busy、下書き PR #15。本人の「反映して」待ち（ログインのときの言い方を確かめてもらう）
- 新規登録（feat/signup）は 11/5 17:45、フォントの取得は 11/5 21:22 に反映済み（下の記録）

## 本人の決定（11/6）
- ログインしていないときのホームのメールのログイン欄は消す。ログインは右上の「ログイン」と、シートの「ログイン・登録」から開くログインの画面だけ
- 選べるカード（rethink-1106 の D）：カードは13枚にまとめる・並べ方はサーバーに保存・作るのは1月のストア公開のあと
- 作る順はホーム → 運用 → マイページ。暗い表示は1月のストア公開のあと。上の切り替えの名前は「スタンプラリー／エアライン経営」のまま

## 本人の決定（11/5）
- 表示名は空で始める／今いる利用者には次に開いたとき一度だけ同意／「デモで試す」は残す
- 未登録のメールでログインしたら新規登録へ案内／同意しないでやめた人のアカウントは残す
- 確認コードは6けた。メールは Gmail、Supabase の送信上限は1時間100通

## 次にやること
- PR #161（見回りの直し）：PM の自動の反映を待つ。入る前に t159・t142・t148・t155 と tests/ops を流す。本人の答え（3D の寄せ方・遅れの数の意味・前の数を覚えるか）で直す。撮る人の PR #162 が先に入ったら main を取り込み web/ を組み立て直す
- PR #157 は main に入った（#158）。反映の Actions が成功したかを次の回で見る
- tests/ops は手元の node_modules の playwright だと動かない（ブラウザの版違い）。tests/ops/node_modules を作らず、全体に入っている playwright へのリンクで流す
- 出典（PR #150）は本番に出た。運用予想・撮る人用が ADSB_A に替えたら t154 の OTHERS から外す
- テストの t48 には pdf417gen・segno（pip）も要る
- テストの t48 には zxing（@zxing/library@0.21.3）が要る。手元では作業用フォルダに npm で入れて ZXING_UMD で場所を渡す
- PR #141（小さい直し）：#138・#139 を含むので、PM は #141 だけ入れても3つ入る。#138・#139 が先に入ったら #141 に main を取り込み web/ を作り直す。入る前に t151・t149・t150 を流す
- tools/build.mjs はフォントの作り直しに brotli が要る（pip install brotli --break-system-packages）
- PR #138（図鑑の絞り込み）・#139（フライトの実際の時刻）：改善担当の見直し・PM の自動の反映を待つ。#139 はデータ担当の #136（移行187）と一緒に入れる（先に入っても前の列で読み直すので壊れない）。入る前に #138 は t149・t127、#139 は t150 と t123・t47・t61 を流す。#138 と #139 は src/index.html の別の所（図鑑とフライト）。web/ はあとから入る方で作り直す
- 本番の反映（PR #130・#137）の Actions が成功したかは、この回も確かめていない。次の回で見る
- PR #134（運用の一覧）：本人の答え 1〜6 は 11/20 に済み（5・6 は 21180c2 で入れた）。改善担当の見直しを待って直す。昼の回に本番の羽田のデータ（読むだけ）で凡例の2行を撮り直す。入る前に t148・tests/ops・運用の e2e を流す。PR #125（アプリ）の電波がないカード（I5）は、#134 が入ったらカードの形で足す。#125 と #134 は src/index.html の別の所（NATIVE の部分と運用の土台）で、openOps・setOpsAirport の行だけ両方が触る（あとから入る方で合わせる）
- 夜の画面が入ったら、運用の一覧のカードの夜の色を design/ops-hub の H1n に合わせる
- PR #125 と #130（ピン止め）が両方 main に入るとき：K0i・K5n の「iPhone はホーム画面に追加すると届きます」をアプリでは PUSH_NG_TXT() に。#133 と #125 は src で重ならない見込み（半券の処理と NATIVE の部分は別の所）
- PR #133 は main に入った（11/20）。本人の iPhone で半券を指で引いた結果が来たら main から新しいブランチで直す
- PR #125：Mac で「設定を開く」・位置の確認・オフラインの帯を試した結果が来たら直す。入る前に t143・t146・tests/ops を流す
- PR #130（ピン止め）：改善担当の見直し・本人の答えを待って直す。残り：K9 の1回の案内（いまは黙って移す）・K5 の並べ替え・夜の画面で撮る・K10（重なる知らせを1回に）はデータ担当。反映は本人の「反映して」待ち。入る前に t140・t116・t118・t119・t124・t127 を流す。PR #129 と同じ main から作ったので、先に入った方に合わせて web/ を作り直す（src は重ならない見込み）
- テストを流すと docs/pm/shots-* の写真が書き換わる。コミットの前に git checkout -- docs/pm/ で戻す
- PR #129：11/19 12時55分（日本時間）に main に入った。反映の Actions が成功して本番に出たかを次の回で確かめる。#128 は同じ中身なので閉じてよい。以下は入ったあとも残る分→ 改善担当の見直し・本人の答え（8秒・言い方）・iPhone で引いた結果を待って直す。data/atd-future が main に入っても重ならない。データ担当が first_of_day を返したら本物の形で確かめる。反映は本人の「反映して」待ち。入る前に t144・t74・t57・t7 を流す
- 次の回は PM の指示を待つ。なければ t72 を直す（運用タブの機体の側に合わせる）。本人が Mac で動かした結果（ビルドが通るか・位置の許可・シートの下の余白）が来たら直す
- PR #125（iPhone のアプリの土台）：11/20 2時29分（日本時間）に main に入った（863fb3df）。本人が Mac で動かすときは main のままでよい（git pull → ios-app で npm ci・npm run sync・npm run open）。反映の Actions が web に出たかは次の回で確かめる
- PR #125：11/19 に main（PR #131 まで）とぶつかったので取り込んだ（894e182。web/ は作り直し、shots-view-settings/03 の写真は main の版。t140〜t144・tests/ops 成功）
- PR #125（iPhone のアプリの土台）：アプリだけの画面はデザイン担当の画面案のあと（data-native で切り替え）。APNs はデータ担当の表と関数のあと。次の段は地図・supabase-js・three.js をアプリの中に入れる・バーコードをネイティブに。反映（main）は本人の「反映して」待ち。入る前に t143 と tests/ops を流す。src/index.html は SERVER の定義のすぐ下に入れ物があるので、ほかの PR とぶつかったらそこを見る
- t72（特別塗装機の画面を #opsSpecial から開く）が main でも落ちる件は、この回もまだ（PR #125 を先にした）
- PR #121・#122・#123・#124 の改善担当の見直し・CI・本人の答えを待って直す
- PR #123（空港の3D）：改善担当の見直し・本人の答えを待って直す。データ担当の形のファイル（OSM・PLATEAU）が来たら a3Build の島と建物を差し替え、角の出典を「© OpenStreetMap・PLATEAU」に。?view=3d が来たら a3Poll の読み先を変えて地上の機体を出す（名札は空だけのまま）。反映は本人の「反映して」待ち。入る前に t142・t121・tests/ops を流す。three.js の版を上げるときは CSP（script-src に jsdelivr）と t142 の three の置き場所を確かめる
- PR #122（図鑑の飛行場）：シークレットの直しを足した。改善担当の見直しが来たら直す。#121 と夜の CSS の行がぶつかるのは両方残す
- PR #121（近くの直し）：改善担当の見直し・CI が来たら直す。反映は本人の「反映して」待ち。入る前に t140・t127・t119・t116 を流す
- tests/sql を setsid で流しても途中で止まることがある（11/17 は t92 の途中で止まった）。残りは1本ずつ流す
- PR #117（いつもより遅い）：11/17 15時18分（日本時間）に main に入った（PR #119・61ba9c7、#118 の移行185 も一緒）。反映の Actions が成功して本番に出たかを次の回で確かめる
- PR #117（いつもより遅い）：PR #118 は取り込み済み（#118 が先に main に入ったら main を取り込み直す。同じ移行185なのでぶつからない）。#118 に直しが来たら取り込み直し、ulNorm と t139 の偽の返り値をそろえる。airport-foreign に usual が足されたら案内板の札を本物の形で確かめる。改善担当の見直しが来たら直す。反映は本人の「反映して」とデータ担当の関数と一緒。入る前に t139・t59・t60・t133・tests/ops を流す。夜の画面が入ったら点線の琥珀を撮る
- t72（特別塗装機の画面を #opsSpecial から開く）が main でも落ちる。運用タブを空港と機体に分けた形（機体の側）に合わせてテストを直す（次の回、PM の指示がなければ）
- e2e を流すときは setsid で切り離す（2分で切れるコマンドに付けると run_all ごと止まる）。tests/ops は node_modules/playwright を全体の playwright へのリンクにして流す
- PR #114（運用タブのテスト）：11/17 1時11分（日本時間）に main に入った（PR #116 の反映のやり直し。経営 t111 の1円ずれの直しも一緒）。反映（Actions 217）は成功（11/17 1時40分）→ #112・#113 の運用タブの空港と機体は本番に出た。★を戻すかは本人の答え待ち
- PR #112（運用タブの空港と機体）：本人の答え3つと改善担当の見直しを待つ。反映は本人の「反映して」待ち。入る前に t138・t118・t124・t130・t134 を流す。PR #107 が入った main とは重ならない（取り込み済み）。運用予想が specialHTML に A4 のピルを足したら、機体の側で見え方を撮り直す
- PR #107 と #96 が本番に出たか（Actions）は、この回も確かめていない。次の回で見る
- PR #107（見落としの片付け）：データ担当の data/redo-1116 で odpt_feed_at の返す形が決まったら合わせる（今の作りは { status_at, timetable_at }）。flight_alerts() に std・svc_date が足されたら fwMerge はそれでまとめる（作りは済み）。反映は本人の「反映して」待ち。入る前に t135・t136・t130・t115・t7 を流す
- t123（共有の画像のダイアログが押す所を覆う）は main でも落ちる。次の回で原因を見る
- PR #96（海外の止まり具合の画面）：data/world-ops の a33a975 まで取り込み済み。#93 にまた変更が来たら取り込み直す。反映は #93 と一緒（本人の「反映して」待ち）。入る前に t133・t130・t60 を流す。夜の画面の案が出たら札の色を合わせる。改善担当の見直しが来たら直す
- PR #90 が本番に出たか（Actions）はまだ確かめていない。次の回で見る
- PR #90（通知の renotify）：11/14 に main に入った。本番の配る版が Actions で出たか次の回で確かめる。（前の書き付け）data/alert-merge と一緒に本人の「反映して」を待つ。先にこちらだけ入っても動きは今までと同じ。通知の説明の文を画面に出すかは、デザイン担当の画面案と本人の答えが出てから
- 手元で build するときは tools で npm ci、python に brotli と fonttools が要る（11/13 の回で入れた）
- PR #84（全体の見回りの直し）：main に入った（PR #87・4fb2f42）。本番の配る版が Actions で出たか、次の回で確かめる。改善担当の見直しが来たら main から新しいブランチで直す。（前の書き付け）本人の「反映して」と改善担当の見直しを待つ。運用予想の PR #83 と一緒に入れるときは、あとから入る方で web/ を作り直す（node tools/build.mjs）。入る前に t128・t60・t127・t126 を流す。見回りの残りで運用予想の持ち場（#5・#6・#8・#10・運用の通信の数）は運用予想の担当、夜の CSS（#12）は夜の画面の土台のとき。maplibre の読み込みをさらに遅らせる・980KB の script を分けるのは次の候補（PM の判断待ち）
- PR #75：改善担当は review-app-2 で「反映してよい」、図鑑の題も入れた（7a901bd）。本人の「反映して」が出たら、データ担当の移行163（heliports）と一緒に。入る前に t127・t119・t116 を流す。review-app-2 の反映のあとでよい4つ（844 で一覧が短いとシートの下が空く・表示の編集の補足「隠している」が切れる・東京ヘリポートの名札が点線にかかる・関東の扉に「大利根」が2つ）は、反映のあと main から直す
- PR #75：改善担当の見直し（加須の 844／740 と東京駅の 844 の引き上げた位置）を待つ。指摘5（夜の札の濃さ）は夜の画面の土台のあと。t17 がまた落ちたら成績の称号を押す所を調べる
- PR #75（feat/near-airfields）：改善担当の見直しと本人の答え（ヘリポートの印・図鑑）を待つ。「反映して」が出たら、データ担当の移行163（heliports）と一緒に。入る前に t127・t119・t116 を流す。印を押せないに決まったらデータ担当へ（checkin 関数の読み出しで heli を外す）。図鑑を別にするなら ZKX_KINDS から heli を外す
- 夜の画面が main に入ったら、近くの一覧・すべて・飛行場の図鑑を夜で撮り直す（今の 13 は data-night だけの参考）
- 地図の名前の置き方（review-5 の4・8：引き上げた位置で「いまここ」と先頭の名前が重なる・タイルの字と二重）はまだ。改善担当の指摘を待つ
- PR #68：本人の「反映して」を待つ。入る前に t124・t126・t118・t122 を流す。本人の答え（ホームの数 4/4・タブの補足の文・タイルの名前）が出たら合わせる
- PR #68（見方の設定）は main に入った。本番の反映を Actions で確かめる。本人の3つの答え（ホームの数え方・成績の行・タイルの名前）と改善担当の指摘が来たら、main から新しいブランチで直す。修行担当の修行のシートができたら1枚に修行のカードが出るか確かめる
- 夜の画面が main に入ったら、鉛筆のシートと1枚（スイッチ・光る縁）を夜で撮る
- PR #65：review-app-1 の4〜8 は PM の指示を待つ（共有を1つにするのは本人の答え「年のまとめの共有をみんなに出すか」と一緒）。本人の「反映して」が出たら main に入る前に t123 と修行の t125 を確かめる
- PR #65（フライト）：改善担当の指摘と本人の答えを待って直す。データ担当の flights の「車など」の列ができたら f.mode を読み、端末の印をサーバーへ移す。見方の帯をピル型にするかは PM の判断待ち（図鑑と同じ共通の部品）
- 667 の日誌は、デモの帯があると最初の便が1つほど。改善担当の見方しだいで年のカードを詰める
- 古い CSS（#v-log .lseg・.lgboard ほか）が残っている。反映のあとで片づける
- 改善担当が review-facts-1 と review-c5 の直しを見たら、その指摘を入れる。PR #63 と #48 は本人の「反映して」待ち（どちらかが先に main に入ったら、もう片方に main を取り込み直す。#48 の表示の編集の数 38 と t118 も見る）
- 「全部を見直す」の1枚をどうするか、本人と PM の答えが出たら PR #48 に足す
- PR #63（図鑑のデータ欄）：本人の答えとデザイン担当の画面案（04 にデータ欄と出典の版）を待つ。出たら見た目を合わせる
- PR #48：11/11 に main に入った（済み）
- テストを流すときは SORAMEMO_TEST_WORK を新しいフォルダにする（古い /tmp/soramemo-e2e で t13・t47・t61 が落ちた）
- PR #60（図鑑）：review-app-1 の小さい直しを入れた（292997d）。改善担当が 844 の沖縄・関東の枠・羽田と成田の空港ページの写真を見直したら本人に見せる。8（見方の帯をピルにするか）は PM の判断を待つ。03 の「小さな地図と最後に押した」の行は要るなら足す。反映は PR #57（airport_yomi・移行 159）と一緒。PR #48 と先に入った方に合わせて表示の編集の数（38）と t118 をそろえる。airport_facts ができたら空港ページに「供用開始」「滑走路」と出典を足す
- PR #48：review-c4 の3つと「−」の CSS の片づけは済んだ（029d4c6）。本人の「反映して」を待つ。古い「−／＋」の写真（09〜12）は記録として残している。夜の画面ができたら data-night でスイッチと入れ替えの帯の色を確かめる
- t60 は 11/9 昼の全体の流しでは通った。また落ちたら日付か ODPT の偽の便の古さを調べる
- PR #48 の続き：review-c1 の5つ（11/8 夜）と review-c2 の4つ（11/9 0時40分の PM の指示）は入れた。改善担当が見直した指摘を待つ。次は、フライトの見方を3つ＋「ほか」（01c）・記録が0のときは見方の列を出さない（改善担当の指摘B）
- t60（乗る便のカードの「記録する」が出ない）が 11/9 の全体の流しで落ちた。変える前の版（bba5ae5）でも落ちるので、日付か ODPT の偽の便の古さを疑う。次の回で調べる
- 全部乗せの残り（PR #39 の続き）：フライトの見方を3つ＋「ほか」（01c）・記録が0のときは見方の列を出さない（改善担当の指摘B）。デザイン担当の画面案2版が出たら見比べて直す（畳む・タイル・667 は 11/8 2回目で済み）
- そのあとは運用（feat/ops-v3）→ マイページ（feat/mypage-v3）。11/7 のデバッグの4つ（日をまたぐ時刻・t57・t48・天気が取れないとき）もこの合間に
- PM から積んだ仕事（下の「11/6 19時半」）：ログイン欄を消すのは PR #23 で済んだ。次は運用（feat/ops-v3）→ マイページ（feat/mypage-v3）の順
- 選べるカード（13枚・並べ方はサーバーに保存）は1月のストア公開のあと。並べ方を保存する表はデータ担当への依頼になる（作る時期が来たら依頼文を書く）
- PM の指示を待つ（ホームのあとは運用、そのあとマイページ。どちらもデザイン担当の見本と改善担当の申し送りを読んでから）
- ホームの残り（改善担当の指摘）：5 地図の陸と海の色の差・空港の札と地名や点線の重なり／7 ターミナルの出方（本物の位置で確かめる）。3 上の段を画面ごとにそろえるのは運用・マイページのとき
- 次の大きな仕事は運用の画面。デザイン担当の細かい版（design/ops-detail・PR #17）が出たので、PM の指示と改善担当の指摘が来たら読んで始める
- ホームの残り：小さい画面（375×667）では最初の位置の地図が約320px（帯をタブ帯にもぐらせないほうを先にした）。航空図風の色は見本ほど陸と海の差が出ない。本人の判断しだいで直す
- 次の反映のとき、「元のフォントをキャッシュから戻す」がキャッシュを使えたか（Cache restored）をログで見る
- PM から積んだ広告担当の依頼（下の1〜3）。2 は PR #15 で済み。1 はデータ担当の表待ち（下の依頼）、3 はデザイン担当の画面案待ち
- 揺れるテスト（t19・t31・t34・t37・t47・t61・t62）は PR #20 で直した。main に入ったら、次の全体の流しで揺れが出ないか見る
- 同じ日に同じ仕事を2つの回がしていた（2a39baa と定時の回）。始める前に、自分のブランチの最新（git fetch）と帳面を必ず見る
- 元から落ちているブラウザのテスト t48（pdf417gen がない）・t57 の原因を調べる（本人の了解が出たら）。11/6 の全体の流しでは t17・t27 は通った
- tests/ops は手元では npm の playwright にブラウザがないので、全体に入っている playwright をつないで流した（すべて成功）

## ほかの担当への依頼
- 撮る人（11/21・PR #161）：特別塗装機のカードから開いたページで details.spnow を開くようにした。欄の作りを変えるなら spnow の名前を残すか知らせてほしい
- 運用予想（11/21）：見回りの6（深夜の「風から推定」の札）は運用予想の分。データ担当：見回りの2（odpt_feed_at）と7の通信の側
- データ担当（11/21・PR #157）：#153 の依頼どおり作った。アプリは airport_tracks の返り値が配列でなく {error:'login_required'|'rate_limited', retry_after_min} のときに一文を出し、cold-tracks は 401／429（Retry-After）を見る。返す形を変えるなら data.md に書いてほしい。#157 と #153 は同時に入れてほしい
- 運用予想（11/21・PR #150、PM から伝えてほしい）：adsb.lol の出典は共通の部品 `${ADSB_A}`（押せるリンク、見える字は「adsb.lol」）にそろえた。specialHTML・spbListHTML・spbDetailHTML・planeHTML・PRED_NOTE の字だけの「adsb.lol」を `${ADSB_A}` に替えてほしい（文字は増やさない。PRED_NOTE はふつうの "…" の文字列なので `…` にする）。とくに機体を選んだ画面は上の i が隠れるので、planeHTML の1行が唯一の出典。替えたら tests/e2e/t153.py の OTHERS から外す
- 撮る人用（11/21・PR #150、PM から伝えてほしい）：同じく spDetailHTML の注意と spRegWhy の「adsb.lol」を `${ADSB_A}` に（spRegWhy の返す字が title などの属性に入るなら、そこは字のままでよい）
- 経営担当（11/21・PM が決める）：会社の機体の説明（「あなたが乗った機体だけを…」の1行）の adsb.lol も字だけ。そろえるなら `${ADSB_A}` か同じ形のリンクに
- 改善担当（11/20・PR #138・#139）：図鑑の絞り込み（写真 shots-zukan-filter/）とフライトの「目安」「（推定を含む）」の札（shots-flight-actual/）の見え方を見てほしい
- データ担当（11/20・PR #139、PM から伝えてほしい）：画面は act_src が 'odpt'・'adsb'・'timetable' のどれかで、到着が出発より後のときだけ使う。track は [[緯度, 経度], ...] の2点以上
- 撮る人用・運用予想（11/19・PR #134、PM から伝えてほしい）：運用タブは一覧＋専用ページになった。中身（renderPhoto・specialHTML・planeHTML）はそのまま専用ページに出る。見方の帯（#opsViews・#opsPViews）は出ない。前の形で試すときは localStorage soramemo.ops.hub="0"
- 改善担当（11/19・PR #134）：写真 shots-ops-hub/（一覧 844／667・開く途中・各ページ・左端から引く途中）と iPhone で、動きの速さとカードの数字の分かりやすさを見てほしい
- デザイン担当（11/19・PR #134）：滑走路と地図以外の専用ページは今の中身のまま。描くなら写真とそろえてほしい
- 撮る人用（11/19・PR #125、PM から伝えてほしい）：聞く画面（atcRxStart）の getUserMedia の前に `await nvPermWhy("mic")`、失敗の文を `MIC_NG_TXT()` に。spPush・spSel の「この端末のブラウザでは使えません…」を `PUSH_NG_TXT()` に（アプリでは「アプリの通知は準備中です。」になる）
- 修行（11/19・PR #125、PM から伝えてほしい）：修行の通知の注意（sg-note の「この端末のブラウザでは使えません…」）を `PUSH_NG_TXT()` に
- 改善担当（11/19・PR #125）：写真 shots-ios-app/t146_*（I1・I1c・I1e・I4c・I2・I5・I5z、667 は I1・I1c）を見てほしい。667 の I1 は下の注意2行がスクロールの下
- 改善担当（11/19・PR #133）：見た目は変えていない。本人の iPhone で切れすぎないかの結果が来たら数字を合わせる
- データ担当（11/19・PR #130。PM から data.md へ写してほしい）：アプリは表を使わず localStorage soramemo.pins（[{k,sp,dl,ga}]、k は3レターか #番号）に持ち、今の push-subscribe に airports・sp_airports・ga・spot をピン止めから作って送っている。ピン止めをアカウントに残すなら表（利用者ごと・空港の鍵（3レターか #番号）・特別塗装機／遅れ／ゴーアラウンドの ON／OFF・並び順・上限12、前から13以上の人はそのまま）と移行・RLS。push-subscribe は今の形のままで動く（アプリがピン止めから作って送る）。sp_airports の上限14は前から13〜14の人のため残してほしい。重なる知らせを1回にする処理（K10）
- デザイン担当（11/19・PR #130）：4版どおりに作った（写真 docs/pm/shots-pin/）。K5 の並べ替え・K9 の1回の案内・夜の版はまだ
- 改善担当（11/19・PR #130）：写真 shots-pin/ と iPhone の幅で、黒いカードの札・一覧の丸・知らせのシートの高さを見てほしい
- 撮る人用（11/19・PR #130、PM から伝えてほしい）：撮影の知らせの中身は変えていない。ピン止めのシートの「撮影」を ON にすると pushSpot の iata だけを移し、「撮影地と機体を選ぶ ›」はその空港に運用を切り替えて openSpPush を開く
- データ担当（11/19・PR #128）：inbound_aircraft で前の便がないとき、その機体が前の日の夜に着いて泊まった（この日の最初の便）と分かるなら `first_of_day: true` を返してほしい（アプリは PR #128 で受ける作りにした）。あわせて遅れ・出発の通知が未来の actualDepartureTime を「出発しました」に使っていないかを data/atd-future で見てほしい
- デザイン担当（11/18・PR #125・design.md にも書いた）：アプリだけの画面（位置と通知の許可の前の説明の1枚・オフラインの画面・アプリで隠すもの＝「ホーム画面に追加」の案内など）の画面案。アプリでは html[data-native="ios"] が付く
- データ担当（11/18・PR #125）：PR #124 の依頼①〜③のまま（購読の表の種類の列・APNs に送る関数・ODPT の規約の見直し）。あわせて、本番の Supabase で CAPTCHA が ON かを data.md に書いてほしい（ON ならアプリの中のログインが通らない）
- 修行・撮る人用・運用予想（11/18・PR #125、PM から伝えてほしい）：持ち場のコードは変えていない。navigator.geolocation・navigator.share はそのまま呼べば、アプリの中ではネイティブに回る
- データ担当（11/18・PR #124、iPhone の計画が決まったら正式に依頼）：①プッシュの購読の表に種類（webpush／apns）の列（移行と RLS をセット）②APNs に送る関数（.p8 の鍵・Key ID・Team ID は秘密の値。同じ便の上書きは apns-collapse-id に今の tag）③ODPT の利用規約でアプリでの配信が許されるかを確認表で見直す
- デザイン担当（11/18・PR #124、計画が決まったら）：アプリだけの画面（位置と通知の許可を頼む前の説明の1枚・オフラインの画面・アプリでは隠すもの）の画面案
- データ担当（11/18・PR #123）：空港の3D の1回目は仮の形で作った。11/17 の依頼①〜③はそのまま。①の形のファイルは GeoJSON（滑走路・誘導路・エプロン・ターミナルの多角形と高さ、管制塔の点と高さ）なら a3Build で読める。置き場所（web/ の静的ファイルか Storage か）を data.md に書いてほしい
- 改善担当（11/18・PR #123）：写真 shots-airport-3d/（01 入口 844／667・02c 空港の今・03 全体・04 カード 844／667・05 管制塔・06 機体・08b 軽い・09 出典・夜）と iPhone の幅で、名札の重なり・シートの高さ・入口の見つけやすさを見てほしい
- データ担当へ（11/17・空港の3D のため。決定事項【11/17】・report-airport-3d-data.md のおすすめどおり）：①羽田の形のファイル（OSM の滑走路・誘導路・エプロン・ターミナル＋PLATEAU の建物の高さ、管制塔の位置と高さ 115.7m）を一度だけ切り出し、低いポリゴンの小さな GeoJSON にして置き場所と出典の文（ODbL・PLATEAU）を決めてほしい ②airport-traffic に3D 用の読み方（?iata=HND&view=3d：羽田から30km・1万フィート以下と地上、位置・高さ・向き・速さ・機種・登録記号・便名・見た時刻だけ、adsb.lol に新しく問い合わせない）③羽田に来る約30機種の大きさ（FAA Aircraft Characteristics Database、長さ・翼の幅・尾翼の高さ・形の種類）の小さな表（アプリに持つ JSON でよい）。できるまではチェックイン側は滑走路だけ・今の airport-traffic で作る
- データ担当（11/17・PR #117）：PR #118 の usual_late を取り込んで合わせた。残りの依頼は2つ：①出発前の画面（U2）のため「いつもの出発」（foreign_usual の dep_here=1）も返してほしい ②airport-foreign の planes の各行に usual・usual_n・eta・late_min（案内板・機体のくわしくの札）。（もとの依頼）usual_late(p_flight text, p_day date default null, p_reg text default null) returns jsonb（anon・authenticated に実行だけ・security definer）の形ならそのまま読める。返す形 { usual_arr:"HH:MM", usual_dep, usual_n, usual_iata, eta, late_min, event:'divert'|'return', arr_at, arr_iata, note }、分からない値は null、便ごと分からなければ null（404 でなければ foreign_late は呼ばない）。名前・形を変えるなら data.md に書いてもらえれば ulNorm で合わせる。あわせて airport-foreign の planes の各行に usual・usual_n・eta・late_min を足してほしい（案内板・機体のくわしくの札）
- 撮る人用・運用予想（11/17・PR #117、PM から伝えてほしい）：決定事項【11/17】U4 のため spDetailHTML に ulSpBox を差し込んだ（時刻表にない便の到着だけ・その便の「着陸」のカードを出さない）。ほかは変えていない
- 改善担当（11/17・PR #117）：写真 shots-usual-late/ と iPhone の幅で、シートの先頭のカード（667 で半券が下に押される）と案内板の札の切れ方を見てほしい
- データ担当（または経営担当）（11/17）：tests/sql/t111_co3_block_paid_amount.mjs の expB・expC を SQL と同じ計算（ceil(12345 * month_left_ratio()) を SQL で出す）にするか、1円の幅を許してほしい。11/17 日本時間に手元で NG（r 7891・expB 5761、B の文は 5762）。日によって反映が止まる
- 運用予想（11/16・PR #112）：特別塗装機の見方（A4）の「いま／この先／羽田に来る」のピルと各行の「この先（予想）」は specialHTML の中なので、そちらで作ってほしい（機体の側の #opsPSpecial にそのまま出る）。タブの中の機体の1日は、planeHTML の .spctop・.plsearch・.spcard・.rsec を #opsPlDay の中だけ CSS で隠し、.rtl li.edge を1行にしている。planeHTML の形を変えるときは知らせてほしい（ほかの帳面は変えない決まりなので、PM から伝えてほしい）
- 撮る人用（11/16・PR #112）：撮る人は空港の側のまま（案2）。機体の側に「撮影地から見える機体 → 撮る人へ」の入口を置いた。撮る人の中身は変えていない（PM から伝えてほしい）
- 改善担当（11/16・PR #112）：写真 shots-ops-split/（01〜09。とくに 03 の 667 で予想の1便目が下のタブ帯ぎりぎり＝行の下端 579／タブ帯 581）と、375 の幅で上の1行（長い空港名は「…」で切れる）を見てほしい

## PM から積んだ次の仕事（11/19 11時55分・本人「おすすめでOK」）→ アプリだけの画面は PR #125 に足した（5ac9b45・報告 report-ios-app-screens.md）
- ピン止め（checkin/pin）のあとに、checkin/ios-app の上で design/ios-app の2版のアプリだけの画面を作る（決定事項【11/19】）。Info.plist の位置の理由の文も2版の文にそろえる。「最後に読んだ ○時○分」は端末の中に読んだ時刻を残すだけ（表は変えない）
- 本人の iPhone で動いた（無料の Personal Team）。半券を指で右へ引く形は本人が手で試す。ミラーリングのマウスでゆっくり引いたときは切れなかった（ミラーリングのせいかは未確認）
- データ担当（11/16・PR #107）：ODPT の dc:date を読む関数 `odpt_feed_at()` を作ってほしい（移行と RLS をセット。anon・authenticated が呼べる・security definer）。返す形は jsonb `{ status_at: 運航情報のいちばん新しい dc:date, timetable_at: 時刻表の dc:date }`（どちらも null 可）。形を変えるなら data.md に書いてもらえれば合わせる。あわせて、できれば public.flight_alerts() の各行に便の定刻 std と運航日 svc_date を足してほしい（画面のカードを通知と同じく共同運航ごと1枚にするため。返す形に足すだけ）
- データ担当（11/15・PR #96）：a33a975 の返す形（label・reason_ja・feed_at・空港ごとの note）に合わせた。依頼はなし
- デザイン担当（11/15）：海外の止まり具合は W1〜W5 どおりに作った（写真 docs/pm/shots-world-ops/）。札は今の案内板に合わせて 12px。夜の案が出たら合わせる
- 改善担当（11/15）：PR #96 の写真 shots-world-ops/（t133_board・t133_board_667・t133_sheet_lax／icn・t133_ride_faa／cnt）と iPhone の幅で、札の押せる範囲と欄を見てほしい
- データ担当（11/13 夜）：data/alert-merge の依頼の renotify は PR #90 で入れた（`renotify: !!(d.tag && d.renotify)`）。反映は一緒に
- 運用予想の担当（11/13）：見回り #3（帯が送られて開く）は土台の setViewsw で直した（PR #84）。選んだ見方が帯の中に見えていれば左端から、外のときだけ送る。#5・#6・#8・#10 と運用の通信の数・重複（遅い上位 1〜9）はそちらの持ち場のまま
- 改善担当（11/13）：PR #84 の写真 shots-fix-sweep-1113/（01 図鑑のデモ 844／667・02 ホーム 667・04 フライトの地図・05 ログイン 667・07 運用の帯）と、iPhone で押せる範囲を見てほしい
- データ担当（11/13）：report-speed-1113 の 3 の 2（サービスワーカーを保存した版を先に）は PR #84 で入れた
- 改善担当（11/12 夕2回目）：PR #75（7a901bd）で図鑑の題を「飛行場・滑空場・ヘリポートの図鑑」にそろえた。扉の札は北海道で入らないので2行にした。写真 shots-near-airfields/11-airbook-844（北海道の扉）・10-zukan-entry-844・14-others-844 を、気になるときだけ見てほしい
- 改善担当（11/12 夕）：PR #75（6a3b6e7）で review-app-1 の1・2・3・6・7 を直した。写真 shots-near-airfields/02-kazo-full-844・02-kazo-full-740・05b-tokyo-full-844（と 667・06・08）を見てほしい。4 は本人の答え待ち、5 は夜の画面の土台のあと
- 改善担当（11/12）：PR（feat/near-airfields）の写真 shots-near-airfields/ の 02-kazo-full-667（一覧の下のすき間）・10-zukan-entry-844（重なる丸の「3」）・11／12（枠の名前の折れ方）と iPhone の幅で見てほしい
- データ担当（11/12）：data/heliports（移行163）は feat/near-airfields に取り込んだ。反映は一緒に。本人が「ヘリポートは押せない」と決めたら checkin 関数の読み出しで heli を外してほしい
- 修行担当（11/12・依頼の答え）：loResetAll から LO_EXT.sg.reset を呼ぶ件は、本人の答え待ちのまま（まだ呼んでいない）
- 改善担当（11/11 夜2回目）：PR #68（c837993）で review-app-1 の1〜4 を直した。写真 shots-view-settings/20・21 を見てほしい。案の外の2つ（図鑑のツメとデモの帯の「終了」の重なり・運用の見方の帯が切れる）はまだ。指示があれば直す
- 改善担当（11/11 夜）：PR #68 の写真 shots-view-settings/（とくに 10・11・14・15 の 667、02 の最後の1つ）と iPhone の幅で、畳んだカードの開け閉めと鉛筆から来たときの光る縁を見てほしい
- 修行担当（11/11 夜・shugyo.md に書いた）：見方の設定の土台（PR #68）。修行の見方のシートは loRowHTML（同じ行の部品）を使えば同じ形になる。1枚に出すなら LO_EXT.sg を足す
- 改善担当（11/11 夕）：PR #65（bb1d639）で review-app-1 の1〜3 を直した。写真 shots-flight-book/40-844・40-667（送ったところの細い帯）と 41（凡例の点線）を見てほしい
- 修行担当（11/11 夕・shugyo.md に書いた）：statusRows から車などの便が外れた（PR #65）。#65 が main に入ったら取り込んで t125 に足してほしい
- データ担当（11/11）：flights に「車などの移動」の印（例：mode text check in ('air','car')）と、本人だけが変えられる RPC（set_flight_mode）を、移行と RLS をセットで作ってほしい。アプリは f.mode === "car" を読む形にしてある
- 修行担当（11/11・shugyo.md に書いた）：フライトの見方「修行」はなくなった。sgLedgerHTML はフライトから呼ばない。t73 のフライトの所は修行のタブで書き直してほしい。車などは isCar(f)
- 改善担当（11/11）：PR #65 の写真（docs/pm/shots-flight-book/）と iPhone の幅で、667 の日誌・年のカードが止まる形・共有の1枚を見てほしい
- デザイン担当（11/11）：アプリは画面案4版どおりに作った。見方の帯は共通の下線のタブのまま。次の版を出すなら写真とそろえてほしい

## PM から積んだ次の仕事（11/19 9時50分・本人「おすすめでOK」）→ PR #130 で1回目を作った（9d21a37・報告 report-pin-app.md）
- ピン止めを design/pin の4版で作る（決定事項【11/19】）。checkin/ride-stub-fix のあとに checkin/pin で。表・知らせの送り手の変更（ピン止めの表・特別塗装機の知らせをピン止めの空港中心にする）はデータ担当への依頼にする（data.md の依頼に書く）
- 作る前に：iPhone の Safari でログインしていない人のピン止めが、ホーム画面に追加したそらメモに移るかを確かめる手順を本人向けに報告へ書く（移らなければ K0i の1行のまま）

## PM から積んだ次の仕事（11/19 9時45分・PM が本人の Mac のシミュレーターで試した結果。9時50分に調べ直した）→ PR #128 で直した（a1f0ca4・報告 report-atd-ticket.md）
- iPhone 17（iOS 27.2）のシミュレーターで checkin/ios-app を動かした。デモを終えてから入り直すと、印をもらう→「はじめての印」の画面→画像で共有（ネイティブの共有シートが開く）まで動いた。運用タブ（北風運用・風）も本番のデータで出た。**アプリの中で印が押せない不具合はなかった**
- 最初に「印の画面が出ない」と見えたのは、同じデモの中で羽田にもう押してあったため（sameAirportMin の「チェックイン済みです」）。ただし半券が切れる動きのあと、その知らせ（say）が画面に見えないまま半券が戻る。web でも同じ。小さな直し：押せなかったときは半券を切る動きをせず、理由を半券のそばか小さな知らせで見せる
- 半券を右へ引く動きは、外からの操作では試せなかった（押す形は動く）。本人の iPhone で試してもらう
## PM から積んだ次の仕事（11/18 7時45分・本人の実地の報告。急ぎ）→ 表示側（1）と朝一番の表示は PR #128 で直した。取り込み側（2）はデータ担当の data/atd-future（移行186）
- 乗る便 JL661（羽田 8:05 発）で、7:34 に「出発しました（08:08）」と出た。まだ出発していない。乗る便のカードは renderRide0 の `if(d.atd)` で出していて、atd は inbound_aircraft → flight_schedule.atd → _shared/odpt_status.ts の odpt:actualDepartureTime から来る。未来の時刻が atd に入っている（ODPT の値が見込みなのか、別の日の便に合わせてしまったのかを調べる）
- 11/18 8時15分 本人の確認：実際の出発は 8:08 で、表示の時刻と同じだった。JAL の運航情報は、出発の前から「実際の出発時刻」の欄に見込みの時刻を入れることがある、と考えられる（だから時刻は正しく、「出発しました」の言い方だけがまちがい）
- 直し方の案：(1) 表示側：atd が今より後なら「出発しました」にせず、見込みとして「出発の見込み 08:08」と出す（checkin）。(2) 取り込み側：actualDepartureTime／actualArrivalTime が取り込んだ時刻より後なら atd／ata に入れず etd／eta にする（data）。通知（遅れ・出発）も同じ値を使っていないか確かめる。テストを足す
- ついでに：朝一番の便で前の便がないときの「この便の前に同じ機体が飛ぶ便は、まだ記録が足りず分かりません」は、前の日の夜に着いた機体なら「朝一番の便（前の便はありません）」と出せないか
- 改善担当（11/10 夜）：PR #63（7c67543）で review-facts-1 の1〜5 を直した。写真 shots-zukan-facts/01b・04・05a・05・07 を見てほしい。PR #48（ae6e870）で review-c5 の1・2 を直した。写真 shots-all-in-tabs/30〜33 と、iPhone の幅で鉛筆のシート（とくに 667 のフライト9行）を見てほしい
- デザイン担当（11/10 夜）：見方の鉛筆のシートは「タブを選ぶ」と同じ部品（番号・絵・≡ なし）で作った。画面案を出すならこの写真（shots-all-in-tabs/30〜32）とそろえてほしい
- 修行担当・撮る人用の担当・運用予想の担当へ（11/10 夜）：運用とフライトの見方の帯の鉛筆が、表示の編集の1枚ではなく見方だけのシート（#dViews）を開くようになった（PR #48）。見方の id と隠す仕組み（loToggleOff・VIEWS）は変えていない
- デザイン担当（11/10 夜）：review-4 の3（04 にデータ欄・出典の版、伊丹の空欄の版）はまだなので、PR #63 では押した回数と同じ角丸カード2枚＋滑走路の行＋出典の1行で作った（写真 docs/pm/shots-zukan-facts/）。画面案を出すなら、この写真とそろえてほしい
- 改善担当（11/10 夜）：PR #63 の写真（01b・02・05 の 667）を見てほしい
- 改善担当（11/10・3回目）：PR #60 に review-app-1 の 1〜4・6・7・9 を入れた（292997d）。写真 docs/pm/shots-zukan-book/03-844-okinawa・03-844-kanto・04-844-hnd・04c-844-nrt を見てほしい。8（見方の帯）は共通の部品なので PM に聞いている
- データ担当（11/10）：airport_facts は PR #59 で作り中と帳面で見た（依頼は重なり）。反映されたら空港ページに出す。もとの依頼：国土交通省「空港一覧」から airport_facts（airport_id・供用開始の年・滑走路の長さ×幅・出典・基準日）を移行と RLS をセットで作ってほしい（会社管理の4空港と番外編は空欄）。PR #57 は feat/zukan-book に取り込んだので反映は図鑑と一緒に
- 改善担当（11/10）：PR #60 の写真（docs/pm/shots-zukan-book/）と iPhone の幅で、ツメ（667・送ったとき）・止まった扉・ターミナルの枠・空港ページのはらう動きを見てほしい
- デザイン担当（11/10）：review-3 の指摘は作る側で入れた。次の版を出すなら PR #60 の写真とそろえてほしい
- 改善担当（11/9 昼）：PR #48 に review-c4 の3つを入れた（029d4c6）。写真 18（667 で成績の行まで見える）・15（「いまは全部乗せです」）・22（夜の入れ替えの帯）を見てほしい。1 は余白ではなく一覧を送る形にした（帯は一覧と重ならない作りのため）
- 改善担当（11/9 定時の回）：PR #48 に review-c3 の6つを入れた。写真 15・16・18・21（と 17・19・20）を見直してほしい。とくに 667 で題と完了が固定されているか、ホームのトーストを見本のすぐ下に移した形
- デザイン担当（11/9）：OFF のスイッチの色は 4版の tokens.md の値（昼 #768090・夜 #66778C）に合わせた（2e57613）。≡ はアプリではスイッチの右端・3本線、題の横に「4/5・5つまで」の数を出している
- 修行担当・撮る人用の担当へ（11/8 夜）：新しい人への提案は「タブを4つにしますか？」の形になった（中身は前と同じ。修行＝運用のタブ・撮る人の見方・撮影地、撮る＝修行のタブ・修行の見方・まとめ）。t57 は 11/8 の日付で「11月の申し込み」の所が落ちている（修行側で見てほしい）
- 改善担当（11/9 1時半）：PR #48 で出す・隠すを ON／OFF のスイッチにした（写真 15〜20）。本人に見せる前に、iPhone の幅で OFF の行がその場に残る形と 667 のトーストを見てほしい
- デザイン担当（11/9）：ON／OFF のスイッチは 07-tabs-v3-onoff の色の変数（--sw-on-*・--sw-off-*）と大きさをそのまま使った。OFF のタブの置き場所は、アプリは PM の指示どおりその場に残している（画面案は一覧の下）。本人の答えが出たらそろえる
- 改善担当：PR #48 に review-c2 の4つを入れた（11/9）。元に戻すのトーストの場所を並べる行のすぐ下に変えたので、iPhone の幅（とくに高さ667）で見直してほしい。吹き出しはログインしたあとに出る
- データ担当（11/8）：表示の設定は upsert を使わず update／insert にした（user_id に update の権限がないので PostgREST の upsert が通らないおそれ）。本物で upsert が通るか見てほしい。PR #37 と PR #39 は一緒に反映する
- 修行担当・撮る人用の担当へ（PM から伝えてほしい、11/8）：新しい人は全部乗せなので、ホームの修行・撮影のカードはひな形の人にだけ出る（今までと同じ）。t62 はマイページの代わりに setPersona で構成を変える形にした。修行と答えた新しい人への提案に「運用の見方『撮る人』」と「撮影地」を入れている
- 経営担当：t99・t105（経営の画面のテスト）が feat/signup の時点で落ちている。経営側で見てほしい
- 経営担当：見やすさの確かめ（tests/a11y/check.py）で、経営の画面の下のタブ（路線・機体）の字の色の濃さが 4.4:1（#bfc2ca／#475268・10.5px）。4.5:1 に届かない。main の版でも同じ
- データ担当：広告担当の依頼 1 のため、登録のときに入口（?from=ig の from、短い文字）を残す列を user_profiles に足してほしい（移行と RLS をセットで。本人だけが一度だけ書ける形）。列ができたら、チェックイン側で登録のときに送る

## 持ち場
- チェックインの画面とロジック（src/・web/）。経営のコードと表には触らない。表の変更はデータ担当へ依頼
- 11/6 から、修行モード（shugyo.md）・撮る人用（satsuei.md）・運用予想（yosoku.md）は下の担当が持つ。チェックイン担当はホーム・運用の土台・マイページ・図鑑・フライト・タブ帯・共通の見た目を持ち、下の担当の持ち場は変えない
- feat/ops-v3 で運用の画面を作り直すときは、撮る人の見方（satsuei.md）と予想の出し方（yosoku.md）の部分の並べ方を変えない。場所が動くなら、その担当の帳面に書く

## 下の担当からの依頼
- 修行（11/20・PR #147 shugyo-jst-year）：修行の年と月を日本時間にした（チェックイン側の関数は変えていない）。全体を流したとき t72・t123（フライトの共有の画面。#dShare の字が押す所をふさぐ）が今の main でも落ちた。チェックイン側で見てほしい
- 運用予想（11/13・PR #83）への答え（11/13 定時の回）：setViewsw は PR #84 で「選んだ見方が帯の中に見えていれば左端から、外のときだけ送る」にした（図鑑・フライトも同じ）。loadPushKey はデモでは呼ばない形に直した（PR #84）。#83 と #84 を重ねると src/index.html は自動で重なり、ぶつかるのは組み立てた web/ だけ（作り直せばよい）。重ねた版で t128・t130・t60 が成功。opsViewsReveal はそのままで動く
- 運用予想（11/13・PR #83 yosoku/fix-sweep-1113）：運用の見方の帯は opsViewsReveal で「はじめ左端・選んだ見方が外のときだけ送る」にした（共通の setViewsw は変えていない）。図鑑・フライトの帯も同じ送り方にするなら setViewsw に入れてほしい。デモの push-subscribe は運用からは呼ばなくなった（遅れのお知らせを出さないため）が、loadPushKey そのものの直し（見回りの9）はそちらで。src/index.html で変えた関数は報告 docs/pm/report-yosoku-fix-sweep-1113.md に
- 修行（11/11 夜・PR #71 shugyo-view-sheet）：修行の見方のシートを作り、`LO_EXT.sg = { groups, toggle, reset }` を足した（1枚に修行のカードが出る。39このうち）。そのため t118・t124（32→39このうち・カードの並びに sg）と t126（修行のカードがない間の1行は LO_EXT.sg を一時的に外して確かめる）を修行側で合わせた。お願い：1枚の「全部乗せに戻す」で修行の見方も戻すなら、loResetAll のあとに `LO_EXT.sg && LO_EXT.sg.reset && LO_EXT.sg.reset()` を呼んでほしい（今は呼ばれないので修行の見方は戻らない。本人の答え待ち）
- 修行（11/8）：t57 が落ちる原因は修行の計画の運賃の欄（11/4 の SG_MONEY で隠した）にテストが入れようとしていたこと。修行側で t57 を直した（PR #44・3/3 成功）。t57 の件はこちらで持つので、チェックイン側は調べなくてよい。t62・t61 は reload の土台の問題のままなので PR #20 を待つ
- 修行（11/6 22時・PM の指示で）：t62 の「修行：開き直しても覚えている」が落ちる原因は修行の部分ではなく、テストの土台（file:// で reload すると localStorage が落ちる）。main で 4/10、PR #20 の t62 で 10/10。修行側では直さないので、PR #20 を main に入れてほしい（入ったら修行側で t62 を10回流し直す）
- 修行（11/6）：データ担当へ渡してほしい。ANA の時刻表は 11/30 まで（10/28 時点）。12月の計画が作れるか、docs/pm/shugyo-timetable-check.sql（ブランチ shugyo-inventory・PR #26。読むだけ）を本人に流してもらい、ANA の最後の日が 12月以降か見てほしい。来ていなければ timetable-sync の取り込みを見てほしい（修行の帳面には「ほかの帳面は checkin.md の依頼欄だけ書いてよい」とあるので、データ担当の帳面には直接書いていない）
- 修行（11/6）：sgSeg（修行のピル）を運用のゴーアラウンドの設定（gaSetHTML）も使っている。運用を作り直すとき（feat/ops-v3）に別の部品へ替えるなら知らせてほしい。修行側で sgSeg を変えるときは先にここへ書く


## PM から積んだ次の仕事（11/18 0時15分、本人の決定）→ PR #122 に足した（673e278）
- checkin/zukan-airfields に足す：図鑑の名前は「基地」のままでよい。秘密の実績（一般の人が行けない飛行場）は見出しを「シークレット」にし、取るまで中身（名前・場所・数）を隠す。テスト t141 も合わせる

## PM から積んだ次の仕事（11/5、本人の「反映して」とは別）
- 広告担当からの依頼（報告 docs/pm/report-ads-early-access.md）
  1. プロフィールのリンク https://soramemo.jp/?from=ig の from を登録のときに残す（表の変更はデータ担当へ依頼）
  2. コードのメールが送れないとき「いま登録が混み合っています。1時間ほどあとで試してください」と出す
  3. 共有画像に「非公式アプリ」の文字を足す案（作る前にデザイン担当の画面案）

## 11/5 17:45 反映済み
- 本人の「反映して」で feat/signup を main に入れた（main 7daa277）。Actions はテスト・データベース・アプリともに成功。本番で登録の入口・otpLength 6・TERMS_VER を確認
- （11/5 済み・#8）次の仕事（PM から）：tools/build_font.py のフォントの取得が github.com の一時的な 504 で反映を2回止めた。取り直し（数回・待ちつき）と raw.githubusercontent.com の URL への切り替えを入れる

## 11/5 21時 反映済み
- fix/font-fetch を本番に流した（取り直しとキャッシュ）。fix/font-fetch-retry は使わない（同じ中身の前の版）

## 11/5 21:22 反映済み（フォントの取得）
- #7・#8 が main に入った（aa0d1ae）。反映の run 197 はテスト・データベース・アプリともに成功。取得の失敗はログになし
- キャッシュは保存済み（key font-src-88da428b…、約5.5MB）。使えるかは次の反映でわかる
- 決めごとの残り：tests/tools のテストを deploy.yml のテストの段に足すか（本人の判断待ち）

## 11/6 18時半 反映済み（main 14916e9）
- feat/home-v3（新しいホーム）を本番に流した。Actions はすべて成功。本番でログインしていないときのホームを確かめた
- ログインしていないときのメールのログイン欄は、本人が「消す」と決めた（11/6）→ PR #23 で t7・t43・t44・t114 も直した
- 次の候補：運用・マイページの改善（improve-1106 の 02・03）。選べるカード（rethink-1106 の D）は 11/6 に決まった（13枚・サーバーに保存・1月のあと）

## PM から積んだ次の仕事（11/8 21時半、全部乗せを案3「タブから選ぶ」に作り直す）→ PR #48 で作った（11/8 夜）
- main に入った（まだ本番に出ていない）PR #39 の上に、ブランチ feat/all-in-tabs で作り直す。画面は design/all-in-filter-alt の C1〜C4（案3）
- 下のタブ帯の長押しで「タブを選ぶ」シート（≡で並べ替え、左へ払うとタブから外す、5つまで・ホームはいつも）。マイページからも同じシートを開ける
- ホームのかたまりは「ホームに出すもの」の見本の上で × で外し、「外したもの」から ＋ で戻す
- 見方は各画面の見方の帯から（隠し方は今の部品を使う）
- 全部乗せに戻す・アンケートの提案は C3・C4 の形。保存は user_view_prefs のまま（並べた順も保存）
- 1版の「表示の編集」の1枚の画面は、全体を見直す所としてマイページに残すかを報告に書く（本人に聞く）

## PM から積んだ次の仕事（11/8 16時15分、本人の依頼「最初は全部乗せ＋フィルターで消せる自分用のカスタム」、1月のストア公開に入れる）
仕様（短く）
- 目的：はじめての人に「気軽に・撮影・修行」の3つのひな形から選ばせず、全部の機能を見せたうえで、要らないものを自分で消せるようにする
- 画面：(1) 始めは全部乗せ（タブ・見方・かたまりを全部出す） (2) フィルターのように表示・非表示を切り替える1枚の画面（マイページの「表示の編集」を作り直す。項目ごとのピルのオン・オフ） (3) 新規登録のアンケートの答えから「これを隠しますか？」を1回だけ提案（断れば全部のまま） (4) 戻すボタン（全部乗せに戻す）
- データ：設定はサーバーに保存（端末を替えても同じ）。表はデータ担当（移行と RLS をセット、本人だけ読み書き、退会で消える）。ログインしていないときは端末に保存
- 1月に入れるのは「表示・非表示と保存」まで。並べ替え・選べるカード（案 D）は公開のあと
- 完了の条件：新しい人は全部乗せで始まる／隠したものが次に開いても隠れている（別の端末でも）／全部乗せに戻せる／アンケートの提案が1回だけ出る／今ひな形を使っている人の表示は変わらない／テストを足す
- 決まりの変更：10/28 の「気軽にをいちばん軽い構成に」と、ひな形を選ぶ形は、本人の 11/8 の決定で置き換える
1. デザイン担当の画面案を待つ（PM が頼んだ。改善担当を通して本人に見せる）
2. 本人の OK のあと、データ担当の表（user_view_prefs など）とあわせて作る。修行・撮る人の見方はそれぞれの担当の持ち場なので、出す・隠すの仕組み（部品）を作って渡す

## PM から積んだ次の仕事（11/7 22時半、全体のデバッグで見つけたもの）
- 日をまたぐ時刻：空港の今の便の一覧（src/index.html の newTime を出す所）が「→25:25」をそのまま出す。「→翌1:25」の形にする（決定事項）。ODPT の値の形はそのままにし、画面で直す。テストを足す
- テスト t57（乗る便の機体・乗った機体の図鑑・修行の計画・順光の目安）が main で落ちる（入力欄が「見えない」で待ちぼうけ）。前から落ちていて PR #20 でも直っていない。どの画面の入力欄かを調べ、画面の不具合かテストの古さかを分けて直す。修行の部分なら修行担当へ
- テスト t48（搭乗券の読み取り）は手元の環境（/tmp/build の @zxing）が要る。CI で流れているか、流れていないなら流す形にするかを報告に書く
- 天気が取れないとき：運用の画面が「気象通報を読み込んでいます…」のまま止まることがある（11/6 夜、デモで確認）。metar 関数がたまに 503 を返すため。失敗したら「いま天気を取れません」と出し、前に取れた値があればそれを時刻付きで出す。関数側の直しはデータ担当（docs/pm/report-debug-1107.md を見る）

## PM から積んだ次の仕事（11/6 23時半、ストアの準備）
- 審査用のログイン：Apple・Google の審査の人がメールのコードを受け取れないため、決まった審査用のアドレスだけ決まったコードで入れる形を作る（方針計画書の「審査用」）。コードやアドレスはソースに直書きせず、サーバーの秘密の設定に置き、審査のメモ欄には本人が書く。表や関数が要るならデータ担当へ依頼。運用の画面（feat/ops-v3）のあとでよい

## PM から積んだ次の仕事（11/6 19時半、ログイン欄を消したあと、この順で）
1. 運用の画面を改善案の3版目に（design/improve-1106 の 03-ops-v3・03b-ops-wind-v3）。風がないときは「北風運用」と言い切らず滑走路の組み合わせ、「推定です。実際の運用と違うことがあります。」を1枚目の下に1行。ブランチ feat/ops-v3
2. マイページを改善案の3版目に（02-mypage-v3）。タイル、大きい字は今の値。運用・成績・表示の編集・デモの終了の入口を残す。上の段をホームとそろえる（review-home-v3 の指摘3）。ブランチ feat/mypage-v3
- どちらも改善担当が見てから本人に見せる。暗い表示は入れない（1月のあと）

## PM から積んだ次の仕事（11/9 0時40分、全部乗せ 案3 の仕上げ）→ PR #48 に足した（a245503）
改善担当の review-c2（design/all-in-filter-alt）：review-c1 の5つはおおむね直った。本人に見せる前に次の2つ、1月までに3つ目。feat/all-in-tabs に足す
1. 文の「× で外し、＋ で戻す」「シートの見本の上で × で外し」を「−」に直す。t119 に「画面の文に『× で外し』がない」を足す
2. 古い写真（docs/pm/shots-all-in-tabs/ の 01・02・04・06・07・08）を撮り直す。とくに高さ667 で新しい C1 とトーストが重ならないか
3. 長押しの吹き出しがログインしていない人の「ログイン・登録｜デモで試す」の字を隠す。ログインかデモを始めたあとに出すか、吹き出しのぶんの余白をあける
4. 小さい所：全部乗せに戻すの確かめの表の左の欄の幅（「タ／ブ」の折れ）・「そのまま」を「外しているものなし」に・トースト「4こ」を「タブ4つ」のように
報告 report-all-in-tabs-c1.md に足す。main には入れない（本人の「反映して」待ち）

## PM から積んだ次の仕事（11/9 1時20分、ON／OFF を試す）→ PR #48 に足した（3281874・色は 811a2ef でデザイン案に合わせた）
本人「ON OFFにしてみて」。PR #48（feat/all-in-tabs）で：
1. タブを選ぶ・ホームに出すものの各行の「−」「＋ 出す」を ON／OFF のスイッチ（字の札 ON／OFF つき、色だけに頼らない、押せる大きさ 44px 以上）にする。ホームの行は「いつも」で切り替えなし。外したものは下の「タブにないもの」へ動かさず、その場で OFF にする形でよい（並べ替えのつまみはそのまま）
2. 外した直後のトースト（行き先・元に戻す）はそのまま。文の「−で外し、＋で戻す」は「OFF にすると隠れます」に
3. t119・t118 を直す。昼の写真（390×844 と 667）を撮って報告に足す。夜の色はデザイン担当の 2版に合わせる（tokens）
試しなので、本人に写真を見せてから決める。main には入れない

## PM から積んだ次の仕事（11/9 3時35分、改善担当 review-c3 を受けて）→ PR #48 に足した（0999d3c・報告 report-all-in-tabs-c3.md）
review-c3（design/all-in-filter-alt）：ON／OFF の方向と「その場に残す」はよい。もう1回直す。PR #48 に足す
1. 667 で題と「完了」が消えない：説明文を1行（例「OFF で隠れます。≡ で並べ替え。」）・題と完了はシートの上に固定し送るのは一覧だけ・トーストで送らない
2. OFF のスイッチの縁とつまみの縁を 3:1 以上（デザイン担当の変数に合わせる。値は design.md に書かれる。先に #8A94A3 前後で作ってよい）
3. OFF の行の補足は「マイページから開けます」の1行にして ON と同じ高さ
4. 5/5 のとき OFF の行の補足を「ON にすると外すタブを選びます」に。入れ替えの写真を足す
5. ホームに出すもの：トーストの高さぶん一覧の下に余白（844 と 667 で重ならない）
6. 小さい所：「チェックインの半券」も薄い地に（今日の数字とそろえる）・≡ の印を等号に見えない形に・写真は同じ状態でそろえる
写真 15・16・18（667）・入れ替えの1枚を撮り直して報告に。main には入れない

## PM から積んだ次の仕事（11/9 5時40分、review-c4 の小さい所。本人が ON／OFF に決めてから）
review-c4：見せてよい。本人の答え（ON／OFF か −／＋ か）を待つ。ON／OFF に決まったら PR #48 に足す
1. 667 で「元に戻す」の帯が最後の行を隠す → 一覧の下に帯の高さぶん余白
2. 写真15 の「全部乗せに戻す」が薄いグレーで押せないように見える → 押せるなら紺に
3. 夜の画面では入れ替えの帯の薄い黄色を使わず、縁だけに（design/night 07c に合わせる）
- 11/9 9時45分 本人：ON／OFF に決定（CLAUDE.md「11/9 の決定」）。上の「5時40分」の1〜3を PR #48 に足してよい
→ PR #48 に足した（029d4c6・報告 report-all-in-tabs-c4.md）

## PM から（11/9 16時35分、小さい直し・急がない）→ PR #60 で直した
- 改善担当 review-2（図鑑）より：はじめの案内の文が「羽田・成田は各ターミナルにも印」と古い。本番は6空港14のターミナル（TERMS）。文を「大きな6空港はターミナルにも印があります」のように直す。次の小さい直しの回でよい

## PM から積んだ次の仕事（11/10 1時、図鑑の作り直し）→ PR #60 で作った（644ff6e・報告 report-zukan-book-app.md）
本人「すべてOK、作ってみて」。CLAUDE.md「11/9 の決定」の図鑑の形と「図鑑のデータ」に従う。ブランチ feat/zukan-book（main から）、下書き PR で止める
- 画面案：design/zukan-book の *-v3（PR #55、fe40c1b）。改善担当の review-3.md が来たら、その指摘も入れる
- 図鑑のタブ（bkSeg・setBookSeg・RG_COL・図鑑の見方のあたり）：右端のツメ（昼は地方の色＝GOD_COLORS、夜は色なし）・上のカードに 16／86 と9地方の数・扉は上に止まって見出し・そろえた枠（高さ104）・ターミナルは TERMS どおり6空港14こ（86 に入らない）・0／86 の人の1行
- 見方の帯：地方別（region・いつも）・地図（map）・行った順（chron）。tiles・signs・region を off から外し、選んでいる見方は tiles・signs→region。読むときに直し、保存は fmt 3（データ担当 report-zukan-data.md の3。サーバーの行は書き換えない）。今の人へ1回だけのお知らせ
- 1空港の詳しい所：押した記録が上・前／次（はらうのは印のカードだけ、端20pxは受けない）・開港と滑走路は airport_facts ができるまで出さない形（04b）
- 索引：字で探す欄（名前・コード・読み）＋ABC順＋50音順。読みは data/zukan-yomi（PR #57）の airport_yomi。PR #57 は本番に入っていないので、このブランチでは #57 を取り込んで作り、反映は一緒に（本人が「反映して」と言ったとき）
- ほかの図鑑・実績：実績・飛行場と滑空場・番外編・機体図鑑（特別塗装機）。「86 の数は変わりません」
- 記号の意味の画面（08）。日付は「2026年11月1日」
- テスト：今の図鑑のテストを直し、ツメ・扉・索引の探す欄（「みや」「ちとせ」「せんとれあ」）・見方の移し替え・0の人を足す。390×844 と 667、昼と夜で撮る
- はじめの案内の「羽田・成田は各ターミナルにも印」の文も直す（16時35分の分）
- 11/10 1時15分 PM：改善担当 review-3（design/zukan-book）の指摘を図鑑の作り直しに入れる：ターミナルの枠の名前は「新千歳 国内」の短さ・ツメで飛んだときも扉が上に止まる形（別の帯なし）・羽田などの空港のページにターミナル 2/3・まだの空港のページ（記録の欄なし）・行った順は「計28回」と月の見出し・「はらうと…」の札はピルにしない。デザイン担当が v4 で描き直し中

## デザイン担当から：図鑑の画面案 v4 の変わった所（11/10、design/zukan-book 31959a1・対応表 answer-3.md）
- ターミナルの枠の名前は「新千歳 国内」「新千歳 国際」「福岡 国内」「福岡 国際」「羽田 第1」の短さ。名前の行は1行（white-space:nowrap・長いときは…）。枠の子は縮ませない（flex-shrink:0）で、枠104に収まる
- 03 ツメで飛んだときも 02c と同じ「扉（1行）が上に止まる」形。別の帯はなし。小さな地図と「最後に押した」は扉の下の最初の行（ツメで飛んだときだけ）。「図鑑の上へ」は止まった扉の右端の上向きの印（44px）
- 扉が止まる位置は top: env(safe-area-inset-top)
- 04 羽田などターミナルのある6空港だけ、データ欄の下に「ターミナル 2/3」の1枚（T1 ✓12・T2 ✓9・T3 まだ）と「ターミナルの印は別に数えます（押した回数 28 には入りません）」。数え方が本番と違うなら文を直す
- 04c まだ行っていない空港（新）：点線の印・「ここでチェックインすると印が付きます」・判定の範囲（空港ごとの値、羽田 2km）・いまの場所から ○km（位置を許している人だけ）。データ欄2つと押した記録は出さない。ターミナルのある空港はターミナルの1枚（全部まだ）
- 02z「いちばん近い ›」：その地方の扉が上に止まる所まで飛び、その空港の枠を地方の色の縁で2秒ほど光らせる（03z・新）
- 02d 行った順：見出しは月（2026年10月）、日付は枠の中の1行（10月25日・13px）、回数は「計28回」、✓ の丸なし、枠は地方別と同じ幅（右のツメの分は空けたまま）
- 04 の「‹ 印のカードをはらうと、となりの空港へ ›」はピルでなく、地も影もない薄いグレーの字1行（13px）
- 06 の「空港の図鑑」は押せる白いカード＋「›」（見出し「もどる」の下）。08 の文は「86 の数に入りません」

## PM から積んだ次の仕事（11/10 6時35分、図鑑のアプリの小さい直し）→ PR #60 に足した（292997d・報告 report-zukan-book-app.md の3回目）
改善担当 review-app-1（design/zukan-book）：もう1回直す（小さい直し）。feat/zukan-book に足す
1. 844 で沖縄のツメを押すと九州が光る → 図鑑のいちばん下に「画面の高さ − 扉の高さ」の余白。t120 に「844 で沖縄」を足す
2. コードのない空港の枠と前／次：2行目を「コードなし」、大きい字は3字（神津島）まで入る大きさに
3. 空港ページ：空港名は「（羽田）」の前で折る（keep-all など）、ターミナルの印の名前は「羽田 第1」。まだの空港のページに「画像で共有」「写真に押す」を出さない
ほかの指摘も review-app-1.md を読んで小さいものは入れる。直したら写真（844 の沖縄・関東の枠・羽田と成田の空港ページ）を撮り直す

## PM から（11/10 16時、図鑑を反映した）→ データ欄は PR #63、PR #48 の取り込み直しは cf47306
- PR #60（図鑑）と #59（airport_facts・移行160）を main に入れた。次にやること：空港ページのデータ欄に「供用開始」「滑走路」と出典の1行（「出典：国土交通省『空港一覧』を加工して作成」）を出す（airport_facts がない空港は出さない形のまま）。ブランチ feat/zukan-facts、下書き PR
- PR #48（タブから選ぶ・ON／OFF）は main（図鑑の入った版）を取り込み直し、表示の編集の数と t118 をそろえる

## PM から積んだ次の仕事（11/10 20時、反映の前の小さい直し）→ 済み（PR #63 7c67543・PR #48 ae6e870）
- feat/zukan-facts（review-facts-1）：データ欄と出典を自分の記録の下へ（667 で自分の記録が見えるように）・出典の字 13px・リンクの押せる高さ 44px・図鑑の上の「ほかの図鑑・実績」をツメにかぶらない幅に（main にも同じ問題）
- PR #48（review-c5 の1）：図鑑の鉛筆は、その画面の見方だけの小さいシート（3行を ON／OFF、題と完了を固定）を開く。1枚の表示の編集を残すなら題と閉じるを固定し、部品を ON／OFF にそろえる（1月の公開の前に）

## PM から積んだ次の仕事（11/11 9時10分、フライトの作り直し）→ PR #65 で作った（3cd5ad2・報告 report-flight-book-app.md）
本人「すべてOK」（CLAUDE.md の 11/11 の決定）。ブランチ feat/flight-book（main から。#63・#48 が main に入ったら取り込み直す）、下書き PR で止める
- 画面案：design/flight-book の *-v4（54e887e）と review-3.md。A1 上の段つきの1画面（シートはやめる）・A2 1便の詳しい所・A2s 共有（登録記号はじめ ON・座席はじめ OFF・「各航空会社とは関係ありません」）・A3 1年のまとめ（路線の数を残す）・地図は今の地図の線の太さ＝回数（1色）・年をまたいで1本につながる日誌・年を選ぶとその年の頭へ
- 車などの移動：便に入れず「車など」と別に数える（日誌の行は会社の帯なし・点線の札「車など」・空の上なし）。便・空の上・距離の数に入れない
- 今の「案内板」「カレンダー」などの見方は、画面案の 07 のとおりにまとめる（見方の帯は ON／OFF の部品）。設定の移し方は図鑑と同じく読むときに直す
- テストを直し・足す（便の数と車など、年をまたぐ所、共有の2つのスイッチ）。390×844 と 667、昼と夜で撮る
- 修行タブの数え方（修行担当の持ち場）に影響する所は shugyo.md に書く
- 11/11 10時半 PM：#63（供用開始・滑走路）と #48（タブから選ぶ・ON／OFF）は main に入れて本番に反映した（#48 は web/ のぶつかりを組み立て直しで解いた、80c7921）。feat/flight-book は main を取り込んでから進める
- 11/11 11時25分 PM：本人が「すべての見方の設定を変えたい（各画面の鉛筆と1か所の一覧の両方）」と決めた（CLAUDE.md「見方の設定」）。フライトの作り直しの見方の帯は、図鑑の鉛筆のシートと同じ部品を使う。1か所の一覧はデザイン担当の画面案（design/view-settings）を待ってから

## PM から積んだ次の仕事（11/11 13時、フライトの反映の前の直し）→ PR #65 で直した（bb1d639・報告 report-flight-book-fix1.md）
改善担当 review-app-1（design/flight-book）：見せてよい。main に入れる前に直す（PR #65）
1. statusRows で isCar(f) の便を飛ばす（成績のステータスの目安と修行の sgYear の両方が直る）。テストに「車などにした便は数えない」
2. 上に止まる年のカードは、止まったら年の字と ‹ › だけの細い帯に（月の見出しを隠さない）
3. 地図の凡例の「車など」を点線に

## PM から積んだ次の仕事（11/11 13時5分、すべての見方の設定を作る）
本人「すべてよい」（CLAUDE.md の 11/11 13時）。PR #65 の直しのあとに。ブランチ feat/view-settings（#65 が main に入ってから main を取り込む）、下書き PR
- 画面案 design/view-settings の *-v2（0176e46）と review-1.md。消せない見方は案A（最後の1つだけ残す・「最後の1つ」の札と理由）
- 各画面の鉛筆のシート（図鑑・フライト・運用。修行のシートは修行担当に shugyo.md で頼む）。マイページの表示の編集の1枚は画面ごとに畳んだカード・題と閉じるは固定・「すべて｜隠しているもの ○」・行き先の字・全部乗せに戻すは下
- 部品は ON／OFF にそろえる（✓ のピルをなくす）。保存は今の user_view_prefs の形のまま（表を変えるならデータ担当へ）
- 経営のタブの中は触らない。テストを直し・足す。390×844 と 667、昼と夜で撮る

## PM から（11/11 17時20分、見方の設定の反映の前の直し）→ PR #68 で直した（c837993・報告 report-view-settings-fix1.md）
改善担当 review-app-1（design/view-settings）：反映してよい。反映の前に PR #68 に：表示の編集の上の「‹ マイページ」「閉じる」「すべて」「隠しているもの」を高さ 44px に。ほかの小さい指摘も review-app-1.md を見て入れられるものは入れる

## PM から積んだ次の仕事（11/12 10時25分、近くの空港と図鑑の飛行場・滑空場を作る）
本人 OK（CLAUDE.md の 11/12 10時）。ブランチ feat/near-airfields（main から、data/heliports を取り込む）、下書き PR
- 近くの空港：画面案 design/near-airfields の *-v5（cd5b029）と review-5.md。CLAUDE.md「近くの空港」「近くの空港の細かい所」どおり（分けずに近い順・半券とパタパタは先頭・20km・民間空港がなければ1つ足す・基地は出さない・判定の決まりは今のまま）。review-5 の3つ：行は「飛行場・滑空場・ヘリポートも出す（はじめ ON）」・667／740 で一覧の下に 12px 以上・見出し「ほかに 20km 以内 ○つ」。src/index.html の nearest・nearestBase・renderHomeMap・showNearest のあたり
- 図鑑の飛行場・滑空場：画面案 design/zukan-airfields の *-v3（7bd5ec0）と review-3.md。最初の画面の入口のカード・ツメと地方の扉の別の図鑑（86 に入れない）・同じ所に重なる行った丸は数の入った1つに・夜の凡例の点を外す。直した 02 の 844 の写真を報告に
- ヘリポート：data/heliports（移行163・t103）を取り込み、種類の札「ヘリポート」
- テストを直し・足す。390×844 と 667／740、昼と夜で撮る

## PM から積んだ次の仕事（11/12 13時30分、近くの空港の反映の前の直し）→ PR #75 で直した（6a3b6e7・報告 report-near-airfields-fix1.md）
改善担当 review-app-1（design/near-airfields）：もう1回直す。PR #75 に：
1. 「ほか○つ」で引き上げたとき、地図の見える高さに「いまここ」と先頭が両方入るよう寄せ直す（閉じたら元へ）
2. 844 も一覧の下を 12px 以上空ける（行の高さを 667 と同じに、または2行に）。引き上げた位置で今日の数字のカードが帯の下からのぞかない
3. 一覧と「すべて」の名前はふだん呼ぶ短い名前（羽田空港・伊丹空港など）か2行まで
4. 「飛行場・滑空場・ヘリポートも出す」が語の途中で折れない
（図鑑のヘリポートの扱いは本人の答え待ち。今の形のまま）直したら加須の 844／740 と東京駅の 844 の引き上げた位置を撮る
- 11/12 14時50分 PM：本人「A」（CLAUDE.md「図鑑のヘリポート」）→ PR #75 で直した（7a901bd・報告 report-zukan-heli-title.md）。PR #75 で、図鑑の題を「飛行場・滑空場・ヘリポートの図鑑」にそろえる（入口・扉の札・ほかの図鑑・実績の行）。今の直し（review-app-1 の1〜4）と同じ回でよい

## PM から積んだ次の仕事（11/13 4時、全体の見回りの直し）→ PR #84 で直した（91a8a4e・報告 report-fix-sweep-1113.md）
報告の元：kaizen/sweep-1113 の docs/pm/report-sweep-1113.md（写真は docs/pm/report-sweep-1113-shots/）と data/speed-1113 の docs/pm/report-speed-1113.md。本人「一度すべてを見てバグや反応しないところを直し、処理速度を早くして」。不具合の直しなので画面案は要らない。見た目が変わるもの（大きさ・並び）は最小にし、変わる所は写真を報告に貼る。ブランチと下書き PR、main と本番には入れない。ブランチ checkin/fix-sweep-1113
1. 図鑑でデモの「終了」が押せない（右端のツメ「北海道」がかぶる）→ ツメの上端をデモの帯の下に
2. 高さ 667 のホームで地図の「＋」「−」が押せない（MAIN.wrap がかぶる）→ 枠に pointer-events:none、中のボタンだけ戻す
3. 乗る便のカード：日本時間0〜4時に、前の日に出た飛行中の国際線で「国際線の記録に入れる」が出ない（e2e t60 が夜中に2回とも失敗）。日付の決め方を直し、t60 を時刻によらず通るように
4. フライトの「地図」に下の地図がない（白地に線と点）→ 今の地図（国土地理院の淡色）を下に敷く。線の太さの描き方は今のまま
5. 高さ 667 のログイン画面で「デモで試す」が画面の外 → 「新規登録」の下に上げ、押せる大きさに
6. 図鑑「図鑑の上へ」が下のタブ帯にもぐる
7. 押せる大きさ 44px 未満の共通部品（見方の帯のピル・上の段のマイページ・デモの「終了」・シートのつまみ）：見た目の大きさは変えず、押せる範囲だけ 44px に広げる
8. 速さ：src/sw.js のアプリ本体を「保存した版を先に出し、裏で新しい版を取る」形に（更新の知らせは今の仕組み）。maplibre は地図を出す直前に読む。開いた直後の app_status・airport_notices・current_events は並べて呼ぶ
9. 小さいもの：デモの便の時刻を固定（開くたびに変わらない）、Turnstile を開き直すとき turnstile.remove() で片付け、デモでは push-subscribe を呼ばない
確かめ方：全 e2e（tests/e2e/run_all.py）を通し、1・2・5 は 390×667 と 844 で押せることをテストに足す。夜の CSS（data-night）の食い違いは土台を入れるときに直すので今回は触らない

### PM のメモ（11/13 6時）
見回りの直し5本（#79・#81〜#84）をまとめて全 e2e：99件中94件、流し直して t19・t47・t123 は通る。t48 は手元の環境だけ。t62「断ったらしばらく聞かない」は main でも3回中2回落ちる（前からの揺れ）。次の回で揺れの原因を直す
経営の t128 は t129 に付け直した（PM）

## PM から積んだ次の仕事（11/13 21時20分、遅れの通知の受け取り）→ PR #90 で入れた（016bba9・報告 report-push-renotify.md）
データ担当の data/alert-merge（遅れの通知を1件にまとめる）の依頼。src/sw.js の push の受け取り（showNotification）で、届いた中身の renotify を渡す（`renotify: !!d.renotify`、tag があるときだけ）。同じ便の通知を上書きしたときにも鳴るようにするため。画面は変えない。ブランチ checkin/push-renotify、下書き PR。data/alert-merge と一緒に反映する

## PM から積んだ次の仕事（11/15 12時40分、海外の空港の止まり具合の画面）→ PR #96 で作った（9f601cc・報告 report-world-ops-app.md）
本人「A」（決定事項【11/15】）。画面案 design/world-ops の W1（案A）・W2・W3・W4・W4b・W5 と docs/pm/report-world-ops-design.md どおり。関数はデータ担当の data/world-ops（#93、world_airport_ops。feed_at・note の分け方・reason の日本語を今足してもらっている）を取り込んで使う。
- 案内板（boardHTML の .bdseq の li）にピンの札（いちばん重いもの1つ、出発前・到着前の便だけ）。便の数の札は便の列にはつけない
- foreignHTML の上に「行き先の海外の空港のいま」の欄（空港ごとに1行、押すと spsheet の形のくわしく。断り書きは欄の中に太字、note はすぐ下）
- renderRideIntl の状態の1行の下に1行（W4・W4b）
- テスト：札が出る・過ぎた便に出ない・便の数の札が便の列に出ない・取れないときは何も出さない。ブランチ checkin/world-ops、下書き PR、本番には入れない

## PM から積んだ次の仕事（11/16 14時10分、見落としの片付け。本人「OK」）→ PR #107 で入れ直した（062e504・報告 report-redo-1116.md）
一覧は docs/pm/board/overlooked-1116.md。作ったのに main に入っていない直しを、今の main に取り込み直して（番号・テストの名前のぶつかりも直して）、新しいブランチの下書き PR に。本番には入れない。古い PR は「入れ直したので閉じてよい」と報告に書く。ブランチ checkin/redo-1116
1. fix/fw-merge（6e689cf）：運用タブの遅れ・欠航・ダイバートのカードを1便1枚に（fwHTML）。#91 の通知のまとめ方（便名＋運航日、共同運航は運航する便）とそろえる。11/16 の本番で出発と到着の両方が634便
2. #15 checkin/send-busy（確認コードのメールが送れないときの言い方）
3. #23 fix/remove-home-login（ホームのメールのログイン欄を消す。今の main にまだあるか確かめてから）
4. #20 checkin/test-waits（揺れるテストの直し。今揺れている t17・t19・t62・t37 も見る）
5. ODPT の dc:date（データの時刻）を画面に出す（ODPT の約束。出典の文の近くに「○時○分時点」。データ担当が返す形を data.md に書く）

## PM から積んだ次の仕事（11/16 15時50分、運用タブを空港と機体に分ける。見落としの片付けの反映のあとに始める）→ PR #112 で作った（361bb78・報告 report-ops-split-app.md）
本人「OK」（決定事項【11/16】運用タブ）。画面案 design/ops-split の2版（A1・A1b・A2・A2e・A3・A4・P1・P2・V3・V1c）と docs/pm/report-ops-split.md どおり。運用タブの土台（切り替え・空港のピル・見方の帯・表示の編集）はチェックイン担当。撮る人の見方の置き場（案2）は撮る人用担当、機体の1日の予想は運用予想担当の部品をそのまま使う（中を変えるときはその担当の帳面に）。ブランチ checkin/ops-split、下書き PR、本番には入れない。テスト：844 と 667 で予想の1便目が見える・鉛筆と選んだ見方が画面の中・「機体」OFF で戻せる

## PM から積んだ急ぎの仕事（11/16 23時55分、#113 の反映がテストで止まった）→ PR #114 でテストを直した（4391d34・報告 report-fix-ops-test.md）
#113（運用タブを空港と機体に分ける＋特別塗装機の表）が main に入ったが、反映の「テスト」で tests/ops/ops.test.mjs の2件が NG になり、本番には入っていない（データベースと関数・アプリは skipped）。
- NG 特別塗装機の欄が出る（羽田に来る特別塗装機）
- NG 地図の名札に特別塗装機の★が出る
運用タブを分けて特別塗装機が「機体」側に移ったため、ops.test.mjs が空港側で探して見つからない形と思われる。画面の決まり（空港側の地図の★は残すのか）を画面案 design/ops-split 2版で確かめ、①画面が正しければ ops.test.mjs を新しい形に直す、②★や欄が本当に消えているなら画面を直す。tests/ops も含めて全部のテストを通す（node tests/ops/ops.test.mjs）。ブランチ checkin/fix-ops-test、下書き PR。main が今このテストで止まっているので急ぎ

## PM から積んだ次の仕事（11/17 12時20分、いつもより遅いの画面）→ PR #117 で作った（0f76975・報告 report-usual-late-app.md）
本人「OK」（決定事項【11/17】）。画面案 design/usual-late 2版（U1・U1n・U2・U2b・U2c・U3・U4・U5）どおり：renderRideIntl（見込みの箱・灰色の点線の札・箱の中の出典の1行・門限とダイバート）・乗る便があるときはホームのシートの先頭に乗る便のカード・foreignHTML（題の下の凡例・灰色の札）・spDetailHTML（着陸の箱）。関数はデータ担当の data/usual-late-rpc を取り込む（まだなら U1n の形で出す）。tests/ops・e2e・sql を全部通す。ブランチ checkin/usual-late、下書き PR、本番には入れない

## PM から積んだ次の仕事（11/17 18時05分、止まっていた決めごとが決まった。上から順に）
1. 近くの空港の小さな直し3つ（大利根が二つ出る・東京ヘリポートの名札が点線にかぶる・夜の名札が薄い）。ブランチ checkin/near-fix → PR #121 で直した（2fc3afc・報告 report-near-fix.md）
2. 図鑑の飛行場・滑空場（決定事項【11/17】・画面案 design/zukan-airfields 2版の *-v2）。ブランチ checkin/zukan-airfields → PR #122 で作った（f6198d9・報告 report-zukan-airfields-app.md）
3. 空港の3D（決定事項【11/17】・画面案 design/airport-3d の最後の版・データ担当の data/airport-3d-data（#72）を取り込む）。ブランチ checkin/airport-3d。データの取り込み（OSM＋PLATEAU の出典 ODbL・約1分遅れ）で足りない所は data.md に依頼 → PR #123 で1回目を作った（c69545b・報告 report-airport-3d-app.md。形は仮）
どれも下書き PR、本番には入れない。tests/ops・e2e・sql を通す

## PM から積んだ次の仕事（11/17 20時30分、iPhone のアプリにする計画）※今の3つ（近くの空港の直し・図鑑の飛行場・空港の3D）のあとでよい
本人「買ったからアプリにできるようがんばろ」（本人が M1 の Mac を買った）。まず計画だけ（コードは作らない）。報告 docs/pm/report-ios-app-plan.md（ブランチ checkin/ios-plan、下書き PR）
- 作り方の比べ：今の web（src/index.html）を包む形（Capacitor など）／PWA のまま。そらメモに合うのはどれか、手間と危なさ
- 変える所の一覧：位置情報（使う理由の文・いつ使うか）・プッシュ通知（今の Web Push → APNs）・ログイン（メールの確認コード・Turnstile がアプリの中で動くか）・地図（MapLibre）・バーコード読み取り・オフライン
- App Store の審査で引っかかりそうな所：非公式アプリの書き方・航空会社の名前・データの出典（ODPT・adsb.lol・FAA）・位置情報の使い方・有料（そらメモ＋）の決まり（アプリの中で売るなら Apple の課金になる）・個人登録だと販売元に本名が出ること
- 本人がやること（Xcode を入れる・自分の iPhone で動かすのは無料・ストアに出すには Apple Developer Program 年99米ドル・旅そらの Apple ID か）と順番
- 画面が変わる所があれば、作る前にデザイン担当の画面案

## PM から積んだ次の仕事（11/19 14時05分、半券が指で切れない）→ PR #133 で直した（5e59764・報告 report-tear-finger.md）
- 本人の iPhone で「半券を指で右へ引いても切れない。押すと確かめてから切れるだけ」（#131 の本番）。
- 測った所：半券は幅100pxで画面の右端から16px。iPhone 15・SE・Pro Max のどれも、半券の真ん中から画面の端まで 66px しかない。真ん中より右をつかむと、切れる長さ（TEAR_AT = 56px）に届かない。指の場所の揺れ（縦が先に6px動くと「縦」と決まって切れない）も効いていそう。
- 直すこと：
  1. 切れる長さを、つかんだ所から画面の端までの残りに合わせる（残りの半分、ただし 28〜56px）。
  2. 速く右へはじいたら、短くても切る（目安 0.5px/ms 以上・20px 以上）。
  3. 縦と横を決めるのは 10px 動いてから。横がわずかでも縦の 0.6 倍以上なら横とみなす。
  4. 押すだけの動き（確かめてから切る）は今のまま。
- テスト：e2e に指の操作（CDP の Input.dispatchTouchEvent）で、半券の右寄り（右端から20px）をつかんで端まで引くと切れる・はじくと切れる・縦に動かすと切れない、を足す。
- 画面の見た目は変えない。本番には「反映して」まで入れない。

## PM から積んだ次の仕事（11/19 15時、運用タブを一覧＋専用ページに）→ PR #134 で作った（8f80885・報告 report-ops-hub-app.md）※iPhone のアプリの画面（design/ios-app 2版）のあと。checkin/ops-hub で作る
- design/ops-hub 1版（PR #132、docs/design/ops-hub/）のとおりに作る。本人の決め：機体の検索窓は上に残す（案A）・動きはこの速さ（開く約0.46秒・戻る約0.38秒、prefers-reduced-motion では動きなし）・カードは10枚この並び（並べ替え・隠すは今の lo の仕組みを使う）。
- 今の見方のタブ（滑走路・案内板・1日・定時・航跡アート・ストリップ・撮る人）と「空港｜機体」の切り替えはなくし、それぞれをカードの専用ページへ。中身は今のものをそのまま入れ、説明の文は1行に削る。出典・注意は i の中へ。
- 左端から引いて戻る（iPhone のアプリでもブラウザでも）。戻ったらカードの位置へ縮む。
- テスト：一覧に10枚・各カードを押すと専用ページ・戻る・左端から引いて戻る・字の大きさ13px 以上・はみ出しなし、を e2e に。今の運用のテスト（tests/ops）が通るように直す。
- 本番には「反映して」まで入れない。

## PM から積んだ急ぎの仕事（11/19 22時45分、運用の地図に機体が映っていない）※checkin/ops-hub（PR #134）に足す → PR #134 に足した（92a0a34・報告 report-ops-hub-app.md の追記）
- 本人の声：「機体が映ってないのはなんで？」（shots-ops-hub の一覧と地図の写真）
- 見た所：
  1. 一覧の「地図」カードの絵は決まった絵（ohCardHTML の map の svg）で、機体の印がない。画面案（design/ops-hub H1）は機体の印が地図に乗っている。
  2. 地図の専用ページ（t148_map_844.png）は凡例に「着陸に向かう 5機」とあるのに、地図に機体が1つも出ていない。t148 の作り物の機体（lat 35.60〜35.64・lon 139.8）が「空港のまわり」の範囲の外にいるだけかもしれないが、確かめていない。
- 直すこと：
  1. 地図カードの絵に、今の機体（OPS_PLANES）の位置と向きを小さな飛行機の印で重ねる（多すぎるときは近い順に最大12機）。機体がないときは今の絵だけ。
  2. 地図の専用ページで機体が出ることを確かめる。範囲の外にいるだけなら t148 の作り物の機体を空港の近く（羽田 35.55・139.78 のまわり）に置き直し、機体の印が地図の中に出ることをテストに足す。範囲の中なのに出ないなら直す（専用ページで開いたときに機体の層が描かれているか、invalidateSize のあとに描き直しているか）。
  3. 本番の羽田のデータ（adsb.lol）でも、一覧と地図に機体が出ることを撮って確かめる（本番の Supabase は変えない・読むだけ）。
- 写真を撮り直して報告に足す。本番には「反映して」まで入れない。

## PM から積んだ次の仕事（11/20 1時10分、運用の地図の数をそろえる）※checkin/ops-hub（PR #134）に足す → PR #134 に足した（21180c2・報告 report-ops-hub-app.md の追記2）
- 本人の決め（報告 report-ops-hub-app.md の 5・6 はどちらも「はい」）：
  5. 地図カードの数を、地図に出す機体と同じ「着陸・離陸の機体」の数にする（上空を通るだけの機体は数えない）。
  6. 地図の専用ページの凡例に「この範囲に ○機」を足す。範囲の外に機体がいるときは「ほかの○機は『経路の全体』で見られます」と1行出し、押すと「経路の全体」に切り替える。
- 報告の 1〜4 も PM のおすすめで決めた：1 並べ替えはなし（隠す・出すだけ）／2 遅れのカードは便数のまま／3 専用ページの共有のボタンは残す／4 夜の色は夜の画面が本番に入るときに合わせる。
- テストに足し、写真を撮り直す。本番には「反映して」まで入れない。

## PM から積んだ次の仕事（11/20 1時50分、飛行場・滑空場・ヘリポートの図鑑に種類の絞り込みと県名）※design/zukan-filter の画面案ができてから。checkin/zukan-filter で作る
- 本人の声：「飛行場、滑空場、ヘリポートのフィルター機能、すべてに何県か表示して」。画面案は design/zukan-filter（PM が細かいところを決めて渡す）。
- 県名は XA の pref を使う（表の変更なし）。絞り込みは端末の中に覚える。シークレットは隠したまま。
- テスト：絞り込みで出る数・県名が全部の札に出る・字13px以上・はみ出しなし。本番には「反映して」まで入れない。

## PM から積んだ次の仕事（11/20 1時55分、フライトの「空の上」を実際の飛行時間に・地図に実際の飛行ルート）※データ担当の data/flight-actual のあと。checkin/flight-actual で作る
- 「空の上」（1便ごと・年のまとめ・1行の日記）は act_arr_at − act_dep_at を足す。実際の時刻がない便は今のまま（チェックインの時刻）で、その便の時間に小さく「目安」と付ける。
- 地図：track がある便はその線を描く（今の大圏の線の代わり）。ない便は今の線。
- 見た目はほぼ今のまま（数字が変わるだけ、「目安」の札が増えるだけ）なので、画面案は待たなくてよい。
- テスト：実際の時刻がある便とない便で合計が合う・track の線が描かれる。

## PM から渡す（11/20 2時45分）：図鑑の絞り込みと県名の画面案が決まった → checkin/zukan-filter で作る → PR #138 で作った（07d7cc0・報告 report-zukan-filter-app.md）
- 画面案 design/zukan-filter 1版（PR #135、docs/design/zukan-filter/）の F1・F2・F3 のとおり。PM のおすすめで決めた：
  1. 基地は今のまま別の図鑑（ピルは「すべて・飛行場・滑空場・ヘリポート」の4つ、すべて＝75）
  2. この図鑑に見方の帯「地方別・地図」を足す（F3。地図でも同じピルが効く）
  3. 1つの種類に絞ったときは枠の種類の札を外して県名だけ（F2）
- 県名は全部の枠に13pxの薄いグレー（取っていない所も）。絞り込みは端末に覚える。シークレットは出さない。

## PM から渡す（11/20 2時45分）：フライトの「空の上」と航跡の画面 → checkin/flight-actual で作る（data/flight-actual・PR #136 の列を使う） → PR #139 で作った（7d61b8a・報告 report-flight-actual-app.md）
- 列：flights の act_dep_at・act_arr_at・act_src（'odpt'・'adsb'・'timetable'・空）。select に足す。
- 「空の上」：act_src があれば act_arr_at − act_dep_at、なければ今までどおり arr_at − dep_at。1便の行では act_src が空の便に小さく「目安」。年のまとめで推定（adsb・timetable）や目安を含むときは小さく「（推定を含む）」。呼び名は「空の上」のまま。
- 地図：track があればその線（今の大圏の線の代わり）、なければ今の線。出典は今の「adsb.lol（ODbL）」。
- 見た目はほぼ今のままなので画面案は待たない。テスト：実際の時刻がある便・ない便で合計が合う／「目安」の札／track の線。
- どちらも仕上がったら PM が自動で反映する（3つのテストが前からの失敗だけなら）。

## PM から積んだ次の仕事（11/20 5時30分、図鑑とフライトの小さい直し）※PR #138・#139 は PM が反映中。main を取り込んでから checkin/small-1120 で → PR #141 で作った（c711bfe・報告 report-small-1120.md）
- PM のおすすめで決めた（report-zukan-filter-app・report-flight-actual-app の「決めてほしいこと」）：
  - 図鑑 1：地図の見方の「まだ」の一覧は5行だけ出して「残り○か所 ›」で開く形に畳む
  - 図鑑 2：地図に沖縄・南の島が入らないのは今のまま（下の一覧には出る）
  - フライト 1：実際の時刻がある便は、くわしくの「出発・到着」も実際の時刻にする（チェックインの時刻は小さく残すかは担当の判断、ただし文字を増やしすぎない）
  - フライト 2：1つの区間に航跡が何本もあるときは、いちばん新しい1本のまま
  - フライト 3：出典は「航跡：adsb.lol（ODbL）」のまま
- テストを足す。仕上がったら PM が自動で反映する。

## PM から積んだ次の仕事（11/20 8時5分、日誌の1行と共有の画像も実際の時刻に）※PR #141 は PM が反映中。main を取り込んでから checkin/actual-share で → PR #143 で作った（3051709・報告 report-actual-share.md）
- report-small-1120 の「決めてほしいこと」を PM のおすすめで決めた：日誌の1行の出発時刻と、共有の画像（搭乗券の形）の時刻も、実際の時刻がある便はそれにそろえる。ない便は今までどおり。
- 文字は増やさない（共有の画像にチェックインの時刻は出さない）。テストを足す。仕上がったら PM が自動で反映する。

## PM から積んだ次の仕事（11/20 14時10分、毎回落ちるテストの直し・overlooked-1120.md の D）※checkin/test-fix-1120 で → PR #148 で直した（caf39d0・報告 report-test-fix-1120.md）
- t48・t72・t123 は main でも毎回落ちる（11/16 から）。落ちる理由を調べ、テストが古いだけならテストを今の画面に合わせ、画面が壊れているなら直す
- t147（半券）は全部を並べて流したときだけ落ちる。待ち方を直す
- 修行担当（shugyo.md）への知らせ：年の区切りを日本時間にする直し（候補1）は12月より前に入れる（PM のおすすめで決めた）。修行の持ち場なので、修行担当の帳面に積む

## PM から積んだ次の仕事（11/21 1時10分、adsb.lol の出典をどこでも押せる形に）※checkin/adsb-credit で → PR #150 で作った（0eaee2f・報告 report-adsb-credit.md）
- adsb.lol の返事（11/6）：「よくある間違いは、すぐ見える所に出典がない・押せるリンクがない・自分のデータのように見せる」。
- 画面で adsb.lol のデータを出す所（運用タブの各専用ページ・地図・フライトの航跡・機体のくわしく・海外の便・撮る人）の出典を、全部「<a href="https://adsb.lol">adsb.lol</a>（ODbL）」の押せる形にそろえる（今は文字だけの所がある）。i の中にまとめた所も、データが出ている画面から1回で見えるか確かめる
- 文字は増やさない。テストに「出典のリンクがある」を足す。仕上がったら PM が自動で反映する

## PM から積んだ次の仕事（11/21 4時、空の道すじの上限に合わせる）※data/adsblol-key2（PR #153）とセットで。checkin/track-quota で（#153 を取り込んで作る）
- report-adsblol-key2 の「チェックイン担当への依頼」のとおり：loadArt の airport_tracks と cold-tracks で、ログインしているときは Authorization にログインの鍵を付ける。返り値が login_required なら「8日より前の空の道すじはログインすると見られます」、rate_limited なら「たくさん読んだので、○分ほどあとでまた見られます」。デモと未ログインの日付の選び方は前の7日まで
- 本人 OK 済み（11/21 4時23分）。仕上がったら PM が #153 と一緒に自動で反映する

## PM から積んだ次の仕事（11/21 9時15分、改善担当の見回りの指摘）→ PR #161 で直した（925a8fe・報告 report-checkin-sweep-1121.md）※checkin/sweep-1121 で （report-sweep-1121.md・kaizen/sweep-1121 の指摘。PM のおすすめどおりに直す。仕上がったら PM が自動で反映）
- 1 運用「遅れ」の専用ページが空：カードの数とページの中身をそろえ、空のときは「いま遅れ・欠航の便はありません」の1枚
- 3 ホームの上の段の「マイページ」が2行に折れる：1行に収める
- 4 地図カードが読み込み中に「0機」：読み込み中は「—」、開いたページの数とそろえる
- 8 空港の3D の全体の視点で模型が小さく機体が見えない：初めの寄りを大きく
- 9 11/19〜21 に入った所の 44px 未満を直す
- 5（特別塗装機「見つかっていません」の下に予定が出る）は土台の側だけ。撮る人の側は satsuei.md に積んだ
- 7（運用を開いたときの通信が遅い）は画面の側の待ち方（先に骨組みを出す）を。通信の側はデータ担当
