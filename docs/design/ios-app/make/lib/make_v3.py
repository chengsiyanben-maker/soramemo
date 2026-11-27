# -*- coding: utf-8 -*-
# ピン止め 3版（PM の指示 11/17 21時20分・改善担当 review-1 を受けて）。中心は空港のまま（K5 の形）。
# 必ず直す3つ：①通知を許可していない・iPhone でホーム画面に置いていないときの形（K0・K0i・K4d・K5n）
# ②ピン止め中かどうかを形と字の両方で（紺の塗り＋塗りのピン＋「ピン止め中」／白＋線のピン＋「ピン止め」）。
#   ピン止め中の札は押せない（外すのは「羽田の知らせ」の下のボタンか、行のピン＋元に戻す）。羽田・成田・石垣の3つをどの画面でもピン止め中にそろえる
# ③ホーム（K1）と運用タブ（K7・K8）を本番の今の形で（白い丸をやめ「ほか1つ」と引いての案内を残す／上は決まった1行）
# ほか：K9b 上限12を超える人・K10 乗る便と空港の遅れが重なるとき・機体ごとの知らせの残し方・K5 から空港を足す・元に戻す・撮影はピン止めの中で1つ
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
import make_v2 as V
from base_ops import I, CHEV, DOWN, LEFT, SRCH, PLANE, TOWER, INFO, SHARE, PEN, TABBAR
PIN, BELL, CLOUD = M.PIN, M.BELL, M.CLOUD
OUT = M.OUT
BELLX = '<path d="M6 16V11a6 6 0 0 1 9.5-4.9"/><path d="M18 11v5l1.5 2H8"/><path d="M10 20.5a2 2 0 0 0 4 0"/><path d="M4 4l16 16"/>'
CHECK = '<path d="m5 12.5 4.5 4.5L19 7.5"/>'
PLUS = '<path d="M12 5v14"/><path d="M5 12h14"/>'
SHAREI = '<path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/>'
UP = '<path d="m6 15 6-6 6 6"/>'

