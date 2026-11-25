# -*- coding: utf-8 -*-
# ホームの「ふだん」と「空港にいるとき」の画面案（外部の読み込みなし・1画面1ファイル）
# 使い方：python3 make/build.py [A|B]   … 下のタブ帯（A＝4つ、B＝今の5つ。はじめは B）
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE + '/src')
from icons import P
TABS = (sys.argv[1] if len(sys.argv) > 1 else 'B').upper()

P.update({
 'live': '<circle cx="12" cy="12" r="2.2"/><path d="M7.8 7.8a6 6 0 0 0 0 8.4M16.2 7.8a6 6 0 0 1 0 8.4M5 5a10 10 0 0 0 0 14M19 5a10 10 0 0 1 0 14"/>',
 'note': '<rect x="5" y="3.5" width="14" height="17" rx="2.5"/><path d="M9 8h6M9 12h6M9 16h3.5"/>',
 'loc': '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
 'plus': '<path d="M12 5v14M5 12h14"/>',
 'target': '<circle cx="12" cy="12" r="7"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/><circle cx="12" cy="12" r="1.6"/>',
 'cloud': '<path d="M7 18h10a4 4 0 0 0 .5-8 6 6 0 0 0-11.4 1.5A3.3 3.3 0 0 0 7 18zM12 11v5M9.8 13.8L12 16l2.2-2.2"/>',
 'arrow': '<path d="M4 12h15M13 6l6 6-6 6"/>',
 'map': '<path d="M9 4.5l-5 2v13l5-2 6 2 5-2v-13l-5 2zM9 4.5v13M15 6.5v13"/>',
})
def ic(n, cls='ic'):
    return '<svg class="%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, P[n])

