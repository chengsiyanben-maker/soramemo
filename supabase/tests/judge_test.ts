import { assertEquals } from "jsr:@std/assert@1";
import { type Airport, decide, km, locate, RULE } from "../functions/_shared/judge.ts";
const { airports, terminals } = JSON.parse(await Deno.readTextFile(new URL("./fixtures.json", import.meta.url)));
const dms = (d: number, m: number, s: number) => d + m / 60 + s / 3600;
const HND = airports.find((a: any) => a.iata === "HND").id, CTS = airports.find((a: any) => a.iata === "CTS").id;
const now = Date.parse("2026-10-04T10:00:00Z");
const pos = (lat: number, lon: number, acc = 20, ts = now) => ({ lat, lon, acc, ts });

// 2026年10月 羽田の実測値（コンパスアプリ）と期待する判定
const field: [string, number, number, string | null][] = [
  ["T1 地下1階", dms(35, 32, 56), dms(139, 47, 4), "HND-T1"],
  ["T2 地上階", dms(35, 33, 3), dms(139, 47, 17), "HND-T2"],
  ["T2 国際線", dms(35, 32, 57), dms(139, 47, 23), "HND-T2"],
  ["T1 バス降車", dms(35, 32, 54), dms(139, 47, 8), "HND-T1"],
  ["T3", dms(35, 32, 39), dms(139, 46, 7), "HND-T3"],
  ["T3 2枚目", dms(35, 32, 42), dms(139, 46, 11), "HND-T3"],
  ["T2→T1 バス中間", dms(35, 32, 50), dms(139, 47, 20), null],
  ["トンネル中盤", dms(35, 33, 5), dms(139, 46, 31), null],
  ["空港南の道路 19:02", dms(35, 32, 18), dms(139, 46, 50), null],
];
for (const [name, lat, lon, term] of field) {
  Deno.test(`羽田実測: ${name}`, () => {
    const p = locate({ lat, lon }, airports, terminals);
    assertEquals(p.airport.id, HND); assertEquals(p.within, true); assertEquals(p.terminal?.id ?? null, term);
  });
}

Deno.test("範囲外（船橋）", () => {
  const d = decide(pos(35.6946, 139.9826), now, null, airports, terminals);
  assertEquals(d.ok, false); if (!d.ok) assertEquals(d.reason, "out_of_range");
});
Deno.test("誤差が大きい位置は拒否", () => {
  const d = decide(pos(35.5494, 139.7798, 3000), now, null, airports, terminals);
  assertEquals(d.ok ? "" : d.reason, "low_accuracy");
});
Deno.test("古い位置は拒否（端末で6分前に取得）", () => {
  const d = decide(pos(35.5494, 139.7798, 20, now - 6 * 60e3), now, null, airports, terminals);
  assertEquals(d.ok ? "" : d.reason, "stale_position");
});
Deno.test("同じターミナルへの30分以内の再チェックインは無視", () => {
  const d = decide(pos(dms(35, 32, 56), dms(139, 47, 4)), now, { airport_id: HND, terminal_id: "HND-T1", at: now - 10 * 60e3 }, airports, terminals);
  assertEquals(d.ok ? "" : d.reason, "already");
});
Deno.test("同じ空港の別ターミナルは記録するがフライトにはしない", () => {
  const d = decide(pos(dms(35, 33, 3), dms(139, 47, 17)), now, { airport_id: HND, terminal_id: "HND-T1", at: now - 10 * 60e3 }, airports, terminals);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.place.terminal?.id, "HND-T2"); assertEquals(d.flight, null); }
});
Deno.test("連打は拒否", () => {
  const d = decide(pos(35.7720, 140.3929), now, { airport_id: HND, terminal_id: "HND-T1", at: now - 5e3 }, airports, terminals);
  assertEquals(d.ok ? "" : d.reason, "too_soon");
});
Deno.test("羽田→新千歳（1時間40分）はフライト成立", () => {
  const cts = airports.find((a: any) => a.id === CTS);
  const d = decide(pos(cts.lat, cts.lon), now, { airport_id: HND, terminal_id: "HND-T2", at: now - 100 * 60e3 }, airports, terminals);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.flight?.from, HND); assertEquals(d.flight?.to, CTS); assertEquals(Math.round(d.flight!.km / 10), 82); }
});
Deno.test("羽田→新千歳を10分は不可能な速さ：フライトにせず印を付ける", () => {
  const cts = airports.find((a: any) => a.id === CTS);
  const d = decide(pos(cts.lat, cts.lon), now, { airport_id: HND, terminal_id: "HND-T2", at: now - 10 * 60e3 }, airports, terminals);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.flight, null); assertEquals(d.flags.includes("impossible_speed"), true); }
});
Deno.test("24時間を超えるとフライトにしない", () => {
  const cts = airports.find((a: any) => a.id === CTS);
  const d = decide(pos(cts.lat, cts.lon), now, { airport_id: HND, terminal_id: null, at: now - (RULE.flightMaxGapH + 1) * 36e5 }, airports, terminals);
  assertEquals(d.ok, true); if (d.ok) assertEquals(d.flight, null);
});

