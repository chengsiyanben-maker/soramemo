// 配る用のファイルを作る：src/ の読みやすい原本から、説明文や空白を省いて縮めた web/ の版を作る。
//   cd tools && npm install terser@5 csso@5 && cd .. && node tools/build.mjs
// 関数や変数の名前は変えない（テストや運営画面から呼ぶため。toplevel の名前は短くしない）。
import { readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { minify } from "terser";
import { minify as cssMinify } from "csso";

let FONT_FILE = null;
const files = ["index.html"];   // 運営コンソール（ops-console/）は公開しないので、ここでは作らない
for (const f of files) {
  const raw = readFileSync(new URL(`../src/${f}`, import.meta.url), "utf8");
  // 版の番号：原本の中身から自動で付ける（設定の画面と、運営に届くエラーに出る）
  const APP_VER = createHash("sha256").update(raw).digest("hex").slice(0, 8);
  const src = raw.replace(/const APP_VERSION = "([^"+]+)";/, (m, v) => `const APP_VERSION = "${v}+${APP_VER}";`);
  if (f === "index.html") console.log(`版の番号: ${src.match(/const APP_VERSION = "([^"]+)"/)[1]}`);
  let out = src;
  // CSS
  out = out.replace(/<style>([\s\S]*?)<\/style>/g, (_, css) => `<style>${cssMinify(css).css}</style>`);
  // JS（<script src> 以外の、中身のある script）
  const scripts = [...out.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  for (const m of scripts) {
    const r = await minify(m[1], { compress: { passes: 2 }, mangle: { toplevel: false }, format: { comments: false } });
    out = out.replace(m[0], `<script>${r.code}</script>`);
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
    const name = execFileSync("python3", [new URL("./build_font.py", import.meta.url).pathname, list, fontDir], { encoding: "utf8" }).trim();
    const face = `@font-face{font-family:"Shippori Mincho";src:url(fonts/${name}) format("woff2");font-weight:500 900;font-display:swap}`;
    out = out.replace(/<link href="https:\/\/fonts\.googleapis\.com\/css2[^>]*>/, `<link rel="preload" href="fonts/${name}" as="font" type="font/woff2" crossorigin><style>${face}</style>`);
    out = out.replace(/<link rel="preconnect" href="https:\/\/fonts\.(googleapis|gstatic)\.com"[^>]*>/g, "");
    FONT_FILE = name;
    console.log(`fonts/${name}: ${chars.size}文字 ${(readFileSync(join(fontDir, name)).length / 1024).toFixed(0)}KB`);
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
    "connect-src 'self' https://*.supabase.co https://challenges.cloudflare.com",
    "manifest-src 'self'", "worker-src 'self'", "base-uri 'none'", "form-action 'none'", "object-src 'none'",
  ].join("; ");
  out = out.replace(/<meta charset="utf-8">/, `<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${csp}">`);
  writeFileSync(new URL(`../web/${f}`, import.meta.url), out);
  const kb = (b) => (b / 1024).toFixed(0) + "KB";
  console.log(`${f}: ${kb(Buffer.byteLength(src))} → ${kb(Buffer.byteLength(out))}（圧縮配信 ${kb(gzipSync(src).length)} → ${kb(gzipSync(out).length)}）`);
}

// サービスワーカー：配る用の中身から版の番号を作って埋め込む（中身が変わると、利用者の端末の保存も入れ替わる）
{
  const page = readFileSync(new URL("../web/index.html", import.meta.url));
  const ver = createHash("sha256").update(page).update(readFileSync(new URL("../web/config.js", import.meta.url))).digest("hex").slice(0, 10);
  const sw = readFileSync(new URL("../src/sw.js", import.meta.url), "utf8").replace("__BUILD__", ver).replace('"./tokushoho.html"]', `"./tokushoho.html"${FONT_FILE ? `, "./fonts/${FONT_FILE}"` : ""}]`);
  writeFileSync(new URL("../web/sw.js", import.meta.url), sw);
  console.log(`sw.js: 版 ${ver}`);
}
