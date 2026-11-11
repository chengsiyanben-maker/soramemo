# -*- coding: utf-8 -*-
# 見方の設定（design/view-settings）の画面案を作る。使い方：python3 make_vs.py
# 01 今のばらばらな所／02 各画面の鉛筆のシート／03 マイページ「表示の編集」の1枚／04 いつも出す物の行／夜の版（667 は shoot.py が撮る）
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import page, tabs, I, img64, TAB_ICONS
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = OUT + '/shots/'
TI = dict(TAB_ICONS)
TI['成績'] = '<path d="M5 19V11M10 19V6M15 19v-5M20 19V9"/>'

X = """
.bgtop{display:flex;align-items:center;height:60px}.bgtop .lg{font-size:17px;font-weight:800;letter-spacing:.2em;color:var(--strong);margin-right:auto}
.bgh1{font-size:28px;font-weight:800;color:var(--strong);margin:6px 2px 0;letter-spacing:.04em}
.band{display:flex;align-items:center;gap:2px;margin-top:8px}
.band b{min-height:44px;display:flex;align-items:center;padding:0 10px;font-size:14px;color:var(--sub);position:relative}
.band b.on{color:var(--strong)}.band b.on::after{content:"";position:absolute;left:10px;right:10px;bottom:4px;height:3px;border-radius:2px;background:var(--navy)}
.band .pen{margin-left:auto;width:44px;height:44px;display:flex;align-items:center;justify-content:center;color:var(--sub)}
.ph{height:150px;margin-top:14px}.ph2{height:96px;margin-top:12px}
.dim{background:rgba(15,23,42,.46)}
.sheet{padding:8px 16px 0;max-height:78vh;display:flex;flex-direction:column}
.shd{flex:none;padding-bottom:6px}
.shd .hl{display:flex;align-items:center;gap:10px;min-height:52px}
.shd h3{font-size:21px;margin:0 auto 0 4px;color:var(--strong)}
.cnt{font-family:var(--sign);font-size:28px;font-weight:700;color:var(--strong)}.cnt small{font-family:var(--gothic);font-size:13px;color:var(--mute);font-weight:600;margin-left:2px}
.lead{font-size:13px;color:var(--sub);margin:0 4px}
.sbody{overflow:hidden;flex:1;padding-bottom:20px}
.gl{font-size:13px;font-weight:800;color:var(--sub);margin:16px 6px 0}
.vr{background:var(--wash);border-radius:16px;margin-top:8px;min-height:60px;padding:6px 12px 6px 16px}
.vr .ic{width:36px;height:36px;border-radius:50%;background:var(--card);display:flex;align-items:center;justify-content:center;color:var(--sub);flex:none}
.alw{width:68px;text-align:center;font-size:13px;font-weight:800;color:var(--sub);flex:none}
.vr.off .tx b{color:var(--sub)}
.sw.dis{opacity:.45}
.more{display:flex;align-items:center;min-height:44px;margin:10px 4px 0;font-size:14px;font-weight:800;color:var(--strong);gap:4px}
.undo{position:absolute;left:16px;right:16px;bottom:18px;min-height:52px;border-radius:999px;background:#1F2937;color:#fff;display:flex;align-items:center;padding:0 8px 0 20px;font-size:14px;font-weight:700;z-index:70;box-shadow:0 10px 30px -10px rgba(0,0,0,.5)}
.undo span{margin-right:auto}.undo .pill{background:transparent;box-shadow:none;color:#fff;text-decoration:underline;text-underline-offset:3px}
.msg{font-size:13px;color:var(--sub);background:var(--wash);border-radius:12px;padding:8px 12px;margin:8px 4px 0;font-weight:700}
/* 表示の編集の1枚 */
.lhd{position:fixed;left:50%;transform:translateX(-50%);top:0;width:min(420px,100vw);height:64px;background:var(--bg);display:flex;align-items:center;padding:0 16px;z-index:30}
.lhd h2{position:absolute;left:0;right:0;text-align:center;font-size:18px;margin:0;color:var(--strong);pointer-events:none}
.sc{position:fixed;left:50%;transform:translateX(-50%);top:64px;bottom:0;width:min(420px,100vw);overflow:hidden;padding:0 16px}
.hero{display:flex;align-items:baseline;gap:6px;margin:6px 4px 0}.hero .num{font-size:44px}
.hero .lb{font-size:13px;color:var(--sub);font-weight:700;margin-left:8px}
.flt{display:flex;gap:8px;margin:12px 0 0}.flt .pill{box-shadow:none;background:var(--card)}.flt .pill.on{background:var(--navy);color:#fff}
.sec{margin-top:14px;padding:4px 8px 10px}
.sh{display:flex;align-items:center;gap:10px;min-height:56px;padding:4px 8px;text-decoration:none;color:inherit}
.sh .ic{width:36px;height:36px;border-radius:50%;background:var(--wash);display:flex;align-items:center;justify-content:center;color:var(--strong);flex:none}
.sh .tt{flex:1;min-width:0}.sh .tt b{display:block;font-size:17px;color:var(--strong);line-height:1.3}.sh .tt small{display:block;font-size:13px;color:var(--sub);line-height:1.4}
.sh .go{font-size:13px;font-weight:800;color:var(--sub);display:flex;align-items:center;gap:2px;white-space:nowrap}
.sh .c2{font-family:var(--sign);font-size:20px;font-weight:700;color:var(--strong)}.sh .c2 small{font-family:var(--gothic);font-size:12px;color:var(--mute)}
.sec .vr{margin:6px 0 0}
.sec .gl{margin:12px 8px 0}
.sec .lnk{display:flex;align-items:center;min-height:44px;padding:0 8px;font-size:13px;font-weight:800;color:var(--sub);margin-top:4px}
.hl-ring{box-shadow:var(--shadow),0 0 0 3px #F2C14E}
.note2{font-size:13px;color:var(--sub);margin:16px 6px 0;line-height:1.6}
.reset{margin:12px 0 0}
.awaynote{font-size:13px;color:var(--sub);background:var(--wash);border-radius:12px;padding:8px 12px;margin:2px 8px 4px}
"""
XN = """
.sw.on{background:#141B24;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.sw.on::after{background:#DCE3EA}
.sw.off{background:#0A0F14;color:#AEB9C6;box-shadow:inset 0 0 0 1.5px #66778C}
.sw.off::after{background:#0A0F14;box-shadow:inset 0 0 0 1.5px #66778C}
.sheet{background:#0D1218;box-shadow:0 -10px 40px -10px rgba(0,0,0,.9),inset 0 1px 0 rgba(150,170,195,.14)}
.grab{background:#2A3644}.dim{background:rgba(0,0,0,.6)}
.vr .ic{background:#141B24}.band b.on::after{background:var(--strong)}
.flt .pill.on{background:#141B24;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
.sh .ic{background:#141B24}.undo{background:#1A2330;box-shadow:inset 0 0 0 1px rgba(150,170,195,.2)}
.hl-ring{box-shadow:var(--shadow),0 0 0 2px #F0AC4E}
.pill.w{background:transparent;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--sel-ring)}
"""
def sw(on, dis=False):
    return '<span class="sw %s%s" role="switch" aria-checked="%s">%s</span>' % ('on' if on else 'off', ' dis' if dis else '', 'true' if on else 'false', 'ON' if on else 'OFF')
