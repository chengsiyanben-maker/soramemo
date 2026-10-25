import { assertEquals } from "jsr:@std/assert@1";
import { type Ap, brg, departureRwy, km, landingRwy, type Pt, samplesOf, splitTracks } from "../functions/_shared/rwy_track.ts";

// 羽田の滑走路の一部（実際の位置）
const HND: Ap = { center: [35.5533, 139.7811], rw: {
  "34L": { id: "34L", thr: [35.536591, 139.785672], hdg: 330 }, "16R": { id: "16R", thr: [35.560452, 139.768734], hdg: 150 },
  "34R": { id: "34R", thr: [35.53969, 139.805142], hdg: 330 }, "16L": { id: "16L", thr: [35.565897, 139.78655], hdg: 150 },
  "22": { id: "22", thr: [35.567459, 139.777114], hdg: 215 }, "04": { id: "04", thr: [35.549015, 139.761274], hdg: 35 } } };
// 進入端から、着陸してくる側へ d km の点
const back = (thr: [number, number], hdg: number, d: number): [number, number] => { const r = Math.PI / 180, a = (hdg + 180) * r;
  return [thr[0] + d * Math.cos(a) / 111.2, thr[1] + d * Math.sin(a) / (111.2 * Math.cos(thr[0] * r))]; };
const fwd = (p: [number, number], hdg: number, d: number) => back(p, hdg + 180, d);

