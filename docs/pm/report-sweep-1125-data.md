# 見直し 2回目のデータの分（特別塗装機の知らせを1つに・夜の静かな時間）報告

PM の指示（11/25 5時10分、report-sweep-1125.md の4番）。ブランチ data/sweep-1125（main 04d22af から）。**移行197・テスト t135 を使った**。本番にはまだ入れていない。
11/25 水曜に定期の回として呼ばれたが、PM の積んだ指示があったのでこちらをした（定期の仕事は次の月曜）。

## 作ったもの
1. **1便で1つの通知**（_shared/livery_note.ts の liveryTag）
   - 予定（odpt-status）・飛んでいる（機体ごとの知らせ livery_push.ts）・着陸に向かっている（airport-traffic の notifyLivery）・海外の機体が向かっている（livery_extra.ts）の tag を、どれも **`sp-便名`**（JAL113 → `sp-JL113`）にそろえた。同じ便は端末の上で同じ通知の書き換えになり、書き換えのときも鳴る（renotify。src/sw.js は前から対応）
   - 指示の例は `sp-登録記号-便名` だったが、予定の便（ODPT）は機体が分からないので、3つのどれでも分かる便名だけにした。同じ時間に同じ便名で飛ぶ機体は1機だけなので、ぶつからない。便名が分からないとき（呼び出し符号なし）だけ `sp-登録記号`
   - 前の tag（`plan-<便>`・`spr-<登録記号>`・`sp-<登録記号>`）はやめた。画面のコードはどれも見ていない
2. **夜の静かな時間（23〜7時、日本時間）**：push_subs に `quiet_night`（はじめ true）を足し、true の人には次を送らない
   - 特別塗装機（予定・飛んでいる・着陸に向かっている・海外の機体）、撮影の知らせ（着陸・離陸の数分前）、運用が変わった知らせ
   - **止めないもの**：乗る便・空港の遅れ・欠航・門限・ダイバートの知らせ（夜こそ要る）。ゴーアラウンドは前からの ga_quiet のまま
   - 夜の間に見つかった予定の便は、7時すぎに静かな時間を選んだ人へ1回だけ送る（まだ出発の前の便だけ。livery_plans.quiet_push_at で二重にしない）
   - push-subscribe は `quiet_night: true|false` を受け付ける。送られてこなければ前の設定のまま（古い画面からの申し込みで戻らない）
3. **運用が変わった知らせは「前の知らせから60分」**：その人のその空港の運用の知らせが60分以内にあれば送らない（北⇔南の行き来・時をまたいでも続けて届かない）。記録は今の spot_notified に `ops-空港@分` で残す（2日で消える今の掃除のまま）

移行197（livery_quiet_night）：push_subs.quiet_night（boolean・not null・はじめ true）、livery_plans.quiet_push_at（timestamptz）。列を足すだけ。RLS は ON のまま、利用者（anon・authenticated）は前と同じく読めない・書けない。lock_timeout 5秒。
**影響**：チェックイン（知らせの設定の画面）。経営は関係しない。航路と機体の記録は消さない。

## 確かめた結果
- t135（新）21項目 OK：今いる購読も新しい購読も true・false にできる・null は入らない・列を渡さない上書きで前の値のまま・朝の送り直しは1回だけ・livery_plans_upcoming は前のまま・RLS と権限・もう一度流しても同じ・lock_timeout は戻る
- deno test 317本 通過（livery_note_test.ts を足した。livery_push_test に夜のテストを足し、時計で結果が変わる1本を昼の時刻に固定。livery_extra_test は tag の期待を便名に）
- deno check（airport-traffic・odpt-status・push-subscribe）通過、migrations.mjs check 187件 重なりなし

## 本人に決めてほしいこと（PM のおすすめで可）
1. **はじめ ON は今いる人にもすぐ効く**：入れた日から、今いる人も夜（23〜7時）は特別塗装機・撮影・運用の知らせが届かなくなる。画面に「夜は知らせない」の行ができるまで OFF にできない。おすすめ：チェックインの画面の行と一緒に入れる（下の依頼）。急ぐならこのまま先に入れてもよい（夜に止まるだけで、消えるものはない）
2. 夜に見つかった予定を朝に送り直すのは 7時すぎの1回。要らなければ外す（おすすめ：残す）
3. 「通知の扱いを変える」に当たるので、自動の反映でも入れる前に本人に一言（11/20 の決まり）

## チェックイン担当への依頼
- 知らせの設定の画面に「夜は知らせない（23時〜7時）」の ON／OFF を1行（はじめ ON）。push-subscribe に `quiet_night: true|false` を付けて送る。文の例：「特別塗装機・撮影・運用の知らせを、夜は止めます。乗る便の遅れは届きます」
- ゴーアラウンドの「知らせない時間」はそのまま（別の設定）

## 本人に流してほしい SQL（反映のあと・読むだけ）
```sql
-- 夜の静かな時間を選んでいる購読の数（はじめ全部 true）
select quiet_night, count(*) from public.push_subs group by 1;
-- 朝に送り直した予定（前の1日）
select count(*) filter (where quiet_push_at is not null) as resent, count(*) as plans
from public.livery_plans where created_at > now() - interval '1 day';
```
