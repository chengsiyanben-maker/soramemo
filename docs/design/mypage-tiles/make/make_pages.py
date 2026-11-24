# -*- coding: utf-8 -*-
# 00 今（今のアプリの写真）と一覧ページを作る。使い方は build.py の頭を見る
import os, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
CSS = """:root{--bg:#EEF1F5;--card:#fff;--ink:#1F2937;--sub:#5F6672;--shadow:0 10px 24px -16px rgba(15,23,42,.35)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0B0E13;--card:#161A21;--ink:#E5E7EB;--sub:#9CA3AF;--shadow:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;line-height:1.6}
.w{max-width:560px;margin:0 auto;padding:20px 16px 48px}h1{font-size:22px;margin:4px 0}h2{font-size:17px;margin:26px 0 8px}
p,li{font-size:14px}.sub{color:var(--sub);font-size:13px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:14px 16px;margin-top:12px}
.shot{display:block;width:100%;max-width:320px;margin:10px auto 0;border-radius:18px;box-shadow:var(--shadow)}
a.row{display:flex;gap:12px;align-items:center;text-decoration:none;color:inherit}a.row img{width:96px;border-radius:12px;box-shadow:var(--shadow);flex:none}
a.row b{display:block;font-size:15px}a.row small{display:block;font-size:13px;color:var(--sub)}ul{padding-left:20px}"""
def page(fn, title, body):
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body><div class="w">%s</div></body></html>' % (title, CSS, body))
img = lambda f: 'data:image/png;base64,' + base64.b64encode(open(os.path.join(HERE, 'now', f), 'rb').read()).decode()
page('00-now.html', '00 今のマイページ', '<h1>00 今（main の web/ をデモで撮った）</h1><p class="sub">2026年11月24日の main。タイルの形は「成績」1枚だけで「表示の編集」の中に半分の幅。頭の札は「16空港・31フライト」で車などが入っている。「知らせ／知らせ」と見出しが重なる。</p>'
     + '<div class="card"><img class="shot" src="%s" alt="今のマイページの全体"></div>' % img('now-full.png'))
SC = [('00-now', '00 今', 'タイルは成績1枚だけ・設定の行が縦に並ぶ'),
      ('A1-tiles6', 'A1 案A：6枚のタイル＋設定はカードで並べる', '頭の下に2列×3（成績・図鑑・フライト・修行・運用・知らせ）。下に「表示の編集」（3つの小さいタイル）・「データとバックアップ」・表示と色・詳しい設定のカード。今の行は畳まずに並べる'),
      ('B1-wide', 'B1 案B：成績を横長に＋設定は1枚の目次', '成績は横長の1枚に3つの数（空港・便・距離）と車などの1行。修行と知らせの2枚。タブにある画面はタイルにせず、外した画面だけ増える。設定は5行の目次で、押すと1枚のページ'),
      ('B2-data', 'B2 案B：目次から開いた「データとバックアップ」', 'バックアップの説明を先頭の箱に。書き出しは「手元の控え」')]
rows = ''.join('<div class="card"><a class="row" href="%s.html"><img src="png/%s.png" alt=""><span><b>%s</b><small>%s</small><small>低い画面（375×667）：png/%s-667.png・全体：png/%s-full.png</small></span></a></div>' % (f, f, t, d, f, f) for f, t, d in SC)
page('index.html', 'マイページのタイル', '<h1>マイページを「タイル」に</h1><p class="sub">ブランチ design/mypage-tiles・画面案だけ（アプリには入れない）。PM の指示 11/24 14時30分（アプリ全体の見直し A の4番）。390×844 と 375×667 で撮った。</p>'
     + '<div class="card"><p><b>両方の案で同じこと</b></p><ul><li>数字は車などを外して数える（デモで 30便・24,017km。見直し A の1番とそろえる）。頭の札から「○空港・○フライト」を外し、数はタイルへ</li><li>タイルは白い角丸カード＋薄い影。名前は小さい灰、数字は大きく太く、単位は小さい灰。右上に ›</li><li>「知らせ」はタイルの名前だけにし、見出しと重ねない</li><li>見出し「データ」を「データとバックアップ」にし、先頭に「記録はサーバーに保存・機種を変えても戻る・無料」の箱（文は PM が決める）</li><li>補足の字の色は 4.5:1 以上（今の 2.5:1 の薄いグレーをやめる）。押す所はすべて 44 以上（JAL・ANA の切り替えと色の丸も）</li><li>エアライン経営の行は非表示中なので出していない</li></ul></div>'
     + rows + '<h2>作り方</h2><p class="sub">main の web/ を http.server 8765 で開く → make/capture_now.py → make/build.py（デモでマイページを開き inject.js で描き直して HTML に書き出す）→ make/shoot.py → make/make_pages.py</p>')
print('ok')
