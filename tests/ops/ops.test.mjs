// 運用タブと公開ページ「空港のいま」の画面のテスト（公開の前に、14空港の表示が壊れていないかを確かめる）
//   cd tests/ops && npm install && npx playwright install chromium && npm test
// 本物のサーバーにはつながない：気象通報・機体・特別塗装機は、作り物の返事を返す（偽のサーバー tests/e2e/fake_sb.js も使う）。
// 地図の部品（Leaflet）は CDN から読む（ネットにつながる環境で動かす）
import http from "node:http";
import { readFileSync } from "node:fs";
import { chromium } from "playwright";
import { opsCoreParts } from "../../tools/ops_core_parts.mjs";
import { OPS_AIRPORTS } from "../../supabase/functions/_shared/ops_core.js";

const ROOT = new URL("../../", import.meta.url).pathname;
const FAKE = "https://fake.supabase.co";
const files = {
  "/index.html": () => readFileSync(ROOT + "src/index.html"),
  "/now.html": () => readFileSync(ROOT + "src/now.html", "utf8").replace("/*@OPS_CORE@*/", () => opsCoreParts().join("\n")),
  "/config.js": () => `window.SORAMEMO_CONFIG = { supabaseUrl: "${FAKE}", supabaseAnonKey: "anon" };`,
  "/icon.svg": () => readFileSync(ROOT + "web/icon.svg"),
};
const server = http.createServer((q, s) => { const p = new URL(q.url, "http://x").pathname, f = files[p];
  if (!f) { s.writeHead(404); return s.end(); } s.writeHead(200, { "Content-Type": p.endsWith(".js") ? "text/javascript" : p.endsWith(".svg") ? "image/svg+xml" : "text/html; charset=utf-8" }); s.end(f()); });
await new Promise((r) => server.listen(0, r));
const BASE = `http://localhost:${server.address().port}`;

// 作り物の機体：運用 mode の着陸の滑走路へ、延長線上をまっすぐ降りてくる機体を2機（実際の機体から判定されるはず）
const D2R = Math.PI / 180, R = 6371;
function dest(p, brg, km) { const d = km / R, t = brg * D2R, la = p[0] * D2R, lo = p[1] * D2R;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(t));
  return [la2 / D2R, (lo + Math.atan2(Math.sin(t) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2))) / D2R]; }
function bearing(a, b) { const y = Math.sin((b[1] - a[1]) * D2R) * Math.cos(b[0] * D2R), x = Math.cos(a[0] * D2R) * Math.sin(b[0] * D2R) - Math.sin(a[0] * D2R) * Math.cos(b[0] * D2R) * Math.cos((b[1] - a[1]) * D2R); return (Math.atan2(y, x) / D2R + 360) % 360; }
function planesFor(def, mode) {
  const rw = def.rwy.flatMap((r) => [[r[0], [r[1], r[2]], [r[5], r[6]]], [r[4], [r[5], r[6]], [r[1], r[2]]]]);
  const id = def.modes[mode].arr[0], [, thr, opp] = rw.find((x) => x[0] === id), back = (bearing(thr, opp) + 180) % 360;
  const pl = (n, off) => { const pts = [11, 9.5, 8, 6.5, 5, 3.6].map((nm) => dest(thr, back, (nm + off) * 1.852)), last = pts.pop();
    return { id: "t" + n, callsign: "TST" + n, lat: last[0], lon: last[1], alt_ft: 2000, kt: 150, hdg: (back + 180) % 360, fpm: -700, phase: "arr", dist_km: 7, type: "B738", reg: n === 1 ? "JA819A" : "JA000T", trail: pts }; };
  return [pl(1, 0), pl(2, 0.3)];
}
// 各空港で、着陸機を降ろす運用（羽田は北風運用、ほかは b）と、判定されるはずの運用
// （仙台・松山は、着陸機だけ見えて向きが優先方式の着陸の向きなら、優先方式と判定する）
const pickMode = (d) => d.iata === "HND" ? "north" : "b";
const expectMode = (d, m) => d.split && d.modes[d.split.mode].arr[0] === d.modes[m].arr[0] ? d.split.mode : m;

let fails = 0;
const ok = (cond, label, extra = "") => { console.log((cond ? "OK " : "NG ") + label + (cond ? "" : "  " + extra)); if (!cond) fails++; };
const browser = await chromium.launch();

