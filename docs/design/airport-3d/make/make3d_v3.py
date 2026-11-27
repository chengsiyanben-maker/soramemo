# -*- coding: utf-8 -*-
# 空港の3D 3版：改善担当 review-1 を2版に入れる。make3d_v2.py を読み、さらに差し替えて *-v3.html に書き出す
# 必ず直す3つ：04 の 667／740 で選んだ機体がカードの上に見える寄せ方・下の段の札と出典の重なり（空の札は上へ）・02 入口の開いたときの1枚（capture_v3.py で本物の画面に描く）
# 使い方：python3 make3d_v3.py → python3 capture_v3.py（main の web/ を http.server 8765 で）→ python3 shoot.py <フォルダの絶対の道> '*-v3' 740 → python3 make_index.py
import os
HERE = os.path.dirname(os.path.abspath(__file__))
v2 = open(os.path.join(HERE, 'make3d_v2.py'), encoding='utf-8').read()

def rep(s, a, b, n=1):
    if a not in s: raise SystemExit('見つからない：' + a[:60])
    return s.replace(a, b) if n == 0 else s.replace(a, b, n)

# make3d.py に当てる差し替え（2版の差し替えのあとに当てる）
R3 = r'''
R += [
 # 10：見出しを「羽田の近くの機体」に、範囲は短く。一覧を差し替えられるように
 ("""def rows(n, night=False):
    out = ''
    for fl, to, st, s2, now, sp in LIST[:n]:""", """LIST_T = [('NH 17', '伊丹へ', '駐機中', '第2ターミナル', False, False), ('NH 255', '福岡へ', '駐機中', '第2ターミナル', False, False), ('NH 981', '石垣へ', '駐機中', '第2ターミナル', False, False)]
def rows(n, night=False, L=None):
    out = ''
    for fl, to, st, s2, now, sp in (L or LIST)[:n]:"""),
 ("""def sheet(n=3, extra=''):
    return '<div class="sheet"><div class="grab"></div><div class="sh"><h2>見えている機体</h2><span><span class="num">12</span><span class="u">機</span></span></div><p class="rng">羽田から30km・高さ約3,000m（1万フィート）以下と地上</p>%s%s</div>' % (rows(n), extra)""",
  """def sheet(n=3, extra='', L=None, h2='羽田の近くの機体', rng='30km・3,000m 以下と地上', cnt=True, cls=''):
    c = '<span><span class="num">12</span><span class="u">機</span></span>' if cnt else ''
    return '<div class="sheet%s"><div class="grab"></div><div class="sh"><h2>%s</h2>%s</div><p class="rng">%s</p>%s%s</div>' % (cls, h2, c, rng, rows(n, L=L), extra)"""),
 # 4：管制塔は映っている機体（名札の3機）を一覧の先頭に
 ("""'<div class="chip" style="bottom:calc(36vh + 12px)">指で左右に回せます</div>' + sheet(3)""", """'<div class="chip" style="bottom:calc(36vh + 12px)">指で左右に回せます</div>' + sheet(3, L=LIST_T, rng='30km・3,000m 以下と地上・映っている機体から')"""),
 ("""'<div class="chip" style="bottom:calc(36vh + 12px)"><i></i>夜・灯りをつけて表示</div>' + sheet(3)""", """'<div class="chip" style="bottom:calc(36vh + 12px)"><i></i>夜・灯りをつけて表示</div>' + sheet(3, L=LIST_T, rng='30km・3,000m 以下と地上・映っている機体から')"""),
 # 5：「機体」は選ぶ前も押せる形のまま（押すと 03b）
 ("dis=(plane is None and on != 'plane')", "dis=False"),
 # 6：到着便は「着陸まで 約3分」を大きく、補足に C 滑走路。登録記号は機体図鑑に入っている特別塗装機（B787-9）
 ("""<div class="cell"><small>次に向かう所</small><b>羽田</b><span class="u">C 滑走路・約3分</span></div>""",
  """<div class="cell"><small>着陸まで</small><b class="num">約3</b><span class="u">分</span><small>C 滑走路へ</small></div>"""),
 ("JA871A", "JA894A"),
 # 1：04 は選んだ機体に寄せ、シートの上の残りの真ん中に置く（667／740 でもカードに隠れない）
 ("""draw=scene('day', 'over', more=",sel:'NH241'"), tags=TAG_SEL)""", """draw=scene('day', 'focus', more=",sel:'NH241',fitSheet:true"), tags=TAG_SEL)"""),
 ("""draw=scene('night', 'over', more=",sel:'NH241'"), tags=TAG_SEL)""", """draw=scene('night', 'focus', more=",sel:'NH241',fitSheet:true"), tags=TAG_SEL)"""),
 ("""psv = ps or {'over': 3, 'tower': 1.3, 'follow': 1}[cam]""", """psv = ps or {'over': 3, 'tower': 1.3, 'follow': 1, 'focus': 2.4}[cam]"""),
 (""" 'thumb': "{pos:HND.P(450,-5300,2900),tgt:HND.P(100,-500,0),fov:46,cy:.52}",""", """ 'thumb': "{pos:HND.P(450,-5300,2900),tgt:HND.P(100,-500,0),fov:46,cy:.52}",
 'focus': "{pos:HND.P(260,-7300,2500),tgt:HND.P(950,-3300,420),fov:52,cy:.5}","""),
 # 2：霧の札は短く
 ('霧・14:00 の通報から', '霧（14:00 の通報）'),
 # 9：入口の絵の上は「3Dで見る ›」と出典だけ。機体の数は見出しの右、説明は1行
 ('<span class="lb">機体 12<small>機・約1分遅れ</small></span>', ''),
 ('<small>14:04 現在</small>', '<small>14:04 現在・機体 12機</small>'),
 ('絵は止まった見本です。3Dは押したときだけ読み込みます（約1.5MB）。機体は約1分遅れです。', '押すと読み込みます（約1.5MB）'),
]
'''
v2 = rep(v2, "for a, b in R:", R3 + "for a, b in R:")
# 2版の足し分（EXTRA・ADD）にも当てる
v2 = rep(v2, "SRC_FOLD = '<div class=\"src\" style=\"bottom:calc(36vh + 6px)\"><span>出典 <b>ⓘ</b></span></div>'",
         "SRC_FOLD = '<div class=\"src\" style=\"bottom:calc(36vh + 6px)\"><span>© OSM <b>ⓘ</b></span></div>'")   # 7：畳んでも名前を残す
