# -*- coding: utf-8 -*-
# 近くの空港 3版：民間空港と飛行場・滑空場を分けずに近い順に並べる（11/11 17時 本人の決定）。使い方：python3 make_near_v3.py
# 1版（make_near.py）・2版（make_near_v2.py）の部品を読み込む。出力は *-v3*.html。地図は capture_v3.py が maps/*-v3-*.jpg に撮る
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_near as M
import make_near_v2 as V2
from make_near import strip, CHEV, OUT

X3 = """
/* 半券：パタパタの段（民間空港でコードがあるときだけ）か種類の札の段。右に「ほか○つ」 */
.bpass{height:175px;min-height:175px}.bpm{padding:10px 12px 10px 18px}
.row1{display:flex;align-items:center;gap:8px;min-height:44px;margin:0 0 2px}
.row1 .flap{margin:0}
.ktag3{display:inline-flex;align-items:center;height:30px;padding:0 12px;border-radius:999px;font-size:14px;font-weight:800;letter-spacing:.04em}
.ktag3.civ{background:rgba(255,255,255,.14);color:#F3F4F6}
.ktag3.fd{background:#DCEBDF;color:#24502F}.ktag3.gl{background:#D7EAF6;color:#134F72}
.more3{margin-left:auto;flex:none;display:inline-flex;align-items:center;gap:2px;min-height:44px;min-width:44px;padding:0 8px 0 14px;border-radius:999px;background:rgba(255,255,255,.12);color:#F3F4F6;font-size:13px;font-weight:800;white-space:nowrap}
.more3 svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;}
.bpm .ds2{font-size:13px;line-height:1.5;color:var(--hero-sub)}
/* 一覧の行 */
.t.cv{background:#E8EDF4;color:#24426E}
.nr2 .tx b .pf{font-style:normal;font-size:13px;font-weight:600;color:var(--mute);margin-left:6px}
.nr2 .tx small.cl{color:#24426E}
.list .all{display:flex;align-items:center;justify-content:center;gap:4px;min-height:48px;margin:2px 10px 6px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--strong)}
.list .all svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
/* すべてのシート */
.allsheet{position:absolute;left:0;right:0;bottom:0;top:96px;background:var(--card);border-radius:28px 28px 0 0;box-shadow:0 -10px 40px -10px rgba(15,23,42,.4);z-index:50;padding:10px 12px 28px;overflow:hidden}
.allsheet .gb{width:40px;height:5px;border-radius:3px;background:#D5DAE1;margin:2px auto 8px}
.allsheet .hl{display:flex;align-items:center;gap:10px;padding:0 6px 6px}
.allsheet h3{margin:0;font-size:20px;color:var(--strong);flex:1}.allsheet h3 small{display:block;font-size:13px;font-weight:600;color:var(--sub)}
/* 比べるページ */
.cmpw{padding:16px 16px 40px}.cmpw h1{font-size:22px;margin:6px 4px 2px;color:var(--strong)}.cmpw>p{font-size:13px;color:var(--sub);margin:4px 4px 0}
.cmpw h2{display:flex;align-items:center;gap:8px;font-size:16px;margin:22px 4px 8px;color:var(--strong)}
.rec{flex:none;white-space:nowrap;display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;background:#16233A;color:#fff;font-size:13px;font-weight:800}
.cmpw .why{font-size:13px;line-height:1.65;color:var(--ink);margin:8px 4px 0}
.civline{margin-top:6px;font-size:13px;color:var(--hero-sub)}.civline b{color:#F3F4F6;font-weight:800}
"""
XN3 = """
.ktag3.fd,.ktag3.gl,.ktag3.civ{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.18)}
.more3{background:#141B24;color:#DCE3EA;box-shadow:inset 0 0 0 1px rgba(220,227,234,.5)}
.t.cv{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}
.nr2 .tx small.cl{color:#AEB9C6}
.list .all{background:#141B24;color:#DCE3EA}
"""
KC = {'空港': 'civ', '飛行場': 'fd', '滑空場': 'gl', 'ヘリポート': 'fd'}
KR = {'空港': 'cv', '飛行場': 'fd', '滑空場': 'gl', 'ヘリポート': 'fd'}

