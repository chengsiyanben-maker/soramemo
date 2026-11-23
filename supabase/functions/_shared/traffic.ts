// 空港の周りを今飛んでいる機体（OpenSky の /states/all）を、地図に描ける形にする。取得とは分けて、テストしやすくしている。
//   states の1件：[icao24, callsign, 国, 位置の時刻, 最後の受信, 経度, 緯度, 気圧高度m, 地上か, 速度m/s, 進行方向, 昇降率m/s, …]

export type Plane = {
  id: string; callsign: string | null;
  lat: number; lon: number; alt_ft: number | null; kt: number | null; hdg: number | null; fpm: number | null;
  phase: "arr" | "dep" | "other";        // 着陸に向かっている・離陸して上昇中・それ以外
  dist_km: number;                         // 空港からの距離
};

const num = (v: unknown) => typeof v === "number" && Number.isFinite(v) ? v : null;
function km(a: [number, number], b: [number, number]) {
  const r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

function bearing(a: [number, number], b: [number, number]) {
  const r = Math.PI / 180, y = Math.sin((b[1] - a[1]) * r) * Math.cos(b[0] * r);
  const x = Math.cos(a[0] * r) * Math.sin(b[0] * r) - Math.sin(a[0] * r) * Math.cos(b[0] * r) * Math.cos((b[1] - a[1]) * r);
  return (Math.atan2(y, x) / r + 360) % 360;
}

// 空中にいて、高度 maxFt 以下の機体だけ。着陸・離陸の見分けは、昇降率と高度と空港からの距離で
// others：近くのほかの空港。そちらへ向かう（そちらから離れていく）機体は、この空港の着陸・離陸に数えない
// （成田から見た羽田の機体、伊丹から見た関西の機体など。関西の24の進入は伊丹の近くを回るため、距離だけでなく向きで見分ける）
export function planesFrom(states: unknown, apt: [number, number], maxFt = 14000, others: [number, number][] = []): Plane[] {
  if (!Array.isArray(states)) return [];
  const out: Plane[] = [];
  for (const s of states) {
    if (!Array.isArray(s) || s[8] === true) continue;
    const lat = num(s[6]), lon = num(s[5]); if (lat == null || lon == null) continue;
    const altM = num(s[7]) ?? num(s[13]); const alt = altM == null ? null : Math.round(altM * 3.281);
    if (alt != null && alt > maxFt) continue;
    const vr = num(s[11]), fpm = vr == null ? null : Math.round(vr * 196.85);
    const d = km(apt, [lat, lon]);
    let phase: Plane["phase"] = fpm != null && fpm <= -300 ? "arr" : fpm != null && fpm >= 300 ? "dep"
      : alt != null && alt < 3000 && d < 25 ? "arr" : "other";   // 低くて空港に近く、ほぼ水平なら最終進入とみなす
    if (phase !== "other") {
      // 向かっている（離陸なら離れていく）空港ほど点が小さくなるようにして、40km以内のほかの空港のほうが小さければ、そちらの機体とみなす
      const hdg = num(s[10]);
      const score = (o: [number, number]) => {
        const dd = km(o, [lat, lon]); if (hdg == null) return dd;
        const c = Math.cos((hdg - bearing([lat, lon], o)) * Math.PI / 180);
        return dd * (phase === "arr" ? 2 - c : 2 + c);
      };
      const mine = score(apt);
      if (others.some((o) => km(o, [lat, lon]) < 40 && score(o) < mine)) phase = "other";
    }
    out.push({
      id: String(s[0]), callsign: typeof s[1] === "string" && s[1].trim() ? s[1].trim() : null,
      lat: Math.round(lat * 1e4) / 1e4, lon: Math.round(lon * 1e4) / 1e4, alt_ft: alt,
      kt: num(s[9]) == null ? null : Math.round(num(s[9])! * 1.944), hdg: num(s[10]) == null ? null : Math.round(num(s[10])!), fpm,
      phase, dist_km: Math.round(d * 10) / 10,
    });
  }
  return out.sort((a, b) => a.dist_km - b.dist_km);
}

// 機体ごとの通ってきた線。新しい位置を足し、古い点（keepMs より前）と、いなくなった機体を消す
export type Trails = Map<string, { t: number; p: [number, number] }[]>;
export function updateTrails(trails: Trails, planes: Plane[], now: number, keepMs = 20 * 60_000) {
  const seen = new Set(planes.map((p) => p.id));
  for (const id of [...trails.keys()]) if (!seen.has(id)) trails.delete(id);
  for (const p of planes) {
    const tr = trails.get(p.id) ?? [];
    const last = tr[tr.length - 1];
    if (!last || last.p[0] !== p.lat || last.p[1] !== p.lon) tr.push({ t: now, p: [p.lat, p.lon] });
    while (tr.length && now - tr[0].t > keepMs) tr.shift();
    trails.set(p.id, tr);
  }
}

// adsb.lol（/v2/lat/…/lon/…/dist/…）の ac を、同じ形にする。
//   ac の1件：hex・flight（便名）・t（機種）・r（登録記号 JA…）・lat・lon・alt_baro（ft か "ground"）・gs（ノット）・track・baro_rate（ft/分）
export function planesFromAdsb(ac: unknown, apt: [number, number], maxFt = 14000, others: [number, number][] = []): (Plane & { type: string | null; reg: string | null })[] {
  if (!Array.isArray(ac)) return [];
  const states = ac.filter((a) => a && typeof a === "object" && (a as Record<string, unknown>).alt_baro !== "ground").map((a) => {
    const x = a as Record<string, unknown>;
    const ft = num(x.alt_baro) ?? num(x.alt_geom), fpm = num(x.baro_rate) ?? num(x.geom_rate);
    // planesFrom と同じ並び（高度はm、速度はm/s、昇降率はm/s）に直して、同じ見分け方を使う
    return [x.hex, x.flight ?? null, null, null, null, num(x.lon), num(x.lat), ft == null ? null : ft / 3.281, false,
      num(x.gs) == null ? null : num(x.gs)! / 1.944, num(x.track), fpm == null ? null : fpm / 196.85, null, null];
  });
  const types = new Map(ac.map((a) => [String((a as Record<string, unknown>)?.hex), typeof (a as Record<string, unknown>)?.t === "string" ? (a as Record<string, unknown>).t as string : null]));
  const regs = new Map(ac.map((a) => [String((a as Record<string, unknown>)?.hex), typeof (a as Record<string, unknown>)?.r === "string" ? (a as Record<string, unknown>).r as string : null]));
  return planesFrom(states, apt, maxFt, others).map((p) => ({ ...p, type: types.get(p.id) ?? null, reg: regs.get(p.id) ?? null }));
}

// 地上の機体（11/22 PM「羽田の3D に地上の機体」）：adsb.lol の ac のうち alt_baro が "ground" で、空港の中心から km 以内のもの。
//   planesFromAdsb は地上の機体を落とすので、別に返す（答えの ground）。空港の車両（category C1〜C3・便名 TEST）と、機種も登録記号もないものは入れない。
//   hdg：進む向き（track。止まっていて送らないときは true_heading・mag_heading、それもなければ null）。moving：5ノット以上
export type GroundPlane = { id: string; callsign: string | null; lat: number; lon: number; hdg: number | null; kt: number | null; type: string | null; reg: string | null; moving: boolean };
export function groundFromAdsb(ac: unknown, apt: [number, number], km = 5): GroundPlane[] {
  if (!Array.isArray(ac)) return [];
  const out: GroundPlane[] = [], kx = 111.32 * Math.cos(apt[0] * Math.PI / 180);
  for (const a of ac) {
    const x = a as Record<string, unknown>;
    if (!x || typeof x !== "object" || x.alt_baro !== "ground") continue;
    const lat = num(x.lat), lon = num(x.lon); if (lat == null || lon == null) continue;
    if (Math.hypot((lon - apt[1]) * kx, (lat - apt[0]) * 110.57) > km) continue;
    const cs = typeof x.flight === "string" ? x.flight.trim().toUpperCase() : "";
    const type = typeof x.t === "string" && x.t ? x.t : null, reg = typeof x.r === "string" && x.r ? x.r : null;
    if (typeof x.category === "string" && /^C/.test(x.category)) continue;
    if (/^TEST/.test(cs) || (!type && !reg)) continue;
    const hdg = num(x.track) ?? num(x.true_heading) ?? num(x.mag_heading), kt = num(x.gs);
    out.push({ id: String(x.hex ?? `cs-${cs}`), callsign: cs || null, lat: Math.round(lat * 1e5) / 1e5, lon: Math.round(lon * 1e5) / 1e5,
      hdg: hdg == null ? null : Math.round(hdg) % 360, kt: kt == null ? null : Math.round(kt), type, reg, moving: (kt ?? 0) >= 5 });
  }
  return out;
}

// 記録の処理（30秒ごと）が live_positions に残した日本中の機体の位置を、adsb.lol の ac と同じ形に戻す。
//   見る人の呼び出しでは adsb.lol に問い合わせず、これを使う（adsb.lol への問い合わせを、見る人の数によらず30秒に3回に保つ）。
//   live_positions は便名のある機体だけなので、便名のない機体（自家用機の一部など）は出ない。maxAgeMs より古い位置は使わない
export type LiveRow = { callsign: string; hex: string | null; lat: number; lon: number; alt_ft: number | null; ground: boolean; fpm: number | null; kt: number | null; trk?: number | null; type: string | null; reg: string | null; seen_at: string };
export function acFromLive(rows: LiveRow[], now: number, maxAgeMs = 75_000): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = [];
  for (const r of rows ?? []) {
    const t = Date.parse(r.seen_at); if (!Number.isFinite(t) || now - t > maxAgeMs) continue;
    out.push({ hex: r.hex ?? `cs-${r.callsign}`, flight: r.callsign, t: r.type ?? undefined, r: r.reg ?? undefined, lat: r.lat, lon: r.lon,
      alt_baro: r.ground ? "ground" : r.alt_ft, gs: r.kt, track: r.trk ?? null, baro_rate: r.fpm });
  }
  return out;
}

