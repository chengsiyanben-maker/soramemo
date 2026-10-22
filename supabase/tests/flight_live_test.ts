// 乗る便を出発から到着まで追う（国際線も）
import { assertEquals } from "jsr:@std/assert@1";
import { liveState, type LiveSched, type Plane, toPlane } from "../functions/_shared/flight_live.ts";
import { callsignsFor } from "../functions/_shared/flight_watch.ts";

const HND = { iata: "HND", lat: 35.5533, lon: 139.7811, name: "羽田" }, LAX = { iata: "LAX", lat: 33.9425, lon: -118.408, name: "ロサンゼルス" };
const T0 = Date.UTC(2026, 9, 20, 15, 30);
const S: LiveSched = { flight: "NH106", dep: "HND", arr: "LAX", std: T0, sta: T0 + 615 * 60_000 };
const P = (o: Partial<Plane>): Plane => ({ callsign: "ANA106", lat: 45, lon: 170, alt_ft: 37000, ground: false, kt: 560, track: 70, type: "B77W", reg: "JA791A", at: T0 + 4 * 36e5, ...o });

Deno.test("便名から呼び出し符号：海外の航空会社も", () => {
  assertEquals(callsignsFor("NH106")[0], "ANA106");
  assertEquals(callsignsFor("ZG21"), ["TZP21"]);
  assertEquals(callsignsFor("KE703"), ["KAL703"]);
});

Deno.test("adsb.lol の1機を読む", () => {
  const p = toPlane({ flight: "ANA106  ", lat: 45, lon: 170, alt_baro: 37000, gs: 560, track: 70, t: "B77W", r: "JA791A", seen_pos: 2 }, T0);
  assertEquals([p?.callsign, p?.alt_ft, p?.reg, p?.at], ["ANA106", 37000, "JA791A", T0 - 2000]);
  assertEquals(toPlane({ flight: "X", lat: null }, T0), null);
  assertEquals(toPlane({ flight: "ANA1", lat: 35, lon: 139, alt_baro: "ground" }, T0)?.ground, true);
});

Deno.test("太平洋の上を飛んでいる：進み具合と到着予想", () => {
  const r = liveState(S, P({}), HND, LAX, T0 + 4 * 36e5);
  assertEquals(r.phase, "air");
  assertEquals((r.progress ?? 0) > 0.2 && (r.progress ?? 0) < 0.6, true);
  assertEquals((r.eta ?? 0) > T0 + 8 * 36e5 && (r.eta ?? 0) < T0 + 12 * 36e5, true);
});

Deno.test("出発前は地上、着いたら到着", () => {
  assertEquals(liveState(S, P({ ground: true, lat: 35.55, lon: 139.78 }), HND, LAX, T0).phase, "taxi");
  assertEquals(liveState(S, P({ ground: true, lat: 33.94, lon: -118.4 }), HND, LAX, T0 + 10 * 36e5).phase, "landed");
});

Deno.test("見つからない：出発前は予定、出発後は電波の届かない所、到着予定を1時間すぎたら着いたとみなす", () => {
  assertEquals(liveState(S, null, HND, LAX, T0 - 36e5).phase, "sched");
  const lost = liveState(S, null, HND, LAX, T0 + 5 * 36e5);
  assertEquals([lost.phase, (lost.progress ?? 0) > 0.4], ["lost", true]);
  assertEquals(liveState(S, null, HND, LAX, T0 + 12 * 36e5).phase, "landed");
});

Deno.test("道筋から大きく外れた同じ呼び出し符号の機体は使わない", () => {
  assertEquals(liveState(S, P({ lat: 10, lon: 100 }), HND, LAX, T0 + 4 * 36e5).phase, "lost");
});

Deno.test("欠航", () => {
  assertEquals(liveState({ ...S, cancelled: true }, P({}), HND, LAX, T0).phase, "cancelled");
});

Deno.test("実際の到着の時刻が、まだ来ていない時刻なら到着にしない", () => {
  assertEquals(liveState({ ...S, ata: T0 + 9 * 36e5 }, P({}), HND, LAX, T0 + 4 * 36e5).phase, "air");
  assertEquals(liveState({ ...S, ata: T0 + 3 * 36e5 }, null, HND, LAX, T0 + 4 * 36e5).phase, "landed");
});

Deno.test("到着予想は着陸の予想に地上走行の目安を足す（羽田は10分）", async () => {
  const { taxiIn } = await import("../functions/_shared/flight_watch.ts");
  assertEquals(taxiIn("HND"), 10); assertEquals(taxiIn("KMJ"), 4); assertEquals(taxiIn("TAK"), 4); assertEquals(taxiIn(null), 4);
});

Deno.test("空港ごとの寄り道：遠いときは全部、近づくと減る", async () => {
  const { arrExtra, predictEta } = await import("../functions/_shared/flight_watch.ts");
  assertEquals(arrExtra("HND", 200), 10); assertEquals(arrExtra("HND", 30), 5); assertEquals(arrExtra("HND", 0), 0); assertEquals(arrExtra("KMJ", 200), 0);
  const p = { lat: 34.7, lon: 135.4, alt_ft: 35000, kt: 450, at: 0 };
  const hnd = predictEta(p, { iata: "HND", lat: 35.5533, lon: 139.7811, name: "" }, "B738"), x = predictEta(p, { iata: "XXX", lat: 35.5533, lon: 139.7811, name: "" }, "B738");
  assertEquals(Math.round((hnd - x) / 60_000), 10);
});
