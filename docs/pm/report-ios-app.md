# 報告：iPhone のアプリ（自分用の段）を Mac で動かす手順

PM の指示 11/18 5時50分（本人「全てOK、iPhone は自分用から試してみよう」）・決定事項【11/18】。ブランチ checkin/ios-app・下書き PR #125。作ったものの細かい所と確かめた結果は docs/pm/report-ios-app-base.md。

## 作ったもの（短く）

- ios-app/：Capacitor 8.6.0（Swift Package Manager・CocoaPods なし・iOS 15 以上）。ios/ のフォルダ（Xcode の一式）、組み立てた web/ をアプリの中に写す build_www.mjs（**server.url は使わない**）
- 位置の入れ物：getCurrentPosition／watchPosition を呼ぶ所はすべて navigator.geolocation を通るので、その中身だけをアプリの中では @capacitor/geolocation に差し替えた（capGeoInstall）。呼ぶ所は変えていないので web では今までどおり動く
- 共有（@capacitor/share）・外のリンク（@capacitor/browser）・Info.plist の位置（使用中のみ）／カメラ／マイクの理由の文
- 自分用の段では入れないもの：プッシュ通知・課金（そらメモ＋の申し込みボタンはアプリでは出さない）・ロボット除け（アプリでは飛ばす）
- web の動きとテストは変えていない（e2e 109／111。落ちた t48・t72 は main でも落ちる。新しいテスト t143 18／18・tests/ops 成功）
- 画面が変わる所（許可の前の説明の1枚・オフラインの画面）は作っていない。デザイン担当の design.md に依頼を書いた

## Mac で動かす（ターミナルに1行ずつ貼る）

1. 作業場所に移る
```
cd ~/dev/soramemo
```
2. ブランチを持ってくる（main はそのまま残る）
```
git fetch origin
```
```
git switch checkin/ios-app
```
3. 道具の版を確かめる（node は v22 以上なら v26 でよい。Xcode は 26 以上）
```
node -v
```
```
xcodebuild -version
```
（はじめて Xcode を使うときだけ）
```
sudo xcodebuild -license accept
```
4. アプリの部品を入れて、web をアプリの中に写す（web/ はブランチに入っているので、組み立て直さなくてよい）
```
cd ios-app
```
```
npm ci
```
```
npm run sync
```
最後に「Sync finished」と出れば済み
5. Xcode を開く
```
npm run open
```

## Xcode で ▶ まで

シミュレーターで動かす（Apple ID は要らない）
1. Xcode の上の真ん中（「App ›」の右）を押して「iPhone 17」などを選ぶ
2. 左上の ▶ を押す。はじめは部品の取り込み（左下に Resolving Package…）で数分かかる
3. シミュレーターの中でそらメモが開く。「デモで試す」で中を見られる。位置はシミュレーターのメニューの Features → Location → Custom Location… で羽田（35.5494／139.7798）を入れる

自分の iPhone で動かす（無料）
1. iPhone を USB でつなぎ、iPhone に出る「このコンピュータを信頼」を押す
2. Xcode の左の一覧でいちばん上の「App」→ 真ん中の「Signing & Capabilities」→ Team で自分の Apple ID を選ぶ（なければ「Add an Account…」で Apple ID を入れ、「（名前）(Personal Team)」を選ぶ）
3. 上の真ん中で自分の iPhone を選ぶ
4. iPhone の 設定 → プライバシーとセキュリティ → デベロッパモード を ON（iPhone が再起動する）
5. ▶ を押す。iPhone に「信頼されていない開発元」と出たら、iPhone の 設定 → 一般 → VPNとデバイス管理 → 自分の Apple ID →「信頼」→ もう一度 ▶
6. 無料の形では7日で開けなくなる。そのときはつないでもう一度 ▶

web の直しをあとで取り込むとき
```
cd ~/dev/soramemo && git pull && cd ios-app && npm run sync
```

## うまくいかないときの見方

| 出たもの | 見る所・すること |
|---|---|
| `npm ci` で止まる | `node -v` が v22 以上か。だめなら `rm -rf node_modules` のあと `npm ci` をもう一度 |
| `npm run sync` で「web/index.html がありません」 | ブランチが checkin/ios-app か（`git status -sb`）。`cd ~/dev/soramemo` からやり直す |
| Xcode で「Missing package product」「Package resolution failed」 | Xcode のメニュー File → Packages → Reset Package Caches。だめなら Xcode を閉じて `npm run sync` → `npm run open` |
| 「Signing for "App" requires a development team」 | 上の「自分の iPhone で動かす」の2（Team を選ぶ） |
| 「Failed to register bundle identifier」 | Signing & Capabilities の Bundle Identifier を `jp.soramemo.app.自分の名前` のように変える（ほかの人と重なっている） |
| 白い画面のまま | Xcode の下の欄（▶ のあとに出るログ。出ていなければメニュー View → Debug Area → Activate Console）の赤い行を写真に撮って送ってほしい。Mac の Safari の 開発 → シミュレーター（または iPhone）→ そらメモ で中の画面のエラーも見られる（Safari の設定 → 詳細 →「Web 開発者用の機能を表示」を ON） |
| 位置の許可が出ない・印が押せない | iPhone の 設定 → そらメモ → 位置情報 が「使用中のみ」か。シミュレーターは上の位置の入れ方 |
| ログインのコードが送れない | 本番でロボット除けが ON だとアプリの中では送れない（自分用の段ではロボット除けを飛ばしているため）。今は「デモで試す」で見る。下の「本人に決めてほしいこと」 |
| 地図が出ない | 電波があるか（地図の部品はまだ毎回ネットから読む。アプリの中に入れるのは次の段） |

困ったときは、出た文の写真と、どの手順の何番かを PM に送ってもらえれば、次の回で直す。

## 本人に決めてほしいこと

1. アプリの中のログイン：本番でロボット除けが ON なら、自分用の段は「デモで試す」で見るか、ログインも試せるようにするか（データ担当に ON かを確かめてもらう依頼を出した）
2. 画面の向きは縦だけでよいか
