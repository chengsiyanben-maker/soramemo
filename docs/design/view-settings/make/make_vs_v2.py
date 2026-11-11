# -*- coding: utf-8 -*-
# 見方の設定 2版（改善担当 review-1 の直し）。使い方：python3 make_vs_v2.py
# 1版（make_vs.py）の部品を読み込んで使う。出力は *-v2.html
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import page, I
from make_vs import X, XN, sw, icon, bg, OUT

X2 = X + """
.vr .tx small{color:var(--sub)}
.vr.off .tx b{color:var(--mute)}.vr.off .tx small{color:var(--mute)}
.vr.dim2 .tx b,.vr.dim2 .tx small{color:var(--pale)}
.last{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;background:var(--card);color:var(--sub);font-size:13px;font-weight:800;margin-left:6px;vertical-align:1px}
.msg2{font-size:13px;color:var(--sub);margin:6px 8px 0;font-weight:700}
.sbody{overflow-y:auto}
.sbody.pad{padding-bottom:88px}
.gl small{display:block;font-size:13px;font-weight:600;color:var(--sub);margin-top:2px}
/* 1枚：畳んだカード */
.lhd{box-shadow:0 8px 14px -12px rgba(17,24,39,.35)}
.sec{padding:2px 8px 4px}
.sh .tt small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sh .c2{margin-left:4px}
.chev{width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub);flex:none}
.chev svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.sec.open .chev svg{transform:rotate(180deg)}
.sec .go2{display:flex;align-items:center;justify-content:flex-end;gap:4px;min-height:44px;padding:0 8px;font-size:14px;font-weight:800;color:var(--strong);margin-top:4px}
.flt2{display:flex;align-items:center;gap:8px;margin:8px 0 0}
.flt2 .pill{box-shadow:none;background:var(--card)}.flt2 .pill.on{background:var(--navy);color:#fff}
.flt2 .sm{font-size:13px;color:var(--sub);margin-left:auto;font-weight:700}
.opt{font-size:13px;font-weight:800;color:var(--strong);background:var(--card);border-radius:999px;display:inline-flex;align-items:center;min-height:28px;padding:0 12px;margin:0 0 6px;box-shadow:var(--shadow)}
"""
XN2 = XN + """
.sw.on{background:#2A3A4C}
.hl-ring{box-shadow:var(--shadow),0 0 0 2px #DCE3EA}
.flt2 .pill.on{background:#141B24;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.lhd{box-shadow:0 8px 14px -12px rgba(0,0,0,.9)}
.last{background:#141B24}
"""
CHEV = '<span class="chev"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span>'

# 見方の説明（全部の行に1行。OFF でも残す）
D = {
 '地方別': '9地方のツメと扉で並べる', '地図': None, '行った順': '行った日ごとに新しい順',
 '日誌': '1便1行・月の見出し', '年のまとめ': '便・路線・距離・空の上',
 '道のり': '大きな数字・2つの道・届くか', '1便ごと': '1便の FOP と内訳', '月ごと': '月末の残り・路線ごと',
 '2つの道': 'FOP だけで／30回＋1万 FOP で', 'JGC（Life Status）': 'JAL を選んだときだけ出ます', '入れたら届くか': '予定と計画を足した推定', '次に乗る便': 'この路線の今日の便数つき',
 '案内板': '出発・到着の便を案内板の形で', '1日の山': '1時間ごとの便の数と遅れ', '滑走路': 'いまの運用と使う滑走路', '定時': '便の定時の割合',
 '空の道すじ': '全機の航跡を重ねる', '短冊': '次の離着陸を1便1枚で', '撮る人': '撮る人向けの次に来る便の帯',
 'これから乗る便': '便名を入れると機体を調べる', 'イベントのお知らせ': '開いているイベント', 'これまでの記録': '空港・路線・距離の数', '最近の印': '最近押した印',
 'ホームの地図': 'ホームそのもの', 'チェックインの半券': 'いちばん近い空港', '今日の数字': '今日の印・空港・フライト',
 '遅れ・ダイバートのお知らせ': '', '地図と近くを飛ぶ機体': '', '特別塗装機': '今日飛ぶ特別塗装機', '撮影地': '', '門限のある時間': '', 'ゴーアラウンド（推定）': '',
 'これまでのパスポート': '', '乗った機体': '', '航空会社別': '', 'ステータスの目安': '', '修行のまとめ': '月ごとのポイント・路線ごと',
}
def desc(name, ctx=''):
    if name == '地図': return {'book': '日本地図に印', 'log': '何度も乗った区間ほど太い線'}.get(ctx, '')
    return D.get(name, '')

