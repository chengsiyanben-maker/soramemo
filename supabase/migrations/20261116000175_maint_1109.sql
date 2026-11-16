-- 定期の手入れ 11/9：古い記録をファイル置き場へ移す処理（cold-archive）を軽く・安全にする。表・索引・RLS・権限は変えない
--   1. cold_done：移した行数を確かめるのに、その日の記録を丸ごと JSON に作り直していた（cold_rows を2回目に呼ぶ）→ 数えるだけにする
--      さらに、消した行数が控えの行数と違えばエラーにして取り消す（数えてから消すまでの間に行が足されても、置き場にない行は消さない）
--   2. cold_rows：その日の記録を jsonb で組み立てていた → json で組み立てる（中身・並びの決まりは同じ。作る時間と作業メモリが減る）
--      返す型が jsonb → json に変わるので、作り直す。呼ぶのは cold-archive（運営の鍵）だけで、受け取る形（行の配列）は同じ
--   チェックイン・経営への影響：なし（どちらも cold_rows・cold_done を使わない）。全機の航跡と機体の記録は今までどおり、置き場に置けたことを確かめてから移す

drop function if exists public.cold_rows(text, date);
create function public.cold_rows(p_tbl text, p_day date) returns json
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
    else raise exception 'bad table';
  end case;
  return coalesce(r, '[]'::json);
end $$;
revoke all on function public.cold_rows(text, date) from public, anon, authenticated;

-- その日の行数（運営だけ・cold_done の中で使う）
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
    else raise exception 'bad table';
  end case;
  return n;
end $$;
revoke all on function public.cold_count(text, date) from public, anon, authenticated;

create or replace function public.cold_done(p_tbl text, p_day date, p_path text, p_rows int, p_bytes int) returns int
language plpgsql security definer set search_path = public as $$
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
  end case;
  get diagnostics n = row_count;
  -- 数えたあとに行が足されていたら、置き場にない行まで消すことになるので、全部取り消す（控えの行も戻る）
  if n <> p_rows then raise exception 'row count changed while deleting (% <> %)', n, p_rows; end if;
  return n;
end $$;
revoke all on function public.cold_done(text, date, text, int, int) from public, anon, authenticated;
