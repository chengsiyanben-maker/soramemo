// 飛行場予報（TAF）を残す形にする（羽田・成田。wx-archive が1時間ごとに取る。移行198 の wx_taf・wx_taf_hours）
//   出どころ：aviationweather.gov の Data API（米国の航空気象センター。パブリックドメイン。METAR と同じ所）
//   原文はそのまま wx_taf に、時間ごとの風（向き・速さ・突風）と、その風から推定した運用を wx_taf_hours に残す。
//   あとで「数時間前の TAF から滑走路の使い方を当てられるか」を ops_log（実際の機体からの判定）と比べるため
export type TafRow = { icao: string; issued: string; valid_from: string; valid_to: string; raw: string };
export type TafHour = {
  icao: string; issued: string; at: string; lead_h: number;
  wdir: number | null; wspd: number | null; wgst: number | null; vrb: boolean; changing: boolean;
  vis_m: number | null; wx: string | null;
  t_kind: string | null; t_wdir: number | null; t_wspd: number | null; t_wgst: number | null;
  est_mode: string | null;
};
// 風から運用を推定する関数（_shared/ops_core.js の def.estimate。羽田は時刻も使う）
export type Estimate = (m: { wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null }, at: Date) => string | null;

const H = 3600_000;
const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
const iso = (sec: unknown) => (typeof sec === "number" && Number.isFinite(sec) ? new Date(sec * 1000).toISOString() : null);

// 視程：API は法定マイル（"6+" は 6マイル以上）で返す。メートルにする（6マイル以上は 9999）
export function visM(v: unknown): number | null {
  if (typeof v === "string" && /^\d+(\.\d+)?\+$/.test(v)) return 9999;
  const n = typeof v === "number" ? v : typeof v === "string" && /^\d+(\.\d+)?$/.test(v) ? Number(v) : NaN;
  if (!Number.isFinite(n)) return null;
  return Math.min(9999, Math.round(n * 1609.344));
}

// deno-lint-ignore no-explicit-any
export function tafRow(t: any): TafRow | null {
  const icao = String(t?.icaoId ?? ""), raw = String(t?.rawTAF ?? "").trim();
  const issued = t?.issueTime ? new Date(t.issueTime) : null, from = iso(t?.validTimeFrom), to = iso(t?.validTimeTo);
  if (!/^[A-Z]{4}$/.test(icao) || !raw || !issued || isNaN(issued.getTime()) || !from || !to || from >= to) return null;
  return { icao, issued: issued.toISOString(), valid_from: from, valid_to: to, raw: raw.slice(0, 2000) };
}

// 時間ごと（毎時0分）の風。基本の予報・FM・BECMG のうち、その時刻にかかる最後のものを使う。
//   BECMG の変わっている途中（timeFrom〜timeBec）は changing＝true（風は変わったあとの値）。
//   TEMPO・PROB は別の列（t_*）に。いくつかかかるときは風（突風があれば突風）の強いもの
// deno-lint-ignore no-explicit-any
export function tafHours(t: any, estimate?: Estimate): TafHour[] {
  const row = tafRow(t); if (!row) return [];
  const fc = (Array.isArray(t.fcsts) ? t.fcsts : []).filter((f: { timeFrom?: unknown; timeTo?: unknown }) => num(f?.timeFrom) != null && num(f?.timeTo) != null);
  const issuedMs = Date.parse(row.issued), out: TafHour[] = [];
  const start = Math.ceil(Date.parse(row.valid_from) / H) * H, end = Date.parse(row.valid_to);
  for (let h = start; h < end && out.length < 48; h += H) {
    const s = h / 1000;
    const covers = (f: { timeFrom: number; timeTo: number }) => f.timeFrom <= s && s < f.timeTo;
    // deno-lint-ignore no-explicit-any
    const main = fc.filter((f: any) => covers(f) && (f.fcstChange == null || f.fcstChange === "FM" || f.fcstChange === "BECMG"))
      // deno-lint-ignore no-explicit-any
      .sort((a: any, b: any) => b.timeFrom - a.timeFrom)[0];
    // deno-lint-ignore no-explicit-any
    const temp = fc.filter((f: any) => covers(f) && (f.fcstChange === "TEMPO" || f.fcstChange === "PROB"))
      // deno-lint-ignore no-explicit-any
      .sort((a: any, b: any) => (num(b.wgst) ?? num(b.wspd) ?? -1) - (num(a.wgst) ?? num(a.wspd) ?? -1))[0];
    const vrb = main?.wdir === "VRB", wdir = vrb ? null : num(main?.wdir), wspd = num(main?.wspd), wgst = num(main?.wgst), vis = visM(main?.visib);
    const hour: TafHour = {
      icao: row.icao, issued: row.issued, at: new Date(h).toISOString(), lead_h: Math.round((h - issuedMs) / H),
      wdir, wspd, wgst, vrb, changing: !!(main && main.fcstChange === "BECMG" && num(main.timeBec) != null && s < main.timeBec),
      vis_m: vis, wx: typeof main?.wxString === "string" && main.wxString.trim() ? main.wxString.trim().slice(0, 40) : null,
      t_kind: temp ? (temp.fcstChange === "PROB" ? `PROB${num(temp.probability) ?? ""}` : "TEMPO").slice(0, 8) : null,
      t_wdir: temp ? (temp.wdir === "VRB" ? null : num(temp.wdir)) : null, t_wspd: temp ? num(temp.wspd) : null, t_wgst: temp ? num(temp.wgst) : null,
      est_mode: null,
    };
    if (estimate && main && wspd != null) {
      try { hour.est_mode = estimate({ wdir, wspd, wgst, vis_m: vis }, new Date(h)); } catch { /* 推定なしで残す */ }
    }
    out.push(hour);
  }
  return out;
}

// 過去の TAF をさかのぼって取る時刻（cursor から3時間ずつ前へ、steps 回）。from より前は取らない
export function backDates(cursor: number, from: number, steps = 8): number[] {
  const out: number[] = [];
  for (let i = 1; i <= steps; i++) { const d = cursor - i * 3 * H; if (d < from) break; out.push(d); }
  return out;
}
// aviationweather.gov の date の形（yyyymmdd_hhmm、UTC）
export const awcDate = (ms: number) => new Date(ms).toISOString().slice(0, 16).replace(/[-:]/g, "").replace("T", "_");
