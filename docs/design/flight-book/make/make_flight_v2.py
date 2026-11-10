# -*- coding: utf-8 -*-
# フライトの2版（本人の決定 11/10 13時「A に糸の地図を入れる」・改善担当 review-1 の必ず直す3つ）
# 使い方：python3 make_flight_v2.py <出力先>
# 部品は common.py（見本の記録は修行の案と同じ26便）。空港の表 /tmp/claude-0/ap.json・輪郭 /tmp/claude-0/jp.txt を先に作る
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
OUT = sys.argv[1]
T = '｜フライトの2版（画面案）'
MON = {}
for f in F: MON.setdefault(f['m'], []).append(f)
ICON_LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" stroke-width="5"/><path d="M16 36l32-12-8 20-6-8z" fill="currentColor"/></svg>'

def routes():
    rt = {}
    for f in F: rt.setdefault(tuple(sorted((f['a'], f['b']))), []).append(f)
    return rt
RT = routes()

def hm2(mins):
    h, m = divmod(mins, 60)
    s = ''
    if h: s += '<span class="num">%d</span><span class="u">時間</span>' % h
    if m or not h: s += '<span class="num">%d</span><span class="u">分</span>' % m
    return s
def hm_txt(mins):
    h, m = divmod(mins, 60)
    return ('%d時間' % h if h else '') + ('%d分' % m if m or not h else '')

CSS2 = """
.hd{display:flex;align-items:center;justify-content:space-between;height:56px}
.logo{display:flex;align-items:center;gap:8px;font-weight:800;font-size:18px;color:var(--strong)}.logo svg{width:24px;height:24px}
.seg{margin-top:4px}.seg b{min-height:44px}
.ttl{display:flex;align-items:center;gap:8px;margin:18px 0 0}.ttl h1{font-size:26px;margin:0 auto 0 2px;color:var(--strong);letter-spacing:.04em}
.yr{padding:16px 18px 10px;display:flex;gap:6px;align-items:flex-end}
.yr .k{font-size:13px;color:var(--sub);font-weight:700;display:block;margin-bottom:6px}
.yr > div{flex:1}.yr .num{font-size:32px}
.spk-h{display:flex;justify-content:space-between;margin:4px 18px 0;font-size:13px;color:var(--sub);font-weight:700}
.spark{display:flex;gap:3px;align-items:flex-end;height:30px;margin:4px 18px 0;padding-top:4px}
.spark i{flex:1;background:var(--navy);border-radius:3px 3px 1px 1px;opacity:.9}.spark i.z{background:var(--line2);height:3px!important}
.mlab{display:flex;gap:3px;margin:2px 18px 12px}.mlab span{flex:1;text-align:center;font-size:13px;color:var(--mute);line-height:1.3}
.mh{display:flex;align-items:baseline;gap:8px;margin:20px 6px 6px}.mh b{font-size:17px;color:var(--strong)}.mh small{font-size:13px;color:var(--sub);font-weight:700}
.mh .r{margin-left:auto;font-size:13px;color:var(--sub)}
.lg{overflow:hidden}
.lr{display:grid;grid-template-columns:42px 1fr auto;gap:10px;align-items:center;min-height:64px;padding:8px 16px;position:relative}
.lr + .lr{box-shadow:inset 0 1px 0 var(--line2)}
.lr .dt{text-align:center;line-height:1.1}.lr .dt .num{font-size:24px;display:block}.lr .dt small{font-size:13px;color:var(--sub);font-weight:700}
.lr .rt{display:flex;align-items:center;gap:4px;font-size:17px;font-weight:800;color:var(--strong);line-height:1.35;white-space:nowrap}
.lr .rt svg{color:var(--pale);width:16px;height:16px}
.lr .sb{font-size:13px;color:var(--sub);line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lr .sb b{font-family:var(--sign);font-size:15px;color:var(--ink);font-weight:700;letter-spacing:.02em}
.lr .tm{text-align:right;line-height:1.15;white-space:nowrap}.lr .tm .num{font-size:20px}.lr .tm .u{margin-left:1px;margin-right:2px}.lr .tm small{display:block;font-size:13px;color:var(--sub);font-weight:700;margin-top:3px}
.lr::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:4px;border-radius:0 3px 3px 0;background:var(--cc)}
.mapcard{margin-top:12px;overflow:hidden;position:relative}
.mapcard svg{display:block}
.mapcard .attr{position:absolute;right:10px;bottom:8px;font-size:13px;color:var(--sub);background:rgba(255,255,255,.85);border-radius:999px;padding:0 10px;line-height:26px}
.mapcard .shr{position:absolute;right:10px;top:10px}
.legend{display:flex;gap:16px;align-items:center;padding:12px 16px 4px;font-size:13px;color:var(--sub);flex-wrap:wrap}
.legend i{display:inline-block;height:0;border-top:solid var(--navy);width:28px;vertical-align:middle;margin-right:6px;border-radius:3px}
.rk{display:flex;align-items:center;gap:12px;min-height:56px;padding:6px 16px}.rk + .rk{box-shadow:inset 0 1px 0 var(--line2)}
.rk .ln{width:30px;flex:none;height:0;border-top:solid var(--navy);border-radius:3px}
.rk .tx{flex:1;min-width:0}.rk .tx b{display:block;font-size:15px;color:var(--strong)}.rk .tx small{font-size:13px;color:var(--sub)}.rk .num{font-size:24px}
.rk .chev{color:var(--pale);font-size:18px;font-weight:700}
"""

