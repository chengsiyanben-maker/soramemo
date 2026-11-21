# -*- coding: utf-8 -*-
# 図鑑を見やすくする画面案の3版（改善担当 review-2 と PM の指示 11/9 16時35分、本人の決定 11/9 22時45分を受けて）
# 使い方：python3 make_v3.py <出力先>
# make_v2.py の部品（最後のページ作りの行を除く）を読み込んで使う。空港の表は /tmp/claude-0/ap.json
# （src/index.html の RAW の先頭86件を [id,名前,コード,都道府県,緯度,経度] で書き出したもの。コードなしは「—」）
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
_v2 = open(os.path.join(HERE, 'make_v2.py'), encoding='utf-8').read()
_v2 = _v2.split('for f in (p02c,')[0].replace("HERE = os.path.dirname(os.path.abspath(__file__))", "")
exec(_v2)

# ---------- ターミナル（本番の TERMS と同じ 6空港14こ） ----------
TERMS = [('CTS', '新千歳', [('国内', '国内線'), ('国際', '国際線')]),
         ('HND', '羽田', [('T1', '第1'), ('T2', '第2'), ('T3', '第3')]),
         ('NRT', '成田', [('T1', '第1'), ('T2', '第2'), ('T3', '第3')]),
         ('NGO', '中部', [('T1', '第1'), ('T2', '第2')]),
         ('KIX', '関西', [('T1', '第1'), ('T2', '第2')]),
         ('FUK', '福岡', [('国内', '国内線'), ('国際', '国際線')])]
TREG = {'CTS': '北海道', 'HND': '関東', 'NRT': '関東', 'NGO': '中部', 'KIX': '近畿', 'FUK': '九州'}
# 見本の記録：羽田 T1・T2 と新千歳の国内線を「行った」（3／14）
TGOT = {('HND', 'T1'): 12, ('HND', 'T2'): 9, ('CTS', '国内'): 4}

V3 = """
.ap .cd .tg{font-size:16px;color:var(--sub);margin-left:3px}
.ap.no .cd .tg{color:var(--mute)}
.sec-h.t{margin-top:16px}
"""

def tcell(code, tag, nm, short_, night=False):
    c = RC[TREG[code]]
    g = TGOT.get((code, tag))
    top = '<span class="cd">%s<span class="tg">%s</span></span><span class="nm">%s %s</span>' % (code, tag, short_, nm)
    if g:
        return '<a class="ap got" href="#" style="--c:%s">%s<span class="ft">%s<span><b>%d</b><span class="u">回</span></span></span></a>' % (c, top, stamp2(True, night, 30 if night else 26), g)
    return '<div class="ap no" style="--c:%s">%s<span class="ft">%s<span>まだ</span></span></div>' % (c, top, stamp2(False, night))

def terms_of(r, night=False):
    s = ''
    for code, sh, L in TERMS:
        if TREG[code] != r:
            continue
        got = sum(1 for t, _ in L if TGOT.get((code, t)))
        s += '<div class="sec-h t">%sのターミナル<small>%d / %d</small></div><div class="grid">' % (sh, got, len(L))
        s += ''.join(tcell(code, t, n, sh, night) for t, n in L) + '</div>'
    return s

def region_block(r, night=False, door_html=None):
    return (door_html or door1(r, night)) + '<div class="grid">' + ''.join(cell2(a, night) for a in byreg(r)) + '</div>' + terms_of(r, night)

def page3(fn, title, body, night=False, extra=''):
    page2(fn, title, body, night, V3 + extra)

