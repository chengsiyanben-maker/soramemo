# -*- coding: utf-8 -*-
# 修行の改善案（design/shugyo-book）を作る。使い方：python3 make_shugyo.py <出力先>
# 数え方は Project の「修行の計算ルール（2026年10月に確認）」：FOP ＝ フライトマイル × 2 ＋ 搭乗ボーナス（見本はセイバー 75%・200）
import sys, math, datetime
sys.path.insert(0, '/tmp/claude-0/gen')
from common import *
import make_flight_parts as MP
OUT = sys.argv[1]
T = '｜修行の改善案（画面案）'
SHOT = '/tmp/claude-0/shots/'
GOAL = 30000; GOAL_N = 30; GOAL_NF = 10000
LEFT = GOAL - FOP_NOW; LEFT_N = GOAL_N - CNT_NOW
DAY = (datetime.date(2026, 11, 9) - datetime.date(2026, 1, 1)).days + 1
YEARP = round(DAY / 365 * 100)
JM = {}
for f in JALF: JM.setdefault(f['m'], []).append(f)
CSS_S = """
.seg b{min-height:44px}
.hero{padding:18px 20px 18px}.hero .lab{display:flex;align-items:center;font-size:13px;color:var(--sub);font-weight:700}.hero .lab span{margin-left:auto}
.hero .big{margin-top:10px}.hero .big .num{font-size:60px}.hero .big .u{font-size:14px}
.hero .left{margin-top:8px;font-size:15px;font-weight:800;color:var(--strong)}.hero .left .num{font-size:22px;margin:0 2px}
.gauge{margin-top:14px}.gauge .gl{display:flex;font-size:13px;color:var(--sub);font-weight:700;margin-top:6px}.gauge .gl span:last-child{margin-left:auto}
.gauge .bar{height:12px;border-radius:6px;background:var(--line2);position:relative;overflow:hidden}.gauge .bar i{position:absolute;left:0;top:0;bottom:0;border-radius:6px;background:var(--jisseki)}
.gauge .bar.t{height:6px;margin-top:10px}.gauge .bar.t i{background:#9AA3AF}
.two{display:flex;gap:8px;margin-top:10px}.two > div{flex:1;padding:12px 14px}.two .k{font-size:13px;color:var(--sub);font-weight:700;display:block}.two .num{font-size:28px;display:block;margin-top:6px}.two small{display:block;font-size:13px;color:var(--sub);margin-top:4px}
.est{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:18px;margin-top:8px}.est .tx{flex:1}.est b{display:block;font-size:15px}.est small{display:block;font-size:13px;opacity:.9}.est .num{font-size:22px;color:inherit}
.est.y{background:var(--yotei);color:var(--yotei-ink)}.est.k{background:var(--keikaku);color:var(--keikaku-ink)}
.tg{display:inline-flex;align-items:center;min-height:24px;padding:0 9px;border-radius:999px;font-size:13px;font-weight:800}
.lst .row + .row{box-shadow:inset 0 1px 0 var(--line2)}.lst .row .r{font-size:13px;color:var(--sub);font-weight:700}
.lst .row .num{font-size:22px}
"""
def head(title='2026年の修行', back=None, band=None):
    if back:
        return '<div class="top"><span class="pill">%s %s</span></div>' % (I['back'], back)
    return ('<div class="top"><h1>%s</h1><span class="pill">会員情報</span></div>'
            '<div style="display:flex;gap:8px;align-items:center"><div class="seg" style="width:170px"><b>ANA</b><b class="on">JAL</b></div><span style="margin-left:auto;font-size:13px;color:var(--sub);font-weight:700">目標 クリスタル</span></div>') % title + (('<div class="vband">' + ''.join('<span class="pill%s">%s</span>' % (' on' if n == band[0] else '', n) for n in band[1]) + '<span class="pill ed" aria-label="見方を選ぶ">' + I['pen'] + '</span></div>') if band else '')
def frow(f, val, tag=''):
    return '<div class="row"><div class="tx"><b>%d/%d　%s → %s</b><small>%s・%s%s</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>' % (
        f['m'], f['d'], short(f['a']), short(f['b']), f.get('no') or f['co'], f['fare'], tag, val)

