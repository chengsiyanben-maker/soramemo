// エアライン経営 co-v3：画面のための co_state の足し算（機体の種類・小型機の一覧）
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
let s = await as(A, `select public.co_state()`);
await db.exec(`update companies set cash = 10000000`);
check('FSC には小型機の一覧を出さない', s.small == null, s.small);
// 機体の種類：旅客機・貨物機（co3_code）・ビジネスジェット・小型機
await db.exec(`insert into aircraft (user_id, type, paid, reg, icao, co3_code) values
  ('${A}', 'nb', 1000, 'JA01AA', 'B738', null), ('${A}', 'lg', 1000, 'JA11KZ', 'B748', 'B748F'),
  ('${A}', 'rj', 1000, 'JA500G', 'GLF6', 'GLF6'), ('${A}', 'prop', 1000, 'SM-0001', 'C208', 'C208')`);
s = await as(A, `select public.co_state()`);
const k = Object.fromEntries(s.fleet.map((f) => [f.reg, f.kind]));
check('機体の種類：旅客機 pax・貨物機 freighter・ビジネスジェット bizjet・小型機 light', k.JA01AA === 'pax' && k.JA11KZ === 'freighter' && k.JA500G === 'bizjet' && k['SM-0001'] === 'light', k);
// 地域航空：小型機の一覧と値段（持っている機体：旅客機など3機 ×1 ＋ 小型機 ×0.5 ＝ 3.5 → ×1.875）
await as(A, `select public.co3_set_policy('regional')`);
s = await as(A, `select public.co_state()`);
const c208 = (s.small || []).find((x) => x.code === 'C208');
check('地域航空：小型機6機種の一覧', (s.small || []).length === 6, s.small);
check('値段は co3_buy_small と同じ（1,600 × 1.875 ＝ 3,000）', c208 && Number(c208.price) === 3000, c208);
const before = Number(s.cash); s = await as(A, `select public.co3_buy_small('C208')`);
check('買うと同じ額が減る（維持費の精算 ±2）', Math.abs(before - Number(s.cash) - 3000) <= 2, { before, after: s.cash });
// 決めた便数（plans）：路線がないと決められない。決めていなければ空
check('決めた便数：はじめは空', s.plans && Object.keys(s.plans).length === 0, s.plans);
check('路線がない区間は便数を決められない', String(await as(A, `select public.co3_set_flights('x-y', 4)`)).includes('route not found'), null);
// スイッチがオフなら種類も一覧も出さない
await db.exec(`update ops.flags set value = 'false' where key = 'co_v3'`);
s = await as(A, `select public.co_state()`);
check('スイッチがオフ：kind も small も出さない', s.fleet.every((f) => f.kind == null) && s.small == null, { f: s.fleet.map((f) => f.kind), small: s.small });
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
