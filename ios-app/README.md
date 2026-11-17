# そらメモ iPhone のアプリ（Capacitor 8）

決定事項【11/18】作り方 A：今の web（src/index.html を組み立てた web/）を Capacitor で包み、位置・共有・外のリンクだけネイティブの部品。まず自分用（シミュレーターと自分の iPhone・無料）。

- 中身は web と同じ。web/ を www/ に写し、capacitor.js を1行足すだけ（build_www.mjs）
- 本番の https://soramemo.jp を読み込むだけの形（server.url）にはしない
- アプリの中だけで働く入れ物は src/index.html の `NATIVE`・`capPlugin`・`capGeoInstall`・`capShareInstall`・`capLinkInstall`（ブラウザでは何もしない）
- アプリの中では使わないもの：サービスワーカー・Web Push（APNs ができるまで）・ロボット除け（Turnstile）
- 位置は「使用中のみ」。使う理由の文は ios/App/App/Info.plist

## Mac で動かす（ターミナルに1行ずつ貼る）

```
cd ~/dev/soramemo
```
```
git fetch origin && git switch checkin/ios-app && git pull
```
```
node -v
```
（v22 より古ければ `brew install node@22 && brew link --overwrite --force node@22`）
```
cd ios-app && npm ci && npm run sync
```
```
npm run open
```
Xcode が開いたら：上の真ん中で「iPhone 17」などのシミュレーターを選んで ▶。

自分の iPhone で動かすとき：
1. iPhone を USB でつなぎ、Xcode の上の真ん中でその iPhone を選ぶ
2. 左の「App」→「Signing & Capabilities」→ Team で自分の Apple ID（Personal Team）を選ぶ（なければ「Add an Account…」）
3. iPhone の 設定 → プライバシーとセキュリティ → デベロッパモード を ON（再起動する）
4. ▶ を押す。はじめは iPhone の 設定 → 一般 → VPNとデバイス管理 で自分の Apple ID を「信頼」
5. 無料の形では7日で開けなくなるので、そのときはもう一度 ▶

web の直しを取り込むとき（web/ はブランチに入っている）：
```
cd ~/dev/soramemo && git pull && cd ios-app && npm run sync
```
