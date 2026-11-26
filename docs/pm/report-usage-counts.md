# 使われ方を、個人を特定しない回数だけで見る（データ担当・11/26 本人の OK ④）

ブランチ data/usage-counts（main 594dd3e から）。**移行208・テスト t147**。影響：チェックイン・経営とも画面は変わらない（運営コンソールで呼ぶ関数が1つ増えるだけ）。checkins に created_at だけの索引を1本足す

## 1. 作ったもの
- 表 `ops.usage_daily`（day・metric・key・n・sessions）：日ごと（日本時間）の回数だけ。**利用者ID・IP・位置・session の値は列がない**。sessions は「その回数を出した起動の数」（起動ごとの使い捨ての値を数えただけ）
- `ops.usage_daily_build(日)`：1日分を作り直す。元は次の4つ（どれも索引で日の範囲だけ読む）

| metric | key | 元 |
|---|---|---|
| checkin | ok（印が押せた数） | public.checkins の数（count だけ） |
| checkin | out_of_range・low_accuracy・stale_position・too_soon・already | ops.checkin_rejections（サーバーが断った理由） |
| checkin | queued（電波がなく端末に保存） | usage_events の checkin_queued |
| client_fail | 画面に返った失敗の理由（server など） | usage_events の checkin_fail |
| geo | 1 許可なし・2 取れない・3 時間切れ | usage_events の geo_fail |
| error | エラーの種類（js・checkin など） | ops.client_errors の kind（中身は見ない） |
| tab | 開いたタブ | usage_events の tab |
| open | 起動（live・demo） | usage_events の open |
| onboard | guide:done／skip、signup の各段（verified・persona・loc_allow・loc_later・done）、terms、gate | usage_events |

- `ops.usage_daily_fill(14)`：毎晩3時37分（cron usage-daily・上限2分・ロック待ち5秒）。前の日と前の前の日（遅れて届いた分）を作り直し、まだの古い日を14日ずつ180日前まで。元の表は180日で消えるが、回数の表は残る
- `admin_usage_counts(日数)`：運営コンソール用の読むだけの関数（管理者だけ）。日ごとに checkin・indoor・geo・client_fail・error・tab・open・onboard を返す。**indoor**＝「屋内などで位置が取れなかった」の目安（サーバーの low_accuracy＋画面の geo_fail の 2 と 3）
- RLS：2つの表は RLS を有効にし、anon・authenticated には何も許さない。作る関数は誰からも呼べない（cron だけ）

## 2. 確かめた結果
- t147 41項目 OK（UTC・日本時間の両方）：列に個人の値がない・各回数が合う・日の境目（0時ちょうどは入る、次の0時は入らない）・ほかの記録（pin など）は数えない・作り直しても二重にならない・元の表は減らない・毎晩の処理の進み方（7日→12日→180日で止まる）・上限・返す中身に session や利用者ID が出ない・管理者でなければ断る・権限・RLS・**元の表を全部読みせずに作れる**
- cron・索引にかかわる前からのテスト10本、t141・t142 も通過

## 3. 気づいたこと
- 「印の成功」は画面の記録にないので、サーバーの checkins の数で数えた（同じ日に同じ人が何回押しても回数として数える）
- はじめての流れは、今の画面の記録（guide・signup・terms・gate）で数えている。11/26 に決まった新しいログインの流れ（ログインなしで始め、最初の現地の印で登録・#237 案B）が入ったら、その段ごとの記録の名前をチェックイン担当に決めてもらい、onboard に足す（関数の中の名前の一覧を1行直す）

## 4. 翌日・翌月に戻った割合（作らない・案だけ）
- 今の session は起動ごとに変わるので、同じ人が次の日に開いたかは分からない（それが個人を特定しない理由でもある）
- 作るなら案：端末に「最初に開いた月」（例 2026-11）だけを持たせ、起動の記録の prop に付けて送る → 月ごとの「その月に初めて開いた端末のうち、翌月も開いた数」を数えられる。ずっと同じ ID は送らない。ただし端末を変えると別に数わる・同意の文の見直しが要るので、本人の OK のあと

## 5. 本人に決めてほしいこと
- なし（表と関数を足すだけ・画面は変わらないので、PM の自動の反映でよいと考える）。運営コンソールに出す画面は、要るならチェックイン担当（管理の画面）とデザイン担当へ
