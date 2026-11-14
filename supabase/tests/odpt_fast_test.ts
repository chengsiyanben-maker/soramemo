// 「この便に乗る」で選ばれた便だけを毎分見るときの、ODPT への問い合わせの決め方
import { assertEquals } from "jsr:@std/assert@1";
import { fastTargets, opOf } from "../functions/_shared/odpt_fast.ts";

const NOW = Date.parse("2026-11-13T01:00:00Z");
const r = (id: number, flight: string, dep: string, arr: string, stdMin: number, extra: Record<string, string | null> = {}) => ({
  id, flight, svc_date: "2026-11-13", dep, arr, std: new Date(NOW + stdMin * 60_000).toISOString(), sta: new Date(NOW + (stdMin + 90) * 60_000).toISOString(),
  source: `ODPT（公共交通オープンデータセンター）フライト時刻表（${/^JL/.test(flight) ? "JAL" : "ANA"}）`, ...extra,
});

Deno.test("出発前は出発空港の出発情報、出発したら到着空港の到着情報。同じ会社・空港・向きは1回", () => {
  const { calls, scheds } = fastTargets([
    r(1, "JL501", "HND", "CTS", 30), r(2, "JL503", "HND", "CTS", 60),
    r(3, "NH55", "HND", "CTS", -20, { atd: "2026-11-13T00:45:00Z" }),
    r(4, "NH99", "HND", "OKA", -200, { atd: "x", ata: "2026-11-13T00:30:00Z" }),   // 着いた便は見ない
  ], NOW);
  assertEquals(calls, [{ type: "Arrival", op: "ANA", airport: "CTS" }, { type: "Departure", op: "JAL", airport: "HND" }]);
  assertEquals(scheds.map((s) => s.id).sort(), [1, 2, 3]);
});

Deno.test("問い合わせは1回に cap 件まで（今に近い便から）。入らなかった便は次の回", () => {
  const rows = ["HND", "ITM", "FUK", "CTS"].map((ap, i) => r(i + 1, "JL" + (100 + i), ap, "OKA", (i + 1) * 10));
  const { calls, scheds } = fastTargets(rows, NOW, 2);
  assertEquals(calls.map((c) => c.airport), ["HND", "ITM"]);
  assertEquals(scheds.map((s) => s.id), [1, 2]);
});

Deno.test("会社は時刻表の出典から、なければ便名から", () => {
  assertEquals([opOf({ flight: "JL1" }), opOf({ flight: "NH1" }), opOf({ flight: "NU1" }), opOf({ flight: "XX1", source: "…（JAL）" })], ["JAL", "ANA", "JAL", "JAL"]);
});
