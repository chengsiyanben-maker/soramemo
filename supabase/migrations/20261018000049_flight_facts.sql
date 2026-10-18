-- パスポート用：利用者のフライト（便名・日付・出発空港）に、毎日の記録（実際の時刻・遅れ・機種・登録記号）を付ける。
-- 返すのは航空会社の公開の運航情報と機体の位置から作った便ごとの実績だけ（利用者の情報は受け取るだけで残さない）。1回300便まで
create or replace function public.flight_facts(p jsonb) returns jsonb
language sql stable security definer set search_path = public as $$
  with q as (
    select x ->> 'f' as f, (x ->> 'd')::date as d, x ->> 'a' as a
    from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) with ordinality as t(x, i)
    where i <= 300 and x ->> 'f' ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$' and x ->> 'd' ~ '^\d{4}-\d{2}-\d{2}$' and x ->> 'a' ~ '^[A-Z]{3}$'
  )
  select coalesce(jsonb_agg(jsonb_build_object('f', q.f, 'd', q.d, 'a', q.a,
           'atd', h.atd, 'ata', h.ata, 'atd_src', h.atd_src, 'ata_src', h.ata_src, 'dep_delay', h.dep_delay, 'arr_delay', h.arr_delay,
           'cancelled', h.cancelled, 'diverted_to', h.diverted_to, 'aircraft', h.aircraft, 'type', h.type, 'reg', h.reg)), '[]'::jsonb)
  from q
  join lateral (
    select * from public.flight_history h
    where h.svc_date = q.d and h.dep = q.a and (h.flight = q.f or q.f = any(h.also))
    order by (h.flight = q.f) desc limit 1
  ) h on true
$$;
revoke all on function public.flight_facts(jsonb) from public;
grant execute on function public.flight_facts(jsonb) to anon, authenticated;
