# -*- coding: utf-8 -*-
# ピン止め 4版（改善担当 review-2 を受けて）。中心は空港のまま（K5 の形）。
# 必ず直す3つ：①「ピン止め中」を押すとその空港の知らせ（シート）を開く（右に小さい ›）。行き止まりをなくす
# ②iPhone の Safari でログインしていない人：ピン止めはホーム画面のそらメモに移らないことがあると書き、「ログインして残す」を出す
# ③知らせの名前を1つに（「遅れ・欠航・ダイバート」）、特別塗装機の説明を1つの文に（アライアンス塗装は海外の会社のものだけ）
# ほか：K0 のボタン「あとで／通知を許可する」・作り手の説明は枠の外（一覧の札）へ・ホームに出すものの行（K1h）・
#   通知の文から仕組みの説明を外す・K9b は「15空港」・K8 の右は押せない小さい印・K4d に取り消す・K7 の1行と欄の位置・
#   機体ごとの知らせの残し方（K5 の補足）・海外の会社の機体の見本（K10）
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
import make_v2 as V
import make_v3 as W
from base_ops import I, CHEV, DOWN, LEFT, SRCH, PLANE, TOWER, INFO, SHARE, PEN, TABBAR
PIN, BELL = M.PIN, M.BELL
OUT = M.OUT
BELLX, CHECK, PLUS, SHAREI = W.BELLX, W.CHECK, W.PLUS, W.SHAREI

CSS = W.CSS + r"""
/* 4版：「ピン止め中」は押すと知らせを開く（形は紺の塗りのまま、右に小さい ›） */
.pinlab{height:44px;padding:0 8px 0 12px;font-size:14px}
.pinlab .cv{display:inline-flex;margin-left:1px;opacity:.85}
.pinlab .cv svg{width:15px;height:15px}
.nc .dkb{display:inline-flex;align-items:center;min-height:44px;margin:-8px -4px -8px 0;padding:0 4px}
.nc .dk .cv svg{width:13px;height:13px}
.pinmark{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--navy)}
.pinmark svg{width:18px;height:18px}
.login1{display:flex;align-items:center;gap:10px;background:var(--pill);border-radius:16px;padding:8px 6px 8px 12px;margin-top:12px}
.login1 p{margin:0;flex:1;font-size:13px;line-height:1.55;color:var(--ink2)}
.login1 p b{display:block;font-size:14px;color:var(--ink)}
.login1 span{flex:none;height:44px;display:inline-flex;align-items:center;padding:0 12px;border-radius:999px;background:var(--card);box-shadow:var(--sh);font-size:14px;font-weight:800;white-space:nowrap}
.over2{font-size:34px;font-weight:900;line-height:1}
.over2 small{font-size:15px;color:var(--sub);font-weight:700;margin-left:2px}
.codes2{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.codes2 span{font-size:13px;font-weight:700;color:var(--ink);background:var(--pill);border-radius:999px;padding:6px 10px}
.mini{background:var(--card);border-radius:22px;box-shadow:var(--sh);padding:12px 14px;display:flex;align-items:center;gap:10px;min-height:56px;margin-bottom:12px}
.mini .tx{flex:1}
.mini .tx b{display:block;font-size:15px;font-weight:800}
.mini .tx span{display:block;font-size:13px;color:var(--mute)}
.mini .go{width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.always{font-size:13px;font-weight:800;color:var(--mute);white-space:nowrap}
.onoff .tx b .newb,.newb{display:inline-block;margin-left:6px;font-size:13px;font-weight:800;color:var(--navy);background:#E9EDF4;border-radius:999px;padding:1px 8px;vertical-align:1px}
"""

def page(name, title, body):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

# ---------- 部品 ----------
def LAB(ap):
    return f'<span class="pinlab" role="button" aria-label="ピン止め中・押すと{ap}の知らせを開く">{PIN(True)}ピン止め中<span class="cv">{I(CHEV)}</span></span>'
BTN = W.BTN
rowpin, oo, onchips = W.rowpin, W.oo, W.onchips
MARK = f'<span class="pinmark" aria-label="ピン止め中">{PIN(True)}</span>'

