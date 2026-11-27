# -*- coding: utf-8 -*-
# 運用タブを「空港」と「機体」に分ける（design/ops-split）2版。改善担当 review-1 を受けて直した画面案を ../*-v2.html に書き出す。
# CSS と部品は make.py（1版）を読み込み、直した所だけ上書きする。PNG は shoot_v2.py で撮る。
# 見本の時刻は 11/15 15:10（羽田・北風運用）。便と予想は見本（画面をまたいで便名と機体をそろえた）。
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
from make import I, CHEV, DOWN, LEFT, PEN, INFO, SHARE, SRCH, TOWER, PLANE, TABBAR, TOP, RUNWAY, FOOT_PL
OUT = M.OUT

CSS2 = M.CSS + r"""
/* 2版：上の1行（空港｜機体＋空港のピル＋ⓘ・共有）。上の段を1段へらす */
.trow{display:flex;align-items:center;gap:6px;margin-top:16px}
.trow .sp{flex:1}
.kind.s span{min-width:0;padding:0 12px;font-size:15px}
.trow .ap{height:48px;padding:0 10px 0 6px;gap:6px}
.trow .ap i{padding:5px 5px}
.trow .search{padding:0 14px;gap:6px;min-width:0;white-space:nowrap;overflow:hidden}
.trow .back{flex:none;padding:0 12px 0 4px}
.trow .ap.plr{padding-right:10px}
/* 2版：見方の帯は横に送れる帯＋右端に固定の鉛筆（本番の .vwrow と同じ） */
.vrow{display:flex;align-items:center;gap:4px;margin:16px 0 12px 0}
.vs{flex:1;min-width:0;display:flex;gap:20px;overflow-x:auto;scrollbar-width:none;font-size:15px;font-weight:800;color:var(--mute);white-space:nowrap;padding:0 2px;
  -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 18px,#000 calc(100% - 22px),transparent);mask-image:linear-gradient(90deg,transparent 0,#000 18px,#000 calc(100% - 22px),transparent)}
.vs.nol{-webkit-mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent);mask-image:linear-gradient(90deg,#000 calc(100% - 22px),transparent)}
.vs.nofade{-webkit-mask-image:none;mask-image:none}
.vs::-webkit-scrollbar{display:none}
.vs span{flex:none;padding:11px 0}
.vs span.on{color:var(--ink);box-shadow:inset 0 -3px 0 var(--ink)}
.vrow .pen{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--mute)}
.vrow.none .vs span{color:var(--mute)}
/* シートの中の切り替えも紺（上と同じ部品） */
.kind.insheet{background:var(--pill)}
.kind.insheet span.on{background:var(--navy);color:#fff;box-shadow:none}
.kind.insheet span em{font-style:normal;font-size:13px;font-weight:700;color:var(--mute);background:var(--card);border-radius:999px;padding:1px 8px;margin-left:2px}
/* 海外の空港のいま（world-ops W1 の札と欄。案内板の便の行はピンの札だけ、便の数は欄の中だけ） */
.st{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:2px 9px 2px 7px;font-size:13px;font-weight:800;white-space:nowrap}
.st svg{flex:none;width:13px;height:13px;fill:currentColor}
.st small{font-size:13px;font-weight:700;opacity:.85;margin-left:2px}
.st.s1{background:#9A3412;color:#fff}.st.s2{background:#FEF3C7;color:#92400E}.st.s3{background:var(--pill);color:var(--ink2)}
.stkey{display:flex;align-items:flex-start;gap:6px;font-size:13px;line-height:1.6;color:var(--mute);margin:8px 0 0}
.stkey svg{flex:none;width:13px;height:13px;fill:var(--mute);margin-top:4px}
.wo{margin-top:14px;background:#F7F8FA;border-radius:18px;padding:12px 14px}
.wo h4{margin:0 0 2px;font-size:15px;font-weight:800;display:flex;justify-content:space-between;align-items:baseline}
.wo h4 small{font-size:13px;font-weight:600;color:var(--mute)}
.wol{list-style:none;margin:0;padding:0}
.wol li{display:flex;align-items:center;gap:8px;min-height:56px;padding:6px 0}
.wol li+li{box-shadow:0 -1px 0 var(--line)}
.wol .tx{flex:1;min-width:0}
.wol .nm{display:block;font-size:16px;font-weight:800}
.wol .nm small{font-size:13px;font-weight:600;color:var(--sub);margin-left:4px}
.wol .wh{display:flex;flex-wrap:wrap;gap:4px 8px;align-items:center;font-size:13px;color:var(--ink2);margin-top:2px}
.wol .go{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.srcnote{font-size:13px;line-height:1.7;color:var(--mute);margin:6px 0 0}
.srcnote b{color:var(--ink2);font-weight:800}
.bdtabs{display:inline-flex;background:var(--pill);border-radius:999px;padding:3px}
.bdtabs span{height:38px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.bdtabs span.on{background:var(--card);color:var(--ink);box-shadow:0 2px 6px -3px rgba(15,23,42,.3)}
.rows .tx .st{margin-top:4px}
.rtl .tx span.tag{display:inline-flex}.rtl .tx span.tag.live{color:var(--ok)}
.rows .tx span.st{display:inline-flex;font-size:13px}
.rows .tx span.st.s1{color:#fff}.rows .tx span.st.s2{color:#92400E}.rows .tx span.st.s3{color:var(--ink2)}
.rows .tx span.st small{display:inline;color:inherit}
.rows .tx span.l2{white-space:normal}
/* 撮る人：空港側と同じ値をつなげて出す（案1） */
.linked{display:flex;align-items:center;gap:10px;background:#F7F8FA;border-radius:16px;padding:8px 6px 8px 14px;margin:0 0 12px}
.linked .tx{flex:1;min-width:0}
.linked b{display:block;font-size:15px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.linked span{display:block;font-size:13px;color:var(--mute)}
/* 操作の数の表 */
.cmp{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}
.cmp th{font-size:13px;font-weight:700;color:var(--mute);text-align:left;padding:4px 6px 8px}
.cmp td{padding:10px 6px;vertical-align:top;box-shadow:0 -1px 0 var(--line);color:var(--ink2);line-height:1.55}
.cmp td b.n{display:block;font-size:24px;font-weight:900;color:var(--ink);line-height:1.1}
.cmp td b.n small{font-size:13px;font-weight:700;color:var(--sub);margin-left:2px}
.cmp td:first-child{font-weight:800;color:var(--ink);width:30%}
.cmp td small.s{display:block;font-size:13px;color:var(--mute)}
.hl{background:#F1F5FF;border-radius:10px}
/* 比べる用の札 */
.cap{display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:999px;background:#FEF3C7;color:#92400E;font-size:13px;font-weight:800;margin:6px 0 0}
.offnote{display:flex;gap:10px;align-items:flex-start;background:#F7F8FA;border-radius:16px;padding:12px 14px;margin-top:12px;font-size:14px;color:var(--ink2);line-height:1.6}
.offnote svg{margin-top:2px;color:var(--mute)}
"""

