// 11/21 本人「便の名前から行き先を判別して、判定を強化して」（data/livery-dest2・_shared/flight_dest.ts）
//   本人の iPhone に届いた6件（ADO14・SKY004・JAL500・JAL140 は羽田行き、TGW866・TZP52 は成田行き）を呼び出し符号のまま確かめる
import { assertEquals } from "jsr:@std/assert@1";
import { applyRoutes, clearRouteCache, knownOf, lookupRoutes, type RouteSource, routesFromSchedule, routesFromUsual, type SchedRow, type UsualRow } from "../functions/_shared/flight_dest.ts";
import { type Apt, type Cand, pickAirport, refinePhases, runwaysFor } from "../functions/_shared/arr_dest.ts";
import { flightOfCallsign, flightsOfCallsign } from "../functions/_shared/flight_watch.ts";

const H = 3600_000;
// 2026-11-21 11:00（日本時間）
const NOW = Date.parse("2026-11-21T02:00:00Z");
const iso = (ms: number) => new Date(ms).toISOString();
const jstMins = (t: number) => Math.floor(((t + 9 * H) % 864e5) / 60_000);

// 時刻表（ODPT の JAL・ANA）にある便と、ない便（スカイマーク・エア・ドゥは全機の記録の「いつもの時刻」にもある）
const SCHED: SchedRow[] = [
  { flight: "JL500", dep: "CTS", arr: "HND", std: iso(NOW - 1.5 * H), sta: iso(NOW + 0.1 * H) },
  { flight: "JL140", dep: "AOJ", arr: "HND", std: iso(NOW - 1.2 * H), sta: iso(NOW + 0.05 * H) },
  // 同じ便名の別の日（前の日・次の日）は選ばない
  { flight: "JL500", dep: "CTS", arr: "HND", std: iso(NOW - 25 * H), sta: iso(NOW - 23 * H) },
];
const USUAL: UsualRow[] = [
  { callsign: "ADO14", iata: "HND", mins: jstMins(NOW + 10 * 60_000) },
  { callsign: "SKY4", iata: "HND", mins: jstMins(NOW + 5 * 60_000) },
  { callsign: "TGW866", iata: "NRT", mins: jstMins(NOW + 20 * 60_000) },
  { callsign: "TZP52", iata: "NRT", mins: jstMins(NOW - 10 * 60_000) },
  // ふだんの時刻が遠い別の空港（同じ呼び出し符号で別の日に飛ぶもの）は選ばない
  { callsign: "TZP52", iata: "KIX", mins: jstMins(NOW + 6 * H) },
];
function fake(sched = SCHED, usual = USUAL) {
  const calls = { schedule: 0, usual: 0, flights: [] as string[][], usualArgs: [] as string[][] };
  const src: RouteSource = {
    schedule: (flights, from, to) => {
      calls.schedule++; calls.flights.push(flights);
      return Promise.resolve(sched.filter((r) => flights.includes(r.flight) && r.std >= from && r.std <= to));
    },
    usual: (cs) => { calls.usual++; calls.usualArgs.push(cs); return Promise.resolve(usual.filter((u) => cs.includes(u.callsign))); },
  };
  return { src, calls };
}
const SIX = ["ADO14", "SKY004", "JAL500", "JAL140", "TGW866", "TZP52"];

Deno.test("呼び出し符号 → 便名：本人の通知の6件と、グループの別会社", () => {
  assertEquals(SIX.map(flightOfCallsign), ["HD14", "BC4", "JL500", "JL140", "TR866", "ZG52"]);
  assertEquals(flightsOfCallsign("JAC3711"), ["3X3711", "JL3711"]);
  assertEquals(flightsOfCallsign("JTA603"), ["NU603", "JL603"]);
  assertEquals(flightsOfCallsign("AKX1234"), ["NH1234"]);
  // 11/21 に足した会社（トキエア・天草・日本貨物・エアロK・エアプレミア）
  assertEquals(["TOK101", "AHX1", "NCA52", "EOK811", "APZ101"].map(flightOfCallsign), ["BV101", "MZ1", "KZ52", "RF811", "YP101"]);
  assertEquals(flightsOfCallsign("N123AB"), []);
});

Deno.test("本人の通知の6件：羽田の4件と成田の2件の行き先が便名から出る（時刻表→いつもの時刻）", async () => {
  clearRouteCache();
  const { src, calls } = fake();
  const r = await lookupRoutes(src, SIX, NOW);
  assertEquals(SIX.map((c) => knownOf(r, c).arr), ["HND", "HND", "HND", "HND", "NRT", "NRT"]);
  assertEquals(r.get("JAL500")?.src, "schedule");
  assertEquals(r.get("SKY4")?.src, "usual");
  // 問い合わせは束ねて1回ずつ
  assertEquals([calls.schedule, calls.usual], [1, 1]);
  assertEquals(calls.usualArgs[0].sort(), ["ADO14", "SKY4", "TGW866", "TZP52"]);
  // 2回目は記憶から（問い合わせなし）
  await lookupRoutes(src, SIX, NOW + 60_000);
  assertEquals([calls.schedule, calls.usual], [1, 1]);
});

