# -*- coding: utf-8 -*-
# 小さな動きの見本を組み立てる：src/base.css・base.js を各ページに埋め込み、外部の読み込みなしで開ける HTML にする
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + '/src')
from icons import ic, tabs
OUT = os.path.dirname(HERE)
CSS = open(HERE + '/src/base.css', encoding='utf-8').read()
JS = open(HERE + '/src/base.js', encoding='utf-8').read()

def page(name, title, body, css='', js=''):
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><style>%s\n%s</style></head><body>%s<script>%s\n%s</script></body></html>') % (title, CSS, css, body, JS, js)
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(html)
    print('書いた', name)

def spec(move, t, why):
    return ('<dl class="spec"><div><dt>動き</dt><dd>%s</dd></div><div><dt>長さ</dt><dd>%s</dd></div>'
            '<div><dt>何のため</dt><dd>%s</dd></div></dl>') % (move, t, why)

def mc(no, name, where, stage, move, t, why, extra=''):
    return ('<section class="mc card" id="m%s"><div class="mh"><span class="no">%s</span><h2>%s</h2></div>'
            '<p class="where">%s</p><div class="stage" data-toast-host>%s</div>%s%s</section>') % (no, no, name, where, stage, spec(move, t, why), extra)

def again(fn, label='もう一度'):
    return '<button type="button" class="again tap" onclick="%s">%s%s</button>' % (fn, ic('retry'), label)

# ───────────── 一覧ページ ─────────────
IDX_CSS = r'''
.top{padding:28px 0 8px}
.top .lead{margin-top:6px}
.ctl{position:sticky;top:0;z-index:5;display:flex;gap:8px;align-items:center;justify-content:space-between;padding:10px 0;background:var(--bg)}
.seg{display:inline-flex;padding:4px;border-radius:999px;background:var(--pill)}
.seg button{min-height:44px;min-width:56px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.seg button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.ctl .sw .lb{min-width:auto;font-size:12px}
.ctl .sw .tx{font-size:12px;font-weight:700;color:var(--sub)}
.mc{margin-top:16px;padding:18px 16px 16px}
.mh{display:flex;align-items:baseline;gap:10px}
.mh .no{font-size:13px;font-weight:800;color:var(--mute);font-variant-numeric:tabular-nums}
.where{margin-top:4px;font-size:13px;color:var(--sub)}
.stage{position:relative;overflow:hidden;margin-top:12px;min-height:148px;padding:20px 14px;border-radius:16px;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}
.stage .toast{bottom:12px}
.stage.tst{padding-bottom:76px}
.spec{margin-top:12px;display:grid;gap:4px}
.spec div{display:grid;grid-template-columns:4.6em 1fr;gap:8px;font-size:13px}
.spec dt{color:var(--mute);font-weight:700}
.spec dd{color:var(--ink)}
.again{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;font-size:13px;font-weight:700;color:var(--sub);background:var(--card);box-shadow:var(--shadow)}
.again svg{width:16px;height:16px}
.sec{margin-top:36px}
.sec h2{font-size:17px}
.sec ul{margin-top:10px;padding:14px 16px 14px 32px;background:var(--card);border-radius:20px;box-shadow:var(--shadow);font-size:14px}
.sec li{margin:4px 0}
.sec li small{display:block;font-size:12px;color:var(--mute)}
.mini-tabs{width:100%}
.bandrow{display:flex;gap:16px;align-items:baseline;justify-content:center;width:100%;padding:12px 16px;background:var(--card);border-radius:18px;box-shadow:var(--shadow)}
.bandrow .k{font-size:12px;font-weight:700;color:var(--sub);margin-right:4px}
.bandrow .num{font-size:22px}
.sk-card{width:100%;display:grid;gap:8px;padding:14px;background:var(--card);border-radius:18px;box-shadow:var(--shadow)}
.sk-card .r{display:flex;align-items:center;gap:10px}
.realrow{display:flex;align-items:center;gap:10px;font-size:14px}
.realrow .cd{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:26px;border-radius:8px;background:var(--hero);color:#fff;font-size:12px;font-weight:800}
:root[data-night=on] .realrow .cd{background:#262B33;color:#E5E7EB}
.realrow b{color:var(--strong)}
.realrow .t{margin-left:auto;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.sgmini{width:100%;padding:14px 16px;background:var(--card);border-radius:18px;box-shadow:var(--shadow)}
.sgmini .big{font-size:34px;line-height:1.1}
.sgmini .k{font-size:12px;font-weight:700;color:var(--sub)}
.stage .sortlist{width:100%}
.regrow{display:flex;align-items:center;gap:10px;padding:8px 8px 8px 16px;background:var(--card);border-radius:999px;box-shadow:var(--shadow)}
.regrow b{font-size:18px;font-weight:800;color:var(--strong);letter-spacing:.04em}
.regrow small{font-size:12px;color:var(--mute)}
.belbtn{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.belbtn svg{width:20px;height:20px}
.belbtn[aria-pressed=true]{background:var(--pin-wash);box-shadow:inset 0 0 0 1.5px var(--pin)}
.offcard{width:100%;padding:14px 16px;background:var(--card);border-radius:18px;box-shadow:var(--shadow);display:flex;align-items:center;gap:12px}
.offcard .tx{flex:1;min-width:0}
.offcard b{display:block;font-size:14px;color:var(--strong)}
.offcard [data-st]{font-size:12px;color:var(--mute)}
.offcard[data-ok="1"] [data-st]{color:var(--ok);font-weight:700}
.retry{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--strong)}
.retry svg{width:18px;height:18px}
.stage.sheetwrap{min-height:220px;justify-content:flex-start}
.stage .sheet{padding-bottom:18px}
.sheet h3{font-size:15px;font-weight:800;color:var(--strong)}
.sheet p{font-size:13px;color:var(--sub);margin-top:4px}
.sheet .pill{margin-top:12px}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
'''