def icon(name):
    return '<span class="ic"><svg class="i" viewBox="0 0 24 24">%s</svg></span>' % TI[name]

def vrow(name, state, sub='', ic=None, dis=False):
    # state：'on' 'off' 'always'
    right = '<span class="alw">いつも</span>' if state == 'always' else sw(state == 'on', dis)
    if state == 'off' and not sub: sub = '見方の帯から隠しています'
    return '<div class="row vr%s">%s<div class="tx"><b>%s</b>%s</div>%s</div>' % (' off' if state == 'off' else '', icon(ic) if ic else '', name, '<small>%s</small>' % sub if sub else '', right)

def bg(title, views, sel, tab, extra=''):
    band = ''.join('<b class="%s">%s</b>' % ('on' if v == sel else '', v) for v in views)
    return ('<div class="wrap"><div class="bgtop"><span class="lg">そらメモ</span><span class="pill">マイページ</span></div>'
            '<div class="bgh1">%s</div><div class="band">%s<span class="pen">%s</span></div>%s'
            '<div class="card ph"></div><div class="card ph2"></div><div class="card ph2"></div></div>%s') % (title, band, I['pen'], extra, tabs(tab))

def sheet(title, n, total, body, undo='', msg=''):
    cnt = '<span class="cnt">%d<small>/%d</small></span>' % (n, total) if total else ''
    return ('<div class="dim"></div><section class="sheet" aria-label="%s"><div class="grab"></div>'
            '<div class="shd"><div class="hl"><h3>%s</h3>%s<span class="pill dark">完了</span></div>'
            '<p class="lead">OFF で見方の帯から隠れます。1つ以上残します。</p>%s</div>'
            '<div class="sbody">%s<a class="more">表示の編集をすべて見る %s</a></div>%s</section>') % (
        title, title, cnt, msg, body, I['arrow'], undo)

