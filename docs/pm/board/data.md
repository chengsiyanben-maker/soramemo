# データ担当の帳面

## いま持っている仕事
- 11/5 21時ごろ main に入った：data/co-leave-support（147 経営の精算・148・149・delete-account の精算）、data/signup-daily（150）、data/livery-keep（151）。#10・#11 は閉じた。#9 は co/leave-handling 向けのまま開いているが、中身は main に入り済み
  - 本番に流れたか（Actions のデータベースの段階）はまだ確かめていない。次の回に確かめる
  - 運用予想の強化（data/rotation-predict）の移行 147 は main の 147_co3_leave と番号がぶつかる。反映のときは rebase で 152 以降に付け直す
- 特別塗装機の予定の便を残す（ブランチ data/livery-keep → main 向けの下書き PR #11）：11/6 済み。報告 docs/pm/report-livery-keep.md
  - 移行151 で livery_plans → flight_schedule の外部キー（cascade）を外し、livery_plans_upcoming を left join に。flight_schedule は今のまま14日で消す。RLS はいまのまま
  - t89（17項目）と SQL のテスト94本すべて通過。チェックインは返す形が同じで影響なし
  - 本人の判断待ち：反映・admin_backup に入れるか・確認表の ODPT の行に書き足すか（第13条3＝許諾が終わったら消す）
- 退会の精算を支える変更（ブランチ data/co-leave-support → co/leave-handling 向けの下書き PR #9）：11/5 済み。報告 docs/pm/report-data-co-leave.md
  - delete-account で co3_leave_settle を定期支払いの停止と deleteUser の前に呼ぶ（失敗で止める）・移行148 co3_news_kind_check に partner・移行149 co3_codeshares.paid_amount
  - t87（26項目）と SQL のテスト95本すべて通過。経営の t86 の1行を「partner があれば partner、なければ event」に直した（経営に確認を頼む）
  - 本人の判断待ち：147 と一緒に反映すること（delete-account だけ先に入ると退会できない）・精算を定期支払いの停止より前にした順番
- 毎日の新規登録の数（ブランチ data/signup-daily → main 向けの下書き PR #10）：11/5 済み。報告 docs/pm/report-data-signups-daily.md
  - 移行150 admin_signups_daily(日数)（運営者だけ・数だけ）と読むだけの SQL docs/pm/signups-daily.sql。t88 ほか通過
  - 本人の判断待ち：ops-console/ はリポジトリにないので画面は未。手元のコンソールで rpc を呼ぶか、当面は SQL Editor で流すか
- 運用予想の強化（ブランチ data/rotation-predict）：本人が docs/pm/rotation-backtest.sql を流して結果を貼り返すのを待っている。報告 docs/pm/report-rotation-predict.md
- プロフィールの表（data/signup-profile）：本番に反映済み（11/5 17:45）。data/profiles は使わない（消さない）

## 守る決定
- 表を変えるときは移行と RLS をセット／本番への適用は本人の「反映して」のあと
- 航路と機体の記録は消さない／退会では本人の記録を消し、全機の記録は残す
- 外部データは規約の範囲を確かめてから。鍵は直書きしない
- あなたは本番のデータベースにつなげない。本番の数字が要るときは、本人が流す読むだけの SQL を書く
- 本人の決定：規約を改定するときは「terms_versions に1行足す → アプリの定数を変える」の順

## 移行の番号（反映のときに node tools/migrations.mjs rebase で付け直す）
- 147：co/leave-handling の co3_leave と data/rotation-predict がぶつかっている
- 148・149：data/co-leave-support／150：data/signup-daily／151：data/livery-keep
- テストの番号：t85 は main の user_profiles と rotation-predict がかぶる。t86 経営・t87 退会のデータ・t88 登録数・t89 特別塗装機の予定を残す

## 次にやること
1. 運用予想の強化：本人の SQL の結果が来たら読んで、予想の重みを直す
2. PR #9・#10・#11 の CI とレビューに答える
3. （PM から積んだ経営の3つの依頼と毎日の登録数は、#9・#10 で済み）

## ほかの担当への依頼
- 経営へ：co3_cs_pay_block で paid_amount に払った額を書き、退会の返金をそちらで計算するよう直す（空の行はいまの計算のまま）。t86 の1行の直しを確かめる。新聞で種類 partner の知らせが出るか確かめる
- 広告へ：登録数は admin_signups_daily（反映のあと）か docs/pm/signups-daily.sql（いまでも SQL Editor で見られる）で見られる
