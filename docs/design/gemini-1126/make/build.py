# -*- coding: utf-8 -*-
# Gemini との話し合いの上位（11/26）から5つの画面案を組み立てる。
#  G 搭乗中・到着印待ちのカード／E 0件の画面の文言／C 屋外で読めるか／F 意見を送る／R 2回目以降の完了カード
# 地図の背景と共通の部品は design/home-airport から写したもの（make/bg・base_home.py）。外部の読み込みはなし。
# ?night=1 で夜。
import os, sys, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import base_home as B
from base_home import ic, tabs, topbar, sheet, POS, APS, VARS

B.P.update({
 'x': '<path d="M6 6l12 12M18 6L6 18"/>',
 'bug': '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8v12M7 13H3.5M20.5 13H17M8 5.5l1.5 2.5M16 5.5L14.5 8M7.5 18l-3 2M16.5 18l3 2"/>',
 'idea': '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z"/>',
 'tower': '<path d="M9 21l1-10h4l1 10M8 11h8M7 7.5h10l-1.5 3.5h-7zM12 3v4.5"/>',
 'msg': '<path d="M5 5h14a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-8l-4 3.5V17H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/>',
 'eye': '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
 'gear': '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
 'bell': '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5h4"/>',
 'shield': '<path d="M12 3l7 3v5.5c0 4.5-3 8-7 9.5-4-1.5-7-5-7-9.5V6z"/>',
 'sliders': '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
 'warn': '<path d="M12 4l9 16H3zM12 10v4.5M12 17.5h.01"/>',
 'search': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
 'map': '<path d="M3.5 6.5l5.5-2 6 2 5.5-2v13l-5.5 2-6-2-5.5 2zM9 4.5v13M15 6.5v13"/>',
 'land': '<path d="M3 20.5h18M4.5 11.5l3.5 1 2.5-5 2 .6-.9 5.5 4.8 1.4c1 .3 1.6 1.4 1.3 2.4l-.1.3-13.6-3.8z"/>',
 'depart': '<path d="M3 20.5h18M3.5 15.5l3.2 1.4 13.1-6c.9-.4 1.3-1.5.9-2.4-.4-.8-1.4-1.2-2.3-.8l-4.3 2-5.6-3.6-1.9.9 3.4 4.4-3.4 1.6-2.3-1.4-1.6.7z"/>',
})

