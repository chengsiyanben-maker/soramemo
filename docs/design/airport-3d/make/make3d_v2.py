# -*- coding: utf-8 -*-
# 空港の3D 2版：データ担当の調べ（report-airport-3d-data.md）を1版に足す。make3d.py を読み、言葉と設定を差し替えて *-v2.html に書き出す
# 使い方：python3 make3d_v2.py → python3 shoot.py <フォルダの絶対の道> '*-v2' → python3 make_index.py
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'make3d.py'), encoding='utf-8').read()
R = [
 ('約2分遅れ', '約1分遅れ'),
 # 管制塔は本当の高さ（115.7m）から。建物も高さを伸ばさない
 (''''tower': "{pos:HND.P(640,-420,232),tgt:HND.P(420,700,0),fov:60,cy:.40}"''', ''''tower': "{pos:HND.P(640,-420,124),tgt:HND.P(430,650,0),fov:60,cy:.40}"'''),
 ("hide = ',hideTower:true' if cam == 'tower' else ''", "hide = (',hideTower:true,vx:1' if cam == 'tower' else '') + ',real:true'"),
 ("'管制塔の高さから・約1分遅れ'", "'管制塔（約116m）から・約1分遅れ'"),
 # 見えている機体の範囲
 ('<h2>見えている機体</h2><span><span class="num">12</span><span class="u">機</span></span></div>%s%s</div>',
  '<h2>見えている機体</h2><span><span class="num">12</span><span class="u">機</span></span></div><p class="rng">羽田から30km・高さ約3,000m（1万フィート）以下と地上</p>%s%s</div>'),
 # 機体のカード
 ('<p class="note">位置は約1分遅れ。高さは機体が送る気圧の高さです。</p>', '<p class="note">位置は約1分遅れ。高さは機体が送る気圧の高さ。形は共通で、大きさは機種どおり（B787-9 長さ63m）。</p>'),
 # 軽い版
 ('機体は印・灯りなし・10秒ごと', '機体は印・灯りなし・20秒ごと'),
 # 霧：通報の時刻
 ("'<div class=\"chip\" style=\"bottom:calc(36vh + 12px)\">遠くがかすんで見えます</div>'", "'<div class=\"chip\" style=\"bottom:calc(36vh + 12px)\">霧・14:00 の通報から</div>'"),
 # 入口の注意
 ('絵は止まった見本です。3Dは押したときだけ読み込みます（約1.5MB）。', '絵は止まった見本です。3Dは押したときだけ読み込みます（約1.5MB）。機体は約1分遅れです。'),
 ("page('", "page2('"),
]
for a, b in R:
    if a not in src: raise SystemExit('見つからない：' + a[:40])
    src = src.replace(a, b)
src = src.replace("def page2(fn,", "def page(fn,")
# 出典のピル（角）と、データの出典のシート
EXTRA = r'''
CSS += """.rng{font-size:13px;color:var(--sub);margin:-2px 4px 4px}
.src{position:absolute;right:16px;height:44px;display:flex;align-items:center}
.src span{height:32px;padding:0 12px;border-radius:999px;background:var(--glass);box-shadow:var(--shadow);font-size:13px;color:var(--sub);display:inline-flex;align-items:center;gap:6px;backdrop-filter:blur(8px)}
.src b{font-weight:700;color:var(--ink)}
.srcs .it{background:var(--wash);border-radius:16px;padding:10px 12px;margin-top:8px}.srcs .it small{display:block;font-size:13px;color:var(--sub)}.srcs .it p{margin:2px 0 0;font-size:14px;line-height:1.55}
.srcs .warn{font-size:14px;font-weight:700;margin:12px 4px 0}
.sheet.tall{height:auto;max-height:78vh;overflow:auto}"""
SRC_FULL = '<div class="src" style="bottom:calc(36vh + 6px)"><span>© OpenStreetMap ・ PLATEAU <b>ⓘ</b></span></div>'
SRC_FOLD = '<div class="src" style="bottom:calc(36vh + 6px)"><span>出典 <b>ⓘ</b></span></div>'
def page2(fn, title, body, night=False, draw=None, tags=None):
    if 'class="sheet"' in body and 'chip' in body:
        body = body.replace('<div class="sheet">', (SRC_FOLD if fn in ('05-tower', '07b-tower-night') else SRC_FULL) + '<div class="sheet">', 1)
    page(fn + '-v2', title.replace(' ', ' 2版：', 1), body, night, draw, tags)
'''
src = src.replace("ICON_X = ", EXTRA + "\nICON_X = ", 1)
src = src.replace("for f in glob.glob(os.path.join(OUT, '0*.html')):", "for f in glob.glob(os.path.join(OUT, '*-v2.html')):")
src = src.replace(".sheet.card{height:auto}</style>", ".sheet.card,.sheet.tall{height:auto}</style>")
# 足す画面：雲の低い日・データの出典
ADD = r'''
page2('07e-overview-clouds', '07e 雲の低い日', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') +
     '<div class="chip" style="bottom:calc(36vh + 12px)">雲が低い日</div>' + sheet(3) + '</div>', draw=scene('fog', 'over', more=",clouds:{base:650,amt:6}"), tags=TAG_AIR)
SRCS = ('<div class="sheet tall srcs"><div class="grab"></div><div class="sh"><h2>データの出典</h2><button class="rb" aria-label="閉じる" style="box-shadow:none;background:var(--wash)">%s</button></div>'
 '<p class="warn" style="margin:0 4px 4px">航法には使えません。形は簡単にしています。</p>'
 '<div class="it"><small>空港の形（滑走路・誘導路・エプロン・ターミナル）</small><p>© OpenStreetMap のデータを加工して作成（ODbL）<br>openstreetmap.org/copyright</p></div>'
 '<div class="it"><small>建物の高さ</small><p>出典：国土交通省 PLATEAU（3D都市モデル・大田区）を加工して作成</p></div>'
 '<div class="it"><small>滑走路の端の位置</small><p>AIP JAPAN をもとに作成</p></div>'
 '<div class="it"><small>機体の位置</small><p>そらメモが受け取った位置を約1分遅らせて表示</p></div>'
 '<div class="it"><small>空</small><p>空港の気象通報（METAR）。日の出・日の入りはこの端末で計算</p></div>'
 '<div class="it"><small>機体の大きさ</small><p>FAA Aircraft Characteristics Database</p></div>'
 '</div>') % ICON_X
page2('09-sources', '09 データの出典', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') + SRCS + '</div>', draw=scene('day', 'over'))
page2('09n-sources-night', '09 夜：データの出典', '<div class="stage"><canvas id="cv"></canvas>' + topbar() + seg('over') + SRCS + '</div>', night=True, draw=scene('night', 'over'))
'''
src = src.replace('<button class="go3">3Dで見る ›</button>', '<span class="lb" style="top:auto;bottom:10px;font-weight:600;color:var(--sub)">© OpenStreetMap</span><button class="go3">3Dで見る ›</button>')
src = src.replace("# 02 入口（空港ページ）", ADD + "\n# 02 入口（空港ページ）", 1)
exec(compile(src, 'make3d_v2', 'exec'))