# ---------- 02 各画面の鉛筆のシート ----------
def s02(night=False):
    sfx = '-night' if night else ''
    xc = X + (XN if night else '')
    # 図鑑
    body = vrow('地方別', 'always') + vrow('地図', 'on') + vrow('行った順', 'on')
    page(OUT + '/02a-book-sheet%s.html' % sfx, '図鑑の見方', bg('図鑑', ['地方別', '地図', '行った順'], '地方別', '図鑑') + sheet('図鑑の見方', 3, 3, body), night, xc)
    # フライト（作り直しの見方）
    body = vrow('日誌', 'always', '1便1行・月の見出し') + vrow('地図', 'on', '何度も乗った区間ほど太い線') + vrow('年のまとめ', 'on', '便・路線・距離・空の上')
    page(OUT + '/02b-log-sheet%s.html' % sfx, 'フライトの見方', bg('フライト', ['日誌', '地図', '年のまとめ'], '日誌', 'フライト') + sheet('フライトの見方', 3, 3, body), night, xc)
    if night: return
    # フライト：OFF にしたところ（行はその場に残る・元に戻す）
    body = vrow('日誌', 'always', '1便1行・月の見出し') + vrow('地図', 'on', '何度も乗った区間ほど太い線') + vrow('年のまとめ', 'off')
    page(OUT + '/02b2-log-sheet-off.html', 'フライトの見方（OFF）', bg('フライト', ['日誌', '地図'], '日誌', 'フライト')
         + sheet('フライトの見方', 2, 3, body, '<div class="undo"><span>「年のまとめ」を隠しました</span><span class="pill">元に戻す</span></div>'), False, X)
    # 修行：見方3つ＋道のりに出すもの4つ（今は別のページ → 同じシートに）
    body = ('<p class="gl">見方</p>' + vrow('道のり', 'on', '大きな数字・2つの道・届くか') + vrow('1便ごと', 'on', '1便の FOP と内訳') + vrow('月ごと', 'on', '月末の残り・路線ごと')
            + '<p class="gl">道のりに出すもの</p>' + vrow('2つの道', 'on', 'FOP だけで／30回＋1万 FOP で') + vrow('JGC（Life Status）', 'on', 'JAL を選んだときだけ出ます')
            + vrow('入れたら届くか', 'on', '予定と計画を足した推定') + vrow('次に乗る便', 'on', 'この路線の今日の便数つき'))
    page(OUT + '/02c-sg-sheet.html', '修行の見方', bg('修行', ['道のり', '1便ごと', '月ごと'], '道のり', '修行') + sheet('修行の見方', 3, 3, body), False, X)
    # 運用：7つ（いつもはない）。いちばん下まで送ったところは 667 の写真
    body = ''.join(vrow(n, 'on') for n in ['案内板', '1日の山', '滑走路', '定時', '空の道すじ', '短冊', '撮る人'])
    page(OUT + '/02d-ops-sheet.html', '運用の見方', bg('運用', ['案内板', '1日の山', '滑走路', '定時'], '滑走路', '運用') + sheet('運用の見方', 7, 7, body), False, X)
    # 最後の1つ（運用で1つだけ残したところ）
    body = ''.join(vrow(n, 'off') for n in ['案内板', '1日の山']) + vrow('滑走路', 'on', dis=True) + ''.join(vrow(n, 'off') for n in ['定時', '空の道すじ', '短冊', '撮る人'])
    page(OUT + '/02e-ops-sheet-last.html', '運用の見方（最後の1つ）', bg('運用', [], '', '運用') + sheet('運用の見方', 1, 7, body, msg='<p class="msg">見方は1つより減らせません。</p>'), False, X)

