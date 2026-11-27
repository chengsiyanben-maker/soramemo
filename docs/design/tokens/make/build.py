# -*- coding: utf-8 -*-
# 見た目の基準表（design/tokens）：今のアプリを測った値（survey.json）と Gemini の基準を並べ、案を付ける。
# 1画面1ファイル。外部の読み込みなし。?night=1 で夜。作り方：survey.py → build.py → shoot.py → index.py
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)

def lum(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
def crs(a, b):
    v = cr(a, b); return ('%.2f' % v) if v < 2 else ('%.1f' % v)

BASE = r'''
:root{
  --gothic:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic UI","Yu Gothic","Meiryo","Noto Sans JP","Noto Sans CJK JP",system-ui,sans-serif;
  --bg:#EEF1F5; --card:#FFFFFF; --ink:#374151; --strong:#1F2937; --sub:#4B5563; --mute:#6B7280; --mute-on-box:#5F6672;
  --box:#F1F3F6; --ring:#DCE1E8; --ring-now:rgba(17,24,39,.07); --hero:#0F1B2D; --hero-sub:#C9D2DE;
  --late:#B42318; --ok:#15803D; --pill:#E6E9EE; --pill-on:#1F2937; --pill-on-ink:#FFFFFF;
  --shadow:0 1px 2px rgba(17,24,39,.04),0 10px 30px -8px rgba(17,24,39,.10);
  --keep:#E7EEF7; --keep-ink:#23406A; --take:#E7F4EC; --take-ink:#1F6B3A; --no:#F4E9E7; --no-ink:#8A2A1C;
}
:root[data-night=on]{
  --bg:#0F141B; --card:#1B1F26; --ink:#E5E7EB; --strong:#F3F4F6; --sub:#C3CBD5; --mute:#AEB9C6; --mute-on-box:#AEB9C6;
  --box:#232830; --ring:rgba(255,255,255,.10); --ring-now:rgba(255,255,255,.06); --hero:#141B24; --hero-sub:#AEB9C6;
  --late:#F87171; --ok:#4ADE80; --pill:#262B33; --pill-on:#DCE3EA; --pill-on-ink:#0F141B;
  --shadow:0 12px 26px -16px rgba(0,0,0,.7);
  --keep:#1E2A3B; --keep-ink:#B9CDE8; --take:#1B2E23; --take-ink:#9EDDB4; --no:#33201D; --no-ink:#F1B3A8;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--ink);font-family:var(--gothic);-webkit-text-size-adjust:100%}
body{padding:20px 20px 48px;font-size:15px;line-height:1.55}
.top{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.back{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow),inset 0 0 0 1px var(--ring);color:var(--strong);font-weight:700;font-size:14px;text-decoration:none}
h1{font-size:22px;font-weight:800;color:var(--strong);line-height:1.3}
.lead{font-size:13px;color:var(--mute);margin:6px 0 18px}
h2{font-size:17px;font-weight:800;color:var(--strong);margin:26px 0 10px}
.card{background:var(--card);border-radius:22px;padding:16px;box-shadow:var(--shadow),inset 0 0 0 1px var(--ring)}
.card + .card{margin-top:12px}
.num{font-weight:800;font-variant-numeric:tabular-nums;color:var(--strong);letter-spacing:-.01em}
.u{font-size:13px;color:var(--mute);font-weight:700;margin-left:2px}
.tag{display:inline-flex;align-items:center;height:26px;padding:0 11px;border-radius:999px;font-size:13px;font-weight:800;white-space:nowrap}
.keep{background:var(--keep);color:var(--keep-ink)} .take{background:var(--take);color:var(--take-ink)} .no{background:var(--no);color:var(--no-ink)}
.sw{display:inline-block;width:16px;height:16px;border-radius:5px;vertical-align:-3px;margin-right:6px;box-shadow:inset 0 0 0 1px rgba(17,24,39,.12)}
.box{background:var(--box);border-radius:12px;padding:12px}
.small{font-size:13px;color:var(--mute)}
.lab{font-size:13px;color:var(--mute);font-weight:700}
'''

def page(name, title, lead, body, extra_css=''):
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s%s</style><script>if(/night=1/.test(location.search))document.documentElement.setAttribute("data-night","on")</script></head><body>'
            '<div class="top"><a class="back" href="index.html" aria-label="一覧へ戻る">‹ 一覧</a></div><h1>%s</h1><p class="lead">%s</p>%s</body></html>') % (title, BASE, extra_css, title, lead, body)
    open(D + '/' + name, 'w', encoding='utf-8').write(html)