CSS = open(HERE + '/src/base.css', encoding='utf-8').read() + r'''
:root{--stub:#E9C46A;--stub-text:#111827;--stub-sub:#3A2E0B;--rw:#7A2E6E;--land:#F4F2EA;--sea:#DCE6EF;--coast:#C9D3DC;--gl:#B7C2CD}
:root[data-night=on]{--stub:#FBBF24;--rw:#4ADE80;--land:#151A21;--sea:#0C1117;--coast:#2A323C;--gl:#3A4552}
html,body{height:100%;overflow:hidden}
body{padding:0;max-width:none}
.scr{position:relative;height:100vh;overflow:hidden;max-width:430px;margin:0 auto}
.map{position:absolute;inset:0;background:var(--sea)}
.map svg{position:absolute;inset:0;width:100%;height:100%}
.float{position:absolute;top:14px;left:16px;right:16px;display:flex;gap:10px;align-items:center;z-index:3}
.fp{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong);white-space:nowrap}
.fp b{font-size:17px;font-variant-numeric:tabular-nums}
.fp small{font-size:12px;color:var(--mute);font-weight:700}
.fp .ic{width:18px;height:18px}
.fp.in{background:var(--hero);color:#fff;box-shadow:none}
:root[data-night=on] .fp.in{background:transparent;box-shadow:inset 0 0 0 1.5px var(--ok);color:var(--ok)}
.fp.in .dot{width:8px;height:8px;border-radius:50%;background:#4ADE80}
.circ{width:44px;justify-content:center;padding:0}
.sp{flex:1}
.ml{font-size:13px;font-weight:800;fill:var(--strong);paint-order:stroke;stroke:var(--land);stroke-width:4px}
.ml.s{font-size:12px;font-weight:700;fill:var(--sub)}
/* シート：灰の地に白いカード、3段 */
.sheet{position:absolute;left:0;right:0;bottom:0;z-index:4;background:var(--bg);border-radius:26px 26px 0 0;box-shadow:0 -10px 30px -12px rgba(17,24,39,.28);padding:10px 16px 0;overflow:hidden;transform:none}
:root[data-night=on] .sheet{box-shadow:0 -10px 30px -10px rgba(0,0,0,.8),inset 0 1px 0 rgba(255,255,255,.06)}
.sheet .grab{width:40px;height:5px;border-radius:3px;background:#C7CDD6;margin:0 auto 12px}
:root[data-night=on] .sheet .grab{background:#3A414C}
.sheet.s{height:236px}.sheet.m{height:58%}.sheet.l{height:88%}
.c{background:var(--card);border-radius:20px;box-shadow:var(--shadow);padding:14px 16px;margin-bottom:12px}
.k{font-size:12px;font-weight:700;color:var(--mute)}
.row{display:flex;align-items:center;gap:10px}
.big{font-size:34px;font-weight:800;color:var(--strong);line-height:1.1;font-variant-numeric:tabular-nums}
.big small{font-size:14px;color:var(--mute);font-weight:700;margin:0 2px}
.cc{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:20px;padding:0 6px;border-radius:999px;font-size:11.5px;font-weight:800;letter-spacing:.04em;background:var(--pill);color:var(--ink)}
.cc.jl{background:rgba(200,16,46,.08);color:#9F1239}
:root[data-night=on] .cc.jl,:root[data-night=on] .cc.nh{background:var(--pill);color:var(--ink)}
.fn{font-size:14px;font-weight:800;color:var(--strong)}
.fn span{font-size:12px;color:var(--mute);font-weight:700;margin-left:4px}
.rt{font-size:17px;font-weight:800;color:var(--strong);text-align:right;line-height:1.3}
.rt small{display:block;font-size:12px;color:var(--mute);font-weight:700}
.sm{display:inline-flex;align-items:center;justify-content:center;gap:4px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--strong);white-space:nowrap}
.sm .ic{width:16px;height:16px}
.quiet{font-size:13px;color:var(--sub);margin-top:2px}
.bar2{height:8px;border-radius:4px;background:var(--bar);overflow:hidden;margin-top:8px}
.bar2 i{display:block;height:100%;border-radius:4px;background:var(--hero)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}
.two .sm{width:100%;min-height:48px;white-space:normal;line-height:1.3;text-align:center}
.two .sm.dark{background:var(--strong);color:#fff}
:root[data-night=on] .two .sm.dark{background:transparent;color:#fff;box-shadow:inset 0 0 0 1.5px #fff}
/* 空港にいるとき */
.apn{display:flex;align-items:baseline;gap:10px;padding:0 4px 10px}
.apn h1{font-size:26px}
.apn span{font-size:13px;color:var(--sub);font-weight:700}
.apn .first{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;background:var(--hero);color:#fff;font-size:12px;font-weight:800}
.ck{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:64px;border-radius:999px;background:var(--stub);color:var(--stub-text);font-size:18px;font-weight:800;box-shadow:0 10px 24px -10px rgba(183,134,42,.7);margin-bottom:12px;position:relative;overflow:hidden}
.ck .ic{width:22px;height:22px}
.ck small{font-size:12px;font-weight:700;color:var(--stub-sub)}
.ck .perf{position:absolute;right:58px;top:10px;bottom:10px;border-left:2px dashed rgba(15,27,45,.3)}
.ck .tear{position:absolute;right:0;top:0;bottom:0;width:58px;display:flex;align-items:center;justify-content:center}
.ck.hold{background:var(--card);color:var(--strong);box-shadow:var(--shadow),inset 0 0 0 2px #B45309}
.ck.hold small{color:#92400E}
:root[data-night=on] .ck.hold{box-shadow:inset 0 0 0 2px var(--amber)}
:root[data-night=on] .ck.hold small{color:var(--amber)}
.ck.done{background:var(--pill);color:var(--sub);box-shadow:none;min-height:52px;font-size:16px}
.ck.done .ic{stroke:var(--ok);stroke-width:2.4}
.ckrow{display:grid;grid-template-columns:1fr auto;gap:10px;margin-bottom:12px}
.ckrow .ck{margin:0}
.ckrow .sm{min-height:52px;background:var(--strong);color:#fff;padding:0 18px}
:root[data-night=on] .ckrow .sm{background:transparent;box-shadow:inset 0 0 0 1.5px #fff;color:#fff}
/* 半券を活かす案 */
.bp{display:flex;min-height:150px;border-radius:24px;box-shadow:var(--shadow);margin-bottom:12px;overflow:hidden}
.bp .main{flex:1;background:var(--hero);color:#fff;padding:14px 16px}
:root[data-night=on] .bp .main{background:#141A22}
.bp .main .k{color:#CBD5E1}
.bp .flaps{display:flex;gap:6px;margin:8px 0}
.bp .flaps b{display:inline-flex;align-items:center;justify-content:center;width:38px;height:46px;border-radius:8px;background:#1E293B;color:#FBBF24;font-size:28px;font-weight:800;box-shadow:inset 0 -23px 0 rgba(0,0,0,.18)}
.bp .main .nm{font-size:17px;font-weight:800}
.bp .main .s2{font-size:12px;color:#CBD5E1}
.bp .stub{width:108px;background:var(--stub);color:var(--stub-text);border-left:2px dashed rgba(15,27,45,.35);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:10px 6px;text-align:center}
.bp .stub b{writing-mode:vertical-rl;font-size:20px;font-weight:800;letter-spacing:.12em}
.bp .stub span{font-size:12px;font-weight:700;color:var(--stub-sub);line-height:1.35}
.live{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-top:6px}
.live .v{font-size:24px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;line-height:1.2;white-space:nowrap}
.live .v small{font-size:12px;color:var(--mute);font-weight:700;margin-left:2px}
.live .v.late{color:#B45309}
:root[data-night=on] .live .v.late{color:var(--amber)}
.live span.l{display:block;font-size:12px;color:var(--mute);font-weight:700}
.hd{display:flex;align-items:center;justify-content:space-between;gap:8px}
.hd h2{font-size:16px}
.more{display:inline-flex;align-items:center;min-height:44px;padding:0 4px 0 10px;font-size:13px;font-weight:800;color:var(--acc)}
.more .ic{width:16px;height:16px}
.cand{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;min-height:56px;margin-top:4px}
.cand .t{font-size:20px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.cand b{display:block;font-size:14px;font-weight:800;color:var(--strong)}
.cand > div > span{display:block;font-size:12px;color:var(--mute)}
.cand .sm{background:var(--strong);color:#fff}
:root[data-night=on] .cand .sm{background:transparent;box-shadow:inset 0 0 0 1.5px #fff;color:#fff}
.msg{font-size:12px;color:var(--sub);line-height:1.6;margin:-4px 6px 12px}
.msg b{color:var(--strong)}
.re{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:inset 0 0 0 1.5px var(--strong);font-size:13px;font-weight:800;color:var(--strong);margin-top:8px}
.re .ic{width:16px;height:16px}
.lst .it{display:flex;align-items:center;gap:12px;min-height:52px}
.lst .it b{flex:1;font-size:15px;font-weight:800;color:var(--strong)}
.lst .it span{font-size:14px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.lst .it span small{font-size:12px;color:var(--mute);font-weight:700}
.ring{width:14px;height:14px;border-radius:50%;flex:none}
.ring.got{background:var(--hero)}
.ring.was{background:transparent;box-shadow:inset 0 0 0 2.5px var(--hero)}
.ring.no{background:var(--track)}
.navwrap{position:absolute;left:0;right:0;bottom:14px;z-index:8;display:flex;justify-content:center;padding:0 14px}
.navwrap .tabs{width:100%}
.tabs.four{grid-template-columns:repeat(4,1fr)}
.tabs button{white-space:nowrap}
.pad{height:96px}
/* まとめて記録 */
.pick{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}
.pick span{display:flex;align-items:center;justify-content:center;gap:6px;min-height:44px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--strong)}
.pick span.on{background:var(--card);box-shadow:inset 0 0 0 2.5px var(--hero)}
.pick span.st{background:var(--hero);color:#fff}
:root[data-night=on] .pick span.st{background:rgba(74,222,128,.14);color:var(--ok)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--sub);font-weight:700;margin-top:10px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:-1px;margin-right:5px}
'''

