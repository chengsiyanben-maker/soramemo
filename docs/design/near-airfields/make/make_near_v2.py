# -*- coding: utf-8 -*-
# 近くの空港に飛行場も 2版（改善担当 review-1 の直し）。使い方：python3 make_near_v2.py
# 1版（make_near.py）の部品を読み込んで使う。出力は *-v2.html。地図は capture_v2.py が maps/*-v2-*.jpg に撮る
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_near as M
from make_near import ticket, strip, CHEV, OUT

X2 = """
.near{padding:0}
.nr2{display:flex;align-items:center;gap:10px;min-height:62px;padding:6px 6px 6px 14px}
.nr2 .t{flex:none;display:inline-flex;align-items:center;justify-content:center;min-width:56px;height:26px;padding:0 8px;border-radius:999px;font-size:13px;font-weight:700}
.t.fd{background:#E6F0E8;color:#2F5E3C}.t.gl{background:#E3F0F8;color:#175F88}
.nr2 .tx{flex:1;min-width:0;line-height:1.35}
.nr2 .tx small{display:block;font-size:13px;font-weight:700;color:var(--sub)}
.nr2 .tx b{display:block;font-size:15px;font-weight:800;color:var(--strong);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nr2 .tx b em{font-style:normal;font-size:13px;font-weight:600;color:var(--mute);margin-left:6px}
.nr2 .o{flex:none;display:inline-flex;align-items:center;min-height:24px;padding:0 9px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:700;color:var(--sub)}
.nr2 .k{flex:none;font-size:18px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.nr2 .k small{font-size:12px;font-weight:600;color:var(--mute);margin-left:2px;font-family:var(--gothic)}
.nr2 .c{flex:none;width:28px;height:44px;display:grid;place-items:center;color:var(--mute)}
.nr2 .c svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.nr2.none .tx b{color:var(--mute);font-weight:700}
.bpm .civ{margin-top:10px;font-size:13px;color:var(--hero-sub)}.bpm .civ b{color:#F3F4F6;font-weight:800}
/* 引き上げた位置の一覧 */
.list .lh{display:flex;align-items:baseline;gap:8px;padding:12px 16px 2px;font-size:15px;font-weight:800;color:var(--strong)}
.list .lh small{font-size:13px;font-weight:600;color:var(--sub)}
.list .nr2{min-height:56px}
.hs.full{top:var(--full-top);bottom:auto;height:calc(100vh - var(--full-top));overflow:hidden}
.strip3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}
.strip3 div{padding:10px 14px;border-radius:22px;background:var(--card);box-shadow:var(--shadow)}
.strip3 span{display:block;font-size:13px;font-weight:700;color:var(--sub)}.strip3 b{font-size:26px;font-weight:800;color:var(--strong)}
/* 表示の編集（マイページ） */
.lay{position:absolute;inset:0;background:var(--bg);z-index:60;overflow:hidden;padding:0 16px}
.lhd2{display:flex;align-items:center;gap:12px;height:72px}
.back{min-height:50px;display:inline-flex;align-items:center;gap:6px;padding:0 18px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:15px;font-weight:800;color:var(--strong)}
.lhd2 h2{margin:0;font-size:20px;color:var(--strong)}
.lc{border-radius:22px;background:var(--card);box-shadow:var(--shadow);margin-top:12px;padding:4px 8px 6px}
.lc .sh{display:flex;align-items:center;gap:12px;min-height:72px;padding:0 6px}
.lc .ic{width:40px;height:40px;border-radius:50%;background:#F1F3F6;display:grid;place-items:center;color:var(--strong)}
.lc .ic svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.lc .tt{flex:1}.lc .tt b{display:block;font-size:18px;color:var(--strong)}.lc .tt small{display:block;font-size:13px;color:var(--sub)}
.lc .n{font-size:22px;font-weight:800;color:var(--strong)}.lc .n small{font-size:12px;color:var(--mute);font-weight:600}
.lc .vr{margin-top:6px}
.lc .go2{display:flex;justify-content:flex-end;align-items:center;min-height:44px;padding:0 8px;font-size:14px;font-weight:800;color:var(--strong)}
.lc.closed .sh{min-height:62px}
"""
XN2 = """
.t.fd,.t.gl{background:#141B24;color:#BCC6D1;box-shadow:inset 0 0 0 1px rgba(150,170,195,.14)}
.nr2 .k{font-family:"Dot",monospace;font-weight:400;color:#5FD993;text-shadow:0 0 6px rgba(95,217,147,.45);font-size:19px}
.nr2 .k small{color:var(--mute);text-shadow:none;font-weight:600}
.nr2 .o{background:#141B24;color:#BCC6D1}
.bpm .civ b{color:#DCE3EA}
"""
KIND = {'飛行場': 'fd', '滑空場': 'gl'}