CSS = V.CSS + r"""
/* ピン止めの2つの形（3版で全画面そろえる） */
.pinbtn{background:var(--card);box-shadow:inset 0 0 0 1.5px #768090;color:var(--ink2)}
.card .pinbtn:not(.on){background:var(--card);box-shadow:inset 0 0 0 1.5px #768090}
.pinbtn.on,.card .pinbtn.on{background:var(--navy);color:#fff;box-shadow:none}
.pinpill:not(.on){background:var(--card);box-shadow:var(--sh),inset 0 0 0 1.5px #768090;color:var(--ink)}
.pinlab{flex:none;display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 12px 0 9px;border-radius:999px;background:var(--navy);color:#fff;font-size:13px;font-weight:800;white-space:nowrap}
.pinlab svg{width:15px;height:15px}
/* 本番のホーム（地図とシート） */
.hsheet3{position:fixed;width:390px;margin:0 auto;left:0;right:0;bottom:0;background:var(--bg);border-radius:26px 26px 0 0;padding:10px 16px 0;z-index:3;box-shadow:0 -12px 30px -20px rgba(15,23,42,.4)}
.hsheet3 .grab{width:40px;height:5px;border-radius:9px;background:#C9CFD8;margin:0 auto 12px}
.hsheet3.col{height:347px}
.hsheet3.exp{top:110px;overflow:hidden}
.hsheet3.exp .in{height:calc(100% - 27px);overflow:hidden;padding-bottom:110px}
.nc{display:flex;border-radius:22px;overflow:hidden;background:#111A2B;color:#fff;min-height:174px}
.nc .l{flex:1;padding:12px 12px 14px 16px;min-width:0}
.nc .t1{display:flex;align-items:center;gap:8px;min-height:30px}
.nc .t1 small{font-size:13px;color:#AEB8C6;flex:1}
.nc .dk{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 10px 0 8px;border-radius:999px;font-size:13px;font-weight:800;white-space:nowrap;background:rgba(255,255,255,.16);color:#fff}
.nc .dk svg{width:14px;height:14px}
.nc .dkbtn{display:inline-flex;align-items:center;min-height:44px;margin:-8px -4px -8px 0;padding:0 4px}
.nc .dkbtn .dk{background:transparent;box-shadow:inset 0 0 0 1.5px rgba(255,255,255,.55);color:#E7ECF3}
.nc .r2{display:flex;align-items:center;gap:8px;margin:6px 0 10px}
.nc .flap{display:flex;gap:5px;margin:0}
.nc .flap b{width:34px;height:40px;border-radius:7px;background:#1E2738;display:flex;align-items:center;justify-content:center;font:700 22px/1 ui-monospace,Menlo,monospace;color:#FFB547}
.nc .oth{margin-left:auto;height:44px;display:inline-flex;align-items:center;gap:2px;padding:0 10px 0 14px;border-radius:999px;background:rgba(255,255,255,.14);font-size:14px;font-weight:800;white-space:nowrap}
.nc .nm{font-size:17px;font-weight:800;line-height:1.35}
.nc .sub{font-size:13px;color:#C9D2DE;display:flex;align-items:center;gap:6px;margin-top:2px}
.nc .sub i{width:8px;height:8px;border-radius:50%;background:#5BD08A;display:inline-block}
.nc .ck{flex:none;width:98px;background:#E9C46A;color:#2B2410;display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:16px 6px 14px;box-shadow:inset 2px 0 0 0 rgba(43,36,16,.25)}
.nc .ck b{writing-mode:vertical-rl;font-size:17px;font-weight:900;letter-spacing:.18em}
.nc .ck span{font-size:13px;font-weight:800;line-height:1.35;text-align:center}
.stat{display:flex;align-items:center;gap:14px;background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:0 6px 0 14px;height:48px;margin-top:10px}
.stat span{font-size:13px;font-weight:800;color:var(--ink2);white-space:nowrap}
.stat b{font-size:21px;font-weight:900;margin-left:4px}
.stat small{font-size:13px;color:var(--sub);font-weight:700}
.stat .up{margin-left:auto;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--ink2)}
.mtop3{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;padding:14px 16px}
.mtop3 .seg{display:flex;background:#fff;border-radius:999px;padding:4px;box-shadow:var(--sh)}
.mtop3 .seg span{height:40px;display:inline-flex;align-items:center;white-space:nowrap;padding:0 12px;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.mtop3 .seg span.on{background:var(--navy);color:#fff}
.mtop3 .mp{height:44px;display:inline-flex;align-items:center;white-space:nowrap;padding:0 14px;border-radius:999px;background:#fff;box-shadow:var(--sh);font-size:14px;font-weight:800}
.map3{position:fixed;inset:0;width:390px;margin:0 auto;background:linear-gradient(160deg,#EEF0F2,#E5E8EC);overflow:hidden}
.map3::before{content:"";position:absolute;left:52px;top:180px;width:256px;height:256px;border-radius:50%;border:1.5px dashed #8A3B67;opacity:.75}
.map3 i{position:absolute;height:6px;border-radius:9px;background:#8A3B67;opacity:.85}
.map3 em{position:absolute;left:206px;top:262px;font-style:normal;font-size:13px;font-weight:800;color:#8A3B67;line-height:1.3}
.map3 u{position:absolute;left:126px;top:288px;width:22px;height:22px;border-radius:50%;background:#2563EB;box-shadow:0 0 0 8px rgba(37,99,235,.18)}
/* 端末の状態の1行 */
.dev{display:flex;align-items:center;gap:10px;background:#F6EEDF;border-radius:18px;padding:10px 8px 10px 12px;margin-top:10px}
.dev .ic2{flex:none;width:36px;height:36px;border-radius:50%;background:#fff;color:#8A5A12;display:flex;align-items:center;justify-content:center}
.dev .tx{flex:1;min-width:0}
.dev .tx b{display:block;font-size:14px;font-weight:800;color:var(--ink);line-height:1.4}
.dev .tx span{display:block;font-size:13px;color:var(--ink2);line-height:1.5}
.dev .go2{flex:none;height:44px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;background:var(--navy);color:#fff;font-size:14px;font-weight:800;white-space:nowrap}
.devok{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--ink2);margin:6px 0 0;min-height:28px}
.devok svg{width:16px;height:16px;color:var(--ok)}
.nd{flex:none;font-size:13px;font-weight:800;color:#8A5A12;white-space:nowrap}
.tg.on.dim2{background:#8C96A6}
/* 知らせの空港カード（ON だけを出す） */
.apc .chips2{gap:6px 6px;align-items:center;padding-bottom:2px}
.onc{display:inline-flex;align-items:center;gap:3px;font-size:13px;font-weight:800;color:var(--navy);background:#E9EDF4;border-radius:999px;padding:3px 10px 3px 7px}
.onc svg{width:14px;height:14px}
.offn{font-size:13px;color:var(--mute);margin-left:2px}
.addap{height:48px;display:flex;align-items:center;justify-content:center;gap:6px;border-radius:999px;background:var(--card);box-shadow:var(--sh),inset 0 0 0 1.5px #C9CFD8;font-size:15px;font-weight:800;color:var(--ink);margin-top:12px}
.addap svg{width:18px;height:18px}
/* 帯（ピン止めした・外した・元に戻す） */
.toast{position:fixed;left:50%;transform:translateX(-50%);bottom:94px;width:358px;min-height:56px;border-radius:18px;background:#1E2738;color:#fff;display:flex;align-items:center;gap:10px;padding:6px 6px 6px 14px;z-index:7;box-shadow:0 14px 30px -14px rgba(15,23,42,.6)}
.toast svg{width:18px;height:18px;flex:none}
.toast p{margin:0;flex:1;font-size:14px;font-weight:700;line-height:1.45}
.toast a{flex:none;height:44px;display:inline-flex;align-items:center;padding:0 12px;border-radius:999px;background:rgba(255,255,255,.14);color:#fff;font-size:14px;font-weight:800;text-decoration:none;white-space:nowrap}
/* 運用タブの上（本番の1行） */
.krow3{display:flex;align-items:center;gap:8px;margin-top:14px}
.ksw{display:inline-flex;background:var(--card);box-shadow:var(--sh);border-radius:999px;padding:4px}
.ksw span{height:40px;padding:0 12px;display:inline-flex;align-items:center;border-radius:999px;font-size:15px;font-weight:800;color:var(--mute)}
.ksw span.on{background:var(--navy);color:#fff}
.apsel{height:48px;display:inline-flex;align-items:center;gap:6px;padding:0 10px 0 6px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:17px;font-weight:900}
.apsel i{font:700 13px/1 ui-monospace,Menlo,monospace;font-style:normal;color:#fff;background:var(--ink);border-radius:6px;padding:5px 6px}
.apsel svg{width:18px;height:18px}
.krow3 .sp{flex:1}
.krow3 .ci{width:44px;height:44px;border-radius:50%;background:var(--card);box-shadow:var(--sh);display:flex;align-items:center;justify-content:center;color:var(--ink2)}
.vw3{position:relative;display:flex;align-items:center;gap:20px;margin:14px 0 12px;font-size:15px;font-weight:800;color:var(--mute);white-space:nowrap;overflow:hidden;padding-right:48px}
.vw3 span{padding:11px 0}
.vw3 span.on{color:var(--ink);box-shadow:inset 0 0 0 0 transparent,inset 0 -3px 0 var(--ink)}
.vw3 .pen{position:absolute;right:0;top:0;width:52px;height:44px;display:flex;align-items:center;justify-content:flex-end;color:var(--mute);background:linear-gradient(90deg,rgba(238,241,245,0),var(--bg) 40%)}
.vw3.lf{mask-image:linear-gradient(90deg,transparent,#000 9%)}
.tmc{flex:none;width:62px}
.tmc b{display:block;font-size:20px;font-weight:900;line-height:1.2}
.tmc small{display:block;font-size:13px;color:var(--sub);font-weight:700}
.pline{display:flex;align-items:center;gap:10px;min-height:56px;background:var(--pill);border-radius:16px;padding:4px 4px 4px 12px;margin-top:10px}
.pline .tx{flex:1;min-width:0}
.pline .tx b{display:block;font-size:15px;font-weight:800}
.pline .tx span{display:block;font-size:13px;color:var(--mute)}
.pline .go{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.hd2{margin-bottom:4px}
.hd2 b{display:block;font-size:16px;font-weight:800}
.hd2 small{display:block;font-size:13px;color:var(--mute)}
.selrow b::after{content:"選んでいる";margin-left:8px;font-size:13px;font-weight:700;color:var(--ok)}
.steps{margin:10px 0 0;padding:0;list-style:none;counter-reset:s}
.steps li{display:flex;gap:10px;align-items:center;min-height:52px;font-size:15px;font-weight:700;color:var(--ink2)}
.steps li::before{counter-increment:s;content:counter(s);flex:none;width:30px;height:30px;border-radius:50%;background:var(--pill);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:var(--ink)}
.steps li+li{box-shadow:0 -1px 0 var(--line)}
.steps svg{width:18px;height:18px;vertical-align:-3px}
.bigic{width:56px;height:56px;border-radius:50%;background:var(--pill);display:flex;align-items:center;justify-content:center;color:var(--navy);margin:8px 0 4px}
.bigic svg{width:26px;height:26px}
.codes{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.codes span{font:700 13px/1 ui-monospace,Menlo,monospace;color:var(--ink);background:var(--pill);border-radius:7px;padding:7px 8px}
.nlist .tx b{white-space:normal;line-height:1.35}
.over{font-size:34px;font-weight:900;line-height:1}
.over small{font-size:15px;color:var(--sub);font-weight:700;margin-left:4px}
"""