def ticket3(kind, code, name, ds, more=0, within=False, night=False, civline=''):
    """先頭の1つの半券。民間空港でコードがあればパタパタ、なければ種類の札。右に「ほか○つ ›」（押すと引き上げて一覧へ）"""
    left = ('<div class="flap">%s</div>' % ''.join('<i>%s</i>' % c for c in code)) if code else '<span class="ktag3 %s">%s</span>' % (KC[kind], kind)
    mo = '<span class="more3">ほか%dつ%s</span>' % (more, CHEV) if more else ''
    st = ('<div class="stub"><span class="v">チェックイン</span><span class="s">→ 右へ引いて<br>印をもらう</span></div>' if within
          else '<div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div>')
    return ('<div class="bpass"><div class="bpm"><div class="lab">いちばん近い空港</div><div class="row1">%s%s</div>'
            '<div class="nm">%s</div><div class="ds">%s</div>%s</div>%s</div>') % (left, mo, name, ds, civline, st)

def out_ds(km, night=False):
    return '<i class="dot"></i>判定範囲の外 ・ ここから %s' % (('<b class="lit">%s</b> km' % km) if night else '<b>%skm</b>' % km)

def lrow(kind, name, km, pref='', civ_label=False):
    lab = '<small class="cl">民間空港でいちばん近い</small>' if civ_label else ''
    return ('<div class="nr2"><span class="t %s">%s</span><span class="tx">%s<b>%s%s</b></span>'
            '<span class="k">%.1f<small class="u">km</small></span><span class="c">%s</span></div>') % (
        KR[kind], kind, lab, name, '<i class="pf">%s</i>' % pref if pref else '', km, CHEV)

def listcard(rows, total, show=3):
    body = ''.join(lrow(*r) for r in rows[:show])
    allb = '<div class="all">すべて %dつ %s</div>' % (total, CHEV) if total > show else ''
    return '<div class="near list"><div class="lh">近くの空港<small>20km 以内 ＋ 民間空港 ・ ほか%dつ</small></div>%s%s</div>' % (total, body, allb)

STRIP3 = ('<div class="strip3"><div><span>今日の印</span><b>0</b></div><div><span>空港</span><b>16</b><small class="u">/86</small></div>'
          '<div><span>フライト</span><b>30</b></div></div>')

def home3(path, title, mapname, inner, ann, night=False, extra='', full_top=None):
    base = M.CSS
    M.CSS = base + V2.X2 + X3 + (V2.XN2 + XN3 if night else '') + ('.hs{--full-top:%dpx}' % full_top if full_top else '')
    try:
        M.home(path, title, mapname, inner, ann, 0, night, extra)
    finally:
        M.CSS = base
    if full_top:
        p = os.path.join(OUT, path); s = open(p).read()
        s = s.replace('<div class="hs" id="hs">', '<div class="hs full" id="hs">', 1)
        open(p, 'w').write(s)

# ---------- 場面（距離は本番の座標で計算。基地は入れない） ----------
# 牛久：竜ヶ崎飛行場 11.3・大利根飛行場 15.3（20km 以内）。民間空港でいちばん近いのは成田 30.5（ターミナルまで）
USHIKU_L = [('飛行場', '大利根飛行場', 15.3, '茨城'), ('空港', '成田国際空港', 30.5, '千葉', True)]
# 竜ヶ崎飛行場の中：大利根 5.2、成田 20.2
RYU_L = [('飛行場', '大利根飛行場', 5.2, '茨城'), ('空港', '成田国際空港', 20.2, '千葉', True)]
# 加須駅：滑空場6つとホンダエアポート（20km 以内）。民間空港は調布 51.5
KAZO_L = [('滑空場', '大利根滑空場', 7.3, '埼玉'), ('滑空場', '羽生滑空場', 7.6, '埼玉'), ('滑空場', '板倉滑空場', 15.3, '群馬'),
          ('滑空場', '妻沼第2滑空場', 16.9, '埼玉'), ('飛行場', 'ホンダエアポート', 18.6, '埼玉'), ('滑空場', '妻沼滑空場', 18.9, '埼玉'),
          ('空港', '調布空港', 51.5, '東京', True)]
