import { assertEquals } from "jsr:@std/assert@1";
import { normalize, parseAtc } from "../functions/_shared/atc_parse.ts";

Deno.test("数の言葉と続く数字をつなぐ", () => {
  assertEquals(normalize("Japan Air one two three, descend and maintain four thousand"), "JAPAN AIR 123 DESCEND AND MAINTAIN 4000");
  assertEquals(normalize("contact tower 118.1"), "CONTACT TOWER 118 DECIMAL 1");
  assertEquals(normalize("niner thousand five hundred"), "9500");
});
Deno.test("着陸許可と風", () => {
  const r = parseAtc("Japan Air 123, runway 22, cleared to land, wind 200 at 18.");
  assertEquals(r.callsign, "JAL123"); assertEquals(r.flight, "JL123");
  assertEquals(r.items[0], { k: "land", rwy: "22" });
  assertEquals(r.ja, "22滑走路への着陸を許可。風は200度から18ノット。");
  assertEquals(r.tags, ["着陸許可"]);
});
Deno.test("離陸許可（左右つき）", () => {
  const r = parseAtc("All Nippon 106, wind 160 at 12, runway 16 right, cleared for takeoff");
  assertEquals(r.flight, "NH106"); assertEquals(r.items[0], { k: "takeoff", rwy: "16R" });
});
Deno.test("地上走行：誘導路と手前で待機", () => {
  const r = parseAtc("All Nippon 106, taxi to holding point runway 16 right via Charlie, Hotel, hold short of runway 22");
  const tx = r.items.find((i) => i.k === "taxi");
  assertEquals(tx, { k: "taxi", to: "16R", via: ["C", "H"] });
  assertEquals(r.items.find((i) => i.k === "hold"), { k: "hold", at: "RWY 22" });
  assertEquals(r.ja, "16R滑走路へ。誘導路 C・H を通る。22滑走路の手前で待機。");
  const s = parseAtc("Skymark 105, taxi to spot 61 via Bravo 5, Alpha");
  assertEquals(s.items[0], { k: "taxi", to: "SPOT 61", via: ["B5", "A"] });
  assertEquals(s.flight, "BC105");
});
Deno.test("ゴーアラウンド・方向・高度・切り替え", () => {
  const r = parseAtc("Skymark 511, go around, turn left heading 090, climb and maintain 3000, contact departure 126.0");
  assertEquals(r.items.map((i) => i.k), ["goaround", "contact", "alt", "hdg"]);
  assertEquals(r.ja.includes("ゴーアラウンド"), true); assertEquals(r.ja.includes("高度 3,000ft まで上昇".replace(" まで", "まで")), true);
  assertEquals(r.items.find((i) => i.k === "contact"), { k: "contact", unit: "DEPARTURE", freq: "126.0" });
});
Deno.test("進入許可と速度", () => {
  const r = parseAtc("Japan Air 903, reduce speed to 210, cleared ILS Z approach runway 34 left");
  assertEquals(r.items.map((i) => i.k), ["app", "spd"]);
  assertEquals(r.items[0], { k: "app", type: "ILS", rwy: "34L" });
});
Deno.test("分からないものは出さない", () => {
  const r = parseAtc("roger");
  assertEquals(r.items.length, 0); assertEquals(r.callsign, null); assertEquals(r.ja, "");
});
