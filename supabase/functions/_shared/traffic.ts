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
