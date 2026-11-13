// 関数どうしで使い回す置き場（表 edge_cache、移行 164）。関数の中の記憶は入れ物（isolate）ごとに消えるので、
// 記憶 → この置き場 → 配信元 の順に見る。置き場の読み書きに失敗しても、今までどおり配信元に取りに行く（遅くなるだけで止まらない）。
export type Entry = { at: number; v: unknown };
// deno-lint-ignore no-explicit-any
type Admin = any;

// まとめて1回で読む（主キーで引く）
export async function readShared(admin: Admin, keys: string[]): Promise<Map<string, Entry>> {
  const out = new Map<string, Entry>();
  if (!keys.length) return out;
  try {
    const { data, error } = await admin.from("edge_cache").select("key, body, at").in("key", keys);
    if (error) return out;
    for (const r of data ?? []) out.set(String(r.key), { at: Date.parse(r.at), v: r.body });
  } catch { /* 置き場が使えないときは配信元へ */ }
  return out;
}

export async function writeShared(admin: Admin, key: string, v: unknown, at = Date.now()): Promise<void> {
  try { await admin.from("edge_cache").upsert({ key, body: v ?? null, at: new Date(at).toISOString() }); } catch { /* 次の回に */ }
}

// 記憶と置き場のうち新しいほう。ttl 以内なら fresh（そのまま使う）、古ければ stale（配信元が取れないときの代わり）
export function choose(mem: Entry | undefined, shared: Entry | undefined, ttl: number, now = Date.now()): { fresh: Entry | null; stale: Entry | null } {
  const best = [mem, shared].filter((x): x is Entry => !!x && Number.isFinite(x.at)).sort((a, b) => b.at - a.at)[0] ?? null;
  if (!best) return { fresh: null, stale: null };
  return now - best.at < ttl ? { fresh: best, stale: null } : { fresh: null, stale: best };
}
