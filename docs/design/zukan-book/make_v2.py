# -*- coding: utf-8 -*-
# 図鑑を見やすくする画面案の2版（改善担当 review-1 と PM の指示 11/9 14時30分を受けて）
# 使い方：python3 make_v2.py <出力先>
# 土台の部品は make.py の前半（色・枠・ツメなど）をそのまま読み込む。空港の表は /tmp/claude-0/ap.json
# （web/index.html の空港の配列の先頭86件を [id,名前,コード,都道府県,緯度,経度] で書き出したもの）
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, 'make.py'), encoding='utf-8').read().split('# ---------- 02 図鑑の基本')[0]
exec(_src.replace('OUT = sys.argv[1]', 'OUT = sys.argv[1] if len(sys.argv) > 1 else HERE'))
_y = open(os.path.join(HERE, 'make.py'), encoding='utf-8').read()
exec(_y[_y.index('YOMI = dict('):_y.index('def p05b')])

# ---------- 2版の部品 ----------
V2 = """
.ttl{margin-top:12px}
.ttl .pill{padding:0 13px}
/* 集めた空港＋9地方の数 */
.hero2{margin-top:10px;background:var(--navy);color:#fff;border-radius:22px;padding:12px 16px 14px}
.hero2 .ht{display:flex;align-items:baseline;gap:8px}
.hero2 .lab{font-size:13px;color:#C9D2DE;font-weight:700}
.hero2 .ht .num{color:#fff;font-size:34px}.hero2 .ht .u{color:#C9D2DE;font-size:13px}
.hero2 .side{margin-left:auto;font-size:13px;color:#C9D2DE;font-weight:600}
.rg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px 12px;margin-top:8px}
.rg div{min-width:0}
.rg .t{display:flex;align-items:baseline;justify-content:space-between;font-size:13px;color:#C9D2DE;font-weight:700;line-height:18px;white-space:nowrap}
.rg .t span:last-child{font-family:var(--sign);font-size:15px;color:#fff}
.rg .t small{font-family:var(--gothic);font-size:12px;color:#C9D2DE;font-weight:600}
.rg .b{display:block;height:3px;border-radius:2px;background:rgba(255,255,255,.18);margin-top:3px;overflow:hidden}
.rg .b i{display:block;height:100%;border-radius:2px;background:var(--c)}
.rg .now .t span:first-child{color:#fff}
/* 1行の扉 */
.door1{margin-top:12px;height:50px;padding:0 16px 0 20px;display:flex;align-items:center;gap:10px;position:relative;overflow:hidden;scroll-margin-top:60px}
.door1::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--c)}
.door1 h2{margin:0;font-size:18px;color:var(--strong);letter-spacing:.04em;line-height:1}
.door1 .num{font-size:22px}.door1 .u{margin-right:2px}
.door1 .bar{flex:1;margin:0 0 0 6px;height:5px}
/* 高さ104の枠 */
.grid{margin-top:8px}
.ap{height:104px;padding:10px 10px 8px}
.ap .ft{margin-top:6px}
.ap .stp{width:26px;height:26px}
.ap .cd.jp{font-size:20px;line-height:1.35}
.ap .nm.nc{color:var(--sub);font-weight:600}
.stick{position:sticky;top:0;z-index:15;background:var(--bg);margin:0 -16px;padding:8px 16px;display:flex;align-items:center;gap:10px}
.stick b{font-size:17px;color:var(--strong)}.stick .dot{width:10px;height:10px;border-radius:50%;background:var(--c)}
.stick small{font-size:13px;color:var(--sub);font-weight:700}.stick .pill{margin-left:auto}
.ann{margin-bottom:110px}
"""
V2_NIGHT = """
.hero2{background:var(--card);box-shadow:var(--shadow)}
.hero2 .lab,.hero2 .side,.hero2 .ht .u,.rg .t,.rg .t small{color:var(--sub)}
.hero2 .ht .num{color:var(--glow1);text-shadow:0 0 6px rgba(95,217,147,.45)}
.rg .t span:last-child{color:var(--strong)}
.rg .b{background:#141B24}.rg .b i{background:var(--glow1)}
.door1::before{display:none}
.ap.got{background:#18222E;box-shadow:inset 0 0 0 1px rgba(150,170,195,.22)}
.ap.no{background:transparent;box-shadow:inset 0 0 0 1.5px #232D39}
.stick{background:var(--bg)}
"""

def stamp2(got, night=False, size=26):
    if got:
        col = '#5FD993' if night else '#16233A'
        sw = 2.6 if night else 2.2
        return ('<svg class="stp" style="width:%dpx;height:%dpx" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="13" fill="none" stroke="%s" stroke-width="2"/>'
                '<circle cx="15" cy="15" r="9.5" fill="none" stroke="%s" stroke-width="1"/><path d="M9 15.5l4 4 8-9" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"/></svg>') % (size, size, col, col, col, sw)
    col = '#66778C' if night else '#5F6875'
    return '<svg class="stp" style="width:%dpx;height:%dpx" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="13" fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="3 3"/></svg>' % (size, size, col)

