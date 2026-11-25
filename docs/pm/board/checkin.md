# チェックイン担当の帳面

## いま持っている仕事
- **11/26 手動の回（PM の指示「11/25 23時05分 乗る便の候補から1回で記録 を checkin/flight-suggest で」）**：checkin/flight-suggest・下書き **PR #239**（22b6bbbe・報告 docs/pm/report-flight-suggest.md・写真 docs/pm/shots-flight-suggest/）。main（dfc945cc）から。checkin/stamp-edge には触っていない。見張りを付けた。テストが通れば PM が自動で反映
  - 候補：fsugAirport（今日チェックインした空港→判定範囲の中の空港）・fsugFetch（airport-now を2分覚える・8秒で区切る・電波なしは off）・fsugList（出る便6・着いた便4。欠航・出発済み・国際線を除く）。入口はフライトの「＋」（#fsugBook）と showStamp の「今日の便を記録」（data-fsug-open → シート #dFsug）
  - 記録：fsugPlan → "plan"（savePlan。出る便・まだチェックインしていない到着）・"set"（今日の同じ区間のフライトに set_flight_airline）・"manual"（日誌。mfInsert は flight_no を付けて、列がなければ外して入れ直す）。確認は fsugConfirm、押すのは fsugGo
  - 過去：#mNo（数字だけでも）→ mNoFill（plan_timetable を JAL・ANA で。前日より前の日付は今日の時刻表で推定と書く）→ mNoApply（出発・到着・航空会社を入れ、flight_facts で実際の時刻と機体）。同じ番号は #mNoPick で選ぶ。change の二重を MNO_LAST で止める
  - 便名の読み：数字だけの「509」を「50」＋「9」と読まないよう、航空会社の2文字は英字を1つ含む形（[A-Z][A-Z0-9]|[0-9][A-Z]）
  - jstDay は前からある関数（12351 行あたり）を使う（重ねて宣言すると組み立てが止まる）
  - テスト：t197 を足した（run_all の上限 600）。fake_sb.js に __mfNoCol。e2e 全部・tests/ops 成功（t195 は同時に流すと 100ms を少し超えることがあり、main の版でも同じ）
  - 本人（PM）に聞くこと：出る便は乗る便として覚えるだけ（その場で日誌にしない）でよいか・札の色・JAL・ANA だけ・デザイン担当／改善担当の見直しを通すか
- 【11/25 23時台 手動の回（同じ「電波・位置が悪いときの続き を checkin/stamp-edge で」の指示）】仕事は PR #238（9eb14811）で済んでいたので作り直さなかった。#233（小さな動き）が main に入って #238 の web/ がぶつかっていたので、main（dfc945cc）を取り込み web/ だけ作り直した（809776a6。src はぶつからなかった）。t196・t24・t146・t194・t145・t183・t11・t13 成功、t195 は1本で成功（同時に流すと長い処理 258ms）。札は toast と mxToast の2つのまま（重ねない2行は main に入っていない）
- 【11/25 23時台】PR #226 は閉じられた（中身の12個は #233 で main に入った）。見張りは外れた。「2つの札を重ねない」（toast と mxToast・ブランチ checkin/micro の 85a7ec37）は main に入っていない。PM が要ると言えば main から新しいブランチで2行を入れ直す
- **11/25 22時台の定時の回（同じ「電波・位置が悪いときの続き」・重なった）**：始めたときは origin に checkin/stamp-edge がなかったが、作っている間に別の回が PR #238 を出していた。押そうとして気づいたので、こちらは **checkin/stamp-edge-b**（dbeb1cdd・報告 docs/pm/report-stamp-edge-b.md・写真 docs/pm/shots-stamp-edge/）に別案として置いた。**PR は出していない**。PM が #238 を選べば消してよい
  - #238 との主な違い：大まかな位置のカードに「もう一度位置を確かめる」（取り直すだけ）と設定から戻ったときの自動の取り直し・ホームの静かな見張り（精度を下げた位置）ではカードを出さない・札は半券のすぐ下（#qPills）・送れず保存の札は 3.5 秒・範囲の外は誤差 300m 超で「建物の中」を添える
  - テスト：t196（別案の版）・t195・t146 を合わせた。e2e 全部（t168 以外）と tests/ops 成功
  - 本人（PM）に聞くこと（報告の5つ）：カードが出るまで10秒（位置の取り方を変えないため）・「本日のチェックインは完了」と30分の決まり・1km の線・Safari の道順・375 でカードが長い
- **11/26 0時台の定時の回（帳面に積まれた 11/25 23時「電波・位置が悪いときの続き」）**：checkin/stamp-edge・下書き **PR #238**（9eb14811・報告 docs/pm/report-stamp-edge.md・写真 docs/pm/shots-stamp-edge/）。main（4844f048・stamp-fast 入り）から。見張りを付けた。テストが通れば PM が自動で反映
  - 1 正確な位置情報 OFF（iPhone で誤差 1km 以上）→ ckLocCard("precise")：道順つきのカード・送らない・ハンコなし・ボタンは「閉じる」だけ。ウェブで許可がない → ckLocCard("denied")＋ nvGeoApply をウェブにも（CK_GEO_NG。半券の代わりのカード・「デモで試す」だけ。設定から戻って許可なら戻す）
  - 2 送信待ち：loadServer の最後に qMerge（端末の判定で通る見込みの分だけ S.checkins に pending・queued で足す）。renderQueue は札（qTagHTML「羽田空港 送信待ち（14:22 記録）」）、図鑑は qTagsFor と記録の行の「送信待ち」。札は data-flush で送り直し。enqueue(p, why, ok) に変えた（ok:false は範囲の外などで、送るまで印にしない）
  - 3 flushQueue で送れたら toast「羽田空港の印が確定しました」（2件以上は「など○件」）
  - 4 文は CK_TXT・ckWhyText（サーバーの理由→文）・ckOutText（範囲の外。誤差が残りより大きければずれの文）。stale_position（保留でない）は時計のずれ。英字のエラーは CK_TXT.server
  - 変えた関数：checkinRun・checkinDecide・checkinServer・ckSend・checkinServerWait・enqueue・renderQueue・flushQueue・loadServer・openAirport・nvGeoApply（足した関数は報告に）
  - テスト：t196 を足した（単独で約100秒・run_all の上限 600）。文を変えたので t195・t144 を合わせた。e2e 全部・tests/ops 成功（手元だけの t168・t166・t190 を除く。t195 は4本同時だと長い処理 155ms で落ち、1本なら成功）
  - 本人（PM）に聞くこと：正確な位置の見分け（誤差 1km 以上・10秒待ってから。早くするなら位置の取り方を変える）・「本日のチェックインは完了」と30分の決まりのずれ・ずれの文に足した1文・送信待ちの帯の点線のふち
- 11/25 22時台（PR #226 の見張り）：#233（release-1125e）で #226 の最初の版（763673a1）と修行の #224 が main に入った。あとから足した「2つの札を重ねない」（85a7ec37）はまだ main にないので、main（dfc945cc）を取り込み web/ を作り直した（4e4fdcb7）。#226 に残る差は src の2行と web/ だけ。t194・t195・t198・t24・t77・t145 成功。PM が残りを入れるか #226 を閉じるかを決める
- 11/25 21時台（PR #226 の見張り）：#231（stamp-fast）が main に入って #226 がぶつかった → main（4844f048）を取り込み、web/ を作り直した（85a7ec37。src はぶつからなかった）。stamp-fast の札 toast()（#smToast）と小さな動きの札 mxToast が重ならないよう、出すときにもう片方を下げるようにした。t194・t195・t24・t145・t183・t184・t167・t120・t123 成功。PR がぶつかりなしなので見張りの予約は入れていない（次の GitHub の知らせで戻る）
- 11/25 手動の回（同じ「stamp-fast を checkin/stamp-fast で」の指示）：直前の回で PR #229（987f3b04）として済み。main も 4354656c のままで取り込み済みなので作り直さなかった。checkin/micro には触っていない。PM の反映を待つ
- **11/25 18時台の定時の回（帳面に積まれた 11/25 17時45分の最優先「印を押すときに待たせない」）**：checkin/stamp-fast・下書き **PR #229**（987f3b04・報告 docs/pm/report-stamp-fast.md・写真 docs/pm/shots-stamp-fast/）。main（4354656c）から。見張りを付けた。テストが通れば PM がすぐ反映
  - 端末の判定（ckJudge。judge.ts と同じ順・数字）で通る見込みなら先にハンコ（ckOptimistic）、送るのは後ろで1つずつ（ckSend・CK_CHAIN）。届かない→今の保留＋札「電波が戻ったら、あとで送ります」。断られた→ハンコを閉じて仮の印を取り消し理由を出す。範囲の外・誤差が大きいは今までどおり待つ（checkinServerWait）
  - 位置：recentPos（30秒・50m・範囲の中）・半券の pointerdown と確かめの画面で geoWarmIfGranted・getPos は3秒で誤差300m以内なら確定・10秒で区切る（FRESH）。0.3秒すぎから「位置を確かめています…」
  - 描き直しは ckLater で分けて。便のボタンは番号が来るまで押せない（ckFlightBtn）。二重押しは CK_BUSY
  - 数字（CPU 4倍遅く）：遅い電波 6,444→385ms・屋内120m 約12秒→3.1秒・直近の位置 438→100ms・長い止まり 113〜134→60〜76ms
  - テスト：t195 を足した（checkin/micro が t194 を使うため）。t24 を合わせた。計測の道具 tests/e2e/stamp_perf.py。fake_sb.js に __netDelay・__fnFail・__mkFlight
  - 本人（PM）に聞くこと：先にハンコ→断られたら取り消すでよいか・直近の位置の使い回し（10月の「押す前の位置は使わない」を変える）・屋内3秒300m・保留の印が端末の上で見えること
- 11/25 手動の回（同じ「小さな動き13個を checkin/micro で」の指示）：直前の回で PR #226（763673a1）として済み。main も 4354656c のままで取り込み済みなので作り直さなかった。PM の自動の反映を待つ
- **11/25 17時台の定時の回（帳面に積まれた 11/25 17時25分「小さな動き13個」）**：checkin/micro・下書き **PR #226**（763673a1・報告 docs/pm/report-micro-app.md・写真 docs/pm/shots-micro/）。main（4354656c）から。見張りを付けた。テストが通れば PM が自動で反映
  - 入れた：01・02・03・04・05・06・07・09・10・11・12・13。08 は修行担当が PR #224（shugyo-micro-bar）で作り済みなので触っていない
  - 作り：style の最後に「小さな動き」の CSS、script の最後に「小さな動き」の JS。01 は scale（transform とぶつけない）。05 は say・uiSay（運用）で最初の文が「〜ました」だけを札（mxToast）に、#msg の字は見た目だけ隠して読み上げ用に残す。ピンの帯も下から出す（translate で。transform にすると帯が横にずれて t145 が落ちた）
  - 10 の部品 mxCopyHTML は「この便の記録」の登録記号だけに付けた。11 の部品 mxBell はピンの「通知を許可する」だけ（撮る人用の .spbell は依頼にした）
  - 変えた関数：say・uiSay・render（今日の数字）・pinAdd・showFacts・opsFailHTML・roBind・タブを選ぶシートの並べ替え・「もう一度」の処理・遅れのページの読み込み中・ピン止めの「通知を許可する」。足した：mxRM・mxDone・mxToast・mxDot・mxPinGo・mxSkel・mxNums・mxFlip・mxCopyHTML・mxBell・mxRetrySvg・mxSpin・mxRetryBox
  - render から先に呼ばれるので、script の最後の変数は var か function にする（let にすると最初の表示で止まった）
  - テスト：t194 を足した。e2e 全部・tests/ops 成功（3D の5本は t142 と同じ作業用フォルダで）
  - 本人（PM）に聞くこと：札にする知らせの決め方・コピーをほかにも付けるか・ホームの札が半券の下の端に少しかかる
- 【11/25 16時42分】PR #219（元日の印を外す）は main に入った。本人の答え（分類の名前「時間帯」か「時間」）が来たら main から新しいブランチで直す
- 【11/25 16時42分】PR #221（t30 の直し）は main に入った。見張りは外れた
- 11/25 手動の回（同じ「t30 を checkin/t30-fix で」の指示）：直前の回で PR #221（242a214b）として済み。main も 663576a8 のままで取り込み済みなので作り直さなかった。drop-newyear には触っていない。PM の自動の反映を待つ
- **11/25 14時台の定時の回（帳面に積まれた 11/25 15時の急ぎ「t30 が main で落ちる」）**：checkin/t30-fix・下書き **PR #221**（c4f4c7d8・報告 docs/pm/report-t30-fix.md・写真 docs/pm/shots-t30-fix/）。main（c5a008e5）から作り、#215 が入った main を取り込んで web/ を作り直した（t30・t193・t142・t190・t189・t163 成功）。見張りを付けた。テストが通れば PM が自動で反映
  - 原因はアプリの不具合：ダイアログの close の知らせはあとから届くので、close() のすぐあとに openMyPage("adv") で開き直すと、届いた知らせで mpPage(null)（目次）に戻り、デモの「開始」が隠れていた。戻る操作の積み（CX_STACK）からも外れていた（#213 の形、#218 のあと毎回出るようになった）
  - 変えた所：dSettings の close の受け手（開いていれば目次に戻さない）・showModal の包みの close の受け手（開いていれば cxPop しない）。見た目は変えていない
  - テスト：t193 を足した（t192 は #219 が使うので飛ばした）。t30・t193 各4回、t189・t183・t163・t120・t123・t118・t119・t124・t145・t184・t73・t47・t54・t57 成功
- 11/25 13時台（PR #219 の見張り）：#220（a3-free の取り込み）が main に入って #219 がぶつかった → main（663576a8）を取り込み、web/ だけ作り直した（af06fc21。src はぶつからなかった）。t192・t182・t17・t141・t145・t118・t119・t124・t142・t190 成功
- 11/25 13時50分ごろ：PR #215（羽田の3D を自由に動かす）は main に入った。本番への反映は PM／本人の判断。本人の答え（展望デッキの位置・1本指・飛ぶの速さ・iPhone での重さ）が来たら main から新しいブランチで直す
- 11/25 手動の回（同じ「元日の印を外す を checkin/drop-newyear で」の指示）：直前の回で PR #219（7a39dcb9）として済み。main も c5a008e5 のままで取り込み済みなので作り直さなかった。3D には触っていない。PM の自動の反映を待つ
- **11/25 13時台の定時の回（PM の指示なし。帳面に積まれた 11/25 13時「元日の印を外す」を進めた）**：checkin/drop-newyear・下書き **PR #219**（7a39dcb9・報告 docs/pm/report-drop-newyear.md・写真 docs/pm/shots-drop-newyear/）。main（c5a008e5）から。見張りを付けた。テストが通れば PM が自動で反映
  - 実績の「元日の印」（ny）と timeMarks の「元日の印」を外した。分類「時間と季節」は「時間帯」に（中身は朝の印・早起きの旅人・夜の印・夜ふかしの旅人）。achState の newyear の数えを外した
  - 変えた関数・表：timeMarks・ACH・achState。経営の行事「年末年始ボーナス」（newyear-2027）は経営の持ち分なので触っていない
  - テスト：t192 を足した。t17 の id から ny を外した。run_all で t192・t182・t17・t141・t145・t118・t119・t124・t15・t16・t34・t37・t41・t52・t70・t47・t120 成功
  - 本人（PM）に聞くこと：分類の名前は「時間帯」でよいか（指示の例は「時間」。変えるなら ACH の4行の1語だけ）