def tabbar():
    if TABS == 'A':
        items = [('home','ホーム','home'),('live','いまの空港','live'),('rec','記録','note'),('me','マイページ','user')]; cls = 'tabs four'
    else:
        items = [('home','ホーム','home'),('book','図鑑','book'),('log','フライト','plane'),('ops','運用','ops'),('sg','修行','stairs')]; cls = 'tabs'
    b = ''.join('<button type="button"%s>%s%s</button>' % (' aria-current="page"' if k == 'home' else '', ic(i), l) for k, l, i in items)
    return '<div class="navwrap"><nav class="%s" aria-label="下のタブ">%s<i class="dot" style="left:calc(6px + (100%% - 12px) * %f - 2.5px)"></i></nav></div>' % (cls, b, .5 / len(items))

# 航空図風の地図（自前で描いた単純な形。出典の要る地図は使わない）
def map_japan(route=False):
    s = ('<svg viewBox="0 0 390 520" preserveAspectRatio="xMidYMin slice">'
         '<g stroke="var(--gl)" stroke-width=".6" opacity=".7">' + ''.join('<path d="M%d 0V520"/>' % x for x in range(30, 390, 60)) + ''.join('<path d="M0 %dH390"/>' % y for y in range(40, 520, 60)) + '</g>'
         '<g transform="translate(78,6) scale(.66)">'
         '<g fill="var(--land)" stroke="var(--coast)" stroke-width="1.2">'
         '<path d="M262 40c20-8 46 2 58 18s6 34-10 44-34 2-46-10-18-44-2-52z"/>'
         '<path d="M236 128c14-6 26 6 30 22l18 46c8 22 10 44 2 64l-16 34c-8 18-26 28-46 34l-44 14c-22 6-44 4-62 12l-30 16c-12 6-26 2-30-8s4-22 16-30l40-22c16-8 30-20 40-34l34-50c10-16 18-34 22-52z"/>'
         '<path d="M92 340c14-6 30-2 38 10s2 26-12 32-30 4-38-6-2-30 12-36z"/>'
         '<path d="M150 336c12-2 26 2 30 10s-4 14-16 14-24-4-26-12 0-10 12-12z"/>'
         '<path d="M40 470c6-3 12 0 12 6s-6 8-12 6-6-10 0-12z"/></g>')
    pts = [(286,74,'札幌',1),(232,262,'羽田',1),(176,276,'中部',1),(150,300,'伊丹',1),(104,358,'福岡',1),(46,476,'那覇',0),(196,232,'小松',0),(258,186,'仙台',1),(120,322,'広島',0)]
    if route:
        s += '<path d="M232 262Q300 170 286 74" fill="none" stroke="var(--strong)" stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round"/>'
    for x, y, n, got in pts:
        s += ('<circle cx="%d" cy="%d" r="8" fill="%s" stroke="#fff" stroke-width="2.5"/>' % (x, y, 'var(--hero)' if got else '#B8C1CC')) + ('<text class="ml%s" x="%d" y="%d" style="font-size:%dpx">%s</text>' % ('' if got else ' s', x + 12, y + 6, 19 if got else 18, n))
    s += '<circle cx="246" cy="250" r="9" fill="#2F6FE4" stroke="#fff" stroke-width="3"/><circle cx="246" cy="250" r="20" fill="rgba(47,111,228,.14)"/></g>'
    return '<div class="map">' + s + '</svg></div>'