// 429（回数の上限）・420 のときに待つ時間。Retry-After（秒）があればそれ、なければ既定。長く待ちすぎない（maxMs まで）
export function retryAfterMs(h: string | null, def = 3000, maxMs = 5000): number {
  const s = Number(h); if (h != null && h.trim() !== "" && Number.isFinite(s) && s >= 0) return Math.min(maxMs, Math.round(s * 1000));
  return Math.min(maxMs, def);
}

// 記録の処理（30秒ごと）で、どの円の機体を航跡の点（track_points）と機体ごとの便の記録（reg_legs）に残すか。
//   slot：その回を始めた時刻の30秒の番号（Math.floor(始めた時刻 / 30000)）。偶数＝毎分の前半の回
//   東・西の円は毎回取るので、航跡は前半の回だけ（1分に1回）、便の記録は2分に1回。
//   北（新千歳）は前半の回だけ、南（那覇）は後半の回だけ取るので、航跡は取った回すべて（1分に1回）、便の記録は北が2分に1回・南も2分に1回（後半の回）。
//   （11/7 まで：時刻の偶数・奇数だけで決めていたので、後半の回にしか取らない南の円（沖縄・奄美・宮古・石垣）は、航跡の点も便の記録も残っていなかった）
export function recordPlan(key: string, slot: number): { track: boolean; legs: boolean } {
  if (key === "SOUTH") return { track: true, legs: slot % 4 === 1 };
  if (key === "NORTH") return { track: true, legs: slot % 4 === 0 };
  return { track: slot % 2 === 0, legs: slot % 4 === 0 };
}