- 11/25 8時台（PR #215 の見張り）：#218（sweep-1125・特別塗装機の知らせ）が main に入って #215 がぶつかった → main（c5a008e5）を取り込み、web/ だけ作り直した（f9d0e77c。src はぶつからなかった）。t190・t160・t142・t159・t181・t191・t163・t161 成功
- 【11/25 8時16分】PR #217（見直し2回目の直し）は main に入った。本人の答え（長い名前の行数・帯の背景の範囲）が来たら main から新しいブランチで直す
- 11/25 手動の回（同じ「見直し 2回目から を checkin/sweep-1125 で」の指示）：直前の回で PR #217（4d874c69）として済み。main も 04d22af8 のままで取り込み済みなので作り直さなかった。PM の自動の反映を待つ
- **11/25 定時の回（PM の指示なし。帳面に積まれた 11/25 5時10分「見直し 2回目から」を進めた）**：checkin/sweep-1125・下書き **PR #217**（4d874c69・報告 docs/pm/report-sweep-1125-checkin.md・写真 docs/pm/shots-sweep-1125/）。見張りを付けた。テストが通れば PM が自動で反映
  - 1 成績の空の上を fbMin の合計に（書き方は fbDurTxt「49時間20分」・札は「推定を含む」を fbSum と同じ決め方）。passCard も
  - 3 遅れのページ：ltJump は開く動き（OH_BUSY・ohup）が終わってから送り、1こま後に合わせ直す。10行未満は送らない。opsStuck で #v-ops に data-stuck → 帯に背景（専用ページすべて）
  - 5 ZK_OLD_VIEW は view.book が tiles・signs・chron か、並べ替えに tiles・signs がある人だけ。ZK_NOTICE_END（2027-01-01）から出さない
  - 6 fbMapHTML：flyRts（乗った区間）と carRts（車など・ul に data-fbcar）
  - 7 飛行場の図鑑：.zx-nm は 15px・keep-all・2行（8字以上は .long で3行まで）。zkxBreak に言葉の切れ目の <wbr> を足した。扉の札（zx-dtag）は外した
  - 9 nvNetRender はウェブでもホームの帯だけ出す（「送っていない印 ○」）。renderQueue から呼ぶ
  - 変えた関数：passStats・renderPassport・passCard・ltJump・opsHubApply・zkxTile・zkxBreak・zkAirBookHTML・fbMapHTML・nvNetRender・renderQueue・ZK_OLD_VIEW（足した：opsStuck・ZK_NOTICE_END）
  - テスト：t191 を足した。t127・t146・t149・t184 を合わせた
  - 本人（PM）に聞くこと：長い名前2つの3行でよいか（2行優先なら長い名前だけ 13px）・帯の背景を全部の専用ページにしてよいか
- 11/24 20時台の手動の回（同じ「a3-free を案B＋管制塔のピルで」の指示）：前の回で PR #215 として済み、main も 04d22af8 のままなので作り直さなかった。足りなかった今の本番との比べの写真（before-all／before-tower／before-plane・390×844 と 375×667）だけを #215 に足した（0bf242dc）
- **11/24 19時台の定時の回（PM の指示なし。帳面に積まれた 11/25 3時20分の「羽田の3D を自由に動かす」を始めた）**：checkin/a3-free・下書き **PR #215**（856d8a2a・報告 docs/pm/report-a3-free.md・写真 docs/pm/shots-a3-free/）。見張りを付けた。本番は本人が写真を見て OK してから
  - 下の4つのボタン（自由・追う・立つ・飛ぶ）＋上のピル（全体・管制塔・機体）は近道。A3.view は前の名前のまま（all＝自由・tower＝管制塔に立つ・plane＝追う、足したのは stand・fly）。追う・立つ・飛ぶではシートを畳む（見出しで開く）
  - 自由：A3.orb（tx・tz・d・p）と A3.yaw。はじめは前の「全体」と同じ。限り A3_LIM（見る点 6km・距離 200〜16,000m・角 6〜88°）。寄ったら機体の大きさの5倍を外していく
  - 立つ：A3_SPOTS。展望デッキは3D の屋上の端で見通しのよい所を探して決めた（T1 は (160,560)・T2 は (720,160) の m）。押した所が屋上なら a3BldH で見る向きの屋上の端まで出る。目の高さのときカメラの near を 1.5 に
  - 飛ぶ：A3.fl・A3.fin。高いほど速い・15〜1,000m・8km
  - 追う：A3.fside（後ろ・横・前）・A3.fk（距離）・A3.fup。1.5秒届かなければ a3Lose で今の位置のまま自由へ
  - 案内は localStorage の soramemo_a3_guide。自動のテスト（webdriver）では window.A3_GUIDE を立てたときだけ出す
  - 変えた関数：a3ShellHTML・a3Status・a3Drag・a3Tap・a3Loop・a3Sync・a3Camera・a3Labels・a3ViewOffset・a3Sheet（中身は a3SheetIn）・a3Select・a3Pills・openAp3d・クリックの処理。足した関数は報告に
  - テスト：t190 を足した。t142・t148・t154・t159・t160〜t168・t181・t184・tests/ops 成功
  - 本人（PM）に聞くこと：展望デッキの位置・自由の1本指は回すだけでよいか・飛ぶの速さ・iPhone での指の操作と重さ
  - 手元の注意：classList.toggle の2つめに undefined を渡すと反転する（!! を付ける）。a3Camera は t159 の作り物のカメラでも呼ばれる（updateProjectionMatrix がない）
- 【11/24 19時台】PR #211（マイページ案B）は #213 で main に入った。#203 も閉じられた
- 11/24 18時台（PR #203 の見張り）：a3-hq の中身（7cde7a3f まで）は PM の #212（release-1124f）で main に入った。#203 に main を取り込み直した。残る差は報告 report-a3-hq-t168.md の追記4行だけ（PM が入れるか閉じるか）。本人の答え（iPhone の重さ・汚れ・映り込みの絵）が来たら main から新しいブランチで直す
- 11/24 手動の回（同じ「その4 を checkin/mypage-b で」の指示）：直前の回で PR #211（889f484f）として済み。main も f7168964（#210）のままで取り込み済みなので作り直さなかった。PM の自動の反映を待つ
- **11/24 17時台の定時の回（PM の指示なし。帳面の「その4」＝その3 を含む。main に sweep-all-1・2・data/sweep-all が入っていた（#210・f7168964）ので始めた）**：checkin/mypage-b・下書き **PR #211**（889f484f・報告 docs/pm/report-mypage-b.md・写真 docs/pm/shots-mypage-b/）。見張りを付けた。テストが通ったので PM の自動の反映でよい
  - マイページ案B：成績を横長の1枚（空港・便・km・車などの1行）＋修行（今のポイント・目標まで ○%）・知らせ（○ / 12 空港）。図鑑・フライト・運用はタブから外したときだけタイル。設定は5行の目次→同じダイアログの中の1枚のページ（data-mp-page。戻るは「マイページ」。中の行と id は今のまま）。データとバックアップの頭に箱・書き出しの説明は短く。デモ・サーバーなしのアカウントのページに1行（acctLocal）。openMyPage(page) でページを開いた形にできる（テストもこれを使う）
  - その3：成績のステータスの目安・修行のまとめ・修行の計画・この路線に乗ったらを外し、入口1枚（stats:status・#stSg）＋あの日の空の行（stats:thatday）。かたまりは5つのまま。気軽に・撮影は入口を隠す（前は修行のまとめを隠していた）。renderStatus・planHTML・renderSgSum は呼ばないだけで残した
  - ピン止め：pinsPull（reload の後）・pinsUp（0.3秒まとめて my_pins_put・rev つき）・pinsFromSrv（conflict と行があるとき）。関数がないサーバーでは端末だけ。「機種を変えると消えます」「準備中」は外した
  - 変えた関数：openMyPage・renderMyPage・renderStats・renderPersonaSettings・pinsSave・pinRedraw・pinDeliverHTML・pinListHTML・reload（表：LO_BLOCKS.stats・PERSONAS・HS）。足した：MP_PAGES・MP_IC・MP_GO・MP_PAGE・mpPage・mpSgNow・mpStats・mpTilesHTML・mpTabNote・mpIdxHTML・renderStSg・PIN_SRV・pinsAcct・pinsClean・pinsSpotNow・pinsUpLater・pinsFromSrv・pinsUp・pinsPull
  - テスト：t189 を足した（fake_sb.js に my_pins／my_pins_put。window.__pinRpc で出す）。前のテスト35本を合わせた（中の行は openMyPage("adv") などでページを開いてから・#dSettings .mp-back で閉じていた所は close()・t47／t51／t54／t57 は #statusBox を足して renderStatus を確かめる・t73 は入口に）。e2e 49本・tests/ops 成功
  - 本人（PM）に聞くこと：気軽に・撮影で成績の修行の入口も隠してよいか・renderStatus／planHTML／renderSgSum を消すか・運用のタイルは「HND の今」だけでよいか
  - 手元の注意：tests/ops は node_modules の playwright 1.56.1 だとブラウザが合わない。node_modules を消し、npm root -g の playwright をリンクすると通る
- 11/24 17時台（PR #203 の見張り）：#210 が main に入って #203 がぶつかった → main（f7168964）を取り込み、ぶつかった web/ だけ作り直した（7cde7a3f・報告に追記 7212c44b）。t142・t16・t160〜t168・t181・t183・t184 の14本と tests/ops 成功。#207・#209（sweep-all-1・2）は #210 で main に入った見込み
- 【11/24 17時22分】PR #207（その1・sweep-all-1）は main に入った。次の回は「その3」（checkin/stats-shugyo-card）を main から始めてよい（始める前に origin のブランチを見る）
- 11/24 手動の回（同じ「t168 の直しを checkin/a3-hq で」の指示）：直前の回で 111c901e として済み（PR #203 の先頭のまま・main も dad55b43 のまま取り込み済み）なので作り直さなかった。sweep-all-1・sweep-all-2 には触っていない
- **11/24 16時台の定時の回（PM 16時の急ぎ「a3-hq を main と合わせると t168 が1件落ちる」）**：checkin/a3-hq（PR #203）に main（#201・#204 まで）を取り込み（72383db3）、テストを直して足した（**111c901e**・報告 docs/pm/report-a3-hq-t168.md）。見張りを付けた。直ったので PM の自動の反映でよい（本人 OK 済み）
  - 原因はテスト：a3Loop は「距離（a3Sync）→ カメラ（a3Camera）」の順なので、視点を変えた最初のコマは前の視点（全体＝約10km 先）の距離。遅い手元では 1.2 秒で1コマも描けず near が空（`{}`）。1コマも描かずに読むと同じ形（最短 10,471m）を再現。アプリは次のコマで正しくなるので変えていない（src・web は変えていない）
  - t168：frames() を足し、view() は2コマ描くまで待つ。0機のときはカメラの位置と近い順を出す。run_all.py：t168 だけ上限 1,800 秒（LIMIT の表）、上限を超えても止まらず失敗として進む
  - 確かめ：run_all.py で t142・t16・t160〜t168・t181 の12本成功（t168 は単独約7.5分）・tests/ops 成功
- **11/24 15時台の手動の回（PM「その2 を checkin/sweep-all-2 で」）**：checkin/sweep-all-2・下書き **PR #209**（bb226c2a・報告 docs/pm/report-sweep-all-2.md・写真 docs/pm/shots-sweep-all-2/）。見張りを付けた。テストが通ったので PM の自動の反映でよい
  - B2 案内板が読めないと遅れ・短冊・撮る人に「読み込めませんでした・もう一度」（10秒ほどで1回だけ自動で取り直す）／A補 引き上げると最近の印まで送る・近くの一覧は「ほか○つ」のときだけ／B3 カードに範囲の札（定時は専用ページと同じ30日）・特別塗装機のページは空と地上を分ける／B4「34R（C）へ」・短冊の説明・「日誌に追加」・日誌の札「手で記録」・「空の上（推定）」／B5 決め打ちの向きのとき滑走路のカード「—」・電波がないときの帯／B6 遅れは今の時刻の行へ（「いまごろ」）／B7 知らせの言い方・「乗る便を選ぶ ›」／B9 字13px・押せる所44px
  - 変えた関数：loadBoard・renderBoard・opsLateHTML・renderOpsLate・ltListHTML・ohCardHTML・opsHubRender・renderOps・specialHTML・opsFlying・renderOpsDerived・a3Rwy・a3State・initSheet の go・nearMoreSync・pinListHTML・renderPassport・passCard。足した：BOARD_ERR・BOARD_RETRY・OPS_FAIL_WAIT・opsFailHTML・opsBoardFail・ltJump・spAir・OH_OT_ASK・ohLastSave・ohNetHTML
  - テスト：t184 を足した・t142（3D の滑走路の形）と t60（「日誌」の文）を合わせた。関係のある e2e 36本と tests/ops 成功
  - #207（その1）とぶつかるのは renderPassport の「空の上（推定）」の1行だけの見込み（#207 が先に入ったら取り込み直す）
  - 本人（PM）に聞くこと：「記録帳」の言葉を修行・ログイン前の引き継ぎの文まで全部そろえるか
  - 撮る人用への依頼：撮る人の上の札（南風運用・逆光・雲底）の高さ44・字13px（見直し B の9。renderPhoto は撮る人用の持ち場なので変えていない）→ satsuei.md には書いていない（ほかの帳面は変えない決まり）。PM から渡してほしい
- **11/24 15時台のもう1つの定時の回（PM の指示なし。帳面の「その1」を始めた）**：手元で同じ「その1」を作り終えて push しようとしたら、別の回が2分先に PR #207 で出していたので、こちらの版（手元のみ・aca4dca3）は push せず #207 に任せた。#207 に無かった所だけを **#207 に足した（49726687）**：
  - 成績の「航空会社別」（renderAirlines）が車などを「航空会社が未記録のフライト 1便あります」と出していた（デモでも出る）→ flyOnly で数える。使い方の勧め（personaSuggestion）の「この90日で○便」も車などを入れない
  - t183 に航空会社別の確かめを足した。t183・tests/ops 成功。報告 report-sweep-all-1.md に追記
  - renderYears・renderOverall も車などを数えるが、置き場（yrTabs・overallBox）が画面に無く使われていないので変えていない（消してよいかは PM へ）
  - 手元の注意：run_all.py の名前の指定は前方一致（t11 で t110〜t119 も流れる）。e2e を流すと docs/pm/shots-* の前の写真18枚ほどが上書きされるので、コミットの前に `git diff --name-only | grep '^docs/pm/shots-' | xargs git checkout --` で戻す。t48 は pdf417gen・segno が要る
- 11/24 手動の回（PM「その1 を checkin/sweep-all-1 で」）：PR #207（82b0084e）で済みで、main も dad55b43 のまま動いていないので作り直さなかった。その2・3D には触っていない
- **11/24 15時台の定時の回（帳面の「その1」。checkin/sweep-all-1）**：下書き **PR #207**（ad3ed46e＋main 取り込み 82b0084e・報告 docs/pm/report-sweep-all-1.md・写真 docs/pm/shots-sweep-all-1/）。見張りを付けた。テストが通っているので PM の自動の反映でよい
  - A1 マイページの頭の札・成績のパスポート（これまで・年ごと・共有画像）は flyOnly で数える（車など・記録帳の便を外し「記録帳の便 ○・車など ○（○ km）は…別に数えています」の1行）。A2 書き出しの説明は PM の決定①（ログイン中）＋ログインしていない人・デモ・サーバーなしの文、見出し「データとバックアップ」。A5 デモの見本の最後の便を昨日に（日の単位でずらす・demoClock は null・demoNow は今より前にしない）。A6 同意の画面はチェックとボタンを下に固定（#auFoot を sticky、dAuth に data-step）。A7 補足の字 #9CA3AF→#646B78（auth の --a-sub・mypage の --mp-sub）。A8 案内の3枚目は「はじめる」1つ＋運用と修行の一文。A9 44px（resend のピル・あとで・色の丸・規約のリンク）。A10 cardBase に「非公式アプリ」。B10 .brand と案内の HND をゴシック（経営の明朝体は触らない。SVG の font-family 属性に var() は効かないので style にした）
  - 変えた関数：passStats・renderPassport・renderMyPage・demoSeed・demoNow・authRender・obShow・cardBase
  - テスト：t183 を足した。t8・t11・t13・t15・t17・t21・t30・t31・t36・t37・t45・t47・t48・t49・t52・t73・t74・t110・t114・t116・t123・t126・t129・t130・t141・t144・t145・t147・t170・t182・tests/ops 成功
  - 本人（PM）に聞くこと：ログインしていない人とデモの書き出しの文・記録帳だけの年がパスポートで 0 になること・デモで「次の空港で…」の帯が時刻によっては出ること
- **11/24 PM の手動の指示（「3D の機体を容量を気にせず最高の質に」を checkin/a3-hq で）**：checkin/a3-hq・下書き **PR #203**（c2ee8c56・報告 docs/pm/report-a3-hq.md・写真 docs/pm/shots-a3-hq/）。見張りを付けた。本番は本人が前後の写真を見て OK してから
  - 質3（最高）をはじめの質に（a3Weak は質1・軽いは質0 のまま）。重いと今までどおり質2 に自動で下げ、仕上げをやめて前の細かさで作り直す（a3Quality）
  - #191 の細かい形・4096 の絵・上塗り・影 4096 を移し、737 のスプリットシミタール・手で作る汚れの絵・昼の映り込み（Poly Haven「Abandoned Parking」CC0・web/3d/env-day.jpg 約86KB）・MSAA 4・SSAO・bloom を足した（three.js の追加の部品は読まない）。細かい形は全部の機体、3km より遠い地上だけ平らな形のまま
  - 入口の字は「約0.7MB」。最高の質の昼は映り込みの絵を読むまで「読み込み中」（最大6秒）
  - 変えた関数：openAp3d・a3Build・a3Loop・a3Quality・a3LightMat・a3HdTex・a3HdGeo・a3HdMats・a3HdMesh・a3Loft・a3Sync。足した：A3_MAX（変数）・a3HdNear・a3PostInit・a3PostResize・a3PostPass・a3PostRender・a3PostOff・A3_FSV・a3EnvDay・a3EachHdMat・A3_ENV_DAY・a3HdWingTex
  - 測った数：1コマ約3.2倍（ソフトの描画）・GPU のメモリ iPhone で約350MB の見込み・届く量 +86KB（開いたとき）・本体 +4.3KB
  - テスト：t168 を最高の質に合わせて確かめを足した（写真は shots-a3-hq に png で出る。コミットしたのは jpg に縮めた cmp だけ）。t142・t160・t161 を合わせた。t142・t160〜t168・t181・tests/ops 成功
  - 本人に聞くこと：iPhone での重さ（質3 のままか・すぐ質2 に下がるか・Safari が読み込み直さないか）・汚れの濃さ・映り込みの絵を使ってよいか（角の出典に Poly Haven を足すか）