def map_hnd(in_area=True):
    s = ('<svg viewBox="0 0 390 520" preserveAspectRatio="xMidYMin slice">'
         '<g transform="translate(0,-112)">'
         '<path d="M0 0h390v150c-60 30-120 10-170 40S90 190 0 230z" fill="var(--land)" stroke="var(--coast)" stroke-width="1.2"/>'
         '<path d="M120 200l140-30 60 130-150 60z" fill="var(--land)" stroke="var(--coast)" stroke-width="1.2"/>'
         '<circle cx="200" cy="270" r="128" fill="none" stroke="var(--rw)" stroke-width="1.6" stroke-dasharray="6 6" opacity=".8"/>'
         '<g stroke="var(--rw)" stroke-width="7" stroke-linecap="round" opacity=".9"><path d="M160 200l46 140"/><path d="M200 190l46 140"/><path d="M150 330l110-50"/><path d="M118 250l56 110"/></g>'
         '<text class="ml" x="232" y="214">HND 羽田</text><text class="ml s" x="232" y="232">判定範囲 2.0km</text>')
    if in_area:
        s += '<circle cx="186" cy="262" r="9" fill="#2F6FE4" stroke="#fff" stroke-width="3"/><circle cx="186" cy="262" r="22" fill="rgba(47,111,228,.15)"/>'
    else:
        s += '<circle cx="356" cy="96" r="9" fill="#2F6FE4" stroke="#fff" stroke-width="3"/><circle cx="356" cy="96" r="40" fill="rgba(47,111,228,.10)" stroke="rgba(47,111,228,.35)" stroke-dasharray="3 4"/>'
    return '<div class="map">' + s + '</g></svg></div>'

