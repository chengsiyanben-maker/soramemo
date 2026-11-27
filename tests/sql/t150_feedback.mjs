// 不具合・意見の報告（移行 feedback）
//   1. 表に位置・メール・IP の列がない。RLS 有効
//   2. ログインした人は自分の分を入れられる。user_id・状態・運営のメモは本人が決められない（trigger が決める）
//   3. 自分の分だけ読める。運営のメモ・利用者 ID・起動の値の列は読めない。my_feedback も自分の分だけ
//   4. 書き換え・消すことはできない（本人も anon も）。anon は表に入れられない
//   5. ログインしていない人（サービスの鍵＝feedback-submit）からは user_id が空・起動の値が要る
//   6. 送りすぎ：同じ利用者・同じ起動の値で10分に3件まで。10分たてばまた送れる。ログインしていない人の全体で10分に30件まで
//   7. 本文：空白だけ・2001字は断る。2000字は入る。種類・空港コードの形の決まり。受け付けの非常停止（feedback_enabled）
//   8. 運営：admin_feedback_list（状態ごとの数・絞り込み・メモが見える）・admin_feedback_set（状態とメモ・admin_actions に残る）。運営でなければ admin only
//   9. 退会（auth.users を消す）で本人の報告も消える
//  10. 夜の知らせ：ng がなく報告だけなら、feedback_alert_hour より前は wait、以降は送る（種類ごとの数）。届いたあとは同じ報告を数えない。
//      ng があればいつでも送り、報告の数も載せる。報告も ng もなければ送らない
//  11. 関数に上限（statement_timeout）。送りすぎの数え方が全部読みにならない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_feedback.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 400)); if (!ok) bad++; };
check('移行がある', !!mine);
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;  -- Supabase の service_role は RLS を通り抜ける
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb, '{}'::jsonb) $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));

const U = '00000000-0000-0000-0000-0000000000a1', V = '00000000-0000-0000-0000-0000000000a2', ADM = '00000000-0000-0000-0000-0000000000ad';
await db.exec(`insert into auth.users (id, email) values ('${U}', 'u@x'), ('${V}', 'v@x'), ('${ADM}', 'a@x'); insert into ops.admins values ('${ADM}');`);
const as = async (role, uid, q, params) => {
  await db.exec(`set role ${role}; select set_config('request.jwt.claim.sub', '${uid ?? ''}', false); select set_config('request.jwt.claims', '${uid ? JSON.stringify({ sub: uid, aal: 'aal2' }) : ''}', false);`);
  try { return await db.query(q, params); } finally { await db.exec(`reset role; select set_config('request.jwt.claim.sub', '', false); select set_config('request.jwt.claims', '', false);`); }
};
const err = async (fn) => { try { await fn(); return ''; } catch (e) { return e.message; } };

// 1. 列と RLS
const cols = (await db.query(`select string_agg(column_name, ',' order by ordinal_position) c from information_schema.columns where table_schema = 'public' and table_name = 'feedback'`)).rows[0].c;
check('列の一覧', cols === 'id,created_at,kind,body,app_version,screen,device,last_error,airport,user_id,session,status,admin_note,updated_at', cols);
check('位置・メール・IP の列がない', !/lat|lon|mail|(^|,)ip|addr|geo/.test(cols), cols);
check('RLS 有効', (await db.query(`select relrowsecurity r from pg_class where oid = 'public.feedback'::regclass`)).rows[0].r === true);

// 2. ログインした人が入れる（ずるい値を入れても trigger が直す）
await as('authenticated', U, `insert into public.feedback (kind, body, app_version, screen, device, last_error, airport, session) values ('bug', '  印が押せない  ', '2026.11.27', 'home', 'ios', 'checkin', 'HND', 'sessaaaa1')`);
const r1 = (await db.query(`select * from public.feedback order by id desc limit 1`)).rows[0];
check('入った行：user_id は本人・状態は open・本文は前後の空白なし', r1.user_id === U && r1.status === 'open' && r1.body === '印が押せない' && r1.admin_note === null, r1);
let e = await err(() => as('authenticated', U, `insert into public.feedback (kind, body, status) values ('bug', 'x', 'fixed')`));
check('状態は本人が入れられない（列の権限）', /permission denied/.test(e), e);
e = await err(() => as('authenticated', U, `insert into public.feedback (kind, body, admin_note) values ('bug', 'x', 'y')`));
check('運営のメモは本人が入れられない', /permission denied/.test(e), e);
e = await err(() => as('authenticated', U, `insert into public.feedback (kind, body, user_id) values ('bug', 'x', '${V}')`));
check('user_id は本人が入れられない（他の人になりすませない）', /permission denied/.test(e), e);
e = await err(() => as('anon', null, `insert into public.feedback (kind, body, session) values ('bug', 'x', 'sessbbbb1')`));
check('anon は表に直接入れられない（feedback-submit を通す）', /permission denied/.test(e), e);

