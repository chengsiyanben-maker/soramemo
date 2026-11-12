# そらメモ　アーリーアクセスの告知（Instagram）

Instagram（ryou_ma767）で、アーリーアクセスの登録を増やすための材料です。目標は登録500人ほど。
有料の広告や予約投稿の道具は使わず、投稿は本人が手で行います。

| ファイル | 中身 |
|---|---|
| [plan-4weeks.md](plan-4weeks.md) | 4週分の投稿予定。11/12 に金・土・日へ組み直し（11/13〜12/6）。日付はここが正 |
| [reach.md](reach.md) | コラボ投稿の声かけ（探し方・DM の文・中身の形）と、X・Threads・YouTube ショートに出すときの違い・アカウントの案 |
| [reels.md](reels.md) | リールの台本（週1本：修行・チェックイン・経営・図鑑・予備の近くの空港）と撮り方 |
| [shoot-guide.md](shoot-guide.md) | 本番（soramemo.jp）のデモで画面を撮る手順（本人用） |
| [posts-shugyo.md](posts-shugyo.md) | 修行の広報（カルーセル6枚・ストーリーズ） |
| [posts-first3.md](posts-first3.md) | 最初の3投稿の文面（ハッシュタグ込み）と画像の説明 |
| [posts-week2.md](posts-week2.md) | 2週目の3投稿（リール①の台本・ストーリーズ・フライトの残し方） |
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
| 4 リール①の表紙 | `images/post4-reel1-cover.html` | `images/png/post4-reel1-cover.png` |
| 5 ストーリーズ（答えの紹介） | `images/post5-story.html` | `images/png/post5-story.png` |
| 6 フライトの残し方（カルーセル5枚） | `images/post6-flight.html` | `images/png/post6-1.png`〜`post6-5.png` |

- 画面は、今のアプリ（main の `src/index.html`）の見た目を HTML で再現した見本です。画面写真ではありません
- 数字・会社名・登録記号は見本です（登録記号は `JA＊＊＊＊` と伏せています）
- 色と形は今のアプリと新規登録の画面案（`docs/design/signup`）に合わせました。航空会社のロゴ・色・機体のデザインは使っていません
- PNG を作り直すときは、HTML をブラウザで開き、各枚（360×450、ストーリーズは360×640）を3倍で書き出します
