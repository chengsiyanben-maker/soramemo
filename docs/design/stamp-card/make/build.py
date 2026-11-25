# -*- coding: utf-8 -*-
# 印をもらったときのカードの画面案を組み立てる：src/ の CSS・JS・印の絵・背景を各ページに埋め込み、外部の読み込みなしで開ける HTML にする
import os, json, base64
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = HERE + '/src/'
OUT = os.path.dirname(HERE)
CSS = open(SRC + 'card.css', encoding='utf-8').read()
JS = open(SRC + 'card.js', encoding='utf-8').read()
ST = json.load(open(SRC + 'stamps.json', encoding='utf-8'))      # 今のアプリの stampSVG／insigniaSVG の出力（デモで取り出した）
RW = json.load(open(SRC + 'runways.json', encoding='utf-8'))     # 案A の滑走路の線（向きと本数をおおまかに）
b64 = lambda p: base64.b64encode(open(SRC + p, 'rb').read()).decode()
BG = ':root .bgmap{background-image:url(data:image/jpeg;base64,%s)}:root[data-night=on] .bgmap{background-image:url(data:image/jpeg;base64,%s)}' % (b64('bg-day.jpg'), b64('bg-night.jpg'))

IC = {
 'x': '<path d="M6 6l12 12M18 6L6 18"/>',
 'clock': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 'plane': '<path d="M12 3c.8 0 1.3.7 1.3 1.5V9.5l7.2 4.3v1.9l-7.2-2.2v4.6l2 1.5V21L12 20.1 8.7 21v-1.4l2-1.5v-4.6l-7.2 2.2v-1.9l7.2-4.3V4.5C10.7 3.7 11.2 3 12 3z"/>',
 'share': '<path d="M12 15V4M8 8l4-4 4 4"/><path d="M5 12v6.5A1.5 1.5 0 006.5 20h11a1.5 1.5 0 001.5-1.5V12"/>',
 'cam': '<path d="M4 8.5A1.5 1.5 0 015.5 7H8l1.5-2h5L16 7h2.5A1.5 1.5 0 0120 8.5v9a1.5 1.5 0 01-1.5 1.5h-13A1.5 1.5 0 014 17.5z"/><circle cx="12" cy="13" r="3.5"/>',
 'up': '<path d="M12 19V6M6.5 11.5L12 6l5.5 5.5"/>',
 'back': '<path d="M15 5l-7 7 7 7"/>',
 'dl': '<path d="M12 4v11M8 11l4 4 4-4"/><path d="M5 19h14"/>',
 'retry': '<path d="M4 12a8 8 0 0113.7-5.6L20 8.5M20 4v4.5h-4.5M20 12a8 8 0 01-13.7 5.6L4 15.5M4 20v-4.5h4.5"/>',
 'star': '<path d="M12 4l2.4 5 5.4.6-4 3.7 1.1 5.4L12 16l-4.9 2.7 1.1-5.4-4-3.7 5.4-.6z"/>',
}
ic = lambda k, c='ic': '<svg class="%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (c, IC[k])

def page(name, title, body, css='', js='', bg=True):
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s\n%s</style></head><body>%s<script>%s\n%s</script></body></html>') % (title, CSS, BG if bg else '', css, body, JS, js)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html)
    print('書いた', name)

def roll(a, b):
    return '<span class="roll num"><span class="col"><span>%s</span><span>%s</span></span></span>' % (a, b)

def rwy_svg(code, lines):
    ls = ''.join('<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-dasharray:%d;--len:%d"/>' % (x1, y1, x2, y2, L, L)
                 for x1, y1, x2, y2 in lines for L in [int(((x2-x1)**2 + (y2-y1)**2) ** .5) + 2])
    return '<svg class="rwy" viewBox="0 0 160 160" role="img" aria-label="%sの印（滑走路の向きと本数）">%s<text x="80" y="146" text-anchor="middle">%s</text></svg>' % (code, ls, code)

