// 11/7 全体のデバッグ：見る人の airport-traffic を live_positions から作る・429 の待ち時間・天気の記録からの代わり
import { assertEquals } from "jsr:@std/assert@1";
import { acFromLive, planesFromAdsb, retryAfterMs } from "../functions/_shared/traffic.ts";
import { metarFromObs, parseMetar } from "../functions/_shared/metar.ts";

const HND: [number, number] = [35.5533, 139.7811];
const now = Date.parse("2026-11-07T13:20:00Z");
const row = (cs: string, over: Record<string, unknown> = {}) => ({ callsign: cs, hex: "84" + cs.slice(-4).toLowerCase(), lat: 35.30, lon: 139.85, alt_ft: 3000, ground: false, fpm: -800, kt: 180, trk: 330, type: "B738", reg: "JA301J", seen_at: new Date(now - 20_000).toISOString(), ...over });

Deno.test("live_positions の行を adsb.lol の形に戻すと、同じ見分けになる", () => {
  const rows = [row("JAL123"), row("ANA45", { fpm: 1500, lat: 35.62, lon: 139.90 }), row("JAL9", { ground: true, alt_ft: null })];
  const fromLive = planesFromAdsb(acFromLive(rows, now), HND);
  const direct = planesFromAdsb([
    { hex: "84l123", flight: "JAL123", t: "B738", r: "JA301J", lat: 35.30, lon: 139.85, alt_baro: 3000, gs: 180, track: 330, baro_rate: -800 },
    { hex: "84ana45", flight: "ANA45", t: "B738", r: "JA301J", lat: 35.62, lon: 139.90, alt_baro: 3000, gs: 180, track: 330, baro_rate: 1500 },
    { hex: "84jal9", flight: "JAL9", alt_baro: "ground", lat: 35.55, lon: 139.78 },
  ], HND);
  assertEquals(fromLive.map((p) => [p.callsign, p.phase, p.alt_ft, p.hdg, p.kt, p.reg]), direct.map((p) => [p.callsign, p.phase, p.alt_ft, p.hdg, p.kt, p.reg]));
  assertEquals(fromLive.length, 2);   // 地上の機体は出ない
});

Deno.test("古い位置（75秒より前）は使わない・hex がなければ便名から作る", () => {
  const ac = acFromLive([row("JAL1", { seen_at: new Date(now - 76_000).toISOString() }), row("JAL2", { hex: null })], now);
  assertEquals(ac.map((a) => [a.flight, a.hex]), [["JAL2", "cs-JAL2"]]);
});

Deno.test("429 の待ち時間：Retry-After（秒）を使い、5秒までにする", () => {
  assertEquals(retryAfterMs("2"), 2000);
  assertEquals(retryAfterMs("30"), 5000);
  assertEquals(retryAfterMs(null), 3000);
  assertEquals(retryAfterMs("あとで"), 3000);
  assertEquals(retryAfterMs("0"), 0);
});

Deno.test("天気の記録（wx_obs）の行を、配信元の通報と同じ形にする", () => {
  const raw = "RJTT 071300Z 34012KT 9999 FEW030 15/08 Q1018 NOSIG";
  const a = metarFromObs({ icao: "RJTT", at: "2026-11-07T13:00:00Z", raw, wdir: 340, wspd: 12, wgst: null, vis_m: 10000 })!;
  const b = parseMetar({ icaoId: "RJTT", reportTime: "2026-11-07T13:00:00.000Z", rawOb: raw, wdir: 340, wspd: 12, visib: "6+" });
  assertEquals(a, { ...b, wgst: null });
  assertEquals(metarFromObs(null), null);
});

Deno.test("記録の処理：南の円（後半の回にだけ取る）も航跡の点と便の記録が1分・2分に1回残る", async () => {
  const { recordPlan } = await import("../functions/_shared/traffic.ts");
  // 4回（2分）ぶん：前半・後半・前半・後半。北は前半、南は後半にだけ取る
  const fetched = (slot: number) => ["EAST", "WEST", slot % 2 === 0 ? "NORTH" : "SOUTH"];
  const n: Record<string, { track: number; legs: number }> = {};
  for (let slot = 1000; slot < 1004; slot++) for (const k of fetched(slot)) {
    const p = recordPlan(k, slot); n[k] ??= { track: 0, legs: 0 }; if (p.track) n[k].track++; if (p.legs) n[k].legs++;
  }
  assertEquals(n, { EAST: { track: 2, legs: 1 }, WEST: { track: 2, legs: 1 }, NORTH: { track: 2, legs: 1 }, SOUTH: { track: 2, legs: 1 } });
});
