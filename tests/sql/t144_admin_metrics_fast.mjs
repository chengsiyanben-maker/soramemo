// 定期の手入れ 11/26 の4回目：admin_metrics の日別を「範囲で1回読んで日ごとにまとめる」形にしても、返す中身が前と同じか（移行 admin_metrics_fast）
//   1. 前の関数（移行204まで）と後の関数（移行205）に同じ種をまき、p_days = 3（→7日）・30・120・500（→120日）で返り値がまったく同じ
//   2. 日本時間の日の境目（0時ちょうど・23時59分）・見る期間の外（121日前・明日）・起点（stats_since）より前の行も、前と同じに数える
//   3. 起点を期間の途中に置いても同じ
//   4. 管理者でなければ前と同じく 'admin only'。権限は authenticated だけのまま（anon は呼べない）
//   5. 全部読みの回数が減る（ops.usage_events は全部読みなしで索引から引く）
//   流す所の時間帯が UTC でも日本時間でも同じ結果になるよう、種の時刻は日本時間で作る
import { PGlite } from '@electric-sql/pglite';
import fs from 'fs';
const dir = new URL('../../supabase/migrations/', import.meta.url).pathname;
const files = fs.readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
const mine = files.find(f => f.endsWith('_admin_metrics_fast.sql'));
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 400)); if (!ok) bad++; };
check('移行がある', !!mine);

