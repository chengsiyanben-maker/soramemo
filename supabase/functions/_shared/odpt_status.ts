// 航空会社の運航情報（ODPT の FlightInformationDeparture / FlightInformationArrival。JAL・ANA グループ）から、
//   ・欠航・出発の大きな遅れ・到着の大きな遅れ・ダイバート・引き返しのお知らせ
//   ・便ごとの実際の時刻（出発・到着）・変更後の時刻・状態・搭乗口（予定の便 flight_schedule に残し、フライトの記録の照合などに使う）
// を作る。機体の位置からの推定（flight_watch.ts）と違い、航空会社が出している情報なので「推定」ではない。取得とは分けて、テストしやすくしている。
// 便は、予定の便の、同じ便名（先頭の0は無視）・同じ出発空港・同じ定刻の便に結ぶ（日付は予定の便から決まる）。結べない便は使わない。
import { flightNo, gateOf, infoText } from "./airport_now.ts";

export type StatusSched = { id: number; flight: string; dep: string; arr: string; std: number; sta?: number };   // ミリ秒（UTC）
export type StatusAlert = { schedule_id: number; kind: "cancel" | "delay_dep" | "delay_arr" | "divert" | "return"; flight: string; dep: string; arr: string; iata: string[]; message: string };
export type StatusUpdate = {
  id: number;
  dep_status?: string | null; etd?: string | null; atd?: string | null; dep_gate?: string | null;
  arr_status?: string | null; eta?: string | null; ata?: string | null; arr_gate?: string | null;
};

const MIN = 60_000;
const last = (v: unknown) => { const s = String(Array.isArray(v) ? v[0] ?? "" : v ?? ""); const i = s.lastIndexOf(":"); return i >= 0 ? s.slice(i + 1) : s; };
const hhmm = (v: unknown): string | null => { const m = String(v ?? "").match(/^(\d{1,2}):(\d{2})/); return m ? `${m[1].padStart(2, "0")}:${m[2]}` : null; };
const hmText = (hm: string) => `${Number(hm.slice(0, 2))}:${hm.slice(3)}`;
const norm = (f: string) => flightNo(f)?.no ?? f;
const ap = (v: unknown) => last(v).slice(0, 3).toUpperCase();
const st = (v: unknown) => { const s = last(v); return s ? s.slice(0, 40) : null; };

// 定刻 base の日の "HH:MM"（日本時間）を、base にいちばん近い時刻（ミリ秒）にする（日付をまたぐ遅れにも対応）
// 同じ便名・同じ出発空港の予定の便のうち、定刻が "HH:MM" にいちばん近い便（差が20分以内）。
// 時刻表（予定の便）と運航情報で定刻が数分ずれることがある（例：JL333 の到着が時刻表では 21:05、運航情報では 21:10）
export function nearestSched(cands: StatusSched[], hm: string, key: "std" | "sta"): StatusSched | undefined {
  let best: StatusSched | undefined, bd = 20 * MIN + 1;
  for (const x of cands) { const t = x[key]; if (t == null) continue; const d = Math.abs(atNear(t, hm) - t); if (d < bd) { bd = d; best = x; } }
  return best;
}
export function atNear(base: number, hm: string): number {
  const d = new Date(base + 9 * 3600_000);
  const t = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), Number(hm.slice(0, 2)), Number(hm.slice(3, 5))) - 9 * 3600_000;
  return [t - 864e5, t, t + 864e5].sort((a, b) => Math.abs(a - base) - Math.abs(b - base))[0];
}

