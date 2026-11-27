# -*- coding: utf-8 -*-
# 運用タブを「全部が一つに並ぶ一覧＋押すと専用ページ」にする画面案（design/ops-hub 1版）。PM の指示 11/19 14時10分＋本人の追記 14時07分（シンプルに）。
# 1画面1ファイルの HTML（iPhone の幅 393・外部の読み込みなし）を ../ に書き出す。PNG と動画は shoot.py で撮る。
# 色と字・上の1行・タブ帯は base_ops.py（design/ops-split の部品＝本番の運用タブ PR #112 の元）。夜の色は design/ios-app の夜と同じ。
# どの画面も同じ1つの仕組み（一覧・広がる動き・専用ページ）から作る。FREEZE で止めた画面が H1〜H4、止めないものが M1（触って試せる）。
# 見本の時刻は 11/19 15:10（羽田・北風運用）。数字は見本。
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base_ops import CSS as BASE, I, CHEV, DOWN, LEFT, SRCH, PLANE, TOWER, INFO, SHARE, TABBAR, TOP

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
W = 393

PIN_ON = '<svg class="i pin" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 3.5h7"/><path style="fill:currentColor" d="M10 3.5v5.2L6.8 13h10.4L14 8.7V3.5Z"/><path d="M12 13v7.5"/></svg>'
PIN_OFF = '<svg class="i pin" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 3.5h7"/><path d="M10 3.5v5.2L6.8 13h10.4L14 8.7V3.5Z"/><path d="M12 13v7.5"/></svg>'
CAM = '<path d="M4 8h3l2-2.5h6L17 8h3v11H4Z"/><circle cx="12" cy="13" r="3.6"/>'
CHECK = '<path d="m5 12 4.5 4.5L19 7"/>'

