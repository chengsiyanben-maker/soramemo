// ダイヤ（予定の便）と、今飛んでいる機体の位置を照らし合わせて、便ごとに「離陸した・着陸した・遅れている・ほかの空港へ向かった」を決める。
// 取得や保存とは分けて、テストしやすくしている（呼び出しは functions/flight-watch）。
//
// 見分け方（どれも推定。航空会社の発表ではない）
//  ・便名と機体の呼び出し符号（コールサイン）を、航空会社の記号と数字で結ぶ（JL509 ↔ JAL509、NH1 ↔ ANA1 など。先頭の0は無視）
//  ・離陸：出発空港の40km以内で、高度8,000ft以下の機体を初めて見た時刻。もっと遠くで初めて見たときは、見た時刻を「離陸（推定）」にする
//  ・着陸：空港の8km以内で、高度1,500ft以下で最後に見た時刻（見えなくなってから5分たったら着陸とみなす）
//  ・遅れ：離陸が定刻（出発の時刻＝ゲートを離れる時刻）から 1時間＋地上走行15分 以上あと、または着陸が到着の定刻より1時間以上あと
//          定刻から1時間15分たっても離陸を確認できないときも知らせる（運休・データの抜けのこともある）
//  ・ダイバート：到着空港ではない空港の15km以内で、高度4,000ft以下に降りてきたとき（出発空港なら「引き返し」）

export type Airport = { iata: string; lat: number; lon: number; name: string };
export type Sched = {
  id: number; flight: string;            // 便名（JL509）
  dep: string; arr: string;              // IATA
  std: number; sta: number;              // 定刻（ミリ秒、UTC）
};
export type Seen = { callsign: string; lat: number; lon: number; alt_ft: number | null; ground: boolean; fpm: number | null; at: number };
export type Watch = {
  phase: "sched" | "air" | "landed";
  takeoff_at: number | null; takeoff_est: boolean;
  landed_at: number | null; landed_iata: string | null;
  low_iata: string | null; low_at: number | null;   // 最後に「空港の近くで低い」と見た空港と時刻
  last: { lat: number; lon: number; alt_ft: number | null; at: number } | null;
  sent: string[];                                   // 送ったお知らせの種類（同じお知らせを二度出さない）
};
export type Alert = { kind: "delay_dep" | "no_takeoff" | "delay_arr" | "divert" | "return" | "divert_landed"; iata: string[]; message: string };

export const blankWatch = (): Watch => ({ phase: "sched", takeoff_at: null, takeoff_est: false, landed_at: null, landed_iata: null, low_iata: null, low_at: null, last: null, sent: [] });

// 便名の航空会社の記号 → 呼び出し符号の記号（グループの別会社が運航すると記号が変わることがあるので、候補を並べる）
const PREFIX: Record<string, string[]> = {
  JL: ["JAL", "JLJ", "JTA", "JAC", "HAC"], NH: ["ANA", "AKX", "AJX"], BC: ["SKY"], HD: ["ADO"], "6J": ["SNJ"], "7G": ["SFJ"],
  NU: ["JTA"], MM: ["APJ"], GK: ["JJP"], IJ: ["SJO"], JH: ["FDA"], OC: ["ORC"], FW: ["IBX"], "3X": ["JAC"],
  EK: ["UAE"], TG: ["THA"], QR: ["QTR"], AF: ["AFR"], BA: ["BAW"], LH: ["DLH"], UA: ["UAL"], AA: ["AAL"], DL: ["DAL"], CX: ["CPA"],
  SQ: ["SIA"], KE: ["KAL"], OZ: ["AAR"], CI: ["CAL"], BR: ["EVA"], CA: ["CCA"], MU: ["CES"], CZ: ["CSN"], HA: ["HAL"], QF: ["QFA"],
  AC: ["ACA"], TK: ["THY"], VN: ["HVN"], PR: ["PAL"], MH: ["MAS"], GA: ["GIA"], AY: ["FIN"], LX: ["SWR"], "7C": ["JJA"], LJ: ["JNA"],
};
export function callsignsFor(flight: string): string[] {
  const m = /^([A-Z0-9]{2})(\d{1,4})[A-Z]?$/.exec(flight.trim().toUpperCase());
  if (!m || !PREFIX[m[1]]) return [];
  const n = String(Number(m[2]));
  return PREFIX[m[1]].map((p) => p + n);
}
// 呼び出し符号の形をそろえる（JAL0509 → JAL509）
export function normCallsign(cs: string): string {
  const m = /^([A-Z]{3})0*(\d{1,4})([A-Z]?)$/.exec(cs.trim().toUpperCase());
  return m ? m[1] + m[2] + m[3] : cs.trim().toUpperCase();
}

