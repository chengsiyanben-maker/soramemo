// データ担当：退会の精算を支える変更（経営の担当からの依頼）
//   1. delete-account は deleteUser の前に co3_leave_settle を呼び、失敗したら止める（ソースの順番を確かめる）
//   2. co3_news の種類に 'partner' が入る（前からの種類も入る・決まりにない種類は断る）
//   3. co3_codeshares.paid_amount（空でもよい・マイナスは断る・RLS はいまのまま）
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
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b', C = '00000000-0000-0000-0000-00000000000c';
await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}'), ('${C}')`);
const as = async (role, uid, sql) => { try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const tryq = async (sql) => { try { await db.exec(sql); return 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } };

// 1. delete-account の順番
const src = fs.readFileSync(new URL('../../supabase/functions/delete-account/index.ts', import.meta.url), 'utf8');
const iSettle = src.indexOf('admin.rpc("co3_leave_settle", { p_uid: user.id })'), iDel = src.indexOf('admin.auth.admin.deleteUser('), iStripe = src.indexOf('stripe.subscriptions.cancel(');
check('delete-account：精算を呼ぶ', iSettle > 0, iSettle);
check('delete-account：精算は deleteUser より前', iSettle > 0 && iSettle < iDel, { iSettle, iDel });
check('delete-account：精算は定期支払いの停止より前', iSettle > 0 && iSettle < iStripe, { iSettle, iStripe });
check('delete-account：精算の失敗で止める', /if \(settleError\) throw settleError;/.test(src.slice(iSettle, iDel)), null);
check('精算はアプリから呼べない', String(await as('authenticated', A, `select public.co3_leave_settle('${A}')`)).startsWith('ERROR: permission denied'), null);
check('精算はサーバー（service_role）から呼べる', !String(await as('service_role', '', `select public.co3_leave_settle('${A}')`)).startsWith('ERROR'), await as('service_role', '', `select public.co3_leave_settle('${A}')`));

// 2. ニュースの種類
for (const k of ['route', 'god', 'rating', 'value', 'slots', 'event', 'partner'])
  check(`ニュースの種類 ${k} が入る`, await tryq(`insert into co3_news (user_id, kind, ref, title) values ('${A}', '${k}', 't87', 'テスト')`) === 'ok', k);
check('決まりにない種類は断る', (await tryq(`insert into co3_news (user_id, kind, ref, title) values ('${A}', 'nope', 't87', 'テスト')`)).includes('co3_news_kind_check'), null);
await db.exec(`delete from co3_news where ref = 't87'`);
await db.exec(`select co3_leave_news('${B}', 't87-leave', '相手の会社が退会しました', null)`);
check('退会の知らせは partner で入る', await q1(`select kind from co3_news where user_id = '${B}' and ref = 't87-leave'`) === 'partner', null);
check('ニュースは本人だけが読める（RLS はいまのまま）', Number(await as('authenticated', C, `select count(*) from co3_news where user_id = '${B}'`)) === 0
  && Number(await as('authenticated', B, `select count(*) from co3_news where user_id = '${B}'`)) === 1, null);

// 3. paid_amount
const col = (await db.query(`select data_type, is_nullable, column_default from information_schema.columns where table_name = 'co3_codeshares' and column_name = 'paid_amount'`)).rows[0];
check('paid_amount は bigint・空でよい・既定は空', col && col.data_type === 'bigint' && col.is_nullable === 'YES' && col.column_default == null, col);
await db.exec(`insert into co3_codeshares (op_id, seller_id, route_key, kind, status, paid_month) values ('${A}', '${B}', '1-2', 'block', 'active', date_trunc('month', now())::date)`);
const id = await q1(`select id from co3_codeshares where op_id = '${A}' and seller_id = '${B}'`);
check('すでにある行の paid_amount は空のまま', await q1(`select paid_amount from co3_codeshares where id = ${id}`) == null, null);
check('マイナスは断る', (await tryq(`update co3_codeshares set paid_amount = -1 where id = ${id}`)).startsWith('ERROR'), null);
check('0 以上は入る', await tryq(`update co3_codeshares set paid_amount = 123456 where id = ${id}`) === 'ok', null);
check('販売会社は払った額を読める', Number(await as('authenticated', B, `select paid_amount from co3_codeshares where id = ${id}`)) === 123456, null);
check('運航会社も読める', Number(await as('authenticated', A, `select paid_amount from co3_codeshares where id = ${id}`)) === 123456, null);
check('ほかの人は読めない', await as('authenticated', C, `select paid_amount from co3_codeshares where id = ${id}`) === 'ok', null);
check('アプリからは書けない', String(await as('authenticated', B, `update co3_codeshares set paid_amount = 0 where id = ${id}`)).startsWith('ERROR: permission denied'), null);
check('RLS は有効のまま', await q1(`select relrowsecurity from pg_class where relname = 'co3_codeshares'`) === true, null);

check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
