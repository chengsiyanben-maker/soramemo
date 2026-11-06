# 修行モードの棚卸し（11/6・修行モード担当の最初の回）

コードは変えていない。main（14916e9、新しいホームが入った版）を読んだ結果。

## 作ったもの
- この棚卸し（関数・画面・テストの一覧と、直したほうがよい所の候補）
- 時刻表の更新を確かめる読むだけの SQL：`docs/pm/shugyo-timetable-check.sql`（本人が SQL Editor で流す）
- t62 の調べ（下の「t62」）

## 画面と関数（src/index.html）

| 画面 | 入口の関数 | 中で使う主な関数 |
|---|---|---|
| ホームの修行のカード（PERSONA が shugyo のとき） | `renderShugyoCard`（4932行あたり） | sgYear・sgGoal・sgLine・sgPlanVerdict・sgDrafts・sgLoadRoute・sgFlState |
| 修行のタブ（v-sg）／窓（dShugyo） | `renderShugyo`・`openShugyo`・`sgGo` | 下のページを SG_PAGE で切り替える。sgTabOn・sgCanTab・sgScroller・sgKeep |
| まとめ（main） | `sgMain` | sgHero・sgTri・sgPlanVerdict・sgConfirmHTML・sgFillRoutes |
| 予定と計画（plan） | `sgPlan` | sgFuture・sgPlanSum・sgPlanLeg |
| 今年の記録（year） | `sgYearPage`・`sgYearPer` | sgYear |
| 路線の運航（ops／routes） | `sgOps`・`sgFillOps`・`sgRoutesPage` | sgLoadRoute（airport-now、2分の覚え）・sgFlState |
| 計画を作る：探す（find・P1） | `sgFind`・`sgFillFind` | sgPQ・sgLoadTT（plan_timetable）・sgSolve・sgLatest・sgNextAps・sgTripLabel・sgDayBar |
| 計画を作る：組む（build・P2） | `sgBuild`・`sgOpenBuild` | sgBuildLegs・sgLegPrice・sgAddPlans |
| 計画を作る（端末版・旧） | `sgPlanner`・`sgBudget` | sgTrip・sgTripCalc・sgSuggest・sgMoney |
| 案をくらべる（compare・P3） | `sgCompare` | sgDrafts・sgDraftStat・sgDraftItems・sgReachWith・sgReachText |
| 年末までの道のり（road・P4） | `sgRoad` | sgReachWith・sgDrafts |
| 実績の確認 | `sgConfirmHTML`・`sgPast`・`sgRecordPlan` | sgDoneKeys・sgPlanDone |
| 会員情報・いまのポイントを合わせる | `sgProfile`・`sgSyncHTML`・`sgActualNote`・`sgSyncOld` | sgBonus |
| この路線に乗ったら（quick） | `sgQuick` | sgLeg・運賃のピル（sgFarePills・sgFareOpts） |
| 成績の「修行のまとめ」 | `renderSgSum`（成績の renderStats から呼ぶ） | sgLedger・sgLedgerHTML・sgPer |
| フライトの見方「修行」 | 4371行あたりで `sgLedgerHTML` を返す | sgLedger |

計算の芯：`sgLeg`（1区間のマイル・PP／FOP・ボーナス）、`sgBonus`、`sgPay`、`sgYear`（今年の実績＋会社のサイトに合わせた数字）、`sgGoal`・`sgNeed`・`sgReach`、乗り継ぎの決まり `SG_MCT`・`SG_XFER`・`sgMct`。保存は `sgGet`・`sgSave`（サーバー版は shugyo_prefs、端末版は localStorage）。金額は `SG_MONEY`（soramemo.sgmoney=1 のときだけ出す）。

## テスト
- ブラウザ：t64（窓で開く修行）・t73（修行モード）・t75（計画を作る）・t76（案をくらべる・道のり）・t77（実績の確認）・t78（運賃の座席と区分・自動／手動）・t80（区間ごとの金額・空港を移る乗り継ぎ）・t62（使う人ごとの構成。修行の部分あり）
- サーバー：tests/sql/t33_shugyo.mjs（shugyo_prefs。運営コンソールが手元にないので今回は流していない）
- 今回の結果：t62・t64・t73・t75・t76・t77・t78・t80 は 8/8 成功（1回ずつ）

