// 撮る人の一覧の登録記号：確認（その便を見つけた）・前の便から・予想（2つたどる）・別の便で見つかった機体は前から予想しない・割合が低いものは出さない
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

// 便を足す（運航日は出発の日本時間の日付）。std・sta は「いまから何分」。reg があれば見張りが機体を見つけたことにする
async function fl(flight, dep, arr, std, sta, reg) {
  const r = await db.query(`insert into public.flight_schedule (svc_date, flight, dep, arr, std, sta, source)
    values (((now() + make_interval(mins => $4::int)) at time zone 'Asia/Tokyo')::date, $1, $2, $3, now() + make_interval(mins => $4::int), now() + make_interval(mins => $5::int), 'test') returning id`, [flight, dep, arr, std, sta]);
  if (reg) await db.query(`insert into public.flight_watch (schedule_id, state) values ($1, $2::jsonb)`, [r.rows[0].id, JSON.stringify({ phase: 'landed', reg })]);
}
// 前の日々の機体のつながり（prev → next を n 回）
let nObs = 0;
async function obs(prev, next, n, iata) {
  for (let i = 1; i <= n; i++) await db.query(`insert into public.rotation_obs (svc_date, reg, prev_flight, next_flight, iata, turn_min)
    values ((now() at time zone 'Asia/Tokyo')::date - $1::int, 'JA' || $2::int, $3, $4, $5, 60)`, [i, ++nObs, prev, next, iata]);
}

// 確認：着陸に来る NH50 を機体の位置で見つけている
await fl('NH50', 'ITM', 'HND', -40, 30, 'JA802A');
// 前の便から：NH10（伊丹→羽田）で JA801A。NH10 のあとは NH20 が4回、NH99 が1回
await fl('NH10', 'ITM', 'HND', -130, -60, 'JA801A');
await fl('NH20', 'HND', 'CTS', 60, 150);
await obs('NH10', 'NH20', 4, 'HND'); await obs('NH10', 'NH99', 1, 'HND');
// 予想：NH31（福岡→伊丹）で JA803A → NH32（伊丹→羽田、まだ見つけていない）→ NH33（羽田→那覇）
await fl('NH31', 'FUK', 'ITM', -150, -80, 'JA803A');
await fl('NH32', 'ITM', 'HND', -30, 40);
await fl('NH33', 'HND', 'OKA', 100, 250);
await obs('NH31', 'NH32', 4, 'ITM'); await obs('NH32', 'NH33', 4, 'HND');
// 別の便で見つかった機体：JA804A は NH40（→羽田）のあと NH41（羽田→伊丹）でも見つかっている。NH40 → NH42 のつながりがあっても予想しない
await fl('NH40', 'CTS', 'HND', -400, -300, 'JA804A');
await fl('NH41', 'HND', 'ITM', -200, -130, 'JA804A');
await fl('NH42', 'HND', 'KOJ', 70, 170);
await obs('NH40', 'NH42', 5, 'HND');
// 割合が低い：NH70（→羽田）で JA805A。NH70 のあとは NH71 が2回、NH79 が3回（NH71 は4割に届かず、NH79 は今日ない）
await fl('NH70', 'KOJ', 'HND', -200, -100, 'JA805A');
await fl('NH71', 'HND', 'KMJ', 80, 180);
await obs('NH70', 'NH71', 2, 'HND'); await obs('NH70', 'NH79', 3, 'HND');
// 3時間半より先の便は出さない
await fl('NH90', 'HND', 'FUK', 300, 400);
await obs('NH10', 'NH90', 4, 'HND');

await db.exec('set role anon');
const rows = (await db.query(`select public.spot_regs('HND') as r`)).rows[0].r;
await db.exec('reset role');
const by = Object.fromEntries(rows.map(x => [x.flight, x]));
check('確認：その便を見つけた機体', by.NH50?.reg === 'JA802A' && by.NH50.src === 'live' && by.NH50.dir === 'arr', by.NH50);
check('前の便から：前の便の機体と割合', by.NH20?.reg === 'JA801A' && by.NH20.src === 'prev' && by.NH20.via === 'NH10' && Number(by.NH20.share) >= 0.4 && by.NH20.dir === 'dep', by.NH20);
check('前の便から：まだ見つけていない着陸の便', by.NH32?.reg === 'JA803A' && by.NH32.src === 'prev', by.NH32);
check('予想：2つたどる', by.NH33?.reg === 'JA803A' && by.NH33.src === 'pred' && by.NH33.via === 'NH31', by.NH33);
check('別の便で見つかった機体は、古い便から予想しない', !by.NH42, by.NH42);
check('割合が低いつながりは出さない', !by.NH71, by.NH71);
check('3時間半より先の便は出さない', !by.NH90, by.NH90);
check('出発した空港（伊丹）の便は出さない', !by.NH31 && !by.NH10, rows.map(x => x.flight));

// 空港の形でない値は空
await db.exec('set role anon');
const empty = (await db.query(`select public.spot_regs('hnd; drop') as r`)).rows[0].r;
let denied = false; try { await db.query(`select * from public.flight_watch`); } catch { denied = true; }
await db.exec('reset role');
check('空港の形でない値は空', Array.isArray(empty) && empty.length === 0, empty);
check('表は直接読めない（RLS はそのまま）', denied);
if (bad) process.exit(1);
