# -*- coding: utf-8 -*-
# はじめて開いたときの流れの画面案を組み立てる（外部の読み込みなし）。?night=1 で夜。
# 地図は design/home-airport の capture_bg.py が今のアプリ（デモ）から撮ったもの（make/bg/）。
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
VARS = open(HERE + '/src/vars.css', encoding='utf-8').read()
POS = json.load(open(HERE + '/bg/bgpos.json'))
APS = json.load(open(HERE + '/src/aps.json', encoding='utf-8'))
REG = {'北海道': '北海道', '青森県': '東北', '岩手県': '東北', '宮城県': '東北', '秋田県': '東北', '山形県': '東北', '福島県': '東北',
       '東京都': '関東', '千葉県': '関東', '茨城県': '関東', '新潟県': '中部', '富山県': '中部', '石川県': '中部', '福井県': '中部', '長野県': '中部', '静岡県': '中部', '愛知県': '中部', '岐阜県': '中部',
       '大阪府': '近畿', '兵庫県': '近畿', '和歌山県': '近畿', '鳥取県': '中国・四国', '島根県': '中国・四国', '岡山県': '中国・四国', '広島県': '中国・四国', '山口県': '中国・四国',
       '徳島県': '中国・四国', '香川県': '中国・四国', '愛媛県': '中国・四国', '高知県': '中国・四国'}
def region(pref): return REG.get(pref, '九州・沖縄')
OVR = {'HND': '羽田', 'ITM': '伊丹', 'NGO': '中部', 'KIX': '関西', 'CTS': '新千歳', 'OKA': '那覇', 'FUK': '福岡', 'NRT': '成田'}
def SHORT(n, c=''): return OVR.get(c) or n.replace('国際空港', '').replace('空港', '').split('（')[0]

P = {
 'pin': '<path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
 'check': '<path d="M5 12.5l4.2 4L19 7"/>',
 'chev': '<path d="M9 6l6 6-6 6"/>',
 'down': '<path d="M6 9l6 6 6-6"/>',
 'up': '<path d="M6 15l6-6 6 6"/>',
 'back': '<path d="M15 6l-6 6 6 6"/>',
 'plus': '<path d="M12 5v14M5 12h14"/>',
 'loc': '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
 'bell': '<path d="M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0"/>',
 'cam': '<path d="M4 8.5h3l1.5-2h7l1.5 2h3v10H4z"/><circle cx="12" cy="13" r="3.3"/>',
 'stairs': '<path d="M5 19h4v-4h4v-4h4V7h3"/>',
 'leaf': '<path d="M5 19c0-8 5-13 14-13 0 9-5 14-13 14M5 19l7-7"/>',
 'later': '<circle cx="12" cy="12" r="8"/><path d="M12 8v4.5l3 2"/>',
 'cloud': '<path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.2 11 3.5 3.5 0 0 0 7 18z"/><path d="M12 15v-4.5M10 12.5l2-2 2 2"/>',
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
 'compass': '<circle cx="12" cy="12" r="8.5" stroke-dasharray="2.2 2.2"/><path d="M8 16l2.5-6.5L17 7l-2.5 6.5z"/>',
 'home': '<path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
 'book': '<path d="M4 5.5c3-1.3 5.5-1 8 1 2.5-2 5-2.3 8-1v13c-3-1.3-5.5-1-8 1-2.5-2-5-2.3-8-1zM12 6.5v13"/>',
 'plane': '<path d="M21 4.5c-.6-.6-2-.5-2.9.4L14 9 5.5 7 4 8.5l7 3.5-3.2 3.2-2.6-.4L4 16l3.3 1.7L9 21l1.2-1.2-.4-2.6L13 14l3.5 7 1.5-1.5L16 11l4.1-4.1c.9-.9 1-2.3.4-2.9z"/>',
 'ops': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/><path d="M12 12l5.5-5.5"/>',
 'locate': '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
 'close': '<path d="M6 6l12 12M18 6L6 18"/>',
}
def ic(n, cls='ic'): return '<svg class="%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, P[n])

