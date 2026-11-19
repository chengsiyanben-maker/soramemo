// iPhone のアプリに入れるファイルを作る（決定事項【11/18】作り方 A：今の web を Capacitor で包む）
//   先に web/ を作る（cd tools && npm ci && cd .. && node tools/build.mjs）。そのあと ios-app で：npm ci && npm run sync
//   web/ の組み立てた版をそのまま www/ に写し、Capacitor の部品（capacitor.js）を1行足すだけ。src/index.html の中身は web と同じ
//   本番の https://soramemo.jp を読み込むだけの形（server.url）にはしない（審査の 4.2・電波がないと何も出ないため）
import fs from "node:fs";
import path from "node:path";

const HERE = new URL(".", import.meta.url).pathname, WEB = path.join(HERE, "../web"), OUT = path.join(HERE, "www");
// 入れないもの：サービスワーカー（アプリの中では使わない）・検索エンジン向け・独自ドメインの設定・公開ページの「空港のいま」と画像の置き場（アプリの画面からは使わない）
const SKIP = new Set(["sw.js", "robots.txt", "sitemap.xml", "CNAME", "og"]);
const skip = (rel) => SKIP.has(rel) || /^now(-[a-z]{3})?\.html$/.test(rel);

if (!fs.existsSync(path.join(WEB, "index.html"))) throw new Error("web/index.html がありません。先に node tools/build.mjs を流してください");
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
for (const ent of fs.readdirSync(WEB, { withFileTypes: true })) {
  if (skip(ent.name)) continue;
  fs.cpSync(path.join(WEB, ent.name), path.join(OUT, ent.name), { recursive: true });
}
// Capacitor の部品（registerPlugin）。config.js より前に読む
const core = path.join(HERE, "node_modules/@capacitor/core/dist/capacitor.js");
if (!fs.existsSync(core)) throw new Error("@capacitor/core がありません。ios-app で npm ci を流してください");
fs.copyFileSync(core, path.join(OUT, "capacitor.js"));
let html = fs.readFileSync(path.join(OUT, "index.html"), "utf8");
const tag = '<script src="config.js"></script>';
if (!html.includes(tag)) throw new Error("config.js の読み込みが見つからない");
html = html.replace(tag, '<script src="capacitor.js"></script>' + tag);
// ホーム画面に追加する案内（manifest）はアプリでは要らない
html = html.replace(/<link rel="manifest"[^>]*>/, "");
fs.writeFileSync(path.join(OUT, "index.html"), html);
const size = (d) => fs.readdirSync(d, { withFileTypes: true }).reduce((s, e) => s + (e.isDirectory() ? size(path.join(d, e.name)) : fs.statSync(path.join(d, e.name)).size), 0);
console.log(`www/ を作りました（${Math.round(size(OUT) / 1024)}KB）`);
