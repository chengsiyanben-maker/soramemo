// 飛行場・滑空場・ヘリポートの図鑑に「種類の絞り込み」と「県名」を足した画面案（1版）。
// 今のアプリ（デモ）の #bookAir の上に描き足すだけ。アプリのコードは変えない（撮るときにページの中で描く）。
// 使う部品は今のアプリのもの（zkxCounts・zkxTile・zkCol・regionOf・REGION・ZK_BACK_MAIN・ZKX_TITLE_BR・XKIND・ZKX_COL）
(() => {
const LAB = { all:"すべて", field:"飛行場", glider:"滑空場", heli:"ヘリポート", mil:"基地" };
const COL = Object.assign({ mil:"#2E4A6B" }, ZKX_COL);
window.ZF_CSS = `
/* 絞り込み：ピルの溝に4つ（基地を足す案は5つ・横に送る）。選んだものは白い面＋薄い影（上の「スタンプラリー｜エアライン経営」と同じ形） */
#v-book .zf-seg{display:flex;gap:2px;margin:2px 0 12px;padding:3px;border-radius:999px;background:var(--zf-track,#E4E8EE)}
#v-book .zf-seg button{flex:1 1 0;min-width:0;min-height:48px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0;padding:2px 2px;border:0;border-radius:999px;background:none;color:var(--bk-sub);font:700 13px/1.2 var(--gothic);white-space:nowrap;cursor:pointer}
#v-book .zf-seg button .u{font:600 12px/1.2 var(--gothic);color:var(--bk-sub);opacity:.9}
#v-book .zf-seg button[aria-pressed="true"]{background:var(--bk-card);color:var(--bk-ink);font-weight:800;box-shadow:0 2px 8px -3px rgba(15,23,42,.28)}
#v-book .zf-seg.scroll{overflow-x:auto;scrollbar-width:none}
#v-book .zf-seg.scroll::-webkit-scrollbar{display:none}
#v-book .zf-seg.scroll button{flex:0 0 auto;padding:2px 11px}
#v-book .zx-k.mil{background:#E3E8EF;color:#2E4A6B}
#v-book .zf-seg i.k{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;vertical-align:1px}
/* 県名：名前のすぐ下に小さく薄いグレー。取っていない所も出す */
#v-book .zx-ap .zf-pf{font-size:13px;font-weight:600;line-height:1.2;color:var(--bk-sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#v-book .zx-ap.no .zf-pf{color:var(--bk-sub)}
#v-book .zf-one .zx-ap .zx-k{display:none}
/* 1つの種類に絞ったとき、扉の札はその名前だけ */
#v-book .zk-door .zf-dt{flex:none;margin-left:auto;display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:999px;background:var(--bk-card);box-shadow:inset 0 0 0 1.5px var(--zf-line,#C9D0D9);font-size:13px;font-weight:800;color:var(--bk-ink);white-space:nowrap}
/* 黒いカードの頭：絞ったら「ヘリポート 1／12」 */
#v-book .zx-hero .ht .lab i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:1px}
/* 地図の見方：絞った種類の点だけ。まだ＝灰の輪、行った＝色の丸と名前 */
#v-book .zf-map{position:relative;margin-top:12px;padding:12px 12px 10px;border-radius:22px;background:var(--bk-card);box-shadow:var(--bk-shadow)}
#v-book .zf-map svg{display:block;width:100%;height:auto;max-height:340px}
#v-book .zk-door .zf-sp{margin-left:auto}
#v-book .zf-map .m86{fill:#DDE2E8}
#v-book .zf-map .my{fill:#fff;stroke:#9AA4B1;stroke-width:1.6}
#v-book .zf-map .mv{stroke:#fff;stroke-width:2}
#v-book .zf-map text{font:700 16px var(--gothic);fill:var(--bk-ink);paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}
#v-book .zf-map text.p{font-weight:600;fill:var(--bk-sub)}
#v-book .zf-lg{display:flex;gap:14px;margin:6px 4px 0;font-size:13px;font-weight:600;color:var(--bk-sub)}
#v-book .zf-lg i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:0}
#v-book .zf-lg i.y{background:#fff;box-shadow:inset 0 0 0 1.6px #9AA4B1}
#v-book .zf-map .src{position:absolute;right:14px;bottom:10px;font-size:12px;color:var(--bk-sub)}
#v-book .zf-list{margin-top:12px}
:root[data-bookseg="air"] #bookAir .zf-wide{margin-right:0}
#bookAir .zk-main .vwrow{margin-top:4px}
#v-book .zf-list h4{margin:14px 4px 6px;font-size:13px;font-weight:800;color:var(--bk-sub)}
#v-book .zf-list .r{display:flex;align-items:center;gap:10px;min-height:48px;padding:0 14px;margin-top:6px;border-radius:16px;background:var(--bk-card);box-shadow:var(--bk-shadow)}
#v-book .zf-list .r b{font-size:15px;font-weight:800;color:var(--bk-ink)}#v-book .zf-list .r.no b{color:var(--zk-pale)}
#v-book .zf-list .r .pf{margin-left:auto;font-size:13px;color:var(--bk-sub);font-weight:600}
#v-book .zf-list .r i{width:10px;height:10px;border-radius:50%;flex:none}
#v-book .zf-list .r.no i{background:#fff;box-shadow:inset 0 0 0 1.6px #9AA4B1}
`;
function kindsOf(base){ return base === "sep" ? ["field", "glider", "heli"] : ["field", "glider", "heli", "mil"]; }
function seg(base, kind, all){
  const ks = base === "pill" ? ["all", "field", "glider", "heli", "mil"] : ["all", "field", "glider", "heli"];
  const n = k => k === "all" ? all.filter(a => base !== "pill" || a.kind !== "mil").length : all.filter(a => a.kind === k).length;
  return `<div class="zf-seg${ks.length > 4 ? " scroll" : ""}" role="group" aria-label="種類で絞り込む">${ks.map(k => `<button type="button" aria-pressed="${k === kind}">${LAB[k]}<span class="u">${n(k)}</span></button>`).join("")}</div>`;
}
const P = (a, W, H) => [((a.lon - 128.6) / (146.2 - 128.6)) * (W - 16) + 8, ((45.6 - a.lat) / (45.6 - 30.8)) * (H - 16) + 8];
const inMap = a => a.lat > 30.5 && a.lon > 128.4;
function mapSVG(list, xv){
  const W = 300, H = 380;
  let g = A.filter(inMap).map(a => { const [x, y] = P(a, W, H); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="1.8" class="m86"/>`; }).join("");
  g += list.filter(a => inMap(a) && !xv.has(a.id)).map(a => { const [x, y] = P(a, W, H); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" class="my"/>`; }).join("");
  g += list.filter(a => inMap(a) && xv.has(a.id)).map(a => { const [x, y] = P(a, W, H); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="6" class="mv" style="fill:${COL[a.kind]}"/><text x="${(x - 10).toFixed(1)}" y="${(y + 4.5).toFixed(1)}" text-anchor="end">${esc(zkxShort(a))}</text>`; }).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="絞った種類の地図">${g}</svg>`;
}
// opts: kind（all／field／glider／heli／mil）・view（region／map）・base（sep＝基地は今のまま別の図鑑／pill＝「基地」のピルを足す／mix＝すべての中だけ）
window.zfRender = (opts) => {
  const { kind = "all", view = "region", base = "sep" } = opts || {};
  const xv = visitedExtra(), vc = new Map(); for(const x of S.checkins) if(IS_EXTRA(x.a)) vc.set(x.a, (vc.get(x.a) || 0) + 1);
  const ks = kindsOf(base);
  const all = XA.filter(a => ks.includes(a.kind));   // シークレット（secret）は今までどおり入れない
  const shownAll = base === "pill" ? all.filter(a => a.kind !== "mil") : all;   // 基地のピルを足す案でも「すべて」は今の75のまま
  const list = kind === "all" ? shownAll : all.filter(a => a.kind === kind);
  const segAll = base === "pill" ? all : shownAll;
  const got = list.filter(a => xv.has(a.id));
  const rgs = REGION.map(([rg]) => { const l = list.filter(a => regionOf(a) === rg); return { rg, list:l, got:l.filter(a => xv.has(a.id)).length }; });
  const one = kind !== "all";
  const lab = one ? `<i style="background:${COL[kind]}"></i>${LAB[kind]}` : "集めた数";
  const kindsRow = one ? "" : `<p class="zx-kinds">${ks.map(k => { const l = list.filter(a => a.kind === k); return `<span>${XKIND[k].short} <b>${l.filter(a => xv.has(a.id)).length}</b><small>/${l.length}</small></span>`; }).join("")}</p>`;
  const hero = `<div class="zk-hero zx-hero"><span class="zx-pill w">もう1つの図鑑</span><div class="ht"><span class="lab">${lab}</span><b class="num">${got.length}</b><span class="u">/ ${list.length}</span><span class="side">まだ ${list.length - got.length}</span></div>
    ${kindsRow}
    ${view === "map" ? "" : `<div class="rg">${rgs.map(r => `<div><span class="t"><span>${r.rg}</span><span>${r.list.length ? `${r.got}<small>/${r.list.length}</small>` : `<small>なし</small>`}</span></span><span class="b"><i style="width:${r.list.length ? Math.round(r.got / r.list.length * 100) : 0}%;background:${zkCol(r.rg)}"></i></span></div>`).join("")}</div>`}</div>`;
  const vw = `<div class="vwrow"><div class="viewsw" role="tablist" aria-label="見方"><button role="tab" aria-selected="${view === "region"}">地方別</button><button role="tab" aria-selected="${view === "map"}">地図</button></div></div>`;
  const tile = a => zkxTile(a, xv.has(a.id), vc.get(a.id) || 0).replace(/(<span class="zx-nm">)([^<]*?)(分屯基地|航空基地|駐屯地|基地)(<\/span>)/, (m, h, n, t, e) => a.kind === "mil" && n ? `${h}${n}<wbr>${t}${e}` : m).replace(/(<span class="zx-nm">[\s\S]*?<\/span>)/, `$1<span class="zf-pf">${esc(a.pref)}</span>`);
  const dt = one ? `<span class="zf-sp"></span>` : `<span class="zx-dtag"><span class="nw">飛行場・</span><span class="nw">滑空場・</span><span class="nw">${base === "mix" ? "ヘリポート・基地" : "ヘリポート"}</span></span>`;
  let body;
  if(view === "map"){
    const done = list.filter(a => xv.has(a.id)), yet = list.filter(a => !xv.has(a.id));
    body = `${hero}<div class="zf-map">${mapSVG(list, xv)}<p class="zf-lg"><span><i style="background:${COL[kind] || "#3D7A4E"}"></i>行った</span><span><i class="y"></i>まだ</span></p></div>
      <div class="zf-list">${yet.length ? `<h4>まだ ${yet.length}</h4>` : ""}${yet.slice(0, 4).map(a => `<div class="r no"><i></i><b>${esc(zkxShort(a))}</b><span class="pf">${esc(a.pref)}</span></div>`).join("")}</div>`;
  } else {
    body = `${hero}${one ? "" : `<p class="zk-lead">集めた空港（${A.length}）とは別に数えます。</p>`}` + rgs.filter(r => r.list.length).map(r => `<section class="zk-rg" data-rg="${r.rg}" style="--c:${zkCol(r.rg)}">
      <div class="zk-door"><h3>${r.rg}</h3><b class="num">${r.got}</b><span class="u">/ ${r.list.length}</span>${dt}<button class="zk-up" type="button" aria-label="図鑑の上へ"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 14l6-6 6 6"/></svg></button></div>
      <div class="zk-grid">${r.list.map(tile).join("")}</div></section>`).join("");
  }
  const tsume = `<nav class="zk-tsume" aria-label="地方へ飛ぶ">${rgs.map(r => `<button type="button" style="--c:${zkCol(r.rg)}" aria-label="${r.rg}へ"${r.list.length && view === "region" ? "" : ` disabled aria-disabled="true"`}><span>${r.rg}</span></button>`).join("")}</nav>`;
  const box = document.getElementById("bookAir");
  box.innerHTML = `${ZK_BACK_MAIN}<div class="book-head"><h2>${ZKX_TITLE_BR}</h2></div><div class="zk-main${one ? " zf-one" : ""}${view === "map" ? " zf-wide" : ""}">${vw}${seg(base, kind, segAll)}${body}</div>${view === "region" ? tsume : ""}`;
};
})();
