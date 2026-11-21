# 撮影記録の表と候補の関数（データ担当・11/6 22時45分の PM の指示）

撮る人用担当の仕様（satsuei/photo-log-spec・PR #24 の docs/pm/spec-photo-log.md の 5、依頼 9-2）どおりに、表 photo_log と関数 photo_candidates を作りました。ブランチ data/photo-log、main 向けの下書き PR。**本番には適用していません**（本人の「反映して」待ち）。

## 1. 作ったもの
- 移行 supabase/migrations/20261106000154_photo_log.sql（153 は定期の手入れ PR #18 が使っているので 154）
  - 表 photo_log：仕様の 5-1 の列のまま。user_id は auth.uid() が既定で auth.users を on delete cascade で参照（退会で消える）。unique (user_id, reg, taken_at)。taken_at は2000年より前を制約で断る
  - RLS：有効。authenticated に select・insert・delete だけ許し、どれも「user_id = 本人」。update は許さない。anon は何もできない
  - 足す前の見張り（トリガー）：撮影時刻を分に丸める・未来を断る・1人1日（日本時間・足した日）200行まで。created_at は手で入れても今の時刻にする（1日の数をごまかせない）
  - 関数 photo_candidates(p_iata, p_at)：ログインした人だけ。[{reg, callsign, type, phase, at, dmin}] を時刻の差の小さい順に20件まで
    - 元は airport_tracks_all（空港・日の主キーで引く）＋ reg_legs（callsign, day の索引で引く。前の日にまたがる便も）
    - 36時間以内は track_points（t の索引で前後20分だけ読み、空港のまわりで絞る）から、22km 以内でいちばん近い点の時刻と、高さの上り下りで着陸／離陸を作って足す。6,000ft より下に来なかった便（上空を通り過ぎた便）は出さない。airport_tracks_all に同じ便が30分以内にあればそちらを使う（※ airport_tracks_all は3時間ごとに作られるので、36時間以内でもある便が多い）
    - 登録記号の分からない便は返さない（選べないため）。航跡の点は返さない
    - 断るときの文：`not recorded`（14空港の外）・`too old`（31日より前）・`future`（5分より先）・`login required`。画面はこの文で言い分ける
  - admin_backup に photo_log を1行足した（バックアップは有料機能にしない）
- テスト tests/sql/t94_photo_log.mjs（38項目）

チェックインと経営の表・関数は変えていません。画面はまだ何も使いません（撮る人用担当が作る）。

## 2. 確かめた結果
- t94：38項目すべて通過（本人だけ読む・足す・消す・書き換えられない・同じ分は1行・200行まで・未来と2000年前を断る・候補の並び順・前後20分・20件まで・登録記号なしは出さない・ほかの空港を出さない・36時間以内の着陸／離陸・上空の便を外す・全機の航跡と重ねない・断る4通り・退会で消えて全機の航跡と機体の記録は残る・バックアップに入る）
- 番号の check：151件・重なりなし
- 関係するテスト（t31・t33・t36・t39・t40・t41・t43・t47・t85）すべて通過

## 3. 気をつけること・本人に決めてほしいこと
1. 仕様の「36時間より前は airport_tracks_all、36時間以内は track_points」は、境目で両方を見る形にした（airport_tracks_all は3時間ごとにできるので、片方だけだと抜ける時間がある）。仕様と違うのはこの点だけ
2. 1日200行は「足した日」で数える（撮影日ではない）。古い写真をまとめて入れる人は1日200枚で止まる。これでよいか
3. 候補は最大20件で、画面は上の3件を出す。羽田の混む時間は前後20分に20便を超えることがあるので、「ほかの機体」の一覧は20件で切れることがある
4. 本人の「反映して」のあと、移行の番号は `node tools/migrations.mjs rebase` で付け直す（定期の手入れの 153 が先に入る場合など）

## 4. 修行担当の依頼：ANA の時刻表が12月以降も入っているか（コードで先に見たこと）
timetable-sync（supabase/functions/timetable-sync・_shared/timetable.ts・移行 20261028000094_timetable.sql）を読みました。
- 取り込みは日付で絞っていない。ODPT が返した期間（isValidFrom〜isValidTo）をそのまま入れる。毎日 3:00〜4:55 に5分ごと・1回に6空港・20時間に1回なので、81空港は毎日1回ずつ入れ替わる。**ODPT に12月の ANA の時刻表が出ていれば、次の朝には入る**
- 取れなかったとき（ODPT の誤り）は前の行のまま残る。結果は timetable_sync_runs.result に `ANA_error` として残る
- 1回の問い合わせが1,000件ちょうどのときは取りこぼしの恐れがあり、`ANA_truncated: true` が付く（コードの注記では、ODPT は1回に1,000件まで返す）。12月の分が別の件で増えると、羽田などで1,000件に届いて、後ろの期間が落ちることがありうる
- 「◯/◯まで」は max(valid_to) なので、1便でも12月まであれば12月と出る。本当に組めるかは日ごとの便の数で見る

本人が shugyo-timetable-check.sql（shugyo-inventory・PR #26）を流した結果の読み方：
| 結果 | 判定 | 次にすること |
|---|---|---|
| 1) ANA の最後の日が12月以降、2) の12月の ANA が毎日ある程度の数（11月と同じくらい） | 入っている | 修行担当に「12月の計画を作れる」と返す |
| 1) は12月以降だが、2) の ANA が12月に入って大きく減る・0の日がある | 一部だけ入っている | 3) の result に ANA_truncated があるか見る。あれば問い合わせを期間か到着空港で分ける直しをデータ担当が作る |
| 1) の ANA が 11/30 のまま、3) に ANA_error も ANA_truncated もなく ran_at が今日 | 取り込みは動いている。ODPT にまだ出ていない | 待つ（ANA の公式の時刻表が12月分を出していれば、ODPT の掲載待ち）。修行の画面は「時刻表がまだ出ていない」のまま |
| 3) に ANA_error がある・ran_at が古い | 取り込みが失敗している | エラーの文をデータ担当に渡してもらう。鍵（ODPT_CONSUMER_KEY）が切れていないかも見る |
| 最後の日が 2099-12-31 | 期間のない行（ODPT に期間がなかった便） | その便は「ずっと」扱いになっているので、データ担当が直す |

3) の結果が長いときは、ANA の誤りと取りこぼしだけを見る1行の SQL（読むだけ）：
```sql
select count(*) as 空港の数, count(*) filter (where result ? 'ANA_error') as ANA_error, count(*) filter (where result ? 'ANA_truncated') as ANA_truncated, min(ran_at) as いちばん古い実行 from public.timetable_sync_runs;
```
