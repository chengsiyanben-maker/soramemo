# -*- coding: utf-8 -*-
# design/home-airport の build.py から写した共通の部品（地図・シート・タブ・カード）。gemini-1126 の build.py が読み込む。
# 地図の背景は capture_bg.py が今のアプリ（デモ）から撮ったもの（make/bg/）。外部の読み込みはなし。
# ?night=1 で夜、?tabs=a で下のタブを4つ（design/ia-ops の案A）、なしで今の5つ（案B）。
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
VARS = open(HERE + '/src/vars.css', encoding='utf-8').read()
POS = json.load(open(HERE + '/bg/bgpos.json'))
APS = json.load(open(HERE + '/src/aps.json', encoding='utf-8'))

P = {
 'home': '<path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
 'book': '<path d="M4 5.5c3-1.3 5.5-1 8 1 2.5-2 5-2.3 8-1v13c-3-1.3-5.5-1-8 1-2.5-2-5-2.3-8-1zM12 6.5v13"/>',
 'plane': '<path d="M21 4.5c-.6-.6-2-.5-2.9.4L14 9 5.5 7 4 8.5l7 3.5-3.2 3.2-2.6-.4L4 16l3.3 1.7L9 21l1.2-1.2-.4-2.6L13 14l3.5 7 1.5-1.5L16 11l4.1-4.1c.9-.9 1-2.3.4-2.9z"/>',
 'ops': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/><path d="M12 12l5.5-5.5"/>',
 'stairs': '<path d="M5 19h4v-4h4v-4h4V7h3"/>',
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
 'pin': '<path d="M9 3.5h6l-1 5.5 3 3H7l3-3zM12 12v8.5"/>',
 'chev': '<path d="M9 6l6 6-6 6"/>',
 'up': '<path d="M6 15l6-6 6 6"/>',
 'plus': '<path d="M12 5v14M5 12h14"/>',
 'check': '<path d="M5 12.5l4.2 4L19 7"/>',
 'retry': '<path d="M19 12a7 7 0 1 1-2.05-4.95M19 4.5v3.8h-3.8"/>',
 'arrow': '<path d="M4 12h15M14 7l5 5-5 5"/>',
 'wifi': '<path d="M4 9a12 12 0 0 1 16 0M7 12.5a7.5 7.5 0 0 1 10 0M10 16a3 3 0 0 1 4 0M12 19.5h.01M3 3l18 18"/>',
 'locate': '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
 'records': '<rect x="4.5" y="4" width="15" height="16" rx="3"/><path d="M8.5 9h7M8.5 13h7M8.5 17h4"/>',
 'compass': '<circle cx="12" cy="12" r="8.5" stroke-dasharray="2.2 2.2"/><path d="M8 16l2.5-6.5L17 7l-2.5 6.5z"/>',
}
def ic(n, cls='ic'):
    return '<svg class="%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, P[n])

