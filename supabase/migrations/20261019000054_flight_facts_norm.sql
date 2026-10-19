-- 直す：毎日の記録の便名は時刻表のまま（NH059 のように0が付く）、利用者の便名は NH59 なので、一致せず実績が付かなかった。
-- 両方の0を取ってくらべる（航空会社の記号2文字のあとの先頭の0）
create or replace function public.flight_no_norm(t text) returns text
language sql immutable as $$ select regexp_replace(upper(t), '^([A-Z0-9]{2})0+(\d)', '\1\2') $$;

create or replace function public.flight_facts(p jsonb) returns jsonb
language sql stable security definer set search_path = public as $$
  with q as (
    select x ->> 'f' as f, public.flight_no_norm(x ->> 'f') as fn, (x ->> 'd')::date as d, x ->> 'a' as a
    from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) with ordinality as t(x, i)
    where i <= 300 and x ->> 'f' ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$' and x ->> 'd' ~ '^\d{4}-\d{2}-\d{2}$' and x ->> 'a' ~ '^[A-Z]{3}$'
  )
  select coalesce(jsonb_agg(jsonb_build_object('f', q.f, 'd', q.d, 'a', q.a,
           'atd', h.atd, 'ata', h.ata, 'atd_src', h.atd_src, 'ata_src', h.ata_src, 'dep_delay', h.dep_delay, 'arr_delay', h.arr_delay,
           'cancelled', h.cancelled, 'diverted_to', h.diverted_to, 'aircraft', h.aircraft, 'type', h.type, 'reg', h.reg)), '[]'::jsonb)
  from q
  join lateral (
    select * from public.flight_history h
    where h.svc_date = q.d and h.dep = q.a
      and (public.flight_no_norm(h.flight) = q.fn or exists (select 1 from unnest(h.also) o where public.flight_no_norm(o) = q.fn))
    order by (public.flight_no_norm(h.flight) = q.fn) desc limit 1
  ) h on true
$$;
revoke all on function public.flight_facts(jsonb) from public;
grant execute on function public.flight_facts(jsonb) to anon, authenticated;