def index():
    cards = []
    cards.append(mc('01', '押すと少し縮む', 'ピル型のボタンとカードのすべて（いちばん土台の動き）',
        '<div class="btnrow"><button class="pill tap" type="button">ピン止め</button><button class="pill dark tap" type="button">画像で共有</button></div>'
        '<p class="lead">押さえたままにすると縮んだまま</p>',
        '押している間だけ 0.97 倍、離すと戻る。色は変えない', '0.12 秒',
        '押せたと指で分かる。波紋は使わない（ほかの OS の見た目に寄るため）'))
    cards.append(mc('02', 'タブの点がすべる', '下のタブ帯（今の青い点）',
        '<div class="mini-tabs">%s</div>' % tabs('home'),
        '押したタブの下へ点がすべる。絵は押した瞬間だけ 0.88 倍', '点 0.25 秒・絵 0.15 秒',
        'どこへ来たかが目で追える'))
    cards.append(mc('03', 'ON／OFF のつまみ', '表示の編集・各画面の見方のシート（今の ON／OFF のスイッチ）',
        '<button type="button" class="sw" role="switch" aria-checked="false" aria-label="運用"><span class="lb">OFF</span><span class="tr"><i class="kn"></i></span></button>'
        '<button type="button" class="sw" role="switch" aria-checked="true" aria-label="修行"><span class="lb">ON</span><span class="tr"><i class="kn"></i></span></button>',
        'つまみがすべり、地の色が変わる。押さえている間はつまみが少し横に伸びる', '0.25 秒',
        '切り替わったことが字（ON／OFF）と動きの2つで分かる'))
    cards.append(mc('04', 'ピンが刺さる', '近くの空港のカード・空港ページの「ピン止め」',
        '<button type="button" class="pinbtn tap" aria-pressed="false">%s<span>ピン止め</span></button>' % ic('pin'),
        'ピン止めにすると、ピンが上から少し傾いて刺さり、ボタンが塗られる。外すときは動きなし', '0.4 秒',
        'ピン止めできたことが一目で分かる。外すほうは静かに'))
    cards.append(mc('05', '下から出る札', '保存しました・ピン止めしました・コピーしました・並びを保存しました',
        '<button class="pill tap" type="button" onclick="SM.toast(this,\'保存しました\')">保存する</button>',
        '下から 16px せり上がって出て、2 秒で下がって消える。タブ帯の上に出す', '出る 0.25 秒・消える 0.15 秒',
        '今の画面の上の字（#msg）より目に入りやすく、操作の場所を離れない'))
    cards.append(mc('06', '骨組みの読み込み', '運用のカード（案内板・滑走路・特別塗装機）・フライトの一覧',
        '<div class="sk-card" id="sk06"><div data-skel hidden>'
        '<div class="r"><span class="skel" style="width:44px;height:26px"></span><span class="skel" style="flex:1;height:14px"></span><span class="skel" style="width:48px;height:14px"></span></div>'
        '<div class="r" style="margin-top:10px"><span class="skel" style="width:44px;height:26px"></span><span class="skel" style="flex:1;height:14px"></span><span class="skel" style="width:48px;height:14px"></span></div></div>'
        '<div data-real><div class="realrow"><span class="cd">JL</span><b>JL 501 新千歳</b><span class="t">14:30</span></div>'
        '<div class="realrow" style="margin-top:10px"><span class="cd">NH</span><b>NH 993 伊丹</b><span class="t">14:35</span></div></div></div>'
        + again("SM.loadInto(document.getElementById('sk06'),1500)", '読み込む'),
        '中身の形をした灰色の上を、薄い光がゆっくり流れる。0.3 秒より早く読めたら骨組みは出さない。読めたら中身が 0.25 秒でふわっと出る', '光 1.4 秒のくり返し',
        '待ち時間が短く感じる。読み込みの丸より、何が出るかが先に分かる'))
    cards.append(mc('07', '数字の繰り上がり', 'ホームの下の帯（今日の印・空港 ○／86・フライト）',
        '<div class="bandrow"><span><span class="k">今日の印</span><b class="num"><span class="roll" id="r07a" data-v="0"></span></b></span>'
        '<span><span class="k">空港</span><b class="num"><span class="roll" id="r07b" data-v="16"></span></b><span class="u">/86</span> <span class="plus" id="p07">＋1</span></span></div>'
        + again("SM.rollSet(r07a,0);SM.rollSet(r07b,16);setTimeout(()=>{SM.rollTo(r07a,1);SM.rollTo(r07b,17);p07.classList.remove('show');void p07.offsetWidth;p07.classList.add('show')},80)", '印をもらったあと'),
        '印をもらって戻ったとき、増えた数字だけが下から上へ入れ替わる。横に小さく「＋1」', '0.35 秒（＋1 は 1.2 秒で消える）',
        '何が増えたかが分かる。パタパタ（案内板風）にはしない：パタパタは近い空港のコードだけ'))
    cards.append(mc('08', '道のりの帯が伸びる', '修行タブの「道のりの1枚」（大きな数字と帯）',
        '<div class="sgmini"><span class="k">今のポイント</span><div><b class="num big" id="n08">0</b><span class="u">FOP</span></div>'
        '<div class="bar" id="b08" style="margin-top:8px"><i></i></div></div>'
        + again("SM.countUp(n08,41744);SM.grow(b08,84)"),
        '画面を開いたときに一度だけ、帯が 0 から今の所まで伸び、数字も数え上がる。2回目からは動かさない', '0.4 秒',
        '「どこまで来たか」が体で分かる。毎回動くとうるさいので最初だけ'))
    cards.append(mc('09', '並べ替えで持ち上がる', '運用タブのカード・ホームのカード・空港のカードの並べ替え（右端の ≡）',
        '<div class="sortlist" id="s09">'
        + ''.join('<div class="srow"><b>%s</b><span class="grip" aria-label="%sを動かす">%s</span></div>' % (n, n, ic('grip')) for n in ('滑走路', '地図', '案内板', '3D'))
        + '</div><p class="lead">≡ を押さえて上下に動かす</p>',
        'つかんだカードが 1.02 倍に浮いて影が濃くなる。ほかのカードはすっと場所をあける。離すと「並びを保存しました」', '浮く 0.15 秒・あける 0.25 秒',
        'つかめたこと・どこに入るかが分かる'))
    cards.append(mc('10', 'コピーが ✓ に', '登録記号・便名・共有の文のコピー',
        '<div class="regrow"><b>JA8089</b><small>B767-300</small><button type="button" class="copy tap" data-copy="JA8089" aria-label="コピー">%s%s</button></div>' % (ic('copy', 'ic cp'), ic('check', 'ic ck')),
        'コピーの絵が ✓ に入れ替わり、1.5 秒で戻る。札「コピーしました」も出す', '0.15 秒',
        'コピーできたかを押した場所で確かめられる'))
    cards.append(mc('11', '鈴が揺れる', 'ピン止めした空港の知らせを ON にしたとき（空港ページ・マイページの知らせ）',
        '<button type="button" class="belbtn bell tap" aria-pressed="false">%s<span>知らせ OFF</span></button>' % ic('bell'),
        'ON にしたときだけ、鈴が左右に小さく2回揺れる。OFF は動きなし', '0.4 秒',
        '知らせが届くようになったと分かる。届いた知らせそのものでは揺らさない'))
    cards.append(mc('12', '「もう一度」の矢印が回る', '電波がないカード・読めなかったカード（運用・空港の今）',
        '<div class="offcard" data-retry-box><span style="color:var(--mute)">%s</span><div class="tx"><b>運航情報を読めませんでした</b><span data-st>最後に読んだ 14時05分</span></div>'
        '<button type="button" class="retry tap">%s<span>もう一度</span></button></div>' % (ic('wifi'), ic('retry')),
        '押すと矢印が1回だけ回り、読めたら下の字が「読めました」に変わる。回り続けない', '0.6 秒（1回）',
        '押したことが伝わる。回り続ける丸で待たせない'))
    cards.append(mc('13', 'シートが上がる', 'ホームのシート・見方のシート・空港を選ぶシート',
        '<button class="pill tap" type="button" data-sheet-open="w13">見方を変える</button>'
        '<div class="scrim" data-sheet-close></div><div class="sheet"><div class="grab"></div><h3>フライトの見方</h3><p>ON にした見方だけが帯に出ます</p>'
        '<button class="pill dark tap" type="button" data-sheet-close>閉じる</button></div>',
        '下から上がって止まる（行き過ぎて戻る動きはしない）。うしろは薄く暗くなる。閉じるときは少し速く', '開く 0.3 秒・閉じる 0.15 秒',
        'どこから出てどこへ戻るかが分かる'))
    for k in (3,4,8,9,10):
        cards[k] = cards[k].replace('<div class="stage" data-toast-host>', '<div class="stage tst" data-toast-host>')
    cards[-1] = cards[-1].replace('<div class="stage" data-toast-host>', '<div class="stage sheetwrap" id="w13" data-toast-host>')

    body = ('<header class="top"><h1>小さな動きの見本</h1>'
            '<p class="lead">そらメモで使う小さな動き 13 個。押すと動きます。どれも 0.12〜0.4 秒で、iPhone の「視差効果を減らす（動きを減らす）」が ON の人には動きなしで出します。音と振動は入れていません。</p></header>'
            '<div class="ctl"><div class="seg" role="group" aria-label="昼と夜"><button type="button" aria-pressed="true" data-mode="day">昼</button><button type="button" aria-pressed="false" data-mode="night">夜</button></div>'
            '<button type="button" class="sw" role="switch" aria-checked="false" id="rmSw"><span class="tx">動きを減らす</span><span class="lb">OFF</span><span class="tr"><i class="kn"></i></span></button></div>'
            + ''.join(cards) +
            '<section class="sec"><h2>今あるもの（変えない）</h2><ul>'
            '<li>印のハンコが押される動き<small>チェックインの印（press・ring）</small></li>'
            '<li>半券を切る動き<small>ホームの乗る便の券（tkTop・tkBot）と、押せなかったときの横ゆれ</small></li>'
            '<li>運用のカードが広がって専用ページになる動き<small>開く約 0.46 秒・戻る約 0.38 秒（ops-hub で決めたもの）</small></li>'
            '<li>パタパタ<small>近い空港のコードだけ（決まりのまま）</small></li></ul></section>'
            '<section class="sec"><h2>入れないもの</h2><ul>'
            '<li>押した波紋<small>ほかの OS の見た目に寄るので、縮み（01）にそろえる</small></li>'
            '<li>いいね・星<small>人に見せ合う場面がないため</small></li>'
            '<li>横にずらして消す<small>航路と機体の記録は消さないため。知らせの一覧にも使わない</small></li>'
            '<li>紙吹雪・大きなお祝い<small>印のハンコが主役なので重ねない</small></li>'
            '<li>数字のパタパタ<small>案内板風は近い空港のコードと最近の印だけ</small></li>'
            '<li>天気・季節にちなんだ動き<small>却下済み</small></li></ul></section>'
            '<section class="sec"><h2>使う画面ごとの見本</h2><ul>'
            '<li><a href="s1-home.html">ホーム</a><small>01・02・05・07・13</small></li>'
            '<li><a href="s2-airport.html">空港ページ（羽田）</a><small>04・05・10・11</small></li>'
            '<li><a href="s3-ops.html">運用</a><small>06・09・10・12</small></li>'
            '<li><a href="s4-edit.html">表示の編集</a><small>03・05・09</small></li>'
            '<li><a href="s5-shugyo.html">修行</a><small>08</small></li></ul></section>')
    js = r'''
document.querySelectorAll('.seg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.seg button').forEach(x=>x.setAttribute('aria-pressed',x===b));
  if(b.dataset.mode==='night')document.documentElement.dataset.night='on';else delete document.documentElement.dataset.night;});
if(document.documentElement.dataset.night==='on'){document.querySelectorAll('.seg button').forEach(x=>x.setAttribute('aria-pressed',x.dataset.mode==='night'));}
rmSw.addEventListener('click',()=>setTimeout(()=>document.documentElement.classList.toggle('rm',rmSw.getAttribute('aria-checked')==='true')));
if(document.documentElement.classList.contains('rm')){rmSw.setAttribute('aria-checked','true');rmSw.querySelector('.lb').textContent='ON';}
SM.grow(b08,84);n08.textContent='41,744';
'''
    page('index.html', '小さな動きの見本', body, IDX_CSS, js)

