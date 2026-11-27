# -*- coding: utf-8 -*-
# 修行の2版（本人「修行はおすすめで」＝ E＋G の月末の残り）。使い方：python3 make_shugyo_v2.py <出力先>
# 見本の記録は common.py の26便（フライトの案と同じ表）。数え方は「修行の計算ルール（2026年10月に確認）」
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
import make_shugyo as S
from make_shugyo import CSS_S, head, JM, GOAL, LEFT, LEFT_N, YEARP, CNT_NOW
import make_flight_parts as MP
OUT = sys.argv[1]
T = '｜修行の2版（画面案）'
LS_NOW = CNT_NOW * 5          # Life Status：国内線は1搭乗5（見本は2026年からの記録だけ）
LS_GOAL = 1500
LS_LEFT_N = (LS_GOAL - LS_NOW + 4) // 5
TODAY_N = 12                  # 見本：今日（11/9）の JAL 羽田→那覇の便数
PT = FOP_NOW * 100 // GOAL
AFTER_K = FOP_NOW + FOP_Y + FOP_K

CSS2 = CSS_S + """
.hero .lab span.tg{margin-left:0}
.two .card{padding:12px 14px 14px}.two .k{font-size:13px;color:var(--sub);font-weight:800}
.two .ato{display:flex;align-items:baseline;gap:4px;margin-top:8px;white-space:nowrap}.two .ato .a{font-size:15px;font-weight:800;color:var(--strong)}.two .ato .num{font-size:28px;display:inline;margin:0}
.two small{display:block;font-size:13px;color:var(--sub);margin-top:4px}
.yr{margin-top:12px;font-size:14px;line-height:1.6;color:var(--ink);font-weight:700}.yr b{color:var(--strong)}
.jgc{display:flex;align-items:center;gap:12px;padding:12px 16px;margin-top:8px}.jgc .tx{flex:1;min-width:0}.jgc .tx b{display:block;font-size:14px;color:var(--strong)}.jgc .tx small{display:block;font-size:13px;color:var(--sub)}
.jgc .v{text-align:right;white-space:nowrap}.jgc .v .num{font-size:22px}.jgc .bar{height:6px;border-radius:3px;background:var(--line2);margin-top:6px;overflow:hidden}.jgc .bar i{display:block;height:100%;background:var(--jisseki)}
.today{display:flex;align-items:center;gap:8px;margin:0 16px 12px;padding:8px 12px;border-radius:14px;background:var(--wash);font-size:13px;color:var(--sub);font-weight:700}.today b{color:var(--strong)}.today .dot{width:8px;height:8px;border-radius:50%;background:#15803D;flex:none}
.empty{padding:18px 18px 18px}.empty p{margin:0;font-size:15px;color:var(--ink);line-height:1.7}.empty .btn{margin-top:14px}
"""