CSS2 = r'''
:root{--shu:#111111;--gold:#A9822E} :root[data-night=on]{--shu:#E5E7EB;--gold:#AEB9C6}
html,body{overflow:hidden}
/* 搭乗中のカード */
.fly{position:relative}
.tag{display:inline-flex;align-items:center;gap:6px;min-height:28px;padding:0 12px;border-radius:999px;font-size:13px;font-weight:800}
.tag.live{background:rgba(37,99,235,.10);color:#1D4ED8}
.tag.live i{width:8px;height:8px;border-radius:50%;background:#2563EB;box-shadow:0 0 0 3px rgba(37,99,235,.18)}
.tag.cxl{background:rgba(17,24,39,.06);color:var(--strong)}
:root[data-night=on] .tag.live{background:rgba(74,222,128,.12);color:#4ADE80}
:root[data-night=on] .tag.live i{background:#4ADE80;box-shadow:0 0 0 3px rgba(74,222,128,.2)}
:root[data-night=on] .tag.cxl{background:rgba(220,227,234,.08);color:#E5E7EB}
.route{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px;margin-top:12px}
.route .cd{display:block;font-size:30px;font-weight:800;letter-spacing:.04em;color:var(--strong);line-height:1.1}
.route .cd.q{color:var(--mute)}
.route .nm{display:block;font-size:13px;font-weight:700;color:var(--sub);margin-top:2px}
.route .r{text-align:right}
.route .ln{position:relative;height:24px}
.route .ln::before{content:"";position:absolute;left:0;right:0;top:50%;border-top:2px dashed #C3C9D2}
:root[data-night=on] .route .ln::before{border-color:#3A414C}
.route .ln svg{position:absolute;left:58%;top:50%;width:24px;height:24px;transform:translate(-50%,-50%) rotate(45deg);background:var(--card);color:var(--strong);padding:1px}
.fly .fl{margin-top:12px;display:flex;align-items:center;flex-wrap:wrap;gap:6px 8px;font-size:14px;color:var(--ink)}
.fly .fl b{font-weight:800;color:var(--strong)}
.fly .msg{margin-top:10px;font-size:14px;color:var(--ink);line-height:1.55}
.fly .foot{margin-top:10px;display:flex;align-items:center;gap:8px}
.fly .foot .note{flex:1;font-size:13px;color:var(--mute);line-height:1.45}
.bigarr{width:100%;min-height:64px;margin-top:14px;border-radius:999px;background:var(--strong);color:#fff;font-size:18px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:10px}
.bigarr svg.ic{width:24px;height:24px}
:root[data-night=on] .bigarr{background:transparent;color:#F9FAFB;box-shadow:inset 0 0 0 2px #F9FAFB}
.fly.mini{padding:12px 14px}
.fly.mini .row{gap:10px}
.fly.mini .cds{font-size:18px;font-weight:800;color:var(--strong);letter-spacing:.04em;white-space:nowrap}
.fly.mini .cds small{font-size:13px;color:var(--mute);margin:0 4px}
/* 一般の画面（地図なし） */
.pg{position:absolute;inset:0;overflow:hidden;padding:18px 16px 110px;display:flex;flex-direction:column;gap:14px}
.pg h1{font-size:24px;font-weight:800;color:var(--strong);letter-spacing:.01em}
.pg .hdr{display:flex;align-items:center;gap:8px;min-height:44px}
.pg .hdr .sp{flex:1}
.iconbtn{width:44px;height:44px;border-radius:50%;background:var(--card);box-shadow:var(--shadow);display:inline-flex;align-items:center;justify-content:center;color:var(--strong)}
.views{display:flex;gap:6px;overflow:hidden}
.views button{min-height:44px;padding:0 16px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--sub);white-space:nowrap}
.views button[aria-current]{background:var(--strong);color:#fff}
:root[data-night=on] .views button[aria-current]{background:rgba(220,227,234,.16);color:#F3F4F6}
.empty{display:flex;flex-direction:column;align-items:flex-start;gap:10px;padding:22px 18px 18px}
.empty .eic{width:52px;height:52px;border-radius:18px;background:var(--pill);display:flex;align-items:center;justify-content:center;color:var(--strong)}
.empty .eic svg{width:28px;height:28px}
.empty h2{font-size:18px;font-weight:800;color:var(--strong);line-height:1.45}
.empty p{font-size:14px;color:var(--ink);line-height:1.6}
.empty .pill.dark{width:100%;min-height:52px;font-size:15px;margin-top:4px}
.big0{display:flex;align-items:baseline;gap:4px}
.big0 .num{font-size:40px;line-height:1.1}
.row .big0 .num{font-size:32px}
.ghostrow{display:flex;align-items:center;gap:12px;min-height:60px;padding:10px 14px;border-radius:16px;background:var(--pill);opacity:.9;width:100%}
.ghostrow .d{font-size:13px;font-weight:800;color:var(--sub);width:40px;line-height:1.25}
.ghostrow .cds{font-size:17px;font-weight:800;color:var(--sub);letter-spacing:.04em}
.ghostrow .mihon{margin-left:auto;font-size:12px;font-weight:800;color:var(--sub);padding:2px 8px;border-radius:999px;box-shadow:inset 0 0 0 1.5px #A0A7B2}
.tiles2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tile{background:var(--card);border-radius:20px;box-shadow:var(--shadow);padding:14px;display:flex;flex-direction:column;gap:6px;min-height:120px}
.tile .lab{font-size:13px}
.tile .num{font-size:30px;line-height:1.1}
.tile p{font-size:13px;color:var(--sub);line-height:1.5}
.toc{padding:6px 6px}
.toc .it{display:flex;align-items:center;gap:12px;min-height:56px;padding:0 10px;border-radius:14px;font-size:15px;font-weight:700;color:var(--strong);width:100%;text-align:left}
.toc .it svg.ic{color:var(--sub)}
.toc .it .ch{margin-left:auto;color:var(--mute)}
.toc .it.new{background:rgba(37,99,235,.06)}
:root[data-night=on] .toc .it.new{background:rgba(220,227,234,.06)}
.toc .it small{display:block;font-size:13px;font-weight:600;color:var(--sub)}
/* 意見を送る */
.dlg{position:absolute;left:0;right:0;bottom:0;top:46px;z-index:8;background:var(--bg);border-radius:26px 26px 0 0;box-shadow:0 -14px 40px -10px rgba(17,24,39,.35);padding:8px 16px 24px;display:flex;flex-direction:column;gap:14px;overflow:hidden}
.scrim{position:absolute;inset:0;z-index:7;background:rgba(15,22,38,.38)}
.dlg .hd2{display:flex;align-items:center;gap:8px}
.dlg .hd2 h2{font-size:20px;font-weight:800;color:var(--strong)}
.dlg .hd2 .sp{flex:1}
.choice{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.choice button{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;min-height:84px;padding:8px 4px;border-radius:18px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong);line-height:1.3;text-align:center}
.choice button svg.ic{width:24px;height:24px;color:var(--sub)}
.choice button[aria-pressed=true]{background:var(--strong);color:#fff;box-shadow:none}
.choice button[aria-pressed=true] svg.ic{color:#fff}
:root[data-night=on] .choice button[aria-pressed=true]{background:rgba(220,227,234,.16);color:#F3F4F6;box-shadow:inset 0 0 0 1.5px #DCE3EA}
.ta{width:100%;min-height:120px;border:0;border-radius:18px;background:var(--card);box-shadow:var(--shadow);padding:14px;font:inherit;font-size:15px;color:var(--ink);line-height:1.6;resize:none}
.ta::placeholder{color:#6B7280}
.cnt{font-size:13px;color:var(--mute);text-align:right;margin-top:-8px}
.sendinfo{padding:12px 14px;border-radius:16px;background:var(--pill);font-size:13px;color:var(--ink);line-height:1.6}
.sendinfo b{color:var(--strong)}
.aprow{display:flex;align-items:center;gap:10px;min-height:56px;padding:0 14px;border-radius:16px;background:var(--card);box-shadow:var(--shadow)}
.aprow .cd{font-size:17px;font-weight:800;letter-spacing:.04em;color:var(--strong)}
.aprow .n{flex:1;font-size:14px;color:var(--ink)}
.aprow .pill.sm{background:var(--pill)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chips button{min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:700;color:var(--strong)}
.chips button[aria-pressed=true]{background:var(--strong);color:#fff;box-shadow:none}
:root[data-night=on] .chips button[aria-pressed=true]{background:rgba(220,227,234,.16);color:#F3F4F6}
.lbl{font-size:13px;font-weight:800;color:var(--sub);margin-bottom:-6px}
.sent{display:flex;flex-direction:column;align-items:center;text-align:center;gap:10px;padding:26px 18px 20px}
.sent .ok{width:56px;height:56px;border-radius:50%;background:rgba(21,128,61,.12);color:var(--ok);display:flex;align-items:center;justify-content:center}
.sent .ok svg{width:30px;height:30px;stroke-width:2.4}
.sent h2{font-size:20px;font-weight:800;color:var(--strong)}
.sent p{font-size:14px;color:var(--ink);line-height:1.6}
.upd .it{display:flex;gap:10px;align-items:flex-start;padding:8px 0}
.upd .it .d{font-size:13px;font-weight:800;color:var(--sub);width:46px;flex:none;padding-top:1px}
.upd .it p{font-size:14px;color:var(--ink);line-height:1.5}
.upd .it .mk2{display:inline-block;font-size:12px;font-weight:800;color:var(--ok);background:rgba(21,128,61,.10);border-radius:999px;padding:0 8px;margin-left:4px}
/* 完了カード（今のダイアログの形） */
.stdlg{position:absolute;left:12px;right:12px;top:50%;transform:translateY(-50%);z-index:8;background:var(--card);border-radius:26px;box-shadow:0 24px 50px -12px rgba(15,22,38,.45);padding:0 18px 18px;overflow:hidden}
.ticket{margin:0 -18px;padding:12px 18px;background:#1F2937;color:#F9FAFB;display:flex;align-items:center;gap:10px;font-size:13px;font-weight:700}
.ticket b{font-size:18px;font-weight:800;letter-spacing:.06em}
.ticket .sp{flex:1}
:root[data-night=on] .ticket{background:#262B33}
.stampbig{width:150px;height:150px;margin:16px auto 4px}
.stampbig svg{width:100%;height:100%}
.stdlg h3{text-align:center;font-size:21px;font-weight:800;color:var(--strong)}
.cnt1{margin:10px auto 0;display:flex;justify-content:center;align-items:baseline;gap:4px;flex-wrap:wrap;font-weight:800;color:var(--strong)}
.cnt1 .num{font-size:30px}
.cnt1 .u{font-size:14px}
.cnt1 .dot{margin:0 8px;color:var(--mute);font-size:18px}
.newline{position:relative}
.newline::after{content:"足す1行";position:absolute;right:0;top:-12px;font-size:12px;font-weight:800;color:#1D4ED8;background:rgba(37,99,235,.10);border-radius:999px;padding:0 8px}
:root[data-night=on] .newline::after{color:#4ADE80;background:rgba(74,222,128,.12)}
.stdlg .nt{margin-top:10px;text-align:center;font-size:14px;color:var(--ink);line-height:1.6}
.stdlg .row2{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
.stdlg .row2 .pill{width:100%}
.btn2{background:var(--pill)!important}
/* 屋外の表 */
.doc{position:static;overflow:auto;height:auto}
html.docmode,html.docmode body{overflow:auto;height:auto}
.docw{max-width:430px;margin:0 auto;padding:18px 16px 40px;display:flex;flex-direction:column;gap:14px}
.docw h1{font-size:22px;font-weight:800;color:var(--strong)}
.docw h2{font-size:17px;font-weight:800;color:var(--strong)}
.docw p,.docw li{font-size:14px;color:var(--ink);line-height:1.65}
.docw ul{padding-left:1.2em}
.ct{display:flex;flex-direction:column;gap:8px}
.ct .r{display:grid;grid-template-columns:56px 1fr auto;gap:10px;align-items:center;padding:10px 12px;border-radius:14px;background:var(--card);box-shadow:var(--shadow)}
.ct .sw{height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800}
.ct .w{font-size:13px;color:var(--ink);line-height:1.45}
.ct .w b{display:block;font-size:14px;color:var(--strong);font-variant-numeric:tabular-nums}
.ct .v{text-align:right;font-variant-numeric:tabular-nums}
.ct .v .num{font-size:20px}
.ct .ok2,.ct .ng{display:block;font-size:12px;font-weight:800;border-radius:999px;padding:0 8px;margin-top:2px}
.ct .ok2{color:#15803D;background:rgba(21,128,61,.10)}
.ct .ng{color:#B42318;background:rgba(180,35,24,.08)}
.tbl{width:100%;border-collapse:separate;border-spacing:0 8px;font-size:13px}
.tbl td{background:var(--card);padding:10px;vertical-align:top;line-height:1.55;color:var(--ink)}
.tbl td:first-child{border-radius:14px 0 0 14px;font-weight:800;color:var(--strong);width:64px}
.tbl td:last-child{border-radius:0 14px 14px 0}
.tbl .old{color:var(--sub)}
.tbl .new b{color:var(--strong)}
.tbl .go{display:inline-block;margin-top:4px;font-size:12px;font-weight:800;padding:0 8px;border-radius:999px;background:var(--pill);color:var(--strong)}
/* 屋外の見本 */
.st3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.st3 .t{border-radius:16px;padding:10px 8px;display:flex;flex-direction:column;align-items:center;gap:6px;min-height:104px;justify-content:center;text-align:center}
.st3 .t .c{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;letter-spacing:0}
.st3 .t b{font-size:13px;font-weight:800;color:var(--strong)}
.st3 .t small{font-size:12px;font-weight:700;color:var(--sub)}
.t.got{background:var(--card);box-shadow:var(--shadow);position:relative} .t.got .c{background:#1F2937;color:#fff}
.t.got::after{content:"✓";position:absolute;right:8px;top:8px;width:20px;height:20px;border-radius:50%;background:#15803D;color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 2px var(--card)}
.t.memo{background:var(--card);box-shadow:var(--shadow)} .t.memo .c{background:#F7DCE3;color:#7A2E44;box-shadow:inset 0 0 0 2px #E8A3B4;outline:2px dashed #C2667E;outline-offset:2px}
.t.yet{background:var(--card);box-shadow:var(--shadow)} .t.yet .c{background:transparent;color:#5F6672;box-shadow:inset 0 0 0 1.5px #8A909A}
.t.wait{background:var(--card);box-shadow:var(--shadow)} .t.wait .c{background:rgba(31,41,55,.30);color:#1F2937;position:relative}
.dl{display:flex;align-items:center;gap:10px;min-height:52px}
.dl .t2{font-size:18px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;width:52px}
.dl .f{flex:1;font-size:14px;color:var(--ink)}
.dl .late{display:inline-flex;align-items:center;gap:4px;min-height:28px;padding:0 10px;border-radius:999px;font-size:14px;font-weight:800;color:#B42318;background:rgba(180,35,24,.08)}
.dl .late svg{width:14px;height:14px}
.dl .late.cx{color:#fff;background:#B42318}
.dl .ontime{font-size:14px;font-weight:700;color:#4B5563}
@media (max-height:700px){.choice button{min-height:68px;gap:2px}.choice button svg.ic{width:20px;height:20px}.ta{min-height:76px}.dlg{gap:10px}.sendinfo{padding:8px 12px}}
.dlg{overflow-y:auto}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
'''

