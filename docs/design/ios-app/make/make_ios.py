# -*- coding: utf-8 -*-
# iPhone のアプリ（自分用の段・Capacitor）だけの画面案（design/ios-app）1版。
# チェックイン担当の依頼（11/18・report-ios-app-base.md）：①位置の許可を頼む前の説明の1枚 ②オフラインの画面 ③アプリで隠すもの。
# 1画面1ファイルの HTML（スマホ幅 390・外部の読み込みなし）を ../ に書き出す。PNG は shoot_ios.py で撮る。
# 色と字・ホーム（地図とシート）・タブ帯は lib/（design/pin 4版の部品をそのまま写したもの。本番の web/ の色に合わせてある）を使う。
# 見本の時刻は 11/19 15:10（羽田・昼の画面）。夜の版は 18:40。
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "lib"))
import make_v2 as V
import make_v3 as W
import make_v4 as X
from base_ops import I, CHEV, DOWN, INFO, SHARE, PLANE

CSS = X.CSS + r"""
/* ---- iPhone のアプリだけの画面 ---- */
.full1{min-height:844px;padding:56px 24px 150px;display:flex;flex-direction:column}
.full1 .bd{font-size:15px;font-weight:800;letter-spacing:.12em;color:var(--ink2);display:flex;align-items:center;gap:6px}
.bigic2{width:88px;height:88px;border-radius:50%;background:var(--card);box-shadow:var(--sh);display:flex;align-items:center;justify-content:center;color:var(--navy);margin:28px 0 18px}
.bigic2 svg{width:40px;height:40px;stroke-width:2}
.full1 h1{font-size:24px;font-weight:900;line-height:1.45;margin:0;color:var(--ink)}
.full1 .lead{font-size:15px;line-height:1.75;color:var(--ink2);margin:10px 0 0}
.why{list-style:none;margin:20px 0 0;padding:6px 16px;background:var(--card);border-radius:22px;box-shadow:var(--sh)}
.why li{display:flex;gap:12px;align-items:flex-start;padding:12px 0}
.why li+li{box-shadow:0 -1px 0 var(--line)}
.why .wi{flex:none;width:36px;height:36px;border-radius:50%;background:var(--pill);color:var(--ink2);display:flex;align-items:center;justify-content:center}
.why .wi svg{width:18px;height:18px}
.why b{display:block;font-size:15px;font-weight:800;line-height:1.5}
.why span{display:block;font-size:13px;line-height:1.6;color:var(--mute)}
.foot1{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;padding:14px 24px 34px;background:linear-gradient(180deg,rgba(238,241,245,0),var(--bg) 26%)}
.foot1 .main{height:54px;border-radius:999px;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800}
.foot1 p{font-size:13px;line-height:1.6;color:var(--mute);margin:10px 4px 0;text-align:center}
.foot1 .sec{height:48px;margin-top:8px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;color:var(--ink2);background:var(--pill)}
/* iPhone が出す確認の場所（見本。形は iOS のもので、まねして描かない） */
.osbox{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);width:290px;border-radius:22px;background:rgba(246,247,249,.97);z-index:9;padding:18px 18px 16px;box-shadow:0 20px 50px -20px rgba(0,0,0,.5);outline:2px dashed #94A3B8;outline-offset:-8px}
.osbox small{display:block;font-size:13px;font-weight:800;color:var(--mute);text-align:center}
.osbox b{display:block;font-size:15px;font-weight:800;text-align:center;margin:8px 0 6px;line-height:1.5}
.osbox p{font-size:13px;line-height:1.65;color:var(--ink2);margin:0}
.osbox .ch{display:flex;flex-direction:column;gap:6px;margin-top:12px}
.osbox .ch span{height:40px;border-radius:12px;background:#E6E9EE;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--ink2)}
/* ホームで位置が使えないときのカード（黒いカードの代わり。チェックインの金の帯は出さない） */
.nloc{border-radius:22px;background:var(--card);box-shadow:var(--sh);padding:16px}
.nloc .t{display:flex;align-items:center;gap:10px}
.nloc .t .wi{flex:none;width:44px;height:44px;border-radius:50%;background:#FEF3C7;color:#92400E;display:flex;align-items:center;justify-content:center}
.nloc .t .wi svg{width:22px;height:22px}
.nloc .t b{font-size:17px;font-weight:800;line-height:1.4}
.nloc p{font-size:14px;line-height:1.7;color:var(--ink2);margin:8px 0 0}
.nloc .bt{display:flex;gap:8px;margin-top:12px}
.nloc .bt span{flex:1;height:44px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;background:var(--pill);color:var(--ink2);white-space:nowrap}
.nloc .bt span.pri{background:var(--navy);color:#fff}
.nloc .acc{display:flex;align-items:baseline;gap:6px;margin-top:10px;font-size:13px;color:var(--mute)}
.nloc .acc b{font-size:22px;font-weight:900;color:var(--ink)}
.nloc .acc b small{font-size:13px;font-weight:700;color:var(--sub);margin-left:2px}
.map0{position:fixed;inset:0;width:390px;margin:0 auto;background:linear-gradient(170deg,#DCE6EE,#CBD8E3);overflow:hidden}
.map0 i{position:absolute;height:2px;background:rgba(255,255,255,.75);transform-origin:left center}
.map0 em{position:absolute;left:150px;top:300px;font-style:normal;font-size:13px;font-weight:800;color:#5B6B7D;background:rgba(255,255,255,.7);border-radius:999px;padding:3px 10px}
/* オフラインの帯（シートの頭。今の queuebar の置き場） */
.offbar{display:flex;align-items:center;gap:10px;background:#FFF7E6;border-radius:18px;padding:10px 12px;margin-bottom:10px;box-shadow:inset 0 0 0 1px rgba(146,64,14,.12)}
.offbar .wi{flex:none;width:32px;height:32px;border-radius:50%;background:#FEF3C7;color:#92400E;display:flex;align-items:center;justify-content:center}
.offbar .wi svg{width:18px;height:18px}
.offbar .tx{flex:1;font-size:13px;line-height:1.55;color:#5B3A0A}
.offbar .tx b{display:block;font-size:14px;color:#3B2606}
.nc.off .ck{background:#E9C46A}
.nc .q{display:block;font-size:13px;color:#FFD58A;margin-top:4px}
/* 比べる表（I3） */
.cmpT{list-style:none;margin:0;padding:0}
.cmpT li{padding:12px 0}
.cmpT li+li{box-shadow:0 -1px 0 var(--line)}
.cmpT b{display:block;font-size:15px;font-weight:800}
.cmpT .fn{display:block;font:600 13px/1.5 ui-monospace,Menlo,monospace;color:var(--mute);margin-top:2px;word-break:break-all}
.cmpT .ab{display:grid;grid-template-columns:40px 1fr;gap:4px 8px;margin-top:6px;font-size:13px;line-height:1.6;color:var(--ink2)}
.cmpT .ab i{font-style:normal;font-weight:800;font-size:13px;color:var(--mute);background:var(--pill);border-radius:999px;text-align:center;height:22px;line-height:22px}
.cmpT .ab i.ap{background:var(--navy);color:#fff}
.cmpT .ab s{color:var(--sub)}
.st2{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;font-size:13px;font-weight:800;margin-left:6px;vertical-align:2px}
.st2.done{background:#E7F5EC;color:var(--ok)}
.st2.todo{background:#FEF3C7;color:#92400E}
/* マイページの設定（アプリ） */
.setl{list-style:none;margin:0;padding:0}
.setl li{display:flex;align-items:center;gap:12px;min-height:56px;padding:8px 0}
.setl li+li{box-shadow:0 -1px 0 var(--line)}
.setl .tx{flex:1;min-width:0}
.setl .tx b{display:block;font-size:15px;font-weight:800}
.setl .tx span{display:block;font-size:13px;line-height:1.55;color:var(--mute)}
.setl .go{flex:none;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.setl .vl{flex:none;font-size:14px;font-weight:800;color:var(--ink2)}
.setl li.gone{opacity:1}
.setl li.gone .tx b{color:var(--sub);text-decoration:line-through}
.gonetag{flex:none;height:28px;display:inline-flex;align-items:center;padding:0 10px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--mute)}
.qbar{background:var(--card);border-radius:18px;box-shadow:var(--sh);padding:12px 14px;margin-bottom:10px;font-size:13px;line-height:1.6;color:var(--ink2);position:relative;outline:2px dashed #CBD2DC;outline-offset:3px}
.qbar b{display:block;font-size:14px}
.qbar .bt{display:flex;gap:8px;margin-top:8px}
.qbar .bt span{height:44px;padding:0 16px;border-radius:999px;background:var(--pill);display:inline-flex;align-items:center;font-size:14px;font-weight:800}
.xmark{position:absolute;right:-6px;top:-10px;height:26px;padding:0 10px;border-radius:999px;background:#B45309;color:#fff;font-size:13px;font-weight:800;display:flex;align-items:center}
/* 夜の画面（決定事項 11/8・11/9：角丸とピルのまま、光る色は緑と琥珀だけ、会社の色と金は使わない、主ボタンは白い字と縁） */
body.night{background:#0E1014;color:#DCE3EA}
body.night{--bg:#0E1014;--card:#16191F;--ink:#E5E7EB;--ink2:#D1D5DB;--mute:#A7B0BC;--sub:#A7B0BC;--pill:#1D232C;--line:#2A2F37;--navy:#0E1014;
  --sh:inset 0 0 0 1px rgba(220,227,234,.10)}
body.night .bigic2{color:#86EFAC;box-shadow:inset 0 0 0 1.5px rgba(134,239,172,.45)}
body.night .why .wi{color:#DCE3EA}
body.night .foot1{background:linear-gradient(180deg,rgba(14,16,20,0),#0E1014 26%)}
body.night .foot1 .main{background:transparent;box-shadow:inset 0 0 0 2px #DCE3EA;color:#fff}
body.night .foot1 .sec{color:#DCE3EA}
body.night .offwi{color:#E9A14B!important;box-shadow:inset 0 0 0 1.5px rgba(233,161,75,.5)!important}
"""

