# -*- coding: utf-8 -*-
# 機体のピン止め 2版：ピン止めの中心を「空港」にする（PM の追記 11/17 16時25分）。
# 空港をピン止め → その空港に特別塗装機が向かってきたら知らせる。今は4か所に分かれている空港ごとの知らせ
# （遅れ・ダイバート＝pushAps／特別塗装機＝sp_airports／ゴーアラウンド＝ga／撮影＝spot）の申し込みを、ピン止めの1か所にまとめる。
# 機体のピン止め（1版の P*.html）は2番目の案として残す。部品は make.py（1版）と base_ops.py から読み込む。
# 見本の時刻は 11/17 15:10（羽田・北風運用・昼）。PNG は shoot_v2.py。
import os, sys, base64, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
from base_ops import I, CHEV, DOWN, LEFT, SRCH, PLANE, TOWER, INFO, SHARE, TABBAR, TOP, kindrow, views
PIN, BELL, PHONE, CLOUD = M.PIN, M.BELL, M.PHONE, M.CLOUD
HERE = M.HERE; OUT = M.OUT

CSS = M.CSS + r"""
/* ホーム：地図とシート（本番の形に合わせる） */
.map{position:absolute;inset:0 0 auto 0;height:420px;background:linear-gradient(160deg,#EDEFF2,#E3E7EC);overflow:hidden}
.map::before{content:"";position:absolute;left:120px;top:110px;width:200px;height:200px;border-radius:50%;border:2px dashed #8A3B67;opacity:.7}
.map i{position:absolute;height:8px;border-radius:9px;background:#8A3B67;opacity:.85}
.mtop{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;padding:12px 16px}
.mtop .seg{display:flex;background:#fff;border-radius:999px;padding:4px;box-shadow:var(--sh)}
.mtop .seg span{height:40px;display:inline-flex;align-items:center;white-space:nowrap;padding:0 10px;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.mtop .seg span.on{background:var(--navy);color:#fff}
.mtop .mp{height:44px;display:inline-flex;align-items:center;white-space:nowrap;padding:0 12px;border-radius:999px;background:#fff;box-shadow:var(--sh);font-size:14px;font-weight:800}
.hsheet{position:absolute;left:0;right:0;top:300px;background:var(--bg);border-radius:26px 26px 0 0;padding:10px 16px 120px;z-index:3;box-shadow:0 -12px 30px -20px rgba(15,23,42,.4)}
.hsheet .grab{width:40px;height:5px;border-radius:9px;background:#C9CFD8;margin:0 auto 10px}
.near1{display:flex;border-radius:22px;overflow:hidden;background:#111A2B;color:#fff}
.near1 .l{flex:1;padding:14px 14px 16px 16px;min-width:0}
.near1 .l small{font-size:13px;color:#AEB8C6}
.flap{display:flex;gap:6px;margin:6px 0 8px}
.flap b{width:38px;height:44px;border-radius:8px;background:#1E2738;display:flex;align-items:center;justify-content:center;font:700 24px/1 ui-monospace,Menlo,monospace;color:#FFB547}
.near1 .nm{display:flex;align-items:center;gap:8px}
.near1 .nm b{font-size:17px;font-weight:800;flex:1;min-width:0}
.near1 .nm .pinbtn{background:rgba(255,255,255,.12);color:#fff;box-shadow:none}
.near1 .nm .pinbtn.on{background:#fff;color:#111A2B}
.near1 .sub{font-size:13px;color:#C9D2DE}
.near1 .ck{flex:none;width:92px;background:#E9C46A;color:#2B2410;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:14px;font-weight:900;writing-mode:vertical-rl;letter-spacing:.2em}
.nlist .tg2{flex:none;font-size:13px;font-weight:800;border-radius:999px;padding:3px 10px;background:#F3EBDD;color:#7A5A22}
.nlist .tg2.ap{background:#E8EEF7;color:#1F3A66}
.nlist .km{flex:none;font-size:18px;font-weight:900}
.nlist .km small{font-size:13px;color:var(--sub);font-weight:700;margin-left:2px}
/* 空港ページ */
.aph{display:flex;align-items:flex-start;gap:10px;margin-top:8px}
.aph .tx{flex:1;min-width:0}
.aph .code{display:inline-block;font:700 14px/1 ui-monospace,Menlo,monospace;color:#fff;background:var(--ink);border-radius:7px;padding:6px 8px}
.aph h2{margin:8px 0 0;font-size:21px;font-weight:900;line-height:1.3}
.aph span.s{display:block;font-size:13px;color:var(--mute);margin-top:2px}
.nrow{display:flex;align-items:center;gap:10px;min-height:56px}
.nrow .bi{flex:none;width:36px;height:36px;border-radius:50%;background:var(--pill);display:inline-flex;align-items:center;justify-content:center;color:var(--ink2)}
.nrow .tx{flex:1;min-width:0}
.nrow .tx b{display:block;font-size:15px;font-weight:800}
.nrow .tx span{display:block;font-size:13px;color:var(--mute)}
.on1{display:inline-flex;align-items:center;gap:4px;font-size:13px;font-weight:800;color:var(--ink2);background:var(--pill);border-radius:999px;padding:2px 9px;margin:2px 4px 0 0}
.nrow .tx .on1,.apc .on1{display:inline-flex}
.on1.x{color:var(--sub);background:transparent;box-shadow:inset 0 0 0 1.5px #D5DAE1}
/* 知らせの設定の空港カード */
.apc{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:12px 12px 12px 16px;margin-top:12px}
.apc .top{display:flex;align-items:center;gap:10px;min-height:48px}
.apc .top i{font:700 13px/1 ui-monospace,Menlo,monospace;font-style:normal;color:#fff;background:var(--ink);border-radius:6px;padding:5px 6px}
.apc .top b{flex:1;font-size:17px;font-weight:800}
.apc .top .go{width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.apc .chips2{display:flex;flex-wrap:wrap;margin-top:2px}
.onoff li.dis .tx b{color:var(--sub)}
.onoff li.dis .tg{opacity:.45}
.more2{font-size:13px;font-weight:800;color:var(--ink2);display:inline-flex;align-items:center;min-height:44px}
.danger{height:48px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:15px;font-weight:800;color:var(--ink2);margin-top:16px}
.pinpill:not(.on){background:var(--card);box-shadow:var(--sh)}
.secth{font-size:13px;font-weight:800;color:var(--mute);margin:22px 4px 0;letter-spacing:.04em}
.mig{display:flex;gap:12px;align-items:flex-start}
.mig .pi{flex:none;width:44px;height:44px;border-radius:50%;background:var(--navy);color:#fff;display:inline-flex;align-items:center;justify-content:center}
.mig p{margin:0;font-size:14px;line-height:1.7;color:var(--ink2)}
.mig p b{display:block;font-size:17px;color:var(--ink);margin-bottom:4px}
.mt16{margin-top:16px}
.grid4{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
.grid4 th{font-weight:800;color:var(--mute);text-align:center;padding:4px 2px 8px}
.grid4 th:first-child{text-align:left}
.grid4 td{text-align:center;padding:6px 2px;height:56px}
.grid4 td:first-child{text-align:left;font-size:15px;font-weight:800}
.grid4 tr+tr td{box-shadow:0 -1px 0 var(--line)}
.dot2{display:inline-flex;width:44px;height:44px;border-radius:50%;align-items:center;justify-content:center;background:var(--pill);color:var(--sub);font-size:13px;font-weight:800}
.dot2.on{background:var(--navy);color:#fff}
.dot2.na{background:transparent;color:#B7BEC8}
"""