CSS = r'''
html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--gothic);-webkit-text-size-adjust:100%}
*{box-sizing:border-box;margin:0;padding:0}
button{font:inherit;color:inherit;border:0;background:none;cursor:pointer;-webkit-tap-highlight-color:transparent}
svg.ic{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.num{font-weight:800;font-variant-numeric:tabular-nums;color:var(--strong);letter-spacing:-.01em}
.u{font-size:13px;color:var(--mute);font-weight:700;margin-left:2px;letter-spacing:0}
:root{--gold:#E9C46A;--gold-ink:#111827;--deep:#0F1B2D;--deep-sub:#A7B0BC;--sheet:#EEF1F5}
:root[data-night=on]{--gold:#D9B45C;--deep:#1B1F26;--deep-sub:#AEB9C6;--sheet:#0F141B}
.ph{position:relative;width:100%;height:100%;overflow:hidden}
.map{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top center}
:root[data-night=on] .map{filter:invert(.92) hue-rotate(180deg) saturate(.5) brightness(.85)}
.mk{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
/* 地図の上 */
.topbar{position:absolute;top:14px;left:14px;right:14px;display:flex;align-items:center;gap:8px;z-index:3}
.appbtn{width:44px;height:44px;border-radius:14px;background:var(--card);box-shadow:var(--shadow);display:flex;align-items:center;justify-content:center;color:#C8102E}
.chip{display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:0 12px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.chip .u{font-size:12px}
.chip.in{background:var(--deep);color:#F9FAFB;box-shadow:none}
.chip.in i{width:8px;height:8px;border-radius:50%;background:#4ADE80}
.mypg{margin-left:auto;display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:800;color:var(--strong)}
:root[data-tabs=a] .mypg{display:none}
.attr{position:absolute;left:12px;z-index:2;padding:2px 10px;border-radius:999px;background:var(--card);font-size:12px;color:var(--sub);box-shadow:var(--shadow)}
.locbtn{position:absolute;right:14px;z-index:2;width:44px;height:44px;border-radius:50%;background:var(--card);box-shadow:var(--shadow);display:flex;align-items:center;justify-content:center;color:var(--strong)}
/* シート：線を使わず、灰色の地に白いカード */
.sheet{position:absolute;left:0;right:0;bottom:0;z-index:4;background:var(--sheet);border-radius:26px 26px 0 0;box-shadow:0 -12px 30px -14px rgba(17,24,39,.28);padding:8px 16px 0;overflow:hidden}
.grab{display:block;width:44px;height:20px;margin:0 auto;position:relative}
.grab::after{content:"";position:absolute;left:4px;right:4px;top:6px;height:5px;border-radius:3px;background:#C9CED6}
:root[data-night=on] .grab::after{background:#3A414C}
.sheet .in{display:flex;flex-direction:column;gap:12px;padding-top:4px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:16px}
.lab{font-size:13px;font-weight:700;color:var(--sub)}
.row{display:flex;align-items:center;gap:10px}
.sp{flex:1}
.pill{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:0 18px;border-radius:999px;background:var(--pill);font-weight:800;font-size:14px;color:var(--strong);white-space:nowrap}
.pill svg.ic{width:18px;height:18px}
.pill.dark{background:var(--strong);color:#fff}
:root[data-night=on] .pill.dark{background:transparent;color:#F3F4F6;box-shadow:inset 0 0 0 1.5px #F3F4F6}
.pill.sm{min-height:44px;padding:0 14px;font-size:13px}
.al{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:22px;padding:0 6px;border-radius:7px;font-size:12px;font-weight:800;letter-spacing:.04em}
.al.jl{background:rgba(200,16,46,.08);color:#A50D26}
.al.nh{background:rgba(28,79,160,.08);color:#1C4FA0}
:root[data-night=on] .al.jl{background:rgba(248,113,113,.12);color:#FCA5A5}
:root[data-night=on] .al.nh{background:rgba(147,197,253,.12);color:#BFDBFE}
.note{font-size:12px;color:var(--mute)}
/* 次のフライト */
.nf .big{display:flex;align-items:baseline;gap:4px;margin-top:2px}
.nf .big .num{font-size:44px;line-height:1.1}
.nf .big .u{font-size:15px}
.nf .rt{text-align:right}
.nf .rt .d{font-size:13px;font-weight:700;color:var(--sub)}
.nf .rt .c{font-size:22px;font-weight:800;color:var(--strong);letter-spacing:.04em;white-space:nowrap}
.nf .rt .c small{font-size:14px;color:var(--mute);margin:0 4px}
.nf .fl{margin-top:10px;display:flex;align-items:center;gap:8px;font-size:14px;color:var(--ink)}
.nf .fl b{font-weight:800;color:var(--strong)}
/* 近い空港（パタパタのコードは小さく残す。案内板風はここだけ） */
.flip{display:inline-flex;gap:3px}
.flip span{position:relative;width:24px;height:32px;border-radius:5px;background:#141A22;color:#F2B84B;font-weight:800;font-size:19px;display:flex;align-items:center;justify-content:center;font-family:ui-monospace,"SF Mono",Menlo,monospace}
.flip span::after{content:"";position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(0,0,0,.6)}
.flip.lg span{width:34px;height:44px;font-size:26px;border-radius:7px;background:#1E2836}
.near .nm{font-size:16px;font-weight:800;color:var(--strong);line-height:1.35}
.near .dist .num{font-size:30px}
.near .msg{margin-top:10px;font-size:13px;color:var(--sub)}
.near .act{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.near .act .pill.wide{width:100%;white-space:normal;text-align:left;min-height:52px;padding:8px 18px;line-height:1.4}
/* 小目標 */
.goal .num{font-size:28px}
.bar{position:relative;height:10px;border-radius:5px;background:var(--bar);overflow:hidden;margin-top:10px}
.bar i{position:absolute;left:0;top:0;bottom:0;border-radius:5px;background:var(--hero)}
.goal .sub{margin-top:8px;font-size:13px;color:var(--sub)}
.goals{display:flex;flex-direction:column;gap:14px}
/* 成績の帯（今の hstrip と同じ並び） */
.strip{display:flex;align-items:baseline;justify-content:space-around;padding:12px 8px}
.strip .k{font-size:13px;font-weight:700;color:var(--sub);margin-right:6px}
.strip .num{font-size:24px}
/* 一覧の行 */
.list .it{display:flex;align-items:center;gap:12px;min-height:52px}
.list .it+.it{margin-top:4px}
.list .it .c{width:46px;font-weight:800;color:var(--strong);letter-spacing:.04em}
.list .it .n{flex:1;font-size:14px;color:var(--ink)}
.list .it .num{font-size:18px}
/* 空港にいるとき：見出し */
.aphd{padding:0 4px}
.aphd h1{font-size:24px;font-weight:800;color:var(--strong);letter-spacing:.01em;line-height:1.3}
.aphd .vis{margin-top:2px;font-size:13px;color:var(--sub);font-weight:700}
.aphd .vis b{color:var(--strong);font-size:16px;font-weight:800}
.first{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;background:rgba(21,128,61,.10);color:var(--ok);font-size:13px;font-weight:800}
/* 案A：全幅のピル */
.ckpill{position:relative;width:100%;min-height:64px;border-radius:999px;background:var(--gold);color:var(--gold-ink);font-size:18px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:10px;box-shadow:0 10px 24px -10px rgba(161,120,20,.55);overflow:hidden}
.ckpill .stub{position:absolute;right:0;top:0;bottom:0;width:22%;border-left:2px dashed rgba(17,24,39,.28);display:flex;align-items:center;justify-content:center;transform-origin:0 100%}
.ckpill .stub svg{width:26px;height:26px}
.ckpill.tear .stub{animation:tear .36s cubic-bezier(.4,0,1,1) forwards}
@keyframes tear{0%{transform:none}40%{transform:translate(4px,-2px) rotate(-6deg)}100%{transform:translate(30px,40px) rotate(24deg);opacity:0}}
.ckdone{display:flex;align-items:center;gap:10px;min-height:56px;padding:0 20px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:15px;font-weight:800;color:var(--strong);animation:fadeIn .25s var(--ease) both}
.ckdone .ck{width:28px;height:28px;border-radius:50%;background:rgba(21,128,61,.12);color:var(--ok);display:flex;align-items:center;justify-content:center}
.ckdone .ck svg{width:18px;height:18px;stroke-width:2.4}
.ckdone small{margin-left:auto;font-size:13px;color:var(--mute);font-weight:700}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
/* 案B：今の黒いカード＋半券を下の横長に */
.bp{border-radius:24px;overflow:hidden;box-shadow:var(--shadow);background:var(--deep);color:#F9FAFB}
:root[data-night=on] .bp{box-shadow:inset 0 0 0 1px rgba(255,255,255,.08)}
.bp .top{padding:16px 16px 14px}
.bp .lb{font-size:13px;font-weight:700;color:var(--deep-sub)}
.bp .nm{font-size:18px;font-weight:800;line-height:1.35}
.bp .vis{font-size:13px;color:var(--deep-sub);font-weight:700}
.bp .vis b{color:#fff;font-size:16px}
.bp .pinpill{display:inline-flex;align-items:center;gap:5px;min-height:44px;padding:0 14px;border-radius:999px;box-shadow:inset 0 0 0 1.5px rgba(249,250,251,.6);font-size:13px;font-weight:800}
.bp .pinpill svg{width:17px;height:17px}
.stubrow{position:relative;height:72px;background:var(--gold);color:var(--gold-ink);display:flex;align-items:center;padding:0 16px 0 84px;font-weight:800;font-size:16px;touch-action:none;user-select:none}
.stubrow::before{content:"";position:absolute;left:12px;right:12px;top:0;border-top:2px dashed rgba(15,27,45,.55)}
.stubrow .kn{position:absolute;left:12px;top:12px;width:60px;height:48px;border-radius:999px;background:var(--deep);color:var(--gold);display:flex;align-items:center;justify-content:center;transition:transform .25s var(--ease)}
.stubrow .kn svg{width:24px;height:24px;stroke-width:2.2}
.stubrow small{display:block;font-size:12px;font-weight:700;opacity:.75}
.stubrow.off{background:#C9B78A}
:root[data-night=on] .stubrow.off{background:#7C6B45}
.donerow{display:flex;align-items:center;gap:10px;min-height:56px;padding:0 16px;background:rgba(255,255,255,.06);font-size:15px;font-weight:800}
.donerow .ck{width:28px;height:28px;border-radius:50%;background:rgba(74,222,128,.16);color:#4ADE80;display:flex;align-items:center;justify-content:center}
.donerow .ck svg{width:18px;height:18px;stroke-width:2.4}
.donerow small{margin-left:auto;font-size:13px;color:var(--deep-sub);font-weight:700}
.offbar{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:18px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--ink)}
.offbar svg{width:20px;height:20px;color:var(--sub);margin-top:1px}
.offbar b{display:block;font-size:14px;color:var(--strong)}
/* この空港のいま */
.now3{display:grid;grid-template-columns:1fr 1.25fr 1fr;gap:8px;margin-top:10px}
.now3 div{display:flex;flex-direction:column;gap:2px;min-width:0}
.now3 .k{font-size:12px;font-weight:700;color:var(--mute)}
.now3 .num{font-size:24px;line-height:1.2;white-space:nowrap}
.now3 .num.s{font-size:20px}
.now3 .u{font-size:12px;margin-left:1px}
.stale{margin-top:10px;font-size:13px;color:var(--sub)}
/* 今日の便を記録 */
.fc{display:flex;align-items:center;gap:10px;min-height:56px}
.fc+.fc{margin-top:6px}
.fc .t{font-size:20px}
.fc .to{flex:1;min-width:0;font-size:14px;color:var(--ink);line-height:1.35}
.fc .to b{display:block;font-size:13px;font-weight:800;color:var(--strong)}
.fc .rec{min-height:44px;padding:0 14px;border-radius:999px;background:var(--strong);color:#fff;font-size:13px;font-weight:800;white-space:nowrap}
:root[data-night=on] .fc .rec{background:transparent;color:#F3F4F6;box-shadow:inset 0 0 0 1.5px #F3F4F6}
.fc .rec.ghost{background:var(--pill);color:var(--strong);box-shadow:none}
.hd{display:flex;align-items:center;gap:8px}
.hd h2{font-size:16px;font-weight:800;color:var(--strong)}
.hd .more{margin-left:auto;display:inline-flex;align-items:center;gap:2px;min-height:44px;padding:0 4px 0 12px;font-size:13px;font-weight:800;color:var(--sub)}
.hd .more svg{width:16px;height:16px}
/* 下のタブ（差し替えられる部品） */
.tabs{position:absolute;left:12px;right:12px;bottom:14px;z-index:6;display:grid;grid-template-columns:repeat(5,1fr);padding:6px;border-radius:999px;background:var(--nav-glass);box-shadow:var(--nav-shadow);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px)}
:root[data-tabs=a] .tabs{grid-template-columns:repeat(4,1fr)}
.tabs button{display:flex;flex-direction:column;align-items:center;gap:2px;padding:7px 0 9px;min-height:56px;border-radius:999px;font-size:12px;font-weight:700;color:var(--nav-ink)}
.tabs button[aria-current=page]{color:var(--acc)}
.tabs .ta,.tabs .tb{display:contents}
.tabs .ta{display:none}
:root[data-tabs=a] .tabs .ta{display:contents}
:root[data-tabs=a] .tabs .tb{display:none}
/* 地図の印 */
.mk .v{fill:var(--strong)} .mk .nv{fill:#fff;stroke:#9AA3AF;stroke-width:1.5}
:root[data-night=on] .mk .v{fill:#E5E7EB} :root[data-night=on] .mk .nv{fill:#0F141B;stroke:#66778C}
.mk .arc{fill:none;stroke:#C8102E;stroke-width:2.2;stroke-dasharray:5 5;opacity:.85}
:root[data-night=on] .mk .arc{stroke:#FCA5A5}
.mk text{font:800 12px var(--gothic);fill:var(--strong);paint-order:stroke;stroke:#fff;stroke-width:3px}
:root[data-night=on] .mk text{fill:#F3F4F6;stroke:#0F141B}
.mk .me{fill:#2563EB;stroke:#fff;stroke-width:3}
.mk .meh{fill:rgba(37,99,235,.16)}
/* 札（印をもらった） */
.toast{position:absolute;left:50%;bottom:100px;z-index:9;display:flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border-radius:999px;background:#1F2937;color:#fff;font-size:14px;font-weight:700;white-space:nowrap;transform:translate(-50%,16px);opacity:0;transition:transform .25s var(--ease),opacity .25s var(--ease)}
.toast.show{transform:translate(-50%,0);opacity:1}
.toast svg{width:18px;height:18px;stroke:#86EFAC}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
'''

