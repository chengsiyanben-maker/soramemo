/* マイページを「タイル」にした画面案。今のアプリのデモでマイページを開き、#dSettings .dlg の中を描き直す。
   アプリのコードは変えない（画面案を作るときだけ読み込む）。数字はデモの記録から、車などを外して数える（report-sweep-all-a の1番） */
const MT_CSS = `
dialog.mypage .mt-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0 0}
dialog.mypage .mt{position:relative;display:flex;flex-direction:column;align-items:flex-start;justify-content:space-between;min-height:112px;padding:14px 16px 13px;border:0;border-radius:22px;background:var(--mp-card);box-shadow:var(--mp-shadow);text-align:left;font-family:var(--gothic);color:var(--mp-ink);cursor:pointer}
dialog.mypage .mt .k{font-size:13px;font-weight:700;color:#6B7280;letter-spacing:.04em}
dialog.mypage .mt .go{position:absolute;top:12px;right:14px;width:16px;height:16px;fill:none;stroke:#9CA3AF;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
dialog.mypage .mt .v{display:flex;align-items:baseline;gap:3px;margin-top:10px;line-height:1.15}
dialog.mypage .mt .v b{font-size:30px;font-weight:800;letter-spacing:-.01em;font-variant-numeric:tabular-nums}
dialog.mypage .mt .v .u{font-size:13px;font-weight:700;color:#6B7280}
dialog.mypage .mt .s{display:block;font-size:12px;color:#6B7280;margin-top:7px;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
dialog.mypage .mt-sec .seg button{min-height:44px}dialog.mypage .mt-sec .swatch{min-width:44px}
dialog.mypage .mt .dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:1px}
dialog.mypage .mt.wide{grid-column:1/-1;min-height:0}
dialog.mypage .mt.wide .s{white-space:normal}
dialog.mypage .mt.wide .row3{display:grid;grid-template-columns:1fr 1fr 1.35fr;gap:8px;width:100%;margin-top:10px}
dialog.mypage .mt.wide .row3 .v{margin-top:0}
dialog.mypage .mt.wide .row3 small{display:block;font-size:12px;color:#6B7280;margin-top:5px}
dialog.mypage .mt .bar{width:100%;height:6px;border-radius:999px;background:#EEF0F3;margin-top:9px;overflow:hidden}
dialog.mypage .mt .bar i{display:block;height:100%;border-radius:999px;background:var(--ana)}
dialog.mypage .mt-note{display:block;font-size:12px;color:#5F6672;margin:10px 4px 0;line-height:1.5}
dialog.mypage .mt-sec{margin:12px 0 0;background:var(--mp-card);border-radius:22px;padding:14px 16px 10px;box-shadow:var(--mp-shadow)}
dialog.mypage .mt-sec h4{font-size:13px;font-weight:700;color:#6B7280;letter-spacing:.06em;margin:0 0 4px}
dialog.mypage .mt-sec .lead{font-size:12.5px;color:#6B7280;margin:0 0 6px;line-height:1.5}
dialog.mypage .mt-sec .set-row small{color:#6B7280;font-size:12px}
dialog.mypage .mt-h{font-size:13px;font-weight:700;color:#5F6672;letter-spacing:.06em;margin:22px 4px 0}
dialog.mypage .mt-mini{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:4px 0 4px}
dialog.mypage .mt-mini button{display:flex;flex-direction:column;align-items:flex-start;gap:6px;min-height:76px;padding:12px;border:0;border-radius:18px;background:#F3F4F6;color:var(--mp-ink);font-family:var(--gothic);text-align:left}
dialog.mypage .mt-mini button span{font-size:12.5px;font-weight:700;color:#4B5563;line-height:1.3}
dialog.mypage .mt-mini button b{font-size:22px;font-weight:800;line-height:1}dialog.mypage .mt-mini button b small{font-size:12px;color:#5F6672;font-weight:700}
dialog.mypage .mt-menu{list-style:none;margin:0;padding:0}
dialog.mypage .mt-menu button{display:flex;align-items:center;gap:12px;width:100%;min-height:58px;padding:8px 2px;border:0;background:none;font-family:var(--gothic);color:var(--mp-ink);text-align:left}
dialog.mypage .mt-menu .ic{flex:none;width:36px;height:36px;border-radius:12px;background:#F3F4F6;display:grid;place-items:center}
dialog.mypage .mt-menu .ic svg{width:18px;height:18px;fill:none;stroke:#4B5563;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
dialog.mypage .mt-menu .t{flex:1;min-width:0}
dialog.mypage .mt-menu .t b{display:block;font-size:15px;font-weight:700}
dialog.mypage .mt-menu .t small{display:block;font-size:12px;color:#6B7280;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
dialog.mypage .mt-menu .ch{flex:none;width:16px;height:16px;fill:none;stroke:#9CA3AF;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
dialog.mypage .mt-menu li+li{box-shadow:0 -1px 0 #F1F2F4}
dialog.mypage .mt-sub .mp-top{margin-bottom:6px}dialog.mypage .mt-sub .mp-back{white-space:nowrap}dialog.mypage .mt-sub .mp-top h3{font-size:16px;white-space:nowrap}dialog.mypage .mt-sub .mp-sp{width:24px}
dialog.mypage .mt-bk{display:flex;gap:12px;align-items:flex-start;background:#F3F7FB;border-radius:18px;padding:14px;margin:4px 0 8px}
dialog.mypage .mt-bk svg{flex:none;width:22px;height:22px;fill:none;stroke:#2563EB;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;margin-top:2px}
dialog.mypage .mt-bk b{display:block;font-size:14px;font-weight:800;color:var(--mp-ink)}
dialog.mypage .mt-bk small{display:block;font-size:12.5px;color:#4B5563;line-height:1.55;margin-top:3px}
dialog.mypage .mt-exp{display:flex;gap:8px}
dialog.mypage .mt-sec .btn2,dialog.mypage .mt-exp .btn2{min-height:44px}
dialog.mypage .mt-pend{display:table;font-size:12px;font-weight:700;color:#92400E;background:#FEF3C7;border-radius:999px;padding:2px 9px;margin-left:6px;vertical-align:1px}
`;
const MT_GO = '<svg class="go" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
const MT_CH = '<svg class="ch" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';
const MT_IC = {
  eye: '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6S2 12 2 12z"/><circle cx="12" cy="12" r="2.6"/>',
  box: '<path d="M4 7l8-4 8 4v10l-8 4-8-4z"/><path d="M4 7l8 4 8-4M12 11v10"/>',
  pal: '<circle cx="12" cy="12" r="9"/><circle cx="8" cy="10" r="1.2"/><circle cx="12" cy="7.5" r="1.2"/><circle cx="16" cy="10" r="1.2"/><path d="M12 21a2.5 2.5 0 0 1 0-5h2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
  doc: '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
  sh: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>'
};
const mtIc = k => `<span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">${MT_IC[k]}</svg></span>`;