Deno.test("羽田と成田の両方の円で「着陸」になった6機：知らせは便名の行き先の1つだけ", async () => {
  clearRouteCache();
  const r = await lookupRoutes(fake().src, SIX, NOW);
  // 形だけでは決めにくい（どちらの最終進入にも乗らず、距離も近い）
  const both: Cand[] = [{ iata: "HND", dist_km: 45, aligned: false }, { iata: "NRT", dist_km: 40, aligned: false }];
  assertEquals(SIX.map((c) => pickAirport(both, knownOf(r, c).arr)), ["HND", "HND", "HND", "HND", "NRT", "NRT"]);
  // 便名の行き先が候補にないとき（ほかの空港へ向かっている）は知らせない
  assertEquals(pickAirport([{ iata: "NRT", dist_km: 30, aligned: true }], knownOf(r, "JAL500").arr), null);
});

// ---- 運用タブの一覧 ----
const D = Math.PI / 180;
function dest(p: [number, number], brg: number, km: number): [number, number] {
  const d = km / 6371, t = brg * D, la = p[0] * D, lo = p[1] * D;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(t));
  const lo2 = lo + Math.atan2(Math.sin(t) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2));
  return [la2 / D, lo2 / D];
}
const HND: Apt = { iata: "HND", at: [35.5533, 139.7811], rws: runwaysFor("HND") };
const NRT: Apt = { iata: "NRT", at: [35.7772, 140.3823], rws: runwaysFor("NRT") };
function finalPlane(a: Apt, id: string, km: number, callsign: string) {
  const r = a.rws.find((x) => x.id === id)!, [lat, lon] = dest(r.thr, (r.hdg + 180) % 360, km);
  return { id: callsign, callsign, lat, lon, alt_ft: Math.round(km / 1.852 * 318 + 100), hdg: Math.round(r.hdg), fpm: -800, phase: "arr", dist_km: 0 };
}

Deno.test("運用タブ：成田の一覧に羽田行きを「着陸」と出さない。羽田の一覧では形で外れても着陸に戻す", async () => {
  clearRouteCache();
  const r = await lookupRoutes(fake().src, SIX, NOW);
  // 成田と羽田のあいだを、まだどちらの最終進入にも乗らずに下りてくる羽田行き（形だけでは成田の着陸にも見える）
  const mid = { id: "a", callsign: "JAL500", lat: 35.70, lon: 140.25, alt_ft: 7000, hdg: 225, fpm: -1200, phase: "arr", dist_km: 15 };
  assertEquals(applyRoutes([mid], refinePhases([mid], NRT, [HND]), "NRT", NRT.rws, r)[0].phase, "other");
  const asOther = { ...mid, phase: "other" };   // 羽田の答えで形の絞り込みに外されていても
  assertEquals(applyRoutes([mid], [asOther], "HND", HND.rws, r)[0].phase, "arr");
  // 成田行き（TGW866）は成田の一覧では着陸、羽田の一覧では外す
  const tgw = finalPlane(NRT, "34L", 15, "TGW866");
  assertEquals(applyRoutes([tgw], refinePhases([tgw], NRT, [HND]), "NRT", NRT.rws, r)[0].phase, "arr");
  assertEquals(applyRoutes([tgw], refinePhases([tgw], HND, [NRT]), "HND", HND.rws, r)[0].phase, "other");
});

Deno.test("運用タブ：便名の行き先と違っても、この空港の最終進入の12km以内・3,000ft以下ならダイバートとして着陸のまま", async () => {
  clearRouteCache();
  const r = await lookupRoutes(fake().src, ["JAL500"], NOW);
  const p = finalPlane(NRT, "16R", 8, "JAL500");
  assertEquals(applyRoutes([p], [p], "NRT", NRT.rws, r)[0].phase, "arr");
  const far = finalPlane(NRT, "16R", 20, "JAL500");
  assertEquals(applyRoutes([far], [far], "NRT", NRT.rws, r)[0].phase, "other");
});