def page(name, title, body):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

def oo(items):
    out = []
    for nm, sub, st, *more in items:
        cls = ' class="dis"' if st == "na" else ""
        tg = '<span class="tg on">ON</span>' if st == "on" else '<span class="tg off">OFF</span>'
        mo = f'<span class="more2">{more[0]} {I(CHEV)}</span>' if more else ""
        out.append(f'<li{cls}><div class="tx"><b>{nm}</b><span>{sub}</span>{mo}</div>{tg}</li>')
    return '<ul class="onoff">' + "".join(out) + "</ul>"

TAB_HOME = TABBAR.replace('<span class="on">', '<span>').replace('<span>' + I('<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>', ''), '<span class="on">' + I('<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>', ''))
TAB_BOOK = TABBAR.replace('<span class="on">', '<span>').replace('<span>' + I('<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>', ''), '<span class="on">' + I('<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>', ''))

MAP = '<div class="map"><i style="left:60px;top:150px;width:240px;transform:rotate(-50deg)"></i><i style="left:150px;top:200px;width:200px;transform:rotate(55deg)"></i><i style="left:220px;top:170px;width:220px;transform:rotate(60deg)"></i></div>'
MTOP = '<div class="mtop"><span class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></span><span class="mp">マイページ</span></div>'

# 空港の知らせの4つ（今ある申し込みをそのまま並べる）
K_SP = "特別塗装機が向かってきたら"
K_LATE = "遅れ・門限ギリギリ・ダイバート"
K_GA = "ゴーアラウンド（推定）"
K_SPOT = "撮影の知らせ"

