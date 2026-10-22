// 古い記録のファイル置き場（Storage の非公開の cold）の決まり：置き場所、圧縮、空の道すじの取り出し（判定だけ）
export const COLD_BUCKET = "cold";
export const COLD_AFTER_DAYS = 400;   // これより前の日を移す
export const coldPath = (tbl: string, day: string) => `${tbl}/${day.slice(0, 4)}/${day}.json.gz`;
export const coldBefore = (now = Date.now(), days = COLD_AFTER_DAYS) => new Date(now + 9 * 3600_000 - days * 86_400_000).toISOString().slice(0, 10);

export async function gzip(s: string): Promise<Uint8Array> {
  return new Uint8Array(await new Response(new Blob([s]).stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer());
}
export async function gunzip(b: Uint8Array | ArrayBuffer): Promise<string> {
  return await new Response(new Blob([b as BlobPart]).stream().pipeThrough(new DecompressionStream("gzip"))).text();
}
// 空の道すじ：移した記録から、その空港の航跡を airport_tracks と同じ形（{d: 出発なら1, p: 線}）で
export function tracksFrom(tbl: "airport_tracks_all" | "flight_tracks", rows: Record<string, unknown>[], iata: string): { d: number; p: string }[] {
  if (tbl === "airport_tracks_all") return rows.filter((r) => r.iata === iata).map((r) => ({ d: Number(r.dep_here) ? 1 : 0, p: String(r.pts) }));
  return rows.filter((r) => r.dep === iata || r.arr === iata).map((r) => ({ d: r.dep === iata ? 1 : 0, p: String(r.pts) }));
}
