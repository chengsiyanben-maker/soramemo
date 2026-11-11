# -*- coding: utf-8 -*-
# 近くの空港 5版：改善担当 review-4 の直しと、本人の答え（11/11 23時42分「近くの空港の細かい所」）。
# 使い方：python3 make_near_v5.py（地図は capture_v5.py が maps/*-v5-*.jpg に撮る）。4版の部品を読み込み、*-v5*.html に書き出す。アプリのコードは変えない
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_near as M
import make_near_v2 as V2
import make_near_v3 as V3
import make_near_v4 as V4
from make_near import strip, CHEV, OUT

DOWN = '<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>'
X5 = """
.map .m740{display:none}
@media (max-height:780px) and (min-height:701px){.map .m740{display:block}.map .m740~.m667{display:none}.map .m844:has(~.m740){display:none}}
/* ヘリポートの札（昼は土色。夜は色なし） */
.ktag3.hp{background:#F1E7D8;color:#5E4114}.t.hp{background:#F3EBDF;color:#6B4A16}
/* review-4 の2：下の「送れる合図」の棒をやめ、薄い影だけ */
.fade4 i{display:none}
/* review-4 の1：「すべて」は一覧の見出しの右へ（送らなくても押せる）。高さ 760 未満は一覧を1行 */
.list .lh{align-items:center;min-height:48px;padding:6px 8px 0 16px}
.list .lh .allp{margin-left:auto;display:inline-flex;align-items:center;gap:2px;min-height:44px;padding:0 10px 0 14px;border-radius:999px;background:var(--pill);font-size:14px;font-weight:800;color:var(--strong);white-space:nowrap}
.list .lh .allp svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
@media (max-height:759px){.list .nr2.r2,.list .nr2.r3{display:none}}
.list .civsec{margin:4px 0 2px;padding-top:0}
/* 番号の部品（5版では使わない。地図が狭いので先頭だけにした） */
.nr2 .no{flex:none;width:24px;height:24px;border-radius:50%;background:#16233A;color:#fff;display:grid;place-items:center;font-size:13px;font-weight:800;margin-right:-4px}
.nr2.wn{padding-left:10px}
@media (max-height:759px){.nr2 .no{display:none}.nr2.wn{padding-left:14px}}
/* 民間空港の行：小見出しをやめ、行の中の2段目に「民間空港でいちばん近い」（高さを詰めて 667 でも帯の上に入れる） */
.list .civsec{margin:0}.nr2 .tx small.cv2{display:block;font-size:13px;font-weight:700;color:var(--sub);line-height:1.3}
.list .lh{min-height:44px;padding-top:4px}
.fade4{height:14px}
/* 民間空港だけを出す（表示の編集・ホームに出すもの） */
.vr.sub{margin-top:2px;margin-left:18px;background:#F4F6F8;position:relative}
.vr.sub::before{content:"";position:absolute;left:-12px;top:-6px;width:9px;height:34px;border-left:2px solid #CBD2DB;border-bottom:2px solid #CBD2DB;border-bottom-left-radius:8px}
.vr.newv{box-shadow:inset 0 0 0 2px #16233A}
.hep{position:absolute;inset:0;background:var(--bg);z-index:60;overflow:hidden;padding:0 16px}
.hep .bk{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-top:14px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:14px;font-weight:800;color:var(--strong)}
.hep h2{font-size:22px;margin:16px 0 4px;color:var(--strong)}.hep p.l{font-size:14px;line-height:1.6;color:var(--sub);margin:0 0 12px}
.hep .mk{border-radius:24px;background:#E7EAF0;padding:8px 10px 10px}
.hep .mk .tg{display:inline-flex;min-height:26px;align-items:center;padding:0 10px;border-radius:999px;background:var(--card);font-size:13px;font-weight:800;color:var(--strong);margin:2px 0 2px 4px}
.hep .mk .vr{background:var(--card)}.hep .mk .vr.fix{background:#F1F3F6}.hep .mk .vr.sub{background:var(--card)}
"""
XN5 = """
.ktag3.hp{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.18)}.t.hp{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}
.list .lh .allp{background:#141B24;color:#DCE3EA}
.nr2 .no{background:#DCE3EA;color:#05070B}
"""
KC = {'空港': 'civ', '飛行場': 'fd', '滑空場': 'gl', 'ヘリポート': 'hp'}
KR = {'空港': 'cv', '飛行場': 'fd', '滑空場': 'gl', 'ヘリポート': 'hp'}
KL = {'空港': '民間空港', '飛行場': '飛行場', '滑空場': '滑空場', 'ヘリポート': 'ヘリポート'}

