# -*- coding: utf-8 -*-
# 空港の3Dの画面案を書き出す。使い方：python3 make3d.py → python3 shoot.py <このフォルダの親の絶対の道> → python3 make_index.py
import os, json, base64
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
SCENE = open(os.path.join(HERE, 'scene.js'), encoding='utf-8').read()

CSS = r"""
:root{--bg:#F4F4F4;--paper:#FFFFFF;--ink:#24292F;--sub:#6B7280;--faint:#9CA3AF;--wash:#EEF1F5;--hero:#0F1B2D;--shadow:0 12px 28px -18px rgba(15,23,42,.45);--glass:rgba(255,255,255,.88);--sel:#0F1B2D;--on-sel:#FFFFFF;--sp:#856620;--sp-bg:#F4ECD8;--now:#0F1B2D;--go:#3D7A4E}
:root[data-night]{--bg:#0B0D10;--paper:#121418;--ink:#E8ECF1;--sub:#A7B0BC;--faint:#7C8592;--wash:#1C2027;--hero:#0B0D10;--shadow:0 12px 28px -18px rgba(0,0,0,.9);--glass:rgba(18,20,24,.86);--sel:transparent;--on-sel:#FFFFFF;--sp:#E8ECF1;--sp-bg:#262B33;--now:#FFB547;--go:#7EE2A8}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;border:0;background:none;padding:0}
.num{font-feature-settings:"tnum";font-weight:800;letter-spacing:-.01em}
.u{font-size:12px;color:var(--sub);font-weight:600;margin-left:2px}
/* 3D の全画面 */
.stage{position:fixed;inset:0;overflow:hidden}
.stage canvas{position:absolute;inset:0;width:100%;height:100%;display:block}
.top{position:absolute;left:0;right:0;top:0;padding:12px 16px 0;display:flex;align-items:center;gap:10px}
.rb{width:44px;height:44px;border-radius:999px;background:var(--glass);box-shadow:var(--shadow);display:flex;align-items:center;justify-content:center;flex:none;backdrop-filter:blur(8px)}
.rb svg{width:20px;height:20px;stroke:var(--ink);fill:none;stroke-width:2.2;stroke-linecap:round}
.ttl{flex:1;min-width:0;background:var(--glass);border-radius:999px;box-shadow:var(--shadow);height:44px;display:flex;flex-direction:column;justify-content:center;padding:0 16px;backdrop-filter:blur(8px)}
.ttl b{font-size:15px;line-height:1.2}.ttl small{font-size:13px;color:var(--sub);line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.seg{position:absolute;left:16px;right:16px;top:66px;display:flex;background:var(--glass);border-radius:999px;box-shadow:var(--shadow);padding:4px;backdrop-filter:blur(8px)}
.seg button{flex:1;height:44px;border-radius:999px;font-size:14px;font-weight:700;color:var(--sub);display:flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap}
.seg button.on{background:var(--sel);color:var(--on-sel)}
:root[data-night] .seg button.on{box-shadow:inset 0 0 0 1.5px #FFFFFF}
.seg button[disabled]{color:var(--faint)}
.chip{position:absolute;left:16px;display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 12px;border-radius:999px;background:var(--glass);box-shadow:var(--shadow);font-size:13px;color:var(--sub);backdrop-filter:blur(8px)}
.chip i{width:8px;height:8px;border-radius:9px;background:var(--go);display:inline-block}
.tag{position:absolute;transform:translate(-50%,-100%);background:var(--paper);color:var(--ink);font-size:13px;font-weight:700;padding:3px 9px;border-radius:999px;box-shadow:var(--shadow);white-space:nowrap}
.tag:after{content:"";position:absolute;left:50%;bottom:-5px;margin-left:-5px;border:5px solid transparent;border-top-color:var(--paper);border-bottom:0}
.tag.sel{background:var(--hero);color:#fff}.tag.sel:after{border-top-color:var(--hero)}
:root[data-night] .tag.sel{background:#121418;box-shadow:inset 0 0 0 1.5px #fff}
:root[data-night] .tag.sel:after{border-top-color:#fff}
.tag small{font-weight:600;color:var(--sub);margin-left:4px;font-size:13px}.tag.sel small{color:rgba(255,255,255,.75)}
/* 下のシート */
.sheet{position:absolute;left:0;right:0;bottom:0;background:var(--paper);border-radius:24px 24px 0 0;box-shadow:0 -10px 30px -18px rgba(15,23,42,.5);padding:8px 16px 16px}
.grab{width:40px;height:5px;border-radius:9px;background:var(--wash);margin:0 auto 10px}
.sh{display:flex;align-items:baseline;justify-content:space-between;margin:2px 4px 6px}
.sh h2{font-size:17px;margin:0}.sh .num{font-size:24px}
.sh small{font-size:13px;color:var(--sub)}
.row{display:flex;align-items:center;gap:12px;min-height:56px;padding:6px 4px;border-radius:16px}
.row + .row{margin-top:2px}
.row .fl{width:84px;flex:none}.row .fl b{display:block;font-size:17px;font-weight:800;line-height:1.2}.row .fl small{display:block;font-size:13px;color:var(--sub)}
.row .st{flex:1;font-size:14px;color:var(--ink)}.row .st small{display:block;font-size:13px;color:var(--sub)}
.row .st.now{color:var(--now);font-weight:700}
.row .go{color:var(--faint);font-size:20px}
.sp{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:999px;background:var(--sp-bg);color:var(--sp);font-size:13px;font-weight:700;margin-left:6px;vertical-align:2px}
.note{font-size:13px;color:var(--sub);line-height:1.6;margin:8px 4px 0}
/* 機体のカード */
.card .hd{display:flex;align-items:flex-start;gap:10px;margin:0 4px}
.card .hd .big{font-size:30px;line-height:1.1}
.card .hd .rt{font-size:14px;color:var(--sub);margin-top:4px}
.card .hd .x{margin-left:auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 0}
.cell{background:var(--wash);border-radius:16px;padding:10px 12px}
.cell small{display:block;font-size:13px;color:var(--sub)}.cell b{font-size:19px}
.btns{display:flex;gap:8px;margin-top:12px}
.pill{height:48px;border-radius:999px;padding:0 18px;font-size:15px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap}
.pill.main{background:var(--hero);color:#fff;flex:1}
:root[data-night] .pill.main{background:transparent;color:#fff;box-shadow:inset 0 0 0 1.5px #fff}
.pill.sub{background:var(--wash);color:var(--ink)}
.banner{position:absolute;left:16px;right:16px;top:126px;background:var(--paper);border-radius:20px;box-shadow:var(--shadow);padding:12px 14px;display:flex;gap:10px;align-items:center}
.banner p{margin:0;font-size:13px;line-height:1.55;color:var(--ink);flex:1}.banner p b{display:block;font-size:14px}
.banner .pill{height:44px;padding:0 14px;font-size:14px}
/* 空港ページ（入口） */
.dlg{position:fixed;left:12px;right:12px;top:62px;bottom:0;background:var(--paper);border-radius:28px 28px 0 0;overflow:hidden;box-shadow:var(--shadow)}
.dlg .in{padding:0 24px 24px}
.under{position:fixed;inset:0;background:#AEB4BB}
:root[data-night] .under{background:#05070A}
.under .pp{position:absolute;top:14px;left:16px;display:flex;gap:6px}
.under .pp span{height:40px;padding:0 14px;border-radius:999px;background:rgba(255,255,255,.55);display:inline-flex;align-items:center;font-size:14px;font-weight:700;color:#24292F}
:root[data-night] .under .pp span{background:rgba(255,255,255,.08);color:#A7B0BC}
.under .pp span.on{background:#0F1B2D;color:#fff}
.rec h4{font-size:17px;margin:20px 0 8px}.rec li{list-style:none;font-size:15px;line-height:2}.rec ul{margin:0;padding:0}
.rec .all{font-size:15px;font-weight:700;margin-top:6px;display:block}
.now3d{background:var(--wash);border-radius:22px;padding:14px;margin-top:22px}
.now3d .h{display:flex;align-items:baseline;justify-content:space-between;margin:0 2px 10px}.now3d .h b{font-size:18px}.now3d .h small{font-size:13px;color:var(--sub)}
.thumb{position:relative;height:200px;border-radius:18px;overflow:hidden;background:#C9DDF0}
.thumb canvas{position:absolute;inset:0;width:100%;height:100%}
.thumb .lb{position:absolute;left:10px;top:10px;font-size:13px;background:var(--glass);border-radius:999px;padding:4px 10px;color:var(--ink);font-weight:700}
.thumb .lb small{color:var(--sub);font-weight:600;font-size:13px}
.thumb .go3{position:absolute;right:10px;bottom:10px;height:44px;padding:0 16px;border-radius:999px;background:var(--hero);color:#fff;font-size:15px;font-weight:800;display:inline-flex;align-items:center;gap:6px;box-shadow:var(--shadow)}
:root[data-night] .thumb .go3{background:#121418;box-shadow:inset 0 0 0 1.5px #fff}
.now3d .ft{font-size:13px;color:var(--sub);margin:10px 2px 0;line-height:1.55}
.now3d .rest{display:flex;gap:8px;margin-top:12px}
.now3d .rest div{flex:1;background:var(--paper);border-radius:16px;padding:10px 12px}.now3d .rest small{display:block;font-size:13px;color:var(--sub)}.now3d .rest b{font-size:22px}
.later{font-size:13px;color:var(--faint);text-align:center;margin-top:14px}
/* 読み込み */
.load{position:absolute;left:24px;right:24px;top:40%;transform:translateY(-50%);background:var(--paper);border-radius:24px;box-shadow:var(--shadow);padding:22px 20px}
.load h2{font-size:18px;margin:0 0 4px}.load p{font-size:13px;color:var(--sub);margin:0 0 14px;line-height:1.6}
.bar{height:8px;border-radius:9px;background:var(--wash);overflow:hidden}.bar i{display:block;height:100%;width:62%;background:var(--hero);border-radius:9px}
.load .n{display:flex;justify-content:space-between;align-items:baseline;margin-top:10px}.load .n .num{font-size:26px}
.load .pill{margin-top:14px;width:100%}
.ghost{position:absolute;inset:0;background:linear-gradient(#DCE7F2,#EEF1F5)}
:root[data-night] .ghost{background:linear-gradient(#070B14,#18233A)}
"""

