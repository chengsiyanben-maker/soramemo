// そらメモのサービスワーカー（オフラインでも開けるようにする）
// ・アプリ本体と設定（HTML・config.js）は最新版を優先し、圏外のときだけ保存した版を使う（更新がすぐ届くように）
// ・アイコンや、版の番号が付いた外部の部品・フォントは、保存した版を使う
// ・サーバー（Supabase）などとの通信には手を出さない（失敗は失敗としてアプリに伝える）
const CACHE = "soramemo-35f1607c11";   // 配る用を作るとき（tools/build.mjs）に中身から自動で付く
const CORE = ["./", "./index.html", "./config.js", "./manifest.webmanifest", "./icon.svg", "./icon-192.png", "./icon-512.png", "./privacy.html", "./terms.html", "./tokushoho.html", "./fonts/mincho0-47aa354c3e.woff2", "./fonts/dot0-91d88f4598.woff2", "./fonts/sign0-046a5a18b8.woff2"];
// フォント（fonts/ の中身はファイル名に中身の印が付いている）は、版が変わっても消さない別の保存場所に置く（公開のたびに取り直さない）
const FONTS = "soramemo-fonts";
const CDN = ["https://cdn.jsdelivr.net/", "https://fonts.googleapis.com/", "https://fonts.gstatic.com/"];

const isFont = (u) => u.origin === location.origin && /\/fonts\/[^/]+\.woff2$/.test(u.pathname);
self.addEventListener("install", (e) => {
  e.waitUntil(Promise.all([caches.open(CACHE), caches.open(FONTS)]).then(async ([c, f]) => {
    const fonts = CORE.filter((p) => p.startsWith("./fonts/"));
    await c.addAll(CORE.filter((p) => !p.startsWith("./fonts/")));
    for (const p of fonts) if (!(await f.match(p))) await f.add(p);
  }));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE && k !== FONTS).map((k) => caches.delete(k))))
    // 古いフォントがたまりすぎたら一度空にする（使うものはまた保存される）
    .then(() => caches.open(FONTS)).then(async (f) => { if ((await f.keys()).length > 80) await caches.delete(FONTS); })
    .then(() => self.clients.claim()));
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
async function cacheFirst(req, name = CACHE) {
  const cache = await caches.open(name), hit = await cache.match(req);
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
    e.respondWith(isPage ? networkFirst(req, req.mode === "navigate" ? "./index.html" : null) : cacheFirst(req, isFont(url) ? FONTS : CACHE));
    return;
  }
  if (CDN.some((p) => req.url.startsWith(p))) e.respondWith(cacheFirst(req));
  // それ以外（Supabase など）はそのまま通す
});

// スマホへの通知（遅れ・ダイバートの推定、特別塗装機）。サーバーの flight-watch・airport-traffic から届く
self.addEventListener("push", (e) => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.title || "そらメモ", { body: d.body || "", tag: d.tag || "soramemo", icon: "icon-192.png", badge: "icon-192.png", data: { url: typeof d.url === "string" && (d.url.startsWith("./#ops") || /^\.\/#special-[A-Z0-9-]{2,10}$/.test(d.url)) ? d.url : "./#ops" } }));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    for (const c of cs) if ("focus" in c) { c.postMessage({ type: "open-ops", url: e.notification.data && e.notification.data.url }); return c.focus(); }
    return self.clients.openWindow((e.notification.data && e.notification.data.url) || "./");
  }));
});