CSS = r'''
*{box-sizing:border-box;margin:0;padding:0}
[hidden]{display:none!important}
html,body{height:100%;background:var(--bg);color:var(--ink);font-family:var(--gothic);-webkit-text-size-adjust:100%}
body{overflow:hidden}
button{font:inherit;color:inherit;border:0;background:none;cursor:pointer;-webkit-tap-highlight-color:transparent}
svg.ic{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
:root{--memo:#F7DCE3;--memo-ink:#9D2B48;--memo-dot:#E8A3B4;--gold:#E9C46A}
:root[data-night=on]{--memo:rgba(244,114,152,.16);--memo-ink:#F9A8C0;--memo-dot:#F39AB2;--gold:#D9B45C}
.num{font-weight:800;font-variant-numeric:tabular-nums;color:var(--strong);letter-spacing:-.01em}
.u{font-size:13px;color:var(--mute);font-weight:700;margin-left:3px}
.scr{position:relative;height:100%;display:flex;flex-direction:column}
.body{flex:1;overflow:hidden;padding:0 20px}
.foot{padding:12px 20px 26px;display:flex;flex-direction:column;gap:6px;background:linear-gradient(to bottom,transparent,var(--bg) 18px)}
.top{display:flex;align-items:center;gap:8px;padding:12px 12px 4px 8px;min-height:60px}
.top .bk{width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:999px;color:var(--sub)}
.steps{display:flex;gap:6px;align-items:center}
.steps i{width:22px;height:6px;border-radius:3px;background:var(--bar)}
.steps i.on{background:var(--strong)}
:root[data-night=on] .steps i.on{background:#E5E7EB}
.steps span{margin-left:6px;font-size:13px;font-weight:700;color:var(--mute)}
.top .skip{margin-left:auto;min-height:44px;padding:0 12px;font-size:14px;font-weight:700;color:var(--sub)}
h1{font-size:25px;font-weight:800;color:var(--strong);line-height:1.4;letter-spacing:.01em}
.lead{margin-top:8px;font-size:15px;color:var(--sub);line-height:1.7}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:16px}
.lab{font-size:13px;font-weight:700;color:var(--sub)}
.note{font-size:13px;color:var(--mute);line-height:1.6}
.row{display:flex;align-items:center;gap:10px}
.sp{flex:1}
.cta{width:100%;min-height:56px;border-radius:999px;background:var(--strong);color:#fff;font-size:17px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:8px}
:root[data-night=on] .cta{background:#F3F4F6;color:#111827}
.sub2{min-height:44px;font-size:14px;font-weight:700;color:var(--sub);display:flex;align-items:center;justify-content:center;gap:4px}
.sub2 b{color:var(--strong)}
.pill{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-weight:800;font-size:14px;color:var(--strong);white-space:nowrap}
.pill svg.ic{width:18px;height:18px}
/* 行った空港のピル：選ぶと淡いピン色（印とは別の見た目） */
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:5px;min-height:44px;padding:0 15px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:700;color:var(--strong)}
.chip svg.ic{width:16px;height:16px;display:none}
.chip[aria-pressed=true]{background:var(--memo);color:var(--memo-ink);box-shadow:inset 0 0 0 1.5px var(--memo-dot)}
.chip[aria-pressed=true] svg.ic{display:block}
.count{display:flex;align-items:baseline;gap:4px}
.count .num{font-size:52px;line-height:1}
.count .num.bump{animation:bump .3s var(--ease)}
@keyframes bump{40%{transform:translateY(-3px) scale(1.06)}}
.count .u{font-size:15px}
.zero{font-size:20px;font-weight:800;color:var(--strong)}
.sec{margin-top:18px}
.sec h2{font-size:15px;font-weight:800;color:var(--strong);margin-bottom:10px}
.reg{background:var(--card);border-radius:20px;box-shadow:var(--shadow);margin-top:8px}
.reg>button{width:100%;min-height:52px;display:flex;align-items:center;gap:8px;padding:0 16px;font-size:15px;font-weight:800;color:var(--strong)}
.reg>button small{font-size:13px;color:var(--mute);font-weight:700}
.reg>button .c{margin-left:auto;font-size:13px;font-weight:800;color:var(--memo-ink)}
.reg>button svg{width:18px;height:18px;color:var(--mute)}
.reg .chips{padding:0 12px 14px}
.reg .chip{box-shadow:none;background:var(--track)}
.reg .chip[aria-pressed=true]{background:var(--memo);box-shadow:inset 0 0 0 1.5px var(--memo-dot)}
.memo-note{display:flex;gap:10px;align-items:flex-start;margin-top:12px;padding:12px 14px;border-radius:18px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--ink);line-height:1.6}
.memo-note .dot{flex:none;width:12px;height:12px;border-radius:50%;background:var(--memo-dot);margin-top:4px}
.memo-note .dot.st{background:var(--strong)}
/* 使い方 */
.opt{display:flex;align-items:center;gap:14px;min-height:72px;padding:12px 16px;border-radius:22px;background:var(--card);box-shadow:var(--shadow);text-align:left;width:100%}
.opt+.opt{margin-top:10px}
.opt .ico{width:44px;height:44px;border-radius:14px;background:var(--track);display:flex;align-items:center;justify-content:center;color:var(--strong)}
.opt b{display:block;font-size:16px;font-weight:800;color:var(--strong)}
.opt small{display:block;font-size:13px;color:var(--sub);line-height:1.5}
.opt[aria-pressed=true]{box-shadow:inset 0 0 0 2px var(--strong),var(--shadow)}
:root[data-night=on] .opt[aria-pressed=true]{box-shadow:inset 0 0 0 2px #E5E7EB}
/* 予定 */
.fld{display:flex;flex-direction:column;gap:2px;min-height:60px;padding:8px 14px;border-radius:16px;background:var(--track);justify-content:center;text-align:left;width:100%}
.fld small{font-size:12px;font-weight:700;color:var(--mute)}
.fld b{font-size:18px;font-weight:800;color:var(--strong)}
.fld b em{font-style:normal;font-size:13px;color:var(--sub);font-weight:700;margin-left:6px}
.fld.ph b{color:var(--mute);font-weight:700;font-size:15px}
.frow{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center}
.frow .ar{color:var(--mute);font-weight:800}
.or{text-align:center;font-size:13px;font-weight:700;color:var(--mute);margin:14px 0}
.ap1 .chip{box-shadow:none;background:var(--track)}
.ap1 .chip[aria-pressed=true]{background:var(--strong);color:#fff;box-shadow:none}
:root[data-night=on] .ap1 .chip[aria-pressed=true]{background:#E5E7EB;color:#111827}
/* できた記録 */
.made{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.made .card{padding:14px}
.made .num{font-size:32px}
.made .wide{grid-column:1/-1;display:flex;align-items:center;gap:12px}
.perm{display:flex;gap:12px;align-items:flex-start}
.perm+.perm{margin-top:14px}
.perm .ico{width:40px;height:40px;border-radius:12px;background:var(--track);display:flex;align-items:center;justify-content:center;color:var(--strong);flex:none}
.perm b{display:block;font-size:15px;font-weight:800;color:var(--strong)}
.perm b small{font-size:12px;color:var(--mute);font-weight:700;margin-left:6px}
.perm p{font-size:13px;color:var(--sub);line-height:1.6}
/* 導入の地図 */
.vals{margin-top:16px;display:flex;flex-direction:column;gap:12px}
.vals div{display:flex;gap:12px;align-items:flex-start}
.vals svg.ic{width:20px;height:20px;color:var(--sub);margin-top:2px}
.vals b{display:block;font-size:15px;font-weight:800;color:var(--strong)}
.vals span{font-size:13px;color:var(--sub);line-height:1.5}
.vals small{display:block;font-size:13px}
@media (max-height:700px){.hero{height:28%}.vals{gap:6px;margin-top:12px}.vals small{display:none}}
.hero{position:relative;height:40%;overflow:hidden;border-radius:0 0 34px 34px;background:var(--card)}
.hero img{position:absolute;left:50%;top:-6%;width:150%;transform:translateX(-50%);opacity:.9}
:root[data-night=on] .hero img{filter:invert(.92) hue-rotate(180deg) saturate(.5) brightness(.85)}
.hero svg.mk{position:absolute;left:50%;top:-6%;width:150%;height:auto;transform:translateX(-50%)}
.mk .m{fill:var(--memo-dot)} .mk .s{fill:var(--strong)} .mk .nv{fill:var(--card);stroke:#B4BBC5;stroke-width:1.2}
:root[data-night=on] .mk .s{fill:#E5E7EB}
.mk .arc{fill:none;stroke:#C8102E;stroke-width:2;stroke-dasharray:5 5;opacity:.8}
.hero .fade{position:absolute;left:0;right:0;bottom:0;height:60px;background:linear-gradient(transparent,var(--card))}
/* ホーム（着地） */
.map{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center}
:root[data-night=on] .map{filter:invert(.92) hue-rotate(180deg) saturate(.5) brightness(.85)}
.mapmk{position:absolute;inset:0;width:100%;height:100%}
.tb{position:absolute;top:14px;left:14px;right:14px;display:flex;align-items:center;gap:8px;z-index:3}
.appbtn{width:44px;height:44px;border-radius:14px;background:var(--card);box-shadow:var(--shadow);display:flex;align-items:center;justify-content:center;color:#C8102E}
.mchip{white-space:nowrap;display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:0 12px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.mchip i{width:9px;height:9px;border-radius:50%;background:var(--memo-dot)}
.mypg{white-space:nowrap;margin-left:auto;display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:800;color:var(--strong)}
.sheet{position:absolute;left:0;right:0;bottom:0;z-index:4;background:var(--bg);border-radius:26px 26px 0 0;box-shadow:0 -12px 30px -14px rgba(17,24,39,.28);padding:8px 16px 100px;display:flex;flex-direction:column;gap:12px}
:root[data-night=on] .sheet{background:#0F141B}
.grab{display:block;width:44px;height:14px;margin:0 auto;position:relative}
.grab::after{content:"";position:absolute;left:4px;right:4px;top:3px;height:5px;border-radius:3px;background:#C9CED6}
.flip{display:inline-flex;gap:3px}
.flip span{position:relative;width:24px;height:32px;border-radius:5px;background:#141A22;color:#F2B84B;font-weight:800;font-size:19px;display:flex;align-items:center;justify-content:center;font-family:ui-monospace,"SF Mono",Menlo,monospace}
.flip span::after{content:"";position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(0,0,0,.6)}
.try{position:relative;background:var(--deep,#0F1B2D);color:#F9FAFB;border-radius:22px;padding:16px 16px 14px}
:root[data-night=on] .try{background:#1B1F26;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
.try b{display:block;font-size:16px;font-weight:800}
.try p{margin-top:4px;font-size:13px;color:#C9D1DB;line-height:1.6;padding-right:30px}
.try .x{position:absolute;right:4px;top:4px;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:#A7B0BC}
.try .go{margin-top:10px;display:inline-flex;align-items:center;gap:4px;min-height:44px;padding:0 16px;border-radius:999px;background:#fff;color:#111827;font-size:14px;font-weight:800}
.tabs{position:absolute;left:12px;right:12px;bottom:14px;z-index:6;display:grid;grid-template-columns:repeat(5,1fr);padding:6px;border-radius:999px;background:var(--nav-glass);box-shadow:var(--nav-shadow);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}
.tabs button{display:flex;flex-direction:column;align-items:center;gap:2px;padding:7px 0 9px;min-height:56px;font-size:12px;font-weight:700;color:var(--nav-ink)}
.tabs button[aria-current=page]{color:var(--acc)}
@media (max-width:380px){.mypg{padding:0 12px}.mypg span{display:none}}
/* 下から出るシート（案B のバックアップ） */
.scrim{position:absolute;inset:0;background:rgba(17,24,39,.36);z-index:7}
.bsheet{position:absolute;left:0;right:0;bottom:0;z-index:8;background:var(--card);border-radius:26px 26px 0 0;padding:10px 20px 28px}
.bsheet h2{font-size:20px;font-weight:800;color:var(--strong);line-height:1.4;margin-top:6px}
.bsheet p{margin-top:6px;font-size:14px;color:var(--sub);line-height:1.7}
.bsheet .free{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;background:rgba(21,128,61,.10);color:var(--ok);font-size:13px;font-weight:800}
.inp{margin-top:14px;min-height:56px;border-radius:16px;background:var(--track);display:flex;align-items:center;padding:0 16px;font-size:16px;color:var(--mute)}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
'''
JS = r'''
(function(){var q=new URLSearchParams(location.search),r=document.documentElement;if(q.get('night')==='1')r.dataset.night='on';
 var small=innerWidth<380||innerHeight<700;
 document.querySelectorAll('img[data-src]').forEach(function(m){m.src=m.dataset.src+(small?'-667':'')+'.png'});
 document.querySelectorAll('svg[data-v]').forEach(function(s){s.innerHTML=s.dataset[small?'s':'v']});
 // 行った空港：押すと数字が増える
 var cnt=document.querySelector('[data-count]'),btn=document.querySelector('[data-next]');
 function upd(){var n=new Set([].map.call(document.querySelectorAll('.chips [aria-pressed=true]'),function(x){return x.dataset.c})).size;if(!cnt)return;
   var box=cnt.closest('.card');box.querySelector('.has').hidden=!n;box.querySelector('.zero').hidden=!!n;
   cnt.textContent=n;cnt.classList.remove('bump');void cnt.offsetWidth;cnt.classList.add('bump');
   if(btn)btn.textContent=n?n+'空港で次へ':'まだない・次へ';}
 document.querySelectorAll('.chips .chip').forEach(function(c){c.addEventListener('click',function(){var on=c.getAttribute('aria-pressed')!=='true';
   document.querySelectorAll('.chip[data-c="'+c.dataset.c+'"]').forEach(function(x){x.setAttribute('aria-pressed',on)});
   if(!c.closest('.ap1'))upd();else document.querySelectorAll('.ap1 .chip').forEach(function(x){if(x!==c)x.setAttribute('aria-pressed','false')})})});
 document.querySelectorAll('.opt').forEach(function(o){o.addEventListener('click',function(){document.querySelectorAll('.opt').forEach(function(x){x.setAttribute('aria-pressed',x===o)})})});
 document.querySelectorAll('.reg>button').forEach(function(b){b.addEventListener('click',function(){var c=b.nextElementSibling;c.hidden=!c.hidden})});
})();
'''
def page(name, title, body):
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s</style></head><body>%s<script>%s</script></body></html>') % (title, VARS, CSS, body, JS)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html); print('書いた', name)

