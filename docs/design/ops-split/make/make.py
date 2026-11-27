# -*- coding: utf-8 -*-
# 運用タブを「空港」と「機体」に分ける（design/ops-split）1版の画面案を作る。
# 1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。PNG は shoot.py で撮る。
# 色と字は main の src/index.html（運用タブの .opsapbtn・.viewsw・ON／OFF のスイッチ --sw-*・運用予想 案A の .rtl）に合わせる。
# 見本の時刻は 11/15 15:10（羽田・北風運用）。機体は アプリの特別塗装機の表（_shared/liveries.ts）にあるもの。便と予想は見本。
import os, base64, io
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

CSS = r"""
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#24292F;--ink2:#374151;--mute:#6B7280;--sub:#8A919C;--pill:#EEF0F3;--line:#E6E9EE;
  --blue:#2563EB;--navy:#16233A;--jal:#B4232A;--ana:#1C4FA0;--late:#B45309;--ok:#1F7A3F;
  --sw-on:#16233A;--sw-off:#E5E8EE;--sw-off-ring:#768090;
  --sh:0 12px 26px -18px rgba(15,23,42,.30),inset 0 0 0 1px rgba(17,24,39,.06);
  --gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg)}
body{width:390px;min-height:844px;margin:0 auto;font:500 15px/1.5 var(--gothic);color:var(--ink);-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
.pad{padding:8px 16px 120px}
button{font:inherit;color:inherit}
svg.i{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;flex:none}
/* アプリの上（今のまま） */
.brand{display:flex;justify-content:space-between;align-items:center;height:52px}
.brand b{font-size:19px;font-weight:800;letter-spacing:.12em;display:flex;align-items:center;gap:6px}
.brand span{height:44px;display:inline-flex;align-items:center;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800}
.mode{display:flex;background:#E3E7EC;border-radius:999px;padding:4px;margin-top:6px}
.mode span{flex:1;height:40px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.mode span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 8px -3px rgba(15,23,42,.3)}
/* 新：空港｜機体（運用タブの中の切り替え。上のスタンプラリー｜エアライン経営と見分けるため、選んだ側は濃い紺） */
.kindrow{display:flex;align-items:center;gap:8px;margin-top:16px}
.kind{display:inline-flex;gap:4px;background:var(--card);box-shadow:var(--sh);border-radius:999px;padding:4px}
.kind span{height:40px;min-width:88px;padding:0 16px;display:inline-flex;align-items:center;justify-content:center;gap:6px;border-radius:999px;font-size:15px;font-weight:800;color:var(--mute)}
.kind span.on{background:var(--navy);color:#fff}
.kind span svg{width:17px;height:17px}
.kindrow .sp{flex:1}
.ic{width:44px;height:44px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:var(--ink2)}
/* 空港・機体を選ぶ欄 */
.pickrow{display:flex;align-items:center;gap:8px;margin-top:12px}
.ap{height:48px;display:inline-flex;align-items:center;gap:8px;padding:0 14px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:17px;font-weight:800}
.ap i{font:700 13px/1 ui-monospace,Menlo,monospace;font-style:normal;color:#fff;background:var(--ink);border-radius:6px;padding:5px 6px}
.ap small{font-size:13px;font-weight:700;color:var(--ana)}
.ap.plr i{background:var(--jal)}
.ap.plr em{font-style:normal;font-size:13px;font-weight:700;color:var(--mute)}
.search{flex:1;height:48px;display:flex;align-items:center;gap:8px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:15px;color:var(--sub)}
.back{height:44px;display:inline-flex;align-items:center;gap:2px;padding:0 12px 0 6px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--ink2)}
/* 見方の帯（今の .viewsw：下線のタブ＋鉛筆） */
.views{display:flex;align-items:center;gap:20px;margin:16px 0 12px 2px;font-size:15px;font-weight:800;color:var(--mute);white-space:nowrap;overflow:hidden}
.views span{padding:11px 0 11px}
.views span.on{color:var(--ink);box-shadow:inset 0 -3px 0 var(--ink)}
.views .pen{margin-left:auto;flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--mute);background:linear-gradient(90deg,rgba(238,241,245,0),var(--bg) 30%)}
.views.fade{mask-image:linear-gradient(90deg,#000 86%,transparent)}
.card{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:16px}
.card+.card,.mt{margin-top:12px}
.h{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin:0 0 8px}
.h b{font-size:16px;font-weight:800}
.h small{font-size:13px;font-weight:600;color:var(--mute)}
.note{font-size:13px;line-height:1.7;color:var(--mute);margin:10px 0 0}
.note b{color:var(--ink2)}
/* 滑走路（今の見方の頭） */
.hero{background:#0F1B2D;color:#fff;border-radius:22px;padding:16px 16px 14px}
.hero .t{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#C9D2DE}
.hero .t em{font-style:normal;font-weight:800;color:#86EFAC;background:rgba(134,239,172,.12);border-radius:999px;padding:2px 10px}
.hero h3{margin:6px 0 10px;font-size:28px;font-weight:900;letter-spacing:.02em}
.hero .rw{display:flex;gap:18px;font-size:13px;color:#C9D2DE}
.hero .rw b{display:inline-block;margin:4px 6px 0 0;border:1.5px solid #fff;border-radius:6px;padding:1px 8px;font-size:16px;font-weight:800;color:#fff}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.tile{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:12px 14px}
.tile span{display:block;font-size:13px;color:var(--mute)}
.tile b{font-size:28px;font-weight:900}
.tile b small{font-size:14px;font-weight:700;color:var(--sub);margin-left:2px}
.tile em{display:block;font-style:normal;font-size:13px;color:var(--sub)}
/* 一覧の行 */
.rows{list-style:none;margin:0;padding:0}
.rows li{display:flex;align-items:center;gap:12px;min-height:60px;padding:8px 0}
.rows li+li{box-shadow:0 -1px 0 var(--line)}
.rows .tx{flex:1;min-width:0}
.rows .tx b{display:block;font-size:16px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rows .tx span{display:block;font-size:13px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rows .tx span span{display:inline;color:inherit}
.rows .tx span .tag{display:inline-flex;vertical-align:1px}
.rows .tx span .tag.live{color:var(--ok)}.rows .tx span .tag.pred{color:#3730A3}.rows .tx span .tag.gray{color:var(--ink2)}
.rows .go{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.reg{font:700 13px/1 ui-monospace,Menlo,monospace}
.sw{flex:none;width:52px;height:52px;border-radius:16px;display:flex;align-items:center;justify-content:center;font:800 13px/1 ui-monospace,Menlo,monospace;color:#fff}
.tag{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:2px 9px;font-size:13px;font-weight:800;white-space:nowrap}
.tag.live{background:#E7F5EC;color:var(--ok)}
.tag.gray{background:var(--pill);color:var(--ink2)}
.tag.pred{background:#EEF2FF;color:#3730A3}
.chips{display:flex;gap:8px;overflow:hidden}
.chip{height:44px;display:inline-flex;align-items:center;gap:6px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800;white-space:nowrap}
.chip.dark{background:var(--navy);color:#fff}
.chip small{font-size:14px;font-weight:700;color:var(--sub)}
.pillbtn{height:44px;display:inline-flex;align-items:center;justify-content:center;gap:4px;padding:0 18px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--ink2)}
/* 運用予想 案A（.rtl）：飛んだ便は1行にたたむ・「ここから予想」の帯 */
.rtl{list-style:none;margin:6px 0 0;padding:0}
.rtl li{display:grid;grid-template-columns:62px 22px 1fr;align-items:start;min-height:52px}
.rtl .tm b{font-size:16px;font-weight:800;font-variant-numeric:tabular-nums}
.rtl .tm small{display:block;font-size:13px;color:var(--sub)}
.rtl .dot{position:relative;height:100%}
.rtl .dot::before{content:"";position:absolute;left:10px;top:0;bottom:0;width:2px;background:#CBD2DC}
.rtl .dot i{position:absolute;left:5px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--ink2)}
.rtl li.pr .dot::before{background:repeating-linear-gradient(#AAB3C0 0 4px,transparent 4px 8px)}
.rtl li.pr .dot i{background:#fff;border:2px solid #6366F1}
.rtl li.now .dot i{background:var(--ok);box-shadow:0 0 0 4px rgba(31,122,63,.18)}
.rtl .tx{padding-bottom:12px}
.rtl .tx b{font-size:16px;font-weight:800}
.rtl .tx span{display:block;font-size:14px;color:var(--ink2)}
.rtl .tx em{display:flex;align-items:center;gap:6px;font-style:normal;font-size:13px;color:var(--mute);margin-top:2px}
.rtl li.fold .tx{color:var(--mute);font-size:14px}
.edge{grid-column:1/-1!important;display:flex!important;align-items:center;gap:8px;min-height:44px!important;margin:4px 0 6px}
.edge b{background:var(--navy);color:#fff;border-radius:999px;padding:3px 12px;font-size:13px;font-weight:800}
.edge span{font-size:13px;font-weight:700;color:var(--ink2)}
.cf{display:inline-flex;gap:3px;margin-right:2px}
.cf i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#6366F1}
.cf i.o{background:#C7CAF5}
/* 撮る人 */
.spot{display:flex;align-items:center;gap:10px}
.next li{min-height:64px}
.tmbig{flex:none;width:58px;font-size:18px;font-weight:900;font-variant-numeric:tabular-nums}
/* 振り分けの表（00） */
.sort{list-style:none;margin:0;padding:0}
.sort li{display:grid;grid-template-columns:1fr 64px 64px;gap:6px;align-items:center;min-height:44px;padding:6px 0;font-size:14px}
.sort li+li{box-shadow:0 -1px 0 var(--line)}
.sort li.hd{font-size:13px;color:var(--mute);font-weight:700;min-height:28px}
.sort li span{text-align:center;font-weight:800}
.sort li small{display:block;font-size:13px;color:var(--sub)}
.dotA{color:var(--ink)}.dotB{color:var(--navy)}
.shot{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 0}
.shot figure{margin:0}
.shot img{width:100%;border-radius:12px;box-shadow:var(--sh);display:block}
.shot figcaption{font-size:13px;color:var(--mute);text-align:center;margin-top:4px}
/* 下のタブ帯（変えない） */
.tabbar{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;width:362px;height:68px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 14px 34px -16px rgba(15,23,42,.35),inset 0 0 0 1px rgba(17,24,39,.06);display:flex;justify-content:space-around;align-items:center;z-index:5}
.tabbar span{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:13px;font-weight:800;color:var(--mute);min-width:56px}
.tabbar span svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8}
.tabbar span.on{color:var(--blue)}
/* シート */
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:8}
.sheet{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;max-height:94vh;overflow:hidden;background:var(--card);border-radius:26px 26px 0 0;padding:10px 20px 28px;z-index:9;box-shadow:0 -18px 40px -20px rgba(15,23,42,.4)}
.sheet .grab{width:40px;height:5px;border-radius:9px;background:#D5DAE1;margin:0 auto 8px}
.shh{display:flex;justify-content:space-between;align-items:center;gap:8px}
.shh h2{font-size:20px;font-weight:900;margin:0}
.shh button{flex:none;height:44px;padding:0 18px;border:0;border-radius:999px;background:var(--navy);color:#fff;font-weight:800;font-size:14px}
.sub{font-size:14px;color:var(--mute);margin:4px 0 0}
.kind.insheet{box-shadow:none;background:var(--pill);margin-top:12px;display:flex}
.kind.insheet span{flex:1}
.kind.insheet span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 8px -3px rgba(15,23,42,.3)}
.onoff{list-style:none;margin:8px 0 0;padding:0}
.onoff li{display:flex;align-items:center;gap:12px;min-height:56px;padding:4px 0}
.onoff li+li{box-shadow:0 -1px 0 var(--line)}
.onoff .tx{flex:1;min-width:0}
.onoff .tx b{display:block;font-size:16px;font-weight:800}
.onoff .tx span{display:block;font-size:13px;color:var(--mute)}
.onoff .grip{flex:none;width:28px;color:#AAB2BD;text-align:center;font-size:18px}
.onoff li.fixed .tx b::after{content:"いつも";margin-left:8px;font-size:13px;font-weight:700;color:var(--mute);background:var(--pill);border-radius:999px;padding:1px 8px}
.tg{flex:none;position:relative;width:76px;height:36px;border-radius:999px;display:flex;align-items:center;font-size:13px;font-weight:800}
.tg.on{background:var(--sw-on);color:#fff;padding-left:12px}
.tg.on::after{content:"";position:absolute;right:4px;top:4px;width:28px;height:28px;border-radius:50%;background:#fff}
.tg.off{background:var(--sw-off);color:#4B5563;box-shadow:inset 0 0 0 1.5px var(--sw-off-ring);justify-content:flex-end;padding-right:12px}
.tg.off::after{content:"";position:absolute;left:4px;top:4px;width:28px;height:28px;border-radius:50%;background:#fff;box-shadow:inset 0 0 0 1.5px var(--sw-off-ring)}
.grp{font-size:14px;font-weight:800;color:var(--ink2);margin:18px 0 0;display:flex;align-items:center;gap:8px}
.grp small{font-size:13px;font-weight:600;color:var(--sub)}
.badge{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;background:#FEF3C7;color:#92400E;font-size:13px;font-weight:800}
/* 表示の編集（全画面） */
.full{padding:10px 16px 40px}
.full .top{display:flex;align-items:center;justify-content:space-between;height:52px}
.full .top h2{font-size:18px;font-weight:900;margin:0}
.pills{display:flex;gap:6px;margin:8px 0 4px;overflow:hidden}
.pills span{height:44px;display:inline-flex;align-items:center;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800;color:var(--mute);white-space:nowrap}
.pills span.on{background:var(--navy);color:#fff}
/* 一覧ページ */
.idx{padding:16px 16px 40px}
.idx h1{font-size:22px;font-weight:900;margin:8px 0 4px}
.idx p{font-size:14px;color:var(--ink2);margin:6px 0}
.idx h2{font-size:16px;font-weight:900;margin:22px 0 6px}
.idx ul{list-style:none;margin:0;padding:0}
.idx li a{display:flex;align-items:center;gap:10px;min-height:52px;padding:6px 14px;margin-top:8px;background:var(--card);border-radius:16px;box-shadow:var(--sh);color:var(--ink);text-decoration:none}
.idx li a b{flex:none;font:800 14px/1 ui-monospace,Menlo,monospace;color:#fff;background:var(--navy);border-radius:8px;padding:6px 7px}
.idx li a span{font-size:14px;font-weight:700}
.idx li a small{display:block;font-size:13px;color:var(--mute);font-weight:500}
"""

