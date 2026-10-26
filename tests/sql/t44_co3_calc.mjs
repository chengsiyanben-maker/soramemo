// エアライン経営 co-v3：仕様書（2026年10月26日）の計算の関数。仕様書に書いた例の数字が出るかを確かめる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const n = async (sql) => Number(await q(sql));
const near = (a, b, tol = 0.05) => Math.abs(a - b) <= tol;

// 運賃と費用
check('運賃：830km で約0.5', near(await n(`select co3.fare(830)`), 0.499, 0.001), await n(`select co3.fare(830)`));
const be = await q(`select string_agg(((co3.policy(p)).breakeven)::text, ',' order by p) from unnest(array['fsc','lcc','mcc']) p`);
check('赤字になる搭乗率：FSC 50%・LCC 40%・ミドルコスト 45%', be === '0.50,0.40,0.45', be);
const cost = await n(`select co3.flight_cost('fsc', 170, 830)`);
check('B737（170席）羽田⇄新千歳の1便の費用は、搭乗率50%の収益と同じ', near(cost, 170 * 0.5 * 0.499, 0.01), cost);
check('旅行の客は運賃1.2倍で 1/1.728 に', near(await n(`select co3.fare_weight(1.2, false)`), 1 / 1.728, 0.001), null);

// 空港の大きさ（令和7年の1日の乗降客数）
const sz = await q(`select string_agg(co3.airport_size(x), ',') from unnest(array[250801, 112713, 8038, 3535, 1009]::numeric[]) x`);
check('空港の大きさ：羽田 超大規模・成田 拠点・広島 大規模・秋田 中規模・山形 小規模', sz === 'xl,hub,large,mid,small', sz);
check('海外の空港は拠点', await q(`select co3.airport_size(0, true)`) === 'hub', null);

// 路線のお客さん
check('本物の便：羽田⇄山形（1日4便・85席）で約120人', near(await n(`select co3.route_pax_real(4, 85)`), 119, 0.5), null);
// 令和7年の国内の旅客数：広島 2,487,401・秋田 1,257,846、全国の合計 228,369,366
const hs = await n(`select co3.route_pax_nodirect(2487401, 1257846, 228369366, 900)`);
check('本物の便がない路線：広島⇄秋田で約19人', near(hs, 18.8, 0.3), hs);
check('本物の便がない路線は最低10人', await n(`select co3.route_pax_nodirect(368401, 2898553, 228369366, 830)`) === 10, null);
check('近い路線は 0.3 倍', near(await n(`select co3.route_pax_nodirect(9e7, 9e7, 228369366, 250)`) / await n(`select co3.route_pax_nodirect(9e7, 9e7, 228369366, 900)`), 0.3, 0.001), null);
const sh = await q(`select string_agg(round(co3.route_share(x) * 100)::text, ',') from unnest(array[1,2,3,5,10,20]) x`);
check('1社あたりの客：1社100%・2社75%・3社67%・5社60%・10社30%・20社15%', sh === '100,75,67,60,30,15', sh);

// 地元の応援
check('地元の応援：大規模 ×3（広島⇄秋田 19人 → 57人、最低500人なし）', near(await n(`select co3.local_support('large', 19, false, 40)`), 57, 0.01), null);
check('本物の便がある本拠地の路線は最低500人（山形 小規模 80人 → 500人）', await n(`select co3.local_support('small', 80, true, 40)`) === 500, null);
check('本拠地にして30日たつまでは効かない', await n(`select co3.local_support('small', 80, true, 10)`) === 80, null);
check('拠点以上は ×1', await n(`select co3.local_support('hub', 800, true, 40)`) === 800, null);

// 上乗せ
check('上乗せの最大：1.4 × 1.6 × 1.25 ＝ 2.8倍', near(await n(`select co3.bonus_mult(0.9, 0.9, 0.9)`), 2.8, 0.001), null);
check('はじめの上乗せ：60日目 1.5・61日目 1.3・91日目 1.15・121日目 1', await q(`select string_agg(co3.newbie_mult(d)::text, ',') from unnest(array[60,61,91,121]) d`) === '1.5,1.3,1.15,1', null);

// 着陸料
const b737 = await n(`select co3.landing_fee(false, false, 119, 'jet', 79, false, false)`);
check('着陸料：B737-800（客119人）で約3.8', near(b737, 3.81, 0.02), b737);
const b789 = await n(`select co3.landing_fee(true, false, 0, 'wide', 254, false, false)`);
check('着陸料：B787-9 の国際線で約11', near(b789, 10.8, 0.1), b789);
const b789h = await n(`select co3.landing_fee(true, false, 0, 'wide', 254, true, false)`);
check('着陸料：羽田の B787-9 の国際線で約18', near(b789h, 18.0, 0.1), b789h);
check('離島は半分', near(await n(`select co3.landing_fee(false, false, 119, 'jet', 79, false, true)`), b737 / 2, 0.001), null);