# ---------- 02 図鑑の基本（昼・夜）：ターミナルを地方の並びのあとに ----------
def p02v3(night=False):
    b = tsume2('北海道') + '<div class="wrap">' + header(night) + '<div class="main">' + titlerow2() + vband2() + hero2(night)
    b += region_block('北海道', night) + door1('東北', night) + '<div class="grid">' + ''.join(cell2(a, night) for a in byreg('東北')[:3]) + '</div>'
    if night:
        b += ann('02 の夜（3版）', ['2版の夜の形のまま。新千歳のターミナル（国内線・国際線）を北海道の並びのあとに足した',
                                   '行った枠は少し明るい地と細い縁、✓ は緑で 30px'])
    else:
        b += ann('02 図鑑の基本（3版）', ['ターミナルは本番と同じ6空港14こ。それぞれの地方の並びのあとに「新千歳のターミナル 1/2」の形で置く（北海道＝新千歳、関東＝羽田・成田、中部＝中部、近畿＝関西、九州＝福岡）',
                                       'ターミナルは「集めた空港 16/86」にも9地方の数にも入れない（今の本番と同じ数え方）',
                                       'そのほかは2版のまま（9地方の数は見るだけ・扉は1行・枠104・667 で1段目が見える）'])
    b += '</div></div>' + tabs()
    page3('02-zukan-base%s-v3.html' % ('-night' if night else ''), '図鑑の基本 3版' + ('（夜）' if night else ''), b, night)

# ---------- 02z はじめての人（0／86） ----------
EX0 = ('.hero0 .msg{margin-top:6px;font-size:15px;font-weight:700;color:#fff;line-height:1.55}'
       '.hero0 .near{margin-top:8px;display:flex;align-items:center;gap:10px;height:44px;border-radius:999px;background:rgba(255,255,255,.12);padding:0 8px 0 16px;color:#fff;text-decoration:none}'
       '.hero0 .near small{font-size:13px;color:#C9D2DE;font-weight:700}.hero0 .near b{font-size:15px}.hero0 .near .cd{font-family:var(--sign);font-size:18px;font-weight:700;letter-spacing:.02em}'
       '.hero0 .near .km{margin-left:auto;font-family:var(--sign);font-size:18px;font-weight:700}.hero0 .near .km .u{color:#C9D2DE}'
       '.hero0 .near .go{width:32px;height:32px;border-radius:50%;background:#fff;color:var(--navy);display:flex;align-items:center;justify-content:center;font-weight:800}')

