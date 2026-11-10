# -*- coding: utf-8 -*-
# フライトの4版（PM の指示 11/10 20時・改善担当 review-3）。使い方：python3 make_flight_v4.py <出力先>
# 1. 券の下の行を2行に（1行目 機種・登録記号・座席／2行目 そらメモ（非公式アプリ）・関係ありません）。いちばん長い機種名の1枚を足す
# 2. 日誌は年をまたいで1本につながる形にそろえる。A1p の文は「年を選ぶとその年の頭へ飛ぶ（地図と年のまとめは年ごと）」、「2024年へ」は2025年の終わりへ
# 3. 「航路なし／車など／ほかの移動」は画面では「車など」の1つに（本人の答え待ちの案）
# 4. 見本の旅程（8/12 は宮崎→羽田）・年の切り替えを日誌と年のまとめで同じ場所に・空の上は「45時間21分」でそろえる
# 3版の部品（make_flight_v3.py）を読み込んで使う。3版の画面は作業用の場所に書き出して捨てる
import sys, os, datetime, tempfile, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = sys.argv[1]
_tmp = tempfile.mkdtemp()
sys.argv = [sys.argv[0], _tmp]
with contextlib.redirect_stdout(io.StringIO()):
    import make_flight_v3 as V3
from common import *
V = V3.V
T = '｜フライトの4版（画面案）'
header, lrow, hm2, MON, ann = V.header, V.lrow, V.hm2, V.MON, V.ann
ysw, mblock, M25, Y25 = V3.ysw, V3.mblock, V3.M25, V3.Y25
CAR = '車など'   # 画面に出す名前（本人の答え待ち）。作る人の言葉は「航路なし」

CSS4 = V3.CSS3 + """
.y1 .num{font-size:26px}
.y1{justify-content:space-between;padding:2px 10px 0}
.y1 > span > .u:first-child{margin-right:4px}
.gap{display:flex;align-items:center;justify-content:center;gap:8px;margin:18px 0 0;font-size:13px;color:var(--sub);font-weight:700}
.gap i{display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--pale)}
"""

def ycard(y=2026, n=None, km_=None, mins=None, extra=''):
    n = len(F) if n is None else n; km_ = TOTAL_KM if km_ is None else km_; mins = TOTAL_MIN if mins is None else mins
    return ('<div class="card yc">%s<div class="y1"><span><span class="num">%d</span><span class="u">便</span></span><span><span class="num">%s</span><span class="u">km</span></span>'
            '<span><span class="u">空の上</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></span></div>%s</div>') % (
        ysw(y, True, y < 2026), n, c(km_), mins // 60, mins % 60, extra)

# ---------- A1 日誌 ----------
def pA1():
    body = '<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(4) + ann('A1 日誌（4版）', [
        '空の上は「45時間21分」。年のまとめ（A3）と同じ数・同じ書き方にした（review-3 の5）',
        '年の切り替え（‹ 2026年 ›）は数字のカードの上の段。年のまとめも同じ場所・同じ幅（review-3 の4）',
        '日誌は年をまたいで1本につながる（A1y）。年を選ぶと、その年の頭へ飛ぶ（A1p）']) + '</div>' + tabs('フライト')
    page(OUT + '/A1-log-v4.html', 'A1 日誌' + T, body, extra_css=CSS4)

