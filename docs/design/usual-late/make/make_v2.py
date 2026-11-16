# -*- coding: utf-8 -*-
# 「いつもより○分遅い（推定）」の見せ方 2版（改善担当 review-1 の必ず直す3つ＋指摘4〜10）。
# make.py の部品（CSS・tabbar・page など）を読み込み、*-v2.html を ../ に書き出す。PNG は shoot_v2.py で撮る。
# 1版からの主な変更：
#  1 時刻表にない便の札は橙をやめて灰色の点線（橙と赤は航空会社が出した遅れだけ）。言葉はどこでも「いつもより」から
#  2 札に「（推定）」（小さく薄いグレー）
#  3 大きな時刻と札の箱の中に「推定・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）」の1行。
#    ホームのシートは本番の位置（上の端 844＝495px・667＝318px）で描く
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
from make import WAVE, INFO, WARN, tabbar

CSS2 = r"""
/* 2版：時刻表にない便の札は灰色の点線＋波の印＋（推定）。色で「航空会社の遅れ」と分ける */
.u2{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:3px 10px 3px 8px;font-size:13px;font-weight:800;line-height:1.35;white-space:nowrap;border:1.5px dashed #9AA1AC;color:#374151;background:#fff}
.u2 svg{flex:none;width:14px;height:14px;stroke:#6B7280;fill:none;stroke-width:2;stroke-linecap:round}
.u2 small{font-size:13px;font-weight:600;color:var(--sub)}
.u2.big{font-size:15px;padding:4px 12px 4px 10px}
.tag.g2{background:#EEF0F3;color:var(--ink2)}
.bdseq .fl i.g2{color:var(--ink2);background:#EEF0F3}
/* ホームのシート：本番の位置（上の端＝画面の高さ−349px） */
.mapv{height:calc(100vh - 327px);min-height:340px;background:linear-gradient(180deg,#E9EDF1,#E3E8EE);position:relative;overflow:hidden}
.mapv svg{position:absolute;inset:0;width:100%;height:100%}
.hs2{position:relative;margin-top:-22px;background:#EEF1F5;border-radius:26px 26px 0 0;padding:10px 16px 120px;box-shadow:0 -10px 24px -18px rgba(15,23,42,.35)}
.hs2 .grab{width:40px;height:5px;border-radius:9px;background:#C9CFD7;margin:0 auto 10px}
.r2{padding:4px 16px 12px;border-radius:18px;background:var(--card);box-shadow:var(--sh);font-size:14px;line-height:1.5}
.r2 .rh{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:44px}
.r2 .rh b{font-size:17px;font-weight:800}
.r2 .rh span{flex:1;font-size:15px;color:var(--ink2)}
.r2 .rh button{border:0;background:none;color:var(--mute);font-weight:700;font-size:14px;min-height:44px;padding:0 4px;text-decoration:underline}
.r2 .co{display:block;color:var(--mute);font-size:13px}
.e2{margin-top:8px;background:#F7F8FA;border-radius:16px;padding:10px 14px 10px}
.e2 .k{font-size:13px;color:var(--mute);font-weight:700}
.e2 .k em{font-style:normal;color:var(--ok);font-weight:800;margin-right:6px}
.e2 .row{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px}
.e2 .t{font-size:32px;font-weight:900;font-variant-numeric:tabular-nums;line-height:1.15}
.e2 .t small{font-size:15px;font-weight:700;color:var(--sub);margin-left:2px}
.e2 .us-n{font-size:14px;color:var(--ink2)}
.e2 .us-n b{font-weight:800;font-variant-numeric:tabular-nums}
.e2 .bd{margin-top:4px}
.e2 .src{display:flex;gap:5px;align-items:flex-start;font-size:13px;line-height:1.55;color:var(--ink2);margin-top:6px;font-weight:700}
.e2 .src svg{flex:none;width:14px;height:14px;stroke:#6B7280;fill:none;stroke-width:2;stroke-linecap:round;margin-top:2px}
.e2 .src span{font-weight:500;color:var(--mute)}
.e2 .none{font-size:20px;font-weight:800;color:var(--ink2);margin:2px 0}
.more{display:flex;align-items:center;min-height:44px;font-size:13px;font-weight:700;color:var(--mute);text-decoration:underline}
.r2 .rmeta{display:flex;justify-content:space-between;font-size:13px;color:var(--mute);margin-top:8px}
.r2 .rbar{margin-top:6px}
.nb{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.65;color:var(--ink2);background:#F4F6F9;border-radius:14px;padding:9px 12px;margin-top:8px}
.nb svg{flex:none;width:16px;height:16px;stroke:var(--ink2);fill:none;stroke-width:2;margin-top:2px}
.nb b{font-weight:800}
.nb small{display:block;color:var(--mute);font-size:13px}
/* 運用タブの上（PR #112 の形） */
.hd{display:flex;justify-content:space-between;align-items:center;height:52px}
.hd b{display:flex;align-items:center;gap:8px;font-size:20px;font-weight:800;letter-spacing:.04em}
.hd b svg{width:24px;height:24px;stroke:var(--ink);fill:none;stroke-width:2}
.hd span{height:40px;display:inline-flex;align-items:center;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:13px;font-weight:800}
.seg2{display:flex;background:#E3E7EC;border-radius:999px;padding:4px;margin-top:8px}
.seg2 span{flex:1;height:36px;display:flex;align-items:center;justify-content:center;border-radius:999px;font-size:14px;font-weight:800;color:var(--mute)}
.seg2 span.on{background:#fff;color:var(--ink);box-shadow:0 2px 6px -2px rgba(15,23,42,.25)}
.or2{display:flex;align-items:center;gap:8px;margin-top:12px}
.or2 .sw span{height:40px;padding:0 12px}
.or2 .ap{height:44px;font-size:17px}
.or2 .ic{margin-left:auto;display:flex;gap:8px}
.or2 .ic i{width:44px;height:44px;border-radius:50%;background:var(--card);box-shadow:var(--sh);display:flex;align-items:center;justify-content:center}
.or2 .ic svg{width:20px;height:20px;stroke:var(--ink2);fill:none;stroke-width:2}
.vw2{display:flex;align-items:center;margin:14px 0 10px}
.vw2 .s{display:flex;gap:20px;flex:1;overflow:hidden;white-space:nowrap;font-size:15px;font-weight:800;color:var(--mute);padding:0 4px}
.vw2 .s span{padding-bottom:6px}
.vw2 .s span.on{color:var(--ink);box-shadow:inset 0 -3px 0 var(--ink)}
.vw2 .pen{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center}
.vw2 .pen svg{width:18px;height:18px;stroke:var(--mute);fill:none;stroke-width:2}
.key2{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;font-size:13px;line-height:1.6;color:var(--ink2);margin:14px 0 0}
.key2 b{font-weight:800}
.key2 .u2{padding:1px 8px 1px 6px}
/* 便のくわしく */
.lc{display:block;margin-top:10px;background:#F7F8FA;border-radius:18px;padding:12px 14px}
.lc>small{display:block;font-size:13px;color:var(--mute);font-weight:700}
.lc .row{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 12px}
.lc .t{font-size:30px;font-weight:900;font-variant-numeric:tabular-nums}
.lc .t small{font-size:15px;font-weight:700;color:var(--sub);margin-left:2px}
.lc .us-n{font-size:14px;color:var(--ink2)}
.lc .src{display:flex;gap:5px;font-size:13px;line-height:1.55;color:var(--ink2);margin-top:6px;font-weight:700}
.lc .src svg{flex:none;width:14px;height:14px;stroke:#6B7280;fill:none;stroke-width:2;margin-top:2px}
.lc .src span{font-weight:500;color:var(--mute)}
"""
M.CSS = M.CSS + CSS2

