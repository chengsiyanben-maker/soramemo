// src/index.html の「運用の判定の中心」（// <ops-core> 〜 // </ops-core> の部分）を取り出す。
// サーバーの _shared/ops_core.js（tools/sync_ops_core.mjs）と、公開ページ「空港のいま」（now.html。tools/build.mjs）で使う
import { readFileSync } from "node:fs";
export function opsCoreParts() {
  const src = readFileSync(new URL("../src/index.html", import.meta.url), "utf8");
  const parts = [...src.matchAll(/\/\/ <ops-core>[^\n]*\n([\s\S]*?)\/\/ <\/ops-core>\n/g)].map((m) => m[1]);
  if (parts.length !== 2) throw new Error(`<ops-core> の部分が2つ見つからない（${parts.length}）`);
  return parts;
}
