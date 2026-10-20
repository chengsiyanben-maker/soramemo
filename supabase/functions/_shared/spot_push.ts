// 撮影の知らせ：いつもの空港に着陸しに来る機体のうち、選んだ種類のものが「着陸の数分前」になったら知らせる。
// 取得・送信とは分けて、判定だけをここに置く（テストしやすいように）。
//   機体は airport-traffic の空港ごとの機体（着陸・離陸の見分け付き）。着陸までの時間は、空港までの距離と対地速度からの推定
import { callsignsFor, flightOfCallsign, foreignFlightOf, normCallsign } from "./flight_watch.ts";

export type SpotKind = "special" | "big" | "foreign" | "reg" | "ops";
export type SpotSub = { id: number; spot_iata: string | null; spot_kinds: string[]; spot_lead: number; spot_regs: string[]; spot_flights: string[] };
export type SpotPlane = { callsign: string | null; reg: string | null; type: string | null; phase: string; dist_km: number; kt: number | null; alt_ft: number | null };
export type Livery = { name: string; kind?: string };

// 大きな機体（ボーイング747・767・777・787、エアバスA330・A340・A350・A380）。ICAO の機種の記号
export const BIG = /^(B7[4678]|A3[3458])/i;

// 着陸までの分（推定）：まっすぐの距離より少し長く飛ぶ（1.15倍）として、いまの対地速度で割る。速度が分からなければ180ノット
export function etaMin(p: Pick<SpotPlane, "dist_km" | "kt">): number {
  const kmPerMin = Math.max(p.kt ?? 180, 130) * 1.852 / 60;
  return (p.dist_km * 1.15) / kmPerMin + 0.5;
}

// 日本時間の日付（"2026-10-21"）
export const jstDate = (t = Date.now()) => new Date(t + 9 * 3600_000).toISOString().slice(0, 10);

// 知らせる理由（いちばん強いもの1つ）。知らせないなら null
//   flight：「この便を知らせる」で選んだ便 / reg：指定した登録記号 / special：特別塗装機 / big：大きな機体 / foreign：海外の航空会社
export function spotReason(p: SpotPlane, sub: SpotSub, livery: Livery | undefined, now = Date.now()): { why: "flight" | "reg" | "special" | "big" | "foreign"; label: string } | null {
  if (p.phase !== "arr" || !p.callsign) return null;
  const cs = normCallsign(p.callsign), today = jstDate(now), k = new Set(sub.spot_kinds);
  for (const f of sub.spot_flights) {
    const [no, day] = f.split("@");
    if (day === today && callsignsFor(no).includes(cs)) return { why: "flight", label: "知らせを選んだ便" };
  }
  if (p.reg && k.has("reg") && sub.spot_regs.includes(p.reg)) return { why: "reg", label: `指定した機体 ${p.reg}` };
  if (livery && livery.kind !== "alliance" && k.has("special")) return { why: "special", label: `特別塗装機「${livery.name}」` };
  if (p.type && BIG.test(p.type) && k.has("big")) return { why: "big", label: "大きな機体" };
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
