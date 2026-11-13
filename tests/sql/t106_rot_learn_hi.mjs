// 運用予想を learn_hi に切り替える（移行 166）：predict_rotation_v2 は rot_predict('learn_hi', …) と同じ答え・返す形は今のまま・
// 2回しか見ていない便は出さない・よく見る便は今までどおり・権限は anon・authenticated に実行だけ・表と採点は変えない
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows[0];
const mig = fs.readFileSync(dir + files.find((f) => f.endsWith('_rot_learn_hi.sql')), 'utf8');
const T = `(now() at time zone 'Asia/Tokyo')::date`;
const at = (off, hm) => `((${T} - ${off}) + time '${hm}') at time zone 'Asia/Tokyo'`;
const rows = [];
const leg = (reg, cs, off, hm, endHm, dep, arr, type) => rows.push(`('${reg}', '${cs}', ${T} - ${off}, '${type}', ${at(off, hm)}, ${at(off, endHm)}, '${dep}', '${arr}')`);
// よく見る便：毎日 SKY1 → SKY2（20日）
for (let off = 1; off <= 20; off++) { leg('JA73SA', 'SKY1', off, '07:00', '09:00', 'HND', 'FUK', 'B738'); leg('JA73SA', 'SKY2', off, '10:00', '12:00', 'FUK', 'HND', 'B738'); }
// 2回しか見ていない便：NEW1 → NEW2
for (const off of [2, 3]) { leg('JA02NW', 'NEW1', off, '09:00', '10:00', 'OKD', 'MMB', 'DH8D'); leg('JA02NW', 'NEW2', off, '11:00', '12:00', 'MMB', 'OKD', 'DH8D'); }
// 今日の分（画面向けの関数が「いまの便」に使う）
leg('JA73SA', 'SKY1', 0, '07:00', '07:30', 'HND', 'FUK', 'B738'); leg('JA02NW', 'NEW1', 0, '09:00', '09:30', 'OKD', 'MMB', 'DH8D');
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values ${rows.join(',\n')}`);
for (let off = 0; off <= 20; off++) await db.query(`select public.rot_pairs_build(${T} - ${off})`);

const v2 = async (reg) => { await db.exec('set role anon'); try { return (await q(`select public.predict_rotation_v2('${reg}') as p`)).p; } finally { await db.exec('reset role'); } };
const often = await v2('JA73SA'), rare = await v2('JA02NW'), none = await v2('JA99ZZ');
check('method は learn_hi・予想の印・返す形の鍵は今のまま', often.method === 'learn_hi' && often.estimate === true && often.src === 'reg'
  && JSON.stringify(Object.keys(often).sort()) === JSON.stringify(['estimate', 'known', 'method', 'next', 'reg', 'src', 'type']), often);
check('よく見る便は今までどおり出す（SKY2・src learn）', often.known.callsign === 'SKY1' && often.next[0]?.callsign === 'SKY2' && often.next[0].src === 'learn', often);
const hiDirect = (await q(`select public.rot_predict('learn_hi', 'JA73SA', ${T}, 'SKY1', 'FUK', '07:00', 4) as p`)).p;
check('rot_predict(learn_hi) と同じ便の並び', JSON.stringify(often.next) === JSON.stringify(hiDirect), { often: often.next, hiDirect });
const lo = (await q(`select public.rot_predict('learn', 'JA02NW', ${T}, 'NEW1', 'MMB', '09:00', 1) as p`)).p;
check('2回しか見ていない便：learn なら出るが、画面向けは出さない', lo[0]?.callsign === 'NEW2' && rare.method === 'learn_hi' && rare.known.callsign === 'NEW1' && !rare.next.some((s) => s.callsign === 'NEW2'), { lo, rare });
check('記録のない機体：known は空・next は空・method は learn_hi', none.known === null && Array.isArray(none.next) && none.next.length === 0 && none.method === 'learn_hi', none);
check('おかしな登録記号は null', (await v2('ja 1')) === null);

const acl = (await q(`select has_function_privilege('anon', 'public.predict_rotation_v2(text)', 'execute') as a, has_function_privilege('authenticated', 'public.predict_rotation_v2(text)', 'execute') as b,
  has_function_privilege('anon', 'public.rot_predict(text, text, date, text, text, time, int)', 'execute') as c, (select prosecdef from pg_proc where oid = 'public.predict_rotation_v2(text)'::regprocedure) as d`));
check('権限は今のまま（v2 は anon・authenticated が実行できる・rot_predict は呼べない・security definer）', acl.a && acl.b && !acl.c && acl.d, acl);
let denied = 0;
for (const t of ['rot_pairs', 'rot_eval', 'reg_legs']) { await db.exec('set role anon'); try { await db.query(`select 1 from public.${t} limit 1`); } catch { denied++; } await db.exec('reset role'); }
check('表は anon から読めないまま', denied === 3, denied);
const code = mig.replace(/--.*$/gm, '');
check('移行は関数1つだけ（表・索引・RLS・採点・cron に触らない）', (code.match(/create or replace function/gi) || []).length === 1
  && !/\b(create table|alter table|create index|drop|delete|truncate|update|insert|policy|cron\.)\b/i.test(code), code);
for (let off = 1; off <= 3; off++) await db.query(`select public.rot_eval_day(${T} - ${off})`);
const ms = (await db.query(`select distinct method from public.rot_eval order by 1`)).rows.map((r) => r.method).join(',');
check('毎晩の採点は3通りのまま', ms === 'base,learn,learn_hi', ms);
if (bad) process.exit(1);
