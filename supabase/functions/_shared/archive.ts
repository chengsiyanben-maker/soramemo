// 毎日の飛行機の記録（便ごとの実績・間引いた航跡）を作る部品。daily-archive から使う。
// 便ごとの実績：時刻表（ODPT）に、航空会社の運航情報（実際の時刻）と、機体の位置からの推定（離陸・着陸・登録記号・機種）を合わせる。
// 共同運航で同じ便が複数の便名で載っているときは1つにまとめ、ほかの便名は also に残す。

export type SchedRow = {
  svc_date: string; flight: string; dep: string; arr: string; std: string; sta: string;
  atd: string | null; ata: string | null; dep_status: string | null; arr_status: string | null;
  aircraft: string | null; source: string; state: Record<string, unknown> | null;
};
export type History = {
  svc_date: string; flight: string; dep: string; arr: string; std: string; sta: string;
  atd: string | null; ata: string | null; atd_src: "odpt" | "adsb" | null; ata_src: "odpt" | "adsb" | null;
  dep_delay: number | null; arr_delay: number | null; cancelled: boolean; diverted_to: string | null;
  aircraft: string | null; type: string | null; reg: string | null; callsign: string | null; also: string[];
  eta60?: string | null; eta30?: string | null; eta15?: string | null;
};

const num = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;
const str = (v: unknown): string | null => typeof v === "string" && v ? v : null;
const iso = (ms: number | null) => ms == null ? null : new Date(ms).toISOString();
const mins = (a: string | null, b: string) => a == null ? null : Math.round((Date.parse(a) - Date.parse(b)) / 60_000);

export function toHistory(r: SchedRow): History {
  const st = r.state ?? {};
  const takeoff = st.takeoff_est === false ? num(st.takeoff_at) : null;
  const landedIata = str(st.landed_iata), landed = num(st.landed_at);
  const atd = r.atd ?? iso(takeoff), ata = r.ata ?? (landedIata === r.arr ? iso(landed) : null);
  const cancelled = /cancel/i.test(r.dep_status ?? "") || /cancel/i.test(r.arr_status ?? "");
  return {
    svc_date: r.svc_date, flight: r.flight, dep: r.dep, arr: r.arr, std: r.std, sta: r.sta,
    atd: cancelled ? null : atd, ata: cancelled ? null : ata,
    atd_src: cancelled || !atd ? null : r.atd ? "odpt" : "adsb", ata_src: cancelled || !ata ? null : r.ata ? "odpt" : "adsb",
    dep_delay: cancelled ? null : mins(atd, r.std), arr_delay: cancelled ? null : mins(ata, r.sta), cancelled,
    diverted_to: !cancelled && landedIata && landedIata !== r.arr && landedIata !== r.dep ? landedIata : null,
    aircraft: r.aircraft, type: str(st.type), reg: str(st.reg), callsign: str(st.cs), also: [],
    eta60: iso(num(st.eta60)), eta30: iso(num(st.eta30)), eta15: iso(num(st.eta15)),
  };
}

// 共同運航のまとめ：出発・到着の空港と定刻が同じ便を1つにする。機体を見つけた便（呼び出し符号がある便）、
// 航空会社の実際の時刻がある便を優先し、残りの便名は also に入れる
export function buildHistory(rows: SchedRow[]): History[] {
  const groups = new Map<string, History[]>();
  for (const r of rows) {
    const h = toHistory(r), k = `${h.dep}|${h.arr}|${h.std}|${h.sta}`;
    const g = groups.get(k); if (g) g.push(h); else groups.set(k, [h]);
  }
  const score = (h: History) => (h.callsign ? 4 : 0) + (h.atd_src === "odpt" || h.ata_src === "odpt" ? 2 : 0) + (h.reg ? 1 : 0);
  const out: History[] = [];
  for (const g of groups.values()) {
    g.sort((a, b) => score(b) - score(a) || a.flight.localeCompare(b.flight));
    const best = { ...g[0], also: g.slice(1).map((x) => x.flight).sort() };
    // ほかの便名の方にだけある情報で埋める（実際の時刻・登録記号など）
    for (const x of g.slice(1)) {
      if (!best.atd && x.atd) { best.atd = x.atd; best.atd_src = x.atd_src; best.dep_delay = x.dep_delay; }
      if (!best.ata && x.ata) { best.ata = x.ata; best.ata_src = x.ata_src; best.arr_delay = x.arr_delay; }
      best.reg ??= x.reg; best.type ??= x.type; best.callsign ??= x.callsign; best.aircraft ??= x.aircraft;
      best.eta60 ??= x.eta60; best.eta30 ??= x.eta30; best.eta15 ??= x.eta15;
      if (x.cancelled && !best.atd && !best.ata) best.cancelled = true;
    }
    out.push(best);
  }
  return out.sort((a, b) => a.std.localeCompare(b.std) || a.flight.localeCompare(b.flight));
}

