# -*- coding: utf-8 -*-
# 近くの空港に飛行場も（design/near-airfields）の画面案を作る。使い方：python3 make_near.py
# 地図は maps/ の写真（capture.py が今のアプリのデモで撮る。シートと上の段は写真に入れず、この HTML で描く）
import os, base64, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
MAPS = os.path.join(HERE, 'maps')
ROOT = '/home/claude/soramemo'
DOT = base64.b64encode(open(ROOT + '/web/fonts/dot0-8d4bfa62e8.woff2', 'rb').read()).decode()

def mapimg(name):
    out = ''
    for h in (844, 667):
        p = os.path.join(MAPS, '%s-%d.jpg' % (name, h))
        if os.path.exists(p):
            out += '<img class="m%d" alt="" src="data:image/jpeg;base64,%s">' % (h, base64.b64encode(open(p, 'rb').read()).decode())
    return out or '<div class="mph"></div>'

CSS = """
@font-face{font-family:"Dot";src:url(data:font/woff2;base64,%s) format("woff2");unicode-range:U+0-7F}
:root{--gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic","Meiryo","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;
--bg:#EEF1F5;--card:#FFFFFF;--strong:#1F2937;--ink:#374151;--sub:#5F6878;--mute:#6B7280;--pill:rgba(17,24,39,.06);
--hero:#0F1B2D;--hero-sub:#A7B0BC;--ok:#7EE2A8;--off-bg:#DDE1E7;--off-ink:#374151;--stub:#E9C46A;--stub-sub:#3A2E0B;--apt:#7A1F5C;
--shadow:0 1px 2px rgba(17,24,39,.04),0 10px 30px -8px rgba(17,24,39,.10),inset 0 0 0 1px rgba(17,24,39,.07);--tag:#F1ECF0;--tag-ink:#6E3F5E}
*{box-sizing:border-box}html,body{margin:0;height:100%%}
body{background:var(--bg);color:var(--ink);font-family:var(--gothic);font-size:15px;line-height:1.6;-webkit-text-size-adjust:100%%}
.phone{position:relative;width:100%%;max-width:420px;height:100vh;margin:0 auto;overflow:hidden;background:#F2F2F0}
.map{position:absolute;inset:0;overflow:hidden}
.map img{position:absolute;left:0;top:0;width:390px;display:none}
.map .m844{display:block}
@media (max-height:700px){.map .m844{display:none}.map .m667{display:block}}
.mph{position:absolute;inset:0;background:#EDEDEA}
.zoom{position:absolute;right:14px;display:flex;flex-direction:column;gap:8px;z-index:5}
.zoom b{width:44px;height:44px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);display:grid;place-items:center;font:400 22px var(--gothic);color:var(--strong)}
.credit{position:absolute;left:14px;z-index:5;font-size:13px;font-weight:500;color:var(--sub);background:rgba(255,255,255,.92);border-radius:999px;padding:1px 10px}
.hs{position:absolute;left:0;right:0;bottom:0;z-index:10;background:var(--bg);border-radius:28px 28px 0 0;padding:0 16px 94px;box-shadow:0 -8px 24px -14px rgba(17,24,39,.25)}
.grab{height:24px;position:relative}.grab::before{content:"";position:absolute;left:50%%;top:7px;width:40px;height:5px;margin-left:-20px;border-radius:3px;background:#9CA3AF;opacity:.6}
.bpass{display:flex;min-height:168px;border-radius:24px;box-shadow:var(--shadow)}
.bpm{flex:1;min-width:0;background:var(--hero);color:#F9FAFB;border-radius:24px 0 0 24px;padding:12px 16px 14px 18px}
.bpm .lab{font-size:13px;letter-spacing:.02em;color:var(--hero-sub)}
.flap{display:flex;gap:5px;margin:4px 0 6px}
.flap i{font-style:normal;width:34px;height:40px;border-radius:5px;background:#1C2027;color:#FFB547;font-family:"Dot",monospace;font-size:27px;line-height:40px;text-align:center;position:relative;box-shadow:inset 0 -2px 0 #0B0D10}
.flap i::after{content:"";position:absolute;left:0;right:0;top:19px;height:2px;background:#0B0D10}
.bpm .nm{font-size:16px;font-weight:800;line-height:1.35}
.bpm .ds{font-size:13px;line-height:1.5;color:var(--hero-sub);margin-top:2px}
.bpm .ds b{color:#F3F4F6;font-weight:800}
.dot{display:inline-block;width:10px;height:10px;margin-right:5px;border-radius:999px;background:var(--hero-sub);vertical-align:-1px}.dot.ok{background:var(--ok)}
.ktag{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;font-size:13px;font-weight:700;background:rgba(255,255,255,.12);color:#E8ECF1;margin-left:6px;vertical-align:2px}
.stub{flex:none;width:100px;border-radius:0 24px 24px 0;border-left:2px dashed rgba(15,27,45,.35);background:var(--stub);color:#111827;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px 6px}
.stub .v{writing-mode:vertical-rl;font-size:16px;font-weight:800;letter-spacing:.06em;line-height:1}
.stub .s{font-size:13px;font-weight:700;line-height:1.35;text-align:center;color:var(--stub-sub)}
.stub.off{background:var(--off-bg);color:var(--off-ink);border-left-color:#9CA3AF}.stub.off .s{color:var(--off-ink)}
.near{margin-top:8px;border-radius:22px;background:var(--card);box-shadow:var(--shadow);padding:6px 0 4px}
.near .h{display:flex;align-items:baseline;gap:8px;padding:6px 16px 0;font-size:13px;font-weight:800;color:var(--sub)}
.near .h small{margin-left:auto;font-size:13px;font-weight:600;color:var(--mute)}
.near .more{display:none}
.nr{display:flex;align-items:center;gap:10px;min-height:48px;padding:0 6px 0 16px}
.nr .t{flex:none;display:inline-flex;align-items:center;justify-content:center;min-width:56px;height:26px;padding:0 8px;border-radius:999px;font-size:13px;font-weight:700;background:var(--tag);color:var(--tag-ink)}
.nr .t.civ{background:#E8EDF4;color:#24426E}
.nr .n{flex:1;min-width:0;font-size:15px;font-weight:800;color:var(--strong);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nr .k{flex:none;font-size:18px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;letter-spacing:.01em}
.nr .k small{font-size:12px;font-weight:600;color:var(--mute);margin-left:2px}
.nr .c{flex:none;width:28px;height:44px;display:grid;place-items:center;color:var(--mute)}
.nr .c svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
@media (max-height:700px){.near{padding:2px 0}.near .h{display:none}.near .nr.x{display:none}.nr .o{display:inline-flex}}
.nr .o{display:none;flex:none;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:700;color:var(--sub)}
.strip{display:flex;align-items:center;height:48px;margin-top:8px;padding:0 4px 0 16px;border-radius:22px;background:var(--card);box-shadow:var(--shadow);color:var(--ink)}
.strip>div{flex:1;display:flex;align-items:baseline;gap:6px;min-width:0;white-space:nowrap}
.strip .l{font-size:13px;font-weight:700;color:var(--sub)}
.strip b{font-size:22px;font-weight:800;line-height:1.1;color:var(--strong);font-variant-numeric:tabular-nums}
.strip small{font-size:12px;font-weight:600;color:var(--mute);margin-left:-4px}
.strip .up{flex:none;width:44px;height:44px;display:grid;place-items:center;color:var(--sub)}
.strip .up svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.tabs{position:absolute;left:14px;right:14px;bottom:12px;height:74px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 10px 30px -8px rgba(17,24,39,.22),0 0 0 1px rgba(17,24,39,.04);display:flex;z-index:20}
.tabs b{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:13px;font-weight:700;color:#5F6875;position:relative}
.tabs b.on{color:#1F2937}.tabs b.on::after{content:"";position:absolute;bottom:7px;width:5px;height:5px;border-radius:50%%;background:#2563EB}
.tabs svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.tabs b.on svg{stroke:#2563EB}
.topz{position:absolute;left:16px;right:16px;top:11px;display:flex;gap:10px;z-index:5;white-space:nowrap}
.seg{display:flex;background:var(--card);border-radius:999px;padding:3px;box-shadow:var(--shadow)}
.seg{flex:none}.seg b{min-height:44px;display:flex;align-items:center;padding:0 9px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.seg b.on{background:#16233A;color:#fff}
.mp{margin-left:auto;flex:none;min-height:50px;display:flex;align-items:center;gap:4px;padding:0 12px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.mp svg,.cmp svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.cmp{position:absolute;left:14px;top:70px;width:44px;height:44px;border-radius:14px;background:var(--card);box-shadow:var(--shadow);display:grid;place-items:center;color:var(--sub);z-index:5}
.note{max-width:420px;margin:0 auto;padding:14px 16px 40px;font:13px/1.7 var(--gothic);color:var(--ink)}.note b{display:block;color:var(--strong);font-size:15px}
.ann{position:absolute;left:12px;right:12px;z-index:30;font:13px/1.65 var(--gothic);background:#FFF6DC;color:#4A3D10;padding:10px 12px;border-radius:16px;box-shadow:0 6px 18px -10px rgba(0,0,0,.35)}
.ann b{display:block}.ann ul{margin:2px 0 0;padding-left:1.2em}
/* シート（ホームの鉛筆） */
.dimbg{position:absolute;inset:0;background:rgba(15,23,42,.42);z-index:40}
.sheet{position:absolute;left:0;right:0;bottom:0;background:var(--card);border-radius:28px 28px 0 0;box-shadow:0 -10px 40px -10px rgba(15,23,42,.4);z-index:50;padding:10px 16px 28px;max-height:88vh;overflow:hidden}
.sheet .gb{width:40px;height:5px;border-radius:3px;background:#D5DAE1;margin:2px auto 10px}
.shd .hl{display:flex;align-items:center;gap:10px}
.shd h3{margin:0;font-size:22px;color:var(--strong);flex:1}
.cnt{font-size:24px;font-weight:800;color:var(--strong)}.cnt small{font-size:13px;color:var(--mute);font-weight:600}
.done{min-height:44px;display:inline-flex;align-items:center;padding:0 18px;border-radius:999px;background:#16233A;color:#fff;font-weight:800;font-size:15px}
.lead{font-size:13px;color:var(--sub);margin:6px 4px 10px}
.vr{display:flex;align-items:center;gap:12px;min-height:60px;padding:4px 16px;margin-top:7px;border-radius:18px;background:#F4F6F8}
.vr .tx{flex:1;min-width:0}.vr .tx b{display:block;color:var(--strong);font-size:15px;line-height:1.4}.vr .tx small{display:block;color:var(--sub);font-size:13px;line-height:1.5}
.vr.new{background:#F4F6F8;box-shadow:inset 0 0 0 2px #16233A}
.newt{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;background:#16233A;color:#fff;font-size:13px;font-weight:800;margin-left:6px;vertical-align:1px}
.alw{flex:none;width:68px;text-align:center;font-size:13px;font-weight:800;color:var(--sub)}
.sw{width:68px;height:34px;border-radius:999px;display:flex;align-items:center;flex:none;position:relative;font-size:13px;font-weight:800}
.sw.on{background:#16233A;color:#fff;padding-left:12px}
.sw.on::after{content:"";position:absolute;right:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff}
.sw.off{background:#E5E8EE;color:#4B5563;box-shadow:inset 0 0 0 1.5px #768090;justify-content:flex-end;padding-right:10px}
.sw.off::after{content:"";position:absolute;left:4px;top:4px;width:26px;height:26px;border-radius:50%%;background:#fff;box-shadow:inset 0 0 0 1.5px #768090}
.more2{display:flex;align-items:center;gap:6px;min-height:48px;margin-top:6px;padding:0 4px;font-size:15px;font-weight:800;color:var(--strong)}
""" % DOT