def page(name, title, body, doc=False):
    cls = ' class="docmode"' if doc else ''
    html = ('<!doctype html><html lang="ja"%s><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s\n%s</style></head><body>%s<script>%s</script></body></html>') % (
            cls, title, VARS, B.CSS, CSS2, body if doc else '<div class="ph">%s</div>' % body, B.JS)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html)
    print('書いた', name)

S = []
def add(name, title, body, kind='phone', doc=False):
    page(name, title, body, doc); S.append((name, title, kind))

# ───── 地図（広い日本地図。いる場所を指定できる） ─────
def marks(key, me='ME', arc=True, label2='新千歳'):
    d = POS[key]; out = []
    visited = {'HND', 'NRT', 'CTS', 'ITM', 'KIX', 'FUK', 'OKA', 'HKD', 'SDJ', 'KMQ', 'NGO', 'HIJ', 'AOJ', 'AKJ', 'KUH', 'MMB'}
    for a in APS:
        c = a[2]
        if c not in d: continue
        x, y = d[c]
        out.append(('<circle class="v" cx="%.1f" cy="%.1f" r="4.5"/>' if c in visited else '<circle class="nv" cx="%.1f" cy="%.1f" r="3.5"/>') % (x, y))
    if arc:
        (x1, y1), (x2, y2) = d['HND'], d['CTS']
        out.insert(0, '<path class="arc" d="M%.1f %.1fQ%.1f %.1f %.1f %.1f"/>' % (x1, y1, (x1 + x2) / 2 + 46, (y1 + y2) / 2, x2, y2))
        out.append('<text x="%.1f" y="%.1f">羽田</text><text x="%.1f" y="%.1f">%s</text>' % (x1 + 9, y1 + 16, x2 + 9, y2 + 4, label2))
    if me:
        if me == 'ME': x, y = d['ME']; x, y = x - 8, y - 8
        elif me == 'AIR':  # 空の上（弧の途中）
            (x1, y1), (x2, y2) = d['HND'], d['CTS']; t = .55; mx, my = (x1 + x2) / 2 + 46, (y1 + y2) / 2
            x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * mx + t * t * x2; y = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * my + t * t * y2
        else: x, y = d[me]; x, y = x + 4, y + 6
        out.append('<circle class="meh" cx="%.1f" cy="%.1f" r="14"/><circle class="me" cx="%.1f" cy="%.1f" r="6"/>' % (x, y, x, y))
    return ''.join(out)

