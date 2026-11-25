// 羽田・成田の地上の動き（11/25 PM の指示「羽田・成田はいろいろなデータを細かく取る」の1番。adsb.lol・ODbL）
//   記録の処理（30秒ごと）の地上の機体（空港の中心から5km、答えの ground）から、1機ごとに
//   着陸（滑走路の上を走っていた）→ 止まった場所（スポット）・地上を走った時間（到着）、
//   止まっていた → 動き出した → 離陸（速く走ったあと見えなくなった）・地上を走った時間（出発）を残す。
//   見張りの状態は ground_watch（短く置く）、まとまった1回ごとは ground_moves（ずっと残す）。移行199
//   時刻は30秒ごとの点なので ±30秒くらいの目安（地上を走る時間は分の単位なので使える）
import { onDeparture, type Rw } from "./rwy_learn.ts";

export type GPlane = { id: string; callsign: string | null; lat: number; lon: number; hdg: number | null; kt: number | null; type: string | null; reg: string | null; moving: boolean };
export type GWatch = {
  iata: string; hex: string; callsign: string | null; reg: string | null; type: string | null;
  mode: "arr" | "park" | "dep";
  t0: string | null;            // 到着：着陸を見た時刻／出発：動き出した時刻（分からなければ null）
  rwy: string | null;
  still_n: number;              // 続けて止まっていた回数
  still_at: string | null;      // 止まり始めた時刻
  stand_lat: number | null; stand_lon: number | null;
  last_at: string; last_lat: number; last_lon: number; last_kt: number | null;
  written_at: string;           // 表に書いた時刻（書く回数を減らすため）
};
export type GMove = {
  iata: string; hex: string; callsign: string | null; reg: string | null; type: string | null;
  kind: "arr" | "dep"; rwy: string | null;
  t_rwy: string | null;         // 到着：着陸を見た時刻／出発：離陸した時刻
  t_block: string | null;       // 到着：止まった時刻／出発：動き出した時刻
  taxi_sec: number | null;
  stand_lat: number | null; stand_lon: number | null;
  lost: boolean;                // 止まる前に見えなくなった（最後に見た所をスポットとした）
};
export type GRunway = { id: string; end: [number, number]; opp: [number, number] };

const R = Math.PI / 180;
const FAST = 30, ROLL = 40, STILL_N = 2;
const GONE_ARR = 5 * 60_000, GONE_DEP = 3 * 60_000, KEEP_PARK = 6 * 3600_000, REWRITE_STILL = 10 * 60_000, REWRITE_MOVE = 2 * 60_000;

// 滑走路の中心線からの距離（km）。端から端までの線分
export function rwyDistKm(p: { lat: number; lon: number }, r: GRunway): number {
  const kx = 111.32 * Math.cos(r.end[0] * R), ky = 110.57;
  const ax = (r.end[1] - p.lon) * kx, ay = (r.end[0] - p.lat) * ky, bx = (r.opp[1] - p.lon) * kx, by = (r.opp[0] - p.lat) * ky;
  const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy;
  const t = L ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / L)) : 0;
  return Math.hypot(ax + t * dx, ay + t * dy);
}
// 滑走路の上（中心線から 80m 以内）。向きが分かれば、走っている向きの滑走路の名前
export function onRunway(p: { lat: number; lon: number; hdg: number | null }, rws: GRunway[]): GRunway | null {
  let best: GRunway | null = null, bd = 0.08;
  for (const r of rws) { const d = rwyDistKm(p, r); if (d < bd) { bd = d; best = r; } }
  return best;
}
const angd = (a: number, b: number) => Math.abs(((a - b + 540) % 360) - 180);
function brg(a: [number, number], b: [number, number]) {
  const y = Math.sin((b[1] - a[1]) * R) * Math.cos(b[0] * R), x = Math.cos(a[0] * R) * Math.sin(b[0] * R) - Math.sin(a[0] * R) * Math.cos(b[0] * R) * Math.cos((b[1] - a[1]) * R);
  return (Math.atan2(y, x) / R + 360) % 360;
}
// 滑走路の上を走っている向きの名前（end → opp に向かう向きなら end の名前）
export function rwyName(p: { hdg: number | null }, r: GRunway, rws: GRunway[]): string | null {
  if (p.hdg == null) return null;
  const h = brg(r.end, r.opp);
  if (angd(p.hdg, h) <= 30) return r.id;
  if (angd(p.hdg, (h + 180) % 360) <= 30) return rws.find((x) => x.end[0] === r.opp[0] && x.end[1] === r.opp[1])?.id ?? null;
  return null;
}

const iso = (ms: number) => new Date(ms).toISOString();
// 2つの時刻の差（秒）。0〜6時間の外は分からないとして null（表の決まりに合わせる）
const sec = (a: string | null, b: string | null) => {
  if (!a || !b) return null;
  const s = Math.round((Date.parse(b) - Date.parse(a)) / 1000);
  return Number.isFinite(s) && s >= 0 && s <= 21600 ? s : null;
};

