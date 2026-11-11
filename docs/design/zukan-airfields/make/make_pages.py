# -*- coding: utf-8 -*-
# 01 今（今のアプリの写真3枚）と一覧ページを作る。使い方：python3 make_pages.py（build.py と shoot.py のあと）
import os, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
CSS = """:root{--bg:#EEF1F5;--card:#fff;--ink:#1F2937;--sub:#6B7280;--shadow:0 10px 24px -16px rgba(15,23,42,.35);--fd:#3E7D52;--gl:#1F7FB6}
@media (prefers-color-scheme: dark){:root{--bg:#0B0E13;--card:#161A21;--ink:#E5E7EB;--sub:#9CA3AF;--shadow:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;line-height:1.6}
.w{max-width:560px;margin:0 auto;padding:20px 16px 48px}h1{font-size:22px;margin:4px 0 4px}h2{font-size:17px;margin:26px 0 8px}
p,li{font-size:14px;color:var(--ink)}.sub{color:var(--sub);font-size:13px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:14px 16px;margin-top:12px}
.shot{display:block;width:100%;max-width:300px;margin:10px auto 0;border-radius:18px;box-shadow:var(--shadow)}
.card b.n{display:inline-flex;align-items:center;justify-content:center;min-width:26px;height:26px;border-radius:999px;background:#16233A;color:#fff;font-size:13px;margin-right:6px}
a.row{display:flex;gap:12px;align-items:center;text-decoration:none;color:inherit}a.row img{width:96px;border-radius:12px;box-shadow:var(--shadow);flex:none}
a.row b{display:block;font-size:15px}a.row small{display:block;font-size:13px;color:var(--sub)}
ul{padding-left:20px}"""
def page(fn, title, body):
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body><div class="w">%s</div></body></html>' % (title, CSS, body))
img = lambda f: 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(HERE, 'now', f), 'rb').read()).decode()
NOW = [('now-main-844.jpg', '図鑑の最初の画面', '上の黒いカードは「集めた空港 16／86」。飛行場・滑空場への道は、右上の「ほかの図鑑・実績」のピルだけで、目に入りにくい。'),
       ('now-others-844.jpg', 'ほかの図鑑・実績', '4つの図鑑が同じ大きさで並ぶ。飛行場・滑空場は2つ目で、0／63 の数だけ。'),
       ('now-air-844.jpg', '飛行場・滑空場（今の別冊）', '「滑空場 0／33」「飛行場 0／30」の畳んだ行が2つだけ。開くと印の丸が並ぶ。地方で分かれず、86空港の図鑑と形が違う。')]
page('01-now.html', '01 今の図鑑', '<h1>01 今（main の web/ をデモで撮った）</h1><p class="sub">2026年11月11日の main。デモの記録（集めた空港 16、飛行場・滑空場 0）。</p>'
     + ''.join('<div class="card"><b class="n">%d</b><b>%s</b><p>%s</p><img class="shot" src="%s" alt="%s"></div>' % (i + 1, t, d, img(f), t) for i, (f, t, d) in enumerate(NOW)))
SC = [('01-now', '01 今', '今の図鑑の3つの画面'), ('02-entry', '02 図鑑の最初の画面に入口', '黒いカードの下に「もう1つの図鑑」の白いカード（3／63・飛行場と滑空場の数・小さな地図）'),
      ('02b-entry-zero', '02b まだ1つもないとき', '0／63 でも同じ大きさで出す'), ('03-airfield-book', '03 飛行場・滑空場の図鑑', 'ツメ＋地方の扉＋そろえた枠。枠に種類の札（飛行場／滑空場）'),
      ('03b-airfield-kanto', '03b 関東の扉まで送ったところ', '扉が上に止まり、ツメの関東が出る。行った枠は白、まだは薄い'),
      ('04-entry-night', '04 夜：入口', '夜は種類の色をやめ、点と札は灰の濃淡だけ'), ('04b-airfield-book-night', '04b 夜：飛行場・滑空場の図鑑', 'ツメは色なし（今の夜の図鑑と同じ）')]
SC = [x for x in SC if x[0] == '01-now'] + [('02-entry-v2', '02 2版：入口', '「もう1つの図鑑」は緑のピル、数字は28pxにして「集めた空港とは別に数えます」をすぐ横に。667 は1行の形'),
      ('02b-entry-zero-v2', '02b 2版：まだ1つもないとき', '0／63 でも同じ形'), ('03-airfield-book-v2', '03 2版：飛行場・滑空場の図鑑', '説明に「番外編」の語を使わない。扉に「飛行場・滑空場」の札'),
      ('03b-airfield-kanto-v2', '03b 2版：関東まで送ったところ', '上に止まる扉に「飛行場・滑空場」の札が残る。カタカナは語の切れ目で折る'),
      ('04-entry-night-v2', '04 2版：夜の入口', '灰の濃淡だけ'), ('04b-airfield-book-night-v2', '04b 2版：夜の図鑑', 'ツメも札も色なし')] + [(f, t.replace(' ', ' 1版：', 1), d) for f, t, d in SC if f != '01-now']
rows = ''.join('<div class="card"><a class="row" href="%s.html"><img src="png/%s.png" alt=""><span><b>%s</b><small>%s</small><small>低い画面（667）：<span>png/%s-667.png</span></small></span></a></div>' % (f, f if f != '01-now' else '02-entry', t, d, f) for f, t, d in SC)
page('index.html', '図鑑の飛行場・滑空場', '<h1>図鑑の飛行場・滑空場の入口</h1><p class="sub">ブランチ design/zukan-airfields・画面案だけ（アプリには入れない）。11/11 本人「今のまま別の図鑑で目立たせる」。</p>'
     + '<div class="card"><p><b>決めた形</b></p><ul><li>図鑑の最初の画面：上の黒いカード（16／86）のすぐ下に、白いカード「もう1つの図鑑　飛行場・滑空場」。数（3／63）・飛行場と滑空場の数・小さな地図・「上の『集めた空港』とは別に数えます」</li><li>押した先：86空港の図鑑と同じ「ツメ＋地方の扉＋そろえた枠」。枠は名前（「滑空場」「飛行場」「空港」を外した短い名前）と種類の札</li><li>四国は飛行場・滑空場がないので、ツメは薄く押せない、上のカードは「なし」</li><li>自衛隊の飛行場（番外編）は今のまま「ほかの図鑑・実績」の中</li><li>「ほかの図鑑・実績」のピルと、その中の飛行場・滑空場の行は今のまま残す</li></ul></div>'
     + rows + '<h2>作り方</h2><p class="sub">main の web/ を http.server 8765 で開く → make/build.py（デモに入り、inject.js で図鑑の上に描き足して HTML に書き出す）→ make/shoot.py &lt;このフォルダ&gt; → make/make_pages.py。夜は今のアプリにまだ夜の画面がないので、暗い配色に夜の決まり（琥珀は使わず白い字）を足して近づけた。</p>')
print('ok')
