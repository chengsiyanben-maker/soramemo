// 機体の運用の予想を、たまった記録から学ぶ（案）：機体のつながり・今の予想と同じ決め方・新しい日を重く・機体の型・時刻表・特別塗装機の予定・
// 記録が少ないときは今の予想に戻す・画面向けの関数・毎晩の採点・権限。docs/pm/rotation-backtest.sql（読むだけ）も同じ数になるか確かめる
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
const q = async (sql, args) => (await db.query(sql, args)).rows[0];
const T = `(now() at time zone 'Asia/Tokyo')::date`;
const at = (off, hm) => `((${T} - ${off}) + time '${hm}') at time zone 'Asia/Tokyo'`;
const rows = [];
const leg = (reg, cs, off, hm, endHm, dep, arr, type) => rows.push(`('${reg}', '${cs}', ${T} - ${off}, ${type ? `'${type}'` : 'null'}, ${at(off, hm)}, ${at(off, endHm)}, ${dep ? `'${dep}'` : 'null'}, ${arr ? `'${arr}'` : 'null'})`);
for (let off = 1; off <= 28; off++) {
  // いつも同じ4便（どちらの決め方でも当たる）
  const s = 'JA73S' + (off % 5);
  leg(s, 'SKY1', off, '07:00', '09:00', 'HND', 'FUK', 'B738'); leg(s, 'SKY2', off, '10:00', '12:00', 'FUK', 'HND', 'B738');
  leg(s, 'SKY3', off, '13:00', '14:30', 'HND', 'CTS', 'B738'); leg(s, 'SKY4', off, '15:30', '17:00', 'CTS', 'HND', 'B738');
  // 12日前から次の便が変わった（新しい日を重くすると当たる）
  const r = 'JA60R' + (off % 4);
  leg(r, 'APJ1', off, '08:00', '10:00', 'KIX', 'CTS', 'A320');
  leg(r, off <= 12 ? 'APJ8' : 'APJ2', off, off <= 12 ? '11:30' : '11:00', '13:00', 'CTS', 'KIX', 'A320');
  // 機体の型で次の便が決まる（B789 なら JAL200、B738 なら JAL202）
  const small = off % 3 === 0, j = small ? 'JA30' + (off % 7) + 'J' : 'JA86' + (off % 7) + 'J';
  leg(j, 'JAL100', off, '08:00', '09:10', 'HND', 'ITM', small ? 'B738' : 'B789');
  leg(j, small ? 'JAL202' : 'JAL200', off, '10:00', '11:10', 'ITM', 'HND', small ? 'B738' : 'B789');
  // 到着と出発の空港が食い違う記録（学ぶ予想は使わず、今の予想に戻る）
  if (off <= 4) { leg('JA01AD', 'ADO5', off, '09:00', '10:30', 'HND', 'CTS', 'B763'); leg('JA01AD', 'ADO6', off, '12:00', '13:30', 'HND', 'KMJ', 'B763'); }
}
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values ${rows.join(',\n')}`);
// 今日の分（画面向けの関数で使う）
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values ('JA73S9', 'SKY1', ${T}, 'B738', ${at(0, '07:00')}, ${at(0, '07:30')}, 'HND', 'FUK')`);
for (let off = 0; off <= 28; off++) await db.query(`select public.rot_pairs_build(${T} - ${off})`);

const pc = await q(`select count(*)::int as n, count(*) filter (where not ok)::int as bad, count(*) filter (where prev_cs = 'ADO5' and not ok)::int as ado from public.rot_pairs`);
check('機体のつながりを作る（食い違う記録は印を付けて残す）', pc.n === 28 * 3 + 28 + 28 + 4 && pc.ado === 4 && pc.bad === 4, pc);
const again = await q(`select public.rot_pairs_build(${T} - 1) as n`); const pc2 = await q(`select count(*)::int as n from public.rot_pairs`);
check('何度流しても同じ', again.n === 6 && pc2.n === pc.n, { again, pc2 });

// 今の予想と同じ決め方（base）は predict_rotation_reg と同じ答え
const cur = (await q(`select public.predict_rotation_reg('JA73S9') as p`)).p;
const base = (await q(`select public.rot_predict('base', 'JA73S9', ${T}, 'SKY1', 'FUK', '07:00') as p`)).p;
check('base は今の予想と同じ便を出す', JSON.stringify(cur.next.map(x => x.callsign)) === JSON.stringify(base.map(x => x.callsign)) && base.length === 3 && base[0].callsign === 'SKY2', { cur: cur.next, base });