# 知らせの名前（4版でそろえた。題も札も同じ名前）
K_SP = "特別塗装機が向かってきたら"
K_LATE = "遅れ・欠航・ダイバート"
K_GA = "ゴーアラウンド（推定）"
K_SPOT = "撮影の知らせ"
C_SP, C_LATE, C_SPOT = "特別塗装機", "遅れ・欠航・ダイバート", "撮影"
SP_SUB = "国内・海外の特別塗装機。アライアンス塗装は海外の会社のものだけ。同じ機体は6時間に1回"
MAIN8 = W.MAIN8

def ncard(code, name, sub, pinned, oth="ほか1つ"):
    flap = "".join(f"<b>{c}</b>" for c in code)
    st = (f'<span class="dkb" role="button" aria-label="ピン止め中・押すと知らせを開く"><span class="dk">{PIN(True)}ピン止め中<span class="cv">{I(CHEV)}</span></span></span>' if pinned
          else f'<span class="dkbtn" role="button" aria-pressed="false"><span class="dk">{PIN()}ピン止め</span></span>')
    o = f'<span class="oth">{oth}{I(CHEV)}</span>' if oth else ""
    return f'''<div class="nc"><div class="l"><div class="t1"><small>いちばん近い</small>{st}</div><div class="r2"><div class="flap">{flap}</div>{o}</div>
<div class="nm">{name}</div><div class="sub">{sub}・<i></i>判定範囲の中</div></div><div class="ck"><b>チェックイン</b><span>→ 右へ引いて<br>印をもらう</span></div></div>'''

HND_CARD = ncard("HND", "東京国際空港（羽田）", "第1ターミナル", True)
STAT, home, krow, BRAND, VIEWS7, sprows = W.STAT, W.home, W.krow, W.BRAND, W.VIEWS7, W.sprows
DEV_DENIED, DEV_OK = W.DEV_DENIED, W.DEV_OK
DEV_IOS = f'''<div class="dev"><span class="ic2">{I(BELLX)}</span><div class="tx"><b>iPhone はホーム画面に追加すると届きます</b><span>いまは Safari で開いているので、ON の知らせも届きません</span></div><span class="go2">やり方</span></div>'''
PINNED_CARD = f'''<div class="card mt"><div class="nrow"><span class="bi" style="background:var(--navy);color:#fff">{PIN(True)}</span><div class="tx"><b>ピン止めした空港 3</b><span>羽田・成田・石垣｜知らせの設定</span></div><span class="go">{I(CHEV)}</span></div></div>'''
def near(pinned):
    return f'''<div class="card mt"><div class="hd2"><b>ほかに 20km 以内 1つ</b><small>近い順・ピンの印でピン止め</small></div><ul class="rows nlist">
<li><div class="tx"><b>東京ヘリポート</b><span>ヘリポート・江東区</span></div><span class="km">10.9<small>km</small></span>{rowpin(pinned)}</li></ul></div>'''
PINNED_CARD4 = f'''<div class="card mt"><div class="nrow"><span class="bi" style="background:var(--navy);color:#fff">{PIN(True)}</span><div class="tx"><b>ピン止めした空港 4</b><span>羽田・成田・石垣・東京ヘリポート</span></div><span class="go">{I(CHEV)}</span></div></div>'''

def apc(code, nm, ons, noff):
    return f'<div class="apc"><div class="top"><i>{code}</i><b>{nm}</b><span class="go">{I(CHEV)}</span></div><div class="chips2">{onchips(ons, noff)}</div></div>'

def k6items(ap):
    if ap == "HND":
        return [(K_SP, SP_SUB, "on"),
                (K_LATE, "0時前後に着く便・欠航・ダイバート・引き返し。羽田は24時間なので門限はありません", "on"),
                (K_GA, "1機ごと・続いたとき・強い横風・低い雲・雷", "off", "細かく"),
                (K_SPOT, "撮影地から見える機体を来る前に。ピン止めした空港のうち1つだけ（いまは羽田）", "on", "撮影地と機体を選ぶ")]
    if ap == "NRT":
        return [(K_SP, SP_SUB, "on"),
                (K_LATE, "門限の10分前より遅く着く見込みの便・欠航・ダイバート・引き返し", "off"),
                (K_GA, "1機ごと・続いたとき・強い横風・低い雲・雷", "off", "細かく"),
                (K_SPOT, "ON にすると、撮影の知らせを羽田から成田に移します（1つの空港だけ）", "off")]
    return [(K_SP, SP_SUB, "on"),
            (K_LATE, f"石垣は欠航・ダイバート・引き返しだけ。門限ギリギリと0時前後は{MAIN8}です", "on"),
            (K_GA, "羽田・成田・関西など14空港だけです", "na", "14空港の一覧"),
            (K_SPOT, "ON にすると、撮影の知らせを羽田から石垣に移します（1つの空港だけ）", "off")]

