# -*- coding: utf-8 -*-
# 「機体ごとの運航の実績」（機体の1週間）の画面案を組み立てる
# base.css（design/board-timetable から写した共通の見た目＝main の web/index.html の色と文字。地 #EEF1F5）を各ページに埋め込み、外部の読み込みなしで開ける HTML にする
# 機体・便・時刻はすべて見本（実在の機体のその週の実績ではない）。地図の輪郭は src/index.html の JP_OUTLINE をそのまま使う
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from icons import P
from jp import JP_OUTLINE, proj
OUT = os.path.dirname(HERE)
CSS = open(HERE + '/base.css', encoding='utf-8').read()
P.update({
 'down': '<path d="M6 9l6 6 6-6"/>',
 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
 'expand': '<path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/>',
 'star': '<path d="M12 4l2.4 5 5.4.6-4 3.7 1.1 5.4L12 16l-4.9 2.7 1.1-5.4-4-3.7 5.4-.6z"/>',
 'cam': '<path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
 'week': '<rect x="4" y="5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>',
})
def ic(name, cls='ic'):
    return '<svg class="%s i-%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, name, P[name])

TABS = [('home', 'ホーム', 'home'), ('book', '図鑑', 'book'), ('log', 'フライト', 'plane'), ('now', 'いまの空港', 'ops'), ('me', 'マイページ', 'user')]
def tabbar(cur='now'):
    out = ['<nav class="tabs" aria-label="下のタブ">']
    for k, lb, icn in TABS:
        on = k == cur
        out.append('<button type="button"%s>%s<span>%s</span>%s</button>' % (
            ' aria-current="page"' if on else '', ic(icn), lb, '<i class="dt"></i>' if on else ''))
    out.append('</nav>')
    return ''.join(out)

# ── 空港（見本で使うものだけ） ──
AP = {'HND': ('羽田', 35.549, 139.780), 'FUK': ('福岡', 33.585, 130.451), 'CTS': ('新千歳', 42.775, 141.692),
      'OKA': ('那覇', 26.196, 127.646), 'ITM': ('伊丹', 34.785, 135.438), 'KOJ': ('鹿児島', 31.803, 130.719),
      'UKB': ('神戸', 34.632, 135.224), 'ISG': ('石垣', 24.396, 124.245)}

