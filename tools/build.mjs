// 配る用のファイルを作る：src/ の読みやすい原本から、説明文や空白を省いて縮めた web/ の版を作る。
//   cd tools && npm install terser@5 csso@5 && cd .. && node tools/build.mjs
// 関数や変数の名前は変えない（テストや運営画面から呼ぶため。toplevel の名前は短くしない）。
import { readFileSync, writeFileSync } from "node:fs";
// まだ始まっていない塗装（from が今日より後）は入れない。普通の塗装で飛んでいる機体を、その名前で出さないため
const notYet = (rest) => { const f = rest.match(/from:\s*"(\d{4}-\d{2}-\d{2})"/); return !!f && f[1] > new Date().toISOString().slice(0, 10); };
// 特別塗装機の一覧（アライアンス塗装は除く）。期間が終わったものも、乗ったときの記録として名前は残す
function liveryNames() {
  const ts = readFileSync(new URL("../supabase/functions/_shared/liveries.ts", import.meta.url), "utf8"), m = {};
  for (const x of ts.matchAll(/\{\s*reg:\s*"([A-Z0-9-]+)",\s*name:\s*"([^"]+)"([^}]*)\}/g)) if (!/kind:\s*"alliance"/.test(x[3]) && !notYet(x[3])) m[x[1]] = x[2];
  return JSON.stringify(m);
}
// 特別塗装機の航空会社（図鑑で分ける）
function liveryAirlines() {
  const ts = readFileSync(new URL("../supabase/functions/_shared/liveries.ts", import.meta.url), "utf8"), m = {};
  for (const x of ts.matchAll(/\{\s*reg:\s*"([A-Z0-9-]+)",\s*name:\s*"[^"]+",\s*airline:\s*"([^"]+)"([^}]*)\}/g)) if (!/kind:\s*"alliance"/.test(x[3]) && !notYet(x[3])) m[x[1]] = x[2];
  return JSON.stringify(m);
}
import { gzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { minify } from "terser";
import { minify as cssMinify } from "csso";

let FONT_FILES = [];
import { opsCoreParts } from "./ops_core_parts.mjs";
const files = ["index.html", "now.html"];   // 運営コンソール（ops-console/）は公開しないので、ここでは作らない。now.html は公開ページ「空港のいま」
for (const f of files) {
  const raw = readFileSync(new URL(`../src/${f}`, import.meta.url), "utf8");
  // 版の番号：原本の中身から自動で付ける（設定の画面と、運営に届くエラーに出る）
  const APP_VER = createHash("sha256").update(raw).digest("hex").slice(0, 8);
  const src = raw.replace(/const APP_VERSION = "([^"+]+)";/, (m, v) => `const APP_VERSION = "${v}+${APP_VER}";`);
  if (f === "index.html") console.log(`版の番号: ${src.match(/const APP_VERSION = "([^"]+)"/)[1]}`);
  // 「空港のいま」には、アプリ本体と同じ運用の判定の中心を差し込む（判定の仕方がずれないように）
  let out = f === "now.html" ? src.replace("/*@OPS_CORE@*/", () => opsCoreParts().join("\n")) : src;
  out = out.replace("/*@LIVERIES@*/{}", () => liveryNames());   // 特別塗装機の一覧（登録記号 → 名前）を、サーバーの liveries.ts からアプリに入れる（乗った機体の図鑑の印）
  out = out.replace("/*@LIVERY_AIR@*/{}", () => liveryAirlines());   // 特別塗装機の航空会社（特別塗装機の図鑑で分ける）
  // CSS
  out = out.replace(/<style>([\s\S]*?)<\/style>/g, (_, css) => `<style>${cssMinify(css).css}</style>`);
  // JS（<script src> 以外の、中身のある script）
  const scripts = [...out.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  for (const m of scripts) {
    const r = await minify(m[1], { compress: { passes: 2 }, mangle: { toplevel: false }, format: { comments: false } });
    out = out.replace(m[0], () => `<script>${r.code}</script>`);   // 関数で渡す（縮めたコードの「$`」などを置き換えの記号と取り違えないように）
  }
  // HTMLのコメントと、タグの間の余分な空白
  out = out.replace(/<!--(?!\[)[\s\S]*?-->/g, "").replace(/>\s*\n\s*</g, "><");
  // 明朝体：Google Fonts をやめ、このファイルに出てくる文字（説明文を省いた後）と英数字・記号だけを抜き出したフォントを自前で配る。
  // 文字が増えても自動で作り直される。利用者の端末は Google に問い合わせない
  if (f === "index.html") {
    const chars = new Set([...out].filter((ch) => ch.codePointAt(0) > 0x7f));
    for (let c = 0x20; c < 0x7f; c++) chars.add(String.fromCharCode(c));
    const dir = mkdtempSync(join(tmpdir(), "font-")), list = join(dir, "chars.txt");
    writeFileSync(list, [...chars].join(""));
    const fontDir = new URL("../web/fonts/", import.meta.url).pathname;
    // 明朝体（見出し・印）と、ドット文字（案内板の数字・空港コード）の2つを作る
    // 文字の多い漢字は小分けにし（unicode-range）、画面に出た文字を含むファイルだけが読まれるようにする
    const make = (kind) => execFileSync("python3", [new URL("./build_font.py", import.meta.url).pathname, list, fontDir, kind], { encoding: "utf8" })
      .trim().split("\n").map((l) => l.split("\t"));
    const mincho = make("mincho"), dot = make("dot");
    const face = mincho.map(([n, r]) => `@font-face{font-family:"Shippori Mincho";src:url(fonts/${n}) format("woff2");font-weight:500 900;font-display:swap;unicode-range:${r}}`).join("")
      + dot.map(([n, r]) => `@font-face{font-family:"DotGothic16";src:url(fonts/${n}) format("woff2");font-weight:400;font-display:swap;unicode-range:${r}}`).join("");
    // 先読みは、見出しにすぐ出る明朝体の「英数字・かな」のファイルだけ
    out = out.replace(/<link href="https:\/\/fonts\.googleapis\.com\/css2[^>]*>/, `<link rel="preload" href="fonts/${mincho[0][0]}" as="font" type="font/woff2" crossorigin><style>${face}</style>`);
    out = out.replace(/<link rel="preconnect" href="https:\/\/fonts\.(googleapis|gstatic)\.com"[^>]*>/g, "");
    FONT_FILES = [mincho[0][0], dot[0][0]];   // オフライン用に最初から保存するのは「英数字・かな」だけ。漢字のファイルは使ったときに保存される
    const total = (fs) => fs.reduce((a, [n]) => a + readFileSync(join(fontDir, n)).length, 0) / 1024;
    console.log(`フォント：${chars.size}文字　明朝体 ${mincho.length}ファイル 計${total(mincho).toFixed(0)}KB（英数字・かな ${total(mincho.slice(0, 1)).toFixed(0)}KB）　ドット ${dot.length}ファイル 計${total(dot).toFixed(0)}KB（英数字・かな ${total(dot.slice(0, 1)).toFixed(0)}KB）`);
  }
  // ページの防御設定（CSP）：このファイルに書いたスクリプト（ハッシュで指定）と、決まった配信元のものだけを動かす。
  // 外から差し込まれたスクリプトや、HTMLに直接書いた onclick などは動かない。
  const hashes = [...out.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => `'sha256-${createHash("sha256").update(m[1], "utf8").digest("base64")}'`);
  const csp = [
    "default-src 'self'",
    `script-src 'self' ${hashes.join(" ")} https://cdn.jsdelivr.net https://challenges.cloudflare.com`,
    "frame-src https://challenges.cloudflare.com",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "font-src 'self'",
    "img-src 'self' data: blob: https://cyberjapandata.gsi.go.jp",
    // 運用タブの地図の下地（国土地理院のベクトルタイル）を読み、描画の部品（MapLibre）が裏で動かす処理（blob の worker）を許す
    "connect-src 'self' https://*.supabase.co https://challenges.cloudflare.com https://cyberjapandata.gsi.go.jp https://gsi-cyberjapan.github.io",
    "manifest-src 'self'", "worker-src 'self' blob:", "base-uri 'none'", "form-action 'none'", "object-src 'none'",
  ].join("; ");
  out = out.replace(/<meta charset="utf-8">/, `<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}">`);
  writeFileSync(new URL(`../web/${f}`, import.meta.url), out);
  const kb = (b) => (b / 1024).toFixed(0) + "KB";
  console.log(`${f}: ${kb(Buffer.byteLength(src))} → ${kb(Buffer.byteLength(out))}（圧縮配信 ${kb(gzipSync(src).length)} → ${kb(gzipSync(out).length)}）`);
}

// 「空港のいま」の空港ごとのページ（now-hnd.html など）：共有したときに空港名と空港ごとの画像（web/og/）が出るよう、題名と OGP だけ変えて写す
{
  const base = readFileSync(new URL("../web/now.html", import.meta.url), "utf8");
  const aps = JSON.parse(execFileSync("node", ["--input-type=module", "-e",
    `import { OPS_AIRPORTS } from ${JSON.stringify(new URL("../supabase/functions/_shared/ops_core.js", import.meta.url).href)}; console.log(JSON.stringify(Object.values(OPS_AIRPORTS).map(d => [d.iata, d.name])));`], { encoding: "utf8" }));
  const full = (k, n) => k === "KIX" ? "関西空港" : k === "NGO" ? "中部空港（セントレア）" : `${n}空港`;
  for (const [k, n] of aps) {
    const page = `now-${k.toLowerCase()}.html`, t = `${full(k, n)}のいま｜そらメモ（非公式）`;
    const desc = `${full(k, n)}のいまの滑走路の使い方（運用）を、風と実際に飛んでいる機体から推定します。ログインは不要です（非公式）。`;
    const out = base.replace('data-ap="HND"', `data-ap="${k}"`)
      .replace(/<title>[^<]*<\/title>/, `<title>${t}</title>`)
      .replace(/(<meta name="description" content=")[^"]*/, `$1${desc}`)
      .replace(/(<meta property="og:title" content=")[^"]*/, `$1${t}`)
      .replace(/(<meta property="og:description" content=")[^"]*/, `$1${desc}`)
      .replace(/(<meta property="og:url" content=")[^"]*/, `$1https://soramemo.jp/${page}`)
      .replace(/(<meta property="og:image" content=")[^"]*/, `$1https://soramemo.jp/og/${k}.png`);
    writeFileSync(new URL(`../web/${page}`, import.meta.url), out);
  }
  console.log(`空港のいま：${aps.length}空港のページ`);
  // 検索エンジン向けの案内（ページの一覧）
  const urls = ["", "now.html", ...aps.map(([k]) => `now-${k.toLowerCase()}.html`), "privacy.html", "terms.html", "tokushoho.html"];
  writeFileSync(new URL("../web/sitemap.xml", import.meta.url), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((u) => `  <url><loc>https://soramemo.jp/${u}</loc></url>`).join("\n")}\n</urlset>\n`);
}

// サービスワーカー：配る用の中身から版の番号を作って埋め込む（中身が変わると、利用者の端末の保存も入れ替わる）
{
  const page = readFileSync(new URL("../web/index.html", import.meta.url));
  const ver = createHash("sha256").update(page).update(readFileSync(new URL("../web/config.js", import.meta.url))).digest("hex").slice(0, 10);
  const sw = readFileSync(new URL("../src/sw.js", import.meta.url), "utf8").replace("__BUILD__", ver).replace('"./tokushoho.html"]', `"./tokushoho.html"${FONT_FILES.map((n) => `, "./fonts/${n}"`).join("")}]`);
  writeFileSync(new URL("../web/sw.js", import.meta.url), sw);
  console.log(`sw.js: 版 ${ver}`);
}