JS = r'''
(function(){
 var q=new URLSearchParams(location.search), r=document.documentElement;
 if(q.get('night')==='1')r.dataset.night='on';
 if(q.get('tabs')==='a')r.dataset.tabs='a';
 var small=innerWidth<380||innerHeight<700;
 document.querySelectorAll('img.map').forEach(function(m){m.src=m.dataset.src+(small?'-667':'')+'.png'});
 document.querySelectorAll('svg.mk[data-v]').forEach(function(s){s.innerHTML=s.dataset[small?'s':'v'];s.removeAttribute('data-v');s.removeAttribute('data-s')});
 // シートの高さ：小・ふつう・大（数字は画面の高さに対する割合）
 var sh=document.querySelector('.sheet');
 if(sh){var k={s:.25,m:.56,l:.86}[sh.dataset.h||'m'];var h=Math.round(innerHeight*k);if(sh.dataset.min)h=Math.max(h,+sh.dataset.min);sh.style.height=h+'px';
   var top=innerHeight-h; document.querySelectorAll('.attr').forEach(function(a){a.style.top=(top-34)+'px'});
   document.querySelectorAll('.locbtn').forEach(function(a){a.style.top=(top-58)+'px'});
   sh.querySelector('.in').style.paddingBottom='100px';}
 function toast(t){var e=document.createElement('div');e.className='toast';e.innerHTML='<svg class="ic" viewBox="0 0 24 24"><path d="M5 12.5l4.2 4L19 7"/></svg>'+t;document.body.appendChild(e);requestAnimationFrame(function(){e.classList.add('show')});setTimeout(function(){e.classList.remove('show')},2000)}
 window.__toast=toast;
 // 案A：押すと右の半券が切れて落ちる
 var p=document.querySelector('.ckpill');
 if(p)p.addEventListener('click',function(){p.classList.add('tear');setTimeout(function(){toast('羽田の印を押しました')},300);setTimeout(function(){var d=document.createElement('div');d.className='ckdone';d.innerHTML='<span class="ck"><svg class="ic" viewBox="0 0 24 24"><path d="M5 12.5l4.2 4L19 7"/></svg></span>本日チェックイン済み<small>14:08</small>';p.replaceWith(d)},420)});
 // 案B：つまみを右へ引く（7割で切れる）
 var s=document.querySelector('.stubrow:not(.static)');
 if(s){var kn=s.querySelector('.kn'),x0=null,max=0;
  s.addEventListener('pointerdown',function(e){x0=e.clientX;max=s.clientWidth-84;kn.style.transition='none';s.setPointerCapture(e.pointerId)});
  var tx=s.querySelector('span:not(.kn)');
  window.__pull=function(f){max=s.clientWidth-84;kn.style.transform='translateX('+(f*max)+'px)';tx.style.opacity=Math.max(0,1-f*1.6)};
  s.addEventListener('pointermove',function(e){if(x0===null)return;var d=Math.max(0,Math.min(max,e.clientX-x0));kn.style.transform='translateX('+d+'px)';tx.style.opacity=Math.max(0,1-d/max*1.6)});
  s.addEventListener('pointerup',function(e){if(x0===null)return;var d=e.clientX-x0;x0=null;kn.style.transition='';if(d>max*.7){kn.style.transform='translateX('+max+'px)';setTimeout(function(){toast(s.dataset.done||'羽田の印を押しました')},250)}else kn.style.transform='';tx.style.opacity=''});}
})();
'''