// 新しい日を重く：今の予想は前の決まり（APJ2）、学ぶ予想は今の決まり（APJ8）
const b2 = (await q(`select public.rot_predict('base', 'JA60R1', ${T}, 'APJ1', 'CTS', '08:00', 1) as p`)).p;
const l2 = (await q(`select public.rot_predict('learn', 'JA60R1', ${T}, 'APJ1', 'CTS', '08:00', 1) as p`)).p;
check('新しい日を重くする', b2[0]?.callsign === 'APJ2' && l2[0]?.callsign === 'APJ8' && l2[0].src === 'learn', { b2, l2 });

// 機体の型：B738 の機体なら JAL202
const l3 = (await q(`select public.rot_predict('learn', 'JA303J', ${T}, 'JAL100', 'ITM', '08:00', 1) as p`)).p;
const b3 = (await q(`select public.rot_predict('base', 'JA303J', ${T}, 'JAL100', 'ITM', '08:00', 1) as p`)).p;
check('その便にいつも入る型で絞る', l3[0]?.callsign === 'JAL202' && b3[0]?.callsign === 'JAL200', { l3, b3 });

// 食い違う記録しかないときは、今の予想に戻す（出どころ base）
const l4 = (await q(`select public.rot_predict('learn', 'JA01AD', ${T}, 'ADO5', 'CTS', '09:00', 1) as p`)).p;
check('記録が少ない・食い違うときは今の予想に戻す', l4[0]?.callsign === 'ADO6' && l4[0].src === 'base', l4);

// 時刻表：JAL・ANA は、その日に飛ぶ便か
await db.exec(`insert into public.timetable (operator, dep, arr, flight, days, valid_from, valid_to, dep_time, arr_time, aircraft) values
  ('JAL', 'ITM', 'HND', 'JL200', 127, ${T} - 60, ${T} + 60, '10:00', '11:10', '789'),
  ('JAL', 'ITM', 'HND', 'JL202', 127, ${T} - 60, ${T} + 60, '10:00', '11:10', '738'),
  ('JAL', 'ITM', 'HND', 'JL300', 2, ${T} - 60, ${T} + 60, '12:00', '13:10', '738')`);
const tt = await q(`select public.rot_tt_ok(d, 'JAL200', 'ITM') as a, public.rot_tt_ok(d, 'JAL200', 'CTS') as b, public.rot_tt_ok(d, 'JAL300', 'ITM') as c,
  public.rot_tt_ok(d, 'SKY1', null) as d, public.rot_tt_ok(d, 'ANA21', 'HND') as e from (select (date '2026-11-03') as d) x`);   // 火曜日
check('時刻表で絞る（月曜だけの便は火曜に出さない・ANA は時刻表がなければ絞らない）', tt.a && !tt.b && !tt.c && tt.d && tt.e, tt);
const l5 = (await q(`select public.rot_predict('learn', 'JA303J', ${T}, 'JAL100', 'ITM', '08:00', 1) as p`)).p;
check('時刻表に載っている便は出る', l5[0]?.callsign === 'JAL202', l5);

// 特別塗装機の予定の便を先に
await db.exec(`insert into public.livery_sightings (reg, name, airline, lat, lon, src) values ('JA8088', '特別塗装A', 'JAL', 35, 139, 'test');
  insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source) values (${T} - 1, 'JL500', 'HND', 'OKA', ${at(1, '12:00')}, ${at(1, '14:30')}, 'test');
  insert into public.livery_plans (schedule_id, flight, dep, arr, std, livery) select id, flight, dep, arr, std, '特別塗装A ジェット' from public.flight_schedule where flight = 'JL500'`);
const l6 = (await q(`select public.rot_predict('learn', 'JA8088', ${T} - 1, 'JAL400', 'HND', '08:00', 2) as p`)).p;
const l6b = (await q(`select public.rot_predict('learn', 'JA8088', ${T} - 1, 'JAL400', 'ITM', '08:00', 1) as p`)).p;
check('特別塗装機の予定の便を先に（出発の空港が合うときだけ）', l6[0]?.callsign === 'JAL500' && l6[0].src === 'livery' && l6[0].arr === 'OKA' && l6b.length === 0, { l6, l6b });

// 画面向けの関数（まだ画面にはつながない）
await db.exec('set role anon'); const v2 = (await q(`select public.predict_rotation_v2('JA73S9') as p`)).p; await db.exec('reset role');
check('画面向け：予想の印と出どころ', v2.estimate === true && v2.known.callsign === 'SKY1' && v2.next[0]?.callsign === 'SKY2' && v2.next[0].src === 'learn', v2);

// 毎晩の採点と、読むだけの SQL が同じ数になる（特別塗装機の機体も前の日に飛んだことにする）
await db.exec(`insert into public.reg_legs (reg, callsign, day, type, first_at, last_at, dep, arr) values
  ('JA8088', 'JAL400', ${T} - 1, 'B738', ${at(1, '08:00')}, ${at(1, '09:10')}, 'ITM', 'HND'), ('JA8088', 'JAL500', ${T} - 1, 'B738', ${at(1, '12:00')}, ${at(1, '14:30')}, 'HND', 'OKA')`);