// 時刻は固定する（深夜は別の運用・運用時間外になるため）。ふだんは日本時間の13時
const NOON = new Date("2026-10-16T04:00:00Z");
async function page(iata, mode, at = NOON) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 1400 } });
  await ctx.addInitScript(() => { localStorage.setItem("soramemo.onboarded", "1"); });
  const p = await ctx.newPage(), errs = [];
  await p.clock.setFixedTime(at);
  p.on("pageerror", (e) => errs.push(String(e)));
  const def = OPS_AIRPORTS[iata];
  await p.route("https://cdn.jsdelivr.net/npm/@supabase/**", (r) => r.fulfill({ contentType: "text/javascript", body: readFileSync(ROOT + "tests/e2e/fake_sb.js", "utf8") }));
  await p.route(FAKE + "/**", (r) => {
    const u = new URL(r.request().url());
    if (u.pathname.endsWith("/metar")) return r.fulfill({ json: { id: def.icao, time: at.toISOString(), raw: "TEST", wdir: null, wspd: 2, wgst: null, vis_m: 10000, vis_plus: true } });
    if (u.pathname.endsWith("/airport-traffic")) return r.fulfill({ json: { iata, at: at.toISOString(), source: "adsb.lol", planes: planesFor(def, mode) } });
    if (u.pathname.endsWith("/special_now")) return r.fulfill({ json: [{ reg: "JA819A", name: "ポケモンジェット 赤", airline: "ANA", callsign: "TST1", lat: def.center[0], lon: def.center[1], alt_ft: 2000, iata, phase: "arr", src: "x", at: at.toISOString() }] });
    if (u.pathname.endsWith("/flight_alerts")) return r.fulfill({ json: [] });
    if (u.pathname.endsWith("/push-subscribe")) return r.fulfill({ json: { key: null } });
    return r.fulfill({ json: [] });
  });
  return { ctx, p, errs };
}

// 1) 運用タブ：14空港それぞれで、実際の機体から判定され、地図に線が描かれ、エラーが出ない
for (const def of Object.values(OPS_AIRPORTS)) {
  const mode = pickMode(def), { ctx, p, errs } = await page(def.iata, mode);
  await p.goto(`${BASE}/index.html#ops-${def.iata}`);
  await p.waitForFunction(() => document.querySelector("#opsInfo .opssrc"), null, { timeout: 15000 }).catch(() => {});
  await p.waitForTimeout(2500);
  const info = await p.locator("#opsInfo").innerText().catch(() => "");
  const lines = await p.locator("#opsMap path.leaflet-interactive").count().catch(() => 0);
  const label = def.modes[expectMode(def, mode)].label;
  if (def.noObs) ok(info.includes(def.name) || info.length > 0, `${def.iata}：運用タブが出る（伊丹は着陸機では判定しない）`, info.slice(0, 80));
  else ok(info.includes(label) && info.includes("実際の機体から判定"), `${def.iata}：着陸機2機から「${label}」と判定`, info.slice(0, 120));
  ok(lines > 0, `${def.iata}：地図に経路の線がある（${lines}本）`);
  ok(errs.length === 0, `${def.iata}：画面のエラーなし`, errs.join(" / "));
  if (def.iata === "HND") {
    const sp = await p.locator("#opsSpecial").innerText().catch(() => "");
    ok(sp.includes("ポケモンジェット 赤") && sp.includes("羽田に着陸へ"), "特別塗装機の欄が出る", sp.slice(0, 80));
    const tag = await p.locator(".tlabel.sp").count();
    ok(tag > 0, "地図の名札に特別塗装機の★が出る");
  }
  if (def.iata === "NRT") {
    // 成田：出発経路の方向での絞り込み（34運用は方向が3つ以上ある）
    const n0 = await p.locator('#opsSidDir [data-sid-dir]').count();
    ok(n0 >= 4, `成田：出発経路の方向の切り替えが出る（${n0}個）`);
    if (n0) { const all = lines; await p.locator('#opsSidDir [data-sid-dir="西へ"]').click(); await p.waitForTimeout(800);
      const after = await p.locator("#opsMap path.leaflet-interactive").count(); ok(after < all, `成田：「西へ」で線が減る（${all}→${after}）`); }
  }
  await ctx.close();
}

// 2) 公開ページ「空港のいま」：いくつかの空港で、題名と判定が出る
for (const iata of ["HND", "SDJ", "FUK", "OKA"]) {
  const def = OPS_AIRPORTS[iata], mode = pickMode(def), { ctx, p, errs } = await page(iata, mode);
  await p.goto(`${BASE}/now.html?ap=${iata}`); await p.waitForTimeout(2500);
  const title = await p.locator("#title").innerText(), lbl = await p.locator("#modeLbl").innerText(), src = await p.locator("#src").innerText();
  ok(title.includes(def.name) && lbl === def.modes[expectMode(def, mode)].label && src === "実際の機体から判定", `空港のいま ${iata}：${title}・${lbl}`, `${title} / ${lbl} / ${src}`);
  ok(errs.length === 0, `空港のいま ${iata}：画面のエラーなし`, errs.join(" / "));
  await ctx.close();
}