CSS = BASE + r"""
:root{--hero:#0F1B2D}
body{width:393px}
.tabbar{width:365px}
.sheet{width:393px}
body.lock{overflow:hidden;height:100vh}
/* 一覧の頭：空港のピル（ピン止めの空港に切り替える）と i だけ。「空港｜機体」の切り替えはなくす */
.hubh{display:flex;align-items:center;gap:8px;margin-top:16px}
.hubh .sp{flex:1}
.hubh .ap{gap:6px;padding:0 12px 0 8px;cursor:pointer}
.hubh .ap .pin{width:16px;height:16px;color:var(--navy)}
.hubh .ap>svg:last-child{color:var(--mute)}
.ic.card1{background:var(--card);box-shadow:var(--sh)}
.srch{margin-top:12px;display:flex}
.srch .search{cursor:text}
/* カード：見出し1語＋大きな数字か小さな絵だけ */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.c{position:relative;background:var(--card);border-radius:22px;box-shadow:var(--sh);height:128px;overflow:hidden;cursor:pointer;-webkit-tap-highlight-color:transparent}
.c.w{grid-column:1/-1;height:148px}
.c.wl{grid-column:1/-1;height:128px}
.cin{position:absolute;inset:0;padding:14px 16px}
.lb{font-size:15px;font-weight:800;color:var(--mute);line-height:1.2}
.big{position:absolute;left:16px;bottom:14px;font-size:40px;font-weight:900;line-height:1;letter-spacing:-.01em;font-variant-numeric:tabular-nums;color:var(--ink)}
.big small{font-size:15px;font-weight:700;color:var(--sub);margin-left:3px;letter-spacing:0}
.big.m{font-size:34px}
.cpic{position:absolute;right:14px;top:14px;color:var(--sub)}
.cpic svg{width:22px;height:22px}
.dots{position:absolute;right:16px;bottom:18px;display:flex;gap:5px}
.dots i{width:12px;height:12px;border-radius:50%;display:block}
.ring{position:absolute;right:14px;top:12px;width:36px;height:36px}
.bars{position:absolute;left:16px;right:16px;bottom:14px;height:58px}
.trk{position:absolute;left:0;right:0;bottom:0;height:96px}
/* 滑走路のカード（濃い面はこの紺1色） */
.c.dark{background:var(--hero);box-shadow:none}
.dark .lb{color:#AEB9C8}
.dark .big{color:#fff;font-size:44px}
.rwc{position:absolute;right:16px;bottom:16px;display:flex;gap:6px}
.rwc span{border:1.5px solid rgba(255,255,255,.85);border-radius:8px;padding:2px 8px;font-size:16px;font-weight:800;color:#fff;font-variant-numeric:tabular-nums}
.rwc span.o{border-color:rgba(255,255,255,.35);color:#AEB9C8}
/* 地図のカード（航空図風） */
.mapsvg{position:absolute;inset:0;width:100%;height:100%;display:block}
.c.map .lb{position:absolute;left:12px;top:12px;background:rgba(255,255,255,.92);color:var(--ink2);border-radius:999px;padding:5px 12px}
.c.map .big{left:12px;bottom:12px;background:rgba(255,255,255,.92);border-radius:14px;padding:6px 10px 6px 12px;font-size:30px}
.regs{position:absolute;left:16px;bottom:16px;display:flex;gap:6px}
.regs span{font:700 13px/1 ui-monospace,Menlo,monospace;background:var(--pill);border-radius:999px;padding:7px 10px;color:var(--ink2)}
.sbig{position:absolute;right:14px;top:12px;width:44px;height:44px;border-radius:50%;background:var(--pill);display:flex;align-items:center;justify-content:center;color:var(--ink2)}
.edit{display:flex;justify-content:center;margin-top:18px}
/* 専用ページ（一覧の上にかぶさる。戻るで一覧へ） */
#stage{position:fixed;top:0;left:50%;width:393px;margin-left:-196.5px;height:100vh;z-index:3;pointer-events:none;visibility:hidden}
#stage.on{pointer-events:auto;visibility:visible}
#dvbg{position:absolute;inset:0;background:var(--bg)}
#dv{position:absolute;inset:0;padding:8px 16px 0;z-index:2}
.dtop{display:flex;align-items:center;gap:8px;height:56px}
.dtop .sp{flex:1}
.dtop .back{cursor:pointer;background:var(--card);box-shadow:var(--sh)}
.dtop .ttl{font-size:17px;font-weight:900}
#tgt{border-radius:24px}
.dtiles{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.dtile{background:var(--card);border-radius:20px;box-shadow:var(--sh);padding:12px 16px 14px}
.dtile span{display:block;font-size:14px;font-weight:800;color:var(--mute)}
.dtile b{display:block;font-size:34px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums}
.dtile b small{font-size:15px;font-weight:700;color:var(--sub);margin-left:3px}
.dtile em{display:block;font-style:normal;font-size:13px;color:var(--sub)}
.dline{font-size:14px;line-height:1.6;color:var(--mute);margin:14px 4px 0}
#fly{position:absolute;z-index:1;overflow:hidden;visibility:hidden;will-change:left,top,width,height}
#fly .L{position:absolute;left:0;top:0}
.hero2{background:var(--hero);color:#fff}
.h2in{padding:16px 18px}
.h2in .lb{color:#AEB9C8}
.h2in h3{margin:4px 0 0;font-size:44px;font-weight:900;line-height:1.1;letter-spacing:.01em}
.h2in svg.rw{display:block;width:325px;height:178px;margin:8px auto 4px}
.rwrow{display:flex;gap:18px;font-size:14px;font-weight:800;color:#AEB9C8}
.rwrow b{display:inline-block;margin:4px 6px 0 0;border:1.5px solid #fff;border-radius:8px;padding:1px 8px;font-size:17px;font-weight:800;color:#fff}
/* 地図の専用ページ */
.mapd .dtop{position:absolute;left:16px;right:16px;top:8px;z-index:2}
.mapd .dtop .ic{background:var(--card);box-shadow:var(--sh)}
.mapcard{position:absolute;left:16px;right:16px;top:536px;background:var(--card);border-radius:24px;box-shadow:0 14px 30px -18px rgba(15,23,42,.45),inset 0 0 0 1px rgba(17,24,39,.06);padding:14px 16px 16px}
.mapcard .row{display:flex;align-items:flex-end;justify-content:space-between;gap:8px}
.mapcard .big{position:static;font-size:40px}
.fl{display:flex;gap:6px;margin-top:10px}
.fl span{height:44px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--ink2)}
.fl span.on{background:var(--navy);color:#fff}
/* シート（空港を選ぶ・i の中） */
.aprow{list-style:none;margin:6px 0 0;padding:0}
.aprow li{display:flex;align-items:center;gap:12px;min-height:56px}
.aprow li+li{box-shadow:0 -1px 0 var(--line)}
.aprow .cd{flex:none;font:700 14px/1 ui-monospace,Menlo,monospace;color:#fff;background:var(--ink);border-radius:7px;padding:6px 7px}
.aprow .nm{flex:1;font-size:17px;font-weight:800}
.aprow .ck{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--navy)}
.aprow .pn{flex:none;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--navy);color:#fff}
.aprow .pn.off{background:var(--pill);color:var(--ink2)}
.aprow .pn svg{width:18px;height:18px}
.src{list-style:none;margin:10px 0 0;padding:0}
.src li{padding:10px 0;font-size:14px;line-height:1.6;color:var(--ink2)}
.src li+li{box-shadow:0 -1px 0 var(--line)}
.src li b{display:block;font-size:15px;color:var(--ink)}
.warn{margin-top:12px;background:var(--pill);border-radius:16px;padding:12px 14px;font-size:14px;line-height:1.6;color:var(--ink2)}
.warn b{color:var(--ink)}
/* 夜（design/ios-app の夜と同じ色） */
body.night{background:#0E1014;color:#DCE3EA}
body.night{--bg:#0E1014;--card:#16191F;--ink:#E5E7EB;--ink2:#D1D5DB;--mute:#A7B0BC;--sub:#A7B0BC;--pill:#1D232C;--line:#2A2F37;--navy:#2B3A52;--hero:#17243A;
  --sh:inset 0 0 0 1px rgba(220,227,234,.10)}
body.night .tabbar{background:rgba(22,25,31,.96)}
body.night .tabbar span.on{color:#DCE3EA}
body.night .brand span,body.night .mode span.on{background:#1D232C;color:#DCE3EA}
body.night .mode{background:#16191F}
body.night .ap i,body.night .aprow .cd{background:#DCE3EA;color:#0E1014}
body.night .hubh .ap .pin{color:#DCE3EA}
body.night .c.dark,body.night .hero2{box-shadow:inset 0 0 0 1px rgba(220,227,234,.12)}
body.night .c.map .lb,body.night .c.map .big{background:rgba(22,25,31,.9);color:#E5E7EB}
body.night .fl span.on,body.night .aprow .pn{background:transparent;color:#fff;box-shadow:inset 0 0 0 2px #DCE3EA}
body.night .aprow .ck{color:#DCE3EA}
"""

