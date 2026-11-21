// 機体の行き先（と出発地）を便名で決める（11/21 本人「便の名前から行き先を判別して、判定を強化して」。data/livery-dest2）。
//   特別塗装機の知らせ（recordLiveries）・海外の塗装機の早めの知らせ（notifyInbound）・撮影の知らせ（notifySpot は運用タブの答えを使う）・
//   運用タブの着陸・離陸の一覧（airport-traffic の build）が、みなこの1か所で行き先を決める。
//   1. 呼び出し符号 → 便名（flightsOfCallsign。ADO14 → HD14、SKY004 → BC4、JAL500 → JL500、TGW866 → TR866、TZP52 → ZG52）
//   2. 時刻表（flight_schedule。ODPT の JAL・ANA の国内線と国際線）で、いま飛んでいる便の到着の空港を引く。日付ではなく出発の定刻の幅で引くので、
//      深夜便・遅れて日をまたぐ便・長い国際線も見つかる
//   3. 時刻表にない便（海外の会社・ODPT にない日本の会社）は、全機の記録から作った「いつもの時刻」（foreign_usual）の到着の空港。
//      ふだんの到着の時刻がいまから前後2時間に入るものだけ（同じ呼び出し符号で別の空港に着く日がある便を取り違えないため）
//   4. どちらにもなければ分からない（形の判定 arr_dest.ts に任せる）
//   問い合わせは1回の処理で束ねて1回ずつ（時刻表・いつもの時刻）。答えは入れ物の記憶に10分ためる（分からなかった便も）
import { flightsOfCallsign, normCallsign } from "./flight_watch.ts";
import { onFinal, type Rwy } from "./arr_dest.ts";

export type Route = { dep: string | null; arr: string; src: "schedule" | "usual"; flight: string | null };
export type SchedRow = { flight: string; dep: string; arr: string; std: string; sta: string };
export type UsualRow = { callsign: string; iata: string; mins: number };
// 問い合わせの口（テストでは偽物を渡す）。schedule：便名の一覧と出発の定刻の幅、usual：呼び出し符号の一覧（50件まで）
export type RouteSource = {
  schedule(flights: string[], fromIso: string, toIso: string): Promise<SchedRow[]>;
  usual(callsigns: string[]): Promise<UsualRow[]>;
};

const MIN = 60_000, H = 3600_000;
// 時刻表の行の幅：出発の定刻が20時間前〜1時間後（長い国際線と、出発の少し前に動き出す機体）
export const SCHED_BACK = 20 * H, SCHED_AHEAD = 1 * H;
// 遅れの見込みの上限（定刻の到着から6時間すぎた便は、いま飛んでいる便と見ない）
const LATE_MAX = 6 * H;

// 時刻表の行から、呼び出し符号ごとに いま飛んでいる便を1つ選ぶ。
//   出発の定刻〜到着の定刻＋6時間に いまが入る便のうち、到着の定刻がいまにいちばん近いもの。入る便がなければ、出発の1時間前までの便
export function routesFromSchedule(callsigns: string[], rows: SchedRow[], now: number): Map<string, Route> {
  const byFlight = new Map<string, SchedRow[]>();
  for (const r of rows ?? []) byFlight.set(r.flight, [...(byFlight.get(r.flight) ?? []), r]);
  const out = new Map<string, Route>();
  for (const cs0 of callsigns) {
    const cs = normCallsign(cs0);
    let best: { r: SchedRow; f: string; score: number } | null = null;
    for (const f of flightsOfCallsign(cs)) for (const r of byFlight.get(f) ?? []) {
      const std = Date.parse(r.std), sta = Date.parse(r.sta);
      if (!Number.isFinite(std) || !Number.isFinite(sta)) continue;
      if (now < std - SCHED_AHEAD || now > sta + LATE_MAX) continue;
      // 飛んでいる幅の中なら到着の定刻との差、出発の前なら出発までの時間に大きめの重み
      const score = now < std ? (std - now) * 3 + H : Math.abs(sta - now);
      if (!best || score < best.score) best = { r, f, score };
    }
    if (best) out.set(cs, { dep: best.r.dep, arr: best.r.arr, src: "schedule", flight: best.f });
  }
  return out;
}

// 日本時間の0時からの分
const jstMins = (t: number) => Math.floor(((t + 9 * H) % 864e5) / MIN);
const minsOff = (a: number, b: number) => { const d = Math.abs(a - b) % 1440; return Math.min(d, 1440 - d); };
export const USUAL_WINDOW_MIN = 120;
// いつもの時刻（到着だけ）から、呼び出し符号ごとに行き先を1つ。ふだんの到着の時刻がいまの前後2時間に入るもののうち、いちばん近いもの
export function routesFromUsual(rows: UsualRow[], now: number): Map<string, Route> {
  const nowM = jstMins(now), best = new Map<string, { iata: string; off: number }>();
  for (const u of rows ?? []) {
    if (typeof u.mins !== "number" || !/^[A-Z]{3}$/.test(u.iata)) continue;
    const cs = normCallsign(u.callsign), off = minsOff(u.mins, nowM);
    if (off > USUAL_WINDOW_MIN) continue;
    const b = best.get(cs);
    if (!b || off < b.off) best.set(cs, { iata: u.iata, off });
  }
  const out = new Map<string, Route>();
  for (const [cs, b] of best) out.set(cs, { dep: null, arr: b.iata, src: "usual", flight: null });
  return out;
}

