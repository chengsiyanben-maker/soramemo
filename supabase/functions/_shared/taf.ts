// 飛行場予報（TAF）を残す形にする（wx-archive 関数。11/25 本人「羽田、成田の滑走路の使い方を気象と関連付けて予想できそう？」）
//   出どころ：aviationweather.gov の Data API（米国の航空気象センター。パブリックドメイン。名乗りの User-Agent をつけ、1分100回より少なく）
//   taf_obs：発表ごとの原文（1発表1行）／taf_hours：その発表の1時間ごとの風（ふだんの状態と、一時的な変化 TEMPO・PROB の強いほう）
//   滑走路の予想の当たり具合（rwy_wx_eval）が「数時間前の TAF から当てる」に使う。画面には出さない（構想段階）
export type TafObsRow = { icao: string; issued_at: string; valid_from: string; valid_to: string; raw: string };
export type TafHourRow = {
  icao: string; issued_at: string; hr: string;
  wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null;
  t_wdir: number | null; t_wspd: number | null; t_wgst: number | null;   // その時間に重なる TEMPO・PROB のうち風のいちばん強いもの
};

const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
const iso = (sec: number) => new Date(sec * 1000).toISOString();
const visOf = (v: unknown) => { const s = String(v ?? ""); if (!s) return null; if (s.endsWith("+")) return 10000; const mi = parseFloat(s); return Number.isFinite(mi) ? Math.round(mi * 1609) : null; };

// API の1件 → 原文の行と1時間ごとの行。形が合わなければ null
//   ふだんの状態：最初の組（変化なし）と FM は timeFrom から、BECMG は変わり終わる timeBec から（変わる途中の時間は前の状態のまま）。
//   BECMG・FM で書いていない要素（風だけの BECMG など）は前の値を引き継ぐ
//   時間の行は、その時間の30分の時点で決める（例：13時の行＝13時30分の状態）
// deno-lint-ignore no-explicit-any
export function tafRows(t: any): { obs: TafObsRow; hours: TafHourRow[] } | null {
  const icao = String(t?.icaoId ?? ""), raw = String(t?.rawTAF ?? "");
  const issued = t?.issueTime ? Date.parse(String(t.issueTime)) : NaN, vf = num(t?.validTimeFrom), vt = num(t?.validTimeTo);
  if (!/^[A-Z]{4}$/.test(icao) || !raw || !Number.isFinite(issued) || vf == null || vt == null || vt <= vf || vt - vf > 48 * 3600) return null;
  const issued_at = new Date(issued).toISOString();
  const obs: TafObsRow = { icao, issued_at, valid_from: iso(vf), valid_to: iso(vt), raw: raw.slice(0, 1000) };
  const fc = (Array.isArray(t.fcsts) ? t.fcsts : []) as Record<string, unknown>[];
  type G = { from: number; to: number; wdir: number | null; wspd: number | null; wgst: number | null; vis: number | null; temp: boolean; vrb: boolean };
  const groups: G[] = fc.map((f) => {
    const ch = String(f.fcstChange ?? "").toUpperCase(), from = num(f.timeFrom) ?? vf, to = num(f.timeTo) ?? vt;
    const temp = ch === "TEMPO" || ch.startsWith("PROB") || num(f.probability) != null;
    const start = ch === "BECMG" ? num(f.timeBec) ?? from : from;
    // 風向きの定まらない風（VRB）は、API では wdir が "VRB" か null で来る
    return { from: start, to, wdir: num(f.wdir), wspd: num(f.wspd), wgst: num(f.wgst), vis: visOf(f.visib), temp, vrb: f.wdir === "VRB" };
  });
  const base = groups.filter((g) => !g.temp).sort((a, b) => a.from - b.from), temps = groups.filter((g) => g.temp);
  const hours: TafHourRow[] = [];
  for (let h = Math.floor(vf / 3600) * 3600; h < vt; h += 3600) {
    const mid = h + 1800; if (mid < vf) continue;
    let s: { wdir: number | null; wspd: number | null; wgst: number | null; vis: number | null } = { wdir: null, wspd: null, wgst: null, vis: null };
    for (const g of base) {
      if (g.from > mid) break;
      s = { wdir: g.wspd != null ? (g.vrb ? null : g.wdir) : s.wdir, wspd: g.wspd ?? s.wspd, wgst: g.wspd != null ? g.wgst : s.wgst, vis: g.vis ?? s.vis };
    }
    let tw: G | null = null;
    for (const g of temps) if (g.from <= mid && mid < g.to && g.wspd != null && (!tw || g.wspd > tw.wspd!)) tw = g;
    hours.push({ icao, issued_at, hr: iso(h), wdir: s.wdir, wspd: s.wspd, wgst: s.wgst, vis_m: s.vis,
      t_wdir: tw && !tw.vrb ? tw.wdir : null, t_wspd: tw?.wspd ?? null, t_wgst: tw?.wgst ?? null });
  }
  return { obs, hours };
}

// さかのぼって取るときの時刻（新しい順。stepH 時間おき、days 日ぶん、skipDays 日前から）。API の date= に渡す
export function tafBackDates(now: number, days: number, skipDays = 0, stepH = 3): string[] {
  const out: string[] = [], end = now - skipDays * 864e5, start = end - days * 864e5;
  for (let t = Math.floor(end / 3600e3) * 3600e3; t > start; t -= stepH * 3600e3) out.push(new Date(t).toISOString().slice(0, 19) + "Z");
  return out;
}