# ---------- 絵 ----------
def map_svg(night=False, big=False):
    # 航空図風の地図（羽田のまわり）。海・陸・滑走路・距離の輪・機体。字は入れない
    land, sea, coast, ring, rwy, pl, sp = ("#E7ECE3", "#D9E6F0", "#C9D3C4", "#7C8DAE", "#4B5563", "#1F2A44", "#A9822E")
    if night:
        land, sea, coast, ring, rwy, pl, sp = ("#151B22", "#0F1823", "#25303B", "#4E6283", "#8792A0", "#DCE3EA", "#E0B85C")
    planes = [(120, 170, 160), (250, 120, 200), (300, 230, 250), (80, 360, 20), (330, 420, 300), (170, 470, 340), (60, 250, 100),
              (215, 205, 150), (350, 330, 230), (140, 410, 10), (255, 520, 330), (40, 140, 120), (290, 60, 190), (180, 95, 170)]
    ps = "".join(f'<path transform="translate({x} {y}) rotate({r})" d="M0-7 2 1 7 3 7 5 2 4 1 8 3 10 3 11 0 10.5-3 11-3 10-1 8-2 4-7 5-7 3-2 1Z" fill="{pl}"/>' for x, y, r in planes)
    return f'''<svg class="mapsvg" viewBox="0 0 393 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<rect width="393" height="600" fill="{sea}"/>
<path d="M0 0H393V120C350 150 330 190 300 205 260 225 240 250 228 280 222 300 210 312 196 318 170 330 150 360 120 380 80 405 40 420 0 430Z" fill="{land}" stroke="{coast}" stroke-width="2"/>
<path d="M0 600V520C60 500 100 520 140 560 160 580 170 600 170 600Z" fill="{land}" stroke="{coast}" stroke-width="2"/>
<g fill="none" stroke="{ring}" stroke-width="1.2" stroke-dasharray="5 6" opacity=".75"><circle cx="210" cy="320" r="70"/><circle cx="210" cy="320" r="150"/><circle cx="210" cy="320" r="240"/></g>
<path d="M210 320 196 40M210 320 120 600" stroke="{ring}" stroke-width="1" opacity=".5" fill="none"/>
<g fill="{rwy}"><rect x="-2.5" y="-24" width="5" height="48" transform="translate(200 318) rotate(-23)"/><rect x="-2.5" y="-20" width="5" height="40" transform="translate(222 314) rotate(-23)"/>
<rect x="-2.5" y="-17" width="5" height="34" transform="translate(214 338) rotate(40)"/><rect x="-2.5" y="-17" width="5" height="34" transform="translate(236 340) rotate(50)"/></g>
{ps}
<path transform="translate(232 262) rotate(160)" d="M0-9 2.6 1.3 9 3.8 9 6.4 2.6 5.1 1.3 10.2 3.8 12.8 3.8 14 0 13.4-3.8 14-3.8 12.8-1.3 10.2-2.6 5.1-9 6.4-9 3.8-2.6 1.3Z" fill="{sp}"/>
<circle cx="232" cy="262" r="15" fill="none" stroke="{sp}" stroke-width="2"/>
</svg>'''