def top(n, total=4, skip=True, back=True):
    st = ''.join('<i class="%s"></i>' % ('on' if k < n else '') for k in range(total))
    return ('<div class="top">%s<div class="steps">%s<span>%d / %d</span></div>%s</div>') % (
        '<button type="button" class="bk" aria-label="もどる">%s</button>' % ic('back') if back else '<span style="width:8px"></span>', st, n, total,
        '<button type="button" class="skip">あとで</button>' if skip else '')

MEMO = {'HND', 'CTS', 'ITM', 'FUK', 'OKA', 'NRT'}
def marks(key, memo=MEMO, arc=False, stamp=()):
    d = POS[key]; o = []
    for a in APS:
        c = a[2]
        if c not in d: continue
        x, y = d[c]
        if c in stamp: o.append('<circle class="s" cx="%.1f" cy="%.1f" r="5"/>' % (x, y))
        elif c in memo: o.append('<circle class="m" cx="%.1f" cy="%.1f" r="5.5"/>' % (x, y))
        else: o.append('<circle class="nv" cx="%.1f" cy="%.1f" r="3.2"/>' % (x, y))
    if arc:
        (x1, y1), (x2, y2) = d['HND'], d['CTS']
        o.insert(0, '<path class="arc" d="M%.1f %.1fQ%.1f %.1f %.1f %.1f"/>' % (x1, y1, (x1 + x2) / 2 + 46, (y1 + y2) / 2, x2, y2))
    return ''.join(o).replace('"', '&quot;')