# ---------- 03 マイページ「表示の編集」の1枚 ----------
TABS = [('ホーム', 'always', ''), ('図鑑', 'on', ''), ('フライト', 'on', ''), ('運用', 'on', ''), ('修行', 'on', ''), ('成績', 'off', 'ON で外すタブを選びます')]
SECS = [
 ('ホーム', 'ホームに出すもの', [(None, [('ホームの地図', 'always', ''), ('チェックインの半券', 'always', ''), ('今日の数字', 'always', ''), ('これから乗る便', 'on', ''), ('イベントのお知らせ', 'on', ''), ('これまでの記録', 'on', ''), ('最近の印', 'on', '')])]),
 ('図鑑', '見方・1つ以上', [(None, [('地方別', 'always', ''), ('地図', 'on', ''), ('行った順', 'on', '')])]),
 ('フライト', '見方・1つ以上', [(None, [('日誌', 'always', ''), ('地図', 'on', ''), ('年のまとめ', 'off', '見方の帯から隠しています')])]),
 ('修行', '見方と道のりに出すもの', [('見方', [('道のり', 'on', ''), ('1便ごと', 'on', ''), ('月ごと', 'on', '')]), ('道のりに出すもの', [('2つの道', 'on', ''), ('JGC（Life Status）', 'on', 'JAL を選んだときだけ出ます'), ('入れたら届くか', 'on', ''), ('次に乗る便', 'on', '')])]),
 ('運用', '見方と滑走路の下に出すもの', [('見方', [('案内板', 'on', ''), ('1日の山', 'on', ''), ('滑走路', 'on', ''), ('定時', 'on', ''), ('空の道すじ', 'on', ''), ('短冊', 'off', '見方の帯から隠しています'), ('撮る人', 'on', '')]),
   ('滑走路の下に出すもの', [('遅れ・ダイバートのお知らせ', 'on', ''), ('地図と近くを飛ぶ機体', 'on', ''), ('特別塗装機', 'on', ''), ('撮影地', 'on', ''), ('門限のある時間', 'on', ''), ('ゴーアラウンド（推定）', 'on', '')])]),
 ('成績', 'かたまり', [(None, [('これまでのパスポート', 'on', ''), ('乗った機体', 'on', ''), ('航空会社別', 'on', ''), ('ステータスの目安', 'on', ''), ('修行のまとめ', 'off', '成績から隠しています')])]),
]
def count():
    items = list(TABS)
    for _, _, gs in SECS:
        for _, rows in gs: items += list(rows)
    return sum(1 for r in items if r[1] != 'off'), len(items)

