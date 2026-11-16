// ODPT のデータの時刻（dc:date）の取り出し（_shared/odpt_date.ts）
import { assertEquals } from "jsr:@std/assert@1";
import { feedDates, maxDcDate, putFeedDates } from "../functions/_shared/odpt_date.ts";

Deno.test("いちばん新しい dc:date を ISO で返す（時間帯つきの文字も比べられる）", () => {
  assertEquals(maxDcDate([{ "dc:date": "2026-11-16T14:30:00+09:00" }, { "dc:date": "2026-11-16T05:40:00Z" }, { "dc:date": "2026-11-16T14:35:00+09:00" }]), "2026-11-16T05:40:00.000Z");
});

Deno.test("dc:date がない・形がちがうものは飛ばし、なければ null", () => {
  assertEquals(maxDcDate([]), null);
  assertEquals(maxDcDate([null, 1, "x", {}, { "dc:date": 123 }, { "dc:date": "きのう" }]), null);
  assertEquals(maxDcDate([{ "dc:date": "きのう" }, { "dc:date": "2026-11-16T09:00:00+09:00" }]), "2026-11-16T00:00:00.000Z");
});

Deno.test("種類と航空会社ごとに分ける（来なかった会社も件数0で残す）", () => {
  const items = [
    { "odpt:operator": "odpt.Operator:JAL", "dc:date": "2026-11-16T14:30:00+09:00" },
    { "odpt:operator": "odpt.Operator:JAL", "dc:date": "2026-11-16T14:31:00+09:00" },
    { "odpt:operator": "odpt.Operator:ANA", "dc:date": "2026-11-16T14:20:00+09:00" },
    { "odpt:operator": "odpt.Operator:bad name!", "dc:date": "2026-11-16T15:00:00+09:00" },
    { "dc:date": "2026-11-16T15:00:00+09:00" },
  ];
  assertEquals(feedDates("FlightInformationDeparture", items, ["JAL", "ANA", "SKY"]), [
    { feed: "FlightInformationDeparture:JAL", dc_date: "2026-11-16T05:31:00.000Z", n: 2 },
    { feed: "FlightInformationDeparture:ANA", dc_date: "2026-11-16T05:20:00.000Z", n: 1 },
    { feed: "FlightInformationDeparture:SKY", dc_date: null, n: 0 },
  ]);
  assertEquals(feedDates("FlightSchedule", []), []);
});

Deno.test("残すのに失敗しても例外にせず、エラーの文だけ返す", async () => {
  const ok = { rpc: (_n: string, _a: unknown) => Promise.resolve({ error: null }) };
  const ng = { rpc: () => Promise.resolve({ error: { message: "denied" } }) };
  const boom = { rpc: () => Promise.reject(new Error("net")) };
  const row = [{ feed: "FlightSchedule:JAL", dc_date: null, n: 0 }];
  assertEquals(await putFeedDates(ok, row), null);
  assertEquals(await putFeedDates(ng, row), "feed_date denied");
  assertEquals(await putFeedDates(boom, row), "feed_date net");
  let called = false;
  assertEquals(await putFeedDates({ rpc: () => { called = true; return Promise.resolve({ error: null }); } }, []), null);
  assertEquals(called, false);
});
