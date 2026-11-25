# -*- coding: utf-8 -*-
# タブの組み替えと「いまの空港」の画面案を組み立てる
# base.css（design/micro の共通の見た目＝main の web/index.html の色と文字）を各ページに埋め込み、外部の読み込みなしで開ける HTML にする
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from icons import P
OUT = os.path.dirname(HERE)
CSS = open(HERE + '/base.css', encoding='utf-8').read()

P.update({
 'log': '<path d="M6 4h10a2 2 0 0 1 2 2v14H8a2 2 0 0 1-2-2zM6 18a2 2 0 0 1 2-2h10M10 8h5M10 11h5"/>',
 'search': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
 'down': '<path d="M6 9l6 6 6-6"/>',
 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
 'plus': '<path d="M12 5v14M5 12h14"/>',
 'here': '<path d="M12 3l7 18-7-4-7 4z"/>',
 'cube': '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
})
def ic(name, cls='ic'):
    return '<svg class="%s i-%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, name, P[name])

TABS = {
 'A': [('home', 'ホーム', 'home'), ('now', 'いまの空港', 'ops'), ('rec', '記録', 'log'), ('me', 'マイページ', 'user')],
 'B': [('home', 'ホーム', 'home'), ('book', '図鑑', 'book'), ('log', 'フライト', 'plane'), ('now', 'いまの空港', 'ops'), ('sg', '修行', 'stairs')],
}
def tabbar(plan, cur):
    items = TABS[plan]
    out = ['<nav class="tabs n%d" aria-label="下のタブ">' % len(items)]
    for k, lb, icn in items:
        on = k == cur
        out.append('<button type="button"%s>%s<span>%s</span>%s</button>' % (
            ' aria-current="page"' if on else '', ic(icn), lb, '<i class="dt"></i>' if on else ''))
    out.append('</nav>')
    return ''.join(out)

