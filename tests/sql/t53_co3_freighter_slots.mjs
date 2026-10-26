// エアライン経営 co-v3：旅客の会社の貨物機（1割まで）と、貨物機の発着枠
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
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const ids = Object.fromEntries((await db.query(`select iata, id from airports where iata in ('HND','CTS')`)).rows.map((r) => [r.iata, r.id]));
const hc = `${Math.min(ids.HND, ids.CTS)}-${Math.max(ids.HND, ids.CTS)}`;

// A・B とも羽田でチェックインして、貨物の会社の便の B763（羽田⇄新千歳）を見る
await db.exec(`insert into checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
    ('${A}', ${ids.HND}, 35.55, 139.78, 10, now() - interval '2 hours', now() - interval '2 hours'),
    ('${B}', ${ids.HND}, 35.55, 139.78, 10, now() - interval '2 hours', now() - interval '2 hours');
  insert into flight_history (svc_date, flight, dep, arr, std, sta, type, reg) values
    (((now() - interval '2 hours') at time zone 'Asia/Tokyo')::date, 'KZ201', 'HND', 'CTS', now() - interval '110 minutes', now() - interval '20 minutes', 'B763', 'JA01KZ'),
    (((now() - interval '2 hours') at time zone 'Asia/Tokyo')::date, 'KZ203', 'HND', 'CTS', now() - interval '100 minutes', now() - interval '10 minutes', 'B763', 'JA02KZ')`);
await as(A, `select public.co_state()`); await as(B, `select public.co_state()`);
await db.exec(`update companies set cash = 10000000, satisfaction = 60`);

// FSC（A）：機体がないうちは貨物機を持てない（10機で1機）
check('FSC：機体0機のうちは貨物機を持てない', String(await as(A, `select public.co3_buy_seen('JA01KZ')`)).includes('10 percent'), null);
await db.exec(`insert into aircraft (user_id, type, paid) select '${A}', 'nb', 1000 from generate_series(1, 9)`);
let s = await as(A, `select public.co3_buy_seen('JA01KZ')`);
check('FSC：9機持っていれば10機目に貨物機1機', !String(s).startsWith('ERROR'), s);
check('FSC：2機目の貨物機は持てない（11機で1割を超える）', String(await as(A, `select public.co3_buy_seen('JA02KZ')`)).includes('10 percent'), null);
// LCC（B）は持てない
await as(B, `select public.co3_set_policy('lcc')`);
check('LCC は貨物機を持てない', String(await as(B, `select public.co3_buy_seen('JA02KZ')`)).includes('cannot own freighters'), null);
// FSC の貨物機を貨物の路線（見た区間 羽田⇄新千歳）に入れると、貨物の内わけで稼ぐ
const fid = (await db.query(`select id from aircraft where reg = 'JA01KZ'`)).rows[0].id;
s = await as(A, `select public.co3_cargo_assign(${fid}, '${hc}')`);
let e = s.cargo.find((x) => x.k === hc);
check('FSC の貨物機は貨物の内わけで稼ぐ（B767F 52t・1日6便）', e && Number(e.payload) === 52 && e.flights === 6, e);
check('旅客の内わけには入らない', s.econ.filter((x) => x.k === hc).every((x) => x.flights === 0), s.econ);

// 発着枠：羽田の申し込みを枠（80回×17時間＝1,360便）の約1.5倍にする → A の貨物機の便も申し込みの割合で減る
await db.exec(`insert into auth.users (id) select gen_random_uuid() from generate_series(1, 50);
  insert into companies (user_id) select id from auth.users where id not in ('${A}', '${B}');
  insert into aircraft (user_id, type, route_key, paid) select id, 'nb', '${hc}', 1000 from auth.users where id not in ('${A}', '${B}');
  insert into co3_plans (user_id, route_key, flights) select id, '${hc}', 40 from auth.users where id not in ('${A}', '${B}');
  update companies set last_collect = now() - interval '60 days' where user_id not in ('${A}', '${B}');`);
const total = Number(await q1(`select total from public.co3_slot_totals() where iata = 'HND'`));
check('羽田の申し込み：50社×40便 ＋ A の6便 ＝ 2,006便', total === 2006, total);
s = await as(A, `select public.co_state()`);
e = s.cargo.find((x) => x.k === hc);
check('貨物機の便は 6 × 1,360 ÷ 2,006 → 4便（最低4便）', e.flights === Math.max(4, Math.floor(6 * 1360 / 2006)), e);
check('混雑料金もかかる', Number(e.congestion) > 0, e);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
