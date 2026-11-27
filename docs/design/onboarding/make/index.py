# -*- coding: utf-8 -*-
# 一覧ページ：2つの流れ（案A・案B）と、各画面の PNG。外部の読み込みはなし
import os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
VARS = open(HERE + '/src/vars.css', encoding='utf-8').read()
S = [
 ('o1-intro', 'O1 導入', '専門の言葉なしで1行。「はじめる」と、ログイン・デモで試す（残す）'),
 ('o2-persona', 'O2 使い方', '今の使い方のアンケート（撮る・修行・気軽・あとで決める）をここへ。最初の構成を決める'),
 ('o3-visited', 'O3 行ったことがある空港', '押すと数字がその場で増える。地方ごとに開く。選んだ空港は淡いピン（メモ）で、印とは別'),
 ('o3b-zero', 'O3b 0件', '0% は出さず「これから最初の1空港へ」。ボタンは「まだない・次へ」'),
 ('o4-plan', 'O4 次のフライト', '出発・到着・日付の3つだけ。便名はあとから'),
 ('o4b-myap', 'O4b 予定なし', 'いちばん身近な空港を1つ。ホームからその空港のいまを見られる'),
 ('o5-ready', 'O5 できた記録と許可の理由', '先に理由を書いてから許可を聞く。位置の文は iPhone の画面案（ios-app）と同じ。通知は入れなくても使える'),
 ('o6-home', 'O6 ホームに着いた', 'メモの淡いピンが地図に並ぶ。初回だけ「いま空港にいなくても試せます」（閉じたら出さない）'),
 ('b1-backup', '案B 初めてのチェックインで登録', '印はサーバーで確かめるので、ここで登録が要る。メモと予定もいっしょに保存。無料'),
]
CSS = r'''
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--gothic);max-width:1200px;margin:0 auto;padding:28px 16px 80px;line-height:1.6;font-size:15px}
h1{font-size:24px;font-weight:800;color:var(--strong)}
h2{font-size:18px;font-weight:800;color:var(--strong);margin:36px 0 4px}
.lead{margin-top:6px;font-size:14px;color:var(--sub)}
.flow{margin-top:12px;background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:16px}
.flow b.t{font-size:16px;color:var(--strong)}
.flow p{font-size:13px;color:var(--sub)}
.steps{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.steps span{display:inline-flex;align-items:center;min-height:36px;padding:0 14px;border-radius:999px;background:var(--track);font-size:13px;font-weight:800;color:var(--strong)}
.steps span.now{background:transparent;box-shadow:inset 0 0 0 1.5px #B4BBC5;color:var(--sub)}
.steps i{font-style:normal;color:var(--mute);font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin-top:14px}
.it{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:12px;display:flex;flex-direction:column;gap:8px}
.it img{width:100%;border-radius:14px;display:block}
.it b{font-size:15px;color:var(--strong)}
.it p{font-size:13px;color:var(--sub)}
.vs{display:flex;flex-wrap:wrap;gap:6px}
.vs a{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--strong);text-decoration:none}
.box{margin-top:12px;background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:16px 18px 16px 34px;font-size:14px}
.box li{margin:6px 0}
.box li small{display:block;font-size:13px;color:var(--mute)}
'''
def card(k, t, n):
    vs = ['<a href="%s.html">開く</a>' % k, '<a href="png/%s-667.png">375 幅</a>' % k]
    for sfx, lb in (('-n', '夜'), ('-end', '下まで送る'), ('-move1', '押したとき')):
        if os.path.exists(OUT + '/png/%s%s.png' % (k, sfx)): vs.append('<a href="png/%s%s.png">%s</a>' % (k, sfx, lb))
    return '<div class="it"><a href="%s.html"><img src="png/%s.png" alt="%s" loading="lazy"></a><b>%s</b><p>%s</p><div class="vs">%s</div></div>' % (k, k, t, t, n, ''.join(vs))
def steps(xs): return '<div class="steps">' + '<i>›</i>'.join('<span class="%s">%s</span>' % ('now' if x.startswith('今の') else '', x) for x in xs) + '</div>'
body = ('<h1>はじめて開いたときの流れ</h1>'
        '<p class="lead">60〜90秒で「自分の地図に色がつき、次に開く理由がホームにある」状態にする。390 と 375、O1・O3・O6 は夜も。各 HTML は押して試せる（空港を選ぶと数字が増える）。枠だけのピルは今の画面のまま</p>'
        '<h2>ログインをどこに置くか（2案）</h2>'
        '<div class="flow"><b class="t">案A　今の流れを残す（ログインの流れは変えない）</b><p>導入のあと、今の登録（メール・6けたのコード・同意・名前は空でよい）をしてから、使い方・行った空港・予定・許可へ。メモは最初からサーバーに入る</p>'
        + steps(['O1 導入', '今のログイン・登録', 'O2 使い方', 'O3 行った空港', 'O4 予定', 'O5 許可', 'O6 ホーム']) + '</div>'
        '<div class="flow"><b class="t">案B　端末の中で始めて、あとで登録（本人の OK が要る）</b><p>登録なしで O2〜O6 まで進む。印はサーバーで確かめるので、初めてのチェックインのときに登録（b1）。マイページの「データとバックアップ」からも登録できる。バックアップは無料</p>'
        + steps(['O1 導入', 'O2 使い方', 'O3 行った空港', 'O4 予定', 'O5 許可', 'O6 ホーム', '初めてのチェックインで登録（b1）']) + '</div>'
        '<ul class="box"><li>今のはじめの案内（3枚）は O1〜O5 に置き換えて、なくす<small>3枚の中身（印を押す・半券を切る・図鑑）は、ホームで初めて空港に入ったときの1行の案内へ移す</small></li>'
        '<li>今いる利用者には出さない<small>出すのは新しく始める人だけ。今いる人の「一度だけの同意」は今のまま</small></li></ul>'
        '<h2>画面</h2><div class="grid">%s</div>'
        '<h2>守ったこと</h2><ul class="box"><li>行ったことがあるは「メモ」で、印とは別の記録・別の見た目（淡いピン）。現地で押すと印に変わる</li>'
        '<li>空港の数は実際の数（86）。0%% は出さない</li><li>天気・案内板風を全体に・ロゴは使わない（便名の前も字だけ）</li><li>バックアップは有料にしない</li></ul>') % ''.join(card(*s) for s in S)
html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>はじめての流れの画面案</title><style>%s\n%s</style></head><body>%s</body></html>') % (VARS, CSS, body)
open(OUT + '/index.html', 'w', encoding='utf-8').write(html); print('書いた index.html')
