# データ担当の帳面

## いま持っている仕事
- プロフィールの表（ブランチ data/signup-profile を正）：11/5 に仕上げ済み（terms_versions・terms_current・agree_terms は表にある版だけ受け付ける・admin_backup と restore_from_backup.py に user_profiles）。feat/signup に取り込み済み。報告：docs/pm/report-data-profile-finish.md
  - 本人の判断待ち：改定のときは「terms_versions に1行足す → アプリの定数を変える」の順でよいか。反映のときは `node tools/migrations.mjs rebase` で番号を付け直してから流す
- 運用予想の強化（ブランチ data/rotation-predict）。本人が SQL Editor で流す読むだけの SQL：docs/pm/rotation-backtest.sql。報告：docs/pm/report-rotation-predict.md
- data/profiles は使わない（消さない）

## 守る決定
- 表を変えるときは移行と RLS をセット／本番への適用は本人の「反映して」のあと
- 航路と機体の記録は消さない／退会では本人の記録を消し、全機の記録は残す
- 外部データは規約の範囲を確かめてから。鍵は直書きしない
- あなたは本番のデータベースにつなげない。本番の数字が要るときは、本人が流す読むだけの SQL を書く

## PM から積んだ次の仕事（11/5、運用予想の強化のあと）
- 経営担当からの依頼（ブランチ co/leave-handling の 20261105000147_co3_leave.sql が前提。報告 docs/pm/report-co-leave.md の4）
  1. delete-account で deleteUser の前に co3_leave_settle(p_uid) を呼ぶ。失敗したら削除を止める
  2. co3_news_kind_check に 'partner' を足す移行（RLS はそのまま）
  3. co3_codeshares に paid_amount bigint を足す移行（RLS はそのまま）
- 広告担当からの依頼：毎日の登録数を運営コンソールで見られるようにする（読むだけ）
