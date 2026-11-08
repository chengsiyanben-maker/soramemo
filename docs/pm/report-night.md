# 報告：夜の画面の画面案（1版）

- 担当：デザイン（design）／ブランチ：design/night／11/8 23時の PM の指示（帳面「PM から積んだ次の仕事（夜の画面）」）と 11/8 23時10分の PM の指示（本人「決まりなしのB案は夜限定でやってほしい」・報告に改善担当に見てほしい点と変数の一覧）
- アプリのコードは変えていない。画面案は docs/design/night/

## 作ったもの
- 画面（11枚・HTML と png/、667 の高さも png/*-667.png）：01 ホーム／02 図鑑／03 フライト／04 運用（滑走路）／04b 運用（撮る人の見方）／05 修行／06 マイページ（昼と夜の3つの切り替えつき）／07 タブを選ぶ／08 ログイン（確認コード）／09 昼と夜の切り替えのシート／10 はじめて夜になったときのカード（案）
- 色の決め方：tokens.css（今の色の変数 --sky・--hm-*・--mp-* などに `data-night="on"` で重ねる形）と tokens.md（13色の表・使い方の決まり6つ）
- 一覧：index.html

## 案B からの直し（指示どおり）
- 本文はふだんの書体。等幅の計器の字は数字だけ。光らせるのは1画面に主役の数字1〜2つ
- 光る色は4色 → 2色（緑＝主役の数字・入／琥珀＝いまの場所・選んでいるもの・注意）。水色・桃色はやめた。金と JAL赤・ANA青も夜は使わない
- 字と地の差：全部の字で 4.5:1 以上（本文 約11:1・補足 約6:1・単位 約5:1）。本文は真っ白にせず #BCC6D1
- 外した決まりは「画面全体を黒にしない」だけ。角丸カード＋薄い影・ピル型・黒い区切り線なし・航空図風の地図は守った（案B の四角い枠と押しボタンはやめ、入／切の札だけ残した）

## 測った値（幅390・高さ844と667、メモを外して）
- 13px 未満の字：単位12pxだけ（svg の中の字も縮んだ大きさで 0）
- 44px 未満の押す所：0（入／切の札は高さ36px だが、押すのは高さ56px の行ごと）
- 4.5:1 未満の字：0／はみ出し：0
- 使っている鮮やかな色：どの画面も2色（#5FD993・#F0AC4E）だけ
- 開いたときタブ帯と重なる字：844 でホーム1（いちばん下の「非公式アプリ」の1行）・マイページ2（下の行）。どちらも下に送って読む所

## 迷った点
- 案B の「四角い計器の枠・押しボタン・ソフトキー」は、外してよいのが「画面を黒に」だけなので、角丸とピルに戻した。計器らしさは等幅の光る数字・距離の円・入／切の札で出した
- 会社の色を夜は使わない形にした（光る色を2色にするため）。修行の JAL／ANA はピルの字で分かる
- 修行の予定＝薄い金・計画＝薄い青は、夜は塗り（実績）と縞（計画）＋凡例の字にした
- 撮る人の見方は、夜は光の向きの代わりに日の出の時刻を出した
- 10（はじめて夜になったときのカード）と、ホームの右上の「夜の画面」のピルは指示にない足しもの

## 本人に決めてほしいこと
1. 角丸カードとピルのまま（今の形）でよいか。案B の四角い枠・押しボタンに寄せたいか
2. 夜は JAL赤・ANA青・特別塗装機の金を使わない形でよいか
3. はじめて夜になったときに1回だけカード（10）を出すか。ホームの右上に「夜の画面」のピルを出すか
4. 位置がないときの日の入りの計算を「最後に近かった空港 → 東京」でよいか

## ほかの担当へ
- 改善担当：指示どおり本人の前に見てほしい（とくに光る数字の選び方が大事な所を分かりやすくしているか、04 運用の緑と琥珀の使い分け、07 の入／切）
- チェックイン担当：決まってから。tokens.css の 2.・3. を重ねる形。色をじかに書いている所（.darkcard など）の数を先に数えておいてほしい
- データ担当：昼と夜の設定（自動／いつも昼／いつも夜）を、隠す設定と同じ所に1つ足せるか（決まるまで作らない）

## 改善担当に見てほしい点
1. 光る数字の選び方：1画面に主役の数字1〜2つだけ光らせた。大事な所がひと目で分かるか（01 範囲まで・04 着陸の滑走路と風・05 今年の FOP）
2. 緑と琥珀の使い分け：緑＝主役の数字・入、琥珀＝いまの場所・選んでいるもの・注意。04 運用と 04b 撮る人の見方で、2色の意味が混ざって見えないか
3. 07 タブを選ぶの入／切の札：色を見分けにくい人にも分かるか。札は高さ36px で、押すのは高さ56px の行ごと。押せる所だと分かるか
4. 夜のデッキでのまぶしさ：本文 #BCC6D1・見出し #DCE3EA・琥珀の地のボタンが、暗い所でまぶしすぎないか
5. 却下済みの「アプリ全体を出発案内板風」に寄っていないか（等幅の字は数字だけ・パタパタは近い空港のコードだけ）
6. 05 修行の実績と計画を塗りと縞で分けた形と、06 マイページ・09 シートの「自動／いつも昼／いつも夜」の分かりやすさ
7. 足しもの：10 はじめて夜になったときのカードと、01 右上の「夜の画面」のピルが要るか

## チェックイン担当に渡す色の変数の一覧
本体は docs/design/night/tokens.css（下の一覧はそこから写したもの）。`<html data-night="on">` を付けたときだけ効く。

### 新しく足す夜の元の色（:root）
| 変数 | 値 |
|---|---|
| --n-bg | `#05070B` |
| --n-panel | `#0D1218` |
| --n-panel-2 | `#141B24` |
| --n-ring | `rgba(150,170,195,.10)` |
| --n-ink | `#BCC6D1` |
| --n-strong | `#DCE3EA` |
| --n-sub | `#8996A7` |
| --n-mute | `#7D8A9B` |
| --n-glow-1 | `#5FD993` |
| --n-glow-2 | `#F0AC4E` |
| --n-glow-1-halo | `0 0 6px rgba(95,217,147,.45)` |
| --n-glow-2-halo | `0 0 6px rgba(240,172,78,.40)` |
| --n-on-glow | `#05070B` |
| --n-sea | `#060A0F` |
| --n-land | `#0F151C` |
| --n-coast | `#2B3746` |
| --n-ring-map | `#243040` |
| --n-grid | `rgba(95,217,147,.06)` |
| --n-shadow | `0 14px 30px -18px rgba(0,0,0,.9),inset 0 0 0 1px var(--n-ring)` |
| --n-num | `ui-monospace,"SF Mono","Menlo","Roboto Mono","DejaVu Sans Mono",monospace` |

### 今の変数の読みかえ（:root[data-night="on"]・:root[data-night="on"][data-palette]）
書き方は「今の変数→夜の元の色」。

| 今の変数 | 夜の値 |
|---|---|
| --sky | `var(--n-bg)` |
| --paper | `var(--n-panel)` |
| --ink | `var(--n-ink)` |
| --sumi | `var(--n-sub)` |
| --line | `#222C38` |
| --shu | `var(--n-glow-2)` |
| --shu-text | `var(--n-glow-2)` |
| --shu-wash | `var(--n-panel-2)` |
| --on-shu | `var(--n-on-glow)` |
| --gold | `var(--n-glow-2)` |
| --gold-text | `var(--n-glow-2)` |
| --gold-badge | `var(--n-glow-2)` |
| --on-gold | `var(--n-on-glow)` |
| --dot | `#2A3440` |
| --hero | `var(--n-panel)` |
| --jal | `var(--n-strong)` |
| --ana | `var(--n-strong)` |
| --mil | `var(--n-sub)` |
| --glider | `var(--n-sub)` |
| --field | `var(--n-sub)` |
| --secret | `var(--n-sub)` |
| --go | `var(--n-glow-1)` |
| --stop | `var(--n-glow-2)` |
| --nav-acc | `var(--n-glow-2)` |
| --nav-glass | `rgba(13,18,24,.92)` |
| --nav-edge | `var(--n-ring)` |
| --nav-ink | `var(--n-sub)` |
| --nav-on | `var(--n-strong)` |
| --nav-shadow | `0 10px 30px -6px rgba(0,0,0,.8)` |
| --hm-ink | `var(--n-ink)` |
| --hm-sub | `var(--n-sub)` |
| --hm-mute | `var(--n-mute)` |
| --hm-card | `var(--n-panel)` |
| --hm-tint | `var(--n-panel-2)` |
| --hm-pill | `var(--n-panel-2)` |
| --hm-shadow | `var(--n-shadow)` |
| --cta-hi | `var(--n-glow-2)` |
| --cta-lo | `var(--n-glow-2)` |
| --cta-text | `var(--n-on-glow)` |
| --cta-glow | `transparent` |
| --cta-ring | `transparent` |
| --cta-ring2 | `transparent` |
| --a-bg | `var(--n-bg)` |
| --a-card | `var(--n-panel)` |
| --a-ink | `var(--n-ink)` |
| --a-strong | `var(--n-strong)` |
| --a-sub | `var(--n-sub)` |
| --a-mute | `var(--n-mute)` |
| --a-pill | `var(--n-panel-2)` |
| --a-track | `var(--n-panel-2)` |
| --a-wash | `var(--n-panel-2)` |
| --a-shadow | `var(--n-shadow)` |
| --a-cta | `var(--n-glow-2)` |
| --a-cta-text | `var(--n-on-glow)` |
| --a-jal | `var(--n-strong)` |
| --a-ana | `var(--n-strong)` |
| --bk-card | `var(--n-panel)` |
| --bk-ink | `var(--n-ink)` |
| --bk-sub | `var(--n-sub)` |
| --bk-mute | `var(--n-mute)` |
| --bk-pill | `var(--n-panel-2)` |
| --bk-track | `var(--n-panel-2)` |
| --lg-card | `var(--n-panel)` |
| --lg-ink | `var(--n-ink)` |
| --lg-sub | `var(--n-sub)` |
| --lg-mute | `var(--n-mute)` |
| --lg-pill | `var(--n-panel-2)` |
| --lg-stub | `var(--n-panel-2)` |
| --lg-track | `var(--n-panel-2)` |
| --op-card | `var(--n-panel)` |
| --op-ink | `var(--n-ink)` |
| --op-sub | `var(--n-sub)` |
| --op-mute | `var(--n-mute)` |
| --op-pill | `var(--n-panel-2)` |
| --h3-bg | `var(--n-bg)` |
| --h3-card | `var(--n-panel)` |
| --h3-ink | `var(--n-ink)` |
| --h3-strong | `var(--n-strong)` |
| --h3-sub | `var(--n-sub)` |
| --h3-mute | `var(--n-mute)` |
| --h3-pill | `var(--n-panel-2)` |
| --h3-hero | `var(--n-panel)` |
| --h3-hero-sub | `var(--n-sub)` |
| --h3-off-bg | `var(--n-panel-2)` |
| --h3-off-ink | `var(--n-sub)` |
| --h3-ok | `var(--n-glow-1)` |
| --s-bg | `var(--n-bg)` |
| --s-card | `var(--n-panel)` |
| --s-ink | `var(--n-ink)` |
| --s-mute | `var(--n-sub)` |
| --s-line | `#222C38` |
| --sg-bg | `var(--n-bg)` |
| --sg-card | `var(--n-panel)` |
| --sg-ink | `var(--n-ink)` |
| --sg-faint | `var(--n-mute)` |
| --sg-acc | `var(--n-glow-2)` |
| --sg-line | `#222C38` |
| --chart-bg | `var(--n-sea)` |
| --chart-land | `var(--n-land)` |
| --chart-coast | `var(--n-coast)` |
| --chart-grid | `var(--n-grid)` |
| --chart-apt | `var(--n-strong)` |
| --chart-route | `var(--n-glow-2)` |
| --chart-off | `#3A4654` |
| --c-bg | `var(--n-sea)` |
| --c-land | `var(--n-land)` |
| --c-coast | `var(--n-coast)` |
| --c-apt | `var(--n-strong)` |
| --av-hi | `var(--n-glow-2)` |
| --av-lo | `var(--n-glow-2)` |
| --gamebar | `var(--n-panel)` |

### 要素に直接書いてある変数（今の src/index.html で見つけた所）
- `dialog.mypage`：--mp-bg・--mp-card・--mp-ink・--mp-sub・--mp-mute・--mp-shadow
- `.boardzone`：--sky・--paper・--ink・--sumi・--shu・--shu-text
- `#dSpecial`・`#dLayout`：--s-mute　／　`.fwc`：--fw-mute
- 色をじかに書いている所（.darkcard・#v-log .lbtn など）は変数に置きかえてから重ねる。数はチェックイン担当が数えてほしい

### 夜だけの小さな部品
- `.n-num`：等幅の数字（数字だけに付ける）
- `.n-lit`：緑に光る数字（1画面に3つまで）／`.n-here`：琥珀に光る（いまの場所・いちばん近い時刻）

（数：新しい元の色 20・読みかえ 111）