def page(name, title, body):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

# ---------- 部品 ----------
LAB = f'<span class="pinlab" aria-label="ピン止め中（押せない札）">{PIN(True)}ピン止め中</span>'
BTN = f'<span class="pinpill" role="button" aria-pressed="false">{PIN()}ピン止め</span>'
def rowpin(on):
    return (f'<span class="pinbtn on" role="button" aria-pressed="true" aria-label="ピン止め中・押すと外す（元に戻せる）">{PIN(True)}</span>' if on
            else f'<span class="pinbtn" role="button" aria-pressed="false" aria-label="ピン止めする">{PIN()}</span>')

def oo(items, nd=False):
    """items: (名前, 説明, on/off/na, [右の小さい入口])。nd=True は通知が届かない端末（ON に「届きません」）"""
    out = []
    for nm, sub, st, *more in items:
        cls = ' class="dis"' if st == "na" else ""
        if st == "on":
            tg = (f'<span class="nd">届きません</span><span class="tg on dim2">ON</span>' if nd else '<span class="tg on">ON</span>')
        else:
            tg = '<span class="tg off">OFF</span>'
        mo = f'<span class="more2">{more[0]} {I(CHEV)}</span>' if more else ""
        out.append(f'<li{cls}><div class="tx"><b>{nm}</b><span>{sub}</span>{mo}</div>{tg}</li>')
    return '<ul class="onoff">' + "".join(out) + "</ul>"

K_SP = "特別塗装機が向かってきたら"
K_LATE = "遅れ・門限・ダイバート"
K_GA = "ゴーアラウンド（推定）"
K_SPOT = "撮影の知らせ"
MAIN8 = "羽田・成田・関西・伊丹・中部・新千歳・福岡・那覇の8空港"

MAP = ('<div class="map3"><i style="left:20px;top:280px;width:150px;transform:rotate(-50deg)"></i><i style="left:62px;top:300px;width:160px;transform:rotate(56deg)"></i>'
       '<i style="left:160px;top:250px;width:200px;transform:rotate(62deg)"></i><i style="left:270px;top:440px;width:170px;transform:rotate(-40deg)"></i>'
       '<u></u><em>HND 羽田<br>判定範囲 2.0km</em></div>')
MTOP = '<div class="mtop3"><span class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></span><span class="mp">マイページ</span></div>'
STAT = f'<div class="stat"><span>今日の印<b>0</b></span><span>空港<b>16</b><small>/86</small></span><span>フライト<b>30</b></span><span class="up">{I(UP)}</span></div>'

def ncard(code, name, sub, pinned, oth="ほか1つ"):
    flap = "".join(f"<b>{c}</b>" for c in code)
    st = (f'<span class="dk" aria-label="ピン止め中（押せない札）">{PIN(True)}ピン止め中</span>' if pinned
          else f'<span class="dkbtn" role="button" aria-pressed="false"><span class="dk">{PIN()}ピン止め</span></span>')
    o = f'<span class="oth">{oth}{I(CHEV)}</span>' if oth else ""
    return f'''<div class="nc"><div class="l"><div class="t1"><small>いちばん近い</small>{st}</div><div class="r2"><div class="flap">{flap}</div>{o}</div>
<div class="nm">{name}</div><div class="sub">{sub}・<i></i>判定範囲の中</div></div><div class="ck"><b>チェックイン</b><span>→ 右へ引いて<br>印をもらう</span></div></div>'''

