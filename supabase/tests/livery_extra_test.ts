// 特別塗装機の一覧の足し分（livery_extra）と、海外の塗装機の早めの知らせ（11/16 案1-A・案2-A・案3-A）
import { assertEquals } from "jsr:@std/assert@1";
import { LIVERIES, liveryMap } from "../functions/_shared/liveries.ts";
import { hhmm, inboundEtaMin, jaTime, inboundMessage, mergeLiveries, pickDest, wantsInbound, wantsLiveryPush } from "../functions/_shared/livery_extra.ts";

const ROWS = [
  { reg: "g-ymmu", name: "ワンワールド塗装（777-200ER）", airline: "ブリティッシュ・エアウェイズ", kind: "alliance", src: "https://example.org/ba", from_day: null, until_day: null },
  { reg: "9V-OJJ", name: "ピカチュウジェットTR（名前の直し）", airline: "スクート", kind: "special", src: "https://example.org/tr", until_day: "2026-12-31" },
  { reg: "N1", name: "形が違う", airline: "x", src: "https://example.org/" },
  { reg: "N12345", name: "FR24 の出典", airline: "x", src: "https://www.flightradar24.com/blog/x" },
  { reg: "N54321", name: "http の出典", airline: "x", src: "http://example.org/" },
];

Deno.test("表の行を合わせる：同じ登録記号は表を使い、形の合わない行・FR24・http は使わない", () => {
  const list = mergeLiveries(LIVERIES, ROWS);
  const m = liveryMap(new Date("2026-11-16"), list);
  assertEquals(m.get("G-YMMU")?.kind, "alliance");   // 小文字も大文字にそろえる
  assertEquals(m.get("9V-OJJ")?.name, "ピカチュウジェットTR（名前の直し）");
  assertEquals(list.filter((l) => l.reg === "9V-OJJ").length, 1);
  assertEquals(liveryMap(new Date("2027-01-01"), list).has("9V-OJJ"), false);   // 表の until_day で外れる
  assertEquals(m.has("N1") || m.has("N12345") || m.has("N54321"), false);
  assertEquals(mergeLiveries(LIVERIES, null).length, LIVERIES.length);   // 表が読めないときはコードの一覧だけ
});

Deno.test("案3-A：アライアンス塗装は海外の会社のものだけ知らせる", () => {
  assertEquals(wantsLiveryPush({ reg: "JA861J", kind: "alliance" }), false);
  assertEquals(wantsLiveryPush({ reg: "G-YMMR", kind: "alliance" }), true);
  assertEquals(wantsLiveryPush({ reg: "JA819A", kind: "special" }), true);
  assertEquals(wantsLiveryPush({ reg: "B-18101" }), true);
});

const base = { reg: "G-YMMR", name: "ワンワールド塗装（777-200ER）", airline: "ブリティッシュ・エアウェイズ", kind: "alliance", callsign: "BAW5", lat: 37.5, lon: 141.5, alt_ft: 35000, kt: 480, trk: 225 };
const AP = new Map([["HND", { lat: 35.5533, lon: 139.7811 }], ["NRT", { lat: 35.7772, lon: 140.3823 }], ["KIX", { lat: 34.4336, lon: 135.2336 }]]);

Deno.test("早めに知らせる相手：海外の塗装機・便名あり・5,000ft より上・まだ空港の近くで分かっていない", () => {
  assertEquals(wantsInbound(base), true);
  assertEquals(wantsInbound({ ...base, reg: "JA861J" }), false);
  assertEquals(wantsInbound({ ...base, callsign: null }), false);
  assertEquals(wantsInbound({ ...base, alt_ft: 3000 }), false);
  assertEquals(wantsInbound({ ...base, phase: "arr", iata: "HND" }), false);
});

Deno.test("行き先：向いている日本の空港だけ。後ろの空港・遠すぎる空港・表にない空港は選ばない", () => {
  assertEquals(pickDest(base, [{ iata: "HND", mins: 600 }], AP)?.iata, "HND");
  assertEquals(pickDest({ ...base, trk: 45 }, [{ iata: "HND" }], AP), null);   // 反対へ飛んでいる
  assertEquals(pickDest(base, [{ iata: "LHR" }], AP), null);                  // 日本の空港ではない
  assertEquals(pickDest({ ...base, lat: 50, lon: 150 }, [{ iata: "HND" }], AP), null);   // 1,500km より遠い
  assertEquals(pickDest({ ...base, trk: null }, [{ iata: "HND" }, { iata: "KIX" }], AP), null);   // 向きが分からず候補が2つ
  assertEquals(pickDest({ ...base, trk: null }, [{ iata: "HND" }], AP)?.iata, "HND");
  assertEquals(pickDest(base, [{ iata: "KIX" }, { iata: "HND" }], AP)?.iata, "HND");   // 近いほう
});

Deno.test("着く見込み：距離と速さから。ふだんの時刻が40分以内ならそちら", () => {
  assertEquals(inboundEtaMin(370.4, 400, null), 42);   // 200海里 ÷ 400ノット = 30分 ＋ 降りる分12分
  assertEquals(inboundEtaMin(50, 100, null), 4 + Math.round(50 / 1.852 / 450 * 60));   // 遅すぎる速さは450ノット
  const now = Date.parse("2026-11-16T01:00:00Z");   // 日本時間 10:00
  assertEquals(inboundEtaMin(370.4, 400, 10 * 60 + 60, now), 60);   // ふだん11:00着（距離では42分）→ 60分
  assertEquals(inboundEtaMin(370.4, 400, 10 * 60 + 150, now), 42);  // ふだんの時刻が遠すぎる→距離のほう
  assertEquals(hhmm(now, 42), "10:42");
  const m = inboundMessage(base, { iata: "HND" }, "羽田", 42, now);
  assertEquals(m.body, "ワンワールド塗装（777-200ER）（ブリティッシュ・エアウェイズ・BAW5）が羽田に向かっています。着くのは10時42分ごろ（推定）。");
  assertEquals(m.body.split("推定").length - 1, 1); // 「（推定）」は1回だけ・「見込み」と重ねない
  assertEquals(m.body.includes("見込み"), false);
  assertEquals(jaTime(now, 42), "10時42分");
  assertEquals(jaTime(now, -60 * 3 + 5), "7時05分"); // 時は0を付けない・分は2けた
  const noCs = inboundMessage({ ...base, callsign: "" }, { iata: "HND" }, "羽田", 42, now);
  assertEquals(noCs.body, "ワンワールド塗装（777-200ER）（ブリティッシュ・エアウェイズ）が羽田に向かっています。着くのは10時42分ごろ（推定）。");
  assertEquals([m.tag, m.url], ["sp-G-YMMR", "./#ops-HND"]);
});
