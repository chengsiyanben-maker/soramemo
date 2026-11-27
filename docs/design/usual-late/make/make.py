# -*- coding: utf-8 -*-
# 「いつもより○分遅い（推定）」の見せ方（design/usual-late）1版の画面案を作る。
# 1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。PNG は shoot.py で撮る。
# 色と字は main の src/index.html の乗る便のカード（.ridecard）・運用タブの案内板（.bdseq）・便のくわしく（.spsheet）に合わせる。
# 中身の形はデータ担当の foreign_late(便名, 日)・foreign_usual・foreign_watch（PR #104・report-foreign-collect.md）に合わせる。
import os, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

CSS = r"""
:root{--bg:#EEF1F5;--card:#FFFFFF;--ink:#24292F;--ink2:#374151;--mute:#6B7280;--sub:#8A919C;--pill:#EEF0F3;
  --blue:#2563EB;--intl:#1D4ED8;--intl-wash:#DBEAFE;--late:#B45309;--late-wash:#FEF3C7;--ok:#1F7A3F;
  --us:#92400E;--us-line:#C2853B;--us-gray:#4B5563;--us-gline:#A3AAB5;--hot:#9A3412;--hot-wash:#FFF1EA;
  --sh:0 12px 26px -18px rgba(15,23,42,.30),inset 0 0 0 1px rgba(17,24,39,.06);
  --gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg)}
body{width:390px;min-height:844px;margin:0 auto;font:500 15px/1.5 var(--gothic);color:var(--ink);-webkit-font-smoothing:antialiased;position:relative;overflow-x:hidden}
.pad{padding:12px 16px 120px}
button{font:inherit;color:inherit}
/* いつもとの比べの札（推定）：点線の縁＋波の印。JAL・ANA の「○分遅れ」（塗り・定刻つき）と形で分ける */
.us{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:3px 10px 3px 8px;font-size:13px;font-weight:800;line-height:1.35;white-space:nowrap;border:1.5px dashed var(--us-line);color:var(--us);background:#fff}
.us svg{flex:none;width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round}
.us small{font-size:13px;font-weight:700;opacity:.75}
.us.g{border-color:var(--us-gline);color:var(--us-gray)}
.us.big{font-size:15px;padding:5px 12px 5px 10px}
/* JAL・ANA の遅れ（今の形：定刻＋塗りの字） */
.jl{display:inline-flex;align-items:center;border-radius:6px;padding:1px 7px;font-size:13px;font-weight:800;background:var(--late-wash);color:var(--late)}
/* ホーム（乗る便のカード） */
.mapbg{height:300px;background:linear-gradient(180deg,#E9EDF1,#E3E8EE);position:relative;overflow:hidden}
.mapbg svg{position:absolute;inset:0;width:100%;height:100%}
.topbar{position:absolute;left:16px;right:16px;top:12px;display:flex;justify-content:space-between;gap:8px;z-index:2}
.seg{display:flex;background:#E3E7EC;border-radius:999px;padding:4px}
.seg span{flex:1;height:40px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:15px;font-weight:800;color:var(--mute)}
.topbar .seg{width:236px;background:rgba(255,255,255,.9);box-shadow:var(--sh)}
.topbar .seg span{font-size:14px}
.topbar .seg span.on{background:#1F2937;color:#fff}
.topbar .me{height:48px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);display:flex;align-items:center;font-size:14px;font-weight:800}
.hsheet{position:relative;margin-top:-26px;background:#EEF1F5;border-radius:26px 26px 0 0;padding:10px 16px 120px;box-shadow:0 -10px 24px -18px rgba(15,23,42,.35)}
.hsheet .grab{width:40px;height:5px;border-radius:9px;background:#C9CFD7;margin:0 auto 12px}
.ride{padding:14px 16px;border-radius:18px;background:var(--card);box-shadow:var(--sh);font-size:14px;line-height:1.6}
.ride .rh{display:flex;align-items:baseline;justify-content:space-between;gap:8px}
.ride .rh b{font-size:17px;font-weight:800}
.ride .rh span{flex:1;font-size:15px;color:var(--ink2)}
.ride .rh button{border:0;background:none;color:var(--mute);font-weight:700;font-size:14px;min-height:44px;padding:0 4px;text-decoration:underline}
.ride .rl{display:block;color:var(--mute);font-size:13px;margin-top:2px}
.ride .rv{display:block;font-weight:800;font-size:15px;margin-top:4px}
.ride .rv.ok{color:var(--ok)}
.ride .rv.hot{color:var(--hot)}
.tag{display:inline-flex;font-size:13px;font-weight:700;border-radius:6px;padding:0 6px;margin-left:6px;vertical-align:2px}
.tag.f{background:var(--intl-wash);color:var(--intl)}
.tag.n{background:#EEF0F3;color:var(--ink2)}
/* 到着の見込み（大きな数字＋札） */
.eta{margin-top:10px;background:#F7F8FA;border-radius:16px;padding:12px 14px}
.eta .k{font-size:13px;color:var(--mute);font-weight:700}
.eta .row{display:flex;align-items:center;flex-wrap:wrap;gap:6px 10px;margin-top:2px}
.eta .t{font-size:32px;font-weight:900;letter-spacing:.01em;font-variant-numeric:tabular-nums;line-height:1.15}
.eta .t small{font-size:15px;font-weight:700;color:var(--sub);margin-left:2px}
.eta .us-n{font-size:14px;color:var(--ink2);margin-top:4px}
.eta .us-n b{font-weight:800;font-variant-numeric:tabular-nums}
.eta .us-n small{color:var(--sub);font-size:13px;margin-left:4px}
.eta .two{display:grid;grid-template-columns:1fr 26px 1fr;align-items:end;margin-top:4px}
.eta .two div span{display:block;font-size:13px;color:var(--mute);font-weight:700}
.eta .two div b{font-size:28px;font-weight:900;font-variant-numeric:tabular-nums}
.eta .two div.u b{color:var(--sub);font-weight:800}
.eta .two i{font-style:normal;color:var(--sub);font-size:18px;text-align:center;padding-bottom:6px}
.eta .diff{font-size:14px;font-weight:800;color:var(--us);margin-top:2px}
.usnote{display:flex;gap:6px;align-items:flex-start;font-size:13px;line-height:1.6;color:var(--ink2);margin-top:8px}
.usnote svg{flex:none;width:14px;height:14px;stroke:var(--us-gray);fill:none;stroke-width:2;stroke-linecap:round;margin-top:3px}
.usnote b{font-weight:800}
.box{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.7;color:var(--ink2);background:#F4F6F9;border-radius:14px;padding:10px 12px;margin-top:10px}
.box svg{flex:none;width:16px;height:16px;stroke:var(--mute);fill:none;stroke-width:2;margin-top:3px}
.box.hot{background:var(--hot-wash);color:var(--hot)}
.box.hot svg{stroke:var(--hot)}
.box b{font-weight:800}
.box small{display:block;color:var(--mute);font-size:13px;font-weight:500}
.rbar{height:6px;border-radius:9px;background:#E5E8EC;margin-top:10px;overflow:hidden}
.rbar i{display:block;height:100%;background:var(--blue);border-radius:9px}
.fwnote{font-size:13px;line-height:1.7;color:var(--sub);margin:10px 0 0}
.fwnote mark{background:none;color:var(--ink2);font-weight:700}
.peek{margin-top:12px;height:86px;border-radius:18px;background:var(--card);box-shadow:var(--sh);padding:14px 16px;font-size:15px;font-weight:800;color:var(--ink2)}
/* 運用タブ（11/16 の決定：上は「空港｜機体」と空港のピルの1行） */
.brand{display:flex;justify-content:space-between;align-items:center;height:52px}
.brand b{font-size:20px;font-weight:800;letter-spacing:.06em}
.brand span{height:44px;display:inline-flex;align-items:center;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800}
.opsrow{display:flex;align-items:center;gap:8px;margin-top:10px}
.sw{display:inline-flex;background:#E3E7EC;border-radius:999px;padding:3px}
.sw span{height:44px;padding:0 14px;display:inline-flex;align-items:center;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.sw span.on{background:#1E3A5F;color:#fff}
.ap{height:48px;display:inline-flex;align-items:center;gap:8px;padding:0 14px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:17px;font-weight:800}
.ap i{font-style:normal;font-size:13px;font-weight:800;color:#fff;background:#3B4350;border-radius:8px;padding:2px 7px}
.views{display:flex;gap:22px;margin:16px 4px 12px;font-size:15px;font-weight:800;color:var(--mute);white-space:nowrap;overflow:hidden}
.views span{padding-bottom:6px}
.views span.on{color:var(--ink);box-shadow:inset 0 -3px 0 var(--ink)}
.card{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:16px}
.bdhead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:2px 0 10px}
.bdhead h3{margin:0;font-size:16px;font-weight:800}
.bdtabs{display:inline-flex;gap:4px;background:var(--pill);padding:3px;border-radius:999px}
.bdtabs span{border-radius:999px;padding:0 14px;height:44px;display:inline-flex;align-items:center;font-size:14px;font-weight:700;color:var(--mute)}
.bdtabs span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 6px -2px rgba(15,23,42,.25)}
.bdseq{list-style:none;margin:0 -16px 0 0;padding:16px 16px 0 0;display:grid;grid-auto-flow:column;grid-auto-columns:150px;gap:10px;overflow:hidden;position:relative}
.bdseq::before{content:"";position:absolute;left:0;right:0;top:6px;height:3px;border-radius:2px;background:linear-gradient(90deg,#BFDBFE,var(--blue))}
.bdseq.fg{grid-auto-columns:172px}
.bdseq.fg::before{background:repeating-linear-gradient(90deg,#9CA3AF 0 6px,transparent 6px 11px)}
.bdseq li{position:relative;display:flex;flex-direction:column;gap:2px;font-size:13px;color:var(--mute);min-width:0}
.bdseq .dot{position:absolute;left:0;top:-14px;width:11px;height:11px;border-radius:50%;background:var(--card);border:2.5px solid var(--blue)}
.bdseq.fg .dot{border-color:#9CA3AF;border-style:dashed}
.bdseq b{font-size:15px;font-weight:800;color:var(--ink);line-height:1.3}
.bdseq .fl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bdseq .fl i{font-style:normal;font-size:13px;font-weight:700;color:var(--intl);background:var(--intl-wash);border-radius:4px;padding:0 5px;margin-right:5px}
.bdseq .fl i.n{color:var(--ink2);background:#EEF0F3}
.bdseq .rel{font-size:16px;font-weight:800;color:var(--ink);margin-top:2px}
.bdseq .tm{font-variant-numeric:tabular-nums}
.bdseq .us{align-self:flex-start;margin-top:6px}
.key{display:flex;align-items:flex-start;gap:6px;font-size:13px;line-height:1.6;color:var(--mute);margin:14px 0 0}
.key .us{flex:none;padding:1px 7px 1px 6px}
.sec2{margin-top:22px}
/* 下のタブ帯 */
.tabbar{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;width:362px;height:68px;border-radius:999px;background:rgba(255,255,255,.96);box-shadow:0 14px 34px -16px rgba(15,23,42,.35),inset 0 0 0 1px rgba(17,24,39,.06);display:flex;justify-content:space-around;align-items:center;z-index:5}
.tabbar span{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:13px;font-weight:800;color:var(--mute);min-width:56px}
.tabbar span svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8}
.tabbar span.on{color:var(--blue)}
/* シート（便のくわしく＝今の .spsheet に合わせ、字は 13px 以上に） */
.dim{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:8}
.sheet{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;max-height:94vh;overflow:hidden;background:var(--card);border-radius:28px 28px 0 0;padding:10px 20px 28px;z-index:9;box-shadow:0 -18px 40px -20px rgba(15,23,42,.4)}
.sheet .grab{width:40px;height:5px;border-radius:9px;background:#D5DAE1;margin:0 auto 6px}
.shh{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.shh small{display:block;font-size:13px;color:var(--mute)}
.shh h2{font-size:24px;font-weight:900;margin:0}
.shh button{flex:none;width:44px;height:44px;border:0;border-radius:50%;background:var(--pill);font-weight:800;font-size:18px}
.spcard{display:block;margin-top:10px;background:#fff;box-shadow:inset 0 0 0 1px #E6E9EE;border-radius:18px;padding:12px 14px}
.spcard.soft{background:#F4F6F9;box-shadow:none}
.spcard>small{display:block;font-size:13px;color:var(--mute)}
.spcard>b{display:block;font-size:24px;font-weight:900;font-variant-numeric:tabular-nums}
.spcard>b small{font-size:14px;color:var(--sub);font-weight:700;margin-left:2px}
.spcard .lines{font-size:14px;color:var(--ink2);margin-top:4px}
.spgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.spgrid .spcard{margin-top:10px}
.kv{list-style:none;margin:6px 0 0;padding:0}
.kv li{display:grid;grid-template-columns:96px 1fr;gap:8px;padding:8px 0;font-size:14px}
.kv li+li{box-shadow:0 -1px 0 #EEF0F3}
.kv li span{color:var(--mute);font-size:13px}
.kv li b{font-weight:800}
.kv li b small{display:block;font-size:13px;font-weight:600;color:var(--sub)}
/* 一覧 */
h1.t{font-size:20px;font-weight:900;margin:8px 0 4px}
p.lead{font-size:14px;color:var(--ink2);margin:0 0 12px;line-height:1.7}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cmp .card{padding:14px}
.cmp h4{margin:0 0 6px;font-size:15px;font-weight:800}
.cmp p{margin:6px 0 0;font-size:13px;line-height:1.6;color:var(--ink2)}
.cmp .ex{font-size:14px;font-weight:700;margin-top:8px}
.cat{list-style:none;margin:0;padding:0}
.cat li{display:grid;grid-template-columns:158px 1fr;gap:10px;align-items:center;padding:12px 0}
.cat li+li{box-shadow:0 -1px 0 #EEF0F3}
.cat li p{margin:0;font-size:14px;line-height:1.55;color:var(--ink2)}
.cat li p small{display:block;font-size:13px;color:var(--mute)}
.lvh{font-size:14px;font-weight:800;color:var(--mute);margin:16px 0 0}
/* 今の画面 */
.shot{position:relative;border-radius:22px;overflow:hidden;box-shadow:var(--sh);background:#fff}
.shot img{display:block;width:100%}
.mk{position:absolute;width:30px;height:30px;border-radius:50%;background:#C2410C;color:#fff;font-size:15px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #fff}
.nl{list-style:none;margin:12px 0 0;padding:0}
.nl li{display:grid;grid-template-columns:30px 1fr;gap:10px;padding:8px 0;font-size:14px;line-height:1.6;color:var(--ink2)}
.nl li i{font-style:normal;width:26px;height:26px;border-radius:50%;background:#C2410C;color:#fff;font-weight:900;font-size:14px;display:flex;align-items:center;justify-content:center}
"""

