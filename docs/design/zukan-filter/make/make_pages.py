# -*- coding: utf-8 -*-
# 00 今（今のアプリの写真）と一覧ページを作る。使い方：python3 capture_now.py ; python3 build.py ; python3 shoot.py <フォルダ> ; python3 make_pages.py
import os, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
CSS = """:root{--bg:#EEF1F5;--card:#fff;--ink:#1F2937;--sub:#6B7280;--shadow:0 10px 24px -16px rgba(15,23,42,.35)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0B0E13;--card:#161A21;--ink:#E5E7EB;--sub:#9CA3AF;--shadow:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;line-height:1.6}
.w{max-width:560px;margin:0 auto;padding:20px 16px 48px}h1{font-size:22px;margin:4px 0 4px}h2{font-size:17px;margin:26px 0 8px}
p,li{font-size:14px}.sub{color:var(--sub);font-size:13px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:14px 16px;margin-top:12px}
.shot{display:block;width:100%;max-width:300px;margin:10px auto 0;border-radius:18px;box-shadow:var(--shadow)}
a.row{display:flex;gap:12px;align-items:center;text-decoration:none;color:inherit}a.row img{width:96px;border-radius:12px;box-shadow:var(--shadow);flex:none}
a.row b{display:block;font-size:15px}a.row small{display:block;font-size:13px;color:var(--sub)}ul{padding-left:20px}"""
def page(fn, title, body):
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body><div class="w">%s</div></body></html>' % (title, CSS, body))
img = lambda f: 'data:image/png;base64,' + base64.b64encode(open(os.path.join(HERE, 'now', f), 'rb').read()).decode()
page('00-now.html', '00 今の図鑑', '<h1>00 今（main の web/ をデモで撮った）</h1><p class="sub">2026年11月19日の main。種類の数は上の黒いカードにあるが、絞り込みはなく、県名はどこにも出ていない。</p>'
     + '<div class="card"><b>飛行場・滑空場・ヘリポートの図鑑</b><img class="shot" src="%s" alt="今の飛行場・滑空場・ヘリポートの図鑑"></div>' % img('now-air.png'))
SC = [('00-now', '00 今', '絞り込みなし・県名なし', 'now'),
      ('F1-all', 'F1 すべて（おすすめの形）', '見方の帯「地方別・地図」の下にピルの溝「すべて・飛行場・滑空場・ヘリポート」と小さな数。どの枠にも名前の下に県名', None),
      ('F1b-all-kanto', 'F1b すべて：関東まで送ったところ', '県名で同じ地方の中の場所が分かる（栃木県・群馬県・埼玉県…）', None),
      ('F2-heli', 'F2 ヘリポートに絞った', '黒いカードは「● ヘリポート 1／12」と地方ごとの数。枠の種類の札は外して県名だけ。中身のない地方のツメは薄く押せない', None),
      ('F3-heli-map', 'F3 ヘリポートに絞った：地図', '同じピルで地図も絞る。行った所は色の丸と名前、まだは灰の輪。黒いカードは数の1行だけ', None),
      ('F4-base-pill', 'F4 案A：「基地」のピルを足す', 'ピルが5つになり横に送る形。「すべて」は今の75のまま（基地は数に入れない）', None),
      ('F5-base-mix', 'F5 案B：基地は「すべて」の中だけ', '「すべて」が102になり、地方の中に基地の枠が混ざる。図鑑の題と数が変わる', None)]
rows = ''.join('<div class="card"><a class="row" href="%s.html"><img src="png/%s.png" alt=""><span><b>%s</b><small>%s</small><small>低い画面（667）：png/%s-667.png</small></span></a></div>' % (f, f if not n else 'F1-all', t, d, f) for f, t, d, n in SC if f != '00-now') 
rows = '<div class="card"><a class="row" href="00-now.html"><img src="png/00-now.png" alt=""><span><b>00 今</b><small>絞り込みなし・県名なし</small></span></a></div>' + rows
page('index.html', '図鑑の絞り込み', '<h1>図鑑の種類の絞り込みと県名</h1><p class="sub">ブランチ design/zukan-filter・画面案だけ（アプリには入れない）。11/20 本人「飛行場、滑空場、ヘリポートのフィルター機能、すべてに何県か表示して」。</p>'
     + '<div class="card"><p><b>決めた形</b></p><ul><li>絞り込みは見方の帯のすぐ下に、ピルの溝の4つ（上の「スタンプラリー｜エアライン経営」と同じ形）。字は種類の名前と小さな数だけ</li><li>絞ると黒いカードの数・地方の数・扉・ツメがその種類だけになる。地図の見方でも同じピルが効く</li><li>県名は名前のすぐ下に 13px の薄いグレー。取っていない所も出す。1つの種類に絞ったときは種類の札を外す</li><li>基地はおすすめは今のまま「基地」の別の図鑑（F1 の形）。足すなら案A（F4）か案B（F5）</li><li>今の図鑑には地図の見方がないので、図鑑と同じ見方の帯「地方別・地図」を足した</li></ul></div>'
     + rows + '<h2>作り方</h2><p class="sub">main の web/ を http.server 8765 で開く → make/capture_now.py → make/build.py（デモに入り inject.js で #bookAir を描き直して HTML に書き出す）→ make/shoot.py &lt;このフォルダ&gt; → make/make_pages.py</p>')
print('ok')
