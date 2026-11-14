# -*- coding: utf-8 -*-
# 運用予想を見やすく 2版（案A だけ直す。B・C は1版のまま）。改善担当 review-1 の必ず直す3つ＋指摘5〜7・小さいもの。
# 1版の make.py の CSS と部品（地図など）を読み込み、A1〜A6 を *-v2.html に書き出す。PNG は shoot_v2.py で撮る。
import os, html
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
_src = open(os.path.join(HERE, "make.py"), encoding="utf-8").read().split("S = {}")[0]
exec(_src)  # CSS・page・top・tabbar・mapsvg・BACK/CHEV/DOWN・FLOWN など

CSS2 = r"""
/* 2版：確からしさの横に回数（小さく薄く） */
.cf .n{font-weight:600;color:var(--sub);margin-left:2px}
.tl .tag{white-space:nowrap}
.tl .tag .cf{flex-direction:column;align-items:flex-end;gap:1px}
/* 2版：運航情報は点でなく、白地に縁のピル（3段の確からしさとは別の物差し） */
.src{display:inline-flex;align-items:center;height:24px;padding:0 9px;border-radius:999px;background:var(--card);box-shadow:inset 0 0 0 1.5px #9AA3AE;font-size:13px;font-weight:800;color:var(--ink2);white-space:nowrap}
/* 2版：飛んだ便をたたんだ1行 */
.fold{display:grid!important;grid-template-columns:62px 22px 1fr 24px!important;align-items:center!important;min-height:52px}
.fold .tm b{font-size:16px!important;color:var(--mute)}
.fold .tx b{font-size:15px!important;color:var(--ink2)}
.fold .tx small{margin-top:0!important}
.fold svg{width:20px;height:20px;stroke:var(--mute);fill:none;stroke-width:2.2}
.tl li.fold .dot::before{top:-6px}
/* 2版：明日の区切り・出さない便のメモ */
.tl li.day{padding:12px 0 2px 92px}
.tl li.skip{display:grid;grid-template-columns:62px 22px 1fr;padding:6px 0}
.tl li.skip .dot::before{border-left:3px dashed #B7BFC9}
.tl li.skip .tx{font-size:13px;color:var(--sub);line-height:1.5}
.tl li.skip .tx s{color:var(--sub)}
.mini li.skip{grid-template-columns:56px 18px 1fr;padding:4px 0}
.mini li.skip .tx{font-size:13px;color:var(--sub)}
.mini li.day{display:block;padding:8px 0 0 80px;font-size:13px;font-weight:800;color:var(--mute)}
.mini li.day::before{content:"";position:absolute;left:69px;top:0;bottom:0;border-left:2.5px dashed #B7BFC9}
.mini .tx .cf{margin-top:2px}
/* 2版：出典（ODPT）と断り書き */
.odpt{font-size:13px;line-height:1.65;color:var(--mute);margin:10px 2px 0}
.odpt b{color:var(--ink2);font-weight:700}
/* 2版：タブ帯の地を濃く（下の字が透けない） */
.tabbar{background:rgba(255,255,255,.985);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}
.fadebot{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;height:104px;background:linear-gradient(to bottom,rgba(238,241,245,0),var(--bg) 55%);z-index:4;pointer-events:none}
.live.now{color:var(--now);background:var(--now-wash)}
.ruleset{list-style:none;margin:10px 0 0;padding:10px 12px;background:var(--pred-wash);border-radius:14px;font-size:13px;line-height:1.7;color:var(--ink2)}
.ruleset li{display:grid;grid-template-columns:20px 1fr;gap:4px}
.ruleset li i{font-style:normal;font-weight:900;color:var(--hero)}
.lv3 .src{justify-self:start}
.lv3 h3{font-size:14px;font-weight:900;margin:14px 0 2px;color:var(--ink)}
.sheet{max-height:820px;overflow:hidden}
"""
def P(title, body): return page(title, body, CSS2)

