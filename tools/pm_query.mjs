#!/usr/bin/env node
// PM の読むだけの問い合わせ（.github/workflows/pm-query.yml から呼ぶ）
//   ・tools/pm-queries/ の .sql を1つだけ流す。中身は select か with で始まる1文だけ（流す前に確かめて、違えば断る）
//   ・役割 pm_reader の接続（秘密の設定 PM_READER_URL）で、read only の取引の中で COPY して CSV にする（最大20万行）
//   ・変数は「名前=値」を空白で区切って渡す（例 airline=JL day=2026-11-20）。SQL では :'airline' のように使う
//   ・結果は out/ に書く。データの中身はログに出さない（行数と秒だけ）
//   node tools/pm_query.mjs <ファイル名> [変数]     … 環境変数 PM_READER_URL が要る
//   node tools/pm_query.mjs --check <ファイル名>    … 確かめだけ（つながない）
import { readFileSync, writeFileSync, mkdirSync, existsSync, createWriteStream, appendFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const MAX_ROWS = 200000;
const DIR = new URL("./pm-queries/", import.meta.url).pathname;

// 書く・変える・取引や設定を変える言葉（文字列と名前の引用の外にあれば断る）
const BANNED = [
  "insert", "update", "delete", "merge", "truncate", "alter", "create", "drop", "grant", "revoke", "copy", "call", "do",
  "execute", "prepare", "deallocate", "set", "reset", "commit", "rollback", "begin", "start", "savepoint", "release",
  "abort", "vacuum", "analyze", "cluster", "reindex", "lock", "listen", "notify", "unlisten", "refresh", "comment",
  "security", "import", "load", "discard", "checkpoint", "set_config", "pg_sleep", "dblink", "lo_import", "lo_export",
  "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_terminate_backend", "pg_cancel_backend", "nextval", "setval",
];

export function checkName(name) {
  if (typeof name !== "string" || !/^[a-z0-9][a-z0-9_-]{0,60}\.sql$/.test(name)) return "ファイル名は英小文字・数字・_・- と .sql だけ（フォルダは書かない）";
  if (!existsSync(join(DIR, name))) return `tools/pm-queries/${name} がない`;
  return null;
}

// 文字列・名前の引用・コメントを外した「骨組み」を返す。閉じていなければ null
export function skeleton(sql) {
  let out = "", i = 0;
  while (i < sql.length) {
    const c = sql[i], d = sql[i + 1];
    if (c === "-" && d === "-") { const j = sql.indexOf("\n", i); i = j < 0 ? sql.length : j; out += " "; continue; }
    if (c === "/" && d === "*") {
      let depth = 1, j = i + 2;
      while (j < sql.length && depth > 0) {
        if (sql[j] === "/" && sql[j + 1] === "*") { depth++; j += 2; } else if (sql[j] === "*" && sql[j + 1] === "/") { depth--; j += 2; } else j++;
      }
      if (depth > 0) return null;
      i = j; out += " "; continue;
    }
    if (c === "'" || c === '"') {
      let j = i + 1;
      for (;;) {
        if (j >= sql.length) return null;
        if (sql[j] === c) { if (sql[j + 1] === c) { j += 2; continue; } break; }
        j++;
      }
      out += c === "'" ? " '' " : ' "" '; i = j + 1; continue;
    }
    if (c === "$") {
      const m = /^\$([A-Za-z_][A-Za-z0-9_]*)?\$/.exec(sql.slice(i));
      if (m) { const end = sql.indexOf(m[0], i + m[0].length); if (end < 0) return null; out += " '' "; i = end + m[0].length; continue; }
    }
    out += c; i++;
  }
  return out;
}

// 中身を確かめる。良ければ { ok: true, sql: 末尾の ; を外した文 }、だめなら { ok: false, why }
export function checkSql(sql) {
  if (typeof sql !== "string" || !sql.trim()) return { ok: false, why: "中身が空" };
  if (sql.length > 50000) return { ok: false, why: "長すぎる（5万字まで）" };
  if (sql.includes("\\")) return { ok: false, why: "バックスラッシュ（psql の命令）は使えない" };
  const sk = skeleton(sql);
  if (sk === null) return { ok: false, why: "文字列・引用・コメントが閉じていない" };
  const body = sk.trim().replace(/;\s*$/, "");
  if (body.includes(";")) return { ok: false, why: "文は1つだけ（; で区切った2つ目は流さない）" };
  const first = (/^[A-Za-z_]+/.exec(body) || [""])[0].toLowerCase();
  if (first !== "select" && first !== "with") return { ok: false, why: "select か with で始まる文だけ" };
  const words = new Set((body.toLowerCase().match(/[a-z_][a-z0-9_]*/g) || []));
  const hit = BANNED.filter((w) => words.has(w));
  if (hit.length) return { ok: false, why: `使えない言葉：${hit.join("・")}` };
  let depth = 0;
  for (const ch of body) { if (ch === "(") depth++; else if (ch === ")") { depth--; if (depth < 0) break; } }
  if (depth !== 0) return { ok: false, why: "かっこの数が合わない" };
  // 末尾の ; を外す（文字列の中の ; は残す）
  const cut = sql.replace(/;\s*(--[^\n]*\s*)*$/, "");
  if (skeleton(cut) === null || skeleton(cut).includes(";")) return { ok: false, why: "末尾の ; の外し方が分からない（末尾のコメントを消して）" };
  return { ok: true, sql: cut };
}

// 変数「名前=値 名前=値」を確かめて [名前, 値] の並びにする
export function parseParams(text) {
  const out = [];
  for (const part of String(text || "").trim().split(/\s+/).filter(Boolean)) {
    const m = /^([a-z][a-z0-9_]{0,30})=([A-Za-z0-9_.:+-]{1,40})$/.exec(part);
    if (!m) return { ok: false, why: `変数の形がちがう：${part.slice(0, 50)}（名前=値。値は英数字と _ . : + - だけ・40字まで）` };
    out.push([m[1], m[2]]);
  }
  if (out.length > 10) return { ok: false, why: "変数は10個まで" };
  return { ok: true, params: out };
}

// psql に渡す包み。取引は read only・1文60秒。問い合わせは COPY の中の1つの select になるので、取引の外へは出られない
export function wrap(sql) {
  return [
    "\\set ON_ERROR_STOP on",
    "begin transaction isolation level repeatable read read only;",
    "set local statement_timeout = '60s';",
    "copy (select * from (",
    sql,
    `) pm_q limit ${MAX_ROWS + 1}) to stdout with (format csv, header);`,
    "rollback;",
    "",
  ].join("\n");
}

// CSV の行（引用の中の改行は行にしない）を数え、MAX_ROWS を超えた分を切る
export function capCsv(text) {
  let rows = -1, inq = false, cutAt = -1;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') inq = !inq;
    else if (c === "\n" && !inq) { rows++; if (rows === MAX_ROWS) { cutAt = i + 1; } }
  }
  if (cutAt >= 0 && cutAt < text.length) return { text: text.slice(0, cutAt), rows: MAX_ROWS, cut: true };
  return { text, rows: Math.max(rows, 0), cut: false };
}