def cell2(a, night=False):
    g = GOT.get(a['code'])
    c = RC[a['reg']]
    nocode = a['code'] == '—'
    if nocode:
        top = '<span class="cd jp">%s</span><span class="nm nc">コードなし</span>' % short(a)
    else:
        top = '<span class="cd">%s</span><span class="nm">%s</span>' % (a['code'], short(a))
    if g:
        ft = stamp2(True, night, 30 if night else 26) + '<span><b>%d</b><span class="u">回</span></span>' % g
        return '<a class="ap got" href="04-airport-v2.html" style="--c:%s">%s<span class="ft">%s</span></a>' % (c, top, ft)
    return '<div class="ap no" style="--c:%s">%s<span class="ft">%s<span>まだ</span></span></div>' % (c, top, stamp2(False, night))

def regcount(r):
    L = byreg(r)
    return sum(1 for a in L if GOT.get(a['code'])), len(L)

def hero2(night=False, now='北海道'):
    tot = sum(1 for a in A if GOT.get(a['code']))
    s = ('<section class="hero2"><div class="ht"><span class="lab">集めた空港</span><span><span class="num">%d</span><span class="u">/ 86</span></span>'
         '<span class="side">まだ 70 空港</span></div><div class="rg">') % tot
    for r in RN:
        g, n = regcount(r)
        s += '<div class="%s" style="--c:%s"><span class="t"><span>%s</span><span>%d<small>/%d</small></span></span><span class="b"><i style="width:%d%%"></i></span></div>' % (
            'now' if r == now else '', RC[r], r, g, n, round(g / n * 100))
    return s + '</div></section>'

def door1(r, night=False):
    g, n = regcount(r)
    return ('<section class="card door1" id="%s" style="--c:%s"><h2>%s</h2><span><span class="num">%d</span><span class="u">/ %d</span></span>'
            '<span class="bar"><i style="width:%d%%"></i></span></section>') % (r, RC[r], r, g, n, round(g / n * 100))

def titlerow2():
    return ('<div class="ttl"><h1>図鑑</h1>'
            '<a class="pill" href="05-index-v2.html"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg>索引</a>'
            '<a class="pill" href="06-others-v2.html">ほかの図鑑・実績</a></div>')

def vband2(on='地方別'):
    s = '<div class="vband">'
    for v in ['地方別', '地図', '行った順']:
        s += '<span class="pill%s">%s</span>' % (' on' if v == on else '', v)
    return s + '<a class="pill ed" href="07-views-v2.html" aria-label="見方の帯を編集"><svg class="i" viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/></svg></a></div>'

def tsume2(on):
    return tsume(on)

def page2(fn, title, body, night=False, extra=''):
    page(fn, title, body, night, V2 + (V2_NIGHT if night else '') + extra)

def ann(t, items):
    return '<div class="ann"><b>%s</b><ul>%s</ul></div>' % (t, ''.join('<li>%s</li>' % i for i in items))

# ---------- 02 図鑑の基本（昼・夜） ----------
def p02(night=False):
    b = tsume2('北海道') + '<div class="wrap">' + header(night) + '<div class="main">' + titlerow2() + vband2() + hero2(night)
    b += door1('北海道', night) + '<div class="grid">' + ''.join(cell2(a, night) for a in byreg('北海道')) + '</div>'
    b += door1('東北', night) + '<div class="grid">' + ''.join(cell2(a, night) for a in byreg('東北')) + '</div>'
    if night:
        b += ann('02 の夜（2版）', ['行った枠だけ少し明るい地（#18222E）と細い縁。✓ の丸は緑（緑は「集めた・入」の意味）で 30px に大きく',
                                   'まだの枠は地を抜いて細い縁だけ。違いは地・✓ と点線・「回」と「まだ」の3つ',
                                   '9地方の数の帯と「集めた空港 16」は緑。光る数字は 16 の1つだけ。ツメは色なし（選んだ地方だけ強い字＋縁）',
                                   '記号の意味（08 の夜）では「色の帯＝地方」の行を出さない'])
    else:
        b += ann('02 図鑑の基本（2版）', ['「集めた空港」のカードに9地方の数と細い帯9本。今のタイルの「北海道 3/12…」が一目で見える形を残す。今いる地方（北海道）の名前だけ白',
                                       '扉は1行（地方名・数・細い帯）。小さな地図は地方へ飛んだとき（03）だけ',
                                       '枠は高さ104（コード → 名前 → ✓ と回数をすぐ続ける）。667 でも1段目の3つが全部見える',
                                       '帯の1つ目は「地方別」。「図鑑」の字は題とタブ帯だけ',
                                       '右上は「索引」（字で探せる・05）と「ほかの図鑑・実績」（06）',
                                       '指で送って東北に入ると、ツメは「東北」が飛び出す（02c）'])
    b += '</div></div>' + tabs()
    page2('02-zukan-base%s-v2.html' % ('-night' if night else ''), '図鑑の基本 2版' + ('（夜）' if night else ''), b, night)