def tabs(cur='home'):
    b = [('home', 'ホーム', 'home'), ('book', '図鑑', 'book'), ('log', 'フライト', 'plane'), ('ops', '運用', 'ops'), ('sg', '修行', 'stairs')]
    a = [('home', 'ホーム', 'home'), ('now', 'いまの空港', 'ops'), ('rec', '記録', 'records'), ('me', 'マイページ', 'user')]
    f = lambda items: ''.join('<button type="button"%s>%s%s</button>' % (' aria-current="page"' if k == cur else '', ic(i), lb) for k, lb, i in items)
    return '<nav class="tabs" aria-label="下のタブ"><span class="tb">%s</span><span class="ta">%s</span></nav>' % (f(b), f(a))

def topbar(chip=''):
    return ('<div class="topbar"><span class="appbtn" aria-hidden="true">%s</span>%s'
            '<button type="button" class="mypg">%sマイページ</button></div>') % (ic('compass'), chip, ic('user'))

def wide_marks(key, arc=True, me=True):
    d = POS[key]; out = []
    visited = {'HND', 'NRT', 'CTS', 'ITM', 'KIX', 'FUK', 'OKA', 'HKD', 'SDJ', 'KMQ', 'NGO', 'HIJ', 'AOJ', 'AKJ', 'KUH', 'MMB'}
    for a in APS:
        c = a[2]
        if c not in d: continue
        x, y = d[c]
        if c in visited: out.append('<circle class="v" cx="%.1f" cy="%.1f" r="4.5"/>' % (x, y))
        else: out.append('<circle class="nv" cx="%.1f" cy="%.1f" r="3.5"/>' % (x, y))
    if arc:
        (x1, y1), (x2, y2) = d['HND'], d['CTS']
        mx, my = (x1 + x2) / 2 + 46, (y1 + y2) / 2
        out.insert(0, '<path class="arc" d="M%.1f %.1fQ%.1f %.1f %.1f %.1f"/>' % (x1, y1, mx, my, x2, y2))
        out.append('<text x="%.1f" y="%.1f">羽田</text><text x="%.1f" y="%.1f">新千歳</text>' % (x1 + 9, y1 + 16, x2 + 9, y2 + 4))
    if me:
        x, y = d['ME']
        out.append('<circle class="meh" cx="%.1f" cy="%.1f" r="14"/><circle class="me" cx="%.1f" cy="%.1f" r="6"/>' % (x - 8, y - 8, x - 8, y - 8))
    return ''.join(out)

