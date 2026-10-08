// そらメモ＋（Stripe）共通
import Stripe from "npm:stripe@23.0.0";
import { createClient } from "npm:@supabase/supabase-js@2.117.2";

// Stripe の鍵がまだ登録されていなくても起動できるようにする（アカウント削除はこの部品を共有している）。
// 鍵がないあいだ、Stripe への問い合わせは失敗するが、そらメモ＋を使う前に鍵を登録する前提
export const STRIPE_READY = !!Deno.env.get("STRIPE_SECRET_KEY");
export const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") || "sk_test_not_configured", { httpClient: Stripe.createFetchHttpClient() });
export const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
export const SITE_URL = Deno.env.get("SITE_URL") ?? "";          // 例: https://<ユーザー名>.github.io/<リポジトリ名>/
export const PRICE_ID = Deno.env.get("STRIPE_PRICE_ID") ?? "";   // Stripe で作った「月額500円」の価格ID
export const PRICE_ID_YEAR = Deno.env.get("STRIPE_PRICE_ID_YEAR") ?? "";   // 年額プラン（年4,800円）。未登録なら年額は「準備中」

export const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

export async function userFrom(req: Request) {
  const jwt = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  const { data, error } = await admin.auth.getUser(jwt);
  return error || !data?.user ? null : data.user;
}

// Stripe のサブスクリプションを subscriptions 表に反映する
export async function saveSubscription(userId: string, sub: Stripe.Subscription) {
  const end = (sub as unknown as { current_period_end?: number }).current_period_end
    ?? sub.items?.data?.[0]?.current_period_end;
  const { error } = await admin.from("subscriptions").upsert({
    user_id: userId,
    status: sub.status,
    current_period_end: end ? new Date(end * 1000).toISOString() : null,
    provider: "stripe",
    provider_customer: typeof sub.customer === "string" ? sub.customer : sub.customer.id,
    provider_subscription: sub.id,
    updated_at: new Date().toISOString(),
  });
  if (error) throw error;
}

// 回数制限（データベースで数える。超えたら false）
export async function rateOk(key: string, limit: number, windowSec: number): Promise<boolean> {
  const { data, error } = await admin.rpc("rl_check", { p_key: key, p_limit: limit, p_window_sec: windowSec });
  return error ? true : data !== false;
}