# ---------- 02c 送って東北に入ったところ ----------
def p02c():
    b = tsume2('東北') + '<div class="wrap"><div class="main">'
    g, n = regcount('東北')
    b += '<div class="stick" style="--c:%s"><span class="dot"></span><b>東北</b><small>%d / %d</small></div>' % (RC['東北'], g, n)
    L = byreg('北海道')
    b += '<div class="grid" style="margin-top:0">' + ''.join(cell2(a) for a in L[-3:]) + '</div>'
    b += door1('東北') + '<div class="grid">' + ''.join(cell2(a) for a in byreg('東北')) + '</div>'
    b += door1('関東') + '<div class="grid">' + ''.join(cell2(a) for a in byreg('関東')[:3]) + '</div>'
    b += ann('02c 指で送って東北に入ったところ', ['東北の扉が上の端を越えたら、ツメの飛び出しは「北海道」から「東北」へ移る（送るのに合わせてついてくる）',
                                           '上に「東北 1/9」を止めておく。題・帯・集めた空港のカードは送ると上へ消える',
                                           'ツメを押したときは、その地方の扉が「東北 1/9」の下に来る所まで飛ぶ'])
    b += '</div></div>' + tabs()
    page2('02c-scroll-v2.html', '送って東北に入ったところ', b)

# ---------- 03 空港の並び（関東へ飛んだところ） ----------
def p03():
    ex = '.door .bar{height:5px}'
    b = tsume2('関東') + '<div class="wrap"><div class="main">'
    g, n = regcount('関東')
    b += '<div class="stick" style="--c:%s"><span class="dot"></span><b>関東</b><small>%d / %d</small><a class="pill" href="02-zukan-base-v2.html">図鑑の上へ</a></div>' % (RC['関東'], g, n)
    b += door('関東', desc=True)
    b += '<div class="grid">' + ''.join(cell2(a) for a in byreg('関東')) + '</div>'
    for nm, cd in (('羽田のターミナル', 'HND'), ('成田のターミナル', 'NRT')):
        b += '<div class="sec-h">%s<small>0 / 3</small></div><div class="grid">' % nm
        for t in (1, 2, 3):
            b += '<div class="ap no" style="--c:%s"><span class="cd">%s<span style="font-size:16px;color:var(--sub)"> T%d</span></span><span class="nm">%s 第%d</span><span class="ft">%s<span>まだ</span></span></div>' % (RC['関東'], cd, t, nm[:2], t, stamp2(False))
        b += '</div>'
    b += ann('03 関東へ飛んだところ（2版）', ['ツメで飛んだときだけ、扉に小さな地図（● 集めた ○ まだ）と最後に押した日を出す。送って入ったときは 02 と同じ1行の扉',
                                        '枠は高さ104。コードのない空港（調布・新島・神津島）は名前を大きく1回だけ、下は小さく「コードなし」',
                                        '羽田・成田のターミナルは今と同じ数え方で地方の並びのあと'])
    b += '</div></div>' + tabs()
    page2('03-airport-grid-v2.html', '空港の並び 2版', b, extra=ex)

# ---------- 04 1空港の詳しい所 ----------
EX04 = ('.idc{margin-top:10px;padding:16px 18px;display:flex;gap:16px;align-items:center;position:relative;overflow:hidden}.idc::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--c)}'
        '.idc .big{font-family:var(--sign);font-weight:700;font-size:52px;line-height:1;color:var(--strong);letter-spacing:.02em}'
        '.idc h2{font-size:16px;margin:6px 0 0;color:var(--strong);line-height:1.4}.idc small{font-size:13px;color:var(--sub)}'
        '.cmp{margin-top:10px;padding:16px 16px 14px}.cmp h3,.rec h3{margin:0;font-size:15px;color:var(--strong)}.cmp .sub{font-size:13px;color:var(--sub)}'
        '.rw{display:grid;grid-template-columns:64px 1fr;align-items:center;gap:8px;margin-top:10px}.rw .k{font-size:13px;font-weight:700;color:var(--ink);line-height:1.3}'
        '.rw .tr{position:relative;height:26px}.rw .ln{position:absolute;left:0;top:9px;height:8px;border-radius:4px;background:var(--c)}.rw .ln.o{background:#8A93A0}'
        '.rw .vl{position:absolute;top:0;font-size:13px;font-weight:700;color:var(--strong);white-space:nowrap;padding-left:6px;line-height:26px}'
        '.sc{display:grid;grid-template-columns:64px 1fr;gap:8px;margin-top:8px}.sc div{display:flex;justify-content:space-between;font-size:12px;color:var(--mute)}'
        '.grp{font-size:13px;font-weight:700;color:var(--sub);margin-top:14px}'
        '.rec{margin-top:10px;padding:14px 0 6px}.rec h3{padding:0 16px}.rec .row{min-height:48px}'
        '.turn{display:flex;gap:8px;margin-top:14px}.turn a{flex:1;justify-content:space-between;padding:0 14px}.turn .cd{font-family:var(--sign);font-size:18px;color:var(--strong)}'
        '.swp{display:flex;justify-content:center;align-items:center;gap:8px;font-size:13px;color:var(--sub);margin-top:8px;font-weight:600}'
        '.dots{display:flex;gap:5px;justify-content:center;margin-top:10px}.dots i{width:6px;height:6px;border-radius:50%;background:#C5CBD3}.dots i.on{width:18px;border-radius:3px;background:var(--c)}')

