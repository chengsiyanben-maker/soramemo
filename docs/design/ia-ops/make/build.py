# -*- coding: utf-8 -*-
# タブの組み替えと「いまの空港」の画面案を作る（外部の読み込みなし・1画面1ファイル）
# 使い方：python3 make/build.py → docs/design/ia-ops/*.html
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE + '/src')
from icons import P

P.update({
 'live': '<circle cx="12" cy="12" r="2.2"/><path d="M7.8 7.8a6 6 0 0 0 0 8.4M16.2 7.8a6 6 0 0 1 0 8.4M5 5a10 10 0 0 0 0 14M19 5a10 10 0 0 1 0 14"/>',
 'note': '<rect x="5" y="3.5" width="14" height="17" rx="2.5"/><path d="M9 8h6M9 12h6M9 16h3.5"/>',
 'down': '<path d="M6 9l6 6 6-6"/>',
 'search': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8h.01"/>',
 'cube': '<path d="M12 3.5l7.5 4.2v8.6L12 20.5l-7.5-4.2V7.7zM12 12l7.5-4.3M12 12L4.5 7.7M12 12v8.5"/>',
 'loc': '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
 'plus': '<path d="M12 5v14M5 12h14"/>',
 'x': '<path d="M6 6l12 12M18 6L6 18"/>',
 'star': '<path d="M12 4l2.4 5 5.4.7-4 3.8 1 5.4L12 16.3 7.2 18.9l1-5.4-4-3.8 5.4-.7z"/>',
})
def ic(n, cls='ic'):
    return '<svg class="%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, P[n])

