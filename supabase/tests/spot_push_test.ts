import { assert, assertEquals } from "jsr:@std/assert@1";
import { depEtaMin, dueNow, etaMin, famOf, opsChanged, spotDepMessage, spotDepReason, spotMessage, spotReason, type SpotDep, type SpotSub } from "../functions/_shared/spot_push.ts";
import { flightOfCallsign } from "../functions/_shared/flight_watch.ts";

const sub = (o: Partial<SpotSub> = {}): SpotSub => ({ id: 1, spot_iata: "HND", spot_kinds: ["special", "big", "foreign", "reg"], spot_lead: 5, spot_regs: ["JA01XJ"], spot_flights: [], ...o });
const plane = { callsign: "JAL123", reg: "JA02XJ", type: "B738", phase: "arr", dist_km: 20, kt: 180, alt_ft: 3000 };
const NOW = Date.parse("2026-10-21T07:00:00Z");   // 日本時間 16:00

Deno.test("着陸までの分：距離と対地速度から（遅い速度は130ノットとみなす）", () => {
  assertEquals(Math.round(etaMin({ dist_km: 20, kt: 180 }) * 10) / 10, 4.6);
  assertEquals(Math.round(etaMin({ dist_km: 20, kt: 60 }) * 10) / 10, Math.round(etaMin({ dist_km: 20, kt: 130 }) * 10) / 10);
  assert(dueNow(4.6, 5) && !dueNow(6, 5) && !dueNow(0.5, 5));
});

Deno.test("知らせる理由：便・登録記号・特別塗装・大きな機体・海外の順。着陸に向かう機体だけ", () => {
  assertEquals(spotReason(plane, sub(), undefined, NOW), null);   // 小さな機体・日本の会社・指定なし
  assertEquals(spotReason({ ...plane, type: "A359" }, sub(), undefined, NOW)?.why, "big");
  assertEquals(spotReason({ ...plane, type: "A359" }, sub({ spot_kinds: ["special"] }), undefined, NOW), null);   // 選んでいない種類は知らせない
  assertEquals(spotReason({ ...plane, callsign: "KAL703" }, sub(), undefined, NOW)?.why, "foreign");
  assertEquals(spotReason({ ...plane, reg: "JA01XJ", type: "A359" }, sub(), undefined, NOW)?.why, "reg");
  assertEquals(spotReason(plane, sub(), { name: "ミッキー", kind: "special" }, NOW)?.label, "特別塗装機「ミッキー」");
  assertEquals(spotReason(plane, sub(), { name: "スターアライアンス", kind: "alliance" }, NOW), null);   // アライアンス塗装は知らせない
  assertEquals(spotReason(plane, sub({ spot_kinds: [], spot_flights: ["JL123@2026-10-21"] }), undefined, NOW)?.why, "flight");
  assertEquals(spotReason(plane, sub({ spot_kinds: [], spot_flights: ["JL123@2026-10-20"] }), undefined, NOW), null);   // 別の日の便
  assertEquals(spotReason({ ...plane, phase: "dep", type: "A359" }, sub(), undefined, NOW), null);
});

Deno.test("通知の文：便名に直して、あと何分か", () => {
  const m = spotMessage({ ...plane, type: "A359", reg: "JA01XJ" }, { label: "大きな機体" }, "羽田", 4.6);
  assertEquals(m.title, "そらメモ：JL123 があと約5分で着陸");
  assert(m.body.includes("A359・JA01XJ") && m.body.includes("推定"));
  assertEquals(flightOfCallsign("KAL703"), "KE703");
  assertEquals(flightOfCallsign("ANA0012"), "NH12");
});

Deno.test("運用の変化：前の2回と新しい2回がそれぞれそろって違うときだけ", () => {
  const r = (...m: (string | null)[]) => m.map((obs_mode) => ({ obs_mode }));
  assertEquals(opsChanged(r("south", "south", "north", "north")), { from: "north", to: "south" });
  assertEquals(opsChanged(r("south", "north", "north", "north")), null);   // まだ1回だけ
  assertEquals(opsChanged(r("north", "north", "north", "north")), null);
  assertEquals(opsChanged(r("south", "south", null, "north")), null);
  assertEquals(opsChanged([{ obs_mode: "south", obs_mixed: true }, ...r("south", "north", "north")]), null);
});