HND_CARD = ncard("HND", "東京国際空港（羽田）", "第1ターミナル", True)

def home(sheet_inner, extra="", exp=False):
    cls = "hsheet3 exp" if exp else "hsheet3 col"
    inner = f'<div class="in">{sheet_inner}</div>' if exp else sheet_inner
    return f'{MAP}{MTOP}<div class="{cls}"><div class="grab"></div>{inner}</div>{V.TAB_HOME}{extra}'

def krow(code="HND", name="羽田"):
    return f'''<div class="krow3"><span class="ksw" role="tablist"><span class="on">空港</span><span>機体</span></span><span class="apsel"><i>{code}</i>{name}{I(DOWN)}</span><span class="sp"></span>
<span class="ci">{I(INFO)}</span><span class="ci">{I(SHARE)}</span></div>'''
BRAND = f"""<div class="brand"><b>{I('<circle cx="12" cy="12" r="9"/><path d="m8 15 8-6-3 8-1-3Z"/>')}そらメモ</b><span>マイページ</span></div>
<div class="mode"><span class="on">スタンプラリー</span><span>エアライン経営</span></div>"""
VIEWS7 = f'<div class="vw3 lf"><span>滑走路</span><span>定時</span><span>空の道すじ</span><span class="on">撮る人</span><span class="pen">{I(PEN)}</span></div>'
TAB_OPS = TABBAR

def sprows():
    return f'''<ul class="rows">
<li><span class="tmc"><b>16:05</b><small>着（推定）</small></span><div class="tx"><b>ジンベエジェット</b><span><span class="reg">JA05RK</span>・JTA 9 那覇から</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmc"><b>16:40</b><small>着（推定）</small></span><div class="tx"><b>スターアライアンス塗装</b><span><span class="reg">B-58201</span>・BR 192 台北から</span></div><span class="go">{I(CHEV)}</span></li></ul>'''

def onchips(ons, noff):
    ch = "".join(f'<span class="onc">{I(CHECK)}{x}</span>' for x in ons)
    if noff: ch += f'<span class="offn">ほか{noff}つは OFF</span>'
    return ch

def apc(code, nm, ons, noff, note=""):
    n = f'<p class="note" style="margin:4px 0 0">{note}</p>' if note else ""
    return f'<div class="apc"><div class="top"><i>{code}</i><b>{nm}</b>{rowpin(True) if False else ""}<span class="go">{I(CHEV)}</span></div><div class="chips2">{onchips(ons, noff)}</div>{n}</div>'

DEV_DENIED = f'''<div class="dev"><span class="ic2">{I(BELLX)}</span><div class="tx"><b>この端末は通知が許可されていません</b><span>ON の知らせも、いまは届きません</span></div><span class="go2">許可する</span></div>'''
DEV_IOS = f'''<div class="dev"><span class="ic2">{I(BELLX)}</span><div class="tx"><b>iPhone はホーム画面に追加すると届きます</b><span>いまは Safari で開いているので、ON の知らせも届きません</span></div><span class="go2">やり方</span></div>'''
DEV_OK = f'<p class="devok">{I(CHECK)}この端末に届きます（通知を許可済み）</p>'

def build():
    # ---------- K0 はじめてのピン止めで、通知の許可を聞く前の1枚 ----------
    k0 = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="bigic">{I(BELL)}</div><div class="shh"><h2>知らせを届けるには、通知の許可が要ります</h2></div>