// ---------- 電波がなく保留していたチェックイン ----------
Deno.test("保留：3時間前の位置も受け付け、時刻は端末で取った時刻、offlineの印", () => {
  const ts = now - 3 * 36e5;
  const d = decide(pos(dms(35, 32, 56), dms(139, 47, 4), 20, ts), now, null, airports, terminals, true);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.at, ts); assertEquals(d.flags.includes("offline"), true); }
});
Deno.test("保留：25時間前は受け付けない", () => {
  const d = decide(pos(dms(35, 32, 56), dms(139, 47, 4), 20, now - 25 * 36e5), now, null, airports, terminals, true);
  assertEquals(d.ok ? "" : d.reason, "stale_position");
});
Deno.test("通常：3時間前の位置は受け付けない", () => {
  const d = decide(pos(dms(35, 32, 56), dms(139, 47, 4), 20, now - 3 * 36e5), now, null, airports, terminals, false);
  assertEquals(d.ok ? "" : d.reason, "stale_position");
});
Deno.test("保留：後の記録がすでにあれば送れない", () => {
  const d = decide(pos(dms(35, 32, 56), dms(139, 47, 4), 20, now - 3 * 36e5), now, { airport_id: CTS, terminal_id: null, at: now - 36e5 }, airports, terminals, true);
  assertEquals(d.ok ? "" : d.reason, "out_of_order");
});
Deno.test("保留：羽田（保留）→新千歳の到着は、端末の時刻どうしでフライト成立", () => {
  const cts = airports.find((a: any) => a.id === CTS);
  const dep = now - 4 * 36e5, arr = now - 2 * 36e5;
  const d = decide(pos(cts.lat, cts.lon, 20, arr), now, { airport_id: HND, terminal_id: "HND-T1", at: dep }, airports, terminals, true);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.flight?.dep, dep); assertEquals(d.flight?.arr, arr); }
});
Deno.test("保留でも速度チェックは同じ（10分で羽田→新千歳は不可）", () => {
  const cts = airports.find((a: any) => a.id === CTS);
  const d = decide(pos(cts.lat, cts.lon, 20, now - 50 * 60e3), now, { airport_id: HND, terminal_id: null, at: now - 60 * 60e3 }, airports, terminals, true);
  assertEquals(d.ok, true); if (d.ok) { assertEquals(d.flight, null); assertEquals(d.flags.includes("impossible_speed"), true); }
});

// ---------- 関西・中部・新千歳・福岡のターミナル ----------
const more: [string, number, number, string | null][] = [
  ["関西 第1", 34.4343, 135.2442, "KIX-T1"], ["関西 第1の端（中心から約600m）", 34.4343, 135.2508, "KIX-T1"], ["関西 第2", 34.4379, 135.2318, "KIX-T2"],
  ["中部 第1", 34.8598, 136.8160, "NGO-T1"], ["中部 第2", 34.8533, 136.8158, "NGO-T2"],
  ["新千歳 国内線", 42.7877, 141.6808, "CTS-D"], ["新千歳 国際線", 42.7862, 141.6763, "CTS-I"],
  ["福岡 国内線", 33.5973, 130.4481, "FUK-D"], ["福岡 国際線", 33.5848, 130.4443, "FUK-I"], ["福岡 滑走路の中ほど", 33.5900, 130.4500, null],
];
for (const [name, lat, lon, term] of more) {
  Deno.test(`ターミナル: ${name}`, () => {
    const p = locate({ lat, lon }, airports, terminals);
    assertEquals(p.within, true); assertEquals(p.terminal?.id ?? null, term);
  });
}

// ---------- 番外編（自衛隊・米軍の飛行場、滑空場） ----------
const CTS_E: Airport = { id: 6, name: "新千歳空港", iata: "CTS", lat: 42.774753, lon: 141.690414, radius_m: 2000, rare: false };
const CHITOSE_BASE: Airport = { id: 1001, name: "千歳基地", iata: "RJCJ", lat: 42.794498, lon: 141.666, radius_m: 2000, rare: false, extra: true };
const IRUMA: Airport = { id: 1010, name: "入間基地", iata: "RJTJ", lat: 35.8419, lon: 139.410995, radius_m: 2000, rare: false, extra: true };
const MENUMA: Airport = { id: 2017, name: "妻沼滑空場", iata: "滑空場", lat: 36.21338, lon: 139.41697, radius_m: 800, rare: false, extra: true };
const HND_E: Airport = { id: 5, name: "東京国際空港（羽田）", iata: "HND", lat: 35.549678, lon: 139.786958, radius_m: 2000, rare: false };
const EX_LIST = [CTS_E, HND_E, CHITOSE_BASE, IRUMA, MENUMA];

Deno.test("番外編：新千歳空港の範囲内なら、千歳基地の方が近くても新千歳空港", () => {
  // 新千歳の中心から北西へ1.6km（千歳基地まで約1.4km）
  const p = { lat: 42.7855, lon: 141.6770 };
  assertEquals(km(p, CHITOSE_BASE) < km(p, CTS_E), true);
  assertEquals(locate(p, EX_LIST, []).airport.id, 6);
});
Deno.test("番外編：新千歳空港の範囲の外で、千歳基地の範囲内なら千歳基地", () => {
  const p = { lat: 42.8050, lon: 141.6550 };
  const pl = locate(p, EX_LIST, []);
  assertEquals([pl.airport.id, pl.within], [1001, true]);
});
Deno.test("番外編：入間基地のフェンスの外（1.8km）でも押せる。範囲外は民間空港の案内", () => {
  assertEquals(locate({ lat: 35.8580, lon: 139.4100 }, EX_LIST, []).airport.id, 1010);
  const far = locate({ lat: 35.90, lon: 139.40 }, EX_LIST, []);
  assertEquals(far.within, false);
});
Deno.test("番外編：基地や滑空場との間はフライトにしない", () => {
  const now = Date.parse("2026-10-07T12:00:00+09:00");
  const last = { airport_id: 5, terminal_id: null, at: now - 3 * 36e5 };  // 3時間前に羽田
  const d = decide({ lat: 36.21338, lon: 139.41697, acc: 20, ts: now }, now, last, EX_LIST, []);
  if (!d.ok) throw new Error(d.message);
  assertEquals([d.place.airport.id, d.flight], [2017, null]);
});
