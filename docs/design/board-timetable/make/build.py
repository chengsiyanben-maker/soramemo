# -*- coding: utf-8 -*-
# 「いまの空港」の今日の便（案内板）を空港の時刻表のようにする画面案を組み立てる
# base.css（design/ia-ops から写した共通の見た目＝main の web/index.html の色と文字。地だけ #EEF1F5）を各ページに埋め込み、外部の読み込みなしで開ける HTML にする
# 便・機材・ゲートはすべて見本（実在の今日の便ではない）
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from icons import P
OUT = os.path.dirname(HERE)
CSS = open(HERE + '/base.css', encoding='utf-8').read()
P.update({
 'down': '<path d="M6 9l6 6 6-6"/>',
 'search': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
 'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
})
def ic(name, cls='ic'):
    return '<svg class="%s i-%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, name, P[name])

# 下のタブ（11/26 本人「B」：ホーム・図鑑・フライト・いまの空港・マイページ）
TABS = [('home', 'ホーム', 'home'), ('book', '図鑑', 'book'), ('log', 'フライト', 'plane'), ('now', 'いまの空港', 'ops'), ('me', 'マイページ', 'user')]
def tabbar(cur='now'):
    out = ['<nav class="tabs" aria-label="下のタブ">']
    for k, lb, icn in TABS:
        on = k == cur
        out.append('<button type="button"%s>%s<span>%s</span>%s</button>' % (
            ' aria-current="page"' if on else '', ic(icn), lb, '<i class="dt"></i>' if on else ''))
    out.append('</nav>')
    return ''.join(out)

# ── 見本の便 ──  (定刻, 変更後, 会社, 番号, 行き先, 経由, 機材, ゲート, 状況, 推定か)
# 状況：ok 定刻／late 遅れ／board 搭乗中／gone 出発済み・到着済み／x 欠航／est 時刻表にない便（推定）
DEP = [
 ('14:05', '', 'JL', '313', '福岡', '', 'A359', '7', 'gone', 0),
 ('14:20', '', 'NH', '247', '福岡', '', 'B789', '59', 'gone', 0),
 'NOW',
 ('14:30', '14:45', 'JL', '519', '新千歳', '', 'A359', '15', 'late', 0),
 ('14:35', '', 'BC', '513', '神戸', '', 'B738', '', 'est', 1),
 ('14:40', '', 'JL', '461', '松山', '', 'B738', '8', 'board', 0),
 ('14:45', '', 'NH', '65', '新千歳', '', 'B772', '62', 'ok', 0),
 ('14:50', '', 'NH', '469', '那覇', '', 'B763', '61', 'x', 0),
 ('14:55', '', 'JL', '907', '那覇', '', 'A359', '13', 'ok', 0),
 'H15',
 ('15:00', '', 'NH', '255', '福岡', '', 'B789', '64', 'ok', 0),
 ('15:05', '', 'NH', '1793', '石垣', '那覇経由', 'B738', '56', 'ok', 0),
 ('15:10', '15:35', 'JL', '323', '福岡', '', 'B763', '9', 'late', 0),
 ('15:15', '', 'HD', '23', '新千歳', '', 'B763', '18', 'ok', 0),
]
ARR = [
 ('14:10', '14:06', 'JL', '502', '新千歳', '', 'A359', '16', 'gone', 0),
 ('14:15', '14:21', 'NH', '240', '福岡', '', 'B789', '60', 'gone', 0),
 'NOW',
 ('14:25', '14:50', 'JL', '904', '那覇', '', 'A359', '14', 'late', 0),
 ('14:30', '', 'NH', '52', '新千歳', '', 'B772', '63', 'ok', 0),
 ('14:35', '', 'JL', '432', '松山', '', 'B738', '', 'x', 0),
 ('14:40', '', 'NH', '990', '那覇', '', 'B763', '61', 'ok', 0),
 ('14:50', '', 'BC', '514', '神戸', '', 'B738', '', 'est', 1),
 ('14:55', '', 'JL', '120', '伊丹', '', 'B763', '19', 'ok', 0),
 'H15',
 ('15:00', '', 'NH', '18', '伊丹', '', 'B772', '57', 'ok', 0),
 ('15:05', '', 'NH', '1794', '石垣', '宮古経由', 'B738', '55', 'ok', 0),
 ('15:15', '15:40', 'JL', '326', '福岡', '', 'B763', '12', 'late', 0),
]
ST = {
 'dep': {'ok': '定刻', 'late': '遅れ', 'board': '搭乗中', 'gone': '出発済み', 'x': '欠航', 'est': '推定'},
 'arr': {'ok': '定刻', 'late': '遅れ', 'board': '搭乗中', 'gone': '到着済み', 'x': '欠航', 'est': '推定'},
}