// deno-lint-ignore no-explicit-any
export function odptStatus(depItems: any[], arrItems: any[], scheds: StatusSched[], names: (iata: string) => string) {
  const byKey = new Map<string, StatusSched[]>();
  for (const s of scheds) { const k = `${norm(s.flight)}|${s.dep}`; byKey.set(k, [...(byKey.get(k) ?? []), s]); }
  const alerts = new Map<string, StatusAlert>(), updates = new Map<number, StatusUpdate>();
  const route = (s: StatusSched) => `${s.flight}（${names(s.dep)}→${names(s.arr)}）`;
  let note: string | null = null;   // いま見ている便の、航空会社のお知らせの文（理由）
  const add = (s: StatusSched, kind: StatusAlert["kind"], message: string, iata = [s.dep, s.arr]) =>
    alerts.set(`${s.id}|${kind}`, { schedule_id: s.id, kind, flight: s.flight, dep: s.dep, arr: s.arr, iata,
      message: (note ? message.replace(/（航空会社の運航情報）$|・航空会社の運航情報）$/, (m) => m.slice(0, -1) + `。${note}）`) : message).slice(0, 300) });
  const upd = (s: StatusSched, u: Omit<StatusUpdate, "id">) => updates.set(s.id, { ...(updates.get(s.id) ?? { id: s.id }), ...u });
  const iso = (base: number, hm: string | null) => hm ? new Date(atNear(base, hm)).toISOString() : null;

  // 出発
  for (const it of Array.isArray(depItems) ? depItems : []) {
    const fn = flightNo(it?.["odpt:flightNumber"]), dep = ap(it?.["odpt:departureAirport"]), std = hhmm(it?.["odpt:scheduledDepartureTime"]);
    if (!fn || !std || !/^[A-Z]{3}$/.test(dep)) continue;
    const s = nearestSched(byKey.get(`${fn.no}|${dep}`) ?? [], std, "std");
    if (!s) continue;
    note = infoText(it["odpt:flightInformationText"], it["odpt:flightInformationSummary"]);
    const status = st(it["odpt:flightStatus"]), actual = hhmm(it["odpt:actualDepartureTime"]), est = hhmm(it["odpt:estimatedDepartureTime"]);
    upd(s, { dep_status: status, atd: iso(s.std, actual), etd: iso(s.std, est), dep_gate: gateOf(it["odpt:departureGate"]) });
    const sl = (status ?? "").toLowerCase();
    if (/cancel/.test(sl)) { add(s, "cancel", `${route(s)}は、欠航です（航空会社の運航情報）`); continue; }
    if (/return/.test(sl)) add(s, "return", `${route(s)}は、${names(s.dep)}へ引き返しました（航空会社の運航情報）`);
    const t = actual ?? est;
    if (!t) continue;
    const late = Math.round((atNear(s.std, t) - atNear(s.std, std)) / MIN);   // 運航情報の定刻から
    if (late >= 60) add(s, "delay_dep", `${route(s)}は、出発が約${late}分遅れ${actual ? "ました" : "る見込みです"}（定刻 ${hmText(std)} → ${actual ? "出発" : "変更後"} ${hmText(t)}・航空会社の運航情報）`);
  }
  // 到着（相手の空港は「出発空港」の項目）
  for (const it of Array.isArray(arrItems) ? arrItems : []) {
    const fn = flightNo(it?.["odpt:flightNumber"]), dep = ap(it?.["odpt:departureAirport"] ?? it?.["odpt:originAirport"]);
    const sta = hhmm(it?.["odpt:scheduledArrivalTime"]);
    if (!fn || !sta || !/^[A-Z]{3}$/.test(dep)) continue;
    const s = nearestSched(byKey.get(`${fn.no}|${dep}`) ?? [], sta, "sta");
    if (!s || s.sta == null) continue;
    note = infoText(it["odpt:flightInformationText"], it["odpt:flightInformationSummary"]);
    const status = st(it["odpt:flightStatus"]), actual = hhmm(it["odpt:actualArrivalTime"]), est = hhmm(it["odpt:estimatedArrivalTime"]);
    upd(s, { arr_status: status, ata: iso(s.sta, actual), eta: iso(s.sta, est), arr_gate: gateOf(it["odpt:arrivalGate"]) });
    const sl = (status ?? "").toLowerCase();
    if (/cancel/.test(sl)) { add(s, "cancel", `${route(s)}は、欠航です（航空会社の運航情報）`); continue; }
    if (/divert/.test(sl)) add(s, "divert", `${route(s)}は、${names(s.arr)}以外の空港へ向かいました（ダイバート・航空会社の運航情報）`, [s.arr, s.dep]);
    if (/return/.test(sl)) add(s, "return", `${route(s)}は、${names(s.dep)}へ引き返しました（航空会社の運航情報）`);
    const t = actual ?? est;
    if (!t) continue;
    const late = Math.round((atNear(s.sta, t) - atNear(s.sta, sta)) / MIN);
    if (late >= 60) add(s, "delay_arr", `${route(s)}は、到着が約${late}分遅れ${actual ? "ました" : "る見込みです"}（定刻 ${hmText(sta)} → ${actual ? "到着" : "変更後"} ${hmText(t)}・航空会社の運航情報）`, [s.arr, s.dep]);
  }
  return { alerts: [...alerts.values()], updates: [...updates.values()] };
}