def build():
    # ---------- 00-v2 今の空港ごとの知らせ（散らばり）----------
    from PIL import Image
    imgs = []
    for f, cap in [("00d.jpg", "ホーム（近くの空港）"), ("00c.jpg", "運用タブ（空港）")]:
        im = Image.open(os.path.join(HERE, "now", f)).convert("RGB"); w = 300; im = im.resize((w, int(im.size[1] * w / im.size[0]))).crop((0, 0, w, 520))
        bio = io.BytesIO(); im.save(bio, "JPEG", quality=62)
        imgs.append(f'<figure><img src="data:image/jpeg;base64,{base64.b64encode(bio.getvalue()).decode()}" alt=""><figcaption>{cap}</figcaption></figure>')
    rows = [("遅れ・ダイバート（門限）", "運用タブ 空港側の下", "12空港まで"),
            ("特別塗装機が来たら", "運用タブ 特別塗装機の欄", "14空港まで"),
            ("ゴーアラウンド（推定）", "運用タブ ゴーアラウンドの設定", "主な14空港"),
            ("撮影の知らせ", "撮る人の設定", "いつもの空港 1つ"),
            ("この機体が飛んだら", "特別塗装機のくわしく", "機体ごと")]
    tbl = '<ul class="sort"><li class="hd" style="grid-template-columns:1.2fr 1.2fr .8fr"><div>知らせ</div><span>申し込む所（今）</span><span>数</span></li>' + "".join(
        f'<li style="grid-template-columns:1.2fr 1.2fr .8fr"><div>{a}</div><span style="font-weight:600;font-size:13px">{b}</span><span style="font-weight:600;font-size:13px">{c}</span></li>' for a, b, c in rows) + "</ul>"
    z = f'''<div class="idx"><h1>今の空港ごとの知らせ</h1><p>本番（soramemo.jp）をデモで 11/17 夕方に撮影。空港ごとの知らせは4つあり、申し込む所がばらばらです。近くの空港のシートには知らせの入口がありません。</p>
<div class="shot" style="grid-template-columns:1fr 1fr">{"".join(imgs)}</div>
<h2>いま申し込む所</h2><div class="card">{tbl}<p class="note">どれもこの端末への通知（ログインはいらない）。2版では上の4つを「ピン止めした空港」の1か所にまとめ、機体ごとの知らせは機体のピン止め（1版・2番目の案）にまとめます。</p></div></div>'''
    page("00-v2", "00 今の空港ごとの知らせ", z)

    # ---------- K1 ホーム：近くの空港のシートでピン止め ----------
    k1 = f'''{MAP}{MTOP}<div class="hsheet"><div class="grab"></div>
<div class="near1"><div class="l"><small>いちばん近い</small><div class="flap"><b>H</b><b>N</b><b>D</b></div>
<div class="nm"><b>東京国際空港（羽田）</b><span class="pinbtn on" aria-label="ピン止めを外す" aria-pressed="true">{PIN(True)}</span></div><span class="sub">第1ターミナル・判定範囲の中</span></div><div class="ck">チェックイン</div></div>
<div class="card mt"><div class="h"><b>ほかに 20km 以内 2つ</b><small>近い順</small></div><ul class="rows nlist">
<li><span class="tg2">ヘリポート</span><div class="tx"><b>東京ヘリポート</b><span>東京</span></div><span class="km">10.9<small>km</small></span><span class="pinbtn" aria-label="ピン止めする" aria-pressed="false">{PIN()}</span></li>
<li><span class="tg2 ap">空港</span><div class="tx"><b>成田国際空港</b><span>いちばん近い民間空港を1つ足しています</span></div><span class="km">60<small>km</small></span><span class="pinbtn on" aria-pressed="true">{PIN(True)}</span></li></ul></div>
<p class="note">ピンの印で空港をピン止め。ピン止めした空港に<b>特別塗装機が向かってきたら知らせます</b>（はじめの設定）。</p></div>{TAB_HOME}'''
    page("K1-v2", "K1 ホーム 近くの空港でピン止め", k1)

    # ---------- K2 空港ページ（羽田）----------
    k2 = f'''<div class="pad"><div class="zktop"><span class="back">{I(LEFT)}閉じる</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">HND</span><h2>東京国際空港（羽田）</h2><span class="s">東京都大田区・供用開始 1931年</span></div><span class="pinpill on" aria-pressed="true">{PIN(True)}ピン止め中</span></div>
<div class="card mt"><div class="nrow"><span class="bi">{I(BELL)}</span><div class="tx"><b>羽田の知らせ</b><span><span class="on1">特別塗装機</span><span class="on1">遅れ・門限</span></span></div><span class="go">{I(CHEV)}</span></div></div>
<div class="card mt"><div class="h"><b>いまの運用</b><small>実際の機体から判定</small></div><div style="font-size:28px;font-weight:900">北風運用</div><p class="note" style="margin-top:4px">着陸 34L・34R／離陸 05・34R</p></div>
<div class="card mt"><div class="h"><b>この空港に向かっている特別塗装機</b><small>3時間のうち</small></div><ul class="rows">
<li><span class="tmbig">16:05</span><div class="tx"><b>ジンベエジェット</b><span><span class="reg">JA05RK</span>・JTA 9 那覇から（推定）</span></div></li></ul></div>
<p class="note">空港ページの上の「ピン止め」で付け外し。知らせの中身は「羽田の知らせ」から。</p></div>{TAB_HOME}'''
    page("K2-v2", "K2 空港ページ ピン止め", k2)

    # ---------- K3 図鑑の空港1枚 ----------
    k3 = f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}関東</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">NRT</span><h2>成田国際空港</h2><span class="s">千葉県成田市</span></div><span class="pinpill" aria-pressed="false">{PIN()}ピン止め</span></div>
