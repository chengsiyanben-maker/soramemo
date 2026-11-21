# -*- coding: utf-8 -*-
# 図鑑を見やすくする画面案の4版（改善担当 review-3 と PM の指示 11/10 1時15分を受けた小さい直し）
# 使い方：python3 make_v4.py <出力先>
# make_v3.py の部品（最後のページ作りの行を除く）を読み込んで使う。空港の表は /tmp/claude-0/ap.json
# （src/index.html の RAW の先頭86件を [id,名前,コード,都道府県,緯度,経度] で書き出したもの。コードなしは「—」）
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_v3 = open(os.path.join(HERE, 'make_v3.py'), encoding='utf-8').read()
_v3 = _v3.split('for f in (p02zero,')[0].replace("HERE = os.path.dirname(os.path.abspath(__file__))", "")
exec(_v3)

# ---------- 1. ターミナルの枠の名前を短く（「新千歳 国内」「福岡 国際」「羽田 第1」） ----------
TERMS = [('CTS', '新千歳', [('国内', '国内'), ('国際', '国際')]),
         ('HND', '羽田', [('T1', '第1'), ('T2', '第2'), ('T3', '第3')]),
         ('NRT', '成田', [('T1', '第1'), ('T2', '第2'), ('T3', '第3')]),
         ('NGO', '中部', [('T1', '第1'), ('T2', '第2')]),
         ('KIX', '関西', [('T1', '第1'), ('T2', '第2')]),
         ('FUK', '福岡', [('国内', '国内'), ('国際', '国際')])]

V4 = """
.ap .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ap>*{flex-shrink:0}
/* 止まった扉：上の安全な余白の下に止まる */
.door1.pin{position:sticky;top:env(safe-area-inset-top,0px);z-index:15;margin-top:0;border-radius:0 0 18px 18px;box-shadow:0 10px 22px -16px rgba(17,24,39,.45)}
.door1 .up{margin-left:4px;margin-right:-10px;min-width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;color:var(--sub);text-decoration:none;font-size:13px;font-weight:700}
.door1 .up svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
/* 扉の下の最初の行（送れば流れていく） */
.rhead{margin-top:8px;padding:10px 12px 10px 16px;display:flex;align-items:center;gap:12px}
.rhead .mini{width:72px;height:72px;flex:none}
.rhead .ds{font-size:13px;color:var(--sub);line-height:1.6}.rhead .ds b{display:block;font-size:15px;color:var(--strong)}
/* 光らせた枠（いちばん近い空港へ飛んだとき） */
.ap.glow{box-shadow:0 0 0 3px var(--c),0 0 0 7px rgba(194,96,58,.22)}
/* 1空港のターミナルの1枚 */
.tm{margin-top:10px;padding:14px 16px 12px}
.tm .h{display:flex;align-items:baseline;gap:8px}.tm h3{margin:0;font-size:15px;color:var(--strong)}.tm .h .num{font-size:22px;margin-left:auto}
.tm .g{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}
.tm .t{border-radius:14px;background:var(--wash);padding:8px 10px;display:flex;flex-direction:column;gap:4px;min-height:64px}
.tm .t .cd{font-family:var(--sign);font-weight:700;font-size:20px;color:var(--strong);line-height:1}
.tm .t .f{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--sub);font-weight:700}.tm .t .f b{font-family:var(--sign);font-size:18px;color:var(--strong)}
.tm .t.no .cd{color:#5F6875}
.tm p{margin:8px 0 0;font-size:13px;color:var(--sub);line-height:1.6}
/* まだの空港の1枚 */
.yet{margin-top:10px;padding:16px 18px}
.yet b{display:block;font-size:16px;color:var(--strong);line-height:1.5}
.yet .r{display:flex;align-items:baseline;gap:6px;margin-top:10px}.yet .r small{font-size:13px;color:var(--sub);font-weight:700}.yet .r .num{font-size:26px;margin-left:auto}
.yet p{margin:6px 0 0;font-size:13px;color:var(--sub);line-height:1.6}
.idc.no .big{color:#5F6875}
/* はらうの札：地も影もない字1行 */
.hint2{margin-top:6px;text-align:center;font-size:13px;color:var(--sub);font-weight:600}
"""