ODPT = '<p class="odpt">運航情報の出典：公共交通オープンデータセンター（正確・完全とは限りません。表示について航空会社へ直接問い合わせないでください）</p>'
ODPT_S = '<p class="odpt" style="margin-top:8px">運航情報の出典：公共交通オープンデータセンター（正確・完全とは限りません。航空会社へ直接問い合わせないでください）</p>'
FOOT2 = ('<p class="note">飛んだ便は機体の位置の記録（adsb.lol）から。予想は、この機体が前の記録でいまの便のあとに飛んだ便から出し、'
         '機体の入れ替えで違うことがあります。<b style="color:var(--ink2)">予想です。保証しません。</b></p>')

def cf2(level, n=None):
    """level: 'lv'（運航情報）／3／2／1。n は（見た回数, そのうち続いた回数）"""
    if level == "lv": return '<span class="src">運航情報</span>'
    w = {3: "高い", 2: "中くらい", 1: "低い"}[level]
    cnt = f'<span class="n">{n[0]}回中{n[1]}回</span>' if n else ""
    return f'<span class="cf c{level}"><span><span class="d"><i></i><i></i><i></i></span> {w}</span>{cnt}</span>'

# 見本（1版と同じ JA339J・14時50分の場面）。回数を足した。高いは5回以上だけ
NOW2 = ("14:18", "発", "JL258", "広島 → 羽田", "着く 15:24ごろ（推定）")
PRED2 = [("16:15", "JL147", "羽田 → 青森", "lv", None), ("18:35", "JL148", "青森 → 羽田", 3, (12, 11)), ("20:30", "JL599", "羽田 → 新千歳", 2, (10, 7))]
TMR2 = [("07:30", "JL502", "新千歳 → 羽田", 1, (5, 2))]

def prow(t, f, rt, lv, n):
    return f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span></div><div class="tag">{cf2(lv, n)}</div></li>'

def fold_row():
    return (f'<li class="fold"><div class="tm"><b>07:40</b><small>〜13:14</small></div><div class="dot"><i></i></div>'
            f'<div class="tx"><b>今日飛んだ 3便</b><small>JL141・JL142・JL259</small></div>{DOWN}</li>')

def now_row():
    t, e, f, rt, s = NOW2
    return f'<li class="now"><div class="tm"><b>{t}</b><small>{e}</small></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b><span>{rt}</span><small>{s}</small></div><div class="tag">飛行中</div></li>'

EDGE = '<li class="edge"><b>ここから予想</b><small>予想です。保証しません</small></li>'

def tl2(fold=True, pred=True):
    r = [fold_row() if fold else "", now_row()]
    if pred:
        r.append(EDGE)
        r += [prow(*p) for p in PRED2]
        r.append('<li class="day">明日 11月14日（土）</li>')
        r += [prow(*p) for p in TMR2]
    return '<ul class="tl">' + "".join(r) + '</ul>'

def mini2(n=2):
    t, e, f, rt, s = NOW2
    r = [f'<li class="now"><div class="tm"><b>{t}</b><small>{e}</small></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b> {rt}<small>{s}</small></div><div class="tag">飛行中</div></li>',
         '<li class="edge"><b>ここから予想</b><small>予想です。保証しません</small></li>']
    for t, f, rt, lv, c in PRED2[:n]:
        r.append(f'<li class="p"><div class="tm"><b>{t}<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>{f}</b> {rt}<small>{cf2(lv, c)}</small></div><div></div></li>')
    return '<ul class="mini">' + "".join(r) + '</ul>'

def plane_card2():
    return ('<div class="card"><div class="plane"><span><b>JA339J</b><small>B738・★JAL Jubilee Express</small></span>'
            '<span class="live now">飛行中</span></div></div>')

def map_card():
    return (f'<div class="card"><div class="opsh"><b>今日の地図</b></div><div class="map" style="margin-top:6px">{mapsvg(h=170)}</div>'
            '<div class="legend"><span><i></i>飛んだ</span><span><i class="n"></i>いま</span><span><i class="p"></i>予想</span></div></div>')

S2 = {}

S2["A1"] = ("案A 機体の1日（2版）", "飛んだ便は1行にたたみ、開いたときに「いま」と予想が見える。地図は予想の下へ。確からしさに回数、運航情報は縁のピル",
  P("案A 機体の1日 2版", f'''<div class="pad">{top("機体の1日")}
    <div class="search"><input value="JA339J" aria-label="登録記号"><button class="btn1">探す</button></div>
    {plane_card2()}
    <div class="sec"><b>今日</b><span>11月13日（金）</span></div>
    {tl2()}
    <div class="row2"><button class="pillbtn w">確からしさとは</button><button class="pillbtn line">近づいたら知らせる</button></div>
    {map_card()}
    {FOOT2}{ODPT}</div>'''))