# ---------- A1y 年をまたぐ所と2025年の終わり ----------
def pA1y():
    m26 = sorted(MON)[:2]   # 2026年の 1月・2月
    s = '<div class="wrap"><div class="stk">%s</div>' % ysw(2026, True, False)
    s += '<p class="note" style="margin:10px 4px 0">（日誌を下へ送ったところ。上の年は、下の「2025年」の帯を過ぎると 2025年に変わる）</p>'
    for m in reversed(m26):
        s += mblock(m, MON[m])
    s += '<div class="yd"><b>2025年</b><small>%d便・%s km</small><span class="r">まとめ ›</span></div>' % (Y25['n'], c(Y25['km']))
    for m in sorted(M25, reverse=True):
        s += mblock(m, M25[m], 2025)
    s += '<div class="gap"><i></i><i></i><i></i>10月〜2月は続けて出ます<i></i><i></i><i></i></div>'
    # 2025年の終わり（1月の便のあと）
    jan = [dict(m=1, d=18, wd=WD[datetime.date(2025, 1, 18).weekday()], a='FUK', b='HND', co='ANA', no='NH256', dep='17:00', mins=95, km=round(km('FUK', 'HND'))),
           dict(m=1, d=16, wd=WD[datetime.date(2025, 1, 16).weekday()], a='HND', b='FUK', co='ANA', no='NH241', dep='07:25', mins=115, km=round(km('HND', 'FUK')))]
    s += mblock(1, jan, 2025)
    s += ('<div class="more"><p class="note">2025年の便はここまで</p><span class="pill">2024年へ（12便）</span></div>')
    s += ann('A1y 年をまたぐ所（4版）', [
        '日誌は年をまたいで1本につながる。年が変わる所に「2025年」の帯（便の数と距離・押すと年のまとめ）、月の見出しにも小さく年',
        '上の年は、送ると見ている所の年に変わり、画面の上に残る',
        '「2024年へ」はその年の最後（1月の便のあと）だけに置く。押すと続けて 2024年の12月から出る（記録がない年は出さない）。年の途中には置かない（review-3 の2）',
        '2025年の便は見本（年の合計の数も見本）']) + '</div>' + tabs('フライト')
    page(OUT + '/A1y-log-years-v4.html', 'A1y 年をまたぐ所' + T, s, extra_css=CSS4)

# ---------- A1p 年を選ぶ ----------
def pA1p():
    yrs = [(2026, len(F), TOTAL_KM), (2025, Y25['n'], Y25['km']), (2024, 12, 9860), (2023, 4, 3120)]
    rows = ''.join('<div class="row"><div class="tx"><b>%d年</b><small>%d便・%s km</small></div>%s</div>' % (
        y, n, c(k), '<span class="tg" style="display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:800;background:#16233A;color:#fff">見ている年</span>' if y == 2026 else '<span style="color:var(--pale);font-weight:700">›</span>') for y, n, k in yrs)
    body = ('<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(1) + '</div><div class="dim"></div><div class="sheet"><div class="grab"></div>'
            '<div style="font-size:18px;font-weight:800;color:var(--strong);margin:0 4px 8px">年を選ぶ</div><div class="card lst">%s</div>'
            '<p class="note">記録のある年だけ出ます。<br>日誌：その年の頭（いちばん新しい便）へ飛びます。前後の年の便も続けて見られます。<br>地図と年のまとめ：選んだ年だけになります。</p></div>') % rows + tabs('フライト')
    page(OUT + '/A1p-year-pick-v4.html', 'A1p 年を選ぶ' + T, body, extra_css=CSS4 + '.lst .row + .row{box-shadow:inset 0 1px 0 var(--line2)}')