def mapimg5(name):
    """4版までの 844・667 に、引き上げた位置だけ 740 の写真も足す（review-4 は 740 でも確かめる）"""
    import base64
    out = ''
    for h in (844, 740, 667):
        p = os.path.join(M.MAPS, '%s-%d.jpg' % (name, h))
        if os.path.exists(p):
            out += '<img class="m%d" alt="" src="data:image/jpeg;base64,%s">' % (h, base64.b64encode(open(p, 'rb').read()).decode())
    return out or '<div class="mph"></div>'
M.mapimg = mapimg5

def ticket5(kind, code, name, ds, rows=(), within=False, opened=False):
    """4版の半券。直したところ：20km 以内がなく民間空港だけのときのピルは「近くの民間空港 ›」（review-4 の4）。
    引き上げた位置ではピルを「閉じる ⌄」にする（review-4 の5）"""
    n = sum(1 for r in rows if len(r) < 5)
    civ = any(len(r) >= 5 for r in rows)
    left = ('<div class="flap">%s</div>' % ''.join('<i>%s</i>' % c for c in code)) if code else '<span class="ktag3 %s">%s</span>' % (KC[kind], KL[kind])
    if opened:
        mo = '<span class="more3">閉じる%s</span>' % DOWN
    else:
        mo = ('<span class="more3">ほか%dつ%s</span>' % (n, CHEV)) if n else (('<span class="more3">近くの民間空港%s</span>' % CHEV) if civ else '')
    st = ('<div class="stub"><span class="v">チェックイン</span><span class="s">→ 右へ引いて<br>印をもらう</span></div>' if within
          else '<div class="stub off"><span class="v">チェックイン</span><span class="s">範囲に入る<br>と切れる</span></div>')
    return ('<div class="bpass"><div class="bpm"><div class="lab">いちばん近い</div><div class="row1">%s%s</div>'
            '<div class="nm">%s</div><div class="ds">%s</div></div>%s</div>') % (left, mo, name, ds, st)

def lrow5(kind, name, km, pref='', no=0, cls='', cap=''):
    num = '<span class="no">%d</span>' % no if no else ''
    return ('<div class="nr2%s%s">%s<span class="t %s">%s</span><span class="tx">' + ('<small class="cv2">%s</small>' % cap if cap else '') + '<b>%s%s</b></span>'
            '<span class="k">%.1f<small class="u">km</small></span><span class="c">%s</span></div>') % (
        cls, ' wn' if no else '', num, KR[kind], KL[kind], name, '<i class="pf">%s</i>' % pref if pref else '', km, CHEV)

def listcard5(rows, show=3):
    """見出しの右に「すべて ›」（送らなくても押せる）。844 は3行・高さ 760 未満は1行"""
    near = [r for r in rows if len(r) < 5]; civ = [r for r in rows if len(r) >= 5]
    body = ''.join(lrow5(*r[:4], cls=' r%d' % (i + 1)) for i, r in enumerate(near[:show]))   # 番号は付けない（地図は先頭だけ）
    allp = '<span class="allp">すべて%s</span>' % CHEV if len(near) > 1 else ''
    cs = ('<div class="civsec">%s</div>' % lrow5(*civ[0][:4], cap='民間空港でいちばん近い')) if civ else ''
    if not near:
        return '<div class="near list civonly"><div class="lh">20km 以内<small>ほかはありません</small></div>%s</div>' % cs
    return '<div class="near list"><div class="lh">20km 以内<small>%dつ ・ 近い順</small>%s</div>%s%s</div>' % (len(near), allp, body, cs)

