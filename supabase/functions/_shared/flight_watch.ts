// ダイヤ（予定の便）と、今飛んでいる機体の位置を照らし合わせて、便ごとに「離陸した・着陸した・遅れている・ほかの空港へ向かった」を決める。
// 取得や保存とは分けて、テストしやすくしている（呼び出しは functions/flight-watch）。
//
// 見分け方（どれも推定。航空会社の発表ではない）
//  ・便名と機体の呼び出し符号（コールサイン）を、航空会社の記号と数字で結ぶ（JL509 ↔ JAL509、NH1 ↔ ANA1 など。先頭の0は無視）
//  ・離陸：出発空港の40km以内で、高度8,000ft以下の機体を初めて見た時刻。もっと遠くで初めて見たときは、見た時刻を「離陸（推定）」にする
//  ・着陸：空港の8km以内で、高度1,500ft以下で最後に見た時刻（見えなくなってから5分たったら着陸とみなす）
//          受信機に低いところが映らない空港もあるので、到着空港の40km以内・10,000ft以下で見えなくなって10分たったときも着陸とみなす（その時刻は最後に見た時刻）
//  ・遅れ：離陸が定刻（出発の時刻＝ゲートを離れる時刻）から 1時間＋地上走行15分 以上あと、または着陸が到着の定刻より1時間以上あと
//          定刻から1時間15分たっても離陸を確認できないときも知らせる（運休・データの抜けのこともある）
//  ・ダイバート：到着空港ではない空港の8km以内で、高度2,000ft以下に降りてきたとき（その空港への最終進入。出発空港なら「引き返し」）。
//          到着空港のほうが近いときや、到着空港の20km以内のときは数えない（北九州と山口宇部、出雲と美保のように近い空港への進入で誤らないよう）
//  ・同じ番号の別の会社の便（JL552 と JTA552 など）を取り違えないよう、出発空港と到着空港を結ぶ帯の外にいる機体は、その便とみなさない

export type Airport = { iata: string; lat: number; lon: number; name: string };
export type Sched = {
  id: number; flight: string;            // 便名（JL509）
  dep: string; arr: string;              // IATA
  std: number; sta: number;              // 定刻（ミリ秒、UTC）
  aircraft?: string | null;              // 機種（ODPT の IATA の機種の記号：738・E70・Q4A など）
};
// プロペラ機（ATR・ボンバルディア Q400 など）とエンブラエル機：低く飛ぶ・小さな空港を使うため受信機に映らないことが多く、
// 「離陸を確認できず」が誤りになりやすいので出さない
export const hardToSee = (t?: string | null) => !!t && /^(AT|AR|Q\d|Q4|D[H8]|DHC|SF|SAB|YS|BN|DO|E\d|EM|ER)/i.test(t.trim());
export type Seen = { callsign: string; lat: number; lon: number; alt_ft: number | null; ground: boolean; fpm: number | null; kt?: number | null; type?: string | null; reg?: string | null; at: number };
export type Watch = {
  phase: "sched" | "air" | "landed";
  takeoff_at: number | null; takeoff_est: boolean;
  landed_at: number | null; landed_iata: string | null;
  low_iata: string | null; low_at: number | null;   // 最後に「空港の近くで低い」と見た空港と時刻
  last: { lat: number; lon: number; alt_ft: number | null; at: number } | null;
  sent: string[];                                   // 送ったお知らせの種類（同じお知らせを二度出さない）
  start?: number;                                   // 見張りを始めた時刻（ダイヤを入れたのが定刻より後なら、離陸を見逃しているので「離陸を確認できず」は出さない）
  eta?: number | null;                              // 到着予想（推定。機体の位置・速度と機種の巡航速度から。ミリ秒）
  cs?: string | null; reg?: string | null; type?: string | null;   // 見つけた機体の呼び出し符号・登録記号・機種（毎日の記録と航跡に使う）
  eta60?: number | null; eta30?: number | null; eta15?: number | null;   // 到着の60・30・15分前ごろの到着予想（当たり具合を毎日の記録で確かめる）
};
export type Alert = { kind: "delay_dep" | "no_takeoff" | "delay_arr" | "divert" | "return" | "divert_landed"; iata: string[]; message: string };