def idcard():
    return ('<section class="card idc"><svg viewBox="0 0 96 96" width="88" height="88" aria-label="羽田の印"><circle cx="48" cy="48" r="44" fill="none" stroke="#16233A" stroke-width="3"/><circle cx="48" cy="48" r="36" fill="none" stroke="#16233A" stroke-width="1.2"/>'
            '<text x="48" y="56" text-anchor="middle" font-family="Sign,Barlow Condensed,sans-serif" font-weight="700" font-size="26" fill="#16233A">HND</text><text x="48" y="72" text-anchor="middle" font-family="Sign,sans-serif" font-weight="600" font-size="9" fill="#16233A">2025.12.14</text></svg>'
            '<div><div class="big">HND</div><h2>東京国際空港（羽田）</h2><small>東京都・関東</small></div></section>')

def rec():
    return ('<section class="card rec"><h3>押した記録</h3>'
            '<div class="row"><div class="tx"><b>2026年11月1日</b><small>28回目</small></div></div>'
            '<div class="row"><div class="tx"><b>2026年10月18日</b><small>27回目</small></div></div>'
            '<div class="row"><div class="tx"><b>すべて見る</b><small>28回ぶん</small></div><span style="font-size:18px;color:var(--sub);font-weight:700">›</span></div></section>')

def turn():
    L = byreg('関東'); i = [a['code'] for a in L].index('HND')
    def lab(a): return short(a) + ('' if a['code'] == '—' else ' <span class="cd">%s</span>' % a['code'])
    dots = ''.join('<i class="%s"></i>' % ('on' if j == i else '') for j in range(len(L)))
    return ('<div class="turn"><a class="pill" href="#">‹ <span>%s</span></a><a class="pill" href="#"><span>%s</span> ›</a></div>'
            '<div class="dots" aria-label="関東の4番目">%s</div>'
            '<div class="swp">左右にはらっても、となりの空港へ移ります</div>') % (lab(L[i - 1]), lab(L[i + 1]), dots)

def p04(nodata=False):
    c = RC['関東']
    b = '<div class="wrap" style="--c:%s"><div class="top"><a class="pill" href="03-airport-grid-v2.html">‹ 関東</a><a class="pill" href="08-kigou-v2.html">記号の意味</a></div>' % c
    b += idcard()
    if nodata:
        b += ('<div class="dl"><div><div class="k">押した回数</div><div class="v"><span class="num">28</span><span class="u">回</span></div></div>'
              '<div><div class="k">はじめて押した日</div><div class="v s"><span class="num">2025</span><span class="u">年</span><span class="num">12</span><span class="u">月</span><span class="num">14</span><span class="u">日</span></div></div></div>')
        b += rec() + turn()
        b += ann('04b 開港・滑走路の表がないとき', ['データ欄は「押した回数」「はじめて押した日」の2つだけ。空の欄や「—」は置かない',
                                              '大きさ比べのカードは出さない。押した記録のすぐ下が「‹ 前／次 ›」',
                                              '表ができたら 04 の形（データ欄4つ・記録の下に大きさ比べ）にする。どちらでも上の印・データ欄・記録の位置は変わらない'])
        fn, t = '04b-airport-nodata-v2.html', '1空港の詳しい所（表がないとき）'
    else:
        b += ('<div class="dl"><div><div class="k">押した回数</div><div class="v"><span class="num">28</span><span class="u">回</span></div></div>'
              '<div><div class="k">はじめて押した日</div><div class="v s"><span class="num">2025</span><span class="u">年</span><span class="num">12</span><span class="u">月</span><span class="num">14</span><span class="u">日</span></div></div>'
              '<div><div class="k">開港</div><div class="v"><span class="num">1931</span><span class="u">年</span></div></div>'
              '<div><div class="k">滑走路</div><div class="v"><span class="num">4</span><span class="u">本</span></div></div></div>')
        b += rec()
        MAX = 3400
        def rw(k, m, o=False):
            return '<div class="rw"><span class="k">%s</span><span class="tr"><i class="ln%s" style="width:%.1f%%"></i><span class="vl" style="left:%.1f%%">%s<span class="u">m</span></span></span></div>' % (k, ' o' if o else '', m / MAX * 70, m / MAX * 70, format(m, ','))
        b += '<section class="card cmp"><h3>大きさ比べ</h3><div class="sub">滑走路の長さ・同じ縮尺</div>'
        b += rw('C 滑走路', 3360) + rw('A 滑走路', 3000) + rw('B 滑走路', 2500) + rw('D 滑走路', 2500)
        b += '<div class="grp">押したほかの空港（いちばん長い滑走路）</div>' + rw('新千歳', 3000, True) + rw('福岡', 2800, True) + rw('石垣', 2000, True)
        b += '<div class="sc"><span></span><div><span>0</span><span>1,000</span><span>2,000</span><span>3,000m</span></div></div></section>'
        b += turn()
        b += ann('04 1空港の詳しい所（2版）', ['右上は「記号の意味」（08）。「見方」の字は使わない',
                                          'データ欄は自分の記録（押した回数・はじめて押した日）を上の段、開港・滑走路を下の段。そのすぐ下に「押した記録」、大きさ比べはその下',
                                          '「‹ 前／次 ›」はどちらも「名前＋コード」。コードのない空港は名前だけ（‹ 調布）。下の点は関東の何番目か',
                                          '左右にはらっても、となりの空港へ（今の案内標の「次々に見る」楽しさを残す）',
                                          '開港の年・滑走路の長さは見本の値。表がないときは 04b の形'])
        fn, t = '04-airport-v2.html', '1空港の詳しい所 2版（羽田）'
    b += '</div>' + tabs()
    page2(fn, t, b, extra=EX04)