Deno.test("着陸：34L の延長線上の最後の点", () => {
  const r = HND.rw["34L"], t0 = 1_760_000_000;
  const pts: Pt[] = [[t0, ...back(r.thr, r.hdg, 40), 90], [t0 + 60, ...back(r.thr, r.hdg, 25), 60], [t0 + 120, ...back(r.thr, r.hdg, 12), 30], [t0 + 180, ...back(r.thr, r.hdg, 4), 12]];
  assertEquals(landingRwy(HND, pts), "34L");
  assertEquals(landingRwy(HND, pts.map((p) => [p[0], p[1], p[2] + 0.08, p[3]] as Pt)), null);   // 横に7km ずれている
});
Deno.test("離陸：16R の先の線の上", () => {
  const r = HND.rw["16R"], s = HND.rw["34L"].thr, t0 = 1_760_000_000;   // 16R の始まりは 34L の進入端
  const pts: Pt[] = [[t0, ...fwd(s, r.hdg, 4.5), 15], [t0 + 60, ...fwd(s, r.hdg, 10), 40], [t0 + 120, ...fwd(fwd(s, r.hdg, 12), 240, 10), 80]];
  assertEquals(departureRwy(HND, pts), "16R");
});
Deno.test("途切れで分ける・来た方面・自家用機は除く", () => {
  assertEquals(splitTracks([[0, 0, 0, 0], [60, 0, 0, 0], [3000, 0, 0, 0]]).length, 2);
  const r = HND.rw["22"], t0 = 1_760_000_000;
  const far = fwd(HND.center, 20, 70);   // 北北東 70km から
  const pts: Pt[] = [[t0, ...far, 120], [t0 + 300, ...back(r.thr, r.hdg, 30), 60], [t0 + 600, ...back(r.thr, r.hdg, 12), 30], [t0 + 720, ...back(r.thr, r.hdg, 4), 10]];
  const s = samplesOf("JAL123", pts, { HND });
  assertEquals(s.length, 1); assertEquals(s[0].rwy, "22"); assertEquals(s[0].dir, "arr"); assertEquals(s[0].flight, "JL123");
  assertEquals(s[0].first_brg, 20); assertEquals(typeof s[0].ent60, "number"); assertEquals(s[0].ent120, 20);
  assertEquals(Math.round(km(HND.center, far)), 70); assertEquals(Math.round(brg(HND.center, far)), 20);
  assertEquals(samplesOf("JA4123", pts, { HND }).length, 0);
});
Deno.test("空の道すじ：出発・到着した空港ごとに、80km 以内の部分", async () => {
  const { tracksOf } = await import("../functions/_shared/rwy_track.ts");
  const r = HND.rw["22"], t0 = Date.parse("2026-10-21T15:30:00Z") / 1000;   // 日本時間 0:30（日付は22日）
  const pts: Pt[] = [[t0, ...fwd(HND.center, 20, 150), 140], [t0 + 300, ...fwd(HND.center, 20, 60), 100], [t0 + 600, ...back(r.thr, r.hdg, 12), 30], [t0 + 720, ...back(r.thr, r.hdg, 4), 10]];
  const t = tracksOf("ANA24", pts, { HND });
  assertEquals(t.length, 1); assertEquals(t[0].dep_here, 0); assertEquals(t[0].day, "2026-10-22"); assertEquals(t[0].iata, "HND");
  assertEquals(tracksOf("JA4123", pts, { HND }).length, 0);
});
Deno.test("空の道すじ：最初に見えたのが22km より先でも、低く上りながら離れていく機体は出発に数える", async () => {
  const { tracksOf } = await import("../functions/_shared/rwy_track.ts");
  const NRT: Ap = { center: [35.76858, 140.388714], rw: {} }, t0 = Date.parse("2026-10-24T03:00:00Z") / 1000;
  // 成田を北へ離陸：最初に見えたのは30km 先・4,000ft
  const dep: Pt[] = [[t0, ...fwd(NRT.center, 340, 30), 40], [t0 + 60, ...fwd(NRT.center, 340, 38), 60], [t0 + 120, ...fwd(NRT.center, 340, 46), 80], [t0 + 180, ...fwd(NRT.center, 340, 55), 100]];
  const t = tracksOf("ANA101", dep, { NRT, HND });
  assertEquals(t.length, 1); assertEquals(t[0].iata, "NRT"); assertEquals(t[0].dep_here, 1);
  // 高いところ（12,000ft）で最初に見えた機体は、通り過ぎただけかもしれないので数えない
  assertEquals(tracksOf("ANA102", dep.map((p) => [p[0], p[1], p[2], p[3] + 80] as Pt), { NRT, HND }).length, 0);
  // 下りながら近づいてくる機体（到着）で、最後に見えたのが30km 先
  const arr: Pt[] = [...dep].reverse().map((p, i) => [t0 + i * 60, p[1], p[2], p[3]] as Pt);
  const a = tracksOf("JAL55", arr, { NRT, HND });
  assertEquals(a.length, 1); assertEquals(a[0].dep_here, 0);
  // 羽田から出た機体は、成田に近い点がなければ成田の出発にしない
  const r = HND.rw["16R"], s = HND.rw["34L"].thr;
  const h: Pt[] = [[t0, ...fwd(s, r.hdg, 4.5), 15], [t0 + 60, ...fwd(s, r.hdg, 10), 40], [t0 + 120, ...fwd(s, r.hdg, 16), 60], [t0 + 180, ...fwd(s, r.hdg, 24), 80]];
  const ht = tracksOf("ANA200", h, { NRT, HND });
  assertEquals(ht.map((x) => x.iata), ["HND"]);
});
Deno.test("空の道すじ：読んだ幅の端で切れているかもしれない航跡は入れない", async () => {
  const { tracksOf } = await import("../functions/_shared/rwy_track.ts");
  const r = HND.rw["16R"], s = HND.rw["34L"].thr, t0 = Date.parse("2026-10-24T03:00:00Z") / 1000;
  const h: Pt[] = [[t0, ...fwd(s, r.hdg, 4.5), 15], [t0 + 60, ...fwd(s, r.hdg, 10), 40], [t0 + 120, ...fwd(s, r.hdg, 16), 60], [t0 + 180, ...fwd(s, r.hdg, 24), 80]];
  assertEquals(tracksOf("ANA200", h, { HND }, { from: t0 - 3600, to: t0 + 7200 }).length, 1);
  assertEquals(tracksOf("ANA200", h, { HND }, { from: t0 - 600, to: t0 + 7200 }).length, 0);    // 始まりが幅の端に近い
  assertEquals(tracksOf("ANA200", h, { HND }, { from: t0 - 3600, to: t0 + 900 }).length, 0);    // 終わりが幅の端に近い（まだ飛んでいるかもしれない）
});