NIGHT = """
:root{--bg:#05070B;--card:#0D1218;--strong:#DCE3EA;--ink:#BCC6D1;--sub:#8996A7;--mute:#7D8A9B;--hero:#0D1218;--hero-sub:#8996A7;--ok:#5FD993;
--shadow:0 14px 30px -18px rgba(0,0,0,.9),inset 0 0 0 1px rgba(150,170,195,.10);--tag:#141B24;--tag-ink:#BCC6D1;color-scheme:dark}
.phone{background:#05070B}
.bpm{box-shadow:inset 1px 0 0 rgba(150,170,195,.10),inset 0 1px 0 rgba(150,170,195,.10),inset 0 -1px 0 rgba(150,170,195,.10)}
.flap i{background:#05070B;color:#DCE3EA;box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}.flap i::after{background:#1A222C}
.bpm .ds b.lit{color:#5FD993;text-shadow:0 0 6px rgba(95,217,147,.45);font-family:"Dot",monospace;font-weight:400;font-size:15px}
.ktag{background:#141B24;color:#BCC6D1}
.stub{background:#0A0F14;color:#DCE3EA;border-left-color:rgba(150,170,195,.35);box-shadow:inset 0 0 0 1px rgba(150,170,195,.10)}
.stub.off{background:#0A0F14;color:#BCC6D1}.stub.off .s{color:#AEB9C6}
.nr .t,.nr .t.civ{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}
.nr .k{font-family:"Dot",monospace;font-weight:400;color:#5FD993;text-shadow:0 0 6px rgba(95,217,147,.45);font-size:19px}
.strip b{font-family:"Dot",monospace;font-weight:400;color:#BCC6D1}
.tabs{background:#0D1218;box-shadow:0 10px 30px -6px rgba(0,0,0,.8),inset 0 0 0 1px rgba(150,170,195,.10)}
.tabs b{color:#8996A7}.tabs b.on{color:#DCE3EA}.tabs b.on svg{stroke:#DCE3EA}.tabs b.on::after{background:#DCE3EA}
.seg{background:#0D1218}.seg b.on{background:#141B24;color:#DCE3EA;box-shadow:inset 0 0 0 1.5px rgba(220,227,234,.72)}
.zoom b,.credit,.cmp,.mp{background:#0D1218;color:#BCC6D1}
.grab::before{background:#3A4654}
.ann{background:#1A1A10;color:#E9DFB8;box-shadow:inset 0 0 0 1px #4A4220}
.hs{box-shadow:0 -1px 0 rgba(150,170,195,.10)}
"""

