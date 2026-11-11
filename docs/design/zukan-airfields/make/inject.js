// 図鑑の飛行場・滑空場の画面案：今のアプリ（デモ）の図鑑の上に、入口と別の図鑑を描き足す。アプリのコードは変えない（撮るときにページの中で描くだけ）
(() => {
const KD = { field:["飛行場", "fd"], glider:["滑空場", "gl"] };
const AF = () => XA.filter(a => a.kind === "field" || a.kind === "glider");
const short = a => { const s = a.name.replace(/（.*）/, "").replace(/(滑空場|飛行場|空港)$/, ""); return s || a.name; };
window.ZA_CSS = `
/* 図鑑の最初の画面の入口（上の 16／86 とは別のカード：白地・緑の縁どり・小さな地図） */
#v-book .za-in{display:block;width:100%;margin-top:12px;padding:14px 14px 12px 18px;border:0;border-radius:22px;background:var(--bk-card);box-shadow:var(--bk-shadow);color:var(--bk-ink);font-family:var(--gothic);text-align:left;position:relative;overflow:hidden;cursor:pointer}
#v-book .za-in::before{content:"";position:absolute;left:0;top:14px;bottom:14px;width:5px;border-radius:0 4px 4px 0;background:var(--za-fd)}
#v-book .za-in .h{display:flex;align-items:center;gap:8px}
#v-book .za-in .h .lab{font-size:13px;font-weight:700;color:var(--bk-sub)}
#v-book .za-in .h .gt{margin-left:auto;display:inline-flex;align-items:center;gap:2px;min-height:44px;padding:0 12px 0 14px;margin-right:-4px;margin-top:-10px;margin-bottom:-10px;border-radius:999px;background:var(--za-pill);font-size:14px;font-weight:800;color:var(--bk-ink)}
#v-book .za-in .h .gt svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
#v-book .za-in h3{margin:4px 0 0;font-size:19px;font-weight:800;line-height:1.3;color:var(--bk-ink)}
#v-book .za-in .bd{display:flex;align-items:flex-end;gap:12px;margin-top:6px}
#v-book .za-in .nb{flex:1;min-width:0}
#v-book .za-in .nb .r{display:flex;align-items:baseline;gap:6px}
#v-book .za-in .nb .num{font-family:var(--sign);font-weight:700;font-size:40px;line-height:1;color:var(--bk-ink)}
#v-book .za-in .nb .u{font-size:13px;color:var(--bk-sub);font-weight:600}
#v-book .za-in .nb .ks{display:flex;flex-wrap:wrap;gap:6px 10px;margin-top:10px}
#v-book .za-in .nb .ks span{display:inline-flex;align-items:baseline;gap:5px;font-size:13px;font-weight:700;color:var(--bk-sub)}
#v-book .za-in .nb .ks b{font-family:var(--sign);font-size:17px;color:var(--bk-ink)}
#v-book .za-in .nb .ks small{font-size:12px;color:var(--bk-sub);font-weight:600}
#v-book .za-in .nb .ks i{width:9px;height:9px;border-radius:50%;align-self:center}
#v-book .za-in .nb p{margin:8px 0 0;font-size:13px;color:var(--bk-sub);line-height:1.5}
/* 小さな地図：点は飛行場（緑）と滑空場（空色）。行った所は塗り、まだは輪。灰の小さな点は 86空港（形を見せるだけ） */
#v-book .za-map{position:relative;flex:none;width:136px;height:146px;margin:-8px -2px -2px 0}
#v-book .za-map i{position:absolute;transform:translate(-50%,-50%);border-radius:50%}
#v-book .za-map i.ap{width:3px;height:3px;background:var(--za-ap)}
#v-book .za-map i.x{width:7px;height:7px;box-shadow:inset 0 0 0 1.5px var(--k)}
#v-book .za-map i.x.on{width:10px;height:10px;background:var(--k);box-shadow:0 0 0 2px var(--bk-card)}
/* 種類の札 */
#v-book .za-t{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:999px;font-size:13px;font-weight:800;line-height:1;white-space:nowrap}
#v-book .za-t.fd{background:var(--za-fd-bg);color:var(--za-fd-ink)}#v-book .za-t.gl{background:var(--za-gl-bg);color:var(--za-gl-ink)}#v-book .za-t.hp{background:var(--za-pill);color:var(--bk-sub)}
/* 飛行場・滑空場の図鑑の枠：名前が長いので2行まで。種類の札を名前の下に */
#v-book .zk-ap.za{height:118px}
#v-book .zk-ap.za .cd.jp.lg{font-size:14px;line-height:1.25;-webkit-line-clamp:3}
#v-book .zk-ap.za .cd.jp{font-size:16px;line-height:1.3;white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:0}
#v-book .zk-ap.za .za-t{align-self:flex-start;margin-top:4px}
#v-book .zk-ap.za.no .za-t{opacity:.85}
#v-book .za-kinds{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
#v-book .za-kinds span{display:inline-flex;align-items:baseline;gap:5px;padding:4px 10px;border-radius:999px;background:rgba(255,255,255,.1);font-size:13px;color:#C9D2DE;font-weight:700}
#v-book .za-kinds b{font-family:var(--sign);font-size:16px;color:#fff}#v-book .za-kinds small{font-size:12px;font-weight:600}
#v-book .zk-hero .rg .za0 .t span:last-child{color:#8D9AAB;font-family:var(--gothic);font-size:13px}
#v-book .zk-tsume button.za0{opacity:.45;cursor:default}
#v-book .za-sep{margin:14px 4px 0;font-size:13px;color:var(--bk-sub);line-height:1.6}
#v-book .zk-ttl .zk-pill.zk-back{margin-right:auto}
:root{--za-fd:#3E7D52;--za-gl:#1F7FB6;--za-fd-bg:#DCEBDF;--za-fd-ink:#24502F;--za-gl-bg:#D7EAF6;--za-gl-ink:#134F72;--za-pill:#EEF1F5;--za-ap:#C5CCD6}
/* 夜：会社の色・金は使わない。地方と種類の色をやめ、点と札は灰の濃淡だけ */
:root[data-night="on"]{--za-fd:#AEB9C6;--za-gl:#AEB9C6;--za-fd-bg:#141B24;--za-fd-ink:#BCC6D1;--za-gl-bg:#141B24;--za-gl-ink:#BCC6D1;--za-pill:#141B24;--za-ap:#3A4654}
:root[data-night="on"][data-palette="board"]{--shu:#DCE3EA;--nav-on:#DCE3EA}
:root[data-night="on"] .brand{font-family:var(--gothic);font-weight:800;letter-spacing:.04em;color:#DCE3EA}
:root[data-night="on"] #v-book .za-t{box-shadow:inset 0 0 0 1px rgba(150,170,195,.22)}
:root[data-night="on"] #v-book .za-t.gl{box-shadow:inset 0 0 0 1px rgba(150,170,195,.22),inset 0 0 0 3px #141B24,inset 0 0 0 4px rgba(150,170,195,.0)}
:root[data-night="on"] #v-book .za-in::before{background:rgba(220,227,234,.55)}
:root[data-night="on"] #v-book .za-in .h .gt{box-shadow:inset 0 0 0 1px rgba(220,227,234,.5);color:#DCE3EA}
:root[data-night="on"] #v-book .za-map i.x.on{background:#DCE3EA}
:root[data-night="on"] #v-book .za-map i.x{--k:#AEB9C6}
`;
const CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>';
function counts(){
  const xv = visitedExtra(), l = AF();
  const g = k => [l.filter(a => a.kind === k && xv.has(a.id)).length, l.filter(a => a.kind === k).length];
  return { xv, all:[l.filter(a => xv.has(a.id)).length, l.length], fd:g("field"), gl:g("glider") };
}
function miniMap(xv, night){
  const ap = A.map(a => { const [x, y] = bkXY(a); return `<i class="ap" style="left:${x}%;top:${y}%"></i>`; }).join("");
  const xs = AF().map(a => { const [x, y] = bkXY(a), on = xv.has(a.id); return `<i class="x${on ? " on" : ""}" style="left:${x}%;top:${y}%;--k:var(--za-${KD[a.kind][1]})"></i>`; }).join("");
  return `<span class="za-map" aria-hidden="true">${ap}${xs}</span>`;
}
// 02：図鑑の最初の画面に入口
window.zaEntry = () => {
  const c = counts();
  const card = `<button class="za-in" type="button" data-zkseg="air" aria-label="飛行場・滑空場の図鑑、${c.all[1]}のうち${c.all[0]}。86空港の数には入りません">
    <span class="h"><span class="lab">もう1つの図鑑</span><span class="gt">開く${CHEV}</span></span>
    <h3>飛行場・滑空場</h3>
    <span class="bd"><span class="nb"><span class="r"><b class="num">${c.all[0]}</b><span class="u">/ ${c.all[1]}</span></span>
      <span class="ks"><span><i style="background:var(--za-fd)"></i>飛行場 <b>${c.fd[0]}</b><small>/${c.fd[1]}</small></span><span><i style="background:var(--za-gl)"></i>滑空場 <b>${c.gl[0]}</b><small>/${c.gl[1]}</small></span></span>
      <p>上の「集めた空港」とは別に数えます</p></span>${miniMap(c.xv)}</span></button>`;
  document.querySelector("#zkBody .zk-hero").insertAdjacentHTML("afterend", card);
};
// 03：飛行場・滑空場の図鑑（86空港の図鑑と同じ「ツメ＋地方の扉＋そろえた枠」）
window.zaBook = () => {
  const c = counts(), vc = new Map(); for(const ck of S.checkins) if(IS_EXTRA(ck.a)) vc.set(ck.a, (vc.get(ck.a) || 0) + 1);
  const rgs = REGION.map(([rg, prefs]) => { const list = AF().filter(a => prefs.includes(a.pref)).sort((x, y) => y.lat - x.lat); return { rg, list, got:list.filter(a => c.xv.has(a.id)).length }; });
  const hero = `<div class="zk-hero"><div class="ht"><span class="lab">集めた飛行場・滑空場</span><b class="num">${c.all[0]}</b><span class="u">/ ${c.all[1]}</span><span class="side">まだ ${c.all[1] - c.all[0]}</span></div>
    <div class="rg">${rgs.map(r => r.list.length ? `<div><span class="t"><span>${r.rg}</span><span>${r.got}<small>/${r.list.length}</small></span></span><span class="b"><i style="width:${Math.round(r.got / r.list.length * 100)}%;background:${zkCol(r.rg)}"></i></span></div>`
      : `<div class="za0"><span class="t"><span>${r.rg}</span><span>なし</span></span><span class="b"></span></div>`).join("")}</div>
    <div class="za-kinds"><span>飛行場 <b>${c.fd[0]}</b><small>/${c.fd[1]}</small></span><span>滑空場 <b>${c.gl[0]}</b><small>/${c.gl[1]}</small></span></div></div>`;
  const tile = a => { const on = c.xv.has(a.id), n = vc.get(a.id) || 0, [kl, kc] = KD[a.kind];
    return `<button class="zk-ap za${on ? "" : " no"}" type="button" style="--c:${zkCol(regionOf(a))}" aria-label="${esc(a.name)}、${kl}、${on ? n + "回" : "まだ"}"><span class="cd jp${short(a).length > 7 ? " lg" : ""}">${esc(short(a))}</span><span class="za-t ${kc}">${kl}</span><span class="ft">${on ? `<svg class="zk-stp" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="11.5"/><path d="m8 13.5 3.3 3.3L18.5 9"/></svg><b>${n}</b>回` : `<svg class="zk-stp no" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="11.5"/></svg>まだ`}</span></button>`; };
  const body = rgs.filter(r => r.list.length).map(r => `<section class="zk-rg" id="zarg-${r.rg}" data-rg="${r.rg}" style="--c:${zkCol(r.rg)}">
    <div class="zk-door"><h3>${r.rg}</h3><b class="num">${r.got}</b><span class="u">/ ${r.list.length}</span><span class="bar"><i style="width:${Math.round(r.got / r.list.length * 100)}%"></i></span><button class="zk-up" type="button" aria-label="図鑑の上へ"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 14l6-6 6 6"/></svg></button></div>
    <div class="zk-grid">${r.list.map(tile).join("")}</div></section>`).join("");
  const tsume = `<nav class="zk-tsume" aria-label="地方へ飛ぶ">${rgs.map(r => `<button type="button" class="${r.list.length ? "" : "za0"}${r.rg === window.ZA_ON ? " on" : ""}" style="--c:${zkCol(r.rg)}" aria-label="${r.rg}へ${r.list.length ? "" : "（なし）"}"${r.list.length ? "" : " disabled"}><span>${r.rg}</span></button>`).join("")}</nav>`;
  const bm = document.getElementById("bookMain");
  bm.querySelector(".zk-ttl").innerHTML = `<button class="zk-pill zk-back" type="button" data-zkseg="main"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>図鑑</button>`;
  bm.querySelector(".zk-ttl").insertAdjacentHTML("afterend", `<div class="book-head"><h2>飛行場・滑空場</h2></div>`);
  const vw = bm.querySelector(".vwrow"); if(vw) vw.remove();
  document.getElementById("zkBody").innerHTML = `<div class="zk-main"><p class="zk-lead">定期便のない飛行場と、グライダーの滑空場。ここで集めても「集めた空港（86）」の数は変わりません。自衛隊の飛行場は「番外編」にあります。</p>${hero}${body}<p class="zk-foot"><button class="zk-link" type="button">記号の意味</button></p></div>${tsume}`;
};
})();
// 夜の下のタブ：選んだタブの字と点を白に（琥珀は「いま・次」だけ）
window.ZA_CSS += `:root[data-night="on"] nav.tabs button[aria-current="page"],:root[data-night="on"] nav.tabs button[aria-current="page"] *{color:#DCE3EA!important}
:root[data-night="on"] nav.tabs button[aria-current="page"]::before,:root[data-night="on"] nav.tabs button[aria-current="page"]::after{background:#DCE3EA!important}`;
