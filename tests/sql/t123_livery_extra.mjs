// 移行184：特別塗装機の一覧の足し分（livery_extra）と、海外の塗装機の便のふだん着く空港（livery_inbound_usual）
//   1. 誰でも読める・anon と authenticated は書けない・service_role は書ける（RLS）
//   2. 出典は https 必須・Flightradar24 は入らない・登録記号の形・終わる日が始まる日より前は入らない
//   3. livery_inbound_usual は到着（dep_here=0）だけ・曜日ごとの行を優先・service_role だけが呼べる
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of fs.readdirSync(dir).sort()) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const fails = async (sql, role) => { try { if (role) await db.exec(`set role ${role}`); await db.exec(sql); return false; } catch { return true; } finally { await db.exec('reset role'); } };

// 1
check('RLS が有効', (await db.query(`select relrowsecurity r from pg_class where relname = 'livery_extra'`)).rows[0].r === true, null);
check('service_role は書ける', !(await fails(`insert into public.livery_extra (reg, name, airline, kind, src) values ('G-YMMU', 'ワンワールド塗装（777-200ER）', 'ブリティッシュ・エアウェイズ', 'alliance', 'https://example.org/ba')`, 'service_role')), null);
await db.exec('set role anon');
const r = (await db.query(`select reg, kind from public.livery_extra`)).rows;
await db.exec('reset role');
check('anon は読める', r.length === 1 && r[0].kind === 'alliance', r);
check('anon は書けない', await fails(`insert into public.livery_extra (reg, name, airline, src) values ('B-12345', 'x', 'x', 'https://example.org/')`, 'anon'), null);
check('authenticated は書き換えられない', await fails(`update public.livery_extra set name = 'x'`, 'authenticated') || (await db.query(`select name from public.livery_extra`)).rows[0].name !== 'x', null);
check('authenticated は消せない', await fails(`delete from public.livery_extra`, 'authenticated') || (await db.query(`select count(*)::int c from public.livery_extra`)).rows[0].c === 1, null);

// 2
check('Flightradar24 の出典は入らない', await fails(`insert into public.livery_extra (reg, name, airline, src) values ('B-12345', 'x', 'x', 'https://www.flightradar24.com/blog/x')`), null);
check('http の出典は入らない', await fails(`insert into public.livery_extra (reg, name, airline, src) values ('B-12345', 'x', 'x', 'http://example.org/')`), null);
check('出典なしは入らない', await fails(`insert into public.livery_extra (reg, name, airline, src) values ('B-12345', 'x', 'x', null)`), null);
check('登録記号の形が違うと入らない', await fails(`insert into public.livery_extra (reg, name, airline, src) values ('g ymmu', 'x', 'x', 'https://example.org/')`), null);
check('kind は special・alliance だけ', await fails(`insert into public.livery_extra (reg, name, airline, kind, src) values ('B-12345', 'x', 'x', 'other', 'https://example.org/')`), null);
check('終わる日が始まる日より前は入らない', await fails(`insert into public.livery_extra (reg, name, airline, src, from_day, until_day) values ('B-12345', 'x', 'x', 'https://example.org/', '2026-12-01', '2026-11-01')`), null);
check('kind を書かなければ special', !(await fails(`insert into public.livery_extra (reg, name, airline, src) values ('B-18101', 'ピカチュウジェットCI', 'チャイナエアライン', 'https://example.org/ci')`)) &&
  (await db.query(`select kind from public.livery_extra where reg = 'B-18101'`)).rows[0].kind === 'special', null);

// 3
const dow = (await db.query(`select extract(dow from (now() at time zone 'Asia/Tokyo'))::int d`)).rows[0].d;
await db.exec(`insert into public.foreign_usual (callsign, iata, dep_here, dow, mins, n, spread, last_day) values
  ('BAW5', 'HND', 0, -1, 600, 8, 10, current_date), ('BAW5', 'HND', 0, ${dow}, 615, 3, 5, current_date),
  ('BAW5', 'HND', 1, -1, 700, 8, 10, current_date), ('EVA198', 'NRT', 0, ${(dow + 1) % 7}, 500, 3, 5, current_date)`);
const u = (await db.query(`select * from public.livery_inbound_usual(array['BAW5', 'EVA198'])`)).rows;
check('到着だけ・曜日ごとの行を優先（BAW5 は 615）・その日の曜日でない行は出ない', u.length === 1 && u[0].callsign === 'BAW5' && u[0].iata === 'HND' && u[0].mins === 615, u);
check('anon は呼べない', await fails(`select * from public.livery_inbound_usual(array['BAW5'])`, 'anon'), null);
check('authenticated は呼べない', await fails(`select * from public.livery_inbound_usual(array['BAW5'])`, 'authenticated'), null);
check('service_role は呼べる', !(await fails(`select * from public.livery_inbound_usual(array['BAW5'])`, 'service_role')), null);
const many = Array.from({ length: 80 }, (_, i) => `'X${i}'`).join(',');
check('たくさん渡しても動く（先頭50だけ見る）', !(await fails(`select * from public.livery_inbound_usual(array[${many}])`)), null);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('すべて OK');
