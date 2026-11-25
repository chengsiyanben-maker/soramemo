# -*- coding: utf-8 -*-
# 一覧ページ：画面ごとの PNG（390×844）を並べ、押すとその画面の HTML を開く
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
NIGHT = {'g1-boarding', 'g2-arrive', 'f2-form', 'r1-repeat', 'c2-outdoor'}
GROUPS = [('g', '① 搭乗中・到着印待ちのカード', '出発の印から8時間、ホームのシートのいちばん上。別の空港の範囲に入ったら「到着印を押す」を大きく'),
          ('e', '② 0件の画面の文言', '何の場所かを1行＋どうすると埋まるか1行＋押すもの1つ。E0 が今の文と案の表'),
          ('c', '③ 屋外で読めるか', 'C1 が今の色の測り（4.5:1 の目安）と案、C2 が色だけにしない見本'),
          ('f', '④ 意見を送る', 'マイページの目次の最後に1行。3択＋自由文、位置は送らない'),
          ('r', '⑤ 2回目以降の完了カード', '今のカードに「通算14回目・23日ぶり」の1行を足すだけ（印をもらったときのカード 案B にはもう入っている）')]
css = ('body{margin:0;background:#F4F5F7;color:#374151;font-family:"Hiragino Sans","Noto Sans JP",system-ui,sans-serif}'
       '.w{max-width:1200px;margin:0 auto;padding:24px 16px 60px}h1{font-size:24px;color:#1F2937}h2{font-size:19px;color:#1F2937;margin:34px 0 4px}'
       'p{font-size:14px;line-height:1.6}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:16px;margin-top:12px}'
       'a{display:block;text-decoration:none;color:#1F2937;font-size:13px;font-weight:700}a img{width:100%;border-radius:18px;box-shadow:0 10px 30px -8px rgba(17,24,39,.18);background:#fff}'
       'a span{display:block;margin-top:6px;line-height:1.45}a small{color:#6B7280;font-weight:600}')
out = ['<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gemini 上位の画面案（11/26）</title><style>%s</style></head><body><div class="w">' % css,
       '<h1>Gemini との話し合いの上位から 5つの画面案</h1><p>画面案だけ（アプリには入れない）。押すと HTML が開きます。?night=1 で夜。写真は 390×844 と 375×667（-667）</p>']
for k, t, d in GROUPS:
    out.append('<h2>%s</h2><p>%s</p><div class="g">' % (t, d))
    for name, title, kind in S:
        if name[0] != k: continue
        n = name[:-5]
        out.append('<a href="%s"><img src="png/%s.png" alt="" loading="lazy"><span>%s%s</span></a>' % (name, n, title, '<br><small>夜：png/%s-n.png</small>' % n if n in NIGHT else ''))
    out.append('</div>')
out.append('</div></body></html>')
open(D + '/index.html', 'w', encoding='utf-8').write(''.join(out)); print('書いた index.html')