def card(st, date, mark, name, pref, mx, goal='', note='', more='', acts=None, hint=''):
    if acts is None:
        acts = ('<button class="pill main" type="button">%s今日の便を記録する</button>'
                '<div class="row2"><button class="pill" type="button">%s画像で共有</button><button class="pill" type="button">%s写真に押す</button></div>') % (ic('plane'), ic('share'), ic('cam'))
    return ('<div class="phone"><div class="bgmap" aria-hidden="true"></div><div class="scrim"></div>'
            '<div class="scw"><section class="sc" role="dialog" aria-modal="true" aria-labelledby="scName">'
            '<div class="grab" aria-hidden="true"></div>'
            '<div class="top">%s<time>%s</time><button class="x" type="button" aria-label="閉じる">%s</button></div>'
            '%s<h2 class="name" id="scName">%s</h2><p class="pref">%s</p>%s'
            '<div class="mx">%s</div>%s%s'
            '<div class="acts">%s%s</div>'
            '</section></div><button class="replay" type="button">%sもう一度（見本の操作）</button></div>') % (
            st, date, ic('x'), mark, name, pref, note, mx, goal, more, ('<p class="hint">%s</p>' % hint) if hint else '', acts, ic('retry'))

def mxcell(k, v):
    return '<div><span class="k">%s</span><div class="v">%s</div></div>' % (k, v)

def goal(rg, a, b, n, text):
    return ('<div class="goal"><div class="gl"><b>%s</b><span class="gv"><span class="num">%s</span><span class="u">/%s</span></span></div>'
            '<div class="bar"><i style="width:%.1f%%;--from:%.1f%%"></i></div><p>%s</p></div>') % (rg, b, n, b / n * 100, a / n * 100, text)

def stamp(svg, tier=False, extra='', cls=''):
    return '<div class="mark%s%s">%s<div class="stamp">%s</div><div class="ring"></div></div>' % (' tier' if tier else '', (' ' + cls) if cls else '', extra, svg)

DATE = '2026.11.25'
P = lambda t, c='first': '<span class="st %s">%s</span>' % (c, t)
COLLECT = lambda a, b: mxcell('集めた空港', roll(a, b) + '<span class="u">/86</span><span class="plus">＋1</span>')
VISIT = lambda a, b=None: mxcell('訪問', (roll(a, b) if b else '<span class="num">%s</span>' % a) + '<span class="u">回目</span>')

# ── 案B（おすすめ）：今のハンコを活かす ──
page('b1-first.html', 'B1 はじめての印（案B）', card(P('はじめての印'), DATE, stamp(ST['HND0']), '東京国際空港（羽田）', '東京都',
     VISIT('1') + COLLECT(16, 17), goal('関東', 2, 3, 9, 'あと6空港で関東がそろいます')))
memo = '<div class="memo"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="50"/><text x="60" y="70" text-anchor="middle" font-size="28">IZO</text></svg></div>'
page('b2-memo.html', 'B2 メモから印へ（案B）', card(P('現地の印になりました'), DATE, stamp(ST['IZO0'], extra=memo, cls='memo-on'), '出雲空港', '島根県',
     COLLECT(17, 18) + mxcell('メモの空港', roll(23, 22) + '<span class="u">空港</span>'),
     goal('中国', 1, 2, 9, 'あと7空港で中国がそろいます'),
     note='<p class="note">メモの空港が、<b>現地で押した印</b>に変わりました</p>'))
page('b3-repeat.html', 'B3 2回目以降（案B）', card(P('チェックイン', 'calm'), DATE, stamp(ST['ITM2'], tier=True), '大阪国際空港（伊丹）', '大阪府',
     VISIT(11, 12) + mxcell('前回から', '<span class="num">38</span><span class="u">日ぶり</span>'),
     goal('近畿', 4, 4, 5, 'あと1空港：南紀白浜'), hint='羽田 → 伊丹 514km の移動を記録しました'))