# ───────────── 画面ごとの見本（390 幅の1画面） ─────────────
SCR_CSS = r'''
body{padding:0;max-width:430px}
.phone{position:relative;min-height:100vh;overflow:hidden}
.demo{position:relative;z-index:9;display:flex;gap:6px;flex-wrap:wrap;padding:10px 16px;background:repeating-linear-gradient(135deg,transparent 0 8px,rgba(100,107,120,.06) 8px 16px)}
.demo .lab{width:100%;font-size:12px;font-weight:700;color:var(--mute)}
.demo button{min-height:44px;padding:0 14px;border-radius:999px;font-size:13px;font-weight:700;color:var(--sub);background:transparent;box-shadow:inset 0 0 0 1.5px rgba(100,107,120,.45);border:0}
.bottomnav{position:absolute;left:14px;right:14px;bottom:14px;z-index:6}
.hd{display:flex;align-items:center;justify-content:space-between;padding:14px 16px 6px}
.hd .brand{font-size:20px;font-weight:800;color:var(--strong)}
.wrap{padding:0 16px}
.sec-t{margin:22px 4px 8px;font-size:13px;font-weight:800;color:var(--sub)}
'''

def demo(btns):
    return '<div class="demo"><span class="lab">見本の操作（アプリには出ません）</span>%s</div>' % ''.join('<button type="button" onclick="%s">%s</button>' % (f, l) for l, f in btns)

