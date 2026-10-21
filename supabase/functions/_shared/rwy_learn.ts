// 着陸する滑走路の学習：近づいている機体の来た方面を残し、空港の近くで滑走路の延長線上に乗ったら、その滑走路を記録する（判定だけ）
import { flightOfCallsign, normCallsign } from "./flight_watch.ts";

export type ArrPlane = { id: string; callsign: string | null; lat: number; lon: number; alt_ft: number | null; hdg: number | null; phase: string; dist_km: number; type?: string | null };
export type ArrWatch = { iata: string; hex: string; dir?: "arr" | "dep"; rwy?: string | null; ex30?: number | null; ex60?: number | null; callsign: string | null; type: string | null; first_km: number | null; first_brg: number | null; ent120: number | null; ent60: number | null; ent30: number | null; pts: [number, number, number, number][]; updated_at: string };
export type Rw = Record<string, { id: string; thr: [number, number]; hdg: number; end?: [number, number] }>;

const R = Math.PI / 180;
export function km(a: [number, number], b: [number, number]) {
  const dl = (b[0] - a[0]) * R, dn = (b[1] - a[1]) * R, h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * R) * Math.cos(b[0] * R) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
export function brg(a: [number, number], b: [number, number]) {
  const y = Math.sin((b[1] - a[1]) * R) * Math.cos(b[0] * R), x = Math.cos(a[0] * R) * Math.sin(b[0] * R) - Math.sin(a[0] * R) * Math.cos(b[0] * R) * Math.cos((b[1] - a[1]) * R);
  return (Math.atan2(y, x) / R + 360) % 360;
}
const angd = (a: number, b: number) => Math.abs(((a - b + 540) % 360) - 180);

// いまの位置と向きから、乗っている滑走路の延長線（横のずれ0.6km以内・進入端の手前12kmから滑走路の上まで・向きが20°以内）
export function onFinal(p: { lat: number; lon: number; hdg: number | null }, rw: Rw): string | null {
  let best: string | null = null, bl = 0.6;
  for (const r of Object.values(rw)) {
    if (p.hdg == null || angd(p.hdg, r.hdg) > 20) continue;
    const d = km(r.thr, [p.lat, p.lon]); if (d < 0.05) return r.id;
    const rel = (brg(r.thr, [p.lat, p.lon]) - r.hdg) * R, along = -d * Math.cos(rel), lat = Math.abs(d * Math.sin(rel));
    if (along < -3.5 || along > 12) continue;
    if (lat < bl) { bl = lat; best = r.id; }
  }
  return best && /^[0-9]{2}[LRC]?$/.test(best) ? best : null;
}

// 離陸した滑走路：滑走路の始まり（end）から先へ16kmまでの線の上（横のずれ0.7km以内）で、向きが25°以内
export function onDeparture(p: { lat: number; lon: number; hdg: number | null }, rw: Rw): string | null {
  let best: string | null = null, bl = 0.7;
  for (const r of Object.values(rw)) {
    if (p.hdg == null || angd(p.hdg, r.hdg) > 25) continue;
    const s0 = r.end ?? r.thr, d = km(s0, [p.lat, p.lon]);
    const rel = (brg(s0, [p.lat, p.lon]) - r.hdg) * R, fw = d * Math.cos(rel), lat = Math.abs(d * Math.sin(rel));
    if (fw < 0 || fw > 16) continue;
    if (lat < bl) { bl = lat; best = r.id; }
  }
  return best && /^[0-9]{2}[LRC]?$/.test(best) ? best : null;
}