PIN = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1a5 5 0 0 0-5 5c0 3.6 5 9 5 9s5-5.4 5-9a5 5 0 0 0-5-5zm0 7a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/></svg>'
def st(cls, text, src=""):
    return f'<span class="st {cls}">{PIN}{text}{f"<small>{src}</small>" if src else ""}</span>'

# 見方の帯を選んだ見方まで送る（本番の帯と同じく横に送れる）
SCROLL = """<script>for(const v of document.querySelectorAll('.vs')){const o=v.querySelector('.on');if(o){const r=o.offsetLeft+o.offsetWidth-v.clientWidth+30;if(r>0){v.scrollLeft=r;}else{v.classList.add('nol');}}else{v.classList.add('nol');}if(v.scrollWidth<=v.clientWidth)v.classList.add('nofade');}</script>"""

def page(name, title, body, extra=""):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS2}</style></head><body>{body}{extra}{SCROLL}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

def kind(side, cls="s"):
    a = "on" if side == "ap" else ""; m = "on" if side == "pl" else ""
    return f'<div class="kind {cls}" role="tablist" aria-label="運用で見るもの"><span class="{a}">空港</span><span class="{m}">機体</span></div>'

AP_PILL = f'<span class="ap"><i>HND</i>羽田{I(DOWN)}</span>'
SEARCH = f'<span class="search">{I(SRCH)}登録記号・便名</span>'

