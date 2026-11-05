# データ担当の帳面

## いま持っている仕事
- プロフィールの表（ブランチ data/signup-profile を正。feat/signup に取り込み済み）。仕上げ：規約の版の表とバックアップへの追加を data/profiles から取り込む。報告：docs/pm/report-data-profile-finish.md
- 運用予想の強化（ブランチ data/rotation-predict）。本人が SQL Editor で流す読むだけの SQL：docs/pm/rotation-backtest.sql。報告：docs/pm/report-rotation-predict.md
- data/profiles は使わない（消さない）

## 守る決定
- 表を変えるときは移行と RLS をセット／本番への適用は本人の「反映して」のあと
- 航路と機体の記録は消さない／退会では本人の記録を消し、全機の記録は残す
- 外部データは規約の範囲を確かめてから。鍵は直書きしない
- あなたは本番のデータベースにつなげない。本番の数字が要るときは、本人が流す読むだけの SQL を書く
