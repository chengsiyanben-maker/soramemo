// ODPT のデータの時刻（dc:date）。ODPT の利用規約で、データを出すときはデータの時刻を添えることになっている。
//   取り込むたびに、種類（FlightInformationDeparture など）と航空会社ごとに、いちばん新しい dc:date を odpt_feed_dates に残す。
//   画面（チェックイン担当）は odpt_feed_dates を select して「ODPT のデータ ○時○分 時点」と出す。
//   airport-now は返す flights に dc_date（その空港の便の中でいちばん新しい dc:date）を足す。

// 一覧の中でいちばん新しい dc:date（ISO の文字）。なければ null
export function maxDcDate(items: unknown[]): string | null {
  let best: string | null = null, bestMs = -Infinity;
  for (const x of items) {
    const v = x && typeof x === "object" ? (x as Record<string, unknown>)["dc:date"] : null;
    if (typeof v !== "string") continue;
    const ms = Date.parse(v);
    if (!Number.isFinite(ms) || ms <= bestMs) continue;
    best = new Date(ms).toISOString(); bestMs = ms;
  }
  return best;
}

export type FeedDate = { feed: string; dc_date: string | null; n: number };

// 種類（type）と航空会社ごとに分けて、いちばん新しい dc:date と件数を出す。航空会社は odpt:operator（odpt.Operator:JAL）から
export function feedDates(type: string, items: unknown[], ops: string[] = []): FeedDate[] {
  const by = new Map<string, unknown[]>();
  for (const op of ops) by.set(op, []);
  for (const x of items) {
    const v = x && typeof x === "object" ? (x as Record<string, unknown>)["odpt:operator"] : null;
    const op = typeof v === "string" ? v.replace(/^odpt\.Operator:/, "") : "";
    if (!/^[A-Za-z0-9]{1,16}$/.test(op)) continue;
    if (!by.has(op)) by.set(op, []);
    by.get(op)!.push(x);
  }
  return [...by].map(([op, l]) => ({ feed: `${type}:${op}`, dc_date: maxDcDate(l), n: l.length }));
}

// 残す（失敗しても取り込みは止めない。エラーの文だけ返す）
// deno-lint-ignore no-explicit-any
export async function putFeedDates(admin: any, rows: FeedDate[]): Promise<string | null> {
  if (!rows.length) return null;
  try {
    const { error } = await admin.rpc("odpt_feed_date_put", { p: rows });
    return error ? "feed_date " + error.message : null;
  } catch (e) { return "feed_date " + (e instanceof Error ? e.message : String(e)); }
}