Deno.test("運用タブ：離陸は時刻表の出発地で決める。いつもの時刻（出発地なし）と、便名の分からない機体は形の判定のまま", () => {
  const routes = new Map([
    ["JAL501", { dep: "HND", arr: "CTS", src: "schedule" as const, flight: "JL501" }],
    ["TGW867", { dep: null, arr: "SIN", src: "usual" as const, flight: null }],
  ]);
  const p = (cs: string | null, phase = "dep") => ({ callsign: cs, lat: 35.6, lon: 140.0, alt_ft: 5000, hdg: 90, phase });
  assertEquals(applyRoutes([p("JAL501")], [p("JAL501")], "HND", HND.rws, routes)[0].phase, "dep");
  assertEquals(applyRoutes([p("JAL501")], [p("JAL501")], "NRT", NRT.rws, routes)[0].phase, "other");
  assertEquals(applyRoutes([p("TGW867")], [p("TGW867")], "NRT", NRT.rws, routes)[0].phase, "dep");
  assertEquals(applyRoutes([p(null)], [p(null, "other")], "NRT", NRT.rws, routes)[0].phase, "other");
});

// ---- 時刻表の行の選び方 ----
Deno.test("時刻表：日をまたぐ深夜便・遅れた便・長い国際線もいま飛んでいる便を選ぶ", () => {
  const night = Date.parse("2026-11-21T15:50:00Z");   // 11/22 0:50（日本時間）
  const rows: SchedRow[] = [
    // 前の日 23:30 発・0:40 着の便が10分遅れ（運航日は前の日）
    { flight: "JL3711", dep: "ITM", arr: "HND", std: "2026-11-21T14:30:00Z", sta: "2026-11-21T15:40:00Z" },
    // 同じ便名の次の日の便（まだ出発の1時間より前）は選ばない
    { flight: "JL3711", dep: "ITM", arr: "HND", std: "2026-11-22T14:30:00Z", sta: "2026-11-22T15:40:00Z" },
    // 13時間の国際線
    { flight: "JL5", dep: "JFK", arr: "HND", std: "2026-11-21T03:00:00Z", sta: "2026-11-21T16:10:00Z" },
  ];
  const r = routesFromSchedule(["JAC3711", "JAL005"], rows, night);
  assertEquals(r.get("JAC3711")?.arr, "HND");
  assertEquals(r.get("JAC3711")?.flight, "JL3711");   // 3X3711 ではなく JL の便名で載っていても見つかる
  assertEquals(r.get("JAL5")?.dep, "JFK");
  // 到着の定刻から6時間すぎた便は、いま飛んでいる便と見ない
  assertEquals(routesFromSchedule(["JAL500"], [SCHED[0]], NOW + 7 * H).size, 0);
});

Deno.test("いつもの時刻：前後2時間に入る到着だけ。いちばん近いもの", () => {
  const r = routesFromUsual(USUAL, NOW);
  assertEquals(r.get("TZP52")?.arr, "NRT");
  assertEquals(routesFromUsual([{ callsign: "TZP52", iata: "KIX", mins: jstMins(NOW + 3 * H) }], NOW).size, 0);
  // 0時をまたぐ（23:50 と 0:20 は30分差）
  const t = Date.parse("2026-11-21T15:20:00Z");   // 0:20
  assertEquals(routesFromUsual([{ callsign: "KAL703", iata: "NRT", mins: 23 * 60 + 50 }], t).get("KAL703")?.arr, "NRT");
});

Deno.test("問い合わせ：失敗したときは記憶に入れない（次の回にもう一度引く）・便名に直せない呼び出し符号は引かない・いつもの時刻は50件ずつ", async () => {
  clearRouteCache();
  let n = 0;
  const bad: RouteSource = { schedule: () => { n++; return Promise.reject(new Error("timeout")); }, usual: () => Promise.resolve([]) };
  assertEquals((await lookupRoutes(bad, ["JAL500"], NOW)).size, 0);
  await lookupRoutes(bad, ["JAL500"], NOW);
  assertEquals(n, 2);
  clearRouteCache();
  const { src, calls } = fake([], []);
  await lookupRoutes(src, ["N123AB", "JA01CJ", null, ""], NOW);
  assertEquals(calls.schedule, 0);
  const many = Array.from({ length: 120 }, (_, i) => `KAL${i + 1}`);
  await lookupRoutes(src, many, NOW);
  assertEquals([calls.schedule, calls.usual], [1, 3]);
  // 分からなかった便も記憶に入れる（10分は引き直さない）
  await lookupRoutes(src, many, NOW + 5 * 60_000);
  assertEquals([calls.schedule, calls.usual], [1, 3]);
});

Deno.test("時刻表だけ引く（海外の塗装機の早めの知らせ）：見つからなかった便は記憶に入れず、あとの運用タブではいつもの時刻まで引ける", async () => {
  clearRouteCache();
  const { src, calls } = fake();
  const r = await lookupRoutes(src, ["TGW866", "JAL500"], NOW, false);
  assertEquals([r.get("JAL500")?.arr, r.has("TGW866"), calls.usual], ["HND", false, 0]);
  const r2 = await lookupRoutes(src, ["TGW866", "JAL500"], NOW);
  assertEquals([r2.get("TGW866")?.arr, calls.usual], ["NRT", 1]);
});
