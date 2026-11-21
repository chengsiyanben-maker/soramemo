# -*- coding: utf-8 -*-
# iPhone のアプリだけの画面案 2版（PM の指示 11/19 9時55分）。1版（make_ios.py）の部品を使う。
# 1 位置の説明：理由は「空港にいるかを確かめて印を押すため・使用中のみ・印を押すときだけ送る」。カメラ（搭乗券）とマイク（管制の聞き取り）は使うときの小さい版
# 2 電波がないとき：アプリには画面が全部入っている前提。データが読めないカードの形と「もう一度」
# 3 位置を許可しなかった人：設定アプリへの道・デモで試す
# 4 アプリで隠すものの一覧と、代わりに出す1行
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "lib"))
import make_ios as B
import make_v2 as V
import make_v3 as W
import make_v4 as X
from base_ops import I, CHEV, DOWN, INFO, SHARE, PLANE, TOWER, TABBAR
OUT = B.OUT

CSS2 = r"""
/* 2版：データが読めないカード（どの画面のカードも同じ形。枠と題は残し、中身の代わりにこの形） */
.nod{display:flex;align-items:center;gap:12px;padding:6px 0 2px}
.nod .wi{flex:none;width:40px;height:40px;border-radius:50%;background:var(--pill);color:var(--mute);display:flex;align-items:center;justify-content:center}
.nod .wi svg{width:20px;height:20px}
.nod .tx{flex:1;min-width:0}
.nod .tx b{display:block;font-size:15px;font-weight:800}
.nod .tx span{display:block;font-size:13px;line-height:1.55;color:var(--mute)}
.nod .re{flex:none;height:44px;padding:0 16px;border-radius:999px;background:var(--pill);display:inline-flex;align-items:center;font-size:14px;font-weight:800;color:var(--ink2)}
.last{display:block;font-size:13px;color:var(--sub);margin-top:8px}
.offtop{display:flex;align-items:center;gap:10px;background:#FFF7E6;border-radius:18px;padding:10px 12px;margin-top:12px;box-shadow:inset 0 0 0 1px rgba(146,64,14,.12)}
.offtop .wi{flex:none;width:32px;height:32px;border-radius:50%;background:#FEF3C7;color:#92400E;display:flex;align-items:center;justify-content:center}
.offtop .wi svg{width:18px;height:18px}
.offtop .tx{flex:1;font-size:13px;line-height:1.55;color:#5B3A0A}
.offtop .tx b{display:block;font-size:14px;color:#3B2606}
body.night .offtop,body.night .offbar{background:transparent;box-shadow:inset 0 0 0 1.5px rgba(233,161,75,.55)}
body.night .offtop .wi,body.night .offbar .wi{background:transparent;color:#E9A14B}
body.night .offtop .tx,body.night .offtop .tx b{color:#E9A14B}
body.night .nod .re{color:#DCE3EA}
body.night .tabbar{background:rgba(22,25,31,.96)}
body.night .brand span,body.night .mode span.on{background:#1D232C;color:#DCE3EA}
body.night .mode{background:#16191F}
body.night .tabbar span.on{color:#DCE3EA}
body.night .ksw span.on{background:transparent;color:#fff;box-shadow:inset 0 0 0 2px #DCE3EA}
body.night .apsel i{background:#DCE3EA;color:#0E1014}
/* 地図のタイルが読めないとき（線と空港の点は中に入っているので出る） */
.mapoff{background:repeating-linear-gradient(45deg,#E3E8EE 0 10px,#DDE3EA 10px 20px)!important}
.mapnote{position:absolute;left:50%;top:140px;transform:translateX(-50%);z-index:2;font-size:13px;font-weight:800;color:#5B6B7D;background:rgba(255,255,255,.85);border-radius:999px;padding:6px 14px;white-space:nowrap}
/* 使うときの小さい説明（カメラ・マイク）：シートだが下に引いて閉じる取っ手は付けない */
.ask{position:fixed;left:50%;transform:translateX(-50%);bottom:0;width:390px;background:var(--card);border-radius:26px 26px 0 0;padding:22px 20px 34px;z-index:9;box-shadow:0 -18px 40px -20px rgba(15,23,42,.5)}
.ask .hd{display:flex;align-items:center;gap:12px}
.ask .hd .wi{flex:none;width:52px;height:52px;border-radius:50%;background:var(--pill);color:var(--navy);display:flex;align-items:center;justify-content:center}
.ask .hd .wi svg{width:26px;height:26px}
.ask .hd b{font-size:19px;font-weight:900;line-height:1.4}
.ask p{font-size:14px;line-height:1.7;color:var(--ink2);margin:12px 0 0}
.ask ul{margin:8px 0 0;padding:0 0 0 18px;font-size:14px;line-height:1.7;color:var(--ink2)}
.ask .main{height:52px;margin-top:16px;border-radius:999px;background:var(--navy);color:#fff;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800}
.ask small{display:block;font-size:13px;line-height:1.6;color:var(--mute);margin-top:10px;text-align:center}
/* 設定アプリへの道（文字だけ。iOS の画面は描かない） */
.path{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-top:10px;font-size:13px;font-weight:800;color:var(--ink2)}
.path span{background:var(--pill);border-radius:999px;padding:3px 10px}
.path i{font-style:normal;color:var(--sub)}
"""
CSS = B.CSS + CSS2

