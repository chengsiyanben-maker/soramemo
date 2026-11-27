# -*- coding: utf-8 -*-
# 使い方：python3 make.py <出力先>（写真と空港の表は /tmp/claude-0/s/ に置いた前提。各 HTML がそのまま元なので、直すときは HTML を直してもよい）
# 図鑑を見やすくする画面案（design/zukan-book）を作る
import json, base64, os, sys
OUT = sys.argv[1]
S = '/tmp/claude-0/s/'
os.makedirs(OUT, exist_ok=True)
AP = json.load(open('/tmp/claude-0/ap.json'))
SIGN = base64.b64encode(open('/home/claude/soramemo/web/fonts/sign0-046a5a18b8.woff2', 'rb').read()).decode()
def img64(f): return 'data:image/jpeg;base64,' + base64.b64encode(open(S + f, 'rb').read()).decode()

REGION = [("北海道", ["北海道"]), ("東北", ["青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"]),
          ("関東", ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"]),
          ("中部", ["新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県"]),
          ("近畿", ["三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"]),
          ("中国", ["鳥取県", "島根県", "岡山県", "広島県", "山口県"]), ("四国", ["徳島県", "香川県", "愛媛県", "高知県"]),
          ("九州", ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県"]), ("沖縄", ["沖縄県"])]
# 今の本番の地方の色（GOD_COLORS）
RC = {"北海道": "#5B8FB9", "東北": "#4E9A7C", "関東": "#C2603A", "中部": "#7A6BB0", "近畿": "#B8577E",
      "中国": "#3F8E9C", "四国": "#6E9A3E", "九州": "#C27C2C", "沖縄": "#2C9AA8"}
def tint(h, a):
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return '#%02X%02X%02X' % tuple(round(255 - (255 - c) * a) for c in (r, g, b))
def reg(pref):
    for n, ps in REGION:
        if pref in ps: return n
A = []
for x in AP:
    A.append(dict(id=int(x[0]), name=x[1], code=x[2], pref=x[3], lat=float(x[4]), lon=float(x[5]), reg=reg(x[3])))
def short(a):
    n = a['name']
    if a['code'] in ('HND', 'ITM', 'NKM'): return n[n.index('（') + 1:n.index('）')]
    if '（' in n: n = n[:n.index('（')]
    return n.replace('空港', '').replace('国際', '') or n
def codeof(a): return a['code'] if a['code'] != '—' else short(a)
# デモの記録（今の本番のデモと同じ数：16/86、羽田は 28回 2025/12/14）
GOT = {'CTS': 6, 'AKJ': 1, 'HKD': 2, 'SDJ': 1, 'HND': 28, 'NGO': 2, 'ITM': 3, 'HIJ': 1, 'MYJ': 1,
       'FUK': 4, 'KOJ': 1, 'NGS': 1, 'KMJ': 1, 'OKA': 2, 'ISG': 1, 'MMY': 1}
def byreg(r): return sorted([a for a in A if a['reg'] == r], key=lambda a: -a['lat'])
RN = [n for n, _ in REGION]

CSS_DAY = """
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#1F2937;--strong:#111827;--sub:#4B5563;--mute:#5F6875;--pale:#7A8390;--wash:#F6F7F9;
--navy:#0F1B2D;--acc:#2563EB;--shadow:0 1px 2px rgba(17,24,39,.04),0 10px 26px -14px rgba(17,24,39,.22);
--sw-on-bg:#16233A;--sw-on-ink:#FFFFFF;--sw-off-bg:#E5E8EE;--sw-off-ring:#768090;--sw-off-ink:#4B5563;--sel:#16233A}
"""
CSS_NIGHT = """
:root{--bg:#05070B;--card:#0D1218;--ink:#BCC6D1;--strong:#DCE3EA;--sub:#8996A7;--mute:#7D8A9B;--pale:#6E7B8C;--wash:#0A0F14;
--navy:#0D1218;--acc:#DCE3EA;--shadow:0 14px 30px -18px rgba(0,0,0,.9),inset 0 0 0 1px rgba(150,170,195,.10);
--glow1:#5FD993;--sel-ring:rgba(220,227,234,.72);--sel:#DCE3EA;color-scheme:dark}
"""
CSS = """
@font-face{font-family:"Sign";src:url(data:font/woff2;base64,%s) format("woff2");font-weight:600 800;unicode-range:U+20-7E}
:root{--gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic","Meiryo","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;--sign:"Sign","Barlow Condensed","Arial Narrow",var(--gothic)}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:15px;line-height:1.6;-webkit-text-size-adjust:100%%}
.phone{position:relative;max-width:420px;margin:0 auto;overflow:hidden;min-height:100vh}
.wrap{padding:10px 16px 0}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow)}
.u{font-family:var(--gothic);font-size:12px;font-weight:600;color:var(--mute);margin-left:3px;letter-spacing:0}
.num{font-family:var(--sign);font-weight:700;color:var(--strong);line-height:1;letter-spacing:.01em}
.top{display:flex;align-items:center;justify-content:space-between;height:56px}
.logo{display:flex;align-items:center;gap:8px;font-weight:800;font-size:18px;color:var(--strong)}
.logo svg{width:24px;height:24px}
.pill{height:44px;display:inline-flex;align-items:center;justify-content:center;gap:6px;font-size:14px;font-weight:700;color:var(--ink);background:var(--card);box-shadow:var(--shadow);border-radius:999px;padding:0 16px;flex:none;text-decoration:none}
.pill.on{background:var(--sel);color:#fff}
.seg{display:flex;background:#E2E6EC;border-radius:999px;padding:4px;margin-top:4px}
.seg b{flex:1;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:14px;color:var(--sub)}
.seg b.on{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.ttl{display:flex;align-items:center;gap:8px;margin:18px 0 0}.main .ttl .pill{padding:0 14px}
.ttl h1{font-size:26px;margin:0 auto 0 2px;color:var(--strong);letter-spacing:.04em}
.vband{display:flex;gap:8px;align-items:center;margin:12px 0 0}
.vband .pill{box-shadow:none;background:transparent;color:var(--sub);padding:0 14px}
.vband .pill.on{background:var(--sel);color:#fff}
.vband .ed{margin-left:auto;width:44px;padding:0}
svg.i{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.tabs{position:fixed;left:50%%;transform:translateX(-50%%);bottom:14px;width:calc(min(420px,100vw) - 28px);height:64px;border-radius:999px;background:rgba(255,255,255,.94);box-shadow:0 10px 30px -8px rgba(17,24,39,.22),0 2px 6px rgba(17,24,39,.06);display:flex;padding:0 8px;z-index:30}
.tabs b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:13px;font-weight:700;color:#5F6875;position:relative}
.tabs b.on{color:#1F2937}.tabs b.on::after{content:"";position:absolute;bottom:5px;width:5px;height:5px;border-radius:50%%;background:var(--acc)}
.tabs svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.tabs b.on svg{stroke:var(--acc)}
/* ツメ（端の見出し） */
.tsume{position:fixed;right:max(0px,calc(50vw - 210px));top:122px;display:flex;flex-direction:column;gap:2px;z-index:20}
.tsume a{width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:14px 0 0 14px;background:var(--tc);color:var(--strong);font-size:13px;font-weight:700;text-decoration:none;writing-mode:vertical-rl;letter-spacing:0;line-height:1;position:relative;box-shadow:inset 4px 0 0 var(--c)}
.tsume a.on{width:52px;margin-left:-8px;background:var(--card);box-shadow:inset 6px 0 0 var(--c),-6px 6px 18px -8px rgba(17,24,39,.35);font-weight:800}
.tsume a.sm{font-size:13px}
.main{margin-right:52px}
/* 扉 */
.door{margin-top:18px;padding:18px 18px 16px;display:flex;gap:14px;align-items:center;position:relative;overflow:hidden}
.door::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--c)}
.door h2{margin:0;font-size:24px;color:var(--strong);letter-spacing:.04em;line-height:1.2}
.door .cnt{margin-top:8px}.door .cnt .num{font-size:40px}
.door .ds{font-size:13px;color:var(--sub);margin-top:6px;line-height:1.5}
.door .tx{flex:1;min-width:0}
.bar{height:6px;border-radius:3px;background:#E8EBF0;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%%;background:var(--c);border-radius:3px}
.mini{flex:none;width:104px;height:104px;border-radius:18px;background:var(--wash)}
/* 空港の並び（そろえた枠） */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}
.ap{position:relative;border-radius:18px;background:var(--card);box-shadow:var(--shadow);height:132px;padding:12px 10px 10px;display:flex;flex-direction:column;text-decoration:none;color:inherit;overflow:hidden}
.ap::before{content:"";position:absolute;left:10px;top:0;width:22px;height:4px;border-radius:0 0 3px 3px;background:var(--c)}
.ap .cd{font-family:var(--sign);font-weight:700;font-size:26px;line-height:1.05;color:var(--strong);letter-spacing:.02em}
.ap .cd.jp{font-family:var(--gothic);font-size:20px;line-height:1.3;font-weight:800}
.ap .nm{font-size:13px;font-weight:700;color:var(--ink);line-height:1.35;margin-top:3px}
.ap .ft{margin-top:auto;display:flex;align-items:center;gap:6px;font-size:13px;color:var(--sub)}
.ap .ft b{font-family:var(--sign);font-size:18px;color:var(--strong);font-weight:700}
.ap.no{background:var(--wash);box-shadow:inset 0 0 0 1px #E3E6EB}
.ap.no .cd{color:var(--pale)}.ap.no .nm{color:var(--sub);font-weight:600}
.stp{width:30px;height:30px;flex:none}
.sec-h{display:flex;align-items:baseline;gap:8px;margin:22px 2px 0;font-size:15px;font-weight:800;color:var(--strong)}
.sec-h small{font-size:13px;color:var(--sub);font-weight:600}
.ann{position:relative;z-index:10;margin:20px 0 120px;font:13px/1.7 var(--gothic);background:#FFF6DC;color:#4A3D10;padding:12px 14px;border-radius:16px}
.ann b{display:block}.ann ul{margin:4px 0 0;padding-left:1.2em}
.hero{margin-top:12px;background:var(--navy);color:#fff;border-radius:22px;padding:16px 18px;display:flex;align-items:flex-end;gap:12px}
.hero .lab{font-size:13px;color:#C9D2DE;font-weight:700}
.hero .num{color:#fff;font-size:44px}.hero .u{color:#C9D2DE;font-size:14px}
.hero .side{margin-left:auto;text-align:right;font-size:13px;color:#C9D2DE;line-height:1.5}
.rbar{display:flex;gap:2px;margin-top:8px;height:6px}.rbar i{display:block;border-radius:2px}
.back{display:inline-flex}
.dl{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.dl > div{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:12px 14px 12px}
.dl .k{font-size:13px;color:var(--sub);font-weight:700}
.dl .v{margin-top:4px}.dl .v .num{font-size:30px}
.dl .v.s .num{font-size:24px}
.row{display:flex;align-items:center;gap:12px;min-height:52px;padding:4px 16px}
.row .tx{flex:1;min-width:0}.row .tx b{display:block;color:var(--strong);font-size:15px;line-height:1.4}.row .tx small{display:block;color:var(--sub);font-size:13px;line-height:1.5}
.chip{display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:700;background:var(--tc);color:var(--strong)}
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:50}
.sheet{position:fixed;left:50%%;transform:translateX(-50%%);bottom:0;width:min(420px,100vw);background:var(--card);border-radius:28px 28px 0 0;box-shadow:0 -10px 40px -10px rgba(15,23,42,.4);z-index:60;padding:10px 16px 24px}
.grab{width:40px;height:5px;border-radius:3px;background:#D5DAE1;margin:2px auto 10px}
.sw{width:68px;height:34px;border-radius:999px;display:flex;align-items:center;flex:none;position:relative;font-size:13px;font-weight:800}
.sw.on{background:var(--sw-on-bg);color:var(--sw-on-ink);padding-left:12px}
.sw.on::after{content:"";position:absolute;right:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff}
.sw.off{background:var(--sw-off-bg);color:var(--sw-off-ink);box-shadow:inset 0 0 0 1.5px var(--sw-off-ring);justify-content:flex-end;padding-right:10px}
.sw.off::after{content:"";position:absolute;left:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff;box-shadow:inset 0 0 0 1.5px var(--sw-off-ring)}
.btn{height:52px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;background:var(--sel);color:#fff;margin-top:14px}
.note{font-size:13px;color:var(--sub);margin:8px 2px 0;line-height:1.6}
""" % SIGN

NIGHT_EXTRA = """
.pill.on,.vband .pill.on{background:#141B24;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.seg{background:#0A0F14;box-shadow:inset 0 0 0 1px rgba(150,170,195,.10)}
.seg b.on{background:#141B24;box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.tabs{background:#0D1218;box-shadow:0 10px 30px -6px rgba(0,0,0,.8),inset 0 0 0 1px rgba(150,170,195,.10)}
.tabs b{color:var(--sub)}.tabs b.on{color:var(--strong)}.tabs b.on svg{stroke:var(--strong)}.tabs b.on::after{background:var(--strong)}
.tsume a{background:#0D1218;box-shadow:inset 0 0 0 1px rgba(150,170,195,.12);color:var(--ink)}
.tsume a.on{background:#141B24;box-shadow:inset 0 0 0 1.5px var(--sel-ring);color:var(--strong)}
.door::before,.ap::before{display:none}
.bar{background:#141B24}.bar i{background:var(--glow1)}
.mini{background:#0A0F14}
.ap.no{background:transparent;box-shadow:inset 0 0 0 1.5px #232D39}
.hero{background:var(--card);box-shadow:var(--shadow)}.hero .lab,.hero .side,.hero .u{color:var(--sub)}
.hero .num.lit{color:var(--glow1);text-shadow:0 0 6px rgba(95,217,147,.45)}
.ann{background:#1A1A10;color:#E9DFB8;box-shadow:inset 0 0 0 1px #4A4220}
.u{color:var(--mute)}
"""

ICON_LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" stroke-width="5"/><path d="M16 36l32-12-8 20-6-8z" fill="currentColor"/></svg>'
TAB_ICONS = {
 'ホーム': '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
 '図鑑': '<path d="M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1z"/><path d="M12 6v14"/>',
 'フライト': '<path d="M10.5 13.5 4 11l1.5-1.5 7 1 3.5-3.5c1-1 2.5-1.2 3-.5s.5 2-.5 3L15 13l1 7-1.5 1.5-2.5-6.5-3 3v2.5L7.5 22 6 18l-4-1.5L3.5 15H6z"/>',
 '運用': '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><path d="M12 3.5v3M12 17.5v3"/>',
 '修行': '<path d="M4 20h4v-4h4v-4h4V8h4"/>'}
def tabs(on='図鑑'):
    return '<nav class="tabs">' + ''.join('<b class="%s"><svg viewBox="0 0 24 24">%s</svg>%s</b>' % ('on' if k == on else '', v, k) for k, v in TAB_ICONS.items()) + '</nav>'
def tsume(on, night=False):
    s = '<nav class="tsume" aria-label="地方へ飛ぶ">'
    for n in RN:
        s += '<a href="#%s" class="%s" style="--c:%s;--tc:%s">%s</a>' % (n, 'on' if n == on else '', RC[n], tint(RC[n], .16), n)
    return s + '</nav>'
def stamp(a, got, c, night=False, size=30):
    if got:
        col = '#DCE3EA' if night else '#16233A'
        return '<svg class="stp" style="width:%dpx;height:%dpx" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="13" fill="none" stroke="%s" stroke-width="2"/><circle cx="15" cy="15" r="9.5" fill="none" stroke="%s" stroke-width="1"/><path d="M9 15.5l4 4 8-9" fill="none" stroke="%s" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>' % (size, size, col, col, col)
    col = '#5F6875' if not night else '#66778C'
    return '<svg class="stp" style="width:%dpx;height:%dpx" viewBox="0 0 30 30" aria-hidden="true"><circle cx="15" cy="15" r="13" fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="3 3"/></svg>' % (size, size, col)
def cell(a, night=False):
    g = GOT.get(a['code'])
    c = RC[a['reg']]
    cd = codeof(a)
    jp = ' jp' if a['code'] == '—' else ''
    nm = short(a)
    if g:
        ft = stamp(a, True, c, night) + '<span><b>%d</b><span class="u">回</span></span>' % g
        return '<a class="ap" href="04-airport.html" style="--c:%s"><span class="cd%s">%s</span><span class="nm">%s</span><span class="ft">%s</span></a>' % (c, jp, cd, nm, ft)
    ft = stamp(a, False, c, night) + '<span>まだ</span>'
    return '<div class="ap no" style="--c:%s"><span class="cd%s">%s</span><span class="nm">%s</span><span class="ft">%s</span></div>' % (c, jp, cd, nm, ft)
def minimap(r, night=False):
    L = byreg(r)
    la = [a['lat'] for a in L]; lo = [a['lon'] for a in L]
    W = 104; pad = 14
    dx = max(lo) - min(lo) or 1; dy = max(la) - min(la) or 1
    sc = (W - 2 * pad) / max(dx, dy)
    ox = (W - dx * sc) / 2; oy = (W - dy * sc) / 2
    s = '<svg class="mini" viewBox="0 0 %d %d" aria-label="%sの空港の場所">' % (W, W, r)
    c = '#5FD993' if night else RC[r]
    for a in L:
        x = ox + (a['lon'] - min(lo)) * sc; y = oy + (max(la) - a['lat']) * sc
        if GOT.get(a['code']):
            s += '<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (x, y, c)
        else:
            s += '<circle cx="%.1f" cy="%.1f" r="4" fill="none" stroke="%s" stroke-width="1.5"/>' % (x, y, '#66778C' if night else '#8A93A0')
    return s + '</svg>'
def door(r, night=False, desc=True):
    L = byreg(r); g = sum(1 for a in L if GOT.get(a['code']))
    last = {'北海道': '旭川　2026/5/24', '関東': '羽田　2026/11/1'}.get(r, '')
    ds = ('<div class="ds">最後に押した：%s</div>' % last) if (desc and last) else ''
    return ('<section class="card door" id="%s" style="--c:%s"><div class="tx"><h2>%s</h2><div class="cnt"><span class="num">%d</span><span class="u">/ %d 空港</span></div>'
            '<div class="bar"><i style="width:%d%%"></i></div>%s</div>%s</section>') % (r, RC[r], r, g, len(L), round(g / len(L) * 100), ds, minimap(r, night))
def page(fn, title, body, night=False, extra=''):
    css = (CSS_NIGHT if night else CSS_DAY) + CSS + (NIGHT_EXTRA if night else '') + extra
    html = '<!doctype html>\n<html lang="ja"%s><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>%s｜図鑑を見やすく（画面案）</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (
        ' data-night="on"' if night else '', title, css, body)
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(html)

def header(night=False):
    return ('<div class="top"><span class="logo">%s そらメモ</span><span class="pill">マイページ</span></div>'
            '<div class="seg"><b class="on">スタンプラリー</b><b>エアライン経営</b></div>') % ICON_LOGO
def titlerow():
    return ('<div class="ttl"><h1>図鑑</h1>'
            '<a class="pill" href="05-legend-index.html"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg>索引</a>'
            '<a class="pill" href="06-bessatsu.html">別冊</a></div>')
def vband(on='図鑑'):
    s = '<div class="vband">'
    for v in ['図鑑', '地図', '行った順']:
        s += '<span class="pill%s">%s</span>' % (' on' if v == on else '', v)
    return s + '<a class="pill ed" href="07-views.html" aria-label="見方の帯を編集"><svg class="i" viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/></svg></a></div>'
def hero(night=False):
    tot = sum(1 for a in A if GOT.get(a['code']))
    rb = ''.join('<i style="flex:%d;background:%s"></i>' % (len(byreg(r)), ('#5FD993' if night else RC[r]) if any(GOT.get(a['code']) for a in byreg(r)) else ('#141B24' if night else '#2A3A55')) for r in RN)
    return ('<section class="hero"><div><div class="lab">集めた空港</div><span class="num%s">%d</span><span class="u">/ 86</span></div>'
            '<div class="side">全国の 19%%<br>まだ 70 空港</div></section>') % (' lit' if night else '', tot)

# ---------- 02 図鑑の基本 ----------
def p02(night=False):
    b = tsume('北海道', night) + '<div class="wrap">' + header(night) + '<div class="main">' + titlerow() + vband() + hero(night)
    b += door('北海道', night)
    b += '<div class="grid">' + ''.join(cell(a, night) for a in byreg('北海道')) + '</div>'
    b += door('東北', night) + '<div class="grid">' + ''.join(cell(a, night) for a in byreg('東北')[:6]) + '</div>'
    if night:
        ann = ('<b>02 の夜（夜の画面の色）</b><ul><li>ツメは地方の色を使わず、選んでいる地方だけ強い字＋細い縁（夜は光る色を緑と琥珀の2色まで、の決まり）</li>'
               '<li>光らせるのは「集めた空港 16」だけ。扉の進み具合と地図の点は緑の細い線と点</li><li>まだの空港は地を抜いて細い縁だけ。字は 4.5:1 以上</li></ul>')
    else:
        ann = ('<b>02 図鑑の基本：ツメ＋地方の扉＋空港の並び</b><ul><li>右端のツメ（9地方）を押すと、その地方の扉へ飛ぶ。ツメはいつも同じ場所に出したまま</li>'
               '<li>切り替えは「見方」の帯1段だけ（図鑑・地図・行った順）。飛行場・番外編・特別塗装・実績は右上の「別冊」へ（06）</li>'
               '<li>扉：地方名・集めた数・進み具合・空港の場所の小さな地図（●集めた ○まだ）</li>'
               '<li>地方の色は今の本番の地方の色（守り神の色）。ツメの左の帯・扉の左の帯・枠の上の小さな帯だけに使う</li>'
               '<li>上の「そらメモ・スタンプラリー／エアライン経営」は今の本番のまま</li></ul>')
    b += '<div class="ann">' + ann + '</div></div></div>' + tabs()
    page('02-zukan-base%s.html' % ('-night' if night else ''), '図鑑の基本' + ('（夜）' if night else ''), b, night)

# ---------- 03 空港の並び ----------
def p03():
    ex = '.stick{position:sticky;top:0;z-index:15;background:var(--bg);margin:0 -16px;padding:8px 16px 8px;display:flex;align-items:center;gap:10px}.stick b{font-size:17px;color:var(--strong)}.stick .dot{width:10px;height:10px;border-radius:50%;background:var(--c)}.stick small{font-size:13px;color:var(--sub);font-weight:700}.stick .pill{margin-left:auto}'
    L = byreg('関東')
    b = tsume('関東') + '<div class="wrap"><div class="main"><div class="stick" style="--c:%s"><span class="dot"></span><b>関東</b><small>1 / 9</small><a class="pill" href="02-zukan-base.html">図鑑の上へ</a></div>' % RC['関東']
    b += door('関東')
    b += '<div class="grid">' + ''.join(cell(a) for a in L) + '</div>'
    for nm, cd in (('羽田のターミナル', 'HND'), ('成田のターミナル', 'NRT')):
        b += '<div class="sec-h">%s<small>0 / 3</small></div><div class="grid">' % nm
        for t in (1, 2, 3):
            b += '<div class="ap no" style="--c:%s"><span class="cd">%s<span style="font-size:16px;color:var(--sub)"> T%d</span></span><span class="nm">第%dターミナル</span><span class="ft">%s<span>まだ</span></span></div>' % (RC['関東'], cd, t, t, stamp(None, False, ''))
        b += '</div>'
    b += ('<div class="ann"><b>03 空港の並び：どの空港も同じ枠</b><ul><li>枠は全部同じ大きさ（幅いっぱいに3つ・高さ132）。並びは今と同じ北から南</li>'
          '<li>上から：3レターコード（大きく太く）→ 短い名前 → 印（✓の丸）と押した回数。コードのない空港（新島・神津島・調布）は名前を同じ位置に</li>'
          '<li>まだの空港も同じ枠・同じ場所に、薄い地とコード、点線の丸と「まだ」。名前は読める濃さ（4.5:1 以上）</li>'
          '<li>上に「関東 1/9」を止めておき、どの地方を見ているか分かるように。ツメの「関東」が飛び出す</li>'
          '<li>羽田・成田のターミナルは同じ枠で地方の並びのあとに（今と同じ数え方）</li><li>集めた枠を押すと 04（1空港の詳しい所）</li></ul></div>')
    b += '</div></div>' + tabs()
    page('03-airport-grid.html', '空港の並び', b, extra=ex)

# ---------- 04 1空港の詳しい所 ----------
def p04():
    ex = ('.idc{margin-top:12px;padding:18px;display:flex;gap:16px;align-items:center;position:relative;overflow:hidden}.idc::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--c)}'
          '.idc .big{font-family:var(--sign);font-weight:700;font-size:56px;line-height:1;color:var(--strong);letter-spacing:.02em}'
          '.idc h2{font-size:16px;margin:6px 0 0;color:var(--strong);line-height:1.4}.idc small{font-size:13px;color:var(--sub)}'
          '.cmp{margin-top:10px;padding:16px 16px 14px}.cmp h3,.rec h3{margin:0;font-size:15px;color:var(--strong)}.cmp .sub{font-size:13px;color:var(--sub)}'
          '.rw{display:grid;grid-template-columns:64px 1fr;align-items:center;gap:8px;margin-top:10px}.rw .k{font-size:13px;font-weight:700;color:var(--ink);line-height:1.3}'
          '.rw .tr{position:relative;height:26px}.rw .ln{position:absolute;left:0;top:9px;height:8px;border-radius:4px;background:var(--c)}.rw .ln.o{background:#8A93A0}'
          '.rw .vl{position:absolute;top:0;font-size:13px;font-weight:700;color:var(--strong);white-space:nowrap;padding-left:6px;line-height:26px}'
          '.sc{display:grid;grid-template-columns:64px 1fr;gap:8px;margin-top:8px}.sc div{display:flex;justify-content:space-between;font-size:12px;color:var(--mute)}'
          '.grp{font-size:13px;font-weight:700;color:var(--sub);margin-top:14px}'
          '.rec{margin-top:10px;padding:16px 0 8px}.rec h3{padding:0 16px}'
          '.turn{display:flex;gap:8px;margin-top:14px}.turn a{flex:1;justify-content:space-between}.turn .cd{font-family:var(--sign);font-size:18px;color:var(--strong)}')
    c = RC['関東']
    b = '<div class="wrap" style="--c:%s"><div class="top"><a class="pill" href="03-airport-grid.html">‹ 関東</a><a class="pill" href="05-legend-index.html">見方</a></div>' % c
    b += ('<section class="card idc"><svg viewBox="0 0 96 96" width="96" height="96" aria-label="羽田の印"><circle cx="48" cy="48" r="44" fill="none" stroke="#16233A" stroke-width="3"/><circle cx="48" cy="48" r="36" fill="none" stroke="#16233A" stroke-width="1.2"/>'
          '<text x="48" y="56" text-anchor="middle" font-family="Sign,Barlow Condensed,sans-serif" font-weight="700" font-size="26" fill="#16233A">HND</text><text x="48" y="72" text-anchor="middle" font-family="Sign,sans-serif" font-weight="600" font-size="9" fill="#16233A">2025.12.14</text></svg>'
          '<div><div class="big">HND</div><h2>東京国際空港（羽田）</h2><small>東京都・関東</small></div></section>')
    b += ('<div class="dl"><div><div class="k">開港</div><div class="v"><span class="num">1931</span><span class="u">年</span></div></div>'
          '<div><div class="k">滑走路</div><div class="v"><span class="num">4</span><span class="u">本</span></div></div>'
          '<div><div class="k">押した回数</div><div class="v"><span class="num">28</span><span class="u">回</span></div></div>'
          '<div><div class="k">はじめて押した日</div><div class="v s"><span class="num">2025</span><span class="u">年</span><span class="num">12</span><span class="u">月</span><span class="num">14</span><span class="u">日</span></div></div></div>')
    # 大きさ比べ（同じ縮尺：3,400m = 全幅）
    MAX = 3400
    def rw(k, m, o=False):
        return '<div class="rw"><span class="k">%s</span><span class="tr"><i class="ln%s" style="width:%.1f%%"></i><span class="vl" style="left:%.1f%%">%s<span class="u">m</span></span></span></div>' % (k, ' o' if o else '', m / MAX * 70, m / MAX * 70, format(m, ','))
    b += '<section class="card cmp"><h3>大きさ比べ</h3><div class="sub">滑走路の長さ・同じ縮尺</div>'
    b += rw('C 滑走路', 3360) + rw('A 滑走路', 3000) + rw('B 滑走路', 2500) + rw('D 滑走路', 2500)
    b += '<div class="grp">押したほかの空港（いちばん長い滑走路）</div>'
    b += rw('新千歳', 3000, True) + rw('福岡', 2800, True) + rw('石垣', 2000, True)
    b += '<div class="sc"><span></span><div><span>0</span><span>1,000</span><span>2,000</span><span>3,000m</span></div></div></section>'
    b += ('<section class="card rec"><h3>押した記録</h3>'
          '<div class="row"><div class="tx"><b>2026年11月1日</b><small>28回目</small></div></div>'
          '<div class="row"><div class="tx"><b>2026年10月18日</b><small>27回目</small></div></div>'
          '<div class="row"><div class="tx"><b>すべて見る</b><small>28回ぶん</small></div><span style="font-size:18px;color:var(--sub);font-weight:700">›</span></div></section>')
    b += '<div class="turn"><a class="pill" href="#">‹ <span class="cd">CHOFU</span>調布</a><a class="pill" href="#">大島 <span class="cd">OIM</span> ›</a></div>'
    b += ('<div class="ann"><b>04 1空港の詳しい所：データ欄と大きさ比べ</b><ul><li>上に印とコード（大きく太く）・空港名・都道府県と地方</li>'
          '<li>データ欄は4つのタイル：開港・滑走路の数・押した回数・はじめて押した日。数字は大きく太く、単位は小さく薄く</li>'
          '<li>大きさ比べ：羽田の滑走路と、押したほかの空港のいちばん長い滑走路を同じ縮尺の線で。羽田は地方の色、ほかは灰色</li>'
          '<li>いちばん下の「‹ 前／次 ›」は同じ地方の並び（北から南）。今の「案内標」の見方の、となりへ進む楽しさをここへ移す</li>'
          '<li>この下に今の「空港の今」「ターミナル」などがそのまま続く（変えない）</li>'
          '<li>開港の年・滑走路の長さは見本の値。本番にはこの表がまだないので、データ担当に出典つきの表を頼む（報告に書いた）</li></ul></div></div>')
    b = b.replace('<span class="cd">CHOFU</span>', '')
    b += tabs()
    page('04-airport.html', '1空港の詳しい所（羽田）', b, extra=ex)

# ---------- 05 凡例と索引 ----------
def p05():
    ex = ('.lg{margin-top:12px;padding:6px 0}.lg .row{min-height:60px}.lg .ic{width:48px;display:flex;justify-content:center;flex:none}'
          '.lt{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.lt a{min-width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-family:var(--sign);font-size:18px;font-weight:700;color:var(--strong);text-decoration:none}'
          '.ix{margin-top:10px;padding:4px 0}.ix .lh{font-family:var(--sign);font-weight:700;font-size:20px;color:var(--strong);padding:12px 16px 2px}'
          '.ix .row .cd{font-family:var(--sign);font-weight:700;font-size:20px;width:52px;color:var(--strong)}.ix .row.no .cd{color:#5F6875}.ix .row.no .tx b{color:var(--sub);font-weight:600}'
          '.ix .st{font-size:13px;color:var(--sub);font-weight:700}')
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:6px"><h1>見方と索引</h1></div>'
    b += '<div class="vband"><span class="pill on">見方</span><span class="pill">索引</span></div>'
    c = RC['関東']
    b += '<section class="card lg">'
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>✓の丸 … 印を押した空港</b><small>数字は押した回数</small></div></div>' % stamp(None, True, '', size=34)
    b += '<div class="row"><span class="ic">%s</span><div class="tx"><b>点線の丸 … まだの空港</b><small>同じ枠・同じ場所に薄く載せています</small></div></div>' % stamp(None, False, '', size=34)
    b += '<div class="row"><span class="ic"><svg width="34" height="34" viewBox="0 0 34 34"><circle cx="17" cy="17" r="6" fill="%s"/></svg></span><div class="tx"><b>扉の地図の ● ○</b><small>● 集めた　○ まだ（場所は北が上）</small></div></div>' % c
    b += '<div class="row"><span class="ic" style="gap:3px;flex-direction:column;align-items:center">' + ''.join('<i style="display:block;width:28px;height:4px;border-radius:2px;background:%s"></i>' % RC[r] for r in RN[:3]) + '</span><div class="tx"><b>色の帯 … 地方</b><small>右端のツメ・扉・枠の上の帯が同じ色</small></div></div>'
    b += '<div class="row"><span class="ic"><span class="num" style="font-size:22px">HND</span></span><div class="tx"><b>3レターコード</b><small>コードのない空港は名前を同じ位置に</small></div></div>'
    b += '</section><div class="note">この図鑑は国内の86空港と羽田・成田のターミナルです。飛行場・番外編・特別塗装機・実績は「別冊」にあります。</div>'
    # 索引
    b += '<div class="sec-h" style="margin-top:26px">索引<small>ABC順</small><span style="margin-left:auto;display:flex;gap:6px"><span class="pill on">ABC順</span><a class="pill" href="05b-index-kana.html">50音順</a></span></div>'
    L = sorted([a for a in A if a['code'] != '—'], key=lambda a: a['code'])
    letters = sorted(set(a['code'][0] for a in L))
    b += '<div class="lt">' + ''.join('<a href="#L%s">%s</a>' % (l, l) for l in letters) + '</div>'
    b += '<section class="card ix">'
    cur = ''
    for a in L:
        if a['code'][0] != cur:
            cur = a['code'][0]; b += '<div class="lh" id="L%s">%s</div>' % (cur, cur)
        g = GOT.get(a['code'])
        b += '<div class="row%s"><span class="cd">%s</span><div class="tx"><b>%s</b></div><span class="chip" style="--tc:%s">%s</span><span class="st">%s</span></div>' % (
            '' if g else ' no', a['code'], short(a), tint(RC[a['reg']], .16), a['reg'], ('%d回' % g) if g else 'まだ')
    b += '<div class="lh">コードのない空港</div>'
    for a in [a for a in A if a['code'] == '—']:
        b += '<div class="row no"><span class="cd" style="font-family:var(--gothic);font-size:15px">—</span><div class="tx"><b>%s</b></div><span class="chip" style="--tc:%s">%s</span><span class="st">まだ</span></div>' % (short(a), tint(RC[a['reg']], .16), a['reg'])
    b += '</section>'
    b += ('<div class="ann"><b>05 凡例と索引</b><ul><li>図鑑の右上「索引」と、1空港の「見方」から開く1枚。上のピルで「見方」と「索引」へ飛ぶ</li>'
          '<li>見方：印・まだ・扉の地図・地方の色・コードの5つだけ。レア・ノルマの言い方はしない</li>'
          '<li>索引：コードの ABC 順（頭の字のピルで飛ぶ）。50音順は 05b。名前の読みの表が要る（いまの本番にない）。行を押すとその空港の枠へ</li>'
          '<li>コードのない空港（新島・神津島・調布）は索引の最後にまとめる</li></ul></div></div>')
    b += tabs()
    page('05-legend-index.html', '凡例と索引', b, extra=ex)

# ---------- 06 別冊 ----------
def p06():
    ex = ('.bk{margin-top:10px;padding:16px 16px 14px;display:flex;gap:14px;align-items:center;text-decoration:none;color:inherit}'
          '.bk .sp{width:54px;height:72px;border-radius:10px 14px 14px 10px;flex:none;background:var(--b);box-shadow:inset 6px 0 0 rgba(0,0,0,.14);display:flex;align-items:center;justify-content:center;color:#fff}'
          '.bk .sp svg{width:26px;height:26px;fill:none;stroke:#fff;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}'
          '.bk .tx{flex:1;min-width:0}.bk b{display:block;font-size:17px;color:var(--strong);line-height:1.35}.bk small{display:block;font-size:13px;color:var(--sub);line-height:1.5;margin-top:2px}'
          '.bk .n{text-align:right;flex:none}.bk .n .num{font-size:28px}'
          '.base{margin-top:14px;padding:14px 16px;display:flex;align-items:center;gap:12px;background:var(--wash);border-radius:18px;box-shadow:inset 0 0 0 1px #E3E6EB}'
          '.base b{font-size:15px;color:var(--strong)}.base small{display:block;font-size:13px;color:var(--sub)}')
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:6px"><h1>別冊</h1></div>'
    b += '<div class="note" style="font-size:14px">空港の図鑑（86）とは別に数えます。ここで集めても「集めた空港」の数は変わりません。</div>'
    books = [('#3D7A4E', '<path d="M3 17h18M6 17l3-8h6l3 8M12 9V5"/>', '飛行場・滑空場', '定期便のない空港や小型機の飛行場、グライダーの滑空場', 0, 63, '滑空場 0/33・飛行場 0/30'),
             ('#2B4A73', '<path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7z"/>', '番外編', '自衛隊の飛行場と、一般の人が行けない飛行場', 0, 32, '自衛隊 0/27・一般の人が行けない 0/5'),
             ('#6B3FA0', '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.5 6.7 19.4l1.2-6L3.4 9.3l6-.7z"/>', '実績', '空港の印や回数・路線・距離で達成するもの', 21, 522, '飛行場・滑空場の実績 0/10 ほか'),
             ('#8A6A1F', '<path d="M10.5 13.5 4 11l1.5-1.5 7 1 3.5-3.5c1-1 2.5-1.2 3-.5s.5 2-.5 3L15 13l1 7-1.5 1.5-2.5-6.5-3 3v2.5L7.5 22 6 18l-4-1.5L3.5 15H6z"/>', '機体図鑑（特別塗装機）', '乗った・見た特別塗装機。空港の図鑑とは別物', 0, 93, '乗った 0・見た 0')]
    for col, ic, t, d, g, n, s in books:
        b += '<a class="card bk" href="#" style="--b:%s"><span class="sp"><svg viewBox="0 0 24 24">%s</svg></span><span class="tx"><b>%s</b><small>%s</small><small>%s</small></span><span class="n"><span class="num">%d</span><span class="u">/ %d</span></span></a>' % (col, ic, t, d, s, g, n)
    b += '<div class="base"><div><b>空港の図鑑</b><small>国内86空港＋羽田・成田のターミナル</small></div><span style="margin-left:auto" class="num">16<span class="u">/ 86</span></span></div>'
    b += ('<div class="ann"><b>06 番外編と実績の置き場：「別冊」の棚</b><ul><li>今は「86空港・飛行場・番外編・特別塗装・実績」が同じ段のピルに並び、実績は右にはみ出して見えない。空港の図鑑の一部に見える</li>'
          '<li>案：空港の図鑑の右上に「別冊」を1つだけ置き、開くと4冊の棚。背表紙の色は今の本番の色（飛行場の緑・番外編の紺・秘密の紫）。機体図鑑の色だけ新しい</li>'
          '<li>中身（飛行場・番外編の一覧、実績の一覧、特別塗装機）は今の画面のまま。そろえた枠に直すのは図鑑の基本が決まってから</li>'
          '<li>機体図鑑は特別塗装機だけ（決まりのとおり）。空港の図鑑の数には入れない</li></ul></div></div>')
    b += tabs()
    page('06-bessatsu.html', '別冊（番外編と実績の置き場）', b, extra=ex)

# ---------- 07 見方 ----------
def p07():
    b = tsume('北海道') + '<div class="wrap">' + header() + '<div class="main">' + titlerow() + vband() + hero() + door('北海道') + '</div></div>' + tabs()
    b += '<div class="dim"></div><section class="sheet"><div class="grab"></div><div style="display:flex;align-items:center"><b style="font-size:18px;color:var(--strong)">見方の帯</b><span style="margin-left:auto;font-size:13px;color:var(--sub);font-weight:700">3つ</span></div>'
    b += '<div class="note" style="margin-top:2px">OFF で帯から隠れます。</div>'
    rows = [('図鑑', '地方ごとの並び（基本）', None), ('地図', '集めた空港を地図で', 'on'), ('行った順', 'はじめて押した日の順（今の年代記）', 'on')]
    for t, s, st in rows:
        right = '<span style="font-size:13px;color:var(--sub);font-weight:700">いつも</span>' if st is None else '<span class="sw %s">%s</span>' % (st, st.upper())
        b += '<div class="row" style="padding:6px 2px;min-height:60px"><div class="tx"><b>%s</b><small>%s</small></div>%s</div>' % (t, s, right)
    b += '<div class="sec-h" style="margin-top:12px;font-size:14px">まとめた見方</div>'
    for t, s in [('タイル', '→ 図鑑そのもの（地方ごとの並び）'), ('地方', '→ 各地方の扉（数と進み具合）'), ('案内標', '→ 1空港の「‹ 前／次 ›」')]:
        b += '<div class="row" style="padding:4px 2px;min-height:48px"><div class="tx"><b>%s</b><small>%s</small></div></div>' % (t, s)
    b += '<div class="btn">完了</div></section>'
    page('07-views.html', '見方をどうするか', b)
    # 07 の説明（シートの外）は一覧に書く

# ---------- 01 今の見にくい所 ----------
def p01():
    ex = ('.shot{position:relative;margin-top:12px;border-radius:22px;overflow:hidden;box-shadow:var(--shadow)}.shot img{display:block;width:100%}'
          '.mk{position:absolute;width:28px;height:28px;border-radius:50%;background:#C2410C;color:#fff;font:800 15px/28px var(--gothic);text-align:center;box-shadow:0 0 0 3px #fff}'
          '.box{position:absolute;border:3px solid #C2410C;border-radius:14px}'
          '.iss{margin-top:12px;padding:6px 0}.iss .row{align-items:flex-start;padding:10px 16px}.iss .mk{position:static;flex:none;margin-top:2px}'
          '.two{display:grid;grid-template-columns:1fr 1fr;gap:8px}.two .shot{margin-top:8px}.cap{font-size:13px;color:var(--sub);font-weight:700;margin:6px 2px 0}')
    b = '<div class="wrap"><div class="ttl" style="margin-top:10px"><h1 style="font-size:22px">今の図鑑の見にくい所</h1></div>'
    b += '<div class="note">main の web/ をデモで開き、390×844 で撮った写真（タイルの見方）</div>'
    b += ('<div class="shot"><img src="%s" alt="今の図鑑（タイルの見方）">'
          '<span class="box" style="left:20%%;top:21.6%%;width:79%%;height:6.8%%"></span><span class="mk" style="left:2%%;top:22.6%%">1</span>'
          '<span class="box" style="left:3%%;top:29.4%%;width:85%%;height:5%%"></span><span class="mk" style="left:89%%;top:30%%">2</span>'
          '<span class="box" style="left:4%%;top:55.5%%;width:92%%;height:31.5%%"></span><span class="mk" style="left:86%%;top:52.5%%">3</span>'
          '<span class="mk" style="left:8%%;top:88%%">4</span></div>') % img64('sh-tile.jpg')
    b += '<section class="card iss">'
    iss = [('切り替えが2段で、どれが基本か分からない', '上の段は「86空港・飛行場・番外編・特別塗装・実績」の5つ、下の段は「地図・案内標・タイル・年代記・地方」の5つ。「実績」は右にはみ出して見えない'),
           ('見方ごとに形も大きさも変わる', '案内標は1空港が画面の4分の1（86空港で 11,869px の長さ）、タイルは丸い印、年代記は行った所だけ。同じ空港を見比べられない'),
           ('空港が地方のタイルの奥に隠れている', 'タイルの見方では、地方を押すまで空港が出ない。86空港を一度に見渡せず、ほかの地方へ移るには上まで戻る'),
           ('まだの空港が何の空港か分からない・中身が少ない', 'まだの空港は名前とコードが薄い丸だけ。行った空港も印と回数だけで、開港や滑走路など図鑑らしい中身がない'),
           ('空港の図鑑と別の物が同じ段に並ぶ', '特別塗装（機体図鑑）と実績が空港の図鑑と同じピルの段にあり、空港の図鑑の一部に見える')]
    for i, (t, s) in enumerate(iss, 1):
        b += '<div class="row"><span class="mk">%d</span><div class="tx"><b>%s</b><small>%s</small></div></div>' % (i, t, s)
    b += '</section>'
    b += ('<div class="two"><div><div class="shot"><img src="%s" alt="案内標の見方"><span class="mk" style="left:6%%;top:40%%">2</span></div><div class="cap">案内標：1画面に3空港半</div></div>'
          '<div><div class="shot"><img src="%s" alt="地方を開いたところ"><span class="mk" style="left:6%%;top:30%%">4</span></div><div class="cap">地方を開いたところ：まだは薄い丸</div></div></div>') % (img64('sh-annai.jpg'), img64('sh-open.jpg'))
    b += '<div class="ann"><b>01 の見方</b><ul><li>橙の丸の番号は下の一覧の番号。写真は今の本番（main）をデモで撮ったもの</li><li>5（特別塗装・実績）は写真の右上、はみ出した所</li></ul></div></div>'
    page('01-now-problems.html', '今の図鑑の見にくい所', b, extra=ex)

for f in (p01, p03, p04, p05, p06, p07):
    f()
p02(False); p02(True)

# ---------- 一覧 ----------
items = [('01-now-problems', '01 今の図鑑の見にくい所', '今の本番の写真に番号。見にくい所5つ'),
         ('02-zukan-base', '02 図鑑の基本', 'ツメ（9地方）＋地方の扉＋空港の並び。切り替えは見方の帯1段'),
         ('02-zukan-base-night', '02 図鑑の基本（夜）', '夜の画面の色。ツメは色なし・光るのは集めた数だけ'),
         ('03-airport-grid', '03 空港の並び', '関東へ飛んだところ。どの空港も同じ枠、まだも同じ枠で薄く'),
         ('04-airport', '04 1空港の詳しい所（羽田）', 'データ欄4つ・大きさ比べ（同じ縮尺）・押した記録・‹ 前／次 ›'),
         ('05-legend-index', '05 凡例と索引', '見方5つと、コードの ABC 順の索引'),
         ('05b-index-kana', '05b 索引（50音順）', '短い名前の読みで、あ〜わの行ごと'),
         ('06-bessatsu', '06 番外編と実績の置き場', '「別冊」の棚に4冊。空港の図鑑の数とは別'),
         ('07-views', '07 今の5つの見方をどうするか', '帯は「図鑑・地図・行った順」の3つ。タイル・地方・案内標はまとめる')]
ix = '<div class="wrap"><div class="ttl"><h1 style="font-size:22px">図鑑を見やすく（画面案）</h1></div><div class="note">ブランチ design/zukan-book。11/9 12時10分の PM の指示（本人「図鑑が見にくいので、実際の図鑑を調べて参考に」）。アプリのコードは変えていない。幅390で見る。</div>'
ix += '<section class="card" style="margin-top:12px;padding:4px 0">'
for f, t, d in items:
    ix += '<a class="row" href="%s.html" style="text-decoration:none;min-height:64px"><div class="tx"><b>%s</b><small>%s</small></div><span style="font-size:18px;color:var(--sub);font-weight:700">›</span></a>' % (f, t, d)
ix += '</section>'
ix += ('<div class="sec-h">紙の図鑑から借りた工夫</div><section class="card" style="margin-top:10px;padding:12px 16px;font-size:14px;line-height:1.7">'
       '<b>1. ツメ</b>：右端に9地方。押すと扉へ（02・03）<br><b>2. 見せ方をそろえる</b>：全空港を同じ枠・同じ大きさ（03）<br><b>3. なかまの見開き</b>：地方ごとの扉→並び（02）<br>'
       '<b>4. データ欄</b>：コード・名前・開港・滑走路・押した日と回数（04）<br><b>5. まだも同じ枠</b>：薄い地と点線の丸（03）<br><b>6. 凡例と索引</b>（05）<br><b>7. 大きさ比べ</b>：滑走路を同じ縮尺の線で（04）</section>')
ix += ('<div class="sec-h">07 の考え方（今→案）</div><section class="card" style="margin-top:10px;padding:12px 16px;font-size:14px;line-height:1.7">'
       '地図 → 残す（帯）<br>年代記 → 「行った順」と名前を変えて残す（帯）<br>タイル → 図鑑そのもの（基本）<br>地方 → 各地方の扉に入れる<br>案内標 → 1空港の「‹ 前／次 ›」へ<br>'
       '帯の出す・隠すは 11/8・11/9 の決定どおり見方の帯の ✎ から ON／OFF。図鑑はいつも出す</section>')
ix += '<div class="note" style="margin:14px 2px 40px">PNG：png/ に各画面の 390×844 と 390×667（*-667.png）、長い画面は全体（*-full.png）。</div></div>'
page('index.html', '一覧', ix)
print('ok')

# ---------- 05b 索引（50音順） ----------
YOMI = dict(成田='なりた',中部='ちゅうぶ',関西='かんさい',伊丹='いたみ',羽田='はねだ',新千歳='しんちとせ',稚内='わっかない',釧路='くしろ',函館='はこだて',仙台='せんだい',新潟='にいがた',広島='ひろしま',高松='たかまつ',松山='まつやま',高知='こうち',福岡='ふくおか',北九州='きたきゅうしゅう',長崎='ながさき',熊本='くまもと',大分='おおいた',宮崎='みやざき',鹿児島='かごしま',那覇='なは',旭川='あさひかわ',帯広='おびひろ',秋田='あきた',山形='やまがた',山口宇部='やまぐちうべ',利尻='りしり',奥尻='おくしり',中標津='なかしべつ',紋別='もんべつ',女満別='めまんべつ',青森='あおもり',花巻='はなまき',大館能代='おおだてのしろ',庄内='しょうない',福島='ふくしま',大島='おおしま',新島='にいじま',神津島='こうづしま',三宅島='みやけじま',八丈島='はちじょうじま',佐渡='さど',富山='とやま',能登='のと',松本='まつもと',静岡='しずおか',神戸='こうべ',南紀白浜='なんきしらはま',鳥取='とっとり',隠岐='おき',出雲='いずも',石見='いわみ',岡山='おかやま',佐賀='さが',対馬='つしま',福江='ふくえ',壱岐='いき',種子島='たねがしま',屋久島='やくしま',奄美='あまみ',喜界='きかい',徳之島='とくのしま',沖永良部='おきのえらぶ',与論='よろん',粟国='あぐに',久米島='くめじま',南大東='みなみだいとう',北大東='きただいとう',宮古='みやこ',下地島='しもじしま',多良間='たらま',石垣='いしがき',与那国='よなぐに',調布='ちょうふ',小牧='こまき',但馬='たじま',天草='あまくさ',札幌丘珠='さっぽろおかだま',三沢='みさわ',茨城='いばらき',小松='こまつ',米子='よなご',岩国='いわくに',徳島='とくしま')
GYO = [('あ','あいうえお'),('か','かきくけこがぎぐげご'),('さ','さしすせそざじずぜぞ'),('た','たちつてとだぢづでど'),('な','なにぬねの'),('は','はひふへほばびぶべぼぱぴぷぺぽ'),('ま','まみむめも'),('や','やゆよ'),('ら','らりるれろ'),('わ','わをん')]
def p05b():
    ex = ('.lt{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}.lt a{min-width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:16px;font-weight:800;color:var(--strong);text-decoration:none}'
          '.ix{margin-top:10px;padding:4px 0}.ix .lh{font-weight:800;font-size:18px;color:var(--strong);padding:12px 16px 2px}.ix .lh small{font-size:13px;color:var(--sub);font-weight:700;margin-left:8px}'
          '.ix .row .tx small{font-size:13px}.ix .row .cd{font-family:var(--sign);font-weight:700;font-size:18px;width:46px;color:var(--strong);text-align:right}.ix .row.no .cd{color:#5F6875}.ix .row.no .tx b{color:var(--sub);font-weight:600}'
          '.ix .st{font-size:13px;color:var(--sub);font-weight:700;width:36px;text-align:right}')
    missing = [short(a) for a in A if short(a) not in YOMI]
    assert not missing, missing
    L = sorted(A, key=lambda a: YOMI[short(a)])
    b = '<div class="wrap"><div class="top"><a class="pill" href="02-zukan-base.html">‹ 図鑑</a></div><div class="ttl" style="margin-top:6px"><h1>見方と索引</h1></div>'
    b += '<div class="vband"><a class="pill" href="05-legend-index.html">見方</a><span class="pill on">索引</span></div>'
    b += '<div class="sec-h" style="margin-top:18px">索引<small>50音順</small><span style="margin-left:auto;display:flex;gap:6px"><a class="pill" href="05-legend-index.html#LA">ABC順</a><span class="pill on">50音順</span></span></div>'
    groups = []
    for g, ks in GYO:
        m = [a for a in L if YOMI[short(a)][0] in ks]
        if m: groups.append((g, m))
    b += '<div class="lt">' + ''.join('<a href="#K%s">%s</a>' % (g, g) for g, _ in groups) + '</div><section class="card ix">'
    for g, m in groups:
        b += '<div class="lh" id="K%s">%s行<small>%d空港</small></div>' % (g, g, len(m))
        for a in m:
            gt = GOT.get(a['code'])
            b += '<div class="row%s"><div class="tx"><b>%s</b><small>%s</small></div><span class="chip" style="--tc:%s">%s</span><span class="cd">%s</span><span class="st">%s</span></div>' % (
                '' if gt else ' no', short(a), YOMI[short(a)], tint(RC[a['reg']], .16), a['reg'], a['code'] if a['code'] != '—' else '—', ('%d回' % gt) if gt else 'まだ')
    b += '</section>'
    b += ('<div class="ann"><b>05b 索引（50音順）</b><ul><li>05 の「50音順」を押したところ。行（あ〜わ）のピルで飛ぶ</li>'
          '<li>名前は図鑑の枠と同じ短い名前（羽田・伊丹・小牧など）で並べ、下に読みを出す。コードのない空港（新島・神津島・調布）もここでは混ぜて並ぶ</li>'
          '<li>読みは画面案のために書いた。本番では空港の表に読みの列が要る（データ担当）</li></ul></div></div>')
    b += tabs()
    page('05b-index-kana.html', '索引（50音順）', b, extra=ex)
p05b()
