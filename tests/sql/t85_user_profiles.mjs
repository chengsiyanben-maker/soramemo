// 利用者のプロフィール：登録で自動に作られる・いまいる人の分も作られる・本人だけが読める・直せるのは表示名と使い方の答えだけ・
// 同意はサーバーの時刻で入る・答えた日時は答えが変わったときだけ・アカウント削除で消える
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const OLD = '00000000-0000-0000-0000-000000000001', A = '11111111-1111-1111-1111-111111111111', B = '22222222-2222-2222-2222-222222222222';
const files = fs.readdirSync(dir).sort();
// プロフィールの SQL の前からいた利用者
for (const f of files) {
  if (f.includes('_user_profiles')) await db.exec(`insert into auth.users (id, created_at) values ('${OLD}', '2026-10-10 10:00+09')`);
  await db.exec(fs.readFileSync(dir + f, 'utf8'));
}
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } };
const as = async (uid, fn) => { await db.exec(`set request.jwt.claim.sub = '${uid}'; set role authenticated`); try { return await fn(); } finally { await db.exec('reset role; reset request.jwt.claim.sub'); } };

const old = (await db.query(`select created_at = '2026-10-10 10:00+09'::timestamptz as ok, persona, agreed_at from public.user_profiles where user_id = '${OLD}'`)).rows[0];
check('いまいる利用者の分も作られ、登録日は auth.users の作成日', old?.ok && old.persona === 'unanswered' && old.agreed_at === null, old);

await db.exec(`insert into auth.users (id) values ('${A}'), ('${B}')`);
const n = (await db.query(`select count(*)::int n from public.user_profiles where user_id in ('${A}', '${B}')`)).rows[0].n;
check('登録すると自動で1行できる', n === 2, n);

// 本人だけが読める
const seen = await as(A, async () => (await db.query(`select user_id from public.user_profiles`)).rows.map((r) => r.user_id));
check('本人の行だけが見える', seen.length === 1 && seen[0] === A, seen);
check('ログインしていない人は読めない', await fails(`set role anon; select * from public.user_profiles; reset role`)); await db.exec('reset role');

// 本人が直せるのは表示名と使い方の答えだけ
await as(A, () => db.exec(`update public.user_profiles set display_name = '  そら太郎 ', persona = 'spot'`));
const a1 = (await db.query(`select display_name, persona, persona_answered_at from public.user_profiles where user_id = '${A}'`)).rows[0];
check('表示名（前後の空白を落とす）と使い方の答え・答えた日時が入る', a1.display_name === 'そら太郎' && a1.persona === 'spot' && a1.persona_answered_at !== null, a1);
check('他人の行は直せない（0行）', (await as(A, () => db.query(`update public.user_profiles set persona = 'casual' where user_id = '${B}'`))).affectedRows === 0);
check('登録日は直せない', await as(A, () => fails(`update public.user_profiles set created_at = now() - interval '1 year'`)));
check('同意の日時は直せない', await as(A, () => fails(`update public.user_profiles set agreed_at = now(), terms_version = '2026-10-15', privacy_version = '2026-10-21'`)));
check('答えた日時は直せない', await as(A, () => fails(`update public.user_profiles set persona_answered_at = now()`)));
check('行は作れない・消せない', await as(A, () => fails(`insert into public.user_profiles (user_id) values ('${A}')`)) && await as(A, () => fails(`delete from public.user_profiles`)));
check('決まった答え以外は入らない', await as(A, () => fails(`update public.user_profiles set persona = 'pilot'`)));
check('表示名は20文字まで・空白だけはだめ', await as(A, () => fails(`update public.user_profiles set display_name = '${'あ'.repeat(21)}'`)) && await as(A, () => fails(`update public.user_profiles set display_name = '   '`)));

// 答えた日時は答えが変わったときだけ入れ直す・未回答に戻すと空
await db.exec(`alter table public.user_profiles disable trigger user_profiles_touch; update public.user_profiles set persona_answered_at = '2026-11-01' where user_id = '${A}'; alter table public.user_profiles enable trigger user_profiles_touch`); // 古い日時にしておく
await as(A, () => db.exec(`update public.user_profiles set display_name = 'そら'`));
const a2 = (await db.query(`select persona_answered_at = '2026-11-01'::timestamptz as same from public.user_profiles where user_id = '${A}'`)).rows[0];
check('表示名だけ変えても、答えた日時はそのまま', a2.same, a2);
await as(A, () => db.exec(`update public.user_profiles set persona = 'shugyo'`));
const a3 = (await db.query(`select persona_answered_at > '2026-11-02'::timestamptz as newer from public.user_profiles where user_id = '${A}'`)).rows[0];
check('答えを変えると、答えた日時が入れ直される', a3.newer, a3);
await as(A, () => db.exec(`update public.user_profiles set persona = 'unanswered'`));
const a4 = (await db.query(`select persona_answered_at from public.user_profiles where user_id = '${A}'`)).rows[0];
check('未回答に戻すと、答えた日時は空', a4.persona_answered_at === null, a4);

// 同意
const ag = await as(A, async () => (await db.query(`select public.agree_terms('2026-10-15', '2026-10-21') as r`)).rows[0].r);
check('同意の記録：版と日時が入る', ag.terms_version === '2026-10-15' && ag.privacy_version === '2026-10-21' && ag.agreed_at, ag);
check('版の形が違うと断る', await as(A, () => fails(`select public.agree_terms('v1', '2026-10-21')`)));
check('ログインしていないと同意できない', await fails(`set role anon; select public.agree_terms('2026-10-15', '2026-10-21'); reset role`)); await db.exec('reset role');

// アカウント削除で消える（ほかの人の行は残る）
await db.exec(`delete from auth.users where id = '${A}'`);
const left = (await db.query(`select user_id from public.user_profiles order by user_id`)).rows.map((r) => r.user_id);
check('削除した人の行だけ消える', !left.includes(A) && left.includes(B) && left.includes(OLD), left);
if (bad) process.exit(1);
