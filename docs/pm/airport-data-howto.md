# 空港のデータの作り方（滑走路の線・判定の範囲との比べ）

data/ap-shape（11/26）で作った。いまアプリが使う空港の表（airports・terminals）は変えていない。ここは「印のカード用の滑走路の線」と「判定の範囲の確かめ」を作る手順。

## 1. 元のデータ

| 元 | 中身 | 置き場 | 使い方 |
|---|---|---|---|
| そらメモの airports・terminals の表 | 空港 194 か所（86空港＋番外編）の点・半径・種類、ターミナル14か所 | `data/ap_shape/raw/master.json`（移行を全部流した模擬のデータベースから書き出す。本番にはつながない） | 正（どの空港を作るか・中心・名前） |
| 運用タブの AIP の線（`supabase/functions/_shared/ops_core.js` の rwy） | 14空港の滑走路の両端（国の AIP の座標から作った今の線） | `data/ap_shape/raw/aip_rwy.json`（同じ道具で写す） | いちばん優先する |
| OurAirports（runways.csv・airports.csv） | 滑走路の両端の座標・長さ・向き | `data/ap_shape/raw/oa_*_jp.csv`（全世界の CSV から日本の分だけ） | AIP の線がない空港。パブリックドメイン |
| 国土数値情報 空港データ C28（令和3年） | 空港の区域の面・ターミナルビルの点 | **リポジトリに置かない**（利用約款を読めていない） | 判定の範囲と比べる表を作るためにだけ読む |
| OpenStreetMap | — | 使わない | ODbL。配るデータに混ぜない（羽田の3D は別に © を出して使っている） |

## 2. 手で直す所
- `data/ap_shape/overrides.json` だけを手で直す（raw/ は直さない。作り直すと上書きされる）
- キーは ICAO（なければ airports の id）。`exclude`（外す線の名前）・`add`（足す線 `[緯度1, 経度1, 緯度2, 経度2, 名前]`）・`note`（理由）
- 新しい滑走路ができた・閉じた・OurAirports が古いときにここで直す。AIP の線がある14空港は ops_core.js（元は src/index.html の ops-core）を直すと両方に効く

## 3. 作る手順
```
cd tests/sql && npm install && cd ../..                      # 模擬のデータベース（PGlite）を使うため
node tools/ap_master_dump.mjs                                 # 1. master.json・aip_rwy.json
python3 tools/ap_shape.py subset <airports.csv> <runways.csv> # 2. OurAirports を日本の分だけに（https://davidmegginson.github.io/ourairports-data/ から）
python3 tools/ap_shape.py build                               # 3. runway_lines.json・preview.html・build_log.txt
python3 tools/ap_shape.py compare <C28 の UTF-8 フォルダ>      # 4. docs/pm/ap-shape-compare.md（shapely が要る）
python3 -m unittest discover -s tests/tools                   # 確かめ
```

線の作り方（build）
1. 空港ごとに線を決める：AIP の線 → なければ OurAirports の両端の座標 → それもなければ OurAirports の長さと向き（向きがなければ滑走路の番号×10から西偏を引く）で、空港の点を真ん中に作る（「推定」の札）。AIP の線にない向きの滑走路は OurAirports から足す（仙台の 12/30 など）
2. 線をまとめた外枠の真ん中を原点にした平面へ（横は cos(緯度) で縮める＝角度と縦横の比が実物と同じ）
3. 長い辺を 0.15〜0.85 いっぱいにし、短い辺は真ん中に寄せる。v は下向き（SVG と同じ）。小数3けた
4. 確かめ：86空港すべてに1本以上・全部の数字が 0.15〜0.85・AIP と OurAirports の向きのずれ（3°より大きければ build_log.txt に出す）。86空港に線のない空港があると止まる

## 4. 出来上がり
- `data/ap_shape/runway_lines.json`（約42KB・194 か所）：`airports[]` に `id`（airports の id）・`iata`・`icao`・`name`・`kind`（airport・field・glider・mil・secret・heli）・`game_target`・`src`（aip／aip+ourairports／ourairports／ourairports-est／none）・`lines`（`[u1,v1,u2,v2]` の並び）・`names`（滑走路の名前）・`span_m`（四角の1辺が実際に何 m か）
- `data/ap_shape/preview.html`：全部を1枚に並べた確かめ用のページ（昼夜の色あり）
- 画面での使い方の例（デザイン担当の design/stamp-card の 160 の箱なら）：`x = u × 160`・`y = v × 160`。長さは空港の大きさによらず四角いっぱい（Gemini の案どおり）。大きさで変えたいときは span_m を使う

## 5. 今の airports の表とのつなぎ
- `id` が airports の id と同じなので、画面は今の空港の表の id（`BY[id]`）で引ける。コードは iata（なければ icao）
- 表（データベース）には入れていない。画面に入れるときは、(a) 画面の中に持つ（約42KB・空港の表と同じく変わらない）か、(b) 表 `airport_runway_lines`（移行と RLS をセット）に入れて読むかを、印のカードの画面案が決まってから決める
- 判定（関数 checkin・_shared/judge.ts・画面の nearest）は円のまま。国土数値情報の面で判定を変える案は ap-shape-compare.md の4節（本人の OK が要る）

## 6. 更新するとき
- 年に一度か、滑走路の新設・閉鎖を聞いたとき：OurAirports を取り直して subset → build → preview.html を目で見る → テスト
- airports の表に空港を足したら、dump からやり直す
