# -*- coding: utf-8 -*-
# 機体のピン止め（design/pin）1版の画面案を作る。1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。
# PNG は shoot.py で撮る。色と字・上の1行・タブ帯は base_ops.py（design/ops-split の部品。本番の運用タブ PR #112 の元）を使う。
# 見本の時刻は 11/17 15:10（羽田・北風運用。日の入りより前なので昼の画面）。機体は特別塗装機の表にあるものと、ふつうの登録記号。便と予想は見本。
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base_ops import CSS as BASE, I, CHEV, DOWN, LEFT, SRCH, PLANE, TOWER, INFO, SHARE, TABBAR, TOP, kindrow, views

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)

# ピンの印（線の印。絵文字は使わない）。外した状態は線だけ、付けた状態は塗る
PIN_D = '<path d="M8.5 3.5h7"/><path d="M10 3.5v5.2L6.8 13h10.4L14 8.7V3.5"/><path d="M12 13v7.5"/>'
def PIN(on=False):
    f = ' style="fill:currentColor"' if on else ""
    return f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 3.5h7"/><path{f} d="M10 3.5v5.2L6.8 13h10.4L14 8.7V3.5Z"/><path d="M12 13v7.5"/></svg>'
BELL = '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15Z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>'
PHONE = '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 18h2"/>'
CLOUD = '<path d="M7 18a4 4 0 0 1-.6-8 5.5 5.5 0 0 1 10.7 1.2A3.5 3.5 0 0 1 17 18Z"/>'
GRIP = "≡"

