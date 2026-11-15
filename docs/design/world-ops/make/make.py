# -*- coding: utf-8 -*-
# 海外の空港の止まり具合の札（design/world-ops）1版の画面案を作る。
# 1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。PNG は shoot.py で撮る。
# 色と字は main の src/index.html の運用タブ（案内板 .bdseq）と乗る便のカード（.ridecard）に合わせる。
# 中身の形はデータ担当の world_airport_ops（PR #93・report-world-ops.md の 1）に合わせる。
import os, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

CSS = r"""
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#24292F;--ink2:#374151;--mute:#6B7280;--sub:#8A919C;--pill:#EEF0F3;--hero:#0F1B2D;
  --blue:#2563EB;--intl:#1D4ED8;--intl-wash:#DBEAFE;--late:#B45309;
  --st1:#9A3412;--st2:#92400E;--st2-wash:#FEF3C7;--cnt:#374151;--cnt-wash:#EEF0F3;
  --sh:0 12px 26px -18px rgba(15,23,42,.30),inset 0 0 0 1px rgba(17,24,39,.06);
  --gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg)}
body{width:390px;min-height:844px;margin:0 auto;font:500 15px/1.5 var(--gothic);color:var(--ink);-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
.pad{padding:12px 16px 120px}
button{font:inherit;color:inherit}
/* 運用タブの上（今のアプリに合わせる） */
.brand{display:flex;justify-content:space-between;align-items:center;height:52px}
.brand b{font-size:20px;font-weight:800;letter-spacing:.06em}
.brand span{height:44px;display:inline-flex;align-items:center;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800}
.seg{display:flex;background:#E3E7EC;border-radius:999px;padding:4px;margin-top:8px}
.seg span{flex:1;height:40px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:15px;font-weight:800;color:var(--mute)}
.seg span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 8px -3px rgba(15,23,42,.3)}
.aprow{display:flex;align-items:center;gap:8px;margin-top:14px}
.ap{height:48px;display:inline-flex;align-items:center;gap:8px;padding:0 16px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:18px;font-weight:800}
.ap i{font-style:normal;font-size:13px;font-weight:800;color:#fff;background:#3B4350;border-radius:8px;padding:2px 7px}
.views{display:flex;gap:22px;margin:18px 4px 12px;font-size:15px;font-weight:800;color:var(--mute);white-space:nowrap;overflow:hidden}
.views span{padding-bottom:6px}
.views span.on{color:var(--ink);box-shadow:inset 0 -3px 0 var(--ink)}
.card{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:16px}
.card+.card{margin-top:12px}
/* 案内板（今の .bdhead・.bdtabs・.bdseq に合わせ、字は 13px 以上に） */
.bdhead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 0 10px}
.bdhead h3{margin:0;font-size:16px;font-weight:800}
.bdhead h3 small{font-size:13px;font-weight:600;color:var(--mute);margin-left:4px}
.bdtabs{display:inline-flex;gap:4px;background:var(--pill);padding:3px;border-radius:999px}
.bdtabs span{border-radius:999px;padding:0 14px;height:44px;display:inline-flex;align-items:center;font-size:14px;font-weight:700;color:var(--mute)}
.bdtabs span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 6px -2px rgba(15,23,42,.25)}
.bdkind{margin-bottom:6px}
.bdseq{list-style:none;margin:0 -16px 0 0;padding:16px 16px 0 0;display:grid;grid-auto-flow:column;grid-auto-columns:128px;gap:10px;overflow:hidden;position:relative}
.bdseq::before{content:"";position:absolute;left:0;right:0;top:6px;height:3px;border-radius:2px;background:linear-gradient(90deg,#BFDBFE,var(--blue))}
.bdseq li{position:relative;display:flex;flex-direction:column;gap:2px;font-size:13px;color:var(--mute);min-width:0}
.bdseq .dot{position:absolute;left:0;top:-14px;width:11px;height:11px;border-radius:50%;background:var(--card);border:2.5px solid var(--blue)}
.bdseq b{font-size:15px;font-weight:800;color:var(--ink);line-height:1.3}
.bdseq .fl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bdseq .fl i{font-style:normal;font-size:13px;font-weight:700;color:var(--intl);background:var(--intl-wash);border-radius:4px;padding:0 5px;margin-right:5px}
.bdseq .rel{font-size:17px;font-weight:800;color:var(--ink);margin-top:2px}
.bdseq .tm em{font-style:normal;color:var(--late);font-weight:700;margin-left:4px}
.bdseq li.past{opacity:.6}
/* 止まり具合の札（空港全体のようす。ピン形の印をつけて、この便のことと分ける） */
.st{display:inline-flex;align-items:center;gap:4px;max-width:100%;margin-top:6px;border-radius:999px;padding:3px 9px 3px 7px;font-size:13px;font-weight:800;line-height:1.35;white-space:nowrap;align-self:flex-start}
.st svg{flex:none;width:13px;height:13px;fill:currentColor}
.st small{font-size:13px;font-weight:700;opacity:.8;margin-left:2px}
.st.s1{background:var(--st1);color:#fff}
.st.s2{background:var(--st2-wash);color:var(--st2)}
.st.s3{background:var(--cnt-wash);color:var(--cnt)}
.stkey{display:flex;align-items:flex-start;gap:6px;font-size:13px;line-height:1.6;color:var(--mute);margin:12px 0 0}
.stkey svg{flex:none;width:13px;height:13px;fill:var(--mute);margin-top:4px}
/* 海外の空港のいま（案A） */
.wo{margin-top:18px;background:#F7F8FA;border-radius:18px;padding:12px 14px 12px}
.wo h4{margin:0 0 4px;font-size:15px;font-weight:800;display:flex;justify-content:space-between;align-items:baseline}
.wo h4 small{font-size:13px;font-weight:600;color:var(--mute)}
.wol{list-style:none;margin:0;padding:0}
.wol li{display:grid;grid-template-columns:1fr auto;align-items:center;gap:2px 8px;min-height:56px;padding:8px 0}
.wol li+li{box-shadow:0 -1px 0 #E6E9EE}
.wol .nm{font-size:16px;font-weight:800}
.wol .nm small{font-size:13px;font-weight:600;color:var(--sub);margin-left:4px}
.wol .wh{grid-column:1;font-size:14px;color:var(--ink2);display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.wol .wh .st{margin-top:0}
.wol .go{grid-row:1/3;grid-column:2;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.wol .go svg{width:18px;height:18px;stroke:var(--sub);fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.srcnote{font-size:13px;line-height:1.7;color:var(--mute);margin:8px 0 0}
.srcnote b{color:var(--ink2);font-weight:800}
.sec2{margin-top:18px}
.sec2 p{font-size:14px;color:var(--sub);margin:4px 0 0}
.fwnote{font-size:13px;line-height:1.7;color:var(--sub);margin:14px 0 0}
.fwnote mark{background:none;color:var(--ink2);font-weight:700}
/* 下のタブ帯 */
.tabbar{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;width:362px;height:68px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 14px 34px -16px rgba(15,23,42,.35),inset 0 0 0 1px rgba(17,24,39,.06);display:flex;justify-content:space-around;align-items:center;z-index:5}
.tabbar span{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:13px;font-weight:800;color:var(--mute);min-width:56px}
.tabbar span svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8}
.tabbar span.on{color:var(--blue)}
/* シート */
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:8}
.sheet{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;max-height:92vh;overflow:hidden;background:var(--card);border-radius:26px 26px 0 0;padding:10px 20px 28px;z-index:9;box-shadow:0 -18px 40px -20px rgba(15,23,42,.4)}
.sheet .grab{width:40px;height:5px;border-radius:9px;background:#D5DAE1;margin:0 auto 10px}
.shh{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.shh h2{font-size:20px;font-weight:900;margin:0}
.shh h2 small{font-size:14px;font-weight:700;color:var(--sub);margin-left:6px}
.shh button{flex:none;height:44px;padding:0 16px;border:0;border-radius:999px;background:var(--pill);font-weight:800;font-size:14px}
.big{margin-top:12px;border-radius:20px;padding:14px 16px}
.big.s1{background:#FFF1EA}
.big.s3{background:#F4F6F9}
.big .k{display:flex;align-items:center;gap:8px}
.big .k b{font-size:28px;font-weight:900;letter-spacing:.01em}
.big.s1 .k b{color:var(--st1)}
.big .k span{font-size:13px;font-weight:800;color:#fff;background:var(--st1);border-radius:999px;padding:2px 10px}
.big.s3 .k span{background:#4B5563}
.big .k b small{font-size:15px;font-weight:700;color:var(--sub);margin-left:2px}
.big .why{font-size:15px;color:var(--ink2);margin-top:2px}
.kv{list-style:none;margin:10px 0 0;padding:0}
.kv li{display:grid;grid-template-columns:104px 1fr;gap:8px;padding:9px 0;font-size:15px}
.kv li+li{box-shadow:0 -1px 0 #EEF0F3}
.kv li span{color:var(--mute);font-size:14px}
.kv li b{font-weight:800}
.kv li b small{display:block;font-size:13px;font-weight:600;color:var(--sub)}
.subh{font-size:15px;font-weight:800;margin:16px 0 4px}
.cnt3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:6px}
.cnt3 div{background:#F4F6F9;border-radius:14px;padding:10px 12px}
.cnt3 span{display:block;font-size:13px;color:var(--mute)}
.cnt3 b{font-size:24px;font-weight:900;font-variant-numeric:tabular-nums}
.cnt3 b small{font-size:13px;font-weight:700;color:var(--sub);margin-left:2px}
.cnt3 .hot b{color:var(--st1)}
.box{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.7;color:var(--ink2);background:#F4F6F9;border-radius:14px;padding:10px 12px;margin-top:14px}
.box svg{flex:none;width:16px;height:16px;stroke:var(--mute);fill:none;stroke-width:2;margin-top:3px}
/* ホーム（乗る便のカード）＝今の .ridecard に合わせ、字は 13px 以上に */
.mapbg{height:300px;background:linear-gradient(180deg,#E9EDF1,#E3E8EE);position:relative;overflow:hidden}
.mapbg svg{position:absolute;inset:0;width:100%;height:100%}
.topbar{position:absolute;left:16px;right:16px;top:12px;display:flex;justify-content:space-between;gap:8px;z-index:2}
.topbar .seg{margin:0;width:236px;background:rgba(255,255,255,.9);box-shadow:var(--sh)}
.topbar .seg span{height:40px;font-size:14px}
.topbar .seg span.on{background:#1F2937;color:#fff}
.topbar .me{height:48px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);display:flex;align-items:center;font-size:14px;font-weight:800}
.hsheet{position:relative;margin-top:-26px;background:#EEF1F5;border-radius:26px 26px 0 0;padding:10px 16px 120px;box-shadow:0 -10px 24px -18px rgba(15,23,42,.35)}
.hsheet .grab{width:40px;height:5px;border-radius:9px;background:#C9CFD7;margin:0 auto 12px}
.ride{padding:14px 16px;border-radius:18px;background:var(--card);box-shadow:var(--sh);font-size:14px;line-height:1.6}
.ride .rh{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
.ride .rh b{font-size:17px;font-weight:800}
.ride .rh span{flex:1;font-size:15px;color:var(--ink2)}
.ride .rh button{border:0;background:none;color:var(--mute);font-weight:700;font-size:14px;min-height:44px;padding:0 4px;text-decoration:underline}
.ride .rl{display:block;color:var(--mute);font-size:13px;margin-top:4px}
.ride .rv{display:block;font-weight:800;font-size:15px;margin-top:4px}
.ride .rv.ok{color:#1F7A3F}
.wline{display:flex;gap:8px;align-items:flex-start;margin-top:10px;border-radius:14px;padding:10px 12px;font-size:14px;line-height:1.55}
.wline svg{flex:none;width:16px;height:16px;fill:currentColor;margin-top:3px}
.wline.s1{background:#FFF1EA;color:var(--st1)}
.wline.s3{background:#F4F6F9;color:var(--ink2)}
.wline b{font-weight:800}
.wline small{display:block;font-size:13px;color:var(--mute);font-weight:500;margin-top:2px}
.rbar{height:6px;border-radius:9px;background:#E5E8EC;margin-top:8px;overflow:hidden}
.rbar i{display:block;height:100%;background:var(--blue);border-radius:9px}
.peek{margin-top:12px;height:86px;border-radius:18px;background:var(--card);box-shadow:var(--sh);padding:14px 16px;font-size:15px;font-weight:800;color:var(--ink2)}
/* 札の一覧 */
.cat{list-style:none;margin:0;padding:0}
.cat li{display:grid;grid-template-columns:150px 1fr;gap:10px;align-items:center;padding:12px 0}
.cat li+li{box-shadow:0 -1px 0 #EEF0F3}
.cat li p{margin:0;font-size:14px;line-height:1.55;color:var(--ink2)}
.cat li p small{display:block;font-size:13px;color:var(--mute)}
.lvh{font-size:14px;font-weight:800;color:var(--mute);margin:16px 0 0}
h1.t{font-size:20px;font-weight:900;margin:8px 0 4px}
p.lead{font-size:14px;color:var(--ink2);margin:0 0 12px;line-height:1.7}
/* 今の画面 */
.shot{position:relative;border-radius:22px;overflow:hidden;box-shadow:var(--sh);background:#fff}
.shot img{display:block;width:100%}
.mk{position:absolute;width:30px;height:30px;border-radius:50%;background:#C2410C;color:#fff;font-size:15px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #fff}
.nl{list-style:none;margin:12px 0 0;padding:0}
.nl li{display:grid;grid-template-columns:30px 1fr;gap:10px;padding:8px 0;font-size:14px;line-height:1.6;color:var(--ink2)}
.nl li i{font-style:normal;width:26px;height:26px;border-radius:50%;background:#C2410C;color:#fff;font-weight:900;font-size:14px;display:flex;align-items:center;justify-content:center}
"""