S2["A2"] = ("案A 運用の特別塗装機（2版）", "小さい時間の線。「14:18 発」、予想は2便まで。回数と運航情報のピル、出典を足した",
  P("案A 運用の特別塗装機 2版", f'''<div class="pad" style="padding-top:20px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★FLYING HONU（緑）<small>ANA・NH184（JA382A）</small></div><div class="wh">飛行中・高度 30,400ft</div><button class="pillbtn">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2.2"')}</button></li>
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL258（JA339J）</small></div><div class="wh">広島から羽田へ・高度 24,000ft</div>
        <button class="pillbtn dark">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:#fff;fill:none;stroke-width:2.2;transform:rotate(180deg)"')}</button>
        {mini2(2)}
        <div class="minifoot"><small>あと2便の予想</small><button class="pillbtn line">機体の1日 ›</button></div>{ODPT_S}</li>
      <li><div class="nm">★結ジンベエ<small>JTA・JTA49（JA07RK）</small></div><div class="wh">飛行中・高度 32,000ft</div><button class="pillbtn">この先の便（予想）{DOWN.replace('<svg', '<svg style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2.2"')}</button></li>
    </ul></div></div><div class="fadebot"></div>{tabbar()}'''))

S2["A3"] = ("案A 撮る人のくわしく（2版）", "着陸の滑走路にも（推定）。この機体の運用（予想）は同じ部品で、回数・運航情報のピル・出典",
  P("案A 撮る人のくわしく 2版", f'''<div class="pad">{top("JL258")}
    <div class="card"><small style="font-size:13px;color:var(--mute)">着陸</small><div style="display:flex;align-items:baseline;gap:8px"><b style="font-size:34px;font-weight:900">15:24</b><small style="font-size:13px;color:var(--sub)">ごろ（推定）</small><span style="margin-left:auto;font-size:15px;font-weight:800">34L か 34R<small style="font-size:13px;color:var(--sub);font-weight:600">（推定）</small></span></div>
      <div style="font-size:14px;color:var(--ink2);margin-top:4px">広島 → 羽田・B738・高度 24,000ft・空港まで約180km</div></div>
    <div class="card"><div><small style="font-size:13px;color:var(--mute)">この機体の運用（予想）</small><b style="display:block;font-size:18px;font-weight:900">JA339J <span style="font-size:13px;color:var(--mute);font-weight:600">★JAL Jubilee Express</span></b></div>
      {mini2(3)}
      <div class="row2"><button class="pillbtn line">機体の1日 ›</button><button class="pillbtn">確からしさとは</button></div>{ODPT_S}</div>
    <div class="card" style="opacity:.55"><small style="font-size:13px;color:var(--mute)">どこから撮る</small><div style="font-size:15px;font-weight:800;margin-top:4px">城南島海浜公園・浮島町公園 …</div></div>
    </div>'''))

S2["A4"] = ("案A 特別塗装機のくわしく（2版）", "今日の足あとは飛んだ便を1行にたたみ、開いたときに「この先（予想）」の1便目まで見える",
  P("案A 特別塗装機のくわしく 2版", f'''<div class="pad">{top("JAL Jubilee Express", "特別塗装機")}
    <div class="hero"><small>JAL・JA339J</small><div class="nm">JAL Jubilee Express</div><div class="rt">HIJ<i>→</i>HND<span>JL258</span></div>
      <div class="tiles"><div><span>着く（推定）</span><b>15:24</b></div><div><span>時刻表</span><b>15:20</b></div><div><span>高さ</span><b>24,000<small>ft</small></b></div></div></div>
    <div class="sec" style="margin-top:16px"><b>今日の足あと</b><span>見えた記録から</span></div>
    {tl2(pred=False)}
    <div class="sec" style="margin-top:16px"><b>この先（予想）</b><span>予想です。保証しません</span></div>
    <ul class="tl">{"".join(prow(*p) for p in PRED2)}<li class="day">明日 11月14日（土）</li>{"".join(prow(*p) for p in TMR2)}</ul>
    <div class="row2"><button class="pillbtn line">機体の1日 ›</button><button class="pillbtn w">確からしさとは</button></div>
    {ODPT}</div>'''))

