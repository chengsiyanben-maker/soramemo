// 「この便に乗る」で選ばれた便だけを毎分見るときに、ODPT へ何を問い合わせるかを決める（odpt-status?fast=1）。取得とは分けて、テストしやすくしている。
//   ・まだ出発していない便は出発空港の出発情報、出発した便は到着空港の到着情報
//   ・同じ会社・同じ空港・同じ向きは1回にまとめる。定刻が今に近い便から、1回に cap 件まで
import type { StatusSched } from "./odpt_status.ts";

export type FastRow = { id: number; flight: string; svc_date: string; dep: string; arr: string; std: string; sta: string; source?: string | null; atd?: string | null; ata?: string | null };
export type FastCall = { type: "Departure" | "Arrival"; op: "JAL" | "ANA"; airport: string };

// 便の会社（時刻表の出典に書いた会社。なければ便名の記号から）
export function opOf(r: { flight: string; source?: string | null }): "JAL" | "ANA" {
  const m = /（(JAL|ANA)）/.exec(r.source ?? "");
  if (m) return m[1] as "JAL" | "ANA";
  return /^(JL|NU|JC|HAC|RAC|XM|MZ)/.test(r.flight) ? "JAL" : "ANA";
}

export function fastTargets(rows: FastRow[], now: number, cap = 6): { calls: FastCall[]; scheds: StatusSched[] } {
  const live = rows.filter((r) => !r.ata && Date.parse(r.sta) > now - 6 * 3600_000 && Date.parse(r.std) < now + 4 * 3600_000)
    .sort((a, b) => Math.abs(Date.parse(a.std) - now) - Math.abs(Date.parse(b.std) - now));
  const calls = new Map<string, FastCall>(), used = new Set<number>();
  for (const r of live) {
    const c: FastCall = r.atd ? { type: "Arrival", op: opOf(r), airport: r.arr } : { type: "Departure", op: opOf(r), airport: r.dep };
    const k = `${c.type}|${c.op}|${c.airport}`;
    if (!calls.has(k)) { if (calls.size >= cap) continue; calls.set(k, c); }
    used.add(r.id);
  }
  const scheds = live.filter((r) => used.has(r.id)).map((r) => ({ id: r.id, flight: r.flight, dep: r.dep, arr: r.arr, std: Date.parse(r.std), sta: Date.parse(r.sta) }));
  return { calls: [...calls.values()], scheds };
}