BASE = open(HERE + '/src/base.css', encoding='utf-8').read()
CSS = BASE + r'''
body{padding:0 16px 132px}
.frame{position:relative;min-height:100vh}
/* 頭：空港のピル＋最後に読んだ時刻と ↻（スクロールしても残る） */
.head{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:10px;padding:14px 0 12px;background:var(--bg)}
.ap{display:inline-flex;white-space:nowrap;flex:none;align-items:center;gap:8px;min-height:48px;padding:0 14px 0 6px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-weight:800;font-size:18px;color:var(--strong)}
.ap .code{display:inline-flex;align-items:center;justify-content:center;height:30px;padding:0 9px;border-radius:999px;background:var(--hero);color:#fff;font-size:13px;letter-spacing:.06em}
.ap .ic{width:18px;height:18px;color:var(--sub)}
.ap .here{width:16px;height:16px;color:var(--acc);margin-left:-2px}
.sp{flex:1}
.rf{display:inline-flex;white-space:nowrap;flex:none;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:700;color:var(--sub)}
.rf b{font-size:15px;color:var(--strong);font-variant-numeric:tabular-nums}
.rf .ic{width:18px;height:18px;color:var(--strong)}
.iq{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);color:var(--sub)}
.iq .ic{width:20px;height:20px}
.mp{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.mp .ic{width:18px;height:18px}
.brand{display:flex;align-items:center;justify-content:space-between;padding:16px 0 2px}
.brand b{font-size:21px;font-weight:800;color:var(--strong);letter-spacing:.04em}
/* 要約カード：3つの大きな数字 */
.sum{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:18px 14px 16px}
.sum.two{grid-template-columns:repeat(2,1fr)}
.sum .k{font-size:12px;font-weight:700;color:var(--mute)}
.sum .v{display:block;font-size:26px;line-height:1.25;margin-top:6px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;white-space:nowrap}
.sum .v small{font-size:13px;color:var(--mute);font-weight:700;margin-left:2px}
.sum .v.late{color:#B45309}
.sum .s{display:block;font-size:12px;color:var(--mute);margin-top:4px;line-height:1.45}
.sum > div{min-width:0}
.sum > a{display:block;min-width:0;border-radius:14px;margin:-6px;padding:6px;color:inherit;text-decoration:none}
.sum > a .k::after{content:" ›";color:var(--mute)}
/* ピルのタブ */
.seg{display:flex;gap:4px;padding:4px;margin:18px 0 14px;border-radius:999px;background:var(--track)}
.seg button{flex:1;min-height:44px;border-radius:999px;font-size:14px;font-weight:800;color:var(--sub);white-space:nowrap}
.seg button[aria-selected=true]{background:var(--card);color:var(--strong);box-shadow:0 1px 3px rgba(17,24,39,.12)}
.chips{display:flex;gap:8px;overflow-x:auto;margin:0 -16px 6px;padding:2px 16px 8px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:none;display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:700;color:var(--ink);white-space:nowrap}
.chip.on{background:var(--strong);color:#fff;box-shadow:none}
.chip .n{font-size:12px;color:var(--mute);margin-left:5px;font-weight:700}
.chip.on .n{color:#CBD5E1}
.dir{display:inline-flex;padding:3px;border-radius:999px;background:var(--track);flex:none}
.dir span{display:inline-flex;align-items:center;min-height:38px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.dir span.on{background:var(--card);color:var(--strong);box-shadow:0 1px 3px rgba(17,24,39,.12)}
.dirwrap{flex:none;display:flex;align-items:center;min-height:44px}
/* 1時間ごとのカード：線でなく余白で区切る */
.hr{margin-top:14px;padding:8px 16px 6px}
.hr h3{display:flex;align-items:baseline;gap:8px;font-size:15px;font-weight:800;color:var(--strong);padding:6px 0 2px}
.hr h3 small{font-size:12px;color:var(--mute);font-weight:700}
.fl{display:grid;grid-template-columns:62px 1fr auto;align-items:center;gap:10px;min-height:60px;padding:9px 0}
.fl + .fl{margin-top:4px}
.fl .t{font-size:21px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;line-height:1.1}
.fl .t s{display:block;font-size:12px;color:var(--mute);font-weight:700;text-decoration:line-through;margin-top:2px}
.fl .t.late{color:#B45309}
.fl .m{min-width:0}
.fl .m b{display:flex;align-items:center;gap:6px;font-size:15px;font-weight:800;color:var(--strong);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fl .m span{display:block;font-size:12px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cc{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:20px;padding:0 6px;border-radius:999px;font-size:11.5px;font-weight:800;letter-spacing:.04em;background:var(--pill);color:var(--ink)}
.cc.jl{background:rgba(200,16,46,.08);color:#9F1239}
.cc.nh{background:rgba(28,79,160,.08);color:#1C4FA0}
.st{font-size:12px;font-weight:800;color:var(--sub);text-align:right;white-space:nowrap}
.st.late{color:#B45309}
.st.cx{color:#B91C1C}
.st.gone{color:var(--mute);font-weight:700}
.sp-star{width:14px;height:14px;color:#B45309;fill:#FDE68A;stroke:#B45309}
.src{font-size:12px;color:var(--sub);margin:16px 4px 0;line-height:1.6}
/* 下のタブ帯 */
.navwrap{position:fixed;left:0;right:0;bottom:14px;z-index:8;display:flex;justify-content:center;padding:0 14px}
.navwrap .tabs{width:100%;max-width:402px}
.tabs.four{grid-template-columns:repeat(4,1fr)}
.tabs button{white-space:nowrap}
/* 滑走路・3D */
.rw{background:var(--hero);color:#fff;border-radius:22px;padding:18px 18px 16px;box-shadow:var(--shadow)}
.rw .k{font-size:13px;font-weight:700;color:#CBD5E1}
.rw .big{font-size:40px;font-weight:800;line-height:1.15;margin-top:4px}
.rw .row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.rw .tag{display:inline-flex;align-items:center;gap:6px;min-height:34px;padding:0 12px;border-radius:999px;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.7);font-weight:800;font-size:14px}
.rw .tag small{font-size:12px;color:#CBD5E1;font-weight:700}
.chart{position:relative;height:200px;border-radius:22px;overflow:hidden;background:#E6EDF5;box-shadow:var(--shadow);margin-top:14px}
.chart svg{position:absolute;inset:0;width:100%;height:100%}
.chart .lb{position:absolute;left:14px;top:12px;font-size:13px;font-weight:800;color:var(--strong);background:rgba(255,255,255,.9);border-radius:999px;padding:4px 12px}
.d3{display:flex;gap:14px;align-items:center;margin-top:14px}
.d3 .pv{flex:none;width:96px;height:96px;border-radius:16px;background:linear-gradient(160deg,#DCE6F1,#B8C9DC);position:relative;overflow:hidden}
.d3 .pv svg{position:absolute;inset:0;width:100%;height:100%}
.d3 h4{font-size:16px;font-weight:800;color:var(--strong)}
.d3 p{font-size:12px;color:var(--mute);margin:2px 0 10px;line-height:1.5}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.mini{padding:14px 16px;min-height:104px}
.mini .k{font-size:13px;font-weight:800;color:var(--strong)}
.mini .v{font-size:26px;font-weight:800;color:var(--strong);margin-top:8px;font-variant-numeric:tabular-nums}
.mini .v small{font-size:12px;color:var(--mute);font-weight:700;margin-left:2px}
.mini .s{font-size:12px;color:var(--mute)}
/* 特別塗装機 */
.lv{display:flex;gap:14px;padding:14px 16px;margin-top:12px}
.lv .sw2{flex:none;width:58px;height:58px;border-radius:16px;position:relative;overflow:hidden}
.lv .sw2 svg{position:absolute;inset:0;width:100%;height:100%}
.lv .b{min-width:0;flex:1}
.lv h4{font-size:16px;font-weight:800;color:var(--strong);line-height:1.35}
.lv .r{font-size:13px;color:var(--sub);font-weight:700;margin-top:2px;font-variant-numeric:tabular-nums}
.lv .r small{font-size:12px;color:var(--mute);font-weight:600}
.state{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:800;margin-top:8px;background:var(--pill);color:var(--ink)}
.state.now{background:rgba(21,128,61,.10);color:#166534}
.state.pre{background:transparent;box-shadow:inset 0 0 0 1.5px #9CA3AF;color:var(--sub);border-style:dashed}
.got{display:inline-flex;align-items:center;gap:4px;font-size:12px;color:var(--mute);font-weight:700;margin-left:8px}
.got .ic{width:14px;height:14px;stroke:var(--ok);stroke-width:2.4}
/* 記録 */
.rtop{display:flex;align-items:center;gap:10px;padding:16px 0 4px}
.rtop h1{flex:1}
.hero{background:var(--hero);color:#fff;border-radius:22px;padding:18px;margin-top:12px}
.hero .k{font-size:13px;color:#CBD5E1;font-weight:700}
.hero .nums{display:flex;gap:22px;margin-top:6px}
.hero .nums b{font-size:32px;font-weight:800;font-variant-numeric:tabular-nums}
.hero .nums small{font-size:13px;color:#CBD5E1;font-weight:700;margin-left:3px}
.mh{display:flex;align-items:baseline;gap:8px;margin:22px 4px 8px;font-size:15px;font-weight:800;color:var(--strong)}
.mh small{font-size:12px;color:var(--mute);font-weight:700}
.lg{display:grid;grid-template-columns:44px 1fr auto;gap:12px;align-items:center;min-height:62px;padding:8px 0}
.lg .d{font-size:20px;font-weight:800;color:var(--strong);text-align:center;line-height:1.1}
.lg .d small{display:block;font-size:12px;color:var(--mute);font-weight:700}
.lg b{font-size:16px;font-weight:800;color:var(--strong)}
.lg > div > span{display:block;font-size:12px;color:var(--mute)}
.lg .km{font-size:15px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.lg .km small{font-size:12px;color:var(--mute);font-weight:700;margin-left:2px}
.optnote{display:flex;gap:8px;align-items:flex-start;font-size:12px;color:var(--sub);margin:4px 4px 0;line-height:1.55}
/* シート */
.scrim{opacity:1;pointer-events:auto;position:fixed;z-index:20}
.sheet{position:fixed;z-index:21;transform:none;max-width:430px;margin:0 auto;padding:10px 20px 34px}
.sheet h2{font-size:20px}
.kv{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:14px 0 6px}
.kv .k{font-size:12px;color:var(--mute);font-weight:700}
.kv .v{display:block;font-size:22px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.kv .v small{font-size:12px;color:var(--mute);font-weight:700;margin-left:2px}
.bigbtn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;min-height:54px;border-radius:999px;background:var(--strong);color:#fff;font-size:16px;font-weight:800;margin-top:14px}
.bigbtn .ic{width:20px;height:20px}
.subbtn{display:flex;align-items:center;justify-content:center;width:100%;min-height:48px;border-radius:999px;background:var(--pill);color:var(--strong);font-size:15px;font-weight:800;margin-top:10px}
.fine{font-size:12px;color:var(--mute);margin-top:12px;line-height:1.6}
.srch{display:flex;align-items:center;gap:8px;min-height:48px;padding:0 16px;border-radius:999px;background:var(--track);color:var(--mute);font-size:15px;font-weight:600;margin:6px 0 12px}
.srch .ic{width:18px;height:18px}
.grp{font-size:12px;font-weight:800;color:var(--mute);margin:14px 2px 4px;letter-spacing:.04em}
.aprow{display:flex;align-items:center;gap:12px;min-height:56px}
.aprow .code{display:inline-flex;align-items:center;justify-content:center;width:52px;height:32px;border-radius:999px;background:var(--pill);font-weight:800;font-size:13px;color:var(--strong);letter-spacing:.06em}
.aprow b{flex:1;font-size:16px;font-weight:800;color:var(--strong)}
.aprow span{font-size:12px;color:var(--mute);font-weight:700}
.aprow .ic{width:18px;height:18px;color:var(--mute)}
.only{margin-top:16px;padding:14px 16px;font-size:13px;color:var(--sub);line-height:1.6}
.only b{color:var(--strong)}
.note{position:relative;margin:14px 0 0;padding:10px 14px;border-radius:14px;background:var(--pin-wash);font-size:12px;color:var(--sub);line-height:1.6}
'''

