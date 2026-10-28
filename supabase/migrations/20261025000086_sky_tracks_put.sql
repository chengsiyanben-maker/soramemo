-- 空の道すじの線を入れる（rwy-learn から・service_role だけ）。
--   同じ機体（呼び出し符号）・同じ空港・同じ日で、入れる線の前後90分にある線のうち、時刻か出発・到着が食い違うものを消してから入れる。
--   判定を直したあとに位置の記録を読み直すと、古い判定の線が入れ替わる。何度読んでも結果は同じ。位置の記録から作り直せる線だけが入れ替わる
create or replace function public.airport_tracks_put(p_rows jsonb) returns int
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  create temp table if not exists _atp (iata text, day date, callsign text, at timestamptz, dep_here smallint, pts text) on commit drop;
  truncate _atp;
  insert into _atp select x.iata, x.day, x.callsign, x.at, x.dep_here, x.pts
    from jsonb_to_recordset(p_rows) as x(iata text, day date, callsign text, at timestamptz, dep_here smallint, pts text)
    where x.iata ~ '^[A-Z]{3}$' and x.callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and x.at is not null and x.dep_here in (0, 1) and length(x.pts) <= 4000;
  delete from public.airport_tracks_all a using _atp r
    where a.iata = r.iata and a.callsign = r.callsign and a.day = r.day
      and a.at between r.at - interval '90 minutes' and r.at + interval '90 minutes'
      and not exists (select 1 from _atp q where q.iata = a.iata and q.callsign = a.callsign and q.day = a.day and q.at = a.at and q.dep_here = a.dep_here);
  insert into public.airport_tracks_all (iata, day, callsign, at, dep_here, pts) select iata, day, callsign, at, dep_here, pts from _atp
    on conflict (iata, day, callsign, at) do update set dep_here = excluded.dep_here, pts = excluded.pts;
  get diagnostics n = row_count;
  return n;
end
$$;
revoke all on function public.airport_tracks_put(jsonb) from public, anon, authenticated;