def page(title, body, night=False):
    return ('<!doctype html><html lang="ja"%s><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s</style></head><body><div class="scr">%s%s</div></body></html>') % (' data-night="on"' if night else '', title, CSS, body, tabbar())

# ── 部品
def float_out():
    mp = '' if TABS == 'A' else '<button class="fp">%sマイページ</button>' % ic('user')
    return '<div class="float"><span class="fp"><b>16</b><small>/86 空港</small></span><span class="sp"></span>%s<button class="fp circ" aria-label="いまの場所へ">%s</button></div>' % (mp, ic('target'))
def float_in(name='羽田'):
    return '<div class="float"><span class="fp in"><i class="dot"></i>HND %sの判定の中</span><span class="sp"></span><button class="fp circ" aria-label="いまの場所へ">%s</button></div>' % (name, ic('target'))

NEXT = ('<section class="c"><div class="hd"><span class="k">次のフライト</span><button class="sm">%s予定</button></div>'
        '<div class="row" style="margin-top:2px"><div class="big"><small>あと</small>14<small>日</small></div><span class="sp"></span>'
        '<div class="rt">羽田 → 新千歳<small>12月9日（水）</small></div></div>'
        '<div class="fn" style="margin-top:6px"><span class="cc jl">JL</span> 503<span>8:15 発・A350-900</span></div></section>') % ic('plus')
NEAR = ('<section class="c"><span class="k">いちばん近い空港</span><div class="row" style="margin-top:2px"><div class="fn" style="font-size:18px">羽田<span>HND・第1ターミナル</span></div>'
        '<span class="sp"></span><div class="big" style="font-size:28px">28.4<small>km</small></div></div>'
        '<p class="quiet">空港に近づくとチェックインできます</p>'
        '<div class="row" style="margin-top:8px;flex-wrap:wrap"><button class="sm">羽田のいまを見る%s</button><button class="sm">ほか3つ%s</button></div></section>') % (ic('chev'), ic('chev'))
GOAL = ('<section class="c"><div class="hd"><span class="k">次の小さな目標</span></div><div class="row"><div class="fn" style="font-size:16px">関東</div><span class="sp"></span>'
        '<div class="big" style="font-size:26px">4<small>/6</small></div></div><div class="bar2"><i style="width:66%"></i></div>'
        '<p class="quiet">あと2空港（調布・大島）</p></section>')
EMPTY = ('<section class="c"><span class="k">次のフライト</span><p class="quiet" style="margin-top:4px">予定を入れると、出発までの日数がここに出ます</p>'
         '<div class="two"><button class="sm dark">%s次の予定を入れる</button><button class="sm">行ったことがある空港をまとめて記録</button></div></section>') % ic('plus')