# ---------- 01 ----------
def p01():
    css = MP.CSS01
    body = '''<div class="wrap"><div class="top"><h1>01 今の見にくい所</h1></div>
<p class="note" style="margin-top:0">main の web/ をデモ（見本の記録）で開き、修行のタブを幅390で撮った。上が高さ 844、下は同じ画面を最後まで送ったところ（下半分）。</p>
''' + MP.shots([(SHOT + 'sg-844.png', 180, 844, '高さ 844（上の切り替えを除く）', [(1, 330, 470), (2, 290, 555), (3, 200, 705)]),
              (SHOT + 'sg-full.png', 860, 1700, '最後まで送ったところ', [(4, 340, 1200), (5, 340, 1385)])]) + '''
<ol class="pb">
<li><b>今年の何割まで来たかが分からない。</b>棒は FOP だけで、1年のどこにいるか（今日は1年の%d%%）と並べて見られない。ペースが速いのか遅いのかは自分で計算する</li>
<li><b>2つの道（FOP だけ／回数＋FOP）の箱の意味が読み取りにくい。</b>「30回＋10,000 FOP あと16回」と「搭乗 14回」が同じ大きさの箱で並ぶ</li>
<li><b>空の行が続く。</b>予定・計画がないと「—」の行が2つ、「予定の便はまだありません」、計画を作る、0便・なしの行……と、何もない知らせが5つ縦に続く</li>
<li><b>年末までの見通しが奥にある。</b>いちばん知りたい「届くか」は、リストの4行目「年末までの道のり」を開いてから</li>
<li><b>修行の路線の運航が修行の中にある。</b>今日の便数・定刻は、乗る日でなければ使わない。計算の道具（路線を入れて計算する）とも並んでいて、ページが長い（1,800px）</li>
</ol></div>''' % YEARP
    page(OUT + '/01-now-problems.html', '01 今の見にくい所' + T, body, extra_css=css)

# ---------- E 正攻法：道のりの1枚 ----------
def eb(night=False):
    lit = ' lit' if night else ''
    nxt = YOTEI[0]
    return head(band=('道のり', ['道のり', '1便ごと', '月ごと'])) + '''
<div class="card hero" style="margin-top:12px"><div class="lab"><span class="tg" style="background:var(--wash);color:var(--strong)">実績</span>&nbsp;記録した便だけ<span>FLY ON ポイント</span></div>
<div class="big"><span class="num%s">%s</span><span class="u">FOP</span></div>
<div class="left">クリスタルまで あと<span class="num">%s</span><span class="u">FOP</span></div>
<div class="gauge"><div class="bar"><i style="width:%.1f%%"></i></div><div class="gl"><span>ポイント %d%%</span><span>3万</span></div>
<div class="bar t"><i style="width:%d%%"></i></div><div class="gl"><span>1年 %d%%（今日 11/9）</span><span>12/31</span></div></div></div>
<div class="two"><div class="card"><span class="k">FOP だけの道</span><span class="num">%s</span><small>あと（FOP）</small></div><div class="card"><span class="k">30回＋1万 FOP の道</span><span class="num">%d<span class="u">回</span></span><small>あと（1万 FOP は済み）</small></div></div>
<div class="sec-h">入れたら届くか<small>推定</small></div>
<div class="est y"><div class="tx"><b>予定の2便に乗ると</b><small>あと %s FOP・あと %d回</small></div><span><span class="num">＋%s</span></span></div>
<div class="est k"><div class="tx"><b>計画（残した案）の6便にも乗ると</b><small>FOP だけの道で届く</small></div><span><span class="num">＋%s</span></span></div>
<p class="note">予定と計画は実績と分けて足しています。届くかは推定です。</p>
<div class="sec-h">次に乗る便<span class="r">予定と計画 ›</span></div>
<div class="card"><div class="row"><div class="tx"><b>11月22日（日）　羽田 → 那覇</b><small>%s・%s・<span class="tg tag-y">予定</span></small></div><span><span class="num%s" style="font-size:22px">%s</span><span class="u">FOP</span></span></div></div>
''' % (lit, c(FOP_NOW), c(LEFT), FOP_NOW / GOAL * 100, FOP_NOW * 100 // GOAL, YEARP, YEARP, c(LEFT), LEFT_N,
       c(LEFT - FOP_Y), LEFT_N - 2, c(FOP_Y), c(FOP_K), nxt['no'], nxt['fare'], ' amb' if night else '', c(fop(nxt)))
def pE1():
    body = '<div class="wrap">' + eb() + '''<div class="card lst" style="margin-top:10px"><div class="row"><div class="tx"><b>1便ごと</b></div><span class="r">%d便 ›</span></div><div class="row"><div class="tx"><b>月ごと</b></div><span class="r">11月 %s ›</span></div><div class="row"><div class="tx"><b>路線を入れて計算する</b></div><span class="r">›</span></div></div>
<div class="ann"><b>E 正攻法「道のりの1枚」</b><ul><li>大きな数字の下に、ポイントの棒と「1年の何割か」の細い棒を並べる（同じ棒にはまぜない）</li><li>2つの道は「あと」だけを同じ形で</li><li>予定と計画は色の帯を分けて「入れたら」の推定だけ。空のときは帯ごと出さない</li><li>路線の運航は外し、予定の便のカードに「今日の便数」を出す形へ（修行担当と相談）</li></ul></div></div>''' % (CNT_NOW, c(sum(fop(f) for f in JM[11]))) + tabs('修行')
    page(OUT + '/E1-overview.html', 'E1 道のりの1枚' + T, body, extra_css=CSS_S)
