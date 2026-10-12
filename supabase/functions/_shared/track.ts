// 実際に飛んだ航路（OpenSky の /tracks/all の path）を、地図に描ける小さな形にする。
//   path の1点：[時刻, 緯度, 経度, 気圧高度, 進行方向, 地上にいるか]
//   返す形：[[緯度, 経度], ...]（小数3桁＝約100m。点は最大 MAX_POINTS）

export const TRACK = { maxPoints: 150, tolerance: 0.02 };   // 許す誤差は緯度経度で0.02度（約2km）。日本全体の地図では見分けがつかない

type P = [number, number];
const ok = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

// 線分 a-b から点 p までの距離（緯度経度をそのまま平面として扱う。誤差は地図の上では問題にならない）
function dist(p: P, a: P, b: P): number {
  const dx = b[1] - a[1], dy = b[0] - a[0], L = dx * dx + dy * dy;
  if (!L) return Math.hypot(p[0] - a[0], p[1] - a[1]);
  const t = Math.max(0, Math.min(1, ((p[1] - a[1]) * dx + (p[0] - a[0]) * dy) / L));
  return Math.hypot(p[0] - (a[0] + t * dy), p[1] - (a[1] + t * dx));
}

// 点を間引く（Douglas–Peucker）。曲がり角は残り、まっすぐな区間の点は減る
export function simplify(pts: P[], tol: number): P[] {
  if (pts.length <= 2) return pts.slice();
  const keep = new Uint8Array(pts.length); keep[0] = keep[pts.length - 1] = 1;
  const stack: [number, number][] = [[0, pts.length - 1]];
  while (stack.length) {
    const [i, j] = stack.pop()!;
    let best = -1, idx = -1;
    for (let k = i + 1; k < j; k++) { const d = dist(pts[k], pts[i], pts[j]); if (d > best) { best = d; idx = k; } }
    if (best > tol) { keep[idx] = 1; stack.push([i, idx], [idx, j]); }
  }
  return pts.filter((_, k) => keep[k]);
}

export function compactTrack(path: unknown): P[] | null {
  if (!Array.isArray(path)) return null;
  const pts: P[] = [];
  for (const q of path) {
    if (!Array.isArray(q) || !ok(q[1]) || !ok(q[2])) continue;
    if (q[1] < 20 || q[1] > 50 || q[2] < 120 || q[2] > 155) continue;   // 日本の周りの外は捨てる（受信の誤り）
    pts.push([q[1], q[2]]);
  }
  if (pts.length < 2) return null;
  let tol = TRACK.tolerance, out = simplify(pts, tol);
  while (out.length > TRACK.maxPoints) { tol *= 1.6; out = simplify(pts, tol); }
  return out.map(([la, lo]) => [Math.round(la * 1000) / 1000, Math.round(lo * 1000) / 1000]);
}
