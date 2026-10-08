// 照合の実行（データの読み書きと OpenSky への問い合わせは外から渡す）
import { match, type OpenSkyFlight, type RecordedFlight, windowFor } from "./verify.ts";

export type Row = { id: number; fromIcao: string | null; toIcao: string | null; dep: number; arr: number; flightNo: string | null; attempts: number };
export type Deps = {
  loadFlights: () => Promise<Row[]>;
  fetchArrivals: (icao: string, begin: number, end: number) => Promise<OpenSkyFlight[]>;
  save: (id: number, status: "verified" | "no_data" | null, note: string, attempts: number) => Promise<void>;
};
export const JOB = { maxPerRun: 200, maxAttempts: 3 };

export async function runVerification(d: Deps) {
  const rows = (await d.loadFlights()).slice(0, JOB.maxPerRun);
  const sum = { checked: 0, verified: 0, no_data: 0, unmatched: 0, errors: 0 };
  const cache = new Map<string, OpenSkyFlight[]>();
  for (const r of rows) {
    sum.checked++;
    if (!r.fromIcao || !r.toIcao) { await d.save(r.id, "no_data", "ICAOコードのない空港", r.attempts + 1); sum.no_data++; continue; }
    const f: RecordedFlight = { fromIcao: r.fromIcao, toIcao: r.toIcao, dep: r.dep, arr: r.arr, flightNo: r.flightNo };
    const { begin, end } = windowFor(f);
    const key = `${r.toIcao}:${begin}:${end}`;
    let arrivals: OpenSkyFlight[];
    try {
      arrivals = cache.get(key) ?? await d.fetchArrivals(r.toIcao, begin, end);
      cache.set(key, arrivals);
    } catch (e) {
      sum.errors++; console.error("OpenSky", e); continue;     // 回数は数えず、次の晩にもう一度
    }
    const v = match(f, arrivals);
    if (v.status === "verified") { await d.save(r.id, "verified", `${(v.matched.callsign ?? "").trim()} ${v.byCallsign ? "便名一致" : "空港と時間帯で一致"}`, r.attempts + 1); sum.verified++; }
    else if (v.status === "no_data") { await d.save(r.id, "no_data", "到着記録なし", r.attempts + 1); sum.no_data++; }
    else { await d.save(r.id, null, "当てはまる便なし", r.attempts + 1); sum.unmatched++; }
  }
  return sum;
}