def tabbar(plan, cur):
    if plan == 'A':
        items = [('home','ホーム','home'),('live','いまの空港','live'),('rec','記録','note'),('me','マイページ','user')]
        cls = 'tabs four'
    else:
        items = [('home','ホーム','home'),('book','図鑑','book'),('log','フライト','plane'),('live','いまの空港','live'),('sg','修行','stairs')]
        cls = 'tabs'
    out = ['<div class="navwrap"><nav class="%s" aria-label="下のタブ">' % cls]
    n = len(items)
    pos = 0
    for i,(k,lb,icn) in enumerate(items):
        if k == cur: pos = i
        out.append('<button type="button"%s>%s%s</button>' % (' aria-current="page"' if k == cur else '', ic(icn), lb))
    # 点の位置：枠の左の余白6px＋1つ分の真ん中
    out.append('<i class="dot" aria-hidden="true" style="left:calc(6px + (100%% - 12px) * %f - 2.5px)"></i></nav></div>' % ((pos + .5) / n))
    return ''.join(out)

def head(code='HND', name='羽田', here=True, t='14:22', brand=False):
    h = ''
    if brand:
        h += '<div class="brand"><b>そらメモ</b><button class="mp">%sマイページ</button></div>' % ic('user')
    h += ('<div class="head"><button class="ap" aria-label="空港を選ぶ"><span class="code">%s</span>%s%s%s</button>'
          '<span class="sp"></span><button class="rf" aria-label="最後に読んだ時刻・押すと読み直す"><b>%s</b><span>時点</span>%s</button>'
          '<button class="iq" aria-label="出典と注意">%s</button></div>') % (
          code, (ic('loc','ic here') if here else ''), name, ic('down'), t, ic('retry'), ic('info'))
    return h

