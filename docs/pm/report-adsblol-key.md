# adsb.lol の鍵と使い方の守り（data/adsblol-key、11/21）

PM の指示 11/21 1時10分。表・移行・RLS は変えていない（チェックイン・経営への影響なし。画面の返す形も同じ）。

## 作ったもの
1. **鍵を付ける形**：`supabase/functions/_shared/adsblol.ts`（新）
   - api.adsb.lol に問い合わせる2か所（airport-traffic の記録の円・flight-live の呼び出し符号）は `adsbLolHeaders()` を使う。Supabase の秘密の設定 `ADSBLOL_API_KEY` があれば鍵を付け、なければ今までどおり鍵なしで動く。鍵はコードに書いていない
   - ヘッダーの名前は `ADSBLOL_KEY_HEADER` で変えられる（既定 `api-auth`）。**案内のページ（api.adsb.lol/docs・www.adsb.lol/mmb）をこの回は開けず、正しい名前を確かめられていない**。鍵を入れるときに案内の名前を見て、違えば ADSBLOL_KEY_HEADER にも入れる
   - 鍵は adsb.lol にだけ付け、adsb.im（別の運営）には付けない
   - ほかの adsb.lol の使い方（flight-watch・foreign_now・daily-archive など）は live_positions・reg_legs を読むだけで、外へは問い合わせていないことを確かめた
2. **名乗り**：adsb.lol・adsb.im への問い合わせ5か所の User-Agent を `soramemo (<関数名>; https://soramemo.jp/)` にした
3. **Retry-After**：airport-traffic は前から守っている。flight-live は守っていなかったので、429・420 を受けたら Retry-After の秒（なければ30秒、長くても5分）まで問い合わせない形にした（その間は「見つからない」と同じ扱い。45秒の覚えはそのまま）
4. **adsb.im の利用条件**：ページを開けず未確認。Project の「外部データの利用規約の確認表」に行を足し「条件が分からないまま使っている」と書いた。問い合わせは今の上限のまま増やさない
5. テスト `supabase/tests/adsblol_test.ts`（6本）

## 確かめた結果
- deno test 278本 通過（足した6本を含む）・deno check（airport-traffic・flight-live・airport-foreign・adsblol.ts）通過

## 外にデータをまとめて返す口（指示の 4）
表（live_positions・reg_legs・airport_tracks_all・track_points・flight_tracks・foreign_legs）はどれも RLS 有効で anon・authenticated からは読めない。これらを読む関数は全部に grant／revoke が書かれている（既定の public 実行のまま残っているものはない）。ログインなしで呼べるものは：

| 口 | 返すもの | 今の上限 | 判定 |
|---|---|---|---|
| **airport_tracks(p_iata, p_day)**（anon） | その空港・その日の全機の航跡の線（便名なし・時刻は時だけ） | 1回 3,000＋2,000本。**日付はどの過去の日でもよく、回数の上限なし** | 空港×日を回せば全機の航跡をまとめて持っていける。adsb.lol の「大量に配り直さない」に近い |
| **cold-tracks**（関数、ログイン不要） | 400日より前の日の同じ線 | 1回 3,000本・回数の上限なし | 同上 |
| reg_history(p_reg, p_days)（anon） | 1機の便（30日まで・80件） | 機体ごと | 機体を回せば reg_legs を持っていける。量は小さい |
| livery_board・predict_rotation_*・usual_late・foreign_late | 塗装機や1便の答え | 少ない | 問題なし |
| airport-traffic（関数） | いまの空港のまわりの位置 | 置き場30秒 | 自分のアプリで位置を見せる使い方で問題なし |

**上限の案**（どれも画面の作りに関わるので、まだ作っていない）
- 案1（おすすめ・画面は変わらない）：airport_tracks と cold-tracks をログインした人だけにし、1人1時間あたりの日数に上限（例 60日）。ログインしていない人とデモは今日と前の7日だけ。空の道すじは決定事項の機能なので、ログインした人は今までどおりどの日も見られる。移行（関数の grant と小さな数える表＋RLS）とチェックイン担当への依頼（呼ぶときにログインの鍵を付ける）
- 案2：日付の上限だけ（ログインなしは前の7日まで）。移行1本で済むが、ログインしない人は古い日が見られなくなる
- 案3：今のまま（線だけで便名がないので、配り直しの価値は小さいと見る）

## 本人に決めてほしいこと
1. adsb.lol の鍵を取る（どの鍵か：まずは匿名の鍵で試す→1か月ごとに取り直しが要るので、続けるなら adhoc の鍵を申し込むのがおすすめ）。取ったら Supabase の秘密の設定に `ADSBLOL_API_KEY`、案内のヘッダー名が `api-auth` でなければ `ADSBLOL_KEY_HEADER` も入れる。入れたあとログの「adsb.lol 429」が減るか見る
2. adsb.im の条件：https://adsb.im/ と github.com/vradarserver/standing-data の LICENSE を開いて確かめるか（この回の環境では開けなかった）
3. 外に返す口の上限：案1・案2・案3のどれか（おすすめ案1）
4. 「反映して」（表は変えないので関数の公開だけ。鍵がなくても今までどおり動く）
