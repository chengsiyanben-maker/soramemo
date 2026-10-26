// エアライン経営 co-v3：機種の表
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
const A = '00000000-0000-0000-0000-00000000000a';
await db.exec(`insert into auth.users (id) values ('${A}')`);
const as = async (uid, sql) => { try { await db.exec(`set role authenticated; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];

const cnt = (await db.query(`select kind, count(*)::int as n from co3_types group by kind order by kind`)).rows.map((r) => `${r.kind}${r.n}`).join(',');
check('機種の数：ビジネスジェット10・貨物機8・ヘリ2・旅客機28・小型機4', cnt === 'bizjet10,freighter8,heli2,pax28,small4', cnt);
check('B737-800 は 170席・15,300・維持費15（仕様書の表）', (await q1(`select seats || '/' || price || '/' || upkeep from co3_types where code = 'B738'`)) === '170/15300/15', null);
const look = await q1(`select string_agg(coalesce(public.co3_type_of(x), '-'), ',') from unnest(array['A359', '359', 'B738', '73H', 'DH8D', 'DH4', 'E170', 'B77W', 'B77L', 'xyz', '']) x`);
check('記号から機種：ICAO も時刻表も（777F は B77L）', look === 'A359,A359,B738,B738,DH8D,DH8D,E170,B77W,B77F,-,-', look);
check('翼の幅：B737-800 C・B767 D・B787 E・A380 F', (await q1(`select string_agg(wing, '' order by code) from co3_types where code in ('A388','B738','B763','B789')`)) === 'FCDE', null);
check('機種の表はだれでも読める', Number(await as(A, `select count(*) from co3_types`)) === 52, null);
check('アプリから書き換えられない', String(await as(A, `update co3_types set price = 1 where code = 'B738'`)).startsWith('ERROR') || (await q1(`select price from co3_types where code = 'B738'`)) === 15300, null);

// 会社の機体の数字：機種が分かれば表、分からなければ大きさの区分の目安
await db.exec(`insert into companies (user_id) values ('${A}');
  insert into aircraft (user_id, type, icao, paid) values ('${A}', 'lg', 'A359', 1000), ('${A}', 'nb', null, 1000), ('${A}', 'wb', '763', 1000)`);
const specs = (await db.query(`select (public.co3_ac_spec(id)).* from aircraft where user_id = '${A}' order by id`)).rows;
check('A350-900：369席・280t・大きいジェット・E', specs[0].code === 'A359' && Number(specs[0].seats) === 369 && Number(specs[0].mtow) === 280 && specs[0].noise === 'wide' && specs[0].wing === 'E' && specs[0].wide, specs[0]);
check('機種が分からない小型ジェット：目安の170席', specs[1].code === null && Number(specs[1].seats) === 170 && specs[1].wide === false, specs[1]);
check('時刻表の記号 763：B767-300ER 270席・D（中型以上）', specs[2].code === 'B763' && Number(specs[2].seats) === 270 && specs[2].wide === true, specs[2]);
check('本物の便の座席：E170 は機種の表で76席、記号がなければ170席', Number(await q1(`select public.co3_seats_of('E170', null)`)) === 76 && Number(await q1(`select public.co3_seats_of(null, null)`)) === 170, null);

if (bad) { console.log(`NG ${bad}`); process.exit(1); } else console.log('すべて OK');