def summary():
    return ('<section class="card sum" aria-label="この空港のいま">'
            '<div><span class="k">使っている滑走路</span><span class="v">34R<small>ほか2</small></span><span class="s">離陸 05・34R<br>着陸 34L・34R</span></div>'
            '<div><span class="k">平均の遅れ</span><span class="v late">+12<small>分</small></span><span class="s">出発・この1時間</span></div>'
            '<a href="#" aria-label="特別塗装機のタブへ"><span class="k">特別塗装機</span><span class="v">4<small>機</small></span><span class="s">今日来る<br>（予想を含む）</span></a>'
            '</section>')

def seg(sel, items=('今日の便','滑走路・3D','特別塗装機')):
    return '<div class="seg" role="tablist">' + ''.join('<button role="tab" aria-selected="%s">%s</button>' % ('true' if x == sel else 'false', x) for x in items) + '</div>'

def fl(t, code, cls, no, dest, ac, st, stcls='', late=None, star=False):
    tt = ('<div class="t late">%s<s>%s</s></div>' % (late, t)) if late else '<div class="t">%s</div>' % t
    return ('<div class="fl">%s<div class="m"><b><span class="cc %s">%s</span>%s%s</b><span>%s・%s</span></div>'
            '<div class="st %s">%s</div></div>') % (tt, cls, code, no, (ic('star','sp-star') if star else ''), dest, ac, stcls, st)

