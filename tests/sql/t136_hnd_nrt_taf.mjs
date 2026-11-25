// 羽田・成田の TAF と滑走路の予想の当たり具合（移行 198）
//   1. taf_obs・taf_hours：入る・同じ発表は重ならない・形の誤りは入らない
//   2. 権限：利用者（anon・authenticated）は読めない・書けない・関数を呼べない。RLS は ON
//   3. rwy_wx_eval：作った記録で、いまの推定・実況の風（追い風7kt）・粘り・TAF の当たりの数が手で数えたとおり
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
let bad = 0; const check = (label, ok, v) => { console.log((ok ? 'OK ' : 'NG ') + label, ok ? '' : JSON.stringify(v)?.slice(0, 900)); if (!ok) bad++; };
const q = async (sql) => (await db.query(sql)).rows;
const q1 = async (sql) => Object.values((await db.query(sql)).rows[0] ?? {})[0];
const fails = async (sql) => { try { await db.exec(sql); return false; } catch { return true; } };

for (const f of files) { if (f === mine) break; await db.exec(fs.readFileSync(dir + f, 'utf8')); }
check('移行は 198 番', /^\d{8}000198_hnd_nrt_taf\.sql$/.test(mine), mine);
await db.exec(fs.readFileSync(dir + mine, 'utf8'));

// 1. 表
const T0 = `date_trunc('hour', now()) - interval '10 hours'`;
await db.exec(`insert into public.taf_obs (icao, issued_at, valid_from, valid_to, raw) values ('RJTT', ${T0} - interval '7 hours', ${T0} - interval '6 hours', ${T0} + interval '24 hours', 'TAF RJTT ...')`);
check('同じ発表は重ならない（ignore）', (await q(`insert into public.taf_obs (icao, issued_at, valid_from, valid_to, raw) values ('RJTT', ${T0} - interval '7 hours', ${T0}, ${T0} + interval '1 hour', 'x') on conflict do nothing returning icao`)).length === 0, null);
check('有効の終わりが始まりより前は入らない', await fails(`insert into public.taf_obs (icao, issued_at, valid_from, valid_to, raw) values ('RJAA', now(), now(), now() - interval '1 hour', 'x')`), null);
check('空港の形の誤りは入らない', await fails(`insert into public.taf_hours (icao, hr, issued_at, wdir, wspd) values ('HND', now(), now(), 10, 5)`), null);
check('風向 400 は入らない', await fails(`insert into public.taf_hours (icao, hr, issued_at, wdir, wspd) values ('RJTT', now(), now(), 400, 5)`), null);

// 2. 権限
for (const t of ['taf_obs', 'taf_hours']) {
  check(`${t} の RLS は ON`, await q1(`select relrowsecurity from pg_class where oid = 'public.${t}'::regclass`) === true, null);
  for (const r of ['anon', 'authenticated']) {
    check(`${r} は ${t} を読めない`, await fails(`set role ${r}; select * from public.${t}; reset role;`), null); await db.exec('reset role');
    check(`${r} は ${t} に書けない`, await fails(`set role ${r}; delete from public.${t}; reset role;`), null); await db.exec('reset role');
  }
}
for (const r of ['anon', 'authenticated']) {
  check(`${r} は rwy_wx_eval を呼べない`, await fails(`set role ${r}; select * from public.rwy_wx_eval('HND', 7); reset role;`), null); await db.exec('reset role');
}
check('空港が HND・NRT 以外は止まる', await fails(`select * from public.rwy_wx_eval('ITM', 7)`), null);

// 3. 当たり具合：羽田の記録を5分ごとに12行（T0 から1時間。日本時間の昼）
//   風：340°・10kt（追い風 −9.8）×4 → 160°・10kt（追い風 +9.8）×4 → 160°・6kt（+5.9）×4
//   実機：北 ×5 → 南 ×7（5行目と6行目の間で切り替わる）。記録の est_mode：北 ×4 → 南 ×8
await db.exec(`insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode)
  select ${T0} + make_interval(mins => 5 * g), 'HND', case when g < 4 then 340 else 160 end, case when g < 8 then 10 else 6 end,
         case when g < 4 then 'north' else 'south' end, case when g < 5 then 'north' else 'south' end
  from generate_series(0, 11) g;
  insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode, obs_mixed) values (${T0} + interval '3 minutes', 'HND', 0, 0, 'north', 'south', true);`);