def trow(side, sel=None, show_kind=True):
    """上の1行。side=ap：空港のピル＋ⓘ・共有／pl：探す欄＋ⓘ／sel：機体を選んだあと（‹ 戻る＋登録記号のピル＋共有）"""
    k = kind(side) if show_kind else ""
    if side == "ap":
        return f'<div class="trow">{k}{AP_PILL}<span class="sp"></span><span class="ic">{I(INFO)}</span><span class="ic">{I(SHARE)}</span></div>'
    if sel:
        return f'<div class="trow">{k}<span class="back">{I(LEFT)}戻る</span><span class="ap plr"><i>{sel}</i>{I(DOWN)}</span><span class="sp"></span><span class="ic">{I(SHARE)}</span></div>'
    return f'<div class="trow">{k}{SEARCH}<span class="ic">{I(INFO)}</span></div>'

def views(items, on):
    none = " none" if on is None else ""
    return f'<div class="vrow{none}"><div class="vs" role="tablist">' + "".join(f'<span class="{"on" if x == on else ""}">{x}</span>' for x in items) + f'</div><span class="pen" aria-label="見方を変える">{I(PEN)}</span></div>'

AP_VIEWS = ["案内板", "1日の山", "滑走路", "定時", "空の道すじ", "短冊", "撮る人"]
PL_VIEWS_1 = ["最近見た", "特別塗装機", "次に来る機体"]   # 案1
PL_VIEWS_2 = ["最近見た", "特別塗装機"]                 # 案2（おすすめ）

RUNWAY2 = f"""<div class="hero"><div class="t"><span>いまの運用</span><em>● 実際の機体から判定</em></div><h3>北風運用</h3>
<div class="rw"><div>着陸<br><b>34L</b><b>34R</b></div><div>離陸<br><b>05</b><b>34R</b></div></div>
<div style="margin-top:10px"><span style="display:inline-flex;align-items:center;gap:4px;height:44px;padding:0 14px;border-radius:999px;background:rgba(255,255,255,.1);font-size:14px;font-weight:800">ほかの向き{I(DOWN)}</span></div></div>
<div class="tiles"><div class="tile"><span>風</span><b>7<small>kt</small></b><em>340° から</em></div><div class="tile"><span>視程</span><b>10<small>km 以上</small></b><em>気象通報 15:00</em></div></div>
<div class="card mt"><div class="h"><b>地図と近くを飛ぶ機体</b><small>空港のまわり</small></div><div style="height:120px;border-radius:14px;background:linear-gradient(160deg,#E4EAF0,#D9E1EA)"></div></div>
<div class="card"><div class="h"><b>運用時間</b><small>羽田</small></div><p style="margin:0;font-size:15px;color:var(--ink2)"><b style="font-size:24px;font-weight:900;color:var(--ink)">24</b><small style="font-size:13px;color:var(--sub);margin-left:2px">時間</small>　深夜は使う滑走路が変わります</p></div>"""

# 機体の行（飛行中は緑の点。地上の機体は「いま飛んでいる」に入れない）
RECENT = [("JA339J", "JAL Jubilee Express", "JAL・B737-800", "#B4232A", "live", "JL 323 福岡へ"),
          ("JA01XJ", "A350 1号機（赤のロゴ）", "JAL・A350-900", "#B4232A", "pred", "15:40ごろ 羽田に着く")]
SP_FLY = [("JA05RK", "ジンベエジェット", "JTA・B737-800", "#0E7490", "live", "JTA 9 那覇へ"),
          ("JA228J", "J-AIR 創立30周年記念機", "J-AIR・E190", "#B4232A", "live", "JL 2205 松山へ")]
def rowpl(reg, nm, sub, col, kind_, line):
    tag = {"live": '<span class="tag live">● 飛行中</span>', "pred": '<span class="tag pred">予想</span>', "gray": '<span class="tag gray">地上</span>'}[kind_]
    return f'<li><span class="sw" style="background:{col}">{reg[2:]}</span><div class="tx"><b>{nm}</b><span><span class="reg">{reg}</span>・{sub}</span><span>{tag} {line}</span></div><span class="go">{I(CHEV)}</span></li>'

def sp_card(n=2):
    return (f'<div class="card"><div class="h"><b>いま飛んでいる特別塗装機</b><small>飛行中 17機</small></div><ul class="rows">{"".join(rowpl(*r) for r in SP_FLY[:n])}</ul>'
            f'<div style="margin-top:6px"><span class="pillbtn">特別塗装機をすべて見る {I(CHEV)}</span></div></div>')

