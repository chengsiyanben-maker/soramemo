-- 海外の会社の便の実績（foreign_legs）の180日より前を、ファイル置き場（cold-archive）へ移す（11/16 PM の指示・本人「おすすめ」）
--   foreign_legs は1年で約140MB の見込み。ほかの表と同じ仕組み（cold-archive が毎晩、日ごとに gzip の JSON を非公開の置き場に置き、
--   置けたことと行数を確かめてから表から外す）で、180日より前の日を移す。記録は消さない（置き場のファイルから読める）。
--   ほかの表は今までどおり p_before（400日）。foreign_late・foreign_usual が読むのは前の8週だけなので、画面には影響しない
--   直す関数：cold_days_of・cold_candidates（174 の形に foreign_legs を足す）、cold_rows・cold_count・cold_done（175 の形に足す）。
--   cold_done は 178 で付けた lock_timeout 5s を作り直しても残るように、定義に書いた。表は cold_days の tbl の決まりに foreign_legs を足すだけ。RLS・権限は変えない
--   反映の順：data/redo-1116（173〜180）のあと。影響：チェックイン・経営とも、なし
set lock_timeout = '10s';

-- 控えの表 cold_days に foreign_legs を足せるようにする（tbl の決まりの一覧に足す。行は書き換えない）
do $$
declare c text;
begin
  for c in select conname from pg_constraint where conrelid = 'public.cold_days'::regclass and contype = 'c' and pg_get_constraintdef(oid) like '%airport_tracks_all%' loop
    execute format('alter table public.cold_days drop constraint %I', c);
  end loop;
end $$;
alter table public.cold_days add constraint cold_days_tbl_check
  check (tbl in ('airport_tracks_all', 'flight_tracks', 'flight_history', 'reg_legs', 'rwy_samples', 'ops_log', 'ga_events', 'rotation_obs', 'foreign_legs'));

create or replace function public.cold_days_of(p_tbl text, p_before date, p_n int) returns setof date
language plpgsql stable security definer set search_path = public as $$
declare
  d date; k text; x timestamptz; i int;
  lim timestamptz := (p_before::timestamp at time zone 'Asia/Tokyo');
  n int := greatest(1, least(coalesce(p_n, 6), 40));
begin
  case p_tbl
    when 'flight_tracks' then
      i := 0; d := (select min(svc_date) from public.flight_tracks where svc_date < p_before);
      while d is not null and i < n loop
        return next d; i := i + 1;
        d := (select min(svc_date) from public.flight_tracks where svc_date > d and svc_date < p_before);
      end loop;
    when 'flight_history' then
      i := 0; d := (select min(svc_date) from public.flight_history where svc_date < p_before);
      while d is not null and i < n loop
        return next d; i := i + 1;
        d := (select min(svc_date) from public.flight_history where svc_date > d and svc_date < p_before);
      end loop;
    when 'rotation_obs' then
      i := 0; d := (select min(svc_date) from public.rotation_obs where svc_date < p_before);
      while d is not null and i < n loop
        return next d; i := i + 1;
        d := (select min(svc_date) from public.rotation_obs where svc_date > d and svc_date < p_before);
      end loop;
    when 'reg_legs' then
      i := 0; d := (select min(day) from public.reg_legs where day < p_before);
      while d is not null and i < n loop
        return next d; i := i + 1;
        d := (select min(day) from public.reg_legs where day > d and day < p_before);
      end loop;
    when 'ops_log' then
      i := 0; x := (select min(at) from public.ops_log where at < lim);
      while x is not null and i < n loop
        d := (x at time zone 'Asia/Tokyo')::date; return next d; i := i + 1;
        x := (select min(at) from public.ops_log where at >= ((d + 1)::timestamp at time zone 'Asia/Tokyo') and at < lim);
      end loop;
    when 'airport_tracks_all' then
      -- 空港ごとに最大 n 日（同じ日が空港をまたいで出るので、呼ぶ側で重ねを除く）
      k := (select min(iata) from public.airport_tracks_all);
      while k is not null loop
        i := 0; d := (select min(day) from public.airport_tracks_all where iata = k and day < p_before);
        while d is not null and i < n loop
          return next d; i := i + 1;
          d := (select min(day) from public.airport_tracks_all where iata = k and day > d and day < p_before);
        end loop;
        k := (select min(iata) from public.airport_tracks_all where iata > k);
      end loop;
    when 'ga_events' then
      k := (select min(iata) from public.ga_events);
      while k is not null loop
        i := 0; x := (select min(at) from public.ga_events where iata = k and at < lim);
        while x is not null and i < n loop
          d := (x at time zone 'Asia/Tokyo')::date; return next d; i := i + 1;
          x := (select min(at) from public.ga_events where iata = k and at >= ((d + 1)::timestamp at time zone 'Asia/Tokyo') and at < lim);
        end loop;
        k := (select min(iata) from public.ga_events where iata > k);
      end loop;
    when 'rwy_samples' then
      k := (select min(src) from public.rwy_samples);
      while k is not null loop
        i := 0; x := (select min(at) from public.rwy_samples where src = k and at < lim);
        while x is not null and i < n loop
          d := (x at time zone 'Asia/Tokyo')::date; return next d; i := i + 1;
          x := (select min(at) from public.rwy_samples where src = k and at >= ((d + 1)::timestamp at time zone 'Asia/Tokyo') and at < lim);
        end loop;
        k := (select min(src) from public.rwy_samples where src > k);
      end loop;
    when 'foreign_legs' then
      i := 0; d := (select min(day) from public.foreign_legs where day < p_before);
      while d is not null and i < n loop
        return next d; i := i + 1;
        d := (select min(day) from public.foreign_legs where day > d and day < p_before);
      end loop;
    else raise exception 'bad table';
  end case;
  return;
