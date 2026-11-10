# -*- coding: utf-8 -*-
# 修行の3版（PM の指示 11/10 15時30分・改善担当 review-2 の必ず直す3つ）。使い方：python3 make_shugyo_v3.py <出力先>
# 1. 夜の「予定」の金をやめる（札の字と点線の縁で分ける） 2. JGC の数は「記録した便から（推定）」・今の数を入れる形
# 3. 上の段（そらメモ・マイページ／スタンプラリー｜エアライン経営）をフライト・図鑑とそろえる
# 見本の記録は common.py の26便。数え方は「修行の計算ルール（2026年10月に確認）」
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from make_shugyo import CSS_S, JM, GOAL, LEFT, LEFT_N, YEARP, CNT_NOW
import make_flight_parts as MP
OUT = sys.argv[1]
T = '｜修行の3版（画面案）'
LS_NOW = CNT_NOW * 5          # Life Status：国内線は1搭乗5（記録した便だけ）
LS_GOAL = 1500
LS_IN = 1240                  # 見本：会員情報に入れた今の Life Status（入れた人の版）
TODAY_N = 12
PT = FOP_NOW * 100 // GOAL
AFTER_K = FOP_NOW + FOP_Y + FOP_K
ICON_LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" stroke-width="5"/><path d="M16 36l32-12-8 20-6-8z" fill="currentColor"/></svg>'

CSS3 = CSS_S + """
.hd{display:flex;align-items:center;justify-content:space-between;height:56px}
.logo{display:flex;align-items:center;gap:8px;font-weight:800;font-size:18px;color:var(--strong)}.logo svg{width:24px;height:24px}
.seg{margin-top:4px}.seg b{min-height:44px}
.ttl{display:flex;align-items:center;gap:8px;margin:8px 0 0}.ttl h1{font-size:26px;margin:0 2px;color:var(--strong);letter-spacing:.04em}
.ttl .seg.co{margin:0 auto 0 6px;width:132px}
.vband{margin-top:4px}
.hero{padding:12px 18px 12px}.hero .big{margin-top:2px}.hero .big .num{font-size:50px;line-height:1.05}
.gauge{margin-top:6px}.gauge .gl{margin-top:4px}.gauge .bar.t{margin-top:6px}
.two{margin-top:8px}.two .card{padding:10px 14px 12px}.two .k{font-size:13px;color:var(--sub);font-weight:800}
.two .ato{display:flex;align-items:baseline;gap:4px;margin-top:8px;white-space:nowrap}.two .ato .a{font-size:15px;font-weight:800;color:var(--strong)}.two .ato .num{font-size:28px;display:inline;margin:0}
.two small{display:block;font-size:13px;color:var(--sub);margin-top:4px}
.yr{margin:6px 0 0;font-size:14px;line-height:1.6;color:var(--ink);font-weight:700}.yr b{color:var(--strong)}
.jgc{padding:12px 16px;margin-top:8px}.jgc .tp{display:flex;align-items:center;gap:12px}.jgc .tx{flex:1;min-width:0}.jgc .tx b{display:block;font-size:14px;color:var(--strong)}.jgc .tx small{display:block;font-size:13px;color:var(--sub)}
.jgc .v{text-align:right;white-space:nowrap}.jgc .v .num{font-size:22px}.jgc .bar{height:6px;border-radius:3px;background:var(--line2);margin-top:6px;overflow:hidden;display:flex}.jgc .bar i{display:block;height:100%;background:var(--jisseki)}.jgc .bar i.in{background:#9AA3AF}
.jgc .est-tg{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;font-size:13px;font-weight:800;background:var(--wash);color:var(--sub);margin-left:6px;vertical-align:1px}
.jgc .in-row{display:flex;align-items:center;gap:8px;margin-top:10px}.jgc .in-row small{flex:1;font-size:13px;color:var(--sub);line-height:1.5}
.today{display:flex;align-items:center;gap:8px;margin:0 16px 12px;padding:8px 12px;border-radius:14px;background:var(--wash);font-size:13px;color:var(--sub);font-weight:700}.today b{color:var(--strong)}.today .dot{width:8px;height:8px;border-radius:50%;background:#15803D;flex:none}
.empty{padding:18px 18px 18px}.empty p{margin:0;font-size:15px;color:var(--ink);line-height:1.7}.empty .btn{margin-top:14px}
.rc{padding:16px 18px 16px}.rc .k{font-size:13px;color:var(--sub);font-weight:800}.rc .rr{display:flex;align-items:baseline;gap:10px;min-height:44px;padding:6px 0}.rc .rr + .rr{box-shadow:inset 0 1px 0 var(--line2)}.rc .rr .tx{flex:1;font-size:14px;font-weight:700;color:var(--ink)}.rc .rr .num{font-size:28px}.rc .rr small{display:block;font-size:13px;color:var(--sub);font-weight:600}
.rc .rr .n2{min-width:56px;text-align:right;font-size:13px;color:var(--sub);font-weight:700;white-space:nowrap}.rc .rr .n2 b{display:block;font-family:var(--sign);font-size:18px;color:var(--strong)}
.yr12{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.yr12 > div{background:var(--card);border-radius:14px;padding:10px 10px 10px;box-shadow:var(--shadow)}
.yr12 .mo{font-size:13px;font-weight:800;color:var(--sub);display:block}.yr12 .num{font-size:22px;display:block;margin-top:4px}.yr12 small{display:block;font-size:13px;color:var(--sub);font-weight:700;margin-top:2px}
.yr12 > div.y{background:var(--yotei);box-shadow:none}.yr12 > div.y .mo,.yr12 > div.y small,.yr12 > div.y .num{color:var(--yotei-ink)}.yr12 > div.k{background:var(--keikaku);box-shadow:none}.yr12 > div.k .mo,.yr12 > div.k small,.yr12 > div.k .num{color:var(--keikaku-ink)}
"""
# 夜：予定は金をやめ、札の字「予定」と点線の縁で分ける。計画は細い実線の縁。どちらも地は暗い灰
NCSS = """.gauge .bar i{background:#5FD993}.gauge .bar.t i{background:#4A5664}.jgc .bar i{background:#8996A7}.jgc .bar i.in{background:#4A5664}
.today{background:#0A0F14}.today .dot{background:#5FD993}
.est.y{background:#121922;color:#DCE3EA;box-shadow:none;border:1.5px dashed #6B7787}
.est.k{background:#121922;color:#DCE3EA;box-shadow:none;border:1px solid #3A4654}
.est .tx b .tg{margin-right:6px}
.tag-y{background:transparent!important;color:#DCE3EA!important;border:1.5px dashed #6B7787}
.tag-k{background:transparent!important;color:#DCE3EA!important;border:1px solid #3A4654}
.yr12 > div.y{background:#121922;border:1.5px dashed #6B7787}.yr12 > div.y .mo,.yr12 > div.y small,.yr12 > div.y .num{color:#DCE3EA}
.yr12 > div.k{background:#121922;border:1px solid #3A4654}.yr12 > div.k .mo,.yr12 > div.k small,.yr12 > div.k .num{color:#DCE3EA}
.logo{color:var(--strong)}"""