def rw_svg():
    # 羽田の4本の滑走路を上から見た形（上が北）。使っている所を白、使っていない B（04/22）は薄く。緑の三角は降りる向き・離陸の向き
    on, off = "#FFFFFF", "#3A4A63"
    t = 'font-size="14" font-weight="800" font-family="inherit"'
    ln = lambda x1, y1, x2, y2, c, w=9: f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'
    return f'''<svg class="rw" viewBox="0 0 325 178" aria-hidden="true">
{ln(112,128,170,92,off,8)}
{ln(96,150,150,18,on)}{ln(150,140,198,30,on)}
{ln(212,150,290,96,on)}
<path d="M90 172l6-14 6 14Z" fill="#86EFAC" transform="rotate(22 96 165)"/>
<path d="M144 162l6-14 6 14Z" fill="#86EFAC" transform="rotate(22 150 155)"/>
<path d="M296 86l-14 2 9 10Z" fill="#86EFAC"/>
<text x="58" y="160" fill="#fff" {t}>34L</text><text x="160" y="160" fill="#fff" {t}>34R</text>
<text x="196" y="174" fill="#fff" {t}>05</text>
</svg>'''

def bars_svg(night=False):
    hs = [10, 34, 52, 58, 46, 40, 44, 50, 54, 48, 38, 42, 56, 50, 40, 30, 22, 12]
    now = 9
    cur, past, fut = ("#16233A", "#AAB3C0", "#DDE2E9") if not night else ("#DCE3EA", "#6B7480", "#2A313B")
    out = []
    n = len(hs); bw = 100 / n
    for i, h in enumerate(hs):
        c = cur if i == now else (past if i < now else fut)
        out.append(f'<rect x="{i*bw+0.8:.2f}" y="{58-h}" width="{bw-1.6:.2f}" height="{h}" rx="1.4" fill="{c}"/>')
    return f'<svg class="bars" viewBox="0 0 100 58" preserveAspectRatio="none" aria-hidden="true">{"".join(out)}</svg>'

def trk_svg(night=False):
    c = "#3B4B66" if not night else "#9FB0C9"
    lines = ["M-10 30C40 40 80 70 110 96", "M20 -5C50 30 85 70 110 96", "M200 10C170 40 140 70 110 96", "M200 60C170 75 140 85 110 96",
             "M-10 80C30 82 70 90 110 96", "M90 -5C95 30 102 70 110 96", "M200 110C160 106 130 100 110 96", "M150 -5C140 30 125 70 110 96"]
    return f'<svg class="trk" viewBox="0 0 175 96" preserveAspectRatio="xMidYMax slice" aria-hidden="true"><g fill="none" stroke="{c}" stroke-width="1.6" opacity=".55">{"".join(f"<path d=\"{d}\"/>" for d in lines)}</g></svg>'