def I(d, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{d}</svg>'
CHEV = '<path d="m9 6 6 6-6 6"/>'
DOWN = '<path d="m6 9 6 6 6-6"/>'
LEFT = '<path d="M15 6l-6 6 6 6"/>'
PEN = '<path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="m13.5 6.5 4 4"/>'
INFO = '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>'
SHARE = '<path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/>'
SRCH = '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>'
TOWER = '<path d="M9 21h6"/><path d="M10 21V11h4v10"/><path d="M7 7h10l-1.5 4h-7Z"/><path d="M12 3v4"/>'
PLANE = '<path d="M10.5 13.5 4 11l1.4-1.4 7 1.1 3.9-3.9c.8-.8 2.1-.8 2.9 0s.8 2.1 0 2.9l-3.9 3.9 1.1 7L15 22l-2.5-6.5-3 3v2.5L8 22.5l-1.3-3.2L3.5 18 5 16.5h2.5Z"/>'

TABBAR = f"""<nav class="tabbar">
<span>{I('<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>','')}ホーム</span>
<span>{I('<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>','')}図鑑</span>
<span>{I(PLANE,'')}フライト</span>
<span class="on">{I('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18 6"/>','')}運用</span>
<span>{I('<path d="M4 18 10 12l3 3 7-8"/><path d="M15 7h5v5"/>','')}修行</span></nav>"""

TOP = f"""<div class="brand"><b>{I('<circle cx="12" cy="12" r="9"/><path d="m8 15 8-6-3 8-1-3Z"/>')}そらメモ</b><span>マイページ</span></div>
<div class="mode"><span class="on">スタンプラリー</span><span>エアライン経営</span></div>"""

def kindrow(side):
    a = "on" if side == "ap" else ""; m = "on" if side == "pl" else ""
    return f"""<div class="kindrow"><div class="kind" role="tablist" aria-label="運用で見るもの"><span class="{a}">{I(TOWER)}空港</span><span class="{m}">{I(PLANE)}機体</span></div><span class="sp"></span>
<span class="ic">{I(INFO)}</span><span class="ic">{I(SHARE)}</span></div>"""

APPICK = f'<div class="pickrow"><span class="ap"><i>HND</i>羽田<small>近く</small>{I(DOWN)}</span></div>'

def views(items, on, fade=False):
    return f'<div class="views{" fade" if fade else ""}">' + "".join(f'<span class="{"on" if x == on else ""}">{x}</span>' for x in items) + f'<span class="pen">{I(PEN)}</span></div>'

AP_VIEWS_1 = ["案内板", "1日の山", "滑走路", "定時", "空の道すじ", "短冊", "撮る人"]
PL_VIEWS_1 = ["探す", "特別塗装機", "次に来る機体"]
PL_VIEWS_2 = ["探す", "特別塗装機"]

def page(name, title, body, extra=""):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>{body}{extra}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

RUNWAY = f"""<div class="hero"><div class="t"><span>いまの運用</span><em>● 実際の機体から判定</em></div><h3>北風運用</h3>
<div class="rw"><div>着陸<br><b>34L</b><b>34R</b></div><div>離陸<br><b>05</b><b>34R</b></div></div></div>
<div class="tiles"><div class="tile"><span>風</span><b>7<small>kt</small></b><em>340° から</em></div><div class="tile"><span>視程</span><b>10<small>km 以上</small></b><em>気象通報 15:00</em></div></div>
<div class="card mt"><div class="h"><b>地図と近くを飛ぶ機体</b><small>空港のまわり</small></div><div style="height:120px;border-radius:14px;background:linear-gradient(160deg,#E4EAF0,#D9E1EA)"></div></div>"""

FOOT_PL = '<p class="note">機体の位置は adsb.lol（ODbL）。予想は記録した便から作ったもので、<b>予想です。保証しません。</b></p>'

def build():
    # ---------- A1 空港側（滑走路）----------
    page("A1", "A1 空港側", f"""<div class="pad">{TOP}{kindrow("ap")}{APPICK}{views(AP_VIEWS_1, "滑走路", True)}{RUNWAY}</div>{TABBAR}""")

    # ---------- A1b 空港側（案内板＋海外の空港のいま）----------
    board = f"""<div class="card"><div class="h"><b>これから着く便</b><small>到着｜出発</small></div>
<ul class="rows">
<li><span class="tmbig">15:18</span><div class="tx"><b>JL 332 福岡から</b><span>B737-800・34L 着陸（推定）</span></div></li>
<li><span class="tmbig">15:25</span><div class="tx"><b>NH 18 伊丹から</b><span>B787-8・34R 着陸（推定）</span></div></li>
<li><span class="tmbig">15:31</span><div class="tx"><b>JL 44 ロンドンから</b><span>A350-1000・<span class="tag gray">ロンドン：便の数 欠航1</span></span></div></li>
</ul></div>
<div class="card"><div class="h"><b>行き先の海外の空港のいま</b><small>W1 の形</small></div><p class="note" style="margin-top:0">空港全体のようすです。<b>運航の判断には使えません。</b></p></div>"""
    page("A1b", "A1b 空港側 案内板", f"""<div class="pad">{TOP}{kindrow("ap")}{APPICK}{views(AP_VIEWS_1, "案内板")}{board}</div>{TABBAR}""")

    # ---------- A2 機体側のはじめ（何も選んでいない）----------
    recent = [("JA339J", "JAL Jubilee Express", "JAL・B737-800", "#B4232A", True, "JL 323 羽田→福岡・飛行中"),
              ("JA01XJ", "A350 1号機（赤のロゴ）", "JAL・A350-900", "#B4232A", False, "15:40 羽田に着く（予想）")]
    def rowpl(reg, nm, sub, col, live, line):
        tag = '<span class="tag live">● 飛行中</span>' if live else ('<span class="tag gray">地上</span>' if "駐機" in line else '<span class="tag pred">予想</span>')
        return f'<li><span class="sw" style="background:{col}">{reg[2:]}</span><div class="tx"><b>{nm}</b><span><span class="reg">{reg}</span>・{sub}</span><span>{tag} {line}</span></div><span class="go">{I(CHEV)}</span></li>'
    sp_now = [("JA05RK", "ジンベエジェット", "JTA・B737-800", "#0E7490", True, "JTA 9 羽田→那覇・飛行中"),
              ("JA381A", "FLYING HONU（青）", "ANA・A380", "#1C4FA0", False, "成田に駐機中"),
              ("JA228J", "J-AIR 創立30周年記念機", "J-AIR・E190", "#B4232A", True, "JL 2205 伊丹→松山・飛行中")]
    a2 = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す（例：JA339J）</span></div>
{views(PL_VIEWS_1, "探す")}
<div class="card"><div class="h"><b>最近見た機体</b><small>この端末で開いた順</small></div><ul class="rows">{"".join(rowpl(*r) for r in recent)}</ul></div>
<div class="card"><div class="h"><b>いま飛んでいる特別塗装機</b><small>17機</small></div><ul class="rows">{"".join(rowpl(*r) for r in sp_now)}</ul>
<div style="margin-top:8px"><span class="pillbtn">特別塗装機をすべて見る {I(CHEV)}</span></div></div>
{FOOT_PL}</div>"""
    page("A2", "A2 機体側 はじめ", a2 + TABBAR)

    # ---------- A2e 機体側のはじめ（最近見た機体がない人）----------
    a2e = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す（例：JA339J）</span></div>
{views(PL_VIEWS_1, "探す")}
<div class="card"><div class="h"><b>機体を1機ずつ追う</b></div><p class="note" style="margin-top:0;font-size:14px;color:var(--ink2)">登録記号（JA で始まる記号）か便名で探すと、その機体の今日の便と、この先の便（予想）が出ます。開いた機体はここに残ります。</p>
<div class="chips" style="margin-top:10px"><span class="chip">羽田に来る機体 <small>12</small></span><span class="chip">乗った機体 <small>8</small></span></div></div>
<div class="card"><div class="h"><b>いま飛んでいる特別塗装機</b><small>17機</small></div><ul class="rows">{"".join(rowpl(*r) for r in sp_now)}</ul></div>
{FOOT_PL}</div>"""
    page("A2e", "A2e 機体側 はじめ（最近なし）", a2e + TABBAR)

    # ---------- A3 機体を選んだあと（機体の1日 = 運用予想 案A を運用タブの中に）----------
    a3 = f"""<div class="pad">{TOP}{kindrow("pl")}
<div class="pickrow"><span class="back">{I(LEFT)}探す</span><span class="ap plr"><i>JA339J</i>B737-800<em>JAL</em>{I(DOWN)}</span></div>
{views(PL_VIEWS_1, "探す")}
<div class="card"><div class="h"><b>JAL Jubilee Express</b><small>特別塗装機</small></div>
<ul class="rtl">
<li class="fold"><div class="tm"><b>06:30</b><small>〜13:05</small></div><div class="dot"><i style="background:#AAB3C0"></i></div><div class="tx">今日飛んだ 3便 <span style="display:inline;color:var(--blue);font-weight:800">開く</span></div></li>
<li class="now"><div class="tm"><b>14:18</b><small>発</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 323</b><span>羽田 → 福岡</span><em><span class="tag live">● 飛行中</span>16:05 着く見込み（推定）</em></div></li>
<li class="edge"><b>ここから予想</b><span>予想です。保証しません</span></li>
<li class="pr"><div class="tm"><b>17:00</b><small>ごろ</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 332</b><span>福岡 → 羽田</span><em><span class="cf"><i></i><i></i><i></i></span>高い・12回中11回</em></div></li>
<li class="pr"><div class="tm"><b>20:00</b><small>ごろ</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 117</b><span>羽田 → 伊丹</span><em><span class="cf"><i></i><i></i><i class="o"></i></span>中くらい・7回中5回</em></div></li>
</ul>
<p class="note">時刻は予定（ODPT：公共交通オープンデータセンター）と、機体の位置から推定した時刻。正確・完全とは限りません。</p></div>
<div class="card"><div class="h"><b>今日の道すじ</b><small>地図</small></div><div style="height:110px;border-radius:14px;background:linear-gradient(160deg,#E4EAF0,#D9E1EA)"></div></div>
</div>"""
    page("A3", "A3 機体側 機体の1日", a3 + TABBAR)

    # ---------- A4 機体側・特別塗装機 ----------
    def sprow(reg, nm, sub, col, where, pred):
        return f'<li><span class="sw" style="background:{col}">{reg[2:]}</span><div class="tx"><b>{nm}</b><span><span class="reg">{reg}</span>・{sub}</span><span>{where}</span><span style="color:#3730A3;font-weight:700">この先（予想）{pred}</span></div><span class="go">{I(CHEV)}</span></li>'
    a4 = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す（例：JA339J）</span></div>
{views(PL_VIEWS_1, "特別塗装機")}
<div class="chips" style="margin-bottom:12px"><span class="chip dark">いま</span><span class="chip">この先</span><span class="chip">羽田に来る</span></div>
<div class="card"><div class="h"><b>いま飛んでいる</b><small>17機・アライアンス塗装 3機</small></div><ul class="rows">
{sprow("JA339J","JAL Jubilee Express","JAL・B737-800","#B4232A",'<span class="tag live">● 飛行中</span> JL 323 羽田→福岡',"17:00ごろ 福岡→羽田")}
{sprow("JA05RK","ジンベエジェット","JTA・B737-800","#0E7490",'<span class="tag live">● 飛行中</span> JTA 9 羽田→那覇',"18:40ごろ 那覇→石垣")}
{sprow("JA228J","J-AIR 創立30周年記念機","J-AIR・E190","#B4232A",'<span class="tag live">● 飛行中</span> JL 2205 伊丹→松山',"16:30ごろ 松山→伊丹")}
</ul></div>
<div class="card"><div class="h"><b>これから飛ぶ予定</b><small>航空会社の運航情報</small></div><ul class="rows">
<li><span class="tmbig">19:35</span><div class="tx"><b>★A350 1号機（赤のロゴ）</b><span>JL 25 羽田→香港・運航情報に記載</span></div></li></ul>
<p class="note">特別塗装機の一覧は航空会社の発表などをもとにそらメモがまとめたもの。運航情報は ODPT（正確・完全とは限りません）。</p></div>
</div>"""
    page("A4", "A4 機体側 特別塗装機", a4 + TABBAR)

    # ---------- 案1：撮る人を2つに分ける ----------
    p1 = f"""<div class="pad">{TOP}{kindrow("ap")}{APPICK}{views(AP_VIEWS_1, "撮る人", True)}
<div class="card"><div class="h"><b>見に行くなら（北風運用）</b><small>日の入り 16:35</small></div>
<ul class="rows">
<li><div class="tx"><b>城南島海浜公園</b><span>34R の着陸がま上を通る・順光は午前</span></div><span class="go">{I(CHEV)}</span></li>
<li><div class="tx"><b>第1ターミナル 展望デッキ</b><span>34L 着陸と 05 離陸が見える</span></div><span class="go">{I(CHEV)}</span></li>
<li><div class="tx"><b>浮島町公園</b><span>05 離陸の上昇が見える</span></div><span class="go">{I(CHEV)}</span></li></ul></div>
<div class="chips mt"><span class="chip">撮影条件と天気</span><span class="chip">空港の傾向</span><span class="chip">管制の交信</span></div>
<div class="card mt" style="display:flex;align-items:center;gap:10px"><div style="flex:1"><b style="font-size:15px">次に来る機体は「機体」へ</b><p class="note" style="margin:2px 0 0">選んだ撮影地から見える機体を、来る順に出します</p></div><span class="pillbtn">機体へ {I(CHEV)}</span></div>
</div>"""
    page("P1", "P1 案1 空港側 撮る人", p1 + TABBAR)

    p2 = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す</span></div>
{views(PL_VIEWS_1, "次に来る機体")}
<div class="pickrow" style="margin-top:0;margin-bottom:12px"><span class="chip">{I(TOWER)}羽田 {I(DOWN)}</span><span class="chip">第1ターミナル 展望デッキ {I(DOWN)}</span></div>
<div class="card"><div class="h"><b>次に来る機体</b><small>この3時間・来る順</small></div>
<div class="chips" style="margin-bottom:6px"><span class="chip dark">すべて</span><span class="chip">着陸</span><span class="chip">離陸</span></div>
<ul class="rows next">
<li><span class="tmbig">15:18</span><div class="tx"><b>JL 332 福岡から</b><span><span class="reg">JA737N</span>・B737-800・34L 着陸</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:40</span><div class="tx"><b>★A350 1号機（赤のロゴ）</b><span><span class="reg">JA01XJ</span>・JL 318 福岡から（推定）</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:52</span><div class="tx"><b>NH 242 福岡から</b><span><span class="reg">JA894A</span>・B787-9・34R 着陸</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">16:05</span><div class="tx"><b>BR 192 台北から</b><span>A321neo・34L 着陸（推定）</span></div><span class="go">{I(CHEV)}</span></li>
</ul>
<p class="note">「推定」は機体の位置と予想から出したおおよその時刻です。<b>予想です。保証しません。</b></p></div>
</div>"""
    page("P2", "P2 案1 機体側 次に来る機体", p2 + TABBAR)

    # ---------- 案2：撮る人は空港側にまとめる ----------
    q1 = f"""<div class="pad">{TOP}{kindrow("ap")}{APPICK}{views(AP_VIEWS_1, "撮る人", True)}
<div class="pickrow" style="margin-top:0;margin-bottom:12px"><span class="chip">第1ターミナル 展望デッキ {I(DOWN)}</span></div>
<div class="card"><div class="h"><b>次に来る機体</b><small>この3時間</small></div><ul class="rows next">
<li><span class="tmbig">15:18</span><div class="tx"><b>JL 332 福岡から</b><span><span class="reg">JA737N</span>・34L 着陸</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:40</span><div class="tx"><b>★A350 1号機（赤のロゴ）</b><span><span class="reg">JA01XJ</span>・JL 318（推定）</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:52</span><div class="tx"><b>NH 242 福岡から</b><span><span class="reg">JA894A</span>・34R 着陸</span></div><span class="go">{I(CHEV)}</span></li></ul></div>
<div class="card"><div class="h"><b>見に行くなら（北風運用）</b><small>日の入り 16:35</small></div><ul class="rows">
<li><div class="tx"><b>城南島海浜公園</b><span>34R の着陸がま上を通る</span></div><span class="go">{I(CHEV)}</span></li></ul></div>
<div class="chips mt"><span class="chip">撮影条件と天気</span><span class="chip">空港の傾向</span><span class="chip">機体を探す</span></div>
</div>"""
    page("Q1", "Q1 案2 空港側 撮る人", q1 + TABBAR)

    q2 = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す（例：JA339J）</span></div>
{views(PL_VIEWS_2, "探す")}
<div class="card"><div class="h"><b>最近見た機体</b><small>この端末で開いた順</small></div><ul class="rows">{"".join(rowpl(*r) for r in recent)}</ul></div>
<div class="card" style="display:flex;align-items:center;gap:10px"><div style="flex:1"><b style="font-size:15px">撮影地から見える機体</b><p class="note" style="margin:2px 0 0">空港の「撮る人」にあります</p></div><span class="pillbtn">撮る人へ {I(CHEV)}</span></div>
<div class="card"><div class="h"><b>いま飛んでいる特別塗装機</b><small>17機</small></div><ul class="rows">{"".join(rowpl(*r) for r in sp_now[:2])}</ul></div>
</div>"""
    page("Q2", "Q2 案2 機体側 はじめ", q2 + TABBAR)

    # ---------- V1 見方の設定（鉛筆）----------
    def oo(items):
        out = []
        for nm, sub, st in items:
            cls = ' class="fixed"' if st == "fix" else ""
            tg = "" if st == "fix" else (f'<span class="tg on">ON</span>' if st == "on" else '<span class="tg off">OFF</span>')
            out.append(f'<li{cls}><span class="grip">≡</span><div class="tx"><b>{nm}</b><span>{sub}</span></div>{tg}</li>')
        return '<ul class="onoff">' + "".join(out) + "</ul>"
    ap_items = [("案内板", "出発・到着の便を案内板の形で", "on"), ("1日の山", "1時間ごとの便の数と遅れ", "on"), ("滑走路", "いまの運用と使う滑走路", "on"),
                ("定時", "便の定時の割合", "on"), ("空の道すじ", "全機の航跡を重ねる", "on"), ("短冊", "次の離着陸を1便1枚で", "off"), ("撮る人", "撮影地と見に行く場所", "on")]
    pl_items = [("探す", "最近見た機体・登録記号で探す", "on"), ("特別塗装機", "いま飛んでいる・この先（予想）", "on"), ("次に来る機体", "撮影地から見える機体を来る順に", "on")]
    v1 = f"""<div class="pad">{TOP}{kindrow("ap")}{APPICK}{views(AP_VIEWS_1, "滑走路", True)}{RUNWAY}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>運用の見方</h2><button>完了</button></div>
<p class="sub">出す見方を ON にします。最後の1つは残ります。</p>
<div class="kind insheet"><span class="on">{I(TOWER)}空港</span><span>{I(PLANE)}機体</span></div>
{oo(ap_items)}</div>"""
    page("V1", "V1 見方の設定 空港", v1)
    v1b = f"""<div class="pad">{TOP}{kindrow("pl")}<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す</span></div>{views(PL_VIEWS_1, "探す")}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>運用の見方</h2><button>完了</button></div>
<p class="sub">出す見方を ON にします。最後の1つは残ります。</p>
<div class="kind insheet"><span>{I(TOWER)}空港</span><span class="on">{I(PLANE)}機体</span></div>
{oo(pl_items)}
<div class="grp">機体の側ごと隠す <small>運用は空港だけになります</small></div>
<ul class="onoff"><li><div class="tx"><b>「機体」を出す</b><span>OFF にすると上の切り替えが消えます</span></div><span class="tg on">ON</span></li></ul></div>"""
    page("V1b", "V1b 見方の設定 機体", v1b)

    # ---------- V2 表示の編集（マイページ）----------
    v2 = f"""<div class="full"><div class="top"><span class="back">{I(LEFT)}戻る</span><h2>表示の編集</h2><span class="pillbtn" style="background:var(--navy);color:#fff">完了</span></div>
<div class="pills"><span>タブ</span><span class="on">見方</span><span>ホームに出すもの</span></div>
<div class="grp">図鑑 <small>3つ中3つ</small></div>
<div class="grp">フライト <small>2つ中2つ</small></div>
<div class="grp">運用（空港） <small>7つ中6つ</small></div>
{oo(ap_items[:3] + [ap_items[5]])}
<p class="note" style="margin-top:2px">ほか3つ（定時・空の道すじ・撮る人）は ON</p>
<div class="grp">運用（機体） <small>3つ中3つ</small></div>
{oo(pl_items)}
<ul class="onoff"><li><div class="tx"><b>「機体」を出す</b><span>OFF で運用は空港だけ</span></div><span class="tg on">ON</span></li></ul>
<div class="grp">修行 <small>3つ中3つ</small></div>
</div>"""
    page("V2", "V2 表示の編集", v2)

    # ---------- 00 今の並びの整理 ----------
    from PIL import Image
    imgs = []
    for f, cap in [("00-runway.jpg", "滑走路（下に特別塗装機）"), ("06-photo.jpg", "撮る人（機体を探す・特別塗装機）"), ("01-board.jpg", "案内板")]:
        im = Image.open(os.path.join(HERE, "now", f)).convert("RGB"); w = 240; im = im.resize((w, int(im.size[1] * w / im.size[0])))
        im = im.crop((0, 0, w, 520)); bio = io.BytesIO(); im.save(bio, "JPEG", quality=62)
        imgs.append(f'<figure><img src="data:image/jpeg;base64,{base64.b64encode(bio.getvalue()).decode()}" alt=""><figcaption>{cap}</figcaption></figure>')
    rows = [("案内板", "A", ""), ("1日の山・定時・空の道すじ・短冊", "A", ""), ("滑走路と地図・門限・ゴーアラウンド・お知らせ", "A", ""),
            ("海外の空港のいま（W1）", "A", ""), ("撮影地・見に行く場所・撮影条件", "A", ""),
            ("機体を探す（今は撮る人の小さなボタン）", "B", "撮る人用"), ("機体の1日＋運用予想 案A（今はシート）", "B", "運用予想"),
            ("特別塗装機のいま／この先（今は滑走路と撮る人の下）", "B", "運用予想"), ("撮る人の次に来る機体", "AB", "撮る人用")]
    def mk(v, k):
        if v == "AB": return '<span>案2</span>' if k == "A" else '<span>案1</span>'
        return '<span>●</span>' if v == k else '<span></span>'
    tbl = '<ul class="sort"><li class="hd"><div>今あるもの</div><span>空港</span><span>機体</span></li>' + "".join(
        f'<li><div>{n}{f"<small>作る担当：{o}</small>" if o else ""}</div>{mk(v,"A")}{mk(v,"B")}</li>' for n, v, o in rows) + "</ul>"
    z = f"""<div class="idx"><h1>今の運用タブ</h1><p>本番（soramemo.jp）をデモで 11/15 19時ごろ撮影。見方の帯は7つで、機体のものは見方の下やシートに散らばっています。</p>
<div class="shot">{"".join(imgs)}</div>
<h2>振り分け</h2><div class="card">{tbl}<p class="note">運用タブの土台・空港側はチェックイン担当。機体を探すと次に来る機体は撮る人用担当、機体の1日と特別塗装機の予想は運用予想担当。</p></div></div>"""
    page("00", "00 今の並びの整理", z)

    # ---------- 一覧 ----------
    L = [("おすすめの形", [("A1", "空港側（滑走路）", "上に「空港｜機体」。選ぶ欄は空港"), ("A1b", "空港側（案内板）", "海外の空港のいまも空港側"),
                       ("A2", "機体側のはじめ", "最近見た機体＋いま飛んでいる特別塗装機"), ("A2e", "機体側のはじめ（最近なし）", "はじめて開いた人"),
                       ("A3", "機体を選んだあと", "機体の1日（運用予想 案A）をタブの中に"), ("A4", "機体側・特別塗装機", "いま／この先／羽田に来る")]),
         ("撮る人の置き場所 案1（おすすめ）：分ける", [("P1", "空港側・撮る人", "撮影地と見に行く場所だけ"), ("P2", "機体側・次に来る機体", "撮影地を選ぶ小さな欄つき")]),
         ("撮る人の置き場所 案2：空港側にまとめる", [("Q1", "空港側・撮る人", "今のまま次に来る機体も"), ("Q2", "機体側のはじめ", "撮る人への入口だけ")]),
         ("見方の設定", [("V1", "鉛筆のシート（空港）", "シートの中でも空港｜機体"), ("V1b", "鉛筆のシート（機体）", "「機体」ごと隠せる"), ("V2", "表示の編集", "運用（空港）と運用（機体）に分ける")]),
         ("今の画面", [("00", "今の並びの整理", "本番の写真と振り分け")])]
    body = '<div class="idx"><h1>運用タブを「空港」と「機体」に</h1><p>design/ops-split 1版（11/15）。画面案だけで、アプリには入れません。下のタブ帯は変えません。</p>'
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "運用を空港と機体に", body + "</div>")

if __name__ == "__main__":
    build(); print("ok")