ICON_X = '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>'
ICON_DOT = '<svg viewBox="0 0 24 24" style="fill:var(--ink);stroke:none"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>'

CAMS = {
 'over':  "{pos:HND.P(200,-6000,3000),tgt:HND.P(-150,-1300,0),fov:56,cy:.36}",
 'tower': "{pos:HND.P(640,-420,232),tgt:HND.P(420,700,0),fov:60,cy:.40}",
 'follow':"{pos:HND.P(950,-3300-200,420+48),tgt:HND.P(950,-1300,0),fov:58,cy:.40}",
 'thumb': "{pos:HND.P(450,-5300,2900),tgt:HND.P(100,-500,0),fov:46,cy:.52}",
}
def page(fn, title, body, night=False, draw=None, tags=None):
    js = ''
    if draw:
        js = '<script>' + SCENE + '</script><script>(function(){const cv=document.getElementById("cv");const T=drawAirport(cv,%s);const L=%s;const st=cv.parentElement;const sh=st.querySelector(".sheet");const lim=sh?sh.getBoundingClientRect().top-8:innerHeight;const ref=st.querySelector(".top");L.forEach(function(t){const p=T[t.id];if(!p||p.z<5||p.y<150||p.y>lim)return;const e=document.createElement("div");e.className="tag"+(t.sel?" sel":"");e.innerHTML=t.html;e.style.left=Math.max(56,Math.min(cv.clientWidth-56,p.x))+"px";e.style.top=p.y+"px";st.insertBefore(e,ref);});})()</script>' % (draw, json.dumps(tags or [], ensure_ascii=False))
    html = '<!doctype html><html lang="ja"%s><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body>%s%s</body></html>' % (' data-night' if night else '', title, CSS, body, js)
    open(os.path.join(OUT, fn + '.html'), 'w', encoding='utf-8').write(html)