// 入れ物の記憶（呼び出し符号 → 便の行き先。分からなかった便は null）
const TTL = 10 * MIN, CACHE = new Map<string, { at: number; r: Route | null }>();
export function clearRouteCache() { CACHE.clear(); }

// 呼び出し符号の一覧から行き先を引く。記憶にないものだけを、時刻表で1回・残りをいつもの時刻で1回（50件ずつ）引く。
//   問い合わせが失敗・時間切れのときは、その回は分からないことにする（記憶には入れない。形の判定に任せる）
//   withUsual=false：時刻表だけ引く（海外の塗装機の早めの知らせは、いつもの時刻を自分で候補ごと引くため）。このときは見つかった便だけ記憶に入れる
export async function lookupRoutes(src: RouteSource, callsigns: (string | null | undefined)[], now = Date.now(), withUsual = true): Promise<Map<string, Route>> {
  const out = new Map<string, Route>(), miss: string[] = [];
  for (const c of new Set(callsigns.filter((x): x is string => !!x && !!x.trim()).map(normCallsign))) {
    const hit = CACHE.get(c);
    if (hit && now - hit.at < TTL) { if (hit.r) out.set(c, hit.r); }
    else if (flightsOfCallsign(c).length) miss.push(c);   // 便名に直せない呼び出し符号（自家用機など）は引かない
  }
  if (!miss.length) return out;
  const flights = [...new Set(miss.flatMap(flightsOfCallsign))];
  let sched: Map<string, Route>;
  try {
    sched = routesFromSchedule(miss, await src.schedule(flights, new Date(now - SCHED_BACK).toISOString(), new Date(now + SCHED_AHEAD).toISOString()), now);
  } catch (e) { console.error("route schedule", e); return out; }
  const rest = withUsual ? miss.filter((c) => !sched.has(c)) : [];
  const usual = new Map<string, Route>();
  let usualOk = true;
  for (let i = 0; i < rest.length; i += 50) {
    try { for (const [k, v] of routesFromUsual(await src.usual(rest.slice(i, i + 50)), now)) usual.set(k, v); }
    catch (e) { console.error("route usual", e); usualOk = false; break; }
  }
  if (CACHE.size > 5000) CACHE.clear();
  for (const c of miss) {
    const r = sched.get(c) ?? usual.get(c) ?? null;
    if (r) out.set(c, r);
    if (r || (usualOk && withUsual)) CACHE.set(c, { at: now, r });
  }
  return out;
}

// 運用タブの空港ごとの答えに、便名の行き先を当てる。raw：形だけで見分けた答え、refined：滑走路の向きと距離で絞った答え（arr_dest.ts の refinePhases）。
//   便名の行き先が分かる機体：
//     着陸（raw が arr）… 行き先がこの空港なら着陸（形の絞り込みで外れていても戻す）。ほかの空港なら外す。
//       ただし、この空港の最終進入の12km以内・3,000ft 以下に乗っていれば着陸のまま（ダイバート。便名の行き先と違っても降りてくる）
//     離陸（raw が dep）… 時刻表の出発地がこの空港なら離陸、ほかの空港なら外す。いつもの時刻（出発地が分からない）のときは絞った答えのまま
//   分からない機体は絞った答えのまま
type P = { callsign: string | null; phase: string; lat: number; lon: number; alt_ft: number | null; hdg: number | null };
export function applyRoutes<T extends P>(raw: T[], refined: T[], iata: string, rws: Rwy[], routes: Map<string, Route>): T[] {
  return refined.map((p, i) => {
    const r0 = raw[i] ?? p, r = p.callsign ? routes.get(normCallsign(p.callsign)) : undefined;
    if (!r || (r0.phase !== "arr" && r0.phase !== "dep")) return p;
    if (r0.phase === "arr") {
      if (r.arr === iata) return { ...p, phase: "arr" };
      if (onFinal(p, rws, 12) && p.alt_ft != null && p.alt_ft <= 3000) return { ...p, phase: "arr" };
      return { ...p, phase: "other" };
    }
    if (!r.dep) return p;
    return { ...p, phase: r.dep === iata ? "dep" : "other" };
  });
}

// 知らせの行き先（pickAirport に渡す known）。時刻表・いつもの時刻とも行き先は使い、出発地は時刻表のときだけ
export function knownOf(routes: Map<string, Route>, cs: string | null | undefined): { arr: string | null; dep: string | null } {
  const r = cs ? routes.get(normCallsign(cs)) : undefined;
  return { arr: r?.arr ?? null, dep: r?.src === "schedule" ? r.dep : null };
}
