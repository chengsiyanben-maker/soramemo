// adsb.lol・adsb.im に問い合わせるときの名乗りと鍵（11/21）。
//   adsb.lol の返事（11/6）：鍵があると自分の枠になる（共有の IP は 429 になりやすい）・User-Agent で名乗る・Retry-After を守る。
//   鍵は Supabase の秘密の設定 ADSBLOL_API_KEY に本人が入れる（コードに書かない）。なければ今までどおり鍵なしで動く。
//   ヘッダーの名前は ADSBLOL_KEY_HEADER で変えられる（既定 "api-auth"。adsb.lol の案内で確かめてから入れる）。
//   鍵は api.adsb.lol にだけ付ける（adsb.im は別の運営なので付けない）。
export const CONTACT = "https://soramemo.jp/";

type Env = (k: string) => string | undefined;
const denoEnv: Env = (k) => { try { return Deno.env.get(k); } catch { return undefined; } };

// 例：soramemo (airport-traffic; https://soramemo.jp/)
export function userAgent(tag: string): string {
  return `soramemo (${tag}; ${CONTACT})`;
}

// api.adsb.lol 向けのヘッダー（名乗り＋あれば鍵）
export function adsbLolHeaders(tag: string, env: Env = denoEnv): Record<string, string> {
  const h: Record<string, string> = { "User-Agent": userAgent(tag) };
  const key = (env("ADSBLOL_API_KEY") ?? "").trim();
  if (key) {
    const name = (env("ADSBLOL_KEY_HEADER") ?? "").trim();
    h[/^[A-Za-z0-9-]{1,64}$/.test(name) ? name : "api-auth"] = key;
  }
  return h;
}

// adsb.im（経路の routeset）向け：名乗りだけ
export function adsbImHeaders(tag: string): Record<string, string> {
  return { "Content-Type": "application/json", "User-Agent": userAgent(tag) };
}

// 429・420 を受けたあと、次に問い合わせてよい時刻（Retry-After の秒。なければ既定、長すぎるときは上限）
export function backoffUntil(now: number, retryAfter: string | null, defMs = 30_000, maxMs = 300_000): number {
  const s = Number(retryAfter);
  const ms = retryAfter != null && retryAfter.trim() !== "" && Number.isFinite(s) && s >= 0 ? s * 1000 : defMs;
  return now + Math.min(maxMs, Math.round(ms));
}