def vrow2(name, state, ctx='', ic=None, dis=False, dim=False, sub=None):
    s = sub if sub is not None else desc(name, ctx)
    right = '<span class="alw">いつも</span>' if state == 'always' else sw(state == 'on', dis or dim)
    tag = '<span class="last">最後の1つ</span>' if dis else ''
    cls = ' off' if state == 'off' else ''
    if dim: cls += ' dim2'
    return '<div class="row vr%s">%s<div class="tx"><b>%s%s</b>%s</div>%s</div>' % (cls, icon(ic) if ic else '', name, tag, '<small>%s</small>' % s if s else '', right)

def sheet2(title, n, total, body, undo='', lead=True, scroll_end=False):
    cnt = '<span class="cnt">%d<small>/%d</small></span>' % (n, total)
    sc = '<script>(function(){var b=document.querySelector(".sbody");b.scrollTop=b.scrollHeight;})()</script>' if scroll_end else ''
    return ('<div class="dim"></div><section class="sheet" aria-label="%s"><div class="grab"></div>'
            '<div class="shd"><div class="hl"><h3>%s</h3>%s<span class="pill dark">完了</span></div>%s</div>'
            '<div class="sbody%s">%s<a class="more">表示の編集をすべて見る %s</a></div>%s</section>%s') % (
        title, title, cnt, '<p class="lead">OFF で見方の帯から隠れます。最後の1つは残ります。</p>' if lead else '',
        ' pad' if undo else '', body, I['arrow'], undo, sc)

VIEWS = {
 'book': ['地方別', '地図', '行った順'],
 'log': ['日誌', '地図', '年のまとめ'],
 'ops': ['案内板', '1日の山', '滑走路', '定時', '空の道すじ', '短冊', '撮る人'],
}