- 11/24 手動の回（PM「季節の印を checkin/drop-season-marks で」）：PR #200（0975a67f）で済みで、main も ee7eca61 のままなので作り直さなかった。#200 に紛れていた図鑑の写真18枚（shots-zukan-book・shots-zukan-facts）は main のものに戻すコミットを足した。**#200 の差分は季節の印の中身だけ（src・web・t17・t182・報告・写真3枚）**。テストは通っているので、PM の自動の反映でよい。13時台の回の版は checkin/drop-season-marks-b に置いてある（PR なし。違いは見出し「時間と日付」だけ。#200 が入れば消してよい）
- **11/24 13時台の定時の回（PM の指示なし。帳面の「季節の印を外す」を始めた）**：別の回（12時台の回）が2分先に同じ仕事を PR #200（checkin/drop-season-marks・0975a67f）で出していたので、こちらの版（手元の 690389fc）は push せず #200 に任せた。中身はほぼ同じ。違いは2つ（PM へ）：
  - こちらは実績の見出し「時間と季節」を「時間と日付」に変えた（#200 は「時間と季節」のまま・本人に聞く形）。見出しを変えるなら ACH の5行（morn1・morn10・night1・night10・ny）の1語だけ
  - **#200 には図鑑の写真18枚（docs/pm/shots-zukan-book/・shots-zukan-facts/）の書き換えが紛れている**（e2e を流すと前の写真を上書きするため）。入れる前にその18枚を main に戻すとよい（git checkout origin/main -- docs/pm/shots-zukan-book docs/pm/shots-zukan-facts）
  - こちらで確かめたこと：同じ形の t182 が main の web では10件落ち、直した web では全部成功。e2e 25本（t7・8・11・13・15・16・17・19・21・30・34・36・37・41・45・49・52・70・120・121・127・145・163・170・182）と tests/ops 成功。t7・t30・t41・t45・t127・t145・t170 は run_all.py 経由（index_server_test.html と config.js が要る）で流すこと
  - そのあと a3-hq を始めようとして checkin/a3-hq を目印に push したが、#191 の移植（約250行）＋SSAO・bloom・環境の絵の規約の確認・前後の写真と fps の測定まで要り、この回の残りでは中途半端になるので手を止めた。**checkin/a3-hq は中身なし（main ee7eca61 と同じ）。消そうとしたが権限で消せなかった。次の回はこのブランチで始めてよい（ほかの回が動いているのではない）**
- **11/24 12時台の定時の回（PM の指示なし。帳面の 11/24 12時25分の積み「季節の印を外す」）**：checkin/drop-season-marks・下書き **PR #200**（0975a67f・報告 docs/pm/report-drop-season-marks.md・写真 docs/pm/shots-drop-season-marks/）。見張りを付けた。テストが通ったので PM の自動の反映でよい
  - 外した：印の画面の「○の訪問」「四季がそろった」・空港の詳しい画面の春夏秋冬の札・実績 season1／season10 と fourSeason の数え。称号に選んでいた人にも出ない。残した：振り返りの季節ごとの回数（yearStats・renderYearPlus）
  - 変えた関数：showStamp・openAirport・achState（ACH の表から2行）
  - テスト：t182 を足した・t17 から season1 を外した。t15・16・17・19・34・37・41・52・70・120・121・141・145 と tests/ops 成功（t41・t141・t145 は作業用フォルダに index_server_test.html と config.js が要る＝run_all.py が置くもの）
  - 本人に聞くこと：実績の分類名「時間と季節」を「時間」に変えるか
- 11/24 の始めに見たとき：PR #198（sweep-1124）は #199 で main に入っていた（main ee7eca61）
- 11/24 手動の回（同じ「sweep-1124 を checkin/sweep-1124 で。管制塔の屋根を最初に・3D の前後の写真」の指示）：直前の回で PR #198（480346b9）として済み（管制塔の前後の写真は docs/pm/shots-sweep-1124/02-*）。main も 32ea294f のままなので作り直さなかった
- **11/24 定時の回（PM の指示なし。帳面の 11/24 4時15分の積み「見回り sweep-1124」を始めた）**：checkin/sweep-1124・下書き **PR #198**（480346b9・報告 docs/pm/report-sweep-1124-checkin.md・写真 docs/pm/shots-sweep-1124/）。この回の会話で見張りを付けた。テストが通ったので PM の自動の反映でよい
  - 2 管制塔：目を塔の上（約118m）・管制室の外（前へ40m）へ。建物だけカメラの前 420m より手前を切る（A3_TOWER_CUT。地面・機体・灯りは切らない。全体・機体の視点では何も切らない向きに面を置く。面は材質にはじめに1回だけ付ける＝視点を変えても描き方を作り直さない）。夜のターミナルの壁は暗い灰色（tWall 0x4A4E55）・窓は点（a3TermWindows）
  - 3 カードのボタンを札の上へ（375×667 で下端 597px）・4 選ぶ途中は数を見出しの横（.a3picking）・ピルは「機体」・× で前の視点・5 地図カード「空 ○機」・6 .ropill を白いピル（地＋薄い影）、入口「並べ替え・出すものを選ぶ ›」、タイルの補足「OFF にすると隠れます・並べ替えもここで」・7 3D のピル 44・出典 44×44（見た目は32px の丸のまま）・補足 13px・夜の出典の字を明るく・8 遅れのページの札と出典 13px・時間の札は押せない形・10 デモの帯「（本番とは別の記録）」
  - 変えた関数：a3Build・a3City・a3Camera・a3Sheet・a3CardHTML・a3SrcHTML・a3Pills・ohCardHTML・3D のクリックの受け口。足した：a3TowerClip・a3TermWindows・A3_TOWER_CUT
  - テスト：t181 を足した。t119・t142・t159・t160 を合わせた。e2e 26本と tests/ops 成功。**t168 の影の3件はこの手元では main のままでも落ちる**（swiftshader が遅く質が 2→1 に自動で下がり影が止まる。main を取り出して確かめた）
  - 本人に聞くこと：管制塔のすぐ近く（420m 以内）の建物を消してよいか・デモの帯の「終えると消えます」を省いてよいか
  - 見回りの 1（`bad`）と 9（知らせの文の「推定」2回）はデータ担当の持ち場。PM がデータに振っている（pm/board 16e2608a）
- 11/24 の始めに見たとき：PR #189（影）と #194（経営を隠す間のチェックイン）は開いた PR の一覧になかった（PM が入れたと思われる）
- 11/23 手動の回（同じ「#189 にやわらかい影だけ足す」の指示）：直前の回で 76ef4df1 として済み（PR #189 の先頭のまま・main も 520d9d6a のまま）なので作り直さなかった
- **11/23 22時台の定時の回（PM 22時「#189 にやわらかい影だけ足す」）**：checkin/a3-models（PR #189）に足した（76ef4df1・報告 docs/pm/report-a3-models-shadow.md）。テストが通ったので PM の自動の反映でよい
  - #191 から PCFSoft と見ている所に寄せる範囲（±1.5km・a3ShadowFollow）だけ。細かさは 2048 のまま（GPU のメモリは増えない）。全体の視点（カメラが 1,200m より高い）は前と同じ ±4.2km・空港の真ん中（遠くで影が切れないため）。軽い表示・質 0／1 は影なしのまま
  - 変えた関数：a3Build・a3Loop。足した：A3_SHADOW_R・a3ShadowFollow
  - 1コマの時間（駐機場・3回の中央値の平均）：本番 404ms・#189 424ms・影あと 426ms（本番の約1.05倍。上限 1.3倍以内）
  - テスト：t168（影の確かめを4つ足した）・t142・t160・t161・t164・t165・t166・tests/ops 成功。写真 shots-a3-models/ の cmp_* と vs_shadow.png（左 #189・右 影あと）
  - 手元の注意：tests/ops は入っている Playwright（npm root -g）を node_modules に置くと動く。build は terser・csso・brotli・fonttools が要る
- **同じ回で「下の担当からの依頼」（経営担当 #190）も済ませた**：checkin/keiei-hide-checkin・下書き **PR #194**（1881536e・報告 docs/pm/report-keiei-hide-checkin.md・写真 shots-keiei-hide-checkin/）。この回の会話で見張りを付けた
  - 隠している間はチェックインの一言に行事のボーナスを出さない・図鑑の記号の意味は「地方ごとに色を分けています。」。切り替えが true なら今までどおり
  - 変えた関数：checkinServer・renderZkKigou。t171 を足した（t56・t120 も成功）
- 次にやること：PM の次の指示待ち（#189 と #194 の反映は PM の自動で）
- 11/23 22時（日本時間）：PR #192（a3-models-b・別の回の案）は合わせずに閉じられた（おすすめどおり #189 が正）。この件で持っているものはない
- 11/23 手動の回（同じ「羽田の3D の機体をリアルな3Dモデルに」の指示）：もう PR #189（正）・#192（別の回の案）・#191（容量の制限なし）で済んでいるので作り直さなかった。ロゴ・社名なし・CC0／CC BY のモデルは見つからず手で作った点・前後の写真（#189 は docs/pm/shots-a3-models/、#192 は shots-a3-models-b/）もそろっている。本人の答え待ち
- **11/23 定時の回（PM の指示なし。帳面の 11/23 14時20分の積みを始めた）**：始めたとき origin に checkin/a3-models も開いた PR もなかったが、作っている間（約2時間）に別の回が同じ仕事を **PR #189** で出していた。push がぶつかって気づいた。#189 は触らず、この回の版は **checkin/a3-models-b・下書き PR #192**（6169f80）に置いた（#181 と同じ「別の回の案」の扱い）。報告 docs/pm/report-a3-models-b.md・写真 docs/pm/shots-a3-models-b/。PR #192 はこの回の会話で見張りを付けた
  - おすすめは #189 を正にし、#192 は比べるときだけ。#192 を閉じるかは PM に任せる。どちらも tests/e2e/t168.py を足すので片方だけ入れる
  - #192 の違い：切り替えが画面の大きさ（45px・古い iPhone 80px。#189 は距離 1.6km）・MAX 8 の上下に割れた翼の先と LEAP のぎざぎざ・カードと出典の文は変えない。夕方と夜は尾翼に会社の色を使わない（#189 と同じ）
  - 変えた関数：a3Mesh・a3Sync・a3SetLite。足した：A3_REAL・a3RealKey・A3_TAIL・a3TailCol・a3Rev・a3Loft・a3FusTex・a3Env・a3GeoR・a3RealMats・a3FinMat・a3MeshR・A3_REAL_PX（#189 の A3_HD 系とは別の名前）
  - 確かめ：t168・t142・t160（尾翼の色を許す）・t161〜t166（t164 は見えている方の灯りを見る）・tests/ops 成功、e2e 全部も t48（pdf417gen など手元の不足）以外成功。t166 は4本並べると run_all の240秒を超えることがある（1本なら成功）
  - #186（並べ替え・地上の機体の反映）の Actions「反映」は成功していた（11/23 12時57分）
- **11/23 夕方の回（PM 14時25分「3Dモデルを容量の制限なしで1回試す」）**：ブランチ checkin/a3-models-max（checkin/a3-models の上に作った。#189 のブランチは触っていない）・下書き **PR #191**（1b2af495）・報告 docs/pm/report-a3-models-max.md・写真 docs/pm/shots-a3-models-max/。この回の会話で見張りを付けた。比べる用で、入れる前提ではない
  - A3_MAX = true で、切り替えなし・自動の質下げなし・1機種 約3万の三角形・部品を足す・4096 の胴の絵・上塗りのつや・見ている所に寄せた 4096 のやわらかい影
  - 測った数字：届く量 +7KB・作る時間 0.28秒（#189 は 0.04秒）・1コマの時間は本番の約3.2倍（iPhone の見込み 60fps→約20fps）・機体の絵の GPU メモリ 約216MB
  - 見た目の差は小さく、いちばん分かるのは地面の影。おすすめは「#189 に影だけ足す」（本人の答え待ち）
  - テストは max のときだけ合わせた（t168 の待ち9秒・t142 の札は force・t160 に羽根の色・t161 は細かい形の脚・t166 は平らな形の数から細かい形を除く）
- **11/23 14時台の回（PM 14時20分「羽田の3D の機体をリアルな3Dモデルに」）**：ブランチ checkin/a3-models（main 9a79defd から）・下書き **PR #189**（f0c103a7）・報告 docs/pm/report-a3-models.md・写真 docs/pm/shots-a3-models/（cmp_*＝今の本番と同じ視点・new_zoom_*＝寄り）。この回の会話で見張りを付けた。本番は本人が写真を見て OK してから
  - CC0／CC BY で機種の分かるモデルは見つからず、7機種（787・777・767・737・A350・A321neo・A320）を寸法に合わせて手で作った（外のファイルなし・届く量 +5.6KB）。近い機体（1.6km・選んだ機体）だけ細かい形、遠くは今の形・平らな形。「軽い」と質0は今のまま
  - 尾翼の大まかな会社の色（A3_FIN。ロゴなし・夜は使わない）。JAL は「赤い尾翼」にした（本人に確認中）
  - 確かめ：t168 新・t142・t160（色の確かめを合わせた）・t161・t164・t165・t166・tests/ops 成功
  - 部品：A3_HD・a3HdKey・a3HdGeo・a3HdMats・a3HdMesh・a3Loft・a3Tube。a3-models-max はこれを土台に縛りを外して作るとよい
  - 環境の注意：tests/ops は node_modules に入れた playwright 1.56 では動かない。npm root -g の playwright へのリンクで流した。web/ を作るには pip の brotli が要る（フォントの分割）
- 11/23 昼：PM が PR #181（地上の機体・案B）の中身を main に入れていた（ee1986b・#186 の反映まで）。#181 は main を取り込んで差がなくなった（GitHub 上は開いたまま）。閉じてよい（PM に任せる）。#180 も閉じてよい
- 11/23 12時57分（日本時間）：PR #183（並べ替え）が main に入った（#186 で反映）。本番の反映（Actions）の成否と本人の答え（半券などは動かさないか・入口・右上のピル）は次の回で確かめる。直しは main から新しいブランチで。撮る人用は main を取り込めば部品（roGrip・roBind・roOrder）を使える
- 11/23 12時57分（日本時間）：PR #185（案B＋遅れの絞り込み・t165 の直し）が main に入った。反映の Actions の成否と、関数 airport-traffic の反映（ground）は次の回で見る。#181 は中身が入ったので閉じてよい（PM に任せる）
- 11/23 手動の回（PM が同じ「t165 の急ぎ」を指示）：直前の回で PR #185（checkin/a3-ground-merge・c4d3138）として済み。新しい作業用フォルダで t165 を流し直して成功。作り直しは不要だった
- **11/23 0時台の回（PM の急ぎ「案Bと遅れの絞り込みを合わせると t165 が落ちる」）**：ブランチ checkin/a3-ground-merge（PM が main 01c6c4c と a3-ground-b を合わせたもの）に c4d3138 を足し、下書き **PR #185**。報告 docs/pm/report-a3-ground-merge.md。この回の会話で見張りを付けた。仕上がったら PM が自動で反映
  - 原因：アプリでも #181 でもなく、t165 が file:// で開き直したページで localStorage が消えていた（keepls.py の既知の癖。main 01c6c4c だけでも新しい作業用フォルダだと落ちる）
  - 直し：t165 を goto_http で開く。run_all.py は最後の行が「全部成功」のテスト（t165・t166）も成功に数える。src/・web/ は変えていない（変えた関数なし）
  - 確かめ：t165 3回成功・t160・t161・t166・t142・t164・t163・t162・t159・tests/ops 成功・e2e 全部 140件成功（運営コンソールなしの4件は飛ばす）
  - #185 が入れば #181 の中身も入るので、#181（a3-ground-b）は閉じてよい（PM に任せる）