def header(band=None):
    s = ('<div class="hd"><span class="logo">%s そらメモ</span><span class="pill">マイページ</span></div>'
         '<div class="seg"><b class="on">スタンプラリー</b><b>エアライン経営</b></div>'
         '<div class="ttl"><h1>修行</h1><div class="seg co"><b>ANA</b><b class="on">JAL</b></div><span class="pill">会員情報</span></div>') % ICON_LOGO
    if band:
        s += '<div class="vband">' + ''.join('<span class="pill%s">%s</span>' % (' on' if n == band else '', n) for n in ['道のり', '1便ごと', '月ごと']) + \
             '<span class="pill ed" aria-label="見方を選ぶ">' + I['pen'] + '</span></div>'
    return s

def jgc_card(entered=False):
    if not entered:
        return ('<div class="card jgc"><div class="tp"><div class="tx"><b>JGC（Life Status）<span class="est-tg">推定</span></b><small>記録した便から・国内線は1回 5</small>'
                '<div class="bar"><i style="width:%.1f%%"></i></div></div><div class="v"><span class="num">%d</span><span class="u">／1,500</span></div></div>'
                '<div class="in-row"><small>前の年の搭乗や JAL カードの分は入っていません</small><span class="pill">今の数を入れる</span></div></div>') % (LS_NOW / LS_GOAL * 100, LS_NOW)
    left = LS_GOAL - LS_IN - LS_NOW
    return ('<div class="card jgc"><div class="tp"><div class="tx"><b>JGC（Life Status）</b><small>入れた数 %s ＋ そのあとの便 %d</small>'
            '<div class="bar"><i class="in" style="width:%.1f%%"></i><i style="width:%.1f%%"></i></div></div><div class="v"><span class="num">%s</span><span class="u">／1,500</span>'
            '<small style="display:block;font-size:13px;color:var(--sub);font-weight:700">あと %d回</small></div></div></div>') % (
        c(LS_IN), LS_NOW, LS_IN / LS_GOAL * 100, LS_NOW / LS_GOAL * 100, c(LS_IN + LS_NOW), (left + 4) // 5)

def eb3(night=False, empty=False, entered=False):
    lit = ' lit' if night else ''
    nxt = YOTEI[0]
    s = header(band='道のり') + '''
<div class="card hero" style="margin-top:8px"><div class="lab"><span class="tg" style="background:var(--wash);color:var(--strong)">実績</span>&nbsp;2026年・記録した便<span>目標 クリスタル</span></div>
<div class="big"><span class="num%s">%s</span><span class="u">FOP</span></div>
<div class="gauge"><div class="bar"><i style="width:%.1f%%"></i></div><div class="gl"><span>ポイント %d%%</span><span>3万</span></div>
<div class="bar t"><i style="width:%d%%"></i></div><div class="gl"><span>1年 %d%%（今日 11/9）</span><span>12/31</span></div></div>
<p class="yr">1年の <b>%d%%</b> が過ぎて、ポイントは <b>%d%%</b>。%s</p></div>
<div class="two"><div class="card"><span class="k">FOP だけで</span><div class="ato"><span class="a">あと</span><span class="num">%s</span><span class="u">FOP</span></div><small>3万 FOP で届く</small></div>
<div class="card"><span class="k">30回＋1万 FOP で</span><div class="ato"><span class="a">あと</span><span class="num">%d</span><span class="u">回</span></div><small>1万 FOP は済み</small></div></div>
''' % (lit, c(FOP_NOW), FOP_NOW / GOAL * 100, PT, YEARP, YEARP, YEARP, PT,
       ('予定だけでは届かず、計画まで乗れば届きます（推定）' if not empty else '今のままのペースでは届きません（推定）'),
       c(LEFT), LEFT_N) + jgc_card(entered)
    if empty:
        s += '''<div class="sec-h">入れたら届くか<small>推定</small></div>
<div class="card empty"><p>乗る予定の便や、修行の計画を入れると、年末までに届くかを推定します。</p><div class="btn">計画を作る</div></div>
'''
        return s
    s += '''<div class="sec-h">入れたら届くか<small>推定</small></div>
<div class="est y"><div class="tx"><b>%s2便に乗ると</b><small>あと %s FOP・あと %d回</small></div><span><span class="num">＋%s</span></span></div>
<div class="est k"><div class="tx"><b>%s6便にも乗ると</b><small>FOP だけで届く（%s あまる）</small></div><span><span class="num">＋%s</span></span></div>
<p class="note">予定と計画は実績と分けて足しています。届くかは推定です。</p>
<div class="sec-h">次に乗る便<span class="r">予定と計画 ›</span></div>
<div class="card"><div class="row"><div class="tx"><b>11月22日（日）　羽田 → 那覇</b><small>%s・%s・<span class="tg tag-y">予定</span></small></div><span><span class="num%s" style="font-size:22px">＋%s</span><span class="u">FOP</span></span></div>
<div class="today"><span class="dot"></span><span>この路線の今日（11/9）　<b>%d便</b>・欠航なし</span></div></div>
''' % ('<span class="tg tag-y">予定</span>' if night else '予定の', c(LEFT - FOP_Y), LEFT_N - 2, c(FOP_Y),
       '<span class="tg tag-k">計画（残した案）</span>' if night else '計画（残した案）の', c(AFTER_K - GOAL), c(FOP_K), nxt['no'], nxt['fare'], ' amb' if night else '', c(fop(nxt)), TODAY_N)
    return s

def tools():
    return '''<div class="card lst" style="margin-top:10px"><div class="row"><div class="tx"><b>路線を入れて計算する</b><small>乗る前に FOP を確かめる</small></div><span class="r">›</span></div></div>'''

def ann(t, L):
    return '<div class="ann"><b>%s</b><ul>%s</ul></div>' % (t, ''.join('<li>%s</li>' % x for x in L))

def pE1():
    body = '<div class="wrap">' + eb3() + tools() + ann('E1 道のり（3版）', [
        '上の段（そらメモ・マイページ／スタンプラリー｜エアライン経営）をフライト・図鑑とそろえた（review-2 の3）。ANA｜JAL は題「修行」の横へ、「目標 クリスタル」は大きな数字のカードの右上へ移して、上の段が増えたぶんを詰めた。667 でも2つの道まで見える',
        'JGC（Life Status）は「推定」の札と「記録した便から」。前の年や JAL カードの分は入っていないと1行で書き、「今の数を入れる」を置く（review-2 の2）。入れた人は E1j',
        '今のアプリの JGC の数（80）と見本（100）の違いは、数える便の範囲の違い。どちらに合わせるかは修行担当が決める']) + '</div>' + tabs('修行')
    page(OUT + '/E1-overview-v3.html', 'E1 道のり 3版' + T, body, extra_css=CSS3)

def pE1j():
    body = '<div class="wrap">' + eb3(entered=True) + tools() + ann('E1j 今の Life Status を入れた人', [
        '会員情報に入れた数（見本 1,240）を灰の棒、そのあと記録した便（100）を濃い棒で足す',
        '「推定」の札は外す（入れた数は本人の会員情報の数）。入れた日より前の記録は二重に数えない',
        '入れる形にするか・入れた日をどう持つかは修行担当が決める（表がいるならデータ担当へ）']) + '</div>' + tabs('修行')
    page(OUT + '/E1j-ls-entered-v3.html', 'E1j Life Status を入れた人 3版' + T, body, extra_css=CSS3)

def pE1b():
    body = '<div class="wrap">' + eb3(empty=True) + tools() + ann('E1b 予定・計画が空の人（3版）', [
        '上の段と JGC の書き方を E1 とそろえた。ほかは2版のまま（一文と「計画を作る」1つ）']) + '</div>' + tabs('修行')
    page(OUT + '/E1b-empty-v3.html', 'E1b 予定・計画が空の人 3版' + T, body, extra_css=CSS3)

def pE3(night=False):
    bal = GOAL; cells = ''
    for m in range(1, 12):
        used = sum(fop(f) for f in JM.get(m, []))
        bal -= used
        cells += '<div><span class="mo">%s</span><span class="num">%s</span><small>%s</small></div>' % (('%d月末' % m) if m < 11 else '11月 今日まで', c(bal), ('ひいた ' + c(used)) if used else 'JAL の便なし')
    yb = bal - FOP_Y; kb = yb - FOP_K
    cells += '<div class="y"><span class="mo">11月 予定</span><span class="num">%s</span><small>ひく %s</small></div>' % (c(yb), c(FOP_Y))
    cells += '<div class="k"><span class="mo">12月 計画</span><span class="num">0</span><small>%s あまる</small></div>' % c(-kb)
    rt = {}
    for f in JALF: k = tuple(sorted((f['a'], f['b']))); rt[k] = rt.get(k, 0) + fop(f)
    allr = sorted(rt.items(), key=lambda x: -x[1])
    rk = ''.join('<div class="row"><div class="tx"><b>%s ⇄ %s</b><small>%d回</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>' % (
        short(k[0]), short(k[1]), sum(1 for f in JALF if tuple(sorted((f['a'], f['b']))) == k), c(v)) for k, v in allr[:3])
    rk += '<div class="row"><div class="tx"><b>すべての路線</b><small>%d路線</small></div><span class="r">›</span></div>' % len(allr)
    n_y = LEFT_N - len(YOTEI); n_k = max(0, n_y - len(KEIKAKU))
    if night:
        a = ann('夜の月ごと（3版）', ['予定の月の地は金をやめ、暗い灰に点線の縁。計画は細い実線の縁（どちらも字で「予定」「計画」）'])
    else:
        a = ann('E3 月ごと（3版）', ['上の段を E1 とそろえた', '年末の残りの3行の右に「回数 あと 10 → 8 → 2」（30回＋1万 FOP の道。review-2 の4）',
                                   '「JAL の便なし」の字をほかの補足と同じ濃さに（4.5:1 以上。review-2 の5）', '路線ごとは3つのあとに「すべての路線（%d路線）›」（review-2 の6）' % len(allr)])
    body = '''<div class="wrap">%s
<div class="card rc" style="margin-top:10px"><span class="k">12月31日の残り（クリスタルまで・推定）</span>
<div class="rr"><div class="tx">実績のまま<small>このあと乗らなければ</small></div><span><span class="num">%s</span><span class="u">FOP</span></span><span class="n2">回数 あと<b>%d</b></span></div>
<div class="rr"><div class="tx">予定の2便に乗ると<small>11/22・11/24</small></div><span><span class="num">%s</span><span class="u">FOP</span></span><span class="n2">回数 あと<b>%d</b></span></div>
<div class="rr"><div class="tx">計画の6便にも乗ると<small>%s FOP あまって届く</small></div><span><span class="num">0</span><span class="u">FOP</span></span><span class="n2">回数 あと<b>%d</b></span></div></div>
<div class="sec-h">月末の残り<small>3万 FOP から・実績</small><span class="r">1回 平均 %s</span></div><div class="yr12">%s</div>
<p class="note">%s</p>
<div class="sec-h">路線ごと<small>実績</small></div><div class="card lst">%s</div>
%s</div>''' % (
        header(band='月ごと'), c(LEFT), LEFT_N, c(yb), n_y, c(-kb), n_k, c(FOP_NOW // CNT_NOW), cells,
        '縁のついた2つは予定と計画（実績の月とは分けて、最後に足す）。' if night else '色の地の2つは予定と計画（実績の月とは分けて、最後に足す）。', rk, a) + tabs('修行')
    if night:
        page(OUT + '/N3-months-night-v3.html', 'N3 夜の月ごと 3版' + T, body, night=True, extra_css=CSS3 + NCSS)
    else:
        page(OUT + '/E3-months-v3.html', 'E3 月ごと 3版' + T, body, extra_css=CSS3)

def p07():
    css = CSS3 + MP.CSS07 + """.sh-h{font-size:15px;font-weight:800;color:var(--strong);margin:16px 4px 6px}"""
    def rows(L):
        return ''.join('<div class="vrow">%s<div class="tx"><b>%s</b><small>%s</small></div><span class="sw %s">%s</span>%s</div>' % (
            ('<span class="n">%s</span>' % n) if n is not None else '', a, b, o, o.upper(), ('<span style="color:var(--pale)">%s</span>' % I['grip']) if n is not None else '') for a, b, o, n in L)
    v = [('道のり', '大きな数字・2つの道・届くか', 'on', '1'), ('1便ごと', '1便の FOP と内訳', 'on', '2'), ('月ごと', '月末の残り・路線ごと', 'on', '3')]
    d = [('2つの道', 'FOP だけで／30回＋1万 FOP で', 'on', None), ('JGC（Life Status）', '生涯 1,500 まで', 'off', None), ('入れたら届くか', '予定と計画を足した推定', 'on', None), ('次に乗る便', 'この路線の今日の便数つき', 'on', None)]
    body = '<div class="wrap">' + eb3() + '</div><div class="dim"></div><div class="sheet"><div class="grab"></div><div style="font-size:18px;font-weight:800;color:var(--strong);margin:0 4px">見方を選ぶ</div>' + \
        '<div class="sh-h">見方</div><div class="card">%s</div><div class="sh-h">道のりに出すもの</div><div class="card">%s</div>' % (rows(v), rows(d)) + \
        '<p class="note">目指さないものは OFF にできます。</p></div>' + tabs('修行')
    page(OUT + '/07-views-v3.html', '07 見方を選ぶ 3版' + T, body, extra_css=css)

def pN1():
    body = '<div class="wrap">' + eb3(night=True) + tools() + ann('夜の画面（E1 3版）', [
        '「予定」の金をやめた（11/9 の決定「夜は会社の色と金を使わない」。review-2 の1）。予定は札の字「予定」と点線の縁、計画は札の字「計画」と細い実線の縁。地はどちらも暗い灰',
        '光るのは実績の FOP（緑）と次に乗る便の FOP（琥珀＝「次」）だけ。予定の帯には琥珀も使わない',
        '上の段・JGC の書き方は昼と同じ']) + '</div>' + tabs('修行')
    page(OUT + '/N1-overview-night-v3.html', 'N1 夜の画面 3版' + T, body, night=True, extra_css=CSS3 + NCSS)

def pN1b():
    body = '<div class="wrap">' + eb3(night=True, empty=True) + tools() + '</div>' + tabs('修行')
    page(OUT + '/N1b-empty-night-v3.html', 'N1b 夜・予定が空 3版' + T, body, night=True, extra_css=CSS3 + NCSS)

for fn in (pE1, pE1j, pE1b, pE3, p07, pN1, pN1b): fn()
pE3(night=True)
print('ok', FOP_NOW, LEFT, LEFT_N, LS_NOW, AFTER_K - GOAL)
