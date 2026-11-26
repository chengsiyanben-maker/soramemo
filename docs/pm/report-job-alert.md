# 夜の処理が止まったら運営へ1日1回知らせる（データ担当・11/26 本人の OK ⑤）

ブランチ data/job-alert（main 594dd3e から）。**移行209・テスト t148・Edge Function ops-alert（新しい関数）**。影響：チェックイン・経営とも画面は変わらない（運営だけ）

## 1. 作ったもの
- 流れ：pg_cron（毎時41分・上限10秒）→ Edge Function `ops-alert` → `ops_alert_claim()`（11/26 の死活の記録 ops.data_health() に ng があり、今日まだ届いていなければ「送る」）→ 送り先へメールか Webhook → `ops_alert_done()`
- **1日1回**：日本時間の1日に届けるのは1回まで。届かなかったときは1時間ごとに試し直す（1日6回まで）。誰がいつ何度関数を呼んでも、データベースの記録で止まる
- 送り先は **Edge Function の秘密の設定 `OPS_ALERT_TO`**（カンマ区切り。メールアドレスか https:// の Webhook）。コード・表・ログには書かない（ログは届いた数だけ）
- 表 `ops.ops_alert_log`（日・試した回数・届いたか・ng の項目の名前と最後の時刻・結果の短い文）。宛先の列はない。RLS 有効・anon／authenticated は読めない。2つの関数は service_role だけ
- 知らせの文（例）
  - 件名：そらメモ：夜の処理・取り込みが止まっています（2件）
  - 本文：「11/27 07:41 時点で、次の処理が止まっているか失敗しています。・便の実績（最後：11/26 00:00・上限 28時間）…」と、見る所（admin_data_health・cron.job_run_details）

## 2. 確かめた結果
- t148 19項目 OK（UTC・日本時間）：ng があれば送る・項目の形・届いたら同じ日は送らない・届かなければ試し直し6回で止まる・あとから失敗を書いても届いた印は消えない・次の日はまた送る・ng がなければ送らず記録もしない・宛先の列がない・権限と RLS・上限・cron の文・config.toml
- deno：ops_alert_test.ts 5本（送り先の読み方・文・SMTP の設定・結果の文に宛先が入らない）を含め341本通過。deno check（ops-alert）通過。秘密の文字列の確かめ 問題なし
- **メールを実際に送るところは確かめていない**（ここからは送れない）。設定のあと、下の 3 の 5 で一度試してほしい

## 3. 本人にお願いする設定（新しい外部のアカウントは作らない）
メールで受け取るなら、今の Gmail（新規登録の確認メールに使っているもの）のアプリパスワードを使う形がいちばん手間が少ない。
1. Google アカウントの「セキュリティ」で2段階認証が有効なのを確かめ、「アプリ パスワード」を1つ作る（名前は例「そらメモ 知らせ」）。16文字の値が出る
2. Supabase のダッシュボード →「Edge Functions」→「Secrets」に次を入れる
   - `OPS_ALERT_TO`：受け取るメールアドレス（複数ならカンマ区切り。Slack・Discord の Webhook の URL も書ける）
   - `OPS_SMTP_USER`：送る Gmail のアドレス
   - `OPS_SMTP_PASS`：1 のアプリパスワード
   - （任意）`OPS_SMTP_FROM`（差出人。既定は OPS_SMTP_USER）・`OPS_SMTP_HOST`（既定 smtp.gmail.com）・`OPS_SMTP_PORT`（既定 465。Supabase の関数からは 25・587 は使えないので 465 のまま）
3. メールを使わず Webhook だけにするなら、`OPS_ALERT_TO` に Webhook の URL だけを入れればよい（SMTP は要らない）
4. 送り先を入れないうちは、関数は動いても誰にも送らない（記録に skip no_target と残る）
5. 試し方：反映のあと、SQL Editor で `select * from ops.ops_alert_log order by day desc limit 7;` を見る（毎時41分に動いた結果）。ng がない日は送られない（それで正しい）。ng がある日に届いたかは、この表の ok と result（例 mail 1 / hook 0 / failed 0）、Edge Functions の ops-alert のログの「ops_alert」の行で見られる

## 4. 気づいたこと
- 知らせる項目は死活の記録の15項目すべて（夜の処理だけでなく、毎時・毎分の取り込みの止まりも含む）。夜の処理だけに絞るなら、ops_alert_claim の中で key を選ぶ（1行）
- 11/26 の data_health_watch（ops.client_errors に下書きを書く仕組み）はそのまま残した（管理の画面で見る用）

## 5. 本人に決めてほしいこと
1. 受け取り方：メール（3 の 1・2）か Webhook か両方か
2. 知らせる項目をすべてにするか、夜の処理だけにするか
