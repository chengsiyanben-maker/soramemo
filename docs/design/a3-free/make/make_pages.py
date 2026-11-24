# -*- coding: utf-8 -*-
# 一覧ページ（index.html）を作る。絵は png/ の 390 幅のもの
import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
G = [
 ('今', [('00-now', '00 今', '視点は「全体・管制塔・機体」の3つ。指で左右に回せるだけ')]),
 ('案A（おすすめ）：上のピルを4つの見方にする', [
   ('A1-free-guide', 'A1 自由・はじめての1回', '開いたら「自由」。はじめての人にだけ指の動き4つのカード'),
   ('A2-free-moved', 'A2 自由・寄ったところ', '動かしたら右上に「全体に戻す」（今の「全体」の位置へ）'),
   ('A3a-follow-pick', 'A3a 追う・機体を選ぶ', '機体が決まっていないときは、近くの機体のシートから選ぶ'),
   ('A3-follow', 'A3 追う', '機体の後ろに付いて動く。付く位置は後ろ・横・前、指で角度と距離'),
   ('A3b-follow-lost', 'A3b 機体が消えた', '位置が届かなくなったら自由に戻し、下に一言と「ほかを追う」'),
   ('A4-stand-pick', 'A4 立つ・場所を選ぶ', '先頭に「管制塔」（今の視点）、展望デッキ・滑走路の端。地面を押した所にも'),
   ('A5-stand', 'A5 立つ', '目の高さ 約1.6m。向きの札と「場所を変える」'),
   ('A6-fly', 'A6 飛ぶ', '左のつまみで進む、右で上下と向き。高さを大きな数字で'),
   ('A6b-fly-limit', 'A6b 飛ぶ・上限', '1,000m で止まり「これより上には行けません」'),
 ]),
 ('案B：見方は下の4つのボタン（親指の届く所）', [
   ('B1-free', 'B1 自由', '上のピルをなくし、空が広い。指の案内は札の1行'),
   ('B5-stand', 'B5 立つ', '向きの札と「場所」は上に'),
   ('B6-fly', 'B6 飛ぶ', '飛ぶのつまみと4つのボタンが下に重なり、混む'),
 ]),
]
css = """*{box-sizing:border-box;margin:0;padding:0}body{font-family:"Hiragino Sans","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;background:#F4F5F7;color:#1F2937;padding:24px 16px 48px}
h1{font-size:22px;font-weight:800;margin-bottom:6px}p.lead{font-size:14px;color:#4B5563;line-height:1.7;margin-bottom:16px}
.box{background:#fff;border-radius:20px;box-shadow:0 2px 12px rgba(15,22,38,.06);padding:16px 18px;margin-bottom:18px;font-size:14px;line-height:1.75}
.box b{font-weight:800}.box li{margin-left:1.2em}
h2{font-size:17px;font-weight:800;margin:26px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
a.it{display:block;background:#fff;border-radius:18px;box-shadow:0 2px 12px rgba(15,22,38,.06);padding:8px 8px 12px;color:inherit;text-decoration:none}
a.it img{display:block;width:100%;border-radius:12px}
a.it b{display:block;font-size:14px;font-weight:800;margin:8px 4px 2px}a.it span{display:block;font-size:12px;color:#6B7280;margin:0 4px;line-height:1.5}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:8px 6px;vertical-align:top}tr+tr td{box-shadow:inset 0 1px 0 #F1F3F6}th{color:#6B7280;font-weight:600}td:first-child,th:first-child{white-space:nowrap}"""
body = ['<h1>羽田の3D を自由に動かす（画面案 1版）</h1><p class="lead">本人が選んだ4つの見方（自由・追う・立つ・飛ぶ）の入れ方。案は2つ。背景は今の羽田の3D（main の web/・デモ）を昼にして撮ったもの。どの画面も390×844 と 375×667 で、12px 未満の字・44px 未満の押す所・はみ出し・字の切れは 0。</p>',
 '<div class="box"><b>今の3つの視点はどうなるか（案A・案B 共通）</b><ul><li>全体 → 「自由」のはじめの位置。動かしたら「全体に戻す」で戻る</li><li>管制塔 → 「立つ」のおすすめの場所の先頭（高さ 約118m は今のまま）</li><li>機体 → 「追う」（今の機体の視点を、付く位置と指で変えられるように）</li></ul></div>',
 '<div class="box"><b>指の動き</b><table><tr><th>見方</th><th>1本指</th><th>2本指</th><th>ほか</th></tr>'
 '<tr><td>自由</td><td>なぞって回す</td><td>つまんで寄る・離れる／なぞってずらす／上下で傾ける</td><td>地面の下・空港から遠すぎる所には行かない</td></tr>'
 '<tr><td>追う</td><td>なぞって角度</td><td>つまんで距離</td><td>付く位置 後ろ・横・前。機体が消えたら自由へ</td></tr>'
 '<tr><td>立つ</td><td>なぞって見回す</td><td>つまんでズーム（目の位置は動かない）</td><td>地面を押すとそこに立つ（約1.6m）</td></tr>'
 '<tr><td>飛ぶ</td><td>左のつまみで前後左右</td><td>—</td><td>右のボタンで上下・向き。高さ 1,000m まで</td></tr></table>'
 '<p style="margin-top:8px">「閉じる」（左上の ×）はどの見方でもいつも押せる。はじめての案内は「自由」で1回だけ、ほかの見方ははじめて開いたときに上の札の1行だけ。</p></div>']
for t, items in G:
    body.append('<h2>%s</h2><div class="grid">' % t)
    for f, n, d in items:
        body.append('<a class="it" href="%s.html"><img src="png/%s.png" alt="%s"><b>%s</b><span>%s</span></a>' % (f, f, n, n, d))
    body.append('</div>')
open(ROOT + '/index.html', 'w').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>3D を自由に動かす 画面案</title><style>%s</style></head><body>%s</body></html>' % (css, ''.join(body)))