def tcell(code, tag, nm, short_, night=False):
    c = RC[TREG[code]]
    g = TGOT.get((code, tag))
    top = '<span class="cd">%s<span class="tg">%s</span></span><span class="nm">%s %s</span>' % (code, tag, short_, nm)
    if g:
        return '<a class="ap got" href="04-airport-v4.html" style="--c:%s">%s<span class="ft">%s<span><b>%d</b><span class="u">回</span></span></span></a>' % (c, top, stamp2(True, night, 30 if night else 26), g)
    return '<div class="ap no" style="--c:%s">%s<span class="ft">%s<span>まだ</span></span></div>' % (c, top, stamp2(False, night))

def page4(fn, title, body, night=False, extra=''):
    page2(fn, title, body, night, V3 + V4 + extra)

UP = '<a class="up" href="02-zukan-base-v4.html" aria-label="図鑑の上へ"><svg viewBox="0 0 24 24"><path d="M6 14l6-6 6 6"/></svg></a>'

def door_pin(r, up=True):
    g, n = regcount(r)
    return ('<section class="card door1 pin" id="%s" style="--c:%s"><h2>%s</h2><span><span class="num">%d</span><span class="u">/ %d</span></span>'
            '<span class="bar"><i style="width:%d%%"></i></span>%s</section>') % (r, RC[r], r, g, n, round(g / n * 100), UP if up else '')

# ---------- 02 図鑑の基本（昼・夜） ----------
def p02v4(night=False):
    b = tsume2('北海道') + '<div class="wrap">' + header(night) + '<div class="main">' + titlerow2() + vband2() + hero2(night)
    b += region_block('北海道', night) + door1('東北', night) + '<div class="grid">' + ''.join(cell2(a, night) for a in byreg('東北')[:3]) + '</div>'
    b += ann('02 図鑑の基本（4版）' + ('の夜' if night else ''),
             ['ターミナルの枠の名前を「新千歳 国内」「新千歳 国際」の短さにした（羽田は「羽田 第1」、福岡は「福岡 国内」「福岡 国際」）。✓ と回数が枠104の中に収まる',
              '名前の行は1行だけ（折り返さない）。それでも長いときは「…」で切る',
              'そのほかは3版のまま'])
    b += '</div></div>' + tabs()
    page4('02-zukan-base%s-v4.html' % ('-night' if night else ''), '図鑑の基本 4版' + ('（夜）' if night else ''), b, night)

