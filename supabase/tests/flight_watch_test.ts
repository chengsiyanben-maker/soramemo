// ダイヤと機体の位置の照らし合わせ：離陸・着陸・遅れ・ダイバート・引き返し
import { assertEquals } from "jsr:@std/assert@1";
import { type Airport, blankWatch, callsignsFor, cruiseOf, hardToSee, landingFrom, predictEta, normCallsign, onRoute, type Sched, type Seen, step, type Watch } from "../functions/_shared/flight_watch.ts";

const APS = new Map<string, Airport>([
  ["HND", { iata: "HND", lat: 35.5497, lon: 139.787, name: "羽田" }],
  ["CTS", { iata: "CTS", lat: 42.7748, lon: 141.6904, name: "新千歳" }],
  ["HKD", { iata: "HKD", lat: 41.77, lon: 140.822, name: "函館" }],
]);
const T0 = Date.UTC(2026, 9, 26, 1, 0);   // 10:00 JST
const MIN = 60_000;
const S: Sched = { id: 1, flight: "JL509", dep: "HND", arr: "CTS", std: T0, sta: T0 + 95 * MIN };
const at = (lat: number, lon: number, alt: number, t: number, fpm = 0): Seen => ({ callsign: "JAL509", lat, lon, alt_ft: alt, ground: false, fpm, at: t });
function run(seq: [Seen | null, number][]) {
  let w: Watch = blankWatch(); const all: string[] = [];
  for (const [s, now] of seq) { const r = step(S, w, s, now, APS); w = r.watch; all.push(...r.alerts.map((a) => a.kind)); }
  return { w, all };
}

Deno.test("便名と呼び出し符号を結ぶ（先頭の0は無視、グループ会社の記号も候補に）", () => {
  assertEquals(callsignsFor("JL035"), ["JAL35", "JLJ35", "JTA35", "JAC35", "HAC35"]);
  assertEquals(callsignsFor("BC001"), ["SKY1"]);
  assertEquals(callsignsFor("6J91"), ["SNJ91"]);
  assertEquals(callsignsFor("XX123"), []);
  assertEquals(normCallsign("JAL0509 "), "JAL509");
});

Deno.test("定刻どおり：離陸と着陸を記録し、お知らせは出さない", () => {
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(39.5, 141.0, 37000, T0 + 50 * MIN), T0 + 50 * MIN],
    [at(42.72, 141.68, 1200, T0 + 88 * MIN, -700), T0 + 88 * MIN],
    [null, T0 + 95 * MIN],
  ]);
  assertEquals(w.phase, "landed"); assertEquals(w.landed_iata, "CTS"); assertEquals(w.takeoff_est, false);
  assertEquals(all, []);
});

Deno.test("出発が1時間以上遅れ・到着も1時間以上遅れ", () => {
  const { all } = run([
    [null, T0 - 10 * MIN],
    [null, T0 + 60 * MIN],
    [at(35.56, 139.80, 2000, T0 + 80 * MIN, 2500), T0 + 80 * MIN],
    [at(42.72, 141.68, 1200, T0 + 160 * MIN, -700), T0 + 160 * MIN],
    [null, T0 + 170 * MIN],
  ]);
  assertEquals(all, ["delay_dep", "delay_arr"]);
});

Deno.test("定刻から1時間15分たっても離陸を確認できない：いまは知らせない（共同運航便で誤るため）", () => {
  const { all } = run([[null, T0 - 10 * MIN], [null, T0 + 70 * MIN], [null, T0 + 76 * MIN], [null, T0 + 90 * MIN]]);
  assertEquals(all, []);
});

Deno.test("ダイバート：函館へ降りていき、そのまま着陸", () => {
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(41.80, 140.85, 3500, T0 + 85 * MIN, -800), T0 + 85 * MIN],
    [at(41.775, 140.83, 900, T0 + 90 * MIN, -700), T0 + 90 * MIN],
    [null, T0 + 96 * MIN],
  ]);
  assertEquals(all, ["divert", "divert_landed"]);
  assertEquals(w.landed_iata, "HKD");
});

Deno.test("引き返し：離陸から20分より後に、羽田へ降りてくる", () => {
  const { all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(35.58, 139.84, 3000, T0 + 25 * MIN, -500), T0 + 25 * MIN],   // 離陸直後の旋回は数えない
    [at(35.60, 139.85, 3000, T0 + 60 * MIN, -900), T0 + 60 * MIN],
  ]);
  assertEquals(all, ["return"]);
});

Deno.test("定刻を過ぎてから見張り始めた便（ダイヤを後から入れた）は、「離陸を確認できず」を出さない", () => {
  const { all } = run([[null, T0 + 80 * MIN], [null, T0 + 90 * MIN], [null, T0 + 120 * MIN]]);
  assertEquals(all, []);
});

