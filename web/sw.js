// そらメモのサービスワーカー（オフラインでも開けるようにする）
// ・アプリ本体と設定（HTML・config.js）は最新版を優先し、圏外のときだけ保存した版を使う（更新がすぐ届くように）
// ・アイコンや、版の番号が付いた外部の部品・フォントは、保存した版を使う
// ・サーバー（Supabase）などとの通信には手を出さない（失敗は失敗としてアプリに伝える）
const CACHE = "soramemo-d337b1e7a7";   // 配る用を作るとき（tools/build.mjs）に中身から自動で付く
const CORE = ["./", "./index.html", "./config.js", "./manifest.webmanifest", "./icon.svg", "./icon-192.png", "./icon-512.png", "./privacy.html", "./terms.html", "./tokushoho.html", "./fonts/mincho-01eb19316e.woff2"];
const CDN = ["https://cdn.jsdelivr.net/", "https://fonts.googleapis.com/", "https://fonts.gstatic.com/"];

self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE))); self.skipWaiting(); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

async function networkFirst(req, fallback) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    return (await cache.match(req, { ignoreSearch: true })) || (fallback && (await cache.match(fallback))) || Response.error();
  }
}
async function cacheFirst(req) {
  const cache = await caches.open(CACHE), hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res.ok || res.type === "opaque") cache.put(req, res.clone());
  return res;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    const isPage = req.mode === "navigate" || /\.(html|js|webmanifest)$/.test(url.pathname) || url.pathname.endsWith("/");
    e.respondWith(isPage ? networkFirst(req, req.mode === "navigate" ? "./index.html" : null) : cacheFirst(req));
    return;
  }
  if (CDN.some((p) => req.url.startsWith(p))) e.respondWith(cacheFirst(req));
  // それ以外（Supabase など）はそのまま通す
});
