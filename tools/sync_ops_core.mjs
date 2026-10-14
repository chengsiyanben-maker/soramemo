// src/index.html の「運用の判定の中心」（// <ops-core> 〜 // </ops-core> の部分）を、サーバーの関数でも使えるように
// supabase/functions/_shared/ops_core.js に写す。画面とサーバーで、判定の仕方がずれないようにするため。
//   node tools/sync_ops_core.mjs          （写す）
//   node tools/sync_ops_core.mjs --check  （写したものが古くないか確かめる。古ければ失敗する）
import { readFileSync, writeFileSync } from "node:fs";
import { opsCoreParts } from "./ops_core_parts.mjs";

const parts = opsCoreParts();
const out = `// 自動で作るファイル：src/index.html の <ops-core> の部分を tools/sync_ops_core.mjs で写したもの。ここは直接直さない。
// deno-lint-ignore-file
// @ts-nocheck
const opsDef = () => { throw new Error("サーバーでは空港の定義を引数で渡す"); };
${parts.join("\n")}
export { OPS_AIRPORTS, windEstimate, observeOps, obsText, runwaysOf };
`;
const path = new URL("../supabase/functions/_shared/ops_core.js", import.meta.url);
if (process.argv.includes("--check")) {
  let cur = ""; try { cur = readFileSync(path, "utf8"); } catch {}
  if (cur !== out) { console.error("supabase/functions/_shared/ops_core.js が古い。node tools/sync_ops_core.mjs で写し直す"); process.exit(1); }
  console.log("ops_core.js は最新");
} else { writeFileSync(path, out); console.log("ops_core.js を写した"); }