// 機種ごとの巡航速度（真対気速度の目安・ノット）と、到着空港の手前の進入の平均速度。ICAO の機種記号（B738 など）と ODPT の機種記号（738 など）の両方を受ける
const CRUISE: [RegExp, number, number][] = [
  [/^(B77|77|B78|78|A35|35|B74|74|A38|38)/i, 485, 230],   // 大型機（777・787・A350）
  [/^(B76|76|A30|30|A33|33)/i, 470, 225],                // 767・A300・A330
  [/^(B73|73|B38|7M|7S|A3[12]|3[12]|A2|32N|31N|21N|A20N|A21N)/i, 450, 220],   // 737・A320 系
  [/^(E1|E7|E9|E2|ER|EM|CRJ|CR[79]|E70|E75|E90|E95)/i, 430, 210],   // エンブラエル・CRJ
  [/^(DH8D|Q4|DH4|Q400)/i, 330, 180],                     // Q400
  [/^(AT[47]|AT[0-9]|ATR|AR[0-9])/i, 275, 165],           // ATR
  [/^(SF3|SB2|DH8|DHC|DH[0-9]|Q[0-9]|D[0-9])/i, 260, 160],  // そのほかのプロペラ機
];
export function cruiseOf(type?: string | null): { cruise: number; approach: number } {
  const t = (type ?? "").trim();
  for (const [re, c, a] of CRUISE) if (t && re.test(t)) return { cruise: c, approach: a };
  return { cruise: 440, approach: 210 };
}
// 到着予想（推定）：到着空港まで残りの距離を、巡航中は今の対地速度（上空の風を含む）か機種の巡航速度で、
// 最後の40海里（約74km）は進入の平均速度で飛ぶとみなし、進入・着陸に4分を足す。上昇中は機種の巡航速度を使う
export function predictEta(p: { lat: number; lon: number; alt_ft: number | null; kt?: number | null; at: number }, arr: Airport, type?: string | null): number {
  const { cruise, approach } = cruiseOf(type), nm = km(p, arr) / 1.852, alt = p.alt_ft ?? 0;
  const inCruise = alt >= 18000 && p.kt != null && p.kt > cruise * 0.6 && p.kt < cruise * 1.5;
  const v = inCruise ? p.kt! : cruise * 0.95;
  const far = Math.max(0, nm - 40), near = Math.min(nm, 40);
  const nearV = alt < 10000 && p.kt != null && p.kt > 100 ? Math.min(approach, p.kt) : approach;
  return p.at + (far / v + near / nearV) * 3600_000 + 4 * MIN;
}
// 降りる途中で見えなくなった機体の着陸の時刻（推定）：最後に見た位置から、残りを進入の速度で飛んだとみなす（predictEta と同じ考え方）。
// 最後に見た時刻より前にはしない
export function landingFrom(last: { lat: number; lon: number; alt_ft: number | null; at: number }, arr: Airport, type?: string | null): number {
  return Math.max(last.at, Math.round(predictEta({ ...last, kt: null }, arr, type)));
}
export const blankWatch = (): Watch => ({ phase: "sched", takeoff_at: null, takeoff_est: false, landed_at: null, landed_iata: null, low_iata: null, low_at: null, last: null, sent: [] });