def s1():
    css = r'''
.map{position:absolute;inset:0;background:#E9EEF2}
:root[data-night=on] .map{background:#121820}
.map svg{position:absolute;inset:0;width:100%;height:100%}
.chips{position:absolute;top:98px;left:16px;right:16px;display:flex;justify-content:space-between;z-index:2}
.home-sheet{position:absolute;left:0;right:0;bottom:0;z-index:3;padding:10px 16px 108px;background:var(--bg);border-radius:26px 26px 0 0;box-shadow:0 -10px 30px -12px rgba(17,24,39,.25)}
.home-sheet .grab{width:40px;height:5px;border-radius:3px;background:#D6DAE0;margin:0 auto 12px}
.near{display:flex;border-radius:22px;overflow:hidden;background:#111827;color:#fff;box-shadow:var(--shadow)}
.near .l{flex:1;padding:16px}
.near .k{font-size:12px;color:#AEB9C6;font-weight:700}
.near .cd{display:flex;gap:6px;margin:8px 0}
.near .cd span{display:inline-flex;align-items:center;justify-content:center;width:34px;height:42px;border-radius:8px;background:#1F2937;color:#FBBF24;font-size:24px;font-weight:800}
.near b{font-size:16px}
.near small{display:block;font-size:12px;color:#AEB9C6}
.near .r{width:96px;background:#E8C060;color:#1F2937;display:flex;align-items:center;justify-content:center;writing-mode:vertical-rl;font-weight:800;font-size:17px;letter-spacing:.2em;border-left:2px dashed rgba(17,24,39,.35)}
.near .pinbtn{position:absolute;margin:-4px 0 0;right:112px}
.band{display:flex;align-items:baseline;gap:14px;margin-top:10px;padding:12px 16px;border-radius:18px;background:var(--card);box-shadow:var(--shadow)}
.band .k{font-size:12px;font-weight:700;color:var(--sub);margin-right:4px}
.band .num{font-size:22px}
.band .more{margin-left:auto}
.sheetwrap{position:absolute;inset:0;z-index:8;pointer-events:none}
.sheetwrap.open{pointer-events:auto}
.sheetwrap .sheet{padding-bottom:40px}
.vrow{display:flex;align-items:center;justify-content:space-between;min-height:52px;font-size:15px;font-weight:700;color:var(--strong)}
'''
    body = ('<div class="phone" data-toast-host>' + demo([
        ('数字が増える（07）', "SM.rollSet(rA,0);SM.rollSet(rB,16);setTimeout(()=>{SM.rollTo(rA,1);SM.rollTo(rB,17);pB.classList.remove('show');void pB.offsetWidth;pB.classList.add('show')},60)"),
        ('シート（13）', "document.getElementById('sw1').classList.add('open')"),
        ('札（05）', "SM.toast(this,'保存しました')")]) +
        '<div class="map"><svg viewBox="0 0 390 844" preserveAspectRatio="xMidYMid slice"><g fill="none" stroke="#C9D3DC" stroke-width="1"><path d="M0 300 C120 280 200 330 390 290"/><path d="M0 420 C140 400 230 450 390 410"/></g>'
        '<circle cx="190" cy="300" r="120" fill="none" stroke="#8B3A6B" stroke-dasharray="5 5" opacity=".7"/><g stroke="#8B3A6B" stroke-width="5" stroke-linecap="round" opacity=".8"><path d="M130 220 L220 370"/><path d="M180 190 L270 340"/><path d="M60 290 L130 170"/></g></svg></div>'
        '<div class="home-sheet"><div class="grab"></div>'
        '<div class="near"><div class="l"><span class="k">いちばん近い</span><div class="cd"><span>H</span><span>N</span><span>D</span></div><b>東京国際空港（羽田）</b><small>第1ターミナル・判定範囲の中</small></div><div class="r">チェックイン</div></div>'
        '<div class="band"><span><span class="k">今日の印</span><b class="num"><span class="roll" id="rA" data-v="0"></span></b></span>'
        '<span><span class="k">空港</span><b class="num"><span class="roll" id="rB" data-v="16"></span></b><span class="u">/86</span> <span class="plus" id="pB">＋1</span></span>'
        '<span><span class="k">フライト</span><b class="num">30</b></span></div></div>'
        '<div class="sheetwrap" id="sw1"><div class="scrim" data-sheet-close></div><div class="sheet"><div class="grab"></div><h2>ホームに出すもの</h2>'
        + ''.join('<div class="vrow">%s<button type="button" class="sw" role="switch" aria-checked="%s"><span class="lb">%s</span><span class="tr"><i class="kn"></i></span></button></div>' % (n, 'true' if o else 'false', 'ON' if o else 'OFF') for n, o in (('近くの空港', 1), ('今日の数字', 1), ('乗る便', 1), ('ピン止めした空港', 0)))
        + '<button class="pill dark tap" style="width:100%;margin-top:12px" type="button" data-sheet-close>閉じる</button></div></div>'
        '<div class="bottomnav">' + tabs('home') + '</div></div>')
    page('s1-home.html', 'ホームの動き', body, SCR_CSS + css)

