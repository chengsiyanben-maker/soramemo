// FAA NAS Status の XML を読む：地上待機・出発の間引き・閉鎖・出発／到着の遅れ・除氷、就航先だけ残す、時刻の読み方、古い判定
import { assertEquals } from "jsr:@std/assert@1";
import { isStale, parseClock, parseDayTime, parseMinutes, parseNas, parseUpdateTime } from "../functions/_shared/faa_nas.ts";

const XML = `<?xml version="1.0" encoding="UTF-8"?>
<AIRPORT_STATUS_INFORMATION>
  <Update_Time>Sun Nov 15 01:02:03 2026 GMT</Update_Time>
  <Dtd_File>http://www.fly.faa.gov/AirportStatus.dtd</Dtd_File>
  <Delay_type>
    <Name>Ground Delay Programs</Name>
    <Ground_Delay_List>
      <Ground_Delay><ARPT>SFO</ARPT><Reason>low ceilings</Reason><Avg>1 hour and 3 minutes</Avg><Max>2 hours and 1 minute</Max></Ground_Delay>
      <Ground_Delay><ARPT>PHL</ARPT><Reason>wind</Reason><Avg>45 minutes</Avg><Max>1 hour</Max></Ground_Delay>
    </Ground_Delay_List>
  </Delay_type>
  <Delay_type>
    <Name>Ground Stop Programs</Name>
    <Ground_Stop_List>
      <Program><ARPT>LAX</ARPT><Reason>equipment / outage</Reason><End_Time>6:30 pm PST</End_Time></Program>
    </Ground_Stop_List>
  </Delay_type>
  <Delay_type>
    <Name>General Arrival/Departure Delay Info</Name>
    <Arrival_Departure_Delay_List>
      <Delay><ARPT>EWR</ARPT><Reason>WX:Low Ceilings</Reason>
        <Arrival_Departure Type="Arrival"><Min>16 minutes</Min><Max>30 minutes</Max><Trend>Increasing</Trend></Arrival_Departure>
        <Arrival_Departure Type="Departure"><Min>31 minutes</Min><Max>45 minutes</Max><Trend>Decreasing</Trend></Arrival_Departure>
      </Delay>
    </Arrival_Departure_Delay_List>
  </Delay_type>
  <Delay_type>
    <Name>Airport Closures</Name>
    <Airport_Closure_List>
      <Airport><ARPT>GUM</ARPT><Reason>!GUM 11/045 GUM AD AP CLSD &amp; TYPHOON</Reason><Start>Nov 14 at 20:00 UTC.</Start><Reopen>Nov 15 at 06:00 UTC.</Reopen></Airport>
    </Airport_Closure_List>
  </Delay_type>
  <Delay_type>
    <Name>Airspace Flow Programs</Name>
    <Airspace_Flow_List><Airspace_Flow><CTL_Element>FCAA05</CTL_Element><Reason>WX</Reason></Airspace_Flow></Airspace_Flow_List>
  </Delay_type>
</AIRPORT_STATUS_INFORMATION>`;

Deno.test("Update_Time を読む", () => {
  assertEquals(new Date(parseUpdateTime("Sun Nov 15 01:02:03 2026 GMT")!).toISOString(), "2026-11-15T01:02:03.000Z");
  assertEquals(parseUpdateTime(null), null);
  assertEquals(parseUpdateTime("よめない"), null);
});

Deno.test("遅れの分を読む", () => {
  assertEquals([parseMinutes("1 hour and 3 minutes"), parseMinutes("45 minutes"), parseMinutes("2 hours"), parseMinutes("?")], [63, 45, 120, null]);
});

Deno.test("終わりの時刻（日付なし）は取った時刻より後のいちばん近い時刻", () => {
  const ref = Date.parse("2026-11-15T01:02:03Z");   // 太平洋の標準時で 11/14 17:02
  assertEquals(new Date(parseClock("6:30 pm PST", ref)!).toISOString(), "2026-11-15T02:30:00.000Z");
  // 過ぎて1時間より前なら次の日
  assertEquals(new Date(parseClock("3:00 pm PST", ref)!).toISOString(), "2026-11-15T23:00:00.000Z");
  assertEquals(parseClock("6:30 pm XYZ", ref), null);
});

Deno.test("閉鎖の始まり・再開（年は取った時刻から、年をまたいでも近い方）", () => {
  const ref = Date.parse("2026-11-15T01:00:00Z");
  assertEquals(new Date(parseDayTime("Nov 15 at 06:00 UTC.", ref)!).toISOString(), "2026-11-15T06:00:00.000Z");
  assertEquals(new Date(parseDayTime("Jan 2 at 0400 UTC", Date.parse("2026-12-31T20:00:00Z"))!).toISOString(), "2027-01-02T04:00:00.000Z");
});

Deno.test("XML を読み、就航先（日本から直行便のある空港）だけ残す", () => {
  const { updatedAt, rows } = parseNas(XML);
  assertEquals(new Date(updatedAt!).toISOString(), "2026-11-15T01:02:03.000Z");
  const by = Object.fromEntries(rows.map((r) => [`${r.iata}|${r.kind}`, r]));
  assertEquals(Object.keys(by).sort(), ["EWR|delay_arr", "EWR|delay_dep", "GUM|closure", "LAX|ground_stop", "SFO|gdp"]);   // PHL は就航先でない・空域は使わない
  assertEquals([by["SFO|gdp"].avg_delay, by["SFO|gdp"].max_delay, by["SFO|gdp"].reason], [63, 121, "low ceilings"]);
  assertEquals(by["LAX|ground_stop"].ends, "2026-11-15T02:30:00.000Z");
  assertEquals([by["GUM|closure"].starts, by["GUM|closure"].ends, by["GUM|closure"].reason],
    ["2026-11-14T20:00:00.000Z", "2026-11-15T06:00:00.000Z", "!GUM 11/045 GUM AD AP CLSD & TYPHOON"]);
  assertEquals([by["EWR|delay_arr"].avg_delay, by["EWR|delay_arr"].max_delay, by["EWR|delay_arr"].trend, by["EWR|delay_dep"].trend], [16, 30, "increasing", "decreasing"]);
});

Deno.test("就航先で絞らなければ全部の空港", () => {
  assertEquals(parseNas(XML, null).rows.some((r) => r.iata === "PHL"), true);
});

Deno.test("空の XML・止まっている空港がないときは0行", () => {
  assertEquals(parseNas("<AIRPORT_STATUS_INFORMATION><Update_Time>Sun Nov 15 01:02:03 2026 GMT</Update_Time></AIRPORT_STATUS_INFORMATION>").rows, []);
  assertEquals(parseNas("").updatedAt, null);
});

Deno.test("Update_Time が10分より前・読めないときは古い", () => {
  const t = Date.parse("2026-11-15T01:02:03Z");
  assertEquals([isStale(t, t + 9 * 60_000), isStale(t, t + 11 * 60_000), isStale(null, t)], [false, true, true]);
});