NOTE_EST = '<p class="note">どれも機体の位置（adsb.lol・ODbL）や運航情報（ODPT）からの<b>推定です。保証しません。</b>乗る便の遅れは、乗る便の知らせ1つにまとめます。</p>'

def build():
    # ---------- K0 はじめてのピン止めで、通知の許可を聞く前の1枚 ----------
    k0 = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="bigic">{I(BELL)}</div><div class="shh"><h2>羽田をピン止めしました。知らせを届けますか</h2></div>
<p class="sub" style="line-height:1.7">特別塗装機が羽田に向かってきたら、この端末に知らせます。このあと端末の確認で「許可」を押してください。</p>
<div style="display:flex;gap:8px;margin-top:16px"><span class="pillbtn" style="flex:1">あとで</span><span class="pillbtn" style="flex:1.6;background:var(--navy);color:#fff">通知を許可する</span></div>
<p class="note">許可しなくてもピン止めはできます（知らせだけ届きません）。あとから「知らせ」の画面で許可できます。</p></div>'''
    page("K0-v4", "K0 通知の許可を聞く前の1枚", k0)

    # ---------- K0i iPhone の Safari でホーム画面に置いていない（ログインしていない人の1行を足す）----------
    k0i = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="shh"><h2>iPhone は、ホーム画面に追加すると知らせが届きます</h2></div>
<p class="sub" style="line-height:1.7">いまは Safari で開いているので、iPhone の決まりで知らせが届きません。</p>
<div class="login1"><p><b>先にログインしてください</b>iPhone では、ホーム画面のそらメモと Safari で保存場所が分かれます。ログインしないと、ここでしたピン止めは移りません。</p><span>ログインする</span></div>
<ul class="steps"><li>Safari の下の共有の印 {I(SHAREI)} を押す</li><li>「ホーム画面に追加」を押す</li><li>ホーム画面のそらメモから開き、通知を許可する</li></ul>
<p class="note">ログインしないときは、ホーム画面のそらメモでもう一度ピン止めしてください。</p>
<div style="display:flex;gap:8px;margin-top:12px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1.4;background:var(--navy);color:#fff">やり方を図で見る</span></div></div>'''
    page("K0i-v4", "K0i iPhone でホーム画面に置いていない", k0i)

    # ---------- K1 ホーム（本番の形・羽田はピン止め中 ›）----------
    page("K1-v4", "K1 ホーム（本番の形）ピン止め中", home(HND_CARD + STAT))
    # ---------- K1s 札を押したとき：羽田の知らせをシートで ----------
    k1s = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田の知らせ</h2><button>完了</button></div>
{DEV_OK}{oo(k6items("HND"))}
<div class="danger" style="margin-top:10px">羽田のピン止めを外す</div></div>'''
    page("K1s-v4", "K1s 札を押すと羽田の知らせ", k1s)
    page("K1n-v4", "K1n ホーム ピン止めしていない空港", home(ncard("ITM", "大阪国際空港（伊丹）", "南ターミナル", False, oth="ほか2つ") + STAT))
    page("K1o-v4", "K1o シートを引き上げたとき", home(HND_CARD + near(False) + PINNED_CARD + STAT, exp=True))

    # ---------- K1h ホームに出すもの（新しいかたまりの行）----------
    def hrow(nm, sub, st):
        right = '<span class="always">いつも</span>' if st == "always" else f'<span class="tg {st}">{st.upper()}</span>'
        return f'<li><div class="tx"><b>{nm}</b><span>{sub}</span></div>{right}</li>'
    k1h = f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}表示の編集</span><h2>ホームに出すもの</h2><span style="width:72px"></span></div>
<ul class="onoff card" style="padding:4px 16px">{hrow("いちばん近い空港", "パタパタとチェックイン", "always")}{hrow("今日の数字", "今日の印・空港・フライト", "always")}
{hrow("ほかの近くの空港", "20km 以内の空港・飛行場", "on")}
<li><div class="tx"><b>ピン止めした空港<span class="newb">新しい</span></b><span>ピン止めが1つ以上あるときだけ出ます。はじめは ON</span></div><span class="tg on">ON</span></li>
{hrow("乗る便", "乗る便があるときはいちばん上に", "on")}</ul>
<p class="note">OFF にしても、ピン止めと知らせはそのままです。</p></div>'''
    page("K1h-v4", "K1h ホームに出すもの", k1h)

    # ---------- K2 空港ページ（羽田）----------
    k2 = f'''<div class="pad"><div class="zktop"><span class="back">{I(LEFT)}閉じる</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">HND</span><h2>東京国際空港（羽田）</h2><span class="s">東京都大田区・供用開始 1931年</span></div>{LAB("羽田")}</div>
<div class="card mt"><div class="nrow"><span class="bi">{I(BELL)}</span><div class="tx"><b>羽田の知らせ</b><span>何を知らせるか・ピン止めを外す</span></div><span class="go">{I(CHEV)}</span></div>
<div class="chips2" style="display:flex;flex-wrap:wrap;gap:6px;padding:0 0 4px 46px">{onchips([C_SP, C_LATE, C_SPOT], 1)}</div></div>
<div class="card mt"><div class="h"><b>いまの運用</b><small>実際の機体から判定</small></div><div style="font-size:28px;font-weight:900">北風運用</div><p class="note" style="margin-top:4px">着陸 34L・34R／離陸 05・34R</p></div>
<div class="card mt"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間</small></div>{sprows()}</div></div>{V.TAB_HOME}'''
    page("K2-v4", "K2 空港ページ ピン止め中", k2)

    # ---------- K3 図鑑の空港（成田）／K3s 札を押したとき ----------
    def k3body(extra=""):
        return f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}関東</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">NRT</span><h2>成田国際空港</h2><span class="s">千葉県成田市</span></div>{LAB("成田")}</div>