PIN = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1a5 5 0 0 0-5 5c0 3.6 5 9 5 9s5-5.4 5-9a5 5 0 0 0-5-5zm0 7a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/></svg>'
CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
INFO = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>'
NOTE = "出典：FAA NAS Status。運航の判断には使えません。遅れることがあります。便の数は JAL・ANA の運航情報（ODPT）から数えたものです"
ODPT = "出典：公共交通オープンデータセンター（正確・完全とは限りません。表示について航空会社へ直接問い合わせないでください。<u>くわしく</u>）"

def st(cls, text, src=""):
    return f'<span class="st {cls}">{PIN}{text}{f"<small>{src}</small>" if src else ""}</span>'

def tabbar(on):
    ic = {"ホーム":'<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>', "図鑑":'<path d="M4 5h7v15H4zM13 5h7v15h-7z"/>', "フライト":'<path d="M3 13l18-7-7 18-2-8z"/>',
          "運用":'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>', "修行":'<path d="M5 19h4v-5h4V9h4V5"/>'}
    return '<nav class="tabbar">' + "".join(f'<span class="{"on" if k == on else ""}"><svg viewBox="0 0 24 24">{v}</svg>{k}</span>' for k, v in ic.items()) + '</nav>'

def page(name, title, body, extra=""):
    h = f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=390,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>{body}{extra}</body></html>'
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(h)