def s02(night=False):
    sfx = '-v2' + ('-night' if night else '')
    xc = X2 + (XN2 if night else '')
    body = ''.join(vrow2(v, 'on', 'book') for v in VIEWS['book'])
    page(OUT + '/02a-book-sheet%s.html' % sfx, '図鑑の見方', bg('図鑑', VIEWS['book'], '地方別', '図鑑') + sheet2('図鑑の見方', 3, 3, body), night, xc)
    if night: return
    body = ''.join(vrow2(v, 'on', 'log') for v in VIEWS['log'])
    page(OUT + '/02b-log-sheet-v2.html', 'フライトの見方', bg('フライト', VIEWS['log'], '日誌', 'フライト') + sheet2('フライトの見方', 3, 3, body), False, xc)
    # OFF と元に戻す：帯が出ている間は下に余白（送れば最後の行とリンクが見える）
    body = vrow2('日誌', 'on', 'log') + vrow2('地図', 'on', 'log') + vrow2('年のまとめ', 'off', 'log')
    page(OUT + '/02b2-log-sheet-off-v2.html', 'フライトの見方（OFF）', bg('フライト', ['日誌', '地図'], '日誌', 'フライト')
         + sheet2('フライトの見方', 2, 3, body, '<div class="undo"><span>「年のまとめ」を隠しました</span><span class="pill">元に戻す</span></div>', scroll_end=True), False, xc)
    # 修行：題の下の文は見方の見出しの下へ。道のりに出すものは「道のりの画面に出すかたまり」
    def sg(road_on):
        b = ('<p class="gl">見方<small>OFF で見方の帯から隠れます。最後の1つは残ります。</small></p>'
             + vrow2('道のり', 'on' if road_on else 'off') + vrow2('1便ごと', 'on') + vrow2('月ごと', 'on')
             + '<p class="gl">道のりに出すもの<small>%s</small></p>' % ('道のりの画面に出すかたまり' if road_on else '道のりを ON にすると出ます'))
        b += ''.join(vrow2(n, 'on', dim=not road_on) for n in ['2つの道', 'JGC（Life Status）', '入れたら届くか', '次に乗る便'])
        return b
    page(OUT + '/02c-sg-sheet-v2.html', '修行の見方', bg('修行', ['道のり', '1便ごと', '月ごと'], '道のり', '修行') + sheet2('修行の見方', 3, 3, sg(True), lead=False), False, xc)
    page(OUT + '/02c2-sg-sheet-roadoff-v2.html', '修行の見方（道のり OFF）', bg('修行', ['1便ごと', '月ごと'], '1便ごと', '修行') + sheet2('修行の見方', 2, 3, sg(False), lead=False), False, xc)
    body = ''.join(vrow2(v, 'on') for v in VIEWS['ops'])
    page(OUT + '/02d-ops-sheet-v2.html', '運用の見方', bg('運用', ['案内板', '1日の山', '滑走路', '定時'], '滑走路', '運用') + sheet2('運用の見方', 7, 7, body), False, xc)
    # 最後の1つ：帯は1つでも名前を残す。押せない行に札、文は行の下
    body = ''.join(vrow2(n, 'off') for n in ['案内板', '1日の山']) + vrow2('滑走路', 'on', dis=True) + '<p class="msg2">見方は1つより減らせません。ほかを ON にすると OFF にできます。</p>' + ''.join(vrow2(n, 'off') for n in ['定時', '空の道すじ', '短冊', '撮る人'])
    page(OUT + '/02e-ops-sheet-last-v2.html', '運用の見方（最後の1つ）', bg('運用', ['滑走路'], '滑走路', '運用') + sheet2('運用の見方', 1, 7, body), False, xc)

# ---------- 03 表示の編集の1枚（畳んだカード） ----------
TABS = [('ホーム', 'always'), ('図鑑', 'on'), ('フライト', 'on'), ('運用', 'on'), ('修行', 'on'), ('成績', 'off')]
SECS = [
 ('ホーム', 'home', '見本で編集', [(None, [('ホームの地図', 'always'), ('チェックインの半券', 'always'), ('今日の数字', 'always'), ('これから乗る便', 'on'), ('イベントのお知らせ', 'on'), ('これまでの記録', 'on'), ('最近の印', 'on')])]),
 ('図鑑', 'book', '図鑑へ', [(None, [(v, 'on') for v in VIEWS['book']])]),
 ('フライト', 'log', 'フライトへ', [(None, [('日誌', 'on'), ('地図', 'on'), ('年のまとめ', 'off')])]),
 ('修行', '', '修行へ', [('見方', [('道のり', 'on'), ('1便ごと', 'on'), ('月ごと', 'on')]), ('道のりに出すもの', [('2つの道', 'on'), ('JGC（Life Status）', 'on'), ('入れたら届くか', 'on'), ('次に乗る便', 'on')])]),
 ('運用', '', '運用へ', [('見方', [(v, 'off' if v == '短冊' else 'on') for v in VIEWS['ops']]),
   ('滑走路の下に出すもの', [(n, 'on') for n in ['遅れ・ダイバートのお知らせ', '地図と近くを飛ぶ機体', '特別塗装機', '撮影地', '門限のある時間', 'ゴーアラウンド（推定）']])]),
 ('成績', '', 'タイルへ', [(None, [('これまでのパスポート', 'on'), ('乗った機体', 'on'), ('航空会社別', 'on'), ('ステータスの目安', 'on'), ('修行のまとめ', 'off')])]),
]
def hidden_names(gs):
    return [n for _, rows in gs for n, s in rows if s == 'off']

