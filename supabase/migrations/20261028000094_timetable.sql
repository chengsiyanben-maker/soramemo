-- 修行の計画の画面：JAL・ANA の国内線の時刻表（ODPT の公式のフライト時刻表、公共交通オープンデータ基本ライセンス）。
-- ・timetable：曜日（日曜=1 … 土曜=64 の足し算）と有効な期間つきで持ち、先の日の便も組めるようにする。利用者からは直接読めない
-- ・plan_timetable(日付, 航空会社)：その日に飛ぶ便だけを返す（ログインしていなくても使える。画面には出典を添える）
-- ・timetable_replace：取り込みの関数（timetable-sync）が、空港・航空会社ごとに1回の処理で入れ替える
-- ・timetable-sync 関数を毎日 日本時間 3:00〜4:55 に5分ごとに呼ぶ（1回に6空港、20時間に1回）
create table if not exists public.timetable (
  operator    text not null check (operator in ('JAL', 'ANA')),
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$' and arr <> dep),
  flight      text not null check (flight ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$'),
  days        smallint not null check (days between 1 and 127),
  valid_from  date not null,
  valid_to    date not null check (valid_to >= valid_from),
  dep_time    text not null check (dep_time ~ '^[0-2][0-9]:[0-5][0-9]$'),
  arr_time    text not null check (arr_time ~ '^[0-2][0-9]:[0-5][0-9]$'),
  arr_day     smallint not null default 0 check (arr_day in (0, 1)),
  aircraft    text check (aircraft is null or length(aircraft) <= 20),
  synced_at   timestamptz not null default now(),
  primary key (operator, dep, flight, valid_from, valid_to, dep_time)
);
create index if not exists timetable_op_valid on public.timetable (operator, valid_to, valid_from);
alter table public.timetable enable row level security;
revoke all on public.timetable from public, anon, authenticated;

create table if not exists public.timetable_sync_runs (
  iata    text primary key check (iata ~ '^[A-Z]{3}$'),
  ran_at  timestamptz not null default now(),
  result  jsonb
);
alter table public.timetable_sync_runs enable row level security;
revoke all on public.timetable_sync_runs from public, anon, authenticated;

-- その日に飛ぶ便。f は [便名, 出発, 到着, 出発時刻, 到着時刻, 翌日着(0/1), 機材] の並び。
-- until：その航空会社の時刻表が出ている最後の日（その日より先は「時刻表がまだ出ていない」）
create or replace function public.plan_timetable(p_date date, p_operator text) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'date', p_date, 'operator', p_operator,
    'until', (select max(valid_to) from public.timetable where operator = p_operator),
    'f', coalesce((select jsonb_agg(jsonb_build_array(t.flight, t.dep, t.arr, t.dep_time, t.arr_time, t.arr_day, t.aircraft) order by t.dep_time, t.flight)
      from public.timetable t
      where t.operator = p_operator and t.valid_from <= p_date and t.valid_to >= p_date
        and (t.days & (1 << extract(dow from p_date)::int)) <> 0), '[]'::jsonb))
  where p_operator in ('JAL', 'ANA')
    and p_date between (now() at time zone 'Asia/Tokyo')::date - 1 and (now() at time zone 'Asia/Tokyo')::date + 400
$$;
revoke all on function public.plan_timetable(date, text) from public;
grant execute on function public.plan_timetable(date, text) to anon, authenticated;

-- 取り込みの入れ替え（サーバーの関数だけが使う）
create or replace function public.timetable_replace(p_operator text, p_dep text, p_rows jsonb) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  if p_operator not in ('JAL', 'ANA') or p_dep !~ '^[A-Z]{3}$' or jsonb_typeof(p_rows) <> 'array' then raise exception 'bad input'; end if;
  delete from public.timetable where operator = p_operator and dep = p_dep;
  insert into public.timetable (operator, dep, arr, flight, days, valid_from, valid_to, dep_time, arr_time, arr_day, aircraft)
  select p_operator, p_dep, r->>'arr', r->>'flight', (r->>'days')::smallint, (r->>'valid_from')::date, (r->>'valid_to')::date,
         r->>'dep_time', r->>'arr_time', coalesce((r->>'arr_day')::smallint, 0), nullif(r->>'aircraft', '')
  from jsonb_array_elements(p_rows) r
  where r->>'dep' = p_dep and r->>'operator' = p_operator
  on conflict do nothing;
  get diagnostics n = row_count;
  return n;
end;
$$;
revoke all on function public.timetable_replace(text, text, jsonb) from public, anon, authenticated;
grant execute on function public.timetable_replace(text, text, jsonb) to service_role;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、時刻表の取り込みの定期実行は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  -- 日本時間 3:00〜4:55（世界時 18:00〜19:55）に5分ごと
  execute $q$
    select cron.schedule('timetable-sync', '*/5 18,19 * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/timetable-sync',
        headers := '{"User-Agent": "soramemo (timetable-sync)"}'::jsonb,
        timeout_milliseconds := 120000)
    $job$)
  $q$;
end
$outer$;
