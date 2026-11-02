// 試遊版のデータベースで、会社の状態（co_state）の重さを測る：node tools/play/prof.mjs
import { buildDb, UID } from './seed.mjs';
const db = await buildDb();
const as = async (sql) => { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${UID}',false);`); try { const r = await db.query(sql); return Object.values(r.rows[0] ?? {})[0]; } finally { await db.exec('reset role'); } };
let s = await as(`select public.co_state()`); await db.exec(`update companies set cash = cash + 1000000`);
const h = await as(`select public.co_hangar()`);
for (const [i, k] of [['B738','5-6'],['A321','5-16'],['B763','5-23']].entries()) { const x = h.find(r=>r[0]===k[0]) || h.filter(r=>!r.owned)[i]; const y = h.find(r=>r.icao===k[0]); s = await as(`select public.co_buy('${y.ride}')`); s = await as(`select public.co_assign(${s.fleet[s.fleet.length-1].id}, '${k[1]}')`); }
await db.exec(`set track_functions = 'all'`);
for (const q of ['co_state', 'co_hangar']) {
  await db.exec('begin');
  await db.exec(`set local role authenticated; select set_config('request.jwt.claim.sub','${UID}',true);`);
  const t = Date.now(); await db.query(`select public.${q}()`); console.log('==', q, Date.now() - t, 'ms');
  await db.exec('reset role');
  const r = await db.query(`select schemaname||'.'||funcname f, calls, round(total_time) tot, round(self_time) self from pg_stat_xact_user_functions order by self_time desc limit 14`);
  for (const x of r.rows) console.log(x.f, x.calls, x.tot, x.self);
  await db.exec('commit');
}