def header():
    return ('<div class="hd"><span class="logo">%s そらメモ</span><span class="pill">マイページ</span></div>'
            '<div class="seg"><b class="on">スタンプラリー</b><b>エアライン経営</b></div>') % ICON_LOGO
def titlerow(band_on, share=False):
    bands = [('日誌', 'log'), ('地図', 'map'), ('年のまとめ', 'yr')]
    vb = ''.join('<span class="pill%s">%s</span>' % (' on' if k == band_on else '', n) for n, k in bands)
    return ('<div class="ttl"><h1>フライト</h1><span class="pill ic" aria-label="搭乗券を読み取る">%s</span><span class="pill ic dark" aria-label="フライトを足す">%s</span></div>'
            '<div class="vband">%s<span class="pill ed" aria-label="見方を選ぶ">%s</span></div>') % (I['scan'], I['plus'], vb, I['pen'])

def lrow(f):
    return ('<div class="lr" style="--cc:%s"><div class="dt"><span class="num">%d</span><small>%s</small></div>'
            '<div style="min-width:0"><div class="rt">%s%s%s</div><div class="sb"><b>%s</b> 発・%s</div></div>'
            '<div class="tm">%s<small>%s km</small></div></div>') % (
        CO_COL[f['co']], f['d'], f['wd'], short(f['a']), I['arrow'], short(f['b']), f['dep'], f['no'], hm2(f['mins']), c(f['km']))