# ---------- 05 索引（字で探す欄＋ABC／50音） ----------
EX05 = ('.srch{display:flex;align-items:center;gap:10px;height:52px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);padding:0 18px;margin-top:12px;font-size:15px;color:var(--sub)}'
        '.srch.on{box-shadow:inset 0 0 0 2px var(--sel),var(--shadow);color:var(--strong);font-weight:700}.srch .cur{display:inline-block;width:2px;height:20px;background:var(--acc);margin-left:1px;vertical-align:middle}'
        '.srch .x{margin-left:auto;width:44px;height:44px;margin-right:-12px;display:flex;align-items:center;justify-content:center;color:var(--sub)}'
        '.lt{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.lt a{min-width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:16px;font-weight:800;color:var(--strong);text-decoration:none}'
        '.lt.abc a{font-family:var(--sign);font-size:18px;font-weight:700}'
        '.ix{margin-top:10px;padding:4px 0}.ix .lh{font-weight:800;font-size:18px;color:var(--strong);padding:12px 16px 2px}.ix .lh small{font-size:13px;color:var(--sub);font-weight:700;margin-left:8px}'
        '.ix .row .cd{font-family:var(--sign);font-weight:700;font-size:18px;width:46px;color:var(--strong)}.ix .row.no .cd{color:#5F6875}.ix .row.no .tx b{color:var(--sub);font-weight:600}'
        '.ix .row .tx small{font-size:13px}.ix .st{font-size:13px;color:var(--sub);font-weight:700;width:36px;text-align:right}'
        '.ix mark{background:#FFF0B8;color:var(--strong);border-radius:3px;padding:0 1px}'
        '.seg2{display:flex;gap:6px;margin-top:14px;align-items:center}.seg2 .lbl{font-size:13px;color:var(--sub);font-weight:700;margin-right:4px}'
        '.foot{display:flex;justify-content:center;margin:14px 0 0}')

def idx_head(state):
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base-v2.html">‹ 図鑑</a><a class="pill" href="08-kigou-v2.html">記号の意味</a></div><div class="ttl" style="margin-top:4px"><h1>索引</h1></div>'
    if state == 'search':
        b += '<label class="srch on"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg><span>みや<span class="cur"></span></span><span class="x" aria-label="消す">✕</span></label>'
    else:
        b += '<label class="srch"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg><span>名前・コード・読みで探す</span></label>'
    return b

