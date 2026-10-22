// エアライン経営のつくり直し：乗った機体だけ買える・最初は半額・機体なしは半分・維持費・売る・実際の空・国際線・先に確定・ランキングと友だち
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`update ops.flags set value = 'true' where key = 'game_released'`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b', C = '00000000-0000-0000-0000-00000000000c';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}'), ('${C}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS','OKA','ISG')`)).rows.map((r) => [r.iata, r.id]));
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

const cls = await q1(`select string_agg(coalesce(public.ac_class(x), '-'), ',') from unnest(array['B789','789','73H','A359','DH8D','E190','B77W','A21N','DH4','xyz']) x`);
check('機種の記号から大きさ（ICAO・時刻表どちらも）', cls === 'wb,wb,nb,lg,prop,rj,lg,nb,prop,-', cls);

// A：羽田→新千歳（JL501・JA01XJ の A350）と、那覇→石垣（便名なし）、羽田→ソウル（国際線・JA79AN の B77W）、もう一つ機種だけ分かる便
const D = `((now() - interval '1 day') at time zone 'Asia/Tokyo')::date`;
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
  ('${A}', ${ids.HND}, ${ids.CTS}, now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 819.6, 'JL501', 'JL'),
  ('${A}', ${ids.OKA}, ${ids.ISG}, now() - interval '1 day', now() - interval '1 day' + interval '60 minutes', 395.4, null, null),
  ('${A}', ${ids.CTS}, ${ids.HND}, now() - interval '20 hours', now() - interval '18 hours', 819.6, 'NH56', 'NH');
  insert into intl_flights (user_id, flown_on, dep, arr, flight_no, distance_km) values ('${A}', ${D}, 'HND', 'GMP', 'NH861', 1210);
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg, aircraft) values
    (${D}, 'JL501', 'HND', 'CTS', now() - interval '1 day', now() - interval '1 day' + interval '90 minutes', 'A359', 'JA01XJ', '359'),
    (((now() - interval '20 hours') at time zone 'Asia/Tokyo')::date, 'NH56', 'CTS', 'HND', now() - interval '20 hours', now() - interval '18 hours', null, null, '738'),
    (${D}, 'NH861', 'HND', 'GMP', now() - interval '1 day', now(), 'B77W', 'JA79AN', '77W')`);

let s = await as(A, 'select public.co_state()');
check('はじめの資金は 5,000', Number(s.cash) === 5000, s.cash);
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;
check('路線：国内2本と国際線1本（機体なしは ×0.5）', s.routes.length === 3 && s.routes.every((r) => Number(r.mult) === 0.5) && s.routes.some((r) => r.intl && r.k === 'GMP-HND'), s.routes);
const h = await as(A, 'select public.co_hangar()');
check('乗った機体：登録記号2機と、機種だけの1機', h.length === 3 && h.some((x) => x.ride === 'r:JA01XJ' && x.cls === 'lg' && !x.intl) && h.some((x) => x.ride === 'r:JA79AN' && x.intl) && h.some((x) => x.ride.startsWith('f:') && x.cls === 'nb' && x.reg === null), h);
const half = h.find((x) => x.ride.startsWith('f:'));
check('最初の1機は半額（小型 25,000 → 12,500）', Number(half.price) === 12500, half);
check('乗っていない機体は買えない', String(await as(A, `select public.co_buy('r:JA99ZZ')`)).includes('not ridden'), null);
check('お金が足りない', String(await as(A, `select public.co_buy('r:JA01XJ')`)).includes('not enough'), null);
check('ほかの人の乗った機体は買えない', String(await as(B, `select public.co_buy('r:JA01XJ')`)).includes('not ridden'), null);
await db.exec(`update companies set cash = 200000, last_collect = now() where user_id = '${A}'`);
s = await as(A, `select public.co_buy('${half.ride}')`);
check('買うと資金が減り、半額は1回だけ', Number(s.cash) === 200000 - 12500 && s.bought === 1 && s.fleet.length === 1 && s.fleet[0].reg === null && Number(s.upkeep) === 25, { cash: s.cash, b: s.bought, u: s.upkeep });
check('同じものは2回買えない', String(await as(A, `select public.co_buy('${half.ride}')`)).includes('already'), null);
s = await as(A, `select public.co_buy('r:JA01XJ')`);
check('2機目は半額でなく、持っている数で +25%（大型 80,000 × 1.25）', Number(s.cash) === 187500 - 100000, s.cash);
const lg = s.fleet.find((x) => x.reg === 'JA01XJ');
const oi = `${Math.min(ids.OKA, ids.ISG)}-${Math.max(ids.OKA, ids.ISG)}`;
check('大型は離島の路線に入れられない', String(await as(A, `select public.co_assign(${lg.id}, '${oi}')`)).includes('too small'), null);
check('国内線の機体は国際線に入れられない', String(await as(A, `select public.co_assign(${lg.id}, 'GMP-HND')`)).includes('not intl'), null);
s = await as(A, `select public.co_assign(${lg.id}, '${hc}')`);
const r1 = s.routes.find((r) => r.k === hc);
check('機体を入れると倍率が機体のものになる', Number(r1.mult) === 2.3 && Number(r1.ac_id) === Number(lg.id), r1);

// 先に確定：1日前から数えている状態で増便すると、増便の前の倍率で1日分が入る
await db.exec(`update companies set last_collect = now() - interval '1 day' where user_id = '${A}'`);
const before = await as(A, 'select public.co_state()');
s = await as(A, `select public.co_upgrade('${hc}')`);
const cost = Number(before.routes.find((r) => r.k === hc).cost);
check('増便の前にそれまでの収益が資金に入る（後から増えない）', Math.abs(Number(s.cash) - (Number(before.cash) + Number(before.pending) - cost)) <= 1 && Number(s.pending) === 0, { b: before.cash, p: before.pending, cost, after: s.cash });

