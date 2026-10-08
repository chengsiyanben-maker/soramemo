// チェックイン判定（サーバー側）。DBやネットワークに触れない純粋な関数だけを置く。
// 数値は 2026年10月の羽田実地検証を反映している。

// extra：番外編（自衛隊・米軍の飛行場、滑空場）。民間空港より優先度が低く、これらとの間はフライトにしない
export type Airport = { id: number; name: string; iata: string; lat: number; lon: number; radius_m: number; rare: boolean; extra?: boolean };
export type Terminal = { id: string; airport_id: number; name: string; tag: string; lat: number; lon: number; stamp_m?: number };
export type LastCheckin = { airport_id: number; terminal_id: string | null; at: number } | null;
export type Position = { lat: number; lon: number; acc: number; ts: number };

export const RULE = {
  maxAccuracyM: 1000,      // これより誤差が大きい位置は受け付けない
  maxPositionAgeMs: 5 * 60e3, // 端末で取得してから5分以上たった位置は古いとみなす
  maxQueuedAgeMs: 24 * 36e5,  // 電波がなく端末に保留したチェックインは、24時間以内なら受け付ける
  maxFutureSkewMs: 2 * 60e3,  // 端末時計の進みすぎの許容
  minIntervalMs: 20e3,     // 同じ利用者の連続チェックインの最短間隔
  sameSpotMin: 30,         // 同じ空港・同じターミナルへの再チェックインを無視する分数
  flightMaxGapH: 24,       // 出発から到着までの最大時間
  flightMaxKmh: 1000,      // これより速い移動はフライトとして認めない
  termRadiusM: 800,        // ターミナルから800m以内も空港の範囲とする
  termStampM: 400,         // ターミナルの印はそのターミナルから400m以内のときだけ
};

export function km(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const R = 6371, r = Math.PI / 180;
  const dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export type Place = { airport: Airport; terminal: Terminal | null; within: boolean; distKm: number };

// 民間空港の範囲内なら民間空港。そうでなければ、範囲内の番外編の飛行場。どちらでもなければ、いちばん近い民間空港（範囲外の案内用）
export function locate(p: { lat: number; lon: number }, airports: Airport[], terminals: Terminal[]): Place {
  const civil = airports.filter((a) => !a.extra), extra = airports.filter((a) => a.extra);
  const c = locateIn(p, civil.length ? civil : airports, terminals);
  if (c.within || !extra.length) return c;
  let eb = extra[0], ed = Infinity;
  for (const a of extra) { const k = km(p, a); if (k < ed) { ed = k; eb = a; } }
  if (ed * 1000 <= eb.radius_m) return { airport: eb, terminal: null, within: true, distKm: ed };
  return c;
}
function locateIn(p: { lat: number; lon: number }, airports: Airport[], terminals: Terminal[]): Place {
  let best = airports[0], d = Infinity;
  for (const a of airports) { const k = km(p, a); if (k < d) { d = k; best = a; } }
  const byId = new Map(airports.map((a) => [a.id, a]));
  for (const t of terminals) { const k = km(p, t); if (k < d) { d = k; best = byId.get(t.airport_id)!; } }
  let term: Terminal | null = null, tk = Infinity;
  for (const t of terminals) { if (t.airport_id !== best.id) continue; const k = km(p, t); if (k < tk) { tk = k; term = t; } }
  const airportKm = km(p, best);
  const within = airportKm * 1000 <= best.radius_m || (term !== null && tk * 1000 <= RULE.termRadiusM);
  return { airport: best, terminal: term && tk * 1000 <= (term.stamp_m ?? RULE.termStampM) ? term : null, within, distKm: Math.min(d, airportKm) };
}

export type Decision =
  | { ok: false; reason: string; message: string; place?: Place }
  | {
    ok: true; at: number; place: Place; flags: string[];
    flight: { from: number; to: number; dep: number; arr: number; km: number } | null;
  };

// queued = 電波がなく端末に保留していたチェックイン。判定の時刻は端末が位置を取った時刻（p.ts）を使い、offline の印を付ける
export function decide(p: Position, now: number, last: LastCheckin, airports: Airport[], terminals: Terminal[], queued = false): Decision {
  if (!(Number.isFinite(p.lat) && Number.isFinite(p.lon) && Math.abs(p.lat) <= 90 && Math.abs(p.lon) <= 180)) {
    return { ok: false, reason: "bad_position", message: "位置の形式が正しくありません。" };
  }
  if (!Number.isFinite(p.acc) || p.acc <= 0) return { ok: false, reason: "bad_accuracy", message: "位置の誤差が不明です。" };
  const maxAge = queued ? RULE.maxQueuedAgeMs : RULE.maxPositionAgeMs;
  if (!Number.isFinite(p.ts) || now - p.ts > maxAge || p.ts - now > RULE.maxFutureSkewMs) {
    return { ok: false, reason: "stale_position", message: queued ? "24時間以上前のチェックインは送れません。" : "古い位置は使えません。もう一度チェックインしてください。" };
  }
  const at = queued ? Math.min(p.ts, now) : now;
  if (queued && last && at <= last.at) {
    return { ok: false, reason: "out_of_order", message: "このチェックインより後の記録がすでにあるため、送れませんでした。" };
  }
  if (p.acc > RULE.maxAccuracyM) {
    return { ok: false, reason: "low_accuracy", message: `位置の精度が低すぎます（誤差 約${Math.round(p.acc)}m）。窓の近くか屋外でもう一度押してください。` };
  }
  if (last && at - last.at < RULE.minIntervalMs) {
    return { ok: false, reason: "too_soon", message: "少し時間をおいてからもう一度押してください。" };
  }
  const place = locate(p, airports, terminals);
  if (!place.within) {
    const rest = Math.max(0, place.distKm - place.airport.radius_m / 1000);
    return { ok: false, reason: "out_of_range", message: `${place.airport.name}の判定範囲の外です。あと約${rest.toFixed(1)}km近づいてください。`, place };
  }
  const tid = place.terminal ? place.terminal.id : null;
  if (last && last.airport_id === place.airport.id && last.terminal_id === tid && at - last.at < RULE.sameSpotMin * 60e3) {
    return { ok: false, reason: "already", message: "ここにはチェックイン済みです。", place };
  }

  const flags: string[] = [];
  if (p.acc > 300) flags.push("low_accuracy");
  if (queued) flags.push("offline");
  let flight = null;
  if (last && last.airport_id !== place.airport.id) {
    const h = (at - last.at) / 36e5;
    const a = airports.find((x) => x.id === last.airport_id);
    if (a && h <= RULE.flightMaxGapH && !a.extra && !place.airport.extra) {
      const d = km(a, place.airport);
      if (h > 0 && d / h <= RULE.flightMaxKmh) flight = { from: a.id, to: place.airport.id, dep: last.at, arr: at, km: d };
      else flags.push("impossible_speed"); // 旅客機でも不可能な速さ。フライトにせず、目視確認の対象にする
    }
  }
  return { ok: true, at, place, flags, flight };
}