def mapw(me='ME', arc=True):
    v = marks('wide', me, arc).replace('"', '&quot;'); s = marks('wide-667', me, arc).replace('"', '&quot;')
    return ('<img class="map" data-src="make/bg/bg-wide" alt="">'
            '<svg class="mk" data-v="%s" data-s="%s"></svg><span class="attr">地図：国土地理院</span>'
            '<button type="button" class="locbtn" aria-label="いまの場所へ">%s</button>') % (v, s, ic('locate'))

CHIP_N = '<span class="chip">空港 16<span class="u">/86</span></span>'
CHIP_CTS = '<span class="chip in" style="white-space:nowrap"><i></i>新千歳の範囲の中</span>'
CHIP_HND = '<span class="chip in" style="white-space:nowrap"><i></i>羽田の範囲の中</span>'

# ───── ① 搭乗中・到着印待ち ─────
def MORE(h):  # シートを上へ引くと続きが出るカード（測るときは切れに数えない）
    return h.replace('class="card', 'class="more card', 1)
def fly(dest=True, foot_btn='搭乗しなかった'):
    r = ('<div class="r"><span class="cd">CTS</span><span class="nm">新千歳（便から）</span></div>' if dest else
         '<div class="r"><span class="cd q">？</span><span class="nm">着いた空港で決まります</span></div>')
    fl = ('<div class="fl"><span class="al jl">JL</span><b>JL503</b><span>09:45 着の見込み</span><span class="note">（航空会社の運航情報）</span></div>' if dest else
          '<div class="fl"><button type="button" class="pill sm">乗る便を選ぶ%s</button><span class="note">羽田 08:00〜09:30 発の候補から</span></div>' % ic('chev'))
    return ('<div class="card fly"><div class="row"><span class="tag live"><i></i>搭乗中・到着印待ち</span><span class="sp"></span>'
            '<span class="note">羽田の印 08:02</span></div>'
            '<div class="route"><div><span class="cd">HND</span><span class="nm">羽田</span></div><div class="ln">%s</div>%s</div>%s'
            '<p class="msg">着いた空港でチェックインすると、羽田からのフライトになります</p>'
            '<div class="foot"><span class="note">このカードは 16:02 に消えます（印から8時間）</span>'
            '<button type="button" class="pill sm">%s</button></div></div>') % (ic('plane'), r, fl, foot_btn)

FLY_MINI = ('<div class="card fly mini"><div class="row"><span class="tag live"><i></i>搭乗中</span>'
            '<span class="cds">HND<small>→</small>CTS</span><span class="sp"></span><span class="note">JL503・09:45 着</span></div></div>')