def ops_top():
    return ('<div class="brand"><b>そらメモ</b><span>マイページ</span></div>'
            '<div class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></div>'
            '<div class="aprow"><span class="ap"><i>NRT</i>成田 ▾</span></div>'
            '<div class="views"><span class="on">案内板</span><span>1日の山</span><span>滑走路</span><span>定時</span><span>空の道すじ</span></div>')

# 場面：11月15日（日）14時10分（日本時間）・成田の出発・国際線
FLIGHTS = [
    ("ソウル（仁川）へ", "NH861・321", "あと15分", "定刻 14:25", st("s3", "今日 欠航3便")),
    ("ロサンゼルスへ", "JL62・789", "あと35分", "定刻 14:45", st("s1", "地上待機中", "FAA")),
    ("ホノルルへ", "NH184・789", "あと55分", "定刻 15:05", st("s2", "到着の遅れ", "FAA")),
    ("シンガポールへ", "JL711・789", "あと1時間15分", "定刻 15:25", ""),
]
def seq(pills=True):
    out = '<ol class="bdseq">'
    for nm, fl, rel, tm, p in FLIGHTS:
        out += f'<li><span class="dot"></span><b>{nm}</b><span class="fl"><i>国際</i>{fl}</span><span class="rel">{rel}</span><span class="tm">{tm}</span>{p if pills else ""}</li>'
    return out + '</ol>'