# ---------- A2s 共有：券の下を2行に ----------
SHARE_CSS = CSS4 + """
.bp{margin:6px 0 0;border-radius:22px;background:#16233A;color:#fff;overflow:hidden;position:relative}
.bp .tp{display:flex;justify-content:space-between;align-items:center;padding:14px 18px 0;font-size:13px;font-weight:700;color:#C9D2DE}
.bp .rt{display:flex;align-items:center;justify-content:space-between;padding:6px 18px 0}
.bp .rt .num{color:#fff;font-size:48px}.bp .rt small{display:block;font-size:14px;color:#C9D2DE;font-weight:700;margin-top:4px}
.bp .rt svg{color:#7F8DA1;width:26px;height:26px}
.bp .gr{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:14px 18px 16px}
.bp .gr .k{font-size:13px;color:#AEB9C7;font-weight:700}.bp .gr .num{color:#fff;font-size:22px}.bp .gr .u{color:#AEB9C7}
.bp .ft{padding:12px 18px 12px;background:#1F2E48;position:relative}
.bp .ft::before,.bp .ft::after{content:"";position:absolute;top:-9px;width:18px;height:18px;border-radius:50%;background:var(--card)}
.bp .ft::before{left:-9px}.bp .ft::after{right:-9px}
.bp .ft .l1{font-size:15px;color:#fff;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:clip}
.bp .ft .l2{margin-top:6px;font-size:14px;color:#C9D2DE;font-weight:700;white-space:nowrap}
.bp .ft .l3{margin-top:2px;font-size:13px;color:#AEB9C7;font-weight:600;white-space:nowrap}
.bp .acc{position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--jal)}
.bp .acc.ana{background:var(--ana)}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px}.btns .btn{margin-top:12px}
.swr{display:flex;align-items:center;gap:12px;min-height:52px;padding:2px 2px}.swr + .swr{box-shadow:inset 0 1px 0 var(--line2)}
.swr .tx{flex:1}.swr .tx b{display:block;font-size:15px;color:var(--strong)}.swr .tx small{display:block;font-size:13px;color:var(--sub)}
"""
def share_page(fn, ttl, f, seat_on, notes):
    behind = '''<div class="wrap" aria-hidden="true"><div style="display:flex;align-items:center;gap:8px;height:60px"><span class="pill">%s フライト</span><span style="margin-left:auto" class="pill">%s 画像で共有</span><span class="pill ic">%s</span></div>
<div class="card" style="height:220px"></div></div>''' % (I['back'], I['share'], I['pen'])
    seat = '・%s席' % f['seat'] if seat_on else ''
    sheet = '''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div style="display:flex;align-items:baseline;gap:8px;margin:0 2px 6px"><b style="font-size:18px;color:var(--strong)">画像で共有</b><span style="margin-left:auto;font-size:13px;color:var(--sub)">会社のロゴは入りません</span></div>
<div class="bp"><span class="acc%s"></span><div class="tp"><span>2026.%d.%d（%s）</span><span>%s・%s</span></div>
<div class="rt"><div><span class="num">%s</span><small>%s</small></div>%s<div style="text-align:right"><span class="num">%s</span><small>%s</small></div></div>
<div class="gr"><div><div class="k">出発</div><span class="num">%s</span></div><div><div class="k">空の上</div>%s</div><div><div class="k">距離</div><span class="num">%s</span><span class="u">km</span></div></div>
<div class="ft"><div class="l1 clipchk">%s・%s%s</div><div class="l2 clipchk"><b>そらメモ（非公式アプリ）</b></div><div class="l3 clipchk">各航空会社とは関係ありません</div></div></div>
<div style="margin-top:8px"><div class="swr"><div class="tx"><b>登録記号を出す</b><small>%s</small></div><span class="sw on">ON</span></div>
<div class="swr"><div class="tx"><b>座席を出す</b><small>%s</small></div><span class="sw %s">%s</span></div></div>
<div class="btns"><span class="btn w">閉じる</span><span class="btn">共有する</span></div></div>''' % (
        ' ana' if f['co'] == 'ANA' else '', f['m'], f['d'], f['wd'], f['co'], f['no'], f['a'], short(f['a']), I['arrow'], f['b'], short(f['b']), f['dep'], hm2(f['mins']), c(f['km']),
        f['typ'], f['reg'], seat, 'OFF にすると機種だけ', ('%s席が入ります' % f['seat']) if seat_on else ('ON にすると %s席が入ります' % f['seat']), 'on' if seat_on else 'off', 'ON' if seat_on else 'OFF')
    body = behind + sheet + ann(ttl, notes) + tabs('フライト')
    page(OUT + '/' + fn + '.html', ttl + T, body, extra_css=SHARE_CSS)

