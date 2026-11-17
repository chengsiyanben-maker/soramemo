# 「いつもより○分遅い（推定）」の画面に要る関数の報告

担当：データ（data）　ブランチ：data/usual-late-rpc（main 32d923d から）　日付：2026-11-17（火）
PM の指示：11/17 12時20分（決定事項【11/17】いつもより遅い・案A、design/usual-late 2版の「データ担当へ」）。本番には入れていない。

## 1. 作ったもの
- 移行 **185** `20261117000185_usual_late.sql`：読むだけの関数 `usual_late(p_flight, p_reg, p_day, p_arr, p_land)` を1つ足しただけ。**表は変えていない**（RLS も今のまま。anon・authenticated は関数の実行だけ）
- テスト **t124** `tests/sql/t124_usual_late.mjs`（32項目）

## 2. 呼び方と返す形（チェックイン担当へ渡す）
```js
// 乗る便のカード：flight-live の返事の land_pred（着陸の見込み）を渡す。案内板・便のくわしくは便名か登録記号だけでよい
const { data } = await sb.rpc('usual_late', { p_flight: 'BA5', p_land: live.land_pred ?? null });
// 登録記号から：{ p_reg: 'G-XWBA' }／空港を決めたいとき：{ p_arr: 'HND' }／前の日：{ p_day: '2026-11-16' }（前7日〜次の日まで）
```
```json
{ "flight": "BA5", "reg": null, "callsign": "BAW5", "day": "2026-11-17", "arr": "HND", "reason": null,
  "usual": { "time": "19:35", "mins": 1175, "n": 7, "dow": 1, "spread": 16, "weeks": 8 },
  "eta":   { "at": "2026-11-17T11:07:00Z", "time": "20:07", "src": "live", "landed": false, "iata": "HND" },
  "late_min": 32, "kind": "late", "event": null, "divert_to": null, "curfew_near": null,
  "seen_at": "…", "ground": false,
  "source": "adsb.lol（ODbL）", "note": "推定です。定刻や航空会社の発表ではありません" }
```
| 画面（design/usual-late 2版） | 使う値 |
|---|---|
| 大きな「20:07 ごろ」 | eta.time（eta が null なら U1n-v2「見込みはまだ出せません」） |
| 札「いつもより32分遅い（推定）」 | kind が late のとき late_min。usual なら「いつもどおり」、early なら「いつもより○分早い」（-late_min）。null なら札を出さない |
| 「いつもは 19:35 ごろ」 | usual.time（usual が null なら「いつもの時刻はまだありません」） |
| 「月曜日・前の8週の7回から」 | usual.dow（0＝日曜…6＝土曜。null は曜日を問わない → 「前の8週の7回から」だけ）・usual.weeks・usual.n |
| U4 のばらつき | usual.spread（四分位の幅・分）。「19:28〜19:44」と出すなら time ± spread/2 |
| 箱の中の1行 | note と source をそのまま |
| 着いたあと（U3・U4） | eta.landed が true（実績の着陸）・eta.iata |
| ダイバート・引き返し（U2c） | event（'divert'・'return'）・divert_to。このときは late_min・kind は null（比べない） |
| 門限に近い（U2b） | curfew_near（見張りの関数をつなぐまでは null） |

- 着く見込みの元（eta.src）：`track`＝その日の実績（着いたあと。3時間ごとに作る foreign_legs）→ `live`＝画面が渡した p_land（flight-live の land_pred。いまの15分前〜20時間後のものだけ）→ `watch`＝見張り（foreign_watch.eta、10分以内に書かれたもの）。どれもなければ eta は null
- **比べるのは着陸の時刻**：いつもの時刻（foreign_usual）は航跡の着陸の時刻なので、flight-live の `eta_pred`（駐機場に着く見込み）ではなく `land_pred` を渡す
- `reason`：'odpt'（JAL・ANA など ODPT の会社。画面は今までどおり ODPT の定刻と遅れ）・'unknown'（記号を知らない・登録記号がその日と前の日に見えていない）。形のちがう値（便名も登録記号も読めない・空港や日の形がちがう）は null
- 札の幅は画面案どおり（15分以上遅い＝late・前後14分以内＝usual・15分以上早い＝early）
- 誰が乗るか・誰が選んだか（push_subs）は返さない

## 3. 確かめた結果
- t124：32項目すべて OK（便名・登録記号・先頭の0、曜日を先に、見込みの元の順、0時をまたぐ便、次の日・前の日の同じ便を取らない、ダイバート、odpt・unknown・null、権限、表は読めないまま）
- 番号の確かめ（migrations.mjs check）：175件で重なりなし
- SQL のテスト全部：125本すべて通過（下の 6）

## 4. 迷った点
- 飛んでいる間の見込みをサーバーだけで出すには機体の速さが要るが、live_positions に速さの列がない。そこで乗る便のカードは flight-live の land_pred を渡してもらう形にした（画面はすでに flight-live を呼んでいる。値は表示のずれを計算するだけで、どこにも書かない）。案内板・便のくわしくでは見込みは実績か見張りの分だけになる
- 見張りの関数（flight-watch に foreign_watch をつなぐ、帳面の 0000000000000000000a）はまだ。つないだら foreign_watch.eta を**着陸の見込み**で書き、門限は state.curfew_near（true／false）に入れる約束にした

## 5. 本人に決めてほしいこと
1. 案内板（U3）で、乗る便に選ばれていない飛行中の便にも見込みを出したいか。出すなら live_positions に速さ（kt）を足して、関数の中で見込みを出す案を作る（airport-traffic の書き込みに1列足す。表の移行と RLS はセット）
2. 「反映して」が出たら番号を確かめる（main に別の移行が先に入っていれば rebase。PR #111 の 183 とは別の番号なので、どちらが先でもよい）

## 6. SQL のテスト全部
手元で tests/sql の t*.mjs を全部（125本・約35分）流して、すべて通過。経営・チェックインのテストの値は変わらない（表を変えていないため）

## 7. 本人に流してほしい読むだけの SQL（反映の前でよい。重くない）
```sql
-- いつもの時刻が曜日ごとにある便と、曜日を問わないだけの便の数（画面の「月曜日」がどのくらい出るか）
select dep_here, count(*) filter (where dow >= 0) dow_rows, count(*) filter (where dow = -1) all_rows,
       round(avg(spread) filter (where dow = -1), 1) avg_spread
  from public.foreign_usual group by 1 order by 1;
```

## 8. ほかの担当への依頼
- チェックインへ（PM から checkin.md に写してほしい）：上の 2 のとおり `rpc('usual_late', …)`。乗る便のカードは flight-live の `land_pred` を `p_land` に渡す。renderRideIntl・foreignHTML・spDetailHTML から。出典の文は時刻表にない便では ODPT を外して note・source を出す
