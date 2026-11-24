# -*- coding: utf-8 -*-
# 画面案の HTML を作る：bg/ の背景（今の羽田の3D を昼にして撮ったもの）の上に、案の操作を重ねる
# 外部の読み込みなしで開けるよう、背景は JPEG にして HTML の中に入れる（390×844 用と 375×667 用の2枚、画面の高さで切り替え）
import base64, io, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def uri(name):
    im = Image.open('%s/bg/%s.png' % (HERE, name)).convert('RGB'); b = io.BytesIO(); im.save(b, 'JPEG', quality=80)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
_cache = {}
SAME = {'follow'}
def bgcss(name):
    if name not in _cache:
        _cache[name] = (uri(name), None if name in SAME else uri(name + '-667'))
    a, b = _cache[name]
    if b is None:   # 追う：375 の撮り直しでは別の機体が映るので、390 の絵を真ん中で切って使う
        return '.scene{background-image:url(%s);background-position:center 45%%}' % a
    return '.scene{background-image:url(%s)}@media (max-height:720px){.scene{background-image:url(%s)}}' % (a, b)

CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#0F1626}
body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;color:#1F2937;-webkit-text-size-adjust:100%;overflow:hidden}
button{font:inherit;color:inherit;border:0;background:none;cursor:pointer}
.scene{position:fixed;inset:0;background-size:cover;background-position:center top}
.glass{background:rgba(255,255,255,.92);box-shadow:0 2px 10px rgba(15,22,38,.12)}
.top{position:absolute;left:12px;right:12px;top:10px;display:flex;gap:10px;align-items:center;z-index:5}
.rnd{flex:none;width:44px;height:44px;border-radius:50%;display:grid;place-items:center;color:#111827}
.rnd svg{width:22px;height:22px}
.ttl{flex:1;min-width:0;min-height:44px;display:flex;flex-direction:column;justify-content:center;padding:4px 16px;border-radius:999px}
.ttl b{font-size:15px;font-weight:800}
.ttl span{font-size:13px;color:#6B7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pills{position:absolute;left:12px;right:12px;top:64px;display:grid;gap:4px;padding:4px;border-radius:999px;z-index:5}
.pills.n4{grid-template-columns:repeat(4,1fr)}
.pills button{min-height:44px;border-radius:999px;color:#4B5563;font-weight:700;font-size:14px;display:flex;align-items:center;justify-content:center;gap:5px;white-space:nowrap}
.pills button svg{width:17px;height:17px;flex:none}
.pills button.on{background:#111827;color:#fff}
.under{position:absolute;left:12px;right:12px;top:122px;display:flex;justify-content:space-between;align-items:flex-start;gap:8px;z-index:4}
.under.b{top:64px}
.chips{display:flex;flex-direction:column;align-items:flex-start;gap:6px}
.chip{display:inline-flex;align-items:center;gap:8px;padding:6px 14px;min-height:32px;border-radius:999px;background:rgba(255,255,255,.9);font-size:13px;color:#374151;box-shadow:0 1px 6px rgba(15,22,38,.08)}
.chip .dot{width:9px;height:9px;border-radius:50%;background:#2F7D4F}
.pbtn{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;font-size:14px;font-weight:700;color:#111827;white-space:nowrap}
.pbtn svg{width:18px;height:18px}
.alt{display:flex;flex-direction:column;align-items:flex-end;padding:8px 16px;border-radius:20px}
.alt b{font-size:26px;font-weight:800;line-height:1.05;letter-spacing:-.01em}
.alt b small{font-size:13px;font-weight:600;color:#6B7280;margin-left:2px}
.alt span{font-size:12px;color:#6B7280}
.peek{position:absolute;left:0;right:0;bottom:0;height:78px;padding:8px 20px 0;border-radius:28px 28px 0 0;background:#fff;box-shadow:0 -4px 20px rgba(15,22,38,.12);z-index:3}
.grab{width:40px;height:5px;border-radius:3px;background:#E5E7EB;margin:0 auto 8px}
.peek .row{display:flex;align-items:baseline;justify-content:space-between;min-height:44px}
.peek .row b{font-size:16px;font-weight:800}
.num{font-size:24px;font-weight:800}
.num small{font-size:13px;color:#6B7280;font-weight:600;margin-left:3px}
.sheet{position:absolute;left:0;right:0;bottom:0;padding:8px 20px 20px;border-radius:28px 28px 0 0;background:#fff;box-shadow:0 -4px 20px rgba(15,22,38,.12);z-index:6}
.sheet h3{font-size:17px;font-weight:800;display:flex;justify-content:space-between;align-items:center;min-height:44px}
.sheet .sub{font-size:13px;color:#6B7280;margin:-4px 0 8px}
.lst{list-style:none}
.lst li{display:flex;align-items:center;gap:14px;min-height:56px;padding:6px 0}
.lst li+li{box-shadow:inset 0 1px 0 #F1F3F6}
.lst .ic{flex:none;width:40px;height:40px;border-radius:14px;background:#F3F4F6;display:grid;place-items:center;color:#374151}
.lst .ic svg{width:20px;height:20px}
.lst .tx{flex:1;min-width:0}
.lst .tx b{display:block;font-size:15px;font-weight:700}
.lst .tx span{display:block;font-size:13px;color:#6B7280}
.lst .go{color:#9CA3AF;font-size:20px}
.lst .fl b{font-size:17px;font-weight:800}
.x44{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;background:#F3F4F6;color:#374151;font-size:18px}
.card{position:absolute;left:16px;right:16px;border-radius:24px;background:#fff;box-shadow:0 8px 28px rgba(15,22,38,.18);padding:18px 18px 16px;z-index:7}
.card h3{font-size:18px;font-weight:800;margin-bottom:4px}
.card .sub{font-size:13px;color:#6B7280;margin-bottom:10px}
.g{display:grid;grid-template-columns:1fr 1fr;gap:8px 10px;margin-bottom:12px}
.g div{display:flex;align-items:center;gap:8px;padding:8px;border-radius:16px;background:#F5F6F8}
.g svg{flex:none;width:36px;height:36px}
.g b{display:block;font-size:14px;font-weight:700}
.g span{display:block;font-size:12px;color:#6B7280}
.dark{display:flex;align-items:center;justify-content:center;width:100%;min-height:48px;border-radius:999px;background:#111827;color:#fff;font-size:15px;font-weight:700}
.note{font-size:12px;color:#6B7280;text-align:center;margin-top:8px}
.toast{position:absolute;left:16px;right:16px;bottom:96px;display:flex;align-items:center;gap:12px;padding:12px 12px 12px 16px;border-radius:20px;background:rgba(17,24,39,.92);color:#F3F4F6;font-size:14px;z-index:7;box-shadow:0 6px 20px rgba(15,22,38,.2)}
.toast b{font-weight:700}
.toast span{flex:1}
.toast button{min-height:44px;padding:0 14px;border-radius:999px;background:rgba(255,255,255,.14);color:#fff;font-weight:700;font-size:14px;white-space:nowrap}
.follow{position:absolute;left:12px;right:12px;top:122px;display:flex;align-items:center;gap:10px;padding:6px 6px 6px 16px;border-radius:24px;z-index:4}
.follow .tx{flex:1;min-width:0}
.follow .tx b{font-size:16px;font-weight:800}
.follow .tx span{display:block;font-size:13px;color:#6B7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.seg{display:flex;gap:4px;padding:4px;border-radius:999px}
.seg button{min-height:44px;min-width:56px;padding:0 12px;border-radius:999px;font-size:14px;font-weight:700;color:#4B5563}
.seg button.on{background:#111827;color:#fff}
.dock2{position:absolute;left:12px;right:12px;bottom:92px;display:flex;justify-content:space-between;align-items:flex-end;z-index:4}
.pin{position:absolute;transform:translate(-50%,-100%);display:flex;flex-direction:column;align-items:center;z-index:4}
.pin .lb{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:0 12px;border-radius:999px;background:#fff;font-size:13px;font-weight:700;box-shadow:0 2px 10px rgba(15,22,38,.18);white-space:nowrap}
.pin .lb.dk{background:#111827;color:#fff;min-height:44px;font-size:14px}
.pin .st{width:2px;height:16px;background:#111827}
.pin .ft{width:12px;height:12px;border-radius:50%;background:#111827;box-shadow:0 0 0 4px rgba(255,255,255,.8)}
.cmp{display:flex;align-items:center;gap:10px;padding:6px 16px 6px 6px;border-radius:999px}
.cmp i{width:44px;height:44px;border-radius:50%;background:#F3F4F6;display:grid;place-items:center}
.cmp i svg{width:26px;height:26px}
.cmp b{display:block;font-size:15px;font-weight:800}
.cmp span{display:block;font-size:12px;color:#6B7280}
.stick{width:132px;height:132px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:inset 0 0 0 2px rgba(255,255,255,.9),0 2px 10px rgba(15,22,38,.12);position:relative;backdrop-filter:blur(2px)}
.stick .k{position:absolute;left:50%;top:50%;width:56px;height:56px;margin:-28px 0 0 -28px;transform:translate(6px,-12px);border-radius:50%;background:#fff;box-shadow:0 3px 10px rgba(15,22,38,.25);display:grid;place-items:center;color:#9CA3AF}
.stick .ar{position:absolute;font-size:12px;color:#374151;font-weight:700}
.lab{display:block;text-align:center;font-size:12px;color:#374151;font-weight:700;margin-top:6px;text-shadow:0 0 4px #fff,0 0 4px #fff}
.rail{display:flex;flex-direction:column;align-items:center;gap:6px;padding:6px;border-radius:999px}
.rail button{width:48px;height:48px;border-radius:50%;background:#F3F4F6;display:grid;place-items:center;color:#111827}
.rail button svg{width:22px;height:22px}
.rail .bar{width:6px;height:56px;border-radius:3px;background:#E5E7EB;position:relative}
.rail .bar i{position:absolute;left:-5px;width:16px;height:16px;border-radius:50%;background:#111827;bottom:30%}
.turn{display:flex;gap:6px;padding:6px;border-radius:999px;margin-top:8px}
.turn button{width:48px;height:48px;border-radius:50%;background:#F3F4F6;display:grid;place-items:center}
.turn button svg{width:22px;height:22px}
.dock{position:absolute;left:12px;right:12px;bottom:90px;display:grid;grid-template-columns:repeat(4,1fr);gap:4px;padding:5px;border-radius:28px;z-index:5}
.dock button{min-height:56px;border-radius:22px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;color:#4B5563;font-size:13px;font-weight:700}
.dock button svg{width:22px;height:22px}
.dock button.on{background:#111827;color:#fff}
.tag{position:absolute;right:12px;bottom:92px;z-index:4}
.pinT{left:326px;top:220px}@media (max-height:720px){.pinT{left:291px;top:174px}}
.fingers{position:absolute;z-index:4;pointer-events:none}
"""
I = {
 'x': '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
 'more': '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="18" cy="12" r="1.8"/></svg>',
 'free': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4" fill="currentColor" stroke="none"/><path d="M20 12a8 8 0 0 1-13.7 5.6M4 12a8 8 0 0 1 13.7-5.6"/><path d="M18 3.5v3.2h-3.2M6 20.5v-3.2h3.2"/></svg>',
 'follow': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 4 13 9.5H7.5L5.5 8H4l1.6 3L4 14h1.5l2-1.5H13L21 18"/><circle cx="4" cy="20" r="1" fill="currentColor"/></svg>',
 'stand': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2.2"/><path d="M12 8v7M8.5 11h7M12 15l-3 6M12 15l3 6"/></svg>',
 'fly': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="10" width="6" height="4" rx="1.2"/><circle cx="5" cy="6" r="2.4"/><circle cx="19" cy="6" r="2.4"/><circle cx="5" cy="18" r="2.4"/><circle cx="19" cy="18" r="2.4"/><path d="M7 8l2 2M17 8l-2 2M7 16l2-2M17 16l-2-2"/></svg>',
 'back': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4v4.5h4.5"/></svg>',
 'up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15l6-6 6 6"/></svg>',
 'down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>',
 'tl': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 7H5V3"/><path d="M5.5 7A8 8 0 1 1 4 12"/></svg>',
 'tr': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 7h4V3"/><path d="M18.5 7A8 8 0 1 0 20 12"/></svg>',
 'tower': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7h8l-1 4H9z"/><path d="M10 11l-1 10h6l-1-10M12 3v4"/></svg>',
 'deck': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 20h18M5 20v-8h14v8M3 12h18M8 12V8h8v4"/></svg>',
 'rw': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21 10.5 3h3L15 21z"/><path d="M12 6v2M12 11v2M12 16v2"/></svg>',
 'tap': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7" opacity=".5"/></svg>',
 'cmp': '<svg viewBox="0 0 26 26"><circle cx="13" cy="13" r="11" fill="none" stroke="#D1D5DB" stroke-width="1.5"/><path d="M13 3.5 16 13h-6z" fill="#111827" transform="rotate(-90 13 13)"/><path d="M13 22.5 10 13h6z" fill="#D1D5DB" transform="rotate(-90 13 13)"/></svg>',
}
# 指の絵（はじめての1回の案内）：丸が指、矢印が動き
def finger(kind):
    d = {'one': '<circle cx="20" cy="22" r="6" fill="#111827"/><path d="M8 33q12 6 24 0" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/><path d="M29 30.5l3 2.5-3.6 1.2" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
         'pinch': '<circle cx="13" cy="25" r="5.5" fill="#111827"/><circle cx="27" cy="15" r="5.5" fill="#111827"/><path d="M8 31 4 35M32 9l4-4" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>',
         'pan': '<circle cx="15" cy="18" r="5" fill="#111827"/><circle cx="26" cy="18" r="5" fill="#111827"/><path d="M8 31h24M28 28l4 3-4 3" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
         'tilt': '<circle cx="15" cy="22" r="5" fill="#111827"/><circle cx="26" cy="22" r="5" fill="#111827"/><path d="M34 8v24M31 11l3-3 3 3M31 29l3 3 3-3" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'}[kind]
    return '<svg viewBox="0 0 40 40">%s</svg>' % d

def top(sub='機体の位置は約1分遅れ'):
    return '<div class="top"><button class="rnd glass" aria-label="閉じる">%s</button><div class="ttl glass"><b>羽田　3D</b><span>%s</span></div><button class="rnd glass" aria-label="設定と出典">%s</button></div>' % (I['x'], sub, I['more'])
MODES = [('free', '自由'), ('follow', '追う'), ('stand', '立つ'), ('fly', '飛ぶ')]
def pills(on):
    return '<div class="pills n4 glass" role="group" aria-label="見方">' + ''.join('<button class="%s" aria-pressed="%s">%s%s</button>' % ('on' if k == on else '', str(k == on).lower(), I[k], t) for k, t in MODES) + '</div>'
def dock(on):
    return '<div class="dock glass" role="group" aria-label="見方">' + ''.join('<button class="%s" aria-pressed="%s">%s<span>%s</span></button>' % ('on' if k == on else '', str(k == on).lower(), I[k], t) for k, t in MODES) + '</div>'
def peek(n=15):
    return '<div class="peek"><div class="grab"></div><div class="row"><b>羽田の近くの機体</b><span class="num">%d<small>機</small></span></div></div>' % n
def back(label='全体に戻す'):
    return '<button class="pbtn glass">%s%s</button>' % (I['back'], label)
def alt(m, sub='上限 1,000m'):
    return '<div class="alt glass"><b>%s<small>m</small></b><span>高さ・%s</span></div>' % (m, sub)
def stick(): 
    return '<div><div class="stick"><span class="ar" style="left:50%;top:6px;transform:translateX(-50%)">前</span><span class="ar" style="left:50%;bottom:6px;transform:translateX(-50%)">後ろ</span><span class="ar" style="left:8px;top:50%;transform:translateY(-50%)">左</span><span class="ar" style="right:8px;top:50%;transform:translateY(-50%)">右</span><div class="k"></div></div><span class="lab">なぞって進む</span></div>'
def flyright():
    return ('<div style="display:flex;flex-direction:column;align-items:center"><div class="rail glass"><button aria-label="上がる">%s</button><div class="bar"><i></i></div><button aria-label="下がる">%s</button></div>'
            '<div class="turn glass"><button aria-label="左を向く">%s</button><button aria-label="右を向く">%s</button></div><span class="lab">高さ・向き</span></div>') % (I['up'], I['down'], I['tl'], I['tr'])

def page(title, bg, body):
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>%s</title><style>%s%s</style></head><body><div class="scene"></div>%s</body></html>' % (title, CSS, bgcss(bg), body)

guide = ('<div class="card" style="bottom:96px"><h3>指で自由に動かせます</h3><p class="sub">空港のどこへでも。地面の下と遠すぎる所には行きません</p><div class="g">'
         '<div>%s<p><b>回す</b><span>1本指でなぞる</span></p></div><div>%s<p><b>寄る・離れる</b><span>2本指でつまむ</span></p></div>'
         '<div>%s<p><b>ずらす</b><span>2本指でなぞる</span></p></div><div>%s<p><b>傾ける</b><span>2本指で上下に</span></p></div></div>'
         '<button class="dark">わかった</button><p class="note">はじめての1回だけ。⋯ からもう一度見られます</p></div>') % (finger('one'), finger('pinch'), finger('pan'), finger('tilt'))

S = {}
S['A1-free-guide'] = ('A1 案A 自由（はじめての1回の案内）', 'free', top() + pills('free') + '<div class="under"><div class="chips"><span class="chip"><i class="dot"></i>位置を受信中</span></div></div>' + guide + peek())
S['A2-free-moved'] = ('A2 案A 自由（寄ったところ・全体に戻す）', 'free2', top() + pills('free') + '<div class="under"><div class="chips"><span class="chip"><i class="dot"></i>位置を受信中</span></div>' + back() + '</div>' + peek())
S['A3a-follow-pick'] = ('A3a 案A 追う（機体を選ぶ）', 'free', top() + pills('follow') +
    '<div class="sheet"><div class="grab"></div><h3>どの機体を追いますか<button class="x44" aria-label="やめる">×</button></h3><p class="sub">押した機体の後ろに付いて、一緒に動きます</p><ul class="lst">'
    '<li class="fl"><div class="tx"><b>JL 616</b><span>到着・着陸まで約1分・34L（A）へ</span></div><span class="go">›</span></li>'
    '<li class="fl"><div class="tx"><b>NH 82</b><span>到着・着陸まで約2分・34R（C）へ</span></div><span class="go">›</span></li>'
    '<li class="fl"><div class="tx"><b>JL 332</b><span>到着・着陸まで約3分・34L（A）へ</span></div><span class="go">›</span></li>'
    '<li class="fl"><div class="tx"><b>NH 241</b><span>出発・C 滑走路で離陸の順番待ち</span></div><span class="go">›</span></li></ul>'
    '<p class="note" style="text-align:left">3D の中の機体を押しても選べます</p></div>')
S['A3-follow'] = ('A3 案A 追う（後ろに付いて動く）', 'follow', top() + pills('follow') +
    '<div class="follow glass"><div class="tx"><b>NH 82 を追っています</b><span>到着・着陸まで約2分・高さ 約530m</span></div><button class="x44" aria-label="追うのをやめる">×</button></div>'
    '<div class="dock2"><span class="chip">指で回す・寄る</span><div class="seg glass" role="group" aria-label="付く位置"><button class="on">後ろ</button><button>横</button><button>前</button></div></div>' + peek())
S['A3b-follow-lost'] = ('A3b 案A 追う（機体が消えて自由に戻った）', 'free2', top() + pills('free') +
    '<div class="under"><div class="chips"><span class="chip"><i class="dot"></i>位置を受信中</span></div>' + back() + '</div>'
    '<div class="toast"><span><b>NH 82</b> は駐機場に入り、位置が届かなくなりました。自由に戻りました</span><button>ほかを追う</button></div>' + peek())
S['A4-stand-pick'] = ('A4 案A 立つ（場所を選ぶ）', 'free', top() + pills('stand') +
    '<div class="pin pinT"><span class="lb">' + I['tower'] + '管制塔</span><i class="st"></i><i class="ft"></i></div>' +
    '<div class="pin" style="left:38%%;top:44%%"><span class="lb dk">ここに立つ</span><i class="st"></i><i class="ft"></i></div>'
    '<div class="sheet"><div class="grab"></div><h3>どこに立ちますか</h3><p class="sub">3D の地面を押した所にも立てます（目の高さ 約1.6m）</p><ul class="lst">'
    '<li><span class="ic">%s</span><div class="tx"><b>管制塔</b><span>いまの「管制塔」の視点。高さ 約118m</span></div><span class="go">›</span></li>'
    '<li><span class="ic">%s</span><div class="tx"><b>第1ターミナル 展望デッキ</b><span>A 滑走路と駐機場</span></div><span class="go">›</span></li>'
    '<li><span class="ic">%s</span><div class="tx"><b>第2ターミナル 展望デッキ</b><span>C 滑走路と駐機場</span></div><span class="go">›</span></li>'
    '<li><span class="ic">%s</span><div class="tx"><b>C 滑走路の南の端</b><span>着陸する機体を正面から</span></div><span class="go">›</span></li></ul></div>' % (I['tower'], I['deck'], I['deck'], I['rw']))
S['A5-stand'] = ('A5 案A 立つ（目の高さで見回す）', 'stand', top() + pills('stand') +
    '<div class="under"><div class="cmp glass"><i>%s</i><p><b>西を見ています</b><span>押した所・目の高さ 約1.6m</span></p></div></div>' % I['cmp'] +
    '<div class="dock2"><span class="chip">指でなぞって見回す</span><button class="pbtn glass">%s場所を変える</button></div>' % I['stand'] + peek())
S['A6-fly'] = ('A6 案A 飛ぶ（ドローンのように）', 'fly', top() + pills('fly') +
    '<div class="under"><div class="chips"><span class="chip">左で進む・右で高さと向き</span></div>' + alt('380') + '</div>'
    '<div class="dock2" style="bottom:96px">' + stick() + flyright() + '</div>' + peek())
S['A6b-fly-limit'] = ('A6b 案A 飛ぶ（上限まで上がった）', 'fly', top() + pills('fly') +
    '<div class="under"><div class="chips"><span class="chip">これより上には行けません</span></div>' + alt('1,000', '上限') + '</div>'
    '<div class="dock2" style="bottom:96px">' + stick() + flyright() + '</div>' + peek())
# 案B：上のピルをなくし、見方は下の4つのボタン（親指の届く所）
S['B1-free'] = ('B1 案B 自由（見方は下の4つのボタン）', 'free2', top() + '<div class="under b"><div class="chips"><span class="chip"><i class="dot"></i>位置を受信中</span><span class="chip">1本指で回す・2本指で寄る</span></div>' + back() + '</div>' + dock('free') + peek())
S['B5-stand'] = ('B5 案B 立つ', 'stand', top() + '<div class="under b"><div class="cmp glass"><i>%s</i><p><b>西を見ています</b><span>押した所・目の高さ 約1.6m</span></p></div><button class="pbtn glass">%s場所</button></div>' % (I['cmp'], I['stand']) + dock('stand') + peek())
S['B6-fly'] = ('B6 案B 飛ぶ', 'fly', top() + '<div class="under b"><div class="chips"><span class="chip">左で進む・右で高さと向き</span></div>' + alt('380') + '</div>'
    '<div class="dock2" style="bottom:160px">' + stick() + flyright() + '</div>' + dock('fly') + peek())

NOWCSS = '.scene{background-size:100% auto}'
if __name__ == '__main__':
    open('%s/00-now.html' % ROOT, 'w').write(page('00 今の羽田の3D（全体・管制塔・機体の3つの視点）', 'now', '').replace('</style>', NOWCSS + '</style>'))
    for k, (t, bg, body) in S.items():
        open('%s/%s.html' % (ROOT, k), 'w').write(page(t, bg, body))
    print(len(S), 'files')