def s2():
    css = r'''
.aphd{display:flex;align-items:center;gap:10px;padding:14px 16px}
.aphd .bk{display:inline-flex;width:44px;height:44px;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.aphd h1{font-size:18px}
.hero{display:flex;gap:16px;align-items:center}
.stamp{width:88px;height:88px;border-radius:50%;box-shadow:inset 0 0 0 3px var(--jal);display:flex;align-items:center;justify-content:center;color:var(--jal);font-size:24px;font-weight:800;letter-spacing:.04em}
.hero .tx b{display:block;font-size:30px;font-weight:800;color:var(--strong);line-height:1}
.hero .tx h2{margin-top:6px}
.hero .tx p{font-size:13px;color:var(--sub)}
.acts{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.belbtn{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 16px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong)}
.belbtn svg{width:20px;height:20px}
.belbtn[aria-pressed=true]{background:var(--pin-wash);box-shadow:inset 0 0 0 1.5px var(--pin)}
.dl{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.dl .card{padding:14px}
.dl .k{font-size:12px;font-weight:700;color:var(--sub)}
.dl .num{font-size:26px}
.regs .r{display:flex;align-items:center;gap:10px;min-height:56px}
.regs .r b{font-size:17px;font-weight:800;color:var(--strong);letter-spacing:.04em}
.regs .r small{font-size:12px;color:var(--mute);flex:1}
'''
    body = ('<div class="phone" data-toast-host>' + demo([
        ('ピン止め（04）', "document.querySelector('.pinbtn').click()"), ('知らせ（11）', "document.querySelector('.bell').click()"), ('コピー（10）', "document.querySelector('.copy').click()")]) +
        '<div class="aphd"><span class="bk">%s</span><h1>空港</h1></div><div class="wrap">' % ic('back') +
        '<div class="card"><div class="hero"><div class="stamp">HND</div><div class="tx"><b>HND</b><h2>東京国際空港（羽田）</h2><p>東京都・関東</p></div></div>'
        '<div class="acts"><button type="button" class="pinbtn tap" aria-pressed="false">%s<span>ピン止め</span></button>' % ic('pin') +
        '<button type="button" class="belbtn bell tap" aria-pressed="false">%s<span>知らせ OFF</span></button></div>' % ic('bell') +
        '<div class="dl"><div class="card"><span class="k">押した回数</span><div><b class="num">12</b><span class="u">回</span></div></div>'
        '<div class="card"><span class="k">はじめて押した日</span><div><b class="num" style="font-size:18px">2026</b><span class="u">年</span><b class="num" style="font-size:18px">4</b><span class="u">月</span><b class="num" style="font-size:18px">3</b><span class="u">日</span></div></div></div></div>'
        '<p class="sec-t">いまいる特別塗装機</p><div class="card regs">'
        '<div class="r"><b>JA8089</b><small>B767-300・特別塗装</small><button type="button" class="copy tap" data-copy="JA8089" aria-label="コピー">%s%s</button></div>' % (ic('copy', 'ic cp'), ic('check', 'ic ck')) +
        '<div class="r"><b>JA602A</b><small>B767-300ER・特別塗装</small><button type="button" class="copy tap" data-copy="JA602A" aria-label="コピー">%s%s</button></div></div>' % (ic('copy', 'ic cp'), ic('check', 'ic ck')) +
        '</div><div class="bottomnav">' + tabs('book') + '</div></div>')
    page('s2-airport.html', '空港ページの動き', body, SCR_CSS + css)