def rows(data, kind, plan):
    out = []
    for i, f in enumerate(data):
        if f == 'NOW':
            out.append('<div class="nowl" role="separator"><span>いま <b class="num">14:22</b></span></div>')
            continue
        if f == 'H15':
            out.append('<div class="hrl">15時台</div>')
            continue
        t, t2, al, no, dst, via, eq, gate, st, est = f
        lab = ST[kind][st]
        tcls = 't'
        t2h = ''
        if t2:
            cls2 = 'chg' if st == 'late' else 'chg ok2'
            t2h = '<span class="%s num flap" data-k="t2">%s</span>' % (cls2, t2)
        else:
            t2h = '<span class="chg num flap" data-k="t2"></span>'
        sth = '<span class="flap" data-k="st">%s</span>' % lab
        dst_h = '<b>%s</b>%s' % (dst, '<small>%s</small>' % via if via else '')
        gate_h = '<span class="num">%s</span>' % gate if gate else '<span class="na">—</span>'
        rid = '%s-%s%s' % (kind, al, no)
        out.append(
            '<button type="button" class="r s-%s" id="%s" aria-label="%s %s%s %s %s">'
            '<span class="c-t"><span class="sch num">%s</span>%s</span>'
            '<span class="c-no"><small>%s</small><b class="num">%s</b></span>'
            '<span class="c-dst">%s</span>'
            '<span class="c-eq">%s</span>'
            '<span class="c-g">%s</span>'
            '<span class="c-st">%s</span>'
            '</button>' % (st, rid, t, al, no, dst, lab, t, t2h, al, no, dst_h, eq, gate_h, sth))
    return ''.join(out)

def board(kind, plan):
    lab_dst = '行き先' if kind == 'dep' else '出発地'
    head = ('<div class="cols" aria-hidden="true"><span class="c-t">%s</span><span class="c-no">便名</span>'
            '<span class="c-dst">%s</span><span class="c-eq">機材</span><span class="c-g">ゲート</span><span class="c-st">状況</span></div>'
            % ('定刻<br>変更' , lab_dst))
    data = DEP if kind == 'dep' else ARR
    title = '出発' if kind == 'dep' else '到着'
    cap = ('<div class="bcap"><b>%s</b><span>今日 %s <span class="num">%d</span>便・欠航 <span class="num">%d</span>便</span></div>'
           % (title, title, 186 if kind == 'dep' else 184, 3 if kind == 'dep' else 2))
    src = ('<p class="src">出典 ODPT（運航情報 14時22分・時刻表 11月26日時点）。'
           '「推定」は時刻表にない便で、全機の記録からの見込み（出典 adsb.lol・ODbL）。ゲートは変わることがあります。</p>')
    return ('<section class="bd bd-%s" aria-label="今日の便 %s">%s%s<div class="list">%s</div>'
            '<div class="more"><button type="button">16時台から先を見る</button></div>%s</section>'
            % (plan, title, cap, head, rows(data, kind, plan), src))

