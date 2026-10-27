// エアライン経営 co-v3：仕事の客が多い路線の運賃の上がり方（FSC・ミドルコストだけ、最大 +20%）
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
const n = async (sql) => Number(Object.values((await db.query(sql)).rows[0])[0]);
check('大きい空港どうし（仕事の客 60%）FSC：+20%', await n(`select co3.biz_fare_rise('fsc', 0.60)`) === 0.2, null);
check('地方（45%）ミドルコスト：+10%', Math.abs(await n(`select co3.biz_fare_rise('mcc', 0.45)`) - 0.1) < 1e-9, null);
check('リゾート（12%）：0%', await n(`select co3.biz_fare_rise('fsc', 0.12)`) === 0, null);
check('LCC・地域航空は上げない', await n(`select co3.biz_fare_rise('lcc', 0.60)`) === 0 && await n(`select co3.biz_fare_rise('regional', 0.60)`) === 0, null);
check('上限は +20%', await n(`select co3.biz_fare_rise('fsc', 0.95)`) === 0.2, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
