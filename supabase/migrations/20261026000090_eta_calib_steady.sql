-- 到着予想の寄り道の補正を、ゆっくり直す形に変える（10/26）。
-- 前は「前に変えた後の記録が10便あれば、ずれの7割を直す」だったため、羽田・福岡などで日ごとの振れを追いかけて、
-- 次の日に逆向きにずれていた（羽田：この7日 −3.4分 → 補正 → この1日 −3.5分、福岡：−1.5分 → +5.9分）。
-- 地上走行（taxi）の決め方は今のまま。表と RLS は変えない。
create or replace function public.refresh_eta_calib() returns int
language plpgsql security definer set search_path = public as $$
declare r record; n int := 0; old record; nt real; ne real; ea timestamptz;
begin
  for r in
    with x as (
      select arr, ata_src as src, extract(epoch from (eta30 - ata)) / 60 as diff, ata
      from public.flight_history
      where svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and eta30 is not null and ata is not null and not cancelled and diverted_to is null
    )
    select arr,
      count(*) filter (where src = 'odpt') as no, percentile_cont(0.5) within group (order by diff) filter (where src = 'odpt') as mo,
      count(*) filter (where src = 'adsb') as na, percentile_cont(0.5) within group (order by diff) filter (where src = 'adsb') as ma
    from x group by arr
  loop
    select * into old from public.eta_calib where iata = r.arr;
    nt := old.taxi; ne := old.extra; ea := old.extra_at;
    if r.no >= 10 and r.na >= 10 then nt := greatest(0, least(20, round((r.ma - r.mo)::numeric, 1)));
    elsif r.no >= 10 and r.na < 10 then nt := greatest(0, least(20, round((-r.mo)::numeric, 1)));
    end if;
    -- 寄り道：前に変えた後の、機体の位置の記録だけで
    declare m real; c int; dd int;
    begin
      select percentile_cont(0.5) within group (order by extract(epoch from (eta30 - ata)) / 60), count(*), count(distinct svc_date) into m, c, dd
      from public.flight_history
      where arr = r.arr and ata_src = 'adsb' and eta30 is not null and ata is not null and not cancelled and diverted_to is null
        and svc_date >= (now() at time zone 'Asia/Tokyo')::date - 14 and (ea is null or ata > ea);
      -- 2日分・40便がそろってから、ずれの3割だけ（1回に2分まで）直す。日ごとの振れ（風向き・混み具合）を追いかけて行き過ぎないため
      if c >= 40 and dd >= 2 and abs(m) >= 0.5 then
        ne := greatest(0, least(15, round((coalesce(ne, 0) - greatest(-2, least(2, 0.3 * m)))::numeric, 1))); ea := now();
      end if;
    end;
    insert into public.eta_calib (iata, taxi, extra, n_odpt, n_adsb, extra_at, updated_at) values (r.arr, nt, ne, r.no, r.na, ea, now())
    on conflict (iata) do update set taxi = excluded.taxi, extra = excluded.extra, n_odpt = excluded.n_odpt, n_adsb = excluded.n_adsb, extra_at = excluded.extra_at, updated_at = now();
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.refresh_eta_calib() from public, anon, authenticated;

-- 日ごとの到着予想のずれ（機体の位置で着陸時刻が分かった便の中央値と便数だけ）。補正が落ち着いたかを見るため。個々の便は返さない
create or replace function public.eta_daily(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('day', d, 'n', n, 'median', med) order by d), '[]'::jsonb) from (
    select svc_date as d, count(*) as n, round((percentile_cont(0.5) within group (order by extract(epoch from (eta30 - ata)) / 60))::numeric, 1) as med
    from public.flight_history
    where arr = upper(p_iata) and ata_src = 'adsb' and eta30 is not null and ata is not null and not cancelled and diverted_to is null
      and svc_date >= (now() at time zone 'Asia/Tokyo')::date - least(greatest(p_days, 1), 60)
    group by svc_date having count(*) >= 3
  ) t
$$;
revoke all on function public.eta_daily(text, int) from public;
grant execute on function public.eta_daily(text, int) to anon, authenticated;