ARRIVE = ('<div class="card fly"><div class="row"><span class="tag live"><i></i>新千歳に着きました</span><span class="sp"></span>'
          '<span class="note">羽田の印 08:02</span></div>'
          '<div class="route"><div><span class="cd">HND</span><span class="nm">羽田 08:02</span></div><div class="ln">%s</div>'
          '<div class="r"><span class="cd">CTS</span><span class="nm">新千歳 いま</span></div></div>'
          '<button type="button" class="bigarr">%s新千歳で到着印を押す</button>'
          '<p class="msg" style="text-align:center">羽田 → 新千歳 819km を JL503 として記録します</p>'
          '<div class="foot" style="justify-content:center"><button type="button" class="pill sm">便を選び直す</button>'
          '<button type="button" class="pill sm">あとで</button></div></div>') % (ic('plane'), ic('land'))

SAME = ('<div class="card fly"><div class="row"><span class="tag cxl">まだ羽田にいます</span><span class="sp"></span>'
        '<span class="note">羽田の印 08:02</span></div>'
        '<div class="route"><div><span class="cd">HND</span><span class="nm">羽田</span></div><div class="ln">%s</div>'
        '<div class="r"><span class="cd">CTS</span><span class="nm">新千歳（便から）</span></div></div>'
        '<div class="fl"><span class="al jl">JL</span><b>JL503</b><span>欠航</span><span class="note">（航空会社の運航情報 10:12）</span></div>'
        '<p class="msg">欠航や取りやめのときは「搭乗しなかった」で閉じます。羽田の印はそのまま残ります</p>'
        '<div class="foot"><button type="button" class="pill sm">別の便に乗る</button><span class="sp" style="flex:1"></span>'
        '<button type="button" class="pill dark sm">搭乗しなかった</button></div></div>') % ic('plane')

add('g1-boarding.html', 'G1 搭乗中・到着印待ち（便が分かる）', mapw('AIR') + topbar(CHIP_N) + sheet(fly() + MORE(B.NEXT), 'm', 420) + tabs())
add('g1b-nofl.html', 'G1b 搭乗中・便が分からない', mapw('AIR', arc=False) + topbar(CHIP_N) + sheet(fly(dest=False) + MORE(B.NEXT), 'm', 480) + tabs())
add('g2-arrive.html', 'G2 別の空港に着いた・到着印を大きく', mapw('CTS') + topbar(CHIP_CTS) + sheet(ARRIVE + MORE(B.NOW3.replace('羽田', '新千歳')), 'm', 470) + tabs())
add('g3-same.html', 'G3 同じ空港に戻った・欠航', mapw('HND', arc=True) + topbar(CHIP_HND) + sheet(SAME + MORE(B.NOW3), 'm', 440) + tabs())
add('g4-small.html', 'G4 シート小のとき', mapw('AIR') + topbar(CHIP_N) + sheet(FLY_MINI, 's', 150) + tabs())

# ───── ② 0件の画面の文言 ─────
def empty(icn, h, p, btn, extra=''):
    return ('<div class="card empty"><span class="eic">%s</span><h2>%s</h2><p>%s</p>%s'
            '<button type="button" class="pill dark">%s</button></div>') % (ic(icn), h, p, extra, btn)
def screen(title, views, inner, cur, right=''):
    vs = ''.join('<button type="button"%s>%s</button>' % (' aria-current="page"' if i == 0 else '', v) for i, v in enumerate(views))
    return ('<div class="pg"><div class="hdr"><h1>%s</h1><span class="sp"></span>%s</div>%s%s</div>' % (
        title, right, '<div class="views">%s</div>' % vs if views else '', inner)) + tabs(cur)

