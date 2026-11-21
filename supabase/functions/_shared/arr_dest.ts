// 着陸・離陸に向かう空港を1つに決める（11/21 急ぎ：羽田行きの特別塗装機を「成田に着陸に向かっています」と知らせていた）。
//   原因：空港ごとの円は重なる（羽田60海里・成田40海里、両空港は約57km）。羽田へ降りる機体が成田の円の中でも高度を下げているので、
//   成田の答えでも「着陸」になり、空港を順に回すと後の成田で上書きされていた。
//   1. refinePhases：空港ごとの答えの arr/dep を、滑走路の向きと距離（最終進入の範囲）・高さ・向かっている向きで絞る（運用タブの一覧にも効く）
//   2. pickAirport：1機が2つ以上の空港で arr（dep）になったとき、便名の行き先（出発地）＞最終進入に乗っていて近い方＞はっきり近い方。決められなければ null（知らせない）
// 取得とは分けて、テストしやすくしている。
import RW from "./jp_runways.json" with { type: "json" };

export type Rwy = { id: string; thr: [number, number]; hdg: number };
export type Apt = { iata?: string; at: [number, number]; rws: Rwy[] };

const R = Math.PI / 180;
export function km(a: [number, number], b: [number, number]) {
  const dl = (b[0] - a[0]) * R, dn = (b[1] - a[1]) * R;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * R) * Math.cos(b[0] * R) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
export function bearing(a: [number, number], b: [number, number]) {
  const y = Math.sin((b[1] - a[1]) * R) * Math.cos(b[0] * R);
  const x = Math.cos(a[0] * R) * Math.sin(b[0] * R) - Math.sin(a[0] * R) * Math.cos(b[0] * R) * Math.cos((b[1] - a[1]) * R);
  return (Math.atan2(y, x) / R + 360) % 360;
}
const off = (a: number, b: number) => Math.abs(((a - b) % 360 + 540) % 360 - 180);   // 2つの向きの差（0〜180°）

// 空港の滑走路（jp_runways.json。着陸の向きと接地点）。ない空港は空の配列
// deno-lint-ignore no-explicit-any
const RWJ = RW as any as Record<string, { center: [number, number]; rw: Record<string, Rwy> }>;
export function runwaysFor(iata: string): Rwy[] {
  return Object.values(RWJ[iata]?.rw ?? {});
}

type Pos = { lat: number; lon: number; alt_ft: number | null; hdg: number | null };
type P = Pos & { phase: string };

// 最終進入の範囲：滑走路の延長線の上（横に3km以内）で、接地点の手前 maxKm 以内、向きが滑走路と30°以内、
// 高さが3°の進入より大きく上でない（距離の海里×320ft の1.6倍＋1,500ft まで）
export function onFinal(p: Pos, rws: Rwy[], maxKm = 25): Rwy | null {
  if (p.hdg == null) return null;
  for (const r of rws) {
    const d = km(r.thr, [p.lat, p.lon]); if (d > maxKm + 1) continue;
    const a = off(bearing(r.thr, [p.lat, p.lon]), (r.hdg + 180) % 360);
    const along = d * Math.cos(a * R), cross = Math.abs(d * Math.sin(a * R));
    if (along < -1 || along > maxKm || cross > 3) continue;
    if (off(p.hdg, r.hdg) > 30) continue;
    if (p.alt_ft != null && p.alt_ft > (Math.max(0, along) / 1.852) * 320 * 1.6 + 1500) continue;
    return r;
  }
  return null;
}

// 離陸の上昇の範囲：滑走路の向こう端（＝反対向きの接地点）から先 maxKm 以内、延長線の横4km以内、向きが30°以内
export function onClimbOut(p: Pos, rws: Rwy[], maxKm = 20): Rwy | null {
  if (p.hdg == null) return null;
  for (const r of rws) {
    // 離陸の向き r.hdg で飛ぶとき、出ていく端は「反対向きの接地点」。ここでは近い方の端の代わりに接地点 thr から測り、手前2kmまで許す
    const d = km(r.thr, [p.lat, p.lon]); if (d > maxKm + 5) continue;
    const a = off(bearing(r.thr, [p.lat, p.lon]), r.hdg);
    const along = d * Math.cos(a * R), cross = Math.abs(d * Math.sin(a * R));
    if (along < -2 || along > maxKm + 4 || cross > 4) continue;
    if (off(p.hdg, r.hdg) > 30) continue;
    return r;
  }
  return null;
}