// 発着枠と混雑料金
check('羽田の枠：80回 × 17時間、遊ぶ会社500社で約13,600便', await n(`select co3.slot_capacity(80, 17, 500)`) === 13600, null);
check('遊ぶ会社が50社より少なくても1倍', await n(`select co3.slot_capacity(80, 17, 10)`) === 1360, null);
check('枠に収まれば申し込みどおり', await n(`select co3.slot_allot(10, 1000, 1360)`) === 10, null);
check('1.25倍の申し込みなら8割（10便 → 8便）', await n(`select co3.slot_allot(10, 1700, 1360)`) === 8, null);
check('どの会社も最低4便', await n(`select co3.slot_allot(6, 10000, 1360)`) === 4, null);
const cr = await q(`select string_agg(round(co3.congestion_rate(x, 100) * 100)::text, ',') from unnest(array[90, 125, 150, 200, 300]::numeric[]) x`);
check('混雑料金：枠に収まれば0%・1.25倍で5%・1.5倍で10%・2倍で20%・上限20%', cr === '0,5,10,20,20', cr);
check('羽田の地方の枠の路線は半分', near(await n(`select co3.congestion_rate(150, 100, true)`), 0.05, 0.0001), null);

// 機体
check('翼の幅：B737（35.8m）C・B767（47.6m）D・B787（60.1m）E・A380（79.8m）F',
  await q(`select string_agg(co3.wing_class(x), '') from unnest(array[35.8, 47.6, 60.1, 79.8]) x`) === 'CDEF', null);
check('記録が多い空港は本物で発着した最大の区分', await q(`select co3.airport_wing_cap('E', 3000, 2500, 45)`) === 'E', null);
check('記録が少なく 1,200m 未満は B', await q(`select co3.airport_wing_cap(null, 10, 800, 25)`) === 'B', null);
check('記録が少なく 2,500m×45m は D（E・F は記録がないと入れない）', await q(`select co3.airport_wing_cap(null, 0, 2500, 45)`) === 'D', null);
check('記録が少ない空港で、ジェット機は 2,000m×45m が要る', (await q(`select co3.can_land('C', true, 'C', 10, 1800, 45)`)) === false && (await q(`select co3.can_land('C', false, 'C', 10, 1800, 45)`)) === true, null);
check('機体の値段：最初は半額、3機持っていると +75%', await n(`select co3.aircraft_price(15300, 0, true)`) === 7650 && await n(`select co3.aircraft_price(15300, 3, false)`) === 26775, null);
check('小型機・プロペラ機は0.5機と数える', await n(`select co3.aircraft_price(7500, 4 * co3.count_weight(true), false)`) === 11250, null);

// 貨物（令和7年：羽田の国内 476,065t、那覇 177,597t、那覇の相手の合計の目安 約890,000t）
const oka = await n(`select co3.cargo_dom_route(177597, 476065, 889000)`);
check('貨物：羽田⇄那覇 約260〜280トン/日', oka > 255 && oka < 285, oka);
check('国際線の区間：羽田（742,846t/年）の便の2割の区間で約407トン', near(await n(`select co3.cargo_intl_route(742846, 20, 100)`), 407, 1), null);
check('貨物機の分は7割、国際線1トン＝4席分', near(await n(`select co3.cargo_for_freighters(100)`), 70, 0.001) && await n(`select co3.cargo_seat_eq(true)`) === 4, null);

// プライベートジェット・地域航空
check('VIP の客：羽田⇄那覇（客 約5,900人/日）× リゾート20%', near(await n(`select co3.vip_pax(5880, 'resort')`), 1176, 0.5), null);
check('ATR72（70席）：遊覧（度合い1.5）約400・チャーター約300', near(await n(`select co3.regional_job(70, 'sightseeing', 1.5)`), 399, 0.5) && near(await n(`select co3.regional_job(70, 'charter')`), 301, 0.5), null);
check('セスナ172（4席）：遊覧 約23・チャーター 約17', near(await n(`select co3.regional_job(4, 'sightseeing', 1.5)`), 22.8, 0.1) && near(await n(`select co3.regional_job(4, 'charter')`), 17.2, 0.1), null);
check('遊覧の上限：度合い0.5で3機・1.5で9機。チャーターは空港ごとに週3件', await n(`select co3.sightseeing_cap(0.5)`) === 3 && await n(`select co3.sightseeing_cap(1.5)`) === 9 && await n(`select co3.charter_jobs_per_week(2)`) === 6, null);

// アプリからは呼べない
await db.exec(`set role authenticated`);
let denied = false; try { await db.query(`select co3.fare(100)`); } catch (e) { denied = true; }
await db.exec(`reset role`);
check('アプリ（authenticated）からは呼べない', denied, null);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