LIVE = ('<section class="c"><div class="hd"><h2>羽田のいま</h2><button class="more">くわしく%s</button></div>'
        '<div class="live"><div><span class="l">平均の遅れ</span><div class="v late">+12<small>分</small></div></div>'
        '<div><span class="l">滑走路</span><div class="v">34R<small>ほか2</small></div></div>'
        '<div><span class="l">特別塗装機</span><div class="v">4<small>機</small></div></div></div></section>') % ic('chev')
def CAND(done=False):
    return ('<section class="c"><div class="hd"><h2>今日の便を記録</h2><button class="more">ほかの便%s</button></div>'
            '<div class="cand"><div class="t">14:35</div><div><b><span class="cc jl" style="margin-right:4px">JL</span>519 新千歳ゆき</b><span>運航情報から・定刻・A350-900</span></div><button class="sm">記録する</button></div>'
            '<div class="cand"><div class="t">15:00</div><div><b><span class="cc jl" style="margin-right:4px">JL</span>115 伊丹ゆき</b><span>運航情報から・定刻・787-8</span></div><button class="sm">記録する</button></div></section>') % ic('chev')
def APN(first=False):
    if first:
        return '<div class="apn"><h1>羽田</h1><span class="first">はじめての空港</span></div>'
    return '<div class="apn"><h1>羽田</h1><span>12回目の訪問・前回 10月18日</span></div>'

def CK_PILL():
    return ('<button class="ck"><span>羽田でチェックイン</span><span class="perf"></span><span class="tear">%s</span></button>'
            '<p class="msg">押すと右の端が切れて印になります（今の半券の動きを短くしたもの）。</p>') % ic('arrow')
def CK_STUB():
    return ('<div class="bp"><div class="main"><span class="k">いまいる空港</span><div class="flaps"><b>H</b><b>N</b><b>D</b></div>'
            '<div class="nm">羽田</div><div class="s2">第1ターミナル・判定範囲の中</div></div>'
            '<button class="stub"><b>チェックイン</b><span>→ 右へ引いて<br>印をもらう</span></button></div>')
CK_HOLD = ('<button class="ck hold">%s<span>チェックインを保存<br><small>電波が戻ったら送ります</small></span></button>'
           '<p class="msg">電波が悪いので、この端末に<b>時刻と位置</b>を残しました。送ったあとサーバーで判定して、印になります。</p>') % ic('cloud')
CK_DONE = ('<div class="ckrow"><button class="ck done">%s本日チェックイン済み</button><button class="sm">%s今日の便を記録</button></div>') % (ic('check'), ic('plus'))

SC = {}
def add(key, title, body, night=False):
    SC[key] = (title, page(title, body, night))

# ふだん
add('H1', 'ふだん・シートふつう', map_japan(True) + float_out() + '<div class="sheet m"><div class="grab"></div>' + NEXT + NEAR + GOAL + '</div>')
add('H1e', 'ふだん・予定なし', map_japan() + float_out() + '<div class="sheet m"><div class="grab"></div>' + EMPTY + NEAR + GOAL + '</div>')
add('H2', 'ふだん・シート小', map_japan(True) + float_out() + ('<div class="sheet s"><div class="grab"></div><section class="c"><div class="row"><span class="k">次のフライト</span>'
    '<div class="big" style="font-size:26px"><small>あと</small>14<small>日</small></div><span class="sp"></span><div class="rt" style="font-size:15px">羽田 → 新千歳<small>12月9日</small></div></div></section></div>'))
add('H3', 'ふだん・シート大', map_japan(True) + float_out() + '<div class="sheet l"><div class="grab"></div>' + NEXT + NEAR + GOAL +
    ('<section class="c lst"><span class="k">地方の進み具合</span>'
     '<div class="it"><b>北海道</b><span>3<small>/13</small></span></div><div class="it"><b>東北</b><span>2<small>/9</small></span></div><div class="it"><b>関東</b><span>4<small>/6</small></span></div></section>') + '</div>')