def ring_svg(pct, night=False):
    bg, fg = ("#E5E8EE", "#16233A") if not night else ("#2A313B", "#DCE3EA")
    import math
    a = 2 * math.pi * pct / 100; r = 14
    x = 18 + r * math.sin(a); y = 18 - r * math.cos(a)
    large = 1 if pct > 50 else 0
    return f'<svg class="ring" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="{r}" fill="none" stroke="{bg}" stroke-width="5"/><path d="M18 4A{r} {r} 0 {large} 1 {x:.2f} {y:.2f}" fill="none" stroke="{fg}" stroke-width="5" stroke-linecap="round"/></svg>'

# ---------- カード ----------
def cards(night, variant):
    C = []
    C.append(("rw", "c w dark", f'<div class="cin"><div class="lb">滑走路</div><div class="big">北風</div><div class="rwc"><span>34L</span><span>34R</span><span>05</span></div></div>'))
    C.append(("map", "c w map", f'{map_svg(night)}<div class="lb">地図</div><div class="big">23<small>機</small></div>'))
    if variant == "B":
        C.append(("pl", "c", f'<div class="cin"><div class="lb">機体</div><span class="sbig">{I(SRCH)}</span><div class="regs"><span>JA339J</span></div></div>'))
    C.append(("board", "c", '<div class="cin"><div class="lb">案内板</div><div class="big m">15:18<small>着</small></div></div>'))
    C.append(("sp", "c", f'<div class="cin"><div class="lb">特別塗装機</div><div class="big">2<small>機</small></div><div class="dots"><i style="background:#B4232A"></i><i style="background:#0E7490"></i></div></div>'))
    C.append(("late", "c", '<div class="cin"><div class="lb">遅れ</div><div class="big">8<small>分</small></div></div>'))
    C.append(("strip", "c", '<div class="cin"><div class="lb">短冊</div><div class="big">2<small>分後</small></div></div>'))
    day_cls = "c wl" if variant == "B" else "c"
    C.append(("day", day_cls, f'<div class="cin"><div class="lb">1日の山</div>{bars_svg(night)}</div>'))
    C.append(("ontime", "c", f'<div class="cin"><div class="lb">定時</div>{ring_svg(86, night)}<div class="big">86<small>%</small></div></div>'))
    C.append(("art", "c", f'{trk_svg(night)}<div class="cin"><div class="lb">空の道すじ</div></div>'))
    C.append(("photo", "c", f'<div class="cin"><div class="lb">撮る人</div><span class="cpic">{I(CAM)}</span><div class="big">4<small>か所</small></div></div>'))
    return "".join(f'<div class="{cls}" data-k="{k}">{body}</div>' for k, cls, body in C)

def hub_list(night, variant):
    srch = f'<div class="srch"><span class="search">{I(SRCH)}登録記号・便名で探す</span></div>' if variant == "A" else ""
    return f'''<div id="list" class="pad">{TOP}
<div class="hubh"><span class="ap" id="apbtn"><i>HND</i>羽田{PIN_ON}{I(DOWN)}</span><span class="sp"></span><span class="ic card1">{I(INFO)}</span></div>
{srch}<div class="grid">{cards(night, variant)}</div>
<div class="edit"><span class="pillbtn">並べ替え・隠す</span></div></div>'''

# ---------- 専用ページ（中身） ----------
def detail_rw():
    rest = f'''<div class="dtiles"><div class="dtile"><span>風</span><b>7<small>kt</small></b><em>340° から</em></div><div class="dtile"><span>視程</span><b>10<small>km 以上</small></b><em>15:00 の気象通報</em></div></div>
<p class="dline">実際に飛んでいる機体の向きから判定しています。</p>'''
    to = f'<div class="h2in" style="width:361px"><div class="lb">羽田の滑走路</div><h3>北風運用</h3>{rw_svg()}<div class="rwrow"><div>着陸<br><b>34L</b><b>34R</b></div><div>離陸<br><b>05</b><b>34R</b></div></div></div>'
    return dict(top='<div class="dtop"><span class="back">{L}運用</span><span class="sp"></span><span class="ic card1">{I}</span></div>', tgt="361x392", rest=rest, to=to, cls="hero2", radius=24, page="")