<div class="kv"><div><small>はじめての印</small><b>2025<small>/3/8</small></b></div><div><small>印</small><b>7<small>回</small></b></div></div></div>{V.TAB_BOOK}{extra}'''
    page("K3-v4", "K3 図鑑の空港 ピン止め中", k3body())
    page("K3s-v4", "K3s 札を押すと成田の知らせ", k3body(f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>成田の知らせ</h2><button>完了</button></div>
{DEV_OK}{oo(k6items("NRT"))}<div class="danger" style="margin-top:10px">成田のピン止めを外す</div></div>'''))
    page("K3n-v4", "K3n 図鑑の空港 ピン止めしていない", f'''<div class="zk"><div class="zktop"><span class="back">{I(LEFT)}中部</span><span class="ic">{I(SHARE)}</span></div>
<div class="aph"><div class="tx"><span class="code">NGO</span><h2>中部国際空港</h2><span class="s">愛知県常滑市</span></div>{BTN}</div>
<div class="kv"><div><small>はじめての印</small><b>2024<small>/11/2</small></b></div><div><small>印</small><b>2<small>回</small></b></div></div></div>{V.TAB_BOOK}''')

    # ---------- K4 ピン止めした直後／K4d 許可なし ----------
    K4ITEMS = [(K_SP, "アライアンス塗装は海外の会社のものだけ。同じ機体は6時間に1回", "on"), (K_LATE, "0時前後に着く便・欠航・ダイバート・引き返し", "off"),
               (K_GA, "1機ごと・続いたとき・強い横風など", "off"), (K_SPOT, "ピン止めした空港のうち1つだけ ON にできます", "off")]
    FOOT = '<div style="display:flex;align-items:center;gap:8px;margin-top:6px"><p class="note" style="flex:1;margin:0"><b>推定です。保証しません。</b></p><span class="pillbtn">取り消す</span></div>'
    page("K4-v4", "K4 ピン止めした直後（許可済み）", home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田をピン止めしました</h2><button>完了</button></div>
<p class="sub">何を知らせますか。あとから「ピン止め中」を押して変えられます。</p>{DEV_OK}{oo(K4ITEMS)}{FOOT}</div>''')
    page("K4d-v4", "K4d 通知を許可していないとき", home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div><div class="shh"><h2>羽田をピン止めしました</h2><button>完了</button></div>
{DEV_DENIED}{oo(K4ITEMS, nd=True)}{FOOT}</div>''')

    # ---------- K4t・K4u（ピン止めした空港のかたまりも出す）----------
    page("K4t-v4", "K4t 2回目からは帯だけ", home(HND_CARD + near(True) + PINNED_CARD4 + STAT, exp=True,
        extra=f'<div class="toast">{PIN(True)}<p>東京ヘリポートをピン止めしました</p><a>知らせの設定</a></div>'))
    page("K4u-v4", "K4u 外したときは元に戻せる", home(HND_CARD + near(False) + PINNED_CARD + STAT, exp=True,
        extra=f'<div class="toast">{PIN()}<p>東京ヘリポートのピン止めを外しました。知らせも止めました</p><a>元に戻す</a></div>'))

    # ---------- K5 知らせ（1か所）----------
    def k5body(dev):
        return f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}マイページ</span><h2>知らせ</h2><span style="width:72px"></span></div>
{dev}
<div class="pinh" style="margin-top:14px"><span class="pi">{PIN(True)}</span><b>ピン止めした空港</b><span class="n">3 / 12</span><span class="sp"></span><span class="ed">並べ替え</span></div>
{apc("HND", "羽田", [C_SP, C_LATE, C_SPOT], 1)}
{apc("NRT", "成田", [C_SP], 3)}
{apc("ISG", "石垣", [C_SP, C_LATE], 1)}
<div class="addap">{I(PLUS)}空港をピン止め</div>
<p class="note">ピン止めはアカウントに保存します（ログインしていないときはこの端末だけ）。</p>
<p class="secth">便</p>
<div class="card" style="margin-top:8px"><div class="nrow"><span class="bi">{I(PLANE)}</span><div class="tx"><b>乗る便</b><span>JL 323（11/17）・15分の遅れから</span></div><span class="go">{I(CHEV)}</span></div></div>
<p class="secth">機体ごと</p>
<div class="card" style="margin-top:8px"><div class="nrow"><span class="bi">{I(BELL)}</span><div class="tx"><b>機体ごとの知らせ 2機</b><span>前に申し込んだ機体。どの空港へ飛ぶときも届きます。新しく足すことはできません</span></div><span class="go">{I(CHEV)}</span></div></div></div>'''
    page("K5-v4", "K5 知らせ（許可済み）", k5body(DEV_OK))
    page("K5n-v4", "K5n 知らせ（iPhone でホーム画面に置いていない）", k5body(DEV_IOS))

    # ---------- K6 羽田の知らせ／K6n 石垣 ----------
    def k6page(ap, nm, full, items):
        return f'''<div class="full"><div class="top"><span class="back">{I(LEFT)}知らせ</span><h2>{nm}の知らせ</h2><span style="width:72px"></span></div>