# 空港の近く（位置がずれたとき）
add('H5g', '空港の近く・位置がずれた', map_hnd(False) + float_out() + ('<div class="sheet m"><div class="grab"></div>'
    '<section class="c"><span class="k">いちばん近い空港</span><div class="row" style="margin-top:2px"><div class="fn" style="font-size:18px">羽田<span>判定範囲の外</span></div>'
    '<span class="sp"></span><div class="big" style="font-size:28px">2.6<small>km</small></div></div>'
    '<p class="quiet">位置の誤差が大きいようです（±900m）。ターミナルの中にいるときは、もう一度確かめてください。</p>'
    '<button class="re">%s羽田にいますか？ もう一度位置を確かめる</button></section>' % ic('target') + LIVE + '</div>'))
# 空港にいるとき
add('H4a', '空港・まだ（全幅のボタン）', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_PILL() + LIVE + CAND() + '</div>')
add('H4b', '空港・まだ（半券を活かす）', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_STUB() + LIVE + CAND() + '</div>')
add('H4f', '空港・はじめて', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN(True) + CK_PILL() + LIVE + '</div>')
add('H5', '空港・電波が悪い', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_HOLD + LIVE + '</div>')
add('H6', '空港・済み', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_DONE + LIVE + CAND() + '</div>')
add('H4s', '空港・シート小', map_hnd() + float_in() + '<div class="sheet s"><div class="grab"></div>' + APN() + CK_PILL().split('<p class="msg"')[0] + '</div>')
# まとめて記録（印とは別の記録）
add('H7', '行ったことがある空港をまとめて記録', map_japan() + float_out() + ('<div class="sheet l"><div class="grab"></div>'
    '<div class="apn"><h1 style="font-size:22px">行ったことがある空港</h1></div>'
    '<section class="c"><span class="k">関東</span><div class="pick"><span class="st">羽田</span><span class="on">成田</span><span>調布</span><span>大島</span><span class="on">八丈島</span><span>茨城</span></div>'
    '<span class="k" style="display:block;margin-top:14px">北海道</span><div class="pick"><span class="st">新千歳</span><span class="on">函館</span><span>旭川</span></div>'
    '<div class="legend"><span><i style="background:var(--hero)"></i>印（現地で押した）</span><span><i style="box-shadow:inset 0 0 0 2.5px var(--hero)"></i>行ったことがある（印ではない）</span></div></section>'
    '<p class="msg">ここで選んだ空港は<b>印になりません</b>。図鑑では輪だけの形で出て、印の数（16/86）にも入りません。現地でチェックインすると印になります。</p>'
    '<button class="ck" style="background:var(--strong);color:#fff;box-shadow:none;min-height:54px;font-size:16px">3つの空港を記録</button></div>'))
# 夜
add('H1n', 'ふだん（夜）', map_japan(True) + float_out() + '<div class="sheet m"><div class="grab"></div>' + NEXT + NEAR + GOAL + '</div>', True)
add('H4an', '空港・まだ（夜）', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_PILL() + LIVE + CAND() + '</div>', True)
add('H5n', '空港・電波が悪い（夜）', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_HOLD + LIVE + '</div>', True)
add('H6n', '空港・済み（夜）', map_hnd() + float_in() + '<div class="sheet m"><div class="grab"></div>' + APN() + CK_DONE + LIVE + CAND() + '</div>', True)

def write(suffix=''):
    for k, (t, h) in SC.items():
        if suffix and k not in ('H1', 'H4a'): continue  # タブ帯の案A は2枚だけ
        open('%s/%s%s.html' % (OUT, k, suffix), 'w', encoding='utf-8').write(h)
    print('書いた：', ', '.join(SC), TABS)

if __name__ == '__main__':
    write('' if TABS == 'B' else '-tabA')
