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
for name, title, desc in SCREENS:
    cards.append('<article class="card it"><h2>%s</h2><p class="lead">%s</p><div class="sh2"><a href="%s.html"><img src="png/%s.png" alt="%s 昼"></a><a href="%s.html?n=1"><img src="png/%s-n.png" alt="%s 夜"></a></div>'
                 '<p class="lk"><a class="pill" href="%s.html">開く</a><a class="pill" href="%s.html?n=1">夜</a></p></article>' % (title, desc, name, name, title, name, name, title, name, name))
html = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>機体の1週間｜画面案</title><style>%s
body{max-width:860px;padding:24px 16px 60px}
h1{font-size:24px;margin-bottom:6px}
.intro{font-size:14px;color:var(--ink);line-height:1.8}
.warn{margin:14px 0;padding:14px 16px;border-radius:16px;background:#FFF7E6;color:#7A4B00;font-size:13px;line-height:1.7}
.it{margin-top:18px}.it h2{font-size:18px}
.sh2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;align-items:start}
.sh2 img{width:100%%;border-radius:14px;box-shadow:var(--shadow)}
.lk{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.lk .pill{text-decoration:none;font-size:13px}
table{width:100%%;border-collapse:separate;border-spacing:0 6px;font-size:13px;margin-top:8px}
td,th{padding:8px 10px;text-align:left;vertical-align:top;background:var(--card)}
th{color:var(--sub);font-weight:700;background:transparent}
td:first-child{border-radius:12px 0 0 12px;font-weight:800;color:var(--strong);white-space:nowrap}
td:last-child{border-radius:0 12px 12px 0}
</style></head><body>
<h1>機体の1週間（画面案）</h1>
<p class="intro">登録記号ごとに、その機体がこの1週間に飛んだ便を日ごとに並べる案です。今の「機体の1日」（今日と予想）の上に「今日｜1週間」を足し、入口は いまの空港の「機体」・撮る人の機体のくわしく・特別塗装機の図鑑 の3つ。地図は紺の地に航路の跡を重ねます。機体・便・時刻はすべて見本です。</p>
<p class="warn"><b>本人の見直しで作った画面案です。</b>却下済みの「機体と運航の実績」を 11/27 に本人が見直し、「まず画面案を見て決める」段階。アプリには入れていません。機体図鑑は特別塗装機だけのままで、ふつうの機体は登録記号で探して出します。</p>
<table><tr><th></th><th>案A 日ごとの一覧（おすすめ）</th><th>案B 1週間の帯</th></tr>
<tr><td>見え方</td><td>今の「機体の1日」の行と同じ形が日ごとに続く。定刻・実際・遅れが1行で読める</td><td>7日の動きが1枚で分かる（どの時間に何便）。短い便は空港コードが入らない</td></tr>
<tr><td>長さ</td><td>今日と前の2日は開き、ほかは「羽田→福岡→羽田…」の1行にたたむ</td><td>帯は1枚。くわしくは日を押してから</td></tr>
<tr><td>推定</td><td>「推定」は点線の下線、時刻は「ごろ 離陸」</td><td>点線の枠だけの箱</td></tr>
<tr><td>作る手間</td><td>今の行の部品をそのまま使える（少ない）</td><td>帯の部品を新しく作る</td></tr></table>
%s
<p style="margin-top:18px;font-size:12px;color:var(--mute)">測った値（390×844・375×667・夜）：12px 未満 %d・44 未満のボタン %d・はみ出し %d・字の切れ %d・エラー %d・動きを減らす設定で動くもの %d。全体の写真は png/*-full.png。作り方：make/build.py → make/shoot.py → make/index.py</p>
</body></html>''' % (CSS, ''.join(cards), tot['small'], tot['tap'], tot['over'], tot['cut'], len(M['errors']), rm)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)
print('一覧を作った')