// デモの数字（車などを外す）
function mtNums(){
  const car = f => f.airline === "CAR" || f.mode === "car" || f.car || (typeof isCar === "function" && isCar(f));
  let fl = S.flights.filter(f => !car(f));
  if(fl.length === S.flights.length){ // 車などの印が見つからないときは、デモの長崎→福岡（約90km）を外す
    const i = S.flights.findIndex(f => Math.round(f.km) >= 85 && Math.round(f.km) <= 95); if(i >= 0) fl = S.flights.filter((_, j) => j !== i);
  }
  const carN = S.flights.length - fl.length, carKm = Math.round(S.flights.reduce((s, f) => s + (f.km || 0), 0) - fl.reduce((s, f) => s + (f.km || 0), 0));
  return { ap: visited().size, all: 86, fl: fl.length, km: Math.round(fl.reduce((s, f) => s + (f.km || 0), 0)), carN, carKm, routes: new Set(fl.map(f => [f.from, f.to].sort().join("-"))).size };
}
const n3 = x => x.toLocaleString("ja-JP");

function mtTop(){ // 頭（戻る・題・名前のカード）は今のまま。数の札は下のタイルへ移す
  const top = document.querySelector("#dSettings .mp-top").outerHTML, prof = document.querySelector("#mpProf");
  prof.querySelectorAll(".mp-chip").forEach(c => { if(/空港・/.test(c.textContent)) c.remove(); });
  return top + prof.outerHTML;
}
function tile(k, v, u, s, extra){ return `<button class="mt" type="button"><span class="k">${k}</span>${MT_GO}<span class="v"><b>${v}</b><span class="u">${u}</span></span>${extra || ""}<span class="s">${s}</span></button>`; }

function tilesA(n){
  return `<div class="mt-grid">
    ${tile("成績", n3(n.km), "km", `${n.ap}空港・${n.fl}フライト`)}
    ${tile("図鑑", n.ap, `/ ${n.all}`, `まだ ${n.all - n.ap} 空港`)}
    ${tile("フライト", n.fl, "便", `車など ${n.carN} は別に数える`)}
    ${tile("修行", "11,028", "PP", '<span class="dot" style="background:var(--ana)"></span>ブロンズまで 36%')}
    ${tile("運用", "南風", "", "羽田　22・23 から出発")}
    ${tile("知らせ", 0, "/ 12 空港", "ピン止めした空港")}
  </div>`;
}
function tilesB(n){
  return `<div class="mt-grid">
    <button class="mt wide" type="button"><span class="k">成績</span>${MT_GO}
      <span class="row3"><span><span class="v"><b>${n.ap}</b><span class="u">空港</span></span><small>図鑑 ${n.ap}/${n.all}</small></span>
      <span><span class="v"><b>${n.fl}</b><span class="u">便</span></span><small>${n.routes}路線</small></span>
      <span><span class="v"><b>${n3(n.km)}</b><span class="u">km</span></span><small>飛んだ距離</small></span></span>
      <span class="s">車など ${n.carN}（${n.carKm} km）は便と距離に入れず、別に数えています</span></button>
    ${tile("修行", "11,028", "PP", "ブロンズまで 36%", '<span class="bar"><i style="width:36%"></i></span>')}
    ${tile("知らせ", 0, "/ 12 空港", "ピン止めした空港")}
  </div>
  <p class="mt-note">図鑑・フライト・運用は下のタブ帯から。タブから外した画面は、ここにタイルが増えます。</p>`;
}

