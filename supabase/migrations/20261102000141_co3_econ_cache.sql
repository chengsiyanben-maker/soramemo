-- エアライン経営 co-v3：重い計算を、1回の処理（トランザクション）の中で使い回す
--   会社の状態（co_state）を1回出すあいだに、同じ計算が何度も呼ばれていた
--   （路線ごとの稼ぎ co3_route_econ が17回、見た機体 co3_seen_flights と貨物の路線 co3_cargo_routes が9回ずつ。収益・会社の価値・借りられる額・出資などがそれぞれ呼ぶ）。
--   試遊版（ブラウザの中のデータベース）で測ると、路線10本・機体1機で co_state に約25秒かかっていた。計算の中身と数字は変えない。
--   ・同じ処理の中で、ゲームの表がどれも書き換わっていなければ、前に出した結果を返す
--     （書き換わったかは、その処理の中で増えた・変わった・消えた行の数で見る。1行でも変われば計算し直す）
--   ・処理が終われば覚えた結果は消える（set_config の第3引数 true）。ほかの人の処理とは混ざらない
--   ・もとの計算は「名前_calc」に名前を変えて残す（例：co3_route_econ_calc）。これからの直しは _calc のほうに入れる
--   表は変えない（RLS もそのまま）

create or replace function co3.xact_writes() returns bigint
language sql stable set search_path = pg_catalog as $$
  select coalesce(sum(pg_stat_get_xact_tuples_inserted(c.oid) + pg_stat_get_xact_tuples_updated(c.oid) + pg_stat_get_xact_tuples_deleted(c.oid)), 0)::bigint
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where c.relkind = 'r' and n.nspname in ('public', 'ops')
$$;
revoke all on function co3.xact_writes() from public, anon, authenticated;

do $do$
declare fn text; res text; cols text; sp text;
begin
  foreach fn in array array['co3_route_econ', 'co3_seen_flights', 'co3_cargo_routes'] loop
    if to_regprocedure(format('public.%s_calc(uuid)', fn)) is null then
      execute format('alter function public.%I(uuid) rename to %I', fn, fn || '_calc');
    end if;
    select pg_get_function_result(format('public.%s_calc(uuid)', fn)::regprocedure),
           coalesce((select array_to_string(p.proconfig, ',') from pg_proc p where p.oid = format('public.%s_calc(uuid)', fn)::regprocedure), 'search_path=public')
      into res, sp;
    cols := substring(res from '^TABLE\((.*)\)$');
    if cols is null then raise exception '% の形が違う: %', fn, res; end if;
    execute format($f$
create or replace function public.%1$I(p_uid uuid) returns %2$s
language plpgsql stable security definer set search_path = %3$s as $b$
declare
  k text := p_uid::text || '|' || pg_backend_pid() || '|' || now()::text || '|' || coalesce(current_setting('co3.season_day', true), '') || '|' || co3.xact_writes();
  c text := current_setting(%4$L, true);
  j jsonb;
begin
  if c is not null and c <> '' and split_part(c, chr(1), 1) = k then
    j := split_part(c, chr(1), 2)::jsonb;
  else
    select coalesce(jsonb_agg(to_jsonb(t) order by t.ordinality), '[]'::jsonb) into j from public.%5$I(p_uid) with ordinality t;
    perform set_config(%4$L, k || chr(1) || j::text, true);
  end if;
  return query select * from jsonb_to_recordset(j) as x(%6$s);
end;
$b$$f$, fn, res, replace(sp, 'search_path=', ''), 'co3.cache_' || fn, fn || '_calc', cols);
    execute format('revoke all on function public.%I(uuid) from public, anon, authenticated', fn);
    execute format('revoke all on function public.%I(uuid) from public, anon, authenticated', fn || '_calc');
  end loop;
end
$do$;

-- 混雑空港の申し込みの合計（co3_slot_totals）も同じように使い回す（路線ごと・便数の案ごとに呼ばれ、1回の表示で300回を超えていた）
do $do$
declare res text; cols text; sp text;
begin
  if to_regprocedure('public.co3_slot_totals_calc()') is null then
    execute 'alter function public.co3_slot_totals() rename to co3_slot_totals_calc';
  end if;
  select pg_get_function_result('public.co3_slot_totals_calc()'::regprocedure),
         coalesce((select array_to_string(p.proconfig, ',') from pg_proc p where p.oid = 'public.co3_slot_totals_calc()'::regprocedure), 'search_path=public')
    into res, sp;
  cols := substring(res from '^TABLE\((.*)\)$');
  if cols is null then raise exception 'co3_slot_totals の形が違う: %', res; end if;
  execute format($f$
create or replace function public.co3_slot_totals() returns %1$s
language plpgsql stable security definer set search_path = %2$s as $b$
declare
  k text := pg_backend_pid() || '|' || now()::text || '|' || coalesce(current_setting('co3.season_day', true), '') || '|' || co3.xact_writes();
  c text := current_setting('co3.cache_slot_totals', true);
  j jsonb;
begin
  if c is not null and c <> '' and split_part(c, chr(1), 1) = k then
    j := split_part(c, chr(1), 2)::jsonb;
  else
    select coalesce(jsonb_agg(to_jsonb(t) order by t.ordinality), '[]'::jsonb) into j from public.co3_slot_totals_calc() with ordinality t;
    perform set_config('co3.cache_slot_totals', k || chr(1) || j::text, true);
  end if;
  return query select * from jsonb_to_recordset(j) as x(%3$s);
end;
$b$$f$, res, replace(sp, 'search_path=', ''), cols);
  execute 'revoke all on function public.co3_slot_totals() from public, anon, authenticated';
  execute 'revoke all on function public.co3_slot_totals_calc() from public, anon, authenticated';
end
$do$;