<div class="aph" style="margin-top:0;align-items:center"><div class="tx"><span class="code">{ap}</span><span class="s" style="display:inline;margin-left:8px;font-size:15px;font-weight:800;color:var(--ink)">{full}</span></div></div>
{DEV_OK}<div class="card mt">{oo(items)}</div>{NOTE_EST}
<div class="danger">{nm}のピン止めを外す</div>
<p class="note" style="text-align:center">外すと{nm}の知らせはすべて止まります（すぐあとなら元に戻せます）。</p></div>'''
    page("K6-v4", "K6 羽田の知らせ", k6page("HND", "羽田", "東京国際空港", k6items("HND")))
    page("K6n-v4", "K6n 石垣の知らせ", k6page("ISG", "石垣", "新石垣空港", k6items("ISG")))

    # ---------- K7 運用タブ（撮る人：撮影地・運用の下に特別塗装機の欄。本番の並び）----------
    k7 = f'''<div class="pad">{BRAND}{krow()}{VIEWS7}
<div class="mini"><div class="tx"><b>撮影地</b><span>城南島海浜公園・34L 着陸がよく見える</span></div><span class="go">{I(CHEV)}</span></div>
<div class="mini"><div class="tx"><b>いまの運用</b><span>北風運用・着陸 34L・34R</span></div><span class="go">{I(CHEV)}</span></div>
<div class="card"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間・機体の位置からの推定</small></div>{sprows()}
<div class="pline"><span style="color:var(--navy)">{PIN(True)}</span><div class="tx"><b>羽田はピン止め中</b><span>特別塗装機・遅れ・撮影が ON</span></div><span class="go">{I(CHEV)}</span></div></div></div>{TABBAR}'''
    page("K7-v4", "K7 運用タブ 空港側", k7)
    k7n = f'''<div class="pad">{BRAND}{krow("ITM", "伊丹")}{VIEWS7}
