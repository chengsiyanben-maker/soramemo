// 撮影の知らせ：いつもの空港に着陸しに来る機体のうち、選んだ種類のものが「着陸の数分前」になったら知らせる。
// 取得・送信とは分けて、判定だけをここに置く（テストしやすいように）。
//   機体は airport-traffic の空港ごとの機体（着陸・離陸の見分け付き）。着陸までの時間は、空港までの距離と対地速度からの推定
import { callsignsFor, flightOfCallsign, foreignFlightOf, normCallsign } from "./flight_watch.ts";

export type SpotKind = "special" | "big" | "foreign" | "reg" | "ops" | "dep";
export type SpotSub = { id: number; spot_iata: string | null; spot_kinds: string[]; spot_lead: number; spot_regs: string[]; spot_flights: string[];
  spot_fams?: string[] | null; spot_livs?: string[] | null };
export type SpotPlane = { callsign: string | null; reg: string | null; type: string | null; phase: string; dist_km: number; kt: number | null; alt_ft: number | null };
export type Livery = { name: string; kind?: string };

// 大きな機体（ボーイング747・767・777・787、エアバスA330・A340・A350・A380）。ICAO の機種の記号
export const BIG = /^(B7[4678]|A3[3458])/i;

// 機種のまとまり（撮る人の「表示する機体」と同じ。アプリの SP_FAMS と同じ並び・同じ書き方にする）
//   機種の記号は ICAO（B77W・B789・A359・A21N・E190・DH8D など）。時刻表の書き方（789・77W・Q4A など）も読めるように
export const FAMS: [string, string, RegExp][] = [
  ["777", "777", /^B?77[0-9A-Z]/i], ["787", "787", /^B?78[0-9A-Z]/i], ["767", "767", /^B?76[0-9A-Z]/i], ["747", "747", /^B?74[0-9A-Z]/i],
  ["737", "737", /^(B?73[0-9A-Z]|B3[789]M)/i], ["A350", "A350", /^A?35[0-9K]/i], ["A330", "A330", /^A?33[0-9N]/i], ["A380", "A380", /^A?38[0-9]/i],
  ["A320", "A320・A321", /^(A?3(19|20|21)|A[12][019]N|32[01N])/i], ["small", "小さな機体", /^(E1[79]0|E17|E19|E7|E75|E90|DH8|Q4|AT[4-7]|SF3|SB3|CRJ|DHC)/i],
];
export const famOf = (type: string | null | undefined): string | null => {
  const t = String(type ?? "").trim().toUpperCase(); if (!t) return null;
  const f = FAMS.find(([, , re]) => re.test(t)); return f ? f[0] : "other";
};
export const FAM_KEYS = [...FAMS.map(([k]) => k), "other"];
export const BIG_FAMS = ["777", "787", "767", "747", "A350", "A330", "A380"];

// 着陸までの分（推定）：まっすぐの距離より少し長く飛ぶ（1.15倍）として、いまの対地速度で割る。速度が分からなければ180ノット
export function etaMin(p: Pick<SpotPlane, "dist_km" | "kt">): number {
  const kmPerMin = Math.max(p.kt ?? 180, 130) * 1.852 / 60;
  return (p.dist_km * 1.15) / kmPerMin + 0.5;
}

// 日本時間の日付（"2026-10-21"）
export const jstDate = (t = Date.now()) => new Date(t + 9 * 3600_000).toISOString().slice(0, 10);

// 知らせる理由（いちばん強いもの1つ）。知らせないなら null
//   flight：「この便を知らせる」で選んだ便 / reg：指定した登録記号 / special：特別塗装機 / big：大きな機体 / foreign：海外の航空会社
export function spotReason(p: SpotPlane, sub: SpotSub, livery: Livery | undefined, now = Date.now()): { why: "flight" | "reg" | "special" | "big" | "fam" | "foreign"; label: string } | null {
  if (p.phase !== "arr" || !p.callsign) return null;
  const cs = normCallsign(p.callsign), today = jstDate(now), k = new Set(sub.spot_kinds);
  for (const f of sub.spot_flights) {
    const [no, day] = f.split("@");
    if (day === today && callsignsFor(no).includes(cs)) return { why: "flight", label: "知らせを選んだ便" };
  }
  if (p.reg && k.has("reg") && sub.spot_regs.includes(p.reg)) return { why: "reg", label: `指定した機体 ${p.reg}` };
  if (livery && livery.kind !== "alliance" && (k.has("special") || (sub.spot_livs ?? []).includes(livery.name))) return { why: "special", label: `特別塗装機「${livery.name}」` };
  if (p.type && BIG.test(p.type) && k.has("big")) return { why: "big", label: "大きな機体" };
  // 表示する機体と同じ選び方（機種のまとまり）で知らせる人
  const fam = famOf(p.type);
  if (fam && (sub.spot_fams ?? []).includes(fam)) { const f = FAMS.find(([key]) => key === fam); return { why: "fam", label: f ? f[1] : "選んだ機種" }; }
  if (foreignFlightOf(cs) && k.has("foreign")) return { why: "foreign", label: "海外の航空会社" };
  return null;
}