WAVE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 9c1.6-2.6 3.2-2.6 4.8 0s3.2 2.6 4.8 0 2.6-2.6 3.4-1"/></svg>'
INFO = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>'
WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg>'
ADSB = "出典：adsb.lol（ODbL）の全機の記録"
NOTPUB = "定刻や航空会社の発表ではありません"
ODPT = "出典：公共交通オープンデータセンター（運航情報 19時48分・時刻表 11月16日時点。正確・完全とは限りません。表示について航空会社へ直接問い合わせないでください。<u>くわしく</u>）"

def us(text, g=False, big=False):
    return f'<span class="us{" g" if g else ""}{" big" if big else ""}">{WAVE}{text}</span>'

def tabbar(on):
    ic = {"ホーム":'<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>', "図鑑":'<path d="M4 5h7v15H4zM13 5h7v15h-7z"/>', "フライト":'<path d="M3 13l18-7-7 18-2-8z"/>',
          "運用":'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>', "修行":'<path d="M5 19h4v-5h4V9h4V5"/>'}
    return '<nav class="tabbar">' + "".join(f'<span class="{"on" if k == on else ""}"><svg viewBox="0 0 24 24">{v}</svg>{k}</span>' for k, v in ic.items()) + '</nav>'

def page(name, title, body, extra=""):
    h = f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=390,initial-scale=1"><title>{title}</title><style>{CSS}</style></head><body>{body}{extra}</body></html>'
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(h)

