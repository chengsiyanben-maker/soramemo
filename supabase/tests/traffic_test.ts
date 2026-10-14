// 空港の周りの機体：空中・高度の絞り込み、着陸・離陸の見分け、通ってきた線
import { assertEquals } from "jsr:@std/assert@1";
import { planesFrom, type Trails, updateTrails } from "../functions/_shared/traffic.ts";

const HND: [number, number] = [35.5533, 139.7811];
const st = (id: string, lat: number, lon: number, altM: number | null, ground: boolean, vr: number | null, cs = "JAL123 ") =>
  [id, cs, "Japan", 0, 0, lon, lat, altM, ground, 75, 330, vr, null, altM, null, false, 0];

Deno.test("空中で低い機体だけ。着陸・離陸・最終進入を見分け、近い順に並べる", () => {
  const p = planesFrom([
    st("a", 35.30, 139.85, 900, false, -4),     // 降下中 → 着陸
    st("b", 35.62, 139.90, 800, false, 9),      // 上昇中 → 離陸
    st("c", 35.53, 139.80, 200, false, 0),      // 低く空港の近くでほぼ水平 → 最終進入
    st("d", 35.60, 139.79, 0, true, 0),         // 地上 → 除く
    st("e", 35.00, 139.50, 11000, false, 0),    // 高すぎる → 除く
    st("f", 35.10, 140.30, 3000, false, 0),     // 水平飛行 → その他
  ], HND);
  assertEquals(p.map((x) => [x.id, x.phase]), [["c", "arr"], ["b", "dep"], ["a", "arr"], ["f", "other"]]);
  assertEquals(p[0].callsign, "JAL123");
  assertEquals(p[2].alt_ft, 2953);
  assertEquals(p[2].fpm, -787);
});

Deno.test("通ってきた線：点を足し、同じ位置は重ねず、いなくなった機体と古い点は消す", () => {
  const tr: Trails = new Map();
  const P = (id: string, lat: number, lon: number) => ({ id, callsign: null, lat, lon, alt_ft: 1000, kt: 140, hdg: 330, fpm: -700, phase: "arr" as const, dist_km: 10 });
  updateTrails(tr, [P("a", 35.0, 139.9), P("b", 35.2, 139.8)], 0);
  updateTrails(tr, [P("a", 35.1, 139.9)], 30_000);
  updateTrails(tr, [P("a", 35.1, 139.9)], 60_000);
  assertEquals(tr.get("a")!.map((x) => x.p), [[35.0, 139.9], [35.1, 139.9]]);
  assertEquals(tr.has("b"), false);
  updateTrails(tr, [P("a", 35.2, 139.9)], 30 * 60_000);
  assertEquals(tr.get("a")!.map((x) => x.p), [[35.2, 139.9]]);
});

import { planesFromAdsb } from "../functions/_shared/traffic.ts";
Deno.test("adsb.lol の形からも同じように見分け、機種を添える。地上は除く", () => {
  const p = planesFromAdsb([
    { hex: "86a1", flight: "SFJ54   ", t: "A20N", lat: 35.30, lon: 139.85, alt_baro: 2950, gs: 150, track: 337, baro_rate: -800 },
    { hex: "86a2", flight: "ANA243 ", t: "B788", lat: 35.62, lon: 139.90, alt_baro: 2600, gs: 200, track: 60, baro_rate: 2400 },
    { hex: "86a3", flight: "SIA635", t: "B78X", lat: 35.55, lon: 139.78, alt_baro: "ground" },
    { hex: "86a4", flight: "JAL1", t: "B738", lat: 35.0, lon: 139.5, alt_baro: 33000, baro_rate: 0 },
  ], [35.5533, 139.7811]);
  assertEquals(p.map((x) => [x.callsign, x.phase, x.type, x.alt_ft]), [["ANA243", "dep", "B788", 2600], ["SFJ54", "arr", "A20N", 2950]]);
  assertEquals(p[1].fpm, -800);
});

Deno.test("ほかの空港のほうが近い機体は、この空港の着陸・離陸に数えない", () => {
  const NRT: [number, number] = [35.7772, 140.3823], HND: [number, number] = [35.5533, 139.7811];
  const p = planesFromAdsb([
    { hex: "a1", flight: "JAL562", lat: 35.45, lon: 139.85, alt_baro: 3000, gs: 160, track: 340, baro_rate: -700 },   // 羽田へ降りていく
    { hex: "a3", flight: "ANA605", lat: 35.50, lon: 139.83, alt_baro: 500, gs: 160, track: 150, baro_rate: 2000 },     // 羽田から離陸した
    { hex: "a2", flight: "NCA001", lat: 35.70, lon: 140.45, alt_baro: 2500, gs: 150, track: 337, baro_rate: -700 },   // 成田へ降りていく
  ], NRT, 14000, [HND]);
  const by = Object.fromEntries(p.map((x) => [x.id, x.phase]));
  assertEquals(by["a1"], "other");
  assertEquals(by["a2"], "arr");
  assertEquals(by["a3"], "other");
});
Deno.test("関西の24の進入で伊丹の近くを回る機体は、関西の着陸のまま", () => {
  const KIX: [number, number] = [34.4336, 135.2336], ITM: [number, number] = [34.7856, 135.4380];
  const p = planesFromAdsb([{ hex: "b1", flight: "KAL723", lat: 34.62, lon: 135.36, alt_baro: 2400, gs: 170, track: 202, baro_rate: -600 }], KIX, 14000, [ITM]);
  assertEquals(p[0].phase, "arr");
  const q = planesFromAdsb([{ hex: "b1", flight: "KAL723", lat: 34.62, lon: 135.36, alt_baro: 2400, gs: 170, track: 202, baro_rate: -600 }], ITM, 14000, [KIX]);
  assertEquals(q[0].phase, "other");
});