CSS = BASE + r"""
/* ピンの押す所：44px の丸。付けた状態は濃い紺で塗る（JAL赤・ANA青は使わない） */
.pinbtn{flex:none;width:44px;height:44px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--card);box-shadow:var(--sh);color:var(--ink2)}
.pinbtn.on{background:var(--navy);color:#fff;box-shadow:none}
.card .pinbtn:not(.on){background:var(--pill);box-shadow:none}
.pinbtn svg{width:20px;height:20px}
.pinpill{height:44px;display:inline-flex;align-items:center;gap:6px;padding:0 16px 0 12px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--ink2)}
.pinpill.on{background:var(--navy);color:#fff}
.pinpill svg{width:18px;height:18px}
/* ピン止めの段 */
.pinh{display:flex;align-items:center;gap:8px;margin:0 0 2px}
.pinh .pi{width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;display:inline-flex;align-items:center;justify-content:center}
.pinh .pi svg{width:16px;height:16px}
.pinh b{font-size:16px;font-weight:800}
.pinh .n{font-size:13px;font-weight:600;color:var(--mute)}
.pinh .sp{flex:1}
.pinh .ed{height:44px;display:inline-flex;align-items:center;padding:0 4px 0 10px;font-size:14px;font-weight:800;color:var(--ink2)}
.keep{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--mute);margin:2px 0 4px}
.keep svg{width:16px;height:16px}
.keep a{color:var(--ink2);font-weight:800;text-decoration:none;margin-left:auto;min-height:44px;display:inline-flex;align-items:center}
.prow li{align-items:flex-start;padding:12px 0}
.prow .sw{margin-top:2px}
.prow .go{align-self:center}
.st{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px;font-size:13px;color:var(--ink2)}
.st .tag{padding:2px 9px}
.tag.park{background:var(--pill);color:var(--ink2)}
.tag.old{background:transparent;color:var(--mute);box-shadow:inset 0 0 0 1.5px #C9CFD8}
.nx{display:flex;align-items:baseline;gap:6px;margin-top:4px;font-size:13px;color:var(--ink2)}
.nx b{font-size:15px;font-weight:800;font-variant-numeric:tabular-nums}
.nx .pv{font-size:13px;font-weight:800;color:#3730A3;background:#EEF2FF;border-radius:999px;padding:1px 8px}
.nx .no{color:var(--mute)}
.rows .tx .nx,.rows .tx .st{display:flex;flex-wrap:wrap;overflow:visible;white-space:normal}
.rows .tx .nx span,.rows .tx .st span{display:inline;white-space:nowrap;flex:none;overflow:visible}
.rows .tx .nx .no{white-space:normal;flex:1 1 auto;min-width:0}
.seen{display:block;font-size:13px;color:var(--sub);margin-top:2px}
.more{display:flex;justify-content:center;margin-top:6px}
.hintc{display:flex;align-items:center;gap:12px}
.hintc .pi{flex:none;width:44px;height:44px;border-radius:50%;background:var(--pill);color:var(--ink2);display:inline-flex;align-items:center;justify-content:center}
.hintc p{margin:0;font-size:14px;line-height:1.6;color:var(--ink2)}
.hintc p small{display:block;font-size:13px;color:var(--mute)}
/* 機体の1日の上の段（ピンを足す） */
.selrow{display:flex;align-items:center;gap:8px;margin-top:12px}
.selrow .sp{flex:1}
.selrow .back{flex:none;white-space:nowrap;padding:0 10px 0 4px}
.selrow .ap{flex:none;white-space:nowrap;font-size:16px;gap:6px;padding:0 14px 0 6px}
/* 知らせた直後の小さな帯（トースト） */
.toast{position:fixed;left:50%;transform:translateX(-50%);bottom:96px;width:358px;background:var(--navy);color:#fff;border-radius:18px;padding:12px 12px 12px 16px;display:flex;align-items:center;gap:10px;z-index:6;box-shadow:0 14px 30px -14px rgba(15,23,42,.6)}
.toast .tx{flex:1;font-size:14px;line-height:1.5}
.toast .tx b{display:block;font-size:15px}
.toast .tx small{font-size:13px;color:#C9D2DE}
.toast .act{flex:none;height:44px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;background:rgba(255,255,255,.14);font-size:14px;font-weight:800}
/* 特別塗装機の欄の行：右にピン、その左に › の代わりに行全体を押す */
.sprow li{gap:10px}
/* 図鑑の1機 */
.zk{padding:8px 16px 120px}
.zktop{display:flex;align-items:center;justify-content:space-between;height:52px}
.zkimg{height:150px;border-radius:18px;background:linear-gradient(135deg,#F3D7D9 0 30%,#fff 30% 58%,#E9EEF5 58%);display:flex;align-items:flex-end;padding:12px;color:var(--mute);font-size:13px}
.zkname{display:flex;align-items:flex-start;gap:10px;margin-top:14px}
.zkname .tx{flex:1}
.zkname h2{margin:0;font-size:22px;font-weight:900;line-height:1.3}
.zkname .tx>span{display:block;font-size:13px;color:var(--mute);margin-top:2px}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
.kv div{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:12px 14px}
.kv small{display:block;font-size:13px;color:var(--mute)}
.kv b{font-size:20px;font-weight:900}
.kv b small{display:inline;font-size:13px;color:var(--sub);font-weight:700;margin-left:2px}
/* 一覧（すべて・並べ替え） */
.ed li{min-height:64px}
.ed .grip{flex:none;width:28px;color:#AAB2BD;text-align:center;font-size:18px}
.ed .rm{flex:none;height:44px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--ink2)}
.meter{display:flex;align-items:center;gap:10px;margin:8px 0 4px}
.meter .bar{flex:1;height:8px;border-radius:9px;background:var(--pill);overflow:hidden}
.meter .bar i{display:block;height:100%;background:var(--navy);border-radius:9px}
.meter b{font-size:20px;font-weight:900}
.meter b small{font-size:13px;color:var(--sub);font-weight:700}
/* 知らせの見本（ロック画面の上の通知の形。特定の機種の見た目はまねしない） */
.lock{min-height:844px;background:linear-gradient(180deg,#26344D,#3E5576 60%,#5D7593);padding:70px 14px 40px;color:#fff}
.lock .clk{text-align:center;font-size:64px;font-weight:300;letter-spacing:.02em;line-height:1}
.lock .dt{text-align:center;font-size:15px;color:#DCE3EC;margin:6px 0 26px}
.nt1{background:rgba(255,255,255,.92);color:var(--ink);border-radius:20px;padding:12px 14px;margin-top:10px}
.nt1 .ap{all:unset;display:flex;align-items:center;gap:6px;font-size:13px;color:var(--mute)}
.nt1 .ap i{width:20px;height:20px;border-radius:6px;background:var(--navy);display:inline-block}
.nt1 .ap em{font-style:normal;margin-left:auto}
.nt1 b{display:block;font-size:15px;font-weight:800;margin-top:4px;line-height:1.45}
.nt1 p{margin:2px 0 0;font-size:14px;line-height:1.55;color:var(--ink2)}
.lab{font-size:13px;font-weight:800;color:#DCE3EC;margin:22px 4px 0}
.lab small{font-size:13px;font-weight:600;color:#B8C4D3}
.cmp{background:rgba(255,255,255,.12);border-radius:18px;padding:12px 14px;margin-top:22px;font-size:14px;line-height:1.7;color:#EEF2F7}
.cmp b{color:#fff}
"""

