// 日本中の空港の、着陸・離陸した滑走路を、1日の航跡（track_points：15,000ft 未満を1分に1点）から見つける（判定だけ）
//   着陸：空港の近く（8km 以内）で 3,000ft 以下の最後の点が、滑走路の延長線の上（横のずれ 0.8km 以内・進入端の手前15kmから滑走路の上まで）にあり、
//         その前の点からの進む向きが滑走路の向きと45°以内
//   離陸：空港の近く（12km 以内）で 3,000ft 以下の最初の点が、滑走路の先の線の上（横のずれ 0.8km 以内・始まりから先へ16kmまで）にあり、
//         次の点への進む向きが滑走路の向きと45°以内
//   来た方面：航跡が空港から120・60・30km の円に入った方角（着陸）、出た方角（離陸）
import { flightOfCallsign } from "./flight_watch.ts";
import { encodePolyline } from "./archive.ts";

export type Rwy = { id: string; thr: [number, number]; hdg: number };
export type Ap = { center: [number, number]; rw: Record<string, Rwy> };
export type Pt = [number, number, number, number];   // [秒, 緯度, 経度, 高度（百フィート）]

const R = Math.PI / 180;
export const km = (a: [number, number], b: [number, number]) => { const h = Math.sin((b[0] - a[0]) * R / 2) ** 2 + Math.cos(a[0] * R) * Math.cos(b[0] * R) * Math.sin((b[1] - a[1]) * R / 2) ** 2; return 2 * 6371 * Math.asin(Math.sqrt(h)); };
export const brg = (a: [number, number], b: [number, number]) => { const y = Math.sin((b[1] - a[1]) * R) * Math.cos(b[0] * R), x = Math.cos(a[0] * R) * Math.sin(b[0] * R) - Math.sin(a[0] * R) * Math.cos(b[0] * R) * Math.cos((b[1] - a[1]) * R); return (Math.atan2(y, x) / R + 360) % 360; };
const angd = (a: number, b: number) => Math.abs(((a - b + 540) % 360) - 180);
const ll = (p: Pt): [number, number] => [p[1], p[2]];

// 滑走路の線からの位置：along は進入端から手前（着陸してくる側）へ正、lat は横のずれ
function rel(r: Rwy, p: [number, number]) {
  const d = km(r.thr, p); if (d < 0.02) return { along: 0, lat: 0 };
  const a = (brg(r.thr, p) - r.hdg) * R; return { along: -d * Math.cos(a), lat: Math.abs(d * Math.sin(a)) };
}
// 反対向きの滑走路の進入端（離陸の始まり）。同じ滑走路で向きが反対のもの
function startOf(ap: Ap, r: Rwy): [number, number] {
  let best: Rwy | null = null;
  for (const o of Object.values(ap.rw)) if (o.id !== r.id && angd(o.hdg, r.hdg + 180) < 12 && (!best || km(o.thr, r.thr) > km(best.thr, r.thr))) {
    // 平行滑走路のうち、横のずれがいちばん小さい（同じ滑走路）もの
    const lat = rel(r, o.thr).lat; if (lat < 0.25) best = o;
  }
  return best ? best.thr : r.thr;
}