// 30秒ごとの1回。rw は離陸した滑走路を決めるのに使う（rwy_learn の onDeparture）
export function groundStep(iata: string, rws: GRunway[], rw: Rw, planes: GPlane[], watch: Map<string, GWatch>, now: number) {
  const upserts: GWatch[] = [], moves: GMove[] = [], deletes: string[] = [], seen = new Set<string>();
  const t = iso(now);
  const emit = (w: GWatch, kind: "arr" | "dep", tRwy: string | null, tBlock: string | null, lost = false) => moves.push({
    iata, hex: w.hex, callsign: w.callsign, reg: w.reg, type: w.type, kind, rwy: w.rwy,
    t_rwy: tRwy, t_block: tBlock, taxi_sec: kind === "arr" ? sec(tRwy, tBlock) : sec(tBlock, tRwy),
    stand_lat: w.stand_lat, stand_lon: w.stand_lon, lost });
  for (const p of planes) {
    if (!p.id || seen.has(p.id)) continue;
    seen.add(p.id);
    const old = watch.get(p.id), kt = p.kt ?? 0, still = !p.moving;
    const kclass = (k: number | null) => ((k ?? 0) >= FAST ? 2 : (k ?? 0) >= 5 ? 1 : 0);
    let w: GWatch;
    if (!old) {
      const onR = p.moving ? onRunway(p, rws) : null;
      w = { iata, hex: p.id, callsign: p.callsign, reg: p.reg, type: p.type, mode: onR && kt >= 15 ? "arr" : p.moving ? "dep" : "park",
        t0: onR && kt >= 15 ? t : null, rwy: onR && kt >= 15 ? rwyName(p, onR, rws) : null,
        still_n: still ? 1 : 0, still_at: still ? t : null, stand_lat: still ? p.lat : null, stand_lon: still ? p.lon : null,
        last_at: t, last_lat: p.lat, last_lon: p.lon, last_kt: p.kt, written_at: t };
      upserts.push(w); continue;
    }
    w = { ...old, callsign: p.callsign ?? old.callsign, reg: p.reg ?? old.reg, type: p.type ?? old.type };
    const changed = (m: Partial<GWatch>) => Object.entries(m).some(([k, v]) => (w as Record<string, unknown>)[k] !== v);
    let dirty = kclass(p.kt) !== kclass(old.last_kt);
    if (still) {
      if (w.still_n === 0) { w.still_at = t; w.stand_lat = p.lat; w.stand_lon = p.lon; dirty = true; }
      w.still_n += 1;
      if (w.mode === "arr" && w.still_n >= STILL_N) { emit(w, "arr", w.t0, w.still_at); w.mode = "park"; w.t0 = null; w.rwy = null; dirty = true; }
      // 出発のあと長く止まった（5分）：離陸ではなく場所の移動だったとみて、止まっている機体に戻す
      else if (w.mode === "dep" && w.still_n >= 10 && !onRunway(p, rws)) { w.mode = "park"; w.t0 = null; w.rwy = null; dirty = true; }
    } else {
      if (w.mode === "park") {
        // 止まっていた（2回以上）機体が動き出した：出発の始まり。止まりきっていなければ動き出しの時刻は分からない
        const t0 = w.still_n >= STILL_N ? t : null;
        if (changed({ mode: "dep" })) { w.mode = "dep"; w.t0 = t0; dirty = true; }
      }
      if (w.mode === "dep" && kt >= ROLL) { const r = onDeparture(p, rw); if (r && r !== w.rwy) { w.rwy = r; dirty = true; } }
      if (w.still_n) { w.still_n = 0; dirty = true; }
    }
    w.last_at = t; w.last_lat = p.lat; w.last_lon = p.lon; w.last_kt = p.kt;
    const every = still ? REWRITE_STILL : REWRITE_MOVE;
    if (dirty || now - Date.parse(w.written_at) >= every) { w.written_at = t; upserts.push(w); }
    else watch.set(p.id, w);   // 書かない回も、この回の中では新しい値を使う
  }
  // 見えなくなった機体
  for (const [hex, w] of watch) {
    if (seen.has(hex)) continue;
    const gone = now - Date.parse(w.last_at);
    if (w.mode === "dep" && (w.last_kt ?? 0) >= ROLL && gone >= 0) { emit(w, "dep", w.last_at, w.t0); deletes.push(hex); }   // 速く走ったあと地上にいない：離陸
    else if (w.mode === "dep" && gone >= GONE_DEP) deletes.push(hex);                                                     // 走っている途中で見えなくなった（分からない）
    else if (w.mode === "arr" && gone >= GONE_ARR) {
      if ((w.last_kt ?? 0) < 15) { emit({ ...w, stand_lat: w.last_lat, stand_lon: w.last_lon }, "arr", w.t0, w.last_at, true); }
      deletes.push(hex);
    } else if (w.mode === "park" && gone >= KEEP_PARK) deletes.push(hex);
  }
  return { upserts, moves, deletes };
}