PAGE_CSS = r'''
body{padding:0 16px 132px}
.tabs{position:fixed;left:50%;bottom:14px;width:calc(100% - 28px);max-width:402px;transform:translateX(-50%);z-index:20}
.tabs.n4{grid-template-columns:repeat(4,1fr)}
.tabs button{position:relative}
.tabs button span{white-space:nowrap;letter-spacing:-.02em}
.tabs .dt{position:absolute;bottom:7px;left:50%;width:5px;height:5px;margin-left:-2.5px;border-radius:50%;background:var(--acc)}
.top{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:18px 0 6px}
.brand{display:flex;align-items:center;gap:8px;font-size:20px;font-weight:800;color:var(--strong);letter-spacing:.04em}
.brand svg{width:24px;height:24px;stroke-width:2}
.mepill{min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.plan{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--sub)}
.head{display:flex;align-items:center;gap:8px;padding:10px 0 4px}
.ap{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:0 14px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.ap .cd{display:inline-flex;align-items:center;justify-content:center;height:28px;padding:0 8px;border-radius:9px;background:var(--hero);color:#fff;font-size:13px;font-weight:800;letter-spacing:.06em}
.ap b{font-size:18px;font-weight:800;color:var(--strong)}
.ap svg{width:18px;height:18px;color:var(--sub)}
.ap .pn{width:16px;height:16px;color:var(--pin)}
.upd{margin-left:auto;display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.upd small{font-size:12px;font-weight:600;color:var(--mute)}
.upd svg{width:17px;height:17px;color:var(--sub)}
.ibtn{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:50%;background:var(--card);box-shadow:var(--shadow);color:var(--sub)}
.ibtn svg{width:20px;height:20px}
.sum{margin-top:12px;padding:16px 14px 14px;display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.sum.c2{grid-template-columns:repeat(2,1fr)}
.sum > div{min-width:0;padding:0 4px}
.sum .k{font-size:12px;font-weight:700;color:var(--sub);white-space:nowrap}
.sum .v{margin-top:2px;font-size:28px;line-height:1.15;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;letter-spacing:-.02em;white-space:nowrap}
.sum .v .u{font-size:13px}
.sum .v.sm{font-size:22px;line-height:1.45}
.sum .s{margin-top:4px;font-size:12px;color:var(--mute);line-height:1.4}
.sum .warn{color:#9A3412}
.seg3{display:flex;margin-top:16px;padding:4px;border-radius:999px;background:var(--pill)}
.seg3 button{flex:1;min-height:44px;padding:0 6px;border-radius:999px;font-size:14px;font-weight:800;color:var(--sub);white-space:nowrap}
.seg3 button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.tools{display:flex;gap:8px;margin-top:14px;align-items:center}
.dir{display:inline-flex;padding:3px;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.dir button{min-height:40px;min-width:56px;padding:0 12px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.dir button[aria-pressed=true]{background:var(--strong);color:#fff}
.chip{display:inline-flex;align-items:center;min-height:46px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:700;color:var(--ink);white-space:nowrap}
.srch{flex:1;min-width:0;display:flex;align-items:center;gap:6px;min-height:46px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--mute);white-space:nowrap;overflow:hidden}
.srch svg{width:17px;height:17px;flex:none}
.hr{margin-top:18px;padding:16px 16px 6px}
.hr .hh{display:flex;align-items:baseline;justify-content:space-between}
.hr .hh b{font-size:17px;font-weight:800;color:var(--strong)}
.hr .hh small{font-size:12px;color:var(--mute);font-weight:600}
.fl{display:grid;grid-template-columns:62px 1fr auto;align-items:center;gap:10px;min-height:48px;padding:7px 0;margin-top:8px}
.fl .t{font-size:20px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;letter-spacing:-.02em;line-height:1.1}
.fl .t s{display:block;font-size:12px;font-weight:600;color:var(--mute);text-decoration:line-through}
.fl .t.late{color:#9A3412}
.fl .m{min-width:0}
.fl .m b{font-size:15px;font-weight:800;color:var(--strong)}
.fl .m .no{display:inline-block;margin-right:8px;font-size:13px;font-weight:800;color:var(--sub);font-variant-numeric:tabular-nums}
.fl .m small{display:block;font-size:12px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fl .st{font-size:12px;font-weight:700;color:var(--mute);text-align:right;white-space:nowrap}
.fl .st.late{color:#9A3412}
.fl .st.x{color:var(--strong)}
.acc{display:inline-block;width:3px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.acc.jl{background:var(--jal);opacity:.75}.acc.nh{background:var(--ana);opacity:.75}.acc.ot{background:#9CA3AF}
.more{display:flex;justify-content:center;margin:8px 0 6px}
.more button{min-height:44px;padding:0 16px;border-radius:999px;font-size:13px;font-weight:700;color:var(--sub)}
.note{margin-top:14px;font-size:12px;color:var(--mute);text-align:center}
/* 記録 */
.rt{display:flex;align-items:center;justify-content:space-between;padding:8px 0 0}
.rt h1{font-size:26px}
.rt .acts{display:flex;gap:8px}
.cbtn{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;background:var(--card);box-shadow:var(--shadow);color:var(--strong)}
.cbtn.dark{background:var(--strong);color:#fff;box-shadow:none}
.cbtn svg{width:22px;height:22px}
.views{display:flex;gap:22px;margin-top:10px;font-size:15px;font-weight:800;color:var(--sub)}
.views span{display:inline-flex;align-items:center;min-height:44px}
.views .on{color:var(--strong);box-shadow:inset 0 -3px 0 var(--strong)}
.yr{margin-top:10px;padding:18px 18px 14px}
.yr .y{text-align:center;font-size:22px;font-weight:800;color:var(--strong)}
.yr .row{display:flex;justify-content:space-between;align-items:baseline;margin-top:8px}
.yr .row .num{font-size:30px}
.yr .sk{margin-top:4px;font-size:13px;color:var(--ink)}
.yr .sk .num{font-size:22px}
.yr .car{margin-top:6px;font-size:12px;color:var(--mute);text-align:center}
.mo{display:flex;justify-content:space-between;align-items:baseline;margin:20px 4px 8px}
.mo b{font-size:17px;font-weight:800;color:var(--strong)}
.mo small{font-size:13px;color:var(--mute)}
.lg{display:grid;grid-template-columns:44px 1fr auto;gap:12px;align-items:center;padding:14px 16px;margin-top:10px}
.lg .d{text-align:center;line-height:1.1}
.lg .d b{display:block;font-size:24px;font-weight:800;color:var(--strong)}
.lg .d small{font-size:12px;color:var(--mute)}
.lg .r b{font-size:17px;font-weight:800;color:var(--strong)}
.lg .r small{display:block;font-size:12px;color:var(--mute)}
.lg .k{text-align:right;font-size:13px;color:var(--mute)}
.lg .k .num{font-size:19px}
/* 滑走路・3D */
.rw{margin-top:16px;padding:16px}
.rw .tt{display:flex;justify-content:space-between;align-items:baseline}
.rw .tt b{font-size:15px;font-weight:800;color:var(--strong)}
.rw .tt small{font-size:12px;color:var(--mute)}
.rw svg.plan{display:block;width:100%;height:auto;margin-top:8px}
.rwl{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:10px}
.rwl div{padding:10px 12px;border-radius:14px;background:var(--bg)}
.rwl b{display:block;font-size:22px;font-weight:800;color:var(--strong);line-height:1.2}
.rwl small{font-size:12px;color:var(--mute)}
.rwl .off b{color:#9CA3AF}
.d3{margin-top:14px;padding:0;overflow:hidden}
.d3 .pv{position:relative;height:150px;background:linear-gradient(#E9F0F8,#F6F8FB)}
.d3 .pv svg{position:absolute;inset:0;width:100%;height:100%}
.d3 .bt{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px 14px}
.d3 .bt b{font-size:15px;font-weight:800;color:var(--strong)}
.d3 .bt small{display:block;font-size:12px;color:var(--mute)}
.d3 .pill.dark svg{width:18px;height:18px}
.mapc{margin-top:14px;padding:0;overflow:hidden}
.mapc .mp{height:132px;background:#E8EEF5;position:relative}
.mapc .mp svg{position:absolute;inset:0;width:100%;height:100%}
.mapc .bt{display:flex;justify-content:space-between;align-items:center;padding:12px 14px 14px}
.mapc .bt b{font-size:15px;font-weight:800;color:var(--strong)}
.mapc .bt small{display:block;font-size:12px;color:var(--mute)}
.chev{width:20px;height:20px;color:var(--mute)}
/* 特別塗装機 */
.lv{margin-top:12px;padding:16px}
.lv .a{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.lv .a b{font-size:17px;font-weight:800;color:var(--strong)}
.lv .a .rg{display:block;font-size:13px;font-weight:800;color:var(--sub);letter-spacing:.06em}
.lv .stp{flex:none;display:inline-flex;align-items:center;min-height:30px;padding:0 12px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--strong);white-space:nowrap}
.lv .stp.now{background:var(--pin-wash);box-shadow:inset 0 0 0 1.5px var(--pin)}
.lv .b{display:flex;justify-content:space-between;align-items:baseline;margin-top:10px;font-size:13px;color:var(--ink)}
.lv .b .num{font-size:20px}
.lv .b small{font-size:12px;color:var(--mute)}
.lv .z{margin-top:8px;font-size:12px;color:var(--mute)}
.lvh{display:flex;justify-content:space-between;align-items:baseline;margin:18px 4px 0}
.lvh b{font-size:15px;font-weight:800;color:var(--strong)}
.lvh small{font-size:12px;color:var(--mute)}
/* シート */
.dim{position:fixed;inset:0;background:rgba(15,23,42,.38);z-index:30}
.sh{position:fixed;left:0;right:0;bottom:0;z-index:31;max-width:430px;margin:0 auto;background:var(--card);border-radius:26px 26px 0 0;padding:10px 20px 30px;box-shadow:0 -10px 30px -10px rgba(17,24,39,.25)}
.sh .grab{width:40px;height:5px;border-radius:3px;background:var(--track);margin:0 auto 14px}
.sh h2{font-size:20px}
.sh .route{display:flex;align-items:center;justify-content:space-between;margin-top:14px;padding:14px 16px;border-radius:18px;background:var(--bg)}
.sh .route div{text-align:center;min-width:0}
.sh .route .num{font-size:28px;line-height:1.15}
.sh .route small{display:block;font-size:12px;color:var(--mute)}
.sh .route b.c{display:block;font-size:15px;font-weight:800;color:var(--strong)}
.sh .route svg{width:24px;height:24px;color:var(--mute);flex:none}
.sh dl{margin-top:12px;display:grid;gap:6px}
.sh dl div{display:flex;justify-content:space-between;font-size:14px}
.sh dt{color:var(--mute)}
.sh dd{font-weight:700;color:var(--strong)}
.sh .go{display:flex;width:100%;margin-top:18px;min-height:52px;font-size:15px}
.sh .go svg{width:20px;height:20px}
.sh .fine{margin-top:10px;font-size:12px;color:var(--mute);text-align:center}
.pk{display:flex;align-items:center;gap:12px;min-height:56px;padding:8px 12px;margin-top:8px;border-radius:16px;background:var(--bg)}
.pk .cd{display:inline-flex;align-items:center;justify-content:center;min-width:48px;height:30px;border-radius:9px;background:var(--hero);color:#fff;font-size:13px;font-weight:800;letter-spacing:.06em}
.pk b{font-size:16px;font-weight:800;color:var(--strong)}
.pk small{display:block;font-size:12px;color:var(--mute)}
.pk .r{margin-left:auto;font-size:12px;font-weight:700;color:var(--sub);white-space:nowrap}
.pk svg{width:16px;height:16px;color:var(--pin)}
.shh{margin-top:16px;font-size:12px;font-weight:800;color:var(--mute)}
'''