BOARD_HEAD = ('<div class="bdhead"><h3>これから出る便</h3><span class="bdtabs"><span>到着</span><span class="on">出発</span></span></div>'
              '<div class="bdtabs bdkind"><span>すべて</span><span>国内線</span><span class="on">国際線</span></div>')
KEY = f'<p class="stkey">{PIN}<span>ピンの札は、行き先の空港全体のようすです（この便のことではありません）。押すとくわしく出ます。</span></p>'
FOREIGN = '<div class="sec2"><div class="bdhead"><h3>海外の航空会社（いま近くにいる便）</h3></div><p>いま、この空港の近くに出た海外の航空会社の便は見つかりません。</p></div>'
DELAY = '<div class="sec2"><div class="bdhead"><h3>今日の遅れ・欠航</h3><span style="font-size:14px;color:var(--mute)">遅れ <b style="color:var(--ink);font-size:17px">4</b>便・欠航 <b style="color:var(--ink);font-size:17px">0</b>便</span></div></div>'

def wo_rows():
    rows = [
        ("ロサンゼルス", "LAX", st("s1", "地上待機中", "FAA"), "15時30分まで見込み"),
        ("ホノルル", "HNL", st("s2", "到着の遅れ 平均45分", "FAA"), ""),
        ("ソウル（仁川）", "ICN", st("s3", "今日の欠航 3便"), "遅れ 2便"),
    ]
    return "".join(f'<li><span class="nm">{n}<small>{c}</small></span><span class="wh">{p}{f"<span>{x}</span>" if x else ""}</span><span class="go">{CHEV}</span></li>' for n, c, p, x in rows)