def pE2():
    f = JALF[1]
    t = f['tpm']; fm = int(t * .75)
    css = CSS_S + """.calc{padding:6px 18px 16px}.cl{display:flex;align-items:baseline;gap:8px;min-height:44px;padding:8px 0}.cl + .cl{box-shadow:inset 0 1px 0 var(--line2)}.cl .k{flex:1;font-size:14px;color:var(--sub)}.cl .k b{color:var(--strong)}.cl .num{font-size:24px}
.cl.tot .num{font-size:44px}.cl .op{font-family:var(--sign);font-size:20px;color:var(--pale);width:20px}"""
    body = '''<div class="wrap">%s
<div class="card" style="padding:16px 18px"><p class="note" style="margin:0;font-weight:700">2026年%d月%d日（%s）・%s</p><div style="font-size:26px;font-weight:800;color:var(--strong);margin-top:4px">%s → %s</div><p class="note" style="margin:4px 0 0">普通席・%s（記録した運賃）</p></div>
<div class="sec-h">FOP の数え方</div>
<div class="card calc"><div class="cl"><span class="op"></span><span class="k">区間マイル</span><span class="num">%s</span></div>
<div class="cl"><span class="op">×</span><span class="k">積算率 <b>75%%</b>（普通席・セイバー）</span><span class="num">%s</span></div>
<div class="cl"><span class="op">×</span><span class="k"><b>2</b></span><span class="num">%s</span></div>
<div class="cl"><span class="op">＋</span><span class="k">搭乗ボーナス（セイバー）</span><span class="num">200</span></div>
<div class="cl tot"><span class="op">＝</span><span class="k"><b>この便の FOP</b></span><span><span class="num">%s</span><span class="u">FOP</span></span></div></div>
<div class="two"><div class="card"><span class="k">回数</span><span class="num">＋1<span class="u">回</span></span><small>JAL グループ便</small></div><div class="card"><span class="k">Life Status</span><span class="num">＋5</span><small>国内線は1搭乗5</small></div></div>
<div class="btn w">運賃を選び直す</div>
<p class="note">式は各社の公開ページ（2026年10月に確認）。キャンペーンのボーナスは含みません。</p>
<div class="ann"><b>E2 1便の内訳</b><ul><li>「1便ごと」の行を押すと開く。計算の式を上から1行ずつ（家計簿の明細のように）</li><li>今のフライトの見方「修行」はここに移す</li></ul></div></div>''' % (
        head(back='1便ごと'), f['m'], f['d'], f['wd'], f['no'], short(f['a']), short(f['b']), f['fare'], c(t), c(fm), c(fm * 2), c(fop(f))) + tabs('修行')
    page(OUT + '/E2-flight.html', 'E2 1便の内訳' + T, body, extra_css=css)