<p class="sub" style="line-height:1.7">このあと端末の確認が出ます。「許可」を押すと、ピン止めした空港の知らせがこの端末に届きます。</p>
<ul class="steps"><li>羽田をピン止めしました（もう済んでいます）</li><li>端末の確認で「許可」を押す</li><li>何を知らせるかを選ぶ（はじめは特別塗装機だけ）</li></ul>
<div style="display:flex;gap:8px;margin-top:14px"><span class="pillbtn" style="flex:1">許可しないで続ける</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">続ける</span></div>
<p class="note">許可しなくてもピン止めはできます（知らせだけ届きません）。あとから「知らせ」の画面の上で許可できます。この1枚は最初のピン止めのときだけ。</p></div>'''
    page("K0-v3", "K0 通知の許可を聞く前の1枚", k0)

    # ---------- K0i iPhone の Safari でホーム画面に置いていない ----------
    k0i = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="bigic">{I(BELLX)}</div><div class="shh"><h2>iPhone は、ホーム画面に追加すると知らせが届きます</h2></div>
<p class="sub" style="line-height:1.7">いまは Safari で開いているので、iPhone の決まりで知らせが届きません。ピン止めはこのまま使えます。</p>
<ul class="steps"><li>Safari の下の共有の印 {I(SHAREI)} を押す</li><li>「ホーム画面に追加」を押す</li><li>ホーム画面のそらメモから開き、通知を許可する</li></ul>
<div style="display:flex;gap:8px;margin-top:14px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">やり方を図で見る</span></div>
<p class="note">iPhone のアプリ（計画中）ができたら、この手順はいらなくなります。Android とパソコンは K0 の形。</p></div>'''
    page("K0i-v3", "K0i iPhone でホーム画面に置いていない", k0i)

    # ---------- K1 ホーム（本番の形・羽田はピン止め中）----------
    k1 = home(HND_CARD + STAT)
    page("K1-v3", "K1 ホーム（本番の形）ピン止め中", k1)

    # ---------- K1n ピン止めしていない空港にいるとき（伊丹）----------
    k1n = home(ncard("ITM", "大阪国際空港（伊丹）", "南ターミナル", False, oth="ほか2つ") + STAT)
    page("K1n-v3", "K1n ホーム ピン止めしていない空港", k1n)

    # ---------- K1o シートを引き上げたとき（ほかの空港の行にピン）----------
    k1o = home(HND_CARD + f'''<div class="card mt"><div class="hd2"><b>ほかに 20km 以内 1つ</b><small>近い順・ピンの印でピン止め</small></div><ul class="rows nlist">
<li><div class="tx"><b>東京ヘリポート</b><span>ヘリポート・江東区</span></div><span class="km">10.9<small>km</small></span>{rowpin(False)}</li></ul></div>
<div class="card mt"><div class="nrow"><span class="bi" style="background:var(--navy);color:#fff">{PIN(True)}</span><div class="tx"><b>ピン止めした空港 3</b><span>羽田・成田・石垣｜知らせの設定</span></div><span class="go">{I(CHEV)}</span></div></div>
{STAT}''', exp=True)
    page("K1o-v3", "K1o シートを引き上げたとき", k1o)

    # ---------- K2 空港ページ（羽田）----------
    k2 = f'''<div class="pad"><div class="zktop"><span class="back">{I(LEFT)}閉じる</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">HND</span><h2>東京国際空港（羽田）</h2><span class="s">東京都大田区・供用開始 1931年</span></div>{LAB}</div>
<div class="card mt"><div class="nrow"><span class="bi">{I(BELL)}</span><div class="tx"><b>羽田の知らせ</b><span>ピン止めの付け外しと、何を知らせるか</span></div><span class="go">{I(CHEV)}</span></div>
<div class="chips2" style="display:flex;flex-wrap:wrap;gap:6px;padding:0 0 4px 46px">{onchips(["特別塗装機", "遅れ・ダイバート", "撮影"], 1)}</div></div>
<div class="card mt"><div class="h"><b>いまの運用</b><small>実際の機体から判定</small></div><div style="font-size:28px;font-weight:900">北風運用</div><p class="note" style="margin-top:4px">着陸 34L・34R／離陸 05・34R</p></div>
<div class="card mt"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間</small></div>{sprows()}</div>
<p class="note">「ピン止め中」は押せない札。外すのは「羽田の知らせ」の下のボタンから（K6）。</p></div>{V.TAB_HOME}'''
    page("K2-v3", "K2 空港ページ ピン止め中", k2)

    # ---------- K3 図鑑の空港（成田＝ピン止め中）----------
    k3 = f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}関東</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">NRT</span><h2>成田国際空港</h2><span class="s">千葉県成田市</span></div>{LAB}</div>
<div class="kv"><div><small>はじめての印</small><b>2025<small>/3/8</small></b></div><div><small>印</small><b>7<small>回</small></b></div></div>
<p class="note">成田はどの画面でもピン止め中（ホーム・知らせ・空港を選ぶシートと同じ）。</p></div>{V.TAB_BOOK}'''
    page("K3-v3", "K3 図鑑の空港 ピン止め中", k3)

    # ---------- K3n 図鑑の空港（中部＝ピン止めしていない）----------
    k3n = f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}中部</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">NGO</span><h2>中部国際空港</h2><span class="s">愛知県常滑市</span></div>{BTN}</div>
<div class="kv"><div><small>はじめての印</small><b>2024<small>/11/2</small></b></div><div><small>印</small><b>2<small>回</small></b></div></div>
<p class="note">していないときは白地に線のピンと「ピン止め」（押せるボタン・影つき）。している時は紺の塗りに塗りのピンと「ピン止め中」（押せない札・影なし）。</p></div>{V.TAB_BOOK}'''
    page("K3n-v3", "K3n 図鑑の空港 ピン止めしていない", k3n)

    # ---------- K4 ピン止めした直後（最初の1回だけ・許可済み）----------
    K4ITEMS = [(K_SP, "国内・海外・アライアンス塗装。同じ機体は6時間に1回", "on"), (K_LATE, "0時前後に着く便・欠航・ダイバート・引き返し", "off"),
               (K_GA, "1機ごと・続いたとき・強い横風など", "off"), (K_SPOT, "ピン止めした空港のうち1つだけ ON にできます", "off")]
    k4 = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田をピン止めしました</h2><button>完了</button></div>