def recent_card():
    return f'<div class="card"><div class="h"><b>最近見た機体</b><small>この端末で開いた順</small></div><ul class="rows">{"".join(rowpl(*r) for r in RECENT)}</ul></div>'

def wo_box():
    rows = [("ロサンゼルス", "LAX", st("s1", "地上待機中", "FAA"), "16時30分まで見込み"),
            ("ロンドン", "LHR", st("s3", "今日の欠航 1便"), "JAL・ANA の便の数")]
    lis = "".join(f'<li><div class="tx"><span class="nm">{n}<small>{c}</small></span><span class="wh">{p}<span>{x}</span></span></div><span class="go">{I(CHEV)}</span></li>' for n, c, p, x in rows)
    return (f'<div class="wo"><h4>行き先の海外の空港のいま<small>15:06 更新</small></h4><ul class="wol">{lis}</ul>'
            f'<p class="srcnote"><b>空港全体のようすです。運航の判断には使えません。</b>アメリカの空港は FAA（アメリカ連邦航空局）の発表、ほかの空港は JAL・ANA の今日の便の数（空港全体の数です。この便のことではありません）。</p></div>')

def build():
    # ---------- A1 空港側（滑走路）：上を1行に・鉛筆を右端に固定 ----------
    page("A1-v2", "A1 空港側（2版）", f"""<div class="pad">{TOP}{trow("ap")}{views(AP_VIEWS, "滑走路")}{RUNWAY2}</div>{TABBAR}""")
    # 比べる用：1版と同じ2段（帯の鉛筆だけ直した）
    two = f"""{M.kindrow("ap")}{M.APPICK}"""
    page("A1x-v2", "A1x 空港側 2段（比べる用）", f"""<div class="pad">{TOP}{two}{views(AP_VIEWS, "滑走路")}{RUNWAY2}</div>{TABBAR}""")

    # ---------- A1b 空港側（案内板）：便の行はピンの札だけ、便の数は欄の中だけ ----------
    board = f"""<div class="card"><div class="h" style="align-items:center"><b>これから出る便</b><span class="bdtabs"><span>到着</span><span class="on">出発</span></span></div>
<ul class="rows">
<li><span class="tmbig">15:30</span><div class="tx"><b>NH 247 福岡へ</b><span>B787-9・05 離陸（推定）</span></div></li>
<li><span class="tmbig">16:05</span><div class="tx"><b>JL 16 ロサンゼルスへ</b><span>B777-300ER・国際線</span><span class="l2">{st("s1", "地上待機中", "FAA")}</span></div></li>
<li><span class="tmbig">16:30</span><div class="tx"><b>JL 41 ロンドンへ</b><span>B777-300ER・国際線</span></div></li>
</ul>
<p class="stkey">{PIN}<span>ピンの札は行き先の空港全体のようすです（この便のことではありません）。便の数は下の欄にだけ出します。</span></p>
{wo_box()}</div>"""
    page("A1b-v2", "A1b 空港側 案内板（2版）", f"""<div class="pad">{TOP}{trow("ap")}{views(AP_VIEWS, "案内板")}{board}</div>{TABBAR}""")

    # ---------- A2 機体側のはじめ：見方は「最近見た」・特別塗装機は2行＋入口・飛んでいる機体だけ ----------
    a2 = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_2, "最近見た")}{recent_card()}{sp_card(2)}{FOOT_PL}</div>"""
    page("A2-v2", "A2 機体側 はじめ（2版）", a2 + TABBAR)

    a2e = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_2, "最近見た")}
<div class="card"><div class="h"><b>機体を1機ずつ追う</b></div><p class="note" style="margin-top:0;font-size:14px;color:var(--ink2)">上の欄に登録記号（例：JA339J）か便名（例：JL 323）を入れると、その機体の今日の便と、この先の便（予想）が出ます。開いた機体はここに残ります。</p>
<div class="chips" style="margin-top:10px"><span class="chip">羽田に来る機体 <small>12</small></span><span class="chip">乗った機体 <small>8</small></span></div></div>
{sp_card(2)}{FOOT_PL}</div>"""
    page("A2e-v2", "A2e 機体側 はじめ（最近なし・2版）", a2e + TABBAR)

    # ---------- A3 機体を選んだあと：帯の下線を外す・戻るは1つ ----------
    a3 = f"""<div class="pad">{TOP}{trow("pl", sel="JA339J")}{views(PL_VIEWS_2, None)}
<div class="card"><div class="h"><b>JAL Jubilee Express</b><small>B737-800</small></div>
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
    page("A3-v2", "A3 機体側 機体の1日（2版）", a3 + TABBAR)
    # 比べる用：上が2段のまま
    a3x = a3.replace(trow("pl", sel="JA339J"), f'{M.kindrow("pl")}<div class="pickrow"><span class="back">{I(LEFT)}戻る</span><span class="ap plr"><i>JA339J</i>B737-800<em>JAL</em>{I(DOWN)}</span></div>')
    page("A3x-v2", "A3x 機体の1日 2段（比べる用）", a3x + TABBAR)

    # ---------- A4 特別塗装機：「この先」は札＋区間を先に（切れない） ----------
    def sprow(reg, nm, sub, col, now, pred):
        return (f'<li><span class="sw" style="background:{col}">{reg[2:]}</span><div class="tx"><b>{nm}</b><span><span class="reg">{reg}</span>・{sub}</span>'
                f'<span><span class="tag live">● 飛行中</span> {now}</span><span><span class="tag pred">この先</span> {pred}</span></div><span class="go">{I(CHEV)}</span></li>')
    a4 = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_2, "特別塗装機")}
<div class="chips" style="margin-bottom:12px"><span class="chip dark">いま</span><span class="chip">この先</span><span class="chip">羽田に来る</span></div>
<div class="card"><div class="h"><b>いま飛んでいる</b><small>17機</small></div><ul class="rows">
{sprow("JA339J","JAL Jubilee Express","JAL・B737-800","#B4232A","JL 323 福岡へ","福岡→羽田 17:00ごろ")}
{sprow("JA05RK","ジンベエジェット","JTA・B737-800","#0E7490","JTA 9 那覇へ","那覇→石垣 18:40ごろ")}
{sprow("JA228J","J-AIR 創立30周年記念機","J-AIR・E190","#B4232A","JL 2205 松山へ","松山→伊丹 16:30ごろ")}
</ul><p class="note">「この先」は予想です。保証しません。地上にいる機体は「この先」に出します。</p></div>
<div class="card"><div class="h"><b>これから飛ぶ予定</b><small>航空会社の運航情報</small></div><ul class="rows">
<li><span class="tmbig">19:35</span><div class="tx"><b>★A350 1号機（赤のロゴ）</b><span>JL 25 羽田→香港・運航情報に記載</span></div></li></ul>
<p class="note">特別塗装機の一覧は航空会社の発表などをもとにそらメモがまとめたもの。運航情報は ODPT（正確・完全とは限りません）。</p></div>
</div>"""
    page("A4-v2", "A4 機体側 特別塗装機（2版）", a4 + TABBAR)

    # ---------- 撮る人 案2（おすすめに変更）：空港側にまとめる ----------
    nextrows = f"""<li><span class="tmbig">15:18</span><div class="tx"><b>JL 312 福岡から</b><span><span class="reg">JA737N</span>・34L 着陸</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:40</span><div class="tx"><b>★A350 1号機（赤のロゴ）</b><span><span class="reg">JA01XJ</span>・JL 318（推定）</span></div><span class="go">{I(CHEV)}</span></li>
<li><span class="tmbig">15:52</span><div class="tx"><b>NH 242 福岡から</b><span><span class="reg">JA894A</span>・34R 着陸</span></div><span class="go">{I(CHEV)}</span></li>"""
    q1 = f"""<div class="pad">{TOP}{trow("ap")}{views(AP_VIEWS, "撮る人")}
<div class="pickrow" style="margin-top:0;margin-bottom:12px"><span class="chip">第1ターミナル 展望デッキ {I(DOWN)}</span></div>
<div class="card"><div class="h"><b>次に来る機体</b><small>この3時間・来る順</small></div><ul class="rows next">{nextrows}</ul>
<p class="note">「推定」は機体の位置と予想から出したおおよその時刻です。<b>予想です。保証しません。</b></p></div>
<div class="card"><div class="h"><b>見に行くなら（北風運用）</b><small>日の入り 16:35</small></div><ul class="rows">
<li><div class="tx"><b>城南島海浜公園</b><span>34R の着陸がま上を通る</span></div><span class="go">{I(CHEV)}</span></li></ul></div>
<div class="chips mt"><span class="chip">撮影条件と天気</span><span class="chip">空港の傾向</span><span class="chip">管制の交信</span></div>
</div>"""
    page("Q1-v2", "Q1 案2 空港側 撮る人（2版）", q1 + TABBAR)

    q2 = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_2, "最近見た")}{recent_card()}