// 航跡の間引き：前の点から 1.2km 未満、かつ高度の差が 500ft 未満の点は捨てる（最後の点は残す）
export type Pt = { lat: number; lon: number; alt: number | null };
function kmBetween(a: Pt, b: Pt) {
  const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
export function thin(pts: Pt[]): Pt[] {
  if (pts.length <= 2) return pts.slice();
  const out = [pts[0]];
  for (let i = 1; i < pts.length - 1; i++) {
    const p = pts[i], q = out[out.length - 1];
    if (kmBetween(p, q) >= 1.2 || Math.abs((p.alt ?? 0) - (q.alt ?? 0)) >= 500) out.push(p);
  }
  out.push(pts[pts.length - 1]);
  return out;
}

// Google の polyline 形式（小数4桁＝約11m）。高度は百フィート単位で別の列に入れる
export function encodePolyline(pts: { lat: number; lon: number }[], precision = 4): string {
  const f = 10 ** precision; let lat = 0, lon = 0, s = "";
  const enc = (v: number) => { let x = v < 0 ? ~(v << 1) : v << 1; let o = ""; while (x >= 0x20) { o += String.fromCharCode((0x20 | (x & 0x1f)) + 63); x >>= 5; } return o + String.fromCharCode(x + 63); };
  for (const p of pts) { const a = Math.round(p.lat * f), b = Math.round(p.lon * f); s += enc(a - lat) + enc(b - lon); lat = a; lon = b; }
  return s;
}
export function decodePolyline(s: string, precision = 4): { lat: number; lon: number }[] {
  const f = 10 ** precision, out: { lat: number; lon: number }[] = []; let i = 0, lat = 0, lon = 0;
  const next = () => { let r = 0, sh = 0, b; do { b = s.charCodeAt(i++) - 63; r |= (b & 0x1f) << sh; sh += 5; } while (b >= 0x20); return r & 1 ? ~(r >> 1) : r >> 1; };
  while (i < s.length) { lat += next(); lon += next(); out.push({ lat: lat / f, lon: lon / f }); }
  return out;
}

// 前の日（日本時間）の日付
export function jstYesterday(now = Date.now()): string {
  return new Date(now + 9 * 3600_000 - 86_400_000).toISOString().slice(0, 10);
}

// 便名の0を取る（時刻表は NH059、利用者の記録は NH59）
export const normFlight = (f: string) => f.toUpperCase().replace(/^([A-Z0-9]{2})0+(\d)/, "$1$2");
// 利用者のフライトの航跡（flights.track：[[緯度, 経度], ...] 2〜200点）。多ければ間を均等に間引く（最初と最後は残す）
export function userTrack(pts: { lat: number; lon: number }[], max = 200): [number, number][] | null {
  if (pts.length < 2) return null;
  const out: [number, number][] = [];
  const n = Math.min(max, pts.length);
  for (let i = 0; i < n; i++) { const p = pts[Math.round(i * (pts.length - 1) / (n - 1))]; out.push([Math.round(p.lat * 1e4) / 1e4, Math.round(p.lon * 1e4) / 1e4]); }
  return out;
}
