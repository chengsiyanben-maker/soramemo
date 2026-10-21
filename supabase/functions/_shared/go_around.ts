// ゴーアラウンドの見つけ方と、ゴーアラウンドが起きやすい天気の目安（判定だけ。取得・保存・送信は airport-traffic）
//   ゴーアラウンド（推定）：着陸に向かう機体が、空港から 10km 以内で 1,000ft 以下まで降りてから、6分以内に、着陸せず
//   いちばん低いところより 500ft 以上高く、上昇中（300ft/分以上）で見えたもの。自家用機など（呼び出し符号が JA…）は除く
import { flightOfCallsign, normCallsign } from "./flight_watch.ts";

export const GA = { trackFt: 4000, trackKm: 25, lowFt: 1000, lowTrackFt: 1500, lowKm: 10, climbFt: 500, windowMin: 6, maxKm: 20 };
export type GaPlane = { id: string; callsign: string | null; lat: number; lon: number; alt_ft: number | null; fpm: number | null; hdg: number | null; phase: string; dist_km: number; type?: string | null; reg?: string | null };
export type Watch = { iata: string; hex: string; callsign: string | null; low_ft: number | null; low_km: number | null; low_at: string | null; low_lat: number | null; low_lon: number | null; low_hdg: number | null; pts: [number, number, number][]; updated_at: string };
export type GaEvent = { iata: string; at: string; hex: string; callsign: string | null; flight: string | null; type: string | null; reg: string | null; low_ft: number; low_km: number | null; low_at: string | null; low_lat: number | null; low_lon: number | null; low_hdg: number | null; pts: [number, number, number][] };

const isPrivate = (cs: string | null) => /^JA(?:\d{4}|\d{3}[A-Z]|\d{2}[A-Z]{2})$/.test(cs ?? "");
const iso = (t: number) => new Date(t).toISOString();

// 30秒ごとの機体の一覧から、見張りの更新・消す行・見つけたゴーアラウンドを出す
export function gaStep(iata: string, planes: GaPlane[], watch: Map<string, Watch>, now: number) {
  const upserts: Watch[] = [], events: GaEvent[] = [], deletes: string[] = [];
  for (const p of planes) {
    if (!p.callsign || isPrivate(p.callsign) || p.alt_ft == null) continue;
    const w = watch.get(p.id), pt: [number, number, number] = [Math.floor(now / 1000), p.alt_ft, p.dist_km];
    const fresh = !!(w && w.low_at && now - Date.parse(w.low_at) <= GA.windowMin * 60_000);
    // 降りてくるところ（いちばん低い所より 400ft 以上高い点）を見ていないもの（離陸した直後の機体など）は数えない
    const seenDescent = !!(w && w.low_ft != null && w.low_at && w.pts.some((q) => q[0] < Date.parse(w.low_at!) / 1000 && q[1] >= w.low_ft! + 400));
    if (w && fresh && seenDescent && w.low_ft != null && w.low_ft <= GA.lowFt && p.alt_ft >= w.low_ft + GA.climbFt && (p.fpm ?? 0) >= 300 && p.dist_km <= GA.maxKm) {
      const cs = normCallsign(p.callsign), fl = flightOfCallsign(cs);
      events.push({ iata, at: iso(now), hex: p.id, callsign: cs, flight: fl && /^[A-Z0-9]{2}[0-9]{1,4}$/.test(fl) ? fl : null, type: p.type ?? null, reg: p.reg ?? null,
        low_ft: w.low_ft, low_km: w.low_km, low_at: w.low_at, low_lat: w.low_lat, low_lon: w.low_lon, low_hdg: w.low_hdg, pts: [...w.pts, pt].slice(-24) });
      deletes.push(p.id); continue;
    }
    if (p.phase === "arr" && p.alt_ft <= GA.trackFt && p.dist_km <= GA.trackKm) {
      const nw: Watch = w ? { ...w, pts: [...w.pts] } : { iata, hex: p.id, callsign: normCallsign(p.callsign), low_ft: null, low_km: null, low_at: null, low_lat: null, low_lon: null, low_hdg: null, pts: [], updated_at: iso(now) };
      nw.pts = [...nw.pts, pt].slice(-20);
      if (p.alt_ft <= GA.lowTrackFt && p.dist_km <= GA.lowKm && (nw.low_ft == null || p.alt_ft < nw.low_ft || !fresh)) {
        nw.low_ft = p.alt_ft; nw.low_km = p.dist_km; nw.low_at = iso(now); nw.low_lat = p.lat; nw.low_lon = p.lon; nw.low_hdg = p.hdg;
      }
      nw.updated_at = iso(now); upserts.push(nw);
    } else if (w && fresh) {
      upserts.push({ ...w, pts: [...w.pts, pt].slice(-20), updated_at: iso(now) });
    }
  }
  return { upserts, events, deletes };
}

