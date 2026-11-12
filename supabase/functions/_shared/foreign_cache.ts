// airport-foreign の置き場（edge_cache）の答えを、そのまま使うか・作るか・代わりに出すかを決める（取得とは分けてテストしやすくしている）
//   fresh：ttl 以内なので、そのまま使う（位置を読まず、経路のデータにも問い合わせない）
//   stale：今回作れなかった（経路が取れない・エラー）ので、10分以内の古い答えを代わりに出す
//   build：作った答えを使う（置き場の答えがない・古すぎる、または今回ちゃんと作れた）
import type { Entry } from "./edge_cache.ts";
export const STALE_MAX = 10 * 60_000;
export function pickForeign(shared: Entry | undefined, buildError: string | null, ttl: number, now = Date.now()): { use: "fresh" | "stale" | "build" } {
  const ok = !!shared && Number.isFinite(shared.at) && shared.v != null && typeof shared.v === "object";
  if (ok && now - shared!.at < ttl) return { use: "fresh" };
  if (buildError && ok && now - shared!.at < STALE_MAX) return { use: "stale" };
  return { use: "build" };
}