- 11/22 手動の回（PM が同じ「並べ替え」を指示）：直前の回で PR #183（checkin/reorder・9e11e12）と satsuei.md への使い方として済み。main は 01c6c4c のままで作り直しは不要だった
- **11/22 22時台の回（PM 22時5分「いろいろな物の順番を入れ替えられるように」）**：ブランチ checkin/reorder（main 1a87bfd から。あとで main 01c6c4c＝#179 入りを取り込み）・下書き **PR #183**（9e11e12）・報告 docs/pm/report-reorder.md・写真 docs/pm/shots-reorder/01〜10。PR #183 はこの回の会話で見張りを付けた。仕上がったら PM が自動で反映
  - 部品：roGrip（≡）・roBind（マウスはすぐ・指は0.25秒押してから・矢印のキー・読み上げ用の「上へ」「下へ」・読み上げで「○番目にしました」）・roOrder（覚えた並びに今ある物を合わせる）・roMoved・roSay・roFocus
  - 運用の一覧：右上の「並べ替え」→編集の形（カードは div に・≡・下は「はじめの並びに戻す」）→「完了」。並びは layout.order.ohub（OH_EDIT・ohOrder・ohOrderSaved・ohReorder。隠したカードは前の場所のまま）
  - ホームに出すもの：「並べ替え」で行のスイッチが ≡ に（HE.ro・heReorder）。並びは今までの layout.order.home。はじめの並び loOrderDef。戻したら loTidy で全部乗せのまま
  - 変えた関数：ohCards・opsHubRender・opsHubApply・heHTML・openHomeEd・HE・rsHTML（確認のシートに「カードの並び」の行）。CSS は .ropill・.rogrip・.roh・.rokb・.rodrag・.ohtools・.hehd・.hepc.ro・.rodef
  - テスト：t167（新・28項目）。t119・t127・t148・t154・t159・t162・t163・t124・t118・t126・t160・t161・t164・t142・t120・t123・t165・tests/ops 成功。t165 は main でも1回目だけ「開き直しても絞り込みは同じ」が落ちることがある（2回目から成功）
  - 本人に聞くこと：ホームの半券・今日の数字・いちばん上のカードは動かさないままでよいか／入口は「ホームに出すもの」の中だけでよいか／運用の右上のピルで一覧が約30px 下がるのでよいか
- 11/22 22時7分（日本時間）：PR #179（今日の遅れの絞り込み）が main に入った。便ごとの一覧はデータ担当が airport_board に 'bad' を足すまで出ない（それまでは前の時間ごとの札）。反映の Actions の成否は次の回で見る
- 11/22 21時24分（日本時間）：PR #180（地上の機体）が main に入らずに閉じられた（理由は書かれていない。中身は main にもほかのブランチにもなく、checkin/a3-ground に残っている）。自分からは開き直さない。PM か本人の指示を待つ
- **11/22 19時台にもう1つの回（このセッション）が同じ「地上の機体」を作っていた**：ブランチ checkin/a3-ground-b・下書き **PR #181**（1546ada）・報告 docs/pm/report-a3-ground.md（a3-ground-b の中）・比べ写真 docs/pm/shots-a3-ground/cmp_*（管制塔の南東つき）。PR #180 には触っていない。**PM が #180 と #181 のどちらか一方を選ぶ**（選ばなかった方は閉じる）
  - #181 の違い：地上 5km・最小 空22px／地上16px・3km より先の地上機は平らな機体の形（縁取り。三角形約30）・向きが分からない機体はターミナルへ機首・テストは t166（#180 の t165 は #179 の t165 とぶつかる。#180 を選ぶなら t165 の番号を付け直す）・地上の位置は 11/22 19時の羽田の実データ20機・描く量 render_info.json（描く呼び出し 全体の昼 28→127）
  - 変えた関数：新 a3NoseIn・a3Moving・a3Lo・A3_MINPX／変えた a3Poll・a3State・a3Mesh・a3Sync・a3Labels・a3Sheet。関数は groundFromAdsb（_shared/traffic.ts）と supabase/tests/ground_test.ts。t160・t161 を合わせた
- 11/22 19時台の回（PM 18時55分「羽田の3D に地上の機体・見やすく」）：ブランチ checkin/a3-ground（main 1a87bfd から）・下書き **PR #180**（161f716）・報告 docs/pm/report-a3-ground.md・比べ写真 docs/pm/shots-a3-ground/compare-{all,tower}-{day,night}.png と new-pick-ground-day.png。PR #180 はこの回の会話で見張りを付けた。本番は本人が写真を見て OK してから
  - 関数：_shared/traffic.ts に groundFromAdsb（新）。airport-traffic の build の答えに ground（中心から4km・近い順・200機まで・hdg と kt つき）。表は変えていない。live_positions は便名のある機体だけなので、便名なしの駐機機は出ない
  - 画面：新 a3Moving（地上で4kt 以上）・a3MoveArrow（琥珀の矢印）／変えた a3State（地上を移動中・止まっている）・a3Mesh（部品に名前・夜は胴に emissive・A3.pm.far＝奥行きを比べない胴）・a3Sync（見た目の下限 空22px・地上8px／地上20機より多いと全体の視点は胴だけ／止まっている地上機は灯りなし／全体の視点の地上機と影の丸は depthTest なしで上に重ねる＝地面の polygonOffset で隠れていたため）・a3Labels（地上は選んだ機体だけ札・札に data-a3-tag）・a3Sheet（空 ○機・地上 ○機、地上の見出しと6行）・クリックの受けに data-a3-tag／CSS .a3tag（pointer-events:auto）・.a3nl・.a3gh
  - テスト：t165（新・19項目）。関数は supabase/tests/traffic_test.ts に1件足した（deno は npm i -g deno で入る）。t164・t163・t162・t161・t160・t142・t159・t154・tests/ops 成功
  - 本人に聞くこと：入れてよいか・地上の大きさ（8px）と影の丸の濃さ・矢印でよいか・4km の範囲。iPhone での重さ
- 「今日の遅れ」の絞り込み：下書き PR #179（checkin/delay-filter・別の回が作った。一覧はデータ担当の 'bad' 待ち）
- 11/22 夕方の回（PM「今日の遅れにも絞り込み」）：ブランチ checkin/delay-filter（main 1a87bfd から）・下書き **PR #179**（f859b1e）・報告 docs/pm/report-delay-filter.md・写真 docs/pm/shots-delay-filter/01〜04。PR #179 はこの回の会話で見張りを付けた
  - 遅れの専用ページ（#opsLate）に、ピルの絞り込み：種類（すべて・遅れ・欠航。数つき）・向き（すべて・出発・到着）・航空会社（便名の頭2字。一覧にいる会社だけ・横にすべる）・30分以上の遅れだけ（欠航は残す）。便ごとの行。0件は「この条件の便はありません」＋「絞り込みを戻す」。端末に覚える（soramemo.ops.lateFilter）
  - **便ごとの一覧は airport_board の 'bad' が来たときだけ**。今の本番は返さないので、データ担当が関数に 'bad' を足すまで見た目は前のまま（案 docs/pm/delay-filter-board-bad.sql。PGlite で bad 以外は前と同じ・数が hours と合うのを確かめた）
  - 変えた関数：新 ltLoad・ltSave・ltAirline・ltRow・ltMatch・ltListHTML・LT_KEY・LT_DEF・LT_F・[data-ltf] の押す動き／変えた opsLateHTML／CSS は .opslate .ltnone の下
  - テスト：t165（新）。t159・t148・t162・t163・tests/ops 成功
- 11/22 夕方の回で確かめた：反映の Actions は #178（main 1a87bfd）で成功。#175・#176 の反映は失敗していたが、#178 が同じ中身を含めて出したので、閉じるはいつでも（#174）・運用の3D の入口（#173）・灯りと機体（#172）は本番に出ている
- 11/22 1時45分（日本時間）：PM が checkin/a3-lights を #176（pm/release-1122b）で main に入れた（f10e7b8・テストは t164 に付け直し）。PR #172 はそのあとぶつかったので main を取り込んだ（1301052）。コードは main と同じで、残る差は報告の t164 の字と t164 の写真だけ。PR #172 は閉じてよい。本番の反映（Actions）の成否と、本人の iPhone での見え方・重さは次の回で確かめる。直しは main から新しいブランチで
- 11/22 0時45分（日本時間）：#175 が main に入って PR #172（灯りと機体）がぶつかった。main を取り込み（ec2f0ed）、灯りと機体のテストを **t164** に変えた（main の t162 は運用の3D の入口）。web/ を組み立て直し、t164・t160・t161・t142・t162・t163・t159 成功。入る前に流すのは t164・t163・t162・t161・t160・t142・t159・t154・tests/ops
- 11/22 0時46分（日本時間）：PR #174（閉じるはいつでも）が運用タブの3D の入口と一緒に #175 で main に入った（798967989）。反映の Actions はその時点で動いている途中。成否は次の回で確かめる。運用から3D を開いて戻ると 3D → 専用ページの順に閉じるかを、main で t163 に足す
- 11/22 0時46分（日本時間）：PR #173（運用タブの3D のカード）が main に入った。本番の反映（Actions）の成否は次の回で確かめる。直しは main から新しいブランチで
- 11/21 23時台の回（PM「閉じるはいつでも押せるように」）：ブランチ checkin/close-always（main 3665d4c から）・下書き **PR #174**（4ce47de）・報告 docs/pm/report-close-always.md・写真 docs/pm/shots-close-always/01〜07。PR #174 はこの回の会話で見張りを付けた。仕上がったら PM が自動で反映
  - 3D：.a3top を読み込み中の幕（.a3load z-index 4）より上に（z-index 7）。幕が出ているあいだは × だけ（:has で題と「…」を隠す）。左の端24pxから引いて閉じる（#dAp3d の pointer を capture で受け、端から始めた指は a3Drag へ渡さない。3割か速く）
  - 頭の sticky：dialog.spfull の .spctop・.pintop、dialog.mypage の .mp-top、dialog.spsheet の .sph（× は見た目32pxのまま押せる所44px）。空港のページに .cxbar（右上の ×）。運用の専用ページの .opsbar を sticky
  - 戻る操作：showModal を包んで開いた画面を CX_STACK に積み、history.pushState。popstate で上の1枚を閉じる（cancel を止めた画面は閉じない）。× で閉じたら history.go で数を合わせる（state.cx より多くは戻らない）。history.scrollRestoration = "manual"（入れないと t123 の年に飛んだ先が戻された）。運用の専用ページは "ops" として積む（opsHubOpen・opsPlOpen で積み、opsHubBack・openOps で外す）。開く動きの途中の戻るは OH_OPEN_T を止めてすぐ戻す
  - 変えた関数：新 cxPush・cxPop・cxFlush・CX_STACK・popstate・showModal の包み・3D の端から引く操作／変えた openAirport・opsHubOpen・opsHubBack・opsPlOpen・openOps／CSS は style の最後
  - テスト：t163（新・26項目）・t120（上の × を数えない）。e2e 全体 132件成功（運営コンソールなしの4件を除く。t48 も pdf417gen・segno で成功）・tests/ops 成功
- 11/21 手動の回（PM が同じ「運用タブにも3D の入口を」を指示）：直前の回で PR #173（checkin/ops-3d・d10c6dd3）として済み。main は 3665d4ca のままで作り直しは不要だった。checkin/a3-lights（別の回）には触っていない
- 11/21 夜の定時の回（PM 21時40分「運用タブにも3D の入口を」）：ブランチ checkin/ops-3d（main 3665d4ca＝#171 から）・下書き **PR #173**（d10c6dd3）・報告 docs/pm/report-ops-3d.md・写真 docs/pm/shots-ops-3d/。仕上がったので PM の自動の反映を待つ
  - 運用の一覧に「3D」のカード（羽田だけ・地図のすぐ後・見出し「3D」＋縮図の線の絵＋「約0.6MB」）。押すと openAp3d（専用ページなし）。鉛筆のシートと表示の編集の1枚に「「3D」のカード」の ON／OFF（LAYOUT.opsA3＝0。数には入れない・全部乗せで戻る）
  - 変えた関数：新 opsA3On・opsA3Set・OH_A3_ROW・ohA3On・OH_A3_ART・CSS .ohc.a3／変えた OH_CARDS・ohCards・ohCardHTML・opsHubOpen・loSecDef（ops）・vsHTML・data-lo-a3・data-vs-a3 の処理
  - テスト：新 t162（19項目）・t148（並びに a3）・t124（運用（空港）のスイッチ 12→13）・tests/ops（羽田11枚・ほか10枚）を直した。e2e 全体 131／132（t48 は pdf417gen がないだけ）
  - 本人に聞くこと（PM のおすすめで可）：カードを半分の幅のままか横いっぱいか・「押すと読み込みます」を足すか
  - PR #171（羽田の3D リアル版）の反映の Actions は成功（11/21 21時2分）を確かめた。iPhone での重さ・見え方は本人の答え待ち
- 残り：PM が積んだ「滑走路の灯りと機体をもっと現実的に」（checkin/a3-lights）はこの回では手を付けていない（別の回で）
- 11/21 22時台の定時の回（PM の指示なし。滑走路の灯りの回 #172 と同じ時間に並んで動いた）：#171（PR #169 を含む）の反映 Actions は成功＝羽田の3D は本番に出た（#170 は t110 で失敗→#171 で直って通った）。修行の依頼「t72・t123 が落ちる」は main ですでに直っていた（4/4 成功）。e2e 全体 125/131（落ちたのは運営コンソールなしの4件・pip のない t48・並べたときの t130 の揺れ）。コードの変更なし・PR なし。報告はブランチ checkin/fix-t72-t123（088e0672）の docs/pm/report-fix-t72-t123.md
- 11/21 手動の回（PM が同じ「滑走路の灯りと機体をもっと現実的に」を指示）：直前の回で PR #172（checkin/a3-lights・474f492）として済み。main は 3665d4c のままで取り込み済み、作り直しは不要だった。比べ写真は report-a3-lights.md と docs/pm/shots-a3-lights/cmp-{dusk,night}.jpg・models.jpg。PM が本人に見せて OK を待つ
- 11/21 夜の定時の回（PM 11/21 21時35分「滑走路の灯りと機体をもっと現実的に」）：ブランチ checkin/a3-lights（main 3665d4c＝#171 から）・下書き **PR #172**（474f492）・報告 docs/pm/report-a3-lights.md・比べ写真 docs/pm/shots-a3-lights/cmp-{dusk,night}.jpg（上＝本番 #171、下＝新しい版。全体・管制塔・機体・進入中の機体（近く））と models.jpg（機種の並び）。PR #172 はこの回の会話で見張りを付けた。本番は本人が写真を見て OK してから
  - 灯り：AIP JAPAN RJTT AD 2.14（第三者の写し nagodede.github.io の RJTT_full.pdf。AD 2.14 のページは 2022/10 発効）を A3_LGT に。縁 白／端600m 黄・中心線 白／赤白／赤・末端の緑と翼の形の列（04・05 なし）・終わりの赤・接地帯900m・PALS 900m（23 は870m、04・05 なし、34R は CAT III の赤い列）と順に流れる閃光（119灯）・PAPI（34R だけ右・05 なし。a3Papi でカメラからの角度で色）・誘導路の縁の青90m と中心線の緑30m
  - 描き方：a3LightMat（芯＋光の輪・足し合わせ・点滅の種類 0 いつも／1 流れる閃光／2 衝突防止灯／3 白い閃光）。**灯りは見ている所へ 4m＋距離の2% 寄せて描く**（地面は polygonOffset で手前へずらしているので、そのままだと浅い角度で灯りがめり込んで見えなかった。前の本番も同じ不具合）。夕方は uK 0.6
  - 機体：胴は LatheGeometry（尾は上がる）。A3_MODELS に e（E170/E190）・crj・q4（Q400）・atr を足し、flex（787 の反り）・tt（T 字の尾翼）・bog（主脚の車輪 2/4/6）・pr／nb（プロペラ）。geo の鍵は「機種/丸の細かさ」。地上の機体の高さは車輪が地面に着く高さ（長さ×rad×2.3）
  - 機体の灯り：a3AcLights（acl＝航空灯・衝突防止灯・白い閃光、land＝着陸灯は空で脚を出しているあいだ）。夕方と夜だけ
  - 古い端末：a3Weak（iPhone で画面の画素 120万未満、または CPU 4つ以下で iPhone 以外）→ はじめ q1・A3.seg 10・lightsFine を出さない。q0 で lightsFine を隠す
  - 重さ：読む量は約0.6MB のまま（アプリ本体が圧縮で約2.4KB 増）
  - 変えた関数：新 A3_LGT・A3_LGT_SP・A3_LC・a3LightMat・a3LightBox・a3RwyLights・a3Papi・a3AcLights・a3Weak／変えた a3Build・A3_MODELS・A3_MODEL_RE・a3Model・a3Geo・a3Mesh・a3Sync・a3Loop・a3Quality・a3SrcHTML・A3_SIZE
  - テスト：t162（新・16項目）・t161（E190→e・DH8D→q4・出典に AD 2.14）・t160／t161 は navigator.hardwareConcurrency を8にして開く（試す機械は CPU 2つで古い端末の形になる）・t142・t159・t154・tests/ops 成功