def flights():
    h = ('<div class="chips"><span class="dirwrap"><span class="dir"><span class="on">出発</span><span>到着</span></span></span>'
         '<span class="chip on">すべて<span class="n">212</span></span><span class="chip">遅れあり<span class="n">31</span></span>'
         '<span class="chip">第1<span class="n">96</span></span><span class="chip">第2<span class="n">88</span></span><span class="chip">第3<span class="n">28</span></span></div>')
    h += '<section class="card hr"><h3>14時台<small>出発 18便・遅れ 4便</small></h3>'
    h += fl('14:30', 'JL', 'jl', '513', '新千歳', 'A350-900', '出発済み', 'gone')
    h += fl('14:35', 'NH', 'nh', '61', '新千歳', '787-9', '遅れ +15', 'late', late='14:50', star=True)
    h += fl('14:40', 'BC', '', '11', '神戸', '737-800', '定刻')
    h += fl('14:45', 'JL', 'jl', '323', '福岡', '767-300ER', '定刻')
    h += fl('14:55', 'NH', 'nh', '993', '那覇', '777-200', '欠航', 'cx')
    h += '</section>'
    h += '<section class="card hr"><h3>15時台<small>出発 21便</small></h3>'
    h += fl('15:00', 'JL', 'jl', '115', '伊丹', '787-8', '定刻')
    h += fl('15:00', '6J', '', '29', '宮崎', '737-800', '定刻')
    h += fl('15:05', 'NH', 'nh', '247', '福岡', 'A321neo', '定刻')
    h += '</section>'
    h += '<p class="src">出典 ODPT（運航情報 14時21分・時刻表 11月25日時点）。ODPT にない会社（BC・6J など）は adsb.lol（ODbL）からの推定です。遅れは航空会社の発表ではありません。</p>'
    return h

def page(title, body, plan='A', cur='live', extra=''):
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s</style></head><body><div class="frame">%s</div>%s%s</body></html>') % (title, CSS, body, tabbar(plan, cur) if plan else '', extra)

SCREENS = {}

# ── 案A：いまの空港（今日の便）
SCREENS['A1'] = ('案A いまの空港・今日の便', page('案A いまの空港', head() + summary() + seg('今日の便') + flights(), 'A', 'live'))

# ── 案B：タブは今のまま・運用の名前を「いまの空港」に
SCREENS['B1'] = ('案B いまの空港・今日の便', page('案B いまの空港', head(brand=True) + summary() + seg('今日の便') + flights(), 'B', 'live'))

# ── 案A：記録（フライト｜図鑑｜修行）
rec = ('<div class="rtop"><h1>記録</h1><button class="iq" aria-label="見方を変える">%s</button></div>' % ic('pencil'))
rec += seg('フライト', ('フライト','図鑑','修行'))
rec += ('<section class="hero"><span class="k">これまで（車などは別）</span><div class="nums"><span><b>30</b><small>便</small></span>'
        '<span><b>24,017</b><small>km</small></span><span><b>16</b><small>空港</small></span></div></section>')
rec += '<div class="mh">2026年11月<small>3便・2,415km</small></div><section class="card" style="padding:4px 16px">'
rec += ('<div class="lg"><div class="d">22<small>日</small></div><div><b>羽田 → 新千歳</b><span><span class="cc jl">JL</span> 513・A350-900</span></div><div class="km">894<small>km</small></div></div>'
        '<div class="lg"><div class="d">15<small>日</small></div><div><b>伊丹 → 羽田</b><span><span class="cc nh">NH</span> 30・787-9</span></div><div class="km">514<small>km</small></div></div>'
        '<div class="lg"><div class="d">3<small>日</small></div><div><b>羽田 → 福岡</b><span><span class="cc jl">JL</span> 307・767-300ER</span></div><div class="km">1,007<small>km</small></div></div>')
rec += '</section><div class="mh">2026年10月<small>5便・4,102km</small></div><section class="card" style="padding:4px 16px">'
rec += ('<div class="lg"><div class="d">28<small>日</small></div><div><b>那覇 → 羽田</b><span><span class="cc nh">NH</span> 994・777-200</span></div><div class="km">1,687<small>km</small></div></div>'
        '<div class="lg"><div class="d">26<small>日</small></div><div><b>羽田 → 那覇</b><span><span class="cc nh">NH</span> 993・777-200</span></div><div class="km">1,687<small>km</small></div></div>')
rec += '</section>'
rec += '<p class="optnote">修行のピルは、表示の編集で修行を OFF にした人には出ません（ピルが2つになる）。</p>'
SCREENS['A2'] = ('案A 記録・フライト', page('案A 記録', rec, 'A', 'rec'))