Deno.test("プロペラ機・エンブラエル機は「離陸を確認できず」を出さない（ジェット機は出す）", () => {
  for (const t of ["Q4A", "Q84", "AT7", "ATR", "DH4", "E70", "E90", "E75"]) assertEquals(hardToSee(t), true, t);
  for (const t of ["738", "73H", "763", "32P", "359", "788", null, undefined]) assertEquals(hardToSee(t), false, String(t));
  const prop: Sched = { ...S, aircraft: "Q4A" }; let w: Watch = blankWatch(); const all: string[] = [];
  for (const now of [T0 - 10 * MIN, T0 + 76 * MIN, T0 + 90 * MIN]) { const r = step(prop, w, null, now, APS); w = r.watch; all.push(...r.alerts.map((a) => a.kind)); }
  assertEquals(all, []);
});

Deno.test("到着空港の手前で受信が切れた：降下中に見えなくなって10分たてば着陸とみなし、「まだ飛行中」は出さない", () => {
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(42.55, 141.62, 6000, T0 + 85 * MIN, -900), T0 + 85 * MIN],   // 新千歳の約25km手前・6,000ft で最後
    [null, T0 + 90 * MIN], [null, T0 + 96 * MIN], [null, T0 + 160 * MIN],
  ]);
  assertEquals(w.phase, "landed"); assertEquals(w.landed_iata, "CTS");
  assertEquals(all, []);
});

Deno.test("途中で見えなくなった便には「まだ飛行中」を出さない。今も見えていれば出す", () => {
  const lost = run([[at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN], [at(39.5, 141.0, 37000, T0 + 50 * MIN), T0 + 50 * MIN], [null, T0 + 160 * MIN]]);
  assertEquals(lost.all, []);
  const still = run([[at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN], [at(41.0, 141.3, 20000, T0 + 156 * MIN), T0 + 156 * MIN]]);
  assertEquals(still.all, ["delay_arr"]);
});

Deno.test("近い空港への進入はダイバートとしない（北九州へ降りる途中で山口宇部の近くを通る）", () => {
  const aps = new Map<string, Airport>([...APS, ["KKJ", { iata: "KKJ", lat: 33.8459, lon: 131.0349, name: "北九州" }], ["UBJ", { iata: "UBJ", lat: 33.93, lon: 131.2786, name: "山口宇部" }]]);
  const s: Sched = { id: 2, flight: "7G77", dep: "HND", arr: "KKJ", std: T0, sta: T0 + 110 * MIN };
  let w: Watch = blankWatch(); const all: string[] = [];
  for (const [p, now] of [[at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN], [at(33.92, 131.25, 3000, T0 + 100 * MIN, -800), T0 + 100 * MIN], [at(33.88, 131.10, 1500, T0 + 104 * MIN, -700), T0 + 104 * MIN]] as [Seen, number][]) {
    const r = step(s, w, p, now, aps); w = r.watch; all.push(...r.alerts.map((a) => a.kind));
  }
  assertEquals(all, []);
});

Deno.test("同じ番号の別の会社の便（JL552 と JTA552）：出発・到着を結ぶ帯の外の機体はその便とみなさない", () => {
  const aps = new Map<string, Airport>([...APS, ["AKJ", { iata: "AKJ", lat: 43.6708, lon: 142.4475, name: "旭川" }]]);
  const s: Sched = { id: 3, flight: "JL552", dep: "AKJ", arr: "HND", std: T0, sta: T0 + 100 * MIN };
  assertEquals(onRoute(s, { lat: 26.2, lon: 127.65 }, aps), false);   // 那覇の近く
  assertEquals(onRoute(s, { lat: 39.5, lon: 141.0 }, aps), true);     // 途中の東北
});

Deno.test("機種ごとの巡航速度：777 は速く、Q400・ATR は遅い（ICAO と ODPT の記号のどちらでも）", () => {
  assertEquals(cruiseOf("B77W").cruise > cruiseOf("B738").cruise, true);
  assertEquals(cruiseOf("738").cruise, cruiseOf("B738").cruise);
  assertEquals(cruiseOf("DH8D").cruise < cruiseOf("E190").cruise, true);
  assertEquals(cruiseOf("AT76").cruise < cruiseOf("DH8D").cruise, true);
  assertEquals(cruiseOf(null).cruise, 440);
});

