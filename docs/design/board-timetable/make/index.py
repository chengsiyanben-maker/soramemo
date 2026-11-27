# -*- coding: utf-8 -*-
# 一覧ページ（index.html）を作る。画像は同じフォルダの png/ を使う（外部の読み込みなし）
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CSS = open(HERE + '/base.css', encoding='utf-8').read()
SCREENS = json.load(open(HERE + '/screens.json', encoding='utf-8'))
M = json.load(open(HERE + '/measure.json', encoding='utf-8'))
tot = {k: sum(len(v.get(k, [])) for v in M['measure'].values()) for k in ['small', 'tap', 'over', 'cut']}
rm = sum(v.get('running', 0) for k, v in M['measure'].items() if k.endswith('-rm'))
cards = []
for name, title, kind, plan, desc in SCREENS:
    cards.append(
        '<article class="card it"><h2>%s</h2><p class="lead">%s</p>'
        '<div class="sh"><a href="%s.html"><img src="png/%s-list.png" alt="%s の一覧の部分"></a>'
        '<img src="png/m-%s.png" alt="状況が変わったときのパタパタのコマ"></div>'
        '<p class="lk"><a class="pill" href="%s.html">開く</a><a class="pill" href="%s.html?n=1">夜</a><a class="pill" href="%s.html?rm=1">動きを減らす</a></p></article>'
        % (title, desc, name, name, title, name, name, name, name))
html = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>案内板を時刻表に｜画面案</title><style>%s
body{max-width:820px;padding:24px 16px 60px}
h1{font-size:24px;margin-bottom:6px}
.intro{font-size:14px;color:var(--ink);line-height:1.8}
.warn{margin:14px 0;padding:14px 16px;border-radius:16px;background:#FFF7E6;color:#7A4B00;font-size:13px;line-height:1.7}
.it{margin-top:18px}
.it h2{font-size:18px}
.sh{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;align-items:start}
.sh img{width:100%%;border-radius:14px;box-shadow:var(--shadow)}
.lk{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.lk .pill{text-decoration:none;font-size:13px;min-height:44px}
table{width:100%%;border-collapse:separate;border-spacing:0 6px;font-size:13px;margin-top:8px}
td,th{padding:8px 10px;text-align:left;vertical-align:top;background:var(--card)}
th{color:var(--sub);font-weight:700;background:transparent}
td:first-child{border-radius:12px 0 0 12px;font-weight:800;color:var(--strong);white-space:nowrap}
td:last-child{border-radius:0 12px 12px 0}
@media (max-width:560px){.sh{grid-template-columns:1fr}}
</style></head><body>
<h1>案内板を時刻表に（画面案）</h1>
<p class="intro">「いまの空港」の今日の便の一覧だけを、空港の出発・到着の時刻表のように列をそろえた案です。列は 定刻（変更後）・便名・行き先（経由）・機材・ゲート・状況。数字は等幅で大きく太く、パタパタは状況が変わったセルだけ（動きを減らす設定では字が変わるだけ）。便・機材・ゲートはすべて見本で、実在の今日の便ではありません。</p>
<p class="warn"><b>決まりとの食い違い：</b>デザインの原則「出発案内板風は近い空港のコードと最近の印だけ」と、却下済み「アプリ全体を出発案内板風にする案」に触れるため、PM が本人に確認中です。この画面案は本人の OK まで入れません。案A も紺の地は今日の便のカードの中だけにとどめ、上の頭・ピル・タブは今のままです。</p>
<table><tr><th></th><th>案A 紺の地に白・黄</th><th>案B 明るい角丸カード</th></tr>
<tr><td>見え方</td><td>空港の時刻表にいちばん近い。屋外でも白と黄がはっきり</td><td>今の画面と地続き。ほかのカードと並んでも浮かない</td></tr>
<tr><td>遅れ</td><td>変更後の時刻と「遅れ」を黄</td><td>変更後の時刻と「遅れ」を今の茶色（#9A3412）</td></tr>
<tr><td>欠航</td><td>黄の札「欠航」、行は薄く</td><td>枠のピル「欠航」、時刻・便名・行き先に線</td></tr>
<tr><td>夜の画面</td><td>黄を緑に（夜は光る色を緑だけ）</td><td>今の夜の色。遅れは淡い橙</td></tr>
<tr><td>決まりとの距離</td><td>案内板風が一覧全体に広がる（遠い）</td><td>見た目は今の原則のまま（近い）</td></tr></table>
%s
<p class="note" style="margin-top:18px;font-size:12px;color:var(--mute)">測った値（390×844・375×667・夜）：12px 未満 %d・44 未満のボタン %d・はみ出し %d・字の切れ %d・エラー %d・動きを減らす設定で動くもの %d。作り方：make/build.py → make/shoot.py → make/index.py</p>
</body></html>''' % (CSS, ''.join(cards), tot['small'], tot['tap'], tot['over'], tot['cut'], len(M['errors']), rm)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
print('一覧を作った')
