// 11/22 羽田の3D に地上の機体：adsb.lol の ac と live_positions の行から、地上の機体（答えの ground）を作る
import { assertEquals } from "jsr:@std/assert@1";
import { acFromLive, groundFromAdsb, planesFromAdsb } from "../functions/_shared/traffic.ts";

const HND: [number, number] = [35.5533, 139.7811];
const g = (over: Record<string, unknown>) => ({ hex: "84aa01", flight: "JAL98   ", t: "B789", r: "JA861J", alt_baro: "ground", gs: 0, lat: 35.5492, lon: 139.7838, ...over });

Deno.test("地上の機体だけを、空港の中心から5km 以内で返す", () => {
  const out = groundFromAdsb([
    g({}),
    g({ hex: "a2", flight: "ANA860", t: "B763", gs: 47.5, track: 329.88, lat: 35.545, lon: 139.79 }),
    g({ hex: "a3", alt_baro: 3000 }),                              // 空の機体は入れない
    g({ hex: "a4", lat: 35.62, lon: 139.78 }),                     // 7km 北（空港の外）は入れない
  ], HND);
  assertEquals(out.map((p) => [p.id, p.callsign, p.hdg, p.kt, p.moving, p.type]), [["84aa01", "JAL98", null, 0, false, "B789"], ["a2", "ANA860", 330, 48, true, "B763"]]);
});

Deno.test("空港の車両（category C・便名 TEST）と、機種も登録記号もないものは入れない", () => {
  const out = groundFromAdsb([
    g({ hex: "v1", flight: "TEST    ", t: undefined, r: undefined, category: "C2" }),
    g({ hex: "v2", flight: "OPS1", category: "C1" }),
    g({ hex: "v3", flight: null, t: undefined, r: undefined }),
    g({ hex: "ok", flight: null }),                                  // 便名がなくても機種があれば入れる
  ], HND);
  assertEquals(out.map((p) => [p.id, p.callsign]), [["ok", null]]);
});

Deno.test("向き：track がなければ true_heading・mag_heading。どれもなければ null", () => {
  const out = groundFromAdsb([g({ hex: "h1", true_heading: 181.4 }), g({ hex: "h2", mag_heading: 359.6 }), g({ hex: "h3" })], HND);
  assertEquals(out.map((p) => p.hdg), [181, 0, null]);
});

Deno.test("live_positions の地上の行（見る人の呼び出し）からも作れる。空の機体の並びには入らない", () => {
  const now = Date.parse("2026-11-22T10:00:00Z");
  const rows = [{ callsign: "JAL98", hex: "84aa01", lat: 35.5492, lon: 139.7838, alt_ft: null, ground: true, fpm: null, kt: 12, trk: 250, type: "B789", reg: "JA861J", seen_at: new Date(now - 10_000).toISOString() }];
  const ac = acFromLive(rows, now);
  assertEquals(planesFromAdsb(ac, HND).length, 0);
  assertEquals(groundFromAdsb(ac, HND).map((p) => [p.callsign, p.hdg, p.kt, p.moving, p.reg]), [["JAL98", 250, 12, true, "JA861J"]]);
});