PIN = '<svg viewBox="0 0 24 24"><path d="M3 12l18-8-6 18-3-7z"/></svg>'
I_INFO = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>'
I_SHARE = '<svg viewBox="0 0 24 24"><path d="M12 3v12M7 8l5-5 5 5M5 13v7h14v-7"/></svg>'
I_PEN = '<svg viewBox="0 0 24 24"><path d="M4 20l4-1 11-11-3-3L5 16z"/></svg>'

def u2(text, big=False):
    return f'<span class="u2{" big" if big else ""}">{WAVE}{text}<small>（推定）</small></span>'

SRC = f'<p class="src">{INFO}<span><b style="color:var(--ink2);font-weight:700">推定</b>・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）</span></p>'
MORE = '<a class="more">出典と注意 ›</a>'

def home2(card, label="HND 羽田"):
    mp = ('<svg viewBox="0 0 390 420" preserveAspectRatio="xMidYMid slice"><path d="M0 300 C80 260 140 330 220 290 S340 250 390 270 L390 420 L0 420Z" fill="#DCE3EA"/>'
          '<path d="M60 380 L250 90" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/><path d="M150 360 L330 130" stroke="#7B2D5B" stroke-width="7" stroke-linecap="round" opacity=".8"/>'
          '<circle cx="190" cy="230" r="120" fill="none" stroke="#7B2D5B" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>'
          f'<text x="208" y="214" font-size="15" font-weight="800" fill="#7B2D5B" font-family="sans-serif">{label}</text></svg>')
    return (f'<div class="mapv">{mp}<div class="topbar"><div class="seg"><span class="on">スタンプラリー</span><span>エアライン経営</span></div><span class="me">マイページ</span></div></div>'
            f'<div class="hs2"><div class="grab"></div>{card}<div class="peek">近くの空港</div></div>{tabbar("ホーム")}')