def home5(path, title, mapname, inner, ann, night=False, extra='', full=False, scroll=None):
    base = M.CSS
    M.CSS = base + V2.X2 + V3.X3 + V4.X4 + X5 + (V2.XN2 + V3.XN3 + V4.XN4 + XN5 if night else '')
    try:
        M.home(path, title, mapname, inner, ann, 0, night, (extra or '') + ('<div class="fade4"></div>' if full else ''))
    finally:
        M.CSS = base
    if full:
        p = os.path.join(OUT, path); s = open(p).read()
        s = s.replace('<div class="hs" id="hs">', '<div class="hs full" id="hs">', 1)
        if scroll:
            s = s.replace('</body>', '<script>document.getElementById("hs").scrollTop=%d</script></body>' % scroll)
        open(p, 'w').write(s)

out_ds = V4.out_ds
U, R, K, O, Y, W = V3.USHIKU_L, V3.RYU_L, V3.KAZO_L, V3.OSAKA_L, V3.YAO_L, V3.KAWA_L
TOKYO_L = [('空港', '東京国際空港（羽田）', 14.7, '東京')]   # 東京駅：先頭は東京ヘリポート 8.2km。羽田は 20km 以内の民間空港なので普通の行

def vr(name, sub, st, cls=''):
    right = '<span class="alw">いつも</span>' if st == 'always' else '<span class="sw %s">%s</span>' % (st, 'ON' if st == 'on' else 'OFF')
    return '<div class="vr%s"><div class="tx"><b>%s</b><small>%s</small></div>%s</div>' % (cls, name, sub, right)

CIV_ROW = lambda st='off': vr('民間空港だけを出す', '飛行場・滑空場・ヘリポートを並びに出さない', st, ' sub newv')

def layout5():
    home_ic = '<svg viewBox="0 0 24 24"><path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/></svg>'
    book_ic = '<svg viewBox="0 0 24 24"><path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/></svg>'
    rows = (vr('ホームの地図', 'ホームそのもの', 'always') + vr('チェックインの半券', 'いちばん近い空港', 'always') + CIV_ROW()
            + vr('今日の数字', '今日の印・空港・フライト', 'always') + vr('これから乗る便', '便名を入れると機体を調べる', 'on')
            + vr('イベントのお知らせ', '開いているイベント', 'on') + vr('これまでの記録', '空港・路線・距離の数', 'on') + vr('最近の印', '最近押した印', 'on'))
    return ('<div class="lay"><div class="lhd2"><span class="back">‹ 閉じる</span><h2>表示の編集</h2></div>'
            '<div class="lc"><div class="sh"><span class="ic">%s</span><span class="tt"><b>ホーム</b><small>全部出しています</small></span><span class="n">4<small class="u">/4</small></span></div>'
            '%s<div class="go2">見本で編集 ›</div></div>'
            '<div class="lc closed"><div class="sh"><span class="ic">%s</span><span class="tt"><b>図鑑</b><small>全部出しています</small></span><span class="n">3<small class="u">/3</small></span></div></div></div>') % (home_ic, rows, book_ic)

def hepage5():
    rows = (vr('チェックインの半券', 'いちばん近い空港', 'always', ' fix') + CIV_ROW() + vr('今日の数字', '今日の印・空港・フライト', 'always', ' fix')
            + vr('これから乗る便', '便名を入れると機体を調べる', 'on') + vr('イベントのお知らせ', '開いているイベント', 'on')
            + vr('これまでの記録', '空港・路線・距離', 'on') + vr('最近の印', '', 'on'))
    return ('<div class="hep"><span class="bk">‹ 戻る</span><h2>ホームに出すもの</h2><p class="l">ホームのシートの見本です（並びは本物と同じ）。OFF にすると隠れます。</p>'
            '<div class="mk"><span class="tg">見本</span>%s</div></div>') % rows