def page(name, title, body, plan=None, cur=None):
    bar = tabbar(plan, cur) if plan else ''
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s</style></head><body>%s%s</body></html>') % (title, CSS, PAGE_CSS, body, bar)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html)
    print('書いた', name)

BRAND = '<div class="brand"><svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M8 15.5l8-7.5-2.5 8-2-2.5z"/></svg>そらメモ</div>'
def top(plan, label):
    right = '<button class="mepill">マイページ</button>' if plan == 'B' else ''
    return '<div class="top">%s<span class="plan">%s</span>%s</div>' % (BRAND, label, right)

def head(code='HND', name='羽田', t='14:22'):
    return ('<div class="head"><button class="ap">%s<span class="cd">%s</span><b>%s</b>%s</button>'
            '<button class="upd"><small>最後に読んだ</small>%s%s</button></div>') % (
            ic('pin', 'ic pn'), code, name, ic('down'), t, ic('retry'))

def summary(three=True):
    if three:
        return ('<section class="card sum">'
                '<div><div class="k">滑走路</div><div class="v sm">34R<span class="u">/</span>34L</div><div class="s">離陸 34R<br>着陸 34L</div></div>'
                '<div><div class="k">平均の遅れ</div><div class="v">+12<span class="u">分</span></div><div class="s">いつもより<br>（推定）</div></div>'
                '<div><div class="k">特別塗装機</div><div class="v">4<span class="u">機</span></div><div class="s">今日来る<br>（予想）</div></div>'
                '</section>')
    return ('<section class="card sum c2">'
            '<div><div class="k">今日の便</div><div class="v">24<span class="u">便</span></div><div class="s">出発 12・到着 12</div></div>'
            '<div><div class="k">平均の遅れ</div><div class="v sm">ほぼ定刻</div><div class="s">いつもより（推定）</div></div>'
            '</section>')

