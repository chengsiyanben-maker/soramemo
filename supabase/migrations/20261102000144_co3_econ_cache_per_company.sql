-- エアライン経営 co-v3：重い計算の使い回し（000142）を、会社ごとに覚えるようにする
--   000142 は「最後に計算した会社」1社ぶんだけを覚えていた。出資・共同運航があると、1回の表示の中で自分と相手の会社の計算を
--   交互に呼ぶので、覚えた結果が毎回入れ替わって使い回せず、co_state が約7秒→約50秒になっていた（試遊版で測った）。
--   覚える場所の名前に会社（利用者の番号）を入れる。中身の計算と数字は変えない。表は変えない（RLS もそのまま）

do $do$
declare fn text; res text; cols text; sp text;
begin
  foreach fn in array array['co3_route_econ', 'co3_seen_flights', 'co3_cargo_routes'] loop
    if to_regprocedure(format('public.%s_calc(uuid)', fn)) is null then raise exception '% の計算（_calc）がない', fn; end if;
    select pg_get_function_result(format('public.%s_calc(uuid)', fn)::regprocedure),
           coalesce((select array_to_string(p.proconfig, ',') from pg_proc p where p.oid = format('public.%s_calc(uuid)', fn)::regprocedure), 'search_path=public')
      into res, sp;
    cols := substring(res from '^TABLE\((.*)\)$');
    if cols is null then raise exception '% の形が違う: %', fn, res; end if;
    execute format($f$
create or replace function public.%1$I(p_uid uuid) returns %2$s
language plpgsql stable security definer set search_path = %3$s as $b$
declare
  nm text := %4$L || replace(coalesce(p_uid::text, 'none'), '-', '');
  k text := pg_backend_pid() || '|' || now()::text || '|' || coalesce(current_setting('co3.season_day', true), '') || '|' || co3.xact_writes();
  c text := current_setting(nm, true);
  j jsonb;
begin
  if c is not null and c <> '' and split_part(c, chr(1), 1) = k then
    j := split_part(c, chr(1), 2)::jsonb;
  else
    select coalesce(jsonb_agg(to_jsonb(t) order by t.ordinality), '[]'::jsonb) into j from public.%5$I(p_uid) with ordinality t;
    perform set_config(nm, k || chr(1) || j::text, true);
  end if;
  return query select * from jsonb_to_recordset(j) as x(%6$s);
end;
$b$$f$, fn, res, replace(sp, 'search_path=', ''), 'co3.c_' || fn || '_', fn || '_calc', cols);
    execute format('revoke all on function public.%I(uuid) from public, anon, authenticated', fn);
  end loop;
end
$do$;
