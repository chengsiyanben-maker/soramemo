import { assertEquals } from "jsr:@std/assert@1";
import { cloudsFromRaw, fromObs, fromShared, OBS_MAX_MS, pickWx, SHARED_MAX_MS } from "../functions/_shared/checkin_wx.ts";

const NOW = Date.parse("2026-11-25T03:00:00Z");
const iso = (msAgo: number) => new Date(NOW - msAgo).toISOString();

Deno.test("原文から雲の層を取り出す（RMK より後ろは見ない・VV はくもり扱い）", () => {
  assertEquals(cloudsFromRaw("RJTT 250230Z 34008KT 9999 FEW020 BKN040 12/03 Q1021 RMK 1CU020"), [{ cover: "FEW" }, { cover: "BKN" }]);
  assertEquals(cloudsFromRaw("RJCC 250230Z 31012KT 0400 FG VV002 M02/M02 Q1012"), [{ cover: "OVX" }]);
  assertEquals(cloudsFromRaw("RJTT 250230Z 34008KT CAVOK 12/03 Q1021"), []);
});

Deno.test("天気の記録の1行から：BKN があればくもり（FEW だけで晴れにしない）", () => {
  assertEquals(fromObs({ at: iso(20 * 60_000), raw: "RJTT 250230Z 34008KT 9999 FEW020 BKN040 12/03 Q1021", wspd: 8 }, NOW), { weather: "cloudy", wind_kt: 8 });
  assertEquals(fromObs({ at: iso(20 * 60_000), raw: "RJTT 250230Z 34008KT 9999 FEW020 12/03 Q1021", wspd: 8 }, NOW), { weather: "clear", wind_kt: 8 });
  assertEquals(fromObs({ at: iso(5 * 60_000), raw: "RJCC 250230Z 31012KT 3000 -SN BKN010 M02/M04 Q1012", wspd: 12 }, NOW), { weather: "snow", wind_kt: 12 });
});

Deno.test("古すぎる記録・空の記録は使わない", () => {
  assertEquals(fromObs({ at: iso(OBS_MAX_MS + 60_000), raw: "RJTT 250130Z 34008KT 9999 FEW020 12/03 Q1021", wspd: 8 }, NOW), null);
  assertEquals(fromObs(undefined, NOW), null);
  assertEquals(fromObs({ at: iso(60_000), raw: "RJTT NIL", wspd: null }, NOW), null);
});

Deno.test("置き場（空港の今の形）から：sky と wspd、風は0〜200に丸める", () => {
  assertEquals(fromShared({ at: NOW - 60_000, v: { sky: "雨", wspd: 14.6 } }, NOW), { weather: "rain", wind_kt: 15 });
  assertEquals(fromShared({ at: NOW - 60_000, v: { sky: null, wspd: 250 } }, NOW), { weather: null, wind_kt: 200 });
  assertEquals(fromShared({ at: NOW - SHARED_MAX_MS - 1, v: { sky: "雨", wspd: 3 } }, NOW), null);
  assertEquals(fromShared({ at: NOW - 60_000, v: null }, NOW), null);
});

Deno.test("置き場を先に、なければ記録、どちらもなければ null（あとで配信元から書き足す）", () => {
  const sh = { at: NOW - 60_000, v: { sky: "晴れ", wspd: 5 } };
  const ob = { at: iso(10 * 60_000), raw: "RJTT 250250Z 34008KT 9999 -RA BKN020 12/03 Q1021", wspd: 8 };
  assertEquals(pickWx(sh, ob, NOW), { weather: "clear", wind_kt: 5 });
  assertEquals(pickWx(undefined, ob, NOW), { weather: "rain", wind_kt: 8 });
  assertEquals(pickWx(undefined, undefined, NOW), null);
});
