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
V2=[('02-entry-v2','02 2版：入口','見本の絵に「© OpenStreetMap」。機体は約1分遅れ'),('03-overview-day-v2','03 2版：全体（昼）','角に「© OpenStreetMap ・ PLATEAU ⓘ」（開いて5秒は出したまま、押すと09）。シートに「羽田から30km・高さ約3,000m（1万フィート）以下と地上」'),
('04-plane-card-v2','04 2版：機体のカード','形は共通・大きさは機種どおり'),('04n-plane-card-night-v2','04 2版：夜の機体のカード',''),('05-tower-v2','05 2版：管制塔（約116m）から','建物の高さは伸ばさない。出典は畳んだ「出典 ⓘ」'),
('06-follow-dusk-v2','06 2版：機体のうしろ（夕方）',''),('07a-overview-dusk-v2','07a 2版：夕方',''),('07b-tower-night-v2','07b 2版：夜の管制塔',''),('07c-overview-night-v2','07c 2版：夜の全体',''),('07d-overview-fog-v2','07d 2版：霧','「霧・14:00 の通報から」。数字は出さない'),
('07e-overview-clouds-v2','07e 2版（新）：雲が低い日','METAR の雲量と雲の高さで雲の層を描く'),('08-loading-v2','08 2版：読み込み中',''),('08b-lite-v2','08b 2版：軽い版','位置は20秒ごと'),('08c-no-position-v2','08c 2版：位置が届かないとき',''),
('09-sources-v2','09 2版（新）：データの出典','「航法には使えません」を上に。形・建物・滑走路・機体・空・機体の大きさの出典'),('09n-sources-night-v2','09 2版（新）：夜のデータの出典','')]
V3=[('02a-open-v3','02a 3版（新）：開いたとき','本物の羽田の空港ページに入口を描いた。入口が「空港の今」のカードの中だけだと、844 でも「3Dで見る ›」はタブ帯の下（844 は 832px・タブ帯 758px、667 は 819px・581px）で、送らないと気づかない'),
('02b-open-pill-v3','02b 3版（新）：開いたとき＋上に小さなピル','数字のカード（押した回数・はじめて押した日）の下に「3Dで見る ›」と「空港の今・機体 12機・約1分遅れ」。844／740／667 とも開いてすぐ見える（上の端 385／377／371px）。入口のカードは下にそのまま'),
('02c-scrolled-v3','02c 3版：送ったところ（入口のカード）','絵の上は「3Dで見る ›」と出典だけ。機体の数は見出しの右（更新の時刻の横）、説明は1行「押すと読み込みます（約1.5MB）」'),
('02n-entry-night-v3','02 3版：夜の入口（見本の形）','夜も同じ形'),
('03-overview-day-v3','03 3版：全体（昼）','受信中の札は上のピルの下（左上）、出典は右下だけ。見出しは「羽田の近くの機体」、範囲は「30km・3,000m 以下と地上」。「機体」は選ぶ前も押せる形'),
('03b-pick-plane-v3','03b 3版（新）：「機体」を押したとき','一覧を引き上げて「見たい機体を押してください」「押すと、その機体のうしろから見ます」'),
('04-plane-card-v3','04 3版：機体のカード','押した機体に寄せ、カードの上の残りの真ん中に置く（667 で札 169〜194px・カード 287px、740 で 204〜229px・360px）。到着便は「着陸まで 約3分」を大きく、補足に「C 滑走路へ」。登録記号は機体図鑑に入っている特別塗装機（JA894A）'),
('04n-plane-card-night-v3','04 3版：夜の機体のカード','740 の写真も png/ にある'),
('05-tower-v3','05 3版：管制塔','名札の3機（駐機中）を一覧の先頭に。「映っている機体から」と書く。出典の畳んだ形は「© OSM ⓘ」'),
('06-follow-dusk-v3','06 3版：機体のうしろ（夕方）',''),('07a-overview-dusk-v3','07a 3版：夕方','夕方の札も上へ'),('07b-tower-night-v3','07b 3版：夜の管制塔',''),('07c-overview-night-v3','07c 3版：夜の全体',''),
('07d-overview-fog-v3','07d 3版：霧','札は「霧（14:00 の通報）」で上へ。出典の札と重ならない'),('07e-overview-clouds-v3','07e 3版：雲が低い','札は「雲が低い（14:00 の通報）」。雲は遠くと上の端だけ薄く、空港の上は透かす'),
('08-loading-v3','08 3版：読み込み中',''),('08b-lite-v3','08b 3版：軽い版',''),('08c-no-position-v3','08c 3版：位置が届かないとき',''),
('09-sources-v3','09 3版：データの出典','OpenStreetMap の著作権のページは押せるリンクの色と ›'),('09n-sources-night-v3','09 3版：夜のデータの出典','')]
V4=[('02a-open-v4','02a 4版：開いたとき','本物の羽田のページ。入口が「空港の今」のカードの中だけだと「3Dで見る ›」は画面の外（844＝832px・タブ帯 758px）'),
('02b-open-pill-v4','02b 4版：開いたとき＋小さな「3Dで見る ›」','ピルの横は「押すと読み込みます（約1.5MB）」の1行（review-2 の5）。844／740／667 の上の端 385／377／371px'),
('02c-scrolled-v4','02c 4版：送ったところ','絵の出典を「© OSM・PLATEAU」にそろえた（10）。絵も北から見た全体の形'),
('02n-open-pill-night-v4','02n 4版（新）：夜・開いたとき','02b と同じ本物のページを夜の色で（4）。小さなピルと「3Dで見る ›」は白い縁。main に夜の画面がまだないので、アプリの暗い色に夜の決まり（金なし）を重ねて撮った'),
('02nc-scrolled-night-v4','02nc 4版（新）：夜・送ったところ','02c と同じ並び・同じ中身'),
('03-overview-day-v4','03 4版：全体（昼）','北の上空から南へ見る形に変えた。空港の先の海の上に、着陸に向かう JL 318（高さ 700m・約3分・C 滑走路の南の端から約13km）。空の機体は影・地面までの点線・名札に高さ（2）'),
('03b-pick-plane-v4','03b 4版：「機体」を押したとき','右上に ×（選ばずにやめる・元の視点とピルに戻す）（8）'),
('03c-picked-v4','03c 4版（新）：一覧から選んだあと','書いてあるとおり、その機体のうしろから。ピルは「JL 318」が選ばれた形（1）。滑走路はまだ前の遠く'),
('04-plane-card-v4','04 4版：地図の機体を押したとき','視点は全体のまま寄せず、横と縦へずらすだけ。ピルは「全体」のまま。カードを閉じると元の全体へ（1）。札の下に塗装名（字だけ）（9）'),
('04n-plane-card-night-v4','04 4版：夜の機体のカード','740 の写真も png/ にある'),
('05-tower-v4','05 4版：管制塔','開いたときは使っている C 滑走路と進入の向き（南）。一覧は名札の上から順（JL 318・BC 509）（6）'),
('06-follow-dusk-v4','06 4版：機体のうしろ（夕方）','滑走路は前の遠くに小さく。自分の機体の下に地面までの点線'),
('07a-overview-dusk-v4','07a 4版：夕方',''),('07b-tower-night-v4','07b 4版：夜の管制塔','「夜・灯りをつけて表示」の緑の点をやめた（緑の点は受信中だけ）（7）'),('07c-overview-night-v4','07c 4版：夜の全体',''),
('07d-overview-fog-v4','07d 4版：霧','札が2つのときは縦に並べる（霧・受信中）（7）'),('07e-overview-clouds-v4','07e 4版：雲が低い','空港と機体は 03 と同じはっきりさ。雲は地平線より上の空だけ（3）'),
('08-loading-v4','08 4版：読み込み中',''),('08b-lite-v4','08b 4版：軽い版',''),('08c-no-position-v4','08c 4版：位置が届かないとき',''),('09-sources-v4','09 4版：データの出典',''),('09n-sources-night-v4','09 4版：夜のデータの出典','')]
SC=[SC[0]]+V4+V3+V2+[(f,t.replace(' ',' 1版：',1),d) for f,t,d in SC[1:]]
rows=''.join('<div class="card"><a class="row" href="%s.html"><img src="png/%s.png" alt=""><span><b>%s</b><small>%s</small><small>低い画面（667）：png/%s-667.png</small></span></a></div>'%(f,f if f!='01-now' else '02-entry',t,d,f) for f,t,d in SC)
page('index.html','空港の3D','<h1>空港の3D（羽田）</h1><p class="sub">ブランチ design/airport-3d・画面案だけ（アプリには入れない・構想段階）。4版は改善担当 review-2 を入れた版（見本の機体は約3分の所・全体は北から見る形）。3版は改善担当 review-1 を入れた版（02 は本物の羽田の空港ページに入口を描いた写真）。2版はデータ担当の調べ（report-airport-3d-data.md）を足した版。11/11 本人「取り入れて」。空港の形は仮のおおまかな配置、便名・登録記号は見本。</p>'
+'<div class="card"><p><b>決めた形</b></p><ul><li>入口は羽田の空港ページの「空港の今」のカードの中。止まった見本の絵＋「3Dで見る ›」。3Dは押したときだけ読み込む</li><li>3版：空の札・受信中の札は上のピルの下（左上）、出典は右下だけ。選んだ機体はカードの上の残りの真ん中に寄せる。入口の見つけるきっかけとして数字のカードの下に小さな「3Dで見る ›」（02b）</li><li>開いた画面は全画面。上に閉じる・題（約1分遅れを常に書く）・設定、その下に視点のピル3つ、下に見えている機体のシート</li><li>視点：全体（ななめ上から）／管制塔（塔の高さ、左右に回す）／機体（選んだ機体のうしろ）。機体は選ぶまで押せない</li><li>空：昼・夕方・夜・雲や霧の4つ。観測と日の出入りで自動。出す字は「夕方・日の入り」「遠くがかすんで見えます」くらいで、天気の数字は出さない。印や実績にはしない</li><li>低いポリゴンは私たちの色（白い建物・灰の滑走路・航空図風の淡い地面）。会社の色は機体に塗らない。特別塗装機だけ尾翼を金（夜は灰）</li><li>夜の画面では光る色は緑と琥珀（琥珀は「いま」の状態と窓）。滑走路の灯りは白い点</li></ul></div>'
+rows+'<h2>作り方</h2><p class="sub">make/scene.js（canvas の小さな描き手・外部の読み込みなし）→ make/make3d.py（1版）・make/make3d_v2.py（2版）・make/make3d_v3.py（3版）・make/make3d_v4.py（4版）→ make/capture_v4.py（4版の 02a〜02nc、main の web/ を http.server 8765 で）→ make/shoot.py &lt;このフォルダの絶対の道&gt; "*-v4" 740 → make/make_index.py。01 の写真は main の web/ を http.server 8765 で開きデモで撮った。</p>')
print('ok')
