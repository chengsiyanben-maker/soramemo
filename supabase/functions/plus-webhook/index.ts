// POST /functions/v1/plus-webhook（Stripe からの通知。JWTの確認は切って公開する）
// 署名を確かめてから、申し込み・更新・解約を subscriptions 表に反映する。
import Stripe from "npm:stripe@23.0.0";
import { admin, saveSubscription, stripe } from "../_shared/plus.ts";

const SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
const crypto = Stripe.createSubtleCryptoProvider();

async function userIdFor(sub: Stripe.Subscription): Promise<string | null> {
  if (sub.metadata?.user_id) return sub.metadata.user_id;
  const { data } = await admin.from("subscriptions").select("user_id").eq("provider_subscription", sub.id).maybeSingle();
  return data?.user_id ?? null;
}

Deno.serve(async (req) => {
  const sig = req.headers.get("Stripe-Signature");
  const body = await req.text();
  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(body, sig ?? "", SECRET, undefined, crypto);
  } catch (e) {
    console.error("署名が正しくありません", e);
    return new Response("bad signature", { status: 400 });
  }
  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const s = event.data.object as Stripe.Checkout.Session;
        if (s.mode === "subscription" && s.subscription && s.client_reference_id) {
          const sub = await stripe.subscriptions.retrieve(typeof s.subscription === "string" ? s.subscription : s.subscription.id);
          await saveSubscription(s.client_reference_id, sub);
        }
        break;
      }
      case "customer.subscription.created":
      case "customer.subscription.updated":
      case "customer.subscription.deleted": {
        const sub = event.data.object as Stripe.Subscription;
        const uid = await userIdFor(sub);
        if (uid) await saveSubscription(uid, sub);
        break;
      }
    }
    return new Response("ok");
  } catch (e) {
    console.error(e);
    return new Response("error", { status: 500 });
  }
});
