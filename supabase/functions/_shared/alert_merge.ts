// 遅れ・欠航・ダイバートのお知らせ（flight_alerts）を、1つの便（便名＋運航日）につき1件の通知にまとめる。取得・送信とは分けて、テストしやすくしている。
//   ・同じ出発空港・到着空港・定刻の予定の便（共同運航・時刻表の重なり）は1つの便にまとめ、代表の便名を1つ決める
//   ・出発の遅れと到着の遅れ、推定と航空会社の運航情報は、1つの通知にまとめる（運航情報があれば推定より運航情報を使う）
//   ・「この便に乗る」（push_subs.flights）の人へは15分の遅れから知らせる
//   ・空港ごとの通知（push_subs.airports）は主要空港だけ。遅れは「門限（運用時間の終わり）に間に合わないおそれ」と「遅れで0時前後に着く」便だけを知らせる
//     （11/13 本人「通知がくるのは主要空港がいいな、門限ギリギリになりそうな便とか0時に着くような便とか」）。欠航・ダイバート・引き返しも主要空港だけ
//   ・送ってよいか（はじめて・重くなった・運航情報がはじめて届いた・遅れが30分以上ふえた）は、データベースの alert_push_claim が決める（下の shouldSend は同じ決まりの写し）
export type MergeSched = { id: number; flight: string; svc_date: string; dep: string; arr: string; std: string | number; sta?: string | number | null };
export type MergeAlert = { schedule_id: number; kind: string; message: string; iata: string[]; late?: number | null; official?: boolean | null };
export type MergeGroup = {
  gkey: string;            // 代表の便名@運航日@出発空港（通知の tag と送った記録に使う）
  flight: string; svc_date: string; dep: string; arr: string;
  fkeys: string[];         // まとめた便すべての「便名@運航日」（「この便に乗る」の宛先に使う）
  iata: string[];          // 関係する空港（空港ごとの通知の宛先）
  rank: number;            // 1 遅れ・2 門限に間に合わないおそれ／0時前後に着く遅れ・3 引き返し・4 ダイバート・5 欠航
  late: number | null;     // いちばん大きい遅れ（分）。運航情報があれば運航情報の中で
  official: boolean;       // 見出しのお知らせが航空会社の運航情報か
  eta: number | null;      // 到着の見込み（定刻＋遅れ。ミリ秒）
  body: string;            // 通知の本文
};
export type MergeSub = { id: number; airports: string[]; flights: string[] | null };

export const FLIGHT_SUB_MIN = 15;   // 「この便に乗る」の人へ知らせる遅れ（分）
export const OLD_LATE = 60;         // 遅れの分がない古いお知らせは60分とみなす
export const GROW_MIN = 30;         // 送った遅れから、これだけふえたら上書きして知らせる（分）
// 空港ごとの通知を出す主要空港（PM の案：羽田・成田・関西・伊丹・中部・新千歳・福岡・那覇）
export const MAJOR = ["HND", "NRT", "KIX", "ITM", "NGO", "CTS", "FUK", "OKA"];
// 主要空港の門限（運用時間の終わり。日本時間の0時からの分）。ほかの主要空港は24時間なので「0時前後」で見る。2026-11-13 に原文で確かめた
//   伊丹 7時〜21時：豊中市「大阪国際空港の現況等」令和8年度資料（https://www.city.toyonaka.osaka.jp/machi/kukou/gaiyou.files/R8siryou.pdf）・AIP JAPAN AD 2.3（ops_core.js）
//   福岡 7時〜22時（利用時間）：国土交通省 資料 令和8年9月（https://www.mlit.go.jp/koku/content/002023058.pdf）
//   成田 A滑走路 6時〜24時（やむを得ない理由なら24時30分まで）：千葉県「成田空港の離着陸制限の弾力的運用」令和8年8月28日更新（https://www.pref.chiba.lg.jp/kuushin/narita/danryokuka.html）
export const CURFEW: Record<string, { end: number; label: string }> = {
  ITM: { end: 21 * 60, label: "21時" },
  FUK: { end: 22 * 60, label: "22時" },
  NRT: { end: 24 * 60, label: "24時" },
};
export const CURFEW_NEAR = 30;                                 // 門限の30分前より遅く着く見込みなら知らせる
export const MIDNIGHT = { from: 23 * 60 + 30, to: 25 * 60 };   // 0時前後：23時30分〜翌1時

