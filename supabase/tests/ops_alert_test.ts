import { assertEquals } from "jsr:@std/assert@1";
import { alertText, parseTargets, resultText, smtpConfig } from "../functions/_shared/ops_alert.ts";

Deno.test("parseTargets：メールと https の Webhook だけ・同じものは1つ・最大5つ", () => {
  const t = parseTargets(" ops@example.com, https://hooks.example.com/abc \n bad, http://x.example.com, OPS@example.com, javascript:alert(1)");
  assertEquals(t, [{ kind: "mail", to: "ops@example.com" }, { kind: "hook", url: "https://hooks.example.com/abc" }]);
  assertEquals(parseTargets(undefined), []);
  assertEquals(parseTargets(""), []);
  assertEquals(parseTargets("a@b.jp,c@d.jp,e@f.jp,g@h.jp,i@j.jp,k@l.jp").length, 5);
  assertEquals(parseTargets("a@b.jp<script>"), []);
});

Deno.test("alertText：件名に件数、本文に項目の名前と最後の時刻（日本時間）・上限", () => {
  const m = alertText([
    { key: "flight_history", label: "便の実績", last: "2026-11-25T15:00:00Z", limit_min: 1680 },
    { key: "cron_failed", label: "毎日・毎分の処理の失敗（直近26時間）", last: null, limit_min: null },
    { key: "wx", label: "気象", last: "2026-11-26T03:05:00Z", limit_min: 90 },
  ], new Date("2026-11-26T22:41:00Z"));
  assertEquals(m.subject, "そらメモ：夜の処理・取り込みが止まっています（3件）");
  assertEquals(m.text.startsWith("11/27 07:41 時点で"), true);
  assertEquals(m.text.includes("・便の実績（最後：11/26 00:00・上限 28時間）"), true);
  assertEquals(m.text.includes("・毎日・毎分の処理の失敗（直近26時間）（最後：記録なし）"), true);
  assertEquals(m.text.includes("・気象（最後：11/26 12:05・上限 90分）"), true);
  assertEquals(m.text.includes("1日1回まで"), true);
});

Deno.test("alertText：20件より多ければ「ほか」にまとめる", () => {
  const items = Array.from({ length: 23 }, (_, i) => ({ key: `k${i}`, label: `項目${i}`, last: null, limit_min: null }));
  const m = alertText(items, new Date());
  assertEquals(m.text.includes("・ほか 3 件"), true);
  assertEquals(m.text.includes("項目20"), false);
});

Deno.test("smtpConfig：ユーザーとパスワードがなければ null。既定は Gmail の 465", () => {
  assertEquals(smtpConfig(() => undefined), null);
  assertEquals(smtpConfig((k) => ({ OPS_SMTP_USER: "u@example.com" } as Record<string, string>)[k]), null);
  assertEquals(smtpConfig((k) => ({ OPS_SMTP_USER: "u@example.com", OPS_SMTP_PASS: "p" } as Record<string, string>)[k]),
    { host: "smtp.gmail.com", port: 465, user: "u@example.com", pass: "p", from: "u@example.com" });
  assertEquals(smtpConfig((k) => ({ OPS_SMTP_USER: "u", OPS_SMTP_PASS: "p", OPS_SMTP_HOST: "smtp.example.com", OPS_SMTP_PORT: "2465", OPS_SMTP_FROM: "f@example.com" } as Record<string, string>)[k]),
    { host: "smtp.example.com", port: 2465, user: "u", pass: "p", from: "f@example.com" });
});

Deno.test("resultText：宛先は入らない", () => {
  const s = resultText({ mail: 1, hook: 0, failed: 1, skipped: ["no_smtp"] });
  assertEquals(s, "mail 1 / hook 0 / failed 1 / skip no_smtp");
  assertEquals(s.includes("@"), false);
});
