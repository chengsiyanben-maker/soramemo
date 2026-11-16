-- 定期の手入れ 11/10（データ担当）：毎晩・3時間ごとの記録の処理を軽くする。表・列・索引・RLS・権限は変えない
--   1. archive_airport_daily（daily-archive が毎晩2日分呼ぶ）：運用の記録（ops_log）を「日本時間の日付に直して比べる」形で
--      読んでいたので、索引が使えず90日分を丸ごと読んでいた → その日の0時〜24時（日本時間）の範囲で引く（索引 ops_log_at）。
--      日本時間には夏時間がないので、選ばれる行は前とまったく同じ
--   2. airport_tracks_put（rwy-learn が3時間ごとに何十回も呼ぶ）：呼ぶたびに一時の表を作って消していた（システムの表が汚れる）
--      → 一時の表を使わず、1つの文で消して入れる。前後90分の食い違う線を消す決まりと、入れたあとの中身は前と同じ
--      （同じ機体・同じ空港・同じ日・同じ時刻で出発・到着だけ違う線は、前は「消して入れる」、今度は「上書き」。残る行は同じ）
--   3. rwy_learn_points（rwy-learn が3時間ごとに8つ同時に呼ぶ）：航跡の点を jsonb でなく json で組み立てる（作業のメモリが小さい）。
--      返す型 jsonb → json（作り直し）。中身の値・並びは同じ。受け取る rwy-learn は JSON として読むだけなので変えない

-- 1
create or replace function public.archive_airport_daily(p_day date) returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  delete from public.airport_daily where day = p_day;
  with u as (
    select arr as iata, 'arr' as dir, case when ata_src = 'odpt' then arr_delay end as d, cancelled, diverted_to is not null as div
    from public.flight_history where svc_date = p_day
    union all
    select dep, 'dep', case when atd_src = 'odpt' then dep_delay end, cancelled, false from public.flight_history where svc_date = p_day
  ), o as (
    select iata, jsonb_object_agg(mode, cnt * 5) as modes, max(wmax) as max_wind from (
      select iata, coalesce(obs_mode, est_mode) as mode, count(*) as cnt, max(wspd) as wmax
      from public.ops_log
      where at >= (p_day::timestamp at time zone 'Asia/Tokyo') and at < ((p_day + 1)::timestamp at time zone 'Asia/Tokyo')
      group by 1, 2) x group by iata
  )
  insert into public.airport_daily (day, iata, flights, arr, dep, late, cancelled, diverted, avg_delay, modes, max_wind)
  select p_day, u.iata, count(*), count(*) filter (where dir = 'arr'), count(*) filter (where dir = 'dep'),
         count(*) filter (where not cancelled and d >= 15), count(*) filter (where cancelled), count(*) filter (where div),
         round(avg(d) filter (where not cancelled and d >= 15), 1), o.modes, o.max_wind
  from u left join o on o.iata = u.iata
  group by u.iata, o.modes, o.max_wind;
  get diagnostics n = row_count;
  return n;
end
$$;
revoke all on function public.archive_airport_daily(date) from public, anon, authenticated;

-- 2
create or replace function public.airport_tracks_put(p_rows jsonb) returns int
language sql security definer set search_path = public as $$
  with r as (
    select x.iata, x.day, x.callsign, x.at, x.dep_here, x.pts
    from jsonb_to_recordset(p_rows) as x(iata text, day date, callsign text, at timestamptz, dep_here smallint, pts text)
    where x.iata ~ '^[A-Z]{3}$' and x.callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and x.at is not null and x.dep_here in (0, 1) and length(x.pts) <= 4000
  ), g as (
    -- 同じ機体・同じ空港・同じ日に入れる線の時刻をまとめて持つ（ふつうは1〜2個。行どうしを総当たりで比べないため）
    select iata, day, callsign, at, array_agg(at) over (partition by iata, day, callsign) as ats from r
  ), d as (
    -- 入れる線の前後90分にある、同じ機体・同じ空港・同じ日の線のうち、入れる線のどれとも時刻が合わないもの
    delete from public.airport_tracks_all a using g
    where a.iata = g.iata and a.callsign = g.callsign and a.day = g.day
      and a.at between g.at - interval '90 minutes' and g.at + interval '90 minutes'
      and a.at <> all (g.ats)
  ), i as (
    insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) select iata, day, callsign, at, dep_here, pts from r
    on conflict (iata, day, callsign, at) do update set dep_here = excluded.dep_here, pts = excluded.pts
    returning 1
  )
  select count(*)::int from i
$$;
revoke all on function public.airport_tracks_put(jsonb) from public, anon, authenticated;

-- 3
drop function if exists public.rwy_learn_points(timestamptz, timestamptz, int, int);
create function public.rwy_learn_points(p_from timestamptz, p_to timestamptz, p_part int, p_parts int) returns json
language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(json_build_object('cs', callsign, 'p', pts)), '[]'::json) from (
    select callsign, json_agg(json_build_array(extract(epoch from t)::bigint, lat, lon, alt) order by t) as pts
    from public.track_points
    where t >= p_from and t < p_to and callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and abs(hashtext(callsign)) % greatest(p_parts, 1) = p_part
    group by callsign
  ) q
$$;
revoke all on function public.rwy_learn_points(timestamptz, timestamptz, int, int) from public, anon, authenticated;
