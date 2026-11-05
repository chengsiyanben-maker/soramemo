# そらメモ　アーリーアクセスの告知（Instagram）

Instagram（ryou_ma767）で、アーリーアクセスの登録を増やすための材料です。目標は登録500人ほど。
有料の広告や予約投稿の道具は使わず、投稿は本人が手で行います。

| ファイル | 中身 |
|---|---|
| [plan-4weeks.md](plan-4weeks.md) | 11月9日の週から4週分の投稿予定（曜日・時間の目安・種類・ねらい） |
| [posts-first3.md](posts-first3.md) | 最初の3投稿の文面（ハッシュタグ込み）と画像の説明 |
| [metrics.md](metrics.md) | 週ごとに見る数字と、その見方・記録表 |
| [rules.md](rules.md) | 投稿の前に見る決まり（書かないこと・使わないもの） |
| `images/*.html` | 画像案（外部の読み込みなし。ファイルを開けば見られる） |
| `images/png/` | 画像案を書き出した PNG（フィード1080×1350、ストーリーズ1080×1920） |

## 画像の一覧

| 投稿 | HTML | PNG |
|---|---|---|
| 1 そらメモの紹介（カルーセル5枚） | `images/post1-soramemo-intro.html` | `images/png/post1-1.png`〜`post1-5.png` |
| 2 ストーリーズ（1枚） | `images/post2-story.html` | `images/png/post2-story.png` |
| 3 エアライン経営（カルーセル5枚） | `images/post3-airline.html` | `images/png/post3-1.png`〜`post3-5.png` |

- 画面は、今のアプリ（main の `src/index.html`）の見た目を HTML で再現した見本です。画面写真ではありません
- 数字・会社名・登録記号は見本です（登録記号は `JA＊＊＊＊` と伏せています）
- 色と形は今のアプリと新規登録の画面案（`docs/design/signup`）に合わせました。航空会社のロゴ・色・機体のデザインは使っていません
- PNG を作り直すときは、HTML をブラウザで開き、各枚（360×450、ストーリーズは360×640）を3倍で書き出します