def pA2s():
    share_page('A2s-share-v4', 'A2s 画像で共有（4版）', F[0], False, [
        '券の下を2行に分けた：1行目 機種・登録記号（・座席）、2行目 そらメモ（非公式アプリ）。「各航空会社とは関係ありません」はその下に添える（1行に並べると幅390で入らないため）（review-3 の1）',
        '登録記号ははじめ ON・座席ははじめ OFF（11/10 本人の決定どおり）'])
    share_page('A2s2-share-seat-on-v4', 'A2s2 座席を ON にしたところ（4版）', F[0], True, [
        '座席を ON にすると1行目の終わりに「・25K席」が入る。2行目は変わらない'])
    # いちばん長い機種名と3けたの座席（見本：国内線でいちばん長い名前の B777-300ER・羽田→那覇）
    d = datetime.date(2026, 11, 7)
    g = dict(m=11, d=7, wd=WD[d.weekday()], a='HND', b='OKA', co='ANA', no='NH471', typ='B777-300ER', reg='JA751A', dep='08:05', mins=165, km=round(km('HND', 'OKA')), seat='103K')
    share_page('A2s3-share-long-v4', 'A2s3 いちばん長い機種名（4版）', g, True, [
        'いちばん長い機種名（B777-300ER・JA751A）と3けたの座席（103K）でも、1行目は1行に収まり「そらメモ（非公式アプリ）」は折れない（幅390で測った）',
        'アプリでは1行目がはみ出すときは字を小さくせず、座席→登録記号の順に外して出す（2行目はいつも全部出す）',
        '見本の便（11/7 NH471）は券の長さを確かめるための作り物で、日誌の26便には入れていない'])

# ---------- A3 年のまとめ（年の切り替えを日誌と同じ場所に） ----------
def pA3():
    cnt = [len(MON.get(m, [])) for m in range(1, 13)]
    kms = [sum(f['km'] for f in MON.get(m, [])) for m in range(1, 13)]
    mx = max(cnt)
    bars = ''
    for m in range(1, 13):
        h = cnt[m - 1] * 110 // mx if cnt[m - 1] else 3
        bars += '<div class="b"><span class="v">%s</span><i style="height:%dpx"%s></i><span class="l">%d</span></div>' % (cnt[m - 1] or '', h, '' if cnt[m - 1] else ' class="z"', m)
    co = {}
    for f in F: k2 = 'JAL' if f['co'] == 'JTA' else f['co']; co[k2] = co.get(k2, 0) + 1
    big = max(range(12), key=lambda i: kms[i])
    css = CSS4 + """.sum{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.sum > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px}
.sum .k{font-size:13px;color:var(--sub);font-weight:700;display:block;margin-bottom:4px}.sum .num{font-size:30px}
.bars{display:flex;gap:4px;align-items:flex-end;height:160px;padding:14px 14px 10px}.bars .b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bars i{width:100%;background:var(--navy);border-radius:4px 4px 2px 2px}.bars i.z{background:var(--line2)}.bars .v{font-family:var(--sign);font-weight:700;font-size:14px;color:var(--strong);margin-bottom:3px}.bars .l{font-size:13px;color:var(--mute);margin-top:4px}
.cobar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:6px 16px 4px}.cobar i{display:block}
.colg{display:flex;gap:16px;padding:6px 16px 14px;font-size:13px;color:var(--sub)}.colg b{font-family:var(--sign);font-size:18px;color:var(--strong);margin-left:4px}
.shr{display:flex;justify-content:flex-end;margin-top:8px}"""
    body = ('<div class="wrap">' + header() + V.titlerow('yr') +
            '<div class="card yc">%s</div>'
            '<div class="sum"><div><span class="k">便</span><span class="num">%d</span><span class="u">便</span></div><div><span class="k">路線</span><span class="num">%d</span><span class="u">路線（往復で1つ）</span></div>'
            '<div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">空の上</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></div></div>'
            '<div class="shr"><span class="pill">%s この年を画像で共有</span></div>'
            '<div class="sec-h">月ごとの便の数</div><div class="card"><div class="bars">%s</div>'
            '<p class="note" style="margin:0 16px 14px">距離がいちばん長かった月：%d月（%s km）</p></div>'
            '<div class="sec-h">よく乗った路線<span class="r">地図で見る ›</span></div><div class="card">%s</div>'
            '<div class="sec-h">会社</div><div class="card" style="padding-top:12px"><div class="cobar"><i style="flex:%d;background:var(--jal)"></i><i style="flex:%d;background:var(--ana)"></i></div><div class="colg"><span>JAL グループ<b>%d</b></span><span>ANA<b>%d</b></span></div></div>'
            ) % (ysw(2026, True, False), len(F), len(V.RT), c(TOTAL_KM), TOTAL_MIN // 60, TOTAL_MIN % 60, I['share'], bars, big + 1, c(kms[big]), V.route_rows(3), co.get('JAL', 0), co.get('ANA', 0), co.get('JAL', 0), co.get('ANA', 0)) + ann('A3 年のまとめ（4版）', [
                '年の切り替えを日誌（A1）と同じ場所・同じ幅のカードにした。日誌⇄年のまとめを切り替えても年の字が動かない（review-3 の4）',
                '「画像で共有」は4つの数の下の右に「この年を画像で共有」として下げた',
                '空の上は日誌と同じ「45時間21分」']) + '</div>' + tabs('フライト')
    page(OUT + '/A3-year-v4.html', 'A3 年のまとめ' + T, body, extra_css=css)

