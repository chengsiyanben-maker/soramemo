// 空港の今：便と天気の整形
import { assertEquals } from "jsr:@std/assert@1";
import { flightNo, kindOf, normalize, recent, skyOf, terminal, weather } from "../functions/_shared/airport_now.ts";

Deno.test("便名：先頭の0を落とし、航空会社の2文字を分ける", () => {
  assertEquals(flightNo("JL0116"), { airline: "JL", no: "JL116" });
  assertEquals(flightNo(["NH40"]), { airline: "NH", no: "NH40" });
  assertEquals(flightNo("XYZ"), null);
});

Deno.test("ターミナル：Terminal1 → T1、国内線などは null", () => {
  assertEquals(terminal("odpt.AirportTerminal:HND.Terminal2"), "T2");
  assertEquals(terminal("odpt.AirportTerminal:CTS.Domestic"), null);
  assertEquals(terminal(undefined), null);
});

Deno.test("状況：欠航・到着済み・搭乗中・遅れ・定刻", () => {
  assertEquals(kindOf("odpt.FlightStatus:Cancelled", "10:00", null), "cancel");
  assertEquals(kindOf("odpt.FlightStatus:Arrived", "10:00", "09:58"), "done");
  assertEquals(kindOf("odpt.FlightStatus:Boarding", "10:00", null), "board");
  assertEquals(kindOf("odpt.FlightStatus:Delayed", "10:00", "10:20"), "late");
  assertEquals(kindOf("odpt.FlightStatus:OnTime", "10:00", null), "ok");
  assertEquals(kindOf(undefined, "10:00", "10:25"), "late");   // 知らない状況でも、時刻が遅れていれば遅れ
});

Deno.test("到着便の整形：出発地・変更後の時刻・ターミナル", () => {
  const r = normalize({
    "odpt:flightNumber": ["NH0040"], "odpt:scheduledArrivalTime": "21:25", "odpt:estimatedArrivalTime": "21:48",
    "odpt:departureAirport": "odpt.Airport:ITM", "odpt:arrivalAirportTerminal": "odpt.AirportTerminal:HND.Terminal2",
    "odpt:flightStatus": "odpt.FlightStatus:Delayed",
  }, "arr");
  assertEquals(r, { time: "21:25", newTime: "21:48", place: "ITM", airline: "NH", no: "NH40", term: "T2", kind: "late" });
});

Deno.test("出発便の整形：行き先。予定と同じ見込み時刻は変更なし", () => {
  const r = normalize({
    "odpt:flightNumber": "JL0335", "odpt:scheduledDepartureTime": "21:35", "odpt:estimatedDepartureTime": "21:35",
    "odpt:arrivalAirport": "odpt.Airport:FUK", "odpt:departureAirportTerminal": "odpt.AirportTerminal:HND.Terminal1",
  }, "dep");
  assertEquals(r?.place, "FUK");
  assertEquals(r?.newTime, null);
  assertEquals(r?.kind, "ok");
  assertEquals(normalize({ "odpt:flightNumber": "JL1" }, "dep"), null);   // 時刻がないものは捨てる
});

Deno.test("直近の便：前60分〜後180分、時刻順、同じ便名は1つ、日付またぎ", () => {
  const row = (time: string, no: string) => ({ time, newTime: null, place: "ITM", airline: no.slice(0, 2), no, term: null, kind: "ok" as const });
  const rows = [row("23:50", "JL1"), row("00:20", "NH2"), row("21:00", "JL3"), row("23:10", "JL4"), row("23:10", "JL4"), row("04:00", "NH5")];
  assertEquals(recent(rows, 23 * 60 + 30).map((x) => x.no), ["JL4", "JL1", "NH2"]);
});