def eb2(night=False, empty=False):
    lit = ' lit' if night else ''
    nxt = YOTEI[0]
    s = head(band=('道のり', ['道のり', '1便ごと', '月ごと'])) + '''
<div class="card hero" style="margin-top:12px"><div class="lab"><span class="tg" style="background:var(--wash);color:var(--strong)">実績</span>&nbsp;記録した便だけ<span>FLY ON ポイント</span></div>
<div class="big"><span class="num%s">%s</span><span class="u">FOP</span></div>
<div class="gauge"><div class="bar"><i style="width:%.1f%%"></i></div><div class="gl"><span>ポイント %d%%</span><span>3万</span></div>
<div class="bar t"><i style="width:%d%%"></i></div><div class="gl"><span>1年 %d%%（今日 11/9）</span><span>12/31</span></div></div>
<p class="yr">1年の <b>%d%%</b> が過ぎて、ポイントは <b>%d%%</b>。%s</p></div>
<div class="two"><div class="card"><span class="k">FOP だけで</span><div class="ato"><span class="a">あと</span><span class="num">%s</span><span class="u">FOP</span></div><small>3万 FOP で届く</small></div>
<div class="card"><span class="k">30回＋1万 FOP で</span><div class="ato"><span class="a">あと</span><span class="num">%d</span><span class="u">回</span></div><small>1万 FOP は済み</small></div></div>
<div class="card jgc"><div class="tx"><b>JGC（Life Status）</b><small>生涯で 1,500・国内線は1回 5</small><div class="bar"><i style="width:%.1f%%"></i></div></div><div class="v"><span class="num">%d</span><span class="u">／1,500</span><small style="display:block;font-size:13px;color:var(--sub);font-weight:700">あと %d回</small></div></div>
''' % (lit, c(FOP_NOW), FOP_NOW / GOAL * 100, PT, YEARP, YEARP, YEARP, PT,
       ('予定だけでは届かず、計画まで乗れば届きます（推定）' if not empty else '今のままのペースでは届きません（推定）'),
       c(LEFT), LEFT_N, LS_NOW / LS_GOAL * 100, LS_NOW, LS_LEFT_N)
    if empty:
        s += '''<div class="sec-h">入れたら届くか<small>推定</small></div>
<div class="card empty"><p>乗る予定の便や、修行の計画を入れると、年末までに届くかを推定します。</p><div class="btn">計画を作る</div></div>
'''
        return s
    s += '''<div class="sec-h">入れたら届くか<small>推定</small></div>
<div class="est y"><div class="tx"><b>予定の2便に乗ると</b><small>あと %s FOP・あと %d回</small></div><span><span class="num">＋%s</span></span></div>
<div class="est k"><div class="tx"><b>計画（残した案）の6便にも乗ると</b><small>FOP だけで届く（%s あまる）</small></div><span><span class="num">＋%s</span></span></div>
<p class="note">予定と計画は実績と分けて足しています。届くかは推定です。</p>
<div class="sec-h">次に乗る便<span class="r">予定と計画 ›</span></div>
<div class="card"><div class="row"><div class="tx"><b>11月22日（日）　羽田 → 那覇</b><small>%s・%s・<span class="tg tag-y">予定</span></small></div><span><span class="num%s" style="font-size:22px">＋%s</span><span class="u">FOP</span></span></div>
<div class="today"><span class="dot"></span><span>この路線の今日（11/9）　<b>%d便</b>・欠航なし</span></div></div>
''' % (c(LEFT - FOP_Y), LEFT_N - 2, c(FOP_Y), c(AFTER_K - GOAL), c(FOP_K), nxt['no'], nxt['fare'], ' amb' if night else '', c(fop(nxt)), TODAY_N)
    return s

def tools():
    return '''<div class="card lst" style="margin-top:10px"><div class="row"><div class="tx"><b>路線を入れて計算する</b><small>乗る前に FOP を確かめる</small></div><span class="r">›</span></div></div>'''

def pE1():
    body = '<div class="wrap">' + eb2() + tools() + '''
<div class="ann"><b>E1 道のり（2版）</b><ul><li>大きな数字の下の「クリスタルまで あと」の行は、左の箱「FOP だけで あと 8,256」と同じなので1つにした</li><li>2つの道は「あと ○」を大きい数字の前に同じ行で。題は「FOP だけで」「30回＋1万 FOP で」</li><li>JGC（Life Status）の行を戻した。目指さない人は ✎ の「道のりに出すもの」で OFF（07）</li><li>細い棒の意味を字で：「1年の 86% が過ぎて、ポイントは 72%」と届くか（推定）</li><li>次に乗る便のカードに「この路線の今日」の便数と欠航。乗る日は「JL903 定刻」に変わる。修行の路線の運航の欄はタブから外す（修行担当と相談）</li></ul></div></div>''' + tabs('修行')
    page(OUT + '/E1-overview-v2.html', 'E1 道のり 2版' + T, body, extra_css=CSS2)