TABS = [
 ('ホーム', '<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>'),
 ('図鑑', '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>'),
 ('フライト', '<path d="M10.5 13.5 4 11l1.4-1.4 7 1.1 3.9-3.9c.8-.8 2.1-.8 2.9 0s.8 2.1 0 2.9l-3.9 3.9 1.1 7L15 22l-2.5-6.5-3 3v2.5L8 22.5 6.5 19l-3.5-1.5L4.5 16h2.5l3-3"/>'),
 ('運用', '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18 6"/>'),
 ('修行', '<path d="M3.5 19.5h5v-5h5v-5h5v-5"/><path d="M15.5 4.5h3v3"/>')]
def tabs():
    return '<nav class="tabs">' + ''.join('<b class="%s"><svg viewBox="0 0 24 24">%s</svg>%s</b>' % ('on' if k == 'ホーム' else '', v, k) for k, v in TABS) + '</nav>'
CHEV = '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>'
UP = '<svg viewBox="0 0 24 24"><path d="M6 15l6-6 6 6"/></svg>'

def topz():
    return ('<div class="topz"><div class="seg"><b class="on">スタンプラリー</b><b>エアライン経営</b></div>'
            '<div class="mp"><svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20c.9-3.8 4-5.8 7.5-5.8s6.6 2 7.5 5.8"/></svg>マイページ</div></div>'
            '<div class="cmp"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" stroke-dasharray="2 3"/><path d="M8 16l8-8M12 8h4v4"/></svg></div>')

