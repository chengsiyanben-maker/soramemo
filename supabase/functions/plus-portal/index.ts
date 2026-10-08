// POST /functions/v1/plus-portal → { url }（Stripe のお客さまポータル：支払い方法の変更・解約）
import { admin, CORS, json, rateOk, SITE_URL, stripe, userFrom } from "../_shared/plus.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const user = await userFrom(req);
  if (!user) return json({ error: "ログインしてください。" }, 401);
  if (!(await rateOk("plus-portal:" + user.id, 10, 600))) return json({ error: "短い時間に何度も操作されています。少し待ってから試してください。" }, 429);
  const { data: cur } = await admin.from("subscriptions").select("provider_customer").eq("user_id", user.id).maybeSingle();
  if (!cur?.provider_customer) return json({ error: "そらメモ＋の申し込みが見つかりません。" }, 404);
  try {
    const portal = await stripe.billingPortal.sessions.create({ customer: cur.provider_customer, return_url: SITE_URL, locale: "ja" });
    return json({ url: portal.url });
  } catch (e) {
    console.error(e);
    return json({ error: "管理画面を開けませんでした。" }, 500);
  }
});