// 30秒ごとの機体から、見張りの更新と、着陸の滑走路が分かった記録を出す
export function arrStep(iata: string, center: [number, number], rw: Rw, planes: ArrPlane[], watch: Map<string, ArrWatch>, now: number) {
  const upserts: ArrWatch[] = [], samples: Record<string, unknown>[] = [], deletes: string[] = [];
  const iso = new Date(now).toISOString(), sec = Math.floor(now / 1000);
  for (const p of planes) {
    if (!p.callsign || /^JA(?:\d{4}|\d{3}[A-Z]|\d{2}[A-Z]{2})$/.test(p.callsign) || p.alt_ft == null) continue;
    const here: [number, number] = [p.lat, p.lon], d = km(center, here), b = Math.round(brg(center, here));
    const old = watch.get(p.id), sec0 = Math.floor(now / 1000);
    const addPt = (w: ArrWatch) => { const l = w.pts[w.pts.length - 1]; if (!l || sec0 - l[0] >= 55) w.pts = [...w.pts, [sec0, Math.round(p.lat * 1e4) / 1e4, Math.round(p.lon * 1e4) / 1e4, p.alt_ft!] as [number, number, number, number]].slice(-40); };
    // 離陸：滑走路の先の線の上を上がっていく機体を見つけ、30km・60km の円を出た方角を残す（60km を出たら記録）
    if (old?.dir === "dep") {
      const w: ArrWatch = { ...old, pts: [...old.pts], updated_at: iso };
      if (w.ex30 == null && d >= 30) w.ex30 = b;
      if (w.ex60 == null && d >= 60) w.ex60 = b;
      addPt(w);
      if (w.ex60 != null) {
        samples.push({ iata, dir: "dep", at: iso, callsign: w.callsign, flight: flightOfCallsign(w.callsign ?? ""), type: w.type, rwy: w.rwy, first_km: w.first_km, first_brg: w.first_brg, ex30: w.ex30, ex60: w.ex60, pts: w.pts });
        deletes.push(p.id);
      } else upserts.push(w);
      continue;
    }
    if (p.phase === "dep" && p.alt_ft <= 3000 && d <= 15) {
      const r = onDeparture(p, rw);
      if (r) { const w: ArrWatch = { iata, hex: p.id, dir: "dep", rwy: r, ex30: null, ex60: null, callsign: normCallsign(p.callsign), type: p.type ?? null, first_km: Math.round(d * 10) / 10, first_brg: b, ent120: null, ent60: null, ent30: null, pts: [], updated_at: iso };
        addPt(w); upserts.push(w); continue; }
    }
    // 着陸：見張りを始めるのは降りている機体だけ。見張り中の機体は、水平飛行の間も続ける（離陸・上昇に変わったらやめる）
    if (!old ? p.phase !== "arr" || p.alt_ft > 24000 : p.phase === "dep") { if (old && p.phase === "dep") deletes.push(p.id); continue; }
    const w: ArrWatch = watch.get(p.id) ? { ...watch.get(p.id)!, pts: [...watch.get(p.id)!.pts] }
      : { iata, hex: p.id, dir: "arr", callsign: normCallsign(p.callsign), type: p.type ?? null, first_km: Math.round(d * 10) / 10, first_brg: b, ent120: null, ent60: null, ent30: null, pts: [], updated_at: iso };
    if (w.ent120 == null && d <= 120) w.ent120 = b;
    if (w.ent60 == null && d <= 60) w.ent60 = b;
    if (w.ent30 == null && d <= 30) w.ent30 = b;
    const last = w.pts[w.pts.length - 1];
    if (!last || sec - last[0] >= 55) w.pts = [...w.pts, [sec, Math.round(p.lat * 1e4) / 1e4, Math.round(p.lon * 1e4) / 1e4, p.alt_ft] as [number, number, number, number]].slice(-40);
    w.updated_at = iso;
    const r = p.alt_ft <= 2500 && d <= 20 ? onFinal(p, rw) : null;
    if (r) {
      const fl = flightOfCallsign(w.callsign ?? "");
      samples.push({ iata, dir: "arr", at: iso, callsign: w.callsign, flight: fl, type: w.type, rwy: r, first_km: w.first_km, first_brg: w.first_brg, ent120: w.ent120, ent60: w.ent60, ent30: w.ent30, pts: w.pts });
      deletes.push(p.id); continue;
    }
    upserts.push(w);
  }
  return { upserts, samples, deletes };
}

// 羽田：来た方面（空港から見た方角）で、2本ある着陸の滑走路のどちらかを決める（10月18〜20日の JAL・ANA の航跡971機で約89%）
export const HND_SIDE: Record<string, "N" | "S"> = { "34R": "N", "34L": "S", "23": "N", "22": "S", "16R": "N", "16L": "S" };
export const sideOf = (bearing: number) => bearing >= 300 || bearing < 100 ? "N" : "S";