def head(fl, rt, co):
    return (f'<div class="r2"><div class="rh"><b>乗る便 {fl}</b><span>{rt}</span><button>やめる</button></div>'
            f'<span class="co">{co}<span class="tag g2">時刻表にない便</span></span>')

def tail(pct, reg):
    return (f'<div class="rmeta"><span>機体 {reg}</span><span>飛んだ道のり {pct}%</span></div>'
            f'<div class="rbar" role="img" aria-label="飛んだ道のり {pct}%"><i style="width:{pct}%"></i></div>{MORE}</div>')

def p_u1():
    card = (head("BA5", "ロンドン → 羽田", "ブリティッシュ・エアウェイズ") +
            '<div class="e2"><div class="k"><em>飛行中</em>羽田に着く見込み</div>'
            '<div class="row"><span class="t">20:07<small>ごろ</small></span><span class="us-n">いつもは <b>19:35</b> ごろ</span></div>'
            f'<div class="bd">{u2("いつもより32分遅い", big=True)}</div>{SRC}</div>' + tail(97, "G-STBK・77W"))
    M.page("U1-v2", "U1 案A 乗る便のカード（時刻表にない便・飛行中）2版", home2(card))

def p_u1n():
    card = (head("BA5", "ロンドン → 羽田", "ブリティッシュ・エアウェイズ") +
            '<div class="e2"><div class="k"><em>飛行中</em>羽田に着く見込み</div>'
            '<div class="none">見込みはまだ出せません</div>'
            '<div class="us-n">いつもは <b>19:35</b> ごろ<small style="color:var(--sub);font-size:13px;margin-left:4px">（推定）前の8週の7回から</small></div>'
            f'{SRC}</div>' + tail(41, "G-STBK・77W"))
    M.page("U1n-v2", "U1n 乗る便のカード（飛行中・見込みがまだ出せないとき）2版", home2(card))

def p_u1x():
    card = (head("BA5", "ロンドン → 羽田", "ブリティッシュ・エアウェイズ") +
            '<div class="e2"><div class="k"><em>飛行中</em>羽田に着く時刻</div>'
            '<div class="eta" style="background:none;padding:0;margin:0"><div class="two"><div class="u"><span>いつも</span><b>19:35</b></div><i>→</i><div><span>いまの見込み</span><b>20:07</b></div></div></div>'
            f'<div class="bd">{u2("いつもより32分遅い")}</div>{SRC}</div>' + tail(97, "G-STBK・77W"))
    M.page("U1x-v2", "U1x 案B（比べる用）2つの時刻を並べる 2版", home2(card))