// 着陸：空港から22km 以内の最後の3点までを後ろから見て、最初に滑走路の延長線に乗っていた点で決める。
//   延長線の幅は遠いほど広く（0.6km＋手前の距離の5%）、高さは3°の進入の線より上すぎないこと（1,500ft＋1km ごとに200ft）
export function landingRwy(ap: Ap, pts: Pt[]): string | null {
  const idx = pts.map((p, i) => i).filter((i) => km(ap.center, ll(pts[i])) <= 22).slice(-3).reverse();
  for (const i of idx) {
    const p = pts[i], q = pts[i - 1]; if (!q || km(ll(q), ll(p)) < 0.3) continue;
    const mv = brg(ll(q), ll(p)); let best: string | null = null, bl = Infinity;
    for (const r of Object.values(ap.rw)) {
      if (angd(mv, r.hdg) > 40) continue;
      const { along, lat } = rel(r, ll(p));
      if (along < -4 || along > 22 || lat > 0.6 + 0.05 * Math.max(0, along) || p[3] > 15 + 2 * Math.max(0, along)) continue;
      if (lat < bl) { bl = lat; best = r.id; }
    }
    if (best) return best;
  }
  return null;
}
// 離陸：空港から22km 以内の最初の3点までを見て、最初に滑走路の先の線に乗っていた点で決める（幅は0.5km＋滑走路の先の距離の4%）
export function departureRwy(ap: Ap, pts: Pt[]): string | null {
  const idx = pts.map((p, i) => i).filter((i) => km(ap.center, ll(pts[i])) <= 22).slice(0, 3);
  for (const i of idx) {
    // 進む向きでは決めない（離陸してすぐ曲がる機体が多い）。滑走路の始まりから見た位置だけで
    const p = pts[i]; let best: string | null = null, bl = Infinity;
    for (const r of Object.values(ap.rw)) {
      const s0 = startOf(ap, r), d = km(s0, ll(p)), a = (brg(s0, ll(p)) - r.hdg) * R, fw = d * Math.cos(a), lat = Math.abs(d * Math.sin(a));
      const past = Math.max(0, fw - km(s0, r.thr) - 3);   // 滑走路の終わりから先の距離
      // 滑走路が1本（向きが2つ）だけの空港は、離陸してすぐ曲がっても取り違えがないので、幅を広く
      const one = Object.keys(ap.rw).length <= 2, w = one ? 1.0 + 0.1 * past : 0.5 + 0.04 * past;
      if (fw < 0.5 || fw > 25 || lat > w || p[3] > 15 + 2 * past) continue;
      if (lat < bl) { bl = lat; best = r.id; }
    }
    if (best) return best;
  }
  return null;
}
// 1つの機体の1日の点を、20分より長く途切れたところで航跡に分ける
export function splitTracks(pts: Pt[]): Pt[][] {
  const out: Pt[][] = []; let cur: Pt[] = [];
  for (const p of [...pts].sort((a, b) => a[0] - b[0])) { if (cur.length && p[0] - cur[cur.length - 1][0] > 20 * 60) { out.push(cur); cur = []; } cur.push(p); }
  if (cur.length) out.push(cur); return out;
}
const enter = (c: [number, number], pts: Pt[], r: number) => { const p = pts.find((x) => km(c, ll(x)) <= r); return p ? Math.round(brg(c, ll(p))) : null; };
const leave = (c: [number, number], pts: Pt[], r: number) => { const p = pts.find((x) => km(c, ll(x)) >= r); return p ? Math.round(brg(c, ll(p))) : null; };

export type Sample = { iata: string; dir: "arr" | "dep"; at: string; callsign: string; flight: string | null; rwy: string; first_brg: number | null; first_km: number | null;
  ent120: number | null; ent60: number | null; ent30: number | null; ex30: number | null; ex60: number | null; pts: [number, number, number, number][] };
// 1つの機体の航跡から、着陸・離陸の記録を出す（自家用機など、呼び出し符号が登録記号の形のものは除く）
export function samplesOf(callsign: string, pts: Pt[], aps: Record<string, Ap>, skip: Set<string> = new Set()): Sample[] {
  if (!/^[A-Z]{3}\d{1,4}[A-Z]?$/.test(callsign)) return [];
  const out: Sample[] = [], fl = flightOfCallsign(callsign);
  for (const tr of splitTracks(pts)) {
    if (tr.length < 3) continue;
    const thin = tr.slice(-40).map((p) => [p[0], p[1], p[2], p[3] * 100] as [number, number, number, number]);
    const last = tr[tr.length - 1], first = tr[0];
    for (const [iata, ap] of Object.entries(aps)) {
      if (skip.has(iata)) continue;
      if (km(ap.center, ll(last)) <= 22) {
        const rw = landingRwy(ap, tr);
        if (rw) out.push({ iata, dir: "arr", at: new Date(last[0] * 1000).toISOString(), callsign, flight: fl, rwy: rw, first_brg: Math.round(brg(ap.center, ll(first))), first_km: Math.round(km(ap.center, ll(first)) * 10) / 10,
          ent120: enter(ap.center, tr, 120), ent60: enter(ap.center, tr, 60), ent30: enter(ap.center, tr, 30), ex30: null, ex60: null, pts: thin });
      }
      if (km(ap.center, ll(first)) <= 22) {
        const rw = departureRwy(ap, tr);
        if (rw) out.push({ iata, dir: "dep", at: new Date(first[0] * 1000).toISOString(), callsign, flight: fl, rwy: rw, first_brg: null, first_km: null,
          ent120: null, ent60: null, ent30: null, ex30: leave(ap.center, tr, 30), ex60: leave(ap.center, tr, 60), pts: tr.slice(0, 40).map((p) => [p[0], p[1], p[2], p[3] * 100]) });
      }
    }
  }
  return out;
}

