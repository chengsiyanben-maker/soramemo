// エアライン経営を一通り動かして不具合を探す（試遊版のデータベース。本番にはつながない）
//   node tools/play/sweep.mjs [方針…]   例：node tools/play/sweep.mjs fsc cargo
//   方針ごとに：見本の会社 A と相手の会社 B を作り、アプリから呼べる操作を全部呼ぶ → 日を進める → 数字の決まり（NaN・搭乗率100%超えなど）を確かめる
//   出力：断られ方が「想定どおり」でないもの（SQL の誤り・ゼロ除算など）と、決まりに合わない数字、毎日の処理で止まったもの
import { buildDb, UID } from './seed.mjs';

const B = '00000000-0000-4000-8000-0000000000b0';
const POL = process.argv.slice(2).length ? process.argv.slice(2) : ['fsc', 'mcc', 'lcc', 'regional', 'cargo', 'pj'];
// アプリの決まりで断られるもの（画面に日本語の知らせがある）。これ以外の失敗は不具合の候補
const EXPECTED = /rating required|not enough|not ridden|already|not seen|cannot own|10 percent|seen limit|too many seen|invalid policy|premium not allowed|lcc cannot|fsc only|not partner|sellers full|codeshare limit|not orderable|prep max|no typhoon|not peak|not a spare|lounge max|debt limit|no home airport|slot auto|lease limit|leased|type not known|one per day|same partner|listing not found|own listing|not connected|turn too short|outside hours|must end at|legs 1 to 16|not a passenger|too late|trouble not found|fare once a day|not a freighter|too far|invalid flights|not a small|code not found|own code|too small|not intl|invalid amount|invest limit|invest total|invest locked|not visited|no free slot|route not found|airport too small|policy locked|policy once|cooldown|not leased|cannot pay|not orderable|game not released|ridden: use co_buy|guardian not met|airport not visited|not your|no aircraft|not owned/;
const issues = [];
const note = (pol, kind, what, detail) => { issues.push({ pol, kind, what, detail }); console.log(`  [${kind}] ${what}${detail ? ' … ' + String(detail).slice(0, 220) : ''}`); };

