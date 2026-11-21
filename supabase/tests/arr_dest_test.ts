// 11/21 急ぎ：羽田行きの特別塗装機を「成田に着陸に向かっています」と知らせていた直し（_shared/arr_dest.ts）
import { assertEquals } from "jsr:@std/assert@1";
import { type Apt, onFinal, pickAirport, refinePhases, runwaysFor } from "../functions/_shared/arr_dest.ts";

const D = Math.PI / 180;
// p から向き brg（度）に km 進んだ点
function dest(p: [number, number], brg: number, km: number): [number, number] {
  const d = km / 6371, t = brg * D, la = p[0] * D, lo = p[1] * D;
  const la2 = Math.asin(Math.sin(la) * Math.cos(d) + Math.cos(la) * Math.sin(d) * Math.cos(t));
  const lo2 = lo + Math.atan2(Math.sin(t) * Math.sin(d) * Math.cos(la), Math.cos(d) - Math.sin(la) * Math.sin(la2));
  return [la2 / D, lo2 / D];
}
const HND: Apt = { iata: "HND", at: [35.5533, 139.7811], rws: runwaysFor("HND") };
const NRT: Apt = { iata: "NRT", at: [35.7772, 140.3823], rws: runwaysFor("NRT") };
const rw = (a: Apt, id: string) => a.rws.find((r) => r.id === id)!;
// 最終進入の上の機体（接地点の手前 km、3°の進入の高さ、滑走路の向き）
function onFinalPlane(a: Apt, id: string, km: number, phase = "arr") {
  const r = rw(a, id), [lat, lon] = dest(r.thr, (r.hdg + 180) % 360, km);
  return { id: "x", lat, lon, alt_ft: Math.round(km / 1.852 * 318 + 100), hdg: Math.round(r.hdg), fpm: -800, phase };
}

Deno.test("滑走路の表に羽田・成田がある", () => {
  assertEquals(HND.rws.length >= 8, true);
  assertEquals(NRT.rws.length, 4);
});

Deno.test("羽田の34Lの最終進入の機体：羽田では着陸のまま、成田の答えでは着陸にしない", () => {
  const p = onFinalPlane(HND, "34L", 15);
  assertEquals(!!onFinal(p, HND.rws), true);   // 平行の34Rとは1.7kmなので、どちらに合っても良い
  assertEquals(refinePhases([p], HND, [NRT])[0].phase, "arr");
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "other");
});

Deno.test("羽田の22の最終進入（千葉の上、成田の円の中）：成田の答えでは着陸にしない", () => {
  const p = onFinalPlane(HND, "22", 22);
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "other");
  assertEquals(refinePhases([p], HND, [NRT])[0].phase, "arr");
});

Deno.test("成田の34Lの最終進入の機体：成田では着陸のまま、羽田の答えでは着陸にしない", () => {
  const p = onFinalPlane(NRT, "34L", 15);
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "arr");
  assertEquals(refinePhases([p], HND, [NRT])[0].phase, "other");
});

Deno.test("成田の東で高いまま羽田へ降りていく機体（11,000ft・南西向き）：成田には高すぎるので成田の着陸にしない", () => {
  const [lat, lon] = dest(NRT.at, 80, 15);
  const p = { id: "y", lat, lon, alt_ft: 11000, hdg: 230, fpm: -1500, phase: "arr" };
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "other");
});

Deno.test("成田の16Rへ北から降りてくる機体（下降中・まだ最終進入の外）は成田の着陸のまま", () => {
  const r = rw(NRT, "16R"), [lat, lon] = dest(r.thr, 0, 30);
  const p = { id: "z", lat, lon, alt_ft: 6000, hdg: 170, fpm: -900, phase: "arr" };
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "arr");
});

Deno.test("羽田の05から離陸して北東へ上がる機体：成田の答えでは離陸にしない", () => {
  const r = rw(HND, "05"), [lat, lon] = dest(r.thr, r.hdg, 12);
  const p = { id: "d", lat, lon, alt_ft: 5000, hdg: Math.round(r.hdg), fpm: 2500, phase: "dep" };
  assertEquals(refinePhases([p], NRT, [HND])[0].phase, "other");
  assertEquals(refinePhases([p], HND, [NRT])[0].phase, "dep");
});

Deno.test("着陸・離陸でない機体はそのまま", () => {
  const p = { id: "o", lat: 35.7, lon: 140.1, alt_ft: 12000, hdg: 90, fpm: 0, phase: "other" };
  assertEquals(refinePhases([p], NRT, [HND])[0], p);
});

Deno.test("1つに決める：便名の行き先＞最終進入に乗っている近い方＞はっきり近い方。決められなければ null", () => {
  const both = [{ iata: "HND", dist_km: 60, aligned: false }, { iata: "NRT", dist_km: 20, aligned: false }];
  assertEquals(pickAirport(both, "HND"), "HND");                 // 便名の行き先が羽田
  assertEquals(pickAirport([both[1]], "HND"), null);             // 行き先が羽田なのに成田だけ → 知らせない
  assertEquals(pickAirport([{ iata: "HND", dist_km: 40, aligned: true }, { iata: "NRT", dist_km: 20, aligned: false }]), "HND");
  assertEquals(pickAirport(both), "NRT");                        // 20km は 60km の7割以下
  assertEquals(pickAirport([{ iata: "HND", dist_km: 40, aligned: false }, { iata: "NRT", dist_km: 35, aligned: false }]), null);
  assertEquals(pickAirport([{ iata: "NRT", dist_km: 70, aligned: false }]), null);   // 1つでも遠くて最終進入の外
  assertEquals(pickAirport([{ iata: "NRT", dist_km: 30, aligned: false }]), "NRT");
  assertEquals(pickAirport([]), null);
});
