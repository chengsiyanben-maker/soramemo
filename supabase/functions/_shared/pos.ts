// 印の位置を残すときの丸め（11/26 本人の OK・PM の判断：新しい印から小数3桁＝約100m）
//   判定（judge.ts の decide）は丸める前の値でする。丸めるのは checkins に書く値だけ
//   今までの記録は変えない（データベースの中で丸め直す仕組みは作らない）。精度（accuracy_m）は今のまま残す
export const POS_DECIMALS = 3;

// 小数3桁に丸める。数でないもの・範囲の外はそのまま返す（判定で先に断っているので、ここには来ない）
export function roundPos(v: unknown, decimals = POS_DECIMALS): number {
  const n = Number(v);
  if (!Number.isFinite(n) || Math.abs(n) > 180) return n;
  const f = 10 ** decimals;
  const r = Math.round(Math.abs(n) * f) / f; // 0.5 の丸めを正負で同じにする（−35.0005 → −35.001）
  return n < 0 ? -r : r;
}
