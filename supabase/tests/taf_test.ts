import { assertEquals } from "jsr:@std/assert@1";
import { tafBackDates, type TafHourRow, tafRows } from "../functions/_shared/taf.ts";
import { recordStep } from "../functions/_shared/traffic.ts";

// 11/25 に aviationweather.gov から取った羽田の TAF（形をそのまま）
const RJTT = {
  icaoId: "RJTT", issueTime: "2026-11-25T05:05:00.000Z", validTimeFrom: 1795586400, validTimeTo: 1795694400,
  rawTAF: "TAF RJTT 250505Z 2506/2612 14006KT 9999 FEW030 BECMG 2511/2513 04006KT BECMG 2600/2603 16006KT BECMG 2609/2612 30006KT",
  fcsts: [
    { timeFrom: 1795586400, timeTo: 1795604400, timeBec: null, fcstChange: null, wdir: 140, wspd: 6, wgst: null, visib: "6+" },
    { timeFrom: 1795604400, timeTo: 1795651200, timeBec: 1795611600, fcstChange: "BECMG", wdir: 40, wspd: 6, wgst: null, visib: "6+" },
    { timeFrom: 1795651200, timeTo: 1795683600, timeBec: 1795662000, fcstChange: "BECMG", wdir: 160, wspd: 6, wgst: null, visib: "6+" },
    { timeFrom: 1795683600, timeTo: 1795694400, timeBec: 1795694400, fcstChange: "BECMG", wdir: 300, wspd: 6, wgst: null, visib: "6+" },
  ],
};
const hourOf = (rows: TafHourRow[], iso: string) => rows.find((r) => r.hr === iso);

Deno.test("TAF の原文の行と1時間ごとの行", () => {
  const x = tafRows(RJTT)!;
  assertEquals(x.obs, { icao: "RJTT", issued_at: "2026-11-25T05:05:00.000Z", valid_from: "2026-11-25T06:00:00.000Z", valid_to: "2026-11-26T12:00:00.000Z", raw: RJTT.rawTAF });
  assertEquals(x.hours.length, 30);   // 06Z〜翌12Z
  assertEquals(hourOf(x.hours, "2026-11-25T06:00:00.000Z")?.wdir, 140);
  // BECMG 2511/2513：変わり終わる13時から。11・12時の行は前の140°のまま
  assertEquals(hourOf(x.hours, "2026-11-25T12:00:00.000Z")?.wdir, 140);
  assertEquals(hourOf(x.hours, "2026-11-25T13:00:00.000Z")?.wdir, 40);
  assertEquals(hourOf(x.hours, "2026-11-26T03:00:00.000Z")?.wdir, 160);
  assertEquals(hourOf(x.hours, "2026-11-26T11:00:00.000Z")?.wdir, 160);   // 最後の BECMG は終わりの12Z に変わり終わる
  assertEquals(hourOf(x.hours, "2026-11-25T06:00:00.000Z")?.vis_m, 10000);
});

Deno.test("TEMPO の強い風と、書いていない要素の引き継ぎ、VRB", () => {
  const x = tafRows({
    icaoId: "RJAA", issueTime: "2026-11-25T05:05:00Z", validTimeFrom: 1795586400, validTimeTo: 1795600800, rawTAF: "TAF RJAA ...",
    fcsts: [
      { timeFrom: 1795586400, timeTo: 1795600800, fcstChange: null, wdir: 200, wspd: 12, wgst: 22, visib: "6+" },
      { timeFrom: 1795590000, timeTo: 1795597200, fcstChange: "TEMPO", wdir: 220, wspd: 18, wgst: 30, visib: "3" },
      { timeFrom: 1795593600, timeTo: 1795600800, timeBec: 1795593600, fcstChange: "BECMG", wdir: "VRB", wspd: 3, wgst: null, visib: null },
    ],
  })!;
  assertEquals(x.hours.length, 4);
  const [h6, h7, h8, h9] = x.hours;
  assertEquals([h6.wdir, h6.wspd, h6.wgst, h6.t_wspd], [200, 12, 22, null]);
  assertEquals([h7.t_wdir, h7.t_wspd, h7.t_wgst], [220, 18, 30]);
  assertEquals([h8.wdir, h8.wspd, h8.wgst, h8.vis_m, h8.t_wspd], [null, 3, null, 10000, 18]);   // VRB は null・視程は前の値を引き継ぐ
  assertEquals(h9.t_wspd, null);
});

Deno.test("形の合わない TAF は残さない", () => {
  assertEquals(tafRows({ icaoId: "RJTT" }), null);
  assertEquals(tafRows({ ...RJTT, validTimeTo: RJTT.validTimeFrom }), null);
  assertEquals(tafRows({ ...RJTT, issueTime: "bad" }), null);
  assertEquals(tafRows({ ...RJTT, icaoId: "HND" }), null);
});

Deno.test("さかのぼる時刻は3時間おき・新しい順", () => {
  const now = Date.parse("2026-11-25T09:43:00Z");
  const d = tafBackDates(now, 1);
  assertEquals(d[0], "2026-11-25T09:00:00Z");
  assertEquals(d.length, 8);
  assertEquals(d.at(-1), "2026-11-24T12:00:00Z");
  assertEquals(tafBackDates(now, 1, 7)[0], "2026-11-18T09:00:00Z");
});

Deno.test("記録の処理：東の円（羽田・成田）を優先する", () => {
  const none = new Set<string>(), east = new Set(["EAST"]), west = new Set(["WEST"]);
  assertEquals(recordStep("EAST", false, none), "go");
  assertEquals(recordStep("NORTH", true, none), "go");
  assertEquals(recordStep("EAST", false, east), "skip");     // 同じ円を取り直さない
  assertEquals(recordStep("NORTH", true, east), "yield");    // 東が取れなかった回は新千歳・那覇を休む
  assertEquals(recordStep("SOUTH", true, west), "go");       // 西が取れなかっただけなら休まない
  assertEquals(recordStep("WEST", false, east), "go");
});