def wo_box():
    return (f'<div class="wo"><h4>行き先の海外の空港のいま<small>14:06 更新</small></h4><ul class="wol">{wo_rows()}</ul>'
            f'<p class="srcnote"><b>運航の判断には使えません。</b>アメリカの空港は FAA（アメリカ連邦航空局）の発表、ほかの空港は JAL・ANA の今日の便の数です。<br>{NOTE}</p></div>')

def w1():
    body = (f'<div class="pad">{ops_top()}<div class="card">{BOARD_HEAD}{seq(True)}{KEY}{wo_box()}{FOREIGN}{DELAY}'
            f'<p class="fwnote">JAL・ANA の時刻表に載っている便だけです。{ODPT}</p></div></div>{tabbar("運用")}')
    page("W1", "W1 案A 運用タブの案内板（札＋行き先の海外の空港のいま）", body)

def w6():
    body = (f'<div class="pad">{ops_top()}<div class="card">{BOARD_HEAD}{seq(True)}{KEY}{FOREIGN}{DELAY}'
            f'<p class="fwnote">JAL・ANA の時刻表に載っている便だけです。<mark>ピンの札：アメリカの空港は FAA の発表、ほかの空港は JAL・ANA の今日の便の数。運航の判断には使えません。</mark>{NOTE}。{ODPT}</p></div></div>{tabbar("運用")}')
    page("W6", "W6 案B 運用タブの案内板（札だけ・断り書きは下に）", body)