// 3. 読む
await as('authenticated', V, `insert into public.feedback (kind, body) values ('request', '地図を大きく')`);
await db.exec(`update public.feedback set admin_note = '運営だけのメモ' where user_id = '${V}'`);
const mineU = (await as('authenticated', U, `select id, body, status from public.feedback`)).rows;
check('自分の分だけ読める', mineU.length === 1 && mineU[0].body === '印が押せない', mineU);
e = await err(() => as('authenticated', V, `select admin_note from public.feedback`));
check('運営のメモの列は読めない', /permission denied/.test(e), e);
e = await err(() => as('authenticated', V, `select user_id, session from public.feedback`));
check('利用者 ID・起動の値の列は読めない', /permission denied/.test(e), e);
const myV = (await as('authenticated', V, `select * from public.my_feedback()`)).rows;
check('my_feedback は自分の分だけ・メモの列がない', myV.length === 1 && myV[0].body === '地図を大きく' && !('admin_note' in myV[0]), myV);
check('anon は my_feedback を呼べない', (await db.query(`select has_function_privilege('anon', 'public.my_feedback()', 'execute') a`)).rows[0].a === false);

// 4. 書き換え・消す
e = await err(() => as('authenticated', U, `update public.feedback set status = 'fixed'`));
check('本人も書き換えられない', /permission denied/.test(e), e);
e = await err(() => as('authenticated', U, `delete from public.feedback`));
check('本人も消せない', /permission denied/.test(e), e);

// 5. ログインしていない人（サービスの鍵）
await as('service_role', null, `insert into public.feedback (kind, body, session, airport) values ('airport_data', '駐車場の位置が違う', 'anonsess1', 'ITM')`);
const r5 = (await db.query(`select user_id, session, status from public.feedback where session = 'anonsess1'`)).rows[0];
check('サービスの鍵から：user_id は空・起動の値が残る', r5.user_id === null && r5.session === 'anonsess1' && r5.status === 'open', r5);
e = await err(() => as('service_role', null, `insert into public.feedback (kind, body) values ('bug', 'x')`));
check('ログインしていない人は起動の値が要る', /feedback_session_required/.test(e), e);

// 6. 送りすぎ
await db.exec(`delete from public.feedback`);
for (let i = 0; i < 3; i++) await as('authenticated', U, `insert into public.feedback (kind, body) values ('bug', 'n${i}')`);
e = await err(() => as('authenticated', U, `insert into public.feedback (kind, body) values ('bug', 'n3')`));
check('同じ利用者は10分に3件まで', /feedback_too_many/.test(e), e);
check('（断った分は入らない）', (await db.query(`select count(*)::int n from public.feedback`)).rows[0].n === 3);
await db.exec(`update public.feedback set created_at = now() - interval '11 minutes'`);
e = await err(() => as('authenticated', U, `insert into public.feedback (kind, body) values ('bug', 'n4')`));
check('10分たてばまた送れる', e === '', e);
for (let i = 0; i < 3; i++) await as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'a${i}', 'samesess1')`);
e = await err(() => as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'a3', 'samesess1')`));
check('同じ起動の値は10分に3件まで', /feedback_too_many/.test(e), e);
e = await err(() => as('authenticated', V, `insert into public.feedback (kind, body, session) values ('bug', 'v', 'samesess1')`));
check('ログインしていても、同じ起動の値なら数える', /feedback_too_many/.test(e), e);
for (let i = 0; i < 27; i++) await as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'z', 'many${String(i).padStart(5, '0')}')`);
e = await err(() => as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'z', 'manyzzzzz')`));
check('ログインしていない人の全体で10分に30件まで', /feedback_too_many/.test(e), e);
e = await err(() => as('authenticated', V, `insert into public.feedback (kind, body) values ('bug', 'v')`));
check('（全体の上限はログインした人には効かない）', e === '', e);

// 7. 形の決まり・非常停止
await db.exec(`delete from public.feedback`);
const ins = (cols, vals) => err(() => as('authenticated', V, `insert into public.feedback (${cols}) values (${vals})`).finally(() => db.exec(`delete from public.feedback`)));
check('空白だけの本文は断る', /feedback_empty|check/.test(await ins('kind, body', `'bug', '   '`)));
check('2001字は断る', /check/.test(await ins('kind, body', `'bug', repeat('あ', 2001)`)));
check('2000字は入る', (await ins('kind, body', `'bug', repeat('あ', 2000)`)) === '');
check('種類の決まり', /check/.test(await ins('kind, body', `'other', 'x'`)));
check('空港コードの決まり', /check/.test(await ins('kind, body, airport', `'bug', 'x', 'hnd'`)));
check('直前のエラーは種類の形だけ（文は入らない）', /check/.test(await ins('kind, body, last_error', `'bug', 'x', 'TypeError: null'`)));
await db.exec(`insert into ops.flags (key, value) values ('feedback_enabled', 'false')`);
check('feedback_enabled を false にすると受け付けない', /feedback_closed/.test(await ins('kind, body', `'bug', 'x'`)));
await db.exec(`delete from ops.flags where key = 'feedback_enabled'`);

