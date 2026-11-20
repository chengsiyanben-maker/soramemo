import { assertEquals } from "jsr:@std/assert@1";
import { adsbImHeaders, adsbLolHeaders, backoffUntil, userAgent } from "../functions/_shared/adsblol.ts";

const env = (o: Record<string, string>) => (k: string) => o[k];

Deno.test("名乗りに連絡先（https://soramemo.jp/）が入る", () => {
  assertEquals(userAgent("airport-traffic"), "soramemo (airport-traffic; https://soramemo.jp/)");
});

Deno.test("鍵がなければ名乗りだけ（今までどおり動く）", () => {
  assertEquals(adsbLolHeaders("flight-live", env({})), { "User-Agent": "soramemo (flight-live; https://soramemo.jp/)" });
  assertEquals(Object.keys(adsbLolHeaders("x", env({ ADSBLOL_API_KEY: "  " }))), ["User-Agent"]);
});

Deno.test("鍵があれば既定のヘッダー名で付ける", () => {
  assertEquals(adsbLolHeaders("x", env({ ADSBLOL_API_KEY: " k123 " }))["api-auth"], "k123");
});

Deno.test("ヘッダー名は秘密の設定で変えられる・おかしな名前は既定に戻す", () => {
  assertEquals(adsbLolHeaders("x", env({ ADSBLOL_API_KEY: "k", ADSBLOL_KEY_HEADER: "X-Api-Key" }))["X-Api-Key"], "k");
  const h = adsbLolHeaders("x", env({ ADSBLOL_API_KEY: "k", ADSBLOL_KEY_HEADER: "bad header\n" }));
  assertEquals(h["api-auth"], "k");
  assertEquals(Object.keys(h).length, 2);
});

Deno.test("adsb.im には鍵を付けない", () => {
  assertEquals(adsbImHeaders("airport-foreign"), { "Content-Type": "application/json", "User-Agent": "soramemo (airport-foreign; https://soramemo.jp/)" });
});

Deno.test("Retry-After を守る（秒・なし・長すぎ）", () => {
  assertEquals(backoffUntil(1000, "10"), 11_000);
  assertEquals(backoffUntil(1000, null), 31_000);
  assertEquals(backoffUntil(1000, "abc"), 31_000);
  assertEquals(backoffUntil(1000, "99999"), 301_000);
  assertEquals(backoffUntil(1000, "0"), 1000);
});
