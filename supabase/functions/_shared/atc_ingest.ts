// 交信を受け取るときの決まり（判定だけ）：送られてきた形の確かめ、呼び出し符号が近くの機体と合うか、同じ交信の重なり
import { type AtcParsed, parseAtc } from "./atc_parse.ts";

export const ATC_APS: Record<string, [number, number]> = { HND: [35.5533, 139.7811], NRT: [35.7772, 140.3823] };
export const ATC_CH = new Set(["atis", "del", "ramp", "gnd", "twr", "app", "dep"]);
export type AtcIn = { iata: string; ch: string; freq: string | null; at: number; text: string; conf: number | null };

export function checkIn(b: Record<string, unknown>, now: number): AtcIn | string {
  const iata = typeof b.iata === "string" ? b.iata : "", ch = typeof b.ch === "string" ? b.ch : "";
  if (!ATC_APS[iata]) return "unsupported airport";
  if (!ATC_CH.has(ch)) return "bad channel";
  const text = typeof b.text === "string" ? b.text.trim().slice(0, 400) : "";
  if (text.length < 4) return "empty";
  const at = typeof b.at === "number" ? b.at : typeof b.at === "string" ? Date.parse(b.at) : now;
  if (!Number.isFinite(at) || at > now + 60_000 || at < now - 10 * 60_000) return "bad time";
  const freq = typeof b.freq === "string" && /^1[1-3]\d\.\d{1,3}$/.test(b.freq) ? b.freq : null;
  const conf = typeof b.conf === "number" && b.conf >= 0 && b.conf <= 1 ? b.conf : null;
  return { iata, ch, freq, at, text, conf };
}

const R = Math.PI / 180;
const km = (a: [number, number], b: [number, number]) => { const h = Math.sin((b[0] - a[0]) * R / 2) ** 2 + Math.cos(a[0] * R) * Math.cos(b[0] * R) * Math.sin((b[1] - a[1]) * R / 2) ** 2; return 2 * 6371 * Math.asin(Math.sqrt(h)); };
// 呼び出し符号の機体が、15分以内に空港から（地上・タワー・グランドは30km、アプローチ・ディパーチャーは200km）以内で見えていたか
export function verified(p: AtcParsed, iata: string, ch: string, pos: { lat: number; lon: number; seen_at: string } | null, now: number): boolean {
  if (!p.callsign || !p.items.length || !pos) return false;
  if (now - Date.parse(pos.seen_at) > 15 * 60_000) return false;
  return km(ATC_APS[iata], [pos.lat, pos.lon]) <= (ch === "app" || ch === "dep" ? 200 : 30);
}
// 同じ交信の重なり：同じ空港・管制・呼び出し符号・同じ日本語で、前後10秒以内
export const sameMsg = (a: { callsign: string | null; ja: string; at: number }, b: { callsign: string | null; ja: string; at: number }) =>
  !!a.callsign && a.callsign === b.callsign && a.ja === b.ja && Math.abs(a.at - b.at) <= 10_000;

export { parseAtc };
