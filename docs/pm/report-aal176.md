# 報告：AAL176（N791AN）とアメリカン航空のワンワールド塗装（データ担当・11/23）

ブランチ data/aal-oneworld（main 9a79def から）。表・移行・RLS は変えていない（移行・テストの番号は使っていない）。チェックイン・経営への影響なし（運用タブ・特別塗装機の知らせに出る機体が2機増えるだけ）。

## 作ったもの
1. 読むだけの SQL：docs/pm/aal176-check.sql（①航跡の点 track_points ②機体ごとの便 reg_legs ③海外の会社の便 foreign_legs ④知らせの記録 livery_notified ⑤いまの位置 live_positions。どれも索引で引く・上限20秒）
   - live_positions は15分で消える「いまの位置」なので、19:30〜21:30 の記録は ①〜③ で見る
   - **track_points は36時間で消える。11/24 朝8時半（日本時間）までに流してほしい**（それより後は ① が 0 件。②③ は残る）
2. 塗装の一覧（_shared/liveries.ts の ALLIANCE）にアメリカン航空の 777-200ER を2機足した：N791AN・N796AN →「ワンワールド塗装（777-200ER）」、kind alliance（海外の会社なので知らせが出る＝11/16 案3-A）
   - 出典：airportspotting.com「A Guide to American Airlines Special Aircraft Liveries」（ワンワールドの文字と塗装の機体として N791AN・N796AN を明記）。N791AN は World Airline News（2009-04-28）で初のワンワールド塗装機と確認。Flightradar24 は使っていない
   - 同じ一覧の 737-800（N837NN・N919NN・N973AN）は日本に来ないので入れていない
   - アメリカン航空の公式の発表（2009年）は登録記号を書いていなかった

## 確かめた結果
- deno test 全部 306本 通過（liveries_test に1本足した：2機がワンワールド塗装・alliance で出る、737 は入っていない）。deno check 通過
- 11/22 に知らせが出なかったのは、一覧にアメリカン航空が1機もなかったため（④ が 0 件なら確定）

## 本人に決めてほしいこと（PM のおすすめで可）
1. 出典の強さ：airportspotting は撮る人向けの専門サイトで、アメリカン航空の公式の一覧ではない。このままでよいか（おすすめ：このまま。見つかれば公式・報道に差し替える）
2. 反映：コードだけ（移行なし）。airport-traffic・flight-watch など liveries.ts を読む関数の出し直しで効く
3. aal176-check.sql を 11/24 朝8時半までに流してもらう