def s3():
    css = r'''
.aprow{display:flex;align-items:center;gap:8px;padding:6px 16px}
.appill{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 16px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-weight:800;color:var(--strong)}
.appill .cd{display:inline-flex;padding:2px 6px;border-radius:6px;background:#1F2937;color:#fff;font-size:12px}
.sortbtn{margin-left:auto}
.board{margin-top:8px}
.board .r{display:flex;align-items:center;gap:10px;min-height:52px}
.board .cd{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:26px;border-radius:8px;background:#0F1B2D;color:#fff;font-size:12px;font-weight:800}
.board .r b{font-size:14px;color:var(--strong);flex:1}
.board .t{font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.board .reg{font-size:12px;color:var(--mute)}
.board .copy{width:44px;height:44px}
.offcard{margin-top:12px;padding:14px 16px;display:flex;align-items:center;gap:12px}
.offcard .tx{flex:1;min-width:0}
.offcard b{display:block;font-size:14px;color:var(--strong)}
.offcard [data-st]{font-size:12px;color:var(--mute)}
.offcard[data-ok="1"] [data-st]{color:var(--ok);font-weight:700}
.retry{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--pill);font-size:13px;font-weight:800;color:var(--strong)}
.retry svg{width:18px;height:18px}
.sk .r{display:flex;align-items:center;gap:10px;min-height:52px}
'''
    rows = (('JL', 'JL 501 新千歳', '14:30', 'JA8089'), ('NH', 'NH 993 伊丹', '14:35', 'JA602A'), ('JL', 'JL 909 那覇', '14:40', 'JA751J'))
    real = ''.join('<div class="r"><span class="cd">%s</span><b>%s<br><span class="reg">%s</span></b><span class="t">%s</span><button type="button" class="copy tap" data-copy="%s" aria-label="コピー">%s%s</button></div>' % (c, n, rg, t, rg, ic('copy', 'ic cp'), ic('check', 'ic ck')) for c, n, t, rg in rows)
    sk = ''.join('<div class="r"><span class="skel" style="width:44px;height:26px"></span><span class="skel" style="flex:1;height:14px"></span><span class="skel" style="width:44px;height:14px"></span></div>' for _ in rows)
    body = ('<div class="phone" data-toast-host>' + demo([
        ('読み込む（06）', "SM.loadInto(document.getElementById('bd'),1600)"), ('並べ替え（09）', "document.getElementById('sortArea').hidden=!document.getElementById('sortArea').hidden"), ('もう一度（12）', "document.querySelector('.retry').click()")]) +
        '<div class="aprow"><span class="appill"><span class="cd">HND</span>羽田</span><button class="pill sortbtn tap" type="button" onclick="document.getElementById(\'sortArea\').hidden=!document.getElementById(\'sortArea\').hidden">並べ替え</button></div><div class="wrap">'
        '<div id="sortArea" hidden><p class="sec-t">≡ を押さえて上下に動かす</p><div class="sortlist" id="s3sort">'
        + ''.join('<div class="srow"><b>%s</b><span class="grip" aria-label="%sを動かす">%s</span></div>' % (n, n, ic('grip')) for n in ('滑走路', '地図', '案内板', '3D', '特別塗装機'))
        + '</div></div>'
        '<p class="sec-t">案内板（出発）</p><div class="card board" id="bd"><div data-skel hidden class="sk">' + sk + '</div><div data-real>' + real + '</div></div>'
        '<div class="card offcard" data-retry-box><span style="color:var(--mute)">%s</span><div class="tx"><b>運航情報を読めませんでした</b><span data-st>最後に読んだ 14時05分</span></div><button type="button" class="retry tap">%s<span>もう一度</span></button></div>' % (ic('wifi'), ic('retry')) +
        '</div><div class="bottomnav">' + tabs('ops') + '</div></div>')
    page('s3-ops.html', '運用の動き', body, SCR_CSS + css)

