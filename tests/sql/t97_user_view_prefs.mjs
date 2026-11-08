// 表示の設定の表（user_view_prefs）：本人だけ読み書き・退会で消える・提案は1回だけ・rev と日時はサーバーが入れる
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
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email) values ('${A}', 'a@example.com'), ('${B}', 'b@example.com')`);
// その人として1文を流す（エラーなら 'ERROR: …'）
const as = async (role, uid, sql) => {
  try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid ?? ''}', false)`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; }
  catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; }
  finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false)`); }
};
const isErr = (v) => String(v).startsWith('ERROR');

check('RLS は有効', await q1(`select relrowsecurity from pg_class where relname = 'user_view_prefs'`) === true, null);
check('auth.users を on delete cascade で参照', await q1(`select confdeltype from pg_constraint where conrelid = 'public.user_view_prefs'::regclass and contype = 'f'`) === 'c', null);

// 作る：rev・提案の日時はサーバーが入れる
const ins = await as('authenticated', A, `insert into public.user_view_prefs (user_id, prefs) values ('${A}', '{"off": {"home": ["event"]}, "tabs": ["home", "ops"]}') returning rev`);
check('本人は自分の行を作れる（rev は1）', ins === 1, ins);
check('ほかの人の行は作れない', isErr(await as('authenticated', A, `insert into public.user_view_prefs (user_id) values ('${B}')`)), null);
check('rev は自分で入れられない', isErr(await as('authenticated', B, `insert into public.user_view_prefs (user_id, rev) values ('${B}', 99)`)), null);
check('提案の日時は自分で入れられない', isErr(await as('authenticated', B, `insert into public.user_view_prefs (user_id, suggest_shown_at) values ('${B}', now())`)), null);
check('ログインしていない人は作れない', isErr(await as('anon', null, `insert into public.user_view_prefs (user_id) values ('${B}')`)), null);
check('同じ人の2行目は作れない', isErr(await as('authenticated', A, `insert into public.user_view_prefs (user_id) values ('${A}')`)), null);
// upsert（アプリが使う形）
const up = await as('authenticated', B, `insert into public.user_view_prefs (user_id, prefs) values ('${B}', '{"off": {}}') on conflict (user_id) do update set prefs = excluded.prefs returning rev`);
check('upsert で作れる', up === 1, up);
const up2 = await as('authenticated', B, `insert into public.user_view_prefs (user_id, prefs) values ('${B}', '{"off": {"stats": ["sgsum"]}}') on conflict (user_id) do update set prefs = excluded.prefs returning rev`);
check('upsert で直すと rev は2', up2 === 2, up2);

// 読む
const ra = await as('authenticated', A, `select json_agg(prefs) from public.user_view_prefs`);
check('本人は自分の行だけ読める', Array.isArray(ra) && ra.length === 1 && ra[0].tabs[1] === 'ops', ra);
check('ログインしていない人は読めない', isErr(await as('anon', null, `select count(*) from public.user_view_prefs`)), null);

// 直す
check('本人は直せる（rev は2）', await as('authenticated', A, `update public.user_view_prefs set prefs = '{"off": {}}' where user_id = '${A}' returning rev`) === 2, null);
check('前の rev を条件にすると、先に直されていたら0行（別の端末とぶつかったと分かる）', await as('authenticated', A, `with u as (update public.user_view_prefs set prefs = '{}' where user_id = '${A}' and rev = 1 returning 1) select count(*)::int from u`) === 0, null);
check('ほかの人の行は直せない（0行）', await as('authenticated', A, `with u as (update public.user_view_prefs set prefs = '{}' where user_id = '${B}' returning 1) select count(*)::int from u`) === 0, null);
check('rev は自分で直せない', isErr(await as('authenticated', A, `update public.user_view_prefs set rev = 1 where user_id = '${A}'`)), null);
check('user_id は直せない', isErr(await as('authenticated', A, `update public.user_view_prefs set user_id = '${B}' where user_id = '${A}'`)), null);
check('提案の日時は自分で直せない', isErr(await as('authenticated', A, `update public.user_view_prefs set suggest_shown_at = null where user_id = '${A}'`)), null);

// 中身の形
check('配列は入れられない', isErr(await as('authenticated', A, `update public.user_view_prefs set prefs = '[1]' where user_id = '${A}'`)), null);
check('16KB を超える中身は入れられない', isErr(await as('authenticated', A, `update public.user_view_prefs set prefs = jsonb_build_object('x', repeat('a', 17000)) where user_id = '${A}'`)), null);
check('ふつうの大きさ（約4KB）は入る', !isErr(await as('authenticated', A, `update public.user_view_prefs set prefs = jsonb_build_object('x', repeat('a', 4000)) where user_id = '${A}'`)), null);
check('fmt は1〜100', isErr(await as('authenticated', A, `update public.user_view_prefs set fmt = 0 where user_id = '${A}'`)), null);
check('null の中身は入れられない', isErr(await as('authenticated', A, `update public.user_view_prefs set prefs = null where user_id = '${A}'`)), null);

// 提案は1回だけ
const revBefore = await q1(`select rev from user_view_prefs where user_id = '${A}'`);
check('1回目の提案は出してよい', await as('authenticated', A, `select public.view_prefs_claim_suggest()`) === true, null);
check('2回目は出さない（別の端末でも）', await as('authenticated', A, `select public.view_prefs_claim_suggest()`) === false, null);
check('提案を出しても中身と rev は変わらない', await q1(`select rev from user_view_prefs where user_id = '${A}'`) === revBefore && (await q1(`select prefs->>'x' from user_view_prefs where user_id = '${A}'`)).length === 4000, null);
check('提案の日時が入っている', (await q1(`select suggest_shown_at is not null from user_view_prefs where user_id = '${A}'`)) === true, null);
await as('authenticated', A, `update public.user_view_prefs set prefs = '{}' where user_id = '${A}'`);
check('あとで中身を直しても提案の日時は残る', (await q1(`select suggest_shown_at is not null from user_view_prefs where user_id = '${A}'`)) === true, null);
await db.exec(`insert into auth.users (id) values ('00000000-0000-0000-0000-00000000000c')`);
check('行がない人も提案を出せる（空の設定で作る）', await as('authenticated', '00000000-0000-0000-0000-00000000000c', `select public.view_prefs_claim_suggest()`) === true, null);
check('そのとき中身は空・rev は1', (await q1(`select prefs::text || rev from user_view_prefs where user_id = '00000000-0000-0000-0000-00000000000c'`)) === '{}1', null);
check('ログインしていない人は提案の関数を使えない', isErr(await as('anon', null, `select public.view_prefs_claim_suggest()`)), null);
check('ふつうの update では提案の日時は入らない', (await q1(`select suggest_shown_at is null from user_view_prefs where user_id = '${B}'`)) === true, null);

// 消す（全部乗せに戻す）・退会
check('ほかの人の行は消せない（0行）', await as('authenticated', A, `with d as (delete from public.user_view_prefs where user_id = '${B}' returning 1) select count(*)::int from d`) === 0, null);
check('本人は自分の行を消せる（全部乗せに戻す）', await as('authenticated', B, `with d as (delete from public.user_view_prefs where user_id = '${B}' returning 1) select count(*)::int from d`) === 1, null);
await db.exec(`delete from auth.users where id = '${A}'`);
check('退会（auth.users の削除）で一緒に消える', Number(await q1(`select count(*) from user_view_prefs where user_id = '${A}'`)) === 0, null);
check('ほかの人の行は残る', Number(await q1(`select count(*) from user_view_prefs`)) === 1, null);

// ほかを変えていない
check('満足度の初期値は 40 のまま', Number(await q1(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)) === 40, null);
check('user_profiles の使い方の答えはいまのまま', (await q1(`select pg_get_constraintdef(oid) from pg_constraint where conrelid = 'public.user_profiles'::regclass and pg_get_constraintdef(oid) like '%persona%spot%'`)).includes('casual'), null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