def page(name, title, body):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

PL_VIEWS = ["最近見た", "特別塗装機"]
SEARCH = f'<div class="pickrow"><span class="search">{I(SRCH)}登録記号か便名で探す（例：JA339J）</span></div>'
FOOT = '<p class="note">機体の位置は adsb.lol（ODbL）。次の便は記録した便から作った予想で、<b>予想です。保証しません。</b></p>'

# 見本の機体：登録記号・名前・会社と機種・色・いまの状態・どこ・次の便・最後に見た
PINS = [
    ("JA339J", "JAL Jubilee Express", "JAL・B737-800", "#B4232A", "fly", "JL 323 羽田→福岡", ("17:00", "福岡→羽田", True), "いま"),
    ("JA894A", "JA894A", "ANA・B787-9", "#1C4FA0", "park", "伊丹に駐機中", ("16:20", "伊丹→羽田", True), "14:52"),
    ("B-58201", "スターアライアンス塗装", "エバー航空・B777-300ER", "#4B5563", "fly", "BR 192 台北→羽田", None, "いま"),
    ("JA05RK", "ジンベエジェット", "JTA・B737-800", "#0E7490", "old", "那覇の近く", ("あす 07:30", "那覇→石垣", True), "11/15 21:40"),
    ("JA381A", "FLYING HONU（青）", "ANA・A380", "#1C4FA0", "park", "成田に駐機中", ("あす 10:30", "成田→ホノルル", True), "13:05"),
]

def pinrow(reg, nm, sub, col, st, where, nxt, seen, chev=True):
    tag = {"fly": '<span class="tag live">● 飛行中</span>', "park": '<span class="tag park">駐機中</span>', "old": '<span class="tag old">しばらく見ていない</span>'}[st]
    badge = reg[2:] if reg.startswith("JA") else reg.split("-")[-1][-3:]
    title = nm if nm != reg else f'<span class="reg" style="font-size:16px">{reg}</span>'
    regline = f'<span class="reg">{reg}</span>・{sub}' if nm != reg else sub
    if nxt:
        nx = f'<span class="nx"><span>次の便</span><span class="pv">予想</span><b>{nxt[0]}</b><span>ごろ {nxt[1]}</span></span>'
    else:
        nx = '<span class="nx"><span>次の便</span><span class="no">海外の会社の機体は出せません</span></span>'
    seen_t = "最後に見た " + ("たった今" if seen == "いま" else seen)
    go = f'<span class="go">{I(CHEV)}</span>' if chev else ""
    return f'''<li><span class="sw" style="background:{col}">{badge}</span><div class="tx"><b>{title}</b><span>{regline}</span>
<span class="st">{tag}<span>{where}</span></span>{nx}<span class="seen">{seen_t}</span></div>{go}</li>'''