Deno.test("到着予想：同じ位置でも、プロペラ機は遅く、巡航中は今の対地速度（追い風）を使う", () => {
  const itm = { iata: "ITM", lat: 34.7855, lon: 135.4382, name: "伊丹" }, now = Date.parse("2026-10-17T12:00:00Z");
  const p = { lat: 35.2, lon: 137.6, alt_ft: 22000, kt: null, at: now };   // 伊丹の東 約200km
  const jet = predictEta(p, itm, "B738"), prop = predictEta(p, itm, "DH8D");
  assertEquals(prop > jet, true);
  const min = (t: number) => Math.round((t - now) / 60000);
  assertEquals(min(jet) >= 20 && min(jet) <= 35, true);
  const tail = predictEta({ ...p, kt: 560 }, itm, "B738");   // 追い風で対地速度 560kt
  assertEquals(tail < jet, true);
  const odd = predictEta({ ...p, kt: 900 }, itm, "B738");    // おかしな速度は使わない
  assertEquals(odd, jet);
});

Deno.test("着陸して地上を走っているのが見えたら、着陸とみなす（最後に飛んでいた時刻）", () => {
  const ground = (t: number): Seen => ({ ...at(42.78, 141.69, 0, t), ground: true });
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(39.5, 141.0, 37000, T0 + 60 * MIN), T0 + 60 * MIN],
    [at(42.70, 141.68, 1200, T0 + 92 * MIN, -700), T0 + 92 * MIN],
    [ground(T0 + 96 * MIN), T0 + 96 * MIN],
    [ground(T0 + 120 * MIN), T0 + 120 * MIN],
  ]);
  assertEquals([w.phase, w.landed_iata, w.landed_at], ["landed", "CTS", T0 + 92 * MIN]);
  assertEquals(all, []);
});

Deno.test("到着の30分前ごろの到着予想を残す", () => {
  const { w } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(40.6, 141.3, 37000, T0 + 70 * MIN), T0 + 70 * MIN],
  ]);
  assertEquals(w.eta30 != null && Math.abs((w.eta30 ?? 0) - (T0 + 95 * MIN)) < 15 * MIN, true);
});

Deno.test("降りる途中で見えなくなった便：到着予想から15分たったら着いたとみなす（着陸の時刻は入れない）", () => {
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(41.6, 141.5, 16000, T0 + 80 * MIN, -1500), T0 + 80 * MIN],
    [null, T0 + 100 * MIN],
    [null, T0 + 130 * MIN],
  ]);
  assertEquals([w.phase, w.landed_iata, w.landed_at], ["landed", "CTS", null]);
  assertEquals(all, []);
});

Deno.test("空港の近く（120km以内・15,000ft以下）で見えなくなった便は、最後の位置から着陸の時刻を推定する", () => {
  // 新千歳の南 約80km・9,000ft で見えなくなった
  const { w, all } = run([
    [at(35.56, 139.80, 2000, T0 + 18 * MIN, 2500), T0 + 18 * MIN],
    [at(42.05, 141.62, 9000, T0 + 85 * MIN, -1500), T0 + 85 * MIN],
    [null, T0 + 100 * MIN],
    [null, T0 + 130 * MIN],
  ]);
  assertEquals([w.phase, w.landed_iata], ["landed", "CTS"]);
  // 残り約43海里を進入の速度（220kt）で約12分＋着陸の4分 → 最後に見てから15分前後
  const after = ((w.landed_at ?? 0) - (T0 + 85 * MIN)) / MIN;
  assertEquals(after > 12 && after < 19, true);
  assertEquals(all, []);
});

Deno.test("着陸の時刻の推定は、最後に見た時刻より前にならない", () => {
  const ap = APS.get("CTS")!;
  const t = landingFrom({ lat: ap.lat, lon: ap.lon, alt_ft: 0, at: T0 }, ap, "B738");
  assertEquals(t >= T0, true);
});

Deno.test("寄り道：滑走路の使い方ごとの値があれば、いまの使い方の値を使う（分からなければ空港全体）", async () => {
  const { setCalib, setModeCalib, arrExtra } = await import("../functions/_shared/flight_watch.ts");
  setCalib([{ iata: "HND", taxi: 8, extra: 4 }]);
  setModeCalib([{ iata: "HND", mode: "south", extra: 15 }, { iata: "HND", mode: "north", extra: 3 }], [{ iata: "HND", mode: "south" }]);
  assertEquals(arrExtra("HND", 120), 15);
  assertEquals(arrExtra("HND", 30), 7.5);   // 近いほど小さくするのは同じ
  setModeCalib(null, [{ iata: "HND", mode: "north" }]);
  assertEquals(arrExtra("HND", 120), 3);
  setModeCalib(null, [{ iata: "HND", mode: "city" }]);   // まだ学んでいない使い方
  assertEquals(arrExtra("HND", 120), 4);
  setModeCalib(null, []);   // 使い方が分からない
  assertEquals(arrExtra("HND", 120), 4);
  setModeCalib([], []); setCalib([]);
});
