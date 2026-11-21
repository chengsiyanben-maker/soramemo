// 11/21 見回り 7：見る人の airport-traffic を速くする決まり（_shared/traffic_view.ts）
import { assertEquals } from "jsr:@std/assert@1";
import { activeAirports, slimPlanes, viewPlan } from "../functions/_shared/traffic_view.ts";

const now = Date.parse("2026-11-21T06:00:00Z");

Deno.test("置き場の答えの古さで決める：20秒未満はそのまま・60秒未満は返して裏で作り直す・それより古いか無ければ作る", () => {
  assertEquals(viewPlan(now - 5_000, now), "fresh");
  assertEquals(viewPlan(now - 19_999, now), "fresh");
  assertEquals(viewPlan(now - 20_000, now), "stale");
  assertEquals(viewPlan(now - 59_999, now), "stale");
  assertEquals(viewPlan(now - 60_000, now), "build");
  assertEquals(viewPlan(null, now), "build");
  assertEquals(viewPlan(undefined, now), "build");
  assertEquals(viewPlan(NaN, now), "build");
  assertEquals(viewPlan(now + 3_000, now), "fresh");   // 時計のずれ
});

Deno.test("記録の処理が置き場を新しくするのは、見る人のしるしが3分以内の空港だけ", () => {
  const key = (k: string) => `trafficseen:${k}`;
  const sh = new Map([[key("HND"), { at: now - 40_000 }], [key("NRT"), { at: now - 3 * 60_000 }], [key("ITM"), { at: NaN }]]);
  assertEquals(activeAirports(sh, key, ["HND", "NRT", "ITM", "KIX"], now), ["HND"]);
  assertEquals(activeAirports(new Map(), key, ["HND"], now), []);
});

Deno.test("線は着陸・離陸の機体だけ・最後の150点・小数5けた。形（trail は配列）は同じ", () => {
  const pts = Array.from({ length: 160 }, (_, i) => ({ p: [35.1234567 + i / 1e3, 139.7654321] as [number, number] }));
  const tr = new Map([["a", pts], ["b", pts], ["c", pts]]);
  const out = slimPlanes([{ id: "a", phase: "arr", lat: 1, lon: 2 }, { id: "b", phase: "dep" }, { id: "c", phase: "other" }, { id: "d", phase: "arr" }], tr);
  assertEquals(out.map((p) => p.trail.length), [150, 150, 0, 0]);
  assertEquals(out[0].trail[0], [35.13346, 139.76543]);
  assertEquals(out[0].trail[149], [35.28246, 139.76543]);
  assertEquals((out[0] as { lat?: number }).lat, 1);   // ほかの項目はそのまま
  assertEquals(Array.isArray(out[2].trail), true);
});