def home(card, label="HND 羽田"):
    mp = ('<svg viewBox="0 0 390 420" preserveAspectRatio="none"><path d="M0 300 C80 260 140 330 220 290 S340 250 390 270 L390 420 L0 420Z" fill="#DCE3EA"/>'
          '<path d="M60 380 L250 90" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/><path d="M150 360 L330 130" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/>'
          '<circle cx="190" cy="230" r="120" fill="none" stroke="#7B2D5B" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>'
          f'<text x="208" y="214" font-size="15" font-weight="800" fill="#7B2D5B" font-family="sans-serif">{label}</text></svg>')
    return (f'<div class="mapbg">{mp}<div class="topbar"><div class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></div><span class="me">マイページ</span></div></div>'
            f'<div class="hsheet"><div class="grab"></div>{card}<div class="peek">近くの空港</div></div>{tabbar("ホーム")}')

# 場面：11月16日（月）19時50分（日本時間）
def u1():
    card = ('<div class="ride"><div class="rh"><b>乗る便 BA5</b><span>ロンドン → 羽田</span><button>やめる</button></div>'
            '<span class="rl">ブリティッシュ・エアウェイズ<span class="tag f">時刻表にない便</span></span>'
            '<span class="rv ok">飛行中　高度 9,400ft・時速 520km</span>'
            '<div class="eta"><div class="k">羽田に着く見込み（推定）</div>'
            f'<div class="row"><span class="t">20:07<small>ごろ</small></span>{us("いつもより32分遅い", big=True)}</div>'
            '<div class="us-n">いつもは <b>19:35</b> ごろ<small>月曜日・前の8週の7回から</small></div></div>'
            '<div class="rbar" role="img" aria-label="飛んだ道のり 97%"><i style="width:97%"></i></div>'
            '<span class="rl" style="margin-top:8px">機体 G-STBK・77W</span>'
            f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>この便は時刻表がないので、そらメモが集めた記録の「いつもの時刻」と比べています。{ADSB}。</span></p>'
            '<p class="fwnote">機体の位置は adsb.lol から便名で探した推定で、海の上などでは届かないことがあります。出発の前の遅れと欠航は分かりません。空港の時間帯：OpenFlights（ODbL）</p></div>')
    page("U1", "U1 案A 乗る便のカード（時刻表にない便・飛行中）", home(card))