RECENT = [("JA01XJ", "A350 1号機（赤のロゴ）", "JAL・A350-900", "#B4232A"), ("JA737N", "JA737N", "JAL・B737-800", "#B4232A")]
def recentrow(reg, nm, sub, col):
    title = nm if nm != reg else f'<span class="reg" style="font-size:16px">{reg}</span>'
    regline = f'<span class="reg">{reg}</span>・{sub}' if nm != reg else sub
    return f'<li><span class="sw" style="background:{col}">{reg[2:]}</span><div class="tx"><b>{title}</b><span>{regline}</span></div><span class="go">{I(CHEV)}</span></li>'
RECENT_CARD = f'<div class="card"><div class="h"><b>最近見た機体</b><small>この端末で開いた順</small></div><ul class="rows">{"".join(recentrow(*r) for r in RECENT)}</ul></div>'

def pincard(rows, n, keep, more=None, edit=True):
    keepl = {"acc": f'<p class="keep">{I(CLOUD)}アカウントに保存・ほかの端末でも出ます</p>',
             "dev": f'<p class="keep">{I(PHONE)}この端末だけに保存<a>ログインして残す ›</a></p>'}[keep]
    ed = '<span class="ed">並べ替え・外す</span>' if edit else ""
    mo = f'<div class="more"><span class="pillbtn">ピン止めをすべて見る（{more}）{I(CHEV)}</span></div>' if more else ""
    return f'''<div class="card"><div class="pinh"><span class="pi">{PIN(True)}</span><b>ピン止め</b><span class="n">{n} / 20機</span><span class="sp"></span>{ed}</div>
{keepl}<ul class="rows prow">{"".join(pinrow(*r) for r in rows)}</ul>{mo}</div>'''

def build():
    # ---------- P1 機体側のはじめ（ログインした人・3機）----------
    p1 = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "最近見た")}
{pincard(PINS[:3], 3, "acc")}{RECENT_CARD}{FOOT}</div>{TABBAR}'''
    page("P1", "P1 機体側 ピン止めの段", p1)

    # ---------- P1g ログインしない人（この端末だけ）----------
    p1g = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "最近見た")}
{pincard(PINS[:2], 2, "dev")}{RECENT_CARD}{FOOT}</div>{TABBAR}'''
    page("P1g", "P1g ログインしない人", p1g)

    # ---------- P1m たくさんある人（はじめは5機まで）----------
    p1m = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "最近見た")}
{pincard(PINS[:5], 12, "acc", more=12)}{RECENT_CARD}{FOOT}</div>{TABBAR}'''
    page("P1m", "P1m ピン止めが多い人", p1m)

    # ---------- P1e まだ1機もない人 ----------
    p1e = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "最近見た")}
<div class="card hintc"><span class="pi">{PIN()}</span><p>気になる機体をピン止めすると、ここにいつも出ます<small>機体のくわしく・特別塗装機・機体図鑑のピンの印から</small></p></div>
{RECENT_CARD}
<div class="card"><div class="h"><b>いま飛んでいる特別塗装機</b><small>飛行中 17機</small></div><ul class="rows">{recentrow("JA05RK","ジンベエジェット","JTA・B737-800","#0E7490")}</ul></div>{FOOT}</div>{TABBAR}'''
    page("P1e", "P1e ピン止めがない人", p1e)

    # ---------- P1x 比べる用：見方に「ピン止め」を足す ----------
    p1x = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(["ピン止め", "最近見た", "特別塗装機"], "ピン止め")}
{pincard(PINS[:4], 4, "acc")}{FOOT}</div>{TABBAR}'''
    page("P1x", "P1x 比べる用 見方にピン止め", p1x)

    # ---------- P2 機体の1日（選んだあと）：上の段にピン・付けた直後の帯 ----------
    p2 = f'''<div class="pad">{TOP}{kindrow("pl")}