// 実際の空：前の4週の同じ曜日は10便、昨日は8便が飛んで2便が欠航 → 8/10−1＝−20%→−10%、欠航 2/10＝−20%→−10%、合わせて −20%
const y = `(now() at time zone 'Asia/Tokyo')::date - 1`;
for (const w of [7, 14, 21, 28]) for (let i = 0; i < 10; i++) await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta) values (${y} - ${w}, 'JL${600 + i}', 'HND', 'CTS', now(), now() + interval '1 hour')`);
for (let i = 0; i < 10; i++) await db.exec(`insert into flight_history (svc_date, flight, dep, arr, std, sta, cancelled) values (${y}, 'JL${600 + i}', 'HND', 'CTS', now(), now() + interval '1 hour', ${i < 2})`);
await db.exec(`select public.co_sky_refresh()`);
s = await as(A, 'select public.co_state()');
const sky = s.sky[hc];
check('実際の空は ±20%まで（便が少なく欠航もある日は ×0.8）', sky && sky.n >= 9 && sky.cxl === 2 && Number(s.routes.find((r) => r.k === hc).sky) >= 0.8 && Number(s.routes.find((r) => r.k === hc).sky) < 1, sky);
check('国際線は実際の空で変わらない', Number(s.routes.find((r) => r.intl).sky) === 1, null);

// 国際線で乗った機体は国際線に入れられる
await db.exec(`update companies set cash = 500000 where user_id = '${A}'`);
s = await as(A, `select public.co_buy('r:JA79AN')`);
const intlAc = s.fleet.find((x) => x.reg === 'JA79AN');
s = await as(A, `select public.co_assign(${intlAc.id}, 'GMP-HND')`);
check('国際線で乗った機体は国際線に入る', Number(s.routes.find((r) => r.k === 'GMP-HND').ac_id) === Number(intlAc.id), null);

// 古さと売る
await db.exec(`update aircraft set bought_at = now() - interval '200 days' where id = ${lg.id}`);
s = await as(A, 'select public.co_state()');
const old = s.fleet.find((x) => x.id === lg.id);
check('古さ：200日で −10%', Number(old.age) === 0.9 && Number(old.value) === 90000, old);
const cash0 = Number(s.cash);
s = await as(A, `select public.co_sell(${lg.id})`);
check('売るといまの値段の3割（27,000）が入り、また買える一覧に戻る', Number(s.cash) - cash0 >= 27000 && Number(s.cash) - cash0 < 27100 && !s.fleet.some((x) => x.id === lg.id), Number(s.cash) - cash0);
const h2 = await as(A, 'select public.co_hangar()');
check('売った機体はまた買える（半額ではない）', h2.find((x) => x.ride === 'r:JA01XJ' && !x.owned && Number(x.price) === 80000 * 1.5), h2);

// 役職のボーナス：同じ日の3回のチェックインは1日として数える
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) select '${A}', ${ids.HND}, 35.55, 139.78, 10, now(), now() - (i || ' minutes')::interval from generate_series(1, 3) i`);
await as(A, `select public.co_set_role('crew', ${ids.HND})`);
check('役職の階級はチェックインした日の数（1日では階級0）', Number(await q1(`select public.co_bonus('${A}')`)) === 0.1, null);

// ランキングと友だち
await db.exec(`insert into companies (user_id, name, cash) values ('${B}', 'みなみ風航空', 900000), ('${C}', 'かくれ航空', 950000);
  update companies set hide_rank = true where user_id = '${C}'`);
await db.exec(`select public.co_rank_refresh()`);
let rk = await as(A, `select public.co_ranking('all')`);
check('全国：出さない設定の会社は出ない、自分はいまの価値', rk.rows.length === 2 && rk.rows[0].name === 'みなみ風航空' && rk.rows.some((x) => x.me) && !rk.rows.some((x) => x.name === 'かくれ航空') && rk.rank === 2, rk);
const codeC = await q1(`select friend_code from companies where user_id = '${C}'`);
check('合言葉がちがうと友だちになれない', String(await as(A, `select public.co_add_friend('ZZZZZZZZ')`)).includes('code not found'), null);
const myCode = await q1(`select friend_code from companies where user_id = '${A}'`);
check('自分の合言葉では友だちになれない', String(await as(A, `select public.co_add_friend('${myCode}')`)).includes('own code'), null);
const fr = await as(A, `select public.co_add_friend('${codeC.toLowerCase()}')`);
check('合言葉で友だちになる（小文字でもよい）', fr.name === 'かくれ航空', fr);
rk = await as(A, `select public.co_ranking('friends')`);
check('友だちには出さない設定の会社も出る', rk.rows.length === 2 && rk.rows[0].name === 'かくれ航空' && rk.rows[0].code === codeC, rk);
rk = await as(C, `select public.co_ranking('friends')`);
check('友だちはおたがいに', rk.rows.length === 2, rk);
await as(A, `select public.co_remove_friend('${codeC}')`);
rk = await as(C, `select public.co_ranking('friends')`);
check('友だちをやめると、どちらからも消える', rk.rows.length === 1, rk);
check('ほかの表は直接読めない', String(await as(A, `select count(*) from public.co_rank_days`)).startsWith('ERROR') && String(await as(A, `select count(*) from public.co_friends`)).startsWith('ERROR'), null);
check('資金は直接書き換えられない', String(await as(A, `update public.companies set cash = 1`)).startsWith('ERROR'), null);
if (bad) process.exit(1);