// 8. 運営
await as('authenticated', U, `insert into public.feedback (kind, body) values ('bug', 'b1'), ('request', 'r1')`);
await as('service_role', null, `insert into public.feedback (kind, body, session) values ('airport_data', 'd1', 'admsess01')`);
const L = async (args = '') => (await as('authenticated', ADM, `select public.admin_feedback_list(${args}) r`)).rows[0].r;
let l = await L();
check('一覧：新しい順・状態ごとの数', l.items.length === 3 && l.items[0].body === 'd1' && l.counts.open === 3, l);
check('一覧：ログインしていない人の報告は logged_in false', l.items[0].logged_in === false && l.items[1].logged_in === true && l.items[1].user_id === U, l.items);
const idB = l.items.find(x => x.body === 'b1').id;
await as('authenticated', ADM, `select public.admin_feedback_set(${idB}, 'checking', '再現した')`);
l = await L(`'checking'`);
check('状態の切り替えとメモ・絞り込み', l.items.length === 1 && l.items[0].status === 'checking' && l.items[0].admin_note === '再現した' && l.items[0].updated_at && l.counts.checking === 1, l);
await as('authenticated', ADM, `select public.admin_feedback_set(${idB}, 'fixed')`);
check('メモを渡さなければ今のまま', (await L(`'fixed'`)).items[0].admin_note === '再現した');
await as('authenticated', ADM, `select public.admin_feedback_set(${idB}, 'fixed', '')`);
check("'' ならメモを空に", (await L(`'fixed'`)).items[0].admin_note === null);
check('種類で絞る', (await L(`null, 'request'`)).items.map(x => x.body).join() === 'r1');
check('admin_actions に残る', (await db.query(`select count(*)::int n from ops.admin_actions where action = 'feedback_set' and target = '${idB}'`)).rows[0].n === 3);
const seenU = (await as('authenticated', U, `select status from public.feedback where body = 'b1'`)).rows[0];
check('本人には状態が見える', seenU.status === 'fixed', seenU);
check('運営でなければ一覧は admin only', /admin only/.test(await err(() => as('authenticated', U, `select public.admin_feedback_list()`))));
check('運営でなければ切り替えは admin only', /admin only/.test(await err(() => as('authenticated', U, `select public.admin_feedback_set(${idB}, 'open')`))));
check('知らない状態は断る', /bad status/.test(await err(() => as('authenticated', ADM, `select public.admin_feedback_set(${idB}, 'done')`))));
check('ない id は not found', /not found/.test(await err(() => as('authenticated', ADM, `select public.admin_feedback_set(999999, 'open')`))));
const pr = (await db.query(`select has_function_privilege('anon', 'public.admin_feedback_list(text, text, integer, bigint)', 'execute') a, has_function_privilege('anon', 'public.admin_feedback_set(bigint, text, text)', 'execute') b`)).rows[0];
check('anon は運営の関数を呼べない', pr.a === false && pr.b === false, pr);

// 9. 退会
await db.exec(`delete from auth.users where id = '${U}'`);
check('退会で本人の報告が消える（ログインしていない人の分は残る）', (await db.query(`select count(*)::int n from public.feedback`)).rows[0].n === 1);

// 10. 夜の知らせ
await db.exec(`delete from public.feedback; delete from ops.ops_alert_log;
  create or replace function ops.data_health() returns jsonb language sql stable as $$ select '[{"key":"a","label":"a","last":null,"limit_min":1,"ok":true}]'::jsonb $$;`);
const claim = async () => (await db.query(`select public.ops_alert_claim() r`)).rows[0].r;
const setHour = (h) => db.exec(`insert into ops.flags (key, value) values ('feedback_alert_hour', '${h}') on conflict (key) do update set value = excluded.value`);
let c = await claim();
check('報告も ng もなければ送らない（ok）', c.send === false && c.reason === 'ok', c);
await as('authenticated', V, `insert into public.feedback (kind, body) values ('bug', 'x'), ('bug', 'y'), ('request', 'z')`);
await setHour(24);
c = await claim();
check('報告だけ・決めた時刻より前は wait（記録しない）', c.send === false && c.reason === 'wait' && c.feedback_new === 3
  && (await db.query(`select count(*)::int n from ops.ops_alert_log`)).rows[0].n === 0, c);
