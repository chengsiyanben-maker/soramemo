// 運営への知らせ（移行 ops_alert）
//   1. 死活の記録に ng があれば、今日はじめての ops_alert_claim は send = true（項目の名前と最後の時刻だけ）
//   2. 届いた（done ok）あとは、同じ日は何度呼んでも send = false（already）＝1日1回
//   3. 届かなかったときは、試し直せる（1日6回まで）
//   4. ng がなければ送らない（reason ok）。日本時間の日が変われば、また送れる
//   5. 表に宛先の列がない。RLS 有効・anon / authenticated は読めない。関数は service_role だけ
//   6. cron（ops-alert）の文に上限、Edge Function の設定（verify_jwt = false）がある
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_ops_alert.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 400)); if (!ok) bad++; };
check('移行がある', !!mine);
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select null::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select '{}'::jsonb $$;
grant usage on schema public, auth to anon, authenticated, service_role;`);
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));

const claim = async () => (await db.query(`select public.ops_alert_claim() r`)).rows[0].r;
// 空のデータベースでは取り込みの記録がないので、ng がある
const c1 = await claim();
check('ng があれば送る（send true）', c1.send === true && Array.isArray(c1.items) && c1.items.length > 0, c1);
check('項目は key・label・last・limit_min だけ', c1.items.every(x => JSON.stringify(Object.keys(x).sort()) === '["key","label","last","limit_min"]'), c1.items[0]);
check('日は日本時間の今日', c1.day === (await db.query(`select ((now() at time zone 'Asia/Tokyo')::date)::text d`)).rows[0].d, c1.day);
// 届かなかった → 試し直せる
await db.query(`select public.ops_alert_done($1::date, false, 'mail 0 / hook 0 / failed 1')`, [c1.day]);
const c2 = await claim();
check('届かなかったら次も送る', c2.send === true, c2);
for (let i = 0; i < 6; i++) await claim();
const c3 = await claim();
const row = (await db.query(`select attempts, ok from ops.ops_alert_log`)).rows[0];
check('1日6回で止まる', c3.send === false && c3.reason === 'already' && row.attempts === 6 && row.ok === false, { c3, row });
// 届いた → その日はもう送らない
await db.exec(`update ops.ops_alert_log set attempts = 1`);
const c4 = await claim(); check('（試し直しの枠があれば送る）', c4.send === true, c4);
await db.query(`select public.ops_alert_done($1::date, true, 'mail 1 / hook 0 / failed 0')`, [c1.day]);
const c5 = await claim(); const c6 = await claim();
check('届いたあとは同じ日は送らない（1日1回）', c5.send === false && c5.reason === 'already' && c6.send === false, [c5, c6]);
await db.query(`select public.ops_alert_done($1::date, false, 'x')`, [c1.day]);
check('あとから失敗を書いても、届いた印は消えない', (await db.query(`select ok from ops.ops_alert_log`)).rows[0].ok === true);
// 日が変われば、また送れる（前の日の行に見立てる）
await db.exec(`update ops.ops_alert_log set day = day - 1`);
const c7 = await claim(); check('次の日はまた送る', c7.send === true, c7);
// ng がなければ送らない
await db.exec(`delete from ops.ops_alert_log; create or replace function ops.data_health() returns jsonb language sql stable as $$ select '[{"key":"a","label":"a","last":null,"limit_min":1,"ok":true}]'::jsonb $$;`);
const c8 = await claim();
check('ng がなければ送らない（reason ok）', c8.send === false && c8.reason === 'ok', c8);
check('送らないときは記録しない', (await db.query(`select count(*)::int n from ops.ops_alert_log`)).rows[0].n === 0);

// 権限・RLS
const cols = (await db.query(`select string_agg(column_name, ',' order by ordinal_position) c from information_schema.columns where table_schema = 'ops' and table_name = 'ops_alert_log'`)).rows[0].c;
check('表に宛先の列がない', !/to|mail|addr|url|target/.test(cols), cols);
const p = (await db.query(`select has_function_privilege('anon', 'public.ops_alert_claim()', 'execute') a, has_function_privilege('authenticated', 'public.ops_alert_claim()', 'execute') u,
  has_function_privilege('service_role', 'public.ops_alert_claim()', 'execute') s, has_function_privilege('authenticated', 'public.ops_alert_done(date, boolean, text)', 'execute') d,
  has_function_privilege('service_role', 'public.ops_alert_done(date, boolean, text)', 'execute') ds,
  has_table_privilege('authenticated', 'ops.ops_alert_log', 'select') t, (select relrowsecurity from pg_class where oid = 'ops.ops_alert_log'::regclass) rls`)).rows[0];
check('claim・done は service_role だけ', p.a === false && p.u === false && p.s === true && p.d === false && p.ds === true, p);
check('表は authenticated から読めない・RLS 有効', p.t === false && p.rls === true, p);
const cfg = (await db.query(`select string_agg(array_to_string(proconfig, ','), ' | ') c from pg_proc where proname in ('ops_alert_claim', 'ops_alert_done')`)).rows[0].c;
check('関数に上限（statement_timeout）', /statement_timeout=30s/.test(cfg) && /statement_timeout=10s/.test(cfg), cfg);
const sql = fs.readFileSync(dir + mine, 'utf8');
check("cron（ops-alert）は毎時41分・上限10秒・ロック待ち5秒", /cron\.schedule\('ops-alert', '41 \* \* \* \*', \$job\$ set statement_timeout = '10s'; set lock_timeout = '5s';/.test(sql));
check('移行に宛先・鍵を書いていない', !/@[a-z0-9-]+\.[a-z]|OPS_SMTP_PASS\s*=|password/i.test(sql.replace(/OPS_ALERT_TO|OPS_SMTP_\*/g, '')));
const toml = fs.readFileSync(new URL('../../supabase/config.toml', import.meta.url), 'utf8');
check('config.toml に ops-alert（verify_jwt = false）', /\[functions\.ops-alert\]\nverify_jwt = false/.test(toml));
console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