- 11/21 20時27分（日本時間）：PR #169（羽田の3D をもっとリアルに）が main に入った。本番の反映（Actions）の成否と、本人の iPhone での重さ・見え方は次の回で確かめる。直しは main から新しいブランチで
- 11/21 手動の回（PM が同じ「羽田の3D をもっとリアルに」を指示）：直前の回で PR #169（checkin/a3-real・75201636）として済み。main は eabb6e1 のままで作り直しは不要だった。比べ写真は report-a3-real.md と docs/pm/shots-a3-real/cmp-{day,dusk,night}.jpg。PM が本人に見せて OK を待つ
- 11/21 夜の定時の回（PM 11/21 17時15分「羽田の3D をもっとリアルに」）：ブランチ checkin/a3-real（main eabb6e1＝#168 から）・下書き **PR #169**（1b56477・報告の追記 75201636）・報告 docs/pm/report-a3-real.md・比べ写真 docs/pm/shots-a3-real/cmp-{day,dusk,night}.jpg（上＝本番 #168、下＝新しい版。全体・管制塔・機体（空）・機体（地上））。PR #169 はこの回の会話で見張りを付けた。本番は本人が写真を見て OK してから
  - 建物：PLATEAU（大田区 2025・川崎市 2022。PDL1.0＝CC BY 4.0 互換・ODbL も可を原文で確認）の外形と計測高さ。空港の中 261棟（ターミナル約37〜39m）・海沿いの街 26,819棟（約6.5km まで・小さい建物は省く）を hnd.json の bld・city に（city は2点目から差。用途 0 住宅・1 事務所や店・2 工場や倉庫）。作り方 tools/a3_plateau.py（zip は範囲指定で必要なメッシュだけ。大田区と川崎市でメッシュ番号が重なるのでフォルダを分ける）
  - 地面：滑走路の色むら・タイヤの跡・芝と陸と駐機場の色むら（a3Noise。a3Merge が uv を引き継ぐ）・海の照り返し（Phong）。**三角の表裏が混ざって誘導路・屋根・左の翼が黒く見えていた不具合を a3Wind で直した**（今の本番の誘導路の黒い線の原因）。画素の密度 2 で海の色が駐機場に出る件は、海を先に描き深さを書かない形で直した
  - 機体：a3Model（機種→787・777・350・767・747・380・340・737・320、ほかは a3Kind の5つ）と A3_MODELS の割合で a3Geo を作り直し。窓の帯（0x374151）・翼の先・発動機の口と支柱・脚（地上と着陸の前・離陸直後だけ、名前 gear）。地上の機体の視点は屋根より上（約120m）から見下ろす
  - 空：a3Sky2（薄い雲・空港の上約6km は空ける・量は METAR の sky、夜の星は空の球の子）。夜の街の灯り（cityLights）・駐機場の照明（lights.f）・ターミナルは壁だけ灯す（a3Extrude の group 0 屋根／1 壁）
  - 重さ：圧縮して約0.58MB（A3_SIZE「約0.6MB」）・組み立て約0.38秒・三角約41万。質0 で citySmall と clouds を隠す
  - 地上の機体：airport-traffic の答えに ground の並びが来たら出す（今は traffic.ts で落としている → データ担当へ依頼）
  - 変えた関数：新 a3Wind・a3Noise・a3Extrude・a3City・a3Sky2・a3Model・A3_MODELS・A3_MODEL_RE・A3_CITY_COL／変えた a3Build・a3Merge・a3Ribbons・a3RwyTex・a3Colors・a3Geo・a3Mesh・a3Sync・a3Camera・a3Quality・a3Poll・a3Sheet・a3CardHTML・a3SrcHTML・A3_CREDIT・A3_SIZE・A3_SHAPE
  - テスト：t161（新・16項目）・t160（字 約0.6MB・量 0.55〜0.65MB・PLATEAU・窓の帯の色）・t142（字）・tests/ops 成功。e2e 全体 130／131（t48 は pdf417gen・segno を入れて流し直すと成功）
- 11/21 16時21分（日本時間）：PR #164（羽田の3D）が main に入った。本番の反映（Actions）の成否と、本番の羽田の機体での見え方（端の札・本人の iPhone での重さ）は次の回で確かめる。直しは main から新しいブランチで
- 11/21 手動の回（PM が同じ「羽田の3D の完成度を上げる」を指示）：直前の回で PR #164（checkin/a3-model・a3f1c4b）として済み。main は 8ba15f6 のままで取り込み済み、作り直しは不要だった。比べ写真は report-a3-model.md と docs/pm/shots-a3-model/cmp-*（昼夕夜×4視点の12枚）。PM が本人に見せて OK を待つ
- 11/21 夕方の定時の回（PM 11/21 13時40分「羽田の3D の完成度を上げる」）：ブランチ checkin/a3-model（main 8ba15f6 から）・下書き **PR #164**（a3f1c4b）・報告 docs/pm/report-a3-model.md・写真 docs/pm/shots-a3-model/（昼夕夜×全体・管制塔・機体の空と地上、今の本番との比べ写真 cmp-*）。PR #164 はこの回の会話で見張りを付けた。本番は本人が写真を見て OK してから
  - 不具合1（上半分の薄い青の四角）の原因は3D ではなく、下のシートがスクロールする箱だとダイアログの背景が絵の上に透けるブラウザの重ね方の不具合。.a3sheet は overflow hidden、中の .a3body を送る形にした（3D の中で一覧・カード・出典を足すときは .a3body の中に入れる）
  - 不具合2 名札は出典の札と左上の札を避ける／3 管制塔は OSM の位置・管制室の高さ約106m・西を俯角約3.6°／4 機体の視点は近く。全部の視点で絵の中心をシートの上へずらす（a3ViewOffset。カメラの画角は cam.userData.fov に書く）
  - 形：web/3d/hnd.json（OSM を加工・ODbL 1.0・圧縮約34KB。tools/a3_shape.py で作る。OSM の API で羽田のまわりを小分けに1回だけ取った。Overpass はこの環境から届かなかった）。滑走路は HND_RWY のまま、標示は絵（a3RwyTex）
  - 機体は a3Kind で5つの形（会社の色・ロゴなし）。光は実際の太陽の向き・影・夕方の空・夜の灯り。重いと a3Quality で影→細かさを下げる
  - 変えた関数：新 a3Shape・A3_CREDIT・a3ViewOffset・a3SunDir・a3Merge・a3Ribbons・a3Lines・a3RwyTex・a3Quality・a3Kind・a3Geo／変えた openAp3d・a3ShellHTML・a3Credit・a3Build・a3Night・a3Colors・a3Loop・a3Mesh・a3Sync・a3Camera・a3Labels・a3Sheet・a3CardHTML・a3SrcHTML・a3SetLite・A3_TOWER
  - テスト：t160（新）・t142（管制塔の高さ 106・.a3body・出典に OSM）・t159（カメラの見本に userData）・t154（A3_CREDIT を除外）・tests/ops 成功・e2e 全体 130 件すべて成功（a3f1c4b。運営コンソールの4件は飛ばす）
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
- 【11/25 stamp-edge-b】#238 と同じ仕事の別案（ブランチだけ）。PM が #238 を選んだら checkin/stamp-edge-b は消す。#238 にない所（取り直しのボタン・設定から戻ったときの取り直し）を使うなら #238 に移す
- 【重なり防止・再】始めるときだけでなく、push の前にも origin のブランチと開いた PR を見る（11/25 22時台は作っている途中で別の回が同じ仕事を出した）
- 【11/26 stamp-edge】PR #238：PM の自動の反映を待つ。本人の答え（上の4つ）で直す。入る前に t196・t195・t144・t24・t171・t11・t13・t15・t19・t30・t193・t189・tests/ops を流す。#226（micro）とは say・CSS の最後・toast の所が近い（src/index.html）。あとから入る方で web/ を作り直す。micro の mxToast と1つにまとめるときは、確定の札（flushQueue の toast）も含める
- 【11/26 flight-suggest】PR #239：PM の自動の反映を待つ。本人の答え（上の4つ）で直す。入る前に t197・t195・t24・t144・t13・t47・t61・t123・tests/ops を流す。#238（stamp-edge）とは src/index.html の別の所（印の判定・保留と、便の記録・日誌）で、showStamp の同じ行は触っていない。CSS の最後の所が近いので、あとから入る方で web/ を作り直す。データ担当が manual_flights.flight_no を足したら、loadServer で読んで日誌に便名を出す
- 【次の回】PM の指示がなければ、帳面の積みで残っているものを上から見る（いまは新しい積みなし）
- 【11/25 stamp-fast】PR #229：PM の反映を待つ。本人の答え（上の4つ）で直す。入る前に t195・t24・t171・t11・t13・t15・t19・t30・t193・t189・tests/ops を流す。checkin/micro（763673a1）と src/index.html の say・CSS でぶつかる見込み。stamp-fast が先（PM の指示）。micro を入れるときは札を mxToast と toast（.smtoast）の1つにまとめ、t194（micro）と t195（stamp-fast）は両方残す
- 【手元の道具】e2e を流したあと docs/pm の写真の戻しは `git diff --name-only -- docs/pm | xargs git checkout --`（シェルの * は untracked のフォルダも拾って失敗する）。run_all.py の引数は前方一致なので、分けて流すときは t1.py のように .py まで付ける
- 【11/25 micro】PR #226：閉じられた（12個は main に入った）。札を重ねない2行は未反映（PM の判断待ち）。元は「PM の自動の反映を待つ。答え（札の決め方・コピーを付ける所・札の高さ）で直す。入る前に t194・t145・t183・t167・t184・t120・t123・tests/ops を流す。#224（修行の帯）とは src/index.html の別の所。あとから入る方で web/ を作り直す
- 【11/25 t30-fix】PR #221：main に入った（済み）。元は「PM の自動の反映を待つ。入る前に t30・t193・t189・t163・t120・t123 を流す。#219（drop-newyear）・#217・#215 とは src/index.html の別の所（マイページの close と CX の close）。あとから入る方で web/ を作り直す
- 【11/25 drop-newyear】PR #219：PM の自動の反映を待つ。答え（分類の名前「時間帯」か「時間」）で直す。入る前に t192・t182・t17・t141・t145・t118・t119・t124 を流す。#215（a3-free）とは src/index.html の別の所（実績と 3D）でぶつからない見込み。あとから入る方で web/ を作り直す
- 【11/25 sweep-1125】PR #217：PM の自動の反映を待つ。答え（長い名前の行数・帯の背景の範囲）で直す（main から新しいブランチ、または #217 に足す）。入る前に t191・t127・t140・t149・t146・t184・t120・t189・t183・tests/ops を流す
- 【11/25 a3-free】PR #215 は main に入った。答え（展望デッキの位置・1本指・飛ぶの速さ・iPhone での重さ）で直す（main から新しいブランチ、または #215 に足す）。入る前に t190・t142・t159・t160〜t168・t181・tests/ops を流す（t168 は run_all で上限 1,800 秒）
- 【11/24 mypage-b】PR #211：PM の自動の反映を待つ。本人の答え（気軽に・撮影の入口・外した関数・運用のタイル）で直す（main から新しいブランチで）。入る前に t189・t183・t118・t119・t124・t145・t184・t73・t47・t54・t57・tests/ops を流す。マイページの中の行を押すテストは openMyPage("ページ") を先に呼ぶ
- 【11/24 16時台】PR #203：t168 は直した（111c901e）。PM の反映を待つ。main がさらに動いたら取り込み直して t168 を run_all 経由で流す（上限 1,800 秒）。#207 が main に入ったら「その3」（checkin/stats-shugyo-card）を始めてよい
- 【11/24 sweep-all-1】PR #207：PM の自動の反映を待つ。本人の答え（上の3つ）で直す（main から新しいブランチで）。入る前に t183・t114・t182・t8・t13・t31・t73・t110・tests/ops を流す。#207 が main に入ったら「その3」（checkin/stats-shugyo-card）を始めてよい（成績の同じ所）。その2（checkin/sweep-all-2）は別の回の持ち分。始める前に origin のブランチを見る
- 【手元の道具】tests/ops は package.json の playwright 1.56.1 では動かない。node_modules に全体の playwright をつなぐ（ln -s $(npm root -g)/playwright tests/ops/node_modules/）と動く。e2e を流すと docs/pm の前の写真が上書きされるので、コミットの前に git checkout で戻す。pdf417gen・segno（t48）は pip で入れる
- 【11/24 a3-hq】PR #203：本人の答え（iPhone の重さ・汚れの濃さ・映り込みの絵）で直す（main から新しいブランチで）。入る前に t142・t160〜t168・t181・tests/ops を流す。t168 は A3_QLOCK で質を止めて確かめる（画面のないソフトの描画は遅いため）。重すぎるなら、まず A3_MAX のときの胴の絵（4096→2048）と影（4096→2048）から下げる。#191（a3-models-max）のブランチは #203 に移したので閉じてよい（PM に任せる）
- 【11/24 a3-hq】#200（季節の印）と #203 は src/index.html の別の所（印・実績と 3D）でぶつからない見込み。あとから入る方で web/ を作り直す
- 【11/24 13時台】次の回：「3D の機体を容量を気にせず最高の質に」（checkin/a3-hq）を最初から通しでやる。ブランチ checkin/a3-hq は 13時台の回の目印だけで中身なし（main と同じ）なので、そのまま使ってよい。#191 の 1b2af495 の src の差分（A3_MAX・a3HdWingTex・a3ShadowFollow・a3Loft の uv・72 分割・ファンの羽根・脚の扉・アンテナ・上塗りのつや）を移すとき、PM の指示どおり「質の自動の下げ」は残す（#191 は A3_MAX で止めていた）。影の追従は main に a3ShadowFollow が入っているので、そこは合わせるだけ
- 【11/24】PR #200（季節の印）：紛れた写真は戻した。PM の反映を待つ。見出しを「時間と日付」にするかは本人の答えで（変えるなら ACH の5行の1語だけ）
- 【11/24】PR #200（季節の印を外す）：PM の自動の反映を待つ。本人の答え（「時間と季節」の名前）で直す。入る前に t182・t17・t141・t145・tests/ops を流す
- 【11/24】PR #198（sweep-1124）：PM の反映を待つ。本人の答え（近くの建物を消すか・デモの帯）で直す（main から新しいブランチで）。入る前に t181・t142・t160・t159・t119・t162・t163・t167・tests/ops を流す。t168 は手元で main でも落ちるので、速い環境か PM の Actions で見る
- 【11/24】手元の道具：build は tools で npm install と pip の brotli が要る。3D の写真は t166 の open3d（http で web をそのまま出す・bypass_csp）を使うと形のファイル（3d/hnd.json）も読める
- 【11/23 定時の回】PR #192（a3-models-b）は #189 と同じ仕事の別案。PM が #189 を選べば閉じてよい。#192 の切り替え（画面の大きさ）や MAX 8 の翼の先がよければ #189 に移す（main から新しいブランチで）
- 【重なり防止】始める前だけでなく、長い仕事は途中（1時間ごと）にも origin のブランチと開いた PR を見る。11/23 は始めたときになかった checkin/a3-models が途中でできていた
- 【11/23 夕方】a3-models-max は PR #191 で済み。本人が #189 と #191 を見て決めたら、その答え（例：#189 に影だけ足す）を main から新しいブランチで作る
- PR #185（案B＋遅れの絞り込み）：PM の反映を待つ。反映の Actions の成否と、関数 airport-traffic の反映（ground）を次の回で見る
- file:// で開き直すテストは keepls.py の goto_http を使う（t165 で毎回落ちた）。t166 は three.js が作業用フォルダにないと飛ばすので、先に t142 を同じ SORAMEMO_TEST_WORK で流す。e2e の全部は4つに分けて別の作業用フォルダで並べて流すと約20分
- PR #183（並べ替え）：main に入った。本人の答えで直す（main から新しいブランチで）。入る前に t167・t162・t163・t148・t124・t127・t119・tests/ops を流す。撮る人用が satsuei/home-card-switch のピルを部品につなぐとき、困ったら直す
- PR #181（地上の機体・案B）は本人 OK（CLAUDE.md 11/22）。PM が入れる。入る前に t166・t164・t163・t162・t161・t160・t142・t159・tests/ops と deno の supabase/tests。#179 が main に入ったので、ぶつかったら main を取り込み web/ を作り直す
- 同じ仕事を2つの回が重ねないよう、始める前に origin のブランチと開いている PR を見る。ブランチが main と同じ形で先にできていても、ほかの回が動いている途中のことがある（11/22 の a3-ground で重なった）
- PR #181（地上の機体・別案）：PM が #180 と比べて選ぶのを待つ。選ばれたら入る前に t166・t164・t163・t162・t161・t160・t142・t159・tests/ops と deno の supabase/tests を流す
- PR #180（地上の機体）：本人の答えで直す。入る前に t165・t164・t163・t162・t161・t160・t142・t159・t154・tests/ops と deno の traffic_test を流す。関数 airport-traffic の反映も要る（関数の反映を忘れると ground がなく、前と同じ「30km・3,000m 以下」で動く）。比べ写真は git archive origin/main web を取り出し A3_WEB=<web> で t165 を流すと old-*.png が撮れる
- 「運用の『今日の遅れ』にも絞り込み」は別の回が PR #179（checkin/delay-filter・f859b1e）で作った。11/22 夜の回に同じ指示が手動で来たが、重ねて作らないことにした。#179 の直しは #179 の回か、その帳面の続きで
- PR #172 は main に入った中身と同じなので閉じてよい（PM に任せる）
- PR #179（今日の遅れの絞り込み）：データ担当の 'bad' を待つ（下の依頼）。来たら本物の形で t165 の作り物と合うかを見る。本人の答え（向きの「すべて」・30分以上でも欠航を残す・JTA を JAL にまとめるか）で直す。入る前に t165・t159・t148・tests/ops を流す
- 次の回：PM の指示がなければ「羽田の3D に地上の機体・見やすく」（checkin/a3-ground。下の 11/22 18時55分の欄）を始める。始める前に origin に checkin/a3-ground がないか見る
- 運用から3D を開いて戻ると 3D → 専用ページの順に閉じるかを t163 に足す（まだ。a3-ground の回で一緒に）
- PR #172 はコードが main と同じなので閉じてよい（PM に任せる）
- PR #174（閉じるはいつでも）：PM の自動の反映を待つ。本人の答え（3D の読み込み中は × だけでよいか・戻るで閉じてほしくない画面）で直す。入る前に t163・t120・t123・t160・t161・tests/ops を流す。#172（灯り）や ops-3d が先に入ったら main を取り込み web/ を作り直す（a3 の関数は触っていない。ぶつかるなら style の最後と opsHubOpen・opsHubBack の行）。運用から 3D を開く入口ができたら、戻るが 3D → 専用ページの順に閉じるかを t163 に足す
- 次の回：PM の指示がなければ「滑走路の灯りと機体をもっと現実的に」（checkin/a3-lights。下の 11/21 21時35分の欄）を始める。始める前に origin に checkin/a3-lights がないか見る（ほかの回が持っていれば触らない）
- PR #173（3D のカード）：PM の反映を待つ。入る前に t162・t148・t124・tests/ops を流す。a3-lights で A3_SIZE が変わってもカードの字は A3_SIZE を使うので自動で合う
- 次の回：PM の指示がなければ「運用タブにも3D の入口を」（11/21 21時40分の積み。checkin/ops-3d で main から。a3-lights とは別の回）
- 羽田の3D（#169）は本番に出た（#171 の反映 Actions 成功）。本人の iPhone での重さ・見え方の答えが来たら main から新しいブランチで直す。e2e を6本並べて流すと t130 が待ち時間で落ちることがある（1本ずつなら成功）。checkin/ops-3d のブランチは 11/21 22時台に main の先と同じ形で作られていた（別の回が始めた見込み。同じ仕事を重ねないこと）
- PR #172（灯りと機体）：本人の答え（入れてよいか・明るさ・誘導路の青の量・公式 AIP で確かめるか・縁の黄を両端にした簡単化・iPhone での重さ）で直す。入る前に t162・t161・t160・t142・t159・t154・tests/ops を流す。重ければ a3Weak の線か lightsFine を先に減らす。#169 が main に入っているので #172 は #171 の上（ぶつからない）
- 比べ写真の撮り方：本番の web は git archive origin/main web で取り出し、t162 の open3d を A3_WEB で切り替えて同じ場面を撮る（作業用の写しは残していない）
- PR #169（羽田の3D をもっとリアルに）：本人が比べ写真を見た答え（入れてよいか・iPhone での重さ・雲の出し方・夜の灯りの量）で直す。入る前に t161・t160・t142・t159・t154・tests/ops を流す。重ければ街の範囲（tools/a3_plateau.py の SRC の半径）と小さい建物の線（40m²／100m²）を下げて hnd.json を作り直す（PLATEAU の gml は /tmp/a3-plateau/<0|1>/ に置けば取り直さない）。データ担当が ground を返したら本物の形で地上の機体を確かめる
- PR #164（羽田の3D）：本人が写真を見た答え（入れてよいか・管制塔のはじめの向き 西／南東・本人の iPhone で重くないか）で直す。入る前に t160・t142・t159・t154・tests/ops を流す。本番の羽田の機体で全体の視点の端の札を撮り直す。形を新しくするときは tools/a3_shape.py（OSM の API は年に数回まで）
- 3D のテスト（t160）は形のファイルを fetch するので、file:// でなく手元の http で開いている。t142 は file:// のままなので形が読めず、前の仮の島で動く（それも確かめになる）
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
- t72・t123 は main で直っていた（11/21 夜に確かめた）。本人が Mac で動かした結果（ビルドが通るか・位置の許可・シートの下の余白）が来たら直す
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
- 【11/26 データ担当へ（flight-suggest・PR #239）】(1) manual_flights に便名の列 flight_no（text・任意）を足してほしい（移行と RLS をセット。本人の行だけ書ける今の決まりのまま）。アプリは列があれば入れ、なければ外して入れる形にしてある (2) 「日付＋便名 → 出発・到着・時刻・機体」を flight_history から返す読むだけの関数（例 flight_lookup(p_date date, p_flight text)）。今は今の時刻表から推定している
- 【11/25 checkin/micro の回へ（自分の持ち分の別の回）】stamp-fast（PR #229）で toast()・.smtoast（05 の札の形）を足した。micro の mxToast と1つにまとめてほしい。テストは micro が t194、stamp-fast が t195
- 【11/25 撮る人用へ】知らせの鈴（.spbell・data-spnote）を ON にしたとき、mxBell(押したボタン) を呼んでほしい（PR #226 の 11「鈴が揺れる」。描き直しの前に呼ぶ）。コピーの部品 mxCopyHTML(文字, 名前) も使える
- 撮る人用（11/22・satsuei.md に書いた）：ホームの空港のカードの切り替えのピルは、並べ替えの部品（roGrip・roBind・roOrder。PR #183）で並べ替えられる。並びは layout.order.<名前> に入れると端末とサーバーにそろう。#183 が main に入ってからつなぐ
- データ担当（11/22・PR #179、PM から伝えてほしい）：運用の「遅れ」の絞り込みのため、airport_board の返す形に 'bad'（今日・日本時間の15分以上の遅れと欠航の便。1便 {dir:'dep'|'arr', flight, other, sched, est, actual, late(分・欠航は null), cancelled, intl, aircraft}・定刻の順）を足してほしい。'hours' の late・cancel と同じ数え方で、合計が合うこと。案は checkin/delay-filter の docs/pm/delay-filter-board-bad.sql（移行 165 の関数に u・d の列と 'bad' を足しただけ。表・列・RLS・権限は変えない）。画面は 'bad' がないあいだ前のままなので、どちらが先に入ってもよい
- 撮る人用・運用予想・修行へ（11/21 PR #174・知らせだけ）：土台で、全画面の頭（.spctop・.pintop）とシートの頭（.spsheet .sph）を上に止め、戻る操作で上のダイアログを1枚閉じるようにした（showModal を包む）。それぞれのダイアログもそのまま効く。修行の dialog.sgd の頭は sticky にしていない。cancel を止めた画面は戻るでも閉じない
- データ担当（11/21 夜・PR #169）：①外部データの確認表に「PLATEAU（3D都市モデル）大田区 2025・川崎市 2022：公共データ利用規約 第1.0版（CC BY 4.0 互換・ODbL も可）・出典『「3D都市モデル（Project PLATEAU）大田区（2025年度）・川崎市（2022年度）」（国土交通省）を加工して作成』・外形と計測高さと用途だけ使う・測量法の注意（測量には使わない）・11/21 に1回だけ取得（tools/a3_plateau.py）」を足してほしい。②airport-traffic の答えに地上の機体を `ground` の並びで足してほしい（planes と同じ id・callsign・lat・lon・hdg・type・reg。羽田だけでよい。今は _shared/traffic.ts で alt_baro "ground" を落としている）。アプリは対応済み
- データ担当（11/21・PR #164）：外部データの確認表に「OpenStreetMap（羽田の形・3D）：ODbL 1.0・切り出したファイル web/3d/hnd.json を ODbL で公開・角に © OpenStreetMap・11/21 に API で1回だけ取得（作り方 tools/a3_shape.py）」を足してほしい
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
- 【済み 11/21 夜】修行（11/20・PR #147 shugyo-jst-year）：修行の年と月を日本時間にした（チェックイン側の関数は変えていない）。全体を流したとき t72・t123（フライトの共有の画面。#dShare の字が押す所をふさぐ）が今の main でも落ちた。チェックイン側で見てほしい → 今の main（3665d4ca）では caf39d0f・220bba55 で直っていた。t72・t123 とも 4/4 成功（報告 report-fix-t72-t123.md）
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

