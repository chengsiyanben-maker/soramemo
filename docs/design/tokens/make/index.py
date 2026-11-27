# -*- coding: utf-8 -*-
# 一覧ページ：ページごとの PNG（390 幅）を並べ、押すとその HTML を開く
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
NIGHT = {'t2-surface', 't3-type', 't5-carrier'}
css = ('body{margin:0;background:#EEF1F5;color:#374151;font-family:"Hiragino Sans","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif}'
       '.w{max-width:1200px;margin:0 auto;padding:24px 20px 60px}h1{font-size:22px;color:#1F2937;line-height:1.35}p{font-size:14px;line-height:1.6}'
       '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:16px;margin-top:16px}'
       'a{display:block;text-decoration:none;color:#1F2937;font-size:14px;font-weight:700;min-height:44px}'
       'a .im{height:300px;overflow:hidden;border-radius:18px;box-shadow:0 10px 30px -8px rgba(17,24,39,.18),inset 0 0 0 1px #DCE1E8;background:#fff}a img{width:100%;display:block}'
       'a span{display:block;margin-top:6px;line-height:1.45}a small{color:#6B7280;font-weight:600;font-size:13px}')
out = ['<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>見た目の基準表（11/26）</title><style>%s</style></head><body><div class="w">' % css,
       '<h1>見た目の基準表：今のアプリと Gemini の案を突き合わせる</h1><p>表と見本だけ（アプリには入れない）。押すと HTML が開きます。?night=1 で夜。写真は png/ に 390 幅（2倍）と 375 幅（-375）、夜は -n</p><div class="g">']
for name, title, kind in S:
    n = name[:-5]
    out.append('<a href="%s"><div class="im"><img src="png/%s.png" alt="" loading="lazy"></div><span>%s%s</span></a>' % (name, n, title, '<br><small>夜：png/%s-n.png</small>' % n if n in NIGHT else ''))
out.append('</div></div></body></html>')
open(D + '/index.html', 'w', encoding='utf-8').write(''.join(out)); print('書いた index.html')
