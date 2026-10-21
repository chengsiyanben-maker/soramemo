import { assertEquals } from "jsr:@std/assert@1";
import { arrStep, onFinal, sideOf, type ArrWatch } from "../functions/_shared/rwy_learn.ts";

const RW = { "34L": { id: "34L", thr: [35.5366, 139.7857] as [number, number], hdg: 337 }, "34R": { id: "34R", thr: [35.5425, 139.8031] as [number, number], hdg: 337 }, "22": { id: "22", thr: [35.5675, 139.7771] as [number, number], hdg: 217 } };
const C: [number, number] = [35.5533, 139.7811];
Deno.test("延長線上：34L の手前・向きがそろう", () => {
  assertEquals(onFinal({ lat: 35.50, lon: 139.806, hdg: 337 }, RW), "34L");
  assertEquals(onFinal({ lat: 35.50, lon: 139.806, hdg: 157 }, RW), null);   // 逆向き
  assertEquals(onFinal({ lat: 35.50, lon: 139.86, hdg: 337 }, RW), null);    // 横にずれている
});
Deno.test("来た方面を残して、延長線に乗ったら記録する", () => {
  const w = new Map<string, ArrWatch>(), t0 = Date.parse("2026-10-21T06:00:00Z");
  const seq = [{ lat: 36.6, lon: 139.9, alt_ft: 14000, hdg: 190 }, { lat: 36.0, lon: 139.9, alt_ft: 9000, hdg: 190 }, { lat: 35.75, lon: 139.95, alt_ft: 5000, hdg: 200 }, { lat: 35.50, lon: 139.806, alt_ft: 1200, hdg: 337 }];
  let out: Record<string, unknown>[] = [];
  seq.forEach((s, i) => { const r = arrStep("HND", C, RW, [{ id: "86d1", callsign: "JAL510", phase: "arr", dist_km: 0, ...s }], w, t0 + i * 60_000);
    for (const u of r.upserts) w.set(u.hex, u); out = out.concat(r.samples); });
  assertEquals(out.length, 1);
  assertEquals(out[0].rwy, "34L"); assertEquals(out[0].flight, "JL510");
  assertEquals(sideOf(out[0].ent120 as number), "N");
});
Deno.test("北側・南西側", () => { assertEquals(sideOf(10), "N"); assertEquals(sideOf(320), "N"); assertEquals(sideOf(200), "S"); assertEquals(sideOf(120), "S"); });
