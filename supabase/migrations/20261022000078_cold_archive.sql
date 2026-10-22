-- 古い記録をファイル置き場に移す（ずっと残しつつ、データベースを軽く保つ）
--   400日より前の日の記録を、日ごと・表ごとに gzip した JSON にして、非公開のファイル置き場（Storage の cold）へ移し、データベースからは消す。
--   ODPT のデータを含むものがあるので、置き場は非公開。空の道すじは cold-tracks 関数を通して、航跡の線だけを返す。
--   cold_days：移した日の控え（どこに、何行）。移したあとも、ここを見ればどの日の記録がどこにあるか分かる
create table if not exists public.cold_days (
  tbl      text not null check (tbl in ('airport_tracks_all', 'flight_tracks', 'flight_history', 'reg_legs', 'rwy_samples', 'ops_log', 'ga_events', 'rotation_obs')),
  day      date not null,
  path     text not null,
  rows     int not null,
  bytes    int,
  moved_at timestamptz not null default now(),
  primary key (tbl, day)
);
alter table public.cold_days enable row level security;
revoke all on public.cold_days from public, anon, authenticated;

-- 移す日の候補（運営だけ）：表ごとに、p_before より前で、まだ移していない日を古い順に
create or replace function public.cold_candidates(p_before date, p_limit int default 6) returns table (tbl text, day date)
language sql stable security definer set search_path = public as $$
  select t.tbl, t.day from (
    select 'airport_tracks_all' as tbl, day from public.airport_tracks_all where day < p_before group by day
    union all select 'flight_tracks', svc_date from public.flight_tracks where svc_date < p_before group by svc_date
    union all select 'flight_history', svc_date from public.flight_history where svc_date < p_before group by svc_date
    union all select 'reg_legs', day from public.reg_legs where day < p_before group by day
    union all select 'rotation_obs', svc_date from public.rotation_obs where svc_date < p_before group by svc_date
    union all select 'rwy_samples', (at at time zone 'Asia/Tokyo')::date from public.rwy_samples where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
    union all select 'ops_log', (at at time zone 'Asia/Tokyo')::date from public.ops_log where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
    union all select 'ga_events', (at at time zone 'Asia/Tokyo')::date from public.ga_events where at < (p_before::timestamp at time zone 'Asia/Tokyo') group by 2
  ) t
  -- 航跡は、同じ日の便の実績（出発・到着の空港）と一緒に読むので、便の実績より先に移す
  order by t.day, case t.tbl when 'flight_tracks' then 0 when 'flight_history' then 2 else 1 end
  limit greatest(1, least(coalesce(p_limit, 6), 40))
$$;
revoke all on function public.cold_candidates(date, int) from public, anon, authenticated;

-- その日の記録（運営だけ）。flight_tracks には、便の実績の出発・到着の空港を付ける
create or replace function public.cold_rows(p_tbl text, p_day date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare r jsonb; a timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo'); b timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  case p_tbl
    when 'airport_tracks_all' then select jsonb_agg(to_jsonb(x)) into r from public.airport_tracks_all x where day = p_day;
    when 'flight_tracks' then select jsonb_agg(to_jsonb(x) || jsonb_build_object('arr', h.arr)) into r from public.flight_tracks x left join public.flight_history h on h.svc_date = x.svc_date and h.flight = x.flight and h.dep = x.dep where x.svc_date = p_day;
    when 'flight_history' then select jsonb_agg(to_jsonb(x)) into r from public.flight_history x where svc_date = p_day;
    when 'reg_legs' then select jsonb_agg(to_jsonb(x)) into r from public.reg_legs x where day = p_day;
    when 'rotation_obs' then select jsonb_agg(to_jsonb(x)) into r from public.rotation_obs x where svc_date = p_day;
    when 'rwy_samples' then select jsonb_agg(to_jsonb(x)) into r from public.rwy_samples x where at >= a and at < b;
    when 'ops_log' then select jsonb_agg(to_jsonb(x)) into r from public.ops_log x where at >= a and at < b;
    when 'ga_events' then select jsonb_agg(to_jsonb(x)) into r from public.ga_events x where at >= a and at < b;
    else raise exception 'bad table';
  end case;
  return coalesce(r, '[]'::jsonb);
end $$;
revoke all on function public.cold_rows(text, date) from public, anon, authenticated;

-- 移し終えた日を控えて、データベースから消す（運営だけ。控えの行数と、いまの行数が同じときだけ消す）
create or replace function public.cold_done(p_tbl text, p_day date, p_path text, p_rows int, p_bytes int) returns int
language plpgsql security definer set search_path = public as $$
declare n int; a timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo'); b timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  if p_day >= (now() at time zone 'Asia/Tokyo')::date - 30 then raise exception 'too new'; end if;
  n := jsonb_array_length(public.cold_rows(p_tbl, p_day));
  if n <> p_rows then raise exception 'row count changed (% <> %)', n, p_rows; end if;
  insert into public.cold_days (tbl, day, path, rows, bytes) values (p_tbl, p_day, p_path, p_rows, p_bytes)
  on conflict (tbl, day) do update set path = excluded.path, rows = excluded.rows, bytes = excluded.bytes, moved_at = now();
  case p_tbl
    when 'airport_tracks_all' then delete from public.airport_tracks_all where day = p_day;
    when 'flight_tracks' then delete from public.flight_tracks where svc_date = p_day;
    when 'flight_history' then delete from public.flight_history where svc_date = p_day;
    when 'reg_legs' then delete from public.reg_legs where day = p_day;
    when 'rotation_obs' then delete from public.rotation_obs where svc_date = p_day;
    when 'rwy_samples' then delete from public.rwy_samples where at >= a and at < b;
    when 'ops_log' then delete from public.ops_log where at >= a and at < b;
    when 'ga_events' then delete from public.ga_events where at >= a and at < b;
  end case;
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.cold_done(text, date, text, int, int) from public, anon, authenticated;

-- 移した日の一覧（だれでも：どの日まで空の道すじがファイル置き場にあるか）
create or replace function public.cold_days_list(p_tbl text) returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_build_object('first', min(day), 'last', max(day), 'n', count(*)), '{}'::jsonb) from public.cold_days where tbl = p_tbl
$$;
revoke all on function public.cold_days_list(text) from public;
grant execute on function public.cold_days_list(text) to anon, authenticated;

-- 非公開のファイル置き場（Supabase の Storage があるときだけ）
do $outer$
begin
  if exists (select 1 from information_schema.tables where table_schema = 'storage' and table_name = 'buckets') then
    execute $q$ insert into storage.buckets (id, name, public) values ('cold', 'cold', false) on conflict (id) do nothing $q$;
  end if;
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 毎晩（日本時間 6:10）、少しずつ移す
  execute $q$ select cron.schedule('cold-archive', '10 21 * * *', $job$
    select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/cold-archive', headers := '{"User-Agent": "soramemo (cold-archive)"}'::jsonb, timeout_milliseconds := 150000)
  $job$) $q$;
end
$outer$;