<div class="selrow"><span class="back">{I(LEFT)}戻る</span><span class="ap plr"><i>JA339J</i>B737-800</span><span class="sp"></span><span class="pinbtn on" aria-label="ピン止めを外す" aria-pressed="true">{PIN(True)}</span><span class="ic">{I(SHARE)}</span></div>
{views(PL_VIEWS, "最近見た")}
<div class="card"><div class="h"><b>JAL Jubilee Express</b><small>特別塗装機</small></div>
<ul class="rtl">
<li class="fold"><div class="tm"><b>06:30</b><small>〜13:05</small></div><div class="dot"><i style="background:#AAB3C0"></i></div><div class="tx">今日飛んだ 3便 <span style="display:inline;color:var(--blue);font-weight:800">開く</span></div></li>
<li class="now"><div class="tm"><b>14:18</b><small>発</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 323</b><span>羽田 → 福岡</span><em><span class="tag live">● 飛行中</span>16:05 着く見込み（推定）</em></div></li>
<li class="edge"><b>ここから予想</b><span>予想です。保証しません</span></li>
<li class="pr"><div class="tm"><b>17:00</b><small>ごろ</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 332</b><span>福岡 → 羽田</span><em><span class="cf"><i></i><i></i><i></i></span>高い・12回中11回</em></div></li>
</ul></div></div>{TABBAR}
<div class="toast"><span class="pinbtn on" style="background:rgba(255,255,255,.14)">{PIN(True)}</span><div class="tx"><b>ピン止めしました</b><small>飛び始めたとき・羽田に向かうときに知らせます</small></div><span class="act">知らせの設定</span></div>'''
    page("P2", "P2 機体の1日 ピン", p2)

    # ---------- P2o 機体の1日：まだピン止めしていない（押す前）----------
    p2o = f'''<div class="pad">{TOP}{kindrow("pl")}