def p_u2():
    card = (head("BC13", "羽田 → 福岡", "スカイマーク") +
            '<div class="e2"><div class="k"><em style="color:var(--ink2)">出発前</em>いつもの時刻</div>'
            '<div class="eta" style="background:none;padding:0;margin:0"><div class="two"><div><span>羽田を出る</span><b>19:05</b></div><i>→</i><div><span>福岡に着く</span><b>21:05</b></div></div></div>'
            '<div class="us-n" style="margin-top:2px">ごろ・前の8週の8回から</div>'
            f'{SRC}</div>'
            f'<div class="nb">{INFO}<span><b>出発の前の遅れと欠航は分かりません。</b>飛び立つと、いつもとのずれを出します。スカイマークの案内で確かめてください。</span></div>'
            + tail(0, "JA73NY・738"))
    M.page("U2-v2", "U2 乗る便のカード（ODPT にない日本の会社・出発前）2版", home2(card))

def p_u2b():
    card = (head("BC13", "羽田 → 福岡", "スカイマーク") +
            '<div class="e2"><div class="k"><em>飛行中</em>福岡に着く見込み</div>'
            '<div class="row"><span class="t">21:52<small>ごろ</small></span><span class="us-n">いつもは <b>21:05</b> ごろ</span></div>'
            f'<div class="bd">{u2("いつもより47分遅い", big=True)}</div>{SRC}</div>'
            f'<div class="nb">{WARN}<span><b>福岡空港の門限（22時）の10分前より遅い見込み（推定）</b><small>ダイバート（ほかの空港へ）になることがあります</small></span></div>'
            + tail(62, "JA73NY・738"))
    M.page("U2b-v2", "U2b 乗る便のカード（飛行中・門限に近い見込み）2版", home2(card))

def p_u2c():
    card = (head("BA5", "ロンドン → 羽田", "ブリティッシュ・エアウェイズ") +
            '<div class="e2"><div class="k"><em style="color:var(--hot)">いつもと違う空港</em>着いた空港</div>'
            f'<div class="row"><span class="t" style="font-size:28px">成田</span><span class="us-n">20:41 ごろ着陸</span></div>'
            f'<div class="bd">{u2("いつもは 羽田")}</div>{SRC}</div>'
            f'<div class="nb">{INFO}<span><b>ダイバート（ほかの空港へ）の推定です。</b>前の8週は8回すべて羽田に着いていました。ブリティッシュ・エアウェイズの案内で確かめてください。</span></div>'
            + tail(100, "G-STBK・77W"))
    M.page("U2c-v2", "U2c 乗る便のカード（ダイバートの推定）2版", home2(card, "NRT 成田"))

def ops_top2():
    return ('<div class="hd"><b>' + PIN + 'そらメモ</b><span>マイページ</span></div>'
            '<div class="seg2"><span class="on">スタンプラリー</span><span>エアライン経営</span></div>'
            '<div class="or2"><span class="sw"><span class="on">空港</span><span>機体</span></span><span class="ap"><i>HND</i>羽田 ⌄</span>'
            f'<span class="ic"><i>{I_INFO}</i><i>{I_SHARE}</i></span></div>'
            f'<div class="vw2"><div class="s"><span class="on">案内板</span><span>滑走路</span><span>定時</span><span>空の道すじ</span><span>短冊</span></div><span class="pen">{I_PEN}</span></div>')

