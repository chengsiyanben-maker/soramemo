# -*- coding: utf-8 -*-
# フライトの3版（PM の指示 11/10 15時30分・改善担当 review-2 の必ず直す3つ）。使い方：python3 make_flight_v3.py <出力先>
# 1. 搭乗券の共有：「登録記号を出す（はじめ ON）」「座席を出す（はじめ OFF）」の2つ・「会社のロゴは入りません」の1行・券の下に「各航空会社とは関係ありません」
# 2. 「航路なし」（車などの移動）の日誌の行と数え方の1枚（便に入れる版と別に数える版を並べる）
# 3. 年の切り替え（‹ 2025｜2026 ›）と年をまたぐ見出し・続きの出方
# 2版の部品（make_flight_v2.py）をそのまま使う。2版の画面は作業用の場所に書き出して捨てる
import sys, os, datetime, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = sys.argv[1]
_tmp = tempfile.mkdtemp()
sys.argv = [sys.argv[0], _tmp]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import make_flight_v2 as V
from common import *
T = '｜フライトの3版（画面案）'
CSS2, header, lrow, hm2, MON, RT, ann = V.CSS2, V.header, V.lrow, V.hm2, V.MON, V.RT, V.ann

CSS3 = CSS2 + """
.yc{margin-top:12px;padding:6px 6px 12px}
.ysw{display:flex;align-items:center;justify-content:space-between}
.ysw .pill.ic{background:transparent;box-shadow:none;color:var(--sub);font-size:22px;font-weight:700}
.ysw .pill.ic.dis{color:var(--line2)}
.ysw b{font-size:18px;color:var(--strong);letter-spacing:.02em}
.ysw b small{font-size:13px;color:var(--sub);font-weight:700;margin-left:6px}
.y1{display:flex;align-items:baseline;justify-content:space-around;padding:2px 8px 0;white-space:nowrap}
.y1 .num{font-size:28px}
.yd{display:flex;align-items:baseline;gap:10px;margin:30px 0 4px;padding:16px 16px;border-radius:20px;background:var(--card);box-shadow:var(--shadow);color:var(--strong)}
.yd b{font-size:26px;letter-spacing:.03em}.yd small{font-size:13px;color:var(--sub);font-weight:700}.yd .r{margin-left:auto;font-size:13px;color:var(--sub);font-weight:700;white-space:nowrap}
.mh .yy{font-size:13px;color:var(--sub);font-weight:700}
.more{display:flex;flex-direction:column;align-items:center;gap:8px;margin:22px 0 0}
.more .note{margin:0;text-align:center}
.stk{position:sticky;top:0;z-index:20;background:var(--bg);margin:0 -16px;padding:6px 16px 6px;box-shadow:0 8px 16px -14px rgba(17,24,39,.4)}
.stk .ysw{background:var(--card);border-radius:999px;box-shadow:var(--shadow);padding:0 4px}
"""

def ysw(y, prev=True, nxt=True):
    return ('<div class="ysw"><span class="pill ic%s" aria-label="前の年">‹</span><b>%d年<small aria-label="年を選ぶ">▾</small></b><span class="pill ic%s" aria-label="次の年">›</span></div>') % (
        '' if prev else ' dis', y, '' if nxt else ' dis')

def ycard(y=2026, n=None, km_=None, h=None):
    n = len(F) if n is None else n; km_ = TOTAL_KM if km_ is None else km_; h = TOTAL_MIN // 60 if h is None else h
    return ('<div class="card yc">%s<div class="y1"><span><span class="num">%d</span><span class="u">便</span></span><span><span class="num">%s</span><span class="u">km</span></span>'
            '<span><span class="u">空の上</span><span class="num">%d</span><span class="u">時間</span></span></div></div>') % (ysw(y, True, y < 2026), n, c(km_), h)

# ---------- 2025年の見本（年をまたぐ所だけ） ----------
F25 = []
def fl25(m, d, a, b, co, no, dep, arr):
    dt = datetime.date(2025, m, d)
    h1, m1 = map(int, dep.split(':')); h2, m2 = map(int, arr.split(':'))
    F25.append(dict(m=m, d=d, wd=WD[dt.weekday()], a=a, b=b, co=co, no=no, dep=dep, mins=(h2 * 60 + m2) - (h1 * 60 + m1), km=round(km(a, b))))
