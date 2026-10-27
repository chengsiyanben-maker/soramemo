// エアライン経営 co-v3：見た機体（見つけ方・貨物機の見分け・値段・上限・稼ぎと維持費の差）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);   // 季節の需要のない日で手計算する（季節は t72）
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('NRT','HND')`)).rows.map((r) => [r.iata, r.id]));

// A は成田で2時間前にチェックイン。前後45分に発着した機体：NCA の B748（貨物機）、JAL の B789、別の日の機体（見えない）
// B は偽装の印つきのチェックイン
const T = `(now() - interval '2 hours')`;
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
    ('${A}', ${ids.NRT}, 35.77, 140.39, 10, ${T}, ${T}),
    ('${B}', ${ids.NRT}, 35.77, 140.39, 10, ${T}, ${T});
  update checkins set flags = '{impossible_speed}' where user_id = '${B}';
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg) values
    ((${T} at time zone 'Asia/Tokyo')::date, 'KZ110', 'NRT', 'ANC', ${T} + interval '20 minutes', ${T} + interval '7 hours', 'B748', 'JA11KZ'),
    ((${T} at time zone 'Asia/Tokyo')::date, 'JL7', 'NRT', 'JFK', ${T} - interval '30 minutes', ${T} + interval '12 hours', 'B789', 'JA861J'),
    ((${T} at time zone 'Asia/Tokyo')::date, 'JL5', 'NRT', 'ORD', ${T} - interval '40 minutes', ${T} + interval '12 hours', 'B788', 'JA831J'),
    ((${T} at time zone 'Asia/Tokyo')::date, 'JL3', 'NRT', 'LAX', ${T} - interval '35 minutes', ${T} + interval '12 hours', 'B77W', 'JA731J'),
    ((${T} at time zone 'Asia/Tokyo')::date, 'NH9', 'NRT', 'ORD', ${T} + interval '2 hours', ${T} + interval '14 hours', 'B789', 'JA882A')`);
await as(A, `select public.co_state()`);
let list = await as(A, `select public.co3_seen_list()`);
const regs = list.map((x) => x.reg).sort().join(',');
check('前後45分に発着した機体だけ見える（2時間後の便は見えない）', regs === 'JA11KZ,JA731J,JA831J,JA861J', regs);
const kz = list.find((x) => x.reg === 'JA11KZ');
check('NCA の便の B748 は貨物機（B747-8F）、乗ったのと同じ扱い', kz.code === 'B748F' && kz.kind === 'freighter' && kz.as_ridden === true, kz);
const jl = list.find((x) => x.reg === 'JA861J');
check('JAL の B789 は旅客機（B787-9）', jl.code === 'B789' && jl.kind === 'pax' && jl.as_ridden === false, jl);
check('偽装の印つきのチェックインでは見えない', (await as(B, `select public.co3_seen_list()`)).length === 0, null);
check('見た機体の値段：貨物機は1.5倍（B747-8F 48,300 → 72,450）・旅客機は1.3倍（B787-9 42,600 → 55,380）', Number(kz.price) === 72450 && Number(jl.price) === 55380, { kz: kz.price, jl: jl.price });

await db.exec(`update companies set cash = 1000000, satisfaction = 60 where user_id = '${A}'`);
// FSC は機体の1割までしか貨物機を持てない（t53）ので、ここは貨物の会社で確かめる
await db.exec(`update companies set policy = 'cargo' where user_id = '${A}'`);
let s = await as(A, `select public.co3_buy_seen('JA11KZ')`);
const f = s.fleet.find((x) => x.reg === 'JA11KZ');
check('貨物機を買う：72,450 で、差なし（見ただけの旅客機の印はなし）', near(Number(s.cash), 1000000 - 72450, 2) && f, { cash: s.cash });
const fr = (await db.query(`select co3_code, seen, ride, intl from aircraft where reg = 'JA11KZ'`)).rows[0];
check('記録：機種 B748F・差なし・s:登録記号・国際線（行き先が海外）', fr.co3_code === 'B748F' && fr.seen === false && fr.ride === 's:JA11KZ' && fr.intl === true, fr);
check('同じ機体は2回買えない', String(await as(A, `select public.co3_buy_seen('JA11KZ')`)).includes('already'), null);
check('見ていない機体は買えない', String(await as(A, `select public.co3_buy_seen('JA882A')`)).includes('not seen'), null);

