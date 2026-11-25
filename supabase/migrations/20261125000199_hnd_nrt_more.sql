-- 羽田・成田はいろいろなデータを細かく取る（PM の指示 11/25 18時50分。本人「なんなら羽田と成田のデータは細かくいろんなデータを取ってほしい」）
--   規約の一覧は docs/pm/report-hnd-nrt-more.md。ここでは「使ってよい」と分かっていて、今ある取り込みに足すだけで済む2つを入れる
--   1. 地上の動き（adsb.lol・ODbL）：ground_watch（見張りの状態。短く置く）・ground_moves（1回ごと。ずっと残す）
--      着陸を見た時刻 → 止まった時刻と場所（スポット）・地上を走った時間、動き出した時刻 → 離陸した時刻・滑走路。airport-traffic の記録の処理が書く
--   2. 便の変わったこと（ODPT・基本ライセンス）：flight_changes（羽田・成田に関わる便の、ゲート・機材・状態・見込みの時刻（5分以上）の変化の1件ごと。ずっと残す）
--      flight_schedule は最新の値に上書きされるので、いつ・何から何に変わったかが残らなかった。表のトリガーで残す（関数の変更は要らない）
--   量の見込み：ground_moves は羽田・成田で1日 約2,500行（1年で約90万行・百数十MB）。flight_changes は1日 約3,000行前後（1年で約110万行）
--     どちらも消さない。大きくなったら古い日を cold-archive（ファイル置き場）へ移す（記録は消さない）
--   RLS：有効にして方針は作らない（anon・authenticated は読めも書けもしない）。書くのは関数（service_role）とトリガーだけ
--   影響：チェックイン・経営のどちらの画面にも出さない（構想段階）。flight_schedule の書き込み（apply_flight_status・時刻表の取り込み）に小さなトリガーが1つ増える
set lock_timeout = '5s';

-- 1. 地上の動き
create table if not exists public.ground_watch (
  iata       text not null check (iata ~ '^[A-Z]{3}$'),
  hex        text not null check (length(hex) <= 16),
  callsign   text check (length(callsign) <= 10),
  reg        text check (length(reg) <= 10),
  type       text check (length(type) <= 8),
  mode       text not null check (mode in ('arr', 'park', 'dep')),
  t0         timestamptz,
  rwy        text check (rwy ~ '^[0-9]{2}[LRC]?$'),
  still_n    smallint not null default 0,
  still_at   timestamptz,
  stand_lat  real, stand_lon real,
  last_at    timestamptz not null,
  last_lat   real not null, last_lon real not null,
  last_kt    smallint,
  written_at timestamptz not null default now(),
  primary key (iata, hex)
) with (fillfactor = 70);
comment on table public.ground_watch is '羽田・成田の地上の機体の見張り（airport-traffic が書く。6時間で消える。全機の記録は ground_moves に残る）';
create index if not exists ground_watch_last on public.ground_watch (last_at);

create table if not exists public.ground_moves (
  id        bigint generated always as identity primary key,
  iata      text not null check (iata ~ '^[A-Z]{3}$'),
  hex       text not null check (length(hex) <= 16),
  callsign  text check (length(callsign) <= 10),
  reg       text check (length(reg) <= 10),
  type      text check (length(type) <= 8),
  kind      text not null check (kind in ('arr', 'dep')),
  rwy       text check (rwy ~ '^[0-9]{2}[LRC]?$'),
  t_rwy     timestamptz,                 -- 到着：着陸を見た時刻／出発：離陸した時刻
  t_block   timestamptz,                 -- 到着：止まった時刻／出発：動き出した時刻
  taxi_sec  integer check (taxi_sec between 0 and 21600),
  stand_lat real, stand_lon real,
  lost      boolean not null default false,
  saved_at  timestamptz not null default now()
);
comment on table public.ground_moves is '羽田・成田の地上の動き（着陸・離陸ごとに1行。地上を走った時間・スポットの位置）。adsb.lol（ODbL）から。±30秒の目安。ずっと残す';
create index if not exists ground_moves_iata_at on public.ground_moves (iata, saved_at);