def row(kind, name, km, more=0, label='近くの番外編', pref=''):
    o = ''
    lab = '<small>%s%s</small>' % (label, ' ・ ほか%dつ' % more if more else '') if label else ''
    return ('<div class="nr2"><span class="t %s">%s</span><span class="tx">%s<b>%s%s</b></span>%s'
            '<span class="k">%.1f<small class="u">km</small></span><span class="c">%s</span></div>') % (
        KIND[kind], kind, lab, name, '<em>%s</em>' % pref if pref else '', o, km, CHEV)

def none_row():
    return '<div class="near"><div class="nr2 none"><span class="tx"><small>近くの番外編</small><b>20km 以内にはありません</b></span></div></div>'

def card(r): return '<div class="near">%s</div>' % r

def T_out(code, name, km):
    return ticket('いちばん近い空港（86空港）', code, name, '<i class="dot"></i>判定範囲の外 ・ ここから <b>%skm</b>' % km)

S02 = T_out('NRT', '成田国際空港', '30.5') + card(row('飛行場', '竜ヶ崎飛行場', 11.3, 1)) + strip()
S03 = ('<div class="bpass"><div class="bpm"><div class="lab">いま判定範囲の中</div><div class="nm">竜ヶ崎飛行場</div>'
       '<div class="ds"><i class="dot ok"></i>図鑑の番外編（飛行場）の印</div><div class="civ">いちばん近い空港 ・ 成田 <b>20.2km</b></div></div>'
       '<div class="stub"><span class="v">チェックイン</span><span class="s">→ 右へ引いて<br>印をもらう</span></div></div>'
       + card(row('飛行場', '大利根飛行場', 5.2)) + strip())
S04 = T_out('HND', '東京国際空港（羽田）', '14.7') + none_row() + strip()
S06 = T_out('ITM', '大阪国際空港（伊丹）', '10.1') + card(row('飛行場', '八尾空港', 15.3)) + strip()
S07H = T_out('', '調布空港', '51.5') + card(row('滑空場', '加須滑空場', 6.3, 6)) + strip()
KAZO = [('滑空場', '加須滑空場', 6.3, '埼玉'), ('滑空場', '大利根滑空場', 7.3, '埼玉'), ('滑空場', '羽生滑空場', 7.6, '埼玉'), ('滑空場', '板倉滑空場', 15.3, '群馬'),
        ('滑空場', '妻沼第2滑空場', 16.9, '埼玉'), ('飛行場', 'ホンダエアポート', 18.6, '埼玉'), ('滑空場', '妻沼滑空場', 18.9, '埼玉')]

def full_sheet():
    rows = ''.join(row(k, n, d, label='', pref=p) for k, n, d, p in KAZO)
    t = T_out('', '調布空港', '51.5')
    return (t + '<div class="near list"><div class="lh">近くの番外編<small>20km 以内 ・ 7つ</small></div>%s</div>'
            '<div class="strip3"><div><span>今日の印</span><b>0</b></div><div><span>空港</span><b>16</b><small class="u">/86</small></div><div><span>フライト</span><b>30</b></div></div>') % rows

def home2(path, title, mapname, inner, ann, night=False, extra='', full=False):
    base = M.CSS
    M.CSS = base + X2 + (XN2 if night else '') + ('.hs{--full-top:270px}' if full else '')
    try:
        M.home(path, title, mapname, inner, ann, 0, night, extra)
    finally:
        M.CSS = base
    if full:
        p = os.path.join(OUT, path); s = open(p).read()
        s = s.replace('<div class="hs" id="hs">', '<div class="hs full" id="hs">', 1)
        open(p, 'w').write(s)