end $$;
revoke all on function public.cold_days_of(text, date, int) from public, anon, authenticated;

create or replace function public.cold_candidates(p_before date, p_limit int default 6) returns table (tbl text, day date)
language sql stable security definer set search_path = public as $$
  with n as (select greatest(1, least(coalesce(p_limit, 6), 40)) as n)
  select t.tbl, t.day from (
    select distinct x.tbl, x.day from (
                select 'airport_tracks_all'::text as tbl, d as day from n, public.cold_days_of('airport_tracks_all', p_before, n.n) d
      union all select 'flight_tracks', d from n, public.cold_days_of('flight_tracks', p_before, n.n) d
      union all select 'flight_history', d from n, public.cold_days_of('flight_history', p_before, n.n) d
      union all select 'reg_legs', d from n, public.cold_days_of('reg_legs', p_before, n.n) d
      union all select 'rotation_obs', d from n, public.cold_days_of('rotation_obs', p_before, n.n) d
      union all select 'rwy_samples', d from n, public.cold_days_of('rwy_samples', p_before, n.n) d
      union all select 'ops_log', d from n, public.cold_days_of('ops_log', p_before, n.n) d
      union all select 'ga_events', d from n, public.cold_days_of('ga_events', p_before, n.n) d
      -- 海外の会社の便の実績は180日より前から移す（11/16 本人。ほかの表の p_before より早い。消さずに置き場に移す）
      union all select 'foreign_legs', d from n, public.cold_days_of('foreign_legs', greatest(p_before, (now() at time zone 'Asia/Tokyo')::date - 180), n.n) d
    ) x
  ) t
  -- 航跡は、同じ日の便の実績（出発・到着の空港）と一緒に読むので、便の実績より先に移す
  -- （同じ日・同じ順位の表どうしは、前は決まっていなかったので、表の名前の順にそろえる）
  order by t.day, case t.tbl when 'flight_tracks' then 0 when 'flight_history' then 2 else 1 end, t.tbl
  limit (select n from n)
$$;
revoke all on function public.cold_candidates(date, int) from public, anon, authenticated;

create or replace function public.cold_rows(p_tbl text, p_day date) returns json
language plpgsql stable security definer set search_path = public as $$
declare r json; a timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo'); b timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  case p_tbl
    when 'airport_tracks_all' then select json_agg(x) into r from public.airport_tracks_all x where day = p_day;
    when 'flight_tracks' then select json_agg(to_jsonb(x) || jsonb_build_object('arr', h.arr)) into r from public.flight_tracks x left join public.flight_history h on h.svc_date = x.svc_date and h.flight = x.flight and h.dep = x.dep where x.svc_date = p_day;
    when 'flight_history' then select json_agg(x) into r from public.flight_history x where svc_date = p_day;
    when 'reg_legs' then select json_agg(x) into r from public.reg_legs x where day = p_day;
    when 'rotation_obs' then select json_agg(x) into r from public.rotation_obs x where svc_date = p_day;
    when 'rwy_samples' then select json_agg(x) into r from public.rwy_samples x where at >= a and at < b;
    when 'ops_log' then select json_agg(x) into r from public.ops_log x where at >= a and at < b;
    when 'ga_events' then select json_agg(x) into r from public.ga_events x where at >= a and at < b;
    when 'foreign_legs' then select json_agg(x) into r from public.foreign_legs x where day = p_day;
    else raise exception 'bad table';
  end case;
  return coalesce(r, '[]'::json);
end $$;
revoke all on function public.cold_rows(text, date) from public, anon, authenticated;

create or replace function public.cold_count(p_tbl text, p_day date) returns int
language plpgsql stable security definer set search_path = public as $$
declare n int; a timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo'); b timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  case p_tbl
    when 'airport_tracks_all' then select count(*) into n from public.airport_tracks_all where day = p_day;
    when 'flight_tracks' then select count(*) into n from public.flight_tracks where svc_date = p_day;
    when 'flight_history' then select count(*) into n from public.flight_history where svc_date = p_day;
    when 'reg_legs' then select count(*) into n from public.reg_legs where day = p_day;
    when 'rotation_obs' then select count(*) into n from public.rotation_obs where svc_date = p_day;
    when 'rwy_samples' then select count(*) into n from public.rwy_samples where at >= a and at < b;
    when 'ops_log' then select count(*) into n from public.ops_log where at >= a and at < b;
    when 'ga_events' then select count(*) into n from public.ga_events where at >= a and at < b;
    when 'foreign_legs' then select count(*) into n from public.foreign_legs where day = p_day;
    else raise exception 'bad table';
  end case;
  return n;
end $$;
revoke all on function public.cold_count(text, date) from public, anon, authenticated;

create or replace function public.cold_done(p_tbl text, p_day date, p_path text, p_rows int, p_bytes int) returns int
language plpgsql security definer set search_path = public set lock_timeout = '5s' as $$
declare n int; a timestamptz := (p_day::timestamp at time zone 'Asia/Tokyo'); b timestamptz := ((p_day + 1)::timestamp at time zone 'Asia/Tokyo');
begin
  if p_day >= (now() at time zone 'Asia/Tokyo')::date - 30 then raise exception 'too new'; end if;
  n := public.cold_count(p_tbl, p_day);
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
    when 'foreign_legs' then delete from public.foreign_legs where day = p_day;
    else raise exception 'bad table';
  end case;
  get diagnostics n = row_count;
  -- 数えたあとに行が足されていたら、置き場にない行まで消すことになるので、全部取り消す（控えの行も戻る）
  if n <> p_rows then raise exception 'row count changed while deleting (% <> %)', n, p_rows; end if;
  return n;
end $$;
revoke all on function public.cold_done(text, date, text, int, int) from public, anon, authenticated;
