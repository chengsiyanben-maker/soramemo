/* 見本の動かし方：?n=1 夜／?rm=1 動きを減らす／?t=0.5 その時刻で止める（撮影用） */
(function(){
  const q = new URLSearchParams(location.search), R = document.documentElement;
  if(q.get('n') === '1') R.dataset.night = 'on';
  if(q.get('rm') === '1') R.classList.add('rm');
  const ph = document.querySelector('.phone');
  // 半券の切り欠き：印の場所と数字の間（数字のかたまりの少し上）
  function notch(){ const sc = document.querySelector('.sc'), mx = document.querySelector('.mx'); if(sc && mx) sc.style.setProperty('--ny', (mx.offsetTop - 11) + 'px'); }
  function play(){ if(!ph) return; ph.classList.remove('go', 'closing', 'closed'); void ph.offsetWidth; ph.classList.add('go'); }
  function close(){ if(!ph || ph.classList.contains('closed')) return; ph.classList.remove('go'); ph.classList.add('closing');
    setTimeout(() => { ph.classList.remove('closing'); ph.classList.add('closed'); }, R.classList.contains('rm') || matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 160); }
  window.play = play; window.closeCard = close;
  window.__freeze = function(t){ play(); document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; }); };
  addEventListener('load', () => {
    notch();
    const t = q.get('t');
    if(t != null) window.__freeze(parseFloat(t)); else play();
  });
  addEventListener('resize', notch);
  document.addEventListener('click', e => {
    if(e.target.closest('.x') || e.target.classList.contains('scrim')) close();
    if(e.target.closest('.replay')) play();
  });
  // 下へなでて閉じる（見本は 60px 以上で閉じる）
  let y0 = null;
  document.addEventListener('pointerdown', e => { if(e.target.closest('.grab, .top')) y0 = e.clientY; });
  document.addEventListener('pointerup', e => { if(y0 != null && e.clientY - y0 > 60) close(); y0 = null; });
})();