<p class="sub">羽田のことで、何を知らせますか。あとから「羽田の知らせ」で変えられます。</p>{DEV_OK}
{oo(K4ITEMS)}
<div style="display:flex;align-items:center;gap:8px;margin-top:6px"><p class="note" style="flex:1;margin:0"><b>推定です。保証しません。</b>このシートは最初の1回だけ。</p><span class="pillbtn">取り消す</span></div></div>'''
    page("K4-v3", "K4 ピン止めした直後（許可済み）", k4)

    # ---------- K4d 通知を許可していないとき ----------
    k4d = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田をピン止めしました</h2><button>完了</button></div>
{DEV_DENIED}
{oo(K4ITEMS, nd=True)}
<p class="note">許可するまで、ON の知らせにも「届きません」を付けます（スイッチは薄い紺）。「許可する」は、端末の確認が出せるときはその場で、断ったあとは設定のやり方を出します。</p></div>'''
    page("K4d-v3", "K4d 通知を許可していないとき", k4d)

    # ---------- K4t 2回目からは帯だけ（例：東京ヘリポートを付けたとき）----------
    k4t = home(HND_CARD + f'''<div class="card mt"><div class="hd2"><b>ほかに 20km 以内 1つ</b><small>近い順・ピンの印でピン止め</small></div><ul class="rows nlist">
<li><div class="tx"><b>東京ヘリポート</b><span>ヘリポート・江東区</span></div><span class="km">10.9<small>km</small></span>{rowpin(True)}</li></ul></div>{STAT}''', exp=True,
        extra=f'<div class="toast">{PIN(True)}<p>東京ヘリポートをピン止めしました</p><a>知らせの設定</a></div>')
    page("K4t-v3", "K4t 2回目からは帯だけ", k4t)

    # ---------- K4u 外したときは元に戻せる ----------
    k4u = home(HND_CARD + f'''<div class="card mt"><div class="hd2"><b>ほかに 20km 以内 1つ</b><small>近い順・ピンの印でピン止め</small></div><ul class="rows nlist">
<li><div class="tx"><b>東京ヘリポート</b><span>ヘリポート・江東区</span></div><span class="km">10.9<small>km</small></span>{rowpin(False)}</li></ul></div>{STAT}''', exp=True,
        extra=f'<div class="toast">{PIN()}<p>東京ヘリポートのピン止めを外しました。知らせも止めました</p><a>元に戻す</a></div>')
    page("K4u-v3", "K4u 外したときは元に戻せる", k4u)

    # ---------- K5 知らせ（1か所）----------
    def k5body(dev):
        return f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}マイページ</span><h2>知らせ</h2><span style="width:72px"></span></div>
{dev}
<div class="pinh" style="margin-top:14px"><span class="pi">{PIN(True)}</span><b>ピン止めした空港</b><span class="n">3 / 12</span><span class="sp"></span><span class="ed">並べ替え</span></div>
{apc("HND", "羽田", ["特別塗装機", "遅れ・ダイバート", "撮影"], 1)}
{apc("NRT", "成田", ["特別塗装機"], 3)}
{apc("ISG", "石垣", ["特別塗装機", "欠航・ダイバート"], 1)}
<div class="addap">{I(PLUS)}空港をピン止め</div>
<p class="note">ピン止めはアカウントに保存（ログインしない人はこの端末だけ）。知らせはこの端末に届きます。12空港に届いたら「＋」は押せなくなり「12空港まで」と出します。</p>
<p class="secth">便</p>
<div class="card" style="margin-top:8px"><div class="nrow"><span class="bi">{I(PLANE)}</span><div class="tx"><b>乗る便</b><span>JL 323（11/17）・15分の遅れから</span></div><span class="go">{I(CHEV)}</span></div></div>
<p class="secth">機体ごと</p>
<div class="card" style="margin-top:8px"><div class="nrow"><span class="bi">{I(BELL)}</span><div class="tx"><b>機体ごとの知らせ 2機</b><span>特別塗装機のくわしくで申し込んだ機体・今のまま</span></div><span class="go">{I(CHEV)}</span></div></div>
<p class="note">機体のピン止め（1版・2番目の案）を入れないと決めたときも、この行は残します（止め方が分かるように）。</p></div>'''
    page("K5-v3", "K5 知らせ（許可済み）", k5body(DEV_OK))
    page("K5n-v3", "K5n 知らせ（iPhone でホーム画面に置いていない）", k5body(DEV_IOS))

    # ---------- K6 羽田の知らせ ----------
    k6 = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}知らせ</span><h2>羽田の知らせ</h2><span style="width:72px"></span></div>
<div class="aph" style="margin-top:0;align-items:center"><div class="tx"><span class="code">HND</span><span class="s" style="display:inline;margin-left:8px;font-size:15px;font-weight:800;color:var(--ink)">東京国際空港</span></div>{LAB}</div>
{DEV_OK}
<div class="card mt">{oo([(K_SP, "国内・海外・アライアンス塗装（JAL・ANA のアライアンス塗装は知らせない）。同じ機体は6時間に1回", "on"),
    (K_LATE, "0時前後に着く便・欠航・ダイバート・引き返し。羽田は24時間なので門限の知らせはありません", "on"),
    (K_GA, "1機ごと・続いたとき・強い横風・低い雲・雷", "off", "細かく"),
    (K_SPOT, "撮影地から見える機体を来る前に。ピン止めした空港のうち1つだけ（いまは羽田）", "on", "撮影地と機体を選ぶ")])}</div>
<p class="note">どれも機体の位置（adsb.lol・ODbL）や運航情報（ODPT）からの<b>推定です。保証しません。</b>乗る便の遅れは、乗る便の知らせ1つにまとめます。</p>
<div class="danger">羽田のピン止めを外す</div>
<p class="note" style="text-align:center">外すと羽田の知らせはすべて止まります（すぐあとなら元に戻せます）。</p></div>'''
    page("K6-v3", "K6 羽田の知らせ", k6)

    # ---------- K6n 石垣の知らせ（出せない知らせは薄く・理由は空港名で）----------
    k6n = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}知らせ</span><h2>石垣の知らせ</h2><span style="width:72px"></span></div>
<div class="aph" style="margin-top:0;align-items:center"><div class="tx"><span class="code">ISG</span><span class="s" style="display:inline;margin-left:8px;font-size:15px;font-weight:800;color:var(--ink)">新石垣空港</span></div>{LAB}</div>
{DEV_OK}
<div class="card mt">{oo([(K_SP, "国内・海外・アライアンス塗装。同じ機体は6時間に1回", "on"),
    ("欠航・ダイバート・引き返し", f"門限ギリギリの知らせは{MAIN8}だけです", "on"),
    (K_GA, "羽田・成田・関西など14空港だけです", "na", "14空港の一覧"),
    (K_SPOT, "ON にすると、撮影の知らせを羽田から石垣に移します（1つの空港だけ）", "off")])}</div>