def pE3():
    vals = [sum(fop(f) for f in JM.get(m, [])) for m in range(1, 12)]
    mx = max(vals)
    bars = ''.join('<div class="b"><span class="v">%s</span><i style="height:%dpx"%s></i><span class="l">%d</span></div>' % (
        ('%.1f' % (v / 1000)) if v else '', v * 110 // mx if v else 3, '' if v else ' class="z"', m) for m, v in zip(range(1, 12), vals))
    fy = [sum(fop(f) for f in YOTEI if f['m'] == 11), 0]; fk = [0, sum(fop(f) for f in KEIKAKU)]
    rt = {}
    for f in JALF: k = tuple(sorted((f['a'], f['b']))); rt[k] = rt.get(k, 0) + fop(f)
    top = sorted(rt.items(), key=lambda x: -x[1])[:3]
    css = CSS_S + """.bars{display:flex;gap:4px;align-items:flex-end;height:160px;padding:14px 14px 10px}.bars .b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.bars i{width:100%;background:var(--jisseki);border-radius:4px 4px 2px 2px}.bars i.z{background:var(--line2)}.bars .v{font-family:var(--sign);font-weight:700;font-size:13px;color:var(--strong);margin-bottom:3px}.bars .l{font-size:13px;color:var(--mute);margin-top:4px}
.fut{display:flex;gap:8px;padding:12px 14px}.fut > div{flex:1;border-radius:14px;padding:10px 12px}.fut .k{font-size:13px;font-weight:700;display:block}.fut .num{font-size:24px;color:inherit;display:block;margin-top:4px}"""
    rk = ''.join('<div class="row"><div class="tx"><b>%s ⇄ %s</b><small>%d回</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>' % (
        short(k[0]), short(k[1]), sum(1 for f in JALF if tuple(sorted((f['a'], f['b']))) == k), c(v)) for k, v in top)
    body = '''<div class="wrap">%s
<div class="sec-h">月ごとの FOP<small>実績・千</small><span class="r">1回 平均 %s</span></div><div class="card"><div class="bars">%s</div></div>
<div class="sec-h">これから<small>実績と別に</small></div>
<div class="card fut"><div class="tag-y"><span class="k">11月の予定</span><span class="num">＋%s</span></div><div class="tag-k"><span class="k">12月の計画</span><span class="num">＋%s</span></div></div>
<div class="sec-h">路線ごと<small>実績</small></div><div class="card lst">%s</div>
<div class="ann"><b>E3 月ごと</b><ul><li>マラソンの練習ノートのように、月ごとの量を棒で。今の成績の「修行のまとめ」をここに移す</li><li>予定と計画は棒にまぜず、下の別の枠に数字だけ</li><li>金額は出さない（11/4 の決定のまま）</li></ul></div></div>''' % (
        head(band=('月ごと', ['道のり', '1便ごと', '月ごと'])), c(FOP_NOW // CNT_NOW), bars, c(fy[0]), c(fk[1]), rk) + tabs('修行')
    page(OUT + '/E3-months.html', 'E3 月ごと' + T, body, extra_css=css)

# ---------- F 斬新：山登りの高度 ----------
CSS_F = CSS_S + """
body{background:linear-gradient(180deg,#DCE9F5 0,#EEF1F5 520px)}.phone{background:transparent}
.alt{display:flex;align-items:flex-end;gap:10px;margin-top:6px}.alt .num{font-size:56px}.alt small{font-size:13px;color:var(--sub);font-weight:700;display:block}
.mt{margin:10px -16px 0}
"""
def mountain(W=390, H=330, night=False):
    s = '<svg width="%d" height="%d" viewBox="0 0 %d %d" aria-label="FOP を標高にした山の断面">' % (W, H, W, H)
    top = 30; bot = H - 40; L = 16; R = W - 54
    def X(d): return L + (R - L) * d / 365
    def Y(v): return bot - (bot - top) * v / 52000
    # 遠い山なみ
    s += '<path d="M0 %d L60 %d L120 %d L190 %d L260 %d L330 %d L390 %d V%d H0Z" fill="%s"/>' % (Y(14000), Y(26000), Y(19000), Y(33000), Y(24000), Y(40000), Y(30000), H, '#CBD8E6' if not night else '#0B1118')
    for v, n in [(30000, 'クリスタル'), (50000, 'サファイア')]:
        y = Y(v)
        s += '<path d="M%d %.1fH%d" stroke="#5F6875" stroke-width="1" stroke-dasharray="3 4"/>' % (L, y, R)
        s += '<path d="M%d %.1fl9 -9 9 9v8h-18z" fill="#fff" stroke="#16233A" stroke-width="1.6"/>' % (R + 8, y - 4)
        s += '<text x="%d" y="%.1f" font-size="13" font-weight="800" fill="#16233A" text-anchor="end">山小屋 %s %d万</text>' % (R, y - 6, n, v // 10000)
    # 実績の道
    pts = [(0, 0)]; cum = 0
    for f in sorted(JALF, key=lambda f: (f['m'], f['d'])):
        d = (datetime.date(2026, f['m'], f['d']) - datetime.date(2026, 1, 1)).days
        pts.append((d, cum)); cum += fop(f); pts.append((d, cum))
    pts.append((DAY, cum))
    path = 'M' + ' L'.join('%.1f %.1f' % (X(d), Y(v)) for d, v in pts)
    s += '<path d="%s V%d H%d Z" fill="%s"/>' % (path, bot, L, 'rgba(22,35,58,.10)')
    s += '<path d="%s" fill="none" stroke="#16233A" stroke-width="2.6" stroke-linejoin="round"/>' % path
    # 予定（うすい金）と計画（うすい青）は別の道
    y0 = cum; d1 = (datetime.date(2026, 11, 22) - datetime.date(2026, 1, 1)).days; d2 = (datetime.date(2026, 11, 24) - datetime.date(2026, 1, 1)).days
    y1 = y0 + fop(YOTEI[0]); y2 = y1 + fop(YOTEI[1])
    s += '<path d="M%.1f %.1fH%.1fV%.1fH%.1fV%.1f" fill="none" stroke="#C9A646" stroke-width="3" stroke-dasharray="5 4"/>' % (X(DAY), Y(y0), X(d1), Y(y1), X(d2), Y(y2))
    v = y2; p = 'M%.1f %.1f' % (X(d2), Y(v))
    for f in KEIKAKU:
        d = (datetime.date(2026, f['m'], f['d']) - datetime.date(2026, 1, 1)).days
        p += 'H%.1f' % X(d); v += fop(f); p += 'V%.1f' % Y(v)
    s += '<path d="%s" fill="none" stroke="#6E93C8" stroke-width="3" stroke-dasharray="2 4" stroke-linecap="round"/>' % p
    # 登っている人
    s += '<circle cx="%.1f" cy="%.1f" r="8" fill="#C2410C" stroke="#fff" stroke-width="3"/>' % (X(DAY), Y(cum))
    s += '<text x="%.1f" y="%.1f" font-size="13" font-weight="800" fill="#C2410C" text-anchor="end">いまここ</text>' % (X(DAY) - 12, Y(cum) + 4)
    for m in (1, 4, 7, 10):
        d = (datetime.date(2026, m, 1) - datetime.date(2026, 1, 1)).days
        s += '<text x="%.1f" y="%d" font-size="13" fill="#4B5563">%d月</text>' % (X(d), bot + 22, m)
    return s + '</svg>'
def pF1():
    body = '''<div class="wrap">%s
<div class="alt"><div><small>いまの標高</small><span class="num">%s</span><span class="u">FOP</span></div><div style="margin-left:auto;text-align:right"><small>山小屋（クリスタル）まで</small><span class="num" style="font-size:28px">%s</span></div></div>
<div class="mt">%s</div>
<div class="card" style="padding:4px 0"><div class="row"><span class="mi" style="background:#16233A"></span><div class="tx"><b>登った道</b><small>記録した便だけ</small></div></div><div class="row"><span class="mi" style="background:#C9A646"></span><div class="tx"><b>予定の道</b><small>11/22・11/24　＋%s</small></div></div><div class="row"><span class="mi" style="background:#6E93C8"></span><div class="tx"><b>計画の道</b><small>12月の6便　＋%s（推定）</small></div></div></div>
<div class="ann"><b>F 斬新「山登りの高度」</b><ul><li>ポイント＝標高、ステイタス＝山小屋。1年を左から右へ登る山の断面</li><li>予定と計画は別の点線の道（実績の道とは重ねない）</li><li>外した決まり：空の色の地・山なみの絵・点線と細い線</li></ul></div></div>''' % (
        head(band=('山', ['道のり', '山', '1便ごと'])), c(FOP_NOW), c(LEFT), mountain(), c(FOP_Y), c(FOP_K)) + tabs('修行')
    page(OUT + '/F1-mountain.html', 'F1 山登りの高度' + T, body, extra_css=CSS_F)
def pF2():
    css = CSS_F + """.step{display:flex;align-items:center;gap:12px;min-height:60px;padding:8px 16px}.step + .step{box-shadow:inset 0 1px 0 var(--line2)}.step .tx{flex:1}.step .tx b{display:block;font-size:15px;color:var(--strong)}.step .tx small{font-size:13px;color:var(--sub)}
.step .up{width:46px;display:flex;align-items:flex-end;height:34px}.step .up i{display:block;width:100%;background:#16233A;clip-path:polygon(0 100%,35% 20%,65% 20%,100% 100%)}.step .num{font-size:22px}
.camp{display:flex;align-items:center;gap:10px;margin:18px 6px 6px;font-size:15px;font-weight:800;color:var(--strong)}.camp small{font-size:13px;color:var(--sub);font-weight:700;margin-left:auto}"""
    s = '<div class="wrap">' + head(back='山') + '<div class="alt"><div><small>山行記録</small><span class="num" style="font-size:40px">%d</span><span class="u">回登った</span></div></div>' % CNT_NOW
    cum = FOP_NOW
    for m in sorted(JM, reverse=True)[:3]:
        L = JM[m]
        s += '<div class="camp">%d月<small>標高 %s まで</small></div><div class="card">' % (m, c(cum))
        for f in L:
            v = fop(f)
            s += '<div class="step"><span class="up"><i style="height:%dpx"></i></span><div class="tx"><b>%d/%d　%s → %s</b><small>%s・%s</small></div><span><span class="num">＋%s</span></span></div>' % (8 + v * 26 // 1700, f['m'], f['d'], short(f['a']), short(f['b']), f['no'], f['fare'], c(v))
            cum -= v
        s += '</div>'
    s += '<div class="ann"><b>F2 山行記録</b><ul><li>1便＝1回の登り。山の形の小さな図が、登った高さ（FOP）</li><li>月の見出しに「標高いくつまで来たか」。行を押すと E2 の内訳</li></ul></div></div>' + tabs('修行')
    page(OUT + '/F2-mountain-log.html', 'F2 山行記録' + T, s, extra_css=css)

# ---------- G 斬新：残りいくら（逆から数える） ----------
CSS_G = CSS_S + """
.rc{background:#FFFEFA;border-radius:6px;box-shadow:0 1px 2px rgba(17,24,39,.06),0 12px 30px -16px rgba(17,24,39,.3);padding:18px 18px 22px;position:relative;margin-top:12px}
.rc::after{content:"";position:absolute;left:0;right:0;bottom:-8px;height:10px;background:linear-gradient(-45deg,transparent 6px,#FFFEFA 0) 0 0/12px 10px,linear-gradient(45deg,transparent 6px,#FFFEFA 0) 0 0/12px 10px}
.rc .k{font-size:13px;color:var(--sub);font-weight:700}.rc .rem{font-family:var(--sign);font-weight:700;font-size:64px;color:var(--strong);line-height:1}
.led{margin-top:14px;font-variant-numeric:tabular-nums}.ld{display:grid;grid-template-columns:44px 1fr 72px 72px;gap:6px;align-items:baseline;min-height:44px;padding:8px 0;border-top:1px dashed #C9CDD4;font-size:14px}
.ld .d{font-family:var(--sign);font-weight:700;color:var(--sub);font-size:16px}.ld .r{font-weight:700;color:var(--strong)}.ld .m,.ld .b{text-align:right;font-family:var(--sign);font-weight:700;font-size:18px}.ld .m{color:#B42318}.ld .b{color:var(--strong)}
.ld.h{font-size:13px;color:var(--sub);font-weight:700;min-height:28px;border-top:0;padding:0}.ld.h span{text-align:right}.ld.h span:nth-child(2){text-align:left}
.ld.y{background:var(--yotei);border-top:0;border-radius:10px;padding:8px 8px;margin-top:4px}.ld.y .m,.ld.y .b,.ld.y .d,.ld.y .r{color:var(--yotei-ink)}
"""
def pG1():
    rows = ''; bal = GOAL
    seq = sorted(JALF, key=lambda f: (f['m'], f['d']))
    bals = []
    for f in seq: bal -= fop(f); bals.append((f, bal))
    for f, b in bals[-6:][::-1]:
        rows += '<div class="ld"><span class="d">%d/%d</span><span class="r">%s→%s</span><span class="m">−%s</span><span class="b">%s</span></div>' % (f['m'], f['d'], f['a'], f['b'], c(fop(f)), c(b))
    yb = LEFT; yr = ''
    for f in YOTEI:
        yb -= fop(f)
        yr += '<div class="ld y"><span class="d">%d/%d</span><span class="r">%s→%s</span><span class="m">−%s</span><span class="b">%s</span></div>' % (f['m'], f['d'], f['a'], f['b'], c(fop(f)), c(yb))
    body = '''<div class="wrap">%s
<div class="rc"><div class="k">クリスタルまで 残り</div><div class="rem">%s<span class="u" style="font-size:16px">FOP</span></div><p class="note" style="margin:6px 0 0">1月1日の 30,000 から、乗るたびにひいていく</p>
<div class="led"><div class="ld h"><span></span><span>区間</span><span>ひいた</span><span>残り</span></div>%s</div>
<p class="note" style="margin-top:14px;font-weight:700">予定を入れたら（推定）</p>%s</div>
<div class="ann" style="margin-top:28px"><b>G 斬新「家計簿のように、残りから数える」</b><ul><li>「いくら貯まったか」でなく「あといくら」を主役に。乗るたびに残りが減る</li><li>予定は色の地の行で分け、残りの列も「予定を入れたら」として別に出す</li><li>外した決まり：点線の区切り・レシートのぎざぎざ・角の小さい紙。金額（円）は出さない</li></ul></div></div>''' % (
        head(band=('残りから', ['道のり', '残りから', '1便ごと'])), c(LEFT), rows, yr) + tabs('修行')
    page(OUT + '/G1-countdown.html', 'G1 残りから数える' + T, body, extra_css=CSS_G)
def pG2():
    css = CSS_G + """.yr12{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:12px}.yr12 > div{background:#FFFEFA;border-radius:10px;padding:10px 8px;box-shadow:0 1px 2px rgba(17,24,39,.06)}
.yr12 .mo{font-size:13px;font-weight:800;color:var(--sub)}.yr12 .num{font-size:20px;display:block;margin-top:4px}.yr12 small{font-size:13px;color:#B42318;font-weight:700;font-family:var(--sign)}
.yr12 > div.y{background:var(--yotei)}.yr12 > div.y .mo,.yr12 > div.y small,.yr12 > div.y .num{color:var(--yotei-ink)}.yr12 > div.k{background:var(--keikaku)}.yr12 > div.k .mo,.yr12 > div.k small,.yr12 > div.k .num{color:var(--keikaku-ink)}
.yr12 > div.no{background:transparent;box-shadow:inset 0 0 0 1px #D5DAE1}"""
    bal = GOAL; cells = ''
    for m in range(1, 13):
        used = sum(fop(f) for f in JM.get(m, []))
        if m <= 10 or (m == 11):
            bal -= used
            cells += '<div><span class="mo">%d月</span><span class="num">%s</span><small>%s</small></div>' % (m, c(bal), ('−' + c(used)) if used else '±0')
        else:
            pass
    yb = bal - FOP_Y; kb = yb - FOP_K
    cells += '<div class="y"><span class="mo">11月 予定</span><span class="num">%s</span><small>−%s</small></div>' % (c(yb), c(FOP_Y))
    cells += '<div class="k"><span class="mo">12月 計画</span><span class="num">%s</span><small>−%s</small></div>' % ('0', c(FOP_K))
    body = '''<div class="wrap">%s
<div class="rc"><div class="k">12月31日の残り（計画まで乗れば・推定）</div><div class="rem">0<span class="u" style="font-size:16px">FOP</span></div><p class="note" style="margin:6px 0 0">%s FOP あまって、クリスタルに届く見込み</p></div>
<div class="sec-h" style="margin-top:28px">月末の残り<small>実績</small></div><div class="yr12">%s</div>
<p class="note">色の地の2つは予定と計画（実績の月とは分けて、右下に足す）。</p>
<div class="ann"><b>G2 年の見通し</b><ul><li>家計簿の1年のページのように、月末ごとの残りを並べる</li><li>年末に残りがいくつになりそうかを、いちばん上に（推定）</li></ul></div></div>''' % (
        head(back='残りから'), c(-(kb)), cells) + tabs('修行')
    page(OUT + '/G2-countdown-year.html', 'G2 年の見通し' + T, body, extra_css=css)

# ---------- H 斬新：回数のマス目（会員カード） ----------
CSS_H = CSS_S + """
.pc{border-radius:20px;padding:18px 16px 16px;background:#16233A;color:#E7ECF3;margin-top:12px;box-shadow:0 18px 30px -18px rgba(22,35,58,.7)}
.pc .k{font-size:13px;font-weight:700;color:#C9D2DE;display:flex}.pc .k span{margin-left:auto}
.pc .big{display:flex;align-items:baseline;gap:6px;margin-top:6px}.pc .big .num{color:#fff;font-size:54px}.pc .big .u{color:#C9D2DE;font-size:14px}
.cells{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:14px}
.cells i{aspect-ratio:1;border-radius:12px;display:flex;align-items:center;justify-content:center;font:700 14px var(--sign);font-style:normal}
.cells i.f{background:#E9C46A;color:#2B230B}.cells i.e{box-shadow:inset 0 0 0 1.5px rgba(233,236,243,.45);color:#9FB0C6}
.cells i.sel{box-shadow:0 0 0 3px #fff}
.fopline{display:flex;align-items:center;gap:10px;margin-top:14px;font-size:13px;color:#C9D2DE;font-weight:700}.fopline .bar{flex:1;height:8px;border-radius:4px;background:rgba(255,255,255,.18);overflow:hidden}.fopline .bar i{display:block;height:100%;background:#E9C46A}
"""
def cells(sel=None):
    s = '<div class="cells" aria-label="30回のマス目">'
    seq = sorted(JALF, key=lambda f: (f['m'], f['d']))
    for i in range(30):
        if i < len(seq):
            f = seq[i]
            s += '<i class="f%s">%d/%d</i>' % (' sel' if sel == i else '', f['m'], f['d'])
        else:
            s += '<i class="e">%d</i>' % (i + 1)
    return s + '</div>'
def pH1():
    body = '''<div class="wrap">%s
<div class="pc"><div class="k">30回＋1万 FOP の道<span>実績</span></div><div class="big"><span class="num">あと %d</span><span class="u">マス</span></div>
%s<div class="fopline"><span>1万 FOP</span><span class="bar"><i style="width:100%%"></i></span><span>済み</span></div></div>
<div class="est y"><div class="tx"><b>予定を入れたら</b><small>2マス埋まって、あと %d マス（推定）</small></div></div>
<div class="est k"><div class="tx"><b>計画まで乗ったら</b><small>6マス埋まって、あと %d マス（推定）</small></div></div>
<div class="card lst" style="margin-top:10px"><div class="row"><div class="tx"><b>FOP だけの道</b><small>あと %s FOP</small></div><span class="r">切り替え ›</span></div></div>
<div class="ann"><b>H 斬新「回数のマス目」</b><ul><li>30回の道を、会員カードの30マスにする。乗った日がマスに入る</li><li>予定と計画はマスに入れず、下の色の帯で「埋まったら」だけ</li><li>外した決まり：カード全体を濃い地に・金色のマス（金は特別塗装機と「集めた」だけの決まりに当たる）</li></ul></div></div>''' % (
        head(band=('マス目', ['道のり', 'マス目', '1便ごと'])), LEFT_N, cells(), LEFT_N - 2, LEFT_N - 8, c(LEFT)) + tabs('修行')
    page(OUT + '/H1-cells.html', 'H1 回数のマス目' + T, body, extra_css=CSS_H)
def pH2():
    seq = sorted(JALF, key=lambda f: (f['m'], f['d']))
    i = 15; f = seq[i]
    body = '''<div class="wrap">%s
<div class="pc"><div class="k">30回＋1万 FOP の道<span>実績</span></div><div class="big"><span class="num">あと %d</span><span class="u">マス</span></div>%s</div></div>
<div class="dim"></div><div class="sheet"><div class="grab"></div>
<p class="note" style="margin:0;font-weight:700">%d マス目・2026年%d月%d日（%s）</p><div style="font-size:24px;font-weight:800;color:var(--strong);margin-top:2px">%s → %s</div>
<div class="two"><div class="card" style="box-shadow:none;background:var(--wash)"><span class="k">回数</span><span class="num">＋1<span class="u">回</span></span></div><div class="card" style="box-shadow:none;background:var(--wash)"><span class="k">この便の FOP</span><span class="num">%s</span></div></div>
<div class="btn">内訳を見る</div><p class="note">マスを押すと、その日の便が下から出る。</p></div>''' % (
        head(), LEFT_N, cells(sel=i), i + 1, f['m'], f['d'], f['wd'], short(f['a']), short(f['b']), c(fop(f)))
    page(OUT + '/H2-cell.html', 'H2 マスを押したところ' + T, body, extra_css=CSS_H)

# ---------- 07 ----------
def p07():
    css = CSS_S + MP.CSS07
    M = [('大きな数字と棒', '残す＋「1年の何割」の細い棒'), ('2つの道の箱', '「あと」だけの2枚'), ('実績・予定・計画の3行', '予定・計画があるときだけ色の帯'), ('次に乗る便・計画を作る・5つの行', '次に乗る便1枚＋3つの行'),
         ('年末までの道のり', '月ごと・年の見通しへ'), ('修行の路線の運航', '予定の便のカードへ（タブからは外す）'), ('フライトの見方「修行」', '1便ごと（E2 の内訳）'), ('成績の「修行のまとめ」', '月ごと（E3）')]
    mp = ''.join('<span class="a">%s</span>%s<span class="b">%s</span>' % (a, I['arrow'], b) for a, b in M)
    rows = [('道のり', '大きな数字・2つの道・届くか', 'on', '1'), ('1便ごと', '1便の FOP と内訳', 'on', '2'), ('月ごと', '月の FOP・路線ごと', 'on', '3'), ('山（F）', 'ポイント＝標高', 'off', ''), ('残りから（G）', '家計簿のように', 'off', ''), ('マス目（H）', '30回の道', 'off', '')]
    rs = ''.join('<div class="vrow"><span class="n">%s</span><div class="tx"><b>%s</b><small>%s</small></div><span class="sw %s">%s</span><span style="color:var(--pale)">%s</span></div>' % (n, a, b, o, o.upper(), I['grip']) for a, b, o, n in rows)
    body = '''<div class="wrap"><div class="top"><h1>07 見方をまとめる</h1></div>
<div class="sec-h">今の修行のタブ → 3つの見方</div><div class="card mp">%s</div>
<div class="sec-h">見方を選ぶ（✎ を押したとき）</div><div class="card">%s</div>
<p class="note">今の修行のタブには見方の帯がない。帯を足すなら「道のり・1便ごと・月ごと」の3つで、ON／OFF は 11/9 の決定どおり。斬新な案は OFF で始める見方として足す形。</p>
<div class="ann"><b>07 今の見方をどうまとめるか</b><ul><li>フライトの見方「修行」を見ていた人（user_view_prefs の log に sg）は、修行のタブの「1便ごと」へ</li><li>成績の「修行のまとめ」を出していた人は「月ごと」を ON のまま</li><li>計算の道具（路線を入れて計算する）は「道のり」のいちばん下の行に残す</li></ul></div></div>''' % (mp, rs) + tabs('修行')
    page(OUT + '/07-views.html', '07 見方をまとめる' + T, body, extra_css=css)

def pN1():
    css = CSS_S + """.gauge .bar i{background:#5FD993}.gauge .bar.t i{background:#4A5664}.est.y,.est.k{box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}"""
    body = '<div class="wrap">' + eb(night=True) + '''<div class="ann"><b>夜の画面（E 道のりの1枚）</b><ul><li>光るのは実績の FOP（緑）と次に乗る便の FOP（琥珀＝「次」）だけ</li><li>予定と計画の帯は、夜はごく暗い金と紺の地に明るい字。会社の色は使わない</li></ul></div></div>''' + tabs('修行')
    page(OUT + '/N1-overview-night.html', 'N1 夜の画面' + T, body, night=True, extra_css=css)

if __name__ == '__main__':
  for fn in (p01, pE1, pE2, pE3, pF1, pF2, pG1, pG2, pH1, pH2, p07, pN1): fn()
  print('ok', FOP_NOW, CNT_NOW, LEFT, LEFT_N)
