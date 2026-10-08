// テスト用の偽 Turnstile：描画するとすぐに合図（トークン）を返す
(function(){ let n = 0; const cbs = {};
  window.turnstile = { render(sel, o){ const id = 'w' + (++n); cbs[id] = o; window.__tsOpts = o; setTimeout(() => o.callback('tok-' + n), 50); return id; },
                       reset(id){ window.__tsReset = (window.__tsReset || 0) + 1; const o = cbs[id]; if(o) setTimeout(() => o.callback('tok-r' + window.__tsReset), 50); } };
})();
