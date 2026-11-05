// 運営コンソール：毎日の新規登録の数（admin_signups_daily）
//   運営者だけ・数だけ（メールや ID を返さない）・日本時間の日の区切り・0 の日も返す・日数は 1〜365・同意と使い方の答えの内訳
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
const as = async (role, uid, sql) => { try { await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub','${uid}',false);`); const r = await db.query(sql); return r.rows.length ? Object.values(r.rows[0])[0] : 'ok'; } catch (e) { return 'ERROR: ' + e.message.split('\n')[0]; } finally { await db.exec('reset role'); } };
const ADM = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', U = (n) => `00000000-0000-0000-0000-${String(n).padStart(12, '0')}`;
// 日本時間の「今日の 0:05」「昨日の 23:55」「3日前の正午」「40日前」に登録した人
const T = `(now() at time zone 'Asia/Tokyo')::date`;
await db.exec(`insert into auth.users (id, email, created_at) values
  ('${ADM}', 'admin@example.com', ((${T} - 100)::timestamp at time zone 'Asia/Tokyo')),
  ('${U(1)}', 'a@example.com', ((${T})::timestamp + interval '5 minutes') at time zone 'Asia/Tokyo'),
  ('${U(2)}', 'b@example.com', ((${T})::timestamp + interval '5 minutes') at time zone 'Asia/Tokyo'),
  ('${U(3)}', 'c@example.com', ((${T} - 1)::timestamp + interval '23 hours 55 minutes') at time zone 'Asia/Tokyo'),
  ('${U(4)}', 'd@example.com', ((${T} - 3)::timestamp + interval '12 hours') at time zone 'Asia/Tokyo'),
  ('${U(5)}', 'e@example.com', ((${T} - 40)::timestamp + interval '12 hours') at time zone 'Asia/Tokyo');
  insert into ops.admins (user_id) values ('${ADM}');
  update user_profiles set persona = 'spot' where user_id = '${U(1)}';
  update user_profiles set persona = 'shugyo', terms_version = '2026-11-04', privacy_version = '2026-11-04', agreed_at = now() where user_id = '${U(2)}';
  update user_profiles set persona = 'casual' where user_id = '${U(3)}';`);

check('ふつうの利用者は呼べない', String(await as('authenticated', U(1), 'select public.admin_signups_daily(30)')).includes('admin only'), null);
check('ログインしていない人は呼べない', String(await as('anon', '', 'select public.admin_signups_daily(30)')).startsWith('ERROR'), null);
const r = await as('authenticated', ADM, 'select public.admin_signups_daily(30)');
check('運営者は呼べる', r && typeof r === 'object' && Array.isArray(r.rows), r);
check('30日ぶんの行（0 の日も含む）', r.rows.length === 30 && r.days === 30, r.rows.length);
check('新しい日が先', r.rows[0].day > r.rows[1].day, [r.rows[0].day, r.rows[1].day]);
check('今日（日本時間 0:05）に2人', r.rows[0].signups === 2, r.rows[0]);
check('昨日（日本時間 23:55）は昨日に入る', r.rows[1].signups === 1 && r.rows[1].casual === 1, r.rows[1]);
check('3日前に1人・未回答', r.rows[3].signups === 1 && r.rows[3].unanswered === 1, r.rows[3]);
check('0 の日は 0', r.rows[2].signups === 0, r.rows[2]);
check('今日の内訳（撮る1・修行1・同意1）', r.rows[0].spot === 1 && r.rows[0].shugyo === 1 && r.rows[0].agreed === 1 && r.rows[0].unanswered === 0, r.rows[0]);
check('期間の合計は 4（40日前と100日前は入らない）', r.total === 4 && r.all_users === 6, { total: r.total, all: r.all_users });
check('メールや ID は返さない', !JSON.stringify(r).includes('@') && !JSON.stringify(r).includes('00000000-0000'), null);
const r1 = await as('authenticated', ADM, 'select public.admin_signups_daily(0)');
const r9 = await as('authenticated', ADM, 'select public.admin_signups_daily(9999)');
check('日数は 1〜365 に収める', r1.rows.length === 1 && r9.rows.length === 365, [r1.rows.length, r9.rows.length]);
check('退会した人は数えない', await (async () => { await db.exec(`delete from auth.users where id = '${U(4)}'`); const x = await as('authenticated', ADM, 'select public.admin_signups_daily(30)'); return x.rows[3].signups === 0 && x.total === 3; })(), null);
check('満足度の初期値は 40 のまま', Number(Object.values((await db.query(`select column_default from information_schema.columns where table_name = 'companies' and column_name = 'satisfaction'`)).rows[0])[0]) === 40, null);
console.log(bad ? `NG ${bad}件` : 'すべて OK'); process.exit(bad ? 1 : 0);
