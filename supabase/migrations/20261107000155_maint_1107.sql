-- 定期の手入れ（11/7）：古い記録をファイル置き場へ移す日の候補（cold_candidates）を、一時ファイルを使わない形にする
--   前の作りは、表ごとに 400日より前の行をすべて読んで日ごとにまとめ（group by）、合わせて並べ替えていた。
--   400日より前の行が多いと、まとめる並べ替えが作業メモリに入りきらず一時ファイルを使う（本番は一時ファイルの余裕がない）。
--   新しい作りは、表ごとに「古い方から次の日」を索引で1件ずつ引く（最大 p_limit 日）。読む行は日の数だけで、並べ替えは最大 8表×40日。
--   結果（どの表のどの日を、どの順で返すか）は前と同じ。表・列・索引・RLS・権限は変えない。チェックイン・経営のどちらにも影響しない。
--   使う索引（どれも今ある btree）：
--     flight_tracks・flight_history・rotation_obs は主キーの先頭（svc_date）／reg_legs は reg_legs_day／ops_log は ops_log_at
--     airport_tracks_all は主キー (iata, day, …)、ga_events は ga_events_iata_at (iata, at desc)、rwy_samples は rwy_samples_src_at (src, at)
--     → この3つは「空港（または取り先）ごと」に次の日を引いて合わせる（空港や取り先の一覧も索引で1件ずつ引く）

-- 表ごとの、p_before より前の日を古い順に最大 p_n 日（運営だけ）
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
    else raise exception 'bad table';
  end case;
  return;
end $$;
revoke all on function public.cold_days_of(text, date, int) from public, anon, authenticated;

-- 移す日の候補（運営だけ）：表ごとに、p_before より前で、まだ移していない日を古い順に（前と同じ結果・同じ引数と形）
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
    ) x
  ) t
  -- 航跡は、同じ日の便の実績（出発・到着の空港）と一緒に読むので、便の実績より先に移す
  -- （同じ日・同じ順位の表どうしは、前は決まっていなかったので、表の名前の順にそろえる）
  order by t.day, case t.tbl when 'flight_tracks' then 0 when 'flight_history' then 2 else 1 end, t.tbl
  limit (select n from n)
$$;
revoke all on function public.cold_candidates(date, int) from public, anon, authenticated;