def ticket(label, code, name, dist, stub='out', tag=''):
    flap = '<div class="flap">%s</div>' % ''.join('<i>%s</i>' % c for c in code) if code else ''
    st = ('<div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div>' if stub == 'out'
          else '<div class="stub"><span class="v">チェックイン</span><span class="s">→ 右へ引いて<br>印をもらう</span></div>')
    return '<div class="bpass"><div class="bpm"><div class="lab">%s</div>%s<div class="nm">%s%s</div><div class="ds">%s</div></div>%s</div>' % (label, flap, name, tag, dist, st)

def nrow(kind, name, km, extra=False, civ=False):
    k = ('%.1f' % km) if km < 100 else '%d' % km
    return '<div class="nr%s"><span class="t%s">%s</span><span class="n">%s</span><span class="k">%s<small class="u">km</small></span><span class="c">%s</span></div>' % (
        ' x' if extra else '', ' civ' if civ else '', kind, name, k, CHEV)

def near(rows, title='近くの飛行場', right='20km以内'):
    hidden = sum(1 for r in rows if 'nr x' in r)
    if hidden: rows = [rows[0].replace('<span class="k">', '<span class="o">ほか%dつ</span><span class="k">' % hidden, 1)] + rows[1:]
    return '<div class="near"><div class="h">%s<small>%s</small></div>%s</div>' % (title, right, ''.join(rows))

