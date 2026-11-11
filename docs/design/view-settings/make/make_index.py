# -*- coding: utf-8 -*-
# 一覧ページ（index.html）を作る。使い方：python3 make_index.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CSS_DAY, CSS
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = [
 ('01 今の見方の設定', [('01-now', '01 今のばらばらな所')], '開く物が3通り（シート・修行の別のページ・ホームの別のページ）、部品が2通り（ON／OFF と ✓ のピル）。表示の編集の1枚に修行がない'),
 ('02 各画面の鉛筆のシート', [('02a-book-sheet', '02a 図鑑'), ('02b-log-sheet', '02b フライト（日誌・地図・年のまとめ）'), ('02b2-log-sheet-off', '02b2 OFF にしたところ'), ('02c-sg-sheet', '02c 修行（見方＋道のりに出すもの）'), ('02d-ops-sheet', '02d 運用（7つ）'), ('02e-ops-sheet-last', '02e 最後の1つ')],
  '全部同じ形：題・数・完了は上に固定、OFF の行はその場に残り「見方の帯から隠しています」、下に「元に戻す」の帯、いちばん下に「表示の編集をすべて見る」。修行は別のページをやめて同じシートに（道のりに出すものは見出しで分ける・番号は外す）'),
 ('03 マイページ「表示の編集」の1枚', [('03a-layout-top', '03a いちばん上'), ('03b-layout-sg', '03b 修行・運用のところ'), ('03c-layout-bottom', '03c いちばん下（全部乗せに戻す）'), ('03d-layout-from-pen', '03d 鉛筆の「すべて見る」から'), ('03e-layout-hidden', '03e 隠しているものだけ')],
  '画面ごとのカード（見出しを押すとその画面へ）の下に ON／OFF の行。✓ のピルと取り消し線はやめる。題と「‹ マイページ」は上に固定、「全部乗せに戻す」はいちばん下。経営は入れない'),
 ('04 いつも出す物の行', [('04-always', '04 いつもの行と最後の1つ')], 'スイッチの代わりに「いつも」（スイッチと同じ幅）。最後の1つはスイッチを薄くして「見方は1つより減らせません」'),
 ('05 夜（667 は各画面の png/*-667.png）', [('02a-book-sheet-night', '夜：図鑑の見方'), ('02b-log-sheet-night', '夜：フライトの見方'), ('03a-layout-top-night', '夜：表示の編集')], '夜は ON を強い字と細い縁（会社の色・金・琥珀は使わない）。いつもの印も光らせない'),
]
css = """.wrap{padding:16px 16px 60px}.g{margin-top:22px}.g h2{font-size:18px;margin:0 4px 8px;color:var(--strong)}
.th{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px}.th a{flex:none;width:150px;text-decoration:none;color:var(--ink);font-size:13px;font-weight:700}
.th img{width:150px;border-radius:14px;box-shadow:var(--shadow);display:block;margin-bottom:6px}"""
s = '<div class="wrap"><h1 style="font-size:24px;margin:8px 4px 0;color:var(--strong)">すべての見方の設定</h1><p class="note">ブランチ design/view-settings。画面案だけでアプリには入れない。幅390・高さ844で作り、png/ に 844（2倍）と 667 の写真。本人の決定（11/11 11時「両方」）：各画面の鉛筆と、マイページの1枚。</p>'
for t, items, d in G:
    s += '<section class="g"><h2>%s</h2><div class="th">%s</div><p class="note">%s</p></section>' % (t, ''.join('<a href="%s.html"><img src="png/%s.png" alt="">%s</a>' % (f, f, c) for f, c in items), d)
s += '</div>'
open(OUT + '/index.html', 'w').write('<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>すべての見方の設定</title><style>%s%s%s</style></head><body>%s</body></html>\n' % (CSS_DAY, CSS, css, s))
