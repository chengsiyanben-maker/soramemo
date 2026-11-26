# 報告：co3-trouble-detect に時間の上限（keiei/timeout）

PM 11/26 7時45分の依頼（データ担当の 11/16・11/26 の見回りから）。経営の画面は非表示のまま（KEIEI_VISIBLE はそのまま）。

## 作ったもの
- 移行 `20261126000204_co3_trouble_detect_timeout.sql`（cron の付け直しだけ。表・関数・RLS・権限・画面は変えない）
  - 調べると、この仕事は 10/28 の移行119（便ごとのトラブル co3-legs-check に置きかえ）で**もう止めてある**。移行166 で作らなかったのはそのため。データ担当の見回りは、止めた行（unschedule）を見ていなかったと思われる
  - それでも本番に残っている（119 の取り消しが効かなかった）場合に備え、**残っているときだけ**、同じ時刻・同じ中身のまま文の先頭に `set statement_timeout = '3min'; set lock_timeout = '5s';` を付けて付け直す
  - ないときは何もしない（新しく作らない・消さない）。前に別の上限が付いていても 3分・5秒にそろえ、二重にしない
  - pg_cron の有無は `cron.job` の表があるかで見る（テストで pg_cron の代わりを置いて確かめられるようにするため）
- SQL テスト `tests/sql/t143_co3_trouble_detect_timeout.mjs`（13項目）

## 確かめた結果
- t143 すべて通過（仕事がないとき作らない／残っているとき時刻と中身はそのまま上限が付く／2回流しても二重にならない／ほかの仕事は変わらない／移行を全部流せる／付け直した文がそのまま通る）
- t128（経営の仕事20本の上限）通過、移行の番号チェック通過（193件、重なりなし）。203 は data/ops-guard が使っているので 204 にした

## 本人（PM）に決めてほしいこと
- 本番に残っているかを、読むだけの SQL で確かめたい（SQL Editor で流す）：
  ```sql
  select jobid, jobname, schedule, command, active from cron.job where jobname like 'co3-trouble%' order by jobname;
  ```
  - `co3-trouble-expire` だけなら、もう止まっていて移行204 は何もしない（入れても害はない）
  - `co3-trouble-detect` が出たら、119 の決定どおり止める（unschedule）のが本筋。止めるのは「消す作業」なので本人の OK が要る。OK までは移行204 で上限だけ付けておく（PM のおすすめ）
- データ担当へ：co3-trouble-detect はリポジトリの移行では 119 で止めてある。次の見回りの表では unschedule も数えてほしい