## t62（「修行：開き直しても覚えている」が前から落ちる）
- main で t62 を10回流すと **4/10 しか通らない**。落ちるのは「修行：開き直しても覚えている」と「断ったらしばらく聞かない」で、どちらも `pg.reload()` のあと
- 原因はアプリではなくテストの開き方：file:// のページを読み込み直すと、Chromium が直前に書いた localStorage をときどき落とす（チェックイン担当が PR #20 で突き止めたものと同じ）
- **PR #20（checkin/test-waits）の t62 で10回流すと 10/10 成功**。修行側で別に直すことはないので、ブランチ shugyo/fix-t62 は作らなかった。PR #20 が main に入れば直る

## 直したほうがよい所の候補（今回は直していない。順に、PM と本人に選んでもらう）
1. **年の区切りが端末の時刻で決まる**：`sgYear` は便の年を `new Date(r.t).getFullYear()`（端末の時刻）で決め、今月も `new Date().getMonth()`。一方 `sgLedger`・`sgToday` は日本時間。日本時間でない端末だと、1月1日の朝（日本時間 0〜9時）の便が前の年に入る。年末の修行の追い込みの時期なので、12月中に日本時間へそろえたい（`sgYear`・`sgMain`・`sgMoney`・`renderShugyoCard` の月の取り方）
2. **FOP・PP の端数の扱いが計算ルールとずれているかもしれない**：`sgLeg` はフライトマイルを切り捨て（Math.floor）、ポイントは四捨五入（Math.round）で出している。JAL は「FOP ＝ フライトマイル×2＋ボーナス」なので、普通席50%などで区間マイルが奇数のとき 2 ずれる（例：287マイル×50% → 切り捨てなら 286、今は 288）。ANA の PP の端数も同じ。各社の公開ページで端数の扱いを確かめてから直したい（計算ルールの文書に端数の行を足す）
3. **JAL の乗り継ぎ時間がまだ公式で確かめられていない**：計算ルールの文書に「那覇30分・その他20分は旅行会社のまとめの値。作る前に JAL の公式ページで確かめる」とあるが、`SG_MCT.JAL` はその値のまま入っている
4. **ANA の SFJ（スターフライヤー）便の乗り継ぎ**：決まりでは SFJ に乗り継ぐときは羽田50分だが、`SG_MCT.ANA` は運航会社を見ずに羽田35分。ODPT の ANA の時刻表に SFJ 運航の便が入っているかを確かめ、入っていれば分ける
5. **JAL のカード払いのマイル**：`sgPay` は `Math.round(金額 ÷ 200) × 2`。「200円で2マイル」なら切り捨てのはず（例：1万300円 → 今は 104、切り捨てなら 102）。小さい差なので 2 と一緒に確かめる
6. **`sgSeg` を運用のゴーアラウンドの設定（gaSetHTML）も使っている**：修行のピルの見た目を変えると運用の画面も変わる。修行で変えるときは別の関数に分けるか、チェックイン担当に先に知らせる
7. **端末版の古い「計画を作る」（sgPlanner・sgBudget・sgSuggest・sgMoney）**：サーバー版は「探す・組む」（sgFind・sgBuild）に替わり、端末版だけが古い画面を使う。金額を隠している今は、予算まわりの多くが画面に出ない。残すか、端末版も「自分で区間を入れて計算する」に寄せて消すかを決めたい（消せば 200行ほど減る）
8. **時刻表の期限**：ANA は 11月30日まで（10/28 時点）。更新が来ていないと、12月の「探す」は「まだ出ていません」になる。確かめる SQL を用意した（下）

## 本人に決めてほしいこと
- 上の候補 1（年の区切りを日本時間へ）を 12月の前に直してよいか（画面は変わらない。数字の数え方だけ）
- 候補 2・5（端数）は、各社のページで確かめてから直す、でよいか
- 候補 7（端末版の古い計画の画面）を残すか、消すか
- `docs/pm/shugyo-timetable-check.sql` を SQL Editor で流して、ANA の「最後の日」が 12月以降になっているか見てほしい（なっていなければ、データ担当に取り込みを見てもらう）