def layout_page():
    def vr(name, sub, st):
        right = '<span class="alw">いつも</span>' if st == 'always' else '<span class="sw %s">%s</span>' % (st, 'ON' if st == 'on' else 'OFF')
        return '<div class="vr"><div class="tx"><b>%s</b><small>%s</small></div>%s</div>' % (name, sub, right)
    home_ic = '<svg viewBox="0 0 24 24"><path d="M3.5 10.5 12 4l8.5 6.5"/><path d="M5.5 9v10h4.5v-5.5h4V19h4.5V9"/></svg>'
    book_ic = '<svg viewBox="0 0 24 24"><path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5c-.8 0-1.5.5-1.5 1.2V5.5Z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5.5 1.5 1.2V5.5Z"/></svg>'
    rows = (vr('ホームの地図', 'ホームそのもの', 'always') + vr('チェックインの半券', 'いちばん近い空港', 'always')
            + vr('近くの番外編', '半券の下・20km 以内の飛行場など', 'on') + vr('今日の数字', '今日の印・空港・フライト', 'always')
            + vr('これから乗る便', '便名を入れると機体を調べる', 'on') + vr('イベントのお知らせ', '開いているイベント', 'on')
            + vr('これまでの記録', '空港・路線・距離の数', 'on') + vr('最近の印', '最近押した印', 'on'))
    return ('<div class="lay"><div class="lhd2"><span class="back">‹ マイページ</span><h2>表示の編集</h2></div>'
            '<div class="lc"><div class="sh"><span class="ic">%s</span><span class="tt"><b>ホーム</b><small>全部出しています</small></span><span class="n">8<small class="u">/8</small></span></div>'
            '%s<div class="go2">見本で編集 ›</div></div>'
            '<div class="lc closed"><div class="sh"><span class="ic">%s</span><span class="tt"><b>図鑑</b><small>全部出しています</small></span><span class="n">3<small class="u">/3</small></span></div></div></div>') % (home_ic, rows, book_ic)

def build():
    home2('02-home-near-v2.html', 'ホーム：近くの番外編あり（2版）', 's02-v2', S02,
          '<b>02 2版：判定範囲の外・近くに番外編</b>開いたときはどの高さでも1行（いちばん近い1つ。見出しの横に「ほか1つ」）。2つ目からは引き上げた位置（07）。半券の見出しは「いちばん近い空港（86空港）」、カードは「近くの番外編」にして、図鑑の数に入るかで言葉を分けた。地図の印は図鑑と同じ番外編の色（飛行場は緑・滑空場は空色）で小さく、名前は細め')
    home2('03-home-in-field-v2.html', 'ホーム：飛行場の判定範囲の中（2版）', 's03-v2', S03,
          '<b>03 2版：飛行場の判定範囲の中</b>見出しは「いま判定範囲の中」の1つ。名前に「飛行場」が入るので札は出さない。空いた所に「図鑑の番外編（飛行場）の印」と「いちばん近い空港 ・ 成田 20.2km」。カードの名前は「近くの番外編」のまま（場面で変えない）。地図の名前の「飛行場」の重なりも外した')
    home2('04-home-none-v2.html', 'ホーム：近くに番外編なし（2版）', 's04-v2', S04,
          '<b>04 2版：近くに番外編がない</b>行を消さず「20km 以内にはありません」に替える。20km の境をまたいでもシートの高さが変わらず、地図が跳ねない')
    home2('06-home-yao-v2.html', 'ホーム：名前が「空港」の飛行場（2版）', 's06-v2', S06,
          '<b>06 名前が「〜空港」の飛行場（大阪駅）</b>半券は伊丹 10.1km、カードは「近くの番外編」の［飛行場］八尾空港 15.3km。「いちばん近い空港」より遠いので、言葉の食い違いは出ない。名前に種類の語がない場所は札が見分けの手がかり')
    home2('07-home-kazo-v2.html', 'ホーム：番外編が7つ（加須・2版）', 's07-v2', S07H,
          '<b>07 番外編が7つ（加須駅）</b>開いたときは加須滑空場 6.3km＋「ほか6つ」。いちばん近い民間空港は調布 51.5km（コードがないのでパタパタなし。今と同じ）')
    home2('07b-home-kazo-full-v2.html', '引き上げた位置：番外編の一覧（2版）', 's07-v2', full_sheet(),
          '<b>07b 引き上げた位置</b>20km 以内を全部、近い順に。行の名前の横に県名（埼玉の大利根滑空場と茨城の大利根飛行場のような似た名前を分ける）。行は押すと図鑑のその場所', full=True)
    home2('05-layout-v2.html', '表示の編集：ホーム（2版）', 's02-v2', S02,
          '<b>05 2版：マイページ「表示の編集」のホームのカード</b>見方の設定2版の形（ホームは鉛筆でなく、この1枚と見本のページ）。行は半券の次、はじめ ON、名前は「近くの番外編」。「見本で編集 ›」の見本にも同じ行', extra=layout_page())
    home2('02-home-near-v2-night.html', '夜：ホーム（2版）', 's02n-v2',
          ticket('いちばん近い空港（86空港）', 'NRT', '成田国際空港', '<i class="dot"></i>判定範囲の外 ・ ここから <b class="lit">30.5</b> km') + card(row('飛行場', '竜ヶ崎飛行場', 11.3, 1)) + strip(),
          '<b>夜：02 2版</b>距離の数字だけ緑に光らせ、単位の km はふだんの字・薄いグレー。札は色なし', night=True)