def pE1b():
    body = '<div class="wrap">' + eb2(empty=True) + tools() + '''
<div class="ann"><b>E1b 予定・計画が空の人</b><ul><li>「入れたら届くか」の所に一文と「計画を作る」のボタン1つだけ。空の行（—・まだありません・0便）は並べない</li><li>次に乗る便のカードは出さない（予定を入れると出る）</li><li>届くかの一文は「今のままのペース」の推定に変わる</li></ul></div></div>''' + tabs('修行')
    page(OUT + '/E1b-empty-v2.html', 'E1b 予定・計画が空の人 2版' + T, body, extra_css=CSS2)

def pE2():
    f = JALF[1]
    t = f['tpm']; fm = int(t * .75)
    css = CSS2 + """.calc{padding:6px 18px 16px}.cl{display:flex;align-items:baseline;gap:8px;min-height:44px;padding:8px 0}.cl + .cl{box-shadow:inset 0 1px 0 var(--line2)}.cl .k{flex:1;font-size:14px;color:var(--sub)}.cl .k b{color:var(--strong)}.cl .num{font-size:24px}
.cl.tot .num{font-size:44px}.cl .op{font-family:var(--sign);font-size:20px;color:var(--pale);width:20px}"""
    body = '''<div class="wrap">%s
<div class="card" style="padding:16px 18px"><p class="note" style="margin:0;font-weight:700">2026年%d月%d日（%s）・%s・%s</p><div style="font-size:26px;font-weight:800;color:var(--strong);margin-top:4px">%s → %s</div><p class="note" style="margin:4px 0 0">普通席・%s（記録した運賃）・%s</p></div>
<div class="sec-h">FOP の数え方</div>
<div class="card calc"><div class="cl"><span class="op"></span><span class="k">区間マイル</span><span class="num">%s</span></div>
<div class="cl"><span class="op">×</span><span class="k">積算率 <b>75%%</b>（普通席・セイバー）</span><span class="num">%s</span></div>
<div class="cl"><span class="op">×</span><span class="k"><b>2</b></span><span class="num">%s</span></div>
<div class="cl"><span class="op">＋</span><span class="k">搭乗ボーナス（セイバー）</span><span class="num">200</span></div>
<div class="cl tot"><span class="op">＝</span><span class="k"><b>この便の FOP</b></span><span><span class="num">%s</span><span class="u">FOP</span></span></div></div>
<div class="two"><div class="card"><span class="k">回数</span><div class="ato"><span class="num">＋1</span><span class="u">回</span></div><small>JAL グループ便</small></div><div class="card"><span class="k">JGC（Life Status）</span><div class="ato"><span class="num">＋5</span></div><small>国内線は1回 5</small></div></div>
<div class="btn w">運賃を選び直す</div>
<p class="note">式は各社の公開ページ（2026年10月に確認）。キャンペーンのボーナスは含みません。</p>
<div class="ann"><b>E2 1便の内訳（2版）</b><ul><li>1版から形は変えず、記録をフライトの案と同じ便（11/1 JL907 羽田→那覇・JA861J）にそろえた</li><li>Life Status の箱は E1 と同じ「JGC（Life Status）」の名前に</li><li>今のフライトの見方「修行」はここに移す</li></ul></div></div>''' % (
        head(back='1便ごと'), f['m'], f['d'], f['wd'], f['no'], f['typ'], short(f['a']), short(f['b']), f['fare'], f['reg'], c(t), c(fm), c(fm * 2), c(fop(f))) + tabs('修行')
    page(OUT + '/E2-flight-v2.html', 'E2 1便の内訳 2版' + T, body, extra_css=css)

