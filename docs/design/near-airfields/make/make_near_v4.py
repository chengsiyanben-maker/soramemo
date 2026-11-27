# -*- coding: utf-8 -*-
# 近くの空港 4版：改善担当 review-3 の直し。使い方：python3 make_near_v4.py（地図は capture_v4.py が maps/*-v4-*.jpg に撮る）
# 3版（make_near_v3.py）の部品を読み込み、*-v4*.html に書き出す。アプリのコードは変えない
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_near as M
import make_near_v2 as V2
import make_near_v3 as V3
from make_near import strip, CHEV, OUT

X4 = """
/* 民間空港の札：ほかの札と同じ明るさの地（暗くしない） */
.ktag3.civ{background:#E8EDF4;color:#24426E}
/* 引き上げた位置：本番の sheetTop と同じ「画面の32%」。中は送れる。下が切れている合図に薄い影 */
.hs{--full-top:32vh}
.hs.full{overflow-y:auto;scrollbar-width:none}.hs.full::-webkit-scrollbar{display:none}
.fade4{position:absolute;left:0;right:0;bottom:84px;height:44px;z-index:19;pointer-events:none;background:linear-gradient(rgba(242,242,240,0),var(--bg) 85%)}
.fade4 i{position:absolute;left:50%;bottom:4px;width:36px;height:4px;margin-left:-18px;border-radius:2px;background:#C5CCD6}
/* 一覧：20km 以内だけを数える。民間空港の行は下に少し離して */
.list .civsec{margin:10px 0 2px;padding-top:4px}
.list .civsec .ch{padding:6px 16px 0;font-size:13px;font-weight:700;color:var(--sub)}
.list.civonly{margin-top:8px}
@media (max-height:700px){.list .nr2.r3{display:none}}
"""
XN4 = """
.ktag3.civ{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.18)}
.fade4{background:linear-gradient(rgba(5,7,11,0),var(--bg) 85%)}.fade4 i{background:#3A4654}
"""
KC = {'空港': 'civ', '飛行場': 'fd', '滑空場': 'gl'}
KL = {'空港': '民間空港', '飛行場': '飛行場', '滑空場': '滑空場'}

def ticket4(kind, code, name, ds, rows=(), within=False):
    """見出しは「いちばん近い」だけ。パタパタは民間空港でコードがあるときだけ、ほかは種類の札。
    右のピルは 20km 以内の数（「ほか○つ」）。20km 以内がなく民間空港の行だけのときは「民間空港 ›」"""
    n = sum(1 for r in rows if len(r) < 5)
    civ = any(len(r) >= 5 for r in rows)
    left = ('<div class="flap">%s</div>' % ''.join('<i>%s</i>' % c for c in code)) if code else '<span class="ktag3 %s">%s</span>' % (KC[kind], KL[kind])
    mo = ('<span class="more3">ほか%dつ%s</span>' % (n, CHEV)) if n else (('<span class="more3">民間空港%s</span>' % CHEV) if civ else '')
    st = ('<div class="stub"><span class="v">チェックイン</span><span class="s">→ 右へ引いて<br>印をもらう</span></div>' if within
          else '<div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div>')
    return ('<div class="bpass"><div class="bpm"><div class="lab">いちばん近い</div><div class="row1">%s%s</div>'
            '<div class="nm">%s</div><div class="ds">%s</div></div>%s</div>') % (left, mo, name, ds, st)

def lrow4(kind, name, km, pref='', civ=False, cls=''):
    return ('<div class="nr2%s"><span class="t %s">%s</span><span class="tx"><b>%s%s</b></span>'
            '<span class="k">%.1f<small class="u">km</small></span><span class="c">%s</span></div>') % (
        cls, {'空港': 'cv', '飛行場': 'fd', '滑空場': 'gl'}[kind], KL[kind], name, '<i class="pf">%s</i>' % pref if pref else '', km, CHEV)

def listcard4(rows, show=3):
    near = [r for r in rows if len(r) < 5]; civ = [r for r in rows if len(r) >= 5]
    body = ''.join(lrow4(*r[:4], cls=' r%d' % (i + 1)) for i, r in enumerate(near[:show]))
    allb = '<div class="all">すべて %dつ %s</div>' % (len(near), CHEV) if len(near) > show else ''
    cs = ('<div class="civsec"><div class="ch">民間空港でいちばん近い</div>%s</div>' % lrow4(*civ[0][:4])) if civ else ''
    if not near:
        return '<div class="near list civonly"><div class="lh">20km 以内<small>ほかはありません</small></div>%s</div>' % cs
    return '<div class="near list"><div class="lh">20km 以内<small>%dつ ・ 近い順</small></div>%s%s%s</div>' % (len(near), body, allb, cs)