def sheet_bg():
    return f'<div class="pad">{ops_top()}<div class="card">{BOARD_HEAD}{seq(True)}{KEY}</div></div>{tabbar("運用")}<div class="dim"></div>'

def w2():
    sh = (f'<div class="sheet"><div class="grab"></div><div class="shh"><h2>ロサンゼルス<small>LAX</small></h2><button>閉じる</button></div>'
          '<div class="big s1"><div class="k"><b>地上待機中</b><span>FAA の発表</span></div><div class="why">ロサンゼルスへ向かう便を、出発する空港で止めています</div></div>'
          '<ul class="kv"><li><span>わけ</span><b>天候（低い雲）<small>FAA の発表の言葉：WEATHER / LOW CEILINGS</small></b></li>'
          '<li><span>いつから</span><b>13:42 ごろから<small>現地 20:42（土）</small></b></li>'
          '<li><span>終わる見込み</span><b>15:30 まで見込み<small>現地 22:30（土）。延びることがあります</small></b></li>'
          '<li><span>発表の時刻</span><b>14:06<small>2分ごとに見ています</small></b></li></ul>'
          '<div class="subh">今日の JAL・ANA の便（ロサンゼルス発着）<small style="font-size:13px;font-weight:600;color:var(--sub);margin-left:6px">遅れは30分以上</small></div>'
          '<div class="cnt3"><div><span>便</span><b>8<small>便</small></b></div><div><span>欠航</span><b>0<small>便</small></b></div><div class="hot"><span>遅れ</span><b>2<small>便</small></b></div></div>'
          f'<div class="box">{INFO}<span><b>運航の判断には使えません。</b>FAA（アメリカ連邦航空局）が出している空港のようすを、そらメモが日本語にしたものです。あなたの便が遅れるかどうかは、航空会社の案内で確かめてください。<br>{NOTE}</span></div></div>')
    page("W2", "W2 くわしく（FAA の発表がある空港）", sheet_bg(), sh)

def w3():
    sh = (f'<div class="sheet"><div class="grab"></div><div class="shh"><h2>ソウル（仁川）<small>ICN</small></h2><button>閉じる</button></div>'
          '<div class="big s3"><div class="k"><b>欠航 3<small>便</small></b><span>JAL・ANA の便から</span></div><div class="why">今日の仁川発着の JAL・ANA の便 14便のうち</div></div>'
          '<div class="subh">今日の JAL・ANA の便<small style="font-size:13px;font-weight:600;color:var(--sub);margin-left:6px">遅れは30分以上</small></div><div class="cnt3"><div><span>便</span><b>14<small>便</small></b></div><div class="hot"><span>欠航</span><b>3<small>便</small></b></div><div><span>遅れ</span><b>2<small>便</small></b></div></div>'
          '<ul class="kv" style="margin-top:12px"><li><span>空港の発表</span><b>ありません<small>この地域は、いま空港のようすの公開の情報を使っていません</small></b></li>'
          '<li><span>数えた時刻</span><b>14:06</b></li></ul>'
          f'<div class="box">{INFO}<span><b>運航の判断には使えません。</b>そらメモが JAL・ANA の運航情報から数えた便の数で、空港の発表ではありません。ほかの航空会社の便は入っていません。共同運航は1便に数えています。<br>{NOTE}</span></div></div>')
    page("W3", "W3 くわしく（FAA がない空港・便の数だけ）", sheet_bg(), sh)

def home(card):
    mp = ('<svg viewBox="0 0 390 420" preserveAspectRatio="none"><path d="M0 300 C80 260 140 330 220 290 S340 250 390 270 L390 420 L0 420Z" fill="#DCE3EA"/>'
          '<path d="M60 380 L250 90" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/><path d="M130 400 L320 110" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/>'
          '<circle cx="190" cy="230" r="120" fill="none" stroke="#7B2D5B" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>'
          '<text x="208" y="214" font-size="15" font-weight="800" fill="#7B2D5B" font-family="sans-serif">NRT 成田</text></svg>')
    body = (f'<div class="mapbg">{mp}<div class="topbar"><div class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></div><span class="me">マイページ</span></div></div>'
            f'<div class="hsheet"><div class="grab"></div>{card}<div class="peek">近くの空港</div></div>{tabbar("ホーム")}')
    return body