def year_card(night=False, spark=True):
    cnt = [len(MON.get(m, [])) for m in range(1, 13)]
    mx = max(cnt)
    sp = ''.join('<i style="height:%d%%"%s></i>' % (max(10, v * 100 // mx), '' if v else ' class="z"') for v in cnt)
    lab = ''.join('<span>%s</span>' % (m if m in (1, 4, 7, 10) else '') for m in range(1, 13))
    lit = ' lit' if night else ''
    s = ('<div class="card" style="margin-top:12px"><div class="yr"><div><span class="k">2026年</span><span class="num%s">%d</span><span class="u">便</span></div>'
         '<div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">空の上</span><span class="num">%d</span><span class="u">時間</span></div></div>') % (lit, len(F), c(TOTAL_KM), TOTAL_MIN // 60)
    if spark:
        s += ('<div class="spk-h"><span>月ごとの便の数</span><span>多い月 %d便</span></div><div class="spark" aria-label="月ごとの便の数">%s</div><div class="mlab">%s</div>') % (mx, sp, lab)
    return s + '</div>'

def months(n=4):
    s = ''
    for m in sorted(MON, reverse=True)[:n]:
        L = MON[m]
        s += '<div class="mh"><b>%d月</b><small>%d便</small><span class="r">%s km</span></div><div class="card lg">%s</div>' % (m, len(L), c(sum(f['km'] for f in L)), ''.join(lrow(f) for f in L))
    return s

def ann(t, L):
    return '<div class="ann"><b>%s</b><ul>%s</ul></div>' % (t, ''.join('<li>%s</li>' % x for x in L))

# ---------- 地図（今の地図の描き方の上で、線の太さ＝乗った回数） ----------
def tw(n): return 1.4 + (n - 1) * 1.05
def thread_map(W=358, H=405, vb='18 18 340 385', hi=None, night=False, labels=True, faint=False):
    sea = '#0A0F14' if night else '#EAF0F4'
    land = '#0E151D' if night else '#FBFAF6'
    coast = '#2A3644' if night else '#B7C2CC'
    grid = '#141C26' if night else '#D7E0E8'
    ink = '#BCC6D1' if night else '#16233A'
    dim = '#2A3542' if night else '#C3CBD5'
    vx, vy, vw, vh = map(float, vb.split())
    s = '<svg width="%d" height="%d" viewBox="%s" preserveAspectRatio="xMidYMid slice" aria-label="乗った区間の地図（線が太いほど何度も乗った）">' % (W, H, vb)
    s += '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' % (vx - 50, vy - 50, vw + 100, vh + 100, sea)
    # 航空図のような経緯線（2度ごと）
    for lon in range(122, 150, 2):
        x = (lon - 122.5) * 16.4 * 0.82 + 20
        s += '<path d="M%.1f -50V600" stroke="%s" stroke-width=".7"/>' % (x, grid)
    for lat in range(22, 48, 2):
        y = (46.2 - lat) * 17.6 + 14
        s += '<path d="M-50 %.1fH600" stroke="%s" stroke-width=".7"/>' % (y, grid)
    s += jpmap(land=land, coast=coast)
    used = set()
    for k in RT: used.update(k)
    for a in BY.values():
        if a['code'] in used: continue
        x, y = proj(a['code'])
        s += '<circle cx="%.1f" cy="%.1f" r="1.5" fill="%s"/>' % (x, y, '#3A4654' if night else '#A9B3BE')
    for (a, b), L in sorted(RT.items(), key=lambda x: len(x[1])):
        x1, y1 = proj(a); x2, y2 = proj(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2; dx, dy = x2 - x1, y2 - y1; Ln = math.hypot(dx, dy) or 1; k = min(18, Ln * .12)
        on = hi is None or (a, b) == hi
        col = ink if on else dim
        op = (.9 if hi is None else 1) if on else .9
        if faint and hi is None: op = .9
        s += '<path d="M%.1f %.1fQ%.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round" opacity="%.2f"/>' % (
            x1, y1, mx - dy / Ln * k, my + dx / Ln * k, x2, y2, col, tw(len(L)), op)
    if hi:
        # 押した区間は上にもう1回描く
        a, b = hi; L = RT[hi]
        x1, y1 = proj(a); x2, y2 = proj(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2; dx, dy = x2 - x1, y2 - y1; Ln = math.hypot(dx, dy) or 1; k = min(18, Ln * .12)
        s += '<path d="M%.1f %.1fQ%.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="%.2f" stroke-linecap="round"/>' % (x1, y1, mx - dy / Ln * k, my + dx / Ln * k, x2, y2, ink, tw(len(L)))
    for p in used:
        x, y = proj(p)
        on = hi is None or p in hi
        s += '<circle cx="%.1f" cy="%.1f" r="3.6" fill="%s" stroke="%s" stroke-width="1.5"/>' % (x, y, land if night else '#fff', ink if on else dim)
    if labels:
        LB = [('HND', 8, 4), ('OKA', -4, 20), ('CTS', 8, 4), ('ISG', 4, -9)] if hi is None else [(x, d1, d2) for x, d1, d2 in [('HND', 8, 4), ('OKA', -4, 20)] if x in hi]
        for code, dx, dy in LB:
            x, y = proj(code)
            s += '<text x="%.1f" y="%.1f" font-size="15" font-weight="800" fill="%s" font-family="var(--gothic)" paint-order="stroke" stroke="%s" stroke-width="4" stroke-linejoin="round">%s</text>' % (
                x + dx, y + dy, '#DCE3EA' if night else '#1F2937', land, short(code))
    return s + '</svg>'

def legend():
    return ('<div class="legend"><span>太さ＝回数</span><span><i style="border-top-width:%.1fpx"></i>2回</span><span><i style="border-top-width:%.1fpx"></i>4回</span>'
            '<span><i style="border-top-width:%.1fpx"></i>6回</span></div>') % (tw(2), tw(4), tw(6))

def route_rows(n=4, hi=None):
    top = sorted(RT.items(), key=lambda x: (-len(x[1]), x[0]))[:n]
    s = ''
    for (a, b), L in top:
        s += ('<div class="rk"><span class="ln" style="border-top-width:%.1fpx"></span><div class="tx"><b>%s ⇄ %s</b><small>%s ⇄ %s・%s km</small></div>'
              '<span><span class="num">%d</span><span class="u">回</span></span><span class="chev">›</span></div>') % (tw(len(L)), short(a), short(b), a, b, c(L[0]['km']), len(L))
    return s

# ---------- A1 日誌（1画面・上の段つき）＝本命 ----------
def pA1():
    body = '<div class="wrap">' + header() + titlerow('log') + year_card() + months() + ann('A1 日誌（2版・上の段をつけた1画面）', [
        '右の時間は「2時間20分」と書く（2:20 は時刻に読める・review-1 の1）。2行目の左に出発の時刻「16:00 発」と便名',
        '区間は名前で大きく（那覇 → 羽田）。コードは1便の詳しい所に',
        '上の段（そらメモ・マイページ／スタンプラリー｜エアライン経営）は図鑑と同じ。タブを切り替えても上の段は跳ばない',
        '今の「地図の上のシート」をやめ、ほかのタブと同じ1画面にする。シートの版は A1s で比べる',
        '上のカードの小さい棒に「月ごとの便の数」と書く（review-1 の2）']) + '</div>' + tabs('フライト')
    page(OUT + '/A1-log-v2.html', 'A1 日誌（1画面）' + T, body, extra_css=CSS2)

# ---------- A1s 日誌（今の形：地図の上のシート）＝比べる用 ----------
def pA1s():
    css = CSS2 + """
.mapbg{position:absolute;left:0;right:0;top:0;height:400px;overflow:hidden}
.ov{position:relative;z-index:2;padding:6px 16px 0}
.ov .hd .logo{background:var(--card);border-radius:999px;padding:0 16px;height:44px;box-shadow:var(--shadow)}
.sh{position:relative;z-index:3;margin-top:196px;background:var(--bg);border-radius:28px 28px 0 0;box-shadow:0 -10px 30px -12px rgba(17,24,39,.3);padding:8px 16px 120px}
.sh .grab{background:#C9D0D9}
.sh .ttl{margin-top:2px}
"""
    body = ('<div class="mapbg">%s</div><div class="ov">%s</div><div class="sh"><div class="grab"></div>%s%s%s%s</div>') % (
        thread_map(W=420, H=400, vb='40 40 330 314', labels=False), header(), titlerow('log'), year_card(), months(2),
        ann('A1s 日誌（今のまま地図の上のシート）', [
            '今の本番の形。上の段は地図の上に浮かせ、下からシートを引き出す',
            '良い点：シートを下げると地図が見える。今の人は迷わない',
            '困る点：844 で見える便は2便（A1 は4便）、667 では0便。図鑑や運用は1画面なので、タブを切り替えると上の段の位置が変わる',
            'デザイン担当のおすすめは A1（1画面）。地図は見方の「地図」（M1）で大きく出す'])) + tabs('フライト')
    page(OUT + '/A1s-log-sheet-v2.html', 'A1s 日誌（シートの版）' + T, body, extra_css=css)

# ---------- A2 1便（共有の入口つき） ----------
def vbox(x1, y1, x2, y2, ratio=358 / 150):
    w = max(abs(x2 - x1) + 50, (abs(y2 - y1) + 36) * ratio); h = w / ratio
    return '%.1f %.1f %.1f %.1f' % ((x1 + x2) / 2 - w / 2, (y1 + y2) / 2 - h / 2, w, h)
def pA2():
    f = F[0]
    key = tuple(sorted((f['a'], f['b'])))
    k = RT[key]
    x1, y1 = proj(f['a']); x2, y2 = proj(f['b'])
    css = CSS2 + """.top2{display:flex;align-items:center;gap:8px;height:60px}
.big{display:flex;align-items:center;justify-content:space-between;padding:12px 20px 4px}.big .num{font-size:50px}.big small{display:block;font-size:14px;color:var(--sub);font-weight:700;margin-top:6px}
.big .mid{color:var(--pale)}.tms{display:flex;justify-content:space-between;padding:0 20px 18px;font-size:14px;color:var(--sub)}.tms b{font-family:var(--sign);font-size:22px;color:var(--strong);margin-left:4px}
.dl{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.dl > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px}
.dl .k{font-size:13px;color:var(--sub);font-weight:700}.dl .v{margin-top:4px;font-family:var(--sign);font-weight:700;font-size:26px;color:var(--strong);line-height:1.1}.dl .v .num{font-size:26px}.dl .v small{display:block;font-family:var(--gothic);font-size:13px;color:var(--sub);font-weight:600;margin-top:4px}
.mapc{margin-top:10px;overflow:hidden;height:150px}.mapc svg{display:block}"""
    body = '''<div class="wrap"><div class="top2"><span class="pill">%s フライト</span><span style="margin-left:auto" class="pill">%s 共有</span><span class="pill ic" aria-label="直す">%s</span></div>
<div class="card"><p class="note" style="margin:14px 20px 0;font-weight:700">2026年%d月%d日（%s）・%s・%s</p>
<div class="big"><div><span class="num">%s</span><small>%s</small></div><span class="mid">%s</span><div style="text-align:right"><span class="num">%s</span><small>%s</small></div></div>
<div class="tms"><span>出発<b>%s</b></span><span>到着<b>%s</b></span></div></div>
<div class="dl"><div><div class="k">空の上</div><div class="v">%s</div></div><div><div class="k">距離</div><div class="v"><span class="num">%s</span><span class="u">km</span><small>区間 %s マイル</small></div></div>
<div><div class="k">機体</div><div class="v">%s<small>%s</small></div></div><div><div class="k">座席</div><div class="v">%s<small>記録した席</small></div></div></div>
<div class="card mapc">%s</div>
<div class="sec-h">この区間の便<small>%s ⇄ %s</small><span class="r">%d回</span></div>
<div class="card lg">%s</div>
%s</div>''' % (
        I['back'], I['share'], I['pen'], f['m'], f['d'], f['wd'], f['co'], f['no'], f['a'], short(f['a']), I['arrow'], f['b'], short(f['b']), f['dep'], f['arr'],
        hm2(f['mins']), c(f['km']), c(f['tpm']), f['reg'], f['typ'], f['seat'],
        thread_map(W=358, H=150, vb=vbox(x1, y1, x2, y2), hi=key, labels=False),
        short(f['a']), short(f['b']), len(k), ''.join(lrow(x) for x in k[:4]),
        ann('A2 1便の詳しい所（2版）', ['空の上は「2時間20分」（単位を字で）。出発・到着の時刻は上のカードに',
                                   '右上に「共有」。押すと搭乗券の1枚（A2s）が出る（review-1 の4）',
                                   '小さい地図も M1 と同じ描き方（この区間だけ濃く、ほかの区間はうすく）',
                                   '「この区間の便」の行を押すと、その便の詳しい所へ'])) + tabs('フライト')
    page(OUT + '/A2-flight-v2.html', 'A2 1便の詳しい所' + T, body, extra_css=css)

# ---------- A2s 共有：搭乗券の1枚 ----------
def pA2s():
    f = F[0]
    css = CSS2 + """
.bp{margin:6px 0 0;border-radius:22px;background:#16233A;color:#fff;overflow:hidden;position:relative}
.bp .tp{display:flex;justify-content:space-between;align-items:center;padding:14px 18px 0;font-size:13px;font-weight:700;color:#C9D2DE}
.bp .rt{display:flex;align-items:center;justify-content:space-between;padding:6px 18px 0}
.bp .rt .num{color:#fff;font-size:48px}.bp .rt small{display:block;font-size:14px;color:#C9D2DE;font-weight:700;margin-top:4px}
.bp .rt svg{color:#7F8DA1;width:26px;height:26px}
.bp .gr{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:14px 18px 16px}
.bp .gr .k{font-size:13px;color:#AEB9C7;font-weight:700}.bp .gr .num{color:#fff;font-size:22px}.bp .gr .u{color:#AEB9C7}
.bp .ft{display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:#1F2E48;font-size:13px;color:#C9D2DE;font-weight:700;position:relative}
.bp .ft::before,.bp .ft::after{content:"";position:absolute;top:-9px;width:18px;height:18px;border-radius:50%;background:var(--card)}
.bp .ft::before{left:-9px}.bp .ft::after{right:-9px}
.bp .acc{position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--jal)}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:8px}.btns .btn{margin-top:14px}
.dimbg{filter:none}
"""
    behind = '''<div class="wrap" aria-hidden="true"><div class="top2" style="display:flex;align-items:center;gap:8px;height:60px"><span class="pill">%s フライト</span><span style="margin-left:auto" class="pill">%s 共有</span><span class="pill ic">%s</span></div>
<div class="card" style="height:220px"></div></div>''' % (I['back'], I['share'], I['pen'])
    sheet = '''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div style="display:flex;align-items:baseline;gap:8px;margin:0 2px 6px"><b style="font-size:18px;color:var(--strong)">搭乗券の1枚</b><span style="margin-left:auto;font-size:13px;color:var(--sub)">画像を長押しでも保存できます</span></div>
<div class="bp"><span class="acc"></span><div class="tp"><span>2026.%d.%d（%s）</span><span>%s・%s</span></div>
<div class="rt"><div><span class="num">%s</span><small>%s</small></div>%s<div style="text-align:right"><span class="num">%s</span><small>%s</small></div></div>
<div class="gr"><div><div class="k">出発</div><span class="num">%s</span></div><div><div class="k">空の上</div>%s</div><div><div class="k">距離</div><span class="num">%s</span><span class="u">km</span></div></div>
<div class="ft"><span>%s・%s・%s席</span><span>そらメモ（非公式アプリ）</span></div></div>
<p class="note" style="margin:10px 2px 0">ロゴは使わず、会社名は字だけ。登録記号と座席は「出す」を選んだときだけ（はじめは出す）。</p>
<div class="row" style="padding:6px 2px;min-height:52px"><div class="tx"><b>登録記号と座席を出す</b><small>オフにすると機種だけ</small></div><span class="sw on">ON</span></div>
<div class="btns"><span class="btn w">閉じる</span><span class="btn">共有する</span></div></div>''' % (
        f['m'], f['d'], f['wd'], f['co'], f['no'], f['a'], short(f['a']), I['arrow'], f['b'], short(f['b']), f['dep'], hm2(f['mins']), c(f['km']),
        f['typ'], f['reg'], f['seat'])
    body = behind + sheet + tabs('フライト')
    page(OUT + '/A2s-share-v2.html', 'A2s 共有（搭乗券の1枚）' + T, body, extra_css=css)

# ---------- A3 年のまとめ ----------
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
    css = CSS2 + """.sum{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.sum > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px}
.sum .k{font-size:13px;color:var(--sub);font-weight:700;display:block;margin-bottom:4px}.sum .num{font-size:30px}
.bars{display:flex;gap:4px;align-items:flex-end;height:160px;padding:14px 14px 10px}.bars .b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bars i{width:100%;background:var(--navy);border-radius:4px 4px 2px 2px}.bars i.z{background:var(--line2)}.bars .v{font-family:var(--sign);font-weight:700;font-size:14px;color:var(--strong);margin-bottom:3px}.bars .l{font-size:13px;color:var(--mute);margin-top:4px}
.cobar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:6px 16px 4px}.cobar i{display:block}
.colg{display:flex;gap:16px;padding:6px 16px 14px;font-size:13px;color:var(--sub)}.colg b{font-family:var(--sign);font-size:18px;color:var(--strong);margin-left:4px}
.ttl .yrp{padding:0 14px}"""
    body = ('<div class="wrap">' + header() + titlerow('yr') +
            '<div class="sum"><div><span class="k">2026年</span><span class="num">%d</span><span class="u">便</span></div><div><span class="k">路線</span><span class="num">%d</span><span class="u">路線（往復で1つ）</span></div>'
            '<div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">空の上</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></div></div>'
            '<div class="sec-h">月ごとの便の数<small>日誌の小さい棒と同じ</small></div><div class="card"><div class="bars">%s</div>'
            '<p class="note" style="margin:0 16px 14px">いちばん遠くまで飛んだ月：%d月（%s km）</p></div>'
            '<div class="sec-h">よく乗った路線<span class="r">地図で見る ›</span></div><div class="card">%s</div>'
            '<div class="sec-h">会社</div><div class="card" style="padding-top:12px"><div class="cobar"><i style="flex:%d;background:var(--jal)"></i><i style="flex:%d;background:var(--ana)"></i></div><div class="colg"><span>JAL グループ<b>%d</b></span><span>ANA<b>%d</b></span></div></div>'
            '<span class="btn w" style="margin-top:16px">%s 2026年のまとめを画像で共有</span>'
            ) % (len(F), len(RT), c(TOTAL_KM), TOTAL_MIN // 60, TOTAL_MIN % 60, bars, big + 1, c(kms[big]), route_rows(3), co.get('JAL', 0), co.get('ANA', 0), co.get('JAL', 0), co.get('ANA', 0), I['share']) + ann('A3 年のまとめ（2版）', [
                '上の数字は4つの枠：便・路線・距離・空の上。「路線」を残す（review-1 の9。見本の記録では 10路線、本番のデモでは 15）',
                '日誌の上のカード（小さい棒）はここには出さない。大きい棒も同じ「月ごとの便の数」にそろえ、距離は1行の字に（review-1 の2）',
                'よく乗った路線の左の線は、地図の線と同じ太さ（回数）',
                'いちばん下に今ある「年のまとめを画像で共有」']) + '</div>' + tabs('フライト')
    page(OUT + '/A3-year-v2.html', 'A3 年のまとめ' + T, body, extra_css=css)

# ---------- M1 地図の見方 ----------
def pM1():
    top = max(RT.items(), key=lambda x: len(x[1]))
    body = ('<div class="wrap">' + header() + titlerow('map') +
            '<div class="card mapcard">%s<span class="attr">見本の地図</span></div>%s'
            '<div class="sec-h">乗った区間<small>%d区間・太い順</small><span class="r">すべて ›</span></div><div class="card">%s</div>'
            ) % (thread_map(), '<div class="card" style="margin-top:8px">' + legend() + '<div class="row" style="padding:2px 8px 8px 16px"><div class="tx"><small>いちばん太い線</small><b>%s ⇄ %s（%d回）</b></div><span class="pill">%s 画像で共有</span></div></div>' % (short(top[0][0]), short(top[0][1]), len(top[1]), I['share']),
                 len(RT), route_rows(4)) + ann('M1 地図の見方（D の糸の考えを今の地図に）', [
                '新しい地図は作らない。今の地図（航空図風・国土地理院の地図）の上の線の描き方だけを変える。画面案では地図の絵を輪郭と経緯線で代わりに描いた',
                '線の太さ＝その区間に乗った回数（往復で2回）。線の色は1色（濃い紺）で、会社の色にしない（JAL・ANA の凡例はやめる）',
                '「航路なし」の点線（車や船の移動）は今のまま点線で残す（見本の記録にはない）',
                '線を押すと M2。下の行（太い順）を押しても同じ',
                '「画像で共有」は今の一覧の右上にあるもの（地図の1枚）。地図の下のカードへ移す（地図の上に置くと北海道が隠れる）']) + '</div>' + tabs('フライト')
    page(OUT + '/M1-map-v2.html', 'M1 地図（線の太さ＝回数）' + T, body, extra_css=CSS2)

# ---------- M2 1区間を押したところ ----------
def knots(L, night=False):
    # 1年の帯の上に、乗った日を結び目で置く（日付の間隔どおり）
    ink = '#BCC6D1' if night else '#16233A'; tick = '#2A3542' if night else '#C3CBD5'; txt = '#8996A7' if night else '#5F6875'
    s = '<svg width="326" height="74" viewBox="0 0 326 74" aria-label="乗った日（1年の帯）">'
    s += '<path d="M8 30H318" stroke="%s" stroke-width="%.1f" stroke-linecap="round"/>' % (ink, tw(len(L)))
    for m in range(1, 13):
        x = 8 + (m - 1) / 12 * 310
        s += '<path d="M%.1f 38v6" stroke="%s" stroke-width="1.2"/>' % (x, tick)
        if m in (1, 4, 7, 10):
            s += '<text x="%.1f" y="62" font-size="13" fill="%s" font-family="var(--gothic)" font-weight="700">%d月</text>' % (x, txt, m)
    px = -99
    for f in sorted(L, key=lambda f: (f['m'], f['d'])):
        doy = datetime.date(2026, f['m'], f['d']).timetuple().tm_yday
        x = max(8 + (doy - 1) / 365 * 310, px + 13); px = x
        s += '<circle cx="%.1f" cy="%.1f" r="6.5" fill="%s" stroke="%s" stroke-width="2"/>' % (x, 30, ink, '#0D1218' if night else '#fff')
    return s + '</svg>'
def pM2(night=False):
    key = ('HND', 'OKA'); L = sorted(RT[key], key=lambda f: (f['m'], f['d']))
    css = CSS2 + """.rh{padding:16px 16px 6px}.rh .t{display:flex;align-items:baseline;gap:10px}.rh b{font-size:22px;color:var(--strong)}.rh .t .r{margin-left:auto}.rh .num{font-size:36px}
.rh .s{font-size:13px;color:var(--sub);margin-top:2px}.kn{padding:4px 16px 10px}
.mini{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}.mini > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:10px 12px}.mini .k{font-size:13px;color:var(--sub);font-weight:700;display:block}.mini .num{font-size:22px}
.mapcard.sm{height:240px}"""
    tot = sum(f['mins'] for f in L)
    body = ('<div class="wrap"><div class="top" style="height:60px"><span class="pill">%s 地図</span><span class="pill" style="margin-left:auto">%s 画像で共有</span></div>'
            '<div class="card mapcard sm" style="margin-top:4px">%s</div>'
            '<div class="card" style="margin-top:10px"><div class="rh"><div class="t"><b>羽田 ⇄ 那覇</b><span class="r"><span class="num%s">%d</span><span class="u">回</span></span></div>'
            '<div class="s">HND ⇄ OKA・はじめて 2026年%d月%d日・この前 %d月%d日</div></div><div class="kn">%s</div></div>'
            '<div class="mini"><div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">区間マイル</span><span class="num">%s</span></div><div><span class="k">空の上 合計</span><span class="num">%d</span><span class="u">時間</span><span class="num">%d</span><span class="u">分</span></div></div>'
            '<div class="sec-h">この区間の便<small>新しい順</small></div><div class="card lg">%s</div>') % (
        I['back'], I['share'], thread_map(W=358, H=240, vb='15 178 313 210', hi=key, night=night), ' lit' if night else '', len(L), L[0]['m'], L[0]['d'], L[-1]['m'], L[-1]['d'], knots(L, night),
        c(L[0]['km']), c(L[0]['tpm']), tot // 60, tot % 60, ''.join(lrow(f) for f in reversed(L)))
    if night:
        body += ann('M2 の夜', ['線は白に近い灰（#BCC6D1）。光る緑は回数の数字だけ', '会社の色は使わない（11/9 の決定）']) + '</div>' + tabs('フライト')
        css += """.lr::before{display:none}.mapcard .attr{background:rgba(13,18,24,.85)}"""
        page(OUT + '/N2-route-night-v2.html', 'N2 1区間（夜）' + T, body, night=True, extra_css=css)
    else:
        body += ann('M2 1区間を押したところ（D2 の形）', [
            '地図は押した区間だけ濃く、ほかの区間と空港はうすい灰に',
            '1年の帯に、乗った日を結び目で置く（D2 は等間隔だったが、日付の間隔どおりにした。近い日は少しずらす）',
            '下は日誌と同じ行。今の「路線」の見方はここに入る',
            '「画像で共有」はこの区間の1枚（今の地図の1枚と同じ作り方で、この区間だけ）']) + '</div>' + tabs('フライト')
        page(OUT + '/M2-route-v2.html', 'M2 1区間を押したところ' + T, body, extra_css=css)

# ---------- 夜 ----------
NCSS = """.lr::before{display:none}.spark i{background:#4A5664}.spark i.z{background:#1A222C}.logo{color:var(--strong)}
.mapcard .attr{background:rgba(13,18,24,.85)}.legend i{border-top-color:#BCC6D1}.rk .ln{border-top-color:#BCC6D1}"""
def pN1():
    body = '<div class="wrap">' + header() + titlerow('log') + year_card(night=True) + months() + ann('N1 夜の日誌（2版）', [
        '光るのは今年の便の数だけ（緑）。会社の色の細い帯は夜は出さない', '時間の書き方・上の段は昼と同じ']) + '</div>' + tabs('フライト')
    page(OUT + '/N1-log-night-v2.html', 'N1 夜の日誌' + T, body, night=True, extra_css=CSS2 + NCSS)
def pN1m():
    body = ('<div class="wrap">' + header() + titlerow('map') + '<div class="card mapcard">%s</div>'
            '<div class="card" style="margin-top:8px">%s<div class="row" style="padding:2px 8px 8px 16px"><div class="tx"><small>いちばん太い線</small><b>羽田 ⇄ 那覇（6回）</b></div><span class="pill">%s 画像で共有</span></div></div><div class="sec-h">乗った区間<small>%d区間・太い順</small></div><div class="card">%s</div>') % (
        thread_map(night=True), legend(), I['share'], len(RT), route_rows(4)) + ann('N1m 夜の地図', [
        '海と陸は暗く、経緯線はごく暗い1本。線は白に近い灰で、太さだけが回数', '光る色（緑・琥珀）は地図には使わない']) + '</div>' + tabs('フライト')
    page(OUT + '/N1m-map-night-v2.html', 'N1m 夜の地図' + T, body, night=True, extra_css=CSS2 + NCSS)

for fn in (pA1, pA1s, pA2, pA2s, pA3, pM1, pM2, pN1, pN1m): fn()
pM2(night=True)
print('ok')