def hm(t):
    return '%d:%02d' % (t // 60 % 24, t % 60)
def tm(s):
    h, m = s.split(':'); return int(h) * 60 + int(m)
def dur(m):
    return '%d<span class="u">時間</span>%02d<span class="u">分</span>' % (m // 60, m % 60) if m >= 60 else '%d<span class="u">分</span>' % m

# ── 見本の1週間（JA01XJ・A350-900）── (定刻, 実際, 便名, 出発, 到着, 飛んだ分, 元)  元：odpt＝時刻表と運航情報で確かめた便／est＝機体の位置の記録だけ（推定）
DAYS = [
 ('d21', '11月21日', '土', [('06:35', '06:38', 'JL 301', 'HND', 'FUK', 115, 'odpt'), ('09:10', '09:14', 'JL 306', 'FUK', 'HND', 95, 'odpt'),
                          ('11:30', '11:52', 'JL 907', 'HND', 'OKA', 160, 'odpt'), ('15:15', '15:40', 'JL 912', 'OKA', 'HND', 140, 'odpt'),
                          ('19:00', '19:20', 'JL 517', 'HND', 'CTS', 95, 'odpt')]),
 ('d22', '11月22日', '日', [('07:00', '07:03', 'JL 503', 'CTS', 'HND', 100, 'odpt'), ('09:30', '09:31', 'JL 309', 'HND', 'FUK', 115, 'odpt'),
                          ('12:20', '12:26', 'JL 314', 'FUK', 'HND', 95, 'odpt'), ('14:45', '14:50', 'JL 125', 'HND', 'ITM', 70, 'odpt'),
                          ('17:30', '17:33', 'JL 132', 'ITM', 'HND', 65, 'odpt'), ('19:30', '19:32', 'JL 519', 'HND', 'CTS', 95, 'odpt')]),
 ('d23', '11月23日', '月', []),
 ('d24', '11月24日', '火', [('08:00', '08:02', 'JL 504', 'CTS', 'HND', 100, 'odpt'), ('11:40', '11:44', 'JL 903', 'HND', 'OKA', 160, 'odpt'),
                          ('15:10', '15:11', 'JL 908', 'OKA', 'HND', 140, 'odpt'), ('18:55', '18:58', 'JL 333', 'HND', 'FUK', 115, 'odpt')]),
 ('d25', '11月25日', '水', [('', '06:41', 'JL 302', 'FUK', 'HND', 95, 'est'), ('09:20', '09:26', 'JL 505', 'HND', 'CTS', 95, 'odpt'),
                          ('12:10', '12:11', 'JL 510', 'CTS', 'HND', 100, 'odpt'), ('15:00', '15:18', 'JL 323', 'HND', 'FUK', 115, 'odpt'),
                          ('18:20', '18:22', 'JL 328', 'FUK', 'HND', 95, 'odpt')]),
 ('d26', '11月26日', '木', [('06:45', '06:47', 'JL 501', 'HND', 'CTS', 95, 'odpt'), ('09:15', '09:15', 'JL 506', 'CTS', 'HND', 100, 'odpt'),
                          ('11:55', '12:00', 'JL 911', 'HND', 'OKA', 160, 'odpt'), ('15:20', '15:26', 'JL 916', 'OKA', 'HND', 140, 'odpt'),
                          ('19:05', '19:06', 'JL 335', 'HND', 'FUK', 115, 'odpt'), ('', '21:52', 'JL 340', 'FUK', 'HND', 95, 'est')]),
 ('d27', '11月27日', '金', [('06:30', '06:33', 'JL 301', 'HND', 'FUK', 115, 'odpt'), ('09:05', '09:12', 'JL 306', 'FUK', 'HND', 95, 'odpt'),
                          ('12:00', '12:16', 'JL 905', 'HND', 'OKA', 160, 'live')]),
]
NOW = tm('14:22')
TODAY = 'd27'

# 推定だけの機体（ODPT にない会社。全機の記録 adsb.lol だけ）── (いつもの時刻, 離陸ごろ, 便名, 出発, 到着, 飛んだ分)
EST_DAYS = [
 ('e24', '11月24日', '火', [('07:05', '07:12', 'BC 3', 'HND', 'FUK', 110), ('10:00', '10:21', 'BC 8', 'FUK', 'HND', 90), ('13:35', '13:38', 'BC 301', 'HND', 'KOJ', 100), ('16:30', '16:34', 'BC 306', 'KOJ', 'HND', 85)]),
 ('e25', '11月25日', '水', [('07:30', '07:31', 'BC 101', 'UKB', 'HND', 65), ('09:50', '09:58', 'BC 102', 'HND', 'UKB', 70), ('12:30', '12:44', 'BC 513', 'UKB', 'HND', 65)]),
 ('e26', '11月26日', '木', []),
 ('e27', '11月27日', '金', [('07:05', '07:09', 'BC 3', 'HND', 'FUK', 110), ('10:00', '10:06', 'BC 8', 'FUK', 'HND', 90)]),
]

def week_stats(days):
    n = sum(len(d[3]) for d in days)
    fm = sum(l[5] for d in days for l in d[3])
    late = sum(1 for d in days for l in d[3] if l[0] and tm(l[1]) - tm(l[0]) >= 15)
    est = sum(1 for d in days for l in d[3] if l[6] == 'est')
    return n, fm, late, est

def chain(legs):
    if not legs: return ''
    codes = [legs[0][3]] + [l[4] for l in legs]
    return '<span class="chain">' + '<i>→</i>'.join('<b>%s</b>' % AP[c][0] for c in codes) + '</span>'

def row(l, today=False):
    sch, act, fl, a, b, m, src = l
    al, no = fl.split(' ')
    arr = hm(tm(act) + m)
    if src == 'est':
        t = '<b class="num">%s</b><small>ごろ 離陸</small>' % act
        st = '<span class="st est">推定</span>'
    else:
        d = tm(act) - tm(sch)
        cls = ' late' if d >= 15 else ''
        t = '<b class="num">%s</b><small class="act%s">実際 <span class="num">%s</span></small>' % (sch, cls, act)
        if src == 'live':
            st = '<span class="st live"><i></i>飛行中</span>'
        elif d <= 0:
            st = '<span class="st ok">定刻</span>'
        else:
            st = '<span class="st%s">+<span class="num">%d</span>分</span>' % (' late' if d >= 15 else '', d)
    arrt = ('着 <span class="num">%s</span> の見込み' % arr) if src == 'live' else ('着 <span class="num">%s</span>%s' % (arr, 'ごろ' if src == 'est' else ''))
    return ('<li class="lr s-%s"><span class="c-t">%s</span><span class="c-no"><small>%s</small><b class="num">%s</b></span>'
            '<span class="c-rt"><b>%s<i>→</i>%s</b><small>%s</small></span><span class="c-st">%s</span></li>'
            % (src, t, al, no, AP[a][0], AP[b][0], arrt, st))

def day_card(d, open_=True):
    key, date, wd, legs = d
    n = len(legs); fm = sum(l[5] for l in legs)
    tag = '<span class="tday">今日</span>' if key == TODAY else ''
    if not legs:
        return ('<section class="day empty" id="%s"><div class="dh"><span class="dd"><b>%s</b><small>%s</small></span><span class="dn">飛んだ記録なし</span></div>'
                '<p class="dnote">この日に飛んだ記録はありません。整備や予備の日かもしれませんが、そらメモでは推しはかりません。</p></section>' % (key, date, wd))
    head = ('<span class="dd"><b>%s</b><small>%s</small>%s</span><span class="dn"><b class="num">%d</b><span class="u">便</span>'
            '<span class="sep"></span><span class="u">飛んだ時間</span> <b class="num">%s</b></span>' % (date, wd, tag, n, dur(fm)))
    if not open_:
        return ('<section class="day fold" id="%s"><button type="button" class="dh" aria-expanded="false" data-fold>%s%s</button>'
                '<div class="dch">%s</div><ul class="lrs" hidden>%s</ul></section>' % (key, head, ic('down', 'ic dv'), chain(legs), ''.join(row(l) for l in legs)))
    more = ''
    if key == TODAY:
        more = '<button type="button" class="pmore">この先の2便は「今日」で（予想）%s</button>' % ic('chev')
    return ('<section class="day" id="%s"><button type="button" class="dh" aria-expanded="true" data-fold>%s%s</button>'
            '<div class="dch">%s</div><ul class="lrs">%s</ul>%s</section>' % (key, head, ic('down', 'ic dv'), chain(legs), ''.join(row(l, key == TODAY) for l in legs), more))

# ── 紺の地図：1週間の道すじ（同じ区間はすこしずつずらして重ね、航路の跡のように残す） ──
VB = (64, 52, 244, 330)
def leg_paths(days, est_all=False):
    seen = {}
    out = []
    order = [d[0] for d in days]
    for d in days:
        key = d[0]
        age = order[::-1].index(key)
        for l in d[3]:
            a, b = l[3], l[4]
            src = 'est' if est_all else l[6]
            k = tuple(sorted([a, b])); i = seen.get(k, 0); seen[k] = i + 1
            x1, y1 = proj(AP[a][1], AP[a][2]); x2, y2 = proj(AP[b][1], AP[b][2])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1; L = (dx * dx + dy * dy) ** .5 or 1
            sgn = 1 if (a, b) == k else -1
            off = (6 + i * 2.2) * sgn
            cx, cy = mx - dy / L * off, my + dx / L * off
            out.append('<path class="lg %s age%d%s" d="M%.1f %.1fQ%.1f %.1f %.1f %.1f"/>' % (key, min(age, 4), ' est' if src == 'est' else '', x1, y1, cx, cy, x2, y2))
    return ''.join(out)

def svg_map(days, big=False, est_all=False, sel=''):
    codes = set()
    cnt = {}
    for d in days:
        for l in d[3]:
            codes.update([l[3], l[4]])
            for c in (l[3], l[4]): cnt[c] = cnt.get(c, 0) + 1
    grid = []
    for lat in range(26, 46, 2):
        _, y = proj(lat, 130); grid.append('<path d="M40 %.1fH340"/>' % y)
    for lon in range(124, 148, 2):
        x, _ = proj(36, lon); grid.append('<path d="M%.1f 0V420"/>' % x)
    pts = []
    for c in sorted(codes, key=lambda c: -cnt[c]):
        x, y = proj(AP[c][1], AP[c][2])
        lx, anc = (x + 7, 'start') if c not in ('FUK', 'KOJ', 'UKB', 'ITM', 'CTS') else (x - 7, 'end')
        ly = y + 4 if c != 'ITM' else y - 5
        lab = AP[c][0] + ('<tspan class="ct"> %d</tspan>' % cnt[c] if big else '')
        pts.append('<circle class="apd" cx="%.1f" cy="%.1f" r="%s"/><text class="apl" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                   % (x, y, 3.2 if c == 'HND' else 2.6, lx, ly, anc, lab))
    return ('<svg class="wmap%s" viewBox="%d %d %d %d" role="img" aria-label="1週間に飛んだ道すじの地図"%s>'
            '<g class="grid">%s</g><path class="land" d="%s"/><g class="legs">%s</g>%s</svg>'
            % (' big' if big else '', VB[0], VB[1], VB[2], VB[3], (' data-sel="%s"' % sel) if sel else '', ''.join(grid), JP_OUTLINE, leg_paths(days, est_all), ''.join(pts)))

def map_preview(days, est_all=False):
    cnt = {}
    for d in days:
        for l in d[3]:
            k = '%s–%s' % tuple(AP[c][0] for c in sorted([l[3], l[4]], key=lambda c: c != 'HND'))
            cnt[k] = cnt.get(k, 0) + 1
    top = sorted(cnt.items(), key=lambda x: -x[1])[:4]
    lst = ''.join('<li><span>%s</span><b class="num">%d</b><span class="u2">回</span></li>' % (k, v) for k, v in top)
    return ('<section class="mapc"><div class="mw">%s</div><div class="ms"><b class="mt">よく飛んだ区間</b><ul>%s</ul>'
            '<p class="mleg"><i class="ln now"></i>今日<br><i class="ln old"></i>前の日ほど薄く<br><i class="ln dash"></i>推定</p></div>'
            '<button type="button" class="mbig">%s地図を大きく</button></section>' % (svg_map(days, est_all=est_all), lst, ic('expand')))

PAGE_CSS = r'''
body{padding:0 16px 132px}
.tabs{position:fixed;left:50%;bottom:14px;width:calc(100% - 28px);max-width:402px;transform:translateX(-50%);z-index:20}
.tabs button{position:relative}
.tabs button span{white-space:nowrap;letter-spacing:-.03em}
.tabs .dt{position:absolute;bottom:7px;left:50%;width:5px;height:5px;margin-left:-2.5px;border-radius:50%;background:var(--acc)}
.top{display:flex;align-items:center;gap:8px;padding:16px 0 6px}
.back{display:inline-flex;align-items:center;gap:2px;min-height:44px;padding:0 14px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:800;color:var(--strong)}
.back svg{width:20px;height:20px}
.top h1{flex:1;text-align:center;font-size:17px;margin-right:52px}
.reg{display:flex;align-items:flex-end;justify-content:space-between;gap:10px;margin-top:10px;padding:18px 18px 16px}
.reg .rn{font-size:30px;font-weight:800;letter-spacing:.02em;color:var(--strong);line-height:1.1;font-variant-numeric:tabular-nums}
.reg small{display:block;margin-top:4px;font-size:13px;color:var(--sub);font-weight:600}
.reg .lv{display:inline-flex;align-items:center;gap:4px;margin-top:6px;padding:2px 10px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--strong)}
.reg .lv svg{width:14px;height:14px}
.fly{display:inline-flex;align-items:center;gap:6px;min-height:30px;padding:0 12px;border-radius:999px;background:var(--strong);color:#fff;font-size:12px;font-weight:800;white-space:nowrap}
.fly i{width:7px;height:7px;border-radius:50%;background:#86EFAC}
:root[data-night=on] .fly{background:rgba(74,222,128,.14);color:#4ADE80}
:root[data-night=on] .fly i{background:#4ADE80}
.seg{display:flex;margin-top:12px;padding:4px;border-radius:999px;background:var(--pill)}
.seg button{flex:1;min-height:44px;border-radius:999px;font-size:14px;font-weight:800;color:var(--sub)}
.seg button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.sum{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.sum .k{padding:14px 16px}
.sum .k small{display:block;font-size:12px;color:var(--mute);font-weight:700}
.sum .k b{font-size:26px;line-height:1.2}
.sum .k .u{font-size:12px}
.sum .k.w{grid-column:1/-1;display:flex;align-items:baseline;justify-content:space-between}
.sum .k.w small{display:inline}
.rng{margin-top:14px;display:flex;align-items:baseline;justify-content:space-between}
.rng b{font-size:15px;font-weight:800;color:var(--strong)}
.rng span{font-size:12px;color:var(--mute);font-weight:700}

/* 紺の地図（広報の動画と同じ紺：#0E1E36。夜は #0B1626） */
.mapc{position:relative;display:grid;grid-template-columns:52% 1fr;gap:6px;margin-top:12px;padding:12px 12px 64px;border-radius:22px;background:#0E1E36;color:#F5F7FA;box-shadow:0 10px 30px -10px rgba(14,30,54,.45)}
:root[data-night=on] .mapc,:root[data-night=on] .mapl{background:#0B1626;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}
.mw{min-height:0}
.wmap{display:block;width:100%;height:auto}
.wmap .grid path{stroke:rgba(169,183,203,.10);stroke-width:.5;fill:none}
.wmap .land{fill:#1A2E4C;stroke:#3B5578;stroke-width:.7;stroke-linejoin:round}
.wmap .lg{fill:none;stroke:#F5F7FA;stroke-width:1.15;stroke-linecap:round;opacity:.22}
.wmap .lg.age1{opacity:.5}.wmap .lg.age2{opacity:.34}.wmap .lg.age3{opacity:.26}.wmap .lg.age4{opacity:.2}
.wmap .lg.age0{stroke:#FFD23F;opacity:1;stroke-width:1.6}
.wmap .lg.est{stroke-dasharray:3 2.6}
.wmap .apd{fill:#F5F7FA;stroke:#0E1E36;stroke-width:1}
.wmap .apl{fill:#DCE3EA;font-size:12px;font-weight:800;font-family:var(--gothic);paint-order:stroke;stroke:#0E1E36;stroke-width:3px;stroke-linejoin:round}
.wmap .apl .ct{fill:#A9B7CB;font-weight:700;font-size:11px}
.wmap:not(.big) .apl{font-size:14px}
:root[data-night=on] .wmap .lg.age0{stroke:#4ADE80}
:root[data-night=on] .wmap .land{fill:#15243A;stroke:#2F4664}
:root[data-night=on] .wmap .apd,:root[data-night=on] .wmap .apl{stroke:#0B1626}
.wmap[data-sel] .lg{opacity:.1;stroke:#F5F7FA;stroke-width:1.15}
.wmap[data-sel=d21] .lg.d21,.wmap[data-sel=d22] .lg.d22,.wmap[data-sel=d24] .lg.d24,.wmap[data-sel=d25] .lg.d25,.wmap[data-sel=d26] .lg.d26,.wmap[data-sel=d27] .lg.d27{opacity:1;stroke:#FFD23F;stroke-width:1.8}
:root[data-night=on] .wmap[data-sel] .lg[class*=d2]:not(.age9){}
:root[data-night=on] .wmap[data-sel=d21] .lg.d21,:root[data-night=on] .wmap[data-sel=d22] .lg.d22,:root[data-night=on] .wmap[data-sel=d24] .lg.d24,:root[data-night=on] .wmap[data-sel=d25] .lg.d25,:root[data-night=on] .wmap[data-sel=d26] .lg.d26,:root[data-night=on] .wmap[data-sel=d27] .lg.d27{stroke:#4ADE80}
.ms{display:flex;flex-direction:column;gap:8px;padding:4px 2px 0 4px}
.mt{font-size:12px;font-weight:800;color:#A9B7CB;letter-spacing:.04em}
.ms ul{list-style:none;display:flex;flex-direction:column;gap:6px}
.ms li{display:flex;align-items:baseline;gap:2px;font-size:13px;font-weight:700;color:#F5F7FA}
.ms li span:first-child{flex:1;white-space:nowrap}
.ms li .num{color:#fff;font-size:17px}
.ms .u2{font-size:12px;color:#A9B7CB;font-weight:600}
.mleg{margin-top:auto;font-size:12px;line-height:1.9;color:#A9B7CB;font-weight:700}
.ln{display:inline-block;width:18px;height:0;margin-right:6px;vertical-align:middle;border-top:2px solid #F5F7FA}
.ln.now{border-color:#FFD23F}.ln.old{opacity:.4}.ln.dash{border-top-style:dashed;opacity:.7}
:root[data-night=on] .ln.now{border-color:#4ADE80}
.mbig{position:absolute;left:12px;right:12px;bottom:12px;display:flex;align-items:center;justify-content:center;gap:6px;min-height:44px;border-radius:999px;background:rgba(255,255,255,.09);color:#fff;font-size:14px;font-weight:800}
.mbig svg{width:18px;height:18px}

/* 日ごとのカード（案A） */
.day{margin-top:12px;padding:6px 6px 8px;border-radius:22px;background:var(--card);box-shadow:var(--shadow)}
.dh{display:flex;align-items:center;gap:8px;width:100%;min-height:52px;padding:6px 10px;text-align:left;border-radius:16px}
.dd{display:flex;align-items:baseline;gap:6px;flex:1;min-width:0}
.dd b{font-size:17px;font-weight:800;color:var(--strong);white-space:nowrap}
.dd small{font-size:13px;font-weight:700;color:var(--sub)}
.tday{flex:none;white-space:nowrap;display:inline-flex;align-items:center;height:24px;padding:0 9px;border-radius:999px;background:var(--strong);color:#fff;font-size:12px;font-weight:800;align-self:center}
:root[data-night=on] .tday{background:rgba(220,227,234,.16);color:#DCE3EA}
.dn{display:flex;align-items:baseline;gap:2px;white-space:nowrap;font-size:12px;color:var(--mute)}
.dn .num{font-size:17px}
.dn .sep{display:inline-block;width:10px}
.dv{width:20px;height:20px;color:var(--mute);flex:none;transition:transform var(--t-mid) var(--ease)}
.dh[aria-expanded=false] .dv{transform:rotate(-90deg)}
.dch{padding:0 10px 4px}
.chain{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 4px;font-size:13px;color:var(--ink)}
.chain b{font-weight:700}
.chain i{font-style:normal;color:var(--mute);font-size:12px}
.fold .dch{padding-bottom:8px}
.lrs{list-style:none;margin-top:4px}
.lr{display:grid;grid-template-columns:62px 46px minmax(0,1fr) 64px;column-gap:8px;align-items:center;min-height:60px;padding:8px 10px;border-radius:14px}
.lr + .lr{margin-top:2px}
.lr:nth-child(odd){background:#F6F7F9}
:root[data-night=on] .lr:nth-child(odd){background:rgba(255,255,255,.03)}
.c-t{display:flex;flex-direction:column;line-height:1.15}
.c-t b{font-size:19px;font-weight:800;color:var(--strong);letter-spacing:-.02em}
.c-t small{font-size:12px;font-weight:700;color:var(--mute);white-space:nowrap}
.c-t small .num{color:inherit;font-weight:800}
.c-t .act.late{color:var(--late)}
.c-no{display:flex;flex-direction:column;line-height:1.15}
.c-no small{font-size:12px;font-weight:800;color:var(--sub);letter-spacing:.04em}
.c-no b{font-size:16px;color:var(--strong)}
.c-rt{min-width:0;line-height:1.25}
.c-rt b{display:block;font-size:16px;font-weight:800;color:var(--strong);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.c-rt b i{font-style:normal;margin:0 3px;color:var(--mute);font-weight:700}
.c-rt small{display:block;font-size:12px;font-weight:700;color:var(--mute);white-space:nowrap}
.c-rt small .num{color:var(--sub);font-weight:800}
.c-st{text-align:right}
.st{display:inline-flex;align-items:center;justify-content:center;gap:4px;min-width:56px;height:28px;padding:0 8px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--sub);white-space:nowrap}
.st .num{color:inherit;font-weight:800}
.st.ok{color:var(--strong)}
.st.late{background:rgba(154,52,18,.09);color:var(--late)}
:root[data-night=on] .st.late{background:rgba(253,186,116,.12)}
.st.live{background:var(--strong);color:#fff}
.st.live i{width:6px;height:6px;border-radius:50%;background:#86EFAC}
:root[data-night=on] .st.live{background:rgba(74,222,128,.14);color:#4ADE80}
:root[data-night=on] .st.live i{background:#4ADE80}
.st.est{background:transparent;min-width:0;height:auto;padding:0 2px;border-radius:0;border-bottom:1.5px dotted #9CA3AF;color:var(--mute);font-weight:700}
.s-est .c-t b,.s-est .c-no b,.s-est .c-rt b{color:var(--sub)}
.s-est .c-t b{font-weight:700}
.pmore{display:flex;align-items:center;justify-content:center;gap:4px;width:100%;min-height:44px;margin-top:4px;border-radius:999px;font-size:13px;font-weight:700;color:var(--sub)}
.pmore svg{width:16px;height:16px}
.day.empty .dh{min-height:48px}
.dn{font-weight:700}
.dnote{padding:0 10px 8px;font-size:13px;color:var(--sub);line-height:1.6}
.day{--late:#9A3412}
:root[data-night=on] .day{--late:#FDBA74}
.src{margin:14px 4px 0;font-size:12px;line-height:1.7;color:var(--mute)}
.src b{color:var(--sub)}
.why{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-top:8px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.why svg{width:18px;height:18px;color:var(--sub)}

/* 1週間の帯（案B） */
.band{margin-top:12px;padding:14px 12px 10px;border-radius:22px;background:var(--card);box-shadow:var(--shadow)}
.band .bt{display:flex;align-items:baseline;justify-content:space-between;padding:0 4px 6px}
.band .bt b{font-size:15px;font-weight:800;color:var(--strong)}
.band .bt span{font-size:12px;color:var(--mute);font-weight:700}
.axis,.brow{display:grid;grid-template-columns:50px minmax(0,1fr);column-gap:6px;align-items:center}
.axis .ax{position:relative;height:20px}
.axis .ax span{position:absolute;top:0;transform:translateX(-50%);font-size:12px;font-weight:700;color:var(--mute);font-variant-numeric:tabular-nums}
.brow{width:100%;min-height:46px;text-align:left;border-radius:12px;padding:0 0 0 4px}
.brow + .brow{margin-top:2px}
.brow[aria-pressed=true]{background:var(--pill)}
.brow .bl{display:flex;flex-direction:column;line-height:1.1}
.brow .bl b{font-size:15px;font-weight:800;color:var(--strong)}
.brow .bl small{font-size:12px;font-weight:700;color:var(--mute)}
.brow .tr2{position:relative;height:30px;border-radius:8px;background:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/6 - 1px),rgba(17,24,39,.06) calc(100%/6 - 1px),rgba(17,24,39,.06) calc(100%/6))}
:root[data-night=on] .brow .tr2{background:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/6 - 1px),rgba(255,255,255,.06) calc(100%/6 - 1px),rgba(255,255,255,.06) calc(100%/6))}
.blk{position:absolute;top:3px;bottom:3px;display:flex;align-items:center;justify-content:center;border-radius:6px;background:var(--pin);color:#fff;font-size:12px;font-weight:800;letter-spacing:-.03em;overflow:hidden;white-space:nowrap}
:root[data-night=on] .blk{background:#3B4A60;color:#F3F4F6}
.blk.late{box-shadow:inset 0 -3px 0 #C2410C}
:root[data-night=on] .blk.late{box-shadow:inset 0 -3px 0 #FDBA74}
.blk.est{background:transparent;color:var(--sub);box-shadow:inset 0 0 0 1.5px var(--sub);border:0;background-image:none;outline:1.5px dashed var(--card);outline-offset:-1.5px}
.blk.live{background:var(--acc)}
:root[data-night=on] .blk.est{background:transparent;color:#AEB9C6;box-shadow:inset 0 0 0 1.5px #AEB9C6;outline-color:#1B1F26}
:root[data-night=on] .blk.live{background:#4ADE80;color:#0F141B}
.nowv{position:absolute;top:-2px;bottom:-2px;width:2px;margin-left:-1px;border-radius:2px;background:var(--acc);opacity:.6}
.bnone{position:absolute;inset:0;display:flex;align-items:center;padding-left:10px;font-size:12px;font-weight:700;color:var(--mute)}
.bkey{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 4px 0;font-size:12px;font-weight:700;color:var(--mute)}
.bkey i{display:inline-block;width:18px;height:12px;margin-right:5px;border-radius:3px;vertical-align:-1px;background:var(--pin)}
.bkey i.l{box-shadow:inset 0 -3px 0 #C2410C}
.bkey i.e{background:transparent;box-shadow:inset 0 0 0 1.5px var(--sub)}
.bkey i.v{background:var(--acc)}
:root[data-night=on] .bkey i{background:#3B4A60}
:root[data-night=on] .bkey i.e{background:transparent}
:root[data-night=on] .bkey i.v{background:#4ADE80}

/* 大きな地図（m1） */
.mapl{margin-top:12px;padding:10px 10px 14px;border-radius:22px;background:#0E1E36;color:#F5F7FA;box-shadow:0 10px 30px -10px rgba(14,30,54,.45)}
.chips{display:flex;gap:6px;overflow-x:auto;padding:10px 2px 2px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chips button{flex:none;min-height:44px;min-width:48px;padding:0 12px;border-radius:999px;background:rgba(255,255,255,.08);color:#DCE3EA;font-size:13px;font-weight:800;white-space:nowrap}
.chips button[aria-pressed=true]{background:#F5F7FA;color:#0E1E36}
:root[data-night=on] .chips button[aria-pressed=true]{background:#4ADE80;color:#0B1626}
.mapl .mleg{display:flex;gap:16px;flex-wrap:wrap;margin:8px 4px 0;line-height:1.6}
.mapl .msrc{margin:8px 4px 0;font-size:12px;line-height:1.6;color:#A9B7CB}
.aps{margin-top:12px;padding:14px 16px}
.aps h2{font-size:15px}
.aps ul{list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:8px}
.aps li{display:flex;align-items:baseline;gap:4px;font-size:14px;font-weight:700;color:var(--ink)}
.aps li span:first-child{flex:1}
.aps li .num{font-size:18px}

/* 入口の画面（e1〜e3） */
.ophd{display:flex;align-items:center;gap:8px;padding:16px 0 4px}
.side{display:flex;padding:4px;border-radius:999px;background:var(--pill);margin-top:8px}
.side button{flex:1;min-height:44px;border-radius:999px;font-size:14px;font-weight:800;color:var(--sub)}
.side button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.plq{display:flex;align-items:center;gap:8px;margin-top:10px;min-height:48px;padding:0 6px 0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.plq b{flex:1;font-size:18px;font-weight:800;color:var(--strong);letter-spacing:.03em}
.plq .x{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--sub)}
.tl{margin-top:12px;padding:14px 14px 10px}
.tl .tlh{display:flex;align-items:baseline;justify-content:space-between;padding:0 2px 6px}
.tl .tlh b{font-size:15px;font-weight:800;color:var(--strong)}
.tl .tlh span{font-size:12px;color:var(--mute);font-weight:700}
.teaser{display:flex;align-items:center;gap:12px;width:100%;margin-top:12px;padding:14px 14px 14px 16px;border-radius:20px;background:var(--card);box-shadow:var(--shadow);text-align:left}
.teaser .tx{flex:1;min-width:0}
.teaser .tx b{display:block;font-size:15px;font-weight:800;color:var(--strong)}
.teaser .tx small{display:block;font-size:12px;font-weight:700;color:var(--mute)}
.teaser .tn{display:flex;align-items:baseline;gap:2px}
.teaser .tn .num{font-size:24px}
.teaser .chev{width:20px;height:20px;color:var(--mute)}
.mini{display:flex;gap:3px;margin-top:6px}
.mini i{flex:1;height:22px;border-radius:5px;background:var(--pin);opacity:.85;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:12px;font-weight:800;color:#fff}
.mini i.z{background:var(--track);color:var(--mute);opacity:1}
.mini i.t{background:var(--acc);opacity:1}
:root[data-night=on] .mini i{background:#3B4A60;color:#F3F4F6}
:root[data-night=on] .mini i.z{background:#262B33;color:#8B95A3}
:root[data-night=on] .mini i.t{background:#4ADE80;color:#0F141B}
.new{display:inline-flex;align-items:center;height:20px;margin-left:6px;padding:0 7px;border-radius:999px;background:rgba(37,99,235,.1);color:var(--acc);font-size:12px;font-weight:800;vertical-align:2px}
:root[data-night=on] .new{background:rgba(220,227,234,.12)}
.under{filter:saturate(.6);opacity:.55;pointer-events:none}
.scr{position:fixed;inset:0;background:rgba(17,24,39,.32);z-index:30}
.sh{position:fixed;left:50%;bottom:0;width:100%;max-width:430px;transform:translateX(-50%);z-index:31;background:var(--card);border-radius:24px 24px 0 0;box-shadow:0 -10px 30px -10px rgba(17,24,39,.25);padding:10px 20px 30px;max-height:82vh;overflow:auto}
.sh .grab{width:40px;height:5px;border-radius:3px;background:var(--track);margin:0 auto 12px}
.sh h2{font-size:18px}
.sh .lead2{margin-top:4px;font-size:13px;color:var(--sub)}
.kv{list-style:none;margin-top:12px}
.kv li{display:flex;align-items:baseline;justify-content:space-between;gap:12px;min-height:44px;padding:10px 0}
.kv li + li{box-shadow:inset 0 1px 0 var(--track)}
.kv li span{font-size:13px;color:var(--sub);font-weight:700}
.kv li b{font-size:15px;color:var(--strong);text-align:right}
.kv li b .num{font-size:17px}
.btns{display:flex;flex-direction:column;gap:8px;margin-top:14px}
.btn{display:flex;align-items:center;justify-content:center;gap:6px;min-height:50px;border-radius:999px;font-size:15px;font-weight:800}
.btn.p{background:var(--strong);color:#fff}
:root[data-night=on] .btn.p{background:transparent;color:#fff;box-shadow:inset 0 0 0 1.5px #fff}
.btn.s{background:var(--pill);color:var(--strong)}
.btn svg{width:19px;height:19px}
.rs{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--sub);margin-left:6px;vertical-align:3px}
.lvc{display:flex;flex-direction:column;align-items:flex-start;gap:2px;min-height:96px;padding:14px;border-radius:18px;background:var(--card);box-shadow:var(--shadow);text-align:left}
.lvc b{font-size:15px;color:var(--strong)}
.lvc .nm{font-size:13px;font-weight:700;color:var(--ink)}
.lvc small{font-size:12px;color:var(--mute);font-weight:700}
.lvg{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.bkh{display:flex;align-items:baseline;justify-content:space-between;margin-top:14px}
.bkh b{font-size:17px;font-weight:800;color:var(--strong)}
.bkh span{font-size:12px;color:var(--mute);font-weight:700}
.note2{margin-top:10px;padding:12px 14px;border-radius:16px;background:var(--pill);font-size:13px;color:var(--sub);line-height:1.6}
.note2 b{color:var(--strong)}
.strip{display:grid;grid-template-columns:6px 54px 1fr auto;gap:10px;align-items:center;min-height:62px;padding:8px 12px 8px 0;border-radius:16px;background:var(--card);box-shadow:var(--shadow);margin-top:8px;overflow:hidden}
.strip .sb{align-self:stretch;background:var(--pin)}
.strip .sb.dep{background:#7C93B5}
.strip .t b{display:block;font-size:19px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;line-height:1.1}
.strip .t small{font-size:12px;color:var(--mute);font-weight:700}
.strip .i b{font-size:15px;color:var(--strong)}
.strip .i small{display:block;font-size:12px;color:var(--mute);font-weight:700}
.strip .r2{font-size:13px;font-weight:800;color:var(--strong);text-align:right;font-variant-numeric:tabular-nums}
.strip .r2 small{display:block;font-size:12px;color:var(--mute);font-weight:700}
.est-lead{margin-top:12px;padding:14px 16px;border-radius:20px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--ink);line-height:1.7}
.est-lead b{color:var(--strong)}
.est-lead .ttl{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:800;color:var(--strong);margin-bottom:4px}
.est-lead .ttl svg{width:18px;height:18px;color:var(--sub)}
.usual{display:inline-flex;flex-direction:column;align-items:flex-end;line-height:1.2;white-space:nowrap}
.usual small{font-size:12px;color:var(--mute);font-weight:700}
.usual b{font-size:15px;font-weight:800;color:var(--sub)}
.usual .num{color:inherit}
.c-rt small .st.est{font-size:12px}
'''

JS = r'''
(function(){
  var q = new URLSearchParams(location.search);
  if (q.get('n') === '1') document.documentElement.setAttribute('data-night','on');
  if (q.get('rm') === '1') document.documentElement.classList.add('rm');
  document.querySelectorAll('[data-fold]').forEach(function(b){
    b.addEventListener('click', function(){
      var sec = b.closest('.day'), ul = sec.querySelector('.lrs'), open = b.getAttribute('aria-expanded') === 'true';
      b.setAttribute('aria-expanded', String(!open)); if (ul) ul.hidden = open; sec.classList.toggle('fold', open);
    });
  });
  // 地図の日のピル：その日の道すじだけを明るく
  document.querySelectorAll('[data-day]').forEach(function(b){
    b.addEventListener('click', function(){
      document.querySelectorAll('[data-day]').forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)); });
      var m = document.querySelector('.wmap'); if (b.dataset.day) m.setAttribute('data-sel', b.dataset.day); else m.removeAttribute('data-sel');
    });
  });
  // 帯の日を押すと、その日の便が下に
  document.querySelectorAll('[data-bday]').forEach(function(b){
    b.addEventListener('click', function(){
      document.querySelectorAll('[data-bday]').forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)); });
      document.querySelectorAll('.bdet').forEach(function(s){ s.hidden = s.id !== 'b-' + b.dataset.bday; });
    });
  });
})();
'''

def top(title, back='戻る'):
    return '<div class="top"><button type="button" class="back">%s%s</button><h1>%s</h1></div>' % (ic('back'), back, title)

def reg_card(reg, sub, lv=False, live=True):
    return ('<div class="card reg"><span><span class="rn">%s</span><small>%s</small>%s</span>%s</div>'
            % (reg, sub, '<span class="lv">%s特別塗装（見本）</span>' % ic('star') if lv else '', '<span class="fly"><i></i>飛行中</span>' if live else ''))

def seg(cur):
    return '<div class="seg" role="group"><button type="button" aria-pressed="%s">今日</button><button type="button" aria-pressed="%s">1週間</button></div>' % (
        'true' if cur == 'day' else 'false', 'true' if cur == 'week' else 'false')

def summary(days):
    n, fm, late, est = week_stats(days)
    return ('<div class="rng"><b>11月21日（土）〜 27日（金）</b><span>7日間</span></div>'
            '<div class="sum"><div class="card k"><small>便の数</small><b class="num">%d</b><span class="u">便</span></div>'
            '<div class="card k"><small>飛んだ時間</small><b class="num">%d</b><span class="u">時間</span><b class="num" style="font-size:20px">%02d</b><span class="u">分</span></div>'
            '<div class="card k"><small>15分以上の遅れ</small><b class="num">%d</b><span class="u">便</span></div>'
            '<div class="card k"><small>推定の便</small><b class="num">%d</b><span class="u">便</span></div></div>' % (n, fm // 60, fm % 60, late, est))

SRC = ('<p class="src"><b>出典</b> 便名・定刻・実際の時刻は ODPT（時刻表と運航情報）。どの機体が飛んだかと「推定」の便は、全機の位置の記録（adsb.lol・ODbL）から。'
       '「推定」は時刻表の便に結びつかなかった便で、時刻は離陸・着陸を見た時刻（ごろ）です。保証しません。</p>')

def p_w1():
    days = DAYS[::-1]
    body = (top('機体の1週間') + reg_card('JA01XJ', 'A350-900・JAL') + seg('week') + summary(DAYS) + map_preview(DAYS)
            + ''.join(day_card(d, open_=d[0] in ('d27', 'd26', 'd25')) for d in days)
            + '<button type="button" class="why">%s「推定」とは</button>' % ic('info') + SRC)
    return body, 'now'

def band(days, sel):
    S, E = 6 * 60, 24 * 60
    ax = ''.join('<span style="left:%.2f%%">%d</span>' % ((h * 60 - S) / (E - S) * 100, h) for h in (6, 9, 12, 15, 18, 21, 24))
    rows = []
    for key, date, wd, legs in days:
        blks = []
        for l in legs:
            a0 = tm(l[1]); a1 = a0 + l[5]
            left = (a0 - S) / (E - S) * 100; w = (min(a1, E) - a0) / (E - S) * 100
            late = l[0] and tm(l[1]) - tm(l[0]) >= 15
            cls = 'blk' + (' est' if l[6] == 'est' else '') + (' late' if late else '') + (' live' if l[6] == 'live' else '')
            lab = l[4] if w >= 10.4 else ''
            blks.append('<span class="%s" style="left:%.2f%%;width:%.2f%%" title="%s %s→%s">%s</span>' % (cls, left, w, l[2], l[3], l[4], lab))
        if key == TODAY:
            blks.append('<i class="nowv" style="left:%.2f%%"></i>' % ((NOW - S) / (E - S) * 100))
        if not legs:
            blks.append('<span class="bnone">飛んだ記録なし</span>')
        rows.append('<button type="button" class="brow" data-bday="%s" aria-pressed="%s"><span class="bl"><b class="num">%s</b><small>%s%s</small></span><span class="tr2">%s</span></button>'
                    % (key, 'true' if key == sel else 'false', date.split('月')[1].replace('日', ''), wd, '・今日' if key == TODAY else '', ''.join(blks)))
    return ('<section class="band"><div class="bt"><b>1週間の帯</b><span>押すとその日の便</span></div>'
            '<div class="axis"><span></span><span class="ax">%s</span></div>%s'
            '<div class="bkey"><span><i></i>飛んだ便</span><span><i class="l"></i>15分以上の遅れ</span><span><i class="e"></i>推定</span><span><i class="v"></i>いま飛んでいる</span></div></section>'
            % (ax, ''.join(rows)))

def p_w2():
    det = ''.join('<div class="bdet" id="b-%s"%s>%s</div>' % (d[0], '' if d[0] == 'd26' else ' hidden', day_card(d)) for d in DAYS)
    body = (top('機体の1週間') + reg_card('JA01XJ', 'A350-900・JAL') + seg('week') + band(DAYS[::-1], 'd26') + det
            + map_preview(DAYS) + '<button type="button" class="why">%s「推定」とは</button>' % ic('info') + SRC)
    return body, 'now'

def p_m1():
    chips = '<button type="button" data-day="" aria-pressed="true">7日すべて</button>' + ''.join(
        '<button type="button" data-day="%s" aria-pressed="false">%s</button>' % (d[0], ('今日' if d[0] == TODAY else '%s %s' % (d[1].split('月')[1].replace('日', ''), d[2])))
        for d in DAYS[::-1] if d[3])
    cnt = {}
    for d in DAYS:
        for l in d[3]:
            for c in (l[3], l[4]): cnt[c] = cnt.get(c, 0) + 1
    aps = ''.join('<li><span>%s</span><b class="num">%d</b><span class="u">回</span></li>' % (AP[c][0], v) for c, v in sorted(cnt.items(), key=lambda x: -x[1]))
    body = (top('1週間の道すじ') + '<div class="plq"><b>JA01XJ</b><span class="lead">A350-900</span></div>'
            + '<section class="mapl">' + svg_map(DAYS, big=True) + '<div class="chips" role="group" aria-label="日を選ぶ">' + chips + '</div>'
            + '<p class="mleg"><span><i class="ln now"></i>今日</span><span><i class="ln old"></i>前の日ほど薄く</span><span><i class="ln dash"></i>推定</span></p>'
            + '<p class="msrc">同じ区間はすこしずつずらして重ねるので、何度も飛んだ区間ほど太い束に見えます（航路の跡）。道すじは空港と空港を結んだ線で、実際に飛んだ経路ではありません。'
            + '出典 ODPT・adsb.lol（ODbL）</p></section>'
            + '<section class="card aps"><h2>降りた・飛び立った空港</h2><ul>%s</ul></section>' % aps)
    return body, 'now'

def p_w3():
    days = [(k, d, w, [(u, a, f, x, y, m, 'est') for (u, a, f, x, y, m) in legs]) for (k, d, w, legs) in EST_DAYS]
    def erow(l, usual):
        sch, act, fl, a, b, m, _ = l
        al, no = fl.split(' ')
        dd = tm(act) - tm(usual)
        us = ('<span class="usual"><small>いつもより</small><b>+<span class="num">%d</span>分</b></span>' % dd) if dd >= 5 else '<span class="usual"><small>いつもの</small><b>時刻</b></span>'
        return ('<li class="lr s-est"><span class="c-t"><b class="num">%s</b><small>ごろ 離陸</small></span><span class="c-no"><small>%s</small><b class="num">%s</b></span>'
                '<span class="c-rt"><b>%s<i>→</i>%s</b><small>着 <span class="num">%s</span>ごろ・<span class="st est">推定</span></small></span><span class="c-st">%s</span></li>'
                % (act, al, no, AP[a][0], AP[b][0], hm(tm(act) + m), us))
    cards = []
    for key, date, wd, legs in days[::-1]:
        if not legs:
            cards.append('<section class="day empty"><div class="dh"><span class="dd"><b>%s</b><small>%s</small></span><span class="dn">見えた記録なし</span></div>'
                         '<p class="dnote">飛ばなかったのか、受信できる所を飛ばなかったのかは分かりません。</p></section>' % (date, wd))
            continue
        fm = sum(l[5] for l in legs)
        tag = '<span class="tday">今日</span>' if key == 'e27' else ''
        cards.append('<section class="day"><button type="button" class="dh" aria-expanded="true" data-fold><span class="dd"><b>%s</b><small>%s</small>%s</span>'
                     '<span class="dn"><b class="num">%d</b><span class="u">便</span><span class="sep"></span><span class="u">飛んだ時間</span> <b class="num">%s</b></span>%s</button>'
                     '<div class="dch">%s</div><ul class="lrs">%s</ul></section>' % (date, wd, tag, len(legs), dur(fm), ic('down', 'ic dv'), chain(legs), ''.join(erow(l, l[0]) for l in legs)))
    body = (top('機体の1週間') + reg_card('JA73NX', 'B737-800・スカイマーク', live=False) + seg('week')
            + '<div class="est-lead"><p class="ttl">%sこの機体は、すべて推定です</p>時刻表と運航情報（ODPT）にない会社の機体なので、全機の位置の記録だけで1週間を組み立てています。'
              '<b>定刻と遅れは出せません。</b>代わりに、ふだん同じ便が飛び立つ時刻（いつもの時刻）との差を出します。</div>' % ic('info')
            + '<div class="rng"><b>11月24日（火）〜 27日（金）</b><span>記録は4日分</span></div>'
            + map_preview(days, est_all=True).replace('<i class="ln now"></i>今日<br><i class="ln old"></i>前の日ほど薄く<br>', '<i class="ln now"></i>今日<br>')
            + ''.join(cards) + '<button type="button" class="why">%s「推定」とは</button>' % ic('info')
            + '<p class="src"><b>出典</b> 全機の位置の記録（adsb.lol・ODbL）。便名は無線の呼び出し符号から、出発・到着の空港は離陸・着陸の位置から推しはかっています。受信できない所を飛んだ便は抜けます。保証しません。</p>')
    return body, 'now'

def p_s1():
    under, _ = p_w1()
    sheet = ('<div class="scr"></div><div class="sh" role="dialog" aria-label="推定とは"><div class="grab"></div><h2>「推定」の便とは</h2>'
             '<p class="lead2">時刻表の便に結びつかなかった便です。どの機体がいつ飛んだかは、全機の位置の記録で見ています。</p>'
             '<ul class="kv"><li><span>ふつうの便</span><b>定刻と実際の時刻（ODPT）</b></li>'
             '<li><span>推定の便</span><b>離陸・着陸を見た時刻（ごろ）</b></li>'
             '<li><span>推定の便の遅れ</span><b>出さない<br><small class="lead">ODPT にない会社は「いつもより ○分」</small></b></li>'
             '<li><span>便名</span><b>無線の呼び出し符号から</b></li>'
             '<li><span>出発・到着の空港</span><b>離陸・着陸の位置から</b></li>'
             '<li><span>抜けることがある</span><b>受信できない所を飛んだ便</b></li></ul>'
             '<p class="note2">記録は消さずに残します。ただし推定は、あとで時刻表の便と結びついたら「推定」の札が外れます。</p>'
             '<div class="btns"><button type="button" class="btn s">閉じる</button></div></div>')
    return '<div class="under">' + under + '</div>' + sheet, 'now'

def p_e1():
    body = ('<div class="ophd"><span class="plq" style="margin:0;flex:1"><b>JA01XJ</b><span class="x">閉じる</span></span></div>'
            '<div class="side" role="group"><button type="button" aria-pressed="false">空港</button><button type="button" aria-pressed="true">機体</button></div>'
            + seg('day')
            + '<button type="button" class="teaser"><span class="tx"><b>この機体の1週間<span class="new">新しい</span></b><small>11月21日〜27日・推定 2便を含む</small>'
              '<span class="mini"><i>5</i><i>6</i><i class="z">0</i><i>4</i><i>5</i><i>6</i><i class="t">3</i></span></span>'
              '<span class="tn"><b class="num">29</b><span class="u">便</span></span>%s</button>' % ic('chev', 'ic chev')
            + '<section class="card tl"><div class="tlh"><b>今日 11月27日（金）</b><span>飛んだ便と予想</span></div><ul class="lrs">%s</ul>'
              '<p class="dnote" style="padding:8px 4px 2px">ここから先は予想です。保証しません。（今の「機体の1日」のまま）</p></section>' % ''.join(row(l, True) for l in DAYS[-1][3])
            + '<p class="src">いまの空港 →「機体」→ 登録記号で探す／最近見た機体。今の「機体の1日」の上に「今日｜1週間」を足し、すぐ下に1週間の小さな帯（日ごとの便の数）を置く案です。</p>')
    return body, 'now'

def p_e2():
    under = ('<div class="ophd"><span class="plq" style="margin:0;flex:1"><b>羽田</b><span class="x">撮る人</span></span></div>'
             '<div class="bkh"><b>つぎに来る機体</b><span>B滑走路・着陸</span></div>'
             '<div class="strip"><span class="sb"></span><span class="t"><b>14:56</b><small>着陸</small></span><span class="i"><b>JL 905</b><small>那覇から・A350-900</small></span><span class="r2">JA01XJ<small>いま飛んでいる</small></span></div>'
             '<div class="strip"><span class="sb dep"></span><span class="t"><b>15:05</b><small>離陸</small></span><span class="i"><b>NH 1793</b><small>石垣へ・B737-800</small></span><span class="r2">JA79AN<small>予想</small></span></div>'
             '<div class="strip"><span class="sb"></span><span class="t"><b>15:12</b><small>着陸</small></span><span class="i"><b>JL 326</b><small>福岡から・B767-300ER</small></span><span class="r2">JA602J<small>予想</small></span></div>')
    sheet = ('<div class="scr"></div><div class="sh" role="dialog" aria-label="機体のくわしく"><div class="grab"></div>'
             '<h2>JA01XJ<span class="rs">いま飛んでいる</span></h2><p class="lead2">JL 905 那覇 → 羽田・A350-900</p>'
             '<ul class="kv"><li><span>着陸</span><b><span class="num">14:56</span> の見込み</b></li><li><span>使う滑走路</span><b>B（予想）</b></li>'
             '<li><span>決め方</span><b>この便を機体の位置で見つけた機体</b></li></ul>'
             '<div class="btns"><button type="button" class="btn p">%sこの機体の1週間</button><button type="button" class="btn s">近づいたら知らせる</button></div>'
             '<p class="note2" style="margin-top:12px">今の「機体のくわしく」の下のボタンに足すだけ。開くと「機体の1週間」（案A か案B）へ。</p></div>' % ic('week'))
    return '<div class="under">' + under + '</div>' + sheet, 'now'

def p_e3():
    under = ('<div class="top"><button type="button" class="back">%s図鑑</button><h1>機体図鑑</h1></div>' % ic('back')
             + '<div class="bkh"><b>特別塗装機</b><span>乗った 2・見た 5／38機</span></div>'
             '<div class="lvg"><button type="button" class="lvc"><b>JA01XJ</b><span class="nm">★ 特別塗装（見本）</span><small>JAL・乗った</small></button>'
             '<button type="button" class="lvc"><b>JA8XXA</b><span class="nm">★ 特別塗装（見本2）</span><small>ANA・見た</small></button>'
             '<button type="button" class="lvc"><b>JA8XXB</b><span class="nm">★ 特別塗装（見本3）</span><small>まだ</small></button>'
             '<button type="button" class="lvc"><b>JA8XXC</b><span class="nm">★ 特別塗装（見本4）</span><small>まだ</small></button></div>')
    sheet = ('<div class="scr"></div><div class="sh" role="dialog" aria-label="特別塗装機"><div class="grab"></div>'
             '<h2>★ 特別塗装（見本）</h2><p class="lead2">JA01XJ・A350-900・JAL</p>'
             '<ul class="kv"><li><span>乗った</span><b><span class="num">2</span>回（11月3日・11月15日）</b></li><li><span>この1週間</span><b><span class="num">29</span>便・推定 <span class="num">2</span>便</b></li></ul>'
             '<div class="btns"><button type="button" class="btn p">%sこの機体の1週間</button><button type="button" class="btn s">機体の1日（今日と予想）</button></div>'
             '<p class="note2" style="margin-top:12px"><b>図鑑は特別塗装機だけのまま。</b>ふつうの機体は、いまの空港の「機体」で登録記号を入れると同じ1週間が出ます。</p></div>' % ic('week'))
    return '<div class="under">' + under + '</div>' + sheet, 'book'

def page(name, title, fn, desc):
    body, cur = fn()
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s｜機体の1週間</title><meta name="description" content="%s"><style>%s%s</style></head>'
            '<body>%s%s<script>%s</script></body></html>'
            % (title, desc, CSS, PAGE_CSS, body, tabbar(cur), JS))
    open(os.path.join(OUT, name + '.html'), 'w', encoding='utf-8').write(html)

SCREENS = [
 ('w1-week', '案A 日ごとの一覧（おすすめ）', p_w1, '機体の1日に「今日｜1週間」を足す。上に7日のまとめと紺の地図、下に日ごとのカード（今日と前の2日は開き、ほかは飛んだ順の1行にたたむ）'),
 ('w2-band', '案B 1週間の帯', p_w2, '7日を6時〜24時の帯に並べ、1週間の動きを1枚で。日を押すと、その日の便が下に出る'),
 ('m1-map', '地図 1週間の道すじ', p_m1, '紺の地図。同じ区間はずらして重ね、航路の跡のように残す。今日は黄（夜は緑）、前の日ほど薄く、推定は点線。日のピルでその日だけ'),
 ('w3-est', '推定だけの機体', p_w3, 'ODPT にない会社の機体（どの機体でも登録記号で出せる）。すべて推定で、定刻と遅れの代わりに「いつもより ○分」'),
 ('s1-est', '「推定」とはのシート', p_s1, '推定の便が何で、何を出して何を出さないか'),
 ('e1-now', '入口1 いまの空港の機体', p_e1, 'いまの空港 →「機体」の機体の1日の上に「今日｜1週間」と1週間の小さな帯'),
 ('e2-spot', '入口2 撮る人の機体のくわしく', p_e2, '撮る人の「つぎに来る機体」→ 機体のくわしく の下に「この機体の1週間」'),
 ('e3-zukan', '入口3 特別塗装機の図鑑', p_e3, '機体図鑑（特別塗装機だけのまま）の1機のシートに「この機体の1週間」'),
]
for s in SCREENS:
    page(s[0], s[1], s[2], s[3])
json.dump([[s[0], s[1], s[3]] for s in SCREENS], open(HERE + '/screens.json', 'w'), ensure_ascii=False, indent=1)
print('組み立て', len(SCREENS), '画面')