async function run(pol) {
  console.log(`\n=== 方針 ${pol} ===`);
  const db = await buildDb();
  console.log('  データベースを作った');
  const as = async (uid, sql, params = []) => {
    await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`);
    try { const r = await db.query(sql, params); return { ok: true, v: r.rows.length ? Object.values(r.rows[0])[0] : null, rows: r.rows }; }
    catch (e) { return { ok: false, err: String(e.message).split('\n')[0] }; }
    finally { await db.exec('reset role'); }
  };
  const call = async (uid, name, sql) => {
    const t0 = Date.now(); const r = await as(uid, sql);
    if (process.env.SWEEP_V) console.log(`    ${name} ${Date.now() - t0}ms ${r.ok ? 'ok' : r.err}`);
    if (!r.ok && !EXPECTED.test(r.err)) note(pol, '操作', name, r.err);
    return r;
  };
  // 相手の会社 B：A と同じフライトを持つ
  await db.exec(`insert into auth.users (id, email) values ('${B}', 'b@example.com');
    insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, status, flight_no, airline)
      select '${B}', from_airport, to_airport, dep_at, arr_at, distance_km, status, flight_no, airline from flights where user_id = '${UID}';`);
  console.log('  相手の会社を作った');
  let s = (await call(UID, 'co_state', `select public.co_state()`)).v;
  await call(B, 'co_state(B)', `select public.co_state()`);
  await db.exec(`update companies set cash = 5000000, rating = 5`);
  const p = await call(UID, 'co3_set_policy', `select public.co3_set_policy('${pol}')`);
  await call(B, 'co3_set_policy(B)', `select public.co3_set_policy('fsc')`);
  s = (await call(UID, 'co_state', `select public.co_state()`)).v;
  if (!s) { note(pol, '止まった', 'co_state が出せない'); return; }
  const routes = s.routes || [];
  const rk = (a, b) => (routes.find((r) => (r.a === a && r.b === b) || (r.a === b && r.b === a)) || {}).k;
  const kCTS = rk('HND', 'CTS') || routes[0]?.k;

  // 機体を買う
  const hangar = (await call(UID, 'co_hangar', `select public.co_hangar()`)).v || [];
  const types = [...new Map(hangar.map((h) => [h.icao, h])).values()].slice(0, 4);
  for (const h of types) await call(UID, `co_buy ${h.ride}`, `select public.co_buy('${h.ride}')`);
  for (const h of [...new Map(((await as(B, `select public.co_hangar()`)).v || []).map((h) => [h.icao, h])).values()].slice(0, 2)) await call(B, `co_buy(B)`, `select public.co_buy('${h.ride}')`);
  const seen = (await call(UID, 'co3_seen_list', `select public.co3_seen_list()`)).v || [];
  if (seen[0]) await call(UID, 'co3_buy_seen', `select public.co3_buy_seen('${seen[0].reg}')`);
  for (const t of (s.small || []).slice(0, 2)) await call(UID, `co3_buy_small ${t.code}`, `select public.co3_buy_small('${t.code}')`);
  s = (await call(UID, 'co_state', `select public.co_state()`)).v;
  const fleet = s.fleet || [];
  // 路線に入れる（貨物は貨物の路線）
  const pax = fleet.filter((a) => a.kind !== 'freighter');
  for (let i = 0; i < pax.length; i++) { const r = routes[i % routes.length]; if (r) await call(UID, `co_assign ${pax[i].id}→${r.k}`, `select public.co_assign(${pax[i].id}, '${r.k}')`); }
  for (const a of fleet.filter((a) => a.kind === 'freighter')) { const c = (s.cargo_routes || [])[0]; if (c) await call(UID, 'co3_cargo_assign', `select public.co3_cargo_assign(${a.id}, '${c.k || c.route_key}')`); }
  const bs = (await as(B, `select public.co_state()`)).v;
  for (const a of (bs.fleet || []).slice(0, 1)) await call(B, 'co_assign(B)', `select public.co_assign(${a.id}, '${kCTS}')`);

  // いろいろな操作
  const id0 = fleet[0]?.id, home = (await db.query(`select id from airports where iata = 'HND'`)).rows[0].id;
  const ops = [
    ['co3_set_premium', `select public.co3_set_premium(${pol === 'fsc' ? 20 : 0})`],
    ['co3_set_fare', `select public.co3_set_fare('${kCTS}', 1)`],
    ['co3_set_service', `select public.co3_set_service('paid', 'paid')`],
    ['co3_set_flights', `select public.co3_set_flights('${kCTS}', 6)`],
    ['co3_set_home', `select public.co3_set_home(${home})`],
    ['co3_build_lounge', `select public.co3_build_lounge('HND')`],
    ['co3_set_miles', `select public.co3_set_miles(2)`],
    ['co3_set_safety', `select public.co3_set_safety('high')`],
    ['co3_borrow', `select public.co3_borrow(1000)`],
    ['co3_hire crew', `select public.co3_hire('crew', 5)`],
    ['co3_hire mech', `select public.co3_hire('mech', 3)`],
    ['co3_set_ground', `select public.co3_set_ground('self')`],
    ['co3_set_wind_training', `select public.co3_set_wind_training('normal')`],
    ['co3_build_prep', `select public.co3_build_prep('deice', 'CTS')`],
    ['co3_set_cat3', `select public.co3_set_cat3(${id0})`],
    ['co3_set_wifi', `select public.co3_set_wifi(${id0}, true)`],
    ['co3_set_check_mode', `select public.co3_set_check_mode('self')`],
    ['co3_request_check', `select public.co3_request_check(${id0}, true)`],
    ['co3_set_auto_trouble', `select public.co3_set_auto_trouble(true)`],
    ['co3_slot_apply', `select public.co3_slot_apply('HND', 'main', 6)`],
    ['co3_set_slot_auto', `select public.co3_set_slot_auto(true)`],
    ['co_upgrade', `select public.co_upgrade('${kCTS}')`],
    ['co_build', `select public.co_build(${home})`],
    ['co_rename', `select public.co_rename('しらべる航空')`],
    ['co_set_hide', `select public.co_set_hide(false)`],
    ['co_ranking all', `select public.co_ranking('all')`],
    ['co_ranking friends', `select public.co_ranking('friends')`],
    ['co3_season_rank', `select public.co3_season_rank()`],
    ['co3_order_list', `select public.co3_order_list()`],
    ['co3_cs_candidates', `select public.co3_cs_candidates()`],
    ['co3_ally_list', `select public.co3_ally_list()`],
  ];
  for (const [n, q] of ops) await call(UID, n, q);
  const ol = (await as(UID, `select public.co3_order_list()`)).v || [];
  if (ol[0]) await call(UID, 'co3_order', `select public.co3_order('${ol[0].code}')`);
  const h2 = ((await as(UID, `select public.co_hangar()`)).v || []).find((h) => !h.owned);
  if (h2) { const r = await call(UID, 'co3_lease', `select public.co3_lease('ride', '${h2.ride}')`); const la = r.ok && (r.v.fleet || []).find((a) => a.lease); if (la) await call(UID, 'co3_lease_return', `select public.co3_lease_return(${la.id})`); }
  if (fleet[1]) { const r = await call(UID, 'co3_market_list', `select public.co3_market_list(${fleet[1].id}, 100)`); const ls = r.ok && (r.v.fleet || []).find((a) => a.listed); if (ls) await call(UID, 'co3_market_cancel', `select public.co3_market_cancel(${ls.listed.id})`); }
  // 自分で組むスケジュール（羽田⇄新千歳を2往復）
  if (fleet[0] && kCTS && !['cargo', 'pj'].includes(pol)) {
    const L = [['HND', 'CTS', 480], ['CTS', 'HND', 660], ['HND', 'CTS', 840], ['CTS', 'HND', 1020]].map(([dep, arr, t]) => ({ dep, arr, t }));
    await call(UID, 'co3_set_schedule', `select public.co3_set_schedule(${fleet[0].id}, '${JSON.stringify(L)}'::jsonb)`);
  }
  // 友だち・共同運航・出資・アライアンス
  const codeB = (await as(B, `select public.co_state()`)).v.friend_code, codeA = (await as(UID, `select public.co_state()`)).v.friend_code;
  await call(UID, 'co_add_friend', `select public.co_add_friend('${codeB}')`);
  const cs = await call(UID, 'co3_cs_request', `select public.co3_cs_request('${codeB}', '${kCTS}', 'free')`);
  const bcs = (await as(B, `select public.co_state()`)).v.cs;
  const req = bcs && (bcs.list || []).find((x) => x.status === 'pending');
  if (req) await call(B, 'co3_cs_answer(B)', `select public.co3_cs_answer(${req.id}, true)`);
  await call(UID, 'co3_inv_offer', `select public.co3_inv_offer('${codeB}', 1000)`);
  const binv = (await as(B, `select public.co_state()`)).v.invest;
  const off = binv && (binv.list || []).find((x) => x.status === 'offer');
  if (off) await call(B, 'co3_inv_answer(B)', `select public.co3_inv_answer(${off.id}, true)`);
  if (pol === 'fsc') { await call(UID, 'co3_ally_create', `select public.co3_ally_create('しらべる連合')`); await call(UID, 'co3_ally_rename', `select public.co3_ally_rename('しらべる連合2')`); }
  // 台風の予報を入れて、計画欠航を決める
  await db.exec(`insert into co3_typhoon_fcst (iata, day, source) values ('CTS', co3.today() + 1, 'admin') on conflict do nothing`);
  if (kCTS) await call(UID, 'co3_typhoon_decide', `select public.co3_typhoon_decide('${kCTS}', true)`);

  // 日を進めて、毎日の数字を確かめる
  for (let d = 1; d <= 10; d++) {
    try { await db.query(`select play.advance(1)`); } catch (e) { note(pol, '止まった', `${d}日目：日を進められない`, e.message); break; }
    const st = await as(UID, `select public.co_state()`);
    if (!st.ok) { note(pol, '止まった', `${d}日目：co_state`, st.err); break; }
    check(pol, d, st.v);
    // トラブルが出ていれば対応する
    for (const t of (st.v.troubles || []).filter((t) => !t.result).slice(0, 1)) await call(UID, 'co3_trouble_respond', `select public.co3_trouble_respond(${t.id}, 'snack')`);
    if (d === 3) await call(UID, 'co_collect', `select public.co_collect()`);
  }
  const je = await db.query(`select job, err, count(*)::int n from play.job_errors group by 1, 2`);
  for (const x of je.rows) note(pol, '毎日の処理', x.job, `${x.err}（${x.n}回）`);
  await db.close();
}

// 数字の決まり
function check(pol, d, s) {
  const bad = [];
  const walk = (o, path) => {
    if (o == null) return;
    if (typeof o === 'number') { if (!Number.isFinite(o)) bad.push(`${path} = ${o}`); return; }
    if (typeof o === 'string') { if (/^(NaN|Infinity|-Infinity)$/.test(o)) bad.push(`${path} = ${o}`); return; }
    if (Array.isArray(o)) return o.forEach((x, i) => walk(x, `${path}[${i}]`));
    if (typeof o === 'object') for (const k in o) walk(o[k], path ? `${path}.${k}` : k);
  };
  walk(s, '');
  if (bad.length) note(pol, '数字', `${d}日目：数でない値`, bad.slice(0, 5).join(', '));
  if (!(s.satisfaction >= 0 && s.satisfaction <= 100)) note(pol, '数字', `${d}日目：満足度が0〜100の外`, s.satisfaction);
  if (!Number.isFinite(+s.cash)) note(pol, '数字', `${d}日目：資金`, s.cash);
  for (const e of s.econ || []) {
    const fl = +e.flights, seats = +e.seats, car = +e.carried;
    if (fl > 0 && seats > 0 && car > fl * seats * 1.001) note(pol, '数字', `${d}日目：${e.k} 乗った人が席より多い`, `${car}人 / ${fl}便×${seats}席`);
    if (fl < 0 || car < 0 || +e.revenue < 0) note(pol, '数字', `${d}日目：${e.k} 負の数`, JSON.stringify({ fl, car, rev: e.revenue }));
    if (fl > 40) note(pol, '数字', `${d}日目：${e.k} 便が多すぎる`, fl);
  }
}

for (const p of POL) {
  try { await run(p); } catch (e) { note(p, '止まった', '調べる道具が止まった', e.stack); }
}
console.log(`\n=== まとめ：${issues.length}件 ===`);
const seenKey = new Set();
for (const x of issues) { const k = x.kind + x.what.replace(/\d+日目：/, '') + String(x.detail).slice(0, 80); if (seenKey.has(k)) continue; seenKey.add(k); console.log(`${x.pol}\t${x.kind}\t${x.what}\t${String(x.detail || '').slice(0, 300)}`); }