Deno.test("空模様：雨・霧・雪・雷・晴れ・くもり", () => {
  assertEquals(skyOf(" RJTT 121230Z 34012KT 9999 -RA FEW010 BKN030 17/15 Q1012 "), "雨");
  assertEquals(skyOf(" RJSC 121200Z 00000KT 0400 FG VV002 10/10 Q1015 "), "霧");
  assertEquals(skyOf(" RJCC 121200Z 32020KT 2000 -SHSN BKN015 M02/M04 Q1003 "), "雪");
  assertEquals(skyOf(" RJFF 121200Z 25015KT 9999 VCTS FEW020CB 25/22 Q1008 "), "雷");
  assertEquals(skyOf(" RJTT 121230Z 34012KT CAVOK 17/10 Q1015 "), "晴れ");
  assertEquals(skyOf(" RJAA 121230Z 34012KT 9999 FEW030 17/10 Q1015 NOSIG ", [{ cover: "FEW" }]), "晴れ");
  assertEquals(skyOf(" RJAA 121230Z 34012KT 9999 BKN030 17/10 Q1015 RMK RA ", [{ cover: "BKN" }]), "くもり");   // 備考の RA は数えない
});

Deno.test("天気の整形：視程9999は10km以上", () => {
  const w = weather({ rawOb: "RJTT 121230Z 34012G22KT 9999 FEW030 17/10 Q1015", reportTime: "2026-10-12T12:30:00Z", wdir: 340, wspd: 12, wgst: 22, visib: "6+", clouds: [{ cover: "FEW" }] });
  assertEquals(w, { time: "2026-10-12T12:30:00Z", wdir: 340, wspd: 12, wgst: 22, vis_m: 10000, vis_plus: true, sky: "晴れ" });
});

import { amedasNearest, amedasWeather, tafPeriods } from "../functions/_shared/airport_now.ts";

Deno.test("TAF：これから先の区切りだけ、変化の種類つきで", () => {
  const now = 1791806400 + 3600;   // 最初の区切りの途中
  const f = [
    { timeFrom: 1791806400, timeTo: 1791860400, fcstChange: null, wdir: 360, wspd: 12, visib: "6+", clouds: [{ cover: "BKN" }] },
    { timeFrom: 1791860400, timeTo: 1791903600, timeBec: 1791871200, fcstChange: "BECMG", wdir: 80, wspd: 8, visib: "6+", clouds: [{ cover: "FEW" }] },
    { timeFrom: 1791870000, timeTo: 1791880000, fcstChange: "TEMPO", wdir: null, wspd: null, visib: "3", wxString: "-SHRA", clouds: [{ cover: "BKN" }] },
    { timeFrom: 1791700000, timeTo: 1791800000, fcstChange: null, wdir: 10, wspd: 5 },          // もう終わった区切りは捨てる
  ];
  const p = tafPeriods(f, now);
  assertEquals(p.map((x) => x.kind), ["base", "BECMG", "TEMPO"]);
  assertEquals(p[0].from, now);                       // 今の区切りは「今から」
  assertEquals(p[1].from, 1791871200);                // BECMG は変わり始めの時刻
  assertEquals([p[0].sky, p[1].sky, p[2].sky], ["くもり", "晴れ", "雨"]);
  assertEquals(p[2].vis_m, 4827);
});

Deno.test("アメダス：風を測っている近くの観測所。遠すぎれば使わない", () => {
  const table = {
    "1": { lat: [33, 7.0], lon: [139, 47.0], elems: "11112010", kjName: "八丈島" },
    "2": { lat: [33, 6.5], lon: [139, 47.5], elems: "11012010", kjName: "風なし" },      // 風を測っていない
    "3": { lat: [35, 0], lon: [139, 0], elems: "11112010", kjName: "遠い" },
  };
  assertEquals(amedasNearest(table, 33.115, 139.786)?.name, "八丈島");
  assertEquals(amedasNearest(table, 30, 130), null);
});

Deno.test("アメダス：風向の番号を角度に、風速 m/s をノットに。静穏と雨", () => {
  const w = amedasWeather({ windDirection: [16, 0], wind: [5.0, 0], temp: [18.4, 0], precipitation10m: [0.5, 0], precipitation1h: [1.5, 0] }, "八丈島", "2026-10-12T21:00:00+09:00");
  assertEquals([w.wdir, w.wspd, w.temp, w.sky, w.rain1h, w.calm], [360, 10, 18.4, "雨", 1.5, false]);
  const c = amedasWeather({ windDirection: [0, 0], wind: [0, 0], temp: [10, 0] }, "x", "t");
  assertEquals([c.wdir, c.calm, c.sky], [null, true, null]);
});