// deno-lint-ignore no-explicit-any
export function statusAlerts(items: any[], scheds: StatusSched[], names: (iata: string) => string): StatusAlert[] {
  return odptStatus(items, [], scheds, names).alerts;
}

// ---- 特別塗装機で飛ぶ予定の便 ----
// 航空会社のお知らせの文に「JAL Jubilee Expressで運航いたします。」のように書かれた便を、飛ぶ前に見つける。
// 特別塗装機の一覧（liveries.ts）の名前が文に入っていればその名前、入っていなくても「〇〇ジェット」「〇〇塗装」などで運航すると書いてあれば、その〇〇を使う
export type LiveryPlan = { schedule_id: number; flight: string; dep: string; arr: string; std: string; livery: string; note: string };
const PLAN_WORD = /(ジェット|塗装|Express|ジンベエ|HONU|ポケモン|ピカチュウ|イーブイ|ロコン|ナッシー|Jubilee|JET)/i;
export function liveryOf(text: string, names: string[]): string | null {
  const t = text.replace(/\s+/g, " ");
  // 一覧の名前（長いものから。「ポケモンジェット 緑」より先に「ポケモンジェット」に当たらないように）
  for (const n of [...names].sort((a, b) => b.length - a.length)) if (n.length >= 4 && t.includes(n)) return n;
  const m = t.match(/[「『]?([^「」『』。、]{2,40}?)[」』]?\s*(?:で|にて)運航(?:いた)?(?:します|致します|いたします|予定)/);
  return m && PLAN_WORD.test(m[1]) ? m[1].trim() : null;
}
// deno-lint-ignore no-explicit-any
export function liveryPlans(depItems: any[], scheds: StatusSched[], names: string[]): LiveryPlan[] {
  const byKey = new Map<string, StatusSched[]>();
  for (const s of scheds) { const k = `${norm(s.flight)}|${s.dep}`; byKey.set(k, [...(byKey.get(k) ?? []), s]); }
  const out = new Map<number, LiveryPlan>();
  for (const it of Array.isArray(depItems) ? depItems : []) {
    const text = infoText(it?.["odpt:flightInformationText"]) ?? "";
    if (!text) continue;
    const livery = liveryOf(text, names);
    if (!livery) continue;
    const fn = flightNo(it?.["odpt:flightNumber"]), dep = ap(it?.["odpt:departureAirport"]), std = hhmm(it?.["odpt:scheduledDepartureTime"]);
    if (!fn || !std) continue;
    const s = nearestSched(byKey.get(`${fn.no}|${dep}`) ?? [], std, "std");
    if (!s) continue;
    if (/cancel/i.test(last(it["odpt:flightStatus"]))) continue;
    out.set(s.id, { schedule_id: s.id, flight: s.flight, dep: s.dep, arr: s.arr, std: new Date(s.std).toISOString(), livery: livery.slice(0, 60), note: text.slice(0, 120) });
  }
  return [...out.values()];
}