def topbar(sub='機体の位置は約2分遅れ'):
    return '<div class="top"><button class="rb" aria-label="閉じる">%s</button><div class="ttl"><b>羽田　3D</b><small>%s</small></div><button class="rb" aria-label="表示の設定">%s</button></div>' % (ICON_X, sub, ICON_DOT)
def seg(on, plane=None):
    b = lambda k, t, dis=False: '<button class="%s"%s>%s</button>' % ('on' if k == on else '', ' disabled' if dis else '', t)
    return '<div class="seg">' + b('over', '全体') + b('tower', '管制塔') + b('plane', plane or '機体', dis=(plane is None and on != 'plane')) + '</div>'

LIST = [('NH 241', '福岡から', '着陸まで約3分', 'C 滑走路へ', True, True), ('JL 109', '伊丹へ', '離陸中', 'A 滑走路', True, False),
        ('NH 59', '札幌へ', '上昇中', '高さ 900m', False, False), ('BC 509', '神戸へ', '地上を走行中', 'C 滑走路へ', False, False),
        ('JL 903', '那覇へ', '出発準備', '第1ターミナル', False, False)]
def rows(n, night=False):
    out = ''
    for fl, to, st, s2, now, sp in LIST[:n]:
        out += '<div class="row"><div class="fl"><b class="num">%s</b><small>%s</small></div><div class="st%s">%s%s<small>%s</small></div><span class="go">›</span></div>' % (
            fl, to, ' now' if now else '', st, '<span class="sp">特別塗装機</span>' if sp else '', s2)
    return out