def w4():
    card = ('<div class="ride"><div class="rh"><b>乗る便 JL62</b><span>成田 → ロサンゼルス</span><button>やめる</button></div>'
            '<span class="rl">出発 定刻 14:45　到着 定刻 07:50（現地）（日本時間 00:50）</span>'
            '<span class="rv">出発前（出発の見込み 14:45）</span>'
            f'<div class="wline s1">{PIN}<span><b>到着地ロサンゼルスで地上待機中</b>（FAA・15時30分まで見込み）<small>いまの発表です。着くころには変わっていることがあります</small></span></div>'
            '<span class="rl">機体 JA861J・789</span>'
            f'<p class="fwnote" style="margin-top:10px">到着地のようすは FAA（アメリカ連邦航空局）の発表で、運航の判断には使えません。遅れることがあります。機体の位置は adsb.lol から便名で探した推定です。時刻は時刻表（現地時刻）と航空会社の運航情報。{ODPT}</p></div>')
    page("W4", "W4 乗る便のカードに1行（FAA の発表がある空港）", home(card))

def w4b():
    card = ('<div class="ride"><div class="rh"><b>乗る便 NH861</b><span>成田 → ソウル（仁川）</span><button>やめる</button></div>'
            '<span class="rl">出発 定刻 14:25　到着 定刻 16:55（現地）</span>'
            '<span class="rv">出発前（出発の見込み 14:25）</span>'
            f'<div class="wline s3">{PIN}<span><b>到着地ソウル（仁川）：今日の欠航 3便</b>（JAL・ANA）<small>空港全体の数です。この便のことではありません</small></span></div>'
            '<span class="rl">機体 JA219A・321</span>'
            f'<p class="fwnote" style="margin-top:10px">到着地の便の数は、JAL・ANA の運航情報から数えたもので、空港の発表ではありません。運航の判断には使えません。{ODPT}</p></div>')
    page("W4b", "W4b 乗る便のカードに1行（便の数だけの空港）", home(card))

def w5():
    rows1 = [(st("s1", "閉鎖中", "FAA"), "空港が閉まっている", "FAA の closure"),
             (st("s1", "地上待機中", "FAA"), "その空港へ向かう便を、出発する空港で止めている", "FAA の ground_stop")]
    rows2 = [(st("s2", "到着の間引き中", "FAA"), "着く便を減らすため、出発を遅らせている", "FAA の gdp（データでは「出発の間引き」）"),
             (st("s2", "到着の遅れ", "FAA"), "着く便が 15分以上遅れている。くわしくに平均", "FAA の delay_arr"),
             (st("s2", "出発の遅れ", "FAA"), "出る便が 15分以上遅れている", "FAA の delay_dep"),
             (st("s2", "除氷中", "FAA"), "雪や氷を落とすため、出発に時間がかかる", "FAA の deicing")]
    rows3 = [(st("s3", "今日 欠航3便"), "JAL・ANA のその空港発着の便の欠航の数", "world_flight_counts の cancelled"),
             (st("s3", "今日 遅れ2便"), "30分以上の遅れの数（欠航がないときだけ札に出す）", "late30")]
    li = lambda rs: "".join(f'<li><span>{p}</span><p>{a}<small>{b}</small></p></li>' for p, a, b in rs)
    body = (f'<div class="pad"><h1 class="t">止まり具合の札の一覧</h1><p class="lead">札は3つの重さで分けます。1つの空港に2つ以上あるときは、いちばん重いものを1つだけ札にし、ほかはくわしくに出します（重い順：閉鎖 → 地上待機 → 間引き → 遅れ → 除氷 → 便の数）。どの札にもピンの印をつけ、空港全体のようすだと分かるようにします。</p>'
            f'<div class="card"><div class="lvh">重い（濃い色）</div><ul class="cat">{li(rows1)}</ul><div class="lvh">注意（うすい黄）</div><ul class="cat">{li(rows2)}</ul><div class="lvh">便の数（グレー・FAA の印なし）</div><ul class="cat">{li(rows3)}</ul></div>'
            '<p class="fwnote">出す決まり（データ担当の案に合わせる）：FAA の発表があるか、欠航・30分以上の遅れが1便以上の空港だけ。出る便は出発前、着く便は到着前の便だけに札をつける（過ぎた便にはつけない）。10分より古い発表は出さない（データ側で消える）。時刻は日本時間で出し、くわしくに現地の時刻を添える。夜の画面では、重いは琥珀の縁、注意は琥珀の字にする（金と会社の色は使わない）。</p></div>')
    page("W5", "W5 止まり具合の札の一覧", body)