def seg(on):
    out = ['<div class="seg3" role="tablist">']
    for k in ['今日の便', '滑走路・3D', '特別塗装機']:
        out.append('<button aria-pressed="%s">%s</button>' % ('true' if k == on else 'false', k))
    out.append('</div>')
    return ''.join(out)

def fl(t, no, dest, typ, st, al='nh', late=None, cls=''):
    tt = ('<div class="t late"><s>%s</s>%s</div>' % (t, late)) if late else '<div class="t">%s</div>' % t
    return ('<div class="fl">%s<div class="m"><span class="no"><i class="acc %s"></i>%s</span><b>%s</b><small>%s</small></div>'
            '<div class="st %s">%s</div></div>') % (tt, al, no, dest, typ, cls, st)

def flights(dir_on='出発'):
    tools = ('<div class="tools"><div class="dir"><button aria-pressed="%s">出発</button><button aria-pressed="%s">到着</button></div>'
             '<span class="chip">遅れあり</span><span class="srch">%s便名・行き先</span></div>') % (
             'true' if dir_on == '出発' else 'false', 'false' if dir_on == '出発' else 'true', ic('search'))
    h14 = ('<section class="card hr"><div class="hh"><b>14時台</b><small>出発 18便のうち 4便</small></div>'
           + fl('14:20', 'NH 247', '福岡', 'B787-9・ANA', '出発済み', 'nh')
           + fl('14:30', 'JL 519', '新千歳', 'A350-900・JAL', '+15分', 'jl', late='14:45', cls='late')
           + fl('14:35', 'BC 513', '神戸', 'B737-800・スカイマーク', '定刻', 'ot')
           + fl('14:45', 'NH 65', '新千歳', 'B777-200・ANA', '定刻', 'nh')
           + '<div class="more"><button>14時台をすべて見る（18便）</button></div></section>')
    h15 = ('<section class="card hr"><div class="hh"><b>15時台</b><small>出発 21便のうち 3便</small></div>'
           + fl('15:00', 'JL 909', '那覇', 'B767-300・JAL', '定刻', 'jl')
           + fl('15:05', 'NH 993', '那覇', 'B787-8・ANA', '定刻', 'nh')
           + fl('15:10', '6J 77', '宮崎', 'B737-800・ソラシドエア', '欠航', 'ot', cls='x')
           + '</section>')
    return tools + h14 + h15 + '<p class="note">便と機種は ODPT の時刻表から。遅れは便ごとの実際の時刻から</p>'