S = json.load(open(HERE + '/survey.json', encoding='utf-8'))
def agg(key, mode='day'):
    c = {}
    for v in S[mode].values():
        for k, n in v[key].items(): c[k] = c.get(k, 0) + n
    return c
num = {'tab': 0, 'prop': 0}
for v in S['day'].values():
    for k in num: num[k] += v['num'][k]
fs = agg('fs')

# ---------- T1 基準表 ----------
W = '#FFFFFF'
ROWS = [
 ('面と枠', [
  ('画面の地', '<span class="sw" style="background:#EEF1F5"></span>#EEF1F5（白との差 %s）' % crs(W, '#EEF1F5'), '#F2F4F7（差 %s）' % crs(W, '#F2F4F7'),
   'keep', '今の方が白いカードとの差が少し大きい。変えない'),
  ('カードの輪郭', '影＋内側の 1px（#E3E6EB か 7% の黒。2種類が混ざる）', '影＋1px の枠 #DCE1E8',
   'take', '枠はもうある。<b>#DCE1E8 の1色にそろえる</b>（白との差 %s〜%s → %s。7%% の黒は白の上で #EDEEF0 相当）。差は小さいが、薄い方の枠が日なたで消えるのを防ぐ' % (crs(W, '#EDEEF0'), crs(W, '#E3E6EB'), crs(W, '#DCE1E8'))),
  ('カードの中の小箱', '線で囲む所・地の色 #F6F7F9・#EEF0F3 など', '面 #E8ECF2・角丸 12',
   'take', '線をやめて<b>面 #F1F3F6・角丸 12</b>。小箱の上の灰の字は #5F6672（%s）' % crs('#F1F3F6', '#5F6672')),
 ]),
 ('字の色', [
  ('本文・数字', '#1F2937（いちばん多い）', '#111827',
   'no', '決まりは「真っ黒でなく濃いグレー」。#1F2937 のまま（白の上で %s）' % crs(W, '#1F2937')),
  ('補足の灰', '#6B7280・#5B6270・#7A8390・#9CA3AF の4つ以上', '#4B5563（7:1 前後）',
   'take', '<b>#4B5563／#6B7280 の2つ＋小箱の上 #5F6672</b>。#7A8390（%s）・#9CA3AF（%s）は字に使わない（図鑑の空港コード・運用の「—」など）' % (crs('#F6F7F9', '#7A8390'), crs(W, '#9CA3AF'))),
 ]),
 ('アクセント', [
  ('主ボタン・選んだタブ', '濃いグレーの塗り・金のチェックイン', '航空ネイビー #1C4FA0（ANA の青に近い）',
   'no', 'JAL赤・ANA青は控えめなアクセントの決まり。片方の会社に寄るので入れない'),
  ('遅れ', '#B42318（白の上で %s）＋字' % crs(W, '#B42318'), '#C8102E（JAL の赤に近い）',
   'no', '今の赤のまま。遅れは字と ▲ でも分かるようにする（gemini-1126 の C2）'),
  ('金', '#A9822E（字は #856620）・チェックインの金', '#E9C46A を節目のバッジに', 'no', 'バッジは増やさない。今の金は今の場所だけ'),
 ]),
 ('字の大きさ', [
  ('段の数', '見えている字で %d 種類（13・26・12・17・22・15・14・18・10.5・12.5…）' % len([k for k in fs if k != '0px']), '6段（40／26／20／15／14／12）',
   'take', '<b>7段にそろえる：34・26・22・17・15・13・12</b>（12 は「/86」「km」など単位だけ）'),
  ('いちばん小さい字', '下のタブの名前 10.5px（どの画面にも出る）', '11〜12px のラベル',
   'no', '11〜12px のラベルは入れない（ラベルは 13px 以上、12px は単位だけ）。<b>タブの名前を 12px に</b>上げる案'),
  ('数字の等幅', 'CSS に 57 か所あるが、見えている数字の %d%%（%d／%d）だけ' % (round(num['tab'] * 100 / (num['tab'] + num['prop'])), num['tab'], num['tab'] + num['prop']), 'すべての数字を等幅',
   'take', '<b>アプリ全体の地に1行で等幅</b>。ただし今の日本語のゴシック体は数字がもとからほぼ等幅で、見た目の差は小さい（T3）。急がない'),
 ]),
 ('角丸・影・余白', [
  ('角丸', 'カードで 28・24・22・20・18・16 が混ざる', '16（カード）・24（シート）',
   'take', '数は取り入れ、値は今に寄せる：<b>小箱 12・カード 22・シート 28・ピル 999</b>。16 は今より角張るので使わない'),
  ('影', '0 1px 2px 4% ＋ 0 10px 30px 10%', '0 2px 8px 5%', 'keep', '今のまま（輪郭は上の枠が受け持つ）'),
  ('左右の余白', '20px（ホームのシートは 16）', '16px', 'keep', '大胆な余白の決まりで 20 のまま'),
  ('中と間', 'カードの間 8〜12、中はばらばら', 'ラベルと数字 4・まとまり 16〜20・カードの間 12',
   'take', '<b>中 ＜ 間</b>を決まりに：ラベルと数字 4・まとまり 16・カードの間 12'),
 ]),
 ('そのほか', [
  ('便の航空会社コード', '字だけ（ホームの案B は「JL」「NH」の字の札）', '会社ごとに淡い色の札',
   'take', '見分けるための札として。<b>色は彩度をさらに落とし、どの会社も同じ明るさ</b>（T5）'),
  ('見回りの項目', 'なし', '明るさ中・窓際で 0.5 秒で読めるか', 'take', '改善担当の見回りに足す（T6）'),
 ]),
]
NAME = {'keep': 'そのまま', 'take': '取り入れる', 'no': '入れない'}
cnt = {'keep': 0, 'take': 0, 'no': 0}
b = []
for grp, rows in ROWS:
    b.append('<h2>%s</h2>' % grp)
    for t, now, gem, v, why in rows:
        cnt[v] += 1
        b.append('<div class="card row"><div class="rh"><b>%s</b><span class="tag %s">%s</span></div>'
                 '<dl><dt>今</dt><dd>%s</dd><dt>Gemini</dt><dd>%s</dd><dt>案</dt><dd class="an">%s</dd></dl></div>' % (t, v, NAME[v], now, gem, why))