def p05():
    b = idx_head('abc')
    b += '<div class="seg2"><span class="lbl">字を打たずに探す</span><span class="pill on">ABC順</span><a class="pill" href="05b-index-kana-v2.html">50音順</a></div>'
    L = sorted([a for a in A if a['code'] != '—'], key=lambda a: a['code'])
    letters = sorted(set(a['code'][0] for a in L))
    b += '<div class="lt abc">' + ''.join('<a href="#L%s">%s</a>' % (l, l) for l in letters) + '</div><section class="card ix">'
    cur = ''
    for a in L:
        if a['code'][0] != cur:
            cur = a['code'][0]; b += '<div class="lh" id="L%s">%s</div>' % (cur, cur)
        g = GOT.get(a['code'])
        b += '<div class="row%s"><span class="cd">%s</span><div class="tx"><b>%s</b></div><span class="chip" style="--tc:%s">%s</span><span class="st">%s</span></div>' % (
            '' if g else ' no', a['code'], short(a), tint(RC[a['reg']], .16), a['reg'], ('%d回' % g) if g else 'まだ')
    b += '<div class="lh">コードのない空港</div>'
    for a in [a for a in A if a['code'] == '—']:
        b += '<div class="row no"><div class="tx"><b>%s</b><small>コードなし</small></div><span class="chip" style="--tc:%s">%s</span><span class="st">まだ</span></div>' % (short(a), tint(RC[a['reg']], .16), a['reg'])
    b += '</section>'
    b += ann('05 索引（2版）', ['いちばん上に字で探す欄。空港名・コード・読みのどれでも当たる（打ったところは 05c）',
                              '字を打たない人のために、2番目に「ABC順｜50音順」と頭の字のピル。選ぶ段は2つだけ',
                              '記号の意味は別の画面（08）。右上の「記号の意味」から。「見方｜索引」のピルはなくした',
                              'コードのない空港は最後にまとめ、名前の下に「コードなし」'])
    b += '</div>' + tabs()
    page2('05-index-v2.html', '索引 2版（ABC順）', b, extra=EX05)

def p05b():
    b = idx_head('kana')
    b += '<div class="seg2"><span class="lbl">字を打たずに探す</span><a class="pill" href="05-index-v2.html">ABC順</a><span class="pill on">50音順</span></div>'
    L = sorted(A, key=lambda a: YOMI[short(a)])
    groups = []
    for g, ks in GYO:
        m = [a for a in L if YOMI[short(a)][0] in ks]
        if m: groups.append((g, m))
    b += '<div class="lt">' + ''.join('<a href="#K%s">%s</a>' % (g, g) for g, _ in groups) + '</div><section class="card ix">'
    for g, m in groups:
        b += '<div class="lh" id="K%s">%s行<small>%d空港</small></div>' % (g, g, len(m))
        for a in m:
            gt = GOT.get(a['code'])
            cd = a['code'] if a['code'] != '—' else ''
            sm = YOMI[short(a)] + ('' if cd else '・コードなし')
            b += '<div class="row%s"><span class="cd">%s</span><div class="tx"><b>%s</b><small>%s</small></div><span class="chip" style="--tc:%s">%s</span><span class="st">%s</span></div>' % (
                '' if gt else ' no', cd, short(a), sm, tint(RC[a['reg']], .16), a['reg'], ('%d回' % gt) if gt else 'まだ')
    b += '</section>'
    b += ann('05b 索引の 50音順（2版）', ['05 と同じ上の形（探す欄 → ABC順｜50音順 → 行のピル）',
                                       '行の並びを 05 とそろえ、コードを左、名前と読みをまん中に。コードのない空港は読みのあとに「コードなし」',
                                       '読みは画面案のために書いた。本番では空港の表に読みの列が要る（データ担当）'])
    b += '</div>' + tabs()
    page2('05b-index-kana-v2.html', '索引 2版（50音順）', b, extra=EX05)

def p05c():
    b = idx_head('search')
    q = 'みや'
    hits = [a for a in A if YOMI[short(a)].startswith(q)]
    hits.sort(key=lambda a: YOMI[short(a)])
    b += '<div class="note" style="margin-top:12px">「みや」に当たる空港 %d</div><section class="card ix">' % len(hits)
    for a in hits:
        gt = GOT.get(a['code']); y = YOMI[short(a)]
        b += '<div class="row%s"><span class="cd">%s</span><div class="tx"><b>%s</b><small><mark>%s</mark>%s</small></div><span class="chip" style="--tc:%s">%s</span><span class="st">%s</span></div>' % (
            '' if gt else ' no', a['code'], short(a), y[:len(q)], y[len(q):], tint(RC[a['reg']], .16), a['reg'], ('%d回' % gt) if gt else 'まだ')
    b += '</section><div class="note">名前（宮）・コード（MMY）・読み（みや）のどれでも当たります。行を押すとその空港へ。</div>'
    b += ann('05c 字を打ったところ', ['1字打つごとに下の一覧がしぼられる。打っている間は ABC／50音のピルを隠す',
                                   '当たった所に薄い黄色の印（名前・コード・読みのどれに当たったか分かる）',
                                   '当たらないとき：「当たる空港がありません。飛行場・番外編は〈ほかの図鑑・実績〉にあります」の1行',
                                   '✕ で消すと 05 に戻る'])
    b += '</div>' + tabs()
    page2('05c-index-search-v2.html', '索引 2版（字を打ったところ）', b, extra=EX05)

