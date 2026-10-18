import { assertEquals, assert } from "jsr:@std/assert@1";
import { buildHistory, decodePolyline, encodePolyline, jstYesterday, thin, toHistory, type SchedRow } from "../functions/_shared/archive.ts";

const base = (o: Partial<SchedRow>): SchedRow => ({ svc_date: "2026-10-17", flight: "JL100", dep: "HND", arr: "ITM", std: "2026-10-17T00:00:00.000Z", sta: "2026-10-17T01:05:00.000Z",
  atd: null, ata: null, dep_status: null, arr_status: null, aircraft: "B767", source: "ODPT", state: null, ...o });

Deno.test("実績：航空会社の時刻を優先し、なければ機体の位置からの推定", () => {
  const a = toHistory(base({ atd: "2026-10-17T00:12:00.000Z", state: { takeoff_est: false, takeoff_at: Date.parse("2026-10-17T00:20:00Z"), landed_iata: "ITM", landed_at: Date.parse("2026-10-17T01:20:00Z"), reg: "JA8980", type: "B763", cs: "JAL100" } }));
  assertEquals([a.atd_src, a.dep_delay, a.ata_src, a.arr_delay, a.reg, a.type, a.callsign], ["odpt", 12, "adsb", 15, "JA8980", "B763", "JAL100"]);
});
Deno.test("実績：離陸の推定が不確かな便・ほかの空港に降りた便", () => {
  const a = toHistory(base({ state: { takeoff_est: true, takeoff_at: 1, landed_iata: "KIX", landed_at: Date.parse("2026-10-17T01:30:00Z") } }));
  assertEquals([a.atd, a.ata, a.diverted_to], [null, null, "KIX"]);
});
Deno.test("実績：欠航は時刻と遅れを入れない", () => {
  const a = toHistory(base({ dep_status: "Cancelled", atd: "2026-10-17T00:10:00.000Z" }));
  assertEquals([a.cancelled, a.atd, a.dep_delay], [true, null, null]);
});
Deno.test("共同運航：同じ出発・到着・定刻の便は1つにまとめ、機体を見つけた便を残す", () => {
  const h = buildHistory([base({ flight: "NH3801" }), base({ flight: "HD15", state: { cs: "ADO15", reg: "JA01AN" } }), base({ flight: "JL200", std: "2026-10-17T02:00:00.000Z" })]);
  assertEquals(h.length, 2);
  const m = h.find((x) => x.flight === "HD15")!;
  assertEquals([m.also, m.reg], [["NH3801"], "JA01AN"]);
});
Deno.test("航跡：間引きと polyline の往復", () => {
  const pts = [{ lat: 35.55, lon: 139.78, alt: 0 }, { lat: 35.5501, lon: 139.7801, alt: 1 }, { lat: 35.6, lon: 139.9, alt: 40 }, { lat: 35.7, lon: 140.1, alt: 90 }];
  const t = thin(pts); assertEquals(t.length, 3);
  const d = decodePolyline(encodePolyline(t));
  assert(d.every((p, i) => Math.abs(p.lat - t[i].lat) < 1e-4 && Math.abs(p.lon - t[i].lon) < 1e-4));
});
Deno.test("前の日（日本時間）", () => {
  assertEquals(jstYesterday(Date.parse("2026-10-18T16:00:00Z")), "2026-10-18");   // 日本時間 19日 1:00 → 18日
  assertEquals(jstYesterday(Date.parse("2026-10-18T14:00:00Z")), "2026-10-17");
});