// 知らせる時か：着陸まで「知らせる時間」以下になったら（あまりに近い・もう降りた機体は除く）
export const dueNow = (eta: number, lead: number) => eta <= lead + 0.25 && eta >= 0.75;

// 通知の文
export function spotMessage(p: SpotPlane, reason: { label: string }, apName: string, eta: number): { title: string; body: string } {
  const cs = p.callsign ? normCallsign(p.callsign) : "";
  const fl = flightOfCallsign(cs) ?? cs, min = Math.max(1, Math.round(eta));
  const type = p.type ? `（${p.type}${p.reg ? "・" + p.reg : ""}）` : p.reg ? `（${p.reg}）` : "";
  return { title: `そらメモ：${fl} があと約${min}分で着陸`, body: `${reason.label}の ${fl}${type}が、${apName}にあと約${min}分で着陸しそうです（機体の位置からの推定）。` };
}

// 運用（滑走路の向き）が変わったか：記録（新しい順）のうち、新しい2回がそろって Y、その前の2回がそろって X（≠Y）なら変わった
export function opsChanged(rows: { obs_mode: string | null; obs_mixed?: boolean | null }[]): { from: string; to: string } | null {
  const m = rows.slice(0, 4).map((r) => r.obs_mixed ? null : r.obs_mode);
  if (m.length < 4 || m.some((x) => !x)) return null;
  return m[0] === m[1] && m[2] === m[3] && m[0] !== m[2] ? { from: m[2]!, to: m[0]! } : null;
}

// ---- 離陸の知らせ（「離陸も知らせる」dep を選んだ人と、離陸する便を選んだ人）----
//   便はサーバーの spot_departures（時刻表の便。離陸の時刻＝出発の時刻＋空港の地上走行の分。まだ離陸していないもの）
export type SpotDep = { flight: string; dep: string; arr: string; svc_date: string; aircraft: string | null; reg: string | null; livery: string | null; gate_actual: boolean; takeoff: string };
export function spotDepReason(f: SpotDep, sub: SpotSub): { why: "flight" | "reg" | "special" | "big" | "fam"; label: string } | null {
  if (f.dep !== sub.spot_iata) return null;
  if (sub.spot_flights.includes(`${f.flight}@${f.svc_date}`)) return { why: "flight", label: "知らせを選んだ便" };
  const k = new Set(sub.spot_kinds); if (!k.has("dep")) return null;
  if (f.reg && k.has("reg") && sub.spot_regs.includes(f.reg)) return { why: "reg", label: `指定した機体 ${f.reg}` };
  if (f.livery && (k.has("special") || (sub.spot_livs ?? []).includes(f.livery))) return { why: "special", label: `特別塗装機「${f.livery}」` };
  const fam = famOf(f.aircraft);
  // 時刻表の機種は「789」「77W」のようにも書くので、大きな機体はまとまりで見る
  if (fam && BIG_FAMS.includes(fam) && k.has("big")) return { why: "big", label: "大きな機体" };
  if (fam && (sub.spot_fams ?? []).includes(fam)) { const x = FAMS.find(([key]) => key === fam); return { why: "fam", label: x ? x[1] : "選んだ機種" }; }
  return null;
}
// 離陸までの分（推定）
export const depEtaMin = (f: Pick<SpotDep, "takeoff">, now = Date.now()) => (Date.parse(f.takeoff) - now) / 60_000;
export function spotDepMessage(f: SpotDep, reason: { label: string }, apName: string, eta: number): { title: string; body: string } {
  const min = Math.max(1, Math.round(eta)), type = f.aircraft ? `（${f.aircraft}${f.reg ? "・" + f.reg : ""}）` : f.reg ? `（${f.reg}）` : "";
  return { title: `そらメモ：${f.flight} があと約${min}分で離陸`,
    body: `${reason.label}の ${f.flight}${type}が、${apName}からあと約${min}分で離陸しそうです（${f.gate_actual ? "出発した時刻" : "出発の見込み"}と地上走行の時間からの推定）。` };
}