# 大阪駅：伊丹 10.1・八尾空港 15.3
OSAKA_L = [('飛行場', '八尾空港', 15.3, '大阪')]
# 八尾の近く（近鉄八尾駅）：八尾空港 3.4、民間空港は伊丹 22.6
YAO_L = [('空港', '大阪国際空港（伊丹）', 22.6, '大阪', True)]
# 川越駅：ホンダエアポート 8.5、民間空港は調布 26.5
KAWA_L = [('空港', '調布空港', 26.5, '東京', True)]

def build():
    home3('02-home-near-v3.html', 'ホーム：いちばん近いのが飛行場（3版）', 's02-v3',
          ticket3('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), more=len(USHIKU_L)) + strip(),
          '<b>02 3版：いちばん近いのが飛行場（牛久のあたり）</b>別の段「近くの番外編」はやめ、半券が近い順の先頭になる。先頭が飛行場なのでパタパタの代わりに種類の札「飛行場」。右の「ほか2つ ›」を押すとシートが上がって一覧（02b）。シートの高さは今の本番と同じ（地図は狭くならない・跳ねない）。地図は先頭に寄せ（跳ねない）、ほかの2つは見える所にあれば小さい点（この場面は外）')
    home3('02b-home-near-full-v3.html', '引き上げた位置：近くの空港（3版）', 's02-v3',
          ticket3('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), more=len(USHIKU_L)) + listcard(USHIKU_L, len(USHIKU_L)) + STRIP3,
          '<b>02b 引き上げた位置</b>先頭のあとに近い順。20km 以内に民間空港がないときは、民間空港でいちばん近い1つ（成田）を最後に足す（小さい見出し「民間空港でいちばん近い」）。行を押すと図鑑のその空港', full_top=270)
    home3('03-home-in-field-v3.html', 'ホーム：飛行場の判定範囲の中（3版）', 's03-v3',
          ticket3('飛行場', '', '竜ヶ崎飛行場', '<i class="dot ok"></i>判定範囲の中<br>番外編の印（16/86 は増えません）', more=len(RYU_L), within=True) + strip(),
          '<b>03 3版：飛行場の判定範囲の中</b>見出しは「いちばん近い空港」のまま（中でも外でも同じ言葉）。札「飛行場」と、押しても 16/86 が増えないことを1行で。成田は「ほか2つ」の中（20.2km）')
    home3('04-home-none-v3.html', 'ホーム：近くに何もない（3版）', 's04-v3',
          ticket3('空港', 'HND', '東京国際空港（羽田）', out_ds('14.7')) + strip(),
          '<b>04 3版：20km 以内にほかがない（東京駅）</b>「ほか」のピルを出さないだけで、今の本番と同じ見た目・同じ高さ（改善担当 review-2 の1）。民間空港でいちばん近いのが先頭なので足す行もない')
    home3('06-home-osaka-v3.html', 'ホーム：大阪駅（3版）', 's06-v3',
          ticket3('空港', 'ITM', '大阪国際空港（伊丹）', out_ds('10.1'), more=len(OSAKA_L)) + strip(),
          '<b>06 大阪駅</b>先頭は伊丹 10.1km（パタパタ ITM）。「ほか1つ」は八尾空港 15.3km。地図は先頭（伊丹）に寄せたまま広げない。ほかの空港は地図の見える所にあれば小さい点、外なら描かない（一覧を開いたときに見る）')
    home3('06b-home-yao-v3.html', 'ホーム：八尾空港の近く（3版）', 's06b-v3',
          ticket3('飛行場', '', '八尾空港', out_ds('3.4'), more=len(YAO_L)) + strip(),
          '<b>06b 八尾空港の近く（近鉄八尾駅）</b>名前は「空港」でも種類は飛行場なので、札は「飛行場」・パタパタなし。伊丹（22.6km）は「ほか1つ」の中に「民間空港でいちばん近い」として入る')
    home3('07-home-kazo-v3.html', 'ホーム：いちばん近いのが滑空場（3版）', 's07-v3',
          ticket3('滑空場', '', '加須滑空場', out_ds('6.3'), more=len(KAZO_L)) + strip(),
          '<b>07 3版：いちばん近いのが滑空場（加須駅）</b>先頭は加須滑空場（札「滑空場」）。地図も加須滑空場に寄せる。ほかの6つは点だけ、名前は先頭だけ（review-2 の8）')
    home3('07b-home-kazo-full-v3.html', '引き上げた位置：7つ（3版）', 's07-v3',
          ticket3('滑空場', '', '加須滑空場', out_ds('6.3'), more=len(KAZO_L)) + listcard(KAZO_L, len(KAZO_L)) + STRIP3,
          '<b>07b 引き上げた位置</b>3つまで＋「すべて 7つ ›」（review-2 の4：今日の数字などを遠くしない）。名前の横に県名', full_top=270)
    allrows = ''.join(lrow(*r) for r in KAZO_L)
    sheet = ('<div class="dimbg"></div><section class="allsheet"><div class="gb"></div><div class="hl"><h3>近くの空港<small>加須滑空場のほか ・ 近い順</small></h3>'
             '<span class="done">閉じる</span></div><div class="near list" style="box-shadow:none;margin:0">%s</div></section>') % allrows
    home3('07c-home-kazo-all-v3.html', 'すべて：近くの空港（3版）', 's07-v3',
          ticket3('滑空場', '', '加須滑空場', out_ds('6.3'), more=len(KAZO_L)) + strip(),
          '<b>07c 「すべて」を押したとき</b>シートの上に一覧のシート。民間空港の行はいつも最後', extra=sheet)
    home3('08-home-chofu-v3.html', 'ホーム：調布駅（3版）', 's08-v3',
          ticket3('空港', '', '調布空港', out_ds('2.6')) + strip(),
          '<b>08 調布駅</b>先頭は調布空港（民間空港でもコードがないのでパタパタの代わりに札「空港」。今は何もない所）。20km 以内にほかはないので「ほか」なし。地図の名前は「調布」1つ（review-2 の9）')
    home3('09-home-kawagoe-v3.html', 'ホーム：川越駅（3版）', 's09-v3',
          ticket3('飛行場', '', 'ホンダエアポート', out_ds('8.5'), more=len(KAWA_L)) + strip(),
          '<b>09 川越駅（調布の北）</b>先頭はホンダエアポート 8.5km。名前に種類の語がないので札「飛行場」が手がかり。調布（26.5km）は「ほか1つ」の中')
    # 夜
    home3('02-home-near-v3-night.html', '夜：ホーム 02（3版）', 's02n-v3',
          ticket3('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3', True), more=len(USHIKU_L), night=True) + strip(),
          '<b>夜：02 3版</b>札は色なし（夜は種類の色も使わない）、「ほか2つ」は白い縁。光るのは距離の数字（緑）と「いまここ」（琥珀）だけ', night=True)
    home3('07b-home-kazo-full-v3-night.html', '夜：引き上げた位置（3版）', 's07n-v3',
          ticket3('滑空場', '', '加須滑空場', out_ds('6.3', True), more=len(KAZO_L), night=True) + listcard(KAZO_L, len(KAZO_L)) + STRIP3,
          '<b>夜：07b 3版</b>行の札は色なし、距離の数字だけ緑', night=True, full_top=270)

def build_flap():
    """10 パタパタがずれるとき：A 先頭に合わせて札（おすすめ）／B パタパタは民間空港のまま残す"""
    css = M.CSS + V2.X2 + X3 + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}"""
    A = ticket3('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), more=2)
    B = ('<div class="bpass"><div class="bpm"><div class="lab">いちばん近い空港</div><div class="row1"><span class="ktag3 fd">飛行場</span><span class="more3">ほか2つ%s</span></div>'
         '<div class="nm">竜ヶ崎飛行場</div><div class="ds">%s</div></div><div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div></div>'
         '<div class="bpass" style="margin-top:8px;min-height:0"><div class="bpm" style="border-radius:24px"><div class="lab">民間空港でいちばん近い</div><div class="row1"><div class="flap"><i>N</i><i>R</i><i>T</i></div></div>'
         '<div class="nm">成田国際空港</div><div class="ds">ここから <b>30.5km</b></div></div></div>') % (CHEV, out_ds('11.3'))
    body = ('<div class="cmpw"><h1>10 パタパタがずれるとき</h1><p>先頭が飛行場・滑空場のとき（牛久のあたり）。パタパタは民間空港（コードのある86空港）だけに使う決まりのまま、どう見せるか</p>'
            '<h2><span class="rec">おすすめ</span>A 先頭に合わせて、パタパタの代わりに札</h2>%s'
            '<p class="why">半券は1枚・高さは今と同じ。成田は「ほか2つ」の中（民間空港でいちばん近い）。パタパタは先頭が民間空港のときだけ回る（今の調布と同じ考え）</p>'
            '<h2>B 民間空港のパタパタを別の札で残す</h2>%s'
            '<p class="why">成田のパタパタはいつも見えるが、シートが約120px 高くなり地図が狭くなる（review-2 の1とぶつかる）。「いちばん近い」が2枚あって、どちらで印をもらうか迷う</p></div>') % (A, B)
    open(os.path.join(OUT, '10-flap-v3.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>パタパタがずれるとき</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, body))

G3 = [('02-home-near-v3', '02 先頭が飛行場（牛久）'), ('02b-home-near-full-v3', '02b 引き上げた位置'), ('03-home-in-field-v3', '03 飛行場の中'),
      ('04-home-none-v3', '04 ほかがない（今と同じ）'), ('06-home-osaka-v3', '06 大阪駅'), ('06b-home-yao-v3', '06b 八尾空港の近く'),
      ('07-home-kazo-v3', '07 先頭が滑空場（加須）'), ('07b-home-kazo-full-v3', '07b 引き上げた位置'), ('07c-home-kazo-all-v3', '07c すべて'),
      ('08-home-chofu-v3', '08 調布駅'), ('09-home-kawagoe-v3', '09 川越駅'), ('10-flap-v3', '10 パタパタがずれるとき'),
      ('02-home-near-v3-night', '夜：02'), ('07b-home-kazo-full-v3-night', '夜：07b')]

def build_index():
    css = M.CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:16px 16px 60px}
h1{font-size:24px;margin:8px 4px 0;color:var(--strong)}h2{font-size:18px;margin:26px 4px 0;color:var(--strong)}.w p{font-size:13px;color:var(--sub);margin:6px 4px}
.th{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.th a{text-decoration:none;color:var(--strong);font-size:13px;font-weight:700}
.th img{width:100%;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}"""
    th = lambda G: '<div class="th">%s</div>' % ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s</a>' % (f, f, c) for f, c in G)
    s = ('<div class="w"><h1>近くの空港（飛行場・滑空場も）</h1><p>ブランチ design/near-airfields。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667。地図は main の web/ をデモで開いて撮った写真（先頭と点は撮るときに足した）</p>'
         '<h2>3版（11/11 本人「飛行場なども含めて表示」） ← 本人に見せるのはこちら</h2>'
         '<p>民間空港・飛行場・滑空場を分けずに近い順。いちばん近い1つが半券（種類の札・パタパタは民間空港だけ）、右の「ほか○つ ›」で引き上げて一覧。シートの高さは今の本番と同じ。基地は出さない</p>%s'
         '<h2>2版（記録：別の段「近くの番外編」）</h2>%s<h2>1版（記録）</h2>%s</div>') % (th(G3), th(V2.G2), th(V2.G1))
    open(os.path.join(OUT, 'index.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>近くの空港に飛行場も</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, s))

if __name__ == '__main__':
    build(); build_flap(); build_index()