def s4():
    css = r'''
.ehd{display:flex;align-items:center;gap:10px;padding:14px 16px}
.ehd .bk{display:inline-flex;width:44px;height:44px;align-items:center;justify-content:center;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.ehd h1{font-size:18px}
.seg2{display:flex;gap:6px;padding:4px;border-radius:999px;background:var(--pill);margin:4px 0 6px}
.seg2 button{flex:1;min-height:44px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.seg2 button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.trow{display:flex;align-items:center;gap:6px;min-height:60px;padding:0 4px 0 16px;margin-bottom:10px;background:var(--card);border-radius:18px;box-shadow:var(--shadow)}
.trow b{flex:1;font-weight:700;color:var(--strong)}
.trow .alw{font-size:12px;font-weight:800;color:var(--mute);padding-right:12px}
.srow .sw{margin-right:2px}
'''
    def row(n, on, grip=True):
        sw = '<button type="button" class="sw" role="switch" aria-checked="%s" aria-label="%s"><span class="lb">%s</span><span class="tr"><i class="kn"></i></span></button>' % ('true' if on else 'false', n, 'ON' if on else 'OFF')
        return '<div class="srow"><b>%s</b>%s<span class="grip" aria-label="%sを動かす">%s</span></div>' % (n, sw, n, ic('grip'))
    body = ('<div class="phone" data-toast-host>' + demo([
        ('ON／OFF（03）', "document.querySelectorAll('.sw')[3].click()"), ('持ち上げ（09）', "SM.sortDemo(document.getElementById('s4sort'),2)"), ('保存の札（05）', "SM.toast(this,'表示を保存しました')")]) +
        '<div class="ehd"><span class="bk">%s</span><h1>表示の編集</h1></div><div class="wrap">' % ic('back') +
        '<div class="seg2" role="group" aria-label="編集するもの"><button type="button" aria-pressed="true">タブ</button><button type="button" aria-pressed="false">見方</button><button type="button" aria-pressed="false">ホーム</button></div>'
        '<p class="sec-t">下のタブ（5つまで）</p>'
        '<div class="trow"><b>ホーム</b><span class="alw">いつも</span></div>'
        '<div class="sortlist" id="s4sort">' + row('図鑑', 1) + row('フライト', 1) + row('運用', 1) + row('修行', 0) + row('成績', 0) + '</div>'
        '<p class="lead" style="margin:6px 4px 0">ON にした順にタブに並びます。≡ を押さえて並べ替え。</p>'
        '</div><div class="bottomnav">' + tabs('home') + '</div></div>')
    page('s4-edit.html', '表示の編集の動き', body, SCR_CSS + css)