def mapwide(arc=True):
    v = wide_marks('wide', arc).replace('"', '&quot;'); s = wide_marks('wide-667', arc).replace('"', '&quot;')
    return ('<img class="map" data-src="make/bg/bg-wide" alt="">'
            '<svg class="mk" data-v="%s" data-s="%s"></svg><span class="attr">地図：国土地理院</span>'
            '<button type="button" class="locbtn" aria-label="いまの場所へ">%s</button>') % (v, s, ic('locate'))

def maphnd(me_off=False):
    # 羽田の地図。me_off＝判定範囲の少し外にいる（GPS がずれた）
    x, y = POS['hnd']['hnd']; xs, ys = POS['hnd-667']['hnd']
    def me(x, y):
        if me_off: x, y = x - 150, y - 150
        else: x, y = x + 10, y + 14
        return '<circle class="meh" cx="%.1f" cy="%.1f" r="16"/><circle class="me" cx="%.1f" cy="%.1f" r="7"/>' % (x, y, x, y)
    return ('<img class="map" data-src="make/bg/bg-hnd" alt="">'
            '<svg class="mk" data-v="%s" data-s="%s"></svg><span class="attr">地図：国土地理院</span>') % (me(x, y).replace('"', '&quot;'), me(xs, ys).replace('"', '&quot;'))