def detail_map(night):
    rest = '''<div class="mapcard"><div class="row"><div><div class="lb">近くを飛ぶ機体</div><div class="big">23<small>機</small></div></div></div>
<div class="fl"><span class="on">すべて</span><span>特別塗装機</span><span>着陸</span></div><p class="dline" style="margin:10px 2px 0">機体を押すと、その機体の1日へ。</p></div>'''
    return dict(top='<div class="dtop"><span class="back">{L}運用</span><span class="sp"></span><span class="ic">{I}</span></div>', tgt="393x600", rest=rest, to=map_svg(night, True), cls="", radius=0, page="mapd")

JS = r"""
const $ = s => document.querySelector(s);
const clamp = v => Math.max(0, Math.min(1, v));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => 1 - Math.pow(1 - t, 3);
let cur = null, card = null, r0 = null, r1 = null, P = 0, D = 0;
function rectIn(el){ const s = $('#stage').getBoundingClientRect(), r = el.getBoundingClientRect(); return {x:r.left - s.left, y:r.top - s.top, w:r.width, h:r.height}; }
function setup(k){
  const d = DETAIL[k]; if(!d) return false;
  cur = k; card = document.querySelector('.c[data-k="'+k+'"]');
  $('#stage').classList.add('on'); document.body.classList.add('lock');
  $('#dv').className = d.page; $('#dv').innerHTML = d.top + '<div id="tgt" style="width:'+d.tw+'px;height:'+d.th+'px;'+(d.page==='mapd'?'position:absolute;left:0;top:0':'')+'"></div>' + d.rest;
  const f = $('#fly'); f.className = d.cls; f.innerHTML = '<div class="L from" style="width:'+card.offsetWidth+'px;height:'+card.offsetHeight+'px">'+card.innerHTML+'</div><div class="L to" style="width:'+d.tw+'px;height:'+d.th+'px">'+d.to+'</div>';
  f.style.background = getComputedStyle(card).backgroundColor;
  if(d.page === 'mapd'){ f.querySelector('.from').style.cssText += ';inset:0;width:auto;height:auto'; f.querySelector('.to').style.cssText += ';inset:0;width:auto;height:auto'; f.querySelector('.from svg.mapsvg').remove(); f.style.background='transparent'; f.querySelector('.to').style.opacity=1; }
  r0 = rectIn(card); r1 = rectIn($('#tgt')); f.dataset.r0 = d.radius0 || 22; f.dataset.r1 = d.radius;
  return true;
}
function render(p, d){
  P = p; D = d || 0;
  const f = $('#fly'), st = $('#stage'), list = $('#list');
  if(p <= 0 && D <= 0){ st.classList.remove('on'); f.style.visibility='hidden'; if(card) card.style.visibility=''; list.style.transform=''; document.body.classList.remove('lock'); return; }
  st.classList.add('on'); document.body.classList.add('lock'); card.style.visibility = 'hidden'; f.style.visibility = 'visible';
  const R = {x:lerp(r0.x,r1.x,p), y:lerp(r0.y,r1.y,p), w:lerp(r0.w,r1.w,p), h:lerp(r0.h,r1.h,p)};
  Object.assign(f.style, {left:R.x+'px', top:R.y+'px', width:R.w+'px', height:R.h+'px', borderRadius:lerp(+f.dataset.r0, +f.dataset.r1, p)+'px'});
  const fr = f.querySelector('.from'), to = f.querySelector('.to');
  fr.style.opacity = 1 - clamp(p / 0.35);
  if(cur !== 'map') to.style.opacity = clamp((p - 0.15) / 0.45);
  $('#dvbg').style.opacity = clamp((p - 0.1) / 0.55);
  const q = clamp((p - 0.55) / 0.45);
  for(const el of $('#dv').children){ if(el.id === 'tgt') continue; el.style.opacity = q; el.style.transform = 'translateY(' + (18 * (1 - q)) + 'px)'; }
  list.style.transform = 'scale(' + (1 - 0.03 * p * (1 - D)) + ')'; list.style.transformOrigin = '50% 0';
  // 左端から引いて戻る（iPhone の戻る操作）：ページが指に付いて右へ動き、少し小さくなる
  st.style.transform = D ? 'translateX(' + (D * 393 * 0.62) + 'px) scale(' + (1 - 0.1 * D) + ')' : '';
  st.style.borderRadius = D ? Math.min(28, D * 120) + 'px' : '';
  st.style.overflow = D ? 'hidden' : '';
  st.style.boxShadow = D ? '-18px 0 40px -20px rgba(15,23,42,.5)' : '';
}
function anim(from, to, ms, done, dfrom){
  const t0 = performance.now();
  function step(t){ const k = clamp((t - t0) / ms), e = ease(k); render(lerp(from, to, e), dfrom ? dfrom * (1 - ease(clamp(k / 0.5))) : 0); if(k < 1) requestAnimationFrame(step); else if(done) done(); }
  requestAnimationFrame(step);
}
window.R = (k, p, d) => { if(cur !== k){ render(0,0); setup(k); } render(p, d); };
function open(k){ if(!setup(k)) return; anim(0, 1, 460); }
function close(dfrom){ anim(1, 0, 380, () => render(0, 0), dfrom); }
document.addEventListener('click', e => {
  if(window.FREEZE) return;
  const c = e.target.closest('.c[data-k]'); if(c && !cur && P === 0) return open(c.dataset.k);
  if(e.target.closest('.back')) return close();
});
// 左端から引く
let drag = null;
document.addEventListener('pointerdown', e => { if(window.FREEZE || P < 1) return; const s = $('#stage').getBoundingClientRect(); if(e.clientX - s.left < 28) drag = {x:e.clientX}; });
document.addEventListener('pointermove', e => { if(drag) render(1, clamp((e.clientX - drag.x) / 393)); });
document.addEventListener('pointerup', e => { if(!drag) return; const d = clamp((e.clientX - drag.x) / 393); drag = null; if(d > 0.3) close(d); else anim(1, 1, 200, null, d); });
document.addEventListener('click', e => { if(e.target.closest('.back')) cur = cur; });
const _close = close; close = function(d){ _close(d); setTimeout(() => { cur = null; }, 400); };
window.addEventListener('load', () => { if(window.FREEZE && window.FREEZE.k){ setup(window.FREEZE.k); render(window.FREEZE.p, window.FREEZE.d || 0); } });
"""

