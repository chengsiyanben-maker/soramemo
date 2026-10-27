// エアライン経営 co-v3：地域航空の会社（小型機・遊覧とチャーターの割り当て・定期便の補助）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
await db.exec(`update ops.flags set value = 'true' where key in ('game_released', 'co_v3')`);
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('ISG','OKA','HND','GAJ')`)).rows.map((r) => [r.iata, r.id]));

// 観光地の度合い（10/27 から国の統計）：県の 延べ宿泊者数 ÷ 人口 の順位で 0.5〜1.5、離島は +0.2（1.5まで）
const dg = async (c) => Number(await q1(`select public.co3_degree('${c}')`));
check('観光地の度合い：石垣（沖縄 1.5、離島でも1.5まで）・隠岐（島根 1.11 ＋ 離島 0.2）・羽田（東京 1.35）・山形 0.98・茨城 0.52',
  await dg('ISG') === 1.5 && await dg('OKI') === 1.31 && await dg('HND') === 1.35 && await dg('GAJ') === 0.98 && await dg('IBR') === 0.52,
  { ISG: await dg('ISG'), OKI: await dg('OKI'), HND: await dg('HND'), GAJ: await dg('GAJ'), IBR: await dg('IBR') });
check('観光地の度合い：IATA のある空港はすべて表にある・0.5〜1.5',
  Number(await q1(`select count(*) from airports a where a.iata ~ '^[A-Z]{3}$' and not exists (select 1 from co3_tourism t where t.iata = a.iata)`)) === 0
  && Number(await q1(`select count(*) from co3_tourism where degree < 0.5 or degree > 1.5`)) === 0, null);

// A は石垣と那覇でチェックイン（前の7日に2空港）
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
    ('${A}', ${ids.ISG}, 24.4, 124.2, 10, now() - interval '1 day', now() - interval '1 day'),
    ('${A}', ${ids.OKA}, 26.2, 127.6, 10, now() - interval '2 day', now() - interval '2 day')`);
await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 100000, satisfaction = 60 where user_id = '${A}'`);
await db.exec(`update companies set rating = 5`).catch(() => {});
let s = await as(A, `select public.co3_set_policy('regional')`);
check('方針を地域航空にできる・上級席は0%', s.policy === 'regional' && s.premium === 0, { p: s.policy, pr: s.premium });
check('地域航空は上級席を選べない', String(await as(A, `select public.co3_set_premium(10)`)).includes('premium not allowed'), null);
check('旅客機は小型機として買えない', String(await as(A, `select public.co3_buy_small('B738')`)).includes('not a small'), null);
s = await as(A, `select public.co3_buy_small('C208')`);
s = await as(A, `select public.co3_buy_small('PC12')`);
s = await as(A, `select public.co3_buy_small('R44')`);
const regs = (await db.query(`select reg, paid from aircraft where user_id = '${A}' order by id`)).rows;
check('小型機の値段：表のまま、持っている機体は0.5機と数える（1,600・1,700×1.125・500×1.25）',
  regs.map((r) => Number(r.paid)).join(',') === '1600,1913,625', regs);
check('登録記号は SM- で始まる', regs.every((r) => /^SM-[0-9A-F]{4}$/.test(r.reg)), regs);

// 本拠地がないうちは遊覧なし。チャーターは2空港 × 3件 ＝ 6件、1機1日 席数 × 4.3 × はじめの上乗せ 1.5
let jobs = s.jobs;
check('本拠地なし：3機ともチャーター（席数 × 4.3 × 1.5）', jobs.length === 3 && jobs.every((j) => j.job === 'charter')
  && near(jobs.reduce((a, j) => a + Number(j.earn), 0), (9 + 8 + 3) * 4.3 * 1.5, 0.05), jobs);
// 本拠地を石垣（度合い1.5）に：遊覧は 9機まで、1席 3.8 × 1.5 ＝ 5.7 でチャーターより大きいので、3機とも遊覧
s = await as(A, `select public.co3_set_home(${ids.ISG})`);
jobs = s.jobs;
check('本拠地 石垣：3機とも遊覧（席数 × 5.7 × 1.5）', jobs.every((j) => j.job === 'sightseeing' && j.airport === 'ISG')
  && near(jobs.reduce((a, j) => a + Number(j.earn), 0), (9 + 8 + 3) * 5.7 * 1.5, 0.05), jobs);
check('1日の収益に仕事の稼ぎが入る（維持費の前）', near(Number(s.gross), (9 + 8 + 3) * 5.7 * 1.5, 1), { g: s.gross });

// 定期便の補助：羽田⇄山形（地方の路線）に ATR72 を入れる。本物の便がない表だけの客 約104人、8便 × 70席 → 搭乗率 18.6%
await db.exec(`insert into flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
    ('${A}', ${ids.HND}, ${ids.GAJ}, now() - interval '3 day', now() - interval '3 day' + interval '60 minutes', 300),
    ('${A}', ${ids.ISG}, ${ids.OKA}, now() - interval '4 day', now() - interval '4 day' + interval '60 minutes', 400);
  insert into aircraft (user_id, type, icao, paid, route_key) values
    ('${A}', 'prop', 'AT76', 7500, '${Math.min(ids.HND, ids.GAJ)}-${Math.max(ids.HND, ids.GAJ)}'),
    ('${A}', 'prop', 'AT76', 7500, '${Math.min(ids.ISG, ids.OKA)}-${Math.max(ids.ISG, ids.OKA)}');
  -- はじめの上乗せ（1.5倍）があると離島の路線も黒字になるので、会社を作って200日たった形で確かめる
  update companies set created_at = now() - interval '200 days' where user_id = '${A}';`);
s = await as(A, `select public.co_state()`);
const hg = `${Math.min(ids.HND, ids.GAJ)}-${Math.max(ids.HND, ids.GAJ)}`, io = `${Math.min(ids.ISG, ids.OKA)}-${Math.max(ids.ISG, ids.OKA)}`;
const e1 = s.econ.find((x) => x.k === hg), b1 = s.subsidy.find((x) => x.k === hg);
const cap = e1.flights * Number(e1.seats);
check('地方の路線：搭乗率60%に届かない分の運賃を自治体が払う', b1.kind === 'local' && Number(b1.load) < 0.6
  && near(Number(b1.subsidy), (0.6 * cap - Number(e1.carried)) * Number(e1.revenue) / Number(e1.carried), 0.05), { e1, b1 });
const e2 = s.econ.find((x) => x.k === io), b2 = s.subsidy.find((x) => x.k === io);
check('離島の路線：赤字を補う（赤字 ＋ 補助 ＝ 0）', b2.kind === 'island' && Number(e2.profit) < 0 && near(Number(e2.profit) + Number(b2.subsidy), 0, 0.01), { e2, b2 });
check('路線に入れた機体は仕事に入らない', s.jobs.length === 3, s.jobs);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