def page(name, title, body, sheet_h='m', minh=None):
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s</style></head><body><div class="ph">%s</div><script>%s</script></body></html>') % (title, VARS, CSS, body, JS)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html)
    print('書いた', name)

def sheet(inner, h='m', minh=None):
    return '<section class="sheet" data-h="%s"%s><span class="grab" aria-hidden="true"></span><div class="in">%s</div></section>' % (h, ' data-min="%d"' % minh if minh else '', inner)

# ───── 部品 ─────
NEXT = ('<div class="card nf"><div class="row"><span class="lab">次のフライト</span><span class="sp"></span>'
        '<button type="button" class="pill sm">%s予定</button></div>'
        '<div class="row" style="align-items:flex-end;margin-top:2px"><div class="big"><span class="u" style="margin:0 2px 0 0">あと</span><span class="num">14</span><span class="u">日</span></div><span class="sp"></span>'
        '<div class="rt"><div class="d">12月9日（水）</div><div class="c">HND<small>→</small>CTS</div></div></div>'
        '<div class="fl"><span class="al jl">JL</span><b>JL503</b><span>08:15 発</span><span class="note">・新千歳ゆき</span></div></div>') % ic('plus')
NEXT_S = ('<div class="card nf" style="padding:12px 16px"><div class="row"><span class="lab">次のフライト</span>'
          '<div class="big" style="margin:0"><span class="num" style="font-size:30px">14</span><span class="u">日後</span></div><span class="sp"></span>'
          '<div class="rt"><div class="c" style="font-size:18px">HND<small>→</small>CTS</div></div></div></div>')