sumcard = ('<div class="card sum"><div><span class="num big">%d</span><span class="u">項目</span></div><div class="pills">'
           '<span class="tag keep">そのまま %d</span><span class="tag take">取り入れる %d</span><span class="tag no">入れない %d</span></div>'
           '<p class="small">「今」はデモで5つのタブを開いて見えている要素を測った値（make/survey.json）と src/index.html の CSS。11/26 の main。</p></div>') % (
    sum(cnt.values()), cnt['keep'], cnt['take'], cnt['no'])
page('t1-table.html', 'T1 見た目の基準表',
     '今のアプリと Gemini の基準を並べ、そのまま・取り入れる・入れないを付けた案。アプリはまだ変えない',
     sumcard + ''.join(b),
     '.row .rh{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:16px;color:var(--strong)}'
     '.row dl{display:grid;grid-template-columns:62px 1fr;gap:6px 8px;margin-top:10px;font-size:14px}'
     '.row dt{font-size:13px;font-weight:700;color:var(--mute);padding-top:1px}.row dd{color:var(--ink)}.row dd.an{color:var(--strong)}'
     '.sum{display:flex;flex-direction:column;gap:10px}.big{font-size:34px}.pills{display:flex;gap:6px;flex-wrap:wrap}')

# ---------- T2 カードの輪郭（日なた） ----------
def demo_card(ring, boxed):
    inner = ('<div class="box"><span class="lab">小目標</span><div class="v">関東 <span class="num">5</span><span class="u">/ 6</span>・あと1空港</div></div>' if boxed else
             '<div class="lined"><span class="lab">小目標</span><div class="v">関東 <span class="num">5</span><span class="u">/ 6</span>・あと1空港</div></div>')
    return ('<div class="card dc" style="box-shadow:var(--shadow),inset 0 0 0 1px %s"><div class="lab">集めた空港</div>'
            '<div><span class="num" style="font-size:34px">16</span><span class="u">/ 86</span></div>%s'
            '<div class="dl"><span>平均の遅れ（推定）</span><b class="late">▲ 12<span class="u" style="color:inherit">分</span></b></div></div>') % (ring, inner)