S2["A5"] = ("案A 確からしさとは（2版）", "3段の決め方に回数を足し、運航情報は別の見出しに分けた。出典と断り書きも",
  P("案A 確からしさとは 2版", f'''<div class="pad">{top("機体の1日")}{plane_card2()}</div><div class="dim"></div>
    <div class="sheet"><div class="grab"></div><h2>確からしさ</h2>
    <p>この機体が前の記録で、いまの便のあとに同じ便を飛んだ割合で3段に分けます。<b>3回以上見た便だけ</b>出し、横に回数を書きます。<b>予想です。保証しません。</b></p>
    <ul class="lv3">
      <li>{cf2(3, (12, 11))}<div class="ex"><b>8割以上</b>の日にこの便が続いた。<b>5回以上</b>見た便だけ（3回中3回は「中くらい」）</div></li>
      <li>{cf2(2, (10, 7))}<div class="ex"><b>6〜8割</b>の日に続いた。または8割以上でも見たのが5回より少ない</div></li>
      <li>{cf2(1, (5, 2))}<div class="ex"><b>4〜6割</b>の日に続いた。4割より少ない便は出しません</div></li></ul>
    <ul class="lv3"><li><h3>航空会社の運航情報にある便</h3>{cf2("lv")}<div class="ex">運航情報に「この塗装機で運航」とある便。記録からの予想とは別の物差しで、機体の入れ替えで変わることがあります</div></li></ul>
    {ODPT_S}
    <div class="row2" style="justify-content:flex-end"><button class="pillbtn dark">閉じる</button></div></div>'''))

A6_BASE = ('<li class="now" style="opacity:.9"><div class="tm"><b style="color:var(--ink2)">19:36</b><small>着いた</small></div><div class="dot"><i style="background:#9CA3AF"></i></div>'
           '<div class="tx"><b>JL148</b> 青森 → 羽田<small>記録に入っている最後の便</small></div><div></div></li>')
A6_MINI = ('<ul class="mini">' + A6_BASE +
           '<li class="edge"><b>ここから予想</b><small>予想です。保証しません</small></li>'
           '<li class="skip"><div></div><div class="dot"></div><div class="tx">20:30 JL599 羽田 → 新千歳は、いま飛んでいるので予想に出しません</div></li>'
           '<li class="day">明日 11月14日（土）</li>'
           f'<li class="p"><div class="tm"><b>07:30<em>ごろ</em></b></div><div class="dot"><i></i></div><div class="tx"><b>JL502</b> 新千歳 → 羽田<small>{cf2(1, (5, 2))}</small></div><div></div></li></ul>')

S2["A6"] = ("案A 予想が出ないとき（2版）", "過ぎた便・いまの便より前の便は予想に出さない。JL148 のあと、いま飛ぶ JL599 は出さず、明日の JL502 から",
  P("案A 予想が出ないとき 2版", f'''<div class="pad" style="padding-top:20px;padding-bottom:140px">
    <div class="card"><div class="opsh"><b>いま飛んでいる特別塗装機</b><span>10機</span></div>
    <ul class="spl">
      <li><div class="nm">★JAL Jubilee Express<small>JAL・JL599（JA339J）</small></div><div class="wh">羽田の近く・高度 2,400ft・20:30 発</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        {A6_MINI}
        <div class="warn"><span>!</span><span><b>いま飛んでいる JL599 が記録に入るまで</b>、JL148 からの予想を出しています。</span></div>
        <ul class="ruleset"><li><i>1</i><span>出発の時刻が過ぎた便は、予想に出しません</span></li><li><i>2</i><span>いま飛んでいる便と、それより前の便は、運航情報にあっても出しません</span></li></ul>
        {ODPT_S}</li>
      <li><div class="nm">★FDA シルバー（10号機）<small>FDA・FDA314（JA10FJ）</small></div><div class="wh">伊丹の近く・高度 17,600ft</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div class="warn"><span>…</span><span>この先の便は、<b>まだ記録が足りず予想できません</b>（同じ便を3回見ると出ます）</span></div></li>
      <li><div class="nm">★さくらジンベエ<small>JTA（JA06RK）</small></div><div class="wh">今日はまだ見えていません</div>
        <button class="pillbtn dark">この先の便（予想）</button>
        <div class="warn"><span>…</span><span><b>今日この機体はまだ見えていません</b>。見えたら、そのあとの便を予想します</span></div></li>
    </ul></div></div><div class="fadebot"></div>{tabbar()}'''))