def build():
    home5('02-home-near-v5.html', 'ホーム：いちばん近いのが飛行場（5版）', 's02-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U) + strip(),
          '<b>02 5版：牛久のあたり</b>4版と同じ。地図は左下の出典の札の高さも空けて寄せる（review-4 の3）')
    home5('02b-home-near-full-v5.html', '引き上げた位置：近くの空港（5版）', 's02f-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U, opened=True) + listcard5(U) + V3.STRIP3,
          '<b>02b 5版：引き上げた位置</b>一覧は「20km 以内 1つ」の1行と、すぐ下の「民間空港でいちばん近い」成田。667 でも成田の行まで帯の上に入る（review-4 の1）。半券のピルは「閉じる ⌄」（review-4 の5）。地図は先頭だけで点を出さない（review-4 の6）。下の棒はやめて薄い影だけ（review-4 の2）', full=True)
    home5('03-home-in-field-v5.html', 'ホーム：飛行場の判定範囲の中（5版）', 's03-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', '<i class="dot ok"></i>判定範囲の中<br>飛行場・滑空場の図鑑の印（16/86 とは別）', R, within=True) + strip(),
          '<b>03 5版：飛行場の判定範囲の中</b>図鑑の呼び名にそろえて「飛行場・滑空場の図鑑の印（16/86 とは別）」（review-4 の7）')
    home5('04-home-heli-v5.html', 'ホーム：いちばん近いのがヘリポート（5版）', 's04-v5',
          ticket5('ヘリポート', '', '東京ヘリポート', out_ds('8.2'), TOKYO_L) + strip(),
          '<b>04 5版：東京駅（ヘリポートが入ると）</b>本人の答え「ヘリポートも入れる」。東京ヘリポート（新木場）8.2km が先頭になり、羽田 14.7km は「ほか1つ」。札は「ヘリポート」（昼は土色・夜は色なし）。パタパタは先頭に合わせるので、羽田の HND は出ない。4版の「近くに何もない」場面（羽田が先頭）は、民間空港だけを出す ON の 12 で見られる')
    home5('06-home-osaka-v5.html', 'ホーム：大阪駅（5版）', 's06-v5',
          ticket5('空港', 'ITM', '大阪国際空港（伊丹）', out_ds('10.1'), O) + strip(),
          '<b>06 5版：大阪駅</b>4版と同じ（先頭が民間空港でコードがあるのでパタパタ ITM）')
    home5('06b-home-yao-v5.html', 'ホーム：八尾空港の近く（5版）', 's06b-v5',
          ticket5('飛行場', '', '八尾空港', out_ds('3.4'), Y) + strip(),
          '<b>06b 5版：八尾空港の近く</b>ピルを「近くの民間空港 ›」に（review-4 の4。種類の札と読み違えない）。20km 以内に民間空港がないので、いちばん近い伊丹 22.6km を1つ足す（本人の答え）')
    home5('07-home-kazo-v5.html', 'ホーム：いちばん近いのが滑空場（5版）', 's07-v5',
          ticket5('滑空場', '', '加須滑空場', out_ds('6.3'), K) + strip(),
          '<b>07 5版：加須駅</b>地図は出典の札の高さも空けて寄せ、「いまここ」が札にもぐらない（review-4 の3）')
    home5('07b-home-kazo-full-v5.html', '引き上げた位置：加須（5版）', 's07f-v5',
          ticket5('滑空場', '', '加須滑空場', out_ds('6.3'), K, opened=True) + listcard5(K) + V3.STRIP3,
          '<b>07b 5版：引き上げた位置</b>「すべて ›」は一覧の見出しの右（送らなくても押せる。review-4 の1）。844 は3行、高さ 760 未満（667・740）は1行で、その下に民間空港の調布まで帯の上に入る。地図は先頭だけ（点を出さない。review-4 の6）。ピルは「閉じる ⌄」', full=True)
    home5('07d-home-kazo-full-scrolled-v5.html', '引き上げた位置を送ったところ：加須（5版）', 's07f-v5',
          ticket5('滑空場', '', '加須滑空場', out_ds('6.3'), K, opened=True) + listcard5(K) + V3.STRIP3,
          '<b>07d 5版：シートの中を送ったところ</b>今日の数字まで送って見られる（シートの上の端は動かない）', full=True, scroll=400)
    allrows = ''.join(lrow5(*r[:4]) for r in K if len(r) < 5)
    civ = [r for r in K if len(r) >= 5][0]
    sheet = ('<div class="dimbg"></div><section class="allsheet"><div class="gb"></div><div class="hl"><h3>20km 以内<small>加須滑空場のほか ・ 6つ ・ 近い順</small></h3>'
             '<span class="done">閉じる</span></div><div class="near list" style="box-shadow:none;margin:0">%s<div class="civsec"><div class="ch">民間空港でいちばん近い</div>%s</div></div></section>') % (allrows, lrow5(*civ[:4]))
    home5('07c-home-kazo-all-v5.html', 'すべて：加須（5版）', 's07-v5',
          ticket5('滑空場', '', '加須滑空場', out_ds('6.3'), K) + strip(),
          '<b>07c 5版：「すべて」</b>4版と同じ', extra=sheet)
    home5('08-home-chofu-v5.html', 'ホーム：調布駅（5版）', 's08-v5',
          ticket5('空港', '', '調布空港', out_ds('2.6')) + strip(),
          '<b>08 5版：調布駅</b>4版と同じ。地図の字「調布飛行場」と私たちの名前の重なりは、本番で名前の置き方を決めるときに直す（review-4 の8）')
    home5('09-home-kawagoe-v5.html', 'ホーム：川越駅（5版）', 's09-v5',
          ticket5('飛行場', '', 'ホンダエアポート', out_ds('8.5'), W) + strip(),
          '<b>09 5版：川越駅</b>ピル「近くの民間空港 ›」（調布 26.5km）。地図は出典の札の高さも空けて寄せる（review-4 の3）')
    home5('11-layout-civonly-v5.html', '表示の編集：民間空港だけを出す（5版）', 's02-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U) + strip(),
          '<b>11 5版：マイページ「表示の編集」のホーム</b>本人の答え「民間空港だけを出す」の ON／OFF。半券の行の下に枝の行で置く（半券の中身の設定なので）。はじめ OFF。かたまりではないので「4/4」の数には入れない', extra=layout5())
    home5('11b-home-edit-civonly-v5.html', 'ホームに出すもの：民間空港だけを出す（5版）', 's02-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3'), U) + strip(),
          '<b>11b 5版：ホームに出すもの（見本で編集）</b>ホームの「ホームに出すものを選ぶ ›」から来るページ。見本の半券の下に同じ枝の行（表示の編集と同じ部品・同じ言葉）', extra=hepage5())
    home5('12-home-civonly-on-v5.html', 'ホーム：民間空港だけを出す ON（5版）', 's12-v5',
          ticket5('空港', 'HND', '東京国際空港（羽田）', out_ds('14.7')) + strip(),
          '<b>12 5版：民間空港だけを出す ON（東京駅）</b>今の本番と同じ見え方に戻る：先頭は羽田、パタパタ HND、「ほか」のピルなし（20km 以内に民間空港がほかにないので）。地図にもヘリポート・飛行場の点を出さない')
    home5('02-home-near-v5-night.html', '夜：ホーム 02（5版）', 's02n-v5',
          ticket5('飛行場', '', '竜ヶ崎飛行場', out_ds('11.3', True), U) + strip(),
          '<b>夜：02 5版</b>札は色なし', night=True)
    home5('07b-home-kazo-full-v5-night.html', '夜：引き上げた位置（5版）', 's07fn-v5',
          ticket5('滑空場', '', '加須滑空場', out_ds('6.3', True), K, opened=True) + listcard5(K) + V3.STRIP3,
          '<b>夜：07b 5版</b>昼と同じ形', night=True, full=True)
    home5('04-home-heli-v5-night.html', '夜：ヘリポート（5版）', 's04n-v5',
          ticket5('ヘリポート', '', '東京ヘリポート', out_ds('8.2', True), TOKYO_L) + strip(),
          '<b>夜：04 5版</b>ヘリポートの札も色なし（ほかの札と同じ）', night=True)

