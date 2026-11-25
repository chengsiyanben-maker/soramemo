// 羽田・成田の TAF を残す（移行 198）
//   1. wx_taf・wx_taf_hours ができる。同じ発表はもう一度入らない（関数は ignoreDuplicates）。時間ごとの行は元の TAF がないと入らない
//   2. 権限：利用者（anon・authenticated）は読めない・書けない。RLS は ON。service_role は書ける
//   3. 本人用の読むだけの SQL（docs/pm/hnd-nrt-priority-check.sql）が全部流れ、当たり具合が数えられる
//   4. もう一度流しても同じ・lock_timeout は元に戻る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const db = new PGlite(); const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
const files = fs.readdirSync(dir).sort();
const mine = files.find(f => f.endsWith('_hnd_nrt_taf.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 600)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 198 番', /^\d{8}000198_hnd_nrt_taf\.sql$/.test(mine), mine);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', await q1(`show lock_timeout`));

// 1. 表
await db.exec(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) values
  ('RJTT', now() - interval '3 hours', date_trunc('hour', now()) - interval '2 hours', date_trunc('hour', now()) + interval '28 hours', 'TAF RJTT ...'),
  ('RJAA', now() - interval '3 hours', date_trunc('hour', now()) - interval '2 hours', date_trunc('hour', now()) + interval '28 hours', 'TAF RJAA ...')`);
check('同じ発表は主キーで重ならない', await fails(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) select icao, issued, valid_from, valid_to, raw from public.wx_taf limit 1`), null);
check('ignoreDuplicates の形（on conflict do nothing）なら0行で通る', (await q(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) select icao, issued, valid_from, valid_to, raw from public.wx_taf on conflict (icao, issued) do nothing returning icao`)).length === 0, null);
check('有効の時間が逆なら入らない', await fails(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) values ('RJTT', now(), now(), now() - interval '1 hour', 'x')`), null);
check('ICAO の形が違えば入らない', await fails(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) values ('HND', now(), now(), now() + interval '1 hour', 'x')`), null);
// 時間ごと：羽田は南風を予報（2時間前から今の後まで）、成田は 34運用（b）
await db.exec(`insert into public.wx_taf_hours (icao, at, issued, lead_h, wdir, wspd, est_mode, t_kind)
  select t.icao, h, t.issued, round(extract(epoch from h - t.issued) / 3600)::int, 180, 14, case t.icao when 'RJTT' then 'south' else 'b' end, null
  from public.wx_taf t, generate_series(date_trunc('hour', now()) - interval '2 hours', date_trunc('hour', now()) + interval '2 hours', interval '1 hour') h`);
check('時間ごとの行が入る', await q1(`select count(*)::int from public.wx_taf_hours`) === 10, null);
check('元の TAF がない時間ごとの行は入らない', await fails(`insert into public.wx_taf_hours (icao, at, issued, lead_h) values ('RJTT', now(), now() - interval '9 days', 1)`), null);

// 2. 権限
for (const t of ['wx_taf', 'wx_taf_hours']) {
  check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
  for (const r of ['anon', 'authenticated']) {
    check(`${r} は ${t} を読めない`, await fails(`set role ${r}; select * from public.${t}; reset role;`), null); await db.exec('reset role');
    check(`${r} は ${t} に書けない`, await fails(`set role ${r}; delete from public.${t}; reset role;`), null); await db.exec('reset role');
  }
}
await db.exec(`set role service_role`);
check('service_role は書ける', (await q(`insert into public.wx_taf (icao, issued, valid_from, valid_to, raw) values ('RJTT', now(), now(), now() + interval '30 hours', 'TAF RJTT AMD') returning icao`)).length === 1, null);
await db.exec(`reset role`);

// 3. 読むだけの SQL：ops_log（実機）と rwy_samples・wx_obs を作って、全部の文が流れるか
await db.exec(`insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode)
  select g, 'HND', 180, 14, case when extract(hour from g at time zone 'Asia/Tokyo') between 15 and 18 then 'city' else 'south' end,
         case when g < now() - interval '60 minutes' then 'north' else 'south' end
  from generate_series(now() - interval '150 minutes', now(), interval '5 minutes') g;
insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode)
  select g, 'NRT', 330, 9, 'b', 'b' from generate_series(now() - interval '150 minutes', now(), interval '5 minutes') g;
insert into public.rwy_samples (iata, at, rwy) values ('NRT', now() - interval '1 hour', '34L'), ('NRT', now() - interval '30 minutes', '34R'), ('HND', now(), '22');
insert into public.wx_obs (icao, at, raw, wdir, wspd) values ('RJTT', now() - interval '30 minutes', 'RJTT 18014KT', 180, 14)`);
const sql = fs.readFileSync(new URL('../../docs/pm/hnd-nrt-priority-check.sql', import.meta.url), 'utf8');
const stmts = sql.split(/;\s*\n/).map(s => s.replace(/^\s*--.*$/mg, '').trim()).filter(Boolean);
check('読むだけの SQL は7つ', stmts.length === 7, stmts.length);
const res = [];
for (const [i, s] of stmts.entries()) {
  check(`SQL ${i + 1} は select（読むだけ）`, /^(select|with)\b/i.test(s) && !/\b(insert|update|delete|create|drop|alter|truncate)\b/i.test(s), s.slice(0, 80));
  try { res.push((await db.query(s)).rows); check(`SQL ${i + 1} が流れる`, true); } catch (e) { res.push([]); check(`SQL ${i + 1} が流れる`, false, e.message); }
}
check('1：wx_taf が2空港', res[0].filter(r => r.what === 'wx_taf').length === 2, res[0]);
const nrt2 = res[1].filter(r => r.iata === 'NRT');
check('2：成田は推定と実機が全部合う', nrt2.length > 0 && nrt2.every(r => Number(r.agree_dir) === 100), nrt2);
const hnd4 = res[3].filter(r => r.iata === 'HND' && r.kind === 'since');
check('4：羽田は切り替わりが数えられる', hnd4.length > 0, res[3]);
const hnd7 = res[6].find(r => r.iata === 'HND'), nrt7 = res[6].find(r => r.iata === 'NRT');
check('7：TAF の当たり具合（成田は全部合う・羽田は北風の時間だけ外れる）', !!nrt7 && Number(nrt7.agree_dir) === 100 && !!hnd7 && Number(hnd7.agree_dir) < 100 && Number(hnd7.agree_dir) > 0, res[6]);

// 4. もう一度
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても行はそのまま', await q1(`select count(*)::int from public.wx_taf`) === 3 && await q1(`select count(*)::int from public.wx_taf_hours`) === 10, null);

if (bad) { console.log(`NG ${bad}件`); process.exit(1); }
console.log('t136 すべて OK');