def sheet(n=3, extra=''):
    return '<div class="sheet"><div class="grab"></div><div class="sh"><h2>見えている機体</h2><span><span class="num">12</span><span class="u">機</span></span></div>%s%s</div>' % (rows(n), extra)

TAG_AIR = [{'id': 'NH241', 'html': 'NH 241<small>着陸</small>'}, {'id': 'NH59', 'html': 'NH 59<small>上昇</small>'}, {'id': 'JL109', 'html': 'JL 109<small>離陸</small>'}]

def scene(sky, cam, extra='', ps=None, night=False, more=''):
    psv = ps or {'over': 3, 'tower': 1.3, 'follow': 1}[cam]
    hide = ',hideTower:true' if cam == 'tower' else ''
    return "{sky:'%s',cam:%s,planeScale:%s%s%s}" % (sky, CAMS[cam], psv, hide, more)

# 03 全体（昼）
page('03-overview-day', '03 全体の視点（昼）', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') +
     '<div class="chip" style="bottom:calc(36vh + 12px)"><i></i>位置を受信中</div>' + sheet(3) + '</div>', draw=scene('day', 'over'), tags=TAG_AIR)
for f in ['03-overview-day']:
    pass
# シートの高さ
CSS_SHEET = '.sheet{height:36vh}'
# 04 機体を押した
CARD = lambda night: ('<div class="sheet card"><div class="grab"></div><div class="hd"><div><b class="num big">NH 241</b><div class="rt">福岡 → 羽田　<span class="sp">特別塗装機</span></div></div><button class="rb x" aria-label="閉じる" style="box-shadow:none;background:var(--wash)">%s</button></div>'
     '<div class="grid"><div class="cell"><small>機種</small><b class="num">B787-9</b></div><div class="cell"><small>登録記号</small><b class="num">JA871A</b></div>'
     '<div class="cell"><small>高さ</small><b class="num">420</b><span class="u">m</span></div><div class="cell"><small>次に向かう所</small><b>羽田</b><span class="u">C 滑走路・約3分</span></div></div>'
     '<div class="btns"><button class="pill main">この機体から見る</button><button class="pill sub">機体図鑑 ›</button></div>'
     '<p class="note">位置は約2分遅れ。高さは機体が送る気圧の高さです。</p></div>') % ICON_X