## PM から積んだ次の仕事（11/21 13時40分、羽田の3D の完成度を上げる。本人「モデルは完成度を上げて」）※checkin/a3-model で。本番は本人が写真を見て OK してから → PR #164 で作った（5b5a02a・報告 report-a3-model.md）
- 本番を撮って見えた不具合（PM が 11/21 13時32分に 390×844 で撮った）：
  1. 全体の視点で、上半分に薄い青の四角（空の板か HTML の枠）が地面を隠している。四角の下の端がまっすぐ切れている
  2. 機体の札（MH691 3分）が出典の札と重なる
  3. 管制塔の視点がほぼ地平線だけで、滑走路も機体も見えない（高さ・向き・画角）
  4. 機体の視点も確かめて直す
- 完成度を上げる：
  1. ターミナル（第1・第2・第3）・管制塔・駐機場・誘導路・滑走路の標示（番号・中心線・末端）を、実際の形に近く。海岸線と島の形も
  2. 機体は機種の大きさに合わせた立体（胴体・主翼・尾翼）。会社の色やロゴは使わない（決まり：ロゴは提携後）
  3. 光と影・夕方と夜の見え方（空の色・滑走路の灯り）を自然に
  4. 形の出典は利用規約で使えるものだけ（国土地理院の基盤地図情報・AIP JAPAN・OpenStreetMap など）。使う前に条件を確かめ、出典を「出典 i」に足す（データ担当の確認表にも）
  5. 読み込みは押したときだけのまま。大きさは 0.5MB まで（入口の「約0.2MB」も実際に合わせて直す）。古い iPhone（SE 第2世代）でも 30fps を目安に、重ければ質を自動で下げる
- 確かめ方：3つの視点 × 昼・夕・夜の写真（390×844・2倍）を report に。今の本番と並べた比べ写真も。PM が本人に見せて OK をもらってから反映する

## PM から積んだ次の仕事（11/21 17時15分、羽田の3D をもっとリアルに。本人「もっとリアルに」）※checkin/a3-real で。本番は本人が写真を見て OK してから → PR #169 で作った（1b56477・報告 report-a3-real.md）
- 本人の iPhone では前の版（平たい板）が出ていた（キャッシュかアプリの中の古いファイル）。#168 の版を見たうえで、さらにリアルにする
- やること：
  1. 建物：国交省 PLATEAU（東京都大田区の3D都市モデル。CC BY 4.0 で使えるか原文で確かめる）か OSM の高さ付きの建物で、ターミナル・格納庫・管制塔・まわりの街（大田区・川崎の海沿い）を立体に。屋根と壁の色を分ける
  2. 地面：滑走路の舗装の色むら・標示（番号・中心線・タッチダウン・末端の縞）・誘導路の黄色い線・草地と海の色。海は少し光る
  3. 機体：機種ごとの形（B787・B777・A350・B737・A320 など）の軽い立体。翼・エンジン・尾翼。会社の色やロゴは使わない（白い機体に濃いグレーの窓帯くらい）。地上の機体（駐機場・誘導路）も出せるなら出す（adsb の ground）
  4. 空：時刻に合わせた太陽の位置と空の色・薄い雲・夜の灯り（ターミナル・滑走路の灯火・進入灯）
  5. 重さ：押したときだけ読み込むのはそのまま。大きさは 1.5MB まで（入口の表示も実際に）。古い iPhone では自動で質を下げる。30fps 目安
  6. 出典は「出典 i」に（PLATEAU・OSM・AIP JAPAN・adsb.lol）。データ担当の確認表にも
- 確かめ方：今の本番（#168）と新しい版を並べた写真（全体・管制塔・機体 × 昼・夕・夜、390×844・2倍）を report に。PM が本人に見せて OK のあと反映

## PM から積んだ次の仕事（11/21 21時35分、滑走路の灯りと機体をもっと現実的に。本人「滑走路のライトをもっとリアルに、機体も現実的なものにしたい」）※checkin/a3-lights で。本番は本人が写真を見て OK してから → PR #172 で作った（474f492・報告 report-a3-lights.md）
- 灯り（AIP JAPAN の羽田の灯火の種類に合わせる。夜と夕方）：
  - 滑走路：縁の白（末端から600mは黄）・中心線の白と赤・末端の緑・終わりの赤・接地帯の白
  - 進入灯：A〜D 各滑走路の進入灯の列と、順に流れる閃光（いわゆるラビット）
  - PAPI：滑走路の横の4灯（赤と白。機体から見た高さで色が変わるのは機体の視点だけでよい）
  - 誘導路：縁の青・中心線の緑
  - 夜は灯りが少しにじむ（光の輪）。昼は消すか目立たない
- 機体：
  - 機種ごとの形の差がはっきり分かる立体：B787（反り上がった主翼・2発）・B777（長い胴体・大きな2発）・A350（翼端の曲がり）・B767・B737/A320（翼端の板）・E170/E190・Q400（プロペラ・高い翼）・ATR。エンジンの数と位置・尾翼の形・脚
  - 色は白い胴体と灰色の翼、窓の帯だけ（会社の色・ロゴは使わない。決まり）
  - 機体の灯り：左翼の赤・右翼の緑・尾の白・衝突防止灯の赤い点滅・白い閃光。着陸の手前は着陸灯をつけ、脚を出す（高さ・進入の段階から）
  - 外のモデルを使うなら、CC0 か CC BY などアプリで使える条件のものだけ（出典を「出典 i」に）。自分で作ってもよい
- 重さ：押したときだけ読み込むのは今のまま。合わせて 2MB まで（入口の表示も実際に）。古い iPhone では灯りの数と機体の細かさを自動で下げる
- 確かめ方：今の本番（#171）と並べた比べ写真（全体・管制塔・機体 × 夕・夜。進入中の機体を近くから1枚）を report に。PM が本人に見せて OK のあと反映

## PM から積んだ次の仕事（11/21 21時40分、運用タブにも3D の入口を。→ PR #173 で作った（d10c6dd3・報告 report-ops-3d.md）。本人「3Dの入口がわかりにくいから、運用にも追加して」）※checkin/ops-3d で（a3-lights とは別の回。src/index.html は小さく変える）
- 運用タブの一覧（ops-hub）に「3D」のカードを1枚足す。羽田を選んでいるときだけ出す（a3On と同じ条件）。並びは「地図」のカードのすぐ後
- カードの形は今の一覧の決まりどおり：見出し1語「3D」＋小さな絵（3D の羽田の縮図の静止画か、線の絵）＋「約○MB」を小さく薄いグレー。押すと openAp3d で今の3D を開く（専用ページは作らない）
- 隠す・出すの設定（lo）でも選べるように
- テスト：羽田でカードが出る・ほかの空港では出ない・押すと3D が開く・字13px以上・はみ出しなし
- 見た目は今のカードと同じ形なので画面案は待たない。仕上がったら PM が自動で反映する

## PM から積んだ次の仕事（11/21 22時、閉じるはいつでも押せるように。本人「閉じるの機能は、いつでも触れるように」）※checkin/close-always で → PR #174 で作った（4ce47de・報告 report-close-always.md）
- 全画面で開くもの（羽田の3D・運用の専用ページ・空港のページ・機体のくわしく・シートを広げた時・各種のダイアログ）で、閉じる（×・‹ 戻る）がいつでも見えて押せるようにする：
  1. 読み込み中・3D を指で回している最中・下のシートを上まで引いた時でも、閉じるが隠れない・反応する（重なりの順と、指の操作の取り合いを直す）
  2. 画面の上に固定（iPhone のノッチ・ダイナミックアイランドを避ける）。押せる大きさ44px以上
  3. 3D は × のほかに、左の端から引いても閉じる。iPhone の戻る操作（ブラウザ・ホーム画面のアプリ）でも閉じる
  4. 読み込みに失敗した時も閉じるが残る
