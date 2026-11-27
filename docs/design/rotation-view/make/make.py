# -*- coding: utf-8 -*-
# 運用予想を見やすく（design/rotation-view）1版の画面案を作る。
# 1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。PNG は shoot.py で撮る。
# 色と字は main の src/index.html に合わせる（--sky #EEF1F5・本文 #24292F・薄い字 #6B7280・紺 #0F1B2D・いま #C2410C・ゴシック体）。
import os, base64, html
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

CSS = r"""
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#24292F;--ink2:#374151;--mute:#6B7280;--sub:#8A919C;--pill:#EEF0F3;--hero:#0F1B2D;
  --now:#C2410C;--now-wash:#FDF0E6;--pred:#4B5563;--pred-wash:#F4F6F9;--ok:#1F7A3F;--ok-wash:#E7F6EC;--jal:#C8102E;
  --sh:0 12px 26px -18px rgba(15,23,42,.30),inset 0 0 0 1px rgba(17,24,39,.06);
  --gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg)}
body{width:390px;min-height:844px;margin:0 auto;font:500 15px/1.5 var(--gothic);color:var(--ink);-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
.pad{padding:12px 16px 120px}
button{font:inherit;color:inherit}
.top{display:flex;align-items:center;gap:8px;height:56px}
.back{height:44px;padding:0 16px 0 10px;border:0;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-weight:800;font-size:15px;display:inline-flex;align-items:center;gap:4px}
.back svg{width:20px;height:20px;stroke:var(--ink);fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.top h1{flex:1;text-align:center;font-size:17px;font-weight:800;margin:0 52px 0 0}
.search{display:flex;gap:8px;margin:6px 0 12px}
.search input{flex:1;min-width:0;width:100%;height:48px;border:0;border-radius:999px;background:var(--card);box-shadow:var(--sh);padding:0 18px;font:800 17px var(--gothic);color:var(--ink)}
.btn1{height:48px;padding:0 20px;border:0;border-radius:999px;background:var(--hero);color:#fff;font-weight:800;font-size:15px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:16px}
.card+.card,.card+.sec,.sec+.card{margin-top:12px}
.plane{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.plane b{font-size:22px;font-weight:900;letter-spacing:.01em}
.plane small{display:block;font-size:13px;color:var(--mute);margin-top:2px}
.live{flex:none;font-size:13px;font-weight:800;color:var(--ok);background:var(--ok-wash);border-radius:999px;padding:6px 12px}
.map{margin-top:12px;border-radius:16px;overflow:hidden;background:#E8EEF4;position:relative}
.map svg{display:block;width:100%;height:auto}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:13px;color:var(--mute)}
.legend i{display:inline-block;width:22px;height:0;border-top:3px solid #9CA3AF;vertical-align:middle;margin-right:6px}
.legend i.p{border-top:3px dashed var(--pred)}
.legend i.n{border-top-color:var(--now)}
.sec{display:flex;align-items:baseline;justify-content:space-between;margin:20px 4px 8px}
.sec b{font-size:16px;font-weight:800}
.sec span{font-size:13px;color:var(--mute)}
/* 時間の線 */
.tl{list-style:none;margin:0;padding:6px 14px;background:var(--card);border-radius:22px;box-shadow:var(--sh)}
.tl li{display:grid;grid-template-columns:62px 22px 1fr auto;align-items:start;column-gap:8px;padding:10px 0;position:relative}
.tl .tm b{display:block;font-size:20px;font-weight:900;line-height:1.15;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.tl .tm small{display:block;font-size:13px;color:var(--sub);line-height:1.3}
.tl .dot{position:relative;height:100%;min-height:40px}
.tl .dot::before{content:"";position:absolute;left:10px;top:0;bottom:-20px;border-left:3px solid #CBD2DA}
.tl li:last-child .dot::before{bottom:auto;height:14px}
.tl .dot i{position:absolute;left:4px;top:5px;width:15px;height:15px;border-radius:50%;background:#9CA3AF;box-shadow:0 0 0 3px var(--card)}
.tl .tx b{font-size:16px;font-weight:800}
.tl .tx span{display:block;font-size:15px;color:var(--ink2);line-height:1.4}
.tl .tx small{display:block;font-size:13px;color:var(--mute);margin-top:2px}
.tl .tag{font-size:13px;color:var(--sub);font-weight:700;padding-top:3px;text-align:right}
.tl li.now{background:var(--now-wash);border-radius:16px;margin:4px -8px;padding:10px 8px}
.tl li.now .dot::before{border-left-color:#CBD2DA}
.tl li.now .dot i{background:var(--now);box-shadow:0 0 0 3px var(--now-wash),0 0 0 7px rgba(194,65,12,.18)}
.tl li.now .tag{color:var(--now)}
.tl li.now .tm b{color:var(--now)}
.tl li.p .dot::before{border-left:3px dashed #B7BFC9}
.tl li.p .dot i{background:var(--card);border:2.5px dashed var(--pred);box-shadow:0 0 0 3px var(--card)}
.tl li.p .tm b{color:var(--pred);font-weight:800}
.tl li.p .tm b em{font-style:normal;font-size:13px;font-weight:700;color:var(--sub);margin-left:1px}
.tl li.p .tx b,.tl li.p .tx span{color:var(--pred)}
.tl li.day{display:block;padding:12px 0 2px 92px;font-size:13px;font-weight:800;color:var(--mute)}
.tl li.day::before{content:"";position:absolute;left:80px;top:0;bottom:0;border-left:3px dashed #B7BFC9}
/* 境目 */
.edge{display:block!important;padding:14px 0 10px!important;text-align:center}
.edge::before{content:"";position:absolute;left:0;right:0;top:27px;border-top:2px dashed #C3CAD3}
.edge b{position:relative;display:inline-block;background:var(--hero);color:#fff;font-size:13px;font-weight:800;border-radius:999px;padding:5px 14px}
.edge small{display:block;font-size:13px;color:var(--mute);margin-top:6px}
/* 確からしさ（3段の濃さ＋言葉） */
.cf{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;font-size:13px;font-weight:800;color:var(--pred)}
.cf .d{display:inline-flex;gap:3px}
.cf .d i{width:9px;height:9px;border-radius:50%;background:#D5DAE1}
.cf.c3 .d i{background:var(--pred)}
.cf.c2 .d i:nth-child(-n+2){background:var(--pred)}
.cf.c1 .d i:nth-child(1){background:var(--pred)}
.cf.lv{color:var(--ink)}
.cf.lv .d i{border-radius:3px;background:var(--ink)}
.pillbtn{height:44px;padding:0 18px;border:0;border-radius:999px;background:var(--pill);font-weight:800;font-size:15px;display:inline-flex;align-items:center;gap:6px;color:var(--ink)}
.pillbtn.dark{background:var(--hero);color:#fff}
.pillbtn.w{background:var(--card);box-shadow:var(--sh)}
.pillbtn.line{background:transparent;box-shadow:inset 0 0 0 1.5px #C9CFD7}
.row2{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.note{font-size:13px;line-height:1.7;color:var(--mute);margin:16px 4px 0}
.warn{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.6;color:var(--ink2);background:var(--pred-wash);border-radius:14px;padding:10px 12px;margin-top:10px}
.warn b{font-weight:800}
/* 下のタブ帯 */
.tabbar{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;width:362px;height:68px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 14px 34px -16px rgba(15,23,42,.35),inset 0 0 0 1px rgba(17,24,39,.06);display:flex;justify-content:space-around;align-items:center;z-index:5}
.tabbar span{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:13px;font-weight:800;color:var(--mute);min-width:56px}
.tabbar span svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8}
.tabbar span.on{color:#2563EB}
/* 運用タブの欄（今のアプリの .lo / ops カードに合わせる） */
.opsh{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.opsh b{font-size:17px;font-weight:800}
.opsh span{font-size:13px;color:var(--mute);background:var(--pill);border-radius:999px;padding:3px 10px;font-weight:700}
.spl{list-style:none;margin:0;padding:0}
.spl>li{padding:14px 0}
.spl>li+li{box-shadow:0 -1px 0 #EEF0F3}
.spl .nm{font-size:16px;font-weight:800}
.spl .nm small{font-size:13px;font-weight:500;color:var(--mute);margin-left:4px}
.spl .wh{font-size:14px;color:var(--ink2);margin-top:2px}
.spl .pillbtn{margin-top:10px;height:44px;font-size:14px}
/* 小さい時間の線（一覧の中に開く形） */
.mini{list-style:none;margin:10px 0 0;padding:6px 12px;background:var(--pred-wash);border-radius:18px}
.mini li{display:grid;grid-template-columns:56px 18px 1fr auto;column-gap:6px;align-items:start;padding:8px 0;position:relative}
.mini .tm b{display:block;font-size:17px;font-weight:900;line-height:1.2;font-variant-numeric:tabular-nums}
.mini .tm small{display:block;font-size:13px;color:var(--sub)}
.mini .dot{position:relative;min-height:34px}
.mini .dot::before{content:"";position:absolute;left:7px;top:0;bottom:-16px;border-left:2.5px dashed #B7BFC9}
.mini li:last-child .dot::before{bottom:auto;height:12px}
.mini .dot i{position:absolute;left:1px;top:5px;width:14px;height:14px;border-radius:50%;background:var(--pred-wash);border:2.5px dashed var(--pred)}
.mini li.now .dot i{background:var(--now);border:0;box-shadow:0 0 0 3px var(--pred-wash),0 0 0 6px rgba(194,65,12,.18)}
.mini li.now .dot::before{border-left:2.5px solid #CBD2DA}
.mini li.now .tm b{color:var(--now)}
.mini li.now .tag{color:var(--now);font-size:13px;font-weight:800}
.mini li.p .tm b{color:var(--pred);font-weight:800}
.mini li.p .tm b em{font-style:normal;font-size:13px;color:var(--sub);font-weight:700}
.mini .tx{font-size:14px;line-height:1.45;color:var(--ink2)}
.mini .tx b{font-size:15px;font-weight:800;color:var(--ink)}
.mini li.p .tx,.mini li.p .tx b{color:var(--pred)}
.mini .tx small{display:block;font-size:13px;color:var(--mute)}
.mini .edge{grid-template-columns:1fr!important;padding:12px 0 6px!important}
.mini .edge::before{top:24px}
.mini .edge b{background:var(--hero)}
.mini .edge small{margin-top:4px}
.minifoot{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:10px}
.minifoot small{font-size:13px;color:var(--mute)}
/* 濃い面（特別塗装機のくわしく）＝今のアプリの spbhero に合わせる */
.hero{background:var(--hero);color:#fff;border-radius:24px;padding:18px;position:relative;overflow:hidden;box-shadow:0 18px 34px -22px rgba(15,23,42,.6)}
.hero::before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--jal);opacity:.85}
.hero small{font-size:13px;color:#A7B0BC}
.hero .nm{font-size:22px;font-weight:800;margin-top:2px}
.hero .rt{display:flex;align-items:center;gap:14px;font-size:34px;font-weight:900;margin-top:6px;letter-spacing:.02em}
.hero .rt i{font-style:normal;color:#E9C46A;font-size:26px}
.hero .rt span{margin-left:auto;font-size:14px;font-weight:600;color:#C9D1DB}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.tiles div{background:rgba(255,255,255,.07);border-radius:14px;padding:10px 12px}
.tiles span{display:block;font-size:13px;color:#A7B0BC}
.tiles b{font-size:21px;font-weight:900}
.tiles b small{font-size:13px;color:#A7B0BC;margin-left:2px}
/* シート */
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:8}
.sheet{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;background:var(--card);border-radius:26px 26px 0 0;padding:10px 20px 28px;z-index:9;box-shadow:0 -18px 40px -20px rgba(15,23,42,.4)}
.sheet .grab{width:40px;height:5px;border-radius:9px;background:#D5DAE1;margin:0 auto 12px}
.sheet h2{font-size:19px;font-weight:900;margin:0 0 4px}
.sheet p{font-size:14px;color:var(--ink2);margin:0 0 12px;line-height:1.65}
.lv3{list-style:none;margin:0;padding:0}
.lv3 li{display:grid;grid-template-columns:1fr;gap:4px;align-items:start;padding:12px 0}
.lv3 li+li{box-shadow:0 -1px 0 #EEF0F3}
.lv3 .ex{font-size:14px;line-height:1.6;color:var(--ink2)}
.lv3 .ex b{font-size:15px;color:var(--ink)}
/* 案B：次の1便を大きく */
.next{background:var(--card);border-radius:24px;box-shadow:var(--sh);padding:18px;position:relative}
.next .lab{display:flex;justify-content:space-between;align-items:center}
.next .lab b{font-size:13px;font-weight:800;color:#fff;background:var(--hero);border-radius:999px;padding:5px 12px}
.next .big{display:flex;align-items:baseline;gap:4px;margin-top:12px}
.next .big b{font-size:44px;font-weight:900;line-height:1;letter-spacing:-.02em;color:var(--pred);font-variant-numeric:tabular-nums}
.next .big em{font-style:normal;font-size:15px;font-weight:700;color:var(--sub)}
.next .rt{font-size:22px;font-weight:800;margin-top:8px;color:var(--ink2)}
.next .rt small{font-size:15px;color:var(--mute);font-weight:600;margin-left:6px}
.next .foot{display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:12px;box-shadow:0 -1px 0 #EEF0F3}
.next .foot small{font-size:13px;color:var(--mute)}
.after{list-style:none;margin:0;padding:4px 16px;background:var(--card);border-radius:22px;box-shadow:var(--sh)}
.after li{display:grid;grid-template-columns:94px 1fr auto;gap:8px;align-items:center;padding:12px 0}
.after li+li{box-shadow:0 -1px 0 #EEF0F3}
.after .tm{white-space:nowrap;font-size:18px;font-weight:800;color:var(--pred);font-variant-numeric:tabular-nums}
.after .tm em{font-style:normal;font-size:13px;color:var(--sub)}
.after .tx{font-size:15px;color:var(--pred)}
.after .tx b{font-weight:800}
.flown{display:flex;align-items:center;justify-content:space-between;background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:14px 16px;min-height:56px}
.flown b{font-size:15px;font-weight:800}
.flown small{display:block;font-size:13px;color:var(--mute)}
.flown svg{width:20px;height:20px;stroke:var(--mute);fill:none;stroke-width:2.2}
/* 案C：1日の帯 */
.band{position:relative;height:118px;margin:10px 0 0}
.band .ax{position:absolute;left:0;right:0;top:34px;height:44px;border-radius:12px;background:var(--pred-wash)}
.band .blk{position:absolute;top:34px;height:44px;border-radius:10px}
.band .blk.f{background:#AEB6C0}
.band .blk.n{background:var(--now)}
.band .blk.p{background:repeating-linear-gradient(135deg,rgba(75,85,99,var(--a)) 0 5px,rgba(75,85,99,calc(var(--a)*.35)) 5px 10px);box-shadow:inset 0 0 0 2px rgba(75,85,99,var(--a))}
.band .blk.sel{outline:3px solid var(--hero);outline-offset:2px}
.band .tk{position:absolute;top:84px;font-size:13px;color:var(--sub);transform:translateX(-50%);font-variant-numeric:tabular-nums}
.band .nowl{position:absolute;top:22px;height:64px;border-left:2px solid var(--now)}
.band .nowl span{white-space:nowrap;position:absolute;top:-22px;left:-18px;font-size:13px;font-weight:800;color:var(--now)}
.band .edgeL{position:absolute;top:2px;font-size:13px;font-weight:800;color:#fff;background:var(--hero);border-radius:999px;padding:2px 10px;white-space:nowrap}
.bleg{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--mute);margin-top:4px}
.bleg i{display:inline-block;width:18px;height:12px;border-radius:4px;vertical-align:-1px;margin-right:6px}
.selc{margin-top:12px;background:var(--pred-wash);border-radius:18px;padding:12px 14px;display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center}
.selc .tm{font-size:24px;font-weight:900;color:var(--pred)}
.selc .tm em{font-style:normal;font-size:13px;color:var(--sub)}
.selc .tx{grid-column:1/-1;font-size:15px;color:var(--ink2)}
.selc .tx b{font-weight:800}
.small-list{list-style:none;margin:0;padding:4px 16px;background:var(--card);border-radius:22px;box-shadow:var(--sh)}
.small-list li{display:flex;justify-content:space-between;align-items:center;padding:11px 0;font-size:15px}
.small-list li+li{box-shadow:0 -1px 0 #EEF0F3}
.small-list li .t{font-weight:800;font-variant-numeric:tabular-nums;width:64px;display:inline-block}
.small-list li.p{color:var(--pred)}
.small-list li small{font-size:13px;color:var(--sub)}
/* 今の画面（写真に番号） */
.shot{position:relative;border-radius:22px;overflow:hidden;box-shadow:var(--sh);background:#fff}
.shot img{display:block;width:100%}
.mk{position:absolute;width:28px;height:28px;border-radius:50%;background:#C2410C;color:#fff;font-size:15px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #fff}
.issues{list-style:none;margin:12px 0 0;padding:0;counter-reset:n}
.issues li{display:grid;grid-template-columns:28px 1fr;gap:10px;background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:12px 14px;font-size:14px;line-height:1.6;color:var(--ink2)}
.issues li+li{margin-top:8px}
.issues li i{font-style:normal;width:26px;height:26px;border-radius:50%;background:#C2410C;color:#fff;font-weight:900;display:flex;align-items:center;justify-content:center;font-size:14px}
.issues li b{color:var(--ink)}
.cap{font-size:13px;color:var(--mute);margin:6px 4px 0}
"""

