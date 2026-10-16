-- 門限チャレンジ：運用時間の終わり（門限）がある空港（伊丹21時・福岡22時。AIP JAPAN AD 2.3）で、門限の前後に着く・出る便を返す。
-- 時刻は予定の便（flight_schedule）と、航空会社の運航情報（odpt-status が入れる変更後・実際の時刻）。間に合うかどうかの判定は画面でする
create or replace function public.curfew_flights(p_iata text) returns jsonb
language sql stable security definer set search_path = public as $$
  with c as (
    select p_iata as iata,
      -- 今日（日本時間。0時〜5時は前の日）の門限
      ((((now() at time zone 'Asia/Tokyo') - interval '5 hours')::date + make_interval(hours => h)) at time zone 'Asia/Tokyo') as close_at
    from (select case p_iata when 'ITM' then 21 when 'FUK' then 22 end as h) x where h is not null
  )
  select jsonb_build_object('iata', c.iata, 'close_at', c.close_at, 'flights', coalesce((
    select jsonb_agg(f order by f->>'t') from (
      select jsonb_build_object('dir', 'arr', 'flight', s.flight, 'other', s.dep, 'sched', s.sta, 'est', s.eta, 'actual', s.ata,
               'status', s.arr_status, 'cancelled', coalesce(s.arr_status ~* 'cancel' or s.dep_status ~* 'cancel', false),
               'dep_actual', s.atd, 'source', s.source, 't', coalesce(s.ata, s.eta, s.sta)) f
      from public.flight_schedule s
      where s.arr = c.iata and coalesce(s.ata, s.eta, s.sta) between c.close_at - interval '90 minutes' and c.close_at + interval '90 minutes'
        and s.sta between c.close_at - interval '6 hours' and c.close_at + interval '30 minutes'
      union all
      select jsonb_build_object('dir', 'dep', 'flight', s.flight, 'other', s.arr, 'sched', s.std, 'est', s.etd, 'actual', s.atd,
               'status', s.dep_status, 'cancelled', coalesce(s.dep_status ~* 'cancel', false),
               'dep_actual', s.atd, 'source', s.source, 't', coalesce(s.atd, s.etd, s.std))
      from public.flight_schedule s
      where s.dep = c.iata and coalesce(s.atd, s.etd, s.std) between c.close_at - interval '90 minutes' and c.close_at + interval '90 minutes'
        and s.std between c.close_at - interval '6 hours' and c.close_at + interval '30 minutes'
      limit 60
    ) q), '[]'::jsonb))
  from c
$$;
revoke all on function public.curfew_flights(text) from public;
grant execute on function public.curfew_flights(text) to anon, authenticated;