PAGE_CSS = r'''
body{padding:0 16px 132px}
.tabs{position:fixed;left:50%;bottom:14px;width:calc(100% - 28px);max-width:402px;transform:translateX(-50%);z-index:20}
.tabs button{position:relative}
.tabs button span{white-space:nowrap;letter-spacing:-.03em}
.tabs .dt{position:absolute;bottom:7px;left:50%;width:5px;height:5px;margin-left:-2.5px;border-radius:50%;background:var(--acc)}
.head{display:flex;align-items:center;gap:8px;padding:18px 0 4px}
.ap{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:0 14px 0 8px;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.ap .cd{display:inline-flex;align-items:center;justify-content:center;height:28px;padding:0 8px;border-radius:9px;background:var(--hero);color:#fff;font-size:13px;font-weight:800;letter-spacing:.06em}
:root[data-night=on] .ap .cd{color:#0F141B}
.ap b{font-size:18px;font-weight:800;color:var(--strong)}
.ap svg{width:18px;height:18px;color:var(--sub)}
.upd{margin-left:auto;display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:800;color:var(--strong);font-variant-numeric:tabular-nums}
.upd small{font-size:12px;font-weight:600;color:var(--mute)}
.upd svg{width:17px;height:17px;color:var(--sub)}
.seg3{display:flex;margin-top:12px;padding:4px;border-radius:999px;background:var(--pill)}
.seg3 button{flex:1;min-height:44px;padding:0 6px;border-radius:999px;font-size:14px;font-weight:800;color:var(--sub);white-space:nowrap}
.seg3 button[aria-pressed=true]{background:var(--card);color:var(--strong);box-shadow:var(--shadow)}
.tools{display:flex;gap:8px;margin-top:12px;align-items:center}
.dir{display:inline-flex;padding:3px;border-radius:999px;background:var(--card);box-shadow:var(--shadow)}
.dir button{min-height:40px;min-width:56px;padding:0 12px;border-radius:999px;font-size:13px;font-weight:800;color:var(--sub)}
.dir button[aria-pressed=true]{background:var(--strong);color:#fff}
:root[data-night=on] .dir button[aria-pressed=true]{color:#0F141B}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;font-weight:700;color:var(--ink);white-space:nowrap}
.srch{flex:1;min-width:0;display:flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border-radius:999px;background:var(--card);box-shadow:var(--shadow);font-size:13px;color:var(--mute);white-space:nowrap;overflow:hidden}
.srch svg{width:17px;height:17px;flex:none}
.plan{display:inline-flex;align-items:center;min-height:26px;padding:0 10px;border-radius:999px;background:var(--pill);font-size:12px;font-weight:800;color:var(--sub)}

/* ── 時刻表の共通の骨組み（列の幅は 案A・案B で同じ） ── */
.bd{margin-top:14px;border-radius:22px;padding:14px 10px 12px;overflow:hidden}
.bcap{display:flex;align-items:baseline;justify-content:space-between;padding:0 6px 8px}
.bcap b{font-size:20px;font-weight:800;letter-spacing:.08em}
.bcap > span{font-size:12px;font-weight:700}
.bcap .num{font-size:13px}
.cols,.r{display:grid;grid-template-columns:50px 38px minmax(0,1fr) 34px 38px 62px;column-gap:6px;align-items:center}
.cols{position:sticky;top:0;z-index:2;padding:6px 6px;border-radius:12px;font-size:12px;font-weight:700;line-height:1.25}
.cols .c-g,.cols .c-st{text-align:center;white-space:nowrap;letter-spacing:-.04em}
.bd .num{color:inherit}
.cols > span{font-size:12px;font-weight:700}
.r{width:100%;min-height:56px;padding:8px 6px;text-align:left;border-radius:12px}
.r + .r{margin-top:2px}
.c-t{display:flex;flex-direction:column;line-height:1.1}
.sch{font-size:19px;font-weight:800;letter-spacing:-.03em}
.chg{font-size:15px;font-weight:800;letter-spacing:-.02em;min-height:0}
.chg:empty{display:none}
.c-no{display:flex;flex-direction:column;line-height:1.1}
.c-no small{font-size:12px;font-weight:800;letter-spacing:.04em}
.c-no b{font-size:15px;font-weight:800;letter-spacing:-.02em}
.c-dst{min-width:0;line-height:1.2}
.c-dst b{display:block;font-size:17px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.c-dst small{display:block;font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.c-eq{font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.c-g{text-align:center;font-size:18px;font-weight:800}
.c-g .na{font-size:14px;font-weight:700}
.c-st{text-align:center;font-size:13px;font-weight:800;white-space:nowrap}
.nowl{position:relative;display:flex;justify-content:flex-end;align-items:center;height:28px;margin:4px 6px}
.nowl span{position:relative;z-index:1;padding:0 0 0 8px;font-size:12px;font-weight:700}
.nowl .num{font-size:13px}
.nowl::before{content:"";position:absolute;left:0;right:76px;top:50%;height:2px;border-radius:2px}
.hrl{margin:12px 6px 4px;font-size:12px;font-weight:800;letter-spacing:.06em}
.more{display:flex;justify-content:center;margin:8px 0 2px}
.more button{min-height:44px;padding:0 16px;border-radius:999px;font-size:13px;font-weight:700}
.src{margin:6px 6px 2px;font-size:12px;line-height:1.55}

/* ── 案A：濃い紺の地に白・黄の文字（今日の便の一覧のカードの中だけ） ── */
.bd-a{background:#0E1E36;color:#F5F7FA;box-shadow:0 10px 30px -10px rgba(14,30,54,.45)}
.bd-a{--yl:#FFD23F;--dim:rgba(245,247,250,.55);--lab:#A9B7CB}
.bd-a .bcap b{color:#fff}
.bd-a .bcap > span{color:var(--lab)}
.bd-a .bcap .num{color:#fff}
.bd-a .cols{background:#162B4A;color:var(--lab)}
.bd-a .r{color:#fff}
.bd-a .r:nth-of-type(even){background:rgba(255,255,255,.035)}
.bd-a .c-no small{color:var(--lab)}
.bd-a .c-dst small{color:var(--lab)}
.bd-a .c-eq{color:#C9D3E0}
.bd-a .c-g .na{color:var(--lab)}
.bd-a .chg{color:var(--yl)}
.bd-a .chg.ok2{color:#fff;opacity:.75}
.bd-a .s-ok .c-st{color:#fff}
.bd-a .s-late .c-st,.bd-a .s-board .c-st{color:var(--yl)}
.bd-a .s-board .c-st [data-k=st]::before{content:"";display:inline-block;width:7px;height:7px;margin:0 4px 1px 0;border-radius:50%;background:var(--yl)}
.bd-a .s-x .c-st [data-k=st]{display:inline-block;padding:2px 8px;border-radius:999px;background:var(--yl);color:#0E1E36}
.bd-a .s-x .sch,.bd-a .s-x .c-dst b,.bd-a .s-x .c-no b,.bd-a .s-x .c-g .num,.bd-a .s-x .c-eq{color:var(--dim)}
.bd-a .s-gone{color:var(--dim)}
.bd-a .s-gone .sch,.bd-a .s-gone .c-dst b,.bd-a .s-gone .c-no b,.bd-a .s-gone .c-g .num,.bd-a .s-gone .c-eq,.bd-a .s-gone .c-st{color:var(--dim)}
.bd-a .s-est .c-st{color:var(--lab);font-weight:700}
.bd-a .s-est .c-st [data-k=st]{border-bottom:1.5px dotted var(--lab)}
.bd-a .nowl span{color:var(--yl)}
.bd-a .nowl .num{color:var(--yl)}
.bd-a .nowl::before{background:var(--yl);opacity:.5}
.bd-a .hrl{color:var(--lab)}
.bd-a .more button{color:#fff;background:rgba(255,255,255,.08)}
.bd-a .src{color:var(--lab)}
:root[data-night=on] .bd-a{background:#0B1626;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}
:root[data-night=on] .bd-a{--yl:#4ADE80}
:root[data-night=on] .bd-a .s-x .c-st [data-k=st]{color:#0B1626}

/* ── 案B：今の明るい角丸カードのまま列をそろえる ── */
.bd-b{background:var(--card);box-shadow:var(--shadow);color:var(--strong)}
.bd-b{--late:#9A3412}
:root[data-night=on] .bd-b{--late:#FDBA74}
.bd-b .bcap b{color:var(--strong)}
.bd-b .bcap > span{color:var(--mute)}
.bd-b .cols{background:#F1F3F6;color:var(--sub)}
:root[data-night=on] .bd-b .cols{background:#232830}
.bd-b .r{color:var(--strong)}
.bd-b .c-no small{color:var(--sub)}
.bd-b .c-no small::before{content:"";display:inline-block;width:3px;height:10px;margin-right:4px;border-radius:2px;background:#9CA3AF;vertical-align:-1px}
.bd-b .r[id*="-JL"] .c-no small::before{background:var(--jal);opacity:.75}
.bd-b .r[id*="-NH"] .c-no small::before{background:var(--ana);opacity:.75}
.bd-b .c-dst small{color:var(--mute)}
.bd-b .c-eq{color:var(--sub)}
.bd-b .c-g .na{color:var(--mute)}
.bd-b .chg{color:var(--late)}
.bd-b .chg.ok2{color:var(--sub)}
.bd-b .c-st [data-k=st]{display:inline-block;min-width:48px;padding:3px 4px;border-radius:999px;background:var(--pill);color:var(--sub)}
.bd-b .s-ok .c-st [data-k=st]{color:var(--strong)}
.bd-b .s-late .c-st [data-k=st]{background:rgba(154,52,18,.09);color:var(--late)}
:root[data-night=on] .bd-b .s-late .c-st [data-k=st]{background:rgba(253,186,116,.12)}
.bd-b .s-board .c-st [data-k=st]{background:var(--strong);color:#fff}
:root[data-night=on] .bd-b .s-board .c-st [data-k=st]{color:#0F141B}
.bd-b .s-x .c-st [data-k=st]{background:transparent;color:var(--strong);box-shadow:inset 0 0 0 1.5px var(--strong)}
.bd-b .s-x .c-g .num{color:var(--mute)}
.bd-b .s-x .sch,.bd-b .s-x .c-dst b,.bd-b .s-x .c-no b{color:var(--mute);text-decoration:line-through;text-decoration-thickness:1.5px}
.bd-b .s-gone .sch,.bd-b .s-gone .c-dst b,.bd-b .s-gone .c-no b,.bd-b .s-gone .c-g .num,.bd-b .s-gone .chg{color:var(--mute)}
.bd-b .s-est .c-st [data-k=st]{background:transparent;color:var(--mute);}
.bd-b .s-est .c-st [data-k=st]{box-shadow:none;min-width:0;padding:0 2px;border-radius:0;border-bottom:1.5px dotted #9CA3AF;font-weight:700}
.bd-b .nowl span{color:var(--acc)}
.bd-b .nowl .num{color:var(--acc)}
.bd-b .nowl::before{background:var(--acc);opacity:.35}
.bd-b .hrl{color:var(--sub)}
.bd-b .more button{color:var(--sub)}
.bd-b .src{color:var(--mute)}

/* ── パタパタ（状況が変わったときだけ。動きを減らす設定では動かさない） ── */
.fch{display:inline-block;transform-origin:50% 50%;backface-visibility:hidden}
.fch.go{animation:flip .34s var(--ease) both}
@keyframes flip{0%{transform:perspective(200px) rotateX(-92deg);opacity:.15}55%{transform:perspective(200px) rotateX(12deg);opacity:1}100%{transform:perspective(200px) rotateX(0)}}
.flash{animation:flash 1.6s ease-out 1 both}
.bd-a .flash{--fl:rgba(255,210,63,.16)}
.bd-b .flash{--fl:rgba(37,99,235,.08)}
@keyframes flash{0%,40%{background:var(--fl)}100%{background:transparent}}
@media (prefers-reduced-motion:reduce){.fch.go,.flash{animation:none!important}}
html.rm .fch.go,html.rm .flash{animation:none!important}
.demo{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;justify-content:center}
.demo .pill{font-size:13px}
.demo .note{width:100%;text-align:center;font-size:12px;color:var(--mute)}
'''