def chip(code, name, on=False):
    return '<button type="button" class="chip" data-c="%s" aria-pressed="%s">%s%s</button>' % (code, 'true' if on else 'false', ic('pin'), name)

# ───── 1 導入 ─────
INTRO = ('<div class="scr"><div class="hero"><img src="make/bg/bg-wide.png" alt="">'
         '<svg class="mk" viewBox="0 0 390 844" data-v="%s" data-s="%s"></svg><div class="fade"></div></div>'
         '<div class="body" style="padding-top:20px"><h1>日本の空港を、<br>旅の記録に。</h1>'
         '<p class="lead">空港に着いたらチェックインして印を集める。乗った便も、地図に残していけます。</p>'
         '<div class="vals"><div>%s<span><b>空港で印を押す</b><small>国内86の空港に印があります</small></span></div><div>%s<span><b>乗った便を残す</b><small>行った空港と飛んだ道が地図に</small></span></div>'
         '<div>%s<span><b>空港のいまを見る</b><small>今日の便や特別塗装機を家からでも</small></span></div></div></div>'
         '<div class="foot"><button type="button" class="cta">はじめる</button>'
         '<div class="row" style="justify-content:center;gap:4px"><button type="button" class="sub2">もう使っている人は<b>ログイン</b></button>'
         '<span class="note">・</span><button type="button" class="sub2"><b>デモで試す</b></button></div></div></div>') % (
    marks('wide', arc=True, stamp={'HND', 'CTS'}), marks('wide', arc=True, stamp={'HND', 'CTS'}), ic('pin'), ic('plane'), ic('ops'))
