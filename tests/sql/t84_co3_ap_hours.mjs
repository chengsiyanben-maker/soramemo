// エアライン経営 co-v3：空港ごとの運用時間（国土交通省 空港一覧 令和8年9月1日現在・会社管理の4空港は AIP）でスケジュールとおまかせの便数をしぼる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`set co3.season_day = '2026-05-20'`);
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

// 表
const n = Number(await q1(`select count(*) from co3_ap_hours`));
const jp = Number(await q1(`select count(*) from airports a where a.iata ~ '^[A-Z]{3}$' and not exists (select 1 from co3_ap_hours h where h.iata = a.iata)`));
check('運用時間：ゲームの国内の空港すべて', n >= 88 && jp === 0, { n, jp });
const h = async (i) => [Number(await q1(`select co3.ap_open('${i}')`)), Number(await q1(`select co3.ap_close('${i}')`))];
check('羽田・那覇は24時間、福岡は利用時間 7〜22時、伊丹 7〜21時、成田 6〜24時', JSON.stringify([await h('HND'), await h('OKA'), await h('FUK'), await h('ITM'), await h('NRT')]) === '[[0,1440],[0,1440],[420,1320],[420,1260],[360,1440]]', null);
check('広島 7:30〜22:30・石垣 8〜21時・函館 7:30〜20:30', JSON.stringify([await h('HIJ'), await h('ISG'), await h('HKD')]) === '[[450,1350],[480,1260],[450,1230]]', null);
check('礼文は休止中（開いていない）', JSON.stringify(await h('RBJ')) === '[0,0]', null);
check('喜界：夏は18:30まで', (await h('KKX'))[1] === 1110, await h('KKX'));
await db.exec(`set co3.season_day = '2026-12-01'`);
check('喜界：冬（10〜3月）は17:30まで', (await h('KKX'))[1] === 1050, await h('KKX'));
await db.exec(`set co3.season_day = '2026-05-20'`);
check('表にない空港（海外）は24時間', JSON.stringify(await h('LAX')) === '[0,1440]', null);
check('運用時間はだれでも読める・アプリから書けない', Number(await as(A, `select count(*) from co3_ap_hours`)) >= 88
  && String(await as(A, `update co3_ap_hours set open_min = 0 where iata = 'HKD'`)).startsWith('ERROR')
  && String(await as(A, `select public.admin_co3_ap_hours('HKD', 0, 1440)`)).includes('admin only'), null);

// おまかせの便数の上限
const L = async (a, b, km) => Number(await q1(`select co3.hours_legs('${a}', '${b}', ${km}, 'nb', 'fsc')`));
check('羽田⇄新千歳（どちらも24時間）はしぼらない', await L('HND', 'CTS', 820) === 99, null);
check('羽田⇄石垣：8〜21時に 163分＋折り返し35分 → 4便', await L('HND', 'ISG', 1950) === 4, await L('HND', 'ISG', 1950));
check('羽田⇄礼文：0便', await L('HND', 'RBJ', 1100) === 0, null);

// 自分で組むスケジュール：A は羽田⇄函館を飛んだ
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','HKD')`)).rows.map((r) => [r.iata, r.id]));
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km, flight_no, airline) values
  ('${A}', ${ids.HND}, ${ids.HKD}, now() - interval '2 day', now() - interval '2 day' + interval '80 minutes', 680, 'JL585', 'JL');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg, aircraft) values
    (((now() - interval '2 day') at time zone 'Asia/Tokyo')::date, 'JL585', 'HND', 'HKD', now() - interval '2 day', now() - interval '2 day' + interval '80 minutes', 'B738', 'JA301J', '738') on conflict do nothing;`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 500000, rating = 5, safety = 'low' where user_id = '${A}'`).catch(() => db.exec(`update companies set cash = 500000 where user_id = '${A}'`));
let s = await as(A, `select public.co_buy('r:JA301J')`);
const ac = s.fleet[0].id;
const hk = `${Math.min(ids.HND, ids.HKD)}-${Math.max(ids.HND, ids.HKD)}`;
const blk = Number(await q1(`select co3.sched_block(680, 'nb')`));   // 70分
const leg = (dep, arr, t) => ({ dep, arr, t });
const set = (legs) => as(A, `select public.co3_set_schedule(${ac}, '${JSON.stringify(legs)}'::jsonb)`);
check('函館に 7:30 より前に着く便は組めない', String(await set([leg('HND', 'HKD', 360), leg('HKD', 'HND', 360 + blk + 40)])).includes('outside hours at 1'), null);
check('函館を 20:30 より後に出る便は組めない', String(await set([leg('HND', 'HKD', 1000), leg('HKD', 'HND', 1235)])).includes('outside hours at 2'), null);
s = await set([leg('HND', 'HKD', 420), leg('HKD', 'HND', 420 + blk + 40)]);
check('函館が開いている時間なら組める', typeof s === 'object' && (s.scheds || {})[ac] && s.scheds[ac].length === 2, s && s.scheds);
await as(A, `select public.co3_clear_schedule(${ac})`);
s = await as(A, `select public.co_assign(${ac}, '${hk}')`);
const e = (s.econ || []).find((x) => x.k === hk);
check('おまかせの便数：羽田⇄函館（函館 7:30〜20:30）でも距離の上限（8便）のまま', e && Number(e.flights) <= 8 && Number(e.flights) > 0, e);
console.log(bad ? `NG ${bad}` : 'ALL OK'); process.exit(bad ? 1 : 0);