def p02zero():
    keep = dict(GOT); GOT.clear(); keepT = dict(TGOT); TGOT.clear()
    b = tsume2('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2()
    b += ('<section class="hero2 hero0"><div class="ht"><span class="lab">集めた空港</span><span><span class="num">0</span><span class="u">/ 86</span></span>'
          '<span class="side">9地方・86空港</span></div>'
          '<div class="msg">空港でチェックインすると、ここに印が付きます</div>'
          '<a class="near" href="03-airport-grid-v3.html"><small>いちばん近い</small><b>羽田</b><span class="cd">HND</span><span class="km">12<span class="u">km</span></span><span class="go" aria-hidden="true">›</span></a></section>')
    b += region_block('北海道') + door1('東北') + '<div class="grid">' + ''.join(cell2(a) for a in byreg('東北')[:3]) + '</div>'
    b += ann('02 はじめての人（0／86）', ['集めた空港のカードの中に「空港でチェックインすると、ここに印が付きます」の1行。カードの高さは 16 の人とほぼ同じ（9地方の数の代わりに入れる）',
                                        '9地方の数は全部 0 なので出さない。1つ目の印が付いたら 02 の形（9地方の数）に変わる',
                                        '「いちばん近い 羽田 HND 12km ›」を押すと、その空港の地方（関東）へ飛ぶ。位置を許していない人には出さない（1行の文だけ）',
                                        '枠は86こ全部「まだ」の薄い地。667 でも1段目が全部見える'])
    b += '</div></div>' + tabs()
    page3('02z-first-v3.html', 'はじめての人の図鑑（0／86）', b, extra=EX0)
    GOT.update(keep); TGOT.update(keepT)

# ---------- 02c 送って東北に入ったところ：扉が上に止まって見出しになる ----------
def p02cv3():
    ex = ('.door1.pin{position:sticky;top:0;z-index:15;margin-top:0;border-radius:0 0 18px 18px;box-shadow:0 10px 22px -16px rgba(17,24,39,.45)}'
          '.pinwrap{margin:0 -16px 0 -16px;padding:0 16px}')
    b = tsume2('東北') + '<div class="wrap" style="padding-top:0"><div class="main">'
    g, n = regcount('東北')
    b += ('<section class="card door1 pin" id="東北" style="--c:%s"><h2>東北</h2><span><span class="num">%d</span><span class="u">/ %d</span></span>'
          '<span class="bar"><i style="width:%d%%"></i></span></section>') % (RC['東北'], g, n, round(g / n * 100))
    b += '<div class="grid">' + ''.join(cell2(a) for a in byreg('東北')) + '</div>'
    b += region_block('関東')
    b += ann('02c 送って東北に入ったところ（3版）', ['扉そのものが上まで来たら、そこで止まって見出しになる（別の見出しは置かない。「東北 1/9」は1回だけ）',
                                               '絵は「東北の扉が上に止まり、その下に青森から並ぶ」瞬間。次の関東の扉が下から来て東北の扉に当たったら、押し上げて入れ替わる',
                                               'ツメの飛び出しは、上に止まっている扉の地方。入れ替わった瞬間に「関東」へ移る（切り替えの瞬間は1つだけ）',
                                               'ツメを押したときは、その地方の扉が上に止まる所まで飛ぶ'])
    b += '</div></div>' + tabs()
    page3('02c-scroll-v3.html', '送って東北に入ったところ 3版', b, extra=ex)

# ---------- 02d 行った順 ----------
VISITS = [('2026年10月25日', ['ISG', 'MMY']), ('2026年10月24日', ['OKA']), ('2026年9月13日', ['KOJ', 'KMJ']),
          ('2026年8月9日', ['NGS']), ('2026年7月20日', ['MYJ', 'HIJ']), ('2026年5月24日', ['AKJ']),
          ('2026年5月23日', ['CTS', 'HKD']), ('2026年4月5日', ['SDJ']), ('2026年3月1日', ['ITM', 'NGO']),
          ('2026年1月12日', ['FUK']), ('2025年12月14日', ['HND'])]

def p02d():
    ex = '.main.full{margin-right:0}.dh{display:flex;align-items:baseline;gap:8px;margin:18px 2px 0;font-size:15px;font-weight:800;color:var(--strong)}.dh small{font-size:13px;color:var(--sub);font-weight:600}'
    byc = {a['code']: a for a in A}
    assert sum(len(c) for _, c in VISITS) == 16
    b = '<div class="wrap">' + header() + '<div class="main full">' + titlerow2() + vband2('行った順')
    b += '<div class="note">はじめて押した日の順。新しい日が上です。</div>'
    for d, cs in VISITS:
        b += '<div class="dh">%s<small>%d空港</small></div><div class="grid">' % (d, len(cs))
        b += ''.join(cell2(byc[c]) for c in cs) + '</div>'
    b += ann('02d 行った順（年代記の新しい名前）', ['行った空港だけを、はじめて押した日の見出しごとに並べる。まだの空港は出さない',
                                             '枠は地方別と同じ（高さ104・コード→名前→✓ と回数）。枠の上の細い色の帯で地方が分かる',
                                             '日付は「2026年11月1日」の書き方。同じ日に2つ以上なら1つの見出しにまとめる',
                                             '地方で飛ぶ意味がないので、行った順ではツメを出さない（枠は画面の幅いっぱい）',
                                             'ターミナルは入れない（数に入らないため）。地図は今の本番の地図と同じなので描いていない'])
    b += '</div></div>' + tabs()
    page3('02d-visited-v3.html', '行った順', b, extra=ex)

# ---------- 03 関東へ飛んだところ：ターミナル 羽田 2/3・成田 0/3 ----------
def p03v3():
    r = '関東'
    L = byreg(r); g = sum(1 for a in L if GOT.get(a['code']))
    dh = ('<section class="card door" id="%s" style="--c:%s"><div class="tx"><h2>%s</h2><div class="cnt"><span class="num">%d</span><span class="u">/ %d 空港</span></div>'
          '<div class="bar"><i style="width:%d%%"></i></div><div class="ds">最後に押した：羽田　2026年11月1日</div></div>%s</section>') % (r, RC[r], r, g, len(L), round(g / len(L) * 100), minimap(r))
    b = tsume2(r) + '<div class="wrap"><div class="main">'
    b += '<div class="stick" style="--c:%s"><span class="dot"></span><b>関東</b><small>%d / %d</small><a class="pill" href="02-zukan-base-v3.html">図鑑の上へ</a></div>' % (RC[r], g, len(L))
    b += region_block(r, door_html=dh)
    b += ann('03 関東へ飛んだところ（3版）', ['羽田のターミナル 2/3（第1・第2 を行った）、成田のターミナル 0/3。数え方は今の本番と同じ',
                                        '扉の日付は「2026年11月1日」の書き方にそろえた',
                                        'そのほかは2版のまま（飛んだときだけ扉に小さな地図・コードなしは名前1回）'])
    b += '</div></div>' + tabs()
    page3('03-airport-grid-v3.html', '空港の並び 3版', b, extra='.door .bar{height:5px}')

# ---------- 04 羽田：開港・滑走路は出さない形（11/9 本人の決定）・はらうのは上のカードだけ ----------
def p04v3():
    c = RC['関東']
    ex = EX04 + ('.swz{position:relative}.swz .edge{position:absolute;top:0;bottom:0;width:20px;background:repeating-linear-gradient(45deg,rgba(194,96,58,.10) 0 4px,transparent 4px 8px);border-radius:4px}'
                 '.swz .edge.l{left:-16px}.swz .edge.r{right:-16px}'
                 '.hint{display:flex;justify-content:center;margin-top:8px}.hint span{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:700;color:var(--ink)}'
                 '.dots{margin-top:8px}')
    L = byreg('関東'); i = [a['code'] for a in L].index('HND')
    dots = ''.join('<i class="%s"></i>' % ('on' if j == i else '') for j in range(len(L)))
    b = '<div class="wrap" style="--c:%s"><div class="top"><a class="pill" href="03-airport-grid-v3.html">‹ 関東</a><a class="pill" href="08-kigou-v3.html">記号の意味</a></div>' % c
    b += '<div class="swz"><span class="edge l"></span><span class="edge r"></span>' + idcard().replace('2025.12.14', '2025.12.14') + '</div>'
    b += '<div class="dots" aria-label="関東の%d番目">%s</div>' % (i + 1, dots)
    b += '<div class="hint"><span>‹ 印のカードをはらうと、となりの空港へ ›</span></div>'
    b += ('<div class="dl"><div><div class="k">押した回数</div><div class="v"><span class="num">28</span><span class="u">回</span></div></div>'
          '<div><div class="k">はじめて押した日</div><div class="v s"><span class="num">2025</span><span class="u">年</span><span class="num">12</span><span class="u">月</span><span class="num">14</span><span class="u">日</span></div></div></div>')
    b += rec()
    def lab(a): return short(a) + ('' if a['code'] == '—' else ' <span class="cd">%s</span>' % a['code'])
    b += '<div class="turn"><a class="pill" href="#">‹ <span>%s</span></a><a class="pill" href="#"><span>%s</span> ›</a></div>' % (lab(L[i - 1]), lab(L[i + 1]))
    b += ann('04 羽田（3版）', ['開港・滑走路と大きさ比べは、出典と利用条件が決まるまで出さない（11/9 本人の決定）。データ欄は「押した回数」「はじめて押した日」の2つ。表ができたら 04-v2 の形に足す',
                              'はらって隣の空港へ移れるのは、上の印のカード（HND のカード）だけ。画面の左右の端 20px（斜線の所、本番では見えない）ははらいを受けない（Safari の戻る動きとぶつけない）',
                              '「印のカードをはらうと…」の札は、はじめて開いたときの1回だけ。2回目からは点と下の ‹ › だけ',
                              '点は印のカードのすぐ下に移した（はらえる所の目印）',
                              '日付は「2025年12月14日」の書き方。印の絵の中だけは今の本番の印の書き方（2025.12.14）'])
    b += '</div>' + tabs()
    page3('04-airport-v3.html', '1空港の詳しい所 3版（羽田）', b, extra=ex)

# ---------- 06 ほかの図鑑・実績：86 の数に入らないことを1回はっきり ----------
def p06v3():
    ex = ('.bk{margin-top:8px;padding:12px 14px;display:flex;gap:14px;align-items:center;text-decoration:none;color:inherit;min-height:76px}'
          '.bk .sp{width:42px;height:54px;border-radius:8px 12px 12px 8px;flex:none;background:var(--wash);box-shadow:inset 4px 0 0 var(--b),inset 0 0 0 1px #E3E6EB;display:flex;align-items:center;justify-content:center}'
          '.bk .sp svg{width:22px;height:22px;fill:none;stroke:var(--sub);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}'
          '.bk .tx{flex:1;min-width:0}.bk b{display:block;font-size:16px;color:var(--strong);line-height:1.35}.bk small{display:block;font-size:13px;color:var(--sub);line-height:1.45;margin-top:2px}'
          '.bk .n{text-align:right;flex:none}.bk .n .num{font-size:24px}'
          '.base{margin-top:14px;padding:12px 16px;background:var(--wash);border-radius:18px;box-shadow:inset 0 0 0 1px #E3E6EB}'
          '.base .r{display:flex;align-items:center;gap:12px;min-height:30px}.base b{font-size:15px;color:var(--strong)}.base small{font-size:13px;color:var(--sub)}'
          '.base .r .num{margin-left:auto;font-size:22px}.base .r.s .num{font-size:18px}.base p{margin:6px 0 0;font-size:13px;color:var(--sub);line-height:1.6}')
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base-v3.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:4px"><h1 style="font-size:24px">ほかの図鑑・実績</h1></div>'
    b += '<div class="note" style="margin-top:4px">ここで集めても「集めた空港」の数は変わりません。</div>'
    books = [('#6B3FA0', '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>', '実績', '空港の印や回数・路線・距離で達成するもの', 21, 522),
             ('#3D7A4E', '<path d="M3 17h18M6 17l3-8h6l3 8M12 9V5"/>', '飛行場・滑空場', '定期便のない飛行場とグライダーの滑空場', 0, 63),
             ('#2B4A73', '<path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7z"/>', '番外編', '自衛隊の飛行場と、一般の人が行けない飛行場', 0, 32),
             ('#8A6A1F', '<path d="M10.5 13.5 4 11l1.5-1.5 7 1 3.5-3.5c1-1 2.5-1.2 3-.5s.5 2-.5 3L15 13l1 7-1.5 1.5-2.5-6.5-3 3v2.5L7.5 22 6 18l-4-1.5L3.5 15H6z"/>', '機体図鑑（特別塗装機）', '乗った・見た特別塗装機', 0, 93)]
    for col, ic, t, d, g, n in books:
        b += '<a class="card bk" href="#" style="--b:%s"><span class="sp"><svg viewBox="0 0 24 24">%s</svg></span><span class="tx"><b>%s</b><small>%s</small></span><span class="n"><span class="num">%d</span><span class="u">/ %d</span></span></a>' % (col, ic, t, d, g, n)
    b += ('<div class="base"><div class="r"><b>空港の図鑑</b><span class="num">16<span class="u">/ 86</span></span></div>'
          '<div class="r s"><small>ターミナル</small><span class="num">3<span class="u">/ 14</span></span></div>'
          '<p>国内86空港。大きな6空港はターミナルにも印があります（86 の数には入りません）。</p></div>')
    b += ann('06 ほかの図鑑・実績（3版）', ['空港の図鑑のカードに「ターミナル 3/14」を別の行で出し、「86 の数には入りません」を1回だけはっきり書いた',
                                         '上の説明は1回だけ（「ここで集めても…」）。2版の「空港の図鑑（86）とは別に数えます」は同じ意味なので外した',
                                         'そのほかは2版のまま（実績が上・薄い背表紙・667 で4冊）'])
    b += '</div>' + tabs()
    page3('06-others-v3.html', 'ほかの図鑑・実績 3版', b, extra=ex)

# ---------- 07b 今の人へのお知らせ：閉じるは1つ・2行 ----------
def p07bv3():
    ex = ('.notice{margin-top:10px;padding:14px 16px 12px}.notice b{display:block;font-size:15px;color:var(--strong)}'
          '.notice p{margin:4px 0 0;font-size:13px;color:var(--ink);line-height:1.65}.notice .ok{display:flex;justify-content:flex-end;margin-top:6px}')
    b = tsume2('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow2() + vband2()
    b += ('<section class="card notice"><b>図鑑の見方を3つにまとめました</b>'
          '<p>タイル・地方は「地方別」に、年代記は「行った順」に。案内標は空港を開いて ‹ › で。</p>'
          '<div class="ok"><span class="pill">わかった</span></div></section>')
    b += hero2() + region_block('北海道')
    b += ann('07b 今使っている人へ1回だけのお知らせ（3版）', ['閉じるのは「わかった」1つだけ（右上の ✕ をなくした）',
                                                     '説明は2行。今の5つの見方を使ったことのある人が、次に図鑑を開いたときだけ出す',
                                                     '出ている間は 844 で1段目の枠が少し隠れる。1回だけなので受け入れる（閉じると 02 と同じ位置）'])
    b += '</div></div>' + tabs()
    page3('07b-notice-v3.html', '今の人へのお知らせ 3版', b, extra=ex)

# ---------- 08 記号の意味（昼・夜）：空港コード・ターミナルの数え方 ----------
def p08v3(night=False):
    ex = '.lg{margin-top:12px;padding:6px 0}.lg .row{min-height:64px}.lg .ic{width:52px;display:flex;justify-content:center;align-items:center;gap:4px;flex:none}'
    b = '<div class="wrap"><div class="top"><a class="pill" href="04-airport-v3.html">‹ 戻る</a></div><div class="ttl" style="margin-top:4px"><h1>記号の意味</h1></div>'
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
    b += '<div class="row"><span class="ic"><span class="num" style="font-size:18px">T1</span></span><div class="tx"><b>ターミナル（T1・国内など）</b><small>地方の並びのあとに。86 の数には入りません</small></div></div>'
    b += ('</section><div class="note">この図鑑は国内の86空港です。大きな6空港（新千歳・羽田・成田・中部・関西・福岡）はターミナルにも印があります（86 の数には入りません）。'
          '飛行場・番外編・特別塗装機・実績は「ほかの図鑑・実績」にあります。</div>')
    if night:
        b += ann('08 の夜（3版）', ['夜は地方の色を使わないので「色の帯 … 地方」の行を出さない', '「空港コード（HND など）」「ターミナル」の行を昼と同じに'])
    else:
        b += ann('08 記号の意味（3版）', ['「3レターコード」を「空港コード（HND など）」に',
                                         'ターミナルの行を足し、下の文に「6空港」と「86 の数には入りません」を書いた（06 と同じ言い方）'])
    b += '</div>' + tabs()
    page3('08-kigou%s-v3.html' % ('-night' if night else ''), '記号の意味 3版' + ('（夜）' if night else ''), b, night, ex)

for f in (p02zero, p02cv3, p02d, p03v3, p04v3, p06v3, p07bv3):
    f()
p02v3(False); p02v3(True); p08v3(False); p08v3(True)

# 3版どうしのつなぎ（2版の名前で書いてある所を3版へ）
V3FILES = {'02-zukan-base', '02c-scroll', '03-airport-grid', '04-airport', '06-others', '07b-notice', '08-kigou'}
for fn in os.listdir(OUT):
    if not fn.endswith('-v3.html'):
        continue
    p = os.path.join(OUT, fn); s = open(p, encoding='utf-8').read()
    for k in V3FILES:
        s = s.replace('href="%s-v2.html"' % k, 'href="%s-v3.html"' % k)
    open(p, 'w', encoding='utf-8').write(s)
print('ok')