<div class="mini"><div class="tx"><b>撮影地</b><span>千里川土手・32L 着陸がよく見える</span></div><span class="go">{I(CHEV)}</span></div>
<div class="mini"><div class="tx"><b>いまの運用</b><span>32L 着陸・32R 離陸</span></div><span class="go">{I(CHEV)}</span></div>
<div class="card"><div class="hd2"><b>向かっている特別塗装機</b><small>この先3時間・機体の位置からの推定</small></div><ul class="rows">
<li><span class="tmc"><b>17:20</b><small>着（推定）</small></span><div class="tx"><b>特別塗装機（見本）</b><span>登録記号・便名・出発地</span></div><span class="go">{I(CHEV)}</span></li></ul>
<div class="pline" style="background:var(--card);box-shadow:inset 0 0 0 1.5px #D5DAE1"><div class="tx"><b>伊丹をピン止めすると</b><span>特別塗装機が向かってきたら知らせます</span></div>{BTN}</div></div></div>{TABBAR}'''
    page("K7n-v4", "K7n 運用タブ ピン止めしていない空港", k7n)

    # ---------- K8 空港を選ぶシート（ピン止めの行の右は押せない小さい印）----------
    k8 = f'''<div class="pad">{BRAND}{krow()}</div>{TABBAR}<div class="dim"></div>