// 2機目からは +25%：B787-9 42,600 × 1.3 × 1.25 ＝ 69,225
s = await as(A, `select public.co3_buy_seen('JA861J')`);
// 買う前にそれまでの収益を確定するので、数秒ぶんの維持費（1〜2）が引かれることがある
check('見た旅客機を買う：1.3倍 × 持っている1機ぶん +25% ＝ 69,225', near(Number(s.cash), 1000000 - 72450 - 69225, 2), s.cash);
const pr = (await db.query(`select id, seen from aircraft where reg = 'JA861J'`)).rows[0];
check('見ただけの旅客機の印', pr.seen === true, pr);
check('稼ぎ 0.85（買ったばかり）', Number(await q1(`select public.co3_ac_earn(${pr.id})`)) === 0.85, null);
await db.exec(`update aircraft set bought_at = now() - interval '65 days' where id = ${pr.id}`);
check('60日すぎで 0.95（30日ごとに +0.05、最大 0.95）', Number(await q1(`select public.co3_ac_earn(${pr.id})`)) === 0.95, null);
await db.exec(`update aircraft set bought_at = now() - interval '400 days' where id = ${pr.id}`);
check('最大 0.95 のまま', Number(await q1(`select public.co3_ac_earn(${pr.id})`)) === 0.95, null);
await db.exec(`update companies set rating = 3`).catch(() => {});   // 格付け1・2の維持費 +10%（自動の点検の分）は t68 で試す
check('維持費は機種の表の +30%（B787-9 30 → 39）', Number(await q1(`select public.co3_ac_upkeep(${pr.id})`)) === 39, null);
check('貨物機の維持費は表のまま（B747-8F 48）', Number(await q1(`select public.co3_ac_upkeep(id) from aircraft where reg = 'JA11KZ'`)) === 48, null);
await db.exec(`update aircraft set bought_at = now() where id = ${pr.id}`);

// 上限：会社の機体のうち見ただけの旅客機は半分まで（乗った機体がないうちは2機まで）。1日3機まで
s = await as(A, `select public.co3_buy_seen('JA831J')`);
check('見ただけの旅客機の2機目（乗った機体がないうちは2機まで）', !String(s).startsWith('ERROR'), s);
check('3機目は「見ただけは半分まで」で買えない', String(await as(A, `select public.co3_buy_seen('JA731J')`)).includes('too many seen'), null);

// あとで乗ると差がなくなる：JA861J に乗った記録（便名と毎日の記録が合う）
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
    ('${A}', ${ids.NRT}, ${ids.HND}, now() - interval '1 hour', now() - interval '20 minutes', 60, 'JL1001', 'JL');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg) values
    (((now() - interval '1 hour') at time zone 'Asia/Tokyo')::date, 'JL1001', 'NRT', 'HND', now() - interval '1 hour', now() - interval '20 minutes', 'B789', 'JA861J')`);
check('乗ったら稼ぎ 1.0・維持費の差なし', Number(await q1(`select public.co3_ac_earn(${pr.id})`)) === 1 && Number(await q1(`select public.co3_ac_upkeep(${pr.id})`)) === 30, null);

// 維持費の切り替え：スイッチがオンなら機種の表、オフなら co-v2 の大きさの維持費
const up3 = Number((await as(A, `select public.co_state()`)).upkeep);
await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`);
const up2 = Number((await as(A, `select public.co_state()`)).upkeep);
check('維持費：オンなら機種の表（48＋30＋B787-8 の25×1.3＝32.5 → 111）・オフなら co-v2', up3 === 111 && up2 !== up3, { up3, up2 });

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