Deno.test("機種のまとまり：ICAO の記号と時刻表の書き方の両方", () => {
  const t = ["B77W", "77W", "B789", "789", "B763", "B744", "B738", "B38M", "A359", "A35K", "A333", "A388", "A320", "A21N", "321", "E190", "E75L", "DH8D", "Q4A", "AT76", "SF34", "C172", ""];
  assertEquals(t.map(famOf), ["777", "777", "787", "787", "767", "747", "737", "737", "A350", "A350", "A330", "A380", "A320", "A320", "A320", "small", "small", "small", "small", "small", "small", "other", null]);
});

Deno.test("表示する機体と同じ選び方で知らせる：機種のまとまりと、1機ずつ選んだ特別塗装機", () => {
  const s = sub({ spot_kinds: [], spot_regs: [], spot_fams: ["787", "small"], spot_livs: ["嵐ジェット"] });
  assertEquals(spotReason({ ...plane, type: "B789" }, s, undefined, NOW), { why: "fam", label: "787" });
  assertEquals(spotReason({ ...plane, type: "DH8D" }, s, undefined, NOW)?.label, "小さな機体");
  assertEquals(spotReason(plane, s, undefined, NOW), null);   // 737 は選んでいない
  assertEquals(spotReason(plane, s, { name: "嵐ジェット", kind: "special" }, NOW)?.why, "special");
  assertEquals(spotReason(plane, s, { name: "ミッキー", kind: "special" }, NOW), null);   // 選んでいない塗装機
  assertEquals(spotReason({ ...plane, type: "A359" }, sub({ spot_fams: undefined }), undefined, NOW)?.why, "big");   // 欄がない古い行もこれまでどおり
});

Deno.test("離陸の知らせ：離陸も知らせるを選んだ人だけ（選んだ便は別）。機種は時刻表の書き方でも", () => {
  const dep = (o: Partial<SpotDep> = {}): SpotDep => ({ flight: "NH106", dep: "HND", arr: "LAX", svc_date: "2026-10-21", aircraft: "77W", reg: null, livery: null, gate_actual: true, takeoff: new Date(NOW + 4.5 * 60_000).toISOString(), ...o });
  const on = sub({ spot_kinds: ["big", "dep"] });
  assertEquals(spotDepReason(dep(), on)?.why, "big");                                  // 77W は大きな機体
  assertEquals(spotDepReason(dep(), sub({ spot_kinds: ["big"] })), null);               // 離陸も知らせるを選んでいない
  assertEquals(spotDepReason(dep({ dep: "NRT" }), on), null);                           // ほかの空港
  assertEquals(spotDepReason(dep({ aircraft: "738" }), on), null);                      // 小さな機体
  assertEquals(spotDepReason(dep({ aircraft: "738" }), sub({ spot_kinds: [], spot_flights: ["NH106@2026-10-21"] }))?.why, "flight");   // 選んだ便は離陸も
  assertEquals(spotDepReason(dep({ aircraft: "738", livery: "嵐ジェット" }), sub({ spot_kinds: ["dep"], spot_livs: ["嵐ジェット"] }))?.label, "特別塗装機「嵐ジェット」");
  assertEquals(spotDepReason(dep({ aircraft: "Q4A" }), sub({ spot_kinds: ["dep"], spot_fams: ["small"] }))?.why, "fam");
  assert(dueNow(depEtaMin(dep(), NOW), 5) && !dueNow(depEtaMin(dep(), NOW), 3));
  const m = spotDepMessage(dep(), { label: "大きな機体" }, "羽田", 4.5);
  assertEquals(m.title, "そらメモ：NH106 があと約5分で離陸");
  assert(m.body.includes("出発した時刻と地上走行"));
});