page('o1-intro.html', 'O1 導入', INTRO)

# ───── 2 使い方（今のアンケートをここへ） ─────
OPTS = [('cam', '飛行機を撮る', '空港の運用や特別塗装機を見たい'), ('stairs', '修行をする', '乗った便とポイントを数えたい'),
        ('leaf', '気軽に集める', '旅のついでに空港の印を集めたい'), ('later', 'あとで決める', 'いまは全部をそのまま出す')]
PERSONA = ('<div class="scr">%s<div class="body"><h1>どんなふうに<br>使いますか？</h1>'
           '<p class="lead">はじめに出す画面を合わせます。あとから設定でいつでも変えられます</p><div style="margin-top:18px">%s</div></div>'
           '<div class="foot"><button type="button" class="cta">次へ</button></div></div>') % (
    top(1), ''.join('<button type="button" class="opt" aria-pressed="%s"><span class="ico">%s</span><span><b>%s</b><small>%s</small></span></button>' % ('true' if i == 2 else 'false', ic(a), b, c) for i, (a, b, c) in enumerate(OPTS)))
page('o2-persona.html', 'O2 使い方を選ぶ', PERSONA)

# ───── 3 行ったことがある空港 ─────
POP = [('HND', '羽田'), ('NRT', '成田'), ('CTS', '新千歳'), ('ITM', '伊丹'), ('KIX', '関西'), ('FUK', '福岡'), ('OKA', '那覇'), ('NGO', '中部'), ('KOJ', '鹿児島')]
def visited(sel, open_reg='関東'):
    n = len(sel)
    regs = []
    for r in ('北海道', '東北', '関東', '中部', '近畿', '中国・四国', '九州・沖縄'):
        aps = [a for a in APS if region(a[3]) == r]
        c = sum(1 for a in aps if a[2] in sel)
        regs.append('<div class="reg"><button type="button">%s<small>%d空港</small><span class="c">%s</span>%s</button><div class="chips"%s>%s</div></div>' % (
            r, len(aps), '%d 選択' % c if c else '', ic('up' if r == open_reg else 'down'), '' if r == open_reg else ' hidden',
            ''.join(chip(a[2], SHORT(a[1], a[2]), a[2] in sel) for a in aps)))
    return ('<div class="scr">%s<div class="body" style="overflow:auto"><h1>行ったことがある空港を<br>選んでください</h1>'
            '<div class="card" style="margin-top:14px"><div class="has"%s><span class="lab">選んだ空港</span><div class="count"><span class="num" data-count>%d</span><span class="u">/ 86 空港</span></div></div>'
            '<div class="zero"%s>これから最初の1空港へ</div><p class="note" style="margin-top:4px">あとからいつでも足したり外したりできます</p></div>'
            '<div class="memo-note"><span class="dot"></span><span>ここで選んだ空港は<b>「行ったことがある（メモ）」</b>として淡いピンで残ります。次に行ってチェックインすると、<b>印</b>に変わります</span></div>'
            '<div class="sec"><h2>よく選ばれる空港</h2><div class="chips">%s</div></div>'
            '<div class="sec" style="padding-bottom:20px"><h2>地方から探す</h2>%s</div></div>'
            '<div class="foot"><button type="button" class="cta" data-next>%s</button></div></div>') % (
        top(2), '' if n else ' hidden', n, ' hidden' if n else '', ''.join(chip(c, nm, c in sel) for c, nm in POP), ''.join(regs),
        '%d空港で次へ' % n if n else 'まだない・次へ')
