// 空港の近くにいる海外の航空会社の機体を、この空港に着く便・この空港を出た便に分ける（airport-foreign 関数の中身。取得とは分けてテストしやすくしている）
//   機体：live_positions（機体の記録が取った日本中の機体の最新の位置。adsb.lol の ADS-B）
//   経路：adsb.lol の経路のデータ（routeset）。もっともらしい（plausible）ものだけ使う。どちらも推定で、航空会社の発表ではない
import { foreignFlightOf } from "./flight_watch.ts";

export type LivePos = { callsign: string; lat: number; lon: number; alt_ft: number | null; ground: boolean; fpm: number | null; type?: string | null; reg?: string | null; seen_at: string };
export type Route = { callsign: string; dep: string; arr: string };
export type ForeignNow = { flight: string; airline: string; kind: "arr" | "dep"; other: string; status: "approach" | "landed" | "departed" | "ground"; alt_ft: number | null; type: string | null; km: number };

export function kmBetween(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

// 空港から maxKm 以内の、海外の航空会社の機体（近い順）
export function foreignNear(pos: LivePos[], at: { lat: number; lon: number }, maxKm = 60): (LivePos & { flight: string; airline: string; km: number })[] {
  const out = [];
  for (const p of pos) {
    const f = foreignFlightOf(p.callsign); if (!f) continue;
    const km = kmBetween(at, p); if (km > maxKm) continue;
    out.push({ ...p, ...f, km });
  }
  return out.sort((a, b) => a.km - b.km);
}

// adsb.lol の routeset の答え → 呼び出し符号ごとの経路（途中の空港があれば最初と最後）
// deno-lint-ignore no-explicit-any
//   答えに呼び出し符号がないときは、問い合わせた順（asked）で対応させる
export function parseRoutes(rows: any[], asked: string[] = []): Map<string, Route> {
  const m = new Map<string, Route>();
  (Array.isArray(rows) ? rows : []).forEach((x, i) => {
    const r = /^([A-Z]{3})-(?:[A-Z]{3}-)*([A-Z]{3})$/.exec(String(x?._airport_codes_iata ?? ""));
    const cs = String(typeof x?.callsign === "string" ? x.callsign : asked[i] ?? "").trim().toUpperCase();
    if (!r || !x?.plausible || !cs) return;
    m.set(cs, { callsign: cs, dep: r[1], arr: r[2] });
  });
  return m;
}

// この空港に着く便・この空港を出た便だけを、状態つきで返す。着陸した機体と出発前の機体は空港から8km以内のものだけ
export function classifyForeign(near: (LivePos & { flight: string; airline: string; km: number })[], routes: Map<string, Route>, iata: string): ForeignNow[] {
  const out: ForeignNow[] = [];
  for (const p of near) {
    const r = routes.get(p.callsign.trim().toUpperCase()); if (!r || r.dep === r.arr) continue;
    const kind = r.arr === iata ? "arr" : r.dep === iata ? "dep" : null; if (!kind) continue;
    const onGround = p.ground || (p.alt_ft != null && p.alt_ft < 200);
    if (onGround && p.km > 8) continue;
    const status = kind === "arr" ? (onGround ? "landed" : "approach") : (onGround ? "ground" : "departed");
    out.push({ flight: p.flight, airline: p.airline, kind, other: kind === "arr" ? r.dep : r.arr, status, alt_ft: onGround ? null : p.alt_ft, type: p.type ?? null, km: Math.round(p.km) });
  }
  return out;
}