function secLayout(){
  const t = document.getElementById("tpTileN").innerHTML, h = document.getElementById("heTileN").innerHTML, l = document.getElementById("loTileN").innerHTML;
  return `<section class="mt-sec"><h4>表示の編集</h4><p class="lead">見たいものだけにできます。隠しても記録や機能は消えません。</p>
    <div class="mt-mini"><button type="button"><span>タブを選ぶ</span><b>${t}</b></button><button type="button"><span>ホームに<br>出すもの</span><b>${h}</b></button><button type="button"><span>全部を<br>見直す</span><b>${l}</b></button></div></section>`;
}
function secData(pend, sub){
  return `<section class="mt-sec">${sub ? "" : "<h4>データとバックアップ</h4>"}
    <div class="mt-bk"><svg viewBox="0 0 24 24" aria-hidden="true">${MT_IC.sh}</svg><span>${pend ? '<span class="mt-pend" style="margin:0 0 6px">この文は PM が決める（見直し A の2番）</span>' : ""}<b>記録はサーバーに保存されています</b><small>機種を変えても、同じメールアドレスでログインすれば戻ります。バックアップは無料です。</small></span></div>
    <div class="set-row"><div>記録を書き出す<small>手元の控えです。チェックイン・フライト・記録帳・国際線（無料）</small></div><div class="mt-exp"><button class="btn2">JSON</button><button class="btn2">CSV</button></div></div>
    <div class="set-row"><div>記録を消す<small>この端末に保存した本番の記録をすべて消します。</small></div><button class="btn2 danger">消す</button></div></section>`;
}
function secSettings(){
  // 今の「アカウント」「表示」「詳しい設定」の行をそのまま1枚の「設定」に入れる（補足の字は濃くする）
  const pick = id => { const s = document.querySelector(`#dSettings [aria-labelledby="${id}"]`); if(!s) return ""; const c = s.cloneNode(true); c.querySelector("h4")?.remove(); c.querySelectorAll("[hidden]").forEach(e => e.remove()); return c.innerHTML; };
  const ac = pick("mpAcct"); return `${/set-row/.test(ac) ? `<section class="mt-sec"><h4>アカウント</h4>${ac}</section>` : ""}
    <section class="mt-sec"><h4>表示と色</h4>${pick("mpShow").replace(/<div class="set-row" id="gameRow">[\s\S]*?<\/button><\/div>/, "")}</section>
    <section class="mt-sec"><h4>詳しい設定</h4>${pick("mpAdv")}</section>`;
}
function tail(){ return [...document.querySelectorAll("#dSettings .legal, #dSettings .appver")].map(e => e.outerHTML).join(""); }

function menuB(){
  const row = (ic, t, s) => `<li><button type="button">${mtIc(ic)}<span class="t"><b>${t}</b><small>${s}</small></span>${MT_CH}</button></li>`;
  const c = loCount();
  return `<h4 class="mt-h">設定</h4><section class="mt-sec" style="padding:4px 14px"><ul class="mt-menu">
    ${row("eye", "表示の編集", `タブ ${loTabs().length}/5・出しているもの ${c.on}/${c.all}`)}
    ${row("sh", "データとバックアップ", "記録はサーバーに保存・書き出し（無料）")}
    ${row("pal", "表示と色", "ノーマル・白黒・拠点 羽田")}
    ${row("user", "アカウント", demo ? "デモモード（記録は別）" : "ログイン")}
    ${row("gear", "詳しい設定", "デモ・判定のしくみ・ホーム画面に追加 ほか")}
  </ul></section>`;
}

function mtRender(o){
  if(!document.getElementById("mtCss")){ const s = document.createElement("style"); s.id = "mtCss"; s.textContent = MT_CSS; document.head.appendChild(s); }
  const n = mtNums(), d = document.querySelector("#dSettings .dlg");
  if(o.v === "A") d.innerHTML = mtTop() + tilesA(n) + secLayout() + secData(true) + secSettings() + tail();
  else if(o.v === "B") d.innerHTML = mtTop() + tilesB(n) + menuB() + tail();
  else if(o.v === "Bsub"){
    const back = `<div class="mp-top"><button class="mp-back" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>マイページ</button><h3>データとバックアップ</h3><span class="mp-sp" aria-hidden="true"></span></div>`;
    d.innerHTML = back + secData(true, true) + `<p class="mt-note">「設定」のほかの行（表示の編集・表示と色・アカウント・詳しい設定）も、同じ形の1枚のページで開きます。中の行は今のまま。</p>`;
    d.classList.add("mt-sub");
  }
  document.activeElement && document.activeElement.blur();
  return n;
}