G5 = [('02-home-near-v5', '02 牛久（ほか1つ）'), ('02b-home-near-full-v5', '02b 引き上げた位置'), ('03-home-in-field-v5', '03 飛行場の中'),
      ('04-home-heli-v5', '04 東京駅（先頭がヘリポート）'), ('06-home-osaka-v5', '06 大阪駅'), ('06b-home-yao-v5', '06b 八尾（近くの民間空港 ›）'),
      ('07-home-kazo-v5', '07 加須（ほか6つ）'), ('07b-home-kazo-full-v5', '07b 引き上げた位置'), ('07d-home-kazo-full-scrolled-v5', '07d 送ったところ'),
      ('07c-home-kazo-all-v5', '07c すべて'), ('08-home-chofu-v5', '08 調布駅'), ('09-home-kawagoe-v5', '09 川越駅'),
      ('11-layout-civonly-v5', '11 表示の編集（民間空港だけ）'), ('11b-home-edit-civonly-v5', '11b ホームに出すもの'), ('12-home-civonly-on-v5', '12 民間空港だけ ON'),
      ('02-home-near-v5-night', '夜：02'), ('07b-home-kazo-full-v5-night', '夜：07b'), ('04-home-heli-v5-night', '夜：04')]

def build_index():
    css = M.CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:16px 16px 60px}