def p_u3():
    jl = [("札幌（新千歳）から", "JL526・767", "あと4分", f'定刻 19:50 <span class="jl">18分遅れ</span>'),
          ("福岡から", "NH264・789", "あと9分", "定刻 19:55"),
          ("那覇から", "JL920・738", "あと20分", f'定刻 20:05 <span class="jl">15分遅れ</span>')]
    seq = '<ol class="bdseq">' + "".join(f'<li><span class="dot"></span><b>{a}</b><span class="fl">{b}</span><span class="rel">{c}</span><span class="tm">{d}</span></li>' for a, b, c, d in jl) + '</ol>'
    fg = [("ロンドンから", '<i class="g2">海外</i>BA5・77W', "20:07ごろ", u2("いつもより32分遅い")),
          ("神戸から", '<i class="g2">日本</i>BC106・738', "19:58ごろ", u2("いつもどおり")),
          ("ドーハから", '<i class="g2">海外</i>QR812・77W', "20:16ごろ", '<span style="font-size:13px;color:var(--sub);margin-top:6px">いつもの時刻はまだありません</span>')]
    seq2 = '<ol class="bdseq fg" style="grid-auto-columns:200px">' + "".join(f'<li><span class="dot"></span><b>{a}</b><span class="fl">{b}</span><span class="rel" style="font-size:16px">{c}</span>{e}</li>' for a, b, c, e in fg) + '</ol>'
    body = (f'<div class="pad">{ops_top2()}<div class="card">'
            '<div class="bdhead"><h3>これから着く便</h3><span class="bdtabs"><span class="on">到着</span><span>出発</span></span></div>'
            f'{seq}<p class="fwnote">JAL・ANA の時刻表と運航情報。{M.ODPT}</p>'
            '<div class="sec2"><div class="bdhead"><h3>時刻表にない便（いま近くにいる便）</h3></div>'
            f'<p class="key2" style="margin:-4px 0 0"><span><b>点線の札</b>はいつもの時刻との比べ（推定）。定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）</span></p>{seq2}'
            f'{MORE}</div></div></div>{tabbar("運用")}')
    M.page("U3-v2", "U3 運用タブの案内板（JAL・ANA と時刻表にない便）2版", body)

def p_u4():
    bg = f'<div class="pad">{ops_top2()}<div class="card"><div class="bdhead"><h3>これから着く便</h3></div></div></div>{tabbar("運用")}<div class="dim"></div>'
    sh = ('<div class="sheet"><div class="grab"></div><div class="shh"><div><small>ロンドンから・羽田に着陸</small><h2>BA5</h2></div><button aria-label="閉じる">×</button></div>'
          '<div class="lc"><small>着陸の見込み</small>'
          '<div class="row"><span class="t">20:07<small>ごろ</small></span><span class="us-n">いつもは <b>19:35</b> ごろ</span></div>'
          f'<div style="margin-top:4px">{u2("いつもより32分遅い", big=True)}</div>'
          f'<p class="src">{INFO}<span><b style="color:var(--ink2);font-weight:700">推定</b>・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）</span></p></div>'
          '<div class="spgrid"><div class="spcard"><small>機体</small><b style="font-size:20px">G-STBK</b><div class="lines">77W・ブリティッシュ・エアウェイズ</div></div>'
          '<div class="spcard"><small>滑走路</small><b>C</b><div class="lines">いまの運用からの推定</div></div></div>'
          '<div class="spcard"><small>いつもの時刻（推定）</small>'
          '<ul class="kv"><li><span>いつも</span><b>19:35 ごろ<small>前の8週の着陸の真ん中の値</small></b></li>'
          '<li><span>数えた回数</span><b>7回<small>3回以上そろった便だけ出します</small></b></li></ul></div>'
          f'{MORE}</div>')
    M.page("U4-v2", "U4 便のくわしく（時刻表にない便）2版", bg, sh)

