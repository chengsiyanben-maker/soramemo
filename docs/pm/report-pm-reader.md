# PM が本番を読むだけで見る仕組み（data/pm-reader・11/27）

ブランチ data/pm-reader（main 14646cad から）。**移行212・テスト t151**。本番にはまだ入れていない（本人の「反映して」のあと）。

## 作ったもの
- **移行 `20261127000212_pm_reader.sql`**：役割 `pm_reader`（ログインなしで作る・強い力なし・ほかの役割を受け継がない）
  - 既定：`default_transaction_read_only = on`・`statement_timeout = 60s`・取引の途中で止まったら 120 秒・つなぎっぱなし 600 秒で切る・`search_path = public`
  - 書く権限は一切なし。`public` の中の使用だけ許し、`ops`・`auth` は使えない
  - 読めるのは下の30表だけ。RLS が有効な表には `pm_reader_read`（select だけ・`to pm_reader`）を足した。今の役割の権限・ポリシーは変えていない
- **`.github/workflows/pm-query.yml`**（手で動かすだけ）：入力は `query`（tools/pm-queries/ のファイル名）と `params`（任意の変数）。全体10分まで
- **`tools/pm_query.mjs`**：流す前の確かめと流す本体
  - 断るもの：select / with で始まらない文・2つ目の文（`;`）・バックスラッシュ（psql の命令）・書く/設定を変える言葉（insert・update・delete・copy・set・commit・set_config・pg_sleep など）・閉じていない文字列やコメント・かっこの数違い・フォルダ付きのファイル名
  - 流し方：`begin transaction ... read only` → `set local statement_timeout = '60s'` → `copy (select * from (<問い合わせ>) limit 200001) to stdout csv` → `rollback`。問い合わせは COPY の中の1文なので取引の外へ出られず、既定を変えられても書けない（作った人の権限で動く関数を通しても書けないことを t151 で確かめた）
  - 20万行を超えた分は切って「切った」と出す。ログには行数と秒だけ（接続の文字列はログで伏せる）
  - 変数は `名前=値`（値は英数字と `_ . : + -`・40字まで・10個まで）。SQL では `:'day'` のように使う
- **例 `tools/pm-queries/`**：`promo_day.sql`（`airline=JL day=2026-11-20`：その日の便の一覧。機体が記録にない便は全機の記録から補う）・`reg_week.sql`（`reg=JA8089 from=2026-11-14 to=2026-11-20`：その機体の区間。31日まで）

### 読める表（30）
| まとまり | 表 |
|---|---|
| 便・航跡・機体 | flight_history・flight_tracks・track_points・reg_legs・flight_schedule・flight_changes・timetable・foreign_legs・foreign_usual・airport_daily |
| 空港・航空会社 | airports・terminals・airline_codes・airport_facts・airport_yomi・world_airport_status |
| 運用・天気 | ops_log・rwy_samples・rwy_learned_days・ground_moves・arr_watch・wx_obs・wx_taf・wx_taf_hours |
| 特別塗装機 | livery_extra・livery_sightings・livery_plans |
| 運用予想 | rot_pairs・rot_eval・rotation_obs |

読めない例：checkins・flights・manual_flights・intl_flights・user_profiles・user_pins・各種 prefs・push_subs・subscriptions・companies と co3_*（経営）・atc_feeders／atc_msgs（協力者の ID がある）・track_quota・feedback・ops の表すべて・auth。ファイル置き場に移した古い日（cold-archive）も読めない。

## 確かめた結果
- t151（30項目）：UTC・日本時間とも NG 0。全127表を調べ、読めるのが一覧の30表ちょうど・どれにも書けない・利用者の表など23表は実際に読むと断られる・例の2本が大きい表を全部読みしない
- 本物の Postgres 16 を手元に立てて全移行を流し、本物の psql で `tools/pm_query.mjs` を最後まで流した：CSV が出る・既定は on／1min・checkins は permission denied・`;` の2文目は流す前に断る
- 権限にかかわる既存のテスト34本（t08・t36・t48・t66・t87・t89・t96〜t149 のうち権限・RLS を見るもの）を UTC で流して NG 0。`migrations.mjs check`・`check_secrets.mjs` も問題なし
- 影響：チェックイン・経営とも画面とロジックは変わらない（新しい役割に読む権限を足すだけ）

## 本人がする設定（反映のあと）
1. **パスワードを付ける**：SQL Editor で（パスワードは手元のパスワード管理で作った長いもの。チャットや PR に書かない。流したあと、その SQL を保存した下書きがあれば消す）
   ```sql
   alter role pm_reader with login password 'ここに長いパスワード';
   ```
2. **接続の文字列**：ダッシュボードの Connect → Session pooler の文字列の、ユーザー名 `postgres.<プロジェクトの記号>` を `pm_reader.<プロジェクトの記号>` に、パスワードを 1 のものに変え、末尾に `?sslmode=require` を付ける
3. **GitHub の秘密の設定**：Settings → Secrets and variables → Actions → New repository secret
   - `PM_READER_URL`：2 の文字列
   - `PM_RESULT_KEY`：結果を暗号にする合言葉（下の「決めてほしいこと」1）
4. **流し方**：Actions →「PM の読むだけの問い合わせ」→ Run workflow → `query` と `params`。（この画面は、この yml が main に入ってから出る）
5. **付けたあとの確かめ**（SQL Editor・読むだけ・軽い）：30行の public の表だけが出れば正しい
   ```sql
   select n.nspname, c.relname
     from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where c.relkind in ('r','v','m','p','f')
      and n.nspname not in ('pg_catalog','information_schema','pg_toast')
      and has_table_privilege('pm_reader', c.oid, 'select')
    order by 1, 2;
   ```
   （storage・realtime など Supabase の側の表が出たら、その行を PM に知らせてほしい。手元の模擬にはない表なので）

## 本人に決めてほしいこと
1. **リポジトリが公開なので、結果の置き方**：公開のリポジトリの artifact は GitHub にログインした誰でも落とせる。ODPT の便のデータは「CSV を配らない」決まりなので、公開のあいだは**結果を合言葉（`PM_RESULT_KEY`）で暗号にして置く**形にし、合言葉がないと流さないようにした。PM が中身を読むには合言葉を PM に渡す必要がある。代わりに**リポジトリを非公開にする**なら合言葉なしで CSV のまま置ける（非公開にするとサイトの公開の仕方に影響しないか別に確かめが要る）。どちらにするか
2. 読める表の一覧はこの30でよいか（運用の表のうち ga_events／ga_watch〈小型機〉・eta_calib・co3_wx は入れていない。足すなら移行と t151 の一覧を一緒に直す）
3. 反映は自動の反映のあとに知らせる形でよいか（役割を足すだけで、今の画面・処理は変わらない）