# ───── 案A いまの空港 ─────
page('a1-now.html', '案A いまの空港',
     top('A', '案A') + head() + summary() + seg('今日の便') + flights(), 'A', 'now')

# ───── 案A 記録（フライト） ─────
rec = (top('A', '案A') +
       '<div class="rt"><h1>記録</h1><div class="acts"><button class="cbtn">%s</button><button class="cbtn dark">%s</button></div></div>' % (ic('search'), ic('plus')) +
       '<div class="seg3"><button aria-pressed="true">フライト</button><button aria-pressed="false">図鑑</button><button aria-pressed="false">修行</button></div>' +
       '<div class="views"><span class="on">日誌</span><span>地図</span><span>年のまとめ</span></div>' +
       '<section class="card yr"><div class="y">2026年</div><div class="row"><span><span class="num">30</span><span class="u">便</span></span><span><span class="num">24,017</span><span class="u">km</span></span></div>'
       '<div class="sk">空の上 <span class="num">49</span><span class="u">時間</span> <span class="num">20</span><span class="u">分</span></div>'
       '<div class="car">車など 1（90 km）は別に数えています</div></section>' +
       '<div class="mo"><b>11月　<small>4便</small></b><small>2,820 km</small></div>' +
       '<section class="card lg"><div class="d"><b>23</b><small>月</small></div><div class="r"><b>大分 → 羽田</b><small>19:12 発・ANA</small></div><div class="k"><span class="num">772</span><span class="u">km</span></div></section>' +
       '<section class="card lg"><div class="d"><b>14</b><small>土</small></div><div class="r"><b>羽田 → 大分</b><small>14:36 発・ANA</small></div><div class="k"><span class="num">772</span><span class="u">km</span></div></section>' +
       '<p class="note">修行のピルは、設定で修行を ON にした人だけ出る</p>')
page('a2-record.html', '案A 記録', rec, 'A', 'rec')

# ───── 案B いまの空港 ─────
page('b1-now.html', '案B いまの空港',
     top('B', '案B') + head() + summary() + seg('今日の便') + flights(), 'B', 'now')