fl25(12, 28, 'CTS', 'HND', 'JAL', 'JL514', '15:30', '17:10')
fl25(12, 26, 'HND', 'CTS', 'JAL', 'JL509', '09:30', '11:05')
fl25(12, 6, 'FUK', 'HND', 'ANA', 'NH264', '19:00', '20:35')
fl25(12, 5, 'HND', 'FUK', 'ANA', 'NH247', '08:00', '09:55')
fl25(11, 15, 'OKA', 'HND', 'JAL', 'JL916', '13:00', '15:20')
fl25(11, 13, 'HND', 'OKA', 'JAL', 'JL901', '06:20', '09:05')
M25 = {}
for f in F25: M25.setdefault(f['m'], []).append(f)
Y25 = dict(n=31, km=28410, h=54)   # 2025年の見本の合計（画面に出す数）

def mblock(m, L, y=None):
    yy = '<span class="yy">%d年</span>' % y if y else ''
    return '<div class="mh"><b>%d月</b>%s<small>%d便</small><span class="r">%s km</span></div><div class="card lg">%s</div>' % (m, yy, len(L), c(sum(f['km'] for f in L)), ''.join(lrow(f) for f in L))

# ---------- A1 日誌（年の切り替えつき） ----------
def pA1():
    body = '<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(4) + ann('A1 日誌（3版）', [
        '上のカードに年の切り替え（‹ 2026年 ›）。‹ で前の年、年の字を押すと年の一覧から選ぶ。今年より先は › がうすい（review-2 の3）',
        '数字は1行（26便・23,764 km・空の上 45時間）にして、月の小さい棒は年のまとめ（A3）だけに。最初の便が上がり、667 でも2便見える（review-2 の4）',
        '日誌を下まで送ると年をまたいで続く（A1y）']) + '</div>' + tabs('フライト')
    page(OUT + '/A1-log-v3.html', 'A1 日誌（年の切り替え）' + T, body, extra_css=CSS3)

# ---------- A1y 年をまたぐ所と続き ----------
def pA1y():
    m26 = sorted(MON)[:2]   # 2026年の 1月・2月
    s = '<div class="wrap"><div class="stk">%s</div>' % ysw(2026, True, False)
    s += '<p class="note" style="margin:10px 4px 0">（日誌を下まで送ったところ。上の帯の年は、下の「2025年」の帯を過ぎると 2025年に変わる）</p>'
    for m in reversed(m26):
        s += mblock(m, MON[m])
    s += '<div class="yd"><b>2025年</b><small>%d便・%s km</small><span class="r">まとめ ›</span></div>' % (Y25['n'], c(Y25['km']))
    for m in sorted(M25, reverse=True):
        s += mblock(m, M25[m], 2025)
    s += ('<div class="more"><p class="note">さらに送ると 10月より前が続けて出ます</p><span class="pill">2024年へ</span></div>')
    s += ann('A1y 年をまたぐ所（3版）', [
        '年が変わる所に「2025年」の帯（その年の便の数と距離・押すと年のまとめ）。月の見出しにも小さく年を足す（「12月 2025年」）',
        '上の年の切り替えは、送ると見ている所の年に変わり、画面の上に残る',
        '下まで送ると前の月が続けて出る。年の終わりで止めず、いちばん下に「2024年へ」も置く（記録がない年は出さない）',
        '2025年の6便は見本（年の合計の数も見本）']) + '</div>' + tabs('フライト')
    page(OUT + '/A1y-log-years-v3.html', 'A1y 年をまたぐ所' + T, s, extra_css=CSS3)

# ---------- A1p 年を選ぶ ----------
def pA1p():
    yrs = [(2026, len(F), TOTAL_KM), (2025, Y25['n'], Y25['km']), (2024, 12, 9860), (2023, 4, 3120)]
    rows = ''.join('<div class="row"><div class="tx"><b>%d年</b><small>%d便・%s km</small></div>%s</div>' % (
        y, n, c(k), '<span class="tg" style="display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:800;background:#16233A;color:#fff">見ている年</span>' if y == 2026 else '<span style="color:var(--pale);font-weight:700">›</span>') for y, n, k in yrs)
    body = ('<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(1) + '</div><div class="dim"></div><div class="sheet"><div class="grab"></div>'
            '<div style="font-size:18px;font-weight:800;color:var(--strong);margin:0 4px 8px">年を選ぶ</div><div class="card lst">%s</div>'
            '<p class="note">記録のある年だけ出ます。年を選ぶと日誌・地図・年のまとめがその年に変わります。</p></div>') % rows + tabs('フライト')
    page(OUT + '/A1p-year-pick-v3.html', 'A1p 年を選ぶ' + T, body, extra_css=CSS3 + '.lst .row + .row{box-shadow:inset 0 1px 0 var(--line2)}')

