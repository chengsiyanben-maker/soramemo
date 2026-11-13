// 経営の毎日・毎時の仕事（co・co3）に時間の上限が付いたか（移行 co_cron_timeout）
//   1. 今動いている経営の仕事がすべて付け直されている（止めた co3-trouble-detect は作らない）
//   2. どれも文の先頭で statement_timeout と lock_timeout を付ける
//   3. 時刻と中身は前のまま（上限の2つの set を除くと、前の移行の文と同じ）
//   4. 上限は 15分ごと・毎時は1分以下、外の取り込みは30秒、ほかは5分以下
//   5. 仕事の文は、そのまま流して通る（外の取り込みを除く。空のデータベースで）
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_co_cron_timeout.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)); if (!ok) bad++; };
const RE = /cron\.schedule\('([a-z0-9-]+)',\s*'([^']+)',\s*\$job\$(.*?)\$job\$/gs;
const norm = s => s.replace(/set statement_timeout = '[^']+';\s*set lock_timeout = '[^']+';/g, '').replace(/\s+/g, ' ').trim();

// 前の移行までで、今動いている経営の仕事
const before = new Map();
for (const f of files) {
  if (f === mine) break;
  const s = fs.readFileSync(dir + f, 'utf8');
  for (const m of s.matchAll(RE)) if (/^co3?-/.test(m[1])) before.set(m[1], { when: m[2], cmd: m[3] });
  for (const m of s.matchAll(/cron\.unschedule\('([a-z0-9-]+)'/g)) before.delete(m[1]);
}
check('移行がある', !!mine);
const now = new Map([...fs.readFileSync(dir + mine, 'utf8').matchAll(RE)].map(m => [m[1], { when: m[2], cmd: m[3] }]));
check(`経営の仕事 ${before.size}本がすべて付け直されている`, [...before.keys()].every(k => now.has(k)), [...before.keys()].filter(k => !now.has(k)));
check('止めた仕事・知らない仕事は作らない', [...now.keys()].every(k => before.has(k)), [...now.keys()].filter(k => !before.has(k)));
check('co3-trouble-detect は作らない', !now.has('co3-trouble-detect'));
for (const [k, v] of now) {
  const o = before.get(k); if (!o) continue;
  const head = v.cmd.trim().match(/^set statement_timeout = '(\d+)(s|min)'; set lock_timeout = '5s';/);
  check(`${k}：文の先頭で statement_timeout と lock_timeout 5s`, !!head, v.cmd.slice(0, 80));
  check(`${k}：時刻が同じ（${o.when}）`, v.when === o.when, v.when);
  check(`${k}：中身が同じ`, norm(v.cmd) === norm(o.cmd), [norm(v.cmd), norm(o.cmd)]);
  if (!head) continue;
  const sec = +head[1] * (head[2] === 'min' ? 60 : 1), often = !/^\d+ \d+ \* \* \*$/.test(v.when), http = /net\.http_get/.test(v.cmd);
  check(`${k}：上限 ${sec}秒が決まりの中`, http ? sec <= 30 : often ? sec <= 60 : sec <= 300, sec);
}

// 空のデータベースで、移行を全部流し、仕事の文をそのまま流す
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select jsonb_build_object('sub', current_setting('request.jwt.claim.sub', true), 'aal', 'aal2') $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
let applied = true;
try { for (const f of files) await db.exec(fs.readFileSync(dir + f, 'utf8')); } catch (e) { applied = false; console.log(e.message); }
check('移行を全部流せる（pg_cron がないときは何もしない）', applied);
for (const [k, v] of now) {
  if (/net\.http_get/.test(v.cmd)) continue;
  let err = null; try { await db.exec(v.cmd); } catch (e) { err = e.message; }
  check(`${k}：文をそのまま流して通る`, !err, err);
}
const st = (await db.query(`show statement_timeout`)).rows[0].statement_timeout;
check('流したあと、上限は付いたまま（同じつながりの中だけ）', /min|s$/.test(st), st);
console.log(bad ? `NG ${bad}件` : 'すべて通過'); process.exit(bad ? 1 : 0);