def s5():
    css = r'''
.sghd{display:flex;align-items:center;justify-content:space-between;padding:14px 16px 4px}
.sghd h1{font-size:20px}
.road{padding:20px}
.road .k{font-size:13px;font-weight:700;color:var(--sub)}
.road .big{font-size:52px;line-height:1.05;letter-spacing:-.02em}
.road .goal{display:flex;justify-content:space-between;margin-top:6px;font-size:12px;color:var(--mute)}
.boxes{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.boxes .card{padding:14px}
.boxes .k{font-size:12px;font-weight:700;color:var(--sub)}
.boxes .num{font-size:26px}
.road .note{margin-top:14px;font-size:13px;color:var(--ink)}
.road .note small{font-size:12px;color:var(--mute)}
'''
    body = ('<div class="phone" data-toast-host>' + demo([('開いたとき（08）', "n5.dataset.from=0;SM.countUp(n5,41744);SM.grow(b5,84);SM.grow(b5b,60)")]) +
        '<div class="sghd"><h1>修行</h1><button class="pill tap" type="button">%s見方</button></div><div class="wrap">' % ic('pencil') +
        '<div class="card road"><span class="k">JAL・今のポイント</span><div><b class="num big" id="n5">0</b><span class="u">FOP</span></div>'
        '<div class="bar" id="b5" style="margin-top:12px"><i></i></div><div class="goal"><span>0</span><span>50,000 FOP</span></div>'
        '<div class="boxes"><div class="card"><span class="k">あと</span><div><b class="num">8,256</b><span class="u">FOP</span></div></div>'
        '<div class="card"><span class="k">あと</span><div><b class="num">10</b><span class="u">回</span></div><div class="bar" id="b5b" style="height:6px;margin-top:8px"><i></i></div></div></div>'
        '<p class="note">今のペースなら、12月中に届きそうです<small>（推定）</small></p></div>'
        '</div><div class="bottomnav">' + tabs('sg') + '</div></div>')
    js = "setTimeout(()=>{SM.countUp(n5,41744);SM.grow(b5,84);SM.grow(b5b,60)},250)"
    page('s5-shugyo.html', '修行の動き', body, SCR_CSS + css, js)

index(); s1(); s2(); s3(); s4(); s5()