# ---------- A2s 共有：搭乗券の1枚（スイッチを2つに） ----------
def pA2s(seat_on=False):
    f = F[0]
    css = CSS3 + """
.bp{margin:6px 0 0;border-radius:22px;background:#16233A;color:#fff;overflow:hidden;position:relative}
.bp .tp{display:flex;justify-content:space-between;align-items:center;padding:14px 18px 0;font-size:13px;font-weight:700;color:#C9D2DE}
.bp .rt{display:flex;align-items:center;justify-content:space-between;padding:6px 18px 0}
.bp .rt .num{color:#fff;font-size:48px}.bp .rt small{display:block;font-size:14px;color:#C9D2DE;font-weight:700;margin-top:4px}
.bp .rt svg{color:#7F8DA1;width:26px;height:26px}
.bp .gr{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:14px 18px 16px}
.bp .gr .k{font-size:13px;color:#AEB9C7;font-weight:700}.bp .gr .num{color:#fff;font-size:22px}.bp .gr .u{color:#AEB9C7}
.bp .ft{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:12px 18px;background:#1F2E48;font-size:13px;color:#C9D2DE;font-weight:700;position:relative}
.bp .ft::before,.bp .ft::after{content:"";position:absolute;top:-9px;width:18px;height:18px;border-radius:50%;background:var(--card)}
.bp .ft::before{left:-9px}.bp .ft::after{right:-9px}
.bp .acc{position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--jal)}
.bp .dis{padding:0 18px 12px;background:#1F2E48;font-size:13px;color:#AEB9C7;font-weight:600}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px}.btns .btn{margin-top:12px}
.swr{display:flex;align-items:center;gap:12px;min-height:52px;padding:2px 2px}.swr + .swr{box-shadow:inset 0 1px 0 var(--line2)}
.swr .tx{flex:1}.swr .tx b{display:block;font-size:15px;color:var(--strong)}.swr .tx small{display:block;font-size:13px;color:var(--sub)}
"""
    behind = '''<div class="wrap" aria-hidden="true"><div style="display:flex;align-items:center;gap:8px;height:60px"><span class="pill">%s フライト</span><span style="margin-left:auto" class="pill">%s 画像で共有</span><span class="pill ic">%s</span></div>
<div class="card" style="height:220px"></div></div>''' % (I['back'], I['share'], I['pen'])
    seat = '・%s席' % f['seat'] if seat_on else ''
    sheet = '''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div style="display:flex;align-items:baseline;gap:8px;margin:0 2px 6px"><b style="font-size:18px;color:var(--strong)">画像で共有</b><span style="margin-left:auto;font-size:13px;color:var(--sub)">会社のロゴは入りません</span></div>
<div class="bp"><span class="acc"></span><div class="tp"><span>2026.%d.%d（%s）</span><span>%s・%s</span></div>
<div class="rt"><div><span class="num">%s</span><small>%s</small></div>%s<div style="text-align:right"><span class="num">%s</span><small>%s</small></div></div>
<div class="gr"><div><div class="k">出発</div><span class="num">%s</span></div><div><div class="k">空の上</div>%s</div><div><div class="k">距離</div><span class="num">%s</span><span class="u">km</span></div></div>
<div class="ft"><span>%s・%s%s</span><span>そらメモ（非公式アプリ）</span></div><div class="dis">各航空会社とは関係ありません</div></div>
<div style="margin-top:8px"><div class="swr"><div class="tx"><b>登録記号を出す</b><small>%s</small></div><span class="sw on">ON</span></div>
<div class="swr"><div class="tx"><b>座席を出す</b><small>%s</small></div><span class="sw %s">%s</span></div></div>
<div class="btns"><span class="btn w">閉じる</span><span class="btn">共有する</span></div></div>''' % (
        f['m'], f['d'], f['wd'], f['co'], f['no'], f['a'], short(f['a']), I['arrow'], f['b'], short(f['b']), f['dep'], hm2(f['mins']), c(f['km']),
        f['typ'], f['reg'], seat, 'OFF にすると機種だけ', ('%s席が入ります' % f['seat']) if seat_on else ('ON にすると %s席が入ります' % f['seat']), 'on' if seat_on else 'off', 'ON' if seat_on else 'OFF')
    body = behind + sheet + tabs('フライト')
    if seat_on:
        page(OUT + '/A2s2-share-seat-on-v3.html', 'A2s2 共有（座席を ON にしたところ）' + T, body, extra_css=css)
    else:
        page(OUT + '/A2s-share-v3.html', 'A2s 画像で共有（便のカード）' + T, body, extra_css=css)