# ── 共通：滑走路・3D
rwy = head() + summary() + seg('滑走路・3D')
rwy += ('<section class="rw"><span class="k">滑走路</span><div class="big">北風</div><div class="row">'
        '<span class="tag">34L<small>着陸</small></span><span class="tag">34R<small>離着陸</small></span><span class="tag">05<small>離陸</small></span></div></section>')
rwy += ('<div class="chart"><span class="lb">地図</span><svg viewBox="0 0 358 200" preserveAspectRatio="xMidYMid slice">'
        '<path d="M0 0h358v62c-60 10-110 0-180 14S40 70 0 80z" fill="#EEF0E6"/>'
        '<circle cx="180" cy="112" r="74" fill="none" stroke="#94A3B8" stroke-dasharray="4 5"/>'
        '<g stroke="#334155" stroke-width="7" stroke-linecap="round"><path d="M160 70l18 82"/><path d="M186 64l18 82"/><path d="M160 158l66-26"/></g>'
        '<g fill="none" stroke="#2563EB" stroke-width="2.4" stroke-linecap="round"><path d="M172 196l-6-30"/><path d="M164 176l2-10 7 8"/>'
        '<path d="M232 128l60-22"/><path d="M280 104l12 2-8 9"/></g></svg></div>')
rwy += ('<section class="card d3"><div class="pv"><svg viewBox="0 0 96 96"><path d="M8 64l46-24 34 16-46 26z" fill="#F8FAFC"/>'
        '<g stroke="#475569" stroke-width="5" stroke-linecap="round"><path d="M24 64l36-18"/><path d="M34 70l36-18"/></g>'
        '<rect x="58" y="26" width="5" height="18" fill="#64748B"/><rect x="54" y="20" width="13" height="8" rx="2" fill="#475569"/></svg></div>'
        '<div><h4>3D で空港を見る</h4><p>押すと読み込みます（約0.7MB）<br>自由・追う・立つ・飛ぶ</p><button class="pill dark" style="min-height:44px">%s開く</button></div></section>' % ic('cube'))
rwy += ('<div class="grid2"><section class="card mini"><div class="k">空の道すじ</div><div class="v">412<small>機</small></div><div class="s">今日・羽田の上</div></section>'
        '<section class="card mini"><div class="k">撮る人</div><div class="v">34R<small>着陸</small></div><div class="s">次の特別塗装機 15:10</div></section></div>')
rwy += '<p class="src">3D は押したときだけ開きます。開くと今の4つの見方（自由・追う・立つ・飛ぶ）。</p>'
SCREENS['C1'] = ('共通 滑走路・3D', page('滑走路・3D', rwy, 'A', 'live'))

# ── 共通：特別塗装機
def livery(c1, c2, name, reg, st, stcls, sub, got=False):
    return ('<section class="card lv"><div class="sw2"><svg viewBox="0 0 58 58"><rect width="58" height="58" fill="%s"/>'
            '<path d="M0 40c18-8 34-6 58-16v34H0z" fill="%s"/><path d="M10 30l30-6 8 2-30 8z" fill="#fff" opacity=".9"/></svg></div>'
            '<div class="b"><h4>%s</h4><div class="r">%s<small>　%s</small></div><span class="state %s">%s</span>%s</div></section>') % (
            c1, c2, name, reg, sub, stcls, st, ('<span class="got">%s図鑑にあり</span>' % ic('check')) if got else '')
lv = head() + summary() + seg('特別塗装機')
lv += livery('#E0F2FE', '#0EA5E9', '空色の特別塗装機（例）', 'JA0xxJ', '駐機中', 'now', 'JL 513 で着いた・スポット 12', got=True)
lv += livery('#FCE7F3', '#DB2777', '花の特別塗装機（例）', 'JA8xxA', '15:10 着く予定', '', 'NH 248（福岡から）')
lv += livery('#ECFCCB', '#65A30D', '森の特別塗装機（例）', 'JA7xxJ', '17:40 ごろ（予想）', 'pre', 'いつもの回り方から')
lv += livery('#FEF3C7', '#D97706', '星の特別塗装機（例）', 'JA6xxA', '出発済み 9:05', '', 'NH 461（那覇へ）', got=True)
lv += ('<div class="note">図鑑には、乗った・見た記録から入ります（このページから押して入れることはできません）。'
       '「予想」は保証しません。</div>')
SCREENS['C2'] = ('共通 特別塗装機', page('特別塗装機', lv, 'A', 'live'))