const RANK: Record<string, number> = { cancel: 5, divert_landed: 4, divert: 4, return: 3, delay_dep: 1, delay_arr: 1, no_takeoff: 1 };
export const rankOf = (kind: string) => RANK[kind] ?? 1;
// 先頭の0を除いた便名（JL0501 → JL501）
const normNo = (f: string) => f.replace(/^([A-Z0-9]{2})0+(\d)/, "$1$2");
const MIN = 60_000, JST = 9 * 3600_000;
const toMs = (v: string | number) => typeof v === "number" ? v : Date.parse(v);
const hm = (t: number) => { const d = new Date(t + JST); return `${d.getUTCHours()}時${String(d.getUTCMinutes()).padStart(2, "0")}分`; };
// 日本時間でその日の0時（ミリ秒）
const dayStart = (t: number) => Math.floor((t + JST) / 864e5) * 864e5 - JST;

// 門限・0時前後の知らせ（なければ null）。sta は到着の定刻、late は到着の遅れの見込み（分）
export function nightNotice(dep: string, arr: string, flight: string, sta: number, late: number, names: (i: string) => string = (i) => i): string | null {
  if (late < FLIGHT_SUB_MIN) return null;
  const eta = sta + late * MIN, d0 = dayStart(sta), staMin = (sta - d0) / MIN, etaMin = (eta - d0) / MIN;
  const tail = `${flight} ${names(dep)}→${names(arr)}、到着の見込み ${hm(eta)}（約${late}分遅れ）`;
  const c = CURFEW[arr];
  if (c) {
    if (staMin < c.end && etaMin >= c.end - CURFEW_NEAR) {
      return etaMin >= c.end
        ? `${names(arr)}の門限（${c.label}）に間に合わない見込み：${tail}。出発した空港へ引き返すか、ほかの空港へ向かうことがあります（推定）`
        : `${names(arr)}の門限（${c.label}）に間に合わないおそれ：${tail}`;
    }
    return null;
  }
  // 24時間の空港：定刻は夜（12時以降）で23時30分より前、遅れで 23時30分〜翌1時に着く見込み
  if (staMin >= 12 * 60 && staMin < MIDNIGHT.from && etaMin >= MIDNIGHT.from && etaMin < MIDNIGHT.to) return `0時前後に着く見込み：${tail}`;
  return null;
}