more = ('<div class="more"><div>%s<span><b>階級が上がりました：セカンドオフィサー</b>次の副操縦士まで あと15回</span></div></div>' % ic('up'))
for fn, pill, ttl in (('b4a-mark-on.html', P('5回目の訪問', 'ms'), 'B4a 節目の縁取りあり'), ('b4b-mark-off.html', P('チェックイン', 'calm'), 'B4b 節目の縁取りなし')):
    page(fn, ttl, card(pill, DATE, stamp(ST['HND2'], tier=True), '東京国際空港（羽田）', '東京都',
         VISIT(4, 5) + mxcell('前回から', '<span class="num">9</span><span class="u">日ぶり</span>'), more=more))
page('b5-offline.html', 'B5 電波がないとき（案B）', card('<span class="st wait">%s送信待ち</span>' % ic('clock'), DATE, stamp(ST['KMQ0'], cls='pale'), '小松空港', '石川県',
     mxcell('押した時刻', '<span class="num">14:22</span>') + mxcell('いまの状態', '<span class="num sm">端末に保存</span>'),
     note='<p class="note"><b>電波が戻ったら確定します。</b><br>確定するまで、集めた空港の数には入れません</p>',
     acts='<button class="pill main" type="button">閉じる</button>', hint='今日の便は、電波が戻ってから記録できます'))

# ── 案A（Gemini の案どおり）：コード＋滑走路の線 ──
page('a1-first.html', 'A1 はじめての印（案A）', card(P('はじめての印'), DATE, '<div class="mark">%s</div>' % rwy_svg('HND', RW['HND']), '東京国際空港（羽田）', '東京都',
     VISIT('1') + COLLECT(16, 17), goal('関東', 2, 3, 9, 'あと6空港で関東がそろいます')))
page('a3-repeat.html', 'A3 2回目以降（案A）', card(P('チェックイン', 'calm'), DATE, '<div class="mark">%s</div>' % rwy_svg('ITM', RW['ITM']), '大阪国際空港（伊丹）', '大阪府',
     VISIT(11, 12) + mxcell('前回から', '<span class="num">38</span><span class="u">日ぶり</span>'),
     goal('近畿', 4, 4, 5, 'あと1空港：南紀白浜'), hint='羽田 → 伊丹 514km の移動を記録しました'))

