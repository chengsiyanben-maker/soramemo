// POST /functions/v1/plus-checkout { plan: "month" | "year" } → { url }（Stripe の申し込み画面）
import { admin, CORS, json, PRICE_ID, PRICE_ID_YEAR, rateOk, SITE_URL, stripe, userFrom } from "../_shared/plus.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const user = await userFrom(req);
  if (!user) return json({ error: "ログインしてください。" }, 401);
  if (!(await rateOk("plus-checkout:" + user.id, 5, 600))) return json({ error: "短い時間に何度も操作されています。少し待ってから試してください。" }, 429);
  if (!PRICE_ID || !SITE_URL) return json({ error: "サーバーの設定（STRIPE_PRICE_ID / SITE_URL）がありません。" }, 500);
  let plan = "month";
  try { const b = await req.json(); if (b && b.plan === "year") plan = "year"; } catch (_) { /* 本文なしは月額 */ }
  if (plan === "year" && !PRICE_ID_YEAR) return json({ error: "年額プランは準備中です。月額プランをご利用ください。" }, 400);
  const price = plan === "year" ? PRICE_ID_YEAR : PRICE_ID;
  try {
    const { data: cur } = await admin.from("subscriptions").select("provider_customer").eq("user_id", user.id).maybeSingle();
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price, quantity: 1 }],
      success_url: `${SITE_URL}?plus=success`,
      cancel_url: `${SITE_URL}?plus=cancel`,
      client_reference_id: user.id,
      ...(cur?.provider_customer ? { customer: cur.provider_customer } : { customer_email: user.email }),
      subscription_data: { metadata: { user_id: user.id, plan } },
      locale: "ja",
    });
    return json({ url: session.url });
  } catch (e) {
    console.error(e);
    return json({ error: "申し込み画面を作れませんでした。" }, 500);
  }
});