# ── 共通：便を押したシート
sh = head() + summary() + seg('今日の便') + flights()
sheet = ('<div class="scrim"></div><div class="sheet" role="dialog" aria-label="便のくわしく"><div class="grab"></div>'
         '<div style="display:flex;align-items:center;gap:8px"><span class="cc nh" style="height:24px;font-size:12px">NH</span><h2>61　羽田 → 新千歳</h2></div>'
         '<div class="kv"><div><span class="k">出発の見込み</span><span class="v" style="color:#B45309">14:50</span></div>'
         '<div><span class="k">定刻</span><span class="v">14:35</span></div><div><span class="k">機材</span><span class="v" style="font-size:18px">787-9</span></div></div>'
         '<div style="font-size:13px;color:var(--sub);font-weight:700">JA8xxA・特別塗装機（予想ではなく今日の割り当て）</div>'
         '<button class="bigbtn">%sこの便をフライト記録に追加</button>'
         '<button class="subbtn">この便に乗る（遅れを知らせる）</button>'
         '<p class="fine">出発の見込みは航空会社の運航情報（14時21分）。記録した便はフライトと図鑑に入り、修行の計算にも使います。</p></div>') % ic('plus')
SCREENS['C3'] = ('共通 便を押したとき', page('便のくわしく', sh, 'A', 'live', sheet))

# ── 共通：データが少ない空港（山形）
yg = head('GAJ', '山形', here=False, t='14:20')
yg += ('<section class="card sum two" aria-label="この空港のいま">'
       '<div><span class="k">今日の便</span><span class="v">8<small>便</small></span><span class="s">出発4・到着4</span></div>'
       '<div><span class="k">平均の遅れ</span><span class="v">定刻</span><span class="s">遅れた便 0</span></div></section>')
yg += ('<div class="chips" style="margin-top:16px"><span class="dirwrap"><span class="dir"><span class="on">出発</span><span>到着</span></span></span>'
       '<span class="chip on">すべて<span class="n">4</span></span></div>')
yg += '<section class="card hr"><h3>14時台<small>出発 1便</small></h3>' + fl('14:55', 'JL', 'jl', '178', '伊丹', 'E170', '定刻') + '</section>'
yg += '<section class="card hr"><h3>18時台<small>出発 1便</small></h3>' + fl('18:50', 'JL', 'jl', '182', '伊丹', 'E170', '定刻') + '</section>'
yg += '<section class="card hr"><h3>19時台<small>出発 1便</small></h3>' + fl('19:40', 'JL', 'jl', '186', '羽田', 'E170', '定刻') + '</section>'
yg += ('<p class="only">この空港は<b>今日の便</b>だけ出せます。滑走路・3D・特別塗装機は、データがそろった空港から出します（タブのピルは1つのとき出しません）。</p>')
yg += '<p class="src">出典 ODPT（運航情報 14時19分・時刻表 11月25日時点）。</p>'
SCREENS['C4'] = ('共通 データが少ない空港（山形）', page('山形', yg, 'A', 'live'))

# ── 共通：空港を選ぶシート
ss = head() + summary() + seg('今日の便') + flights()
sheet2 = ('<div class="scrim"></div><div class="sheet" role="dialog" aria-label="空港を選ぶ"><div class="grab"></div><h2>空港を選ぶ</h2>'
          '<div class="srch">%s名前・コード・読み</div>'
          '<div class="grp">いまいる空港</div><div class="aprow"><span class="code">HND</span><b>羽田</b><span>判定の中</span>%s</div>'
          '<div class="grp">ピン止め</div>'
          '<div class="aprow"><span class="code">ITM</span><b>伊丹</b><span>遅れ +8分</span>%s</div>'
          '<div class="aprow"><span class="code">CTS</span><b>新千歳</b><span>定刻</span>%s</div>'
          '<div class="grp">次のフライトの空港</div><div class="aprow"><span class="code">FUK</span><b>福岡</b><span>12月2日</span>%s</div>'
          '</div>') % (ic('search'), ic('loc'), ic('pin'), ic('pin'), ic('plane'))
SCREENS['C5'] = ('共通 空港を選ぶ', page('空港を選ぶ', ss, 'A', 'live', sheet2))

def write():
    for k, (t, html) in SCREENS.items():
        open('%s/%s.html' % (OUT, k), 'w', encoding='utf-8').write(html)
    print('書いた：', ', '.join(SCREENS))

if __name__ == '__main__':
    write()