glare = '.sun{filter:contrast(.55) brightness(1.18) saturate(.7)}'
t2 = ('<h2>屋内（ふつうの見え方）</h2><div class="pair"><div><p class="cap">今</p>%s</div><div><p class="cap">案</p>%s</div></div>'
      '<h2>日なた（画面に光が当たったときの見え方の目安）</h2><p class="small">コントラストを 55%%・明るさを 118%% にして近づけた。今は影とカードの縁が地に溶け、案は 1px の枠と小箱の面が残る</p>'
      '<div class="pair sun"><div><p class="cap">今</p>%s</div><div><p class="cap">案</p>%s</div></div>'
      '<div class="card" style="margin-top:16px"><b style="color:var(--strong)">変えるのは2つだけ</b><ul class="li"><li>カードの内側の 1px を <b>#DCE1E8</b> の1色に（今は #E3E6EB と 7%% の黒が混ざる）。夜は今の白 10%%</li>'
      '<li>カードの中の小箱は線で囲まず <b>面 #F1F3F6・角丸 12</b>。上の灰の字は #5F6672（%s:1）</li></ul></div>') % (
    demo_card('var(--ring-now)', False), demo_card('var(--ring)', True), demo_card('var(--ring-now)', False), demo_card('var(--ring)', True), crs('#F1F3F6', '#5F6672'))
page('t2-surface.html', 'T2 カードの輪郭と小箱', '影は今のまま。日なたで影が消えても輪郭が残るよう、極薄の枠を1色にそろえ、小箱は面で分ける', t2,
     '.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.cap{font-size:13px;font-weight:800;color:var(--mute);margin:0 0 6px 4px}'
     '.dc{padding:14px 12px;border-radius:22px}.dc .v{font-size:13px;color:var(--strong);font-weight:700;margin-top:2px}'
     '.lined{border:1px solid #D6D6D6;border-radius:12px;padding:10px 10px;margin-top:10px}.dc .box{margin-top:10px;padding:10px}.dc .box .lab{color:var(--mute-on-box)}'
     ':root[data-night=on] .lined{border-color:#3A414C}'
     '.dl{display:flex;flex-direction:column;margin-top:12px;font-size:13px;color:var(--mute);font-weight:700}.late{color:var(--late);font-size:22px;font-variant-numeric:tabular-nums}'
     '.li{margin:8px 0 0 18px;font-size:14px;display:grid;gap:6px}' + glare)

# ---------- T3 字の段と等幅 ----------
steps = [('34', '大きな数字', '16', '集めた空港・空の上の時間'), ('26', '数字', '1,248', 'km・回数・時刻の大きい所'),
         ('22', '小さめの数字', '14:35', '今日の便の時刻・遅れ'), ('17', '見出し', '羽田空港', 'カードの見出し・空港名'),
         ('15', '本文', '新千歳へ JL503', '行先・便名・案内の文'), ('13', 'ラベル', '平均の遅れ（推定）', '数字の上の項目名・補足'),
         ('12', '単位だけ', '/ 86　km　分', '数字のすぐ後ろの単位')]
now_sizes = sorted(((float(k[:-2]), n) for k, n in fs.items() if k != '0px'), key=lambda x: -x[1])
rows3 = ''.join('<div class="st"><div class="px"><span class="num">%s</span><span class="u">px</span></div><div class="sm"><div style="font-size:%spx;font-weight:%s;color:var(--strong);line-height:1.2%s">%s</div><div class="small">%s・%s</div></div></div>' % (
    s, s, 800 if int(s) >= 22 or s == '17' else (700 if s in ('13', '12') else 500), ';font-variant-numeric:tabular-nums' if int(s) >= 22 else '', ex, nm, use) for s, nm, ex, use in steps)
chips = ''.join('<span class="chip%s">%s<small>×%d</small></span>' % (' bad' if v < 12 else '', ('%g' % v), n) for v, n in now_sizes)
times = [('07:10', '11', '1'), ('08:45', '18', '7'), ('11:05', '1', '11'), ('14:35', '19', '4')]
def tl(tab):
    return ''.join('<div class="tr"><span class="tt" style="font-variant-numeric:%s">%s</span><span class="fl">JL%s5%s</span></div>' % ('tabular-nums' if tab else 'proportional-nums', t, a, c) for t, a, c in times)
