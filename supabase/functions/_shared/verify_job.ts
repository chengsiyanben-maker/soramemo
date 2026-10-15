// 照合の実行（データの読み書きと OpenSky への問い合わせは外から渡す）
import { match, type OpenSkyFlight, type RecordedFlight, windowFor } from "./verify.ts";
import { compactTrack } from "./track.ts";

export type Row = { id: number; fromIcao: string | null; toIcao: string | null; dep: number; arr: number; flightNo: string | null; attempts: number; fromIata?: string | null; toIata?: string | null };
export type Deps = {
  loadFlights: () => Promise<Row[]>;
  fetchArrivals: (icao: string, begin: number, end: number) => Promise<OpenSkyFlight[]>;
  save: (id: number, status: "verified" | "no_data" | null, note: string, attempts: number, track?: [number, number][] | null) => Promise<void>;
  // 確認できた便の、実際に飛んだ航路（OpenSky の path）。取れなくても照合の結果は変えない
  fetchTrack?: (icao24: string, time: number) => Promise<unknown>;
  // 航空会社の運航情報（ODPT。予定の便に残した実際の時刻）で確かめる。確かめられたら説明の文、だめなら null。
  // OpenSky で確かめられなかったとき（記録なし・当てはまる便なし・通信エラー）にだけ使う
  officialCheck?: (r: Row) => Promise<string | null>;
};
export const JOB = { maxPerRun: 200, maxAttempts: 3 };

export async function runVerification(d: Deps) {
  const rows = (await d.loadFlights()).slice(0, JOB.maxPerRun);
  const sum = { checked: 0, verified: 0, no_data: 0, unmatched: 0, errors: 0, official: 0 };
  const official = async (r: Row) => { if (!d.officialCheck) return false; try { const note = await d.officialCheck(r); if (!note) return false;
    await d.save(r.id, "verified", note, r.attempts + 1); sum.verified++; sum.official++; return true; } catch (e) { console.error("official", e); return false; } };
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
      if (await official(r)) continue;
      sum.errors++; console.error("OpenSky", e); continue;     // 回数は数えず、次の晩にもう一度
    }
    const v = match(f, arrivals);
    if (v.status === "verified") {
      let track: [number, number][] | null = null;
      if (d.fetchTrack) {
        try { track = compactTrack(await d.fetchTrack(v.matched.icao24, Math.floor((v.matched.firstSeen + v.matched.lastSeen) / 2))); }
        catch (e) { console.error("track", e); }
      }
      await d.save(r.id, "verified", `${(v.matched.callsign ?? "").trim()} ${v.byCallsign ? "便名一致" : "空港と時間帯で一致"}`, r.attempts + 1, track); sum.verified++;
    }
    else if (await official(r)) continue;
    else if (v.status === "no_data") { await d.save(r.id, "no_data", "到着記録なし", r.attempts + 1); sum.no_data++; }
    else { await d.save(r.id, null, "当てはまる便なし", r.attempts + 1); sum.unmatched++; }
  }
  return sum;
}