JS = r'''
(function(){
  var q = new URLSearchParams(location.search);
  if (q.get('n') === '1') document.documentElement.setAttribute('data-night','on');
  if (q.get('rm') === '1') document.documentElement.classList.add('rm');
  function chars(el, text){
    el.textContent = '';
    var spans = [];
    Array.from(text).forEach(function(c, i){
      var s = document.createElement('span'); s.className = 'fch'; s.textContent = c === ' ' ? ' ' : c;
      s.style.animationDelay = (i * 0.045) + 's'; el.appendChild(s); spans.push(s);
    });
    return spans;
  }
  var reduce = function(){ return document.documentElement.classList.contains('rm') || matchMedia('(prefers-reduced-motion: reduce)').matches; };
  // 状況を変える：変わったセルの字だけをパタパタ（動きを減らす設定では字を置き換えるだけ）
  window.setState = function(id, st, label, t2){
    var r = document.getElementById(id); if (!r) return;
    r.className = r.className.replace(/s-\w+/, 's-' + st);
    var cells = [[r.querySelector('[data-k=st]'), label]];
    var tc = r.querySelector('[data-k=t2]');
    if (t2 !== undefined && tc) { tc.className = 'chg num flap' + (st === 'late' ? '' : ' ok2'); cells.push([tc, t2]); }
    cells.forEach(function(p){
      if (p[0].textContent === p[1]) return;
      var sp = chars(p[0], p[1]);
      if (!reduce()) sp.forEach(function(s){ s.classList.add('go'); });
    });
    if (!reduce()) { r.classList.remove('flash'); void r.offsetWidth; r.classList.add('flash'); }
  };
  // 撮影用：動きを t 秒の所で止める
  window.__frame = function(t){
    document.querySelectorAll('.fch.go,.flash').forEach(function(s){
      var d = parseFloat(s.style.animationDelay || 0);
      s.style.animationPlayState = 'paused'; s.style.animationDelay = (-(t - d)) + 's';
    });
  };
  window.__demo = DEMO;
  document.querySelectorAll('[data-demo]').forEach(function(b){
    b.addEventListener('click', function(){ var d = DEMO[b.dataset.demo]; d.forEach(function(a){ setState.apply(null, a); }); });
  });
})();
'''