tabs_now = ''.join('<span style="font-size:10.5px">%s</span>' % x for x in ('ホーム', '図鑑', 'フライト', '運用', '修行'))
tabs_new = ''.join('<span style="font-size:12px">%s</span>' % x for x in ('ホーム', '図鑑', 'フライト', '運用', '修行'))
t3 = ('<h2>今、画面に出ている字の大きさ（%d 種類）</h2><div class="card"><div class="chips">%s</div><p class="small" style="margin-top:8px">赤い枠は 12px 未満。10.5px は下のタブの名前（どの画面にも出る）</p></div>'
      '<h2>案：7段</h2><div class="card">%s</div>'
      '<h2>下のタブの名前</h2><div class="card"><p class="cap">今 10.5px</p><div class="tb">%s</div><p class="cap" style="margin-top:12px">案 12px（タブの高さは変えない）</p><div class="tb">%s</div></div>'
      '<h2>数字の等幅</h2><div class="card"><div class="mt"><span></span><b>「1111」</b><b>「0000」</b></div>'
      '<div class="mt"><span>日本語のゴシック体（今の本文）</span><span class="num">97</span><span class="num">97</span></div>'
      '<div class="mt"><span>欧文の書体（Noto Sans）</span><span class="num">73</span><span class="num">80</span></div><p class="small" style="margin-top:8px">40px の太字で4けたの幅を測った（px）。日本語のゴシック体は数字がもとから同じ幅なので、今の画面では桁のずれはほとんど出ない</p></div>'
      '<p class="small" style="margin-top:8px">今は見えている数字の %d%% だけに等幅の指定がある。欧文の書体に切り替わる所（3レターコードの細長い書体など）のために、地に font-variant-numeric: tabular-nums を1行足す案。急がない</p>') % (
    len(now_sizes), chips, rows3, tabs_now, tabs_new, round(num['tab'] * 100 / (num['tab'] + num['prop'])))
page('t3-type.html', 'T3 字の大きさの段と等幅の数字', '数字は大きく太く、単位は小さく薄く。段を7つにそろえ、12px は単位だけに使う', t3,
     '.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{display:inline-flex;align-items:baseline;gap:3px;height:30px;padding:0 10px;border-radius:999px;background:var(--box);font-size:14px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums;align-items:center}'
     '.chip small{font-size:12px;color:var(--mute);font-weight:700}.chip.bad{box-shadow:inset 0 0 0 1.5px var(--late);color:var(--late)}'
     '.st{display:grid;grid-template-columns:58px 1fr;gap:10px;align-items:center;padding:8px 0}.st + .st{margin-top:4px}.px .num{font-size:17px}'
     '.cap{font-size:13px;font-weight:800;color:var(--mute);margin-bottom:6px}.tb{display:flex;justify-content:space-around;background:var(--box);border-radius:999px;height:52px;align-items:center;color:var(--strong);font-weight:700}'
     '.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pair .card + .card{margin-top:0}.pair .card{padding:14px 12px}.tr{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0}'
     '.mt{display:grid;grid-template-columns:1fr 64px 64px;gap:8px;align-items:center;min-height:36px;font-size:14px}.mt b{font-size:13px;color:var(--mute);text-align:right}.mt .num{font-size:22px;text-align:right}')

# ---------- T4 余白（中 < 間） ----------
def sp_card(gap_in, gap_blk, lbl):
    return ('<div class="card sc" style="padding:16px"><div class="blk"><div class="lab">訪問</div><div style="margin-top:%dpx"><span class="num" style="font-size:26px">14</span><span class="u">回目</span></div></div>'
            '<div class="blk" style="margin-top:%dpx"><div class="lab">前回から</div><div style="margin-top:%dpx"><span class="num" style="font-size:26px">23</span><span class="u">日ぶり</span></div></div>%s</div>') % (gap_in, gap_blk, gap_in, lbl)