# ── 共有画像（4:5）──
SH_CSS = r'''
.phone.share{background:var(--bg);padding:0 16px}
.shtop{display:flex;align-items:center;gap:8px;height:64px}
.shtop .back{display:inline-flex;align-items:center;gap:4px;min-height:44px;padding:0 16px 0 10px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:700;color:var(--strong)}
.shtop h1{font-size:17px;font-weight:800;color:var(--strong);margin-left:6px}
.img45{position:relative;width:100%;aspect-ratio:4/5;border-radius:20px;background:#ECEEF1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:18px 26px 14px;box-shadow:var(--shadow)}
.img45 .c{width:100%;background:#fff;border-radius:22px;padding:14px 16px 16px;box-shadow:0 10px 30px -10px rgba(17,24,39,.18);color:#374151}
.img45 .c .t{display:flex;align-items:center;justify-content:space-between}
.img45 .c .st.first{background:#1F2937;color:#fff;box-shadow:none;height:26px;font-size:12px}
.img45 .c time{font-size:12px;color:#6B7280;font-weight:600}
.img45 .c .s{width:118px;height:118px;margin:6px auto 0}
.img45 .c .s svg{width:100%;height:100%}
.img45{--shu:#111111}
.img45 .c .n{text-align:center;font-size:17px;font-weight:800;color:#1F2937;margin-top:4px}
.img45 .c .p{text-align:center;font-size:12px;color:#6B7280;font-weight:600}
.img45 .c .m{display:grid;grid-template-columns:1fr 1fr;margin-top:10px;text-align:center}
.img45 .c .m span{display:block;font-size:12px;color:#646B78;font-weight:700}
.img45 .c .m b{font-size:26px;font-weight:800;color:#1F2937;font-variant-numeric:tabular-nums}
.img45 .c .m small{font-size:12px;color:#6B7280;font-weight:600;margin-left:2px}
.img45 .c .g{margin-top:10px;padding:8px 12px;border-radius:14px;background:#F4F5F7;font-size:12px;color:#646B78;font-weight:600;text-align:center}
.img45 .c .g b{color:#1F2937}
.img45 .foot{margin-top:10px;font-size:12px;font-weight:800;color:#646B78;letter-spacing:.08em}
.shacts{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
.shnote{margin-top:14px;padding:12px 16px;border-radius:18px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--sub);line-height:1.7}
.shnote b{color:var(--strong)}
'''
share = ('<div class="phone share"><div class="shtop"><button class="back" type="button">%s戻る</button><h1>画像で保存・共有</h1></div>'
         '<div class="img45" role="img" aria-label="共有する画像の見本"><div class="c"><div class="t"><span class="st first">はじめての印</span><time>2026.11.25</time></div>'
         '<div class="s">%s</div><div class="n">東京国際空港（羽田）</div><div class="p">東京都</div>'
         '<div class="m"><div><span>訪問</span><b>1</b><small>回目</small></div><div><span>集めた空港</span><b>17</b><small>/86</small></div></div>'
         '<div class="g"><b>関東 3/9</b>・あと6空港</div></div><div class="foot">そらメモ</div></div>'
         '<div class="shacts"><button class="pill" type="button">%s画像を保存</button><button class="pill main" type="button">%s共有…</button></div>'
         '<p class="shnote"><b>画像に入るもの</b>：印・空港名・日付・訪問の回数・集めた空港の数・小目標・「そらメモ」の字<br><b>入れないもの</b>：いる場所の地図や緯度経度・時刻・座席・便名・表示名</p></div>') % (
         ic('back'), ST['HND0'], ic('dl'), ic('share'))
page('b6-share.html', 'B6 共有画像', share, css=SH_CSS, bg=False)

# ── 一覧ページ ──
IDX_CSS = r'''
body{max-width:820px;margin:0 auto;padding:0 16px 80px;line-height:1.6;font-size:15px}
.hd{padding:28px 0 8px}
h1{font-size:22px;font-weight:800;color:var(--strong)}
.lead{font-size:13px;color:var(--sub);margin-top:6px}
.ctl{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 0;background:var(--bg)}
.seg{display:inline-flex;padding:4px;border-radius:999px;background:var(--pill)}
.seg button{min-height:44px;min-width:60px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.seg button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.sec{margin-top:28px}
.sec > h2{font-size:18px;font-weight:800;color:var(--strong)}
.sec > p{font-size:13px;color:var(--sub);margin-top:4px}
.rec{display:inline-block;margin-left:8px;padding:2px 10px;border-radius:999px;background:var(--strong);color:#fff;font-size:12px;font-weight:800;vertical-align:3px}
:root[data-night=on] .rec{background:transparent;color:#4ADE80;box-shadow:inset 0 0 0 1.5px #4ADE80}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-top:12px}
.sh{background:var(--card);border-radius:20px;box-shadow:var(--shadow);padding:10px 10px 12px}
.sh .fr{position:relative;width:100%;aspect-ratio:390/844;border-radius:14px;overflow:hidden;background:var(--bg)}
.sh iframe,.sh img{position:absolute;left:0;top:0;width:390px;height:844px;border:0;transform-origin:0 0}
.sh img{width:100%;height:100%;transform:none}
.sh h3{font-size:14px;font-weight:800;color:var(--strong);margin-top:8px}
.sh p{font-size:12px;color:var(--sub);line-height:1.6}
.sh .row{display:flex;gap:6px;margin-top:6px}
.sh .pill{min-height:44px;font-size:13px;padding:0 12px;flex:1}
.sh .pill svg{width:16px;height:16px}
.box{margin-top:12px;padding:14px 18px;background:var(--card);border-radius:20px;box-shadow:var(--shadow);font-size:14px}
.box li{margin:4px 0 4px 18px}
.box li small{display:block;font-size:12px;color:var(--mute)}
table.tl{width:100%;border-collapse:collapse;font-size:13px}
table.tl th{font-size:12px;color:var(--mute);font-weight:700;text-align:left;padding:6px 8px}
table.tl td{padding:8px;vertical-align:top}
table.tl tr:nth-child(even) td{background:var(--panel)}
table.tl td:first-child{white-space:nowrap;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;border-radius:10px 0 0 10px}
table.tl td:last-child{border-radius:0 10px 10px 0;color:var(--sub)}
'''
def shot(file, title, desc, live=True):
    fr = ('<iframe src="%s" data-src="%s" title="%s" loading="lazy" tabindex="-1"></iframe>' % (file, file, title)) if live else ('<img src="%s" alt="%s">' % (file, title))
    row = ('<div class="row"><button class="pill" type="button" data-again>%sもう一度</button><a class="pill" href="%s" target="_blank">開く</a></div>' % (ic('retry'), file)) if live else ''
    return '<div class="sh"><div class="fr">%s</div><h3>%s</h3><p>%s</p>%s</div>' % (fr, title, desc, row)