<div class="kv"><div><small>はじめての印</small><b>2025<small>/3/8</small></b></div><div><small>印</small><b>7<small>回</small></b></div></div>
<p class="note">図鑑の空港の1枚からもピン止めできます。飛行場・滑空場・ヘリポートの図鑑も同じ。</p></div>{TAB_BOOK}'''
    page("K3-v2", "K3 図鑑の空港 ピン止め", k3)

    # ---------- K4 ピン止めした直後（はじめの1回だけ・何を知らせるか）----------
    k4 = f'''{MAP}{MTOP}<div class="hsheet"><div class="grab"></div><div class="near1"><div class="l"><small>いちばん近い</small><div class="flap"><b>H</b><b>N</b><b>D</b></div><div class="nm"><b>東京国際空港（羽田）</b></div></div><div class="ck">チェックイン</div></div></div>{TAB_HOME}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田をピン止めしました</h2><button>完了</button></div>
<p class="sub">羽田のことで、何を知らせますか。あとから「羽田の知らせ」で変えられます。</p>
{oo([(K_SP, "国内・海外・アライアンス塗装。同じ機体は6時間に1回", "on"), (K_LATE, "門限の10分前より遅く着く便・0時前後に着く便", "off"), (K_GA, "1機ごと・続いたとき・強い横風など", "off"), (K_SPOT, "撮影地から見える機体（いつもの空港1つ）", "off")])}
<p class="note">どれもこの端末に届きます。<b>推定です。保証しません。</b></p></div>'''
    page("K4-v2", "K4 ピン止めした直後", k4)

    # ---------- K5 知らせの設定（1か所）：ピン止めの空港の一覧（おすすめ）----------
    def apc(code, nm, ons, offs):
        ch = "".join(f'<span class="on1">{x}</span>' for x in ons) + "".join(f'<span class="on1 x">{x}</span>' for x in offs)
        return f'<div class="apc"><div class="top"><i>{code}</i><b>{nm}</b><span class="go">{I(CHEV)}</span></div><div class="chips2">{ch}</div></div>'
    k5 = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}戻る</span><h2>知らせ</h2><span style="width:72px"></span></div>
<div class="pinh" style="margin-top:6px"><span class="pi">{PIN(True)}</span><b>ピン止めした空港</b><span class="n">3 / 12</span><span class="sp"></span><span class="ed">並べ替え</span></div>
<p class="keep">{I(CLOUD)}ピン止めはアカウントに保存・知らせはこの端末に届きます</p>
{apc("HND", "羽田", ["特別塗装機", "遅れ・門限"], ["ゴーアラウンド", "撮影"])}
{apc("NRT", "成田", ["特別塗装機"], ["遅れ・門限", "ゴーアラウンド", "撮影"])}
{apc("ISG", "石垣", ["特別塗装機", "欠航・ダイバート"], [])}
<p class="secth">便</p>
<div class="card mt" style="margin-top:8px"><div class="nrow"><span class="bi">{I(PLANE)}</span><div class="tx"><b>乗る便</b><span>JL 323（11/17）・15分の遅れから</span></div><span class="go">{I(CHEV)}</span></div></div>
<p class="secth">機体 <span style="font-weight:600">（2番目の案：機体のピン止め）</span></p>
<div class="card mt" style="margin-top:8px"><div class="nrow"><span class="bi">{PIN()}</span><div class="tx"><b>ピン止めした機体</b><span>3機・飛び始めたとき</span></div><span class="go">{I(CHEV)}</span></div></div>
</div>'''
    page("K5-v2", "K5 知らせ ピン止めの空港の一覧", k5)

    # ---------- K5b 比べる用：表の形で全部並べる ----------
    def cell(st):
        return "<td>" + {"on": '<span class="dot2 on">ON</span>', "off": '<span class="dot2">OFF</span>', "na": '<span class="dot2 na">—</span>'}[st] + "</td>"
    grid = [("羽田", "on", "on", "off", "off"), ("成田", "on", "off", "off", "off"), ("石垣", "on", "on", "na", "na")]
    k5b = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}戻る</span><h2>知らせ</h2><span style="width:72px"></span></div>