def strip():
    return ('<div class="strip"><div><span class="l">今日の印</span><b>0</b></div><div><span class="l">空港</span><b>16</b><small class="u">/86</small></div>'
            '<div><span class="l">フライト</span><b>30</b></div><span class="up">%s</span></div>' % UP)

def home(path, title, mapname, sheet_inner, ann='', ann_top=150, night=False, extra='', topzone=False):
    body = ('<div class="map">%s</div>%s<div class="hs" id="hs"><div class="credit" id="cr">地図：国土地理院</div>'
            '<div class="zoom" id="zm"><b>＋</b><b>−</b></div><div class="grab"></div>%s</div>%s%s%s') % (
        mapimg(mapname), topz(), sheet_inner, tabs(), '', extra)
    # 地図の上の部品はシートの上に置く（シートの上端からの位置）
    css = CSS + (NIGHT if night else '') + '.credit{top:-40px}.zoom{top:-124px}'
    html = ('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<title>%s</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main>%s</body></html>\n') % (title, css, body, '<aside class="note">%s</aside>' % ann if ann else '')
    open(os.path.join(OUT, path), 'w').write(html)

# ---------- 場面 ----------
# 02 牛久のあたり：成田の判定範囲の外（31km）。20km 以内の飛行場は竜ヶ崎・大利根。霞ヶ浦駐屯地（基地 7.7km）は出さない
S02_T = ticket('いちばん近い空港', 'NRT', '成田国際空港', '<i class="dot"></i>判定範囲の外 ・ ここから <b>30.5km</b>')
S02_N = near([nrow('飛行場', '竜ヶ崎飛行場', 11.3), nrow('飛行場', '大利根飛行場', 15.3, extra=True)])
# 03 竜ヶ崎飛行場の判定範囲の中：半券はその飛行場。パタパタは出さない（民間空港だけ）。近くに大利根と、いちばん近い民間空港
S03_T = ticket('判定範囲の中の飛行場', '', '竜ヶ崎飛行場', '<i class="dot ok"></i>判定範囲の中', stub='in', tag='<span class="ktag">飛行場</span>')
S03_N = near([nrow('飛行場', '大利根飛行場', 5.2), nrow('空港', '成田国際空港', 20.2, extra=True, civ=True)], '近くの飛行場と空港', '')
# 04 東京駅：羽田の判定範囲の外（14.7km）。20km 以内に出せる飛行場なし（下総・立川などの基地は出さない）→ 行を出さない
S04_T = ticket('いちばん近い空港', 'HND', '東京国際空港（羽田）', '<i class="dot"></i>判定範囲の外 ・ ここから <b>14.7km</b>')