await setHour(0);
c = await claim();
check('報告だけ・決めた時刻以降は送る（種類ごとの数・ng の項目は空）', c.send === true && c.feedback_new === 3 && c.feedback_kinds.bug === 2 && c.feedback_kinds.request === 1 && c.items.length === 0, c);
await db.query(`select public.ops_alert_done($1::date, true, 'mail 1')`, [c.day]);
c = await claim();
check('届いたあと新しい報告がなければ送らない', c.send === false && c.reason === 'ok', c);
await as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'later', 'latesess1')`);
c = await claim();
check('届いたあとは、新しい報告が来ても同じ日は送らない（1日1回）', c.send === false && c.reason === 'already', c);
await db.exec(`delete from public.feedback where session = 'latesess1'`);
await db.exec(`update ops.ops_alert_log set day = day - 1`);
c = await claim();
check('次の日：届けたあとに新しい報告がなければ送らない', c.send === false && c.reason === 'ok', c);
await as('service_role', null, `insert into public.feedback (kind, body, session) values ('airport_data', 'w', 'nextsess1')`);
c = await claim();
check('次の日：前に届けたあとの報告だけ数える', c.send === true && c.feedback_new === 1 && c.feedback_kinds.airport_data === 1, c);
await db.query(`select public.ops_alert_done($1::date, false, 'failed 1')`, [c.day]);
await as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'v', 'nextsess2')`);
c = await claim();
check('届かなかったら、次の回にその分も合わせて数える', c.send === true && c.feedback_new === 2, c);
await db.exec(`delete from ops.ops_alert_log; delete from public.feedback; delete from ops.flags where key = 'feedback_alert_hour';
  create or replace function ops.data_health() returns jsonb language sql stable as $$ select '[{"key":"wx","label":"気象","last":null,"limit_min":90,"ok":false}]'::jsonb $$;`);
await as('authenticated', V, `insert into public.feedback (kind, body) values ('bug', 'x')`);
await setHour(24);
c = await claim();
check('ng があればいつでも送り、報告の数も載せる', c.send === true && c.items.length === 1 && c.feedback_new === 1, c);
const logCols = (await db.query(`select string_agg(column_name, ',' order by ordinal_position) c from information_schema.columns where table_schema = 'ops' and table_name = 'ops_alert_log'`)).rows[0].c;
check('知らせの記録に本文・宛先の列がない', !/body|to\b|mail|addr|url|target/.test(logCols), logCols);

// 11. 上限・全部読みなし
const cfg = (await db.query(`select string_agg(proname || ':' || array_to_string(proconfig, ','), ' | ') c from pg_proc where proname in ('feedback_before_insert', 'admin_feedback_list', 'admin_feedback_set', 'ops_alert_claim')`)).rows[0].c;
check('関数に上限（statement_timeout）', (cfg.match(/statement_timeout=/g) || []).length === 4, cfg);
await db.exec(`alter table public.feedback disable trigger feedback_before_insert;
  insert into public.feedback (kind, body, session, created_at) select 'bug', 'x', 'bulk' || lpad(g::text, 6, '0'), now() - (g || ' minutes')::interval from generate_series(1, 3000) g;
  alter table public.feedback enable trigger feedback_before_insert; analyze public.feedback;`);
await db.exec('begin; set local enable_seqscan = off');
const s0 = Number((await db.query(`select seq_scan n from pg_stat_xact_user_tables where relname = 'feedback'`)).rows[0]?.n ?? 0);
await as('service_role', null, `insert into public.feedback (kind, body, session) values ('bug', 'x', 'probe0001')`);
await as('authenticated', V, `insert into public.feedback (kind, body) values ('bug', 'x')`);
await db.query(`select public.ops_alert_claim()`);
const s1 = Number((await db.query(`select seq_scan n from pg_stat_xact_user_tables where relname = 'feedback'`)).rows[0]?.n ?? 0);
await db.exec('rollback');
check('送りすぎの数え方・夜の知らせの数え方で表をまるごと読まない', s1 - s0 === 0, { s0, s1 });
const sql = fs.readFileSync(dir + mine, 'utf8');
check('移行に鍵・宛先を書いていない', !/@[a-z0-9-]+\.[a-z]{2}|password|service_role_key/i.test(sql));
const toml = fs.readFileSync(new URL('../../supabase/config.toml', import.meta.url), 'utf8');
check('config.toml に feedback-submit（verify_jwt = false）', /\[functions\.feedback-submit\]\nverify_jwt = false/.test(toml));
console.log(bad ? `NG ${bad}` : 'すべて OK'); process.exit(bad ? 1 : 0);