def detail_js(night):
    out = {}
    for k, d in (("rw", detail_rw()), ("map", detail_map(night))):
        tw, th = d["tgt"].split("x")
        out[k] = dict(top=d["top"].replace("{L}", I(LEFT)).replace("{I}", I(INFO)), tw=int(tw), th=int(th), rest=d["rest"], to=d["to"], cls=d["cls"], radius=d["radius"], page=d["page"])
    return out

def page(name, title, night=False, variant="A", freeze=None, extra=""):
    det = json.dumps(detail_js(night), ensure_ascii=False)
    fz = json.dumps(freeze, ensure_ascii=False) if freeze else "null"
    body = f'''{hub_list(night, variant)}<div id="stage"><div id="dvbg"></div><div id="dv"></div><div id="fly"></div></div>{TABBAR}{extra}
<script>window.FREEZE = {fz}; const DETAIL = {det};{JS}</script>'''
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body class="{"night" if night else ""}">{body}</body></html>'''
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

def ap_sheet():
    def row(cd, nm, sel=False, pin=True):
        ck = f'<span class="ck">{I(CHECK)}</span>' if sel else '<span class="ck"></span>'
        return f'<li><span class="cd">{cd}</span><span class="nm">{nm}</span>{ck}<span class="pn{"" if pin else " off"}">{PIN_ON if pin else PIN_OFF}</span></li>'
    return f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>空港</h2><button>閉じる</button></div>
<div class="grp">ピン止め<small>3</small></div><ul class="aprow">{row("HND","羽田",True)}{row("NRT","成田")}{row("ISG","石垣")}</ul>
<div class="grp">近く</div><ul class="aprow">{row("HND","羽田",False,True).replace("<li>","<li style='opacity:.45'>")}</ul>
<div class="pickrow"><span class="search">{I(SRCH)}空港名・コード</span></div></div>'''

