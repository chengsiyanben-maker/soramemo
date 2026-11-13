# 遅れの通知の受け取り：上書きのときも鳴らす（チェックイン担当・11/13）

PM の指示（11/13 21時20分）：データ担当の data/alert-merge（遅れの通知を1件にまとめる）の依頼。ブランチ checkin/push-renotify（main 4fb2f42 から）・下書き PR。

## 作ったもの
- src/sw.js の push の受け取り（`self.addEventListener("push", …)` の showNotification）で、`renotify: !!(d.tag && d.renotify)` を渡すようにした
  - 届いた中身に tag があり renotify が真のときだけ立てる。tag がないときは今までどおり決まった tag「soramemo」で、renotify は立てない（tag なしで renotify を立てるとブラウザが通知を出さない）
  - renotify がない古い中身（特別塗装機の通知・空港ごとの通知など）は今までどおり鳴らさない
- web/sw.js を組み立て直した（node tools/build.mjs。変わったのは web/sw.js の1行だけ）
- 画面は変えていない。src/index.html は触っていない（変えた関数はなし）
- テスト t132 を足した：web/sw.js を node の vm で読み、偽の self に push を5件送って、渡した中身（renotify・tag・飛び先・本文・アイコン）を確かめる

## 確かめた結果
- t132（9項目）すべて成功。t128（サービスワーカーの配り方）・t60 も成功
- 全体の流し：下に追記

## 本人に決めてほしいこと
- なし（data/alert-merge と一緒に反映する。先にこちらだけ入っても、届く中身に renotify がないので今までと同じ動き）
- data/alert-merge の報告にある「通知の説明の文（この便に乗るは15分以上・空港ごとは主要空港の門限・0時前後と欠航・ダイバートだけ）が要るか」は画面の話なので、デザイン担当の画面案と本人の答えを待つ（今回は入れていない）
