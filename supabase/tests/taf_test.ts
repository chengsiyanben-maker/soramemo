import { assertEquals } from "jsr:@std/assert@1";
import { awcDate, backDates, tafHours, tafRow, visM } from "../functions/_shared/taf.ts";
import { OPS_AIRPORTS } from "../functions/_shared/ops_core.js";

// aviationweather.gov の TAF（format=json）の本物の形（11/25 05:05Z の羽田。使う項目だけ）
const RJTT = { "icaoId": "RJTT", "issueTime": "2026-11-25T05:05:00.000Z", "validTimeFrom": 1795586400, "validTimeTo": 1795694400, "rawTAF": "TAF RJTT 250505Z 2506/2612 14006KT 9999 FEW030 BECMG 2511/2513 04006KT BECMG 2600/2603 16006KT BECMG 2609/2612 30006KT", "fcsts": [{ "timeFrom": 1795586400, "timeTo": 1795604400, "timeBec": null, "fcstChange": null, "probability": null, "wdir": 140, "wspd": 6, "wgst": null, "visib": "6+", "wxString": null }, { "timeFrom": 1795604400, "timeTo": 1795651200, "timeBec": 1795611600, "fcstChange": "BECMG", "probability": null, "wdir": 40, "wspd": 6, "wgst": null, "visib": "6+", "wxString": null }, { "timeFrom": 1795651200, "timeTo": 1795683600, "timeBec": 1795662000, "fcstChange": "BECMG", "probability": null, "wdir": 160, "wspd": 6, "wgst": null, "visib": "6+", "wxString": null }, { "timeFrom": 1795683600, "timeTo": 1795694400, "timeBec": 1795694400, "fcstChange": "BECMG", "probability": null, "wdir": 300, "wspd": 6, "wgst": null, "visib": "6+", "wxString": null }] };
// deno-lint-ignore no-explicit-any
const est = (iata: string) => (m: any, at: Date) => (OPS_AIRPORTS as any)[iata].estimate(m, at).mode;

Deno.test("TAF の原文の行", () => {
  const r = tafRow(RJTT)!;
  assertEquals(r.icao, "RJTT");
  assertEquals(r.issued, "2026-11-25T05:05:00.000Z");
  assertEquals(r.valid_from, "2026-11-25T06:00:00.000Z");
  assertEquals(r.valid_to, "2026-11-26T12:00:00.000Z");
  assertEquals(tafRow({ ...RJTT, icaoId: "xx" }), null);
  assertEquals(tafRow({ ...RJTT, rawTAF: "" }), null);
});

Deno.test("時間ごとの風：基本・BECMG（途中は changing）", () => {
  const h = tafHours(RJTT);
  assertEquals(h.length, 30);                       // 2506/2612 の30時間
  assertEquals(h[0].at, "2026-11-25T06:00:00.000Z");
  assertEquals(h[0].lead_h, 1);
  assertEquals([h[0].wdir, h[0].wspd, h[0].vis_m, h[0].changing], [140, 6, 9999, false]);
  assertEquals([h[5].wdir, h[5].changing], [40, true]);   // 11Z：BECMG 2511/2513 の途中
  assertEquals([h[7].wdir, h[7].changing], [40, false]);  // 13Z：変わり終わった
  assertEquals(h[18].wdir, 160);                    // 26日 00Z
  assertEquals(h[29].wdir, 300);                    // 26日 11Z
});

Deno.test("TEMPO・PROB は別の列・VRB は向きなし", () => {
  const t = structuredClone(RJTT);
  t.fcsts.push({ timeFrom: 1795604400, timeTo: 1795615200, timeBec: null, fcstChange: "TEMPO", probability: null, wdir: 180, wspd: 20, wgst: 32, visib: "3", wxString: "SHRA" } as never);
  t.fcsts.push({ timeFrom: 1795604400, timeTo: 1795611600, timeBec: null, fcstChange: "PROB", probability: 30, wdir: "VRB", wspd: 15, wgst: null, visib: "6+", wxString: "TSRA" } as never);
  t.fcsts[0].wdir = "VRB" as never;
  const h = tafHours(t);
  assertEquals([h[0].wdir, h[0].vrb], [null, true]);
  assertEquals([h[5].t_kind, h[5].t_wdir, h[5].t_wspd, h[5].t_wgst], ["TEMPO", 180, 20, 32]);   // 突風の強い TEMPO を選ぶ
  assertEquals(h[8].t_kind, null);
  assertEquals(visM("3"), 4828);
  assertEquals(visM(null), null);
});

Deno.test("時間ごとの推定の運用（羽田は時刻も使う・成田は風だけ）", () => {
  const s = structuredClone(RJTT);
  s.fcsts[0].wdir = 180; s.fcsts[0].wspd = 15;
  const h = tafHours(s, est("HND"));
  assertEquals(h[0].est_mode, "city");      // 06Z＝15時（日本時間）・南風 15kt
  assertEquals(h[3].est_mode, "city");      // 09Z＝18時（都心ルートの時間の中）
  assertEquals(h[4].est_mode, "south");     // 10Z＝19時（都心ルートの時間の外）
  assertEquals(h[5].est_mode, "north");     // 11Z＝20時・北東の風
  assertEquals(h[14].est_mode, "nightN");   // 20Z＝5時（深夜）
  const n = tafHours(s, est("NRT"));
  assertEquals(n[0].est_mode, "a");         // 南風 → 16運用
});

Deno.test("さかのぼる時刻", () => {
  const c = Date.parse("2026-11-25T00:00:00Z");
  assertEquals(backDates(c, Date.parse("2026-10-15T00:00:00Z")).length, 8);
  assertEquals(backDates(c, Date.parse("2026-11-24T18:00:00Z")).length, 2);
  assertEquals(awcDate(Date.parse("2026-11-24T21:00:00Z")), "20261124_2100");
});
