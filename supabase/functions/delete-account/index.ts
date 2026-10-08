// POST /functions/v1/delete-account  body: { confirm: "削除" }
// 本人のアカウントと、すべての記録（チェックイン・フライト・記録帳・会社・機材・施設・加入情報）を消す。
// そらメモ＋に加入中なら、Stripe の定期支払いを先に止める。各表は auth.users を on delete cascade で参照している。
import { admin, CORS, json, rateOk, STRIPE_READY, stripe, userFrom } from "../_shared/plus.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POSTのみ" }, 405);
  const user = await userFrom(req);
  if (!user) return json({ error: "ログインしてください。" }, 401);
  if (!(await rateOk("delete-account:" + user.id, 3, 3600))) return json({ error: "短い時間に何度も操作されています。少し待ってから試してください。" }, 429);
  let body: { confirm?: string } = {};
  try { body = await req.json(); } catch { /* 空のまま */ }
  if (body.confirm !== "削除") return json({ error: "確認の文字が違います。" }, 400);

  try {
    const { data: sub } = await admin.from("subscriptions").select("status, provider_subscription").eq("user_id", user.id).maybeSingle();
    if (sub?.provider_subscription && ["active", "trialing", "past_due", "unpaid", "incomplete"].includes(sub.status)) {
      if (!STRIPE_READY) return json({ error: "定期支払いを止められませんでした。時間をおいて試してください。" }, 500);
      await stripe.subscriptions.cancel(sub.provider_subscription);
    }
    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) throw error;
    return json({ ok: true });
  } catch (e) {
    console.error(e);
    return json({ error: "削除できませんでした。時間をおいてもう一度試してください。" }, 500);
  }
});