<div class="pinh" style="margin-top:6px"><span class="pi">{PIN(True)}</span><b>ピン止めした空港</b><span class="n">3 / 12</span></div>
<div class="card mt"><table class="grid4"><tr><th>空港</th><th>特別<br>塗装機</th><th>遅れ<br>門限</th><th>ゴー<br>アラウンド</th><th>撮影</th></tr>
{"".join(f"<tr><td>{a}</td>{cell(b)}{cell(c)}{cell(d)}{cell(e)}</tr>" for a, b, c, d, e in grid)}</table>
<p class="note">— はその空港では出せない知らせ（ゴーアラウンドは主な14空港・撮影はいつもの空港1つ）。石垣の「遅れ」は欠航・ダイバート・引き返しだけ。</p></div>
<p class="note">比べる用。1枚で見渡せるが、ゴーアラウンドや撮影の細かい設定はここに入らず、字も小さくなりがち。</p></div>'''
    page("K5b-v2", "K5b 比べる用 表の形", k5b)

    # ---------- K6 1空港の知らせ（羽田）----------
    k6 = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}知らせ</span><h2>羽田の知らせ</h2><span style="width:72px"></span></div>
<div class="aph" style="margin-top:0;align-items:center"><div class="tx"><span class="code">HND</span><span class="s" style="display:inline;margin-left:8px;font-size:15px;font-weight:800;color:var(--ink)">東京国際空港</span></div><span class="pinpill on">{PIN(True)}ピン止め中</span></div>
<div class="card mt">{oo([(K_SP, "国内・海外・アライアンス塗装（JAL・ANA のアライアンス塗装は知らせない）。同じ機体は6時間に1回", "on"), (K_LATE, "門限の10分前より遅く着く便・0時前後に着く便・欠航・ダイバート・引き返し", "on"), (K_GA, "1機ごと・続いたとき・強い横風・低い雲・雷", "off", "細かく"), (K_SPOT, "撮影地から見える機体を来る前に", "off", "撮影地と機体を選ぶ")])}</div>
<p class="note">どれも機体の位置（adsb.lol・ODbL）や運航情報（ODPT）からの<b>推定です。保証しません。</b></p>
<div class="danger">羽田のピン止めを外す</div>
<p class="note" style="text-align:center">外すと、羽田の知らせはすべて止まります。</p></div>'''
    page("K6-v2", "K6 1空港の知らせ 羽田", k6)

    # ---------- K6n 主要でない空港（石垣）----------
    k6n = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}知らせ</span><h2>石垣の知らせ</h2><span style="width:72px"></span></div>
