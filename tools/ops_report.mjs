// 運用の判定の記録（ops_log）のまとめを出す：空港ごとに、風からの推定と実際の機体からの判定が一致した・食い違った回数と、最近の食い違い。
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node tools/ops_report.mjs [日数（既定7）]
const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY, days = Number(process.argv[2] || 7);
if (!url || !key) { console.error("使い方：SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node tools/ops_report.mjs [日数]"); process.exit(1); }
const H = { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" }, base = url.replace(/\/$/, "");
const sum = await (await fetch(`${base}/rest/v1/rpc/ops_log_summary`, { method: "POST", headers: H, body: JSON.stringify({ p_days: days }) })).json();
console.log(`直近${days}日（5分ごとの記録）`);
console.log("空港  記録  実機で判定  一致  食い違い  分かれた  風で決められず  一致の割合");
for (const r of sum) {
  const judged = Number(r.agree) + Number(r.disagree);
  console.log(`${r.iata}  ${String(r.samples).padStart(5)}  ${String(r.observed).padStart(9)}  ${String(r.agree).padStart(4)}  ${String(r.disagree).padStart(7)}  ${String(r.mixed).padStart(7)}  ${String(r.unsure).padStart(13)}  ${judged ? Math.round(Number(r.agree) / judged * 100) + "%" : "—"}`);
}
const since = new Date(Date.now() - days * 864e5).toISOString();
const bad = await (await fetch(`${base}/rest/v1/ops_log?select=at,iata,wdir,wspd,est_mode,obs_mode,obs_arr,obs_dep&not.obs_mode.is.null&est_unsure=eq.false&at=gte.${since}&order=at.desc&limit=500`, { headers: H })).json();
const diff = bad.filter((r) => r.obs_mode !== r.est_mode).slice(0, 30);
if (diff.length) {
  console.log("\n最近の食い違い（風からの推定 → 実際の機体）");
  for (const r of diff) console.log(`${new Date(r.at).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })}  ${r.iata}  風 ${r.wdir ?? "VRB"}/${r.wspd}  ${r.est_mode} → ${r.obs_mode}（着陸${r.obs_arr}・離陸${r.obs_dep}）`);
}