for (let off = 1; off <= 7; off++) await db.query(`select public.rot_eval_day(${T} - ${off})`);
const ev = (await db.query(`select method, k, sum(n)::int as n, sum(predicted)::int as predicted, sum(hit)::int as hit from public.rot_eval group by 1, 2 order by 1, 2`)).rows;
const learn1 = ev.find(r => r.method === 'learn' && r.k === 1), base1 = ev.find(r => r.method === 'base' && r.k === 1);
check('採点：学ぶ予想は今の予想より当たる（この作り物のデータで）', learn1 && base1 && learn1.hit > base1.hit && learn1.n === base1.n, ev);

const bt = fs.readFileSync(new URL('../../docs/pm/rotation-backtest.sql', import.meta.url), 'utf8');
const code = bt.replace(/--.*$/gm, '');
check('読むだけの SQL：書き込み・表や関数の作成をしない', !/\b(insert|update|delete|create|alter|drop|truncate|grant|revoke|merge|copy)\b/i.test(code) && code.trim().split(';').filter(s => s.trim()).length === 1);
// 時刻表・特別塗装機は作り物の値で動くか確かめたので、採点と同じ条件で比べる
await db.exec(`insert into public.flight_history (svc_date, flight, dep, arr, std, sta, reg, type, callsign) select ${T} - g, f.flight, f.dep, f.arr,
  ((${T} - g) + f.t1) at time zone 'Asia/Tokyo', ((${T} - g) + f.t2) at time zone 'Asia/Tokyo', 'JA861J', 'B789', f.cs
  from generate_series(1, 10) g, (values ('JL100', 'HND', 'ITM', time '08:00', time '09:10', 'JAL100'), ('JL200', 'ITM', 'HND', time '10:00', time '11:10', 'JAL200')) f(flight, dep, arr, t1, t2, cs)`);
for (let off = 1; off <= 10; off++) await db.query(`select public.archive_rotations(${T} - ${off})`);
await db.exec('begin transaction read only');
const out = (await db.query(bt)).rows;
await db.exec('commit');
const all = out.filter(r => r['区分'] === '全体');
const same = ['base', 'learn'].every(m => [1, 2, 3, 4].every(k => {
  const a = all.find(r => r['方式'] === m && r['何便先'] === k), e = ev.find(r => r.method === m && r.k === k);
  return (!a && !e) || (a && e && Number(a['基準の数']) === e.n && Number(a['予想を出した数']) === e.predicted && Number(a['当たり']) === e.hit);
}));
check('読むだけの SQL と毎晩の採点が同じ数', same && all.length > 0, { all, ev });
const obs = all.find(r => r['方式'] === 'obs' && r['何便先'] === 1);
check('今の JAL・ANA の予想（rotation_obs）も測れる', obs && Number(obs['当たり']) > 0 && Number(obs['当たり']) === Number(obs['基準の数']), obs);
const lvr = out.find(r => r['方式'] === 'learn' && r['区分'] === '出どころ' && r['値'] === 'livery' && r['何便先'] === 1);
check('特別塗装機の予定の便も測れる', lvr && Number(lvr['当たり']) === 1, lvr);
const kinds = new Set(out.map(r => r['区分']));
check('区分：全体・会社・機種・羽田発着・出どころ', ['全体', '会社', '機種', '羽田発着', '出どころ'].every(k => kinds.has(k)), [...kinds]);

// 権限：記録と採点は運営だけ
const rls = (await db.query(`select relname, relrowsecurity from pg_class where relname in ('rot_pairs', 'rot_eval')`)).rows;
check('行レベルセキュリティ', rls.length === 2 && rls.every(r => r.relrowsecurity), rls);
for (const [label, sql] of [['つながりの表', `select count(*) from public.rot_pairs`], ['採点の表', `select count(*) from public.rot_eval`],
  ['採点', `select public.rot_eval_day(${T} - 1)`], ['予想の本体', `select public.rot_predict('learn', 'JA73S9', ${T}, 'SKY1', null, null)`], ['毎晩', `select public.rot_nightly()`]]) {
  for (const role of ['anon', 'authenticated']) {
    let denied = false; await db.exec(`set role ${role}`); try { await db.query(sql); } catch { denied = true; } await db.exec('reset role');
    check(`${label}は ${role} から使えない`, denied);
  }
}
const night = (await q(`select public.rot_nightly() as r`)).r;
check('毎晩の処理', night.pairs === 7 && night.eval_rows > 0, night);
if (bad) process.exit(1);
