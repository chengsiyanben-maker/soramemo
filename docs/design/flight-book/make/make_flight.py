# -*- coding: utf-8 -*-
# フライトの改善案（design/flight-book）を作る。使い方：python3 make_flight.py <出力先>
import sys, math
sys.path.insert(0, '/tmp/claude-0/gen')
from common import *
OUT = sys.argv[1]
T = '｜フライトの改善案（画面案）'
SHOT = '/tmp/claude-0/shots/'
MON = {}
for f in F: MON.setdefault(f['m'], []).append(f)

def shots(L):
    from PIL import Image
    out = '<div class="shots">'
    k = 358 / 390
    for path, t, b, lab, mk in L:
        im = Image.open(path).crop((0, t, 390, b)); tmp = '/tmp/claude-0/crop.png'; im.save(tmp)
        out += '<div class="shot"><img src="%s" alt="%s">%s<p>%s</p></div>' % (img64(tmp, 72), lab, ''.join(mark(n, x * k, (y - t) * k) for n, x, y in mk), lab)
    return out + '</div>'
def mark(n, x, y):
    return '<i class="mk" style="left:%dpx;top:%dpx">%d</i>' % (x, y, n)

# ---------- 01 今の見にくい所 ----------
def p01():
    css = """.shots{margin-top:8px}.shot{position:relative;margin-top:10px}.shot img{width:100%;border-radius:18px;box-shadow:var(--shadow);display:block}
.shot p{font-size:13px;color:var(--sub);margin:6px 2px 0;text-align:center}
.mk{position:absolute;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:#C2410C;color:#fff;font:800 14px/26px var(--gothic);text-align:center;font-style:normal;box-shadow:0 0 0 3px #fff}
ol.pb{margin:16px 0 0;padding:0;list-style:none;counter-reset:p}ol.pb li{counter-increment:p;position:relative;padding:12px 14px 12px 50px;background:var(--card);border-radius:18px;box-shadow:var(--shadow);margin-top:8px;font-size:14px;line-height:1.65}
ol.pb li::before{content:counter(p);position:absolute;left:14px;top:12px;width:26px;height:26px;border-radius:50%;background:#C2410C;color:#fff;font:800 14px/26px var(--gothic);text-align:center}
ol.pb b{color:var(--strong)}"""
    body = '''<div class="wrap"><div class="top"><h1>01 今の見にくい所</h1></div>
<p class="note" style="margin-top:0">main の web/ をデモ（見本の記録 30便）で開き、フライトのタブを幅390で撮った。上が高さ 844 の下半分、下が 667 の下半分。</p>
''' + shots([(SHOT + 'log-844.png', 380, 844, '高さ 844（下半分）', [(2, 360, 600), (3, 232, 540), (4, 360, 700), (5, 300, 497)]),
              (SHOT + 'log-667.png', 300, 667, '高さ 667（下半分）', [(1, 195, 560)])]) + '''
<ol class="pb">
<li><b>667 では開いたときに1便も見えない。</b>地図・凡例・数字の行・2段の切り替えでシートの上半分が埋まり、最初のカードはタブ帯の後ろ</li>
<li><b>切り替えが2段。</b>「一覧・年ごと・記録帳」のピルの下に、9つの見方の帯（修行・搭乗券・案内板・地図・カレンダー・月ごと・高度・文字だけ・路線）。横に送らないと「月ごと」から右が見えない</li>
<li><b>「記録帳」は見方ではなく入力の画面。</b>過去の便を足す欄で、右上の ＋ と同じ仕事が2か所にある</li>
<li><b>1便のカードが大きい。</b>844 でも1便半。日付は右端の小さな字で、月の区切りがなく「いつの便か」を目で追いにくい</li>
<li><b>今年の様子が一覧から見えない。</b>便・距離の数はあるが、空の上の時間・月ごとの回数・よく乗った路線は「年ごと」の中</li>
</ol></div>'''
    page(OUT + '/01-now-problems.html', '01 今の見にくい所' + T, body, extra_css=css)

# ---------- A 正攻法：航空日誌 ----------
CSS_A = """
.yr{padding:16px 18px;display:flex;gap:6px;align-items:flex-end}
.yr .k{font-size:13px;color:var(--sub);font-weight:700;display:block;margin-bottom:6px}
.yr > div{flex:1}.yr .num{font-size:34px}
.spark{display:flex;gap:3px;align-items:flex-end;height:30px;margin:0 18px 14px;padding-top:4px}
.spark i{flex:1;background:var(--navy);border-radius:3px 3px 1px 1px;opacity:.9}.spark i.z{background:var(--line2);height:3px!important}
.mlab{display:flex;gap:3px;margin:-10px 18px 14px}.mlab span{flex:1;text-align:center;font-size:13px;color:var(--mute)}
.mh{display:flex;align-items:baseline;gap:8px;margin:20px 6px 6px}.mh b{font-size:17px;color:var(--strong)}.mh small{font-size:13px;color:var(--sub);font-weight:700}
.mh .r{margin-left:auto;font-size:13px;color:var(--sub)}
.lg{overflow:hidden}
.lr{display:grid;grid-template-columns:46px 1fr auto;gap:10px;align-items:center;min-height:64px;padding:8px 16px;position:relative}
.lr + .lr{box-shadow:inset 0 1px 0 var(--line2)}
.lr .dt{text-align:center;line-height:1.1}.lr .dt .num{font-size:24px;display:block}.lr .dt small{font-size:13px;color:var(--sub);font-weight:700}
.lr .rt{display:flex;align-items:center;gap:6px;font-family:var(--sign);font-weight:700;font-size:22px;color:var(--strong);line-height:1.1}
.lr .rt svg{color:var(--pale)}
.lr .sb{font-size:13px;color:var(--sub);line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lr .tm{text-align:right;line-height:1.2}.lr .tm .num{font-size:20px}.lr .tm small{display:block;font-size:13px;color:var(--sub);font-weight:700;margin-top:2px}
.lr::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:4px;border-radius:0 3px 3px 0;background:var(--cc)}
"""
def lrow(f):
    return ('<div class="lr" style="--cc:%s"><div class="dt"><span class="num">%d</span><small>%s</small></div>'
            '<div style="min-width:0"><div class="rt">%s%s%s</div><div class="sb">%s → %s・%s %s</div></div>'
            '<div class="tm"><span class="num">%s</span><small>%s km</small></div></div>') % (
        CO_COL[f['co']], f['d'], f['wd'], f['a'], I['arrow'], f['b'], short(f['a']), short(f['b']), f['no'], f['typ'], hm(f['mins']), c(f['km']))