def page(name, title, body, cls=""):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body class="{cls}">{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

LOC = '<path d="M12 21s-6.5-6.1-6.5-11A6.5 6.5 0 0 1 18.5 10c0 4.9-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.4"/>'
LOCX = '<path d="M12 21s-6.5-6.1-6.5-11a6.5 6.5 0 0 1 9.8-5.6"/><path d="M18.4 9.2c.1.3.1.5.1.8 0 4.9-6.5 11-6.5 11"/><path d="M4 4l16 16"/>'
STAMP = '<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>'
MAPI = '<path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6Z"/><path d="M9 4v14"/><path d="M15 6v14"/>'
CLOCK = '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'
EYE = '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>'
CLOUDX = '<path d="M7 18a4 4 0 0 1-.6-8 5.5 5.5 0 0 1 10.7 1.2A3.5 3.5 0 0 1 17 18Z"/><path d="m10 11.5 4 4"/><path d="m14 11.5-4 4"/>'
WIFI0 = '<path d="M2.5 9a14 14 0 0 1 19 0"/><path d="M5.5 12.5a9.5 9.5 0 0 1 13 0"/><path d="M9 16a4.5 4.5 0 0 1 6 0"/><path d="M12 19.5h.01"/><path d="M4 4l16 16"/>'
GEAR = '<circle cx="12" cy="12" r="3"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7"/>'
LOGO = '<circle cx="12" cy="12" r="9"/><path d="m8 15 8-6-3 8-1-3Z"/>'
BRAND1 = f'<div class="bd">{I(LOGO)}そらメモ</div>'

# Info.plist の理由の文（checkin/ios-app の NSLocationWhenInUseUsageDescription）と同じことを言う
WHY = [(STAMP, "印をもらうときに、空港の判定範囲の中かを確かめます", "空港ごとに決めた範囲の中でだけ、チェックインの印を押せます"),
       (MAPI, "ホームの地図に、近い空港を近い順に出します", "飛行場・滑空場・ヘリポートも、近い順に並べます"),
       (CLOCK, "使うのは、そらメモを開いている間だけです", "いる場所を、ほかの人に見せることはありません")]

def why_list():
    return '<ul class="why">' + "".join(f'<li><span class="wi">{I(ic)}</span><div><b>{b}</b>{f"<span>{s}</span>" if s else ""}</div></li>' for ic, b, s in WHY) + "</ul>"

def i1_body():
    return f'''<div class="full1">{BRAND1}<div class="bigic2">{I(LOC)}</div>
<h1>空港にいるかを確かめるために、位置を使います</h1>
<p class="lead">このあと iPhone の確認が出ます。</p>
{why_list()}</div>
<div class="foot1"><div class="main" role="button">次へ</div><p>許可しなくても、図鑑・フライト・運用は見られます。<br>あとから iPhone の設定で変えられます。</p></div>'''

MAP_NOLOC = ('<div class="map0"><i style="left:20px;top:250px;width:160px;transform:rotate(-40deg)"></i><i style="left:120px;top:330px;width:220px;transform:rotate(30deg)"></i>'
             '<i style="left:200px;top:200px;width:200px;transform:rotate(70deg)"></i><em>日本全体を表示中</em></div>')

def home_noloc(card, extra=""):
    return f'{MAP_NOLOC}{W.MTOP}<div class="hsheet3 col"><div class="grab"></div>{card}{W.STAT}</div>{V.TAB_HOME}{extra}'

def build():
    # ---------- I1 位置の許可を頼む前の1枚（ログインか「デモで試す」のあと、はじめてホームを開く前に1回だけ）----------
    page("I1", "I1 位置を使う前の説明", i1_body())
    page("I1n", "I1n 位置を使う前の説明（夜）", i1_body(), "night")

    # ---------- I1b 「次へ」を押したあと：iPhone の確認が上に出る（ここは iOS が出す。描くのは場所と文だけ）----------
    i1b = i1_body() + f'''<div class="dim"></div><div class="osbox"><small>ここに iPhone の確認が出ます（iOS の画面）</small>
<b>「そらメモ」に位置情報の使用を許可しますか？</b>
<p>空港にいるかを確かめて、チェックインの印を押すために使います。いる場所は印を押すときと近くの空港を出すときだけ使い、ほかの人には見せません。</p>
<div class="ch"><span>1度だけ</span><span>アプリの使用中は許可</span><span>許可しない</span></div></div>'''
    page("I1b", "I1b iPhone の確認（見本の場所）", i1b)

    # ---------- I1c 許可しなかったとき：ホームの黒いカードの代わり ----------
    c = f'''<div class="nloc"><div class="t"><span class="wi">{I(LOCX)}</span><b>位置が使えないので、チェックインできません</b></div>
<p>iPhone の設定で、そらメモの位置情報を「このアプリの使用中」にすると使えます。</p>
<div class="bt"><span>デモで試す</span><span class="pri">設定を開く</span></div></div>'''
    page("I1c", "I1c 許可しなかったとき（ホーム）", home_noloc(c))

    # ---------- I1d 「正確な位置情報」がオフ（おおよその位置だけ）：判定範囲（約2km）より粗い ----------
    d = f'''<div class="nloc"><div class="t"><span class="wi">{I(LOC)}</span><b>「正確な位置情報」がオフです</b></div>
<p>おおよその位置では、判定範囲の中か確かめられません。設定で「正確な位置情報」をオンにしてください。</p>
<div class="acc"><span>いまの位置の誤差</span><b>3.2<small>km</small></b><span>（判定範囲 2.0km）</span></div>
<div class="bt"><span class="pri">設定を開く</span></div></div>'''
    page("I1d", "I1d 正確な位置情報がオフ（ホーム）", home_noloc(d))

    # ---------- I2 起動したときにつながらない（全画面）----------
    def i2_body():
        return f'''<div class="full1">{BRAND1}<div class="bigic2 offwi" style="color:#92400E">{I(CLOUDX)}</div>
<h1>いまはサーバーにつながりません</h1>
<p class="lead">電波のよい場所で「もう一度」を押してください。これまでの記録は消えていません。</p>
<ul class="why"><li><span class="wi">{I(WIFI0)}</span><div><b>機内モードやWi-Fiを確かめてください</b><span>機内では、Wi-Fi につながると使えます</span></div></li>
<li><span class="wi">{I(STAMP)}</span><div><b>空港にいるときは、つながってからチェックインできます</b><span>印は、その空港の判定範囲の中で押せます</span></div></li></ul></div>
<div class="foot1"><div class="main" role="button">もう一度</div></div>'''
    page("I2", "I2 起動したときにつながらない", i2_body())
    page("I2n", "I2n 起動したときにつながらない（夜）", i2_body(), "night")

    # ---------- I2b 使っている途中で切れた：シートの頭に帯（今の queuebar の置き場）。チェックインは保留して送る（今の動き）----------
    off = f'''<div class="offbar"><span class="wi">{I(WIFI0)}</span><div class="tx"><b>オフライン</b>チェックインは保留して、電波が戻ったら送ります</div></div>'''
    page("I2b", "I2b 使っている途中でオフライン（ホーム）", W.home(off + X.HND_CARD))

    # ---------- I2c チェックインを保留したあと（今の文のまま。帯の中で数を見せる）----------
    q = f'''<div class="offbar"><span class="wi">{I(WIFI0)}</span><div class="tx"><b>オフライン・保留 1件</b>羽田のチェックインを保留しました。電波が戻ったら自動で送ります（24時間以内）</div></div>'''
    page("I2c", "I2c チェックインを保留したあと", W.home(q + X.HND_CARD))

    # ---------- I3 アプリで隠すもの・言いかえるもの（一覧の表）----------
    rows = [
        ("「ホーム画面に追加しませんか」の帯", "#installBar・renderInstall()", "ホームのシートの頭に出る（iPhone なら出る）", "出さない", "todo",
         "アプリの中は isStandalone() が偽で IS_IOS が真なので、今のままだと帯が出る見込み"),
        ("マイページの「ホーム画面に追加」の行", "#installRow", "設定の中の1行", "出さない", "todo", ""),
        ("ホーム画面に追加するやり方のシート", "doInstall()", "Safari の共有ボタンの手順", "開かない", "todo", ""),
        ("通知の説明（ブラウザ向け）", "pushButtonHTML ほか3か所（11966・12675・14012 行あたり）", "「この端末のブラウザでは使えません（iPhone はホーム画面に追加…）」", "「アプリの通知は準備中です。」", "todo",
         "pushButtonHTML は直してある。ほかの3か所（運用・聞く・撮る人の画面）が古い文のまま"),
        ("位置が使えないときの文", "say()（4901・7113 行あたり）", "「ブラウザかアプリの設定で、このページの位置情報を…」", "「iPhone の設定 → そらメモ → 位置情報で『このアプリの使用中』にしてください」", "todo", ""),
        ("位置が使えない画面の文", "say()（4904 行あたり）", "「ブラウザで直接開くか、設定のデモモードで…」", "「設定のデモモードで試せます」", "todo", ""),
        ("カメラが使えないときの文", "#scanMsg（9464 行あたり）", "「ブラウザの設定でカメラを許可するか…」", "「iPhone の設定 → そらメモ → カメラをオンにするか…」", "todo", ""),
        ("保存できないときの文", "say()（4242 行あたり）", "「ブラウザの設定で保存が許可されているか…」", "「iPhone の空き容量を確かめてください」", "todo", ""),
        ("ピン止めの「iPhone はホーム画面に追加すると届きます」", "design/pin K0i・K5n（まだ作っていない画面）", "Safari で開いているときの1行とシート", "出さない（アプリの通知ができるまでは「準備中」の1行）", "todo", "ピン止めを作るときにチェックイン担当へ"),
        ("そらメモ＋の申し込み・解約", "renderPlusSettings", "申し込みのボタン", "「アプリの中では、そらメモ＋の申し込みはできません。」", "done", ""),
        ("ロボット除け（Turnstile）", "captchaOn", "ログインの箱", "出さない（自分用の段）", "done", ""),
    ]
    li = ""
    for t, fn, web, app, st, nb in rows:
        tag = '<span class="st2 done">済み</span>' if st == "done" else '<span class="st2 todo">これから</span>'
        nbh = f'<i></i><span style="color:var(--mute)">{nb}</span>' if nb else ""
        li += f'<li><b>{t}{tag}</b><span class="fn">{fn}</span><div class="ab"><i>web</i><s>{web}</s><i class="ap">アプリ</i><span>{app}</span>{nbh}</div></li>'
    i3 = f'''<div class="full"><div class="top"><h2>アプリで隠すもの・言いかえるもの</h2></div>
<p class="note" style="margin:0 0 8px">html[data-native="ios"] が付いているときだけ切り替える。ブラウザの形は変えない。</p>
<div class="card"><ul class="cmpT">{li}</ul></div></div>'''
    page("I3", "I3 アプリで隠すもの（一覧）", i3)

    # ---------- I3w いまの web のホーム（帯が出る）／I3h アプリのホーム（帯なし）----------
    qb = '''<div class="qbar"><span class="xmark">アプリでは出さない</span><b>ホーム画面に追加しませんか</b>アプリのように、ホーム画面からすぐに開けます。インストールは不要です。<div class="bt"><span>追加する</span><span>閉じる</span></div></div>'''
    page("I3w", "I3w 今のホーム（Safari）", W.home(qb + X.HND_CARD))
    page("I3h", "I3h アプリのホーム", W.home(X.HND_CARD + W.STAT))

    # ---------- I3m マイページの設定（アプリ）：消す行と言いかえる行 ----------
    m = f'''<div class="pad"><div class="brand"><b>マイページ</b><span>閉じる</span></div>
<div class="card mt"><div class="h"><b>この端末</b><small>アプリ（iPhone）</small></div><ul class="setl">
<li class="gone"><div class="tx"><b>ホーム画面に追加</b><span>アプリの中では出さない</span></div><span class="gonetag">出さない</span></li>
<li><div class="tx"><b>位置情報</b><span>このアプリの使用中・正確な位置情報 オン</span></div><span class="go">{I(CHEV)}</span></li>
<li><div class="tx"><b>スマホへの通知</b><span>アプリの通知は準備中です。</span></div></li>
<li><div class="tx"><b>夜の画面</b><span>いる場所の日の入り〜日の出は夜</span></div><span class="vl">自動</span><span class="go">{I(CHEV)}</span></li>
</ul></div>
<div class="card mt"><div class="h"><b>そらメモ＋</b></div><ul class="setl">
<li><div class="tx"><b>アプリの中では、そらメモ＋の申し込みはできません。</b><span>加入中の人の特典は、そのまま使えます</span></div></li></ul></div>
<p class="note">「位置情報」の行は押すと iPhone の設定のそらメモを開く。値は iPhone から読んだ今の状態。</p></div>'''
    page("I3m", "I3m マイページの設定（アプリ）", m)

    # ---------- 一覧 ----------
    L = [("① 位置の許可を頼む前の説明", [
            ("I1", "位置を使う前の説明の1枚", "ログインか「デモで試す」のあと、はじめてホームを開く前に1回だけ。ボタンは「次へ」1つ（閉じる・あとでは置かない）"),
            ("I1n", "同じ（夜の画面）", "主ボタンは白い字と縁、光る色は緑だけ"),
            ("I1b", "「次へ」のあと", "iPhone の確認が上に出る。iOS の画面なので描かず、場所と文（Info.plist の理由の文）だけ"),
            ("I1c", "許可しなかったとき（ホーム）", "黒いカードの代わりに「位置が使えないので、チェックインできません」。設定を開く・デモで試す"),
            ("I1d", "正確な位置情報がオフ", "おおよその位置（誤差が判定範囲より大きい）のとき")]),
         ("② オフライン", [
            ("I2", "起動したときにつながらない", "全画面。「もう一度」1つ。記録は消えていないと書く"),
            ("I2n", "同じ（夜の画面）", "印は琥珀の線"),
            ("I2b", "使っている途中で切れた", "シートの頭に「オフライン」の帯。チェックインは保留して送る（今の動き）"),
            ("I2c", "チェックインを保留したあと", "帯に「保留 1件」と今の文")]),
         ("③ アプリで隠すもの", [
            ("I3", "隠すもの・言いかえるもの（一覧）", "関数と今の文・アプリの文。「これから」はチェックイン担当へ"),
            ("I3w", "今のホーム（Safari）", "「ホーム画面に追加しませんか」の帯"),
            ("I3h", "アプリのホーム", "帯なし。ほかは web と同じ"),
            ("I3m", "マイページの設定（アプリ）", "「ホーム画面に追加」を出さない・位置情報の行・通知は準備中")])]
    body = '<div class="idx"><h1>iPhone のアプリだけの画面</h1><p>design/ios-app 1版（11/19）。チェックイン担当の依頼（11/18・report-ios-app-base.md）。アプリのコードは変えていない。通知の許可の前の1枚は、アプリの通知（APNs）ができてから。</p>'
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}<small>{s}</small></span></a></li>' for n, t, s in items) + "</ul>"
    body += "</div>"
    page("index", "iPhone のアプリだけの画面", body)

if __name__ == "__main__":
    build(); print("ok")