<div class="aph" style="margin-top:0;align-items:center"><div class="tx"><span class="code">ISG</span><span class="s" style="display:inline;margin-left:8px;font-size:15px;font-weight:800;color:var(--ink)">新石垣空港</span></div><span class="pinpill on">{PIN(True)}ピン止め中</span></div>
<div class="card mt">{oo([(K_SP, "国内・海外・アライアンス塗装。同じ機体は6時間に1回", "on"), ("欠航・ダイバート・引き返し", "主な8空港でないので、門限ギリギリの知らせはありません", "on"), (K_GA, "主な14空港だけです", "na"), (K_SPOT, "いつもの空港を石垣にすると使えます", "na", "いつもの空港を変える")])}</div>
<p class="note">出せない知らせは薄くして残します（なぜ出せないかを書く）。</p></div>'''
    page("K6n-v2", "K6n 主要でない空港 石垣", k6n)

    # ---------- K7 運用タブ（空港側）：今のボタンをピン止めの1行に ----------
    k7 = f'''<div class="pad">{TOP}{kindrow("ap")}<div class="pickrow"><span class="ap"><i>HND</i>羽田<small>近く</small>{I(DOWN)}</span></div>
{views(["案内板", "1日の山", "滑走路", "定時", "空の道すじ", "撮る人"], "撮る人", True)}
<div class="card"><div class="h"><b>この空港に向かっている特別塗装機</b><small>3時間のうち</small></div><ul class="rows">
<li><span class="tmbig">16:05</span><div class="tx"><b>ジンベエジェット</b><span><span class="reg">JA05RK</span>・JTA 9 那覇から（推定）</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">16:40</span><div class="tx"><b>スターアライアンス塗装</b><span><span class="reg">B-58201</span>・BR 192 台北から（推定）</span></div><span class="go">{I(CHEV)}</span></li></ul>
<div class="nrow mt" style="background:var(--pill);border-radius:16px;padding:4px 6px 4px 12px"><span style="color:var(--navy)">{PIN(True)}</span><div class="tx"><b>羽田はピン止め中</b><span>特別塗装機が向かってきたら知らせる：ON</span></div><span class="go">{I(CHEV)}</span></div></div>
<div class="card"><div class="h"><b>ピン止めしていない空港のとき</b><small>例：伊丹</small></div>
<div class="nrow"><div class="tx"><b>伊丹をピン止めして知らせを受ける</b><span>特別塗装機が向かってきたら（はじめの設定）</span></div><span class="pinbtn">{PIN()}</span></div></div>
<p class="note">今の「羽田に特別塗装機が来たら通知する」のボタンの場所。申し込みはピン止めの1か所にまとめ、ここは状態と入口だけ。</p></div>{TABBAR}'''
    page("K7-v2", "K7 運用タブ 空港側", k7)

    # ---------- K8 運用の空港を選ぶシート：ピン止めが先頭 ----------
    k8 = f'''<div class="pad">{TOP}{kindrow("ap")}<div class="pickrow"><span class="ap"><i>HND</i>羽田<small>近く</small>{I(DOWN)}</span></div></div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>空港を選ぶ</h2></div>