E = [
 ('e1-zukan.html', 'E1 図鑑・0件', 'book', '図鑑', ['地方別', '地図', '行った順'],
  '<div class="card"><div class="row"><span class="lab">集めた空港</span><span class="sp"></span><span class="big0"><span class="num">0</span><span class="u">/ 86</span></span></div></div>'
  + empty('book', '行った空港の印が、地方ごとにそろっていく図鑑です', '空港の中でチェックインすると、ここに1つずつ入ります', '近い空港を見る'),
  'まだ印はありません。空港でチェックインすると、はじめて押した日の順に並びます。（行った順）／地方別は 0/86 とタイルが並ぶだけで説明なし',
  '<b>行った空港の印が、地方ごとにそろっていく図鑑です</b><br>空港の中でチェックインすると、ここに1つずつ入ります', 'ホームの「近い空港」'),
 ('e2-flight.html', 'E2 フライト・0件', 'log', 'フライト', [],
  empty('plane', '乗った便が1便1行で残る、航空日誌です', '出発と到着の空港でチェックインすると、自動で入ります',
        '乗った便を足す', '<div class="ghostrow"><span class="d">12月<br>9日</span><span class="cds">HND → CTS</span><span class="mihon">見本</span></div>'),
  'まだフライトはありません。出発する空港と着いた空港の両方でチェックインすると、ここに1便ずつ記録されます。乗った便は右上の ＋ からも足せます。',
  '<b>乗った便が1便1行で残る、航空日誌です</b><br>出発と到着の空港でチェックインすると、自動で入ります（見本の1行つき）', '右上の ＋ と同じ「乗った便を足す」'),
 ('e3-ops.html', 'E3 運用・ピン止めなし', 'ops', '運用', [],
  empty('tower', '空港の滑走路・遅れ・特別塗装機の「いま」を見る場所です', 'よく見る空港をピン止めすると、ここにいつも出ます', '羽田のいまを見る')
  + '<div class="card list"><div class="hd"><h2>北から順に</h2></div>'
  + ''.join('<div class="it"><span class="c">%s</span><span class="n">%s</span></div>' % r for r in (('CTS', '新千歳'), ('SDJ', '仙台'))) + '</div>',
  'ピン止め・よく見る空港がないときは、説明なしで「北から順に」の14空港が並ぶだけ',
  '<b>空港の滑走路・遅れ・特別塗装機の「いま」を見る場所です</b><br>よく見る空港をピン止めすると、ここにいつも出ます', 'いちばん近い空港（14空港の中）の専用ページ'),
 ('e4-mypage.html', 'E4 マイページ・0件', 'me', 'マイページ', [],
  '<div class="card"><div class="row"><span class="lab">成績</span></div>'
  '<div class="row" style="margin-top:6px;gap:18px"><span class="big0"><span class="num">0</span><span class="u">空港</span></span><span class="big0"><span class="num">0</span><span class="u">便</span></span><span class="big0"><span class="num">0</span><span class="u">km</span></span></div>'
  '<p style="margin-top:8px;font-size:14px;color:var(--ink)">空港でチェックインすると、ここの数が増えていきます</p>'
  '<button type="button" class="pill dark" style="width:100%;margin-top:10px">近い空港を見る</button></div>'
  '<div class="tiles2"><div class="tile"><span class="lab">修行</span><p style="color:var(--ink);font-size:14px">JAL・ANA の上級会員までの道のりを数えます</p><span class="note" style="margin-top:auto">修行の画面を開く ›</span></div>'
  '<div class="tile"><span class="lab">知らせ</span><p style="color:var(--ink);font-size:14px">空港をピン止めすると、遅れや特別塗装機を知らせます</p><span class="note" style="margin-top:auto">知らせを開く ›</span></div></div>',
  '成績のタイルに 0 空港・0 便・0 km が並ぶだけ。修行のタイルは「まだ記録した便がありません」',
  '<b>空港でチェックインすると、ここの数が増えていきます</b>（成績）／<b>JAL・ANA の上級会員までの道のりを数えます</b>（修行）／<b>空港をピン止めすると、遅れや特別塗装機を知らせます</b>（知らせ）', 'ホームの「近い空港」・修行の画面・知らせ'),
 ('e5-shugyo.html', 'E5 修行・0件', 'sg', '修行', [],
  '<div class="card"><div class="row"><span class="lab">JAL FLY ON ポイント・2026年</span></div><div class="big0" style="margin-top:6px"><span class="num">0</span><span class="u">FOP</span></div></div>'
  + empty('stairs', '上級会員までの道のりを数える場所です', '乗った便と予定の便から、あと何回・何ポイントかを出します（推定）', '計画を作る'),
  '予定の便はまだありません。「計画を作る」から入れると、ここに次に乗る便を出します。／数字の下は「まだ記録した便がありません」',
  '<b>上級会員までの道のりを数える場所です</b><br>乗った便と予定の便から、あと何回・何ポイントかを出します（推定）', '「計画を作る」（今と同じ）'),
]
for name, title, cur, h1, views, inner, old, new, go in E:
    add(name, title, screen(h1, views, inner, cur, '<button type="button" class="iconbtn" aria-label="足す">%s</button>' % ic('plus') if cur == 'log' else ''))
rows = ''.join('<tr><td>%s</td><td><div class="old">%s</div><div class="new" style="margin-top:6px">%s</div><span class="go">1タップ：%s</span></td></tr>' % (h1, old, new, go)
               for name, title, cur, h1, views, inner, old, new, go in E)
rows += ('<tr><td>ホーム<br>最近の印</td><td><div class="old">まだ印はありません。空港に着いたらチェックインしてください。</div>'
         '<div class="new" style="margin-top:6px"><b>ここに最近の印が並びます</b><br>空港の中でチェックインすると入ります</div><span class="go">1タップ：なし（すぐ上に近い空港がある）</span></td></tr>')
add('e0-table.html', 'E0 0件の文言の表（今と案）', '<div class="docw"><h1>0件の画面の文言</h1>'
    '<p>決まり：何の場所かを1行（太字）＋どうすると埋まるかを1行＋押すもの1つ。「まだ〜ありません」で始めない。「してください」と頼まない。上が今の文（灰色）、下が案</p>'
    '<table class="tbl">%s</table>'
    '<p>そろえた言葉：「チェックイン」「印」「便」「空港の中で」。名前の「航空日誌」「図鑑」は今の画面の題のまま。0 の数字は今のまま大きく出す（消さない）</p></div>' % rows, 'doc', doc=True)