<div class="sheet"><div class="grab"></div><div class="shh"><h2>空港を選ぶ</h2></div>
<div class="pickrow"><span class="search">{I(SRCH)}空港の名前かコード</span></div>
<p class="grp">{PIN(True)} ピン止めした空港 3</p>
<ul class="rows"><li class="selrow"><div class="tx"><b>羽田</b><span>いまいる空港</span></div>{MARK}</li>
<li><div class="tx"><b>成田</b><span>60km</span></div>{MARK}</li>
<li><div class="tx"><b>石垣</b><span>1,950km</span></div>{MARK}</li></ul>
<p class="grp">近い順</p>
<ul class="rows"><li><div class="tx"><b>茨城</b><span>85km</span></div></li>
<li><div class="tx"><b>静岡</b><span>150km</span></div></li></ul></div>'''
    page("K8-v4", "K8 空港を選ぶシート", k8)

    # ---------- K9 今の利用者への1回の案内 ----------
    k9 = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="mig mt"><span class="pi">{PIN(True)}</span><p><b>空港の知らせを、ピン止めにまとめました</b>申し込んでいた空港を、そのままピン止めしています。知らせの中身は変わりません。</p></div>
<div class="card mt" style="box-shadow:inset 0 0 0 1px var(--line);padding:8px 14px">
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>HND</i><b>羽田</b></div><div class="chips2">{onchips([C_SP, C_LATE, C_SPOT], 0)}</div></div>
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>NRT</i><b>成田</b></div><div class="chips2">{onchips([C_SP], 0)}</div></div>
<div class="apc" style="box-shadow:none;margin:0;padding:4px 0"><div class="top"><i>ISG</i><b>石垣</b></div><div class="chips2">{onchips([C_SP, C_LATE], 0)}</div></div></div>
<p class="note"><b>機体ごとの知らせ（2機）と乗る便の知らせは、そのまま続きます。</b></p>
<div style="display:flex;gap:8px;margin-top:12px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">知らせを見る</span></div></div>'''
    page("K9-v4", "K9 今の利用者への案内", k9)

    # ---------- K9b 上限12を超える人（大きい字は「15空港」だけ・名前つき）----------
    names = ["羽田", "成田", "石垣", "伊丹", "関西", "中部", "新千歳", "福岡", "那覇", "鹿児島", "広島", "仙台", "小松", "松山", "大分"]
    k9b = home(HND_CARD + STAT) + f'''<div class="dim"></div><div class="sheet"><div class="grab"></div>
<div class="mig mt"><span class="pi">{PIN(True)}</span><p><b>空港の知らせを、ピン止めにまとめました</b>申し込んでいた空港を、すべてそのままピン止めしています。知らせも今までどおり届きます。</p></div>
<div class="card mt" style="box-shadow:inset 0 0 0 1px var(--line)"><div class="over2">15<small>空港</small></div>
<p class="note" style="margin-top:6px">ピン止めの上限は12空港です。新しく足すのは、12より少なくなってからです。</p>
<div class="codes2">{"".join(f"<span>{c}</span>" for c in names)}</div></div>
<div style="display:flex;gap:8px;margin-top:14px"><span class="pillbtn" style="flex:1">閉じる</span><span class="pillbtn" style="flex:1;background:var(--navy);color:#fff">知らせを見る</span></div></div>'''
    page("K9b-v4", "K9b 上限12を超える人", k9b)

    # ---------- K10 知らせの見本（通知の文から仕組みの説明を外す・海外の会社の機体を足す）----------
    def nt(b, p, when="いま"):
        return f'<div class="nt1"><span class="ap"><i></i>そらメモ<em>{when}</em></span><b>{b}</b><p>{p}</p></div>'
    k10 = f'''<div class="lock"><div class="clk">23:25</div><div class="dt">11月17日 火曜日</div>
<p class="lab">ピン止めの空港に特別塗装機</p>
{nt("羽田にジンベエジェットが向かっています", "JTA 9 那覇から・JA05RK｜着くのは 16:05ごろ（推定）", "15:10")}
<p class="lab">ピン止めの空港に海外の会社の特別塗装機</p>
{nt("成田にエバー航空の特別塗装機が向かっています（推定）", "BR 198 台北から・登録記号（見本）｜着くのは 18:40ごろ", "15:55")}
<p class="lab">乗る便と、ピン止めの空港の遅れが重なるとき</p>
{nt("JL 323（乗る便）は羽田に 0:10ごろ着く見込み", "45分遅れ・福岡 22:30 発｜運航情報（ODPT）")}
<div class="cmp"><b>届く決まり</b><br>・特別塗装機は、ピン止めした空港に向かうときだけ（海外の会社の機体も同じ。同じ機体が同じ空港へは1回）<br>・乗る便が、ピン止めした空港の遅れの知らせにも当たるときは、乗る便の知らせ1つにまとめる<br>・機体ごとの知らせ（前に申し込んだ機体）は、どの空港へ飛ぶときも届く</div></div>'''
    page("K10-v4", "K10 知らせの見本", k10)

    # ---------- 一覧（作り手の説明はここへ）----------
    L = [("4版：空港をピン止め（おすすめ・review-2 の直し）", [
            ("K0-v4", "通知の許可を聞く前の1枚", "最初のピン止めのときだけ。ボタンは「あとで／通知を許可する」。Android とパソコンはこの形"),
            ("K0i-v4", "iPhone でホーム画面に置いていない", "ログインしていない人には手順より先に「先にログイン」（iPhone はホーム画面と Safari で保存場所が分かれる）。ログインしない人はホーム画面でもう一度ピン止め。実機で移ると分かればこの1行は消す。iPhone のアプリができたらこの1枚は要らない"),
            ("K1-v4", "ホーム（本番の形）", "札「ピン止め中 ›」は押すと K1s"),
            ("K1s-v4", "札を押したとき", "羽田の知らせをシートで。外すのは下"),
            ("K1n-v4", "ピン止めしていない空港にいるとき", "黒いカードの上の「ピン止め」"),
            ("K1o-v4", "シートを引き上げたとき", "ほかの空港の行のピンは押すと付け外し（元に戻せる）"),
            ("K1h-v4", "ホームに出すもの", "「ピン止めした空港」の行を足す。はじめ ON（本人に聞く）"),
            ("K2-v4", "空港ページ（羽田）", "「ピン止め中 ›」と「羽田の知らせ」のどちらからも K6"),
            ("K3-v4", "図鑑の空港（成田）", "「ピン止め中 ›」"),
            ("K3s-v4", "札を押したとき（成田）", "図鑑からも知らせへ。行き止まりなし"),
            ("K3n-v4", "図鑑の空港（中部）", "していない＝白地＋線のピン＋「ピン止め」"),
            ("K4-v4", "ピン止めした直後", "最初の1回だけ・取り消す"),
            ("K4d-v4", "通知を許可していないとき", "ON に「届きません」・取り消すを足した。「許可する」は確認が出せればその場で、断ったあとは設定のやり方"),
            ("K4t-v4", "2回目からは帯だけ", "ピン止めした空港 4 のかたまりも出す"),
            ("K4u-v4", "外したとき", "元に戻す"),
            ("K5-v4", "知らせ（1か所）", "名前を「遅れ・欠航・ダイバート」にそろえた。12空港に届いたら「＋」は押せなくなる。機体ごとは今の分だけ残す案"),
            ("K5n-v4", "知らせ（iPhone で置いていない）", "上に端末の1行"),
            ("K6-v4", "羽田の知らせ", "題は「遅れ・欠航・ダイバート」、羽田に門限がないことは補足だけ"),
            ("K6n-v4", "石垣の知らせ", "出せない知らせは薄く、理由は空港名で"),
            ("K7-v4", "運用タブ 空港側", "上の1行と帯は本番（PR #112）のまま。撮影地・運用の下に特別塗装機の欄（本番の並び）。1行は「特別塗装機・遅れ・撮影の知らせが ON」"),
            ("K7n-v4", "運用タブ ピン止めしていない空港", "押すと K4 か K4t の帯"),
            ("K8-v4", "空港を選ぶシート", "右は押せない小さいピンの印。付け外しは知らせの画面で"),
            ("K9-v4", "今の利用者への案内", "1回だけ。ゴーアラウンドを申し込んでいた空港も同じように移す"),
            ("K9b-v4", "上限12を超える人", "大きい字は「15空港」だけ。今は遅れ12・特別塗装機14空港まで（合わせて最大26）"),
            ("K10-v4", "知らせの見本", "通知の文から仕組みの説明を外した。海外の会社の機体の見本を足した")]),
         ("3版（比べる用に残す）", [(n, t, "") for n, t in [("K1-v3", "ホーム"), ("K3-v3", "図鑑の空港"), ("K5-v3", "知らせ"), ("K6-v3", "羽田の知らせ"), ("K8-v3", "空港を選ぶシート")]]),
         ("2版（比べる用に残す）", [(n, t, "") for n, t in [("00-v2", "今の空港ごとの知らせ"), ("K5b-v2", "比べる用：表の形")]]),
         ("1版：機体をピン止め（2番目の案）", [(n, t, "") for n, t in [("P1", "機体側・ピン止めの段"), ("P2", "機体の1日"), ("P3", "特別塗装機の欄"), ("P6", "機体の知らせの設定"), ("P7", "機体の知らせの見本")]])]
    body = ('<div class="idx"><h1>ピン止め</h1><p>design/pin 4版（11/18）。中心は空港。ピン止めした空港に特別塗装機が向かってきたら知らせます。空港ごとの知らせの申し込みはピン止めの1か所（K5）にまとめます。画面案だけで、アプリには入れません。</p>'
            '<p><b>ピン止めの2つの形</b>：している＝紺の塗り＋塗りのピン＋「ピン止め中 ›」（押すとその空港の知らせ）／していない＝白地＋線のピン＋「ピン止め」（押すとピン止め）。羽田・成田・石垣はどの画面でもピン止め中。知らせの名前は「特別塗装機」「遅れ・欠航・ダイバート」「ゴーアラウンド」「撮影」の4つ。</p>')
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n.split("-v")[0]}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    page("index", "ピン止め", body + "</div>")

if __name__ == "__main__":
    M.build(); V.build(); W.build(); build(); print("ok")