def now_page(name, img, title, marks, notes):
    b64 = base64.b64encode(open(os.path.join(HERE, "now", img), "rb").read()).decode()
    mk = "".join(f'<span class="mk" style="left:{x}px;top:{y}px">{i+1}</span>' for i, (x, y) in enumerate(marks))
    nl = "".join(f'<li><i>{i+1}</i><span>{t}</span></li>' for i, t in enumerate(notes))
    body = f'<div class="pad"><h1 class="t">{title}</h1><p class="lead">本番（soramemo.jp）をデモで 11/15 10時ごろに撮影</p><div class="shot"><img src="data:image/jpeg;base64,{b64}" alt="">{mk}</div><ul class="nl">{nl}</ul></div>'
    page(name, title, body)

def index():
    items = [("00a", "今の運用タブの案内板（成田・出発・国際線）"), ("00b", "今の乗る便のカード（国際線）"),
             ("W1", "案A（おすすめ）案内板に札＋「行き先の海外の空港のいま」"), ("W6", "案B 案内板に札だけ（断り書きは下の出典に）"),
             ("W2", "くわしく：FAA の発表がある空港（ロサンゼルス）"), ("W3", "くわしく：便の数だけの空港（仁川）"),
             ("W4", "乗る便のカードに1行（FAA）"), ("W4b", "乗る便のカードに1行（便の数）"), ("W5", "札の一覧（重さ・言葉・出す決まり）")]
    li = "".join(f'<li style="padding:12px 0;box-shadow:0 -1px 0 #EEF0F3"><a href="{k}.html" style="color:var(--ink);font-weight:800;text-decoration:none;display:block;min-height:44px">{k}　{t}<br><small style="font-size:13px;font-weight:500;color:var(--mute)">png/{k}.png</small></a></li>' for k, t in items)
    body = (f'<div class="pad"><h1 class="t">海外の空港の止まり具合の札</h1><p class="lead">design/world-ops 1版（11/15）。場面は 11月15日（日）14時10分、成田の出発・国際線。中身の形はデータ担当の world_airport_ops（PR #93）。アプリには入れない画面案です。</p>'
            f'<div class="card"><ul style="list-style:none;margin:0;padding:0">{li}</ul></div></div>')
    page("index", "海外の空港の止まり具合の札 画面案", body)

if __name__ == "__main__":
    now_page("00a", "00a.jpg", "00a 今の案内板（成田・国際線）", [(318, 352), (300, 300)],
             ["国際線の便の列。行き先の空港のようすを出す所がない。札はここ（時刻の下）に足す",
              "「海外の航空会社」の欄の上に、行き先の海外の空港のようすをまとめる欄を足す（案A）"])
    now_page("00b", "00b.jpg", "00b 今の乗る便のカード（国際線）", [(300, 600)],
             ["状態の1行の下に、到着地のようすを1行足す。出典の文（fwnote）にも FAA を足す"])
    w1(); w6(); w2(); w3(); w4(); w4b(); w5(); index()
    print("ok")