def page(name, title, body, cls=""):
    html = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body class="{cls}">{body}</body></html>"""
    open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8").write(html)

CAM = '<path d="M4 8h3l1.5-2.5h7L17 8h3v11H4Z"/><circle cx="12" cy="13" r="3.5"/>'
MIC = '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0"/><path d="M12 17.5V21"/>'
SEND = '<path d="M4 12 20 4l-5 16-3-7Z"/><path d="m12 13 8-9"/>'
RELOAD = '<path d="M19 12a7 7 0 1 1-2.1-5"/><path d="M19 4v4h-4"/>'
HOME_I = '<path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/>'

# 決定の理由の文（PM の指示 11/19・report-ios-app-plan.md の案）。src/index.html を見た限り、位置を送るのは checkin の関数だけ
WHY2 = [(B.STAMP, "空港にいるかを確かめて、印を押すために使います", "空港ごとに決めた判定範囲の中でだけ、チェックインの印を押せます"),
        (SEND, "いる場所を送るのは、印を押すときだけです", "近くの空港を近い順に並べるのは、この iPhone の中で計算します"),
        (B.CLOCK, "使うのは、そらメモを開いている間だけです", "いる場所を、ほかの人に見せることはありません")]
PLIST2 = "空港にいるかを確かめて、チェックインの印を押すために使います。いる場所は印を押すときだけ送り、ほかの人には見せません。"

def why2():
    return '<ul class="why">' + "".join(f'<li><span class="wi">{I(ic)}</span><div><b>{b}</b><span>{s}</span></div></li>' for ic, b, s in WHY2) + "</ul>"

def i1_body():
    return f'''<div class="full1">{B.BRAND1}<div class="bigic2">{I(B.LOC)}</div>
<h1>空港にいるかを確かめるために、位置を使います</h1>
<p class="lead">このあと iPhone の確認が出ます。</p>
{why2()}</div>
<div class="foot1"><div class="main" role="button">次へ</div><p>許可しなくても、図鑑・フライト・運用は見られます。<br>あとから iPhone の設定で変えられます。</p></div>'''

def nod(title="読み込めませんでした", sub="電波が戻ると、自動で読み直します"):
    return f'<div class="nod"><span class="wi">{I(B.WIFI0)}</span><div class="tx"><b>{title}</b><span>{sub}</span></div><span class="re" role="button">もう一度</span></div>'

TAB_OPS = TABBAR
def ops_top():
    return f'<div class="pad">{V.M.TOP if hasattr(V, "M") else ""}'

def build():
    # ---------- ① 位置の説明（2版の理由の文）----------
    page("I1-v2", "I1 位置を使う前の説明 2版", i1_body())
    page("I1n-v2", "I1n 位置を使う前の説明 2版（夜）", i1_body(), "night")
    i1b = i1_body() + f'''<div class="dim"></div><div class="osbox"><small>ここに iPhone の確認が出ます（iOS の画面）</small>
<b>「そらメモ」に位置情報の使用を許可しますか？</b><p>{PLIST2}</p>
<div class="ch"><span>1度だけ</span><span>アプリの使用中は許可</span><span>許可しない</span></div></div>'''
    page("I1b-v2", "I1b iPhone の確認（見本の場所）2版", i1b)

    # ---------- ① カメラ（搭乗券）：「搭乗券を読み取る」を初めて押したとき ----------
    from base_ops import TOP as BTOP
    bp = f'''<div class="pad">{BTOP}<div class="card mt"><div class="h"><b>搭乗券</b><small>右上のボタンで読み取る</small></div>
<ul class="rows"><li><div class="tx"><b>JL 323 羽田→福岡</b><span>11/19・B737-800</span></div></li></ul></div></div>{TAB_OPS.replace('<span class="on">','<span>')}'''
    cam = bp + f'''<div class="dim"></div><div class="ask" role="dialog"><div class="hd"><span class="wi">{I(CAM)}</span><b>搭乗券のバーコードを、カメラで読みます</b></div>
<p>読んだ便名と日付で、乗った便を記録します。カメラを使うのは、この画面を開いている間だけです。</p>
<div class="main" role="button">次へ</div><small>このあと iPhone の確認が出ます。許可しなくても、便名を打って記録できます。</small></div>'''
    page("I4c-v2", "I4c カメラを使う前（搭乗券）", cam)

    # ---------- ① マイク（管制の聞き取り）：「スマホで受信」を初めて押したとき ----------
    atc = f'''<div class="pad">{BTOP}<div class="card mt"><div class="h"><b>いま聞く周波数</b><small>羽田</small></div>
<ul class="rows"><li><div class="tx"><b>東京タワー 124.35</b><span>北風運用・34L／34R 着陸</span></div></li></ul></div></div>{TAB_OPS}'''
    mic = atc + f'''<div class="dim"></div><div class="ask" role="dialog"><div class="hd"><span class="wi">{I(MIC)}</span><b>管制の音声を、マイクで聞き取ります</b></div>
<p>受信機の音をマイクで拾って、文字にします。<b>音声はこの iPhone の中だけで処理し、送りません。</b></p>
<div class="main" role="button">次へ</div><small>このあと iPhone の確認が出ます。はじめての日は、文字にする部品（約80MB）を読み込みます。</small></div>'''
    page("I4m-v2", "I4m マイクを使う前（管制の聞き取り）", mic)

    # ---------- ③ 位置を許可しなかった人（ホーム）：設定アプリへの道・デモで試す ----------
    c = f'''<div class="nloc"><div class="t"><span class="wi">{I(B.LOCX)}</span><b>位置が使えないので、チェックインできません</b></div>
<p>設定でそらメモの位置情報を「このアプリの使用中」にすると使えます。</p>
<div class="path"><span>設定</span><i>›</i><span>アプリ</span><i>›</i><span>そらメモ</span><i>›</i><span>位置情報</span></div>
<div class="bt"><span>デモで試す</span><span class="pri">設定を開く</span></div></div>'''
    page("I1c-v2", "I1c 位置を許可しなかった人（ホーム）2版", B.home_noloc(c))
    # 半券を押したとき（許可しなかった人）：小さいシートで同じ2つ
    d = B.home_noloc(c) + f'''<div class="dim"></div><div class="ask" role="dialog"><div class="hd"><span class="wi" style="background:#FEF3C7;color:#92400E">{I(B.LOCX)}</span><b>印を押すには、位置が要ります</b></div>
<p>いまは位置の使用を許可していません。設定で「このアプリの使用中」にすると、空港にいるかを確かめて印を押せます。</p>
<div class="path"><span>設定</span><i>›</i><span>アプリ</span><i>›</i><span>そらメモ</span><i>›</i><span>位置情報</span></div>
<div class="main" role="button">設定を開く</div><div class="sec" style="height:48px;margin-top:8px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;background:var(--pill);color:var(--ink2)">デモで試す</div></div>'''
    page("I1e-v2", "I1e 許可しなかった人が印を押そうとしたとき", d)

    # ---------- ② 電波がないとき（アプリの中に画面は入っている）----------
    # ホーム：地図のタイルだけ出ない。判定はこの iPhone の中でできるので、チェックインは保留して送る（今の動き）
    mp = W.MAP.replace('class="map3"', 'class="map3 mapoff"')
    off = f'''<div class="offbar"><span class="wi">{I(B.WIFI0)}</span><div class="tx"><b>電波がありません</b>チェックインは保留して、電波が戻ったら送ります</div></div>'''
    home_off = f'{mp}<span class="mapnote">地図の絵は電波が戻ると出ます</span>{W.MTOP}<div class="hsheet3 col"><div class="grab"></div>{off}{X.HND_CARD}</div>{V.TAB_HOME}'
    page("I2-v2", "I2 電波がないとき（ホーム）2版", home_off)

    # 運用タブ：カードの枠と題は残し、中身の代わりに「読み込めませんでした・もう一度」。最後に読んだ時刻があれば出す
    def ops_off(cls=""):
        return f'''<div class="pad">{BTOP}{X.W.krow("HND", "羽田") if hasattr(X, "W") else W.krow()}
<div class="offtop"><span class="wi">{I(B.WIFI0)}</span><div class="tx"><b>電波がありません</b>戻ると、自動で読み直します</div></div>
<div class="card mt"><div class="h"><b>いまの運用</b><small>実際の機体から判定</small></div>{nod()}<span class="last">最後に読んだのは 15:02（北風運用）</span></div>
<div class="card mt"><div class="h"><b>これから着く便</b><small>到着｜出発</small></div>{nod()}</div>
<div class="card mt"><div class="h"><b>近くを飛ぶ機体</b><small>adsb.lol</small></div>{nod("いまは出せません", "機体の位置は電波があるときだけ読みます")}</div>
</div>{TAB_OPS}'''
    page("I5-v2", "I5 電波がないとき（運用タブ）", ops_off())
    page("I5n-v2", "I5n 電波がないとき（運用タブ・夜）", ops_off(), "night")
    # 図鑑：自分の記録はこの iPhone に入っているので、そのまま見られる（帯だけ）
    zk = f'''<div class="pad">{BTOP}
<div class="offtop"><span class="wi">{I(B.WIFI0)}</span><div class="tx"><b>電波がありません</b>図鑑とフライトは、この iPhone の記録で見られます</div></div>
<div class="card mt"><div class="h"><b>空港の図鑑</b><small>この iPhone の記録</small></div>
<div style="display:flex;align-items:baseline;gap:6px"><b style="font-size:44px;font-weight:900;line-height:1">16</b><small style="font-size:15px;color:var(--sub);font-weight:700">/ 86 空港</small></div>
<span class="last">サーバーと合わせるのは、電波が戻ってから</span></div>
<div class="card mt"><div class="h"><b>空港ページの「空港の今」</b><small>羽田</small></div>{nod()}</div></div>{V.TAB_BOOK}'''
    page("I5z-v2", "I5z 電波がないとき（図鑑）", zk)

    # ---------- ④ アプリで隠すもの：代わりに出す1行 ----------
    rows = [
        ("「ホーム画面に追加しませんか」の帯（ホーム）", "#installBar・renderInstall()", "出さない（代わりの1行もなし）", "アプリの中では isStandalone() が偽・IS_IOS が真なので、今のままだと出る見込み"),
        ("マイページの「ホーム画面に追加」の行", "#installRow", "出さない（代わりの1行もなし）", ""),
        ("ホーム画面に追加するやり方のシート", "doInstall()", "開かない", ""),
        ("そらメモ＋の申し込み・解約のボタン", "renderPlusSettings（済み）", "「アプリの中では、そらメモ＋の申し込みはできません。」加入中の人は「加入中（次の更新 ○月○日）」", ""),
        ("通知の説明（運用・聞く・撮る人の3か所）", "pushButtonHTML（済み）ほか3か所", "「アプリの通知は準備中です。」", "3か所が「この端末のブラウザでは使えません（iPhone はホーム画面に追加…）」のまま"),
        ("位置が許可されていないとき", "say()（4901・7113 行あたり）", "「位置の使用が許可されていません。設定 › アプリ › そらメモ › 位置情報で『このアプリの使用中』にしてください。」＋設定を開く", ""),
        ("位置が使えない画面", "say()（4904 行あたり）", "「位置を使えませんでした。設定のデモモードで試せます。」", ""),
        ("カメラが許可されていないとき", "#scanMsg（9464 行あたり）", "「カメラの使用が許可されていません。設定 › アプリ › そらメモ › カメラ、または「画像から読み取る」で。」", ""),
        ("マイクが許可されていないとき", "atcRxDraw()（12623 行あたり）", "「マイクの使用が許可されていません。設定 › アプリ › そらメモ › マイクで。」", ""),
        ("保存できないとき", "say()（4242 行あたり）", "「この iPhone に保存できませんでした。空き容量を確かめてください。」", ""),
        ("ピン止めの「iPhone はホーム画面に追加すると届きます」", "design/pin K0i・K5n（まだ作っていない）", "出さない（通知ができるまで「アプリの通知は準備中です。」）", ""),
        ("ロボット除け（Turnstile）", "captchaOn（済み）", "出さない（自分用の段）", ""),
    ]
    li = ""
    for t, fn, app, nb in rows:
        done = "済み" in fn
        tag = '<span class="st2 done">済み</span>' if done else '<span class="st2 todo">これから</span>'
        nbh = f'<i></i><span style="color:var(--mute)">{nb}</span>' if nb else ""
        li += f'<li><b>{t}{tag}</b><span class="fn">{fn}</span><div class="ab"><i class="ap">代わり</i><span>{app}</span>{nbh}</div></li>'
    i3 = f'''<div class="full"><div class="top"><h2>アプリで隠すもの・代わりに出す1行</h2></div>
<p class="note" style="margin:0 0 8px">html[data-native="ios"]（NATIVE）のときだけ切り替える。ブラウザの形と文は変えない。</p>
<div class="card"><ul class="cmpT">{li}</ul></div></div>'''
    page("I3-v2", "I3 アプリで隠すもの・代わりの1行 2版", i3)

    # ---------- 一覧 ----------
    L = [("2版（PM の指示 11/19 9時55分）", [
            ("I1-v2", "位置を使う前の説明の1枚", "理由は「印を押すため・使用中のみ・印を押すときだけ送る」。ボタンは「次へ」1つ"),
            ("I1n-v2", "同じ（夜の画面）", "主ボタンは白い字と縁、光る色は緑だけ"),
            ("I1b-v2", "「次へ」のあと", "iPhone の確認の場所。文は新しい理由の文（Info.plist も合わせる）"),
            ("I4c-v2", "カメラを使う前（搭乗券）", "「搭乗券を読み取る」を初めて押したときの小さい版"),
            ("I4m-v2", "マイクを使う前（管制の聞き取り）", "「スマホで受信」を初めて押したときの小さい版"),
            ("I1c-v2", "位置を許可しなかった人（ホーム）", "設定アプリへの道（字だけ）・設定を開く・デモで試す"),
            ("I1e-v2", "許可しなかった人が印を押そうとしたとき", "小さいシートで同じ2つ"),
            ("I2-v2", "電波がないとき（ホーム）", "画面はアプリの中。地図の絵だけ出ない。チェックインは保留して送る"),
            ("I5-v2", "電波がないとき（運用タブ）", "カードの枠と題は残し、中身の代わりに「読み込めませんでした・もう一度」"),
            ("I5n-v2", "同じ（夜の画面）", "帯は琥珀の線"),
            ("I5z-v2", "電波がないとき（図鑑）", "自分の記録は見られる。サーバーのデータのカードだけ同じ形"),
            ("I3-v2", "アプリで隠すもの・代わりに出す1行", "「これから」はチェックイン担当へ")]),
         ("1版（比べる用に残す）", [
            ("I1", "位置を使う前の説明", ""), ("I1d", "正確な位置情報がオフ", "2版でもそのまま使う"),
            ("I2", "起動したときにつながらない（全画面）", "部品をアプリに入れるまでの形"), ("I2b", "使っている途中で切れた", ""), ("I2c", "保留したあと", "2版でもそのまま使う"),
            ("I3", "隠すもの（1版の表）", ""), ("I3w", "今のホーム（Safari）", ""), ("I3h", "アプリのホーム", ""), ("I3m", "マイページの設定（アプリ）", "2版でもそのまま使う")])]
    body = '<div class="idx"><h1>iPhone のアプリだけの画面</h1><p>design/ios-app 2版（11/19・PM の指示 9時55分）。改善担当に見てもらう前提の一覧。アプリのコードは変えていない。通知の許可の前の1枚は、アプリの通知（APNs）ができてから。</p>'
    for h, items in L:
        body += f"<h2>{h}</h2><ul>" + "".join(f'<li><a href="{n}.html"><b>{n}</b><span>{t}{f"<small>{s}</small>" if s else ""}</span></a></li>' for n, t, s in items) + "</ul>"
    body += "</div>"
    page("index", "iPhone のアプリだけの画面", body)

if __name__ == "__main__":
    B.build(); build(); print("ok")
