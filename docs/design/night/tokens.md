# 夜の画面の色と字（トークン）

画面案：docs/design/night/（1版）。11/8 の本人の決定「夜の画面」による。
チェックイン担当が、今の色の変数（src/index.html）に重ねて使う形。夜のときだけ `:root[data-night]` を付ける想定（付け方・切り替えの処理はチェックイン担当が決める）。

## 夜の画面の基本の値

| 名前 | 値 | 使う所 |
|---|---|---|
| --n-bg | #05080D | 地（画面全体） |
| --n-panel | #0D131B | カード（計器の盤面）・シート |
| --n-raise | #151D28 | ピル・押せる行・入力欄 |
| --n-deep | #03050A | タブ帯の下・暗い面 |
| --n-ring | rgba(150,175,205,.10) | 盤面のふち（内側の影として。線は引かない） |
| --n-ink | #B9C4D0 | 本文（真っ白にしない） |
| --n-strong | #D6DEE6 | 見出し・大事な字 |
| --n-sub | #8693A3 | 補足・単位・ラベル |
| --n-glow | #5BCB88 | 光る色1：計器の数字・選んでいるもの・判定範囲・強いボタンの地 |
| --n-glow-halo | rgba(91,203,136,.38) | 光る数字のにじみ（text-shadow 0 0 10px） |
| --n-glow-wash | rgba(91,203,136,.12) | 選んでいるピルの地 |
| --n-amber | #E8A84A | 光る色2：いまここ・注意・予想・特別塗装機・外す |
| --n-amber-halo | rgba(232,168,74,.35) | 琥珀のにじみ |
| --n-amber-wash | rgba(232,168,74,.12) | 琥珀の札の地 |
| --n-jal | #D9707C | 光らない。航空会社の小さな点だけ |
| --n-ana | #86A6E6 | 同上 |
| --n-chart-sea / land / coast / grid / apt | #060B12 / #0C1219 / #283442 / rgba(120,150,190,.07) / #7E8C9C | 夜の航空図 |
| --n-mono | "DejaVu Sans Mono","SF Mono",ui-monospace,Menlo,monospace | 計器の数字だけ |

字と地の差（測った値）：本文 #B9C4D0 は地で 11:1 前後、補足 #8693A3 はカードの上で 4.5:1 以上、緑・琥珀はカードの上で 9:1 前後。

## 光る数字の決まり

- 光らせるのは「その画面でいちばん大事な数字」だけ（今日の数字・集めた数・実績・風・あと何分・確認コード）。一覧の数字（日付・距離・時刻）は光らせず、ふつうの書体の揃った数字（font-variant-numeric: tabular-nums）
- 字の形：`font-family:var(--n-mono); font-weight:700; color:var(--n-glow); text-shadow:0 0 10px var(--n-glow-halo)`
- 単位は光らせない：ふつうの書体・12px・--n-sub
- 空港コード・滑走路の名前・便名は光らせない（字が入るので「数字だけ」に当たらない）
- 光る色は緑と琥珀の2色だけ。ほかの色を光らせない

## 今の変数への重ね方（対応表）

| 今の変数 | 夜の値 |
|---|---|
| --sky | var(--n-bg) |
| --paper | var(--n-panel) |
| --ink | var(--n-ink) |
| --sumi | var(--n-sub) |
| --line | rgba(150,175,205,.10)（線を引いている所は夜は内側の影に） |
| --shu / --shu-text | var(--n-glow) |
| --shu-wash | var(--n-glow-wash) |
| --on-shu | #04130A |
| --gold / --gold-text / --gold-badge | var(--n-amber) |
| --on-gold | #120C02 |
| --dot | #2A3542 |
| --hero | var(--n-panel) |
| --nav-acc / --nav-on | var(--n-glow) |
| --nav-glass | rgba(10,15,22,.94) |
| --nav-ink | var(--n-sub) |
| --hm-ink / --h3-ink / --st-ink / --a-ink | var(--n-ink) |
| --h3-strong / --a-strong | var(--n-strong) |
| --hm-sub / --hm-mute / --h3-sub / --h3-mute / --st-sub / --a-sub | var(--n-sub) |
| --hm-card / --h3-card / --st-card / --a-card | var(--n-panel) |
| --h3-bg / --a-bg / --hm-tint / --st-wash | var(--n-bg) |
| --hm-pill / --h3-pill / --a-pill / --st-track / --a-track | var(--n-raise) |
| --hm-shadow / --h3-shadow / --st-shadow / --a-shadow | 0 10px 28px -14px rgba(0,0,0,.9), inset 0 0 0 1px var(--n-ring) |
| --cta-hi / --cta-lo | var(--n-glow)（グラデーションにしない） |
| --cta-text | #04130A |
| --cta-glow | var(--n-glow-halo) |
| --jal / --a-jal | var(--n-jal) |
| --ana / --a-ana | var(--n-ana) |
| --chart-apt | var(--n-chart-apt) |
| --chart-grid | var(--n-chart-grid) |
| --c-bg / --c-land / --c-coast | var(--n-chart-sea) / var(--n-chart-land) / var(--n-chart-coast) |
| --h3-ok | var(--n-glow) |
| --h3-off-bg / --h3-off-ink | var(--n-raise) / var(--n-sub) |
| --mil / --glider / --field / --secret | 光らせない。夜は 4.5:1 を保つ明るさに（今の「案内板」の値 #7FA6D9 / #5CC1F0 / #7BC48E / #B99AE0 をそのまま使える） |

## 書体
- 本文・見出し・ラベル：ふだんの --gothic のまま
- 計器の数字：--n-mono（数字だけ）
- ドット文字（DotGothic16）とパタパタは、夜も「近い空港のコード」と「最近の印」だけ。夜の画面の数字には使わない（出発案内板風に寄せない）

## 今のアプリの「案内板」の配色との違い
今の `data-palette="board"` は黒地に琥珀・ドット文字の数字。夜の画面は緑が主で、琥珀は注意だけ、数字は等幅。夜の画面を入れるとき「案内板」の配色を残すか（夜と2つになる）は本人に聞く。