def info_sheet():
    return f'''<div class="dim" style="z-index:8"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>出典と注意</h2><button>閉じる</button></div>
<ul class="src"><li><b>滑走路・機体の位置</b>adsb.lol（ODbL）から判定</li><li><b>便・遅れ</b>公共交通オープンデータ（ODPT）</li><li><b>風・視程</b>気象通報</li></ul>
<div class="warn"><b>推定と予想は保証しません。</b>運航の判断には使えません。</div></div>'''

def index():
    items = [
        ("一覧", [("H1", "一覧・案A：機体の検索窓を上に残す（昼）"), ("H1n", "一覧・案A（夜）"), ("H1b", "一覧・案B：機体を一覧の1枚のカードに（昼）"), ("H1bn", "一覧・案B（夜）")]),
        ("広がる途中", [("H2", "滑走路のカードが広がる途中（昼）"), ("H2n", "同（夜）"), ("H2m", "地図のカードが広がる途中（昼）"), ("H2mn", "同（夜）"), ("H2d", "左端から引いて戻る途中（昼）")]),
        ("専用ページ", [("H3", "滑走路（昼）"), ("H3n", "滑走路（夜）"), ("H4", "地図（昼）"), ("H4n", "地図（夜）")]),
        ("ほか", [("H5", "空港を切り替える（ピン止めの空港が先頭）"), ("H6", "i の中（出典と注意をまとめる）"), ("M1", "触って試せる：カードを押すと広がる・戻る／左端から引く")]),
    ]
    sec = "".join(f'<h2>{h}</h2><ul>' + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}</span></a></li>' for n, t in xs) + '</ul>' for h, xs in items)
    vid = '<h2>動き</h2><ul><li><a href="png/motion.mp4"><b>動画</b><span>昼：滑走路を開く→左端から引いて戻る→地図を開く→戻る</span></a></li><li><a href="png/motion-n.mp4"><b>動画</b><span>夜：同じ</span></a></li><li><a href="png/motion-strip.png"><b>連番</b><span>昼の8コマを並べた1枚</span></a></li><li><a href="png/motion-strip-n.png"><b>連番</b><span>夜の8コマ</span></a></li></ul>'
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>運用の一覧（画面案）</title><style>{CSS}</style></head><body>
<div class="idx"><h1>運用タブ：全部を一つに並べて、押すと専用ページ</h1><p>1版（11/19）。カードは見出し1語＋大きな数字か小さな絵だけ。説明は専用ページで1〜2行、出典と注意は i の中。アプリには入れていません。</p>{sec}{vid}</div></body></html>'''
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)

def build():
    page("H1", "H1 一覧 案A（昼）")
    page("H1n", "H1n 一覧 案A（夜）", night=True)
    page("H1b", "H1b 一覧 案B（昼）", variant="B")
    page("H1bn", "H1bn 一覧 案B（夜）", night=True, variant="B")
    page("H2", "H2 広がる途中 滑走路（昼）", freeze={"k": "rw", "p": 0.5})
    page("H2n", "H2n 広がる途中 滑走路（夜）", night=True, freeze={"k": "rw", "p": 0.5})
    page("H2m", "H2m 広がる途中 地図（昼）", freeze={"k": "map", "p": 0.5})
    page("H2mn", "H2mn 広がる途中 地図（夜）", night=True, freeze={"k": "map", "p": 0.5})
    page("H2d", "H2d 左端から引いて戻る途中（昼）", freeze={"k": "rw", "p": 1, "d": 0.4})
    page("H3", "H3 専用ページ 滑走路（昼）", freeze={"k": "rw", "p": 1})
    page("H3n", "H3n 専用ページ 滑走路（夜）", night=True, freeze={"k": "rw", "p": 1})
    page("H4", "H4 専用ページ 地図（昼）", freeze={"k": "map", "p": 1})
    page("H4n", "H4n 専用ページ 地図（夜）", night=True, freeze={"k": "map", "p": 1})
    page("H5", "H5 空港を切り替える", extra=ap_sheet())
    page("H6", "H6 i の中", freeze={"k": "rw", "p": 1}, extra=info_sheet())
    page("M1", "M1 触って試せる")
    page("M1n", "M1n 触って試せる（夜）", night=True)
    index()

if __name__ == "__main__":
    build()
