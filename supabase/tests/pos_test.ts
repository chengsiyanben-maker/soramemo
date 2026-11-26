import { assertEquals } from "jsr:@std/assert@1";
import { POS_DECIMALS, roundPos } from "../functions/_shared/pos.ts";
import { type Airport, decide, km } from "../functions/_shared/judge.ts";

Deno.test("roundPos：小数3桁に丸める（約100m）", () => {
  assertEquals(POS_DECIMALS, 3);
  assertEquals(roundPos(35.549158), 35.549);
  assertEquals(roundPos(139.784553), 139.785);
  assertEquals(roundPos(35.5495), 35.55);
  assertEquals(roundPos("34.158808"), 34.159);
  assertEquals(roundPos(0), 0);
});

Deno.test("roundPos：負の値も正と同じ丸め", () => {
  assertEquals(roundPos(-35.5495), -35.55);
  assertEquals(roundPos(-122.123456), -122.123);
});

Deno.test("roundPos：丸めたあとの小数は3桁まで（浮動小数のはみ出しがない）・ずれは 0.0005 度まで", () => {
  for (let i = 0; i < 2000; i++) {
    const v = 20 + Math.random() * 130;
    const r = roundPos(v);
    const s = String(r);
    assertEquals((s.split(".")[1] ?? "").length <= 3, true, s);
    assertEquals(Math.abs(r - v) <= 0.0005 + 1e-9, true, `${v} → ${r}`);
  }
});

Deno.test("roundPos：丸めのずれは 100m より小さい", () => {
  const p = { lat: 35.5495, lon: 139.7845 };
  const q = { lat: roundPos(p.lat), lon: roundPos(p.lon) };
  assertEquals(km(p, q) * 1000 < 100, true);
});

Deno.test("roundPos：数でないものはそのまま（判定で先に断る）", () => {
  assertEquals(Number.isNaN(roundPos(undefined)), true);
  assertEquals(Number.isNaN(roundPos("abc")), true);
  assertEquals(roundPos(500), 500);
});

Deno.test("判定は丸める前の値でする：円の境目のすぐ内側は、丸めると外になる所でも印になる", () => {
  const a: Airport = { id: 1, name: "テスト空港", iata: "TST", lat: 35.0, lon: 139.0, radius_m: 1000, rare: false };
  const dLon = 0.9995 / (111.19 * Math.cos(35 * Math.PI / 180)); // 東へ約 999.5m
  const p = { lat: 35.0, lon: 139.0 + dLon };
  const q = { lat: roundPos(p.lat), lon: roundPos(p.lon) };
  assertEquals(km(a, q) * 1000 > 1000, true); // 丸めた値なら外
  const now = Date.now();
  const d = decide({ ...p, acc: 10, ts: now }, now, null, [a], []);
  assertEquals(d.ok, true);
});