// 3) 深夜：羽田23時30分は「深夜・北風運用」と夜の説明、福岡23時（機体なし）は「運用時間外」
{
  const def = OPS_AIRPORTS.HND, { ctx, p, errs } = await page("HND", "north", new Date("2026-10-16T14:30:00Z"));
  await p.goto(`${BASE}/index.html#ops-HND`); await p.waitForTimeout(2500);
  const info = await p.locator("#opsInfo").innerText().catch(() => "");
  ok(info.includes(def.modes.nightN.label) && info.includes("夜間："), "羽田 23:30：深夜・北風運用と夜の説明", info.slice(0, 160));
  ok(errs.length === 0, "羽田 23:30：画面のエラーなし", errs.join(" / "));
  await ctx.close();
}
for (const url of ["index.html#ops-FUK", "now.html?ap=FUK"]) {
  const { ctx, p, errs } = await page("FUK", "b", new Date("2026-10-16T14:00:00Z"));
  await p.route(FAKE + "/functions/v1/airport-traffic*", (r) => r.fulfill({ json: { iata: "FUK", at: new Date("2026-10-16T14:00:00Z").toISOString(), source: "adsb.lol", planes: [] } }));
  await p.goto(`${BASE}/${url}`); await p.waitForTimeout(2500);
  const txt = await p.locator("body").innerText().catch(() => "");
  ok(txt.includes("運用時間外") && txt.includes("22時〜7時は離着陸できません"), `福岡 23:00（${url}）：運用時間外`, txt.slice(0, 200));
  ok(txt.includes("運用時間：7時〜22時") && txt.includes("いまは時間外"), `福岡 23:00（${url}）：運用時間の表示`, txt.slice(0, 200));
  ok(errs.length === 0, `福岡 23:00（${url}）：画面のエラーなし`, errs.join(" / "));
  await ctx.close();
}

// 4) 門限チャレンジ：伊丹20時30分。到着済み・間に合いそう（いま見えている機体）・過ぎる見込み・欠航
{
  const at = new Date("2026-10-16T11:30:00Z"), close = "2026-10-16T12:00:00Z", T = (m) => new Date(Date.parse(close) + m * 60000).toISOString();
  const { ctx, p, errs } = await page("ITM", "b", at);
  await p.route(FAKE + "/rest/v1/rpc/curfew_flights", (r) => r.fulfill({ json: { iata: "ITM", close_at: close, flights: [
    { dir: "arr", flight: "JL2087", other: "HND", sched: T(-40), est: null, actual: T(-35), status: "Arrived", cancelled: false },
    { dir: "arr", flight: "TST1", other: "HND", sched: T(-25), est: T(-20), actual: null, status: "EstimatedArrival", cancelled: false, dep_actual: T(-90) },
    { dir: "arr", flight: "NH039", other: "HND", sched: T(-5), est: T(12), actual: null, status: "EstimatedArrival", cancelled: false },
    { dir: "dep", flight: "JL2205", other: "FUK", sched: T(-10), est: null, actual: null, status: "Cancelled", cancelled: true },
    { dir: "arr", flight: "OC070", other: "KMI", sched: T(-75), est: null, actual: null, status: null, cancelled: false },
    { dir: "arr", flight: "IJ123", other: "HND", sched: T(-60), est: null, actual: null, inferred: T(-52), status: null, cancelled: false },
    { dir: "arr", flight: "6J21", other: "HND", sched: T(-8), est: null, actual: null, predicted: T(6), status: null, cancelled: false, dep_actual: T(-80) },
  ] } }));
  await p.goto(`${BASE}/index.html#ops-ITM`); await p.waitForTimeout(3500);
  const txt = await p.locator("#opsCurfew").innerText().catch(() => "");
  ok(txt.includes("門限チャレンジ") && txt.includes("21:00") && txt.includes("あと 30分"), "伊丹 20:30：門限チャレンジと残り時間", txt.slice(0, 120));
  ok(txt.includes("到着") && txt.includes("間に合いそう") && txt.includes("過ぎる見込み") && txt.includes("欠航") && txt.includes("記録なし") && txt.includes("到着（推定）") && txt.includes("機体の位置から推定") && txt.includes("到着予想 21:06"), "伊丹 20:30：便ごとの判定（到着予想も・運航情報がない便は推定の着陸時刻、それもなければ「記録なし」）", txt);
  ok(errs.length === 0, "伊丹 20:30：画面のエラーなし", errs.join(" / "));
  await ctx.close();
}

await browser.close(); server.close();
console.log(fails ? `\n${fails} 件失敗` : "\nすべて成功");
process.exit(fails ? 1 : 0);
