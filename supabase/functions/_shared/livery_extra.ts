// 特別塗装機の一覧の「足し分」（表 livery_extra、移行184）と、海外の塗装機が日本の空港へ向かうのを1回知らせる中身（11/16 案1-A・案2-A・案3-A）。
// 取得・送信とは分けて、テストしやすくしている（airport-traffic が使う）
import type { Livery } from "./liveries.ts";
import { kmBetween } from "./foreign_now.ts";
import { liveryTag } from "./livery_note.ts";

export type ExtraRow = { reg: string; name: string; airline: string; kind?: string | null; src: string; from_day?: string | null; until_day?: string | null };

const REG = /^[A-Z0-9]{1,3}-?[A-Z0-9]{2,6}$/;
// 表の行を一覧の形にして、コードの一覧と合わせる。同じ登録記号は表のほうを使う。形の合わない行・Flightradar24 の出典は使わない
export function mergeLiveries(base: Livery[], rows: ExtraRow[] | null | undefined): Livery[] {
  const extra = new Map<string, Livery>();
  for (const r of rows ?? []) {
    const reg = String(r?.reg ?? "").trim().toUpperCase();
    if (!REG.test(reg) || reg.length > 10 || !r.name?.trim() || !r.airline?.trim()) continue;
    if (!/^https:\/\/\S+$/.test(r.src ?? "") || /(flightradar24|fr24)\./i.test(r.src)) continue;
    extra.set(reg, { reg, name: r.name.trim().slice(0, 60), airline: r.airline.trim().slice(0, 40), src: r.src,
      kind: r.kind === "alliance" ? "alliance" : "special",
      ...(r.from_day ? { from: String(r.from_day).slice(0, 10) } : {}), ...(r.until_day ? { until: String(r.until_day).slice(0, 10) } : {}) });
  }
  return [...base.filter((l) => !extra.has(l.reg)), ...extra.values()];
}

// 海外の会社の機体か（日本の登録記号は JA で始まる）
export const isForeignReg = (reg: string) => !/^JA/.test(reg);
// 空港の特別塗装機の知らせを送るか（案3-A）：特別塗装は全部、アライアンス塗装は海外の会社の機体だけ（国内の会社のものは毎日飛んでいるので送らない）
export const wantsLiveryPush = (v: { reg: string; kind?: string | null }) => v.kind !== "alliance" || isForeignReg(v.reg);

export type Seen = { reg: string; name: string; airline: string; kind?: string | null; callsign: string | null; lat: number; lon: number;
  alt_ft: number | null; kt?: number | null; trk?: number | null; iata?: string | null; phase?: string | null };
export type Dest = { iata: string; mins?: number | null };   // 行き先の候補（mins：ふだん着く時刻、日本時間の0時からの分）

// 早めに知らせる相手か：海外の会社の塗装機・便名がある・飛んでいる（5,000ft より上）・まだ空港の近くで「着陸に向かっている」と分かっていない
export const wantsInbound = (v: Seen) => isForeignReg(v.reg) && wantsLiveryPush(v) && !!v.callsign && typeof v.alt_ft === "number" && v.alt_ft > 5000 && !v.phase;

function bearing(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const r = Math.PI / 180, y = Math.sin((b.lon - a.lon) * r) * Math.cos(b.lat * r);
  const x = Math.cos(a.lat * r) * Math.sin(b.lat * r) - Math.sin(a.lat * r) * Math.cos(b.lat * r) * Math.cos((b.lon - a.lon) * r);
  return (Math.atan2(y, x) / r + 360) % 360;
}

// 行き先を1つに決める：候補のうち日本の空港で、機体の進む向きがその空港に向いている（ずれ60度まで）・1,500km 以内のもの。
// 向きが分からないときは候補が1つだけのときに限る。近いほうを選ぶ。決まらなければ null（知らせない）
export function pickDest(v: Seen, cands: Dest[], airports: Map<string, { lat: number; lon: number }>): (Dest & { km: number }) | null {
  const ok: (Dest & { km: number })[] = [];
  const uniq = [...new Map(cands.filter((c) => airports.has(c.iata)).map((c) => [c.iata, c])).values()];
  for (const c of uniq) {
    const at = airports.get(c.iata)!, km = kmBetween(v, at);
    if (km > 1500) continue;
    if (typeof v.trk === "number") {
      const d = Math.abs(((bearing(v, at) - v.trk + 540) % 360) - 180);
      if (d > 60 && km > 30) continue;
    } else if (uniq.length > 1) continue;
    ok.push({ ...c, km });
  }
  ok.sort((a, b) => a.km - b.km);
  return ok[0] ?? null;
}

// 着く見込み（分後）：残りの距離を対地速度で割り、降りていく分を足す。速さが分からない・遅すぎるときは 450 ノットとみる。
// ふだんの着く時刻（foreign_usual）が距離からの見込みと40分以内なら、ふだんの時刻のほうを使う（混んだ空港の待ちも入っている）
export function inboundEtaMin(km: number, kt: number | null | undefined, usualMins: number | null | undefined, nowMs = Date.now()): number {
  const speed = typeof kt === "number" && kt >= 200 ? kt : 450;
  const byDist = Math.round((km / 1.852) / speed * 60 + (km > 80 ? 12 : 4));
  if (typeof usualMins !== "number") return byDist;
  const nowJ = Math.floor(((nowMs + 9 * 3600_000) % 86400_000) / 60_000);
  const byUsual = ((usualMins - nowJ + 1440) % 1440);
  return Math.abs(byUsual - byDist) <= 40 && byUsual > 0 ? byUsual : byDist;
}

export const hhmm = (nowMs: number, addMin: number) => new Date(nowMs + 9 * 3600_000 + addMin * 60_000).toISOString().slice(11, 16);

// 「10時42分」の形（日本時間）。知らせの文で使う
export const jaTime = (nowMs: number, addMin: number) => { const [h, m] = hhmm(nowMs, addMin).split(":"); return `${Number(h)}時${m}分`; };

// 知らせの中身（推定と書く）：「（推定）」は最後に1回だけ。近くなったときの文（airport-traffic の notifyLivery）と同じく、便名がなければ会社名だけ
export function inboundMessage(v: Seen, dest: { iata: string }, airportName: string, etaMin: number, nowMs = Date.now()) {
  return {
    title: `★${v.name}`,
    body: `${v.name}（${v.airline}${v.callsign ? "・" + v.callsign : ""}）が${airportName}に向かっています。着くのは${jaTime(nowMs, etaMin)}ごろ（推定）。`,
    tag: liveryTag({ callsign: v.callsign, reg: v.reg }),
    renotify: true,
    url: `./#ops-${dest.iata}`,
  };
}