NOPLAN = ('<div class="card nf"><span class="lab">次のフライト</span>'
          '<p style="margin-top:6px;font-size:15px;font-weight:700;color:var(--strong)">予定を入れると、出発までの日数がここに出ます</p>'
          '<div style="display:flex;flex-direction:column;gap:8px;margin-top:12px">'
          '<button type="button" class="pill dark">%s次の予定を入れる</button>'
          '<button type="button" class="pill">行ったことがある空港をまとめて記録</button></div>'
          '<p class="note" style="margin-top:8px">まとめて記録した空港は「行ったことがある」の記録で、印とは別です。現地でチェックインすると印になります</p></div>') % ic('plus')
def near(dist='28.4', msg='空港に近づくとチェックインできます', act=None):
    act = act if act is not None else '<button type="button" class="pill sm">羽田のいまを見る%s</button>' % ic('chev')
    return ('<div class="card near"><div class="row"><span class="lab">いちばん近い空港</span></div>'
            '<div class="row" style="margin-top:8px"><span class="flip"><span>H</span><span>N</span><span>D</span></span>'
            '<div class="nm" style="flex:1;min-width:0">東京国際空港<br>（羽田）</div>'
            '<div class="dist"><span class="num">%s</span><span class="u">km</span></div></div>'
            '<p class="msg">%s</p><div class="act">%s</div></div>') % (dist, msg, act)
GOAL = ('<div class="card goal"><div class="row"><span class="lab">次の小目標</span><span class="sp"></span>'
        '<span class="num">4</span><span class="u">/ 6 関東</span></div>'
        '<div class="bar"><i style="width:66.7%"></i></div><p class="sub">あと2空港で関東がそろいます（八丈島・三宅島）</p></div>')
GOALS = ('<div class="card goal"><div class="row"><span class="lab">地方ごとの進み</span></div><div class="goals" style="margin-top:10px">'
         + ''.join('<div><div class="row"><b style="font-size:14px;color:var(--strong)">%s</b><span class="sp"></span><span class="num" style="font-size:20px">%d</span><span class="u">/ %d</span></div><div class="bar" style="margin-top:6px"><i style="width:%.1f%%"></i></div></div>' % (n, a, b, a * 100 / b)
                   for n, a, b in (('関東', 4, 6), ('北海道', 4, 13), ('東北', 3, 9), ('中部', 1, 13))) + '</div></div>')
STRIP = ('<div class="card strip"><div><span class="k">今日の印</span><span class="num">0</span></div>'
         '<div><span class="k">空港</span><span class="num">16</span><span class="u">/86</span></div>'
         '<div><span class="k">フライト</span><span class="num">30</span></div></div>')
NEARLIST = ('<div class="card list"><div class="hd"><h2>近い空港</h2></div>'
            + ''.join('<div class="it"><span class="c">%s</span><span class="n">%s</span><span class="num">%s</span><span class="u">km</span></div>' % r
                      for r in (('HND', '東京国際空港（羽田）', '28.4'), ('NRT', '成田国際空港', '71.9'), ('IBR', '茨城空港', '104'))) + '</div>')