# ---------- 08 記号の意味（昼・夜） ----------
def p08(night=False):
    ex = '.lg{margin-top:12px;padding:6px 0}.lg .row{min-height:64px}.lg .ic{width:52px;display:flex;justify-content:center;align-items:center;gap:4px;flex:none}'
    b = '<div class="wrap"><div class="top"><a class="pill" href="04-airport-v2.html">‹ 戻る</a></div><div class="ttl" style="margin-top:4px"><h1>記号の意味</h1></div>'
    b += '<section class="card lg">'
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>✓ の丸 … 印を押した空港</b><small>となりの数字は押した回数</small></div></div>' % stamp2(True, night, 34)
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>点線の丸 … まだの空港</b><small>同じ枠・同じ場所に、薄い地で載せています</small></div></div>' % stamp2(False, night, 34)
    fill = '#5FD993' if night else RC['関東']
    ring = '#66778C' if night else '#8A93A0'
    b += ('<div class="row"><span class="ic"><svg width="44" height="22" viewBox="0 0 44 22" aria-hidden="true"><circle cx="11" cy="11" r="6" fill="%s"/><circle cx="33" cy="11" r="5" fill="none" stroke="%s" stroke-width="1.6"/></svg></span>'
          '<div class="tx"><b>塗った丸と白い丸 … 地方の地図</b><small>塗った丸は集めた、白い丸はまだ。%s（北が上）</small></div></div>') % (fill, ring, '塗った色は緑' if night else '塗った色は地方の色')
    if not night:
        b += '<div class="row"><span class="ic" style="flex-direction:column">' + ''.join('<i style="display:block;width:28px;height:4px;border-radius:2px;background:%s"></i>' % RC[r] for r in RN[:3]) + '</span><div class="tx"><b>色の帯 … 地方</b><small>右端のツメ・扉・枠の上の帯が同じ色</small></div></div>'
    b += '<div class="row"><span class="ic"><span class="num" style="font-size:22px">HND</span></span><div class="tx"><b>3レターコード</b><small>コードのない空港は名前を大きく、下に「コードなし」</small></div></div>'
    b += '</section><div class="note">この図鑑は国内の86空港と羽田・成田のターミナルです。飛行場・番外編・特別塗装機・実績は「ほかの図鑑・実績」にあります。</div>'
    if night:
        b += ann('08 の夜', ['夜は地方の色を使わないので「色の帯 … 地方」の行を出さない', '✓ の丸と地図の塗った丸は緑（集めた）'])
    else:
        b += ann('08 記号の意味（新しく分けた画面）', ['1空港の右上・索引の右上の「記号の意味」から開く。索引とは別の画面',
                                                '地図の丸の絵は「塗った丸と白い丸」を並べ、説明に「塗った色は地方の色」と書く（凡例の丸の色と説明をそろえた）',
                                                '項目は5つだけ。レア・ノルマの言い方はしない'])
    b += '</div>' + tabs()
    page2('08-kigou%s-v2.html' % ('-night' if night else ''), '記号の意味' + ('（夜）' if night else ''), b, night, ex)

# ---------- 06 ほかの図鑑・実績 ----------
def p06():
    ex = ('.bk{margin-top:8px;padding:12px 14px;display:flex;gap:14px;align-items:center;text-decoration:none;color:inherit;min-height:76px}'
          '.bk .sp{width:42px;height:54px;border-radius:8px 12px 12px 8px;flex:none;background:var(--wash);box-shadow:inset 4px 0 0 var(--b),inset 0 0 0 1px #E3E6EB;display:flex;align-items:center;justify-content:center}'
          '.bk .sp svg{width:22px;height:22px;fill:none;stroke:var(--sub);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}'
          '.bk .tx{flex:1;min-width:0}.bk b{display:block;font-size:16px;color:var(--strong);line-height:1.35}.bk small{display:block;font-size:13px;color:var(--sub);line-height:1.45;margin-top:2px}'
          '.bk .n{text-align:right;flex:none}.bk .n .num{font-size:24px}'
          '.base{margin-top:14px;padding:12px 16px;display:flex;align-items:center;gap:12px;background:var(--wash);border-radius:18px;box-shadow:inset 0 0 0 1px #E3E6EB}'
          '.base b{font-size:15px;color:var(--strong)}.base small{display:block;font-size:13px;color:var(--sub)}')
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base-v2.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:4px"><h1 style="font-size:24px">ほかの図鑑・実績</h1></div>'
    b += '<div class="note" style="margin-top:4px">空港の図鑑（86）とは別に数えます。ここで集めても「集めた空港」の数は変わりません。</div>'
    books = [('#6B3FA0', '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>', '実績', '空港の印や回数・路線・距離で達成するもの', 21, 522),
             ('#3D7A4E', '<path d="M3 17h18M6 17l3-8h6l3 8M12 9V5"/>', '飛行場・滑空場', '定期便のない飛行場とグライダーの滑空場', 0, 63),
             ('#2B4A73', '<path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7z"/>', '番外編', '自衛隊の飛行場と、一般の人が行けない飛行場', 0, 32),
             ('#8A6A1F', '<path d="M10.5 13.5 4 11l1.5-1.5 7 1 3.5-3.5c1-1 2.5-1.2 3-.5s.5 2-.5 3L15 13l1 7-1.5 1.5-2.5-6.5-3 3v2.5L7.5 22 6 18l-4-1.5L3.5 15H6z"/>', '機体図鑑（特別塗装機）', '乗った・見た特別塗装機', 0, 93)]
    for col, ic, t, d, g, n in books:
        b += '<a class="card bk" href="#" style="--b:%s"><span class="sp"><svg viewBox="0 0 24 24">%s</svg></span><span class="tx"><b>%s</b><small>%s</small></span><span class="n"><span class="num">%d</span><span class="u">/ %d</span></span></a>' % (col, ic, t, d, g, n)
    b += '<div class="base"><div><b>空港の図鑑</b><small>国内86空港＋羽田・成田のターミナル</small></div><span style="margin-left:auto" class="num">16<span class="u">/ 86</span></span></div>'
    b += ann('06 ほかの図鑑・実績（2版）', ['名前を「別冊」から「ほかの図鑑・実績」に。中身が分かる名前にした',
                                         '実績をいちばん上に。図鑑（冊）ではないが、ここから1回で行ける',
                                         '背表紙は薄い地＋左の細い色の線1本だけ。絵は灰色。図鑑のタブで色を使うのはツメと扉の細い帯だけになる',
                                         '1冊の高さを 76 に縮め、667 でも4冊とも見える'])
    b += '</div>' + tabs()
    page2('06-others-v2.html', 'ほかの図鑑・実績', b, extra=ex)