def layout(name, title, scroll_to=None, ring=None, night=False, only_off=False):
    on, total = count()
    def sec(nm, sub, gs, extra=''):
        n_on = sum(1 for _, rows in gs for r in rows if r[1] != 'off'); n_all = sum(len(rows) for _, rows in gs)
        body = ''
        for gl, rows in gs:
            rs = [r for r in rows if (r[1] == 'off' or not only_off)]
            if not rs: continue
            body += ('<p class="gl">%s</p>' % gl if gl else '') + ''.join(vrow(a, b, c) for a, b, c in rs)
        if not body: return ''
        away = '<p class="awaynote">タブは隠しています。マイページのタイルから開けます。</p>' if nm == '成績' and not only_off else ''
        return ('<section class="card sec%s" id="s-%s"><a class="sh">%s<span class="tt"><b>%s</b><small>%s</small></span><span class="c2">%d<small class="u">/%d</small></span><span class="go">%s %s</span></a>%s%s%s</section>') % (
            ' hl-ring' if ring == nm else '', nm, icon(nm), nm, sub, n_on, n_all, '開く' if nm != '成績' else 'タイル', I['arrow'], away, body, extra)
    trs = [t for t in TABS if (t[1] == 'off' or not only_off)]
    tabsec = ('<section class="card sec" id="s-tabs"><div class="sh"><span class="ic"><svg class="i" viewBox="0 0 24 24"><rect x="3" y="15" width="18" height="5" rx="2.5"/><path d="M7 9h10M9 5h6"/></svg></span><span class="tt"><b>タブ</b><small>下のタブ帯・ホームのほか5つまで</small></span><span class="c2">5<small class="u">/6</small></span></div>'
              + ''.join(vrow(a, b, c, ic=a) for a, b, c in trs) + ('' if only_off else '<a class="lnk">並べ替えは「タブを選ぶ」で ›</a>') + '</section>')
    secs = tabsec + ''.join(sec(*s) for s in SECS)
    tail = '' if only_off else ('<section class="card sec"><a class="sh"><span class="ic"><svg class="i" viewBox="0 0 24 24"><path d="M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10Z"/><circle cx="12" cy="11" r="2"/></svg></span><span class="tt"><b>よく見る空港</b><small>運用の空港選びの上に並ぶ</small></span><span class="c2">3<small class="u">/14</small></span><span class="go">選ぶ %s</span></a></section>' % I['arrow'])
    nhid = total - on
    body = ('<header class="lhd"><span class="pill">%s マイページ</span><h2>表示の編集</h2></header>'
            '<div class="sc"><div class="hero"><span class="num">%d</span><span class="u">/ %d</span><span class="lb">出しているもの</span></div>'
            '<div class="flt"><span class="pill%s">すべて</span><span class="pill%s">隠しているもの %d</span></div>'
            '%s%s<p class="note2">アカウントに保存します。別の端末でも同じ表示になります。隠しても記録や機能は消えません。経営の画面はここに入りません。</p>'
            '<span class="btn w reset">全部乗せに戻す</span><div style="height:40px"></div></div>') % (I['back'], on, total, '' if only_off else ' on', ' on' if only_off else '', nhid, secs, tail)
    if scroll_to:
        body += '<script>(function(){var s=document.querySelector(".sc"),e=document.getElementById("%s");s.scrollTop=%s;})()</script>' % (
            scroll_to, 'e.offsetTop-8' if scroll_to != 'end' else 's.scrollHeight')
        body = body.replace('id="end"', '')
    page(OUT + '/%s.html' % name, title, body, night, X + (XN if night else ''))

def s03():
    layout('03a-layout-top', '表示の編集（上）')
    layout('03b-layout-sg', '表示の編集（修行・運用）', 's-修行')
    layout('03c-layout-bottom', '表示の編集（いちばん下）', 'end')
    layout('03d-layout-from-pen', '表示の編集（フライトの鉛筆から）', 's-フライト', ring='フライト')
    layout('03e-layout-hidden', '表示の編集（隠しているもの）', only_off=True)
    layout('03a-layout-top-night', '表示の編集（夜）', night=True)

# ---------- 04 いつも出す物の行 ----------
def s04():
    rows = (vrow('地方別', 'always') + vrow('地図', 'on') + vrow('行った順', 'on'))
    last = vrow('滑走路', 'on', dis=True)
    body = ('<div class="wrap"><div class="bgtop"><span class="lg">いつも出す物の行</span></div>'
            '<p class="note" style="margin-top:0">スイッチの代わりに「いつも」と書く。押せる物に見せない（地は同じ・縁も ›もなし）。</p>'
            '<p class="gl">いつも出す物（スイッチなし）</p><div class="card" style="padding:4px 12px 12px">%s</div>'
            '<p class="gl">いつも出す物の一覧</p><div class="card" style="padding:8px 4px">'
            '<div class="row"><div class="tx"><b>ホームのタブ</b><small>タブの1番目</small></div><span class="alw">いつも</span></div>'
            '<div class="row"><div class="tx"><b>ホームの地図</b><small>ホームそのもの</small></div><span class="alw">いつも</span></div>'
            '<div class="row"><div class="tx"><b>チェックインの半券・今日の数字</b><small>ホームのシートの上</small></div><span class="alw">いつも</span></div>'
            '<div class="row"><div class="tx"><b>図鑑の地方別</b><small>図鑑のはじめの見方</small></div><span class="alw">いつも</span></div>'
            '<div class="row"><div class="tx"><b>フライトの日誌</b><small>フライトのはじめの見方</small></div><span class="alw">いつも</span></div></div>'
            '<p class="note">修行と運用には「いつも」はない。代わりに、最後の1つは OFF にできない（下）。</p>'
            '<p class="gl">最後の1つ（スイッチを薄く・押せない）</p><div class="card" style="padding:4px 12px 12px">%s<p class="msg">見方は1つより減らせません。</p></div>'
            '<div class="ann"><b>決めた形</b><ul><li>「いつも」は 13px の太字・濃いグレー。スイッチと同じ幅 68px の中に置き、行の右がそろう</li>'
            '<li>いつもの行は一覧のいちばん上。数には入れる（図鑑は 3/3。見方の帯に出ている数と同じ）</li>'
            '<li>押しても何も起きない。読み上げは「地方別、いつも出します」</li>'
            '<li>最後の1つは「いつも」と分ける：スイッチは見えたまま薄く、上に「見方は1つより減らせません」</li></ul></div></div>') % (rows, last)
    page(OUT + '/04-always.html', 'いつも出す物の行', body, False, X)