export function mergeAlerts(scheds: MergeSched[], alerts: MergeAlert[], names: (i: string) => string = (i) => i): MergeGroup[] {
  const byId = new Map(scheds.map((s) => [s.id, s]));
  // 同じ便：出発空港・到着空港・定刻が同じ
  const gid = (s: MergeSched) => `${s.dep}|${s.arr}|${toMs(s.std)}`;
  const members = new Map<string, MergeSched[]>();
  for (const s of scheds) members.set(gid(s), [...(members.get(gid(s)) ?? []), s]);
  const byGroup = new Map<string, MergeAlert[]>();
  for (const a of alerts) { const s = byId.get(a.schedule_id); if (s) byGroup.set(gid(s), [...(byGroup.get(gid(s)) ?? []), a]); }
  const out: MergeGroup[] = [];
  for (const [g, list] of byGroup) {
    const mem = members.get(g)!;
    // 代表の便名：運航情報のお知らせが出ている便 → JAL・ANA の便名 → いちばん小さい id
    const offIds = new Set(list.filter((a) => a.official).map((a) => a.schedule_id));
    const rep = [...mem].sort((a, b) => Number(offIds.has(b.id)) - Number(offIds.has(a.id))
      || Number(/^(JL|NH)/.test(b.flight)) - Number(/^(JL|NH)/.test(a.flight)) || a.id - b.id)[0];
    // 見出し：欠航 → ダイバート → 引き返し → 遅れ。同じ重さなら運航情報を先に、遅れは大きい方
    let top = Math.max(...list.map((a) => rankOf(a.kind)));
    let pool = list.filter((a) => rankOf(a.kind) === top);
    if (pool.some((a) => a.official)) pool = pool.filter((a) => a.official);
    const lateOf = (a: MergeAlert) => a.late ?? OLD_LATE;
    const late = top === 1 ? Math.max(...pool.map(lateOf)) : null;
    const head = [...pool].sort((a, b) => lateOf(b) - lateOf(a) || Number(a.kind === "delay_arr") - Number(b.kind === "delay_arr"))[0];
    // 到着の見込み：到着の遅れがあればそれ、なければ出発の遅れをそのまま足す
    const sta = mem.map((s) => s.sta).find((v) => v != null);
    const arrLate = top === 1 ? (pool.find((a) => a.kind === "delay_arr")?.late ?? pool.find((a) => a.kind === "delay_dep")?.late ?? null) : null;
    const eta = sta != null && arrLate != null ? toMs(sta) + arrLate * MIN : null;
    const flight = normNo(rep.flight);
    let body = head.message.slice(0, 300);
    if (top === 1 && sta != null && arrLate != null) {
      const n = nightNotice(rep.dep, rep.arr, flight, toMs(sta), arrLate, names);
      if (n) { top = 2; body = (n + (head.official ? "（航空会社の運航情報から）" : "")).slice(0, 300); }
    }
    out.push({
      gkey: `${flight}@${rep.svc_date}@${rep.dep}`,   // 同じ便名で2区間を飛ぶ日もあるので出発空港も入れる
      flight, svc_date: rep.svc_date, dep: rep.dep, arr: rep.arr,
      fkeys: [...new Set(mem.flatMap((s) => [`${s.flight}@${s.svc_date}`, `${normNo(s.flight)}@${s.svc_date}`]))],
      iata: [...new Set(list.flatMap((a) => a.iata))],
      rank: top, late, official: !!head.official, eta, body,
    });
  }
  return out;
}

// この購読に、この便を知らせてよいか
//   乗る便：15分以上の遅れと、欠航・ダイバート・引き返し
//   空港：選んだ主要空港の便で、門限・0時前後の遅れ（rank 2）と、欠航・ダイバート・引き返し。ふつうの遅れは知らせない
export function eligible(sub: MergeSub, g: MergeGroup): boolean {
  const byFlight = (sub.flights ?? []).some((f) => g.fkeys.includes(f) || g.fkeys.includes(normNo(f)));
  const byAirport = sub.airports.some((i) => MAJOR.includes(i) && g.iata.includes(i));
  if (byFlight && (g.rank > 1 || (g.late ?? OLD_LATE) >= FLIGHT_SUB_MIN)) return true;
  return byAirport && g.rank >= 2;
}

// 前に送ったものと比べて、送り直すか（データベースの alert_push_claim と同じ決まり。テストと説明のための写し）
export type Sent = { rank: number; late: number | null; official: boolean };
export function shouldSend(prev: Sent | null, next: Sent): boolean {
  if (!prev) return true;
  if (next.rank > prev.rank) return true;
  if (next.official && !prev.official && next.rank >= prev.rank) return true;
  return next.rank <= 2 && next.rank === prev.rank && (next.late ?? 0) >= (prev.late ?? 0) + GROW_MIN;
}

// 通知の中身。同じ便は同じ tag にして、端末の上で前の通知を上書きする（上書きのときも鳴らす：renotify）
export function payloadOf(g: MergeGroup, again: boolean) {
  return { title: `そらメモ：${g.flight}`, body: (again ? "【更新】" : "") + g.body, tag: `fw-${g.gkey}`, renotify: true, url: `./#ops-${g.dep}` };
}