# ---------- 07 見方の帯のシート／今の人へのお知らせ ----------
def p07():
    b = tsume2('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2() + hero2() + door1('北海道') + '</div></div>' + tabs()
    b += '<div class="dim"></div><section class="sheet"><div class="grab"></div><b style="font-size:18px;color:var(--strong)">見方の帯</b>'
    b += '<div class="note" style="margin-top:2px">OFF で帯から隠れます。</div>'
    rows = [('地方別', '地方ごとに全部の空港を並べる', None), ('地図', '集めた空港を地図で', 'on'), ('行った順', 'はじめて押した日の順', 'on')]
    for t, s, st in rows:
        right = '<span style="font-size:13px;color:var(--sub);font-weight:700">いつも</span>' if st is None else '<span class="sw %s">%s</span>' % (st, st.upper())
        b += '<div class="row" style="padding:6px 2px;min-height:60px"><div class="tx"><b>%s</b><small>%s</small></div>%s</div>' % (t, s, right)
    b += '<div class="btn">完了</div></section>'
    page2('07-views-v2.html', '見方の帯 2版', b)

def p07b():
    ex = ('.notice{margin-top:10px;padding:14px 16px 12px;position:relative}.notice b{display:block;font-size:15px;color:var(--strong);padding-right:40px}'
          '.notice ul{margin:6px 0 0;padding-left:1.1em;font-size:13px;color:var(--ink);line-height:1.7}.notice .cl{position:absolute;right:4px;top:4px;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub);font-size:16px}'
          '.notice .ok{display:flex;justify-content:flex-end;margin-top:4px}')
    b = tsume2('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2()
    b += ('<section class="card notice"><b>図鑑の見方を3つにまとめました</b><span class="cl" aria-label="閉じる">✕</span><ul>'
          '<li>タイル・地方 → 「地方別」（地方ごとの数はこの下のカード）</li><li>案内標 → 1空港を開いて「‹ 前／次 ›」か左右にはらう</li><li>年代記 → 「行った順」</li></ul>'
          '<div class="ok"><span class="pill">わかった</span></div></section>')
    b += hero2() + door1('北海道') + '<div class="grid">' + ''.join(cell2(a) for a in byreg('北海道')[:6]) + '</div>'
    b += ann('07b 今使っている人へ1回だけのお知らせ', ['今の5つの見方を使ったことのある人が、次に図鑑を開いたときだけ出す。「わかった」か ✕ で閉じたら二度と出ない',
                                                '新しく始めた人には出さない（「タイル」「案内標」を知らないため）。見方の帯のシート（07）にも「まとめた見方」は書かない',
                                                '保存してある見方の ON／OFF（user_view_prefs）の移し方は報告に書いた（作るときにチェックイン担当とデータ担当へ）'])
    b += '</div></div>' + tabs()
    page2('07b-notice-v2.html', '今の人へのお知らせ', b, extra=ex)

for f in (p02c, p03, p05, p05b, p05c, p06, p07, p07b):
    f()
p02(False); p02(True); p04(False); p04(True); p08(False); p08(True)
print('ok')