async function main() {
  const args = process.argv.slice(2);
  const onlyCheck = args[0] === "--check";
  if (onlyCheck) args.shift();
  const name = args[0] ?? process.env.PM_QUERY ?? "";
  const paramText = args.slice(1).join(" ") || process.env.PM_PARAMS || "";
  const bad = checkName(name);
  if (bad) { console.error("断った：" + bad); process.exit(2); }
  const chk = checkSql(readFileSync(join(DIR, name), "utf8"));
  if (!chk.ok) { console.error("断った：" + chk.why); process.exit(2); }
  const pp = parseParams(paramText);
  if (!pp.ok) { console.error("断った：" + pp.why); process.exit(2); }
  if (onlyCheck) { console.log(`OK ${name}（変数 ${pp.params.length}個）`); return; }
  const url = process.env.PM_READER_URL;
  if (!url) { console.error("秘密の設定 PM_READER_URL がない（docs/pm/report-pm-reader.md の手順）"); process.exit(2); }

  const outDir = "out"; mkdirSync(outDir, { recursive: true });
  const wrapper = join(outDir, ".wrap.sql"); writeFileSync(wrapper, wrap(chk.sql));
  const base = name.replace(/\.sql$/, "") + (pp.params.length ? "_" + pp.params.map(([, v]) => v.replace(/[^A-Za-z0-9_-]/g, "")).join("_") : "");
  const raw = join(outDir, ".raw.csv");
  const t0 = Date.now();
  const vargs = pp.params.flatMap(([k, v]) => ["-v", `${k}=${v}`]);
  const code = await new Promise((res) => {
    const ps = spawn("psql", ["-X", "-q", "-d", url, ...vargs, "-f", wrapper], {
      env: { ...process.env, PGCONNECT_TIMEOUT: "20", PGAPPNAME: "pm_query", PM_READER_URL: "" },
      stdio: ["ignore", "pipe", "pipe"],
    });
    const ws = createWriteStream(raw);
    ps.stdout.pipe(ws);
    ps.stderr.on("data", (d) => process.stderr.write(String(d).replaceAll(url, "<PM_READER_URL>")));
    let n = 0, rc = 0; const done = () => { if (++n === 2) res(rc); };
    ws.on("finish", done);
    ps.on("close", (c) => { rc = c; done(); });
  });
  const sec = ((Date.now() - t0) / 1000).toFixed(1);
  if (code !== 0) { console.error(`psql が止まった（終わりの番号 ${code}・${sec}秒）`); process.exit(1); }
  const capped = capCsv(readFileSync(raw, "utf8"));
  const file = join(outDir, base + ".csv");
  writeFileSync(file, capped.text); writeFileSync(raw, "");
  const line = `${name}：${capped.rows}行・${sec}秒${capped.cut ? `（${MAX_ROWS}行で切った。条件を狭めて分けて流す）` : ""}`;
  console.log(line);
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, `- ${line}\n`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) await main();