t4 = ('<div class="cols"><div><p class="cap">今（中と間がほぼ同じ）</p><div class="stack" style="gap:8px">%s%s</div></div>'
      '<div><p class="cap">案（中 ＜ 間）</p><div class="stack" style="gap:12px">%s%s</div></div></div>'
      '<div class="card" style="margin-top:20px"><b style="color:var(--strong)">決める数</b><div class="rule">'
      '<div><span class="num">4</span><span class="u">px</span><p>ラベルと数字</p></div><div><span class="num">16</span><span class="u">px</span><p>カードの中のまとまりの間</p></div>'
      '<div><span class="num">12</span><span class="u">px</span><p>カードとカードの間</p></div><div><span class="num">20</span><span class="u">px</span><p>画面の左右（今のまま。ホームのシートは 16）</p></div></div>'
      '<p class="small" style="margin-top:10px">線を引きたくなったら、まず「余白を足す」か「カードを分ける」で解けないかを見る。Gemini の左右 16px は入れない（大胆な余白の決まり）</p></div>') % (
    sp_card(10, 10, ''), sp_card(10, 10, ''), sp_card(4, 16, ''), sp_card(4, 16, ''))
page('t4-space.html', 'T4 余白の決め方', 'カードの中の余白をカードとカードの間より小さくすると、線を引かなくてもまとまりが見える', t4,
     '.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}.cap{font-size:13px;font-weight:800;color:var(--mute);margin:0 0 6px 4px}.stack{display:flex;flex-direction:column}.stack .card + .card{margin-top:0}'
     '.rule{display:grid;grid-template-columns:1fr 1fr;gap:14px 12px;margin-top:10px}.rule .num{font-size:26px}.rule p{font-size:13px;color:var(--mute);font-weight:700;line-height:1.4}')

# ---------- T5 航空会社コードの札 ----------
FL = [('07:10', 'JL', '503', '新千歳', 0), ('07:25', 'NH', '61', '新千歳', 0), ('07:40', 'BC', '701', '神戸', 12), ('08:05', '7G', '31', '北九州', 0), ('08:30', 'JL', '901', '那覇', 0), ('08:45', 'NH', '993', '那覇', 38)]
GEM = {'JL': ('#FDECEC', '#A61B2B'), 'NH': ('#EBF2FC', '#16428B'), 'BC': ('#EEF1F5', '#334155'), '7G': ('#EEF1F5', '#334155')}
SOFT = {'JL': ('#F3EBEC', '#7A3B43'), 'NH': ('#EAEEF4', '#33476B'), 'BC': ('#EEF0F2', '#4B5563'), '7G': ('#EEF0F2', '#4B5563')}
SOFT_N = {'JL': ('#3A2A2D', '#E8C9CD'), 'NH': ('#26303F', '#C7D3E6'), 'BC': ('#2B3038', '#D1D5DB'), '7G': ('#2B3038', '#D1D5DB')}
def fl_list(mode):
    out = []
    for t, c, n, to, late in FL:
        st = 'data-m="%s" data-c="%s"' % (mode, c)
        out.append('<div class="fr"><span class="tt">%s</span><span class="cc" %s>%s</span><span class="fn"><b>%s</b></span><span class="to">%s</span>%s</div>' % (
            t, st, c, n, to, '<span class="lt">▲ %d分</span>' % late if late else ''))
    return ''.join(out)
soft_css = ''.join(':root .cc[data-c="%s"]{background:%s;color:%s}:root[data-night=on] .cc[data-c="%s"]{background:%s;color:%s}' % (c, SOFT[c][0], SOFT[c][1], c, SOFT_N[c][0], SOFT_N[c][1]) for c in SOFT)
crt = '・'.join('%s %s' % (c, crs(SOFT[c][0], SOFT[c][1])) for c in ('JL', 'NH', 'BC'))
crg = '・'.join('%s %s' % (c, crs(GEM[c][0], GEM[c][1])) for c in ('JL', 'NH', 'BC'))
t5 = ('<p class="small">ロゴの代わりではなく、一覧で見分けるための札。事実の記録として会社のコードだけを書く</p>'
      '<h2>案2（おすすめ）彩度をさらに落とし、どの会社も同じ明るさ</h2><div class="card fl">%s</div><p class="small" style="margin-top:6px">字と地の比：%s</p>'
      '<h2>案1 灰一色（会社で色を分けない）</h2><div class="card fl">%s</div>'
      '<h2>Gemini の色（比べる用・入れない）</h2><div class="card fl">%s</div><p class="small" style="margin-top:6px">字と地の比：%s。赤と青がはっきりして、JAL・ANA の色に寄る</p>') % (
    fl_list('soft'), crt, fl_list('gray'), fl_list('gem'), crg)