// 向かっている（離陸なら離れていく）空港ほど小さくなる点（traffic.ts の planesFrom と同じ考え方）
function score(p: P, o: [number, number], phase: string) {
  const dd = km(o, [p.lat, p.lon]); if (p.hdg == null) return dd;
  const c = Math.cos((p.hdg - bearing([p.lat, p.lon], o)) * R);
  return dd * (phase === "arr" ? 2 - c : 2 + c);
}
// その空港に降りるには高すぎる（3°の進入の倍を超えて、さらに4,000ft 以上上）
function tooHigh(p: Pos, at: [number, number]) {
  if (p.alt_ft == null) return false;
  const nm = km(at, [p.lat, p.lon]) / 1.852;
  return p.alt_ft > nm * 320 * 2 + 4000;
}

// 空港ごとの答えの arr/dep を絞る。others：ほかの空港（滑走路が分からない空港は rws を空に）。
//   arr：この空港の最終進入に乗っていればそのまま。ほかの空港の最終進入に乗っていれば外す。
//        この空港には高すぎて、ほかの空港（110km以内）なら高すぎない、のときも外す。
//        向き・距離の点がほかの空港（110km以内）のほうが1割以上小さければ外す（前は40km以内の空港だけ見ていた）
//   dep：この空港の離陸の上昇に乗っていればそのまま。ほかの空港の離陸の上昇に乗っていれば外す。点の比べ方は arr と同じ
export function refinePhases<T extends P>(planes: T[], self: Apt, others: Apt[], range = 110): T[] {
  return planes.map((p) => {
    if (p.phase !== "arr" && p.phase !== "dep") return p;
    const pos: [number, number] = [p.lat, p.lon];
    const near = others.filter((o) => km(o.at, pos) <= range);
    const drop = (): T => ({ ...p, phase: "other" });
    if (p.phase === "arr") {
      if (onFinal(p, self.rws)) return p;
      if (near.some((o) => onFinal(p, o.rws))) return drop();
      if (tooHigh(p, self.at) && near.some((o) => !tooHigh(p, o.at))) return drop();
    } else {
      if (onClimbOut(p, self.rws)) return p;
      if (near.some((o) => onClimbOut(p, o.rws))) return drop();
    }
    const mine = score(p, self.at, p.phase);
    if (near.some((o) => score(p, o.at, p.phase) < mine * 0.9)) return drop();
    return p;
  });
}

// 1機の候補（空港ごとの答えで arr、または dep になった空港）から、1つに決める。
//   known：便名から分かった行き先（arr）・出発地（dep）。分かっていれば、候補の中にあればそれ、なければ null（ほかの空港へ向かっている）
//   次に、最終進入（離陸の上昇）に乗っている候補の近い方。
//   どれにも乗っていなければ、候補が1つで50km以内ならそれ。2つ以上なら、いちばん近い候補が2番目の7割以下の距離ならそれ。それ以外は null
export type Cand = { iata: string; dist_km: number; aligned: boolean };
export function pickAirport(cands: Cand[], known?: string | null): string | null {
  if (!cands.length) return null;
  if (known) return cands.some((c) => c.iata === known) ? known : null;
  const byDist = [...cands].sort((a, b) => a.dist_km - b.dist_km);
  const al = byDist.filter((c) => c.aligned);
  if (al.length) return al[0].iata;
  if (byDist.length === 1) return byDist[0].dist_km <= 50 ? byDist[0].iata : null;
  return byDist[0].dist_km <= byDist[1].dist_km * 0.7 ? byDist[0].iata : null;
}