page('o3-visited.html', 'O3 行ったことがある空港（6つ選んだ）', visited(MEMO))
page('o3b-zero.html', 'O3b 行ったことがある空港（0）', visited(set(), open_reg=''))

# ───── 4 次のフライトか、いちばん身近な空港 ─────
def plan(filled=True):
    f = ('<div class="frow"><button type="button" class="fld"><small>出発</small><b>羽田<em>HND</em></b></button><span class="ar">→</span>'
         '<button type="button" class="fld"><small>到着</small><b>新千歳<em>CTS</em></b></button></div>'
         '<button type="button" class="fld" style="margin-top:8px"><small>日付</small><b>12月9日（水）<em>あと14日</em></b></button>') if filled else (
         '<div class="frow"><button type="button" class="fld ph"><small>出発</small><b>空港を選ぶ</b></button><span class="ar">→</span>'
         '<button type="button" class="fld ph"><small>到着</small><b>空港を選ぶ</b></button></div>'
         '<button type="button" class="fld ph" style="margin-top:8px"><small>日付</small><b>日付を選ぶ</b></button>')
    aps = [('HND', '羽田'), ('ITM', '伊丹'), ('CTS', '新千歳'), ('FUK', '福岡'), ('NGO', '中部'), ('OKA', '那覇')]
    return ('<div class="scr">%s<div class="body" style="overflow:auto"><h1>次に飛行機に乗る<br>予定はありますか？</h1>'
            '<p class="lead">入れておくと、ホームに出発までの日数が出ます。便名はあとからで大丈夫です</p>'
            '<div class="card" style="margin-top:14px"><span class="lab">次のフライト</span><div style="margin-top:10px">%s</div></div>'
            '<p class="or">予定はまだない</p>'
            '<div class="card ap1"><span class="lab">いちばん身近な空港を1つ</span><p class="note" style="margin:2px 0 10px">ホームからその空港の今日の便や特別塗装機をすぐ見られます</p>'
            '<div class="chips">%s<button type="button" class="chip" data-c="etc" aria-pressed="false">ほかの空港</button></div></div><div style="height:16px"></div></div>'
            '<div class="foot"><button type="button" class="cta">%s</button></div></div>') % (
        top(3), f, ''.join(chip(c, n, (not filled) and c == 'HND') for c, n in aps), 'この予定で次へ' if filled else '羽田で次へ')
