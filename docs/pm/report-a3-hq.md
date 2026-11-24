# 報告：羽田の3D の機体を容量を気にせず最高の質に（checkin/a3-hq・11/24）

PM の積み（11/24 12時30分・本人「３Dモデルはもっと容量を気にせず，高いクオリティにして」）。main（#199 まで）から作った。季節の印のブランチ（checkin/drop-season-marks）とそのコードには触っていない。

## はじめに書いた3行
- 変えるファイル：src/index.html（3D の機体の形・絵・材質・影・仕上げ・質の切り替え）・web/（組み立て直し＋映り込みの絵 web/3d/env-day.jpg）・テスト t142・t160・t161・t168
- 手順：#191（a3-models-max）の細かい形・絵・材質・影を今の main に移す → 「質3＝最高」にして、重いときは今までどおり自動で下げる → 737 の翼の先・汚れの絵・CC0 の映り込み・物の隙間の影・灯りのにじみ・ギザギザ消しを足す
- 確かめ方：3D のテスト全部（t142・t160〜t168・t181）と tests/ops、今の本番と同じ視点の写真（docs/pm/shots-a3-hq/）、増えた量・読み込みの時間・1コマの時間・GPU のメモリを測る

## 作ったもの
- **質3（最高）をはじめの質にした**（古い iPhone などの判定 a3Weak の端末は今までどおり質1、軽い表示は質0）。質3 のときだけ下のすべて。1コマが重い（60コマの平均が45ms より長い）と今までどおり自動で質2 に下げ、仕上げをやめて機体を前の細かさで作り直す（a3Quality）。「軽い」の設定は今のまま
- 形（#191 から移したもの＋足したもの）：1機種 約3万の三角形（胴のまわり 72 分割）・ファンの羽根 22枚・前と主脚の扉・脚の支え・アンテナ・APU の口・ピトー管。翼の先は 787 の反った先・A350 の曲がった先（前から）に加え、**737 のスプリットシミタール（下へ伸びる板）**を足した。寸法は FAA の表のまま（テストで ±4%）
- 細かい形は全部の機体（前は 1.6km 以内だけ）。ただし 3km より遠い地上の機体は、遠くから見つけやすい平らな形のまま（#191 はここも細かい形にしていて、全体の視点で機体が細い線になって消えていた）
- 絵：胴 4096×1024（窓の枠・継ぎ目・貨物扉・扉の取っ手）に、**手で作る汚れ**を足した（扉と窓の後ろへ流れる薄い筋・腹の後ろ半分のくすみ・塗装の細かいむら・腹の細かい板の線）。窓のつや（つるつる）の絵。翼と尾翼の線（スラット・スポイラー・フラップ・補助翼）
- 材質：塗装に上塗りのつや（clearcoat）・エンジンの金属。**昼の映り込みは Poly Haven の「Abandoned Parking」（Sergej Majboroda・CC0）**：トーンマップ済みの JPG（8192×4096）を 1024×512 に縮めて web/3d/env-day.jpg（約86KB）。空・雲・舗装が胴やエンジンに映る。夕方と夜は今までどおり作った空（この絵は昼の景色なので）
- 光と仕上げ（three.js の追加の部品は読まず、アプリの中の小さな仕組み）：やわらかい影を 4096 の細かさ（見ている所の ±1.5km・約0.7m）・**ふちのギザギザ消し（MSAA 4倍）・物の隙間の影（SSAO・半分の細かさ・9km より遠くは弱める）・灯りのにじみ（bloom・夜は強く、昼はごく弱く）**。夜の客室の窓・翼端灯・衝突防止灯の点滅・着陸灯は今ある灯りに、にじみがかかる
- 色：航空会社ごとの尾翼の大まかな色だけ。ロゴ・社名の字は入れていない（決定事項）
- 読み込み：最高の質の昼は、映り込みの絵を読み終わるまで（最大6秒）「3Dを読み込み中…」を出したまま。入口の字は「押すと読み込みます（約0.7MB）」に変えた（前は約0.6MB）

### 映り込みの絵の出典と規約（原文・https://polyhaven.com/license 、11/24 に読んだ）
> All assets (HDRIs, textures and 3D models) on this site are the original work of Poly Haven staff, or artists who willingly and directly donate/sell their work to Poly Haven.
> Our assets are all licensed as CC0, which is effectively Public Domain even in jurisdictions that do not support the Public Domain.
> You can use our assets for any purpose, including commercial work. You do not need to give credit or attribution when using them (although it is appreciated). You can redistribute them, share them around, include them when sharing your own work, or even in a product you sell.