<p class="note">出せない知らせは薄くして残し、なぜ出せないかを空港名で書きます。</p>
<div class="danger">石垣のピン止めを外す</div></div>'''
    page("K6n-v3", "K6n 石垣の知らせ", k6n)

    # ---------- K7 運用タブ（本番の上の1行のまま。変えるのは特別塗装機の欄の下の1行だけ）----------
    k7 = f'''<div class="pad">{BRAND}{krow()}{VIEWS7}
<div class="card"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間・機体の位置からの推定</small></div>{sprows()}
<div class="pline"><span style="color:var(--navy)">{PIN(True)}</span><div class="tx"><b>羽田はピン止め中</b><span>特別塗装機の知らせ：ON</span></div><span class="go">{I(CHEV)}</span></div></div>
<p class="note">上の1行・見方の帯・右端の鉛筆は本番（PR #112）のまま。今の「羽田に特別塗装機が来たら通知する」のボタンを、この1行（状態と「羽田の知らせ」への入口）に替えるだけ。</p></div>{TAB_OPS}'''
    page("K7-v3", "K7 運用タブ 空港側", k7)

    # ---------- K7n ピン止めしていない空港（伊丹）----------
    k7n = f'''<div class="pad">{BRAND}{krow("ITM", "伊丹")}{VIEWS7}
<div class="card"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間・機体の位置からの推定</small></div><ul class="rows">
<li><span class="tmc"><b>17:20</b><small>着（推定）</small></span><div class="tx"><b>特別塗装機（見本）</b><span>登録記号・便名・出発地</span></div><span class="go">{I(CHEV)}</span></li></ul>
<div class="pline" style="background:var(--card);box-shadow:inset 0 0 0 1.5px #D5DAE1"><div class="tx"><b>伊丹をピン止めすると</b><span>特別塗装機が向かってきたら知らせます</span></div>{BTN}</div></div>
<p class="note">していない空港では白地の「ピン止め」ボタン。押すと K4（最初の1回）か K4t の帯。</p></div>{TAB_OPS}'''
    page("K7n-v3", "K7n 運用タブ ピン止めしていない空港", k7n)

    # ---------- K8 空港を選ぶシート（ピン止めが先頭・選んでいるとピン止めは別の印）----------
    k8 = f'''<div class="pad">{BRAND}{krow()}</div>{TAB_OPS}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>空港を選ぶ</h2></div>
<div class="pickrow"><span class="search">{I(SRCH)}空港の名前かコード</span></div>
<p class="grp">{PIN(True)} ピン止めした空港 3</p>
<ul class="rows"><li class="selrow"><div class="tx"><b>羽田</b><span>いまいる空港</span></div>{rowpin(True)}</li>
<li><div class="tx"><b>成田</b><span>60km</span></div>{rowpin(True)}</li>
<li><div class="tx"><b>石垣</b><span>1,950km</span></div>{rowpin(True)}</li></ul>
<p class="grp">近い順</p>
<ul class="rows"><li><div class="tx"><b>茨城</b><span>85km</span></div>{rowpin(False)}</li>
<li><div class="tx"><b>静岡</b><span>150km</span></div>{rowpin(False)}</li></ul>
<p class="note">行を押すと空港を選ぶ。右のピンで付け外し（外すと「元に戻す」の帯）。選んでいる空港は緑の字で、ピン止めの紺とは分ける。</p></div>'''
    page("K8-v3", "K8 空港を選ぶシート", k8)

    # ---------- K9 今の利用者への1回の案内 ----------
    k9 = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="mig mt"><span class="pi">{PIN(True)}</span><p><b>空港の知らせを、ピン止めにまとめました</b>申し込んでいた空港を、そのままピン止めしています。知らせの中身は変わりません。</p></div>