for k, (title, desc, h) in S2.items():
    open(os.path.join(OUT, f"{k}-v2.html"), "w", encoding="utf-8").write(h)

# ---- 一覧ページ（2版を上に、1版はそのまま下に） ----
V1 = {"00a": ("今：機体の1日", "本番で撮った JA339J"), "00b": ("今：運用の特別塗装機", "この先の便を開いたところ"),
      "00c": ("今：これから飛ぶ予定", "運航情報の予定"), "00d": ("今：特別塗装機のくわしく", "JA339J を開いたところ"),
      "A1": ("案A 機体の1日（1版）", ""), "A2": ("案A 運用の特別塗装機（1版）", ""), "A3": ("案A 撮る人のくわしく（1版）", ""),
      "A4": ("案A 特別塗装機のくわしく（1版）", ""), "A5": ("案A 確からしさとは（1版）", ""), "A6": ("案A 予想が出ないとき（1版）", ""),
      "B1": ("案B 機体の1日", "次の1便を大きく（1版のまま）"), "B2": ("案B 運用の特別塗装機", "1版のまま"),
      "C1": ("案C 機体の1日", "1日の帯（1版のまま）"), "C2": ("案C 運用の特別塗装機", "1版のまま")}
def card(href, png, t, d):
    return (f'<a href="{href}" style="display:grid;grid-template-columns:96px 1fr;gap:12px;align-items:center;text-decoration:none;color:inherit;background:#fff;border-radius:20px;box-shadow:var(--sh);padding:10px;margin-bottom:10px">'
            f'<img src="{png}" alt="" style="width:96px;border-radius:12px;display:block"><span><b style="display:block;font-size:15px">{html.escape(t)}</b><small style="font-size:13px;color:var(--mute);line-height:1.6">{html.escape(d)}</small></span></a>')
H = lambda s: f'<h2 style="font-size:17px;font-weight:900;margin:26px 4px 10px">{s}</h2>'
cards = H("2版 案A 時間の線（review-1 を直した）") + "".join(card(f"{k}-v2.html", f"png/{k}-v2.png", f"{k}　{t}", d) for k, (t, d, _) in S2.items())
for g, ks in [("今の画面（本番で撮った）", ["00a", "00b", "00c", "00d"]), ("案B 次の1便を大きく（1版のまま）", ["B1", "B2"]),
              ("案C 1日の帯（1版のまま）", ["C1", "C2"]), ("1版 案A（比べる用）", ["A1", "A2", "A3", "A4", "A5", "A6"])]:
    cards += H(g) + "".join(card(f"{k}.html", f"png/{k}.png", f"{k}　{V1[k][0]}", V1[k][1]) for k in ks)
idx = page("運用予想を見やすく 2版", f'''<div class="pad" style="padding-bottom:40px"><h1 style="font-size:22px;font-weight:900;margin:12px 4px 4px">運用予想を見やすく</h1>
  <p style="font-size:14px;color:var(--mute);margin:0 4px">2版（11/14）。ブランチ design/rotation-view。アプリには入れていません。案A だけ直し、B・C は1版のまま。見本は本番で見た JA339J の今日の便を 14時50分の場面にしたもの。</p>
  <div class="warn" style="margin-top:12px"><span>!</span><span>2版で直したこと：<b>過ぎた便・いまの便より前の便は予想に出さない（A6）／飛んだ便を1行にたたみ、開いたときに予想が見える（A1・A4）／運航情報に出典と断り書き、確からしさに回数</b>。運航情報は縁のピル、言葉は「予想」にそろえ、「推定」は着く時刻と滑走路だけ。「14:18 発」。</span></div>{cards}</div>''', CSS2)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)
print("ok", len(S2))