<div class="card" style="display:flex;align-items:center;gap:10px"><div style="flex:1"><b style="font-size:15px">撮影地から見える機体</b><p class="note" style="margin:2px 0 0">空港の「撮る人」にあります</p></div><span class="pillbtn">撮る人へ {I(CHEV)}</span></div>
{sp_card(2)}</div>"""
    page("Q2-v2", "Q2 案2 機体側 はじめ（2版）", q2 + TABBAR)

    # ---------- 撮る人 案1（比べる用）：撮影地は空港側の値をそのまま使う ----------
    p1 = f"""<div class="pad">{TOP}{trow("ap")}{views(AP_VIEWS, "撮る人")}
<div class="pickrow" style="margin-top:0;margin-bottom:12px"><span class="chip">第1ターミナル 展望デッキ {I(DOWN)}</span></div>
<div class="card"><div class="h"><b>見に行くなら（北風運用）</b><small>日の入り 16:35</small></div>
<ul class="rows">
<li><div class="tx"><b>城南島海浜公園</b><span>34R の着陸がま上を通る・順光は午前</span></div><span class="go">{I(CHEV)}</span></li>
<li><div class="tx"><b>浮島町公園</b><span>05 離陸の上昇が見える</span></div><span class="go">{I(CHEV)}</span></li></ul></div>
<div class="card mt" style="display:flex;align-items:center;gap:10px"><div style="flex:1"><b style="font-size:15px">次に来る機体は「機体」へ</b><p class="note" style="margin:2px 0 0">選んだ撮影地のまま開きます</p></div><span class="pillbtn">機体へ {I(CHEV)}</span></div>
</div>"""
    page("P1-v2", "P1 案1 空港側 撮る人（2版・比べる用）", p1 + TABBAR)
    p2 = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_1, "次に来る機体")}
<div class="linked"><div class="tx"><b>羽田・第1ターミナル 展望デッキ</b><span>空港の「撮る人」で選んだ撮影地</span></div><span class="pillbtn">変える</span></div>
<div class="card"><div class="h"><b>次に来る機体</b><small>この3時間・来る順</small></div>
<ul class="rows next">{nextrows}</ul>
<p class="note">「推定」は機体の位置と予想から出したおおよその時刻です。<b>予想です。保証しません。</b></p></div>
</div>"""
    page("P2-v2", "P2 案1 機体側 次に来る機体（2版・比べる用）", p2 + TABBAR)

    # ---------- C1 撮る人 案1・案2 の操作の数 ----------
    rows = [("撮影地を選んで、次に来る機体を見る", "4", "撮る人 → 撮影地 ▾ → 選ぶ → 機体へ", "3", "撮る人 → 撮影地 ▾ → 選ぶ（同じ画面に出る）"),
            ("2回目から（撮影地は覚えている）", "2", "撮る人 → 機体へ（または 機体 → 次に来る機体）", "1", "撮る人"),
            ("見ている途中で撮影地を変える", "4", "変える → 空港側へ戻る → 撮影地 ▾ → 選ぶ（そのあと機体へ でもう1回）", "2", "撮影地 ▾ → 選ぶ"),
            ("来る機体の1日（予想）を開く", "5", "上の4回 ＋ 行を押す", "4", "上の3回 ＋ 行を押す"),
            ("撮影地の見え方と次に来る機体を見比べる", "—", "空港と機体を行き来する", "0", "1画面にある")]
    tb = '<table class="cmp"><tr><th>したいこと</th><th>案1 分ける</th><th class="hl">案2 まとめる</th></tr>' + "".join(
        f'<tr><td>{a}</td><td><b class="n">{n1}<small>{"回" if n1 != "—" else ""}</small></b><small class="s">{s1}</small></td><td class="hl"><b class="n">{n2}<small>回</small></b><small class="s">{s2}</small></td></tr>' for a, n1, s1, n2, s2 in rows) + "</table>"
    c1 = f"""<div class="idx"><h1>撮る人の置き場所：操作の数</h1><p>運用タブを空港側の「滑走路」で開いた所から数えました（押す回数）。下のタブ帯の「運用」は数に入れていません。</p>
<div class="card">{tb}</div>
<h2>2版のおすすめ：案2（空港側にまとめる）</h2><p>撮る人に要るのは「どこで（撮影地）」と「何が来るか（次に来る機体）」を同時に見ること。今の本番の撮る人もこの2つが1画面にあります。案1 は2版で撮影地を空港側の値につなげ、2回選ばなくてよくしましたが、それでも行き来が1回増えます。機体側には「撮る人へ」の入口だけ置きます（Q2）。</p>
<p>案1 を選ぶ良さは、機体側に「次に来る機体」がまとまり、撮らない人の空港側が少し短くなることです。</p></div>"""
    page("C1-v2", "C1 撮る人 操作の数", c1)

    # ---------- V1 見方の設定（シートの切り替えも紺） ----------
    def oo(items):
        out = []
        for nm, sub, stt in items:
            tg = f'<span class="tg on">ON</span>' if stt == "on" else '<span class="tg off">OFF</span>'
            out.append(f'<li><span class="grip">≡</span><div class="tx"><b>{nm}</b><span>{sub}</span></div>{tg}</li>')
        return '<ul class="onoff">' + "".join(out) + "</ul>"
    ap_items = [("案内板", "出発・到着の便を案内板の形で", "on"), ("1日の山", "1時間ごとの便の数と遅れ", "on"), ("滑走路", "いまの運用と使う滑走路", "on"),
                ("定時", "便の定時の割合", "on"), ("空の道すじ", "全機の航跡を重ねる", "on"), ("短冊", "次の離着陸を1便1枚で", "off"), ("撮る人", "撮影地と次に来る機体", "on")]
    pl_items = [("最近見た", "この端末で開いた機体", "on"), ("特別塗装機", "いま飛んでいる・この先（予想）", "on")]
    v1 = f"""<div class="pad">{TOP}{trow("ap")}{views(AP_VIEWS, "滑走路")}{RUNWAY2}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>運用の見方</h2><button>完了</button></div>
<p class="sub">出す見方を ON にします。最後の1つは残ります。</p>
{kind("ap", "insheet")}
{oo(ap_items)}</div>"""
    page("V1-v2", "V1 見方の設定 空港（2版）", v1)
    v1b = f"""<div class="pad">{TOP}{trow("pl")}{views(PL_VIEWS_2, "最近見た")}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>運用の見方</h2><button>完了</button></div>
<p class="sub">出す見方を ON にします。最後の1つは残ります。</p>
{kind("pl", "insheet")}
{oo(pl_items)}
<div class="grp">機体の側ごと隠す <small>運用は空港だけになります</small></div>
<ul class="onoff"><li><div class="tx"><b>「機体」を出す</b><span>OFF にすると運用タブで特別塗装機と機体の1日が見られなくなります</span></div><span class="tg on">ON</span></li></ul></div>"""
    page("V1b-v2", "V1b 見方の設定 機体（2版）", v1b)

    # ---------- V3 「機体」を出す OFF のとき：運用タブ ----------
    v3 = f"""<div class="pad">{TOP}{trow("ap", show_kind=False)}{views(AP_VIEWS, "滑走路")}{RUNWAY2}</div>{TABBAR}"""
    page("V3-v2", "V3 「機体」を出す OFF のときの運用タブ", v3)
    # ---------- V1c OFF のときの鉛筆のシート（戻し方） ----------
    v1c = f"""<div class="pad">{TOP}{trow("ap", show_kind=False)}{views(AP_VIEWS, "滑走路")}{RUNWAY2}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>運用の見方</h2><button>完了</button></div>
<p class="sub">出す見方を ON にします。最後の1つは残ります。</p>
<div class="kind insheet"><span>空港</span><span class="on">機体<em>隠し中</em></span></div>
<ul class="onoff"><li><div class="tx"><b>「機体」を出す</b><span>ON にすると運用タブの上に「空港｜機体」が戻ります</span></div><span class="tg off">OFF</span></li></ul>
<div class="offnote">{I(INFO)}<span>隠している間は、運用タブで特別塗装機と機体の1日が見られません。シートの「機体」のピルは残るので、ここか、マイページの「表示の編集」の同じ行で戻せます。</span></div></div>"""
    page("V1c-v2", "V1c 「機体」を出す OFF のときのシート（戻し方）", v1c)

    # ---------- V2 表示の編集：7行すべてを V1 と同じ順で ----------
    v2 = f"""<div class="full"><div class="top"><span class="back">{I(LEFT)}戻る</span><h2>表示の編集</h2><span class="pillbtn" style="background:var(--navy);color:#fff">完了</span></div>
<div class="pills"><span>タブ</span><span class="on">見方</span><span>ホームに出すもの</span></div>
<div class="grp">図鑑 <small>3つ中3つ</small></div>
<div class="grp">フライト <small>2つ中2つ</small></div>
<div class="grp">運用（空港） <small>7つ中6つ</small></div>
{oo(ap_items)}
<div class="grp">運用（機体） <small>2つ中2つ</small></div>
<ul class="onoff"><li><div class="tx"><b>「機体」を出す</b><span>OFF で運用は空港だけ（特別塗装機と機体の1日は見られません）</span></div><span class="tg on">ON</span></li></ul>
{oo(pl_items)}
<div class="grp">修行 <small>3つ中3つ</small></div>
</div>"""
    page("V2-v2", "V2 表示の編集（2版）", v2)

    # ---------- 一覧（2版を先に、1版はあと） ----------
    L2 = [("2版：おすすめの形（上は1行）", [("A1-v2", "空港側（滑走路）", "上を1行に。鉛筆は右端に固定"), ("A1b-v2", "空港側（案内板）", "便の行はピンの札だけ・便の数は欄の中"),
                           ("A2-v2", "機体側のはじめ", "最近見た＋特別塗装機は2行と入口"), ("A2e-v2", "機体側のはじめ（最近なし）", "例はどの画面も同じ"),
                           ("A3-v2", "機体を選んだあと", "帯の下線を外す・戻るは1つ"), ("A4-v2", "機体側・特別塗装機", "飛行中と地上を分けて数える")]),
          ("2版：撮る人（案2をおすすめに変えた）", [("Q1-v2", "案2 空港側・撮る人", "撮影地と次に来る機体が1画面"), ("Q2-v2", "案2 機体側のはじめ", "撮る人への入口だけ"),
                           ("C1-v2", "案1・案2 の操作の数", "押す回数を並べた"), ("P1-v2", "案1 空港側・撮る人（比べる用）", "撮影地を選ぶ"), ("P2-v2", "案1 次に来る機体（比べる用）", "撮影地は空港側の値をそのまま")]),
          ("2版：見方の設定", [("V1-v2", "鉛筆のシート（空港）", "切り替えは上と同じ紺"), ("V1b-v2", "鉛筆のシート（機体）", "「機体」を出す"), ("V3-v2", "「機体」を出す OFF の運用タブ", "切り替えが消える"),
                           ("V1c-v2", "OFF のときのシート", "戻し方"), ("V2-v2", "表示の編集", "7行すべてを同じ順で")]),
          ("2版：上の段の比べ（2段のまま）", [("A1x-v2", "空港側 2段", "1行より約60px 下がる"), ("A3x-v2", "機体の1日 2段", "667 で予想の点が帯の下")])]
    L1 = [("1版（11/15）", [("A1", "空港側（滑走路）", ""), ("A1b", "空港側（案内板）", ""), ("A2", "機体側のはじめ", ""), ("A2e", "はじめ（最近なし）", ""),
                         ("A3", "機体を選んだあと", ""), ("A4", "特別塗装機", ""), ("P1", "案1 空港側", ""), ("P2", "案1 機体側", ""), ("Q1", "案2 空港側", ""), ("Q2", "案2 機体側", ""),
                         ("V1", "シート（空港）", ""), ("V1b", "シート（機体）", ""), ("V2", "表示の編集", ""), ("00", "今の並びの整理", "本番の写真と振り分け")])]
    body = '<div class="idx"><h1>運用タブを「空港」と「機体」に</h1><p>design/ops-split 2版（11/16）。改善担当 review-1 を受けて直しました。画面案だけで、アプリには入れません。下のタブ帯は変えません。</p>'
    for h, items in L2 + L1:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}{f"<small>{s}</small>" if s else ""}</span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "運用を空港と機体に", body + "</div>")

if __name__ == "__main__":
    build(); print("ok")