// いちばん低かった所から、どの滑走路に降りようとしていたか（向きが40°以内で、進入端がいちばん近いもの）
export function guessRwy(lat: number | null, lon: number | null, hdg: number | null, rw: Record<string, { id: string; thr: [number, number]; hdg: number }>): string | null {
  if (lat == null || lon == null) return null;
  let best: string | null = null, bd = 12;
  for (const r of Object.values(rw)) {
    if (hdg != null && Math.abs(((hdg - r.hdg + 540) % 360) - 180) > 40) continue;
    const d = Math.hypot((r.thr[0] - lat) * 111, (r.thr[1] - lon) * 111 * Math.cos(lat * Math.PI / 180));
    if (d < bd) { bd = d; best = r.id; }
  }
  return best && /^[0-9]{2}[LRC]?$/.test(best) ? best : null;
}

// 雲底：いちばん低い曇り（BKN）・本曇り（OVC）・鉛直視程（VV）の高さ（ft）
export function ceilOf(raw: string): number | null {
  let c: number | null = null;
  for (const m of String(raw ?? "").matchAll(/\b(?:BKN|OVC|VV)(\d{3})\b/g)) { const v = Number(m[1]) * 100; if (c == null || v < c) c = v; }
  return c;
}
export type WxIn = { wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null; raw?: string | null; ceil_ft?: number | null };
// 起きやすさ：2＝起きやすい・1＝注意・0＝ふつう。arrHdg は使っている（着陸の）滑走路の向き
export function wxRisk(m: WxIn | null, arrHdg: number[]) {
  const out = { level: 0, xwind: null as number | null, gust: m?.wgst ?? null, ceil: null as number | null, vis: m?.vis_m ?? null, ts: false, vcts: false, ws: false, kinds: [] as string[], reasons: [] as string[] };
  if (!m) return out;
  const raw = " " + String(m.raw ?? "") + " ";
  out.ceil = m.ceil_ft !== undefined ? m.ceil_ft ?? null : ceilOf(raw);
  if (m.wdir != null && m.wspd != null && arrHdg.length) {
    const sp = Math.max(m.wspd, 0);
    out.xwind = Math.round(Math.min(...arrHdg.map((h) => Math.abs(Math.sin((m.wdir! - h) * Math.PI / 180)) * sp)));
  }
  out.ts = /\s[+-]?TS[A-Z]*\s/.test(raw); out.vcts = /\sVCTS\s/.test(raw); out.ws = /\sWS\s|\sWS\s?R(?:WY)?\d{2}/.test(raw);
  const k = new Set<string>(); let lv = 0;
  const up = (l: number, kind: string, why: string) => { if (l > lv) lv = l; if (l === 2) k.add(kind); out.reasons.push(why); };
  if (out.xwind != null && out.xwind >= 20) up(2, "wind", `横風 ${out.xwind}kt`); else if (out.xwind != null && out.xwind >= 15) up(1, "wind", `横風 ${out.xwind}kt`);
  if (out.gust != null && out.gust >= 30) up(2, "wind", `突風 ${out.gust}kt`); else if (out.gust != null && out.gust >= 25) up(1, "wind", `突風 ${out.gust}kt`);
  if (out.ceil != null && out.ceil < 500) up(2, "cloud", `雲底 ${out.ceil}ft`); else if (out.ceil != null && out.ceil < 1000) up(1, "cloud", `雲底 ${out.ceil}ft`);
  if (out.vis != null && out.vis < 1600) up(2, "cloud", `見通し ${out.vis}m`); else if (out.vis != null && out.vis < 3000) up(1, "cloud", `見通し ${out.vis}m`);
  if (out.ts) up(2, "ts", "雷雨"); else if (out.vcts) up(1, "ts", "近くで雷雨");
  if (out.ws) up(2, "ts", "ウインドシア");
  out.level = lv; out.kinds = [...k];
  return out;
}
// 夜（23時〜7時、日本時間）か
export const quietNow = (t = Date.now()) => { const h = new Date(t + 9 * 3600_000).getUTCHours(); return h >= 23 || h < 7; };
