/* そらメモ 小さな動きの見本：共通の動き。どれも 0.15〜0.4 秒。動きを減らす設定では状態だけ変える */
(function(){
const R = document.documentElement;
const q = new URLSearchParams(location.search);
if (q.get('night') === '1') R.dataset.night = 'on';
if (q.get('rm') === '1') R.classList.add('rm');
const reduced = () => R.classList.contains('rm') || matchMedia('(prefers-reduced-motion: reduce)').matches;
window.SM = {reduced};

/* M05 下から出る札。いちばん近い [data-toast-host] の中に出す。2 秒で下がる */
function toast(from, msg){
  const host = (from && from.closest && from.closest('[data-toast-host]')) || document.querySelector('[data-toast-host]') || document.body;
  let t = host.querySelector(':scope > .toast');
  if (!t){ t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role','status'); host.appendChild(t); }
  t.innerHTML = '<svg class="ic" viewBox="0 0 24 24"><path d="M5 12.5l4.2 4L19 7"/></svg><span></span>';
  t.querySelector('span').textContent = msg;
  t.classList.remove('show'); void t.offsetWidth; t.classList.add('show');
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 2000);
}
SM.toast = toast;

/* M02 タブの点：押したタブの下へすべる */
function placeDot(nav){
  const cur = nav.querySelector('[aria-current=page]'), dot = nav.querySelector('.dot');
  if (!cur || !dot) return;
  const x = cur.offsetLeft + cur.offsetWidth / 2 - 2.5;
  dot.style.transform = 'translateX(' + x + 'px)';
}
document.querySelectorAll('.tabs').forEach(nav => {
  placeDot(nav);
  nav.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    nav.querySelectorAll('button').forEach(x => x.removeAttribute('aria-current'));
    b.setAttribute('aria-current', 'page'); placeDot(nav);
  });
});
addEventListener('resize', () => document.querySelectorAll('.tabs').forEach(placeDot));

/* M03 ON／OFF */
document.addEventListener('click', e => {
  const s = e.target.closest('.sw[role=switch]'); if (!s) return;
  const on = s.getAttribute('aria-checked') !== 'true';
  s.setAttribute('aria-checked', on); const lb = s.querySelector('.lb'); if (lb) lb.textContent = on ? 'ON' : 'OFF';
});

/* M04 ピン止め */
document.addEventListener('click', e => {
  const p = e.target.closest('.pinbtn'); if (!p) return;
  const on = !p.classList.contains('on');
  p.classList.toggle('on', on); p.classList.remove('go'); void p.offsetWidth; if (on) p.classList.add('go');
  p.setAttribute('aria-pressed', on);
  p.querySelector('span').textContent = on ? 'ピン止め中' : 'ピン止め';
  if (p.dataset.toast !== 'no') toast(p, on ? 'ピン止めしました' : 'ピン止めを外しました');
});

/* M10 コピー */
document.addEventListener('click', e => {
  const c = e.target.closest('.copy'); if (!c) return;
  try { navigator.clipboard && navigator.clipboard.writeText(c.dataset.copy || '').catch(() => {}); } catch(_){}
  c.classList.add('done'); c.setAttribute('aria-label', 'コピーしました');
  clearTimeout(c._h); c._h = setTimeout(() => { c.classList.remove('done'); c.setAttribute('aria-label', 'コピー'); }, 1500);
  if (c.dataset.toast !== 'no') toast(c, 'コピーしました');
});

/* M11 知らせの鈴 */
document.addEventListener('click', e => {
  const b = e.target.closest('.bell'); if (!b) return;
  const on = b.getAttribute('aria-pressed') !== 'true';
  b.setAttribute('aria-pressed', on); b.classList.remove('go'); void b.offsetWidth; if (on) b.classList.add('go');
  const t = b.querySelector('span'); if (t) t.textContent = on ? '知らせ ON' : '知らせ OFF';
  toast(b, on ? '羽田の知らせを受け取ります' : '羽田の知らせを止めました');
});

/* M12 もう一度 */
document.addEventListener('click', e => {
  const r = e.target.closest('.retry'); if (!r) return;
  const box = r.closest('[data-retry-box]');
  r.classList.remove('go'); void r.offsetWidth; r.classList.add('go');
  if (box){
    box.querySelector('[data-st]').textContent = '読み込み中…';
    setTimeout(() => { box.dataset.ok = '1'; box.querySelector('[data-st]').textContent = '読めました・最後に読んだ 14時32分'; }, reduced() ? 300 : 600);
  }
});

/* M13 シート */
document.addEventListener('click', e => {
  const o = e.target.closest('[data-sheet-open]');
  if (o){ document.getElementById(o.dataset.sheetOpen).classList.add('open'); return; }
  const c = e.target.closest('[data-sheet-close]');
  if (c){ c.closest('.sheetwrap').classList.remove('open'); }
});

