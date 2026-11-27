# -*- coding: utf-8 -*-
# 一覧ページ：各画面の PNG を並べ、押すと動く HTML を開く。外部の読み込みはなし
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
VARS = open(HERE + '/src/vars.css', encoding='utf-8').read()
NOTE = {
 'n1-futsu': '次のフライト（あと○日）→いちばん近い空港と距離→次の小目標。押せないチェックインは出さない。近い空港のコード（パタパタ）は白いカードの中に小さく残す',
 'n2-noplan': '予定がないとき：「次の予定を入れる」と「行ったことがある空港をまとめて記録」。まとめて記録は印とは別の記録と書く',
 'n3-small': 'シート小：次のフライトの1行だけ。地図を広く見る',
 'n4-large': 'シート大：地方ごとの進み・今の成績の帯（今日の印・空港・フライト）・近い空港',
 'n5-near': '判定範囲のすぐ外（ターミナルの奥で位置がずれた）：「羽田空港にいますか？もう一度位置を確かめる」。押すと測り直すだけで、印は範囲の中でしか押せない',
 'a1-pill': '案A：全幅の金のピル「羽田にチェックイン」。押すと右の半券が切れて落ち、「本日チェックイン済み」に変わる（0.36秒）',
 'b1-stub': '案B（おすすめ）：今の黒いカードを残し、半券を下の横長に。つまみを右へ引いて切る（7割で切れる）。親指の届く所で、ポケットの中の誤操作も起きにくい',
 'b1-first': 'はじめての空港：回数の代わりに緑の札「はじめての空港」',
 'b2-offline': '電波が悪い：今の保留と同じ「電波が戻ったら、あとで送ります」。空港のいまは最後に読んだ時刻を出す',
 'b3-done': '済み：黒いカードの下が「本日チェックイン済み」に。次にやる「今日の便を記録」を上へ',
 'b4-small': 'シート小（空港）：黒いカードと半券だけ',
 'b5-large': 'シート大（空港）：今日の便の候補・羽田のいま・この空港の訪問',
}
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
CSS = r'''
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--gothic);max-width:1200px;margin:0 auto;padding:28px 16px 80px;line-height:1.6;font-size:15px}
h1{font-size:24px;font-weight:800;color:var(--strong)}
h2{font-size:18px;font-weight:800;color:var(--strong);margin:36px 0 4px}
.lead{margin-top:6px;font-size:14px;color:var(--sub)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin-top:14px}
.it{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:12px;display:flex;flex-direction:column;gap:8px;color:inherit;text-decoration:none}
.it img{width:100%;border-radius:14px;display:block;background:var(--track)}
.it b{font-size:15px;color:var(--strong)}
.it p{font-size:13px;color:var(--sub)}
.it .vs{display:flex;flex-wrap:wrap;gap:6px}
.it .vs a{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--strong);text-decoration:none}
.box{margin-top:12px;background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:16px 18px 16px 34px;font-size:14px}
.box li{margin:6px 0}
.box li small{display:block;font-size:13px;color:var(--mute)}
'''
def card(name, title):
    k = name[:-5]; png = 'png/%s.png' % k
    vs = ['<a href="%s">開く</a>' % name, '<a href="png/%s-667.png">375 幅</a>' % k]
    if os.path.exists(OUT + '/png/%s-n.png' % k): vs.append('<a href="png/%s-n.png">夜</a>' % k)
    if os.path.exists(OUT + '/png/%s-ta.png' % k): vs.append('<a href="png/%s-ta.png">タブ4つ</a>' % k)
    for i in (1, 2):
        if os.path.exists(OUT + '/png/%s-move%d.png' % (k, i)): vs.append('<a href="png/%s-move%d.png">動き%d</a>' % (k, i, i))
    return '<div class="it"><a href="%s"><img src="%s" alt="%s" loading="lazy"></a><b>%s</b><p>%s</p><div class="vs">%s</div></div>' % (name, png, title, title, NOTE.get(k, ''), ''.join(vs))
N = [s for s in S if s[0].startswith('n')]; A = [s for s in S if not s[0].startswith('n')]
body = ('<h1>ホームの「ふだん」と「空港にいるとき」</h1>'
        '<p class="lead">骨格は今のまま「地図とシート」。シートは小・ふつう・大の3段で、空港の判定範囲の中か外かで中身が入れ替わる。各 HTML は ?night=1 で夜、?tabs=a で下のタブ4つ（design/ia-ops の案A）。390 と 375 で撮影。地図はデモで撮った今の地図（国土地理院）</p>'
        '<h2>ふだん（空港の外）</h2><div class="grid">%s</div>'
        '<h2>空港にいるとき（案A と案B、4つの状態）</h2><div class="grid">%s</div>'
        '<h2>チェックインの4つの状態</h2><ul class="box">'
        '<li>空港の外：出さない（N1）。すぐ外なら「もう一度位置を確かめる」だけ（N5）</li>'
        '<li>中・まだ：半券を引く（B1）／全幅のピル（A1）</li>'
        '<li>中・電波が悪い：引けるが「あとで送ります」（B2）。今の保留と同じ動き</li>'
        '<li>済み：「本日チェックイン済み」＋今日の便を記録（B3）</li></ul>'
        '<h2>入れないもの</h2><ul class="box">'
        '<li>「直近15分に圏内にいた」「空港の Wi-Fi」だけで印を通す案<small>印は現地で押したものだけ・最後の判定はサーバー</small></li>'
        '<li>天気の表示、運用を集めるバッジ、案内板風を全体に<small>案内板風は近い空港のコード（パタパタ）だけ</small></li>'
        '<li>航空会社のロゴ<small>便名の前は「JL」「NH」の小さな字の札だけ</small></li></ul>') % (''.join(card(*s) for s in N), ''.join(card(*s) for s in A))
html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>ホームの画面案</title><style>%s\n%s</style></head><body>%s</body></html>') % (VARS, CSS, body)
open(OUT + '/index.html', 'w', encoding='utf-8').write(html); print('書いた index.html')
