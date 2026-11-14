# 海外の空港の止まり具合を作った報告

担当：データ（data）　ブランチ：data/world-ops　日付：2026-11-14（土）の回
PM の指示：11/15 0時10分（本人「OK」：report-world-ops-sources の案1・2。決定事項【11/15】）。本番には入れていない（「反映して」待ち）。画面はまだ（デザイン担当の案のあと、チェックイン担当）。

## 1. 作ったもの
- **移行 169 world_ops**（20261115000169_world_ops.sql。先頭に lock_timeout 10s）
  - 表 **world_airport_status**（iata・source 'faa'・kind［ground_stop 地上待機・gdp 出発の間引き・closure 閉鎖・delay_arr／delay_dep 15分以上の遅れ・deicing 除氷］・reason・starts・ends・avg_delay・max_delay・trend・first_seen・feed_at（FAA の Update_Time）・fetched_at・ended_at）。続いているものは空港・種類ごとに1行（部分の一意の索引）。**RLS 有効・誰でも select、書くのは service_role だけ**
  - world_status_put（取り込み1回分：続きは書き直し・なくなったものは消さずに ended_at・新しく始まったものを返す。一時の表は使わない）／world_status_rows（中で使う）：service_role だけ
  - **world_status_now(p_iata)**：いま出してよいもの（終わっていない・Update_Time も取った時刻も10分以内）。取れない・古いときは何も出ない
  - **world_flight_counts(p_date)**：今ある JAL・ANA の国際線（flight_schedule）を、海外の空港（日本の空港の表にない記号）ごとに「便・欠航・30分以上の遅れ」に数える。共同運航（同じ出発・到着・定刻）は1便、欠航は遅れに数えない。anon・authenticated に実行だけ
  - **world_airport_ops(p_iata)**：画面で使う。`{ source, note, airports: [{ iata, faa: [{kind, reason, starts, ends, avg_delay, max_delay, trend, since}], flights, cancelled, late30 }] }`。note に「出典：FAA NAS Status。運航の判断には使えません。遅れることがあります。便の数は JAL・ANA の運航情報（ODPT）から数えたものです」。止まっている空港が先
  - 通知の記録 alert_push_log に world 列と rank 0（止まり具合だけ）を足し、alert_push_claim に「止まり具合がはじめて分かった・変わったら送り直す」を足した（止まり具合だけの通知で遅れの通知は上書きしない）。RLS は今のまま（関数だけ）
  - pg_cron：world-status（2分ごと・statement_timeout 10s）・world-status-cleanup（毎日 4時35分 日本時間・30s。終わって3日・3日取れていない行を消す。航路・機体の記録ではない）
- **関数 world-status**（supabase/functions/world-status、config.toml に追加）：FAA の XML を1回読み、就航先だけ残して world_status_put。古い（10分より前）・取れないときは書かない。地上待機・閉鎖・出発の間引きが新しく始まった空港は、その空港を出る・着く、まだ着いていない便（定刻が14時間前〜12時間後）について notifyFlights を呼ぶ
- **_shared/faa_nas.ts**：XML の読み方（<ARPT> を含むかたまりを広く拾う）・時刻（Update_Time・「6:30 pm PST」・「Nov 15 at 06:00 UTC」）・就航先の一覧 US_SERVED（24空港・日本語の名前つき）
- **乗る便の通知（alert_merge.ts・alert_push.ts）**：1つの便の1つの通知に1行足す（新しい通知は増やさない・tag は同じ fw-便名@運航日@出発空港）
  - 例：「出発が約40分遅れる見込み\n到着地ロサンゼルスで地上待機中（FAA・15時30分まで見込み）」
  - 着く空港はまだ着いていない便、出る空港はまだ出ていない便だけ。同じ空港に2つあれば 閉鎖 → 地上待機 → 出発の間引き。15分以上の遅れ・除氷は画面だけ（通知には足さない）
  - 遅れのお知らせのない便は、「この便に乗る」の人にだけ、止まり具合だけの通知（rank 0。例「JL62 成田→ロサンゼルス：到着地ロサンゼルスで地上待機中（FAA・…）」）。空港ごとの通知の人には出さない
  - 乗る便は、15分未満の遅れでも止まり具合があれば届く
- 影響：**チェックイン（運用タブ・乗る便の通知）**。経営は使わない（表も関数も読まない）

## 2. 確かめた結果
- SQL のテスト **t108（23項目）**：取り込みの始まり・続き・終わり・また始まり、10分より古いものは出さない、国際線の数え方（共同運航・欠航・別の日・国内線）、画面の関数の形と出典、通知の記録（rank 0・送り直し・上書きしない・今までの30分の決まり）、RLS と権限、仕事の上限。すべて通過
- 関係するテスト t107（30）・t15・t18・t01・t51 通過。番号の重なりなし（161件）。SQL のテスト全部も通過（下）
- 関数のテスト：faa_nas_test（8）・alert_merge_test（20、止まり具合の7つを足した）を含め **deno test 255本すべて通過**。この回は Deno を入れられたので、本物の deno test で流した。world-status・odpt-status・flight-watch の型の確認も通過
- 全体の流し：SQL のテスト全部（111本、t49 も含む）すべて通過（11/14、手元で約30分）

## 3. まだ確かめていないこと
- **FAA の XML の本物の形**：この回も nasstatus.faa.gov を開けなかった（取得の許可が下りなかった）。読み方は FAA の昔からの AirportStatus の形（Ground_Delay・Program・Delay・Airport の入れ物、ARPT・Reason・Avg・Max・End_Time・Start・Reopen・Arrival_Departure Type）に合わせ、名前の違う入れ物でも <ARPT> を含めば拾うようにした。反映の前に、本人のブラウザで XML を開いて1回分を docs/pm/faa-sample.xml に貼ってもらえれば、それでテストを足す
- 時間帯の略号のない時刻・知らない略号の時刻は「終わりの見込みなし」にする（文に「○時まで見込み」が出ないだけ）
- 本番の Edge Functions では未確認（反映のあと、world-status の返す ms・rows・started を cron の記録で見る）

## 4. 本人に決めてほしいこと
1. 反映してよいか（移行169・関数 world-status。画面はまだなので、反映すると通知の1行と表・関数だけが動く）
2. 就航先の一覧（US_SERVED の24空港）：docs/pm/world-destinations.sql（PR #92）の結果で直すか。今の見込みにはサイパン・アンカレッジ・ラスベガス・デンバーなども入れている（直行便がなくても害はない）
3. 止まり具合だけの通知（rank 0：遅れのない乗る便にも「到着地で地上待機中」を出す）を入れてよいか。止めるなら world-status の notifyFlights の第3引数を false にするだけ
4. FAA の XML を1回分貼ってもらえるか（3 のとおり）

## 5. ほかの担当への依頼
- デザイン担当へ：運用タブの海外の便の札・空港のお知らせの画面案。中身は world_airport_ops の返す形（上の 1）。出典の文（note）を必ず出す・「予想」でなく「FAA の発表」なので「保証しない」の書き方は運用予想とは別
- チェックイン担当へ：画面案のあと、rpc('world_airport_ops', { p_iata }) を呼ぶ。止まっていない空港も便の数で返るので、出すのは faa が空でないか cancelled・late30 が1以上の空港だけ、の案。乗る便の通知の本文に改行（\n）が入るようになる（sw.js はそのまま表示でよいはず。確かめてほしい）