function km(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
const MIN = 60_000;
const hm = (ms: number) => { const d = new Date(ms + 9 * 3600_000); return `${d.getUTCHours()}:${String(d.getUTCMinutes()).padStart(2, "0")}`; };

// 1便ぶんを1回進める。seen は今回見つかった機体（見つからなければ null）
export function step(s: Sched, w0: Watch, seen: Seen | null, now: number, aps: Map<string, Airport>): { watch: Watch; alerts: Alert[] } {
  const w: Watch = { ...w0, sent: [...w0.sent] }, out: Alert[] = [];
  const name = (i: string) => aps.get(i)?.name ?? i, route = `${s.flight}（${name(s.dep)}→${name(s.arr)}）`;
  const emit = (a: Alert) => { if (w.sent.includes(a.kind)) return; w.sent.push(a.kind); out.push(a); };
  const dep = aps.get(s.dep);

  if (seen && !seen.ground && w.phase !== "landed") {
    if (w.phase === "sched") {
      w.phase = "air";
      const near = dep && km(seen, dep) <= 40 && (seen.alt_ft ?? 99999) <= 8000;
      w.takeoff_at = seen.at; w.takeoff_est = !near;
    }
    w.last = { lat: seen.lat, lon: seen.lon, alt_ft: seen.alt_ft, at: seen.at };
    // 空港の近くで低いか
    let low: Airport | null = null;
    for (const a of aps.values()) if (km(seen, a) <= 8 && (seen.alt_ft ?? 99999) <= 1500) { low = a; break; }
    if (low) { w.low_iata = low.iata; w.low_at = seen.at; }
    // ほかの空港へ降りていく（離陸の直後は出発空港の近くにいるので、離陸から20分は「引き返し」を見ない）
    if ((seen.alt_ft ?? 99999) <= 4000 && (seen.fpm == null || seen.fpm < 300)) {
      for (const a of aps.values()) {
        if (a.iata === s.arr || km(seen, a) > 15) continue;
        if (a.iata === s.dep) { if (w.takeoff_at != null && seen.at - w.takeoff_at > 20 * MIN) emit({ kind: "return", iata: [s.dep, s.arr], message: `${route}は、${name(s.dep)}へ引き返しているようです（推定）` }); }
        else emit({ kind: "divert", iata: [s.arr, a.iata, s.dep], message: `${route}は、${name(a.iata)}へ向かっているようです（ダイバートの可能性・推定）` });
        break;
      }
    }
  }
  // 見えなくなった：空港の近くで低く見たのが最後なら、着陸とみなす
  if (w.phase === "air" && !seen && w.low_iata && w.low_at && w.last && w.last.at === w.low_at && now - w.low_at >= 5 * MIN) {
    w.phase = "landed"; w.landed_at = w.low_at; w.landed_iata = w.low_iata;
    if (w.landed_iata !== s.arr && w.landed_iata !== s.dep) emit({ kind: "divert_landed", iata: [s.arr, w.landed_iata, s.dep], message: `${route}は、${name(w.landed_iata)}に着陸したようです（ダイバート・推定）` });
  }
  // 遅れ
  if (w.takeoff_at != null && !w.takeoff_est && w.takeoff_at - s.std >= 75 * MIN) {
    const late = Math.round((w.takeoff_at - 15 * MIN - s.std) / MIN);
    emit({ kind: "delay_dep", iata: [s.dep, s.arr], message: `${route}は、出発が約${late}分遅れました（${hm(w.takeoff_at)}ごろ離陸・推定）` });
  }
  if (w.phase === "sched" && now - s.std >= 75 * MIN && now - s.std < 6 * 60 * MIN)
    emit({ kind: "no_takeoff", iata: [s.dep, s.arr], message: `${route}は、出発の定刻（${hm(s.std)}）から1時間以上たっても離陸を確認できていません` });
  if (w.phase === "landed" && w.landed_at != null && w.landed_iata === s.arr && w.landed_at - s.sta >= 60 * MIN)
    emit({ kind: "delay_arr", iata: [s.arr, s.dep], message: `${route}は、到着が約${Math.round((w.landed_at - s.sta) / MIN)}分遅れました（${hm(w.landed_at)}ごろ着陸・推定）` });
  else if (w.phase === "air" && now - s.sta >= 60 * MIN)
    emit({ kind: "delay_arr", iata: [s.arr, s.dep], message: `${route}は、到着の定刻（${hm(s.sta)}）から1時間以上たっても、まだ飛行中です（推定）` });
  return { watch: w, alerts: out };
}
