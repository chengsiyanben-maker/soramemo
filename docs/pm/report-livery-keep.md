# 特別塗装機の予定の便（livery_plans）を消さずに残す（データ担当・2026年11月6日）

ブランチ：`data/livery-keep`（main から。main には入れていない。本番の Supabase にも流していない）

作業の前の3行
- 変えるファイル：移行 `20261106000151_livery_plans_keep.sql`・テスト `tests/sql/t89_livery_plans_keep.mjs`
- 手順：livery_plans → flight_schedule の外部キー（on delete cascade）を外す → 予定の一覧の関数を left join に
- 確かめ方：毎晩の掃除と同じ文で時刻表を消しても予定が残るテストを足す・SQL のテストをすべて流す

## 作ったもの
- livery_plans の外部キーを外した。`schedule_id` は主キーのまま（時刻表は「運航日・便名・出発」で上書きされ id が変わらないので、同じ便が2行になることはない）
- flight_schedule は今のまま14日で消す（掃除の処理・flight_watch・flight_alerts の外部キーは変えない）
- `livery_plans_upcoming` を inner join → left join に。返す形は同じ（9項目）。時刻表がないときは到着の定刻・実際の出発が空、欠航は false
- 残った予定は flight_history と「運航日＝定刻の日本時間の日付・便名・出発」でつなげられる
- RLS：いまのまま（有効・ポリシーなし。利用者は表を直接読めず、読むのは `livery_plans_upcoming` だけ）
- 影響：チェックイン（特別塗装機の予定の一覧と通知）は返す形が同じなので影響なし。odpt-status の upsert（schedule_id でぶつかったら入れない）もそのまま動く。経営は使っていない

## 確かめた結果
- t89：17項目すべて通過（外部キーがない・掃除のあとも残る・flight_watch はいまのまま消える・同じ便は1行・一覧の形が同じ・時刻表がなくても出る・実績とつなげられる・RLS・満足度 40）
- SQL のテスト 94本すべて通過

## 本人に決めてほしいこと
1. 反映（「反映して」のあと、`node tools/migrations.mjs rebase` で番号を付け直して流す）。反映より前に消えた分（14日より前）は戻らない
2. 運営のバックアップ（admin_backup）に livery_plans を入れるか。いまは flight_history など全機の記録も入っていないので、今回は入れていない
3. 外部データ：お知らせの文（ODPT）から作った行を長く持つことになる。確認表（11/4）のとおり、ODPT は保存して自分のサービスの中で使うのは許され、元データの大部分を戻せる形での公開・再配布は禁止（第8条4）。この表は利用者に直接は見せないので範囲内。ただし「許諾が終わったらデータを消す」決まり（第13条3）があるので、ODPT の利用をやめるときはこの表も消す対象になる。確認表の ODPT の行に「livery_plans は残す（第13条3のときは消す）」と書き足してよいか