# ───── 共通：滑走路・3D ─────
PLAN_SVG = ('<svg class="plan" viewBox="0 0 340 170" aria-hidden="true">'
  '<rect x="0" y="0" width="340" height="170" rx="14" fill="#EEF2F7"/>'
  '<path d="M20 150 Q120 140 170 150 T330 135" stroke="#D5DEE9" stroke-width="18" fill="none"/>'
  '<g stroke-linecap="round">'
  '<line x1="120" y1="28" x2="120" y2="140" stroke="#1F2937" stroke-width="7"/>'
  '<line x1="200" y1="30" x2="200" y2="138" stroke="#1F2937" stroke-width="7"/>'
  '<line x1="140" y1="150" x2="240" y2="95" stroke="#9CA3AF" stroke-width="7"/>'
  '<line x1="230" y1="60" x2="300" y2="20" stroke="#1F2937" stroke-width="7"/></g>'
  '<g fill="#2563EB"><path d="M200 16l-7 12h14z"/><path d="M120 150l-7-12h14z"/><path d="M308 14l-13 2 7 10z"/></g>'
  '<g font-size="12" font-weight="800" fill="#374151" font-family="sans-serif">'
  '<text x="92" y="24">34L</text><text x="210" y="26">34R</text><text x="252" y="128">22</text><text x="300" y="44">05</text></g></svg>')
D3_SVG = ('<svg viewBox="0 0 360 150" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
  '<path d="M20 120 L180 60 L340 110 L180 150 Z" fill="#DCE4EE"/>'
  '<path d="M60 118 L230 66" stroke="#4B5563" stroke-width="7" stroke-linecap="round"/>'
  '<path d="M110 132 L290 80" stroke="#4B5563" stroke-width="7" stroke-linecap="round"/>'
  '<path d="M150 98 l40 -12 l18 8 l-40 12 z" fill="#F8FAFC" stroke="#9CA3AF"/>'
  '<path d="M150 98 v-12 l40 -12 v12" fill="#E5E9EF" stroke="#9CA3AF"/>'
  '<path d="M250 40 l14 -3 l-2 4 l10 -2 l-2 3 l-20 4z" fill="#1F2937"/></svg>')
MAP_SVG = ('<svg viewBox="0 0 360 132" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
  '<path d="M0 0H360V60Q260 40 200 70T0 80Z" fill="#F1F3E9"/>'
  '<circle cx="190" cy="78" r="58" fill="none" stroke="#94A3B8" stroke-dasharray="4 4"/>'
  '<circle cx="190" cy="78" r="26" fill="none" stroke="#94A3B8" stroke-dasharray="4 4"/>'
  '<path d="M40 120 C120 100 160 90 186 78" stroke="#2563EB" stroke-width="2" fill="none" opacity=".7"/>'
  '<path d="M330 20 C260 40 220 60 194 76" stroke="#2563EB" stroke-width="2" fill="none" opacity=".7"/>'
  '<path d="M184 66 l-6 22 M196 64 l-6 22 M190 84 l14 -8" stroke="#1F2937" stroke-width="4" stroke-linecap="round"/></svg>')
rw = (top('B', '共通') + head() + summary() + seg('滑走路・3D') +
      '<section class="card rw"><div class="tt"><b>滑走路</b><small>14:20 の航跡から</small></div>' + PLAN_SVG +
      '<div class="rwl"><div><b>34R</b><small>離陸</small></div><div><b>34L</b><small>着陸</small></div>'
      '<div><b>05</b><small>離陸（ときどき）</small></div><div class="off"><b>22</b><small>使っていない</small></div></div></section>' +
      '<section class="card d3"><div class="pv">' + D3_SVG + '</div><div class="bt"><div><b>3D で空港を見る</b><small>押したときだけ読む・約0.7MB</small></div>'
      '<button class="pill dark">%s開く</button></div></section>' % ic('cube') +
      '<section class="card mapc"><div class="mp">' + MAP_SVG + '</div><div class="bt"><div><b>地図</b><small>いま飛んでいる機体と空の道すじ</small></div>%s</div></section>' % ic('chev', 'ic chev'))
page('k1-runway.html', '共通 滑走路・3D', rw, 'B', 'now')

# ───── 共通：特別塗装機 ─────
def lv(name, rg, st, now, fl_, t, tl, z):
    return ('<section class="card lv"><div class="a"><div><b>%s</b><span class="rg">%s</span></div><span class="stp%s">%s</span></div>'
            '<div class="b"><span>%s</span><span><span class="num">%s</span> <small>%s</small></span></div>%s</section>') % (
            name, rg, ' now' if now else '', st, fl_, t, tl, ('<div class="z">%s</div>' % z) if z else '')