# ---------- A3 年のまとめ（年の切り替え・字の直し） ----------
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
    css = CSS3 + """.sum{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.sum > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px}
.sum .k{font-size:13px;color:var(--sub);font-weight:700;display:block;margin-bottom:4px}.sum .num{font-size:30px}
.bars{display:flex;gap:4px;align-items:flex-end;height:160px;padding:14px 14px 10px}.bars .b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bars i{width:100%;background:var(--navy);border-radius:4px 4px 2px 2px}.bars i.z{background:var(--line2)}.bars .v{font-family:var(--sign);font-weight:700;font-size:14px;color:var(--strong);margin-bottom:3px}.bars .l{font-size:13px;color:var(--mute);margin-top:4px}
.cobar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:6px 16px 4px}.cobar i{display:block}
.colg{display:flex;gap:16px;padding:6px 16px 14px;font-size:13px;color:var(--sub)}.colg b{font-family:var(--sign);font-size:18px;color:var(--strong);margin-left:4px}
.yrow{display:flex;align-items:center;gap:8px;margin-top:12px}.yrow .ysw{flex:1;background:var(--card);border-radius:999px;box-shadow:var(--shadow);padding:0 4px}"""
    body = ('<div class="wrap">' + header() + V.titlerow('yr') +
            '<div class="yrow">%s<span class="pill">%s 画像で共有</span></div>'
            '<div class="sum"><div><span class="k">便</span><span class="num">%d</span><span class="u">便</span></div><div><span class="k">路線</span><span class="num">%d</span><span class="u">路線（往復で1つ）</span></div>'
            '<div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">空の上</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></div></div>'
            '<div class="sec-h">月ごとの便の数</div><div class="card"><div class="bars">%s</div>'
            '<p class="note" style="margin:0 16px 14px">距離がいちばん長かった月：%d月（%s km）</p></div>'
            '<div class="sec-h">よく乗った路線<span class="r">地図で見る ›</span></div><div class="card">%s</div>'
            '<div class="sec-h">会社</div><div class="card" style="padding-top:12px"><div class="cobar"><i style="flex:%d;background:var(--jal)"></i><i style="flex:%d;background:var(--ana)"></i></div><div class="colg"><span>JAL グループ<b>%d</b></span><span>ANA<b>%d</b></span></div></div>'
            ) % (ysw(2026, True, False), I['share'], len(F), len(RT), c(TOTAL_KM), TOTAL_MIN // 60, TOTAL_MIN % 60, bars, big + 1, c(kms[big]), V.route_rows(3), co.get('JAL', 0), co.get('ANA', 0), co.get('JAL', 0), co.get('ANA', 0)) + ann('A3 年のまとめ（3版）', [
                '上に年の切り替え（‹ 2026年 ›）。日誌・地図と同じ年を見る（日誌で 2025年にしたら、ここも 2025年）',
                '「画像で共有」は年の切り替えの右に上げた（1便・1区間と同じく上の段。review-2 の7）',
                '「日誌の小さい棒と同じ」を消した（review-2 の8）。棒の下は「距離がいちばん長かった月：3月（4,708 km）」（review-2 の9）']) + '</div>' + tabs('フライト')
    page(OUT + '/A3-year-v3.html', 'A3 年のまとめ' + T, body, extra_css=css)