def build():
    home('02-home-near.html', 'ホーム：近くの飛行場あり', 's02', S02_T + S02_N + strip(),
         '<b>02 空港の判定範囲の外・近くに飛行場</b>いちばん近い民間空港は今のまま主に。半券の下に「近くの飛行場」（20km 以内・近い順に2つまで。高さ700未満の画面は1つ＋「ほか1つ」）。地図にも控えめな印。基地（霞ヶ浦駐屯地 7.7km）は出さない', 150)
    home('03-home-in-field.html', 'ホーム：飛行場の判定範囲の中', 's03', S03_T + S03_N + strip(),
         '<b>03 飛行場の判定範囲の中</b>半券はその飛行場（種類の札つき・パタパタなし）。「近くの」には次に近い飛行場と、いちばん近い民間空港（札「空港」）', 150)
    home('04-home-none.html', 'ホーム：近くに飛行場なし', 's04', S04_T + strip(),
         '<b>04 近くに出せる飛行場がない</b>行ごと出さない（空の札や「ありません」も出さない）。シートと地図は今と同じ', 150)
    home('02-home-near-night.html', '夜：ホーム（近くの飛行場あり）', 's02n',
         ticket('いちばん近い空港', 'NRT', '成田国際空港', '<i class="dot"></i>判定範囲の外 ・ ここから <b class="lit">30.5</b> km') + S02_N + strip(),
         '<b>夜：02</b>カードは夜の色。距離の数字だけ緑に光らせる（光る色は数字だけ）。種類の札は色なし。地図の飛行場の印は薄いグレー。夜の地図はふだんの地図を暗くした見本', night=True)
    # 05 ホームの鉛筆のシート
    def vr(name, sub, st, new=False):
        right = '<span class="alw">いつも</span>' if st == 'always' else '<span class="sw %s">%s</span>' % (st, 'ON' if st == 'on' else 'OFF')
        return '<div class="vr%s"><div class="tx"><b>%s%s</b><small>%s</small></div>%s</div>' % (' new' if new else '', name, '<span class="newt">新</span>' if new else '', sub, right)
    rows = (vr('ホームの地図', 'ホームそのもの', 'always') + vr('チェックインの半券', 'いちばん近い空港', 'always')
            + vr('近くの飛行場', '半券の下・20km 以内の飛行場と滑空場', 'on') + vr('今日の数字', '今日の印・空港・フライト', 'always')
            + vr('これから乗る便', '便名を入れると機体を調べる', 'on') + vr('イベントのお知らせ', '開いているイベント', 'on')
            + vr('これまでの記録', '空港・路線・距離の数', 'on') + vr('最近の印', '最近押した印', 'on'))
    sh = ('<div class="dimbg"></div><section class="sheet"><div class="gb"></div><div class="shd"><div class="hl"><h3>ホームに出すもの</h3>'
          '<span class="cnt">8<small class="u">/8</small></span><span class="done">完了</span></div></div>'
          '<p class="lead">OFF でホームから隠れます。「いつも」は外せません。</p>%s<div class="more2">表示の編集をすべて見る →</div></section>') % rows
    home('05-pen-sheet.html', 'ホームの鉛筆のシート', 's02', S02_T + S02_N + strip(), '<b>05 ホームの鉛筆のシート</b>見方の設定2版（案A）の「ホームに出すもの」に1行足す。半券の次（ホームで出る順）に置き、はじめ ON。説明は「半券の下・20km 以内の飛行場と滑空場」。マイページの「表示の編集」のホームのカードにも同じ行', 0, extra=sh)
    home('05b-home-off.html', 'ホーム：近くの飛行場を OFF', 's02off', S02_T + strip(),
         '<b>05b OFF にしたとき</b>シートからも地図の印からも消える（04 と同じ見た目）。半券の中に「近くに…」の1行も出さない', 150)


