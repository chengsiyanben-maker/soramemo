# -*- coding: utf-8 -*-
# 01 今（今の羽田の空港ページの写真）と一覧ページを作る。make3d.py と shoot.py のあとに。
import os, base64
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(HERE)
CSS=""":root{--bg:#EEF1F5;--card:#fff;--ink:#24292F;--sub:#6B7280;--shadow:0 10px 24px -16px rgba(15,23,42,.35)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;line-height:1.6}
.w{max-width:560px;margin:0 auto;padding:20px 16px 48px}h1{font-size:22px;margin:4px 0}h2{font-size:17px;margin:26px 0 8px}p,li{font-size:14px}.sub{color:var(--sub);font-size:13px}
.card{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:14px 16px;margin-top:12px}.shot{display:block;width:100%;max-width:300px;margin:10px auto 0;border-radius:18px;box-shadow:var(--shadow)}
a.row{display:flex;gap:12px;align-items:center;text-decoration:none;color:inherit}a.row img{width:96px;border-radius:12px;box-shadow:var(--shadow);flex:none}a.row b{display:block;font-size:15px}a.row small{display:block;font-size:13px;color:var(--sub)}ul{padding-left:20px}"""
def page(fn,t,b): open(os.path.join(OUT,fn),'w',encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body><div class="w">%s</div></body></html>'%(t,CSS,b))
img='data:image/png;base64,'+base64.b64encode(open(os.path.join(HERE,'now','hnd-844.png'),'rb').read()).decode()
page('01-now.html','01 今の羽田の空港ページ','<h1>01 今（main の web/ をデモで撮った）</h1><p class="sub">2026年11月11日の main。羽田の空港ページ。下に「空港の今」のカード（読み込み中）、守り神・ターミナル・滑走路が続く。</p><div class="card"><img class="shot" src="%s" alt="今の羽田の空港ページ"><p>3Dの入口は「空港の今」のカードの中に置く（02）。印・記録の上の段は変えない。</p></div>'%img)
SC=[('01-now','01 今','今の羽田の空港ページ'),('02-entry','02 入口（空港ページ）','「空港の今」のカードに止まった見本の絵と「3Dで見る ›」。押したときだけ読み込む（約1.5MB）'),('02n-entry-night','02 夜：入口','夜の画面。主ボタンは白い字と縁'),
('03-overview-day','03 全体の視点（昼）','上に閉じる・題・設定、その下に視点のピル（全体／管制塔／機体）、下に見えている機体のシート。空の機体だけ名札'),
('04-plane-card','04 機体を押したとき','便名・どこから→どこへ・機種・登録記号・高さ・次に向かう所。特別塗装機は札と「機体図鑑 ›」'),('04n-plane-card-night','04 夜：機体を押したとき','会社の色と金を使わない。札は灰'),
('05-tower','05 管制塔の視点','管制塔の高さから。指で左右に回せる'),('06-follow-dusk','06 選んだ機体の視点（夕方）','機体のうしろから。下は高さと着陸までの2つだけ'),
('07a-overview-dusk','07a 夕方','空と光を夕方に。日の入りの時刻だけ出す'),('07b-tower-night','07b 夜（灯り）','滑走路の縁は白、誘導路は緑、建物の窓は琥珀'),('07c-overview-night','07c 夜（全体）','灯りの線で形が分かる'),('07d-overview-fog','07d 雲の多い日・霧','遠くをかすませるだけ。天気の数字は出さない'),
('08-loading','08 開いたときだけ読み込む','大きさと進み具合、やめる'),('08b-lite','08b 電池の少ないときの軽い版','機体は印だけ・灯りなし・10秒ごと。「ふつうに」で戻す'),('08c-no-position','08c 機体の位置が届かないとき','空港の形だけ出し、最後に届いた時刻を書く')]
rows=''.join('<div class="card"><a class="row" href="%s.html"><img src="png/%s.png" alt=""><span><b>%s</b><small>%s</small><small>低い画面（667）：png/%s-667.png</small></span></a></div>'%(f,f if f!='01-now' else '02-entry',t,d,f) for f,t,d in SC)
page('index.html','空港の3D','<h1>空港の3D（羽田）</h1><p class="sub">ブランチ design/airport-3d・画面案だけ（アプリには入れない・構想段階）。11/11 本人「取り入れて」。空港の形は仮のおおまかな配置、便名・登録記号は見本。</p>'
+'<div class="card"><p><b>決めた形</b></p><ul><li>入口は羽田の空港ページの「空港の今」のカードの中。止まった見本の絵＋「3Dで見る ›」。3Dは押したときだけ読み込む</li><li>開いた画面は全画面。上に閉じる・題（約2分遅れを常に書く）・設定、その下に視点のピル3つ、下に見えている機体のシート</li><li>視点：全体（ななめ上から）／管制塔（塔の高さ、左右に回す）／機体（選んだ機体のうしろ）。機体は選ぶまで押せない</li><li>空：昼・夕方・夜・雲や霧の4つ。観測と日の出入りで自動。出す字は「夕方・日の入り」「遠くがかすんで見えます」くらいで、天気の数字は出さない。印や実績にはしない</li><li>低いポリゴンは私たちの色（白い建物・灰の滑走路・航空図風の淡い地面）。会社の色は機体に塗らない。特別塗装機だけ尾翼を金（夜は灰）</li><li>夜の画面では光る色は緑と琥珀（琥珀は「いま」の状態と窓）。滑走路の灯りは白い点</li></ul></div>'
+rows+'<h2>作り方</h2><p class="sub">make/scene.js（canvas の小さな描き手・外部の読み込みなし）→ make/make3d.py → make/shoot.py &lt;このフォルダの絶対の道&gt; → make/make_index.py。01 の写真は main の web/ を http.server 8765 で開きデモで撮った。</p>')
print('ok')
