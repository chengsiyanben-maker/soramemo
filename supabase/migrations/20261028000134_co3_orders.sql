-- エアライン経営 co-v3：新しい機体の発注（仕様書「発注（格付け4から）」）
--   乗った（見た）機種のうち、今も作られている新しい世代（co3_types.gen = 'new'）の旅客機・貨物機だけ
--   値段は機種の表の1.3倍（持っている機体の数での値上がりもかかる。見ただけの機体を買うときと同じ数え方。貨物機も1.3倍）。払うのは発注したとき
--   納入まで 小型（プロペラ・リージョナル・小型ジェット）7日・中型14日・大型30日。納入された機体は古さなし・乗った回数の強さは0から
--   登録記号はゲーム用の「SM-」で始まる記号（SM- と英数字4文字。例 SM-A001。ゲーム全体で重ならない）。本物の登録記号とは関係がない
--   国際線には中型・大型の機体だけ入れられる（乗った記録がないので、機体の大きさで決める）
--   取り消しはできない（仕様書にないため）

create sequence if not exists public.co3_order_seq;
revoke all on sequence public.co3_order_seq from public, anon, authenticated;

create table if not exists public.co3_orders (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  code text not null references public.co3_types (code),
  reg text not null unique check (reg ~ '^SM-[A-Z][0-9]{3}$'),
  price bigint not null,
  ordered_at timestamptz not null default now(),
  deliver_on date not null,
  aircraft_id bigint references public.aircraft (id) on delete set null,
  delivered_at timestamptz
);
create index if not exists co3_orders_user on public.co3_orders (user_id, deliver_on);
alter table public.co3_orders enable row level security;
revoke all on public.co3_orders from public, anon, authenticated;
grant select on public.co3_orders to authenticated;
drop policy if exists co3_orders_own on public.co3_orders;
create policy co3_orders_own on public.co3_orders for select to authenticated using (user_id = (select auth.uid()));

-- 発注の値段
create or replace function public.co3_order_price(p_uid uuid, p_code text) returns bigint
language sql stable security definer set search_path = public as $$
  select round(t.price * 1.3
               * (1 + 0.25 * (select coalesce(sum(co3.count_weight(coalesce(x.kind in ('small', 'heli'), a.type = 'prop'))), 0)
                                from aircraft a left join co3_types x on x.code = a.co3_code where a.user_id = p_uid)))::bigint
    from co3_types t where t.code = p_code
$$;
revoke all on function public.co3_order_price(uuid, text) from public, anon, authenticated;

-- 機種から機体の区分（見た機体を買うときと同じ決め方）
create or replace function public.co3_type_class(p_code text) returns text
language sql stable security definer set search_path = public as $$
  select coalesce(ac_class(t.icao[1]), case when t.wing >= 'E' then 'lg' when t.wing = 'D' then 'wb' when t.kind in ('small', 'heli') then 'prop' else 'nb' end)
    from co3_types t where t.code = p_code
$$;
revoke all on function public.co3_type_class(text) from public, anon, authenticated;

-- 発注できる機種（知っている・新しい世代・旅客機か貨物機）
create or replace function public.co3_order_list() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('code', t.code, 'name', t.name, 'kind', t.kind, 'cls', co3_type_class(t.code), 'seats', t.seats, 'range', t.range_km,
           'price', co3_order_price(auth.uid(), t.code),
           'days', case co3_type_class(t.code) when 'lg' then 30 when 'wb' then 14 else 7 end) order by t.price), '[]'::jsonb)
    from co3_types t where t.gen = 'new' and t.kind in ('pax', 'freighter') and co3_knows_type(auth.uid(), t.code)
$$;
revoke all on function public.co3_order_list() from public, anon;
grant execute on function public.co3_order_list() to authenticated;

create or replace function public.co3_order(p_code text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); t co3_types; price bigint; n bigint; reg text; days int;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 4 then raise exception 'rating required 4'; end if;
  select * into t from co3_types where code = p_code;
  if not found or t.gen <> 'new' or t.kind not in ('pax', 'freighter') then raise exception 'not orderable'; end if;
  if not co3_knows_type(uid, t.code) then raise exception 'type not known'; end if;
  if t.kind = 'freighter' and (select policy from companies where user_id = uid) not in ('fsc', 'mcc', 'cargo') then raise exception 'cannot own freighters'; end if;
  price := co3_order_price(uid, t.code);
  update companies set cash = cash - price where user_id = uid and cash >= price;
  if not found then raise exception 'not enough cash'; end if;
  n := nextval('co3_order_seq');
  reg := 'SM-' || chr(65 + ((n - 1) / 999)::int % 26) || lpad((((n - 1) % 999) + 1)::text, 3, '0');
  days := case co3_type_class(t.code) when 'lg' then 30 when 'wb' then 14 else 7 end;
  insert into co3_orders (user_id, code, reg, price, deliver_on) values (uid, t.code, reg, price, (now() at time zone 'Asia/Tokyo')::date + days);
  return co_state();
end;
$$;
revoke all on function public.co3_order(text) from public, anon;
grant execute on function public.co3_order(text) to authenticated;

-- 毎朝：納入する
create or replace function public.co3_orders_deliver(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); o record; t co3_types; aid bigint; n int := 0;
begin
  for o in select * from co3_orders where aircraft_id is null and delivered_at is null and deliver_on <= d for update skip locked loop
    select * into t from co3_types where code = o.code;
    insert into aircraft (user_id, type, reg, icao, intl, paid, co3_code, bought_at)
    values (o.user_id, co3_type_class(o.code), o.reg, left(coalesce(t.icao[1], t.code), 8), co3_type_class(o.code) in ('wb', 'lg'), o.price, o.code, now()) returning id into aid;
    update co3_orders set aircraft_id = aid, delivered_at = now() where id = o.id;
    perform co3_news_add(o.user_id, 'route', 'order:' || o.reg, '新しい機体 ' || o.reg || '（' || t.name || '）が納入されました', '発注した機体');
    n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_orders_deliver(date) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_orders' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、発注を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'orders', case when v3 then coalesce((select jsonb_agg(jsonb_build_object('id', o.id, 'code', o.code,
        'name', (select name from co3_types where code = o.code), 'reg', o.reg, 'price', o.price, 'deliver_on', o.deliver_on) order by o.deliver_on)
        from co3_orders o where o.user_id = uid and o.aircraft_id is null and o.delivered_at is null), '[]'::jsonb) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-orders', '10 19 * * *', $job$ select public.co3_orders_deliver() $job$) $q$;
  end if;
end
$$;
