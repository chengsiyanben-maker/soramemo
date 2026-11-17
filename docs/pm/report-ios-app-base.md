# 報告：iPhone のアプリの土台（Capacitor 8・自分用の段）

ブランチ checkin/ios-app（main 61ba9c7 から）・下書きのプルリクエスト。決定事項【11/18】（作り方 A・まず自分用・そらメモ＋はアプリの中で売らない・ロボット除けは自分用の段では使わない）と、PR #124 の計画の「7. 順番の案」の4。本番には入れていない。

## 作ったもの

1. **ios-app/**（新しいフォルダ。web とは別に置き、ルートの package.json は増やしていない）
   - package.json：Capacitor 8.6.0（core・ios・cli）、@capacitor/geolocation 8.2.4・share 8.0.3・browser 8.0.5（版は決め打ち）
   - capacitor.config.json：appId `jp.soramemo.app`・名前「そらメモ」・webDir `www`。**server.url は使わない**（本番を読むだけの形にしない）
   - build_www.mjs：組み立てた web/ を www/ に写し、`capacitor.js` を config.js の前に1行足す。sw.js・now*.html・og/・robots・sitemap・CNAME は入れない（約2MB）
   - ios/：`cap add ios` で作った Xcode の一式（Swift Package Manager・CocoaPods なし・iOS 15 以上）
     - Info.plist：言語 ja・縦だけ・位置（使用中のみ）／カメラ（搭乗券）／マイク（管制の聞き取り）の使う理由の文・暗号の申告（使わない）
     - アイコンは今のホーム画面のアイコン（web/icon.svg）を角なしの 1024px に、起動の画面は無地（#EAF0F5）
   - README.md：本人が Mac で動かす手順（下の「本人がすること」と同じ）
2. **src/index.html**（アプリの中だけで働く薄い入れ物。ブラウザでは何もしない）
   - 足した関数：`NATIVE`・`capPlugin`・`capGeoErr`・`capGeoPos`・`capGeoOpts`・`capGeoInstall`・`capShareInstall`・`capOpenUrl`・`capLinkInstall`・`CAP_ON`（SERVER の定義のすぐ下）
   - 位置：navigator.geolocation の中身だけを @capacitor/geolocation に差し替え（呼ぶ所の7か所はそのまま。下の担当のコードも変えずに動く）。拒否は code 1・時間切れは 3 でブラウザと同じ
   - 共有：字と URL は @capacitor/share。閉じたら AbortError（今の「閉じたら何もしない」が効く）。画像つき（シェアの画像）は WebView の navigator.share のまま
   - 外のリンク：target=_blank と window.open の外の URL はアプリの中のブラウザ（@capacitor/browser）
   - 変えた関数：`captchaOn`（アプリの中は false）・`pushOK`（アプリの中は false）・`pushButtonHTML`（アプリの中は「アプリの通知は準備中です。」の1行）・`renderPlusSettings`（アプリの中は申し込み・解約のボタンを出さない。加入中の特典はそのまま）・サービスワーカーの登録（アプリの中ではしない）
   - `<html data-native="ios">` を付けた（デザイン担当の画面案が来たら、アプリで隠すものを CSS で隠せる）
3. **tests/e2e/t143.py**（新・18項目）：偽の Capacitor で、位置（1回・見張り・止める・拒否）・共有・外のリンク・ロボット除けと通知を使わない・そらメモ＋のボタン・www/ の中身。ブラウザでは何も変わらないことも

## 確かめた結果

- t143：18／18 OK（写真 docs/pm/shots-ios-app/ の t143_app_home・t143_app_login・t143_web_home。ホームとログインの見た目は web と同じ、ログインに Turnstile の箱が出ない）
- tests/ops：すべて成功
- e2e の全体：109／111（落ちたのは t48（pdf417gen がない）と t72（特別塗装機を #opsSpecial から開く）で、どちらも main でも落ちる前からのもの。前から落ちていた t123 はこの回は通った。運営コンソールのテスト4本は手元にないので飛ばした）
- `npx cap add ios` は Linux で通った（Package.swift に3つの部品）。**Xcode でのビルドと iPhone での動きはまだ確かめていない**（Mac がないため。本人の Mac で初めて動く）
- tests/sql は表を変えていないので流していない

## 本人がすること（Mac・ターミナルに1行ずつ）

```
cd ~/dev/soramemo
```
```
git fetch origin && git switch checkin/ios-app && git pull
```
```
cd ios-app && npm ci && npm run sync
```
```
npm run open
```
Xcode で「iPhone 17」などのシミュレーターを選んで ▶。自分の iPhone は ios-app/README.md の手順（Personal Team・デベロッパモード・信頼。無料は7日ごとに ▶ し直し）。

## 本人に決めてほしいこと

1. **アプリの中のログイン**：本番の Supabase でロボット除け（CAPTCHA）が ON なら、アプリの中ではコードを送れない（決定どおり Turnstile を使っていないため）。自分用の段は「デモで試す」で見るか、ログインも試したいか（試すなら、①Turnstile の許可に足せるか確かめる ②アプリだけ別の確かめ方、のどちらかを PM・データ担当と決める）
2. 画面の向きは縦だけにした（iPad も縦だけ）。よいか
3. マイクの理由の文「音声はこの iPhone の中だけで処理します」は今の聞き取りの作りに合わせたつもり。申請の前にもう一度確かめる

## ほかの担当への依頼

- デザイン担当：アプリだけの画面（位置と通知の許可を頼む前の説明の1枚・オフラインの画面・アプリで隠すもの＝「ホーム画面に追加」の案内など）の画面案。`html[data-native="ios"]` で切り替えられる
- データ担当：PR #124 の依頼のまま（プッシュの購読の表に種類の列・APNs に送る関数・ODPT の規約の見直し）。アプリの通知はそれまで「準備中」
- 修行・撮る人用・運用予想：持ち場のコードは変えていない。navigator.geolocation・navigator.share はそのまま呼べばアプリの中でもネイティブに回る

## 次の段（決まったら）

- 地図（Leaflet・MapLibre）・supabase-js・three.js をアプリの中に入れる（今は電波があるときだけ読む）
- バーコードをネイティブのカメラの部品に・通知を APNs に（データ担当のあと）