<div class="card mt" style="box-shadow:inset 0 0 0 1px var(--line);padding:8px 14px">
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>HND</i><b>羽田</b></div><div class="chips2">{onchips(["特別塗装機", "遅れ・ダイバート", "撮影"], 0)}</div></div>
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>NRT</i><b>成田</b></div><div class="chips2">{onchips(["特別塗装機"], 0)}</div></div>
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>ISG</i><b>石垣</b></div><div class="chips2">{onchips(["特別塗装機", "欠航・ダイバート"], 0)}</div></div></div>
<p class="note">ゴーアラウンドを申し込んでいた空港も同じように移します。<b>機体ごとの知らせ（2機）と乗る便の知らせは、そのまま続きます。</b></p>
<div style="display:flex;gap:8px;margin-top:12px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">知らせを見る</span></div>
<p class="note" style="text-align:center">この案内は1回だけ出ます。</p></div>'''
    page("K9-v3", "K9 今の利用者への案内", k9)

    # ---------- K9b 上限12を超える人 ----------
    codes = ["HND", "NRT", "ISG", "ITM", "KIX", "NGO", "CTS", "FUK", "OKA", "KOJ", "HIJ", "SDJ", "KMQ", "MYJ", "OIT"]
    k9b = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="mig mt"><span class="pi">{PIN(True)}</span><p><b>空港の知らせを、ピン止めにまとめました</b>申し込んでいた15空港を、すべてそのままピン止めしています。知らせも今までどおり届きます。</p></div>
<div class="card mt" style="box-shadow:inset 0 0 0 1px var(--line)"><div class="over">15<small>/ 12 空港</small></div>
<p class="note" style="margin-top:6px">上限（12）を超えていますが、まとめる前からの空港なのでそのまま続けます。<b>新しくピン止めするのは、11空港以下に減らしてから</b>です。</p>
<div class="codes">{"".join(f"<span>{c}</span>" for c in codes)}</div></div>
<div style="display:flex;gap:8px;margin-top:14px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">知らせを見る</span></div>
<p class="note" style="text-align:center">今は遅れ12・特別塗装機14空港まで申し込めるので、合わせると最大26。この案内は1回だけ。</p></div>'''
    page("K9b-v3", "K9b 上限12を超える人", k9b)

    # ---------- K10 知らせの見本（重なるときを足す）----------
    def nt(b, p, when="いま"):
        return f'<div class="nt1"><span class="ap"><i></i>そらメモ<em>{when}</em></span><b>{b}</b><p>{p}</p></div>'
    k10 = f'''<div class="lock"><div class="clk">23:25</div><div class="dt">11月17日 火曜日</div>
<p class="lab">ピン止めの空港に特別塗装機</p>
{nt("羽田にジンベエジェットが向かっています", "JTA 9 那覇から・JA05RK｜着くのは 16:05ごろ（推定）", "15:10")}
<p class="lab">乗る便と、ピン止めの空港の遅れが重なるとき</p>
{nt("JL 323（乗る便）は羽田に 0:10ごろ着く見込み", "45分遅れ・福岡 22:30 発｜羽田の遅れの知らせとまとめて1回です。運航情報（ODPT）")}
<div class="cmp"><b>重なるときの決まり</b><br>・乗る便が、ピン止めした空港の遅れ・門限の知らせにも当たるときは、<b>乗る便の知らせ1つ</b>にまとめる（11/13 の「1つの便の1日の遅れは1つの通知」）<br>・出発と到着の両方の空港をピン止めしていても、同じ便の遅れは1つ（あとから分かったことは同じ知らせを上書き）<br>・同じ機体が同じ空港に向かうのは1回、同じ機体は6時間に1回まで<br>・同じ機体の特別塗装機とゴーアラウンドは別のできごとなので別の知らせ。文の頭は空港名か便名にして、どれの知らせかすぐ分かるように</div></div>'''
    page("K10-v3", "K10 知らせの見本", k10)

    # ---------- 一覧 ----------
    L = [("3版：空港をピン止め（おすすめ・review-1 の直し）", [
            ("K0-v3", "通知の許可を聞く前の1枚", "最初のピン止めのときだけ"),
            ("K0i-v3", "iPhone でホーム画面に置いていない", "やり方の3つ"),
            ("K1-v3", "ホーム（本番の形）", "「ほか1つ」と引いての案内を残す・札「ピン止め中」"),
            ("K1n-v3", "ピン止めしていない空港にいるとき", "黒いカードの上の「ピン止め」"),
            ("K1o-v3", "シートを引き上げたとき", "ほかの空港の行にピン・ピン止めした空港 3"),
            ("K2-v3", "空港ページ（羽田）", "押せない札・ON の知らせだけ"),
            ("K3-v3", "図鑑の空港（成田）", "ピン止め中にそろえた"),
            ("K3n-v3", "図鑑の空港（中部）", "していないときの形"),
            ("K4-v3", "ピン止めした直後", "最初の1回だけ・取り消す"),
            ("K4d-v3", "通知を許可していないとき", "ON に「届きません」"),
            ("K4t-v3", "2回目からは帯だけ", "知らせの設定 ›"),
            ("K4u-v3", "外したとき", "元に戻す"),
            ("K5-v3", "知らせ（1か所）", "ON だけ出す・＋空港・機体ごと"),
            ("K5n-v3", "知らせ（iPhone で置いていない）", "上に端末の1行"),
            ("K6-v3", "羽田の知らせ", "羽田は門限なし・撮影は1つ"),
            ("K6n-v3", "石垣の知らせ", "理由は空港名で"),
            ("K7-v3", "運用タブ 空港側", "本番の1行のまま・1行だけ替える"),
            ("K7n-v3", "運用タブ ピン止めしていない空港", "ピン止めのボタン"),
            ("K8-v3", "空港を選ぶシート", "選んでいる（緑）とピン止め（紺）を分ける"),
            ("K9-v3", "今の利用者への案内", "機体ごと・乗る便はそのまま"),
            ("K9b-v3", "上限12を超える人", "そのまま続け、新しくは11以下から"),
            ("K10-v3", "知らせの見本", "乗る便と空港の遅れが重なるとき")]),
         ("2版（比べる用に残す）", [(n, t, "") for n, t in [("00-v2", "今の空港ごとの知らせ"), ("K1-v2", "ホーム"), ("K5-v2", "知らせ"), ("K5b-v2", "比べる用：表の形"), ("K7-v2", "運用タブ")]]),
         ("1版：機体をピン止め（2番目の案）", [(n, t, "") for n, t in [("P1", "機体側・ピン止めの段"), ("P2", "機体の1日"), ("P3", "特別塗装機の欄"), ("P6", "機体の知らせの設定"), ("P7", "機体の知らせの見本")]])]
    body = ('<div class="idx"><h1>ピン止め</h1><p>design/pin 3版（11/18）。中心は空港。ピン止めした空港に特別塗装機が向かってきたら知らせます。空港ごとの知らせの申し込みはピン止めの1か所（K5）にまとめます。画面案だけで、アプリには入れません。</p>'
            '<p><b>ピン止めの2つの形</b>：している＝紺の塗り＋塗りのピン＋「ピン止め中」（札・押せない）／していない＝白地＋線のピン＋「ピン止め」（ボタン）。行の丸も紺の塗りと白の線で分ける。羽田・成田・石垣はどの画面でもピン止め中。</p>')
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n.replace("-v3","").replace("-v2","")}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "ピン止め", body + "</div>")

if __name__ == "__main__":
    M.build(); V.build(); build(); print("ok")
