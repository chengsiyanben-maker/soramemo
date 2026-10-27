// 撮影の知らせ：push_subs の撮影の設定は決まった値だけ入る。知らせた記録（spot_notified）は誰からも読めず、購読を消すと一緒に消える
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
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const run = async (sql) => { try { const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } };
const ins = (n, more) => run(`insert into public.push_subs (endpoint, p256dh, auth, spot_iata, spot_kinds, spot_lead, spot_regs, spot_flights) values ('https://fcm.googleapis.com/${n}', 'k', 'a', ${more}) returning id`);

const id = await ins('a', `'HND', '{special,big,ops}', 5, '{JA01XJ}', '{JL123@2026-10-21}'`);
check('撮影の設定が入る', typeof id === 'number', id);
check('知らせる時間は3・5・10分だけ', String(await ins('b', `'HND', '{big}', 7, '{}', '{}'`)).startsWith('ERROR'));
check('知らない種類は入らない', String(await ins('c', `'HND', '{all}', 5, '{}', '{}'`)).startsWith('ERROR'));
check('空港の記号は3文字だけ', String(await ins('d', `'hnd', '{big}', 5, '{}', '{}'`)).startsWith('ERROR'));
check('指定した機体は10機まで', String(await ins('e', `'HND', '{reg}', 5, '{A,B,C,D,E,F,G,H,I,J,K}', '{}'`)).startsWith('ERROR'));
await run(`insert into public.spot_notified (sub_id, key) values (${id}, 'JAL123@2026-10-21')`);
check('同じ機体の知らせは1日1回（重ねて入らない）', String(await run(`insert into public.spot_notified (sub_id, key) values (${id}, 'JAL123@2026-10-21')`)).startsWith('ERROR'));
for (const role of ['anon', 'authenticated']) {
  await db.exec(`set role ${role}`);
  check(`${role} は知らせた記録を読めない`, String(await run(`select count(*) from public.spot_notified`)).startsWith('ERROR'));
  await db.exec(`reset role`);
}
await run(`delete from public.push_subs where id = ${id}`);
check('購読を消すと知らせた記録も消える', Number(await run(`select count(*) from public.spot_notified`)) === 0);
if (bad) { console.error(`${bad} 件 NG`); process.exit(1); }
