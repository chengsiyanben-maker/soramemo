// 気象通報（METAR）を米国の航空気象センターから取り、運用の推定に使う形にする（metar 関数と、運用の記録で使う）
export type Metar = { id: string; time: string; raw: string; wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null; vis_plus: boolean };

// deno-lint-ignore no-explicit-any
export function parseMetar(m: any): Metar {
  // 視程：日本の空港の通報は、視程をメートルの4桁で書く（9999＝10km以上）。原文の数字を優先し、なければマイルの値を換算する
  const raw = String(m.rawOb ?? ""), mv = raw.match(/KT\s+(?:\d{3}V\d{3}\s+)?(\d{4})(?:\s|$)/) || raw.match(/\s(CAVOK)\s/);
  const visRaw = String(m.visib ?? ""), visMi = parseFloat(visRaw);
  const visM = mv ? (mv[1] === "CAVOK" || mv[1] === "9999" ? 10000 : parseInt(mv[1], 10)) : Number.isFinite(visMi) ? Math.round(visMi * 1609) : null;
  return {
    id: m.icaoId, time: m.reportTime, raw: m.rawOb,
    wdir: typeof m.wdir === "number" ? m.wdir : null,          // 風向（度）。風向が変わりやすいとき（VRB）は null
    wspd: m.wspd ?? null, wgst: m.wgst ?? null,                 // 風速・最大瞬間（ノット）
    vis_m: visM, vis_plus: mv ? mv[1] === "9999" || mv[1] === "CAVOK" : visRaw.endsWith("+"),
  };
}

// いくつかの空港をまとめて1回で取る
export async function fetchMetars(ids: string[], timeoutMs = 15000): Promise<Map<string, Metar>> {   // timeoutMs：見る人の呼び出しでは短く
  const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${ids.join(",")}&format=json`,
    { headers: { "User-Agent": "soramemo (metar relay)" }, signal: AbortSignal.timeout(timeoutMs) });
  if (!r.ok) throw new Error("upstream " + r.status);
  const out = new Map<string, Metar>();
  // 同じ空港の通報が複数あれば、新しいものを使う
  // deno-lint-ignore no-explicit-any
  for (const m of (await r.json()) as any[]) { const p = parseMetar(m); const o = out.get(p.id); if (!o || o.time < p.time) out.set(p.id, p); }
  return out;
}

// 配信元が取れないときの代わり：天気の記録（wx_obs。wx-archive が1時間ごとに足す。なので最長で1時間あまり前の通報になる）の1行を、同じ形にする
export function metarFromObs(r: { icao: string; at: string; raw: string; wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null } | null | undefined): Metar | null {
  if (!r || !r.raw) return null;
  const raw = String(r.raw), plus = /\s(9999|CAVOK)(\s|$)/.test(raw);
  return { id: r.icao, time: new Date(r.at).toISOString(), raw, wdir: r.wdir ?? null, wspd: r.wspd ?? null, wgst: r.wgst ?? null, vis_m: r.vis_m ?? null, vis_plus: plus };
}

