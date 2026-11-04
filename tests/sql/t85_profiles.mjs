// 利用者のプロフィール：本人だけが読み書きできる・登録日と同意の日時と使い方の答えた日時はサーバーが決める・
// いまの規約の版にだけ同意できる・使い方の答えは変えられる・アカウントを消すと消える・バックアップから戻すときは値を残す
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
const fails = async (sql) => { try { await db.query(sql); return false; } catch { return true; } };

const A = '00000000-0000-0000-0000-00000000000a', B = '00000000-0000-0000-0000-00000000000b';
await db.exec(`insert into auth.users (id, email, created_at) values ('${A}', 'a@example.com', '2026-11-01 10:00+09'), ('${B}', 'b@example.com', '2026-11-02 10:00+09')`);
const as = async (uid) => { await db.exec('reset role'); await db.exec(`select set_config('request.jwt.claim.sub', '${uid ?? ''}', false)`); await db.exec(uid ? 'set role authenticated' : 'set role anon'); };

// ログインしていない人
await as(null);
const cur = (await db.query(`select public.terms_current() as v`)).rows[0].v;
check('いまの規約の版が読める', cur === '2026-10-15', cur);
check('ログインしていない人はプロフィールを読めない', await fails(`select * from public.profiles`));

// A が登録する（日時を偽っても、サーバーの値になる）
await as(A);
check('古い・ない版では登録できない', await fails(`insert into public.profiles (display_name, terms_version) values ('あ', '2020-01-01')`));
for (const [n, label] of [['', '空'], [' あ', '前に空白'], ['あ'.repeat(21), '21文字'], ['あ\nい', '改行']])
  check(`表示名が${label}なら入らない`, await fails(`insert into public.profiles (display_name, terms_version) values ('${n}', '${cur}')`));
await db.query(`insert into public.profiles (display_name, terms_version, registered_at, terms_agreed_at, usage_answered_at)
  values ('そら太郎', '${cur}', '2020-01-01', '2020-01-01', '2020-01-01')`);
let a = (await db.query(`select * from public.profiles`)).rows[0];
check('登録日はアカウントを作った日時', a.registered_at.toISOString() === '2026-11-01T01:00:00.000Z', a.registered_at);
check('同意の日時はサーバーの今', a.terms_agreed_at > new Date('2026-01-01'), a.terms_agreed_at);
check('使い方ははじめ未回答・答えた日時は空', a.usage_answer === 'none' && a.usage_answered_at === null, a);
check('ほかの人の分として登録できない', await fails(`insert into public.profiles (user_id, display_name, terms_version) values ('${B}', 'x', '${cur}')`));

// 表示名を変えても、同意の日時は動かない（偽っても戻る）
const agreed = a.terms_agreed_at.getTime();
await db.query(`update public.profiles set display_name = 'そら次郎', terms_agreed_at = '2020-01-01', registered_at = '2020-01-01'`);
a = (await db.query(`select * from public.profiles`)).rows[0];
check('表示名を変えられる', a.display_name === 'そら次郎');
check('同意の日時と登録日は書き換えられない', a.terms_agreed_at.getTime() === agreed && a.registered_at.toISOString() === '2026-11-01T01:00:00.000Z', a);
check('古い版に戻せない', await fails(`update public.profiles set terms_version = '2020-01-01'`));

// 使い方の答え（マイページから変える）
await db.query(`update public.profiles set usage_answer = 'spot'`);
a = (await db.query(`select * from public.profiles`)).rows[0];
const t1 = a.usage_answered_at?.getTime();
check('答えると日時が入る', a.usage_answer === 'spot' && t1 > 0, a);
await db.query(`update public.profiles set display_name = 'そら三郎', usage_answered_at = '2020-01-01'`);
a = (await db.query(`select * from public.profiles`)).rows[0];
check('答えを変えなければ日時はそのまま（偽っても戻る）', a.usage_answered_at?.getTime() === t1, a);
await db.query(`update public.profiles set usage_answer = 'shugyo'`);
a = (await db.query(`select * from public.profiles`)).rows[0];
check('答えを変えると日時も新しくなる', a.usage_answer === 'shugyo' && a.usage_answered_at?.getTime() >= t1, a);
check('決まった答え以外は入らない', await fails(`update public.profiles set usage_answer = 'pilot'`));
await db.query(`update public.profiles set usage_answer = 'none'`);
a = (await db.query(`select * from public.profiles`)).rows[0];
check('未回答に戻すと日時は空', a.usage_answer === 'none' && a.usage_answered_at === null, a);
check('本人でも行を消せない（アカウントの削除だけ）', await fails(`delete from public.profiles`));

// B からは見えない・変えられない
await as(B);
check('ほかの人のプロフィールは見えない', (await db.query(`select * from public.profiles`)).rows.length === 0);
const upd = await db.query(`update public.profiles set display_name = '乗っ取り' where user_id = '${A}'`);
check('ほかの人のプロフィールは変えられない', (upd.affectedRows ?? 0) === 0, upd.affectedRows);
await as(A);
check('A の表示名はそのまま', (await db.query(`select display_name from public.profiles`)).rows[0].display_name === 'そら三郎');

// 運営者がバックアップから戻すときは、書いた値を残す
await as(null); await db.exec('reset role');
await db.query(`insert into public.profiles (user_id, display_name, registered_at, terms_version, terms_agreed_at, usage_answer, usage_answered_at)
  values ('${B}', 'び', '2026-11-02 10:00+09', '${cur}', '2026-11-02 10:05+09', 'casual', '2026-11-02 10:06+09')`);
const b = (await db.query(`select * from public.profiles where user_id = '${B}'`)).rows[0];
check('戻すときは書いた日時のまま', b.terms_agreed_at.toISOString() === '2026-11-02T01:05:00.000Z' && b.usage_answered_at.toISOString() === '2026-11-02T01:06:00.000Z', b);
const def = (await db.query(`select pg_get_functiondef('public.admin_backup()'::regprocedure) as d`)).rows[0].d;
check('運営のバックアップに profiles が入る', def.includes("'profiles'"));

// アカウントを消すと消える
await db.query(`delete from auth.users where id = '${A}'`);
check('アカウントを消すとプロフィールも消える', (await db.query(`select count(*)::int as n from public.profiles where user_id = '${A}'`)).rows[0].n === 0);
if (bad) process.exit(1);
