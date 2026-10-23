// 天気の記録：空港の気象通報（METAR）の原文と、気象庁の台風情報をそのまま残す（wx-archive 関数。cron で1時間ごと）
//   METAR：aviationweather.gov（米国の航空気象センター。パブリックドメイン）
//   台風：気象庁 防災情報の台風の JSON（気象庁ホームページの利用規約にもとづき、出どころを書いて使う）
export type WxRow = { icao: string; at: string; raw: string; wx: string | null; wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null };

// METAR の原文から、天気の現象（雨・雪・雷・霧など）の語を取り出す。例：「-SHRA」「+TSRA」「SN」「FZRA」「BR」
const WX_TOKEN = /^(\+|-|VC)?(MI|PR|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PO|SQ|FC|SS|DS)+$|^(\+|-|VC)?(TS|SH)$/;
export function wxTokens(raw: string): string | null {
  const body = String(raw ?? "").split(/\s(?:RMK|TEMPO|BECMG|NOSIG)\b/)[0];
  const t = body.split(/\s+/).filter((w) => WX_TOKEN.test(w));
  return t.length ? t.join(" ") : null;
}
// 雪・凍った雨（雪の日の判定に使う）
export const isSnow = (wx: string | null) => !!wx && /(SN|SG|PL|FZ)/.test(wx);

// deno-lint-ignore no-explicit-any
export function metarRow(m: any): WxRow | null {
  const raw = String(m?.rawOb ?? ""), icao = String(m?.icaoId ?? "");
  const at = m?.obsTime ? new Date(Number(m.obsTime) * 1000).toISOString() : m?.reportTime ? new Date(m.reportTime).toISOString() : null;
  if (!/^[A-Z]{4}$/.test(icao) || !raw || !at || at === "Invalid Date") return null;
  const mv = raw.match(/KT\s+(?:\d{3}V\d{3}\s+)?(\d{4})(?:\s|$)/) || raw.match(/\s(CAVOK)\s/);
  return { icao, at, raw: raw.slice(0, 400), wx: wxTokens(raw),
    wdir: typeof m.wdir === "number" ? m.wdir : null, wspd: typeof m.wspd === "number" ? m.wspd : null, wgst: typeof m.wgst === "number" ? m.wgst : null,
    vis_m: mv ? (mv[1] === "CAVOK" || mv[1] === "9999" ? 10000 : parseInt(mv[1], 10)) : null };
}

// 台風：targetTc.json の1件 → 記録の1行（中身の JSON はそのまま残す）
export type TcRow = { tc_id: string; issue: string; number: string | null; category: string | null; spec: unknown; forecast: unknown };
// deno-lint-ignore no-explicit-any
export function tcKey(t: any): { tc_id: string; issue: string; number: string | null; category: string | null } | null {
  const id = String(t?.tropicalCyclone ?? ""), iss = t?.issue ? new Date(t.issue) : null;
  if (!/^TC\d{4}$/.test(id) || !iss || isNaN(iss.getTime())) return null;
  return { tc_id: id, issue: iss.toISOString(), number: t.typhoonNumber ? String(t.typhoonNumber).slice(0, 8) : null, category: t.category ? String(t.category).slice(0, 8) : null };
}