def page(name, title, kind, plan, desc):
    other = 'arr' if kind == 'dep' else 'dep'
    demo = {
        'dep': {'chg': [['dep-NH65', 'late', '遅れ', '15:05']], 'board': [['dep-JL907', 'board', '搭乗中']], 'x': [['dep-NH255', 'x', '欠航']],
                'back': [['dep-NH65', 'ok', '定刻', ''], ['dep-JL907', 'ok', '定刻'], ['dep-NH255', 'ok', '定刻']]},
        'arr': {'chg': [['arr-NH52', 'late', '遅れ', '14:55']], 'board': [['arr-NH990', 'gone', '到着済み', '14:33']], 'x': [['arr-NH18', 'x', '欠航']],
                'back': [['arr-NH52', 'ok', '定刻', ''], ['arr-NH990', 'ok', '定刻', ''], ['arr-NH18', 'ok', '定刻']]},
    }[kind]
    lbl = {'dep': ('NH 65 が遅れる', 'JL 907 が搭乗中に', 'NH 255 が欠航'), 'arr': ('NH 52 が遅れる', 'NH 990 が着く', 'NH 18 が欠航')}[kind]
    body = (
      '<div class="head"><span class="ap"><span class="cd">HND</span><b>羽田</b>%s</span>'
      '<span class="upd"><small>最後に読んだ</small>14:22 %s</span></div>'
      '<div class="seg3" role="group"><button type="button" aria-pressed="true">今日の便</button><button type="button" aria-pressed="false">滑走路・3D</button><button type="button" aria-pressed="false">特別塗装機</button></div>'
      '<div class="tools"><span class="dir" role="group"><button type="button" aria-pressed="%s">出発</button><button type="button" aria-pressed="%s">到着</button></span>'
      '<span class="chip">遅れあり</span><span class="srch">%s便名・%s</span></div>'
      '%s'
      '<div class="demo"><p class="note">見本：押すと状況が変わり、変わったセルだけパタパタ（動きを減らす設定では字が変わるだけ）</p>'
      '<button type="button" class="pill" data-demo="chg">%s</button><button type="button" class="pill" data-demo="board">%s</button>'
      '<button type="button" class="pill" data-demo="x">%s</button><button type="button" class="pill" data-demo="back">もとに戻す</button></div>'
      % (ic('down'), ic('retry'), 'true' if kind == 'dep' else 'false', 'false' if kind == 'dep' else 'true',
         ic('search'), '行き先' if kind == 'dep' else '出発地', board(kind, plan), lbl[0], lbl[1], lbl[2]))
    html = ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s｜案内板を時刻表に</title><meta name="description" content="%s"><style>%s%s</style></head>'
            '<body>%s%s<script>var DEMO=%s;%s</script></body></html>'
            % (title, desc, CSS, PAGE_CSS, body, tabbar(), json.dumps(demo, ensure_ascii=False), JS))
    open(os.path.join(OUT, name + '.html'), 'w', encoding='utf-8').write(html)

SCREENS = [
 ('a1-dep', '案A 出発', 'dep', 'a', '濃い紺の地に白・黄の文字。変更後の時刻と遅れ・搭乗中は黄、欠航は黄の札、出発済みは薄く'),
 ('a2-arr', '案A 到着', 'arr', 'a', '到着の時刻表。早着・到着済みの実際の時刻は白を少し薄く'),
 ('b1-dep', '案B 出発', 'dep', 'b', '今の明るい角丸カードのまま列をそろえる。状況は小さなピル、遅れは今の茶色、欠航は線で消して枠のピル'),
 ('b2-arr', '案B 到着', 'arr', 'b', '到着の時刻表。会社は便名の左の細い色の印だけ（ロゴなし）'),
]
for s in SCREENS:
    page(*s)
json.dump(SCREENS, open(HERE + '/screens.json', 'w'), ensure_ascii=False, indent=1)
print('組み立て', len(SCREENS), '画面')
