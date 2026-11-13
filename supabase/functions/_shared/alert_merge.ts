// 遅れ・欠航・ダイバートのお知らせ（flight_alerts）を、1つの便（便名＋運航日）につき1件の通知にまとめる。取得・送信とは分けて、テストしやすくしている。
//   ・同じ出発空港・到着空港・定刻の予定の便（共同運航・時刻表の重なり）は1つの便にまとめ、代表の便名を1つ決める
//   ・出発の遅れと到着の遅れ、推定と航空会社の運航情報は、1つの通知にまとめる（運航情報があれば推定より運航情報を使う）
//   ・宛先：「この便に乗る」（push_subs.flights）の人は15分の遅れから、空港（push_subs.airports）の人は60分の遅れから。欠航・ダイバート・引き返しはどちらも知らせる
//   ・送ってよいか（はじめて・重くなった・運航情報がはじめて届いた・遅れが30分以上ふえた）は、データベースの alert_push_claim が決める（下の shouldSend は同じ決まりの写し）
export type MergeSched = { id: number; flight: string; svc_date: string; dep: string; arr: string; std: string | number };
export type MergeAlert = { schedule_id: number; kind: string; message: string; iata: string[]; late?: number | null; official?: boolean | null };
export type MergeGroup = {
  gkey: string;            // 代表の便名@運航日@出発空港（通知の tag と送った記録に使う）
  flight: string; svc_date: string; dep: string; arr: string;
  fkeys: string[];         // まとめた便すべての「便名@運航日」（「この便に乗る」の宛先に使う）
  iata: string[];          // 関係する空港（空港ごとの通知の宛先）
  rank: number;            // 1 遅れ・3 引き返し・4 ダイバート・5 欠航
  late: number | null;     // いちばん大きい遅れ（分）。運航情報があれば運航情報の中で
  official: boolean;       // 見出しのお知らせが航空会社の運航情報か
  body: string;            // 通知の本文（見出しのお知らせの文）
};
export type MergeSub = { id: number; airports: string[]; flights: string[] | null };

export const FLIGHT_SUB_MIN = 15;   // 「この便に乗る」の人へ知らせる遅れ（分）
export const AIRPORT_SUB_MIN = 60;  // 空港ごとの通知の人へ知らせる遅れ（分）
export const GROW_MIN = 30;         // 送った遅れから、これだけふえたら上書きして知らせる（分）
const RANK: Record<string, number> = { cancel: 5, divert_landed: 4, divert: 4, return: 3, delay_dep: 1, delay_arr: 1, no_takeoff: 1 };
export const rankOf = (kind: string) => RANK[kind] ?? 1;
const isDelay = (kind: string) => rankOf(kind) === 1;
// 先頭の0を除いた便名（JL0501 → JL501）
const normNo = (f: string) => f.replace(/^([A-Z0-9]{2})0+(\d)/, "$1$2");

export function mergeAlerts(scheds: MergeSched[], alerts: MergeAlert[]): MergeGroup[] {
  const byId = new Map(scheds.map((s) => [s.id, s]));
  const t = (s: MergeSched) => typeof s.std === "number" ? s.std : Date.parse(s.std);
  // 同じ便：出発空港・到着空港・定刻が同じ
  const gid = (s: MergeSched) => `${s.dep}|${s.arr}|${t(s)}`;
  const members = new Map<string, MergeSched[]>();
  for (const s of scheds) members.set(gid(s), [...(members.get(gid(s)) ?? []), s]);
  const byGroup = new Map<string, MergeAlert[]>();
  for (const a of alerts) { const s = byId.get(a.schedule_id); if (s) byGroup.set(gid(s), [...(byGroup.get(gid(s)) ?? []), a]); }
  const out: MergeGroup[] = [];
  for (const [g, list] of byGroup) {
    const ms = members.get(g)!;
    // 代表の便名：運航情報のお知らせが出ている便 → JAL・ANA の便名 → いちばん小さい id
    const offIds = new Set(list.filter((a) => a.official).map((a) => a.schedule_id));
    const rep = [...ms].sort((a, b) => Number(offIds.has(b.id)) - Number(offIds.has(a.id))
      || Number(/^(JL|NH)/.test(b.flight)) - Number(/^(JL|NH)/.test(a.flight)) || a.id - b.id)[0];
    // 見出し：欠航 → ダイバート → 引き返し → 遅れ。同じ重さなら運航情報を先に、遅れは大きい方
    const top = Math.max(...list.map((a) => rankOf(a.kind)));
    let pool = list.filter((a) => rankOf(a.kind) === top);
    if (pool.some((a) => a.official)) pool = pool.filter((a) => a.official);
    const late = top === 1 ? Math.max(...pool.map((a) => a.late ?? AIRPORT_SUB_MIN)) : null;
    const head = [...pool].sort((a, b) => (b.late ?? AIRPORT_SUB_MIN) - (a.late ?? AIRPORT_SUB_MIN) || Number(a.kind === "delay_arr") - Number(b.kind === "delay_arr"))[0];
    out.push({
      gkey: `${normNo(rep.flight)}@${rep.svc_date}@${rep.dep}`,   // 同じ便名で2区間を飛ぶ日もあるので出発空港も入れる
      flight: normNo(rep.flight), svc_date: rep.svc_date, dep: rep.dep, arr: rep.arr,
      fkeys: [...new Set(ms.flatMap((s) => [`${s.flight}@${s.svc_date}`, `${normNo(s.flight)}@${s.svc_date}`]))],
      iata: [...new Set(list.flatMap((a) => a.iata))],
      rank: top, late, official: !!head.official,
      body: head.message.slice(0, 300),
    });
  }
  return out;
}

// この購読に、この便を知らせてよいか（遅れの大きさと、選び方で分ける）
export function eligible(sub: MergeSub, g: MergeGroup): boolean {
  const byFlight = (sub.flights ?? []).some((f) => g.fkeys.includes(f) || g.fkeys.includes(normNo(f)));
  const byAirport = sub.airports.some((i) => g.iata.includes(i));
  if (g.rank > 1) return byFlight || byAirport;
  const late = g.late ?? AIRPORT_SUB_MIN;
  return (byFlight && late >= FLIGHT_SUB_MIN) || (byAirport && late >= AIRPORT_SUB_MIN);
}

// 前に送ったものと比べて、送り直すか（データベースの alert_push_claim と同じ決まり。テストと説明のための写し）
export type Sent = { rank: number; late: number | null; official: boolean };
export function shouldSend(prev: Sent | null, next: Sent): boolean {
  if (!prev) return true;
  if (next.rank > prev.rank) return true;
  if (next.official && !prev.official && next.rank >= prev.rank) return true;
  return next.rank === 1 && prev.rank === 1 && (next.late ?? 0) >= (prev.late ?? 0) + GROW_MIN;
}

// 通知の中身。同じ便は同じ tag にして、端末の上で前の通知を上書きする（上書きのときも鳴らす：renotify）
export function payloadOf(g: MergeGroup, again: boolean) {
  return { title: `そらメモ：${g.flight}`, body: (again ? "【更新】" : "") + g.body, tag: `fw-${g.gkey}`, renotify: true, url: `./#ops-${g.dep}` };
}