def p_u5():
    cmp = ('<div class="cmp">'
           '<div class="card"><h4>JAL・ANA の便</h4><div class="ex">定刻 19:50 <span class="jl">18分遅れ</span></div>'
           '<p>橙の塗り。「定刻」とくらべる。出典は ODPT（時点つき）。橙と赤は航空会社が出した遅れだけ</p></div>'
           f'<div class="card"><h4>時刻表にない便</h4><div class="ex">20:07ごろ</div><div style="margin-top:4px">{u2("いつもより32分遅い")}</div>'
           '<p>灰色の点線と波の印、（推定）。「定刻」と書かず「いつもより」から。時刻に「ごろ」。出典は adsb.lol（ODbL）</p></div></div>')
    rows = [(u2("いつもより32分遅い"), "いつもより15分以上遅い見込み・遅かった", "late_min ≧ 15"),
            (u2("いつもどおり"), "前後14分以内", "−14 〜 +14"),
            (u2("いつもより18分早い"), "15分以上早い", "late_min ≦ −15"),
            ('<span style="font-size:13px;color:var(--sub)">いつもの時刻はまだありません</span>', "記録が少ない便（札は出さない）", "foreign_usual に行がない")]
    li = "".join(f'<li><span>{p}</span><p>{a}<small>{b}</small></p></li>' for p, a, b in rows)
    rows2 = [(u2("門限の10分前より遅い見込み"), "主要空港などの門限。札は同じ灰色で、カードの箱で説明（赤は使わない）", "foreign_watch。通知と同じ決まり"),
             (u2("いつもは 羽田"), "いつもと違う空港に着いた・出た空港に戻った", "foreign_legs の判定")]
    li2 = "".join(f'<li><span>{p}</span><p>{a}<small>{b}</small></p></li>' for p, a, b in rows2)
    body = (f'<div class="pad"><h1 class="t">見分け方と札の一覧（2版）</h1><p class="lead">時刻表にない便は「いつもの時刻」と比べる推定です。色・言葉・出典で、JAL・ANA の定刻つきの遅れと分けます。</p>'
            f'{cmp}<div class="card" style="margin-top:12px"><div class="lvh" style="margin-top:0">いつもとの比べ</div><ul class="cat">{li}</ul><div class="lvh">見張り（乗る便に選んだときだけ）</div><ul class="cat">{li2}</ul></div>'
            '<p class="fwnote">出す決まり：札はどれも灰色の点線＋波の印＋（推定）。大きな時刻と札の箱の中に「推定・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）」の1行。長い説明（機体の位置の取り方・出発前の遅れと欠航は分からない・空港の時間帯の出典）は「出典と注意 ›」の中に1回だけ。「時刻表にない便」「海外」「日本」の札はどれも灰色。曜日（dow）とばらつき（spread）はデータが返さないので出さない。夜の画面では点線を琥珀にする。</p></div>')
    M.page("U5-v2", "U5 見分け方と札の一覧 2版", body)

ITEMS2 = [("U1-v2", "案A（おすすめ）乗る便・飛行中：見込み＋灰色の点線の札（推定）＋箱の中の出典の1行"),
          ("U1n-v2", "乗る便・飛行中で見込みがまだ出せないとき（新）"),
          ("U1x-v2", "案B（比べる用）いつも → 見込み を並べる"),
          ("U2-v2", "乗る便：ODPT にない日本の会社・出発前"), ("U2b-v2", "乗る便：門限に近い見込み（赤をやめた）"), ("U2c-v2", "乗る便：ダイバートの推定"),
          ("U3-v2", "運用タブの案内板（上は PR #112 の形・凡例に出典）"), ("U4-v2", "便のくわしく（着陸の箱の中に出典・曜日とばらつきなし）"), ("U5-v2", "見分け方と札の一覧")]

def index2():
    li = lambda items: "".join(f'<li style="padding:12px 0;box-shadow:0 -1px 0 #EEF0F3"><a href="{k}.html" style="color:var(--ink);font-weight:800;text-decoration:none;display:block;min-height:44px">{k}　{t}<br><small style="font-size:13px;font-weight:500;color:var(--mute)">png/{k}.png</small></a></li>' for k, t in items)
    body = (f'<div class="pad"><h1 class="t">「いつもより○分遅い（推定）」の見せ方</h1><p class="lead">design/usual-late。2版（11/16 夜）は改善担当 review-1 の直し。場面は 11月16日（月）19時50分。アプリには入れない画面案です。</p>'
            f'<div class="lvh">2版</div><div class="card" style="margin-top:8px"><ul style="list-style:none;margin:0;padding:0">{li(ITEMS2)}</ul></div>'
            f'<div class="lvh">1版（比べる用）</div><div class="card" style="margin-top:8px"><ul style="list-style:none;margin:0;padding:0">{li(M.ITEMS)}</ul></div></div>')
    M.page("index", "いつもより遅いの見せ方 画面案", body)

if __name__ == "__main__":
    p_u1(); p_u1n(); p_u1x(); p_u2(); p_u2b(); p_u2c(); p_u3(); p_u4(); p_u5(); index2()
    print("ok")