def page(title, body, extra=""):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=390, initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}{extra}</style></head><body>{body}</body></html>"""

BACK = '<svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg>'
CHEV = '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>'
DOWN = '<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>'

def tabbar(on="運用"):
    ic = {"ホーム":'<path d="M4 11l8-7 8 7v9H4z"/>', "図鑑":'<path d="M4 5h7v15H4zM13 5h7v15h-7z"/>', "フライト":'<path d="M3 13l18-7-7 18-2-8z"/>', "運用":'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>', "修行":'<path d="M5 19h4v-5h4V9h4V5"/>'}
    return '<nav class="tabbar">' + "".join(f'<span class="{"on" if k==on else ""}"><svg viewBox="0 0 24 24">{v}</svg>{k}</span>' for k, v in ic.items()) + '</nav>'

def cf(level):
    if level == "lv": return '<span class="cf lv"><span class="d"><i></i><i></i><i></i></span>運航情報の予定</span>'
    w = {3:"高い", 2:"中くらい", 1:"低い"}[level]
    return f'<span class="cf c{level}"><span class="d"><i></i><i></i><i></i></span>{w}</span>'

# ---- 見本の機体（本番で 11/13 20時45分に見た JA339J の今日の便をもとに、時刻を 14時50分の場面にした） ----
FLOWN = [("07:40", "〜08:42", "JL141", "羽田 → 青森"), ("09:42", "〜10:40", "JL142", "青森 → 羽田"), ("11:38", "〜13:14", "JL259", "羽田 → 広島")]
NOW = ("14:18", "〜いま", "JL258", "広島 → 羽田", "着く 15:24ごろ（推定）")
PRED = [("16:15", "JL147", "羽田 → 青森", "lv"), ("18:35", "JL148", "青森 → 羽田", 3), ("20:30", "JL599", "羽田 → 新千歳", 2)]
TOMORROW = [("07:30", "JL502", "新千歳 → 羽田", 1)]

def tl_rows(flown=True):
    r = []
    if flown:
        for t, e, f, rt in FLOWN:
            r.append(f'<li><div class="tm"><b>{t}</b><small>{e}</small></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span></div><div class="tag">飛んだ</div></li>')
    t, e, f, rt, s = NOW
    r.append(f'<li class="now"><div class="tm"><b>{t}</b><small>{e}</small></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span><small>{s}</small></div><div class="tag">飛行中</div></li>')
    r.append('<li class="edge"><b>ここから予想</b><small>前の記録からの推定です。保証しません</small></li>')
    for t, f, rt, lv in PRED:
        r.append(f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span></div><div class="tag">{cf(lv)}</div></li>')
    r.append('<li class="day">11月14日（土）</li>')
    for t, f, rt, lv in TOMORROW:
        r.append(f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span></div><div class="tag">{cf(lv)}</div></li>')
    return '<ul class="tl">' + "".join(r) + '</ul>'

def mini(n=2, base=None):
    t, e, f, rt, s = NOW
    r = [f'<li class="now"><div class="tm"><b>{t}</b><small>いま</small></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b> {rt}<small>{s}</small></div><div class="tag">飛行中</div></li>' if not base else base,
         '<li class="edge"><b>ここから予想</b><small>推定です。保証しません</small></li>']
    for t, f, rt, lv in PRED[:n]:
        r.append(f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b> {rt}<small>{cf(lv)}</small></div><div></div></li>')
    return '<ul class="mini">' + "".join(r) + '</ul>'

# ---- 航空図風の地図（緯線・経線と、大まかな海岸線。外部の地図は読まない） ----
COAST = [
 [(41.4,140.0),(42.0,139.8),(43.2,140.3),(44.0,141.6),(45.4,141.9),(44.4,143.3),(43.9,145.3),(43.0,145.7),(42.9,143.4),(42.0,143.2),(42.6,141.5),(41.8,141.0),(41.4,140.0)],
 [(41.5,140.9),(40.6,141.5),(39.5,142.0),(38.3,141.5),(37.0,141.0),(35.7,140.9),(35.1,140.0),(35.3,139.7),(34.9,139.8),(35.2,139.1),(34.6,138.2),(34.6,137.0),(33.5,135.8),(34.3,135.1),(34.4,134.0),(34.0,132.0),(34.0,131.0),(34.5,131.4),(35.5,133.0),(35.6,134.5),(35.8,135.8),(36.8,136.7),(37.5,137.3),(37.0,138.0),(38.0,139.4),(39.5,140.0),(40.6,139.9),(41.5,140.9)],
 [(34.3,133.0),(34.2,134.6),(33.8,134.7),(33.3,134.2),(32.8,132.9),(33.3,132.4),(33.9,132.7),(34.3,133.0)],
 [(33.9,130.9),(33.5,131.7),(32.0,131.5),(31.0,131.0),(31.2,130.2),(32.2,130.1),(32.7,129.7),(33.5,129.6),(33.9,130.9)]]
AP = {"羽田":(35.55,139.78), "青森":(40.73,140.69), "広島":(34.44,132.92), "新千歳":(42.78,141.69)}
def mapsvg(w=358, h=200, lat0=32.6, lat1=44.0, lon0=130.6, lon1=146.0, flown=True, nowseg=True, pred=True):
    sx = lambda lo: (lo - lon0) / (lon1 - lon0) * w
    sy = lambda la: (lat1 - la) / (lat1 - lat0) * h
    g = []
    for la in range(34, 44, 2): g.append(f'<line x1="0" x2="{w}" y1="{sy(la):.1f}" y2="{sy(la):.1f}" stroke="#D3DCE6" stroke-width="1"/>')
    for lo in range(132, 147, 2): g.append(f'<line y1="0" y2="{h}" x1="{sx(lo):.1f}" x2="{sx(lo):.1f}" stroke="#D3DCE6" stroke-width="1"/>')
    for poly in COAST: g.append('<polygon points="' + " ".join(f"{sx(lo):.1f},{sy(la):.1f}" for la, lo in poly) + '" fill="#F7F4EC" stroke="#C9C2AE" stroke-width="1"/>')
    P = lambda k: (sx(AP[k][1]), sy(AP[k][0]))
    def seg(a, b, st):
        (x1, y1), (x2, y2) = P(a), P(b); g.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" {st} stroke-linecap="round"/>')
    if flown: seg("羽田", "青森", 'stroke="#9CA3AF" stroke-width="3.5"'); seg("羽田", "広島", 'stroke="#9CA3AF" stroke-width="3.5"')
    if pred: seg("羽田", "新千歳", 'stroke="#4B5563" stroke-width="3" stroke-dasharray="6 6"'); seg("羽田", "青森", 'stroke="#4B5563" stroke-width="3" stroke-dasharray="6 6" transform="translate(6,2)"')
    if nowseg:
        (x1, y1), (x2, y2) = P("広島"), P("羽田"); mx, my = x1 + (x2 - x1) * .62, y1 + (y2 - y1) * .62
        g.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{mx:.1f}" y2="{my:.1f}" stroke="#C2410C" stroke-width="3.5" stroke-linecap="round"/>')
        g.append(f'<g transform="translate({mx:.1f},{my:.1f}) rotate(-80)"><path d="M0,-9 L3,-2 L10,1 L10,3 L3,2 L2,7 L4,9 L4,10 L0,9 L-4,10 L-4,9 L-2,7 L-3,2 L-10,3 L-10,1 L-3,-2 Z" fill="#C2410C" transform="rotate(90)"/></g>')
    lab = {"羽田":(10, 18), "青森":(10, 4), "広島":(-8, 22), "新千歳":(10, 4)}
    for k in AP:
        x, y = P(k); g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#24292F" stroke="#fff" stroke-width="2"/>')
        dx, dy = lab[k]; g.append(f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" font-size="13" font-weight="800" fill="#24292F" stroke="#F7F4EC" stroke-width="3" paint-order="stroke" font-family="var(--gothic)">{k}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="今日飛んだ区間と予想の区間の地図">{"".join(g)}</svg>'

def top(title, back="戻る"):
    return f'<div class="top"><button class="back">{BACK}{back}</button><h1>{title}</h1></div>'

def plane_card(map_=True, h=200):
    return f'''<div class="card"><div class="plane"><span><b>JA339J</b><small>B738・★JAL Jubilee Express</small></span><span class="live">いま飛行中</span></div>
      {f'<div class="map">{mapsvg(h=h)}</div><div class="legend"><span><i></i>飛んだ</span><span><i class="n"></i>いま</span><span><i class="p"></i>予想</span></div>' if map_ else ''}</div>'''

FOOT = '<p class="note">飛んだ便は機体の位置の記録（adsb.lol）から。予想は、この機体が前の記録でこの便のあとに飛んだ便からの推定で、機体の入れ替えで違うことがあります。<b style="color:var(--ink2)">予想は保証しません。</b></p>'

S = {}  # 名前 → (題, 説明, html)

# ===== 00 今の画面 =====
def img(name):
    return "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(HERE, "now", name + ".jpg"), "rb").read()).decode()
def now_page(name, title, shot, marks, issues, crop_h=520, cap=""):
    mk = "".join(f'<span class="mk" style="left:{x}px;top:{y}px">{i+1}</span>' for i, (x, y) in enumerate(marks))
    li = "".join(f'<li><i>{i+1}</i><span>{t}</span></li>' for i, t in enumerate(issues))
    body = f'''<div class="pad" style="padding-bottom:24px">{top(title, "今の画面")}
      <div class="shot" style="height:{crop_h}px"><img src="{img(shot)}" alt="">{mk}</div><p class="cap">{cap}</p>
      <ul class="issues">{li}</ul></div>'''
    return page(title, body)

S["00a"] = ("今：機体の1日", "本番（11/13 20時45分・デモ）で撮った JA339J。読みにくい所に番号",
  now_page("00a", "機体の1日（今）", "00a", [(300, 40), (330, 250), (20, 470)], [
    "<b>地図の名札が重なる</b>（広島と高松）。予想の線（橙の点線）が何かの説明がない",
    "<b>飛んだ便と予想の便が同じ見た目</b>。札（飛んだ／予想）が小さい灰色のピルで同じ形。境目がない。別の時刻に撮ったときは、<b>いま飛んでいる JL599 が予想の1便目にもう1回出た</b>",
    "<b>予想の確からしさが「予想・64%」の数字だけ</b>で、何の割合か分からない。時刻が小さい字。今は予想が出ないとき何も書かない（この写真）"], crop_h=560,
    cap="本番の写真（機体の1日のいちばん下まで送ったところ）"))
S["00b"] = ("今：運用の特別塗装機", "運用タブの「いま飛んでいる特別塗装機」で「この先の便（推定）」を開いたところ",
  now_page("00b", "運用の特別塗装機（今）", "00b", [(330, 196), (12, 236), (330, 280)], [
    "<b>ピルのボタンがカードの右の端からはみ出す</b>（どの機体の行も）",
    "<b>「いまの便」が古い</b>。一覧では JAL599 で飛んでいるのに、開くと「いまの便：JL148」、予想の1便目が今飛んでいる JL599。見る人には「外れた」に見える",
    "予想は1行の小さい字（12.5px）。<b>時刻・区間・割合が同じ大きさ</b>で並ぶ。説明の字が予想より大きい"], crop_h=560,
    cap="本番の写真（JA339J の行を開いたところ）"))
S["00c"] = ("今：これから飛ぶ予定", "運用タブの「これから飛ぶ予定」（航空会社の運航情報）",
  now_page("00c", "これから飛ぶ予定（今）", "00c", [(330, 60), (330, 200)], [
    "<b>「出発済み」（もう飛んだ便）と、これからの便が同じ一覧に混ざる</b>。並びも 19:55・20:30・20:45 のあとに朝の 06:25 が来る",
    "★と塗装名が長く、<b>時刻と区間が2行目に折り返す</b>。いちばん知りたい時刻が見つけにくい"], crop_h=350,
    cap="本番の写真（予想ではなく運航情報の予定だが、実績と予定が混ざる例として）"))
S["00d"] = ("今：特別塗装機のくわしく", "特別塗装機の画面で JA339J を開いたところ",
  now_page("00d", "特別塗装機のくわしく（今）", "00d", [(330, 330), (330, 520)], [
    "<b>この先の便（予想）が出ない</b>。一覧では開けるのに、くわしくの画面では見られない",
    "「今日の足あと」に「時刻表から」の小さい札。飛んだ便の時刻が記録か時刻表か、が混ざって見える（実績なのか予想なのか迷う）"], crop_h=560,
    cap="本番の写真"))

# ===== 案A：時間の線（おすすめ） =====
S["A1"] = ("案A 機体の1日", "時間の線。飛んだ便（実線）→ いま（橙）→「ここから予想」の帯 → 予想（点線・白い丸）。確からしさは3段の濃さ＋言葉",
  page("案A 機体の1日", f'''<div class="pad">{top("機体の1日")}
    <div class="search"><input value="JA339J" aria-label="登録記号"><button class="btn1">探す</button></div>
    {plane_card()}
    <div class="sec"><b>今日</b><span>11月13日（金）</span></div>
    {tl_rows()}
    <div class="row2"><button class="pillbtn w">確からしさとは</button><button class="pillbtn line">近づいたら知らせる</button></div>
    {FOOT}</div>'''))

S["A2"] = ("案A 運用の特別塗装機", "一覧で開くと、いまの便から始まる小さい時間の線。予想は2便まで、続きは機体の1日へ",
  page("案A 運用の特別塗装機", f'''<div class="pad" style="padding-top:20px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★FLYING HONU（緑）<small>ANA・NH184（JA382A）</small></div><div class="wh">飛行中・高度 30,400ft</div><button class="pillbtn">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2.2"')}</button></li>
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL258（JA339J）</small></div><div class="wh">広島から羽田へ・高度 24,000ft</div>
        <button class="pillbtn dark">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:#fff;fill:none;stroke-width:2.2;transform:rotate(180deg)"')}</button>
        {mini(2)}
        <div class="minifoot"><small>あと2便の予想</small><button class="pillbtn line">機体の1日 ›</button></div></li>
      <li><div class="nm">★結ジンベエ<small>JTA・JTA49（JA07RK）</small></div><div class="wh">飛行中・高度 32,000ft</div><button class="pillbtn">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2.2"')}</button></li>
    </ul></div></div>{tabbar()}'''))

S["A3"] = ("案A 撮る人のくわしく", "撮る人の機体のくわしくの「この機体の運用（予想）」。開いた形は運用タブと同じ部品",
  page("案A 撮る人のくわしく", f'''<div class="pad">{top("JL258")}
    <div class="card"><small style="font-size:13px;color:var(--mute)">着陸</small><div style="display:flex;align-items:baseline;gap:8px"><b style="font-size:34px;font-weight:900">15:24</b><small style="font-size:13px;color:var(--sub)">ごろ（推定）</small><span style="margin-left:auto;font-size:15px;font-weight:800">34L か 34R</span></div>
      <div style="font-size:14px;color:var(--ink2);margin-top:4px">広島 → 羽田・B738・高度 24,000ft・空港まで約180km</div></div>
    <div class="card"><div style="display:flex;justify-content:space-between;align-items:center"><span><small style="font-size:13px;color:var(--mute)">この機体の運用（予想）</small><b style="display:block;font-size:18px;font-weight:900">JA339J <span style="font-size:13px;color:var(--mute);font-weight:600">★JAL Jubilee Express</span></b></span></div>
      {mini(3)}
      <div class="row2"><button class="pillbtn line">機体の1日 ›</button><button class="pillbtn">確からしさとは</button></div></div>
    <div class="card" style="opacity:.55"><small style="font-size:13px;color:var(--mute)">どこから撮る</small><div style="font-size:15px;font-weight:800;margin-top:4px">城南島海浜公園・浮島町公園 …</div></div>
    </div>'''))

S["A4"] = ("案A 特別塗装機のくわしく", "今日の足あと（実績だけ）の下に「この先（予想）」を足す。境目の帯は機体の1日と同じ",
  page("案A 特別塗装機のくわしく", f'''<div class="pad">{top("JAL Jubilee Express", "特別塗装機")}
    <div class="hero"><small>JAL・JA339J</small><div class="nm">JAL Jubilee Express</div><div class="rt">HIJ<i>→</i>HND<span>JL258</span></div>
      <div class="tiles"><div><span>着く（推定）</span><b>15:24</b></div><div><span>時刻表</span><b>15:20</b></div><div><span>高さ</span><b>24,000<small>ft</small></b></div></div></div>
    <div class="sec"><b>今日の足あと</b><span>見えた記録から</span></div>
    {tl_rows().split('<li class="edge">')[0]}</ul>
    <div class="sec"><b>この先（予想）</b><span>保証しません</span></div>
    <ul class="tl">{"".join(f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span></div><div class="tag">{cf(lv)}</div></li>' for t, f, rt, lv in PRED)}</ul>
    <div class="row2"><button class="pillbtn line">機体の1日 ›</button><button class="pillbtn w">確からしさとは</button></div>
    </div>'''))

S["A5"] = ("案A 確からしさとは", "「確からしさとは」を押したときのシート。3段の決め方と、予定の便の意味",
  page("案A 確からしさとは", f'''<div class="pad">{top("機体の1日")}{plane_card(h=170)}</div><div class="dim"></div>
    <div class="sheet"><div class="grab"></div><h2>確からしさ</h2>
    <p>この機体が前の記録で、いまの便のあとに同じ便を飛んだ割合から3段に分けています。<b>どれも予想で、保証しません。</b></p>
    <ul class="lv3">
      <li>{cf("lv")}<div class="ex">航空会社の運航情報に「この塗装機で運航」とある便。機体の入れ替えで変わることがあります</div></li>
      <li>{cf(3)}<div class="ex"><b>8割以上</b>の日にこの便が続いた</div></li>
      <li>{cf(2)}<div class="ex"><b>6〜8割</b>の日にこの便が続いた</div></li>
      <li>{cf(1)}<div class="ex"><b>4〜6割</b>の日にこの便が続いた。4割より少ない便は出しません</div></li></ul>
    <div class="row2" style="justify-content:flex-end"><button class="pillbtn dark">閉じる</button></div></div>'''))

S["A6"] = ("案A 予想が出ないとき", "予想が出ないときも理由を1行で出す。いまの便が古いときは、どの便から出した予想かを書く",
  page("案A 予想が出ないとき", f'''<div class="pad" style="padding-top:20px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL599（JA339J）</small></div><div class="wh">羽田の近く・高度 2,400ft</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        {mini(1, base='<li class="now" style="opacity:.9"><div class="tm"><b style="color:var(--ink2)">19:36</b><small>見えた</small></div><div class="dot"><i style="background:#9CA3AF"></i></div><div class="tx"><b>JL148</b> 青森 → 羽田<small>この便のあとが分かっていません</small></div><div></div></li>')}
        <div class="warn"><span>!</span><span><b>いま飛んでいる JL599 が記録に入るまで</b>、JL148 からの予想を出しています。いまの便と同じ便は出しません</span></div></li>
      <li><div class="nm">★FDA シルバー（10号機）<small>FDA・FDA314（JA10FJ）</small></div><div class="wh">伊丹の近く・高度 17,600ft</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div class="warn"><span>…</span><span>この先の便は、<b>まだ記録が足りず予想できません</b>（毎日の記録が貯まると出ます）</span></div></li>
      <li><div class="nm">★さくらジンベエ<small>JTA（JA06RK）</small></div><div class="wh">今日はまだ見えていません</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div class="warn"><span>…</span><span><b>今日この機体はまだ見えていません</b>。見えたら、そのあとの便を予想します</span></div></li>
    </ul></div></div>{tabbar()}'''))

# ===== 案B：次の1便を大きく =====
S["B1"] = ("案B 機体の1日", "次の1便だけを大きく。そのあとは小さい一覧、飛んだ便はたたむ",
  page("案B 機体の1日", f'''<div class="pad">{top("機体の1日")}
    <div class="search"><input value="JA339J" aria-label="登録記号"><button class="btn1">探す</button></div>
    {plane_card(h=150)}
    <div class="next" style="margin-top:12px"><div class="lab"><b>次の便（予想）</b>{cf("lv")}</div>
      <div class="big"><b>16:15</b><em>ごろ</em></div>
      <div class="rt">羽田 → 青森<small>JL147</small></div>
      <div class="foot"><small>推定です。保証しません</small><button class="pillbtn" style="height:44px">確からしさとは</button></div></div>
    <div class="sec"><b>そのあと（予想）</b><span>3便</span></div>
    <ul class="after">{"".join(f'<li><span class="tm">{t}<em>ごろ</em></span><span class="tx"><b>{f}</b> {rt.replace(" → ","→")}</span>{cf(lv)}</li>' for t, f, rt, lv in PRED[1:] + TOMORROW)}</ul>
    <div class="sec"><b>今日飛んだ便</b><span>いま1便・飛んだ3便</span></div>
    <div class="flown"><span><b>JL258 広島→羽田（いま）</b><small>JL141・JL142・JL259</small></span>{DOWN}</div>
    {FOOT}</div>'''))

S["B2"] = ("案B 運用の特別塗装機", "一覧で開くと、次の1便だけを1行で大きく",
  page("案B 運用の特別塗装機", f'''<div class="pad" style="padding-top:20px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL258（JA339J）</small></div><div class="wh">広島から羽田へ・着く 15:24ごろ</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div style="margin-top:10px;background:var(--pred-wash);border-radius:18px;padding:12px 14px">
          <div style="display:flex;justify-content:space-between;align-items:center"><small style="font-size:13px;font-weight:800;color:var(--mute)">次の便（予想）</small>{cf("lv")}</div>
          <div style="display:flex;align-items:baseline;gap:8px;margin-top:4px"><b style="font-size:30px;font-weight:900;color:var(--pred)">16:15</b><small style="font-size:13px;color:var(--sub)">ごろ</small><span style="font-size:17px;font-weight:800;color:var(--pred)">羽田 → 青森</span></div>
          <div style="font-size:13px;color:var(--mute);margin-top:2px">JL147・推定です。保証しません</div></div>
        <div class="minifoot"><small>そのあと 3便</small><button class="pillbtn line">機体の1日 ›</button></div></li>
      <li><div class="nm">★結ジンベエ<small>JTA・JTA49（JA07RK）</small></div><div class="wh">飛行中・高度 32,000ft</div><button class="pillbtn">この先の便（予想）</button></li>
      <li><div class="nm">★FDA シルバー（10号機）<small>FDA・FDA314（JA10FJ）</small></div><div class="wh">伊丹の近く・高度 17,600ft</div><button class="pillbtn">この先の便（予想）</button></li>
    </ul></div></div>{tabbar()}'''))

# ===== 案C：1日の帯 =====
def band(w=326, sel=1, compact=False):
    t0, t1 = 6, 24
    X = lambda hh, mm: (hh + mm / 60 - t0) / (t1 - t0) * w
    def hm(s): h, m = s.split(":"); return int(h), int(m)
    blocks = []
    for t, e, f, rt in FLOWN:
        a, b = hm(t), hm(e[1:]); blocks.append(f'<span class="blk f" style="left:{X(*a):.1f}px;width:{X(*b)-X(*a):.1f}px"></span>')
    a = hm(NOW[0]); nx = X(14, 50); blocks.append(f'<span class="blk n" style="left:{X(*a):.1f}px;width:{X(15,24)-X(*a):.1f}px"></span>')
    durs = [(16, 15, 17, 28), (18, 35, 19, 36), (20, 30, 22, 5)]; alpha = {"lv":.95, 3:.85, 2:.55, 1:.3}
    for i, ((h1, m1, h2, m2), p) in enumerate(zip(durs, PRED)):
        blocks.append(f'<span class="blk p{" sel" if i == sel else ""}" style="--a:{alpha[p[3]]};left:{X(h1,m1):.1f}px;width:{X(h2,m2)-X(h1,m1):.1f}px"></span>')
    ticks = "".join(f'<span class="tk" style="left:{X(h,0):.1f}px">{h}</span>' for h in (6, 9, 12, 15, 18, 21, 24))
    return f'<div class="band" style="width:{w}px"><span class="ax"></span>{"".join(blocks)}<span class="nowl" style="left:{nx:.1f}px"><span>いま</span></span><span class="edgeL" style="left:{X(15,40):.1f}px">ここから予想</span>{ticks}</div>'
LEG = '<div class="bleg"><span><i style="background:#AEB6C0"></i>飛んだ</span><span><i style="background:#C2410C"></i>いま</span><span><i style="background:repeating-linear-gradient(135deg,#4B5563 0 4px,#C9CED6 4px 8px)"></i>予想（濃いほど確か）</span></div>'
S["C1"] = ("案C 機体の1日", "今日の6時〜24時を1本の帯に。飛んだ便は灰色、いまは橙、予想は斜線で、確かなほど濃い",
  page("案C 機体の1日", f'''<div class="pad">{top("機体の1日")}
    <div class="search"><input value="JA339J" aria-label="登録記号"><button class="btn1">探す</button></div>
    {plane_card(map_=False)}
    <div class="card"><div class="opsh"><b>今日の流れ</b><span>11月13日（金）</span></div>{band()}{LEG}
      <div class="selc"><span class="tm">18:35<em>ごろ</em></span>{cf(3)}<span class="tx"><b>JL148</b> 青森 → 羽田・予想（保証しません）</span></div></div>
    <div class="sec"><b>便の一覧</b><span>押すと帯の上で光る</span></div>
    <ul class="small-list">{"".join(f'<li><span><span class="t">{t}</span>{f} {rt.replace(" → ","→")}</span><small>飛んだ</small></li>' for t, e, f, rt in FLOWN)}
      <li style="color:var(--now)"><span><span class="t">{NOW[0]}</span>{NOW[2]} {NOW[3].replace(" → ","→")}</span><small style="color:var(--now);font-weight:800">飛行中</small></li>
      {"".join(f'<li class="p"><span><span class="t">{t}</span>{f} {rt.replace(" → ","→")}</span>{cf(lv)}</li>' for t, f, rt, lv in PRED)}</ul>
    <p class="note">明日の便（予想）は「明日」に出します。{FOOT[16:-4]}</p></div>'''))

S["C2"] = ("案C 運用の特別塗装機", "一覧で開くと、その機体の今日の帯だけ",
  page("案C 運用の特別塗装機", f'''<div class="pad" style="padding-top:20px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL258（JA339J）</small></div><div class="wh">広島から羽田へ・着く 15:24ごろ</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div style="margin-top:6px">{band(w=326, sel=0)}{LEG}</div>
        <div class="selc"><span class="tm">16:15<em>ごろ</em></span>{cf("lv")}<span class="tx"><b>JL147</b> 羽田 → 青森・予想（保証しません）</span></div>
        <div class="minifoot"><small>帯を押すと便が変わる</small><button class="pillbtn line">機体の1日 ›</button></div></li>
      <li><div class="nm">★結ジンベエ<small>JTA・JTA49（JA07RK）</small></div><div class="wh">飛行中・高度 32,000ft</div><button class="pillbtn">この先の便（予想）</button></li>
    </ul></div></div>{tabbar()}'''))

for k, (title, desc, h) in S.items():
    open(os.path.join(OUT, f"{k}.html"), "w", encoding="utf-8").write(h)

# ---- 一覧ページ ----
GROUPS = [("今の画面（本番で撮った・読みにくい所）", ["00a", "00b", "00c", "00d"]),
          ("案A 時間の線（おすすめ）", ["A1", "A2", "A3", "A4", "A5", "A6"]),
          ("案B 次の1便を大きく", ["B1", "B2"]), ("案C 1日の帯", ["C1", "C2"])]
cards = ""
for g, ks in GROUPS:
    cards += f'<h2 style="font-size:17px;font-weight:900;margin:26px 4px 10px">{g}</h2>'
    for k in ks:
        t, d, _ = S[k]
        cards += f'<a href="{k}.html" style="display:grid;grid-template-columns:96px 1fr;gap:12px;align-items:center;text-decoration:none;color:inherit;background:#fff;border-radius:20px;box-shadow:var(--sh);padding:10px;margin-bottom:10px"><img src="png/{k}.png" alt="" style="width:96px;border-radius:12px;display:block"><span><b style="display:block;font-size:15px">{k}　{html.escape(t)}</b><small style="font-size:13px;color:var(--mute);line-height:1.6">{html.escape(d)}</small></span></a>'
idx = page("運用予想を見やすく 1版", f'''<div class="pad" style="padding-bottom:40px"><h1 style="font-size:22px;font-weight:900;margin:12px 4px 4px">運用予想を見やすく</h1>
  <p style="font-size:14px;color:var(--mute);margin:0 4px">1版（11/13）。ブランチ design/rotation-view。アプリには入れていません。見本の機体は本番で見た JA339J の今日の便を、14時50分の場面にしたもの。</p>
  <div class="warn" style="margin-top:12px"><span>!</span><span>3つの案とも、<b>実績（飛んだ便）と予想を分ける・「予想」「保証しません」を必ず出す・確からしさは3段（濃さ＋言葉）</b>は同じ。違うのは並べ方。</span></div>{cards}</div>''')
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)
print("ok", len(S))