def u1x():
    card = ('<div class="ride"><div class="rh"><b>乗る便 BA5</b><span>ロンドン → 羽田</span><button>やめる</button></div>'
            '<span class="rl">ブリティッシュ・エアウェイズ<span class="tag f">時刻表にない便</span></span>'
            '<span class="rv ok">飛行中　高度 9,400ft・時速 520km</span>'
            '<div class="eta"><div class="k">羽田に着く時刻（推定）</div>'
            '<div class="two"><div class="u"><span>いつも</span><b>19:35</b></div><i>→</i><div><span>いまの見込み</span><b>20:07</b></div></div>'
            '<div class="diff">32分遅い（月曜日・前の8週の7回から）</div></div>'
            '<div class="rbar"><i style="width:97%"></i></div>'
            '<span class="rl" style="margin-top:8px">機体 G-STBK・77W</span>'
            f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>{ADSB}。</span></p>'
            '<p class="fwnote">機体の位置は adsb.lol から便名で探した推定です。出発の前の遅れと欠航は分かりません。</p></div>')
    page("U1x", "U1x 案B（比べる用）2つの時刻を並べる", home(card))

def u2():
    card = ('<div class="ride"><div class="rh"><b>乗る便 BC13</b><span>羽田 → 福岡</span><button>やめる</button></div>'
            '<span class="rl">スカイマーク<span class="tag n">時刻表にない便</span></span>'
            '<span class="rv">出発前</span>'
            '<div class="eta"><div class="k">いつもの時刻（推定）</div>'
            '<div class="two"><div><span>羽田を出る</span><b>19:05</b></div><i>→</i><div><span>福岡に着く</span><b>21:05</b></div></div>'
            '<div class="us-n"><small style="margin:0">ごろ。月曜日・前の8週の8回から</small></div></div>'
            f'<div class="box">{INFO}<span><b>出発の前の遅れと欠航は分かりません。</b>飛び立つと、いつもとのずれを出します。遅れ・欠航はスカイマークの案内で確かめてください。</span></div>'
            f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>{ADSB}から作った「いつもの時刻」です。</span></p></div>')
    page("U2", "U2 乗る便のカード（ODPT にない日本の会社・出発前）", home(card))

def u2b():
    card = ('<div class="ride"><div class="rh"><b>乗る便 BC13</b><span>羽田 → 福岡</span><button>やめる</button></div>'
            '<span class="rl">スカイマーク<span class="tag n">時刻表にない便</span></span>'
            '<span class="rv ok">飛行中　高度 35,000ft・時速 860km</span>'
            '<div class="eta"><div class="k">福岡に着く見込み（推定）</div>'
            f'<div class="row"><span class="t">21:52<small>ごろ</small></span>{us("いつもより47分遅い", big=True)}</div>'
            '<div class="us-n">いつもは <b>21:05</b> ごろ<small>月曜日・前の8週の8回から</small></div></div>'
            f'<div class="box hot">{WARN}<span><b>福岡空港の門限（22時）に近い見込みです（推定）</b><small>門限の10分前より遅く着く見込み。ダイバート（ほかの空港へ）になることがあります</small></span></div>'
            '<div class="rbar"><i style="width:62%"></i></div>'
            '<span class="rl" style="margin-top:8px">機体 JA73NY・738</span>'
            f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>{ADSB}。</span></p></div>')
    page("U2b", "U2b 乗る便のカード（飛行中・門限に近い見込み）", home(card, "HND 羽田"))

def u2c():
    card = ('<div class="ride"><div class="rh"><b>乗る便 BA5</b><span>ロンドン → 羽田</span><button>やめる</button></div>'
            '<span class="rl">ブリティッシュ・エアウェイズ<span class="tag f">時刻表にない便</span></span>'
            '<span class="rv hot">いつもと違う空港に着いたようです</span>'
            '<div class="eta"><div class="k">着いた空港（推定）</div>'
            '<div class="row"><span class="t" style="font-size:28px">成田</span><span class="us g">' + WAVE + 'いつもは 羽田</span></div>'
            '<div class="us-n">20:41 ごろ着陸<small>機体の位置から</small></div></div>'
            f'<div class="box">{INFO}<span><b>ダイバート（ほかの空港へ）の推定です。</b>この便の前の8週は 8回すべて羽田に着いていました。くわしくはブリティッシュ・エアウェイズの案内で確かめてください。</span></div>'
            f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>{ADSB}。</span></p></div>')
    page("U2c", "U2c 乗る便のカード（ダイバートの推定）", home(card, "NRT 成田"))

def ops_top():
    return ('<div class="brand"><b>そらメモ</b><span>マイページ</span></div>'
            '<div class="opsrow"><span class="sw"><span class="on">空港</span><span>機体</span></span><span class="ap"><i>HND</i>羽田 ▾</span></div>'
            '<div class="views"><span class="on">案内板</span><span>1日の山</span><span>滑走路</span><span>定時</span><span>空の道すじ</span></div>')

def u3():
    jl = [("札幌（新千歳）から", "JL526・767", "あと4分", f'定刻 19:50 <span class="jl">18分遅れ</span>'),
          ("福岡から", "NH264・789", "あと9分", "定刻 19:55"),
          ("那覇から", "JL920・738", "あと20分", f'定刻 20:05 <span class="jl">15分遅れ</span>')]
    seq = '<ol class="bdseq">' + "".join(f'<li><span class="dot"></span><b>{a}</b><span class="fl">{b}</span><span class="rel">{c}</span><span class="tm">{d}</span></li>' for a, b, c, d in jl) + '</ol>'
    fg = [("ロンドンから", '<i>海外</i>BA5・77W', "着陸に向かっています", "推定 20:07ごろ", us("いつもより32分遅い")),
          ("神戸から", '<i class="n">日本</i>BC106・738・スカイマーク', "着陸に向かっています", "推定 19:58ごろ", us("いつもどおり", g=True)),
          ("ドーハから", '<i>海外</i>QR812・77W', "着陸に向かっています", "推定 20:16ごろ", '<span style="font-size:13px;color:var(--sub);margin-top:6px">いつもの時刻はまだありません</span>')]
    seq2 = '<ol class="bdseq fg">' + "".join(f'<li><span class="dot"></span><b>{a}</b><span class="fl">{b}</span><span class="rel" style="font-size:14px">{c}</span><span class="tm">{d}</span>{e}</li>' for a, b, c, d, e in fg) + '</ol>'
    body = (f'<div class="pad">{ops_top()}<div class="card">'
            '<div class="bdhead"><h3>これから着く便</h3><span class="bdtabs"><span class="on">到着</span><span>出発</span></span></div>'
            f'{seq}<p class="fwnote">JAL・ANA の時刻表と運航情報。{ODPT}</p>'
            '<div class="sec2"><div class="bdhead"><h3>時刻表にない便（いま近くにいる便）</h3></div>'
            f'{seq2}<p class="key">{us("札", g=True)}<span>点線の札は、そらメモの記録の<b style="color:var(--ink2)">いつもの時刻</b>との比べ（推定）です。定刻ではありません。</span></p>'
            f'<p class="fwnote">海外の航空会社と、JAL・ANA の時刻表にない日本の航空会社の便を、空港から60km以内の機体の位置（adsb.lol）から推定しています。いつもの時刻は前の8週の記録の真ん中の値です。{NOTPUB}。{ADSB}</p></div>'
            f'</div></div>{tabbar("運用")}')
    page("U3", "U3 運用タブの案内板（JAL・ANA と時刻表にない便）", body)

def u4():
    bg = f'<div class="pad">{ops_top()}<div class="card"><div class="bdhead"><h3>これから着く便</h3></div></div></div>{tabbar("運用")}<div class="dim"></div>'
    sh = ('<div class="sheet"><div class="grab"></div><div class="shh"><div><small>ロンドンから・羽田に着陸</small><h2>BA5</h2></div><button aria-label="閉じる">×</button></div>'
          '<div class="spcard soft"><small>機体</small><b style="font-size:20px">G-STBK・77W</b><small>ブリティッシュ・エアウェイズの便。機種は機体の位置のデータから</small></div>'
          '<div class="spgrid"><div class="spcard"><small>着陸</small><b>20:07<small>ごろ</small></b>'
          f'<div style="margin-top:6px">{us("32分遅い")}</div><div class="lines">いつもは 19:35 ごろ</div></div>'
          '<div class="spcard"><small>滑走路</small><b>C</b><div class="lines">いまの運用からの推定</div></div></div>'
          '<div class="spcard"><small>いつもの時刻（推定）</small>'
          '<ul class="kv"><li><span>いつも</span><b>19:35 ごろ<small>月曜日の、前の8週の着陸の真ん中の値</small></b></li>'
          '<li><span>数えた回数</span><b>7回<small>曜日ごとは3回以上、曜日を問わないときは5回以上で出します</small></b></li>'
          '<li><span>ばらつき</span><b>19:28〜19:44<small>7回のうち、真ん中の半分が入る幅</small></b></li></ul></div>'
          f'<p class="usnote">{INFO}<span><b>推定です。{NOTPUB}。</b>時刻表がない便なので、そらメモが集めた着陸の記録と比べています。受信機の届かない低い所では、時刻が数分ずれることがあります。{ADSB}。</span></p></div>')
    page("U4", "U4 便のくわしく（時刻表にない便）", bg, sh)

def u5():
    cmp = ('<div class="cmp">'
           '<div class="card"><h4>JAL・ANA の便</h4><div class="ex">定刻 19:50 <span class="jl">18分遅れ</span></div>'
           '<p>塗りの字。「定刻」の時刻とくらべる。出典は ODPT（運航情報・時刻表の時点つき）</p></div>'
           f'<div class="card"><h4>時刻表にない便</h4><div class="ex">20:07ごろ</div><div style="margin-top:4px">{us("いつもより32分遅い")}</div>'
           '<p>点線の縁と波の印。「定刻」とは書かず「いつも」。時刻に「ごろ」。出典は adsb.lol（ODbL）</p></div></div>')
    rows = [(us("いつもより32分遅い"), "いつもより15分以上遅い見込み・遅かった", "foreign_late の late_min ≧ 15"),
            (us("いつもどおり", g=True), "前後14分以内", "−14 〜 +14"),
            (us("いつもより18分早い", g=True), "15分以上早い（早いのは色をつけない）", "late_min ≦ −15"),
            ('<span style="font-size:13px;color:var(--sub)">いつもの時刻はまだありません</span>', "記録が少ない・ばらつきが大きい便（札は出さない）", "foreign_usual に行がない（曜日ごと3回未満・曜日なし5回未満・幅60分超）")]
    li = "".join(f'<li><span>{p}</span><p>{a}<small>{b}</small></p></li>' for p, a, b in rows)
    rows2 = [('<span class="us" style="border-color:var(--hot);color:var(--hot)">' + WAVE + '門限に近い見込み</span>', "見込みの到着が門限の10分前より遅い（主要空港・福岡など）", "foreign_watch。通知と同じ決まり"),
             (us("いつもは 羽田", g=True), "いつもと違う空港に着いた（ダイバート）・出た空港に戻った（引き返し）", "foreign_legs の判定")]
    li2 = "".join(f'<li><span>{p}</span><p>{a}<small>{b}</small></p></li>' for p, a, b in rows2)
    body = (f'<div class="pad"><h1 class="t">見分け方と札の一覧</h1><p class="lead">時刻表にない便（海外の航空会社と、ODPT にない日本の航空会社）は、定刻の代わりに「いつもの時刻」と比べます。JAL・ANA の定刻つきの遅れと取り違えないよう、形・言葉・出典を分けます。</p>'
            f'{cmp}<div class="card" style="margin-top:12px"><div class="lvh" style="margin-top:0">いつもとの比べ</div><ul class="cat">{li}</ul><div class="lvh">見張り（乗る便に選んだときだけ）</div><ul class="cat">{li2}</ul></div>'
            '<p class="fwnote">出す決まり：出発の前の遅れと欠航は出さない（分からない）。飛んでいる間は着く見込みといつもの到着、着いたあとは着陸の時刻といつもの到着を比べる。時刻はいつも「ごろ」をつけ、札の言葉に「定刻」「遅延」は使わない。断り書き「推定です。定刻や航空会社の発表ではありません」は、札のあるカードの中に太字で1回。出典「adsb.lol（ODbL）」はその文の後ろ。ODPT の出典は時刻表にない便には出さない（今の乗る便のカードは出している）。夜の画面では点線の縁を琥珀にし、会社の色と金は使わない。</p></div>')
    page("U5", "U5 見分け方と札の一覧", body)

def now_page(name, img, title, marks, notes):
    b64 = base64.b64encode(open(os.path.join(HERE, "now", img), "rb").read()).decode()
    mk = "".join(f'<span class="mk" style="left:{x}px;top:{y}px">{i+1}</span>' for i, (x, y) in enumerate(marks))
    nl = "".join(f'<li><i>{i+1}</i><span>{t}</span></li>' for i, t in enumerate(notes))
    body = f'<div class="pad"><h1 class="t">{title}</h1><p class="lead">本番（soramemo.jp）をデモで 11/16 の夜に撮影</p><div class="shot"><img src="data:image/jpeg;base64,{b64}" alt="">{mk}</div><ul class="nl">{nl}</ul></div>'
    page(name, title, body)

ITEMS = [("00a", "今の案内板の「海外の航空会社（いま近くにいる便）」"), ("00b", "今の乗る便のカード（時刻表にない便）"),
         ("U1", "案A（おすすめ）乗る便：見込み＋点線の札「いつもより32分遅い」"), ("U1x", "案B（比べる用）乗る便：いつも → 見込み を並べる"),
         ("U2", "乗る便：ODPT にない日本の会社・出発前（いつもの時刻だけ）"), ("U2b", "乗る便：飛行中・門限に近い見込み"), ("U2c", "乗る便：ダイバートの推定"),
         ("U3", "運用タブの案内板：JAL・ANA の定刻つきと、時刻表にない便の札"), ("U4", "便のくわしく：いつもの時刻・回数・ばらつき"), ("U5", "見分け方と札の一覧")]

def index():
    li = "".join(f'<li style="padding:12px 0;box-shadow:0 -1px 0 #EEF0F3"><a href="{k}.html" style="color:var(--ink);font-weight:800;text-decoration:none;display:block;min-height:44px">{k}　{t}<br><small style="font-size:13px;font-weight:500;color:var(--mute)">png/{k}.png</small></a></li>' for k, t in ITEMS)
    body = (f'<div class="pad"><h1 class="t">「いつもより○分遅い（推定）」の見せ方</h1><p class="lead">design/usual-late 1版（11/16）。場面は 11月16日（月）19時50分。中身の形はデータ担当の foreign_late・foreign_usual・foreign_watch（PR #104）。アプリには入れない画面案です。</p>'
            f'<div class="card"><ul style="list-style:none;margin:0;padding:0">{li}</ul></div></div>')
    page("index", "いつもより遅いの見せ方 画面案", body)

if __name__ == "__main__":
    now_page("00a", "00a.jpg", "00a 今の案内板（海外の航空会社）", [(330, 210), (330, 290)],
             ["「海外の航空会社（いま近くにいる便）」。時刻は「推定」と高度だけで、いつもより遅いかは出ていない。ここに点線の札を足す（U3）",
              "出典の文。ODPT にない日本の会社（スカイマークなど）も入るなら、題と文を「時刻表にない便」に直す"])
    now_page("00b", "00b.jpg", "00b 今の乗る便のカード（時刻表にない便 BA5）", [(330, 610), (330, 690)],
             ["状態の1行だけ。飛んでいる間は、ここに着く見込みと「いつもより○分遅い（推定）」を出す（U1）",
              "時刻表にない便でも ODPT の出典が出ている。adsb.lol（ODbL）の出典と「定刻や航空会社の発表ではありません」に入れ替える"])
    u1(); u1x(); u2(); u2b(); u2c(); u3(); u4(); u5(); index()
    print("ok")