<div class="pickrow"><span class="search">{I(SRCH)}空港の名前かコード</span></div>
<p class="grp">{PIN(True)} ピン止め</p>
<div class="chips" style="flex-wrap:wrap;margin-top:8px"><span class="chip dark">HND 羽田</span><span class="chip">NRT 成田</span><span class="chip">ISG 石垣</span></div>
<p class="grp">近い順</p>
<ul class="rows"><li><div class="tx"><b>羽田</b><span>いまいる空港</span></div><span class="pinbtn on" style="background:var(--navy)">{PIN(True)}</span></li>
<li><div class="tx"><b>成田</b><span>60km</span></div><span class="pinbtn on" style="background:var(--navy)">{PIN(True)}</span></li>
<li><div class="tx"><b>中部</b><span>270km</span></div><span class="pinbtn">{PIN()}</span></li></ul></div>'''
    page("K8-v2", "K8 空港を選ぶ ピン止めが先頭", k8)

    # ---------- K9 今の利用者への1回の案内（まとめたこと）----------
    k9 = f'''{MAP}{MTOP}<div class="hsheet"><div class="grab"></div><div class="near1"><div class="l"><small>いちばん近い</small><div class="flap"><b>H</b><b>N</b><b>D</b></div><div class="nm"><b>東京国際空港（羽田）</b></div></div><div class="ck">チェックイン</div></div></div>{TAB_HOME}<div class="dim"></div>
<div class="sheet"><div class="grab"></div>
<div class="mig mt"><span class="pi">{PIN(True)}</span><p><b>空港の知らせを、ピン止めにまとめました</b>今まで申し込んでいた空港を、そのままピン止めしています。知らせの中身は変わりません。</p></div>
<div class="card mt" style="box-shadow:inset 0 0 0 1px var(--line)">
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>HND</i><b>羽田</b></div><div class="chips2"><span class="on1">特別塗装機</span><span class="on1">遅れ・門限</span></div></div>
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>NRT</i><b>成田</b></div><div class="chips2"><span class="on1">特別塗装機</span></div></div></div>
<div style="display:flex;gap:8px;margin-top:16px"><span class="pillbtn" style="flex:1">あとで</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">知らせを見る</span></div>
<p class="note" style="text-align:center">この案内は1回だけ出ます。</p></div>'''
    page("K9-v2", "K9 今の利用者への案内", k9)

    # ---------- K10 知らせの見本（空港中心）----------
    def nt(b, p, when="いま"):
        return f'<div class="nt1"><span class="ap"><i></i>そらメモ<em>{when}</em></span><b>{b}</b><p>{p}</p></div>'
    k10 = f'''<div class="lock"><div class="clk">15:10</div><div class="dt">11月17日 火曜日</div>