-- 2. 便の変わったこと
create table if not exists public.flight_changes (
  id          bigint generated always as identity primary key,
  at          timestamptz not null default now(),
  schedule_id bigint not null,           -- flight_schedule の行（行が消えても残すので外部キーにしない）
  svc_date    date not null,
  flight      text not null check (length(flight) <= 8),
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$'),
  field       text not null check (field in ('dep_gate', 'arr_gate', 'aircraft', 'dep_status', 'arr_status', 'etd', 'eta')),
  old_v       text check (length(old_v) <= 60),
  new_v       text check (length(new_v) <= 60)
);
comment on table public.flight_changes is '羽田・成田に関わる便の、ゲート・機材・状態・見込みの時刻（5分以上）の変わった記録。ODPT（基本ライセンス）。公開しない。ずっと残す';
create index if not exists flight_changes_sched on public.flight_changes (schedule_id, at);
create index if not exists flight_changes_at on public.flight_changes (at);

create or replace function public.flight_changes_log() returns trigger
language plpgsql security definer set search_path = public as $$
declare rows jsonb := '[]'::jsonb;
begin
  if new.dep_gate is distinct from old.dep_gate then rows := rows || jsonb_build_object('f', 'dep_gate', 'o', old.dep_gate, 'n', new.dep_gate); end if;
  if new.arr_gate is distinct from old.arr_gate then rows := rows || jsonb_build_object('f', 'arr_gate', 'o', old.arr_gate, 'n', new.arr_gate); end if;
  if new.aircraft is distinct from old.aircraft then rows := rows || jsonb_build_object('f', 'aircraft', 'o', old.aircraft, 'n', new.aircraft); end if;
  if new.dep_status is distinct from old.dep_status then rows := rows || jsonb_build_object('f', 'dep_status', 'o', old.dep_status, 'n', new.dep_status); end if;
  if new.arr_status is distinct from old.arr_status then rows := rows || jsonb_build_object('f', 'arr_status', 'o', old.arr_status, 'n', new.arr_status); end if;
  -- 見込みの時刻は5分以上動いたとき（null から入った・null に戻ったときも）
  if (new.etd is null) <> (old.etd is null) or abs(extract(epoch from new.etd - old.etd)) >= 300 then rows := rows || jsonb_build_object('f', 'etd', 'o', old.etd, 'n', new.etd); end if;
  if (new.eta is null) <> (old.eta is null) or abs(extract(epoch from new.eta - old.eta)) >= 300 then rows := rows || jsonb_build_object('f', 'eta', 'o', old.eta, 'n', new.eta); end if;
  insert into public.flight_changes (schedule_id, svc_date, flight, dep, arr, field, old_v, new_v)
  select new.id, new.svc_date, new.flight, new.dep, new.arr, r->>'f', left(r->>'o', 60), left(r->>'n', 60) from jsonb_array_elements(rows) r;
  return null;
end $$;
revoke all on function public.flight_changes_log() from public, anon, authenticated;

drop trigger if exists flight_changes_log on public.flight_schedule;
create trigger flight_changes_log after update of dep_gate, arr_gate, aircraft, dep_status, arr_status, etd, eta on public.flight_schedule
  for each row when ((new.dep in ('HND', 'NRT') or new.arr in ('HND', 'NRT')) and (
    new.dep_gate is distinct from old.dep_gate or new.arr_gate is distinct from old.arr_gate or new.aircraft is distinct from old.aircraft
    or new.dep_status is distinct from old.dep_status or new.arr_status is distinct from old.arr_status
    or new.etd is distinct from old.etd or new.eta is distinct from old.eta))
  execute function public.flight_changes_log();

alter table public.ground_watch enable row level security;
alter table public.ground_moves enable row level security;
alter table public.flight_changes enable row level security;
revoke all on public.ground_watch, public.ground_moves, public.flight_changes from public, anon, authenticated;
grant all on public.ground_watch, public.ground_moves, public.flight_changes to service_role;

-- 見張りの古い行を消す（airport-traffic も消すが、止まっていた回の分の念のため）。毎日 4時53分（日本時間）・上限30秒
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  if exists (select 1 from cron.job where jobname = 'ground-watch-cleanup') then perform cron.unschedule('ground-watch-cleanup'); end if;
  execute $q$ select cron.schedule('ground-watch-cleanup', '53 19 * * *', $job$ set statement_timeout = '30s'; set lock_timeout = '5s';
    delete from public.ground_watch where last_at < now() - interval '1 day' $job$) $q$;
end
$outer$;
reset lock_timeout;