def layout2(name, title, opened=(), ring=None, night=False, only_off=False, scroll_to=None):
    nh = sum(len(hidden_names(g)) for *_, g in SECS) + sum(1 for t in TABS if t[1] == 'off')
    nall = sum(len(rows) for *_, g in SECS for _, rows in g) + len(TABS)
    def card(nm, sub_on, n, tot, inner, op, go=''):
        return ('<section class="card sec%s%s" id="s-%s"><div class="sh">%s<span class="tt"><b>%s</b><small>%s</small></span><span class="c2">%d<small class="u">/%d</small></span>%s</div>%s%s</section>') % (
            ' open' if op else '', ' hl-ring' if ring == nm else '', nm, icon(nm) if nm in ('ホーム', '図鑑', 'フライト', '運用', '修行', '成績') else
            '<span class="ic"><svg class="i" viewBox="0 0 24 24"><rect x="3" y="15" width="18" height="5" rx="2.5"/><path d="M7 9h10M9 5h6"/></svg></span>',
            nm, sub_on, n, tot, CHEV, inner if op else '', ('<a class="go2">%s %s</a>' % (go, I['arrow'])) if op and go and not only_off else '')
    out = ''
    # タブ：分母は上限の5（ホームを入れて5つまで）
    th = [t for t, s in TABS if s == 'off']
    trs = [(t, s) for t, s in TABS if s == 'off' or not only_off]
    inner = ''.join(vrow2(t, s, ic=t, sub=('ON で外すタブを選びます' if s == 'off' else ('タブの1番目' if t == 'ホーム' else ''))) for t, s in trs)
    if not only_off: inner += '<p class="msg2">ホームを入れて5つまで。並べ替えは「タブを選ぶ」で。</p>'
    if not (only_off and not th):
        out += card('タブ', '隠している：' + '・'.join(th) if th else '全部出しています', sum(1 for t in TABS if t[1] != 'off'), 5, inner, 'タブ' in opened or only_off, 'タブを選ぶ')
    for nm, ctx, go, gs in SECS:
        hn = hidden_names(gs)
        if only_off and not hn: continue
        n = sum(1 for _, rows in gs for r in rows if r[1] != 'off'); tot = sum(len(rows) for _, rows in gs)
        inner = ''
        for gl, rows in gs:
            rs = [r for r in rows if r[1] == 'off' or not only_off]
            if not rs: continue
            inner += ('<p class="gl">%s</p>' % gl if gl else '') + ''.join(vrow2(a, b, ctx) for a, b in rs)
        sub = '隠している：' + '・'.join(hn) if hn else '全部出しています'
        if nm == '成績' and not only_off: inner = '<p class="awaynote">タブは隠しています。マイページのタイルから開けます。</p>' + inner
        out += card(nm, sub, n, tot, inner, nm in opened or only_off, go)
    if not only_off:
        out += ('<section class="card sec" id="s-ap"><div class="sh"><span class="ic"><svg class="i" viewBox="0 0 24 24"><path d="M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10Z"/><circle cx="12" cy="11" r="2"/></svg></span><span class="tt"><b>よく見る空港</b><small>羽田・伊丹・福岡</small></span><span class="c2">3<small class="u">/14</small></span>%s</div></section>' % CHEV)
    body = ('<header class="lhd"><span class="pill">%s マイページ</span><h2>表示の編集</h2></header>'
            '<div class="sc"><div class="flt2"><span class="pill%s">すべて</span><span class="pill%s">隠しているもの %d</span><span class="sm">%dこのうち</span></div>'
            '%s<p class="note2">カードを押すと開きます。アカウントに保存し、別の端末でも同じ表示になります。隠しても記録や機能は消えません。経営の画面はここに入りません。</p>'
            '%s<div style="height:40px"></div></div>') % (I['back'], '' if only_off else ' on', ' on' if only_off else '', nh, nall, out,
            '' if only_off else '<span class="btn w reset">全部乗せに戻す</span>')
    if scroll_to:
        body += '<script>(function(){var s=document.querySelector(".sc"),e=document.getElementById("%s");s.scrollTop=e.offsetTop-8;})()</script>' % scroll_to
    page(OUT + '/%s.html' % name, title, body, night, X2 + (XN2 if night else ''))