# ───── ③ 屋外で読めるか ─────
def lum(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def ratio(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
SRC = open(os.path.join(OUT, '..', '..', '..', 'src', 'index.html'), encoding='utf-8').read() if os.path.exists(os.path.join(OUT, '..', '..', '..', 'src', 'index.html')) else ''
def used(c): return len(re.findall('color:' + c, SRC, re.I))
CT = [
 ('#374151', '#FFFFFF', '本文（--ink）', None), ('#1F2937', '#FFFFFF', '見出し・数字（--strong）', None),
 ('#4B5563', '#FFFFFF', '補足の濃いほう', None), ('#646B78', '#F4F5F7', '補足（--sub）を灰の地に', None),
 ('#6B7280', '#FFFFFF', '単位・注（--mute）を白に', None), ('#6B7280', '#F4F5F7', '単位・注（--mute）を灰の地に', '#5F6672'),
 ('#9CA3AF', '#FFFFFF', '薄い灰（ところどころ）', '#6B7280'), ('#8A909A', '#FFFFFF', '薄い灰（ところどころ）', '#6B7280'),
 ('#BDBDBD', '#FFFFFF', 'ごく薄い灰（字なら）', '#6B7280'),
 ('#C8102E', '#FFFFFF', 'JAL 赤の字', None), ('#1C4FA0', '#FFFFFF', 'ANA 青の字', None), ('#B42318', '#FFFFFF', '遅れ・欠航の赤', None),
 ('#AEB9C6', '#1B1F26', '夜：補足', None), ('#8B95A3', '#16191F', '夜：タブの字', None), ('#FF5A6E', '#1B1F26', '夜：JAL 赤の字', None),
]
cts = ''
for fg, bg, what, fix in CT:
    r = ratio(fg, bg); n = used(fg)
    st = '<span class="ok2">4.5 以上</span>' if r >= 4.5 else '<span class="ng">足りない</span>'
    fx = '' if not fix else '<br>→ %s にすると %.1f' % (fix, ratio(fix, bg))
    cts += ('<div class="r"><span class="sw" style="background:%s;color:%s;box-shadow:inset 0 0 0 1px rgba(17,24,39,.08)">あ12</span>'
            '<span class="w"><b>%s 上の %s</b>%s%s%s</span><span class="v"><span class="num">%.1f</span>%s</span></div>') % (
            bg, fg, bg, fg, what, ('・今のアプリで %d か所' % n) if n else '', fx, r, st)

add('c1-contrast.html', 'C1 屋外で読めるか（色の比べ）', '<div class="docw"><h1>屋外で読めるか</h1>'
    '<p>日なたでは画面が白っぽく見え、薄い灰の字から先に消えます。目安は字と地の明るさの比 <b>4.5</b> 以上（大きな太字は 3 以上）。今のアプリ（src/index.html）で使っている字の色を測りました</p>'
    '<div class="ct">%s</div>'
    '<h2>案</h2><ul>'
    '<li>字に使う灰は <b>3つだけ</b>：本文 #374151・補足 #4B5563・注 #6B7280（灰の地では #5F6672）。#9CA3AF・#8A909A・#BDBDBD は線や点・空の枠だけにし、字には使わない</li>'
    '<li>カードに <b>1px のごく薄い輪郭</b>（今の影の中の inset 1px を残す）。日なたで影が消えても形が残る</li>'
    '<li>JAL 赤・ANA 青は字の色としては 4.5 以上で問題なし。ただし <b>色だけで会社を分けない</b>：便名の前に「JL」「NH」の字の札（今のまま）</li>'
    '<li>遅れ・欠航は赤だけにせず、<b>字（「遅れ」「欠航」）と印（▲）</b>を添える。欠航は白抜きの札</li>'
    '<li>印の有無は <b>形と字</b>でも分ける：押した＝塗り＋✓、行ったことがある（メモ）＝淡いピン＋点線の輪＋「メモ」、送信待ち＝薄い塗り＋「待ち」、まだ＝白＋細い輪＋「まだ」</li>'
    '<li>字の大きさ：本文 15px、補足 14px、注・出典・札は <b>最小 13px</b>（11〜12px は使わない決まりのまま。今の画面案の測りも 12px 未満 0 を続ける）。端末の文字の大きさの設定に合わせて大きくなるようにする</li>'
    '</ul><h2>見回りの項目（改善担当へ）</h2>'
    '<p>画面の明るさを中にして窓際か屋外で、遅れの数字・主なボタン・印の有無が 0.5 秒で読めるか。PNG を白っぽくした写真（明るさ＋40%%・コントラスト−30%%）でも同じ所を見る</p></div>' % cts, 'doc', doc=True)

C2 = ('<div class="pg" style="gap:12px"><div class="hdr"><h1>屋外で読める形</h1></div>'
      '<div class="card"><div class="hd"><h2>図鑑の印（色だけにしない）</h2></div><div class="st3" style="grid-template-columns:repeat(4,1fr);margin-top:6px">'
      '<div class="t got"><span class="c">HND</span><b>押した</b><small>✓</small></div>'
      '<div class="t memo"><span class="c">ITM</span><b>メモ</b><small>点線</small></div>'
      '<div class="t wait"><span class="c">CTS</span><b>待ち</b><small>送信待ち</small></div>'
      '<div class="t yet"><span class="c">KMQ</span><b>まだ</b><small>細い輪</small></div></div></div>'
      '<div class="card"><div class="hd"><h2>出発の便（遅れ・欠航）</h2></div>'
      '<div class="dl"><span class="t2">14:35</span><span class="al jl">JL</span><span class="f">JL519 新千歳</span><span class="late">%s遅れ 38分</span></div>'
      '<div class="dl"><span class="t2">15:00</span><span class="al nh">NH</span><span class="f">NH63 新千歳</span><span class="late cx">欠航</span></div>'
      '<div class="dl"><span class="t2">15:10</span><span class="al jl">JL</span><span class="f">JL465 松山</span><span class="ontime">定刻</span></div>'
      '<p class="note" style="margin-top:4px;color:#5F6672">航空会社の運航情報 14:02・出典 ODPT</p></div>'
      '<button type="button" class="pill dark" style="min-height:52px;font-size:15px">羽田のいまを見る</button>'
      '</div>') % ic('warn')
add('c2-outdoor.html', 'C2 屋外で読める形の見本', C2 + tabs('home'))

# ───── ④ 意見を送る ─────
MYTOC = ('<div class="pg"><div class="hdr"><h1>マイページ</h1></div>'
         '<div class="card"><div class="row"><span class="lab">成績</span></div><div class="row" style="margin-top:6px;gap:18px">'
         '<span class="big0"><span class="num">16</span><span class="u">空港</span></span><span class="big0"><span class="num">30</span><span class="u">便</span></span><span class="big0"><span class="num">24,017</span><span class="u">km</span></span></div></div>'
         '<div class="card toc"><button type="button" class="it">%s表示の編集<span class="ch">%s</span></button>'
         '<button type="button" class="it">%s知らせ<span class="ch">%s</span></button>'
         '<button type="button" class="it">%sデータとバックアップ<span class="ch">%s</span></button>'
         '<button type="button" class="it">%sアカウント<span class="ch">%s</span></button>'
         '<button type="button" class="it new">%s<span>意見を送る<small>不具合・ほしい機能・空港データの直し</small></span><span class="ch">%s</span></button></div>'
         '</div>') % (ic('sliders'), ic('chev'), ic('bell'), ic('chev'), ic('shield'), ic('chev'), ic('user'), ic('chev'), ic('msg'), ic('chev'))
add('f1-entry.html', 'F1 マイページの入口（目次の最後）', MYTOC + tabs('me'))

def form(sel, extra='', text='', ph='どの画面で、何をしたら、どうなったか'):
    ch = ''.join('<button type="button" aria-pressed="%s">%s%s</button>' % ('true' if k == sel else 'false', ic(i), t)
                 for k, i, t in (('bug', 'bug', '不具合'), ('idea', 'idea', 'ほしい機能'), ('ap', 'map', '空港データの<br>直し')))
    return ('<div class="scrim"></div><div class="dlg"><span class="grab" aria-hidden="true"></span>'
            '<div class="hd2"><h2>意見を送る</h2><span class="sp"></span><button type="button" class="iconbtn" aria-label="閉じる">%s</button></div>'
            '<div class="choice">%s</div>%s'
            '<textarea class="ta" placeholder="%s">%s</textarea><div class="cnt">%d / 400</div>'
            '<div class="sendinfo"><b>いっしょに送るもの</b>：アプリの版・端末の種類・開いていた画面<br><b>送らないもの</b>：位置・記録・写真</div>'
            '<button type="button" class="pill dark" style="min-height:52px;font-size:16px">送る</button></div>') % (ic('x'), ch, extra, ph, text, len(text))
add('f2-form.html', 'F2 意見を送る（不具合）', MYTOC + tabs('me') + form('bug', text='運用タブで羽田を開くと、特別塗装機のカードが2回出ます'))
add('f3-airport.html', 'F3 空港データの直し（空港ページから）', MYTOC + tabs('me') + form('ap',
    '<p class="lbl">空港</p><div class="aprow"><span class="cd">HND</span><span class="n">東京国際空港（羽田）</span><button type="button" class="pill sm">変える</button></div>'
    '<p class="lbl">どこが違いますか</p><div class="chips"><button type="button">名前・読み</button><button type="button" aria-pressed="true">滑走路</button><button type="button">供用開始</button><button type="button">位置・範囲</button><button type="button">ほか</button></div>',
    text='', ph='正しい内容と、分かれば出典（公式の案内など）'))
add('f4-sent.html', 'F4 送ったあと', MYTOC + tabs('me') +
    '<div class="scrim"></div><div class="dlg" style="top:auto;height:auto"><span class="grab" aria-hidden="true"></span>'
    '<div class="sent"><span class="ok">%s</span><h2>受け取りました</h2><p>返事はしていませんが、すべて読んでいます。直したものは「最近の更新」に出します</p></div>'
    '<div class="card upd"><div class="hd"><h2>最近の更新</h2></div>'
    '<div class="it"><span class="d">11/25</span><p>羽田の3D を自由に動かせるようにしました<span class="mk2">意見から</span></p></div>'
    '<div class="it"><span class="d">11/24</span><p>マイページを成績の1枚と目次にしました</p></div></div>'
    '<button type="button" class="pill dark" style="min-height:52px">閉じる</button></div>' % ic('check'))

# ───── ⑤ 2回目以降の完了カード ─────
ST = json.load(open(HERE + '/src/stamps.json', encoding='utf-8'))
def done(line, note, cnt_html):
    return ('<img class="map" data-src="make/bg/bg-hnd" alt=""><div class="scrim"></div>'
            '<div class="stdlg"><div class="ticket"><b>HND</b><span>東京国際空港（羽田）</span><span class="sp"></span><span>2026.11.26 08:02</span></div>'
            '<div class="stampbig">%s</div><h3>東京国際空港（羽田）</h3>'
            '<div class="cnt1 newline">%s</div>'
            '<p class="nt">%s</p>'
            '<p class="nt">次の空港でチェックインすると、ここからのフライトが記録されます。</p>'
            '<div class="row2"><button type="button" class="pill btn2">閉じる</button><button type="button" class="pill dark">画像で共有</button></div>'
            '<button type="button" class="pill btn2" style="width:100%%;margin-top:8px">写真に押す</button></div>') % (ST['HND0'], cnt_html, note)
add('r1-repeat.html', 'R1 2回目以降（通算14回目・23日ぶり）', done('', 'この空港の印はもう持っています。訪問日として記録しました。',
    '<span class="u">通算</span><span class="num">14</span><span class="u">回目</span><span class="dot">・</span><span class="num">23</span><span class="u">日ぶり</span>'))
add('r2-sameday.html', 'R2 同じ日の2回目', done('', 'この空港の印はもう持っています。訪問日として記録しました。',
    '<span class="u">今日</span><span class="num">2</span><span class="u">回目</span><span class="dot">・</span><span class="u">通算</span><span class="num">15</span><span class="u">回目</span>'))
add('r3-long.html', 'R3 久しぶり（1年以上）', done('', 'この空港の印はもう持っています。訪問日として記録しました。',
    '<span class="u">通算</span><span class="num">3</span><span class="u">回目</span><span class="dot">・</span><span class="num">1</span><span class="u">年</span><span class="num">2</span><span class="u">か月ぶり</span>'))

json.dump(S, open(HERE + '/screens.json', 'w', encoding='utf-8'), ensure_ascii=False)