def bp(state='go', first=False, place=True):
    # 案B の黒いカード。state: go（引ける）／off（電波なし）／done（済み）
    vis = '<span class="first">はじめての空港</span>' if first else '<span class="vis"><b>12</b> 回目の訪問・前回 10月18日</span>'
    top = ('<div class="top"><div class="row"><span class="lb">いま空港にいます</span><span class="sp"></span>'
           '<button type="button" class="pinpill">%sピン止め</button></div>'
           '<div class="row" style="margin-top:6px;gap:12px"><span class="flip lg"><span>H</span><span>N</span><span>D</span></span>'
           '<div style="min-width:0"><div class="nm">東京国際空港（羽田）</div>%s</div></div></div>') % (ic('pin'), vis)
    if state == 'go':
        low = '<div class="stubrow" role="slider" aria-label="右へ引いて印をもらう"><span class="kn">%s</span><span>右へ引いて印をもらう<small>半券を切るとチェックイン</small></span></div>' % ic('arrow')
    elif state == 'off':
        low = '<div class="stubrow off" data-done="この端末に置きました。電波が戻ったら送ります" role="slider" aria-label="右へ引いて印をもらう"><span class="kn">%s</span><span>右へ引いて印をもらう<small>電波が戻ったら、あとで送ります</small></span></div>' % ic('arrow')
    else:
        low = '<div class="donerow"><span class="ck">%s</span>本日チェックイン済み<small>14:08</small></div>' % ic('check')
    return '<div class="bp">%s%s</div>' % (top, low)

NOW3 = ('<div class="card"><div class="hd"><h2>羽田のいま</h2><button type="button" class="more">詳しく%s</button></div>'
        '<div class="now3"><div><span class="k">平均の遅れ</span><span class="num">+12<span class="u">分</span></span></div>'
        '<div><span class="k">使っている滑走路</span><span class="num s">34L・34R</span></div>'
        '<div><span class="k">特別塗装機</span><span class="num">4<span class="u">機</span></span></div></div>'
        '<p class="note" style="margin-top:8px">14:02 に読んだ値・遅れはいまの便の平均</p></div>') % ic('chev')
NOW3_OFF = ('<div class="card"><div class="hd"><h2>羽田のいま</h2></div>'
            '<div class="now3" style="opacity:.55"><div><span class="k">平均の遅れ</span><span class="num">+12<span class="u">分</span></span></div>'
            '<div><span class="k">使っている滑走路</span><span class="num s">34L・34R</span></div>'
            '<div><span class="k">特別塗装機</span><span class="num">4<span class="u">機</span></span></div></div>'
            '<p class="stale">読み込めませんでした・最後に読んだのは 13:41</p></div>')
def flights(first_btn='記録する', title='今日の便を記録'):
    rows = (('jl', 'JL', 'JL519', '14:35', '新千歳ゆき'), ('nh', 'NH', 'NH63', '15:00', '新千歳ゆき'))
    body = ''.join('<div class="fc"><span class="al %s">%s</span><span class="num t">%s</span><span class="to"><b>%s</b>%s</span><button type="button" class="rec%s">%s</button></div>'
                   % (c, a, t, f, to, '' if i == 0 else ' ghost', first_btn if i == 0 else '記録する') for i, (c, a, f, t, to) in enumerate(rows))
    return ('<div class="card"><div class="hd"><h2>%s</h2><button type="button" class="more">ほかの便%s</button></div>%s'
            '<p class="note" style="margin-top:6px">今日の運航情報から、出発が近い便を出しています</p></div>') % (title, ic('chev'), body)
FLIGHTS_L = ('<div class="card"><div class="hd"><h2>今日の便を記録</h2></div>'
             + ''.join('<div class="fc"><span class="al %s">%s</span><span class="num t">%s</span><span class="to"><b>%s</b>%s</span><button type="button" class="rec ghost">記録する</button></div>' % r
                       for r in (('jl', 'JL', '14:35', 'JL519', '新千歳ゆき'), ('nh', 'NH', '15:00', 'NH63', '新千歳ゆき'), ('jl', 'JL', '15:10', 'JL465', '松山ゆき'), ('nh', 'NH', '15:25', 'NH995', '那覇ゆき'), ('jl', 'JL', '15:40', 'JL331', '福岡ゆき')))
             + '</div>')
VISITS = ('<div class="card list"><div class="hd"><h2>羽田の訪問</h2></div>'
          + ''.join('<div class="it"><span class="n">%s</span><span class="note">%s</span></div>' % r for r in (('2026年10月18日', 'JL503 で新千歳へ'), ('2026年9月2日', 'チェックインだけ'), ('2026年8月11日', 'NH995 で那覇へ'))) + '</div>')

