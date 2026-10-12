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