- テスト：上の場面それぞれで × を押すと閉じる（読み込みを止めた状態・シートを上まで引いた状態・3D を回している途中）
- 見た目はほぼ今のまま。仕上がったら PM が自動で反映する

## PM から積んだ次の仕事（11/22 18時55分、羽田の3D に地上の機体・見やすく。本人「地上の機体も写して、もっと見やすく、改善して」）※checkin/a3-ground で。 → PR #180 で作った（161f716・報告 report-a3-ground.md）。本番は本人が写真を見て OK してから
- 地上の機体：live_positions には ground（地上）の機体がある（airport-traffic の 235行目あたり）。3D と下の一覧に、駐機場・誘導路・滑走路の上の機体を出す。向き（trk）どおりに置き、止まっている・動いているで見分ける（動いている機体は小さな矢印か光）。今の「地上の機体はまだ出ません」の文は消す。返す側（関数）で地上が落とされていれば、データ担当への依頼にせず、関数の返す形を足すところまでこの回でやってよい（表は変えない。変えるなら data.md に依頼）
- 見やすく：
  1. 機体の大きさ：全体の視点では実寸だと小さすぎるので、遠いほど少し大きく見せる（最小の見た目の大きさを決める）
  2. 札：重ならないように間引く・近い順に。押すとその機体を選び、下の一覧も同じ機体に合わせる。札の字は13px以上
  3. 地上の機体は札を出さず、押した時だけ便名
  4. 夜は機体の輪郭を少し明るく、背景との差をつける
  5. 下の一覧に「地上 ○機」を分けて出す
- 重さ：地上の機体が増えても 30fps 目安（遠い地上機は簡単な形に）
- 確かめ方：今の本番と並べた比べ写真（全体・管制塔 × 昼・夜。地上の機体が多い時間）を report に。PM が本人に見せて OK のあと反映

## PM から積んだ次の仕事（11/22 19時、運用の「今日の遅れ」にも絞り込み。本人「今日の遅れもフィルター機能をつけて」）※checkin/delay-filter で（a3-ground とは別の回）→ PR #179 で作った（f859b1e・報告 report-delay-filter.md。一覧はデータ担当の 'bad' 待ち）
- 運用タブの「遅れ」の専用ページ（今日の遅れ・欠航の一覧）に、図鑑と同じピル型の絞り込みを付ける（PM のおすすめで決めた）：
  1. 種類：すべて・遅れ・欠航（それぞれ数を小さく）
  2. 向き：出発・到着
  3. 航空会社：一覧に出ている会社だけをピルで（JAL・ANA・スカイマーク…。多いときは横にすべらせる）
  4. 遅れの長さ：30分以上だけ（スイッチ1つ）
- 絞り込みは端末に覚える。0件のときは「この条件の便はありません」の1枚。ほかのページの見た目と同じ形なので画面案は待たない
- テスト：それぞれの絞り込みで数が合う・0件の1枚・字13px以上・はみ出しなし。仕上がったら PM が自動で反映する

## PM から積んだ次の仕事（11/22 22時5分、いろいろな物の順番を入れ替えられるように。本人「あといろんなやつの順序を入れ替えられるように」）※checkin/reorder で
- 11/20 に「並べ替えはなし（隠す・出すだけ）」と決めていたのを、本人の今回の言葉で「並べ替えもできる」に変える
- 入れ替えられるようにする所：
  1. 運用タブの一覧のカード（今の隠す・出すの lo の設定に順番を足す）
  2. ホームのシートのカード（空港のカード・いちばん近い・ピン止めした空港・修行・撮影など、ホームに並ぶもの）
  3. 図鑑・運用の専用ページの中のピル（絞り込みの並び）は今回はしない
  4. ホームの空港のカードの切り替えのピル（着陸・離陸・特別塗装機・遅れ）は撮る人用担当が作っている（satsuei/home-card-switch）。同じ並べ替えの部品を使えるように、部品を1つにして satsuei.md に使い方を書く
- やり方（PM のおすすめ）：一覧の右上の「並べ替え」を押すと編集の形になり、各カードの右に「≡」のつまみ。長押しして上下に動かす。iPhone のアプリでも指で動かせること。キーボードや読み上げでは「上へ・下へ」のボタン
- 順番は端末に覚える（ログインしている人は、今の lo と同じ所にも覚えて別の端末でもそろう）。「はじめの並びに戻す」も
- 見た目は今のカードのまま（つまみが出るだけ）なので画面案は待たない。テスト：動かすと順番が変わる・開き直しても残る・戻すで戻る。仕上がったら PM が自動で反映する

## PM から積んだ急ぎの仕事 →【済み PR #185】（11/23 0時、案B（a3-ground-b #181）と今日の遅れの絞り込み（#182、本番に入った）を合わせると t165 が落ちる）※checkin/a3-ground-merge（PM が main と #181 を合わせて push した）に足す
- t165 を1本で流しても落ちる：「NG 3 開き直しても絞り込みは同じ（遅れ・到着・スカイマーク・30分以上）」と「Page.evaluate: TypeError: Cannot read properties of null (reading 'click')」。#182 だけのときは通っていた
- #181 の変更（airport-traffic の答えに ground・運用の一覧の数の出し方など）が、遅れの専用ページか t165 の作り物のデータとぶつかっていると見ている。どちらが正しいかを見分けて直す（遅れの絞り込みの動きは #182 のまま守る）
- e2e の全部（特に t160・t161・t165・t166）と ops を通す。仕上がったら PM が自動で反映する（案B は本人 OK 済み）

## PM から積んだ次の仕事 →【済み PR #189（別の回の案 #192）】（11/23 14時20分、羽田の3D の機体をリアルな3Dモデルに。本人「３Dモデルをリアルなものにして」）※checkin/a3-models で。本番は本人が前後の写真を見て OK してから → PR #189 で作った（f0c103a7・報告 report-a3-models.md）
- 機体：今の簡単な形をやめて、本物に近い3Dモデル（glTF）にする。羽田に多い機種から：787-8/9・777-300ER・767-300・737-800・A350-900・A321neo・A320。胴体の太さ・主翼の後退角とウイングレット・エンジンの数と形・尾翼・窓の列・車輪（地上の機体）まで分かるように
- 使うモデルは、改変と再配布が認められたもの（CC0 か CC BY。CC BY は出典を3D の角に出す）だけ。規約の原文を確かめて report に書く。見つからない機種は手で作る（FAA の大きさの表 #72 に寸法を合わせる）
- 色：航空会社ごとの大まかな色分け（白の胴体＋尾翼の色）まで。ロゴ・社名の文字・公式の塗装の絵は入れない（決定事項：ロゴは提携後）
- 見た目：金属っぽい材質（PBR）・空と太陽の映り込み・地面への影・夜は窓と翼端の灯り。今の滑走路の灯り（#172）とは合わせる
- 重さ：全部で増えるのは 3MB 以内。遠くの機体は軽い形に切り替える（LOD）。iPhone で 30fps を保つ。「軽い」設定では今の簡単な形のまま
- 写真：前後の比べ（全体・地上の駐機場・寄り・夜）を shots-a3-models/ に。テスト：t142・t165・tests/ops が通ること

## PM から積んだ次の仕事（11/23 14時25分、3Dモデルを容量の制限なしで1回試す。本人「一度容量の制限なくやってみて」）※checkin/a3-models-max で（14時20分の checkin/a3-models とは別の回。比べる用） → PR #191 で作った（1b2af495・報告 report-a3-models-max.md）
- 14時20分の節と同じ中身で、「全部で 3MB 以内」「遠くは軽い形（LOD）」「30fps」の縛りを外す。いちばんリアルに見えるもの（細かいモデル・高い解像度の材質・影の質）を優先する
- ロゴ・社名なし、モデルは CC0／CC BY だけ、は変えない
- 報告に、増えた容量（MB）・読み込みにかかる時間・iPhone 幅でのおおよその fps を書く（本人がどこまで重くしてよいか決めるため）
- 写真は shots-a3-models-max/（全体・駐機場・寄り・夜）。a3-models の写真と同じ視点で撮る

## 下の担当からの依頼 →【済み PR #194】（11/23 経営担当・keiei/hide #190 から。PM が積んだ。急がない・a3-models の後でよい）
- チェックインの直後の一言で、行事のボーナス（`bon.map(... 経営の資金 ...)`）は `keieiShown()` が false の間は出さない（ボーナスはサーバーで今までどおり貯まる）
- 図鑑の見本の説明「地方の色は空港の守り神の色です」は、経営を隠している間は守り神に触れない言い方に

## PM から積んだ次の仕事 →【済み #189 に 76ef4df1】（11/23 22時、3D の機体：#189 にやわらかい影だけ足す。本人 OK 済み）※checkin/a3-models（#189）に足す。テストが通れば PM が自動で反映
- #191（a3-models-max）から「やわらかい影（PCFSoft）・見ている所に寄せる範囲（a3ShadowFollow）」だけを #189 に移す。影の細かさは 2048 から始め、重ければ下げる。形・絵・材質・LOD・質の自動の下げは #189 のまま
- 測る：駐機場の1コマを描く時間（今の本番 342ms・#189 374ms）。今の本番の 1.3倍（約445ms）以内に収める。超えるなら影の細かさ・範囲を下げる。GPU のメモリも報告に
- 「軽い」表示と質 0 では今の影のまま
- テスト：t168・t142・t160・t161・t164・t165・t166・tests/ops。写真：shots-a3-models/ に影を足した後の cmp_close_day・cmp_apron_day・vs_shadow（足す前と後）
- #191 と #192 は PM が閉じる（ブランチは残す）

## PM から積んだ次の仕事 →【済み PR #198（480346b9）】（11/24 4時15分、改善担当の見回り sweep-1124 から。写真はブランチ kaizen/sweep-1124 の docs/pm/report-sweep-1124-shots/）※checkin/sweep-1124 で。テストが通れば PM が自動で反映（3D の見た目が大きく変わる所は前後の写真を報告に）
- 【大】3D の「管制塔」の視点で手前のターミナルの屋根が画面の下半分をふさぐ（02・02b）。カメラを管制塔の上（約115m）・少し滑走路側へ、または near を広げて手前の屋根を切る。夜の屋根は暗い灰色に。確かめ方：昼・夜で 34R/34L と 05/23 の滑走路の灯りが画面の上半分に入る
- 【中】375×667 で機体を選んだシートの「この機体から見る」が画面の外（03）。シートを中身の高さまで上げるか、ボタンを札の上へ
- 【中】3D の「機体」のシートで × が「4機」に重なり、ピルが前の視点のまま（04）。数を左へ移すか隠す、選ぶ途中はピル「機体」を押した形、× で閉じたら前の視点へ
- 【中】運用の一覧の「地図 0機」は空の機体だけ（3D は「2機（地上2）」）。地図のカードの単位を「空 0機」に
- 【中】ホームの並べ替えの入口：「並べ替え」を運用と同じ白いピルに、シートの下のリンクを「並べ替え・出すものを選ぶ ›」に、マイページの「ホームに出すもの」の補足にも「並べ替え」
- 【小】3D の視点のピルの高さ44・「出典 ⓘ」の押せる所44×44・補足13px。遅れの専用ページの札と出典を13px、押せない時間の札は影なしの形に、リンクの色をそろえる。デモの帯の「消えま／す」の折れ（補足を「（本番とは別の記録）」に）

## PM から積んだ次の仕事（11/24 12時25分、「夏の訪問」「四季の空港」の印を外す。本人の指示）→ PR #200 で作った（0975a67f・報告 report-drop-season-marks.md）※checkin/drop-season-marks で。テストが通れば PM が自動で反映
- 外す（src/index.html）：搭乗券の `${SEASONS[seasonOf(t)]}の訪問` の印と「四季がそろった」（6827〜6838 あたり）／実績の「四季の空港」season1・「四季めぐり」season10（9678・9679）と fourSeason の数え（9755〜9756）／空港の詳しい画面の四季の表示（9493 あたりの ss）
- 残す：振り返りの「春夏秋冬それぞれの訪問回数」（11146 の chips）は数字なので残す。経営の季節（co3 の season）には触らない
- 実績の数が2つ減っても、もらった数・全体の数・％・バッジの一覧が壊れないように。すでに「四季の空港」を取った人の表示が残らないこと（計算だけなので記録は消えない）
- テスト：どの画面にも「の訪問」「四季がそろった」「四季の空港」「四季めぐり」が出ない・実績の画面が開ける・既存の e2e が通る。却下済み「季節のスタンプ」の決定とそろえる

## PM から積んだ次の仕事（11/24 12時30分、3D の機体を容量を気にせず最高の質に。→ PR #203 で作った（c2ee8c56・報告 report-a3-hq.md）。本人「３Dモデルはもっと容量を気にせず，高いクオリティにして」）※checkin/a3-hq（main から）。本番は本人が前後の写真を見て OK してから
- 容量の縛りはなし。#191（checkin/a3-models-max、ブランチは残っている）の細かい形・材質・影の仕組みを、今の main（#195 の形・#199 の管制塔の視点）の上に移し、さらに作り込む
- 形：機首と操縦席の窓・ドアの線・主翼のフラップの覆いとスポイラーの線・エンジンのファン（前から見える羽根）と排気口・主脚と前脚の細部（地上の機体）・翼端（787 の反った翼端・A350 の曲がった翼端・737 のスプリットシミタール）・尾翼の付け根。機種の寸法は FAA の表（#72）に合わせる
- 材質：細かいパネルの線と汚れの絵（手で作る・高い解像度でよい）・胴体の白の照り返し・エンジンの金属・窓の映り込み。空の映り込みは CC0 の環境の絵（Poly Haven など。出典と規約の原文を report に）
- 光と仕上げ：やわらかい影（細かく）・物の隙間の影（SSAO）・夜の灯りのにじみ（bloom）・ふちのギザギザ消し。夜は客室の窓・翼端灯・衝突防止灯の点滅・着陸灯
- 色：航空会社ごとの大まかな色分けまで。ロゴ・社名の文字は入れない（決定事項）
- 落ちないように：古い iPhone で fps が下がったら自動で質を下げる仕組みは残す（「軽い」設定は今のまま）。最初の読み込みが長い間は「読み込み中」を出す
- 報告に：増えた容量・読み込みの時間・iPhone 幅での fps・GPU のメモリ。写真は shots-a3-hq/（全体・駐機場・寄り・夜・今の本番との比べ）。テスト：t142・t160〜t168・tests/ops

## PM から積んだ次の仕事 その1 →【済み PR #207（ad3ed46e）】（11/24 14時30分、アプリ全体の見直し A の回から。ブランチ kaizen/sweep-all-a の docs/pm/report-sweep-all-a.md）※checkin/sweep-all-1 で。テストが通れば PM が自動で反映
- 【大】マイページの頭の札と成績の「これまでのパスポート」（これまで・年ごと）のフライト・距離・飛行時間・空の上から「車など」と記録帳の便を外す（11/11 の決定）。ホームとフライトの日誌と同じ数え方の関数にそろえる。デモで「30フライト・24,017km」（A の1番・B の補い）
- 【大】「記録を書き出す」の説明：PM の決定は①。「記録はサーバーに保存されていて、機種を変えてもログインすれば戻ります。書き出しは手元の控えです。」にし、「まとめて取り込む」への言及は消す。データの欄の見出しを「データとバックアップ」に（A の2番）
- 【中】デモの見本の記録の日付を開いた日に合わせてずらす（いちばん新しい便が昨日）。ホームの「今日の印」・修行の「今日」がそろうように（A の5番）
- 【中】375×667 の新規登録の同意の画面で「同意してはじめる」を画面の下に固定（A の6番）
- 【中】ログイン・新規登録・名前・同意・位置・マイページの補足の字の色を 4.5:1 以上に（A の7番）
- 【小】はじめの案内の3枚目の「とばす」を外して「はじめる」1つに。3枚目に「運用（空港の今）や修行も、ログインしなくても見られます」（A の8番）
- 【小】押せる所44px（「アドレスを直す」「コードを送り直す」はピルに・「あとで」・マイページの色の丸・規約のリンク）（A の9番）
- 【小】印の共有画像に小さく「非公式アプリ」（A の10番）
- 【小】明朝体（--mincho の「そらメモ」・印の「HND」）をゴシックにそろえる。PM の決定（デザインの原則「モダンなゴシック体に統一」）（B の10番）
- 成績の修行の部分（A の3番）とマイページのタイル（A の4番）は、本人の OK・デザイン担当の案のあとなので今回はやらない

