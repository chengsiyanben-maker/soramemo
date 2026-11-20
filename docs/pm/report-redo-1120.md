# 見落としの片付け 11/20（データ担当・data/redo-1120）

PM の指示（11/20 14時10分・overlooked-1120.md の A1・A2・A4）。ブランチ data/redo-1120（main 8c39141 から）。

## 作ったもの
1. **定期の手入れ #111 を番号 188 に付け直した**（A1）
   - `supabase/migrations/20261120000188_maint_1116b.sql`：中身は #111 の 183 と同じ（索引を8本足すだけ。aircraft(user_id)・flights の dep_checkin／arr_checkin の部分索引・経営の co3_market／co3_orders の aircraft_id・co3_breakdowns／co3_heavy の spare_id・co3_extra の aircraft_id）。`if not exists` なので2回流しても困らない
   - 今の main（184〜187）とぶつからないかを確かめた：同じ名前・同じ形の索引はなく、184〜187 で足された外部キーにも「引く索引がない」ものは増えていない（テスト t122 の「残るのは小さな表と auth.users を指すものだけ」が通る）
   - テスト `tests/sql/t122_maint_1116b.mjs`（番号の読み替えだけ）。報告と読むだけの SQL `docs/pm/maint/2026-11-16-2-report.md`・`2026-11-16-2-check.sql` も #111 から持ってきた
   - 表・列・RLS・権限は変えない。影響：経営（自分の機体の読み出し・機体を売る・毎晩の処理が速くなるだけ）、チェックイン（退会・管理の取り消しが速くなるだけ）。画面と値は変わらない
   - **#111 は閉じてよい**（この PR が代わり）
2. **inbound_aircraft の first_of_day**（A2・11/19 チェックイン担当の依頼）
   - `supabase/migrations/20261120000189_inbound_first_of_day.sql`：関数の中身だけ（表・RLS・権限は変えない。anon・authenticated は実行だけのまま）
   - 前の便が見つからないとき、次のどちらかで `first_of_day: true`
     - 今日の登録記号が分かる（flight_watch の reg）とき：その機体の前の日の最後の便がこの便の出発空港に着いていて、今日この便より前に同じ機体の便（欠航を除く）がない → `first_src: 'reg'`、泊まった便を `overnight: {flight, dep, arr, arr_at, arr_src, reg}`
     - 前の60日の記録（同じ便名・出発空港・欠航でない日、新しい30日まで）で「その日の機体の最初の便で、前の日の最後の便がここに着いていた」が3日以上かつ7割以上 → `first_src: 'history'`（`first_stay`・`first_of` にその日数）
   - どちらでもなければ false（画面は今までの1行）。前の便が見つかったときも false。今までの値と形は変えていない（足しただけ）
   - 速さ：flight_history は日付の配列（60個）で索引を引く。新しい索引は足していない。1回の呼び出しで最大 30日 × 2 回の索引の引き
   - 影響：チェックイン（PR #128 で受ける作りになっている「朝一番の便です」の1行が出るようになる）。経営は使っていない
3. **#81（data/speed-1113b）は main に全部入っている**（A4）：`git merge-base --is-ancestor origin/data/speed-1113b origin/main` が真、main にない差分は0。**閉じてよい**（閉じるのは PM）

## 確かめた結果
- t122 16項目・t127（新）16項目・t29（前の inbound のテスト）8項目 通過。番号の重なりなし（179件）
- SQL のテスト全部（tests/sql の129本）を手元で流し、129本とも通過（前から落ちることのある経営の t49 も今回は通った）

## 本人（PM）に決めてほしいこと
- first_of_day を記録から出す線（3日以上・7割以上）でよいか（おすすめ：このまま。外れたときも「朝一番の便です」の1行だけで、遅れの見込みは変わらない）
- overnight（泊まった便）を画面に出すか（出すならチェックイン担当へ。返す形はこの報告の 2）

## チェックイン担当への依頼（PM から checkin.md に写してほしい）
- inbound_aircraft が `first_of_day`（true／false）を返すようになった（移行189）。PR #128 の作りのまま読める。あわせて `first_src`（'reg'・'history'・null）と、reg のときだけ `overnight`（前の日に泊まった便：flight・dep・arr・arr_at・arr_src）も返す。出すかは画面案しだい