# ---------- 02z はじめての人：いちばん近い › でその地方の扉へ飛んで枠を光らせる ----------
def p02zv4():
    keep = dict(GOT); GOT.clear(); keepT = dict(TGOT); TGOT.clear()
    b = tsume2('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2()
    b += ('<section class="hero2 hero0"><div class="ht"><span class="lab">集めた空港</span><span><span class="num">0</span><span class="u">/ 86</span></span>'
          '<span class="side">9地方・86空港</span></div>'
          '<div class="msg">空港でチェックインすると、ここに印が付きます</div>'
          '<a class="near" href="03z-near-v4.html"><small>いちばん近い</small><b>羽田</b><span class="cd">HND</span><span class="km">12<span class="u">km</span></span><span class="go" aria-hidden="true">›</span></a></section>')
    b += region_block('北海道') + door1('東北') + '<div class="grid">' + ''.join(cell2(a) for a in byreg('東北')[:3]) + '</div>'
    b += ann('02z はじめての人（4版）', ['「いちばん近い 羽田 ›」を押すと、関東の扉が上に止まる所まで飛び、羽田の枠を光らせる（03z）。羽田の枠を押すとまだの空港のページ（04c）',
                                       'ターミナルの枠の名前を短くした（新千歳 国内）。そのほかは3版のまま'])
    b += '</div></div>' + tabs()
    page4('02z-first-v4.html', 'はじめての人の図鑑（0／86）4版', b, extra=EX0)
    GOT.update(keep); TGOT.update(keepT)

# ---------- 03z はじめての人がいちばん近い空港へ飛んだところ ----------
def p03z():
    keep = dict(GOT); GOT.clear(); keepT = dict(TGOT); TGOT.clear()
    r = '関東'
    b = tsume2(r) + '<div class="wrap" style="padding-top:0"><div class="main">' + door_pin(r)
    g = ''
    for a in byreg(r):
        h = cell2(a)
        if a['code'] == 'HND':
            h = h.replace('class="ap no"', 'class="ap no glow"', 1).replace('<div class="ap no glow"', '<a href="04c-airport-yet-v4.html" class="ap no glow"', 1)
            h = h[:-len('</div>')] + '</a>'
        g += h
    b += '<div class="grid">' + g + '</div>' + terms_of(r)
    b += ann('03z いちばん近い空港へ飛んだところ（はじめての人）', ['関東の扉が上に止まり、羽田の枠に地方の色の縁を付けて光らせる（2秒ほどで消える）',
                                                           '羽田の枠を押すと、まだの空港のページ（04c）',
                                                           '飛んだ形は 03・02c と同じ（扉が上に止まるだけ。別の帯は出さない）'])
    b += '</div></div>' + tabs()
    page4('03z-near-v4.html', 'いちばん近い空港へ飛んだところ', b, extra=EX0)
    GOT.update(keep); TGOT.update(keepT)

# ---------- 02c：止まる位置を安全な余白の下に ----------
def p02cv4():
    b = tsume2('東北') + '<div class="wrap" style="padding-top:0"><div class="main">' + door_pin('東北')
    b += '<div class="grid">' + ''.join(cell2(a) for a in byreg('東北')) + '</div>'
    b += region_block('関東')
    b += ann('02c 送って東北に入ったところ（4版）', ['扉が止まる位置は、画面の上の安全な余白（iPhone の時計と切り欠き）の下。ブラウザの字の段がないとき（ホーム画面に置いて開いたとき）も扉が隠れない',
                                               '止まった扉の右端に「図鑑の上へ」（上向きの印・押せる所は 44px）。03 と同じ',
                                               'そのほかは3版のまま（扉そのものが止まる・ツメの飛び出しは止まっている扉の地方）'])
    b += '</div></div>' + tabs()
    page4('02c-scroll-v4.html', '送って東北に入ったところ 4版', b)

# ---------- 02d 行った順：月の見出し・枠の中に日付・計28回・地方別と同じ幅 ----------
def cell_d(a, day):
    g = GOT.get(a['code'])
    c = RC[a['reg']]
    top = '<span class="cd">%s</span><span class="nm">%s</span>' % (a['code'], short(a))
    return ('<a class="ap got dd" href="04-airport-v4.html" style="--c:%s">%s<span class="day">%s</span>'
            '<span class="ft"><span><span class="u" style="margin:0 2px 0 0">計</span><b>%d</b><span class="u">回</span></span></span></a>') % (c, top, day, g)

def p02dv4():
    ex = ('.mh{display:flex;align-items:baseline;gap:8px;margin:18px 2px 0;font-size:16px;font-weight:800;color:var(--strong)}.mh small{font-size:13px;color:var(--sub);font-weight:600}'
          '.ap.dd{padding-top:8px}.ap.dd .cd{line-height:1.05}.ap.dd .nm{line-height:1.35}.ap.dd .day{font-size:13px;color:var(--sub);font-weight:600;line-height:1.3}'
          '.ap.dd .nm{margin-top:1px}.ap.dd .ft{margin-top:0;line-height:22px}')
    byc = {a['code']: a for a in A}
    months = {}
    order = []
    for d, cs in VISITS:
        y, rest = d.split('年'); m, dd = rest.split('月')
        key = '%s年%s月' % (y, m)
        if key not in months:
            months[key] = []; order.append(key)
        for c in cs:
            months[key].append((c, '%s月%s' % (m, dd)))
    assert sum(len(v) for v in months.values()) == 16
    b = '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2('行った順')
    b += '<div class="note">はじめて押した日の順。新しい日が上です。</div>'
    for k in order:
        L = months[k]
        b += '<div class="mh">%s<small>%d空港</small></div><div class="grid">' % (k, len(L))
        b += ''.join(cell_d(byc[c], day) for c, day in L) + '</div>'
    b += ann('02d 行った順（4版）', ['見出しは月（2026年10月）。はじめて押した日は枠の中の小さな1行（10月25日）',
                                  '回数は「計28回」。その日の回数ではなく、これまでの回数だと分かるように。行った空港だけなので ✓ の丸は出さない（その分で日付の1行を入れた）',
                                  '枠は地方別と同じ幅（3つ並び）。ツメは出さないが、右のツメの分は空けたまま（地方別と切り替えても枠が動かない）',
                                  '16空港で見出しは9こ（3版は11こ）。844 で8空港が見える（3版は5空港）',
                                  'まだの空港・ターミナルは出さない（3版のまま）'])
    b += '</div></div>' + tabs()
    page4('02d-visited-v4.html', '行った順 4版', b, extra=ex)

# ---------- 03 ツメで関東へ飛んだところ：扉が上に止まる形（別の帯なし） ----------
def p03v4():
    r = '関東'
    b = tsume2(r) + '<div class="wrap" style="padding-top:0"><div class="main">' + door_pin(r)
    b += ('<section class="card rhead">%s<div class="ds"><b>最後に押した：羽田</b>2026年11月1日</div></section>') % minimap(r)
    b += '<div class="grid">' + ''.join(cell2(a) for a in byreg(r)) + '</div>' + terms_of(r)
    b += ann('03 ツメで関東へ飛んだところ（4版）', ['02c と同じ形：関東の扉（1行）が上に止まる。3版の別の帯「● 関東 1/9」はなくした（「関東 1/9」は1回だけ）',
                                              '小さな地図と「最後に押した」は、止まった扉の下の最初の行。送れば流れていく（ツメで飛んだときだけ出す）',
                                              '「図鑑の上へ」は止まった扉の右端の上向きの印（押せる所は 44px）',
                                              '羽田のターミナル 2/3・成田 0/3（3版のまま）'])
    b += '</div></div>' + tabs()
    page4('03-airport-grid-v4.html', '空港の並び 4版', b)

# ---------- 04 羽田：ターミナル 2/3 の1枚・札は字1行 ----------
def tcard(code, zero=False):
    for c, sh, L in TERMS:
        if c == code:
            break
    got = 0 if zero else sum(1 for t, _ in L if TGOT.get((code, t)))
    s = '<section class="card tm"><div class="h"><h3>ターミナル</h3><span class="num">%d<span class="u">/ %d</span></span></div><div class="g">' % (got, len(L))
    for t, nm in L:
        g = 0 if zero else TGOT.get((code, t))
        if g:
            s += '<div class="t"><span class="cd">%s</span><span class="f">%s<b>%d</b><span class="u" style="margin:0">回</span></span></div>' % (t, stamp2(True, False, 20), g)
        else:
            s += '<div class="t no"><span class="cd">%s</span><span class="f">%sまだ</span></div>' % (t, stamp2(False, False, 20))
    return s + '</div><p>ターミナルの印は別に数えます（押した回数 28 には入りません）。</p></section>' if not zero else s + '</div><p>ターミナルの印は空港の印とは別に数えます。</p></section>'

def p04v4():
    c = RC['関東']
    ex = EX04 + ('.swz{position:relative}.swz .edge{position:absolute;top:0;bottom:0;width:20px;background:repeating-linear-gradient(45deg,rgba(194,96,58,.10) 0 4px,transparent 4px 8px);border-radius:4px}'
                 '.swz .edge.l{left:-16px}.swz .edge.r{right:-16px}.dots{margin-top:8px}')
    L = byreg('関東'); i = [a['code'] for a in L].index('HND')
    dots = ''.join('<i class="%s"></i>' % ('on' if j == i else '') for j in range(len(L)))
    b = '<div class="wrap" style="--c:%s"><div class="top"><a class="pill" href="03-airport-grid-v4.html">‹ 関東</a><a class="pill" href="08-kigou-v4.html">記号の意味</a></div>' % c
    b += '<div class="swz"><span class="edge l"></span><span class="edge r"></span>' + idcard() + '</div>'
    b += '<div class="dots" aria-label="関東の%d番目">%s</div>' % (i + 1, dots)
    b += '<div class="hint2">‹ 印のカードをはらうと、となりの空港へ ›</div>'
    b += ('<div class="dl"><div><div class="k">押した回数</div><div class="v"><span class="num">28</span><span class="u">回</span></div></div>'
          '<div><div class="k">はじめて押した日</div><div class="v s"><span class="num">2025</span><span class="u">年</span><span class="num">12</span><span class="u">月</span><span class="num">14</span><span class="u">日</span></div></div></div>')
    b += tcard('HND') + rec()
    def lab(a): return short(a) + ('' if a['code'] == '—' else ' <span class="cd">%s</span>' % a['code'])
    b += '<div class="turn"><a class="pill" href="#">‹ <span>%s</span></a><a class="pill" href="#"><span>%s</span> ›</a></div>' % (lab(L[i - 1]), lab(L[i + 1]))
    b += ann('04 羽田（4版）', ['データ欄のすぐ下に「ターミナル 2/3」の1枚（T1 ✓12・T2 ✓9・T3 まだ）。ターミナルのある6空港だけに出し、ほかの空港では出さない',
                              '「ターミナルの印は別に数えます（押した回数 28 には入りません）」を1回だけ',
                              '「印のカードをはらうと…」の札は、地も影もない薄いグレーの字1行にした（押せるピルに見えないように）。はじめて開いたときの1回だけ',
                              'そのほかは3版のまま（開港・滑走路は出さない形・はらうのは印のカードだけ・端20pxは受けない）'])
    b += '</div>' + tabs()
    page4('04-airport-v4.html', '1空港の詳しい所 4版（羽田）', b, extra=ex)

# ---------- 04c まだ行っていない空港（はじめての人の羽田） ----------
def p04c():
    c = RC['関東']
    ex = EX04 + '.dots{margin-top:8px}'
    L = byreg('関東'); i = [a['code'] for a in L].index('HND')
    dots = ''.join('<i class="%s"></i>' % ('on' if j == i else '') for j in range(len(L)))
    idc = ('<section class="card idc no"><svg viewBox="0 0 96 96" width="88" height="88" aria-label="まだの印"><circle cx="48" cy="48" r="44" fill="none" stroke="#5F6875" stroke-width="2" stroke-dasharray="5 5"/>'
           '<text x="48" y="57" text-anchor="middle" font-family="Sign,Barlow Condensed,sans-serif" font-weight="700" font-size="26" fill="#5F6875">HND</text></svg>'
           '<div><div class="big">HND</div><h2>東京国際空港（羽田）</h2><small>東京都・関東</small></div></section>')
    b = '<div class="wrap" style="--c:%s"><div class="top"><a class="pill" href="03z-near-v4.html">‹ 関東</a><a class="pill" href="08-kigou-v4.html">記号の意味</a></div>' % c
    b += idc + '<div class="dots" aria-label="関東の%d番目">%s</div>' % (i + 1, dots)
    b += ('<section class="card yet"><b>ここでチェックインすると印が付きます</b>'
          '<div class="r"><small>判定の範囲</small><span class="num">2<span class="u">km</span></span></div>'
          '<p>空港の真ん中から 2km の中で「チェックイン」を押すと、この空港の印が付きます。</p>'
          '<div class="r" style="margin-top:6px"><small>いまの場所から</small><span class="num">12<span class="u">km</span></span></div></section>')
    b += tcard('HND', zero=True)
    def lab(a): return short(a) + ('' if a['code'] == '—' else ' <span class="cd">%s</span>' % a['code'])
    b += '<div class="turn"><a class="pill" href="#">‹ <span>%s</span></a><a class="pill" href="#"><span>%s</span> ›</a></div>' % (lab(L[i - 1]), lab(L[i + 1]))
    b += ann('04c まだ行っていない空港', ['上の印は点線の丸と薄い字（記号の意味の「まだ」と同じ）',
                                     'データ欄2つと「押した記録」は出さない（0回・— の空の欄を並べない）。代わりに「ここでチェックインすると印が付きます」と判定の範囲の1枚',
                                     '判定の範囲は今の本番の空港ごとの値（羽田は 2km）。「いまの場所から」は位置を許している人だけ',
                                     'ターミナルのある空港は、ターミナルの1枚も出す（全部まだ）',
                                     'はらう・前／次は行った空港と同じ（はらうのは印のカードだけ）'])
    b += '</div>' + tabs()
    page4('04c-airport-yet-v4.html', 'まだ行っていない空港（羽田）', b, extra=ex)

# ---------- 06：空港の図鑑を押せる白いカードに ----------
def p06v4():
    ex = ('.bk{margin-top:8px;padding:12px 14px;display:flex;gap:14px;align-items:center;text-decoration:none;color:inherit;min-height:76px}'
          '.bk .sp{width:42px;height:54px;border-radius:8px 12px 12px 8px;flex:none;background:var(--wash);box-shadow:inset 4px 0 0 var(--b),inset 0 0 0 1px #E3E6EB;display:flex;align-items:center;justify-content:center}'
          '.bk .sp svg{width:22px;height:22px;fill:none;stroke:var(--sub);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}'
          '.bk .tx{flex:1;min-width:0}.bk b{display:block;font-size:16px;color:var(--strong);line-height:1.35}.bk small{display:block;font-size:13px;color:var(--sub);line-height:1.45;margin-top:2px}'
          '.bk .n{text-align:right;flex:none}.bk .n .num{font-size:24px}.bk .gt{font-size:18px;color:var(--sub);font-weight:700;flex:none}'
          '.sh{margin:18px 2px 0;font-size:13px;color:var(--sub);font-weight:700}')
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base-v4.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:4px"><h1 style="font-size:24px">ほかの図鑑・実績</h1></div>'
    b += '<div class="note" style="margin-top:4px">ここで集めても「集めた空港」の数は変わりません。</div>'
    books = [('#6B3FA0', '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>', '実績', '空港の印や回数・路線・距離で達成するもの', 21, 522),
             ('#3D7A4E', '<path d="M3 17h18M6 17l3-8h6l3 8M12 9V5"/>', '飛行場・滑空場', '定期便のない飛行場とグライダーの滑空場', 0, 63),
             ('#2B4A73', '<path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7z"/>', '番外編', '自衛隊の飛行場と、一般の人が行けない飛行場', 0, 32),
             ('#8A6A1F', '<path d="M10.5 13.5 4 11l1.5-1.5 7 1 3.5-3.5c1-1 2.5-1.2 3-.5s.5 2-.5 3L15 13l1 7-1.5 1.5-2.5-6.5-3 3v2.5L7.5 22 6 18l-4-1.5L3.5 15H6z"/>', '機体図鑑（特別塗装機）', '乗った・見た特別塗装機', 0, 93)]
    for col, ic, t, d, g, n in books:
        b += '<a class="card bk" href="#" style="--b:%s"><span class="sp"><svg viewBox="0 0 24 24">%s</svg></span><span class="tx"><b>%s</b><small>%s</small></span><span class="n"><span class="num">%d</span><span class="u">/ %d</span></span></a>' % (col, ic, t, d, g, n)
    b += '<div class="sh">もどる</div>'
    b += ('<a class="card bk" href="02-zukan-base-v4.html" style="--b:#16233A"><span class="sp"><svg viewBox="0 0 24 24"><path d="M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1z"/><path d="M12 6v14"/></svg></span>'
          '<span class="tx"><b>空港の図鑑</b><small>86空港・ターミナル 3/14（86 の数に入りません）</small></span><span class="n"><span class="num">16</span><span class="u">/ 86</span></span><span class="gt">›</span></a>')
    b += ann('06 ほかの図鑑・実績（4版）', ['空港の図鑑は押せる（図鑑に戻る）ので、上の4冊と同じ白いカード＋影＋「›」にした。小さな見出し「もどる」で4冊と分けた',
                                         'ターミナル 3/14 と「86 の数に入りません」は説明の行に1回だけ',
                                         'そのほかは3版のまま'])
    b += '</div>' + tabs()
    page4('06-others-v4.html', 'ほかの図鑑・実績 4版', b, extra=ex)

# ---------- 08：「86 の数に入りません」に縮める ----------
def p08v4(night=False):
    ex = '.lg{margin-top:12px;padding:6px 0}.lg .row{min-height:64px}.lg .ic{width:52px;display:flex;justify-content:center;align-items:center;gap:4px;flex:none}'
    b = '<div class="wrap"><div class="top"><a class="pill" href="04-airport-v4.html">‹ 戻る</a></div><div class="ttl" style="margin-top:4px"><h1>記号の意味</h1></div>'
    b += '<section class="card lg">'
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>✓ の丸 … 印を押した空港</b><small>となりの数字は押した回数</small></div></div>' % stamp2(True, night, 34)
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>点線の丸 … まだの空港</b><small>同じ枠・同じ場所に、薄い地で載せています</small></div></div>' % stamp2(False, night, 34)
    fill = '#5FD993' if night else RC['関東']
    ring = '#66778C' if night else '#8A93A0'
    b += ('<div class="row"><span class="ic"><svg width="44" height="22" viewBox="0 0 44 22" aria-hidden="true"><circle cx="11" cy="11" r="6" fill="%s"/><circle cx="33" cy="11" r="5" fill="none" stroke="%s" stroke-width="1.6"/></svg></span>'
          '<div class="tx"><b>塗った丸と白い丸 … 地方の地図</b><small>塗った丸は集めた、白い丸はまだ。%s（北が上）</small></div></div>') % (fill, ring, '塗った色は緑' if night else '塗った色は地方の色')
    if not night:
        b += '<div class="row"><span class="ic" style="flex-direction:column">' + ''.join('<i style="display:block;width:28px;height:4px;border-radius:2px;background:%s"></i>' % RC[r] for r in RN[:3]) + '</span><div class="tx"><b>色の帯 … 地方</b><small>右端のツメ・扉・枠の上の帯が同じ色</small></div></div>'
    b += '<div class="row"><span class="ic"><span class="num" style="font-size:22px">HND</span></span><div class="tx"><b>空港コード（HND など）</b><small>コードのない空港は名前を大きく、下に「コードなし」</small></div></div>'
    b += '<div class="row"><span class="ic"><span class="num" style="font-size:18px">T1</span></span><div class="tx"><b>ターミナル（T1・国内など）</b><small>地方の並びのあとに。86 の数に入りません</small></div></div>'
    b += ('</section><div class="note">この図鑑は国内の86空港です。大きな6空港（新千歳・羽田・成田・中部・関西・福岡）はターミナルにも印があります（86 の数に入りません）。'
          '飛行場・番外編・特別塗装機・実績は「ほかの図鑑・実績」にあります。</div>')
    b += ann('08 記号の意味（4版）' + ('の夜' if night else ''), ['ターミナルの行を「86 の数に入りません」に縮めた（1行に収まる）。下の文も同じ言い方に'])
    b += '</div>' + tabs()
    page4('08-kigou%s-v4.html' % ('-night' if night else ''), '記号の意味 4版' + ('（夜）' if night else ''), b, night, ex)

for f in (p02zv4, p03z, p02cv4, p02dv4, p03v4, p04v4, p04c, p06v4):
    f()
p02v4(False); p02v4(True); p08v4(False); p08v4(True)

# 4版どうしのつなぎ（3版・2版の名前で書いてある所を4版へ）
V4FILES = {'02-zukan-base', '02c-scroll', '02z-first', '02d-visited', '03-airport-grid', '04-airport', '06-others', '08-kigou'}
for fn in os.listdir(OUT):
    if not fn.endswith('-v4.html'):
        continue
    p = os.path.join(OUT, fn); s = open(p, encoding='utf-8').read()
    for k in V4FILES:
        for v in ('v2', 'v3'):
            s = s.replace('href="%s-%s.html"' % (k, v), 'href="%s-v4.html"' % k)
    open(p, 'w', encoding='utf-8').write(s)
print('ok')