<p class="lab">ピン止めの空港に特別塗装機</p>
{nt("羽田にジンベエジェットが向かっています", "JTA 9 那覇から・JA05RK｜着くのは 16:05ごろ（推定）")}
<p class="lab">海外の会社のアライアンス塗装</p>
{nt("羽田にスターアライアンス塗装が向かっています", "エバー航空 BR 192 台北から・B-58201｜着くのは 16:40ごろ（推定）", "5分前")}
<p class="lab">機体もピン止めしているとき <small>（2番目の案と重なる）</small></p>
{nt("羽田に JAL Jubilee Express が向かっています", "ピン止めの機体・JL 332 福岡から｜着くのは 17:00ごろ（推定）", "12分前")}
<div class="cmp"><b>二重にしない</b>：同じ機体が同じ空港に向かうときは1回だけ（空港と機体の両方をピン止めしていても）。同じ機体は6時間に1回まで（今の決まり）。文の頭は空港の名前にして、どのピン止めの知らせかすぐ分かるようにする。</div></div>'''
    page("K10-v2", "K10 知らせの見本", k10)

    # ---------- 一覧（2版を上に、1版を下に）----------
    L = [("2版：空港をピン止め（おすすめ）", [
            ("00-v2", "今の空港ごとの知らせ", "本番の写真と、4か所に分かれた申し込み"),
            ("K1-v2", "ホーム・近くの空港", "いちばん近い空港と「ほか」の行にピンの印"),
            ("K2-v2", "空港ページ", "名前の横に「ピン止め中」・「羽田の知らせ」の1行"),
            ("K3-v2", "図鑑の空港の1枚", "ピン止めのピル"),
            ("K4-v2", "ピン止めした直後", "はじめは特別塗装機だけ ON"),
            ("K5-v2", "知らせ（1か所）", "ピン止めした空港の一覧・便・機体"),
            ("K5b-v2", "比べる用：表の形", "空港×知らせを1枚に"),
            ("K6-v2", "羽田の知らせ", "4つの ON／OFF・外す"),
            ("K6n-v2", "石垣の知らせ", "出せない知らせは薄く・理由つき"),
            ("K7-v2", "運用タブ 空港側", "今の通知のボタンを状態と入口に"),
            ("K8-v2", "空港を選ぶシート", "ピン止めした空港が先頭"),
            ("K9-v2", "今の利用者への案内", "申し込み済みの空港をそのままピン止め"),
            ("K10-v2", "知らせの見本", "二重にしない")]),
         ("1版：機体をピン止め（2番目の案として残す）", [
            ("P1", "機体側・ピン止めの段", "いまどこ・次の便（予想）・最後に見た"), ("P1g", "ログインしない人", "この端末だけ"),
            ("P1m", "多い人", "はじめは5機"), ("P1e", "1機もない人", ""), ("P1x", "比べる用：見方にピン止め", ""),
            ("P2o", "機体の1日（付ける前）", ""), ("P2", "機体の1日（付けた直後）", ""), ("P3", "特別塗装機の欄", ""),
            ("P4", "機体図鑑の1機", ""), ("P5", "すべて見る", "並べ替え・外す"), ("P5f", "20機いっぱい", ""),
            ("P6", "機体の知らせの設定", ""), ("P7", "機体の知らせの見本", "")])]
    body = '<div class="idx"><h1>ピン止め</h1><p>design/pin 2版（11/17）。ピン止めの中心は空港。空港をピン止めすると、その空港に特別塗装機が向かってきたら知らせます。空港ごとの知らせの申し込みはピン止めの1か所にまとめます。画面案だけで、アプリには入れません。</p>'
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n.replace("-v2","")}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "ピン止め", body + "</div>")

if __name__ == "__main__":
    M.build(); build(); print("ok")