const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin; create schema auth;
create table auth.users (id uuid primary key, email text, created_at timestamptz default now());
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create function auth.jwt() returns jsonb language sql stable as $$ select coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb, '{}'::jsonb) $$;
grant usage on schema public, auth to anon, authenticated, service_role; grant execute on function auth.uid(), auth.jwt() to anon, authenticated, service_role;`);
for (const f of files) if (f !== mine) await db.exec(fs.readFileSync(dir + f, 'utf8'));

const ADM = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
await db.exec(`insert into auth.users (id, email, created_at) values ('${ADM}', 'a@x', now() - interval '400 days'); insert into ops.admins values ('${ADM}');`);
// 日本時間の「今日の0時」から何日前・何時何分、で時刻を作る
const J = (days, hm) => `((((now() at time zone 'Asia/Tokyo')::date - ${days})::timestamp + time '${hm}') at time zone 'Asia/Tokyo')`;
const pts = [];
for (const days of [-1, 0, 1, 2, 6, 7, 29, 30, 31, 60, 119, 120, 121, 200]) for (const hm of ['00:00', '00:00:01', '08:59:59', '09:00', '15:00', '23:59:59']) pts.push([days, hm]);
let i = 0;
for (const [days, hm] of pts) {
  i++;
  const u = `00000000-0000-0000-0000-${String(i).padStart(12, '0')}`;
  await db.exec(`insert into auth.users (id, email, created_at) values ('${u}', 'u${i}@x', ${J(days, hm)});
    insert into public.checkins (user_id, airport_id, lat, lon, accuracy_m, position_at, created_at) values
      ('${u}', 1, 35.5, 139.7, 10, ${J(days, hm)}, ${J(days, hm)}), ('${ADM}', 2, 35.5, 139.7, 10, ${J(days, hm)}, ${J(days, hm)});
    insert into public.flights (user_id, from_airport, to_airport, dep_at, arr_at, distance_km) values
      ('${u}', 1, 2, ${J(days, hm)} - interval '1 hour', ${J(days, hm)}, 300);
    insert into ops.usage_events (session, event, created_at) values ('s${i % 5}', 'open', ${J(days, hm)}), ('s${i}', 'open', ${J(days, hm)}), ('s${i}', 'tab', ${J(days, hm)});`);
}
const asAdmin = `select set_config('request.jwt.claim.sub', '${ADM}', false); select set_config('request.jwt.claims', '${JSON.stringify({ sub: ADM, aal: 'aal2' })}', false);`;
await db.exec(asAdmin);
const DAYS = [3, 30, 120, 500];
const run = async () => { const o = {}; for (const p of DAYS) o[p] = (await db.query(`select public.admin_metrics(${p}) r`)).rows[0].r; return o; };
const seq = async () => {
  const T = `select schemaname||'.'||relname t, seq_scan n from pg_stat_xact_user_tables where relname in ('checkins','flights','usage_events','users')`;
  await db.exec('begin; set local enable_seqscan = off');
  const a = Object.fromEntries((await db.query(T)).rows.map(r => [r.t, Number(r.n)]));
  await db.query(`select public.admin_metrics(120)`);
  const b = Object.fromEntries((await db.query(T)).rows.map(r => [r.t, Number(r.n) - (a[r.t] || 0)]));
  await db.exec('rollback'); return b;
};
const orig = (await db.query(`select value from ops.flags where key = 'stats_since'`)).rows[0]?.value;
const setSince = v => v === undefined ? db.exec(`delete from ops.flags where key = 'stats_since'`)
  : db.query(`insert into ops.flags (key, value) values ('stats_since', $1::jsonb) on conflict (key) do update set value = excluded.value`, [JSON.stringify(v)]);
const SINCE30 = (await db.query(`select to_jsonb(${J(30, '09:00')}) v`)).rows[0].v;
await setSince(undefined);
const oldAll = await run();
await setSince(SINCE30);
const oldSince = await run();
await setSince(undefined);
const seqOld = await seq();

await db.exec(fs.readFileSync(dir + mine, 'utf8'));
await db.exec(asAdmin);
const newAll = await run();
await setSince(SINCE30);
const newSince = await run();
await setSince(undefined);
const seqNew = await seq();
await setSince(orig);

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
for (const p of DAYS) {
  check(`p_days=${p}：前と同じ（起点なし）`, same(oldAll[p], newAll[p]), { old: oldAll[p].daily?.slice(-3), new: newAll[p].daily?.slice(-3) });
  check(`p_days=${p}：前と同じ（起点が30日前）`, same(oldSince[p], newSince[p]), { old: oldSince[p].daily?.slice(-32, -28), new: newSince[p].daily?.slice(-32, -28) });
}
check('日の数は 7・30・120・120', DAYS.map(p => newAll[p].daily.length).join() === '7,30,120,120', DAYS.map(p => newAll[p].daily.length));
const today = newAll[30].daily.at(-1);
check('今日の行に数が入る（0時ちょうど〜23時59分の6つ。明日の分は入らない）', today.checkins === 12 && today.flights === 6 && today.signups === 6, today);
check('期間の外（121日前）は入らない', newAll[120].daily[0].checkins === 12 && newAll[120].daily.every(d => d.checkins <= 12), newAll[120].daily[0]);
const sinceRow = newSince[120].daily.find(d => d.day === newSince[120].daily.at(-31).day);
check('起点の日は起点（9時）より後だけ数える', sinceRow && sinceRow.signups === 3 && sinceRow.flights === 6, sinceRow);
check('ほかの項目（active7・top_airports など）も同じ', same({ ...oldAll[30], daily: 0 }, { ...newAll[30], daily: 0 }));

// 管理者でないとき・権限
const U2 = '00000000-0000-0000-0000-000000000001';
await db.exec(`select set_config('request.jwt.claim.sub', '${U2}', false); select set_config('request.jwt.claims', '${JSON.stringify({ sub: U2, aal: 'aal2' })}', false);`);
let err = ''; try { await db.query(`select public.admin_metrics(30)`); } catch (e) { err = e.message; }
check('管理者でなければ admin only', /admin only/.test(err), err);
const g = (await db.query(`select has_function_privilege('anon', 'public.admin_metrics(integer)', 'execute') a, has_function_privilege('authenticated', 'public.admin_metrics(integer)', 'execute') u`)).rows[0];
check('anon は呼べない・authenticated は呼べる（前のまま）', g.a === false && g.u === true, g);
const sd = (await db.query(`select prosecdef, proconfig from pg_proc where oid = 'public.admin_metrics(integer)'::regprocedure`)).rows[0];
check('security definer と search_path は前のまま', sd.prosecdef === true && JSON.stringify(sd.proconfig).includes('search_path=ops, public, auth'), sd);

// 全部読みの回数
const sum = o => Object.values(o).reduce((a, b) => a + b, 0);
check(`全部読みが減る（前 ${sum(seqOld)} 回 → 後 ${sum(seqNew)} 回）`, sum(seqNew) < sum(seqOld) / 10, { seqOld, seqNew });
check('ops.usage_events は全部読みなし（索引から引く）', !seqNew['ops.usage_events'], seqNew);

console.log(bad ? `NG ${bad}` : 'すべて OK');
process.exit(bad ? 1 : 0);
