# -*- coding: utf-8 -*-
# 空港の3D 4版：改善担当 review-2 を3版に入れる。make3d_v3.py を読み、名前を *-v4 にして書き出したあと、HTML を差し替える
# 必ず直す3つ：03b で選んだあとは「うしろから」へ（03c）・04 は全体の視点のまま横と縦へずらすだけ（ピルは全体のまま）／
#             空の機体に影と地面までの縦の線と名札の高さ、約3分の所（海の上・滑走路の延長）に置く／02n 夜の入口は本物のページの夜の色（capture_v4.py）
# 使い方：python3 make3d_v4.py → python3 capture_v4.py（main の web/ を http.server 8765 で）→ python3 shoot.py <フォルダの絶対の道> '*-v4' 740 → python3 make_index.py
import os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
v3 = open(os.path.join(HERE, 'make3d_v3.py'), encoding='utf-8').read()

def rep(s, a, b, n=1):
    if a not in s: raise SystemExit('見つからない：' + a[:70])
    return s.replace(a, b) if n == 0 else s.replace(a, b, n)

# 見る向き：全体は北の上空から南へ（空港の先に、着陸に向かう海の上の機体が見える）。管制塔はいま使っている C 滑走路と進入の向き（南）
CAM_OVER = "{pos:HND.P(0,7000,2000),tgt:HND.P(800,-3000,0),fov:58,cy:.42}"
CAM_TOWER = "{pos:HND.P(640,-420,124),tgt:HND.P(980,-4200,0),fov:60,cy:.40}"
CAM_FOLLOW = "{pos:HND.P(950,-14600-260,700+46),tgt:HND.P(950,-1580,0),fov:58,cy:.40}"

R4 = r'''
R += [
 # 6：管制塔は映っている機体を、画面の上から順に一覧の先頭に
 ("""LIST_T = [('NH 17', '伊丹へ', '駐機中', '第2ターミナル', False, False), ('NH 255', '福岡へ', '駐機中', '第2ターミナル', False, False), ('NH 981', '石垣へ', '駐機中', '第2ターミナル', False, False)]""",
  """LIST_T = [('NH 241', '福岡から', '着陸まで約3分', 'C 滑走路へ', True, True), ('BC 509', '神戸へ', '地上を走行中', 'C 滑走路へ', False, False), ('JL 109', '伊丹へ', '離陸中', 'A 滑走路', True, False)]"""),
 ("""TAG_T = [{'id': 'NH17', 'html': 'NH 17'}, {'id': 'NH255', 'html': 'NH 255'}, {'id': 'NH981', 'html': 'NH 981'}]""",
  """TAG_T = [{'id': 'NH241', 'html': 'NH 241<small>420m</small>'}, {'id': 'BC509', 'html': 'BC 509'}]"""),
]
'''
v3 = rep(v3, 'v2 = rep(v2, "for a, b in R:", R3 + "for a, b in R:")', 'v2 = rep(v2, "for a, b in R:", R3 + R4 + "for a, b in R:")')
# 03c：一覧から選んだあと（うしろから・ピルは選んだ機体）
ADD4 = r'''
page2('03c-picked', '03c 一覧から機体を選んだあと', '<div class="stage"><canvas id="cv"></canvas>' + topbar('NH 241 のうしろから・約1分遅れ') + seg('plane', 'NH 241') + FOLLOW + '</div>',
      draw=scene('day', 'follow'))
'''
v3 = rep(v3, 'v2 = rep(v2, "page2(\'07e-overview-clouds\'", ADD3 + "\\npage2(\'07e-overview-clouds\'")',
         'v2 = rep(v2, "page2(\'07e-overview-clouds\'", ADD3 + ADD4 + "\\npage2(\'07e-overview-clouds\'")')
# 名前
v3 = rep(v3, "page(fn + '-v3', title.replace(' ', ' 3版：', 1)", "page(fn + '-v4', title.replace(' ', ' 4版：', 1)")
v3 = rep(v3, "glob.glob(os.path.join(OUT, '*-v3.html'))", "glob.glob(os.path.join(OUT, '*-v4.html'))")
v3 = rep(v3, "'02-entry-v3.html'", "'02-entry-v4.html'")
v3 = rep(v3, "exec(compile(src, 'make3d_v3', 'exec'))", "exec(compile(src, 'make3d_v4', 'exec'))")
exec(compile(v3, 'make3d_v3_for_v4', 'exec'))
# 02n（見本の形の夜の入口）は capture_v4.py で本物のページの夜の色に描き直すので消す
os.remove(os.path.join(OUT, '02n-entry-night-v4.html'))