# ---------- R1 「航路なし」（車などの移動）の行と数え方 ----------
def pR1():
    car = dict(m=8, d=11, a='KOJ', b='KMI', km=round(km('KOJ', 'KMI')))
    L8 = MON[8]   # 8/12 KOJ→HND, 8/10 HND→KOJ（新しい順）
    def carrow():
        return ('<div class="lr car"><div class="dt"><span class="num">%d</span><small>%s</small></div>'
                '<div style="min-width:0"><div class="rt">%s%s%s</div><div class="sb"><span class="cg">車など</span> 航路なし</div></div>'
                '<div class="tm"><span class="num">%s</span><span class="u">km</span><small>空の上なし</small></div></div>') % (
            car['d'], WD[datetime.date(2026, 8, 11).weekday()], short(car['a']), I['arrow'], short(car['b']), c(car['km']))
    rows = lrow(L8[0]) + carrow() + lrow(L8[1])
    km8 = sum(f['km'] for f in L8)
    css = CSS3 + """.lr.car::before{display:none}.lr .cg{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;border:1.5px dashed #8A94A3;font-size:13px;font-weight:800;color:var(--ink);margin-right:4px}
.lr.car .rt{color:var(--ink)}
.opt{margin-top:18px}.opt h2{display:flex;align-items:center;gap:8px;font-size:17px;color:var(--strong);margin:0 4px 6px}.opt h2 .tg{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:800;background:#16233A;color:#fff}
.opt h2 .tg.w{background:var(--wash);color:var(--strong)}
.opt .pc{font-size:13px;line-height:1.6;color:var(--ink);margin:8px 4px 0}
.opt .y1 .num{font-size:24px}
.lg2{display:flex;align-items:center;gap:10px;padding:12px 16px;font-size:13px;color:var(--sub)}.lg2 i{display:inline-block;width:40px;border-top:2.5px dashed #16233A}.lg2 i.s{border-top-style:solid}"""
    def opt(tag, ttl, top, mh, good):
        return ('<div class="opt"><h2><span class="tg%s">%s</span>%s</h2><div class="card yc" style="margin-top:0">%s</div>'
                '<div class="mh"><b>8月</b>%s</div><div class="card lg">%s</div><p class="pc">%s</p></div>') % (
            ' w' if tag == '案1' else '', tag, ttl, top, mh, rows, good)
    top1 = ('<div class="y1"><span><span class="num">%d</span><span class="u">便</span></span><span><span class="num">%s</span><span class="u">km</span></span>'
            '<span><span class="u">空の上</span><span class="num">%d</span><span class="u">時間</span></span></div>') % (len(F) + 1, c(TOTAL_KM + car['km']), TOTAL_MIN // 60)
    top2 = ('<div class="y1"><span><span class="num">%d</span><span class="u">便</span></span><span><span class="num">%s</span><span class="u">km</span></span>'
            '<span><span class="u">空の上</span><span class="num">%d</span><span class="u">時間</span></span></div>'
            '<p class="note" style="margin:6px 12px 0;text-align:center">ほかの移動 1（%s km）は別に数える</p>') % (len(F), c(TOTAL_KM), TOTAL_MIN // 60, c(car['km']))
    body = ('<div class="wrap"><div class="top" style="height:52px"><b style="font-size:20px;color:var(--strong)">「航路なし」の移動の数え方</b></div>'
            '<p class="note" style="margin:0 4px">見本に 8月11日の鹿児島 → 宮崎（車など）を1つ足した。日誌の行は2つの案で同じ。違うのは月の見出しと上の数字</p>'
            + opt('案1', '便に入れる', top1, '<small>3便</small><span class="r">%s km</span>' % c(km8 + car['km']),
                  '良い点：数え方が1つで分かりやすい。困る点：「便」の数が実際に乗った便より多くなる。修行（FOP・回数）には入れない決まりと食い違って見える')
            + opt('案2', '別に数える（おすすめ）', top2, '<small>2便・ほかの移動 1</small><span class="r">%s km</span>' % c(km8),
                  '良い点：「便」「空の上」「距離」は乗った便だけで、年のまとめ・修行・地図の数と合う。経営の路線には今のまま数える（決定どおり）。困る点：数字が1つ増える')
            + '<div class="sec-h">地図では</div><div class="card"><div class="lg2"><i class="s"></i>乗った便<i></i>航路なし（点線）</div>'
            '<p class="note" style="margin:0 16px 14px">点線のまま、太さは便と同じ決まり（回数）。年のまとめでは「ほかの移動」を4つの枠の下に1行で</p></div>'
            + ann('R1「航路なし」の行と数え方（3版）', [
                '日誌の行：左の会社の帯なし・「車など」の点線の札・右は時間でなく距離（「空の上なし」）。押すと1便の画面の代わりに移動の記録（出発と着いた空港・日付）',
                '月の見出し・上の数字・年のまとめ・地図で数え方をそろえる（A1・A3・M1 で数が合うように）。本人に案1か案2かを聞く',
                '経営の路線は決定どおり今のまま数える（この画面は記録の見せ方だけ）']) + '</div>' + tabs('フライト'))
    page(OUT + '/R1-no-route-v3.html', 'R1 航路なしの数え方' + T, body, extra_css=css)

# ---------- 夜の日誌（年の切り替え） ----------
def pN1():
    body = '<div class="wrap">' + header() + V.titlerow('log') + ycard() + V.months(4) + ann('N1 夜の日誌（3版）', [
        '年の切り替えと1行の数字を昼とそろえた。光る色は使わない（数字は白に近い字）', '会社の色の細い帯は夜は出さない（2版と同じ）']) + '</div>' + tabs('フライト')
    page(OUT + '/N1-log-night-v3.html', 'N1 夜の日誌' + T, body, night=True, extra_css=CSS3 + V.NCSS + '.ysw .pill.ic.dis{color:#2A3542}')

for fn in (pA1, pA1y, pA1p, pA2s, pA3, pR1, pN1): fn()
pA2s(seat_on=True)
print('ok', len(F), TOTAL_KM, TOTAL_MIN, round(km('KOJ', 'KMI')))
