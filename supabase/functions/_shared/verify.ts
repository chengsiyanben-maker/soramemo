// 便の照合（運航確認）のルール。ネットワークに触れない純粋な関数だけを置く。
// OpenSky Network の /flights/arrival が返す1件（主な項目のみ）
export type OpenSkyFlight = {
  icao24: string;
  callsign: string | null;          // 例 "JAL501  "（後ろに空白が入ることがある）
  estDepartureAirport: string | null; // 例 "RJTT"（推定なので null や別の空港のこともある）
  estArrivalAirport: string | null;
  firstSeen: number;                // UNIX秒
  lastSeen: number;                 // UNIX秒（着陸のころ）
};

export type RecordedFlight = {
  fromIcao: string; toIcao: string;
  dep: number; arr: number;         // チェックインの時刻（ミリ秒）
  flightNo: string | null;          // 例 "JL501"
};

// 航空会社の2文字コード → ICAOのコールサイン記号
export const CALLSIGN_PREFIX: Record<string, string> = {
  JL: "JAL", NU: "JTA", NH: "ANA", BC: "SKY", MM: "APJ", GK: "JJP", IJ: "SJO", "6J": "SNJ", HD: "ADO", "7G": "SFJ", JH: "FDA",
};

export function callsignFor(flightNo: string | null): string | null {
  if (!flightNo) return null;
  const m = flightNo.toUpperCase().match(/^([A-Z0-9]{2})(\d{1,4})$/);
  if (!m || !CALLSIGN_PREFIX[m[1]]) return null;
  return CALLSIGN_PREFIX[m[1]] + String(Number(m[2]));   // 先頭の0は付けない（JL0501 → JAL501）
}

export const VERIFY = {
  beforeDepMin: 30,   // 出発チェックインより少し前に飛び立った記録も認める（チェックインが遅れた場合）
  afterArrMin: 20,    // 機体の最後の電波は駐機まで続くので、到着チェックインより少し後の記録も認める
};

// 照合の窓（OpenSky に問い合わせる範囲、UNIX秒）
export function windowFor(f: RecordedFlight) {
  return { begin: Math.floor((f.dep - VERIFY.beforeDepMin * 60e3) / 1000), end: Math.ceil((f.arr + VERIFY.afterArrMin * 60e3) / 1000) };
}

export type Verdict =
  | { status: "verified"; matched: OpenSkyFlight; byCallsign: boolean }
  | { status: "no_data" }       // その空港・時間帯の到着記録が1件もない（受信範囲の外など）
  | { status: "unmatched" };    // 記録はあるが、当てはまる便がない

export function match(f: RecordedFlight, arrivals: OpenSkyFlight[]): Verdict {
  if (!arrivals.length) return { status: "no_data" };
  const { begin, end } = windowFor(f);
  const want = callsignFor(f.flightNo);
  const cands = arrivals.filter((a) =>
    a.estDepartureAirport === f.fromIcao &&
    (a.estArrivalAirport === null || a.estArrivalAirport === f.toIcao) &&
    a.lastSeen >= begin && a.lastSeen <= end &&
    a.firstSeen >= begin - 3600     // 飛び立ちが出発チェックインより大きく前の機体は除く
  );
  if (want) {
    const hit = cands.find((a) => (a.callsign ?? "").trim().toUpperCase() === want);
    return hit ? { status: "verified", matched: hit, byCallsign: true } : { status: "unmatched" };
  }
  // 便名がないときは、出発空港・到着空港・時間帯の一致だけで確認する
  return cands.length ? { status: "verified", matched: cands[0], byCallsign: false } : { status: "unmatched" };
}
