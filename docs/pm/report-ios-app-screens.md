# 報告：iPhone のアプリだけの画面（design/ios-app 2版・11/19 定時の回）

PM から積んだ仕事（11/19 11時55分・本人「おすすめでOK」・決定事項【11/19】）。ブランチ checkin/ios-app（PR #125）に足した。本番には入れていない。

- 変えるファイル：src/index.html（アプリの中だけの画面と文）・ios-app/ios/App/App/Info.plist・tests/e2e/t146.py（新）・web/（組み立て）
- 手順：位置の説明 → 許可しなかった人 → カメラ・マイクの小さい説明 → 電波がない帯 → 隠すもの・代わりの1行 → Info.plist → テスト
- 確かめ方：偽の Capacitor で t146（36項目）・t143・tests/ops・e2e 全体を流し、390×844／375×667 で撮る

## 作ったもの（どれも html[data-native="ios"] のとき＝NATIVE だけ。ブラウザの形と文は変えていない）
1. 位置の説明（I1-v2）：ログインか「デモで試す」のあと、はじめてホームを開くときに1回だけ全画面（#dLocWhy）。ボタンは「次へ」1つ（閉じる・あとでは置かない、Esc も効かない）。「次へ」で @capacitor/geolocation の requestPermissions（iPhone の確認）。もう答えている人（許可・拒否）には出さない。新規登録の流れの「位置の説明」も、アプリでは同じ文と「次へ」1つにした（見たらホームで2回目は出ない）
2. 位置を許可しなかった人（I1c-v2）：ホームの黒いカード（半券）の代わりに「位置が使えないので、チェックインできません」＋設定の道（設定 › アプリ › そらメモ › 位置情報）＋「デモで試す」「設定を開く」。デモ中は出さない。設定アプリから戻ったら（visibilitychange）許可を見直す
3. 半券を押して許可がないと分かったとき（I1e-v2）：小さいシート「印を押すには、位置が要ります」＋代わりの1行
4. カメラの小さい説明（I4c-v2）：はじめて搭乗券を読むときに1回（startCamera の前）。マイク（I4m-v2）は nvPermWhy("mic") を作った（聞く画面は撮る人用の持ち場なので、呼ぶのは撮る人用への依頼）
5. 電波がないとき（I2-v2・I5-v2・I5z-v2）：ホーム・運用・図鑑・フライトの頭に帯。運用は「最後に読んだのは 15:02（北風運用）」（端末の中に読んだ時刻と運用だけを残す。表は変えない）。電波が戻ると帯を消し、運用は気象通報を読み直す。夜は琥珀の線
6. 隠すもの・代わりの1行（I3-v2）：ホーム画面に追加の帯・マイページの行・やり方のシートを出さない。位置・カメラ・保存の文をアプリの文に。通知とマイクの文は PUSH_NG_TXT()・MIC_NG_TXT() にまとめた（下の担当の画面から呼べる）
7. ホームで静かに位置を見る（homeLocStart）：アプリでは WebView の Permissions API が使えないので、@capacitor/geolocation の checkPermissions で見るようにした（geoPermState）。これで許可済みの人のホームに「いまここ」が出る見込み
8. Info.plist：位置の理由の文を「いる場所は印を押すときだけ送り」に（I1b-v2 と同じ）。カメラ・マイクの文も2版にそろえた。iPad も縦だけ（UIRequiresFullScreen）

## src/index.html で変えた関数
- 足した：NV_KEY・nvGet・nvSet・NV_SVG・NV_TXT・PUSH_NG_TXT・MIC_NG_TXT・nvPathHTML・geoPermState・geoPermAsk・nvFocusTitle・nvOpenSettings・nvLocWhyHTML・nvLocWhyMaybe・nvLocNext・nvGeoRefresh・nvGeoApply・nvLocOffSheet・NV_PERM・nvPermWhy・nvLastSave・nvLastText・nvNetRender・nvNetBack（と NATIVE のときだけの online／offline／visibilitychange／click）
- 変えた：homeState・goTab・homeLocStart・save・checkin・homeRecheck・startCamera・renderInstall・doInstall・pushButtonHTML・openOps・setOpsAirport・authRender（location の段）・登録の click（loc-allow）
- HTML：#nvLocOff・#nvNetHome・#nvNetOps・#nvNetBook・#nvNetLog・#dLocWhy・#dNvSheet。CSS：.nvloc・.nvnet・.nvpath・.nvbt・dialog.nvsheet・.auth .nvrow ほか

## 確かめた結果
- t146（新・36項目）すべて成功：ブラウザでは何も出ない・I1 は1回だけで「次へ」で確認・許可済みには出ない・I1c と「デモで試す」・I1e・I4c は1回だけ・電波がない帯と最後に読んだ時刻・隠すもの・字13px以上・押す所44px以上・はみ出しなし（390×844／375×667）・Info.plist
- tests/ops すべて成功。e2e 全体 114／116（t48・t72 は main でも落ちる）
- 写真：docs/pm/shots-ios-app/t146_*（I1・I1c・I1e・I4c・I2・I5・I5z、667 は I1・I1c）
- まだ確かめていないこと（Mac と iPhone で）：「設定を開く」で設定アプリのそらメモが開くか（"app-settings:" を Capacitor が iOS に渡す前提。開かなければ小さなネイティブの部品を足す）・requestPermissions で確認が出るか・オフラインの online／offline が WKWebView で届くか
- 375×667 の位置の説明は、下の2行の注意がスクロールの下になる（デザイン担当の1版の報告と同じ）

## 本人に決めてほしいこと
1. 位置の説明をデモの人にも出す形でよいか（画面案どおり。デモは位置を使わないので、出さない手もある）
2. 電波がないときの運用の「最後に読んだ」は帯の1行にした。カードごとの「読み込めませんでした／もう一度」は、運用タブを一覧＋専用ページにする仕事（checkin/ops-hub）でカードの形が変わるので、そのときに入れてよいか

## ほかの担当への依頼
- 撮る人用（PM から伝えてほしい）：聞く画面（atcRxStart）の getUserMedia の前に `await nvPermWhy("mic")`、失敗の文を `MIC_NG_TXT()` に。撮影の知らせと表示する機体の選び方の通知の文（spPush・spSel の「この端末のブラウザでは使えません…」）を `PUSH_NG_TXT()` に
- 修行（PM から伝えてほしい）：修行の通知の注意（sg-note の「この端末のブラウザでは使えません…」）を `PUSH_NG_TXT()` に
- ピン止め（PR #130）と重ねるとき：K0i・K5n の「iPhone はホーム画面に追加すると届きます」はアプリでは出さず PUSH_NG_TXT() に（チェックイン担当がどちらかが main に入ったあとで合わせる）
