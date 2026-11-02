// そらメモ 試遊版を作る（本番のアプリ web/index.html ＋ ブラウザの中のデータベース）
//   node tools/build.mjs && node tools/build_play.mjs <書き出す先のフォルダ>
//   できるもの：index.html（アプリと試遊用の帯）・play-db.txt（見本の会社を入れたデータベース。base64）・pglite.wasm / initdb.wasm / pglite-data.txt（base64）
//   本番のサーバーにはつながない。本番のデータは入っていない（見本の利用者と、作り物の便の記録だけ）
import fs from "node:fs";
import path from "node:path";
import { buildDb } from "./play/seed.mjs";

const ROOT = new URL("../", import.meta.url).pathname;
const out = path.resolve(process.argv[2] || "play-out");
fs.mkdirSync(out, { recursive: true });

// 1. データベース
const t0 = Date.now();
const db = await buildDb();
await db.exec(`insert into play.state values ('built', (now() at time zone 'Asia/Tokyo')::date::text) on conflict (k) do update set v = excluded.v`);
const blob = await db.dumpDataDir("gzip");
fs.writeFileSync(path.join(out, "play-db.txt"), Buffer.from(await blob.arrayBuffer()).toString("base64"));
await db.close();
const PGD = ROOT + "tests/sql/node_modules/@electric-sql/pglite/dist/";
for (const f of ["pglite.wasm", "initdb.wasm"]) fs.copyFileSync(PGD + f, path.join(out, f));
fs.writeFileSync(path.join(out, "pglite-data.txt"), fs.readFileSync(PGD + "pglite.data").toString("base64"));
console.log("データベース", Math.round(blob.size / 1024) + "KB", (Date.now() - t0) + "ms");

// 2. アプリ
let html = fs.readFileSync(ROOT + "web/index.html", "utf8");
html = html.replace(/<meta http-equiv="Content-Security-Policy" content="[^"]*">/, "");   // 試遊版の置き場所の決まりに任せる（中のスクリプトを書き足すため）
html = html.replace("<title>そらメモ</title>", "<title>そらメモ試遊版</title>").replace(/<link rel="manifest"[^>]*>/, "").replace(/<link rel="apple-touch-icon"[^>]*>/, "");
// 文字の部品は data: で埋め込む
html = html.replace(/url\(fonts\/([a-z0-9-]+\.woff2)\)/g, (_, f) => `url(data:font/woff2;base64,${fs.readFileSync(ROOT + "web/fonts/" + f).toString("base64")})`);
const cfg = `<script>window.SORAMEMO_CONFIG = { supabaseUrl: "https://play.invalid", supabaseAnonKey: "play", gameReleased: true, play: true };</script>`;
if (!html.includes('<script src="config.js"></script>')) throw new Error("config.js の読み込みが見つからない");
html = html.replace('<script src="config.js"></script>', cfg + `<script>${fs.readFileSync(ROOT + "tools/play/client.js", "utf8")}</script>`);
// サーバーの部品（supabase-js）は読まず、試遊版の代わりを使う
const before = html.length;
html = html.replace("if(await loadScript(SUPABASE_JS),", "if(window.supabase||await loadScript(SUPABASE_JS),");
if (html.length === before) throw new Error("supabase-js の読み込みが見つからない");
// 試遊用の帯と、読み込み中の幕
const bar = fs.readFileSync(ROOT + "tools/play/bar.html", "utf8");
html = html.replace("</body>", bar + "</body>");
fs.writeFileSync(path.join(out, "index.html"), html);
console.log("アプリ", Math.round(html.length / 1024) + "KB →", out);