def s03():
    layout2('03a-layout-top-v2', '表示の編集（畳んだ形）')
    layout2('03b-layout-ops-v2', '表示の編集（運用を開いた）', opened=('運用',), scroll_to='s-運用')
    layout2('03d-layout-from-pen-v2', '表示の編集（フライトの鉛筆から）', opened=('フライト',), ring='フライト', scroll_to='s-フライト')
    layout2('03e-layout-hidden-v2', '表示の編集（隠しているもの）', only_off=True)
    layout2('03a-layout-top-v2-night', '表示の編集（夜）', night=True)
    layout2('03d-layout-from-pen-v2-night', '表示の編集（夜・フライトの鉛筆から）', opened=('フライト',), ring='フライト', night=True, scroll_to='s-フライト')

# ---------- 04 決まりを1つに（案A おすすめ）と案B ----------
def s04():
    a = ''.join(vrow2(v, 'on', 'book') for v in VIEWS['book'])
    last = vrow2('滑走路', 'on', dis=True) + '<p class="msg2">見方は1つより減らせません。ほかを ON にすると OFF にできます。</p>'
    always = (vrow2('ホーム', 'always', sub='タブの1番目') + vrow2('ホームの地図', 'always') + vrow2('チェックインの半券', 'always') + vrow2('今日の数字', 'always'))
    body = ('<div class="wrap"><div class="bgtop"><span class="lg">消せない物の決まり</span></div>'
            '<span class="opt">案A（おすすめ）</span><p class="note" style="margin-top:0">見方は全部の画面で同じ：どれも OFF にできて、最後の1つだけ残る。「いつも」は画面そのもの（ホーム）だけ。</p>'
            '<p class="gl">図鑑の見方（地方別も OFF にできる）</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<p class="gl">最後の1つ（運用で滑走路だけ残したところ）</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<p class="gl">いつも（画面そのものだけ・見方の数には入らない）</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<div class="ann"><b>案A の決まり</b><ul><li>シートの文は全部「OFF で見方の帯から隠れます。最後の1つは残ります。」</li><li>最後の1つはスイッチを薄く、名前の横に「最後の1つ」の札、行の下に理由</li><li>「いつも」は 13px の太字・スイッチと同じ幅。押しても何も起きない</li><li>アプリの今の決まり（図鑑の地方別はいつも・loToggleOff）を外すことになる</li></ul></div></div>') % (a, last, always)
    page(OUT + '/04-always-v2.html', '消せない物の決まり（案A）', body, False, X2)
    b = vrow2('地方別', 'always', sub='ほかの見方の土台なので消せません') + vrow2('地図', 'on', 'book') + vrow2('行った順', 'on', 'book')
    body = ('<div class="wrap"><div class="bgtop"><span class="lg">消せない物の決まり</span></div>'
            '<span class="opt">案B</span><p class="note" style="margin-top:0">図鑑の地方別・フライトの日誌は「いつも」のまま。行の中に消せない理由を1行。修行・運用は最後の1つが残る（2つの決まりのまま）。</p>'
            '<p class="gl">図鑑の見方</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<p class="gl">フライトの見方</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<div class="ann"><b>案B の困る点</b><ul><li>図鑑・フライトと修行・運用で決まりが違う。シートの文も2通りになる</li><li>理由の1行で読めはするが、ほかの見方を使いたい人も1番目は消せない</li></ul></div></div>') % (
        b, vrow2('日誌', 'always', sub='ほかの見方の土台なので消せません') + vrow2('地図', 'on', 'log') + vrow2('年のまとめ', 'on', 'log'))
    page(OUT + '/04b-always-optB-v2.html', '消せない物の決まり（案B）', body, False, X2)

if __name__ == '__main__':
    s02(); s02(night=True); s03(); s04()
    print('ok')
