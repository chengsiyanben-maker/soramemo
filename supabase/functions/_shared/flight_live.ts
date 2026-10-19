// 乗る便を出発から到着まで追う（国際線も）：便名から機体の呼び出し符号を作り、世界中の機体の位置（adsb.lol）から探して、
// 今どこを飛んでいるか・到着予想（推定）・進み具合を返す。取得（index.ts）とは分けて、テストしやすくしている。
import { type Airport, predictEta } from "./flight_watch.ts";

export type Plane = { callsign: string; lat: number; lon: number; alt_ft: number | null; ground: boolean; kt: number | null; track: number | null; type: string | null; reg: string | null; at: number };
export type LiveSched = { flight: string; dep: string; arr: string; std: number; sta: number; etd?: number | null; eta?: number | null; atd?: number | null; ata?: number | null; cancelled?: boolean };
export type Live = {
  phase: "sched" | "taxi" | "air" | "landed" | "lost" | "cancelled";
  pos: { lat: number; lon: number; alt_ft: number | null; kt: number | null; track: number | null; at: number } | null;
  eta: number | null; progress: number | null; reg: string | null; type: string | null; callsign: string | null;
};

function km(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

// adsb.lol の返事（readsb の形）の1機を、使う形にする
// deno-lint-ignore no-explicit-any
export function toPlane(a: any, now: number): Plane | null {
  if (!a || typeof a.lat !== "number" || typeof a.lon !== "number" || typeof a.flight !== "string") return null;
  return {
    callsign: a.flight.trim().toUpperCase(), lat: a.lat, lon: a.lon,
    alt_ft: typeof a.alt_baro === "number" ? Math.round(a.alt_baro) : null, ground: a.alt_baro === "ground",
    kt: typeof a.gs === "number" ? Math.round(a.gs) : null, track: typeof a.track === "number" ? Math.round(a.track) : null,
    type: typeof a.t === "string" ? a.t.slice(0, 8) : null, reg: typeof a.r === "string" && /^[A-Z0-9-]{2,10}$/.test(a.r) ? a.r : null,
    at: now - (typeof a.seen_pos === "number" ? a.seen_pos * 1000 : 0),
  };
}

// 便の今の様子。見つけた機体が、出発空港と到着空港を結ぶ道筋から大きく外れていたら（同じ呼び出し符号の別の便）使わない
export function liveState(s: LiveSched, p: Plane | null, dep: Airport | null, arr: Airport | null, now: number): Live {
  const base: Live = { phase: "sched", pos: null, eta: null, progress: null, reg: p?.reg ?? null, type: p?.type ?? null, callsign: p?.callsign ?? null };
  if (s.cancelled) return { ...base, phase: "cancelled" };
  if (s.ata) return { ...base, phase: "landed", progress: 1 };
  if (p && dep && arr) {
    const total = km(dep, arr), dDep = km(p, dep), dArr = km(p, arr);
    if (dDep + dArr > total * 1.4 + 300) p = null;   // 道筋から外れた機体
    else {
      const pos = { lat: p.lat, lon: p.lon, alt_ft: p.alt_ft, kt: p.kt, track: p.track, at: p.at };
      if (p.ground && dArr <= 10) return { ...base, phase: "landed", pos, progress: 1 };
      if (p.ground && dDep <= 10) return { ...base, phase: "taxi", pos, progress: 0 };
      if (!p.ground) {
        const prog = Math.max(0, Math.min(1, 1 - dArr / Math.max(1, total)));
        return { ...base, phase: "air", pos, progress: Math.round(prog * 100) / 100, eta: Math.round(predictEta({ ...p, kt: p.kt }, arr, p.type)) };
      }
    }
  }
  if (!p) {
    // 機体が見つからない：出発の前なら予定どおり、出発の後なら電波の届かない所（海の上など）を飛んでいる見込み
    const dep_t = s.atd ?? s.etd ?? s.std;
    if (now < dep_t + 20 * 60_000) return { ...base, phase: "sched", reg: null, type: null, callsign: null };
    if (now > (s.eta ?? s.sta) + 60 * 60_000) return { ...base, phase: "landed", reg: null, type: null, callsign: null, progress: 1 };
    const prog = Math.max(0, Math.min(1, (now - dep_t) / Math.max(1, (s.eta ?? s.sta) - dep_t)));
    return { ...base, phase: "lost", reg: null, type: null, callsign: null, progress: Math.round(prog * 100) / 100 };
  }
  return base;
}