/* M07 数字の繰り上がり：<span class="roll" data-v="16"></span> */
function rollSet(el, v){
  el.innerHTML = '<span class="col"><span>' + v + '</span></span>'; el.dataset.v = v; el.classList.remove('up');
}
function rollTo(el, v){
  const old = el.dataset.v;
  el.innerHTML = '<span class="col"><span>' + old + '</span><span>' + v + '</span></span>';
  el.classList.remove('up'); void el.offsetWidth; el.classList.add('up'); el.dataset.v = v;
  el.setAttribute('aria-label', v);
}
document.querySelectorAll('.roll').forEach(el => rollSet(el, el.dataset.v));
SM.rollTo = rollTo; SM.rollSet = rollSet;

/* M08 数え上げ（0.4 秒）。止めた動きで撮れるように、時間は Web Animations の currentTime から読む */
function countUp(el, to, ms){
  ms = ms || 400; const from = +(el.dataset.from || 0);
  const fmt = n => Math.round(n).toLocaleString('ja-JP');
  if (reduced()){ el.textContent = fmt(to); return; }
  const a = el.animate([{opacity:1},{opacity:1}], {duration: ms, fill: 'none'});
  const ease = t => 1 - Math.pow(1 - t, 3);
  (function f(){
    const t = Math.min(1, (a.currentTime || 0) / ms);
    el.textContent = fmt(from + (to - from) * ease(a.playState === 'finished' ? 1 : t));
    if (a.playState !== 'finished') requestAnimationFrame(f);
  })();
}
SM.countUp = countUp;
function grow(bar, pct){ const i = bar.querySelector('i'); i.style.transition = 'none'; i.style.width = '0%'; void i.offsetWidth; i.style.transition = ''; void i.offsetWidth; i.style.width = pct + '%'; }
SM.grow = grow;

/* M06 骨組み：300ms より早く読めたら骨組みは出さない。見本では 1.2 秒かかる読み込み */
function loadInto(box, ms){
  const sk = box.querySelector('[data-skel]'), real = box.querySelector('[data-real]');
  real.hidden = true; sk.hidden = true;
  const t300 = setTimeout(() => { sk.hidden = false; }, 300);
  setTimeout(() => { clearTimeout(t300); sk.hidden = true; real.hidden = false; real.classList.remove('fadein'); void real.offsetWidth; real.classList.add('fadein'); }, ms || 1500);
}
SM.loadInto = loadInto;

/* M09 並べ替え：つまみを押さえて上下に。ほかの行はすっと場所をあける */
document.querySelectorAll('.sortlist').forEach(list => {
  let row = null, y0 = 0, rows = [], idx = 0, step = 0, to = 0;
  const gap = 10;
  list.addEventListener('pointerdown', e => {
    const g = e.target.closest('.grip'); if (!g) return;
    row = g.closest('.srow'); rows = [...list.querySelectorAll('.srow')]; idx = rows.indexOf(row); to = idx;
    step = row.offsetHeight + gap; y0 = e.clientY; row.classList.add('lift'); g.setPointerCapture(e.pointerId); e.preventDefault();
  });
  list.addEventListener('pointermove', e => {
    if (!row) return; const dy = e.clientY - y0;
    row.style.transform = 'translateY(' + dy + 'px) scale(1.02)';
    to = Math.max(0, Math.min(rows.length - 1, idx + Math.round(dy / step)));
    rows.forEach((r, i) => { if (r === row) return;
      let s = 0; if (to > idx && i > idx && i <= to) s = -step; if (to < idx && i < idx && i >= to) s = step;
      r.style.transform = s ? 'translateY(' + s + 'px)' : ''; });
  });
  const end = () => {
    if (!row) return; const r0 = row; row = null;
    rows.forEach(r => { r.style.transition = 'none'; r.style.transform = ''; });
    r0.classList.remove('lift');
    const ref = rows[to]; if (to > idx) ref.after(r0); else if (to < idx) ref.before(r0);
    void list.offsetWidth; rows.forEach(r => r.style.transition = '');
    if (to !== idx) toast(list, '並びを保存しました');
  };
  list.addEventListener('pointerup', end); list.addEventListener('pointercancel', end);
});
/* 撮影や「試す」のための、並べ替えの自動の見本 */
SM.sortDemo = function(list, phase){
  const rows = [...list.querySelectorAll('.srow')]; const r = rows[2], step = r.offsetHeight + 10;
  rows.forEach(x => { x.style.transform = ''; x.classList.remove('lift'); });
  if (phase >= 1){ r.classList.add('lift'); }
  if (phase >= 2){ r.style.transform = 'translateY(' + (-step) + 'px) scale(1.02)'; rows[1].style.transform = 'translateY(' + step + 'px)'; }
};

/* M01 押す縮み：撮影用にクラスでも */
SM.press = el => { el.classList.add('is-down'); setTimeout(() => el.classList.remove('is-down'), 160); };

/* 撮影用：動いているものをすべて止めて、t ミリ秒の所にする */
window.__freeze = function(t){ document.getAnimations().forEach(a => { a.pause(); try { a.currentTime = t; } catch(_){} }); };
})();
