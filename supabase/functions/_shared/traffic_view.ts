// 見る人の airport-traffic を速くするための小さな決まり（11/21 改善担当の見回り 7「運用を開いたときの機体の位置 3.7秒」）
//   1. 置き場（edge_cache）の答えが少し古い（20秒〜60秒）ときは、待たせずにそれを返し、裏で作り直す
//   2. 記録の処理（30秒ごと）は、だれかが見ている空港（見る人のしるし trafficseen:<空港> が3分以内）だけ、置き場の答えを新しくする
//      （だれも見ていない空港には書かない。前に「書き込みが倍になる」ので避けた形を、見ている空港だけに絞って使う）
//   3. 返す線（trail）は、画面が使う着陸・離陸の機体（phase が arr・dep）だけに付ける。それ以外は空の配列（形は同じ）
//      位置は小数5けた（約1m）に丸める。線の点は150まで（今までどおり）
//   返す形（iata・at・source・planes[]・planes[].trail）は変えない

export const VIEW_TTL = 20_000;        // これより新しい答えはそのまま使う（今までの TTL と同じ）
export const VIEW_STALE_OK = 60_000;   // これより新しければ、待たせずに返して裏で作り直す
export const ACTIVE_MS = 3 * 60_000;   // 見る人のしるしがこれより新しい空港は「だれかが見ている」とみなす

export type ViewPlan = "fresh" | "stale" | "build";
// 置き場の答えの時刻（なければ null）から、見る人の呼び出しでどうするかを決める
export function viewPlan(at: number | null | undefined, now: number, ttl = VIEW_TTL, staleOk = VIEW_STALE_OK): ViewPlan {
  if (at == null || !Number.isFinite(at)) return "build";
  const age = now - at;
  if (age < 0) return "fresh";   // 時計のずれ
  if (age < ttl) return "fresh";
  if (age < staleOk) return "stale";
  return "build";
}

// 記録の処理が置き場を新しくする空港：見る人のしるしが ACTIVE_MS 以内のもの（記録の処理が書いた答えの時刻では数えない。数えると自分で延び続ける）
export function activeAirports(shared: Map<string, { at: number }>, keyOf: (iata: string) => string, iatas: string[], now: number, activeMs = ACTIVE_MS): string[] {
  return iatas.filter((k) => { const e = shared.get(keyOf(k)); return !!e && Number.isFinite(e.at) && now - e.at < activeMs; });
}

const r5 = (x: number) => Math.round(x * 1e5) / 1e5;
// 返す機体の一覧を作る。線は arr・dep だけ、最後の max 点、小数5けた
export function slimPlanes<P extends { id: string; phase: string }>(planes: P[], trails: Map<string, { p: [number, number] }[]>, max = 150): (P & { trail: [number, number][] })[] {
  return planes.map((p) => ({
    ...p,
    trail: p.phase === "arr" || p.phase === "dep" ? (trails.get(p.id) ?? []).slice(-max).map((x) => [r5(x.p[0]), r5(x.p[1])] as [number, number]) : [],
  }));
}