def home4(path, title, mapname, inner, ann, night=False, extra='', full=False, scroll=None):
    base = M.CSS
    M.CSS = base + V2.X2 + V3.X3 + X4 + (V2.XN2 + V3.XN3 + XN4 if night else '')
    try:
        M.home(path, title, mapname, inner, ann, 0, night, (extra or '') + ('<div class="fade4"><i></i></div>' if full else ''))
    finally:
        M.CSS = base
    if full:
        p = os.path.join(OUT, path); s = open(p).read()
        s = s.replace('<div class="hs" id="hs">', '<div class="hs full" id="hs">', 1)
        if scroll:
            s = s.replace('</body>', '<script>document.getElementById("hs").scrollTop=%d</script></body>' % scroll)
        open(p, 'w').write(s)

def out_ds(km, night=False):
    return V3.out_ds(km, night)

U, R, K, O, Y, W = V3.USHIKU_L, V3.RYU_L, V3.KAZO_L, V3.OSAKA_L, V3.YAO_L, V3.KAWA_L

def build():
    home4('02-home-near-v4.html', 'ホーム：いちばん近いのが飛行場（4版）', 's02-v4',
          ticket4('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U) + strip(),
          '<b>02 4版：牛久のあたり</b>見出しは「いちばん近い」だけ（review-3 の2）。「ほか1つ」は 20km 以内の大利根飛行場だけを数える（成田 30.5km は数えず、一覧の下に分ける。review-3 の3）。開いたときは地図に点を出さない（review-3 の5）')
    home4('02b-home-near-full-v4.html', '引き上げた位置：近くの空港（4版）', 's02f-v4',
          ticket4('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U) + listcard4(U) + V3.STRIP3,
          '<b>02b 4版：引き上げた位置</b>シートの上の端は本番の sheetTop と同じ「画面の32%」（844＝270・667＝213）。一覧は「20km 以内 1つ」、その下に少し離して「民間空港でいちばん近い」成田。下が切れるときは中を送れる（下の端の薄い影が合図）。地図の点は一覧を開いたときだけ', full=True)
    home4('03-home-in-field-v4.html', 'ホーム：飛行場の判定範囲の中（4版）', 's03-v4',
          ticket4('飛行場', '', '竜ヶ崎飛行場', '<i class="dot ok"></i>判定範囲の中<br>飛行場の図鑑の印（16/86 とは別）', R, within=True) + strip(),
          '<b>03 4版：飛行場の判定範囲の中</b>「番外編の印」をやめ「飛行場の図鑑の印（16/86 とは別）」（review-3 の8。図鑑の飛行場の2版と同じく「番外編」の語を使わない）。成田 20.2km は 20km の外なので「ほか1つ」に数えない')
    home4('04-home-none-v4.html', 'ホーム：近くに何もない（4版）', 's04-v4',
          ticket4('空港', 'HND', '東京国際空港（羽田）', out_ds('14.7')) + strip(),
          '<b>04 4版：東京駅</b>見出しが「いちばん近い」になるだけで、ほかは今の本番と同じ')
    home4('06-home-osaka-v4.html', 'ホーム：大阪駅（4版）', 's06-v4',
          ticket4('空港', 'ITM', '大阪国際空港（伊丹）', out_ds('10.1'), O) + strip(),
          '<b>06 4版：大阪駅</b>先頭は伊丹（パタパタ ITM）。「ほか1つ」は八尾空港 15.3km')
    home4('06b-home-yao-v4.html', 'ホーム：八尾空港の近く（4版）', 's06b-v4',
          ticket4('飛行場', '', '八尾空港', out_ds('3.4'), Y) + strip(),
          '<b>06b 4版：八尾空港の近く</b>20km 以内にほかがなく、民間空港でいちばん近い伊丹（22.6km）だけがあるので、ピルは「民間空港 ›」（数は出さない）')
    home4('07-home-kazo-v4.html', 'ホーム：いちばん近いのが滑空場（4版）', 's07-v4',
          ticket4('滑空場', '', '加須滑空場', out_ds('6.3'), K) + strip(),
          '<b>07 4版：加須駅</b>「ほか6つ」（20km 以内だけ。調布 51.5km は数えない）。開いたときは地図に点を出さない（数と点が合わない問題をなくす）')
    home4('07b-home-kazo-full-v4.html', '引き上げた位置：加須（4版）', 's07f-v4',
          ticket4('滑空場', '', '加須滑空場', out_ds('6.3'), K) + listcard4(K) + V3.STRIP3,
          '<b>07b 4版：引き上げた位置</b>「20km 以内 6つ」の3行（667 は2行）＋「すべて 6つ ›」、その下に少し離して民間空港の調布。下が切れるので薄い影。地図には一覧の点（見える所だけ）', full=True)
    home4('07d-home-kazo-full-scrolled-v4.html', '引き上げた位置を送ったところ：加須（4版）', 's07f-v4',
          ticket4('滑空場', '', '加須滑空場', out_ds('6.3'), K) + listcard4(K) + V3.STRIP3,
          '<b>07d 4版：シートの中を送ったところ</b>一覧の続き・民間空港の行・今日の数字まで送って見られる（シートの上の端は動かない）', full=True, scroll=400)
    allrows = ''.join(lrow4(*r[:4]) for r in K if len(r) < 5)
    civ = [r for r in K if len(r) >= 5][0]
    sheet = ('<div class="dimbg"></div><section class="allsheet"><div class="gb"></div><div class="hl"><h3>20km 以内<small>加須滑空場のほか ・ 6つ ・ 近い順</small></h3>'
             '<span class="done">閉じる</span></div><div class="near list" style="box-shadow:none;margin:0">%s<div class="civsec"><div class="ch">民間空港でいちばん近い</div>%s</div></div></section>') % (allrows, lrow4(*civ[:4]))
    home4('07c-home-kazo-all-v4.html', 'すべて：加須（4版）', 's07-v4',
          ticket4('滑空場', '', '加須滑空場', out_ds('6.3'), K) + strip(),
          '<b>07c 4版：「すべて」</b>題は「20km 以内」。6つのあとに少し離して民間空港の行', extra=sheet)
    home4('08-home-chofu-v4.html', 'ホーム：調布駅（4版）', 's08-v4',
          ticket4('空港', '', '調布空港', out_ds('2.6')) + strip(),
          '<b>08 4版：調布駅</b>札は「民間空港」（ほかの札と同じ明るさ）。見出しが「いちばん近い」なので「空港」の語は名前の1回だけ。地図はズームのボタンの幅だけ右を空けて寄せ、「いまここ」が切れない（review-3 の4）')
    home4('09-home-kawagoe-v4.html', 'ホーム：川越駅（4版）', 's09-v4',
          ticket4('飛行場', '', 'ホンダエアポート', out_ds('8.5'), W) + strip(),
          '<b>09 4版：川越駅</b>20km 以内にほかがないのでピルは「民間空港 ›」（調布 26.5km）')
    home4('02-home-near-v4-night.html', '夜：ホーム 02（4版）', 's02n-v4',
          ticket4('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3', True), U) + strip(),
          '<b>夜：02 4版</b>札は色なし。光るのは距離の数字と「いまここ」だけ', night=True)
    home4('07b-home-kazo-full-v4-night.html', '夜：引き上げた位置（4版）', 's07fn-v4',
          ticket4('滑空場', '', '加須滑空場', out_ds('6.3', True), K) + listcard4(K) + V3.STRIP3,
          '<b>夜：07b 4版</b>昼と同じ位置（画面の32%）・同じ送り方', night=True, full=True)

def build_flap():
    css = M.CSS + V2.X2 + V3.X3 + X4 + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}"""
    A = ticket4('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U)
    B = ('<div class="bpass"><div class="bpm"><div class="lab">いちばん近い</div><div class="row1"><span class="ktag3 fd">飛行場</span><span class="more3">ほか1つ%s</span></div>'
         '<div class="nm">竜ヶ崎飛行場</div><div class="ds">%s</div></div><div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div></div>'
         '<div class="bpass" style="margin-top:8px;min-height:0"><div class="bpm" style="border-radius:24px"><div class="lab">民間空港でいちばん近い</div><div class="row1"><div class="flap"><i>N</i><i>R</i><i>T</i></div></div>'
         '<div class="nm">成田国際空港</div><div class="ds">ここから <b>30.5km</b></div></div></div>') % (CHEV, out_ds('11.3'))
    body = ('<div class="cmpw"><h1>10 パタパタがずれるとき</h1><p>先頭が飛行場・滑空場のとき（牛久のあたり）。パタパタは「民間空港でコードがあるとき」だけに使う決まりのまま、どう見せるか</p>'
            '<h2><span class="rec">おすすめ</span>A 先頭に合わせて、パタパタの代わりに札</h2>%s'
            '<p class="why">半券は1枚・高さは今と同じ。パタパタは先頭が民間空港でコードがあるときだけ回る（調布のようにコードのない民間空港も札）</p>'
            '<p class="why"><b>A だとホームからパタパタが消える場面</b>：牛久（竜ヶ崎飛行場）・八尾の近く（八尾空港）・加須（加須滑空場）・川越（ホンダエアポート）・調布駅（調布空港）など、先頭が飛行場・滑空場か、コードのない民間空港のとき</p>'
            '<h2>B 民間空港のパタパタを別の札で残す</h2>%s'
            '<p class="why">成田のパタパタはいつも見えるが、シートが約120px 高くなり地図が狭くなる。「いちばん近い」が2枚あって、どちらで印をもらうか迷う</p></div>') % (A, B)
    open(os.path.join(OUT, '10-flap-v4.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>パタパタがずれるとき</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, body))

G4 = [('02-home-near-v4', '02 牛久（ほか1つ）'), ('02b-home-near-full-v4', '02b 引き上げた位置'), ('03-home-in-field-v4', '03 飛行場の中'),
      ('04-home-none-v4', '04 ほかがない'), ('06-home-osaka-v4', '06 大阪駅'), ('06b-home-yao-v4', '06b 八尾空港の近く（民間空港 ›）'),
      ('07-home-kazo-v4', '07 加須（ほか6つ）'), ('07b-home-kazo-full-v4', '07b 引き上げた位置'), ('07d-home-kazo-full-scrolled-v4', '07d 送ったところ'),
      ('07c-home-kazo-all-v4', '07c すべて'), ('08-home-chofu-v4', '08 調布駅'), ('09-home-kawagoe-v4', '09 川越駅'), ('10-flap-v4', '10 パタパタがずれるとき'),
      ('02-home-near-v4-night', '夜：02'), ('07b-home-kazo-full-v4-night', '夜：07b')]

def build_index():
    css = M.CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:16px 16px 60px}
h1{font-size:24px;margin:8px 4px 0;color:var(--strong)}h2{font-size:18px;margin:26px 4px 0;color:var(--strong)}.w p{font-size:13px;color:var(--sub);margin:6px 4px}
.th{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.th a{text-decoration:none;color:var(--strong);font-size:13px;font-weight:700}
.th img{width:100%;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}.th small{display:block;font-weight:600;color:var(--sub)}"""
    th = lambda G, v4=False: '<div class="th">%s</div>' % ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s%s</a>' % (f, f, c, '<small>667：png/%s-667.png</small>' % f if v4 else '') for f, c in G)
    s = ('<div class="w"><h1>近くの空港（飛行場・滑空場も）</h1><p>ブランチ design/near-airfields。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667。地図は main の web/ をデモで開いて撮った写真（先頭と点は撮るときに足した）</p>'
         '<h2>4版（改善担当 review-3 の直し） ← 本人に見せるのはこちら</h2>'
         '<p>見出しは「いちばん近い」。札は飛行場・滑空場・民間空港。「ほか○つ」は 20km 以内だけ、民間空港でいちばん近い1つは一覧の下に分ける。引き上げた位置は本番と同じ画面の32%%で、中は送れる。開いたときは地図に点を出さない</p>%s'
         '<h2>3版（記録）</h2>%s<h2>2版（記録）</h2>%s<h2>1版（記録）</h2>%s</div>') % (th(G4, True), th(V3.G3), th(V2.G2), th(V2.G1))
    open(os.path.join(OUT, 'index.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>近くの空港に飛行場も</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, s))

if __name__ == '__main__':
    build(); build_flap(); build_index()