# ---------- R1 車などの移動の行と数え方（名前を1つに・旅程を直す） ----------
def pR1():
    car = dict(m=8, d=11, a='KOJ', b='KMI', km=round(km('KOJ', 'KMI')))
    o10, o12 = MON[8][1], MON[8][0]   # 8/10 HND→KOJ, 8/12 KOJ→HND（新しい順）
    n12 = dict(o12, a='KMI', b='HND', no='NH612', dep='19:40', mins=95, km=round(km('KMI', 'HND')))
    L8 = [n12, o10]
    dkm = n12['km'] - o12['km']; dmin = n12['mins'] - o12['mins']
    tkm, tmin = TOTAL_KM + dkm, TOTAL_MIN + dmin
    def carrow():
        return ('<div class="lr car"><div class="dt"><span class="num">%d</span><small>%s</small></div>'
                '<div style="min-width:0"><div class="rt">%s%s%s</div><div class="sb"><span class="cg">%s</span></div></div>'
                '<div class="tm"><span class="num">%s</span><span class="u">km</span><small>空の上なし</small></div></div>') % (
            car['d'], WD[datetime.date(2026, 8, 11).weekday()], short(car['a']), I['arrow'], short(car['b']), CAR, c(car['km']))
    rows = lrow(L8[0]) + carrow() + lrow(L8[1])
    km8 = sum(f['km'] for f in L8)
    css = CSS4 + """.lr.car::before{display:none}.lr .cg{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;border:1.5px dashed #8A94A3;font-size:13px;font-weight:800;color:var(--ink);margin-right:4px}
.lr.car .rt{color:var(--ink)}
.opt{margin-top:18px}.opt h2{display:flex;align-items:center;gap:8px;font-size:17px;color:var(--strong);margin:0 4px 6px}.opt h2 .tg{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:800;background:#16233A;color:#fff}
.opt h2 .tg.w{background:var(--wash);color:var(--strong)}
.opt .pc{font-size:13px;line-height:1.6;color:var(--ink);margin:8px 4px 0}
.opt .y1 .num{font-size:22px}
.lg2{display:flex;align-items:center;gap:10px;padding:12px 16px;font-size:13px;color:var(--sub)}.lg2 i{display:inline-block;width:40px;border-top:2.5px dashed #16233A}.lg2 i.s{border-top-style:solid}"""
    def y1(n, k, m):
        return ('<div class="y1"><span><span class="num">%d</span><span class="u">便</span></span><span><span class="num">%s</span><span class="u">km</span></span>'
                '<span><span class="u">空の上</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></span></div>') % (n, c(k), m // 60, m % 60)
    def opt(tag, ttl, top, mh, good):
        return ('<div class="opt"><h2><span class="tg%s">%s</span>%s</h2><div class="card yc" style="margin-top:0">%s</div>'
                '<div class="mh"><b>8月</b>%s</div><div class="card lg">%s</div><p class="pc">%s</p></div>') % (
            ' w' if tag == '案1' else '', tag, ttl, top, mh, rows, good)
    top1 = y1(len(F) + 1, tkm + car['km'], tmin)
    top2 = y1(len(F), tkm, tmin) + '<p class="note" style="margin:6px 12px 0;text-align:center">%s 1（%s km）は別に数える</p>' % (CAR, c(car['km']))
    body = ('<div class="wrap"><div class="top" style="height:52px"><b style="font-size:20px;color:var(--strong)">「%s」の移動の数え方</b></div>' % CAR +
            '<p class="note" style="margin:0 4px">見本：8月10日 羽田→鹿児島、11日 鹿児島→宮崎（%s）、12日 宮崎→羽田。日誌の行は2つの案で同じ。違うのは月の見出しと上の数字</p>' % CAR
            + opt('案1', '便に入れる', top1, '<small>3便</small><span class="r">%s km</span>' % c(km8 + car['km']),
                  '良い点：数え方が1つで分かりやすい。困る点：「便」の数が実際に乗った便より多くなる。修行（FOP・回数）には入れない決まりと食い違って見える')
            + opt('案2', '別に数える（おすすめ）', top2, '<small>2便・%s 1</small><span class="r">%s km</span>' % (CAR, c(km8)),
                  '良い点：「便」「空の上」「距離」は乗った便だけで、年のまとめ・修行・地図の数と合う。経営の路線には今のまま数える（決定どおり）。困る点：数字が1つ増える')
            + '<div class="sec-h">地図では</div><div class="card"><div class="lg2"><i class="s"></i>乗った便<i></i>%s（点線）</div>' % CAR +
            '<p class="note" style="margin:0 16px 14px">点線のまま、太さは便と同じ決まり（回数）。年のまとめでは「%s」を4つの枠の下に1行で</p></div>' % CAR
            + ann('R1「%s」の行と数え方（4版）' % CAR, [
                '画面に出す名前を「%s」の1つにした（題・日誌の札・月の見出し・上の数字の下・地図の凡例）。「航路なし」は作る人の言葉としてだけ使う（review-3 の3）。名前は本人の答え待ち（ほかの案は「ほかの移動」）' % CAR,
                '見本の旅程を直した：12日は宮崎→羽田（NH612・1時間35分）。距離と空の上の数もこの便で数え直した（review-3 の6）',
                '日誌の行：左の会社の帯なし・点線の札・右は時間でなく距離（「空の上なし」）。押すと1便の画面の代わりに移動の記録（出発と着いた空港・日付）',
                '経営の路線は決定どおり今のまま数える（この画面は記録の見せ方だけ）']) + '</div>' + tabs('フライト'))
    page(OUT + '/R1-no-route-v4.html', 'R1 車などの移動の数え方' + T, body, extra_css=css)

# ---------- 夜の日誌 ----------
def pN1():
    body = '<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(4) + ann('N1 夜の日誌（4版）', [
        '昼の A1 とそろえた（空の上は「45時間21分」）。光る色は使わない', '会社の色の細い帯は夜は出さない（2版と同じ）']) + '</div>' + tabs('フライト')
    page(OUT + '/N1-log-night-v4.html', 'N1 夜の日誌' + T, body, night=True, extra_css=CSS4 + V.NCSS + '.ysw .pill.ic.dis{color:#2A3542}')

for fn in (pA1, pA1y, pA1p, pA2s, pA3, pR1, pN1): fn()
print('ok', len(F), TOTAL_KM, TOTAL_MIN)