// 便名の航空会社の記号 → 呼び出し符号の記号（グループの別会社が運航すると記号が変わることがあるので、候補を並べる）
const PREFIX: Record<string, string[]> = {
  JL: ["JAL", "JLJ", "JTA", "JAC", "HAC"], NH: ["ANA", "AKX", "AJX"], BC: ["SKY"], HD: ["ADO"], "6J": ["SNJ"], "7G": ["SFJ"],
  NU: ["JTA"], MM: ["APJ"], GK: ["JJP"], IJ: ["SJO"], JH: ["FDA"], OC: ["ORC"], FW: ["IBX"], "3X": ["JAC"],
  EK: ["UAE"], TG: ["THA"], QR: ["QTR"], AF: ["AFR"], BA: ["BAW"], LH: ["DLH"], UA: ["UAL"], AA: ["AAL"], DL: ["DAL"], CX: ["CPA"],
  SQ: ["SIA"], KE: ["KAL"], OZ: ["AAR"], CI: ["CAL"], BR: ["EVA"], CA: ["CCA"], MU: ["CES"], CZ: ["CSN"], HA: ["HAL"], QF: ["QFA"],
  AC: ["ACA"], TK: ["THY"], VN: ["HVN"], PR: ["PAL"], MH: ["MAS"], GA: ["GIA"], AY: ["FIN"], LX: ["SWR"], "7C": ["JJA"], LJ: ["JNA"],
  // 日本に乗り入れているほかの航空会社（国際線を便名で探すとき用。2026-10-20）
  ZG: ["TZP"], "3K": ["JSA"], TW: ["TWB"], ZE: ["ESR"], BX: ["ABL"], RS: ["ASV"], HO: ["DKH"], "9C": ["CQH"], HX: ["CRK"], UO: ["HKE"],
  IT: ["TTW"], JX: ["SJX"], "5J": ["CEB"], VJ: ["VJC"], TR: ["TGW"], D7: ["XAX"], JQ: ["JST"], NZ: ["ANZ"], KL: ["KLM"], OS: ["AUA"],
  SK: ["SAS"], EY: ["ETD"], AI: ["AIC"], ET: ["ETH"], "8L": ["LKE"], MF: ["CXA"], HU: ["CHH"], SC: ["CDG"], FM: ["CSH"], GS: ["GCR"],
  OM: ["MGL"], UL: ["ALK"], WY: ["OMA"], SV: ["SVA"], "6E": ["IGO"], PG: ["BKP"], QH: ["BAV"],
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

// その便の機体として見てよい位置か：出発空港→機体→到着空港の道のりが、まっすぐの距離の1.3倍＋150km以内
export function onRoute(s: Sched, p: { lat: number; lon: number }, aps: Map<string, Airport>): boolean {
  const a = aps.get(s.dep), b = aps.get(s.arr);
  if (!a || !b) return true;
  return km(a, p) + km(p, b) <= km(a, b) * 1.3 + 150;
}
export const NO_TAKEOFF_ALERT = false;
// 1便ぶんを1回進める。seen は今回見つかった機体（見つからなければ null）
export function step(s: Sched, w0: Watch, seen: Seen | null, now: number, aps: Map<string, Airport>): { watch: Watch; alerts: Alert[] } {
  const w: Watch = { ...w0, sent: [...w0.sent] }, out: Alert[] = [];
  if (w.start == null) w.start = now;
  const lateStart = w.start > s.std + 15 * MIN;   // 定刻を15分以上すぎてから見張り始めた便
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
    w.cs = seen.callsign; if (seen.reg) w.reg = seen.reg; if (seen.type) w.type = seen.type;
    const arrA = aps.get(s.arr);
    if (arrA) {
      w.eta = Math.round(predictEta(seen, arrA, seen.type || s.aircraft));
      const rem = w.eta - now;
      for (const m of [60, 30, 15] as const) { const k = `eta${m}` as "eta60" | "eta30" | "eta15"; if (w[k] == null && rem <= m * MIN && rem > (m - 10) * MIN) w[k] = w.eta; }
    }
    // 空港の近くで低いか
    let low: Airport | null = null;
    for (const a of aps.values()) if (km(seen, a) <= 8 && (seen.alt_ft ?? 99999) <= 1500) { low = a; break; }
    if (low) { w.low_iata = low.iata; w.low_at = seen.at; }
    // ほかの空港へ降りていく（離陸の直後は出発空港の近くにいるので、離陸から20分は「引き返し」を見ない）
    const arrAp = aps.get(s.arr), dArr = arrAp ? km(seen, arrAp) : Infinity;
    if ((seen.alt_ft ?? 99999) <= 4000 && (seen.fpm == null || seen.fpm < 300)) {
      for (const a of aps.values()) {
        const dA = km(seen, a);
        if (a.iata === s.arr || dArr < 20 || dArr <= dA) continue;
        // 出発空港（引き返し）は15km・4,000ft以下、ほかの空港（ダイバート）は最終進入の8km・2,000ft以下
        if (a.iata === s.dep ? dA > 15 : (dA > 8 || (seen.alt_ft ?? 99999) > 2000)) continue;
        if (a.iata === s.dep) { if (w.takeoff_at != null && seen.at - w.takeoff_at > 20 * MIN) emit({ kind: "return", iata: [s.dep, s.arr], message: `${route}は、${name(s.dep)}へ引き返しているようです（推定）` }); }
        else emit({ kind: "divert", iata: [s.arr, a.iata, s.dep], message: `${route}は、${name(a.iata)}へ向かっているようです（ダイバートの可能性・推定）` });
        break;
      }
    }
  }
  // 地上にいるのが見えた（着陸して地上を走っている）：空港の近くなら着陸とみなす。着陸の時刻は最後に飛んでいるのを見た時刻
  //（地上の機体も位置を送り続けるので、「見えなくなったら着陸」だけでは、いつまでも飛行中のままになっていた）
  if (w.phase === "air" && seen && seen.ground) {
    let near: Airport | null = null;
    for (const a of aps.values()) if (km(seen, a) <= 8) { near = a; break; }
    if (near) {
      w.phase = "landed"; w.landed_iata = near.iata; w.landed_at = w.low_iata === near.iata && w.low_at ? w.low_at : (w.last?.at ?? seen.at);
      if (w.landed_iata !== s.arr && w.landed_iata !== s.dep) emit({ kind: "divert_landed", iata: [s.arr, w.landed_iata, s.dep], message: `${route}は、${name(w.landed_iata)}に着陸したようです（ダイバート・推定）` });
    }
  }
  // 見えなくなった：空港の近くで低く見たのが最後なら、着陸とみなす
  if (w.phase === "air" && !seen && w.low_iata && w.low_at && w.last && w.last.at === w.low_at && now - w.low_at >= 5 * MIN) {
    w.phase = "landed"; w.landed_at = w.low_at; w.landed_iata = w.low_iata;
    if (w.landed_iata !== s.arr && w.landed_iata !== s.dep) emit({ kind: "divert_landed", iata: [s.arr, w.landed_iata, s.dep], message: `${route}は、${name(w.landed_iata)}に着陸したようです（ダイバート・推定）` });
  }
  if (w.phase === "air" && !seen && w.last && now - w.last.at >= 10 * MIN) {
    const arr = aps.get(s.arr);
    if (arr && km(w.last, arr) <= 40 && (w.last.alt_ft ?? 99999) <= 10000) { w.phase = "landed"; w.landed_at = landingFrom(w.last, arr, w.type || s.aircraft); w.landed_iata = s.arr; }
  }
  // 降りる途中で電波が届かなくなった（空港の近くは受信機が少ない）：到着予想から15分たっても見えなければ、到着空港に着いたとみなす。
  // 最後に見たのが到着空港から120km以内・15,000ft以下（もう降り始めている）なら、そこから着陸の時刻を推定する。
  // それより遠い・高いときは、着陸の時刻は分からないので入れない（古い到着予想を出し続けないため）
  if (w.phase === "air" && !seen && w.last && w.eta != null && now - w.last.at >= 10 * MIN && now - w.eta >= 15 * MIN) {
    const arr = aps.get(s.arr);
    if (arr && km(w.last, arr) <= 200) {
      w.phase = "landed"; w.landed_iata = s.arr;
      w.landed_at = km(w.last, arr) <= 120 && (w.last.alt_ft ?? 99999) <= 15000 ? landingFrom(w.last, arr, w.type || s.aircraft) : null;
    }
  }
  // 遅れ
  if (w.takeoff_at != null && !w.takeoff_est && !lateStart && w.takeoff_at - s.std >= 75 * MIN) {
    const late = Math.round((w.takeoff_at - 15 * MIN - s.std) / MIN);
    emit({ kind: "delay_dep", iata: [s.dep, s.arr], message: `${route}は、出発が約${late}分遅れました（${hm(w.takeoff_at)}ごろ離陸・推定）` });
  }
  // 「離陸を確認できず」は、いまは出さない（NO_TAKEOFF_ALERT）。共同運航便（JL4344＝フジドリームエアラインズの運航など）は
  // 便名と機体の呼び出し符号が一致せず、ジェット機でも離陸を見分けられないため、誤ったお知らせばかりになった（2026-10-15）
  if (NO_TAKEOFF_ALERT && w.phase === "sched" && !lateStart && !hardToSee(s.aircraft) && now - s.std >= 75 * MIN && now - s.std < 6 * 60 * MIN)
    emit({ kind: "no_takeoff", iata: [s.dep, s.arr], message: `${route}は、出発の定刻（${hm(s.std)}）から1時間以上たっても離陸を確認できていません` });
  if (w.phase === "landed" && w.landed_at != null && w.landed_iata === s.arr && w.landed_at - s.sta >= 60 * MIN)
    emit({ kind: "delay_arr", iata: [s.arr, s.dep], message: `${route}は、到着が約${Math.round((w.landed_at - s.sta) / MIN)}分遅れました（${hm(w.landed_at)}ごろ着陸・推定）` });
  // 「まだ飛行中」は、今も実際に飛んでいるのが見えているときだけ（途中で見えなくなった便は、着陸したのか分からないので出さない）
  else if (w.phase === "air" && now - s.sta >= 60 * MIN && w.last && now - w.last.at <= 5 * MIN)
    emit({ kind: "delay_arr", iata: [s.arr, s.dep], message: `${route}は、到着の定刻（${hm(s.sta)}）から1時間以上たっても、まだ飛行中です（推定）` });
  return { watch: w, alerts: out };
}