- 元のファイル：https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Tonemapped%20JPG/abandoned_parking.jpg（md5 52a63a5562573c2f49f287c525041923）・作者 Sergej Majboroda
- クレジットは要らないが、コードのコメントとこの報告に書いた（角の出典には足していない）

## 測った数字（ここは画面のないソフトの描画。iPhone の実際の数ではない）
| | 今の本番（main） | この版（質3） |
|---|---|---|
| 届く量：アプリ本体（圧縮） | 485.3KB | 489.6KB（**+4.3KB**） |
| 届く量：3D を開いたとき | 約0.58MB | 約0.67MB（**+86KB**＝映り込みの絵） |
| 開いて「読み込み中」が消えるまで | 0.8〜1.0秒 | 0.9〜1.1秒 |
| 開いて機体が出そろうまで | 2.5〜3.3秒 | 3.6〜4.6秒（細かい形を作る分） |
| 1コマの時間（駐機場・390×844・画素の密度1） | 109ms | 344ms（**約3.2倍**。うち仕上げ 約60ms） |
| 1コマの時間（全体の視点） | 172ms | 522ms |
| 三角形（駐機場） | 42.3万 | 68.1万 |
| GPU のメモリ（機体の絵） | 約21MB | **約202MB** |
| GPU のメモリ（影） | 16MB | 64MB |
| GPU のメモリ（仕上げ） | 0 | 約20MB（画素の密度1）→ iPhone（密度2）で約80MB |

- iPhone 幅の fps の見込み：1コマの比（約3.2倍）から、今の羽田の3D が iPhone で 60fps なら**約19fps**、30fps なら約10fps。その場合、約4秒で自動で質2 に下がり、今の本番に近い重さに戻る（落ちないための仕組みは残した）
- GPU のメモリは合わせて約350MB（iPhone）の見込み。古い iPhone の Safari ではページが読み込み直されるおそれがある
- 数字のファイル：docs/pm/shots-a3-hq/render_info.json（三角形と描く呼び出し）

## 写真（docs/pm/shots-a3-hq/、左が今の本番・右がこの版）
- cmp_all／apron（駐機場）／close・close2（機体の視点）× day／night
- cmpz_<機種>_day／night：寄り（機種ごとに 前・後ろ・少し引いた所）。787・A350・737・777・A321・767
- いちばん分かる差：寄ったときの胴の板の線と汚れ・窓の枠・アンテナ・地面と翼の付け根の影（物の隙間の影）・昼の映り込みのあたたかい色。夜は灯りのにじみ（着陸灯・翼端灯・窓）

## 確かめた結果
- t168（機体の形）：全部成功。足した確かめ：質3・1機種 3万より多い三角形・1.6〜3km も細かい形・3km より遠い地上は平らな形・上塗りの材質・MSAA 4／SSAO／bloom・昼の映り込みの絵・窓のつや・737 の下の板・胴の絵 4096・影 4096・**質2 に下げると仕上げなし・3万以下で作り直す・影 2048**・夜は映り込みの絵を使わずにじみを強める
- t142・t160・t161・t162・t163・t164・t165・t166・t167・t181・tests/ops：成功
- テストの合わせ方：t142・t160 は入口の字「約0.7MB」と届く量（0.65〜0.75MB）・t160 は質を「2 以上」・ファンの羽根の色・t161 は細かい形のときその脚を見る（#191 と同じ）。画面のないソフトの描画は遅く質が勝手に下がるので、t168 の写真と確かめの間は A3_QLOCK で止める（下げる仕組みは a3Quality(2) で別に確かめる）
- t166 は4本を同時に流したとき1回だけ落ち、1本で流すと成功（重さによる待ち時間。前からある）

## src/index.html で変えた関数
- 変えた：openAp3d・a3Build・a3Loop・a3Quality・a3LightMat・a3HdTex・a3HdGeo・a3HdMats・a3HdMesh・a3Loft・a3Sync・a3HdEnv の前
- 足した：A3_MAX（質3 のとき true になる変数）・a3HdNear・a3PostInit・a3PostResize・a3PostPass・a3PostRender・a3PostOff・A3_FSV・a3EnvDay・a3EachHdMat・A3_ENV_DAY・a3HdWingTex（#191 から）
- 変えた定数：A3_SIZE（約0.7MB）

## 本人に決めてほしいこと
1. 本人の iPhone で重さを見てほしい：質3 のまま動くか、すぐ質2 に下がるか（下がると今の本番に近い見た目に戻る）。GPU のメモリ約350MB で Safari が読み込み直さないか
2. 汚れの濃さ：寄ると少しくすんで見える。今のままか、もっと薄くするか
3. 昼の映り込みの絵（Poly Haven・CC0）を使ってよいか。クレジットは要らないが、角の出典に「Poly Haven」を足すか