# ---------- 01 今 と 一覧 ----------
def img(p, w=None):
    from PIL import Image
    import io
    im = Image.open(p).convert('RGB')
    if w: im = im.resize((w, round(im.height * w / im.width)))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=74)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def build_now():
    S = os.path.join(OUT, 'shots')
    items = [('now-ushiku', '判定範囲の外（成田 30.5km）', '20km 以内に飛行場が2つあっても何も出ない'),
             ('now-near5', '5km 以内に飛行場', '半券の中に「近くに大利根飛行場（飛行場・3.3km）」の1行だけ。押せない'),
             ('now-ryu', '飛行場の判定範囲の中', '見出しが「いちばん近い空港」のまま。種類の札もない')]
    cells = ''.join('<figure><img src="%s" alt=""><figcaption><b>%s</b>%s</figcaption></figure>' % (img(os.path.join(S, f + '.png'), 340), t, d) for f, t, d in items)
    css = CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:14px 14px 40px}
h1{font-size:22px;margin:4px 4px 2px;color:var(--strong)}.w>p{font-size:13px;color:var(--sub);margin:0 4px 12px}
.g{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0}figure img{width:100%;border-radius:16px;box-shadow:var(--shadow);display:block}
figcaption{font-size:13px;line-height:1.5;color:var(--sub);margin:6px 2px 0}figcaption b{display:block;color:var(--strong)}"""
    body = '<div class="w"><h1>01 今のホーム</h1><p>main の web/ をデモで開き、位置を入れて撮った（茨城県南部）。民間空港1つだけを主に出し、飛行場は5km 以内か判定範囲の中のときだけ</p><div class="g">%s</div></div>' % cells
    open(os.path.join(OUT, '01-now.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>今のホーム</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, body))

G = [
 ('01-now', '01 今のホーム'), ('02-home-near', '02 判定範囲の外・近くに飛行場'), ('03-home-in-field', '03 飛行場の判定範囲の中'),
 ('04-home-none', '04 近くに飛行場がない'), ('05-pen-sheet', '05 ホームの鉛筆のシート'), ('05b-home-off', '05b OFF にしたとき'), ('02-home-near-night', '夜：02'),
]
def build_index():
    css = CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:16px 16px 60px}
h1{font-size:24px;margin:8px 4px 0;color:var(--strong)}.w p{font-size:13px;color:var(--sub);margin:6px 4px}
.th{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.th a{text-decoration:none;color:var(--strong);font-size:13px;font-weight:700}
.th img{width:100%;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}"""
    s = ('<div class="w"><h1>近くの空港に飛行場も</h1><p>ブランチ design/near-airfields。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667 の写真。'
         '地図は main の web/ をデモで開いて撮った写真（飛行場の印だけ撮るときに足した）。本人「近くの空港は、飛行場なども表示できるようにして」（11/11）</p>'
         '<p>形：いちばん近い民間空港は今のまま主に。半券の下に「近くの飛行場」のカード（20km 以内・基地は出さない・近い順に2つまで、高さ700未満は1つ＋「ほか1つ」）。行を押すとその飛行場の図鑑のページ。地図には民間空港より小さい印。ホームの鉛筆で ON／OFF（はじめ ON）。パタパタは民間空港のまま</p>'
         '<div class="th">%s</div></div>') % ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s</a>' % (f, f, c) for f, c in G)
    open(os.path.join(OUT, 'index.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>近くの空港に飛行場も</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, s))

if __name__ == '__main__':
    build(); build_now(); build_index()