idx = ('<div class="hd"><h1>印をもらったときのカード 1版</h1><p class="lead">本人が貼った Gemini の案（docs/pm/ext/gemini-stamp-1125.txt）をもとにした画面案です。アプリにはまだ入れません。押すと動き、「もう一度」で最初から。</p></div>'
       '<div class="ctl"><div class="seg" role="group" aria-label="昼と夜"><button type="button" data-n="0" aria-pressed="true">昼</button><button type="button" data-n="1" aria-pressed="false">夜</button></div>'
       '<div class="seg" role="group" aria-label="動き"><button type="button" data-rm="0" aria-pressed="true">動きあり</button><button type="button" data-rm="1" aria-pressed="false">動きを減らす</button></div></div>'
       '<section class="sec"><h2>今の画面</h2><p>半券の上にハンコが押され、階級の羽根と帯、名前、ボタン3つ。ダイアログが画面の真ん中に出ます。</p><div class="grid">%s</div></section>'
       '<section class="sec"><h2>案B　今のハンコを活かす<span class="rec">おすすめ</span></h2><p>地図を薄く残したまま、下から角丸カード。印の場所には今のハンコ（押される動き press と墨の輪 ring もそのまま）。図鑑・共有画像・写真に押すと同じ印のままです。半券は、カードの左右の切り欠きで残します。</p><div class="grid">%s</div></section>'
       '<section class="sec"><h2>5・10・20回目の縁取り　あり／なし</h2><p>今のアプリには「階級」（3・5・20・100・365回で羽根と帯が増える）がすでにあります。縁取りを足すと、節目の見せ方が2つになります。おすすめは「なし」（階級だけ）。</p><div class="grid">%s</div></section>'
       '<section class="sec"><h2>案A　Gemini の案どおり（コード＋滑走路の線）</h2><p>印を新しく「3文字のコード＋滑走路の向きと本数」の絵にします。空港ごとの滑走路の形を86空港ぶん描く必要があり、図鑑や共有画像の印とも見た目が分かれます。</p><div class="grid">%s</div></section>'
       '<section class="sec"><h2>共有画像</h2><div class="grid">%s</div></section>'
       '<section class="sec"><h2>動きの時間割（約1.2秒・いつでも閉じられる）</h2><div class="box"><table class="tl"><tr><th>時刻</th><th>動き</th><th>そろえたもの</th></tr>'
       '<tr><td>0.00</td><td>地図が薄く暗くなり、カードが下から上がる（行き過ぎない）</td><td>micro の 13 シート 0.3秒</td></tr>'
       '<tr><td>0.20</td><td>ハンコが押される（案A は線が引かれ、コードが落ち着く）</td><td>今の press 0.5秒</td></tr>'
       '<tr><td>0.48</td><td>墨の輪が1回広がって消える</td><td>今の ring 0.7秒</td></tr>'
       '<tr><td>0.70</td><td>数字が1つ繰り上がり「＋1」、小目標の帯が伸びる</td><td>micro の 07・08（0.35〜0.4秒）</td></tr>'
       '<tr><td>0.90</td><td>ボタンが静かに出る</td><td>0.25秒</td></tr>'
       '<tr><td>いつでも</td><td>✕・カードの外・下へなでるで閉じる（0.15秒）</td><td>動きを減らす設定では、最後の形がすぐ出る</td></tr></table></div></section>'
       '<section class="sec"><h2>入れないもの</h2><div class="box"><ul>'
       '<li>天気・季節の飾り、ロゴ、案内板風の黒い背景、紙吹雪</li><li>地図のピンの波紋（micro で入れないと決めた「波紋」に当たる）</li>'
       '<li>地方ごとの色分け（Gemini の案）<small>色は1色（昼は紺、夜は緑）。会社の色と金は使わない</small></li>'
       '<li>振動<small>決定事項【11/25】で「振動と音はなし」。今のアプリには印のときの軽い振動（navigator.vibrate）が残っているので、どうするか本人に聞く</small></li></ul></div></section>') % (
       shot('png/00-now.png', '今', '今の印の画面（デモの羽田）', live=False),
       shot('b1-first.html', 'B1 はじめての印', '訪問1回目・集めた空港 16→17／86・関東 3/9') + shot('b2-memo.html', 'B2 メモから印へ', '点線のメモが消えて現地の印に。メモの数は1つ減る') +
       shot('b3-repeat.html', 'B3 2回目以降', '12回目・前回から38日ぶり。階級の羽根はそのまま') + shot('b5-offline.html', 'B5 電波がないとき', '淡い印・送信待ち。確定まで数に入れない'),
       shot('b4a-mark-on.html', 'B4a 縁取りあり', '上の札を「5回目の訪問」にして細い縁') + shot('b4b-mark-off.html', 'B4b 縁取りなし', '札はふつう。階級が上がった行だけ'),
       shot('a1-first.html', 'A1 はじめての印', '羽田は4本の滑走路') + shot('a3-repeat.html', 'A3 2回目以降', '伊丹は平行の2本'),
       shot('b6-share.html', 'B6 画像で保存・共有', '4:5。位置・時刻・座席・便名は入れない'))