v2 = rep(v2, "'<div class=\"chip\" style=\"bottom:calc(36vh + 12px)\">雲が低い日</div>' + sheet(3) + '</div>', draw=scene('fog', 'over', more=\",clouds:{base:650,amt:6}\")",
         "'<div class=\"chip\" style=\"bottom:calc(36vh + 12px)\">雲が低い（14:00 の通報）</div>' + sheet(3) + '</div>', draw=scene('fog', 'over', more=\",clouds:{base:650,amt:6,thin:true}\")")   # 8
v2 = rep(v2, "openstreetmap.org/copyright</p>", "<a class=\"lk\">openstreetmap.org/copyright ›</a></p>")   # 7：押せるリンクの形
v2 = rep(v2, ".sheet.tall{height:auto;max-height:78vh;overflow:auto}\"\"\"",
         ".sheet.tall{height:auto;max-height:78vh;overflow:auto}\n.lk{display:inline-flex;align-items:center;min-height:44px;color:var(--link);font-weight:700;text-decoration:none}\n:root{--link:#1F5FA8}:root[data-night]{--link:#9CC2F0}\n.sheet.pick{height:52vh}.sheet .hintp{font-size:14px;font-weight:700;color:var(--ink);margin:0 4px 6px}\"\"\"")
# 3版の名前
v2 = rep(v2, "page(fn + '-v2', title.replace(' ', ' 2版：', 1)", "page(fn + '-v3', title.replace(' ', ' 3版：', 1)")
v2 = rep(v2, "glob.glob(os.path.join(OUT, '*-v2.html'))", "glob.glob(os.path.join(OUT, '*-v3.html'))")
# 2：空の札・受信中の札・回せますの札は、上のピルの下（左上）へ。出典は右下のまま。名札はその札の下から
ADD3 = r'''
# 03b 「機体」を押したとき（まだ選んでいない）：一覧を引き上げて、押せばその機体から見られると書く
page2('03b-pick-plane', '03b 「機体」を押したとき', '<div class="stage"><canvas id="cv"></canvas>' + topbar() +
      '<div class="seg"><button>全体</button><button>管制塔</button><button class="on">機体</button></div>' +
      sheet(4, h2='見たい機体を押してください', rng='押すと、その機体のうしろから見ます', cnt=False, cls=' pick') + '</div>', draw=scene('day', 'over'), tags=TAG_AIR)
'''
v2 = rep(v2, "page2('07e-overview-clouds'", ADD3 + "\npage2('07e-overview-clouds'")
v2 = rep(v2, "exec(compile(src, 'make3d_v2', 'exec'))",
 "src = src.replace('style=\"bottom:calc(36vh + 12px)\"', 'style=\"top:126px\"')\n"
 "src = src.replace('if(!p||p.z<5||p.y<150||p.y>lim)return;', 'if(!p||p.z<5||p.y<(st.querySelector(\".chip\")?196:150)||p.y>lim)return;')\n"
 "src = src.replace(\"'.sheet{height:36vh;overflow:hidden}.sheet.card,.sheet.tall{height:auto}</style>'\", \"'.sheet{height:36vh;overflow:hidden}.sheet.card,.sheet.tall{height:auto}.sheet.pick{height:52vh}</style>'\")\n"
 "exec(compile(src, 'make3d_v3', 'exec'))")
exec(compile(v2, 'make3d_v2_for_v3', 'exec'))
# 02 の昼は本物の空港ページで描く（capture_v3.py の 02a〜02c）ので、見本の形の昼は書き出さない。夜（02n）は残す
os.remove(os.path.join(os.path.dirname(HERE), '02-entry-v3.html'))