TAG_SEL = [{'id': 'NH241', 'html': 'NH 241', 'sel': True}, {'id': 'NH59', 'html': 'NH 59'}, {'id': 'JL109', 'html': 'JL 109'}]
page('04-plane-card', '04 機体を押したとき', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over', 'NH 241') + CARD(False) + '</div>',
     draw=scene('day', 'over', more=",sel:'NH241'"), tags=TAG_SEL)
page('04n-plane-card-night', '04 夜：機体を押したとき', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over', 'NH 241') + CARD(True) + '</div>',
     night=True, draw=scene('night', 'over', more=",sel:'NH241'"), tags=TAG_SEL)
# 05 管制塔
TAG_T = [{'id': 'NH17', 'html': 'NH 17'}, {'id': 'NH255', 'html': 'NH 255'}, {'id': 'NH981', 'html': 'NH 981'}]
page('05-tower', '05 管制塔の視点', '<div class="stage"><canvas id="cv"></canvas>' + topbar('管制塔の高さから・約2分遅れ') + seg('tower') +
     '<div class="chip" style="bottom:calc(36vh + 12px)">指で左右に回せます</div>' + sheet(3) + '</div>', draw=scene('day', 'tower'), tags=TAG_T)
# 06 選んだ機体（夕方）
FOLLOW = ('<div class="sheet card"><div class="grab"></div><div class="hd"><div><b class="num big">NH 241</b><div class="rt">福岡 → 羽田　C 滑走路へ</div></div></div>'
          '<div class="grid"><div class="cell"><small>高さ</small><b class="num">420</b><span class="u">m</span></div><div class="cell"><small>着陸まで</small><b class="num">約3</b><span class="u">分</span></div></div>'
          '<div class="btns"><button class="pill sub" style="flex:1">全体に戻る</button><button class="pill sub">くわしく ›</button></div></div>')
page('06-follow-dusk', '06 選んだ機体の視点（夕方）', '<div class="stage"><canvas id="cv"></canvas>' + topbar('NH 241 のうしろから・約2分遅れ') + seg('plane', 'NH 241') + FOLLOW + '</div>',
     draw=scene('dusk', 'follow'))
# 07 空の4つ
page('07a-overview-dusk', '07a 夕方', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') +
     '<div class="chip" style="bottom:calc(36vh + 12px)">夕方・日の入り 16:35</div>' + sheet(3) + '</div>', draw=scene('dusk', 'over'), tags=TAG_AIR)
page('07b-tower-night', '07b 夜（灯り）', '<div class="stage"><canvas id="cv"></canvas>' + topbar('管制塔の高さから・約2分遅れ') + seg('tower') +
     '<div class="chip" style="bottom:calc(36vh + 12px)"><i></i>夜・灯りをつけて表示</div>' + sheet(3) + '</div>', night=True, draw=scene('night', 'tower'), tags=TAG_T)
page('07c-overview-night', '07c 夜（全体）', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') +
     '<div class="chip" style="bottom:calc(36vh + 12px)"><i></i>位置を受信中</div>' + sheet(3) + '</div>', night=True, draw=scene('night', 'over'), tags=TAG_AIR)