page('o4-plan.html', 'O4 次のフライト（入れた）', plan(True))
page('o4b-myap.html', 'O4b 予定なし・いちばん身近な空港', plan(False))

# ───── 5 できた記録と、位置・通知の理由 ─────
READY = ('<div class="scr">%s<div class="body"><h1>あなたのそらメモが<br>できました</h1>'
         '<div class="made" style="margin-top:14px"><div class="card"><span class="lab">行ったことがある</span><div class="count"><span class="num">6</span><span class="u">空港</span></div></div>'
         '<div class="card"><span class="lab">次のフライト</span><div class="count"><span class="u" style="margin:0 2px 0 0">あと</span><span class="num">14</span><span class="u">日</span></div></div>'
         '<div class="card wide"><div style="flex:1"><span class="lab">最初の小目標</span><div style="font-size:15px;font-weight:800;color:var(--strong)">関東 2/6・羽田でチェックインして印に</div></div></div></div>'
         '<div class="card" style="margin-top:12px"><div class="perm"><span class="ico">%s</span><div><b>位置情報</b><p>空港の中にいるか確かめて、印を押すために使います。アプリを開いている間だけで、送るのは印を押すときだけです</p></div></div>'
         '<div class="perm"><span class="ico">%s</span><div><b>通知<small>入れなくても使えます</small></b><p>出発の前の日と、ピン止めした空港の知らせに使います</p></div></div></div></div>'
         '<div class="foot"><button type="button" class="cta">次へ（許可を聞きます）</button><button type="button" class="sub2">あとで設定する</button></div></div>') % (top(4, skip=False), ic('loc'), ic('bell'))
