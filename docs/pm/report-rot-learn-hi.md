# 報告：運用予想を learn_hi に切り替える（データ担当・11/13）

PM の指示（11/13 17時30分）・本人「切り替えて」。ブランチ data/rot-learn-hi → 下書き PR（main 向け）。main にも本番にも入れていない。

## 1. 作ったもの
- 移行 166 `supabase/migrations/20261113000166_rot_learn_hi.sql`
  - predict_rotation_v2 が呼ぶ方式を `rot_predict('learn', …)` → `rot_predict('learn_hi', …)` に（学んだ便を出すしきい値が「2回以上・3割以上」→「3回以上・4割以上」）
  - 返す形は今のまま。`method` の値だけ `'learn_hi'` になる（記録のない機体の答えも同じ）。便ごとの `src` は今までどおり livery／learn／base
  - 表・索引・RLS・毎晩の処理（rot-pairs・rot-eval の採点は base・learn・learn_hi の3通りのまま）は変えない。関数の権限も今のまま（anon・authenticated に実行だけ、security definer）
  - 先頭に lock_timeout 10s
  - 影響：チェックイン（運用予想の画面）だけ。経営なし。今のアプリは v2 をまだ呼んでいないので、反映しても運用予想担当が呼び出しを替えるまで画面は変わらない
- テスト `tests/sql/t106_rot_learn_hi.mjs`（10項目）

## 2. 確かめた結果
- t106（10項目）通過：method が learn_hi・返す形の鍵は今のまま・よく見る便は今までどおり出る・rot_predict('learn_hi') と同じ並び・2回しか見ていない便は出さない（learn なら出る）・記録のない機体・おかしな登録記号・権限・表は anon から読めない・移行は関数1つだけ・採点は3通りのまま
- t90（33項目）・t91・t92（26項目）通過。番号の重なりなし（156件）
- アプリ・Edge Functions に predict_rotation_v2 を呼ぶ所はまだない（運用予想担当が替える）

## 3. 反映のあとに流す読むだけの SQL（本人・軽い）
```sql
select public.predict_rotation_v2(reg)->>'method' as method, jsonb_array_length(public.predict_rotation_v2(reg)->'next') as next_n
from (select reg from public.reg_legs where day = (now() at time zone 'Asia/Tokyo')::date order by last_at desc limit 3) r;
```
method が3行とも learn_hi なら入っている。

## 4. 本人に決めてほしいこと
- 「反映して」（PR #79（164）・#81（165）より先に入れる場合も、番号はそのままで並ぶ。後から入れる場合は rebase は要らない）
- 約4週間後（記録が42日そろったら）docs/pm/rotation-eval-view.sql で比べ直す（帳面に書いた）

## 5. ほかの担当へ
- 運用予想へ：predict_rotation_v2 は learn_hi で答える形になった（未反映）。画面の呼び出しを v2 に替えるときは `method` を見ず、今までどおり `estimate`・`next[].src` を使えばよい。「予想・保証しない」の書き方は変えない