def head_flight(band_on, night=False):
    bands = [('日誌', 'log'), ('地図', 'map'), ('年のまとめ', 'yr')]
    vb = ''.join('<span class="pill%s">%s</span>' % (' on' if k == band_on else '', n) for n, k in bands)
    return ('<div class="top"><h1>フライト</h1><span class="pill ic" aria-label="搭乗券を読み取る">%s</span><span class="pill ic dark" aria-label="フライトを足す">%s</span></div>'
            '<div class="vband">%s<span class="pill ed" aria-label="見方を選ぶ">%s</span></div>') % (I['scan'], I['plus'], vb, I['pen'])
def year_card(night=False):
    cnt = [len(MON.get(m, [])) for m in range(1, 13)]
    mx = max(cnt)
    sp = ''.join('<i style="height:%d%%"%s></i>' % (max(10, v * 100 // mx), '' if v else ' class="z"') for v in cnt)
    lab = ''.join('<span>%s</span>' % (m if m in (1, 4, 7, 10) else '') for m in range(1, 13))
    lit = ' lit' if night else ''
    return ('<div class="card" style="margin-top:12px"><div class="yr"><div><span class="k">2026年</span><span class="num%s">%d</span><span class="u">便</span></div>'
            '<div><span class="k">距離</span><span class="num">%s</span><span class="u">km</span></div><div><span class="k">空の上</span><span class="num">%d</span><span class="u">時間</span></div></div>'
            '<div class="spark" aria-label="月ごとの便の数">%s</div><div class="mlab">%s</div></div>') % (lit, len(F), c(TOTAL_KM), TOTAL_MIN // 60, sp, lab)
def logbody(night=False):
    s = '<div class="wrap">' + head_flight('log', night) + year_card(night)
    for m in sorted(MON, reverse=True)[:4]:
        L = MON[m]
        s += '<div class="mh"><b>%d月</b><small>%d便</small><span class="r">%s km</span></div><div class="card lg">%s</div>' % (m, len(L), c(sum(f['km'] for f in L)), ''.join(lrow(f) for f in L))
    return s
def pA1():
    body = logbody() + '''<div class="ann"><b>A 正攻法「航空日誌」</b><ul><li>1便を高さ 64px の1行に（日付・区間・時間を左から）。844 で5便、667 で2便見える（今は 844 で1便半・667 で0便）</li><li>今年の数字と月ごとの小さな棒をいちばん上の1枚に</li><li>見方の帯は「日誌・地図・年のまとめ」の3つ。足すのは右上の ＋ だけ</li><li>左の細い色は会社（JAL赤・ANA青を控えめに）</li></ul></div></div>''' + tabs('フライト')
    page(OUT + '/A1-log.html', 'A1 航空日誌' + T, body, extra_css=CSS_A)
def vbox(x1, y1, x2, y2):
    w = max(abs(x2 - x1) + 50, (abs(y2 - y1) + 36) * 358 / 150); h = w * 150 / 358
    return '%.1f %.1f %.1f %.1f' % ((x1 + x2) / 2 - w / 2, (y1 + y2) / 2 - h / 2, w, h)
def pA2():
    f = F[0]
    k = [x for x in F if {x['a'], x['b']} == {f['a'], f['b']}]
    x1, y1 = proj(f['a']); x2, y2 = proj(f['b'])
    css = CSS_A + """.big{display:flex;align-items:center;justify-content:space-between;padding:18px 20px 6px}.big .num{font-size:52px}.big small{display:block;font-size:13px;color:var(--sub);font-weight:700;margin-top:6px}
.big .mid{color:var(--pale)}.tms{display:flex;justify-content:space-between;padding:0 20px 18px;font-size:14px;color:var(--sub)}.tms b{font-family:var(--sign);font-size:22px;color:var(--strong)}
.dl{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.dl > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px}
.dl .k{font-size:13px;color:var(--sub);font-weight:700}.dl .v{margin-top:4px;font-family:var(--sign);font-weight:700;font-size:26px;color:var(--strong);line-height:1.1}.dl .v small{display:block;font-family:var(--gothic);font-size:13px;color:var(--sub);font-weight:600;margin-top:2px}
.mapc{margin-top:10px;padding:0;overflow:hidden;height:150px}"""
    body = '''<div class="wrap"><div class="top"><span class="pill">%s フライト</span><span style="margin-left:auto" class="pill ic" aria-label="直す">%s</span></div>
<div class="card"><p class="note" style="margin:14px 20px 0;font-weight:700">2026年%d月%d日（%s）・%s</p>
<div class="big"><div><span class="num">%s</span><small>%s</small></div><span class="mid">%s</span><div style="text-align:right"><span class="num">%s</span><small>%s</small></div></div>
<div class="tms"><span>出発 <b>%s</b></span><span>到着 <b>%s</b></span></div></div>
<div class="dl"><div><div class="k">空の上</div><div class="v">%s<small>時間:分</small></div></div><div><div class="k">距離</div><div class="v">%s<span class="u">km</span><small>区間 %s マイル</small></div></div>
<div><div class="k">機体</div><div class="v">%s<small>%s</small></div></div><div><div class="k">座席</div><div class="v">%s<small>記録した席</small></div></div></div>
<div class="card mapc"><svg viewBox="%s" width="100%%" height="150" aria-label="区間の地図" preserveAspectRatio="xMidYMid slice">%s<path d="M%.1f %.1fQ%.1f %.1f %.1f %.1f" fill="none" stroke="#16233A" stroke-width="1.6" stroke-linecap="round"/><circle cx="%.1f" cy="%.1f" r="2.6" fill="#fff" stroke="#16233A" stroke-width="1.4"/><circle cx="%.1f" cy="%.1f" r="2.6" fill="#fff" stroke="#16233A" stroke-width="1.4"/></svg></div>
<div class="sec-h">この区間の便<small>%s ⇄ %s</small><span class="r">%d回</span></div>
<div class="card">%s</div>
<div class="ann"><b>A2 1便の詳しい所</b><ul><li>日誌の1行を押すと開く。大きいのは区間と時刻だけ、ほかは4つの枠</li><li>「この区間」に同じ路線の前の便を並べる（路線の見方を兼ねる）</li><li>登録記号は乗った機体の記録（事実）として出す。分からない便は機種だけ</li></ul></div></div>''' % (
        I['back'], I['pen'], f['m'], f['d'], f['wd'], f['no'], f['a'], short(f['a']), I['arrow'], f['b'], short(f['b']), f['dep'], f['arr'],
        hm(f['mins']), c(f['km']), c(f['tpm']), f['reg'], f['typ'], f['seat'],
        vbox(x1, y1, x2, y2), jpmap(), x1, y1, (x1 + x2) / 2 + 12, (y1 + y2) / 2 - 6, x2, y2, x1, y1, x2, y2,
        short(f['a']), short(f['b']), len(k), ''.join(lrow(x) for x in k[:4])) + tabs('フライト')
    page(OUT + '/A2-flight.html', 'A2 1便の詳しい所' + T, body, extra_css=css)
def pA3():
    cnt = [len(MON.get(m, [])) for m in range(1, 13)]
    kms = [sum(f['km'] for f in MON.get(m, [])) for m in range(1, 13)]
    mx = max(kms)
    bars = ''
    for m in range(1, 13):
        h = kms[m - 1] * 120 // mx if kms[m - 1] else 3
        bars += '<div class="b"><span class="v">%s</span><i style="height:%dpx"%s></i><span class="l">%d</span></div>' % (cnt[m - 1] or '', h, '' if kms[m - 1] else ' class="z"', m)
    rt = {}
    for f in F: rt.setdefault(tuple(sorted((f['a'], f['b']))), []).append(f)
    top = sorted(rt.items(), key=lambda x: -len(x[1]))[:3]
    co = {}
    for f in F: co[f['co'] if f['co'] != 'JTA' else 'JAL'] = co.get(f['co'] if f['co'] != 'JTA' else 'JAL', 0) + 1
    css = CSS_A + """.bars{display:flex;gap:4px;align-items:flex-end;height:170px;padding:14px 14px 10px}.bars .b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bars i{width:100%;background:var(--navy);border-radius:4px 4px 2px 2px}.bars i.z{background:var(--line2)}.bars .v{font-family:var(--sign);font-weight:700;font-size:14px;color:var(--strong);margin-bottom:3px}.bars .l{font-size:13px;color:var(--mute);margin-top:4px}
.cobar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:6px 16px 4px}.cobar i{display:block}
.colg{display:flex;gap:16px;padding:6px 16px 14px;font-size:13px;color:var(--sub)}.colg b{font-family:var(--sign);font-size:18px;color:var(--strong);margin-left:4px}
.rk{display:flex;align-items:center;gap:12px;min-height:56px;padding:6px 16px}.rk + .rk{box-shadow:inset 0 1px 0 var(--line2)}.rk .n{font-family:var(--sign);font-size:22px;font-weight:700;color:var(--pale);width:18px}
.rk .tx{flex:1}.rk .tx b{display:block;font-size:15px;color:var(--strong)}.rk .tx small{font-size:13px;color:var(--sub)}.rk .num{font-size:24px}"""
    rks = ''.join('<div class="rk"><span class="n">%d</span><div class="tx"><b>%s ⇄ %s</b><small>%s ⇄ %s・%s km</small></div><span><span class="num">%d</span><span class="u">回</span></span></div>' % (
        i + 1, short(k[0]), short(k[1]), k[0], k[1], c(v[0]['km']), len(v)) for i, (k, v) in enumerate(top))
    body = '<div class="wrap">' + head_flight('yr') + year_card() + '''
<div class="sec-h">月ごとの距離<small>棒の上は便の数</small></div><div class="card"><div class="bars">%s</div></div>
<div class="sec-h">よく乗った路線</div><div class="card">%s</div>
<div class="sec-h">会社</div><div class="card" style="padding-top:12px"><div class="cobar"><i style="flex:%d;background:var(--jal)"></i><i style="flex:%d;background:var(--ana)"></i></div><div class="colg"><span>JAL グループ<b>%d</b></span><span>ANA<b>%d</b></span></div></div>
<div class="ann"><b>A3 年のまとめ</b><ul><li>今の「年ごと」「月ごと」「高度」「文字だけ」をここに1枚でまとめる</li><li>年の切り替えは題の横のピル（2026 ›）。去年と比べる行は出さない（数字だけ並べる）</li></ul></div></div>''' % (
        bars, rks, co.get('JAL', 0), co.get('ANA', 0), co.get('JAL', 0), co.get('ANA', 0)) + tabs('フライト')
    page(OUT + '/A3-year.html', 'A3 年のまとめ' + T, body, extra_css=css)

# ---------- B 斬新：1本の長い紙の航跡 ----------
CSS_B = """
body{background:#E9E4D8}.phone{background:#E9E4D8}
.top h1{font-family:var(--gothic)}
.tape{position:relative;margin:8px -16px 0;height:330px;overflow:hidden}
.tape .roll{position:absolute;left:0;top:0;height:330px;background:#FBF8F0;background-image:repeating-linear-gradient(90deg,transparent 0 11px,rgba(120,100,60,.10) 11px 12px),repeating-linear-gradient(0deg,transparent 0 29px,rgba(120,100,60,.10) 29px 30px);box-shadow:0 2px 0 #D9D1BD,0 14px 30px -18px rgba(60,40,10,.5)}
.tape .roll::before,.tape .roll::after{content:"";position:absolute;left:0;right:0;height:10px;background:radial-gradient(circle at 6px 5px,#E9E4D8 2.5px,transparent 3px) 0 0/12px 10px}
.tape .roll::before{top:6px}.tape .roll::after{bottom:6px}
.tape svg{position:absolute;left:0;top:0}
.fade{position:absolute;top:0;bottom:0;width:36px;z-index:2}.fade.l{left:0;background:linear-gradient(90deg,#E9E4D8,rgba(233,228,216,0))}.fade.r{right:0;background:linear-gradient(-90deg,#E9E4D8,rgba(233,228,216,0))}
.ovw{margin:12px 0 0;padding:12px 14px}.ovw .k{font-size:13px;color:#5B5140;font-weight:700;display:flex}.ovw .k span{margin-left:auto}
.ovw svg{display:block;margin-top:6px}
.card{background:#FFFDF8;box-shadow:0 1px 0 #D9D1BD,0 10px 24px -16px rgba(60,40,10,.4)}
.sel{display:flex;gap:14px;align-items:center;padding:14px 16px;margin-top:12px}
.sel .num{font-size:30px}.sel .tx{flex:1}.sel .tx small{display:block;font-size:13px;color:var(--sub)}
.ann{background:#FFF6DC}
.tabs{background:rgba(255,253,248,.97)}
"""
SEQ = list(reversed(F))   # 古い順
def tape_svg(W, H, x0, slot, hi=None, times=False):
    # 1便＝1こま（幅 slot）。山の形は上昇・巡航・降下、高さは距離、巡航の長さは空の上の時間
    s = '<svg width="%d" height="%d" viewBox="0 0 %d %d" aria-label="1年の航跡の紙">' % (W, H, W, H)
    base = H - 74
    s += '<path d="M0 %d H%d" stroke="#4A3F2A" stroke-width="1.4"/>' % (base, W)
    pm = None
    for i, f in enumerate(SEQ):
        x = i * slot - x0
        if f['m'] != pm:
            if -60 < x < W:
                s += '<path d="M%.1f 24V%d" stroke="#8A7A58" stroke-width="1" stroke-dasharray="2 3"/><text x="%.1f" y="42" font-size="15" font-weight="800" fill="#4A3F2A">%d月</text>' % (x + 2, base + 8, x + 8, f['m'])
            pm = f['m']
        if x + slot < -10 or x > W + 10: continue
        on = hi is not None and f is hi
        ht = 40 + f['km'] / 1600 * 130
        cl = slot * .22; cr = slot * (.2 + min(.42, f['mins'] / 170 * .42)); x1 = x + 12; x4 = x + slot - 8
        x2 = x1 + cl * .8; x3 = min(x4 - 10, x2 + cr)
        col = '#C2410C' if on else ('#16233A' if f['co'] != 'ANA' else '#2D4F86')
        s += '<path d="M%.1f %dL%.1f %.1fL%.1f %.1fL%.1f %d" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (
            x1, base, x2, base - ht, x3, base - ht, x4, base, 'rgba(194,65,12,.14)' if on else 'rgba(22,35,58,.08)', col, '3' if on else '2')
        s += '<text x="%.1f" y="%.1f" font-size="15" font-weight="700" fill="#2B2416" text-anchor="middle" font-family="var(--sign)">%s</text>' % ((x2 + x3) / 2, base - ht - 8, f['b'])
        s += '<text x="%.1f" y="%d" font-size="14" font-weight="700" fill="#4A3F2A" text-anchor="middle" font-family="var(--sign)">%d/%d</text>' % ((x1 + x4) / 2, base + 22, f['m'], f['d'])
        if times:
            s += '<text x="%.1f" y="%d" font-size="13" fill="#5B5140" text-anchor="start">%s</text><text x="%.1f" y="%d" font-size="13" fill="#5B5140" text-anchor="end">%s</text>' % (x1 - 4, base + 42, f['dep'], x4 + 4, base + 42, f['arr'])
    s += '<text x="16" y="%d" font-size="13" fill="#5B5140">山の高さ＝距離　平らな所＝空の上の時間</text>' % (H - 16)
    return s + '</svg>'
def overview(x0, slot, W):
    import datetime
    ov = '<svg width="330" height="36" viewBox="0 0 330 36">'
    n = len(SEQ); step = 330 / n
    for i, f in enumerate(SEQ):
        ov += '<path d="M%.1f 30V%.1f" stroke="#16233A" stroke-width="3" stroke-linecap="round"/>' % (i * step + step / 2, 30 - 6 - f['km'] / 1600 * 18)
    ov += '<rect x="%.1f" y="1" width="%.1f" height="33" rx="6" fill="none" stroke="#C2410C" stroke-width="2"/><path d="M0 30.5H330" stroke="#8A7A58"/></svg>' % (x0 / slot * step, W / slot * step)
    return ov
def pB1():
    W = 390; slot = 78
    x0 = (len(SEQ) - 5) * slot + 14 - 30
    x0 = len(SEQ) * slot - W + 20
    body = '''<div class="wrap"><div class="top"><h1>フライト</h1><span class="pill ic">%s</span><span class="pill ic dark">%s</span></div>
<p class="note" style="margin-top:0">左へ送ると、1月までさかのぼれます</p>
<div class="tape"><div class="roll" style="width:%dpx">%s</div><div class="fade l"></div></div>
<div class="card ovw"><div class="k">2026年の全部<span>%d便</span></div>%s</div>
<div class="card sel"><div><span class="num">%s → %s</span></div><div class="tx"><b>11月3日（火）・%s</b><small>%s・%s km・%s</small></div></div>
<div class="ann"><b>B 斬新「1本の長い紙の航跡」</b><ul><li>1年を1本の記録紙にして横に送る。1便が1こまの山（上昇・巡航・降下の形）</li><li>下の細い帯が1年の全部。赤い枠がいま見ている所</li><li>外した決まり：紙の地の色・方眼の細い線・ミシン目（黒い区切り線を使わないに当たる）</li></ul></div></div>''' % (
        I['scan'], I['plus'], W, tape_svg(W, 330, x0, slot), len(F), overview(x0, slot, W), F[0]['a'], F[0]['b'], F[0]['no'], hm(F[0]['mins']), c(F[0]['km']), F[0]['typ']) + tabs('フライト')
    page(OUT + '/B1-tape.html', 'B1 1本の長い紙の航跡' + T, body, extra_css=CSS_B)
def pB2():
    W = 390; slot = 130
    target = [x for x in SEQ if x['m'] == 7 and x['a'] == 'HND'][0]
    i = SEQ.index(target)
    x0 = (i - 1) * slot - 14
    css = CSS_B + """.dl{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px}.dl > div{padding:12px}.dl .k{font-size:13px;color:var(--sub);font-weight:700}.dl .num{font-size:24px;display:block;margin-top:4px}"""
    body = '''<div class="wrap"><div class="top"><span class="pill">%s 1年の紙</span><span style="margin-left:auto;font-size:13px;color:var(--sub);font-weight:700">2本の指で広げたところ</span></div>
<div class="tape"><div class="roll" style="width:%dpx">%s</div><div class="fade l"></div><div class="fade r"></div></div>
<div class="card sel"><div><span class="num">%s → %s</span></div><div class="tx"><b>7月4日（土）・%s</b><small>%s %s → %s %s</small></div></div>
<div class="dl"><div class="card"><span class="k">空の上</span><span class="num">%s</span></div><div class="card"><span class="k">距離</span><span class="num">%s<span class="u">km</span></span></div><div class="card"><span class="k">機体</span><span class="num" style="font-size:20px">%s</span></div></div>
<div class="ann"><b>B2 1便の詳しい所</b><ul><li>押した山が赤くなり、紙の下にその便のカード。カードを押すと A2 と同じ詳しい所</li><li>広げると、こまの下に出発と到着の時刻が出る</li></ul></div></div>''' % (
        I['back'], W, tape_svg(W, 330, x0, slot, hi=target, times=True), target['a'], target['b'], target['no'], short(target['a']), target['dep'], short(target['b']), target['arr'], hm(target['mins']), c(target['km']), target['reg']) + tabs('フライト')
    page(OUT + '/B2-tape-flight.html', 'B2 紙の上の1便' + T, body, extra_css=css)

# ---------- C 斬新：時計の文字盤 ----------
CSS_C = """
.dial{display:flex;justify-content:center;margin-top:8px}
.big3{display:flex;gap:8px;margin-top:12px}.big3 > div{flex:1;padding:12px 14px}.big3 .k{font-size:13px;color:var(--sub);font-weight:700;display:block}.big3 .num{font-size:26px;display:block;margin-top:4px}
"""
def dial(sz=330, hi=None, night=False):
    cx = cy = sz / 2; R0 = sz / 2 - 44
    ink = '#DCE3EA' if night else '#16233A'
    s = '<svg width="%d" height="%d" viewBox="0 0 %d %d" aria-label="乗った便を24時間の文字盤に並べた図">' % (sz, sz, sz, sz)
    s += '<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % (cx, cy, sz / 2 - 8, '#0D1218' if night else '#FFFFFF')
    def pt(h, r):
        a = (h / 24) * 2 * math.pi - math.pi / 2
        return cx + r * math.cos(a), cy + r * math.sin(a)
    # 時の目盛り
    for h in range(24):
        x1, y1 = pt(h, sz / 2 - 14); x2, y2 = pt(h, sz / 2 - (24 if h % 6 == 0 else 19))
        s += '<path d="M%.1f %.1fL%.1f %.1f" stroke="%s" stroke-width="%s"/>' % (x1, y1, x2, y2, '#7A8390' if not night else '#4A5664', 2 if h % 6 == 0 else 1)
    for h in (0, 6, 12, 18):
        x, y = pt(h, sz / 2 - 36)
        s += '<text x="%.1f" y="%.1f" font-size="15" font-weight="800" text-anchor="middle" dominant-baseline="central" fill="%s" font-family="var(--sign)">%d</text>' % (x, y, '#4B5563' if not night else '#8996A7', h)
    # 便を弧に（内側から順に重ねる）
    ring = {}
    for i, f in enumerate(sorted(F, key=lambda f: f['dep'])):
        h1, m1 = map(int, f['dep'].split(':')); h2, m2 = map(int, f['arr'].split(':'))
        a, b = h1 + m1 / 60, h2 + m2 / 60
        lane = 0
        while any(not (b <= x or a >= y) for x, y in ring.get(lane, [])): lane += 1
        ring.setdefault(lane, []).append((a, b))
        r = R0 - lane * 5.4
        x1, y1 = pt(a, r); x2, y2 = pt(b, r)
        large = 1 if (b - a) > 12 else 0
        on = hi is not None and int(a) == hi
        col = ('#C2410C' if on else ink) if not night else ('#5FD993' if on else '#6E7B8C')
        op = 1 if (hi is None or on) else .28
        s += '<path d="M%.1f %.1fA%.1f %.1f 0 %d 1 %.1f %.1f" fill="none" stroke="%s" stroke-width="4.4" stroke-linecap="round" opacity="%.2f"/>' % (x1, y1, r, r, large, x2, y2, col, op)
    return s
def hourcount():
    h = {}
    for f in F: h[int(f['dep'][:2])] = h.get(int(f['dep'][:2]), 0) + 1
    return h
def pC1(night=False):
    hc = hourcount(); top = max(hc, key=hc.get)
    early = min(F, key=lambda f: f['dep']); late = max(F, key=lambda f: f['arr'])
    sz = 330
    d = dial(sz, night=night)
    d += '<text x="165" y="146" font-size="15" font-weight="700" text-anchor="middle" fill="%s">いちばん多い</text>' % ('#4B5563' if not night else '#8996A7')
    d += '<text x="165" y="186" font-size="40" font-weight="700" text-anchor="middle" fill="%s" font-family="var(--sign)">%d時台</text>' % ('#111827' if not night else '#5FD993', top)
    d += '<text x="165" y="212" font-size="15" font-weight="700" text-anchor="middle" fill="%s">%d便</text></svg>' % ('#4B5563' if not night else '#8996A7', hc[top])
    body = '''<div class="wrap"><div class="top"><h1>フライト</h1><span class="pill ic">%s</span><span class="pill ic dark">%s</span></div>
<div class="vband"><span class="pill">日誌</span><span class="pill on">時計</span><span class="pill">地図</span><span class="pill ed">%s</span></div>
<div class="dial">%s</div>
<div class="big3"><div class="card"><span class="k">いちばん早い出発</span><span class="num">%s</span><small class="note" style="margin:2px 0 0;display:block">%s → %s</small></div><div class="card"><span class="k">いちばん遅い到着</span><span class="num">%s</span><small class="note" style="margin:2px 0 0;display:block">%s → %s</small></div></div>
<div class="ann"><b>C 斬新「乗った便を時計の文字盤に」</b><ul><li>1便を出発から到着までの弧にして、24時間の文字盤に並べる。重なるほど内側へ</li><li>朝の便が多い人・夕方に帰る人が、1枚で分かる</li><li>外した決まり：数字を大きく並べる形でなく図が主役。目盛りの細い線</li></ul></div></div>''' % (
        I['scan'], I['plus'], I['pen'], d, early['dep'], short(early['a']), short(early['b']), late['arr'], short(late['a']), short(late['b'])) + tabs('フライト')
    page(OUT + '/C1-clock.html', 'C1 時計の文字盤' + T, body, extra_css=CSS_C)
def pC2():
    hc = hourcount(); top = max(hc, key=hc.get)
    d = dial(300, hi=top)
    d += '<text x="150" y="140" font-size="15" font-weight="700" text-anchor="middle" fill="#4B5563">押した時</text><text x="150" y="178" font-size="34" font-weight="700" text-anchor="middle" fill="#C2410C" font-family="var(--sign)">%d時台</text></svg>' % top
    L = sorted([f for f in F if int(f['dep'][:2]) == top], key=lambda f: (f['m'], f['d']), reverse=True)
    css = CSS_A + CSS_C
    body = '''<div class="wrap"><div class="top"><span class="pill">%s 時計</span></div><div class="dial">%s</div>
<div class="sec-h">%d時台に出た便<small>%d便</small></div><div class="card lg">%s</div>
<div class="ann"><b>C2 1つの時を押したところ</b><ul><li>文字盤の時を押すと、その時に出た便が赤く残り、下に日誌の行で並ぶ</li><li>行を押すと A2 と同じ1便の詳しい所</li></ul></div></div>''' % (
        I['back'], d, top, len(L), ''.join(lrow(f) for f in L[:5])) + tabs('フライト')
    page(OUT + '/C2-clock-hour.html', 'C2 時を押したところ' + T, body, extra_css=css)

# ---------- D 斬新：糸の日本地図 ----------
CSS_D = """
body{background:#F2EEE6}.phone{background:#F2EEE6}
.board{margin:8px -16px 0;height:430px;position:relative;overflow:hidden;background:#EDE7DA}
.board svg{display:block}
.card{background:#FFFDF8}
.legend{display:flex;gap:14px;align-items:center;padding:12px 16px;font-size:13px;color:var(--sub)}
.legend i{display:inline-block;height:0;border-top:solid #8E2A1E;width:28px;vertical-align:middle;margin-right:6px}
.tabs{background:rgba(255,253,248,.97)}
"""
def routes():
    rt = {}
    for f in F: rt.setdefault(tuple(sorted((f['a'], f['b']))), []).append(f)
    return rt
def threads_svg(hi=None):
    rt = routes()
    s = '<svg width="390" height="430" viewBox="14 18 386 400" aria-label="乗った路線を糸で結んだ日本地図">'
    s += jpmap(land='#F8F4EA', coast='#C9BFA6')
    pins = set()
    for (a, b), L in sorted(rt.items(), key=lambda x: len(x[1])):
        x1, y1 = proj(a); x2, y2 = proj(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2; dx, dy = x2 - x1, y2 - y1; Ln = math.hypot(dx, dy) or 1; k = min(26, Ln * .16)
        on = hi and (a, b) == hi
        w = 1.2 + len(L) * 1.1
        col = '#8E2A1E' if (hi is None or on) else '#B9A99A'
        s += '<path d="M%.1f %.1fQ%.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" opacity="%.2f"/>' % (x1, y1, mx - dy / Ln * k, my + dx / Ln * k, x2, y2, col, w, .9 if (hi is None or on) else .6)
        pins.update([a, b])
    for p in pins:
        x, y = proj(p)
        s += '<circle cx="%.1f" cy="%.1f" r="4.4" fill="#D9C9A3" stroke="#5B4A2A" stroke-width="1.4"/><circle cx="%.1f" cy="%.1f" r="1.4" fill="#5B4A2A"/>' % (x, y, x, y)
    for code, dx, dy in [('HND', 10, 4), ('OKA', -8, 22), ('CTS', 10, 4), ('FUK', -46, 2), ('ISG', 4, -10)]:
        x, y = proj(code)
        s += '<text x="%.1f" y="%.1f" font-size="15" font-weight="800" fill="#3B2F1A" font-family="var(--gothic)" paint-order="stroke" stroke="#F8F4EA" stroke-width="4">%s</text>' % (x + dx, y + dy, short(code))
    return s + '</svg>'
def pD1():
    rt = routes(); top = max(rt.items(), key=lambda x: len(x[1]))
    body = '''<div class="wrap"><div class="top"><h1>フライト</h1><span class="pill ic">%s</span><span class="pill ic dark">%s</span></div>
<div class="board">%s</div>
<div class="card" style="margin-top:12px"><div class="row"><div class="tx"><b>いちばん太い糸　%s ⇄ %s</b><small>%d回・ほかに %d本</small></div><span class="pill" style="box-shadow:none;background:var(--wash)">糸を押す</span></div>
<div class="legend"><span><i style="border-top-width:2px"></i>1回</span><span><i style="border-top-width:5px"></i>4回</span><span><i style="border-top-width:8px"></i>6回</span></div></div>
<div class="ann"><b>D 斬新「糸の日本地図」</b><ul><li>空港にピンを打ち、乗った路線を糸で結ぶ。同じ路線は乗るほど糸が太くなる</li><li>本番の地図（航空図風・会社の色）とは別に、記録帳の1ページのような1枚</li><li>外した決まり：地図は航空図風・地の色（コルク板のような生成り）</li></ul></div></div>''' % (
        I['scan'], I['plus'], threads_svg(), short(top[0][0]), short(top[0][1]), len(top[1]), len(rt) - 1) + tabs('フライト')
    page(OUT + '/D1-threads.html', 'D1 糸の日本地図' + T, body, extra_css=CSS_D)
def pD2():
    rt = routes(); key = ('HND', 'OKA'); L = sorted(rt[key], key=lambda f: (f['m'], f['d']))
    # 1本の糸に結び目
    s = '<svg width="358" height="120" viewBox="0 0 358 120" aria-label="羽田⇄那覇の糸と結び目">'
    s += '<path d="M14 60 C 120 30, 240 90, 344 60" fill="none" stroke="#8E2A1E" stroke-width="4" stroke-linecap="round"/>'
    for i, f in enumerate(L):
        t = (i + .5) / len(L)
        x = 14 + t * 330; y = 60 + math.sin(t * math.pi * 2) * -14
        s += '<circle cx="%.1f" cy="%.1f" r="8" fill="#8E2A1E"/><text x="%.1f" y="%.1f" font-size="13" font-weight="700" text-anchor="middle" fill="#3B2F1A">%d/%d</text>' % (x, y, x, y + (30 if i % 2 else -18), f['m'], f['d'])
    s += '</svg>'
    css = CSS_A + CSS_D
    body = '''<div class="wrap"><div class="top"><span class="pill">%s 糸の地図</span></div>
<div class="card" style="padding:16px 16px 8px"><div style="display:flex;align-items:baseline;gap:10px"><b style="font-size:22px;color:var(--strong)">羽田 ⇄ 那覇</b><span style="margin-left:auto"><span class="num" style="font-size:34px">%d</span><span class="u">回</span></span></div>
<p class="note" style="margin:2px 0 0">結び目が1回。左が古い</p>%s</div>
<div class="sec-h">この糸の便</div><div class="card lg">%s</div>
<div class="ann"><b>D2 糸を押したところ</b><ul><li>押した糸が1本ほどけて、結び目＝乗った日になる</li><li>下は日誌の行。今の「路線」の見方はここに入る</li></ul></div></div>''' % (
        I['back'], len(L), s, ''.join(lrow(f) for f in reversed(L))) + tabs('フライト')
    page(OUT + '/D2-thread-route.html', 'D2 糸を押したところ' + T, body, extra_css=css)

# ---------- 07 今の見方をどうまとめるか ----------
def p07():
    css = CSS_A + """.mp{display:grid;grid-template-columns:1fr 22px 1fr;gap:6px 6px;align-items:center;padding:12px 14px;font-size:14px}.mp .a{color:var(--sub)}.mp .b{font-weight:800;color:var(--strong)}.mp svg{color:var(--pale)}
.vrow{display:flex;align-items:center;gap:12px;min-height:60px;padding:6px 16px}.vrow + .vrow{box-shadow:inset 0 1px 0 var(--line2)}.vrow .n{font-family:var(--sign);font-weight:700;font-size:18px;color:var(--sub);width:16px}.vrow .tx{flex:1}.vrow .tx b{display:block;font-size:15px;color:var(--strong)}.vrow .tx small{font-size:13px;color:var(--sub)}"""
    M = [('一覧（搭乗券・案内板・文字だけ）', '日誌'), ('地図', '地図'), ('年ごと・月ごと・高度', '年のまとめ'), ('路線', '1便の詳しい所の「この区間」'), ('カレンダー', '日誌の月の見出し'), ('修行', '修行のタブ（フライトから外す）'), ('記録帳（過去の便を足す）', '右上の ＋')]
    mp = ''.join('<span class="a">%s</span>%s<span class="b">%s</span>' % (a, I['arrow'], b) for a, b in M)
    rows = [('日誌', '1便1行・月ごと', 'on', '1'), ('地図', '飛んだ線と空港', 'on', '2'), ('年のまとめ', '月の距離・よく乗った路線', 'on', '3'), ('時計（C）', '何時台に乗るか', 'off', ''), ('糸の地図（D）', '乗るほど太い糸', 'off', '')]
    rs = ''.join('<div class="vrow"><span class="n">%s</span><div class="tx"><b>%s</b><small>%s</small></div><span class="sw %s">%s</span><span style="color:var(--pale)">%s</span></div>' % (n, a, b, o, o.upper(), I['grip']) for a, b, o, n in rows)
    body = '''<div class="wrap"><div class="top"><h1>07 見方をまとめる</h1></div>
<div class="sec-h">今の 9つ＋3つ → 3つ</div><div class="card mp">%s</div>
<p class="note">搭乗券のカードは「画像で共有」の1枚として残す（一覧には使わない）。</p>
<div class="sec-h">見方を選ぶ（✎ を押したとき）</div><div class="card">%s</div>
<p class="note">ON／OFF は 11/9 の決定どおり（タブを選ぶと同じ部品・OFF の行は押した場所に残る・≡ は右端）。斬新な案を入れるなら、OFF で始める見方として足す形。</p>
<div class="ann"><b>07 今の見方をどうまとめるか</b><ul><li>今の人の設定（user_view_prefs の log）は、搭乗券・案内板・文字だけ→日誌、月ごと・高度→年のまとめ、地図→地図、カレンダー・路線→移す先なし（日誌の中に入る）、修行→修行のタブ</li><li>見方の id はサーバーの行を書き換えず、読むときに直す（図鑑と同じ）</li></ul></div></div>''' % (mp, rs) + tabs('フライト')
    page(OUT + '/07-views.html', '07 見方をまとめる' + T, body, extra_css=css)

def pN1():
    body = logbody(night=True) + '''<div class="ann"><b>夜の画面（A 航空日誌）</b><ul><li>光るのは今年の便の数だけ（緑）。会社の色の細い帯は夜は出さない（11/9 の決定：夜は会社の色を使わない）</li><li>行の区切りは影でなく、ごく暗い1本（#1A222C）</li></ul></div></div>''' + tabs('フライト')
    css = CSS_A + """.lr::before{display:none}.spark i{background:#4A5664}.spark i.z{background:#1A222C}"""
    page(OUT + '/N1-log-night.html', 'N1 夜の画面' + T, body, night=True, extra_css=css)

for fn in (p01, pA1, pA2, pA3, pB1, pB2, pC1, pC2, pD1, pD2, p07, pN1): fn()
print('ok')