// 空の道すじ用：1つの機体の航跡のうち、空港から80km 以内の部分（出発・到着した空港ごとに1本）
export type TrackRow = { iata: string; day: string; callsign: string; at: string; dep_here: 0 | 1; pts: string };
// 空港の近くの判定：最初（出発）・最後（到着）の点が空港から22km 以内。
// 地上の近くで電波が届きにくい空港（成田など）では、離陸した機体が最初に見えるのが22km より先になることがあるので、
// 45km 以内でも「6,000ft 以下で、上りながら空港から離れていく（到着は、下りながら近づいてくる）」ときは数える。いちばん近い空港のときだけ
const TRK_NEAR = 22, TRK_LOOSE = 45, TRK_LOW = 60;
function nearestAp(p: Pt, aps: Record<string, Ap>): string | null {
  let best: string | null = null, bd = Infinity;
  for (const [iata, ap] of Object.entries(aps)) { const d = km(ap.center, ll(p)); if (d < bd) { bd = d; best = iata; } }
  return best;
}
// win：読んだ時間の幅（秒）。幅の端から20分以内に始まる・終わる航跡は、まだ途中かもしれないので入れない
//   （3時間ごとに、前後が重なる幅で読むので、途中で切れた航跡は次か前の回にまるごと入る）
export const TRK_EDGE = 20 * 60;
export function tracksOf(callsign: string, pts: Pt[], aps: Record<string, Ap>, win?: { from: number; to: number }): TrackRow[] {
  if (!/^[A-Z]{3}\d{1,4}[A-Z]?$/.test(callsign)) return [];
  const out: TrackRow[] = [];
  for (const tr of splitTracks(pts)) {
    if (tr.length < 3) continue;
    if (win && (tr[0][0] < win.from + TRK_EDGE || tr[tr.length - 1][0] > win.to - TRK_EDGE)) continue;
    const first = tr[0], last = tr[tr.length - 1], first3 = tr[Math.min(tr.length - 1, 3)], last3 = tr[Math.max(0, tr.length - 4)];
    let nf: string | null | undefined, nl: string | null | undefined;
    for (const [iata, ap] of Object.entries(aps)) {
      const dl = km(ap.center, ll(last)), df = km(ap.center, ll(first));
      // 高さの変わり方（百フィート）。離陸してから空港の上へ戻ってくる出発（成田の西行きなど）は、最後の点も空港の近くになるので、
      // 全体で2,000ft より上っていれば到着にしない。下っていれば出発にしない
      const climb = (last[3] ?? 0) - (first[3] ?? 0);
      const arrGeo = dl <= TRK_NEAR || (dl <= TRK_LOOSE && last[3] <= TRK_LOW && last3[3] > last[3] && km(ap.center, ll(last3)) > dl && (nl ??= nearestAp(last, aps)) === iata);
      const arr = arrGeo && climb <= 20;
      const dep = !arr && climb >= -20 && (df <= TRK_NEAR || (df <= TRK_LOOSE && first[3] <= TRK_LOW && first3[3] > first[3] && km(ap.center, ll(first3)) > df && (nf ??= nearestAp(first, aps)) === iata));
      if (!arr && !dep) continue;
      const near = tr.filter((p) => km(ap.center, ll(p)) <= 80); if (near.length < 2) continue;
      const t = arr ? last[0] : first[0];
      const s = encodePolyline(near.map((p) => ({ lat: p[1], lon: p[2] }))); if (s.length > 4000) continue;
      out.push({ iata, day: new Date(t * 1000 + 9 * 3600_000).toISOString().slice(0, 10), callsign, at: new Date(t * 1000).toISOString(), dep_here: dep ? 1 : 0, pts: s });
    }
  }
  return out;
}