h1{font-size:24px;margin:8px 4px 0;color:var(--strong)}h2{font-size:18px;margin:26px 4px 0;color:var(--strong)}.w p{font-size:13px;color:var(--sub);margin:6px 4px}
.th{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.th a{text-decoration:none;color:var(--strong);font-size:13px;font-weight:700}
.th img{width:100%;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}.th small{display:block;font-weight:600;color:var(--sub)}"""
    th = lambda G, sm=False: '<div class="th">%s</div>' % ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s%s</a>' % (f, f, c, '<small>667：png/%s-667.png</small>' % f if sm else '') for f, c in G)
    s = ('<div class="w"><h1>近くの空港（飛行場・滑空場・ヘリポートも）</h1><p>ブランチ design/near-airfields。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667（引き上げた位置は 740 も）。地図は main の web/ をデモで開いて撮った写真（先頭と点は撮るときに足した）</p>'
         '<h2>5版（review-4 の直しと本人の答え） ← 本人に見せるのはこちら</h2>'
         '<p>「すべて ›」は一覧の見出しの右・667 と 740 は一覧1行。下の棒はやめた。地図は出典の札の高さも空けて寄せる。ピルは「近くの民間空港 ›」・引き上げた位置は「閉じる ⌄」。引き上げた位置の地図は先頭だけ。本人の答え：パタパタは先頭に合わせる（4版の 10 の A）・民間空港を1つ足す・20km・民間空港だけを出す（11・11b・12）・ヘリポート（04）</p>%s'
         '<h2>4版（記録）</h2>%s<h2>3版（記録）</h2>%s<h2>2版（記録）</h2>%s<h2>1版（記録）</h2>%s</div>') % (th(G5, True), th(V4.G4), th(V3.G3), th(V2.G2), th(V2.G1))
    open(os.path.join(OUT, 'index.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>近くの空港に飛行場も</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, s))

if __name__ == '__main__':
    build(); build_index()
