#!/usr/bin/env node
// データベースのSQL（supabase/migrations）の番号を管理する。
//   番号の形：日付8桁＋通し番号6桁（例 20261024000084）。通し番号は日付が変わっても増やし続ける（ファイル名の順＝流す順）。
//
//   node tools/migrations.mjs next 名前           … 次の番号のファイル名を出す（例：20261024000085_名前.sql）
//   node tools/migrations.mjs check               … 番号の重なり・形の誤りを調べる（テストで使う）
//   node tools/migrations.mjs rebase [origin/main] … ブランチで足したSQLのうち、本番側の最新より前の番号のものを、最新の後ろに付け直す
//                                                    （反映の前に使う。ブランチを作ってから main に別のSQLが入ったときに必要）
//
// 本番に流すときは supabase db push --include-all を使うので、付け直しを忘れても止まらないが、
// 流す順番がファイル名の順と変わるので、反映の前に rebase で付け直しておく。
import { readdirSync } from "node:fs";
import { execSync } from "node:child_process";
import { join } from "node:path";

const DIR = new URL("../supabase/migrations/", import.meta.url).pathname;
const RE = /^(\d{8})(\d{6})_[^/]+\.sql$/;
const files = () => readdirSync(DIR).filter((f) => f.endsWith(".sql")).sort();
const ver = (f) => f.slice(0, 14);
const seq = (f) => Number(f.slice(8, 14));
const today = () => new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 10).replaceAll("-", "");
const nextName = (list, name) => `${today()}${String(Math.max(0, ...list.map(seq)) + 1).padStart(6, "0")}_${name}.sql`;

const [cmd, arg] = process.argv.slice(2);
if (cmd === "next") {
  if (!arg || !/^[a-z0-9_]+$/.test(arg)) { console.error("名前は英小文字・数字・_ で（例：secret_fields）"); process.exit(1); }
  console.log(nextName(files(), arg));
} else if (cmd === "check") {
  const list = files(), bad = [];
  for (const f of list) if (!RE.test(f)) bad.push(`形がちがう：${f}`);
  const seen = new Map();
  for (const f of list) { const v = ver(f); if (seen.has(v)) bad.push(`番号が重なっている：${seen.get(v)} と ${f}`); seen.set(v, f); }
  const sq = new Map();
  for (const f of list) { const s = seq(f); if (sq.has(s)) bad.push(`通し番号が重なっている：${sq.get(s)} と ${f}`); sq.set(s, f); }
  if (bad.length) { console.error(bad.join("\n")); process.exit(1); }
  console.log(`SQL ${list.length}件：番号の重なりなし`);
} else if (cmd === "rebase") {
  const base = arg || "origin/main";
  const baseList = execSync(`git ls-tree --name-only ${base} supabase/migrations/`, { encoding: "utf8" }).split("\n").filter(Boolean).map((p) => p.split("/").pop()).filter((f) => f.endsWith(".sql"));
  const baseSet = new Set(baseList), baseMax = Math.max(0, ...baseList.map(seq));
  const mine = files().filter((f) => !baseSet.has(f));
  const late = mine.filter((f) => seq(f) <= baseMax);
  if (!late.length) { console.log(`付け直すものはありません（${base} の最新は ${String(baseMax).padStart(6, "0")}）`); process.exit(0); }
  let n = Math.max(baseMax, ...mine.filter((f) => seq(f) > baseMax).map(seq));
  for (const f of late) {
    n++;
    const to = `${today()}${String(n).padStart(6, "0")}${f.slice(14)}`;
    execSync(`git mv ${JSON.stringify(join(DIR, f))} ${JSON.stringify(join(DIR, to))}`);
    console.log(`${f} → ${to}`);
  }
} else {
  console.log("使い方：node tools/migrations.mjs next 名前 | check | rebase [origin/main]");
  process.exit(cmd ? 1 : 0);
}