page('07d-overview-fog', '07d 雲の多い日・霧', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') +
     '<div class="chip" style="bottom:calc(36vh + 12px)">遠くがかすんで見えます</div>' + sheet(3) + '</div>', draw=scene('fog', 'over'), tags=TAG_AIR)
# 08 読み込み・軽い版・届かない
page('08-loading', '08 開いたときだけ読み込む', '<div class="stage"><div class="ghost"></div>' + topbar('読み込み中') +
     '<div class="load"><h2>3Dを読み込んでいます</h2><p>空港の形と、いまの機体の位置だけを読み込みます。開いたときだけで、閉じると片付けます。</p>'
     '<div class="bar"><i></i></div><div class="n"><span><span class="num">0.9</span><span class="u">MB</span></span><small style="font-size:13px;color:var(--sub)">1.5MB のうち</small></div>'
     '<button class="pill sub">やめる</button></div></div>')
page('08b-lite', '08b 電池の少ないときの軽い版', '<div class="stage"><canvas id="cv"></canvas>' + topbar('軽い表示・約2分遅れ') + seg('over') +
     '<div class="banner"><p><b>電池が少ないので軽い表示です</b>機体は印・灯りなし・10秒ごと</p><button class="pill sub">ふつうに</button></div>' + sheet(3) + '</div>',
     draw=scene('day', 'over', more=',light:true'))
NODATA = ('<div class="sheet"><div class="grab"></div><div class="sh"><h2>機体の位置が届いていません</h2></div>'
          '<p class="note" style="font-size:14px;color:var(--ink)">最後に届いたのは 14:02 です。いまは空港の形だけを表示しています。</p>'
          '<div class="btns"><button class="pill sub" style="flex:1">もう一度読み込む</button></div></div>')
page('08c-no-position', '08c 機体の位置が届かないとき', '<div class="stage"><canvas id="cv"></canvas>' + topbar('最後に届いた位置 14:02') + seg('over') + NODATA + '</div>',
     draw=scene('day', 'over', more=",hideAll:true"))

# 02 入口（空港ページ）
def entry(night):
    return ('<div class="under"><div class="pp"><span class="on">スタンプラリー</span><span>エアライン経営</span></div></div><div class="dlg"><div class="in">'
     '<div class="rec"><h4>押した記録</h4><ul><li>2026年5月28日　空港</li><li>2026年5月17日　空港</li></ul><span class="all">すべて見る（24回）</span></div>'
     '<div class="now3d"><div class="h"><b>空港の今</b><small>14:04 現在</small></div>'
     '<div class="thumb"><canvas id="cv"></canvas><span class="lb">機体 12<small>機・約2分遅れ</small></span><button class="go3">3Dで見る ›</button></div>'
     '<p class="ft">絵は止まった見本です。3Dは押したときだけ読み込みます（約1.5MB）。</p>'
     '<div class="rest"><div><small>出発（この1時間）</small><b class="num">28</b><span class="u">便</span></div><div><small>到着（この1時間）</small><b class="num">31</b><span class="u">便</span></div></div></div>'
     '<p class="later">この下は今の空港ページのまま（守り神・ターミナル・滑走路）</p></div></div>')
page('02-entry', '02 羽田の空港ページの入口', entry(False), draw="{sky:'day',cam:%s,planeScale:3.4}" % CAMS['thumb'])
page('02n-entry-night', '02 夜：羽田の空港ページの入口', entry(True), night=True, draw="{sky:'night',cam:%s,planeScale:3.4}" % CAMS['thumb'])

# シートの高さを全部の頁に
import glob
for f in glob.glob(os.path.join(OUT, '0*.html')):
    s = open(f, encoding='utf-8').read()
    if '.sheet{height:36vh}' not in s:
        s = s.replace('</style>', '.sheet{height:36vh;overflow:hidden}.sheet.card{height:auto}</style>', 1)
        open(f, 'w', encoding='utf-8').write(s)
print('ok')