page('t5-carrier.html', 'T5 便の一覧の航空会社コード', '「JL」「NH」の字の札（ホームの案B と同じ）に、見分けるための淡い色を付けるか', t5,
     '.fl{padding:8px 14px}.fr{display:grid;grid-template-columns:52px 40px 1fr auto;align-items:center;gap:10px;min-height:46px}'
     '.tt{font-size:17px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}.cc{display:inline-flex;justify-content:center;align-items:center;width:40px;height:24px;border-radius:999px;font-size:13px;font-weight:800;letter-spacing:.02em}'
     '.fn{font-size:13px;color:var(--mute);font-weight:700;font-variant-numeric:tabular-nums}.fn b{color:var(--strong);font-size:15px;margin-left:1px}.to{grid-column:3;grid-row:1;justify-self:end;margin-right:0;font-size:15px;color:var(--strong);font-weight:700}'
     '.fr .to{grid-column:4}.fr .fn{grid-column:3}.lt{grid-column:3 / 5;justify-self:end;font-size:13px;font-weight:800;color:var(--late);margin-top:-8px;padding-bottom:6px}'
     '' + soft_css + ''.join('.cc[data-m="gem"][data-c="%s"]{background:%s!important;color:%s!important}' % (c, GEM[c][0], GEM[c][1]) for c in GEM) + '.cc[data-m="gray"]{background:#EEF0F2!important;color:#4B5563!important}:root[data-night=on] .cc[data-m="gray"]{background:#2B3038!important;color:#D1D5DB!important}')

# ---------- T6 見回りの項目 ----------
CHK = [('白い地の上に白いカードを直に置いていない', '画面の地は #EEF1F5。カードの輪郭は #DCE1E8 の 1px'),
       ('数字が単位やラベルより目立っている', '数字はラベルの2倍くらい・太字。単位は 12〜13px で薄い灰'),
       ('線を引く前に、余白かカードを分けるかで解けないか見た', '中 4／16・間 12・左右 20'),
       ('灰の字は #4B5563／#6B7280（小箱の上は #5F6672）だけ', '#9CA3AF・#7A8390・#BDBDBD は字に使わない'),
       ('12px 未満の字がない', '12px は単位だけ。タブの名前も 12px 以上'),
       ('明るさ中・窓際で、ボタンの場所と遅れの数字が 0.5 秒で読める', '端末の明るさを中にして窓の近くで見る。遅れは字と ▲ でも分かる'),
       ('色だけで分けていない', '遅れは ▲、欠航は白抜き、印は形と字（gemini-1126 の C2）')]
t6 = '<div class="card">' + ''.join('<div class="ck"><span class="bx" aria-hidden="true"></span><div><b>%s</b><p class="small">%s</p></div></div>' % (a, c) for a, c in CHK) + '</div>' \
     '<p class="small" style="margin-top:12px">改善担当が画面案とアプリを見回るときの項目に足す案。上から5つは測れる（make/shoot.py と同じ測り方）、6つ目は人の目で見る</p>'
page('t6-check.html', 'T6 見回りの項目', '新しい画面を作るときと改善担当が見るときに、この7つを確かめる', t6,
     '.ck{display:grid;grid-template-columns:24px 1fr;gap:12px;padding:10px 0}.ck + .ck{margin-top:4px}.ck b{color:var(--strong);font-size:15px;line-height:1.45}'
     '.bx{width:22px;height:22px;border-radius:7px;box-shadow:inset 0 0 0 2px var(--mute);margin-top:2px}')

json.dump([['t1-table.html', 'T1 見た目の基準表', 'doc'], ['t2-surface.html', 'T2 カードの輪郭と小箱', 'doc'], ['t3-type.html', 'T3 字の段と等幅', 'doc'],
           ['t4-space.html', 'T4 余白の決め方', 'doc'], ['t5-carrier.html', 'T5 航空会社コードの札', 'doc'], ['t6-check.html', 'T6 見回りの項目', 'doc']],
          open(HERE + '/screens.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('書いた', cnt)