// 日本時間の時刻で区分が変わるので、区分ごとではなく「すべて」と「切り替わりの前後」で見る
const ev = await q(`select * from public.rwy_wx_eval('HND', 7)`);
const row = (k, p) => ev.find(r => r.kind.startsWith(k) && r.part === p);
check('分かれていた回は数えない（すべて＝12）', row('1.', 'すべて')?.n === 12, ev.slice(0, 3));
check('いまの推定：12のうち11当たり（5行目だけ外れ）', row('1.', 'すべて')?.hit === 11, row('1.', 'すべて'));
// 追い風7kt：南になるのは追い風 > 7 の 5〜8行目（g=4..7）だけ。g=8..11（+5.9）は北と当てて外れる。g=4 は実機が北で外れ
check('実況の風（追い風7kt）：12のうち7当たり', row('2.', 'すべて')?.hit === 7, row('2.', 'すべて'));
// 追い風5kt・粘りなし：g=4..11 を南。外れは g=4 だけ → 11
const c5 = ev.find(r => r.kind === '4. 組 追い風5kt・粘り0分・戻り幅0kt' && r.part === 'すべて');
check('追い風5kt：12のうち11当たり', c5?.hit === 11, c5);
// 追い風7kt・戻り幅3kt：一度南になったら追い風 ≥ 4 のあいだ南のまま → g=4..11 を南 → 11
const h3 = ev.find(r => r.kind === '4. 組 追い風7kt・粘り0分・戻り幅3kt' && r.part === 'すべて');
check('追い風7kt・戻り幅3kt（粘り）：12のうち11当たり', h3?.hit === 11, h3);
// 追い風7kt・粘り30分：南に変わるのは g=4 から30分後の g=10。g=8,9 は追い風5.9で北に戻りたいので待ちが消える → 実は南にならない → g=0..4 の5当たり
const k30 = ev.find(r => r.kind === '4. 組 追い風7kt・粘り30分・戻り幅0kt' && r.part === 'すべて');
check('追い風7kt・粘り30分：12のうち5当たり', k30?.hit === 5, k30);
check('いちばん良い組が出る（11当たり）', ev.some(r => r.kind.startsWith('3.') && r.part === 'すべて' && r.hit === 11), ev.filter(r => r.kind.startsWith('3.')));
const sw = row('2.', '切り替わりの前後30分');
check('切り替わりの前後30分（切り替わり g=5 の25分前〜30分後で12行すべて）', sw?.n === 12 && !ev.some(r => r.kind.startsWith('2.') && r.part === '切り替わりから離れた時間'), sw);

// TAF：T0 の7時間前に出た発表で、T0 の時間は 160°・12kt（追い風 +11.8）→ 1・3・6時間前の発表として12行すべて南と当てる（実機は北5・南7）
await db.exec(`insert into public.taf_hours (icao, hr, issued_at, wdir, wspd) values ('RJTT', ${T0}, ${T0} - interval '7 hours', 160, 12), ('RJTT', ${T0} + interval '1 hour', ${T0} - interval '7 hours', 160, 12)`);
const ev2 = await q(`select * from public.rwy_wx_eval('HND', 7)`);
const taf1 = ev2.find(r => r.kind === '5. TAF 1時間以上前の発表（追い風7kt）' && r.part === 'すべて');
check('TAF 1時間以上前：12のうち7当たり', taf1?.n === 12 && taf1?.hit === 7, taf1);
check('TAF 12時間以上前は予報がないので出ない', !ev2.some(r => r.kind.startsWith('5. TAF 12時間')), ev2.filter(r => r.kind.startsWith('5.')).map(r => r.kind));
// 新しい発表（2時間前に出た）があれば、1時間以上前の当て方はそちらを使う。3時間以上前は古いほう
await db.exec(`insert into public.taf_hours (icao, hr, issued_at, wdir, wspd) values ('RJTT', ${T0}, ${T0} - interval '2 hours', 340, 12), ('RJTT', ${T0} + interval '1 hour', ${T0} - interval '2 hours', 340, 12)`);
const ev3 = await q(`select * from public.rwy_wx_eval('HND', 7)`);
const n1 = ev3.find(r => r.kind === '5. TAF 1時間以上前の発表（追い風7kt）' && r.part === 'すべて'), n3 = ev3.find(r => r.kind === '5. TAF 3時間以上前の発表（追い風7kt）' && r.part === 'すべて');
check('1時間以上前は新しい発表（北）で5当たり・3時間以上前は古い発表（南）で7当たり', n1?.hit === 5 && n3?.hit === 7, [n1, n3]);
check('成田は記録がなければ0行', (await q(`select * from public.rwy_wx_eval('NRT', 7)`)).length === 0, null);
// 成田：16 向き（a）を南として数える
await db.exec(`insert into public.ops_log (at, iata, wdir, wspd, est_mode, obs_mode) values (${T0}, 'NRT', 160, 12, 'a', 'a'), (${T0} + interval '5 minutes', 'NRT', 340, 12, 'b', 'b')`);
const nrt = (await q(`select * from public.rwy_wx_eval('NRT', 7)`)).find(r => r.kind.startsWith('2.') && r.part === 'すべて');
check('成田：a＝16向き・b＝34向きで2つとも当たり', nrt?.n === 2 && nrt?.hit === 2, nrt);

// 4. もう一度
await db.exec(fs.readFileSync(dir + mine, 'utf8'));
check('もう一度流しても表の中身はそのまま', await q1(`select count(*)::int from public.taf_hours`) === 4, null);
check('移行のあと lock_timeout は元に戻る', (await q1(`show lock_timeout`)) === '0', null);

console.log(bad ? `\n${bad} 件 NG` : '\nすべて OK'); process.exit(bad ? 1 : 0);
