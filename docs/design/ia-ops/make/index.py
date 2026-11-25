# -*- coding: utf-8 -*-
# 一覧ページ（外部の読み込みなし・PNG は同じフォルダの png/ を相対で見る）
import os
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(HERE)
CSS=open(HERE+'/base.css',encoding='utf-8').read()
def fig(f,cap,href=None):
    img='<img src="png/%s.png" alt="%s" loading="lazy">'%(f,cap)
    return '<figure>%s<figcaption>%s</figcaption></figure>'%(('<a href="%s">%s</a>'%(href,img)) if href else img, cap)
body='''<header class="hd"><h1>タブの組み替えと「いまの空港」</h1><p class="lead">画面案 1版（11/25）。2案を並べて比べる。押すと 390 幅の HTML が開く。アプリには入れない</p></header>
<section class="cmp card"><h2>2案のちがい</h2>
<dl><div><dt>案A</dt><dd>下のタブを4つ（ホーム／いまの空港／記録／マイページ）。記録の中を上のピルでフライト｜図鑑｜修行（修行は ON の人だけ）。右上のマイページのピルはなくなる</dd></div>
<div><dt>案B</dt><dd>タブは今のまま（ホーム・図鑑・フライト・運用・修行。使い方の構成で隠せる）。「運用」の名前だけ「いまの空港」に</dd></div>
<div><dt>おすすめ</dt><dd><b>案B</b>。11/8 に決めた「タブから選ぶ（出すタブと順番を選ぶ・ON／OFF）」と、11/24 のマイページ案B（右上のピル）がそのまま生きる。修行はすでに隠せるので、案A の「修行を隠す」利点は今の形で足りている</dd></div></dl></section>
<h2 class="sh2">案A</h2><div class="grid">'''+fig('a1-now','A1 いまの空港（今日の便）','a1-now.html')+fig('a2-record','A2 記録（フライト｜図鑑｜修行）','a2-record.html')+'''</div>
<h2 class="sh2">案B</h2><div class="grid">'''+fig('00-now','00 今の運用タブ')+fig('b1-now','B1 いまの空港（今日の便）','b1-now.html')+'''</div>
<h2 class="sh2">どちらの案でも同じ中身</h2><p class="lead">下のタブだけ違う。ここでは案B のタブで描いた</p><div class="grid">'''+fig('k1-runway','K1 滑走路・3D','k1-runway.html')+fig('k2-livery','K2 特別塗装機','k2-livery.html')+fig('k3-sheet','K3 便を押したとき','k3-sheet.html')+fig('k4-small','K4 データが少ない空港（大分）','k4-small.html')+fig('k5-pick','K5 空港を選ぶ','k5-pick.html')+'''</div>
<section class="cmp card"><h2>今までの決定との合わせ方</h2>
<dl><div><dt>並べ替え（11/23）</dt><dd>案A・案B とも：今のカード（滑走路・地図・3D・案内板・特別塗装機…）を3つのピルに振り分け、並べ替えと隠すは各ピルの中で使える</dd></div>
<div><dt>マイページ（11/24）</dt><dd>案A：タブの4つ目になり、右上のピルはなくす。案B：今のまま右上のピルからタイルのページへ</dd></div>
<div><dt>3D の見方（11/25）</dt><dd>案A・案B とも：「滑走路・3D」の中の「開く」で、今の全画面の3D（下の4つのボタン＋管制塔のピル）をそのまま開く。開くまでは読まない</dd></div>
<div><dt>ピン止め（11/17）</dt><dd>案A・案B とも：空港のピルがピン止めの入口。空港を選ぶシートはピン止めが先頭、次に今いる空港・次の便の空港</dd></div></dl></section>
<section class="cmp card"><h2>入れていないもの</h2><p class="lead">「図鑑に記録」ボタン（図鑑は乗った・見た記録からだけ）／搭乗口（規約を確かめ中）／天気の印／運用を集めるバッジ／案内板風を全体に。特別塗装機の名前と登録記号は見本</p></section>
<section class="cmp card"><h2>測った値</h2><p class="lead">390 と 375 で：12px 未満の字 0・44px 未満のボタン 0・横のはみ出し 0</p></section>'''
css=CSS+'''body{padding:0 16px 60px;max-width:860px}.hd{padding:28px 0 8px}.cmp{margin-top:16px}.cmp dl{margin-top:8px;display:grid;gap:10px}.cmp dl div{display:grid;grid-template-columns:7.5em 1fr;gap:8px;font-size:14px}.cmp dt{font-weight:800;color:var(--strong)}.sh2{margin:30px 0 4px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-top:10px}figure img{width:100%;border-radius:18px;box-shadow:var(--shadow);display:block}figcaption{margin-top:6px;font-size:13px;font-weight:700;color:var(--sub)}'''
open(OUT+'/index.html','w',encoding='utf-8').write('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>タブの組み替えといまの空港</title><style>%s</style></head><body>%s</body></html>'%(css,body))
print('書いた index.html')