def pE3():
    css = CSS2 + """.rc{padding:16px 18px 16px}.rc .k{font-size:13px;color:var(--sub);font-weight:800}.rc .rr{display:flex;align-items:baseline;gap:10px;min-height:44px;padding:6px 0}.rc .rr + .rr{box-shadow:inset 0 1px 0 var(--line2)}.rc .rr .tx{flex:1;font-size:14px;font-weight:700;color:var(--ink)}.rc .rr .num{font-size:30px}.rc .rr small{display:block;font-size:13px;color:var(--sub);font-weight:600}
.yr12{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.yr12 > div{background:var(--card);border-radius:14px;padding:10px 10px 10px;box-shadow:var(--shadow)}
.yr12 .mo{font-size:13px;font-weight:800;color:var(--sub);display:block}.yr12 .num{font-size:22px;display:block;margin-top:4px}.yr12 small{display:block;font-size:13px;color:var(--sub);font-weight:700;margin-top:2px}
.yr12 > div.z small{color:var(--pale)}
.yr12 > div.y{background:var(--yotei);box-shadow:none}.yr12 > div.y .mo,.yr12 > div.y small,.yr12 > div.y .num{color:var(--yotei-ink)}.yr12 > div.k{background:var(--keikaku);box-shadow:none}.yr12 > div.k .mo,.yr12 > div.k small,.yr12 > div.k .num{color:var(--keikaku-ink)}"""
    bal = GOAL; cells = ''
    for m in range(1, 12):
        used = sum(fop(f) for f in JM.get(m, []))
        bal -= used
        cells += '<div%s><span class="mo">%s</span><span class="num">%s</span><small>%s</small></div>' % ('' if used else ' class="z"', ('%d月末' % m) if m < 11 else '11月 今日まで', c(bal), ('ひいた ' + c(used)) if used else 'JAL の便なし')
    yb = bal - FOP_Y; kb = yb - FOP_K
    cells += '<div class="y"><span class="mo">11月 予定</span><span class="num">%s</span><small>ひく %s</small></div>' % (c(yb), c(FOP_Y))
    cells += '<div class="k"><span class="mo">12月 計画</span><span class="num">0</span><small>%s あまる</small></div>' % c(-kb)
    rt = {}
    for f in JALF: k = tuple(sorted((f['a'], f['b']))); rt[k] = rt.get(k, 0) + fop(f)
    top = sorted(rt.items(), key=lambda x: -x[1])[:3]
    rk = ''.join('<div class="row"><div class="tx"><b>%s ⇄ %s</b><small>%d回</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>' % (
        short(k[0]), short(k[1]), sum(1 for f in JALF if tuple(sorted((f['a'], f['b']))) == k), c(v)) for k, v in top)
    body = '''<div class="wrap">%s
<div class="card rc" style="margin-top:12px"><span class="k">12月31日の残り（クリスタルまで・推定）</span>
<div class="rr"><div class="tx">実績のまま<small>このあと乗らなければ</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>
<div class="rr"><div class="tx">予定の2便に乗ると<small>11/22・11/24</small></div><span><span class="num">%s</span><span class="u">FOP</span></span></div>
<div class="rr"><div class="tx">計画の6便にも乗ると<small>%s FOP あまって届く</small></div><span><span class="num">0</span><span class="u">FOP</span></span></div></div>
<div class="sec-h">月末の残り<small>3万 FOP から・実績</small><span class="r">1回 平均 %s</span></div><div class="yr12">%s</div>
<p class="note">色の地の2つは予定と計画（実績の月とは分けて、最後に足す）。</p>
<div class="sec-h">路線ごと<small>実績</small></div><div class="card lst">%s</div>
<div class="ann"><b>E3 月ごと（2版）</b><ul><li>G2 の「月末の残り」を月ごとの見方に入れた。3万から月ごとにひいて、月末にいくつ残ったか</li><li>「ひいた」は赤にせず濃いグレーの字。色で良し悪しを言わない</li><li>年末の残りは「実績のまま／予定まで／計画まで」の3行で、どれも推定</li><li>11月は「今日まで」。ANA だけの月は「JAL の便なし」（乗っていないとは書かない）</li><li>1版の月の棒はやめた（ひいた数と同じ中身のため）。成績の「修行のまとめ」はここへ</li></ul></div></div>''' % (
        head(band=('月ごと', ['道のり', '1便ごと', '月ごと'])), c(LEFT), c(yb), c(-kb), c(FOP_NOW // CNT_NOW), cells, rk) + tabs('修行')
    page(OUT + '/E3-months-v2.html', 'E3 月ごと 2版' + T, body, extra_css=css)

def p07():
    css = CSS2 + MP.CSS07 + """.sh-h{font-size:15px;font-weight:800;color:var(--strong);margin:16px 4px 6px}"""
    def rows(L):
        return ''.join('<div class="vrow">%s<div class="tx"><b>%s</b><small>%s</small></div><span class="sw %s">%s</span>%s</div>' % (
            ('<span class="n">%s</span>' % n) if n is not None else '', a, b, o, o.upper(), ('<span style="color:var(--pale)">%s</span>' % I['grip']) if n is not None else '') for a, b, o, n in L)
    v = [('道のり', '大きな数字・2つの道・届くか', 'on', '1'), ('1便ごと', '1便の FOP と内訳', 'on', '2'), ('月ごと', '月末の残り・路線ごと', 'on', '3')]
    d = [('2つの道', 'FOP だけで／30回＋1万 FOP で', 'on', None), ('JGC（Life Status）', '生涯 1,500 まで（OFF にした例）', 'off', None), ('入れたら届くか', '予定と計画を足した推定', 'on', None), ('次に乗る便', 'この路線の今日の便数つき', 'on', None)]
    body = '<div class="wrap">' + eb2() + '</div><div class="dim"></div><div class="sheet"><div class="grab"></div><div style="font-size:18px;font-weight:800;color:var(--strong);margin:0 4px">見方を選ぶ</div>' + \
        '<div class="sh-h">見方</div><div class="card">%s</div><div class="sh-h">道のりに出すもの</div><div class="card">%s</div>' % (rows(v), rows(d)) + \
        '<p class="note">JGC を目指さない人は「JGC（Life Status）」を OFF。ON／OFF は 11/9 の決定どおり（タブ・ホームと同じ部品）。</p></div>' + tabs('修行')
    page(OUT + '/07-views-v2.html', '07 見方を選ぶ 2版' + T, body, extra_css=css)

def pN1():
    css = CSS2 + """.gauge .bar i{background:#5FD993}.gauge .bar.t i{background:#4A5664}.jgc .bar i{background:#8996A7}.est.y,.est.k{box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}.today{background:#0A0F14}.today .dot{background:#5FD993}"""
    body = '<div class="wrap">' + eb2(night=True) + tools() + '''<div class="ann"><b>夜の画面（E1 2版）</b><ul><li>光るのは実績の FOP（緑）と次に乗る便の FOP（琥珀＝「次」）だけ。JGC の棒は光らせない灰色</li><li>「この路線の今日」の点は緑（運航している＝ふだんの状態）。会社の色・金は使わない</li><li>主ボタン（計画を作る）は白い字と縁</li></ul></div></div>''' + tabs('修行')
    page(OUT + '/N1-overview-night-v2.html', 'N1 夜の画面 2版' + T, body, night=True, extra_css=css)

def pN1b():
    css = CSS2 + """.gauge .bar i{background:#5FD993}.gauge .bar.t i{background:#4A5664}.jgc .bar i{background:#8996A7}"""
    body = '<div class="wrap">' + eb2(night=True, empty=True) + tools() + '</div>' + tabs('修行')
    page(OUT + '/N1b-empty-night-v2.html', 'N1b 夜・予定が空 2版' + T, body, night=True, extra_css=css)

for fn in (pE1, pE1b, pE2, pE3, p07, pN1, pN1b): fn()
print('ok', FOP_NOW, LEFT, LEFT_N, LS_NOW, LS_LEFT_N, AFTER_K - GOAL)