<div class="selrow"><span class="back">{I(LEFT)}戻る</span><span class="ap plr"><i style="background:var(--ink)">JA737N</i>B737-800</span><span class="sp"></span><span class="pinbtn" aria-label="ピン止めする" aria-pressed="false">{PIN()}</span><span class="ic">{I(SHARE)}</span></div>
{views(PL_VIEWS, "最近見た")}
<div class="card"><div class="h"><b>JA737N</b><small>B737-800・JAL</small></div>
<ul class="rtl">
<li class="now"><div class="tm"><b>14:40</b><small>着</small></div><div class="dot"><i style="background:var(--ink2);box-shadow:none"></i></div><div class="tx"><b>JL 306</b><span>福岡 → 羽田</span><em><span class="tag park">駐機中</span>羽田</em></div></li>
<li class="edge"><b>ここから予想</b><span>予想です。保証しません</span></li>
<li class="pr"><div class="tm"><b>15:30</b><small>ごろ</small></div><div class="dot"><i></i></div><div class="tx"><b>JL 315</b><span>羽田 → 福岡</span><em><span class="cf"><i></i><i></i><i class="o"></i></span>中くらい・6回中4回</em></div></li>
</ul></div>
<p class="note">ふつうの機体もピン止めできます。上の <b>ピンの印</b> で付け外し。</p></div>{TABBAR}'''
    page("P2o", "P2o 機体の1日 ピン前", p2o)

    # ---------- P3 特別塗装機の欄：行ごとにピン ----------
    sp = [("JA339J", "JAL Jubilee Express", "JAL・B737-800", "#B4232A", True, "JL 323 羽田→福岡", "17:00ごろ 福岡→羽田"),
          ("JA05RK", "ジンベエジェット", "JTA・B737-800", "#0E7490", False, "JTA 9 羽田→那覇", "18:40ごろ 那覇→石垣"),
          ("JA228J", "J-AIR 創立30周年記念機", "J-AIR・E190", "#B4232A", False, "JL 2205 伊丹→松山", "16:30ごろ 松山→伊丹"),
          ("B-58201", "スターアライアンス塗装", "エバー航空・B777-300ER", "#4B5563", True, "BR 192 台北→羽田", "")]
    def sprow(reg, nm, sub, col, on, where, pred):
        badge = reg[2:] if reg.startswith("JA") else reg[-3:]
        pr = f'<span style="color:#3730A3;font-weight:700">この先（予想）{pred}</span>' if pred else '<span>この先（予想）は出せません（海外の会社）</span>'
        lab = "ピン止めを外す" if on else "ピン止めする"
        return f'<li><span class="sw" style="background:{col}">{badge}</span><div class="tx"><b>{nm}</b><span><span class="reg">{reg}</span>・{sub}</span><span><span class="tag live">● 飛行中</span> {where}</span>{pr}</div><span class="pinbtn{" on" if on else ""}" aria-label="{lab}" aria-pressed="{str(on).lower()}">{PIN(on)}</span></li>'
    p3 = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "特別塗装機")}
<div class="chips" style="margin-bottom:12px"><span class="chip dark">いま</span><span class="chip">この先</span><span class="chip">羽田に来る</span></div>
<div class="card"><div class="h"><b>いま飛んでいる</b><small>17機・アライアンス塗装 3機</small></div><ul class="rows sprow">{"".join(sprow(*r) for r in sp)}</ul>
<p class="note">右のピンの印で付け外し。行を押すと機体の1日が開きます。</p></div>{FOOT}</div>{TABBAR}'''
    page("P3", "P3 特別塗装機の欄 ピン", p3)

    # ---------- P4 機体図鑑（特別塗装機）の1機 ----------
    p4 = f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}機体図鑑</span><span class="ic">{I(SHARE)}</span></div>