# ---------- 01 今のばらばらな所 ----------
def s01():
    shots = [('book-sheet', '1 図鑑：下線のタブ＋鉛筆→シート'), ('fb-sheet', '2 フライト（#65）：同じシート'), ('sg-views', '3 修行（#64）：ピルの帯＋鉛筆→別のページ'),
             ('ops', '4 運用：帯を送ると左が切れる'), ('layout', '5 表示の編集：✓ のピル・取り消し線'), ('layout-667', '6 表示の編集：フライトが古い9つ'),
             ('tabpick', '7 タブを選ぶ：ON／OFF・番号・≡'), ('homeed', '8 ホームに出すもの：別のページ')]
    th = ''.join('<figure class="shot" style="margin:0"><img src="%s" style="width:100%%;border-radius:12px;box-shadow:var(--shadow);display:block"><figcaption style="font-size:13px;font-weight:700;margin-top:4px;line-height:1.5">%s</figcaption></figure>' % (img64(SHOT + f + '.png', 70, 360), c) for f, c in shots)
    tbl = [('図鑑', '下線のタブ', '下のシート', 'ON／OFF', '地方別'), ('フライト', '下線のタブ', '下のシート', 'ON／OFF', '日誌（#65）'), ('修行', 'ピル', '別のページ・番号つき', 'ON／OFF', 'なし'),
           ('運用', '下線のタブ', '下のシート', 'ON／OFF', 'なし'), ('ホーム', '帯なし', 'マイページの別のページ', 'ON／OFF', '半券・今日の数字'), ('表示の編集', '—', 'マイページの1枚', '✓ のピル', '鍵の絵')]
    rows = ''.join('<div class="row" style="min-height:44px;padding:4px 12px"><div class="tx"><b>%s</b><small>帯：%s ／ 開く物：%s ／ 部品：%s ／ いつも：%s</small></div></div>' % t for t in tbl)
    body = ('<div class="wrap"><div class="bgtop"><span class="lg">01 今の見方の設定</span></div>'
            '<p class="note" style="margin-top:0">main（#48 入り）と、作り直し中のフライト（PR #65）・修行（PR #64）を、全部乗せのデモで撮った（390×844。6 だけ 667）。経営は見ていない。</p>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px">%s</div>'
            '<p class="gl">画面ごとの違い</p><div class="card" style="padding:6px 0">%s</div>'
            '<div class="ann"><b>ばらばらな所</b><ul><li>開く物が3通り：図鑑・フライト・運用は下のシート、修行は別のページ（タブ帯が見えたまま）、ホームはマイページの別のページ</li>'
            '<li>部品が2通り：シートとタブを選ぶは ON／OFF、表示の編集の1枚だけ ✓ のピルと取り消し線</li>'
            '<li>表示の編集の1枚にない物：修行の見方・道のりに出すもの。フライトの見方は古い9つのまま（#65 が入れば3つ）</li>'
            '<li>修行の帯だけピル、ほかは下線のタブ（帯の形は PM の判断待ち。この案では変えない）</li>'
            '<li>運用の帯は「滑走路」を選ぶと左へ送られ、「案内板」が切れて見える</li>'
            '<li>修行のページの行だけ番号（1〜3）がある。見方は並べ替えないので番号は要らない</li></ul></div></div>') % (th, rows)
    page(OUT + '/01-now.html', '01 今の見方の設定', body, False, X)

s01(); s02(); s02(night=True); s03(); s04()
print('ok')
