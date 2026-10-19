-- 乗る便を出発から到着まで追う（flight-live から使う）：便名（0を取ってくらべる）と、わかれば出発空港から、
-- 今から20時間前〜30時間後に出る便のうち、いちばん近いものを返す（航空会社の運航情報の見込み・実際の時刻と欠航も）
create or replace function public.live_flight_sched(p_flight text, p_dep text) returns jsonb
language sql stable security definer set search_path = public as $$
  select to_jsonb(q) from (
    select f.flight, f.dep, f.arr, f.std, f.sta, f.etd, f.eta, f.atd, f.ata, f.aircraft,
           coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false) as cancelled
    from public.flight_schedule f
    where p_flight ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$' and public.flight_no_norm(f.flight) = public.flight_no_norm(p_flight)
      and (p_dep is null or f.dep = p_dep)
      and f.std between now() - interval '20 hours' and now() + interval '30 hours'
    order by abs(extract(epoch from (f.std - now()))) limit 1
  ) q
$$;
revoke all on function public.live_flight_sched(text, text) from public, anon, authenticated;