<div class="zkimg">写真（公式・報道・コモンズの出典つき）</div>
<div class="zkname"><div class="tx"><h2>JAL Jubilee Express</h2><span><span class="reg">JA339J</span>・JAL・B737-800</span></div><span class="pinpill on" aria-pressed="true">{PIN(True)}ピン止め中</span></div>
<div class="card mt"><div class="h"><b>いま</b><small>最後に見た たった今</small></div>
<div class="st" style="margin-top:0"><span class="tag live">● 飛行中</span><span>JL 323 羽田→福岡・16:05 着く見込み（推定）</span></div>
<div class="nx"><span>次の便</span><span class="pv">予想</span><b>17:00</b><span>ごろ 福岡→羽田</span></div>
<div style="margin-top:10px"><span class="pillbtn">運用で機体の1日を見る {I(CHEV)}</span></div></div>
<p class="note">ピン止めすると、運用の「機体」のはじめにいつも出ます。予想は<b>予想です。保証しません。</b></p></div>
<nav class="tabbar"><span>{I('<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>','')}ホーム</span><span class="on">{I('<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/>','')}図鑑</span><span>{I(PLANE,'')}フライト</span><span>{I('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 12 18 6"/>','')}運用</span><span>{I('<path d="M4 18 10 12l3 3 7-8"/><path d="M15 7h5v5"/>','')}修行</span></nav>'''
    page("P4", "P4 機体図鑑の1機 ピン", p4)

    # ---------- P5 ピン止めをすべて見る（並べ替え・外す）----------
    allp = PINS + [("JA01XJ", "A350 1号機（赤のロゴ）", "JAL・A350-900", "#B4232A", "park", "羽田に駐機中", None, "")]
    def edrow(r):
        reg, nm, sub, col = r[:4]
        badge = reg[2:] if reg.startswith("JA") else reg[-3:]
        title = nm if nm != reg else f'<span class="reg" style="font-size:16px">{reg}</span>'
        return f'<li><span class="grip">{GRIP}</span><span class="sw" style="background:{col}">{badge}</span><div class="tx"><b>{title}</b><span><span class="reg">{reg}</span>・{sub}</span></div><span class="rm">外す</span></li>'
    p5 = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}戻る</span><h2>ピン止め</h2><span class="pillbtn" style="background:var(--navy);color:#fff">完了</span></div>
<div class="meter"><b>12<small> / 20機</small></b><span class="bar"><i style="width:60%"></i></span></div>
<p class="keep">{I(CLOUD)}アカウントに保存・ほかの端末でも出ます</p>
<div class="card"><p class="note" style="margin:0 0 4px">≡ を押したまま動かすと、運用の「機体」に出る順になります。上の5機がはじめに出ます。</p>
<ul class="rows ed">{"".join(edrow(r) for r in allp)}</ul>
<p class="note">ほか6機</p></div>
<div class="card mt" style="display:flex;align-items:center;gap:10px"><div style="flex:1"><b style="font-size:15px">ピン止めの知らせ</b><p class="note" style="margin:2px 0 0">飛び始めたとき・羽田に向かうとき</p></div><span class="tg on">ON</span></div>
</div>'''
    page("P5", "P5 ピン止めをすべて見る", p5)

    # ---------- P5f 20機いっぱいのとき ----------
    p5f = f'''<div class="pad">{TOP}{kindrow("pl")}
<div class="selrow"><span class="back">{I(LEFT)}戻る</span><span class="ap plr"><i style="background:var(--ink)">JA737N</i>B737-800</span><span class="sp"></span><span class="pinbtn">{PIN()}</span><span class="ic">{I(SHARE)}</span></div>
{views(PL_VIEWS, "最近見た")}<div class="card" style="height:300px"></div></div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>ピン止めは20機まで</h2></div>
<p class="sub">JA737N をピン止めするには、どれか1機を外してください。</p>
<div class="meter"><b>20<small> / 20機</small></b><span class="bar"><i style="width:100%"></i></span></div>
<ul class="rows ed" style="margin-top:4px">
<li><span class="sw" style="background:#0E7490">05RK</span><div class="tx"><b>ジンベエジェット</b><span>最後に見た 11/15 21:40</span></div><span class="rm">外す</span></li>
<li><span class="sw" style="background:#4B5563">201</span><div class="tx"><b>スターアライアンス塗装</b><span>最後に見た 11/14 10:12</span></div><span class="rm">外す</span></li>
<li><span class="sw" style="background:#1C4FA0">381A</span><div class="tx"><b>FLYING HONU（青）</b><span>最後に見た 13:05</span></div><span class="rm">外す</span></li>
</ul>
<p class="note">最後に見たのが古い順。外した機体の記録（乗った・見た）はそのまま残ります。</p>
<div style="display:flex;gap:8px;margin-top:12px"><span class="pillbtn" style="flex:1">やめる</span><span class="pillbtn" style="flex:1">すべて見て選ぶ</span></div></div>'''
    page("P5f", "P5f 20機いっぱい", p5f)

    # ---------- P6 知らせの設定（シート）----------
    def oo(items):
        out = []
        for nm, sub, st in items:
            tg = '<span class="tg on">ON</span>' if st == "on" else '<span class="tg off">OFF</span>'
            out.append(f'<li><div class="tx"><b>{nm}</b><span>{sub}</span></div>{tg}</li>')
        return '<ul class="onoff">' + "".join(out) + "</ul>"
    p6 = f'''<div class="pad">{TOP}{kindrow("pl")}{SEARCH}{views(PL_VIEWS, "最近見た")}{pincard(PINS[:2], 3, "acc")}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>ピン止めの知らせ</h2><button>完了</button></div>
<p class="sub">ピン止めした機体ぜんぶに効きます。</p>
{oo([("飛び始めたとき", "離陸を機体の位置で見つけたら（推定）", "on"), ("自分の空港に向かっているとき", "着くのは○時ごろ（推定）と1回", "on")])}
<div class="grp">自分の空港</div>
<div class="chips" style="margin-top:8px;flex-wrap:wrap"><span class="chip dark">羽田</span><span class="chip">成田</span><span class="chip">＋ 足す</span></div>
<p class="note">特別塗装機の知らせ（空港ごと）と同じ機体が重なるときは、<b>1回だけ</b>知らせます。海外の会社の機体は「飛び始めた」の代わりに「日本の空港に向かっています」を1回。<b>推定です。保証しません。</b></p></div>'''
    page("P6", "P6 ピン止めの知らせの設定", p6)

    # ---------- P7 知らせの見本 ----------
    def nt(t, b, p, when="いま"):
        return f'<div class="nt1"><span class="ap"><i></i>そらメモ<em>{when}</em></span><b>{b}</b><p>{p}</p></div>'
    p7 = f'''<div class="lock"><div class="clk">15:10</div><div class="dt">11月17日 火曜日</div>
<p class="lab">飛び始めたとき</p>
{nt("", "ピン止めの JA894A が飛び始めました", "NH 30 伊丹→羽田・羽田に着くのは 16:20ごろ（推定）")}
<p class="lab">自分の空港に向かっているとき</p>
{nt("", "JAL Jubilee Express（JA339J）が羽田に向かっています", "特別塗装機・ピン止め｜着くのは 16:05ごろ（推定）", "2分前")}
<p class="lab">海外の会社の機体 <small>（予想が出せないので「向かっている」だけ）</small></p>
{nt("", "スターアライアンス塗装（B-58201）が羽田に向かっています", "エバー航空・BR 192 台北から｜着くのは 16:40ごろ（推定）", "12分前")}
<div class="cmp"><b>二重にしない</b>：羽田の「特別塗装機が来たら通知する」を ON にしていても、ピン止めした特別塗装機が羽田に向かうときは上の2つめの1回だけ（札に「特別塗装機・ピン止め」）。飛び始め→向かっているの順で、1機1日にそれぞれ1回まで。</div></div>'''
    page("P7", "P7 知らせの見本", p7)

    # ---------- 一覧 ----------
    L = [("運用の「機体」のはじめ", [("P1", "ピン止めの段（ログインした人）", "最近見たの上・いまどこ・次の便（予想）・最後に見た"),
                                ("P1g", "ログインしない人", "「この端末だけに保存」とログインの入口"),
                                ("P1m", "ピン止めが多い人", "はじめは5機まで・すべて見る"),
                                ("P1e", "まだ1機もない人", "1枚の小さな案内だけ"),
                                ("P1x", "比べる用：見方に「ピン止め」", "見方の帯を3つにする案")]),
         ("付け外しする所", [("P2o", "機体の1日（付ける前）", "上の1行の右にピンの印"), ("P2", "機体の1日（付けた直後）", "帯で「知らせます」と設定への入口"),
                          ("P3", "特別塗装機の欄", "行ごとの右にピンの印"), ("P4", "機体図鑑の1機", "名前の横に「ピン止め中」")]),
         ("並べ替え・上限", [("P5", "ピン止めをすべて見る", "≡ で並べ替え・外す・12 / 20機"), ("P5f", "20機いっぱいのとき", "外す1機を選ぶシート")]),
         ("知らせ", [("P6", "知らせの設定", "2つの ON／OFF と自分の空港"), ("P7", "知らせの見本", "二重にしない決まり")])]
    body = '<div class="idx"><h1>機体のピン止め</h1><p>design/pin 1版（11/17）。画面案だけで、アプリには入れません。下のタブ帯・運用の上の1行は今のまま。見本の時刻は 11/17 15:10。</p>'
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "機体のピン止め", body + "</div>")

if __name__ == "__main__":
    build(); print("ok")