lvp = (top('B', '共通') + head() + summary() + seg('特別塗装機') +
       '<div class="lvh"><b>今日来る 4機</b><small>どれも予想（保証しません）</small></div>' +
       lv('さくら色の塗装', 'JA00A1', 'いる（予想）', True, 'JL 512 新千歳から', '13:55', '着いた', '図鑑：乗ったことあり') +
       lv('夜空の塗装', 'JA00B2', '15:10 着（予想）', False, 'NH 248 福岡から', '15:10', '着（予想）', '') +
       lv('海の塗装', 'JA00C3', '16:40 発（予想）', False, 'BC 517 神戸へ', '16:40', '発（予想）', '') +
       lv('森の塗装', 'JA00D4', '出発した', False, 'JL 905 那覇へ', '10:20', '出発', '図鑑：見たことあり') +
       '<p class="note">名前と登録記号は見本。図鑑に入るのは乗った・見た記録からだけ</p>')
page('k2-livery.html', '共通 特別塗装機', lvp, 'B', 'now')

# ───── 共通：便を押したとき ─────
shp = (top('B', '共通') + head() + summary() + seg('今日の便') + flights() +
       '<div class="dim"></div><div class="sh"><div class="grab"></div><h2>JL 519</h2>'
       '<div class="route"><div><b class="c">羽田</b><span class="num">14:45</span><small>予定 14:30</small></div>%s'
       '<div><b class="c">新千歳</b><span class="num">16:20</span><small>予定 16:05</small></div></div>'
       '<dl><div><dt>機種</dt><dd>A350-900（時刻表から）</dd></div><div><dt>遅れ</dt><dd>+15分</dd></div></dl>'
       '<button class="pill dark go">%sこの便をフライト記録に追加</button>'
       '<p class="fine">日付・便名・区間が入った状態で記録が開きます</p></div>') % (ic('plane'), ic('plus'))
page('k3-sheet.html', '共通 便を押したとき', shp, 'B', 'now')

# ───── 共通：データが少ない空港 ─────
oit = (top('B', '共通') + head('OIT', '大分', '14:22') + summary(False) +
       '<div class="tools"><div class="dir"><button aria-pressed="true">出発</button><button aria-pressed="false">到着</button></div>'
       '<span class="chip">遅れあり</span><span class="srch">%s便名・行き先</span></div>' % ic('search') +
       '<section class="card hr"><div class="hh"><b>14時台</b><small>出発 2便</small></div>'
       + fl('14:05', 'NH 794', '羽田', 'B767-300・ANA', '定刻', 'nh')
       + fl('14:40', 'JL 668', '羽田', 'B737-800・JAL', '定刻', 'jl') + '</section>'
       '<section class="card hr"><div class="hh"><b>15時台</b><small>出発 1便</small></div>'
       + fl('15:30', 'NH 1690', '伊丹', 'DHC8-400・ANA', '定刻', 'nh') + '</section>'
       '<p class="note">滑走路・3D と特別塗装機は、出せる空港だけピルが出る</p>')
page('k4-small.html', '共通 データが少ない空港', oit, 'B', 'now')

# ───── 共通：空港を選ぶ ─────
pick = (top('B', '共通') + head() + summary() + seg('今日の便') + flights() +
        '<div class="dim"></div><div class="sh"><div class="grab"></div><h2>空港を選ぶ</h2>'
        '<div class="shh">ピン止め</div>'
        '<div class="pk"><span class="cd">HND</span><div><b>羽田</b><small>いま見ている</small></div><span class="r">%s</span></div>'
        '<div class="pk"><span class="cd">OIT</span><div><b>大分</b><small>ピン止め</small></div><span class="r">%s</span></div>'
        '<div class="shh">いまいる・次の便</div>'
        '<div class="pk"><span class="cd">NRT</span><div><b>成田</b><small>いまいる空港（3 km）</small></div></div>'
        '<div class="pk"><span class="cd">CTS</span><div><b>新千歳</b><small>次の便の行き先（12/3）</small></div></div>'
        '<div class="srch" style="margin-top:14px">%s空港の名前・コード</div></div>') % (ic('pin'), ic('pin'), ic('search'))
page('k5-pick.html', '共通 空港を選ぶ', pick, 'B', 'now')