IDX_JS = r'''
(function(){
  let N = '0', RM = '0';
  const fit = () => document.querySelectorAll('.sh iframe').forEach(f => { f.style.transform = 'scale(' + (f.parentNode.clientWidth / 390) + ')'; });
  const src = f => f.dataset.src + '?n=' + N + '&rm=' + RM;
  const reload = () => document.querySelectorAll('.sh iframe').forEach(f => { f.src = src(f) + '&r=' + Date.now(); });
  addEventListener('resize', fit); fit();
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-again]'); if(a){ const f = a.closest('.sh').querySelector('iframe'); f.src = src(f) + '&r=' + Date.now(); return; }
    const n = e.target.closest('[data-n]'), m = e.target.closest('[data-rm]');
    if(n){ N = n.dataset.n; document.documentElement.dataset.night = N === '1' ? 'on' : ''; document.querySelectorAll('[data-n]').forEach(b => b.setAttribute('aria-pressed', String(b === n))); reload(); }
    if(m){ RM = m.dataset.rm; document.querySelectorAll('[data-rm]').forEach(b => b.setAttribute('aria-pressed', String(b === m))); reload(); }
  });
  const q = new URLSearchParams(location.search); if(q.get('n') === '1'){ N = '1'; document.documentElement.dataset.night = 'on'; document.querySelectorAll('[data-n]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.n === '1'))); reload(); }
})();
'''
page('index.html', '印のカード 一覧', idx, css=IDX_CSS, js=IDX_JS, bg=False)