# ここから HTML の差し替え（全部の *-v4.html）
LIV = 'A350 1号機（赤のロゴ）'   # アプリの LIVERY_NAMES にある名前（字だけ）
for f in sorted(glob.glob(os.path.join(OUT, '*-v4.html'))):
    s = open(f, encoding='utf-8').read(); n = os.path.basename(f)
    # 見本の機体：着陸に向かう機体は約3分の所（C 滑走路の南の端から約13km・高さ700m）。特別塗装機は名前が人物でない JAL の A350 にする
    if 'drawAirport' in s: s = rep(s, "{id:'NH241', fl:'NH 241', to:'福岡から', arr:true, st:'着陸まで約3分', ty:'B787-9', reg:'JA871A', alt:420,  pos:P(950,-3300), h:337, z:420, sp:true}",
               "{id:'JL318', fl:'JL 318', to:'福岡から', arr:true, st:'着陸まで約3分', ty:'A350-900', reg:'JA01XJ', alt:700,  pos:P(950,-14600), h:337, z:700, sp:true}")
    if 'drawAirport' in s: s = rep(s, "pos:P(760,-500), h:157", "pos:P(760,-1300), h:157")
    s = s.replace('NH 241', 'JL 318').replace('NH241', 'JL318')
    s = s.replace('<b class="num">B787-9</b>', '<b class="num">A350-900</b>').replace('JA894A', 'JA01XJ').replace('B787-9 長さ63m', 'A350-900 長さ67m')
    s = s.replace('<b class="num">420</b><span class="u">m</span>', '<b class="num">700</b><span class="u">m</span>').replace('JL 318<small>420m</small>', 'JL 318<small>700m</small>')
    # 視点
    s = s.replace("{pos:HND.P(200,-6000,3000),tgt:HND.P(-150,-1300,0),fov:56,cy:.36}", CAM_OVER)
    s = s.replace("{pos:HND.P(640,-420,124),tgt:HND.P(430,650,0),fov:60,cy:.40}", CAM_TOWER)
    s = s.replace("{pos:HND.P(950,-3300-200,420+48),tgt:HND.P(950,-1300,0),fov:58,cy:.40}", CAM_FOLLOW)
    # 1：04 は全体の視点のまま（寄せない）。選んだ機体を横と縦へずらしてシートの上の残りの真ん中へ
    s = re.sub(r"cam:\{pos:HND\.P\(260,-7300,2500\),tgt:HND\.P\(950,-3300,420\),fov:52,cy:\.5\},planeScale:2\.4", "cam:" + CAM_OVER + ",planeScale:3", s)
    s = s.replace(",sel:'JL318',fitSheet:true", ",sel:'JL318',shiftTo:'JL318'")
    # 2：空の機体に影と縦の線、名札に高さ
    s = s.replace("planeScale:", "airCue:true,planeScale:")
    s = s.replace('JL 318<small>着陸</small>', 'JL 318<small>700m</small>').replace('NH 59<small>上昇</small>', 'NH 59<small>900m</small>')
    s = s.replace('"html": "JL 318", "sel": true', '"html": "JL 318<small>700m</small>", "sel": true')
    s = s.replace('cam:' + CAM_OVER + ',', 'cam:' + CAM_OVER + ',airScale:2.5,')   # 全体では空の機体を大きめに描く（見つけやすく）
    # 名札は左上の札の下から（札が2つなら2つ目の下から）
    s = s.replace('p.y<(st.querySelector(".chip")?196:150)', 'p.y<(function(){var m=150;st.querySelectorAll(".chip").forEach(function(c){m=Math.max(m,c.getBoundingClientRect().bottom+38)});return m})()')
    # 7：緑の点は「受信中」だけ
    s = s.replace('<i></i>夜・灯りをつけて表示', '夜・灯りをつけて表示')
    if n.startswith('07d'):   # 7：札が2つのときは縦に並べる
        s = rep(s, '霧（14:00 の通報）</div>', '霧（14:00 の通報）</div><div class="chip" style="top:164px"><i></i>位置を受信中</div>')
    if n.startswith('07e'):   # 3：雲が低い日は空港をはっきり、雲は空の部分だけ
        s = rep(s, "sky:'fog'", "sky:'overcast'"); s = rep(s, "clouds:{base:650,amt:6,thin:true}", "clouds:{top:true}")
    if n.startswith('03b'):   # 8：選ばずにやめる ×
        s = rep(s, '<h2>見たい機体を押してください</h2></div>', '<h2>見たい機体を押してください</h2><button class="rb" aria-label="やめる" style="box-shadow:none;background:var(--wash)"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>')
        s = s.replace('.sh{display:flex;align-items:baseline;', '.sh{display:flex;align-items:center;')
    if n.startswith('04'):    # 9：特別塗装機の札の下に塗装名（字だけ）
        s = rep(s, '福岡 → 羽田　<span class="sp">特別塗装機</span></div>', '福岡 → 羽田　<span class="sp">特別塗装機</span></div><div class="lv">%s</div>' % LIV)
        s = s.replace('</style>', '.lv{font-size:13px;color:var(--sub);margin-top:2px}</style>', 1)
    open(f, 'w', encoding='utf-8').write(s)
print('ok v4')