## PM から積んだ次の仕事 その2 →【済み PR #209（bb226c2a）】（11/24 14時30分、アプリ全体の見直し B の回から。ブランチ kaizen/sweep-all-b の docs/pm/report-sweep-all-b.md）※checkin/sweep-all-2 で（その1 とは別の回が同時に進める）。テストが通れば PM が自動で反映
- 【大】運用のデータが読めなかったとき、遅れ・短冊・撮る人のページに「読み込めませんでした・もう一度」のピルを出し、10秒ほどで1回だけ取り直す（B の2番）
- 【大】ホームのシートを引き上げたら「最近の印」が見える位置まで出し、近くの空港の一覧は勝手に開かない（B の A の補い）
- 【中】運用の一覧のカードと専用ページの数をそろえる：特別塗装機・定時・空の機体（地図⇔3D）。そろえられないものはカードに範囲の札（B の3番）
- 【中】呼び方：3D の「B 滑走路へ」→「22（B）へ」、「短冊」のページの頭に1行の説明、フライトの「記録帳」→「日誌」、成績の「飛行時間」→「空の上」（B の4番）
- 【中】電波がないとき滑走路のカードは「—」、一覧の上に「電波がありません・最後に読んだ ○時○分」（B の5番）
- 【中】遅れのページは開いたら今の時刻の行へ送る（B の6番）
- 【中】知らせの画面：「3レター」→「HND のような3文字」、「乗る便」のカードを押せる形（乗る便を選ぶ ›）に、注意の文をカードの中へ。ピン止めの保存はデータ担当の data/sweep-all の関数が入ったらアカウントへ（それまでは「機種を変えると消えます」）（B の7番）
- 【小】運用の押せる所を44px・1日の山の時刻・定時の便数などの字を13px（B の9番）
- 3D の中（checkin/a3-hq が進行中）には触らない。呼び方の「22（B）へ」だけは a3-hq とぶつからない所で

## PM から積んだ次の仕事 その3 →【済み PR #211（その4 と一緒）】（11/24 14時50分、成績の修行の部分を入口1枚に。本人 OK 済み「消してカード1枚に」）※checkin/stats-shugyo-card で。checkin/sweep-all-1 が main に入ってから始める（同じ成績の所を触るため）。テストが通れば PM が自動で反映
- マイページ → 成績の「ステータスの目安」「修行の計画」「修行のまとめ」を外し、「修行の画面を開く」のカード1枚（今のポイントの大きな数字だけ）に置き換える。「あの日の空」は成績の別の行へ（アプリ全体の見直し A の3番）
- 修行タブの中身は変えない（修行担当の持ち場）。修行担当の帳面 shugyo.md に一言書く
- テスト：成績が開ける・修行のカードを押すと修行タブへ・修行の3つの見出しが成績に出ない・既存の e2e が通る

## PM から積んだ急ぎの仕事（11/24 16時、a3-hq を main と合わせると t168 が1件だけ落ちる）※checkin/a3-hq に足して push（PR #203）。直ったら PM が自動で反映（本人 OK 済み）→ PR #203 に足した（111c901e・報告 report-a3-hq-t168.md）
- main（#200・#201・#204 まで）と合わせた所で、t168 の「管制塔の視点：近い7機種の機体は細かい形を出す」が単独でも2回続けて NG。中身は `{}`＝管制塔の視点で 1.6km 以内の機体が0機（near が空なので check が偽になる）
- #199 で管制塔のカメラを上・滑走路側へ動かしたことと、テストの作り物の機体の位置（SE）が合っていない見込み。アプリが正しければテストの作り物の位置か見る距離を直し、アプリの不具合ならアプリを直す（どちらかを報告に）
- t168 は単独で 850〜1000秒かかり、run_all.py の1本 240秒の上限を超える。t168 だけ上限を延ばすか、テストを分けて run_all で最後まで流れるように

## PM から積んだ次の仕事 その4 →【済み PR #211（889f484f・報告 report-mypage-b.md）】（11/24 16時20分、マイページを案B のタイルに＋その3＋ピン止めをアカウントへ。本人 OK 済み「案B」「アカウントにも保存する」）※checkin/mypage-b で。main に sweep-all-1・sweep-all-2・data/sweep-all が入ってから始める（PM が知らせる）。テストが通れば PM が自動で反映
- 画面案：ブランチ design/mypage-tiles の B1（成績を横長の1枚＋修行・知らせの2枚、タブにある画面はタイルにしない、設定は5行の目次＝表示の編集・データとバックアップ・表示と色・アカウント・詳しい設定、押すと1枚のページ）と B2（データとバックアップのページ）。docs/pm/report-mypage-tiles.md
- その3（成績の修行の部分を入口1枚に）も一緒に
- 知らせのピン止め：ログインしているときは rpc('my_pins') で読み、変えたら rpc('my_pins_put', {p_pins, p_spot, p_rev})。はじめてログインして端末にピンがありサーバーが null なら端末の分を上げる。conflict はサーバーの分を出し直す。「アカウントへの保存は準備中」「機種を変えると消えます」の文を外す（data/sweep-all の report-sweep-all-data.md）
- 写真：390・375 の前後。テスト：成績・修行の入口・目次の各ページ・ピンの保存と読み直し・既存の e2e

## PM から積んだ次の仕事 →【済み PR #215（856d8a2a・報告 report-a3-free.md）】（11/25 3時20分、羽田の3D を自由に動かす。本人「案B、管制塔もピルに残す」）※checkin/a3-free（main から）。本番は本人が前後の写真を見て OK してから
- 画面案：ブランチ design/a3-free（docs/design/a3-free/、report-a3-free.md）。形は案B（B1 自由・B5 立つ・B6 飛ぶ）、追うは A3a／A3／A3b の中身を案B の形で
- 4つの見方を画面の下の4つのボタン（自由・追う・立つ・飛ぶ）で切り替える：
  1. 自由：1本指で回す・2本指で寄る離れる／ずらす／傾ける。地面の下と空港から遠すぎる所には行かない。右上に「全体に戻す」。はじめての1回だけ指の動きの案内
  2. 追う：機体を選ぶシート→後ろ・横・前に付いて一緒に動く。指で角度と距離。機体が消えたら今の位置のまま自由へ（下に一言と「ほかを追う」）
  3. 立つ：おすすめの場所（管制塔・第1／第2ターミナルの展望デッキ・C 滑走路の南の端）か、3D の地面を押した所に目の高さ 約1.6m で立つ。指で見回す・2本指はズーム（目の位置は動かない）
  4. 飛ぶ：左のつまみで前後左右・右で上下と向き。高さは大きな数字、空港の上 約1,000m が上限（A6b）
- 本人の指示：上のピルに「管制塔」を残す（押すとその場で管制塔から見る＝立つの管制塔と同じ。今の高さ 約118m）。「全体」は自由のはじめの位置、「機体」は追うへ
- 飛ぶのつまみと下の4つのボタンが重ならないように（案B の迷った点）。375×667 で押せる所 44px・はみ出しなし
- 「閉じる」（左上の ×）はどの見方でもいつも押せる。最高の質（#212）と自動で質を下げる仕組みはそのまま
- 写真：shots-a3-free/（4つの見方・管制塔のピル・はじめての案内・390 と 375・今の本番との比べ）。テスト：指の操作（回す・寄る・ずらす）・4つの切り替え・追うで機体が消えたとき・飛ぶの上限・t142・t160〜t168・tests/ops

## PM から積んだ次の仕事（11/25 5時10分、アプリ全体の見直し 2回目から。→ PR #217 で直した（4d874c69・報告 report-sweep-1125-checkin.md）。ブランチ kaizen/sweep-1125 の docs/pm/report-sweep-1125.md）※checkin/sweep-1125 で（checkin/a3-free とは別の回）。テストが通れば PM が自動で反映
- 【大】成績のパスポート（passStats・passCard）の「空の上」を、フライト（fbSum・fbMin）と同じ数え方にする。（推定）の札も同じ決め方に。デモの30便で両方 49時間20分（1番）
- 【大】運用の「遅れ」のページを開いたとき、「いまごろ」の行が上の浮いたボタンの下（約64px）に来る位置に送る。ボタンの帯に背景を付けるか絞り込みの行を帯の下に貼り付ける。10行未満なら送らない。390×844 と 375×667 で重ならない（3番）
- 【中】図鑑の「図鑑の見方が3つになりました…」は前の見方を使ったことがある人にだけ出す・12月末で出さない（5番）
- 【中】フライトの地図の一覧「乗った区間」から車などを外す。車などは下に別の1行（6番）
- 【中】飛行場・滑空場・ヘリポートの図鑑：名前を字の途中で折らない（keep-all・2行まで）、地方の見出しの重なった札を外す、題と絞り込みの右にツメの幅（7番）
- 【中】ウェブでも電波がないときにホームの nvNetHome を出し、保留した印をシートに1行（9番）
- 3D（checkin/a3-free）には触らない

## PM から積んだ次の仕事 →【済み PR #219（7a39dcb9・報告 report-drop-newyear.md）】（11/25 13時、「元日の印」を外す。本人の指示「外す」）※checkin/drop-newyear で。テストが通れば PM が自動で反映
- 実績の「元日の印」を外す。分類「時間と季節」は季節の言葉を使わない名前（例「時間」）に変え、中身に季節の印が残っていないか見る（11/24 の季節の印を外した決定・却下済み「季節のスタンプ」とそろえる）
- 計算だけなので消える記録はない。実績の数が減っても％・一覧が壊れないこと
- テスト：どの画面にも「元日の印」「時間と季節」が出ない・実績の画面が開ける・既存の e2e

## PM から積んだ急ぎの仕事（11/25 15時、t30 が今の main で単独でも落ちる） → PR #221 で直した（c4f4c7d8・報告 report-t30-fix.md）※checkin/t30-fix で（drop-newyear とは別の回でもよい）。テストが通れば PM が自動で反映
- t30 の `openMyPage("adv")` のあと `#toggleDemo`（デモの「開始」）が見えないまま押せない（30秒）。11/25 1時の反映（#218）の直前の流しでは通っていた
- マイページ案B（#213）の「詳しい設定」のページや、#218（sweep-1125 の画面の直し）で、デモの開始ボタンが隠れていないか（本物の不具合なら使う人もデモを始められない）。アプリの不具合ならアプリを、テストの作りの問題ならテストを直し、どちらかを報告に

## PM から積んだ次の仕事（11/25 17時25分、小さな動き13個を入れる。本人 OK「全部」）※checkin/micro で。テストが通れば PM が自動で反映
- 見本：ブランチ design/micro の docs/design/micro/（index.html・s1〜s5・report-micro.md）。src/base.css・base.js の作りをそのまま使ってよい
- 入れる：01 押すと縮む／02 タブの点／03 つまみ／04 ピンが刺さる／05 下から出る札（say() の「できた」だけを札に、エラーは今までどおり）／06 骨組み（0.3秒より早ければ出さない）／07 数字の繰り上がり＋1／09 並べ替えで持ち上がる／10 コピーが ✓／11 鈴（ON のときだけ）／12 「もう一度」の矢印1回／13 シートが上がる（行き過ぎない）
- 08（修行の道のりの帯）は修行担当の持ち場なので shugyo.md に頼む（その日はじめて開いたときだけ）
- 振動と音は入れない。prefers-reduced-motion では状態だけ変えて動きなし。今の印のハンコ・半券・運用の広がり・パタパタは変えない
- 土台（01・03・05・06・13）から入れる。テスト：動きを減らす設定で動くものが0・札が2秒で消える・骨組みが早い読み込みで出ない・並べ替えの保存・既存の e2e。390・375 で撮る

## PM から積んだ最優先の仕事 →【済み PR #229（987f3b04・報告 report-stamp-fast.md）】（11/25 17時45分、印を押すときロードが長く画面が固まる。本人「印を押す時、ロードが長くて不安になるし、画面が固まる」）※checkin/stamp-fast で。ほかの仕事より先に。テストが通れば PM がすぐ反映
- まず測る：印を押してから印のハンコが出るまで・画面が止まる（長い処理 50ms 超）所を、Performance と遅い電波（Slow 3G・オフライン・位置がなかなか取れない）でそれぞれ。どこで待っているか（位置の取得・サーバーへの保存の await・成績や図鑑の計算の作り直し・3D／地図の描き直し・画像の生成 など）を報告に表で
- 直す方向：
  1. 押したらすぐハンコの動きを出す（保存を待たない）。サーバーへの保存は後ろで。失敗したら今の保留の仕組み（電波がないときの保留）に入れて「あとで送ります」の札
  2. 位置の取得は、押す前から温めておくか、直近の位置（数十秒以内・精度が足りる）があればそれを使う。待つときは「位置を確かめています」と出し、10秒で区切る
  3. 押したあとの重い計算（成績・図鑑・ホームの帯・共有画像）は印の動きのあとに回し、細かく分ける（requestIdleCallback など）。画面が止まる時間を 100ms 未満に
  4. 待つときは小さな動きの見本の骨組みや札（design/micro）を使い、何をしているか分かるように
- 二重に押しても印が2つにならないこと。記録は消さない
- テスト：遅い電波で押してからハンコまで 0.5 秒以内・長い処理 100ms 未満・保存の失敗で保留に入る・二重押し。直す前と後の数字を報告に。checkin/micro（小さな動き）とぶつかる所は、こちらを先に
- 【11/25 18時20分 追記・本人の答え】固まるのは「ブラウザで、空港で実際に押したとき」（iPhone アプリ・デモではない）。本物の位置の取得（watchPosition／getCurrentPosition の待ち・高い精度の要求）と、ログインしているときのサーバーへの保存・その後の読み直しを特に疑う。ウェブの Service Worker・本番の通信の遅さも測る

## PM から積んだ次の仕事 →【済み PR #238（9eb14811・報告 report-stamp-edge.md）】（11/25 23時、電波・位置が悪いときの続き。本人が Gemini の案を貼った：docs/pm/ext/gemini-offline-1125.txt）※checkin/stamp-edge で（stamp-fast の上・main から）。テストが通れば PM が自動で反映（位置の取り方は変えない。変える所が出たら本人の OK）
- すでに stamp-fast で入ったもの（押したらすぐ・保留・断られたら取り消し・位置の使い回し）は変えない。足すのは次だけ：
  1. iOS の「正確な位置情報」が OFF・位置の許可がないとき：何が足りないかと直し方（設定 ＞ そらメモ（または Safari）＞ 位置情報 ＞ 正確な位置情報）を出すカード。押しても判定できないボタンは出さない
  2. 送信待ちの間：地図のピン・図鑑・数はその場で増やし、図鑑の詳しい所とホームのシートに「送信待ち（14:22 記録）」の小さな札。押すと送り直す。いくつ溜まっても時刻の順に送る（今の保留の仕組みの見せ方）
  3. 送れて確定したら「羽田空港の印が確定しました」の札（design/micro の 05 の形・2秒）
  4. 文の言い方をそろえる：通信が混んでいる「通信が混み合っているため、いまの記録を端末に保存しました。つながり次第送ります。」／位置がずれている「建物の中のため、現在地が少しずれているようです。」／範囲の外「いちばん近い羽田空港まであと 2.4 km です。空港に入るとチェックインできます。」／同じ日にもう一度「本日のチェックインは完了しています。続けて今日の便を記録できます。」／端末の時計のずれ「端末の日時がずれているようです。設定で『自動設定』をオンにしてください。」（エラーの番号や英語は出さない）
- 入れないもの：位置が取れていない・範囲の外なのに「羽田空港として保存する」で通す案（印は現地で押したものだけ・最後の判定はサーバー）。「もう一度位置を確かめる」は今のまま
- テスト：正確な位置 OFF のカード・送信待ちの札と送り直し・確定の札・時刻順・文の言い方。390・375

## PM から積んだ次の仕事 →【済み PR #239（22b6bbbe・報告 report-flight-suggest.md）】（11/25 23時05分、乗る便の候補から1回で記録。本人が貼った Gemini の案の7番）※checkin/flight-suggest で。テストが通れば PM が自動で反映
- フライトの「＋記録」と印のあとの「今日の便を記録」で、いまいる空港（または今日チェックインした空港）の今日の運航情報から、これから出る便・いま着いた便を候補として上に並べ、押せば便名・区間・時刻・機材が入った状態で記録できる（確認の1回だけ）
- 過去の便は「日付＋便名（数字だけでも）」で区間と時刻を補う（flight_history・timetable から）
- 便の一覧の航空会社コードは小さな札（彩度を落とした色・事実の記録として。ロゴは使わない）
- テスト：候補が出る・1回で記録・数字だけの便名で補える・電波がないときは候補なしで手入力へ