page('o5-ready.html', 'O5 できた記録と許可の理由', READY)

# ───── 6 ホームに着いた ─────
def tabs():
    items = [('ホーム', 'home', 1), ('図鑑', 'book', 0), ('フライト', 'plane', 0), ('運用', 'ops', 0), ('修行', 'stairs', 0)]
    return '<nav class="tabs">%s</nav>' % ''.join('<button type="button"%s>%s%s</button>' % (' aria-current="page"' if c else '', ic(i), l) for l, i, c in items)
HOME = ('<div class="scr"><img class="map" data-src="make/bg/bg-wide" alt=""><svg class="mapmk mk" data-v="%s" data-s="%s"></svg>'
        '<div class="tb"><span class="appbtn">%s</span><span class="mchip"><i></i>メモ 6</span><span class="mchip">印 0<span class="u" style="font-size:12px">/86</span></span>'
        '<button type="button" class="mypg" aria-label="マイページ">%s<span>マイページ</span></button></div>'
        '<section class="sheet"><span class="grab"></span>'
        '<div class="try"><button type="button" class="x" aria-label="閉じる">%s</button><b>いま空港にいなくても試せます</b>'
        '<p>羽田の今日の便や、いまいる特別塗装機をのぞいてみませんか</p><button type="button" class="go">羽田のいまを見てみる%s</button></div>'
        '<div class="card"><div class="row"><span class="lab">次のフライト</span><span class="sp"></span><span style="font-size:20px;font-weight:800;color:var(--strong)">HND → CTS</span></div>'
        '<div class="count" style="margin-top:2px"><span class="u" style="margin:0 2px 0 0">あと</span><span class="num" style="font-size:40px">14</span><span class="u">日</span><span class="sp"></span><span class="note">12月9日（水）</span></div></div>'
        '<div class="card"><span class="lab">いちばん近い空港</span><div class="row" style="margin-top:8px"><span class="flip"><span>H</span><span>N</span><span>D</span></span>'
        '<b style="flex:1;font-size:16px;color:var(--strong)">羽田空港</b><span class="num" style="font-size:28px">28.4</span><span class="u">km</span></div></div>'
        '</section>%s</div>') % (marks('wide', arc=True), marks('wide-667', arc=True), ic('compass'), ic('user'), ic('close'), ic('chev'), tabs())
page('o6-home.html', 'O6 ホームに着いた（初回だけの案内）', HOME)

# ───── 案B：あとで登録（初めてのチェックインのとき） ─────
BREG = ('<div class="scr"><img class="map" data-src="make/bg/bg-wide" alt=""><svg class="mapmk mk" data-v="%s" data-s="%s"></svg><div class="scrim"></div>'
        '<section class="bsheet"><span class="grab"></span><span class="free">無料</span><h2>印を残すために、<br>記録をバックアップします</h2>'
        '<p>印はサーバーで確かめてから押します。メールで登録すると、いままでのメモ（6空港）と予定もいっしょに保存され、機種を変えても戻せます</p>'
        '<div class="inp">メールアドレス</div><div style="margin-top:12px"><button type="button" class="cta">確認コードを送る</button></div>'
        '<button type="button" class="sub2" style="width:100%%">いまはやめる（印は押されません）</button></section></div>') % (marks('wide'), marks('wide-667'))
page('b1-backup.html', '案B 初めてのチェックインで登録', BREG)