def build_now2():
    # 01 の3枚を下まで入れる（3列）
    from make_near import img
    S = os.path.join(OUT, 'shots')
    items = [('now-ushiku', '判定範囲の外', '20km 以内に飛行場が2つあっても出ない'), ('now-near5', '5km 以内', '半券の中に押せない1行'), ('now-ryu', '飛行場の中', '見出しが「いちばん近い空港」のまま')]
    cells = ''.join('<figure><img src="%s" alt=""><figcaption><b>%s</b>%s</figcaption></figure>' % (img(os.path.join(S, f + '.png'), 240), t, d) for f, t, d in items)
    css = M.CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:14px 12px 40px}
h1{font-size:22px;margin:4px 4px 2px;color:var(--strong)}.w>p{font-size:13px;color:var(--sub);margin:0 4px 12px}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}figure{margin:0}figure img{width:100%;border-radius:12px;box-shadow:var(--shadow);display:block}
figcaption{font-size:13px;line-height:1.45;color:var(--sub);margin:6px 2px 0}figcaption b{display:block;color:var(--strong)}"""
    body = '<div class="w"><h1>01 今のホーム</h1><p>main の web/ をデモで開き、位置を入れて撮った。民間空港1つだけを主に出し、飛行場は5km 以内か判定範囲の中のときだけ</p><div class="g">%s</div></div>' % cells
    open(os.path.join(OUT, '01-now-v2.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>今のホーム</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, body))

G2 = [('02-home-near-v2', '02 判定範囲の外（1行）'), ('03-home-in-field-v2', '03 飛行場の中'), ('04-home-none-v2', '04 なし（高さはそのまま）'),
      ('06-home-yao-v2', '06 八尾空港（名前が空港）'), ('07-home-kazo-v2', '07 加須（7つ）'), ('07b-home-kazo-full-v2', '07b 引き上げた位置'),
      ('05-layout-v2', '05 表示の編集のホーム'), ('02-home-near-v2-night', '夜：02'), ('01-now-v2', '01 今（3枚とも下まで）')]
G1 = [('01-now', '01 今'), ('02-home-near', '02'), ('03-home-in-field', '03'), ('04-home-none', '04'), ('05-pen-sheet', '05 鉛筆'), ('05b-home-off', '05b'), ('02-home-near-night', '夜')]
def build_index():
    css = M.CSS + """.phone{height:auto;min-height:100vh;background:var(--bg);overflow:visible}.w{padding:16px 16px 60px}
h1{font-size:24px;margin:8px 4px 0;color:var(--strong)}h2{font-size:18px;margin:26px 4px 0;color:var(--strong)}.w p{font-size:13px;color:var(--sub);margin:6px 4px}
.th{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.th a{text-decoration:none;color:var(--strong);font-size:13px;font-weight:700}
.th img{width:100%;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}"""
    th = lambda G: '<div class="th">%s</div>' % ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s</a>' % (f, f, c) for f, c in G)
    s = ('<div class="w"><h1>近くの空港に飛行場も</h1><p>ブランチ design/near-airfields。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667。地図は main の web/ をデモで開いて撮った写真（番外編の印だけ撮るときに足した）</p>'
         '<h2>2版（11/11 改善担当 review-1 の直し） ← 本人に見せるのはこちら</h2>'
         '<p>開いたときはいつも1行（いちばん近い1つ＋ほか○つ）、なしのときも行を残して高さを変えない。言葉は「いちばん近い空港（86空港）」と「近くの番外編」。地図の印は番外編の色で小さく。引き上げると20km 以内を全部（県名つき）</p>%s'
         '<h2>1版（記録）</h2>%s</div>') % (th(G2), th(G1))
    open(os.path.join(OUT, 'index.html'), 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<title>近くの空港に飛行場も</title>\n<style>%s</style></head>\n<body><main class="phone">%s</main></body></html>\n' % (css, s))

if __name__ == '__main__':
    build(); build_now2(); build_index()
