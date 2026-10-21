#!/usr/bin/env node
// 統計レポートを作る（運営者用）。運営コンソールで admin_stats_report('HND', '2026-10-01', '2026-10-31') の結果を JSON で保存し、
//   node tools/stats_report.mjs report.json > report.html
// で、印刷・PDF にできるページを作る。数は集計だけで、10人未満の区切りは「—」（admin_stats_report が null にしたもの）。
import { readFileSync } from "node:fs";

const NAME = { HND: "羽田空港", NRT: "成田国際空港", ITM: "大阪国際空港（伊丹）", KIX: "関西国際空港", CTS: "新千歳空港", FUK: "福岡空港", OKA: "那覇空港", NGO: "中部国際空港" };
const r = JSON.parse(readFileSync(process.argv[2] ?? 0, "utf8"));
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const n = (v) => v == null ? "—" : Number(v).toLocaleString("ja-JP");
const hours = Array.from({ length: 24 }, (_, h) => h).filter((h) => h >= 5 && h <= 23);
const hv = hours.map((h) => r.by_hour?.[h] ?? null), hmax = Math.max(1, ...hv.filter((v) => v != null));
const routes = (r.shugyo_routes ?? []).slice(0, 10), rmax = Math.max(1, ...routes.map((x) => x.users));
const ga = Object.entries(r.go_arounds ?? {}).sort((a, b) => b[1] - a[1]);

process.stdout.write(`<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>${esc(NAME[r.iata] ?? r.iata)} 空港レポート</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--ink:#111;--mute:#5C5C5C;--line:#E5E5E5;--bar:#1D4ED8}
body{margin:0;background:#fff;color:var(--ink);font-family:"Noto Sans JP",system-ui,sans-serif}
main{max-width:720px;margin:0 auto;padding:0 16px 40px}
header{background:#111;color:#fff;padding:24px 20px;margin:0 -16px}header small{color:#BDBDBD;letter-spacing:1px}header h1{margin:6px 0 0;font-size:24px;line-height:1.35}header p{margin:8px 0 0;font-size:12px;color:#E5E5E5}
h2{font-size:16px;margin:26px 0 4px}p.s{font-size:11.5px;color:var(--mute);margin:0 0 8px}
.k{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}.k div{background:#F4F4F4;border-radius:14px;padding:12px}.k small{font-size:11px;color:var(--mute)}.k b{display:block;font-size:20px}
.row{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12.5px}.row span:first-child{width:96px}.row i{display:block;height:12px;border-radius:6px;background:var(--bar)}.row .t{flex:1;background:#F4F4F4;border-radius:6px;overflow:hidden}.row b{width:48px;text-align:right}
.note{margin-top:22px;border:1.5px solid var(--line);border-radius:14px;padding:12px 14px;font-size:11.5px;color:var(--mute);line-height:1.7}
@media print{header{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body><main>
<header><small>そらメモ 空港レポート（非公式）</small><h1>${esc(NAME[r.iata] ?? r.iata)}<br>${esc(r.from)} 〜 ${esc(r.to)}</h1><p>そらメモ利用者の集計（個人が分からない統計）</p></header>
<div class="k"><div><small>チェックイン</small><b>${n(r.checkins?.n)}</b></div><div><small>チェックインした人</small><b>${n(r.checkins?.users)}</b></div><div><small>ゴーアラウンド（推定）</small><b>${n(ga.reduce((a, [, v]) => a + v, 0))}</b></div></div>
<h2>時間帯ごとのチェックイン</h2><p class="s">空港に来た人が、いつチェックインしたか（日本時間）</p>
${hours.map((h, i) => `<div class="row"><span>${h}時台</span><span class="t"><i style="width:${hv[i] == null ? 0 : Math.round(hv[i] / hmax * 100)}%"></i></span><b>${n(hv[i])}</b></div>`).join("")}
<h2>修行の計画に入った路線</h2><p class="s">ステイタスを目指す人が、計画に入れた路線（人数）</p>
${routes.length ? routes.map((x) => `<div class="row"><span>${esc(x.route)}</span><span class="t"><i style="width:${Math.round(x.users / rmax * 100)}%;background:#111"></i></span><b>${n(x.users)}</b></div>`).join("") : `<p class="s">10人以上の路線はまだありません。</p>`}
<h2>滑走路ごとのゴーアラウンド（推定）</h2><p class="s">機体の位置（adsb.lol・ODbL）からの推定。航空会社・管制の発表ではありません</p>
${ga.length ? ga.map(([k, v]) => `<div class="row"><span>${esc(k)}</span><span class="t"><i style="width:${Math.round(v / ga[0][1] * 100)}%;background:#C2410C"></i></span><b>${n(v)}</b></div>`).join("") : `<p class="s">この期間はありません。</p>`}
<div class="note"><b>このレポートの作り方</b><br>・個人が分からない集計だけを使います。${esc(r.k ?? 10)}人未満の区切りは「—」にしています。<br>・「統計に使う」をオフにした人の記録は入れていません。<br>・1人ずつの記録、位置、金額、カードの情報は入れていません。<br>・時刻表と運航情報（ODPT）から作った数字は入れていません。<br>・機体の位置から作った数字は ODbL の決まりにもとづきます（© adsb.lol contributors）。</div>
</main></body></html>
`);
