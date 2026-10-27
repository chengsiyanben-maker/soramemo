-- エアライン経営 co-v3：混雑空港の発着枠を「毎月の申し込み」にする（仕様書「混雑空港の発着枠（申し込んだ便数を分け合う）」）
--   対象：混雑空港5つ（羽田・成田・関西・伊丹・福岡）。海外の混む空港はまだ国際線の便を数えていないので、あとで足す
--   毎月1日の深夜3時（日本時間）に、その月の枠を決める（co3_slots_decide。毎日 18:00 UTC に動かし、決まっていなければ決める）
--     申し込み：おまかせの会社（格付け1・2はみなおまかせ）は、そのときに組んでいる便数（co3_slot_use）をそのまま。
--               自分で申し込む会社は、前の月のうちに出した申し込み（co3_slot_apps）。出していない空港は、組んでいる便数
--     枠：時間値 × 運用時間 × ゲームの倍率（遊んでいる会社 ÷ 50、1より小さいときは1）。羽田は2割を「地方の枠」に分ける
--         （羽田と、大きい空港どうしでない相手を結ぶ路線の申し込みだけで分ける）
--     分け方：合計が枠に収まれば申し込みどおり。超えたら申し込みの割合で分け、どの会社も最低1日4便（co3.slot_allot）
--   その月のあいだ：自社の便は「もらった枠 ÷ いま組んでいる便数」の割合まで（1を超えない）。削られた分は運休
--     その月に枠をもらっていない空港（月の途中で始めた路線）は、最低の1日4便まで使える
--     混雑料金の割合は、その月に決まった混み具合（申し込みの合計 ÷ 枠）で固定する
--   まだ一度も決めていない月（入れた直後）は、今までどおり、いまの便数で分ける
--   空港への投資の重み・アライアンスで分ける・枠の売り買いは、それらの仕組みを作るときに足す

alter table public.co3_news drop constraint if exists co3_news_kind_check;
alter table public.co3_news add constraint co3_news_kind_check check (kind in ('route', 'god', 'rating', 'value', 'slots'));
alter table public.co3_news enable row level security;
alter table public.companies add column if not exists slot_auto boolean not null default true;
alter table public.companies enable row level security;

-- 自分で出した申し込み（その月の1日に決まる分）
create table if not exists public.co3_slot_apps (
  user_id uuid not null references auth.users (id) on delete cascade,
  month date not null,
  iata text not null check (iata in ('HND', 'NRT', 'KIX', 'ITM', 'FUK')),
  pool text not null default 'main' check (pool in ('main', 'regional')),
  flights integer not null check (flights between 0 and 400),
  updated_at timestamptz not null default now(),
  primary key (user_id, month, iata, pool)
);
alter table public.co3_slot_apps enable row level security;
drop policy if exists co3_slot_apps_own on public.co3_slot_apps;
create policy co3_slot_apps_own on public.co3_slot_apps for select to authenticated using (user_id = (select auth.uid()));
revoke all on public.co3_slot_apps from public, anon, authenticated;
grant select on public.co3_slot_apps to authenticated;

-- 空港ごとのその月の枠と申し込みの合計（どの会社の分かは出さない。だれでも見られる）
create table if not exists public.co3_slot_month (
  month date not null,
  iata text not null,
  pool text not null default 'main' check (pool in ('main', 'regional')),
  capacity numeric not null,
  total integer not null,
  decided_at timestamptz not null default now(),
  primary key (month, iata, pool)
);
alter table public.co3_slot_month enable row level security;
drop policy if exists co3_slot_month_read on public.co3_slot_month;
create policy co3_slot_month_read on public.co3_slot_month for select to authenticated using (true);
revoke all on public.co3_slot_month from public, anon, authenticated;
grant select on public.co3_slot_month to authenticated;

-- 会社ごとにもらった枠
create table if not exists public.co3_slot_grants (
  user_id uuid not null references auth.users (id) on delete cascade,
  month date not null,
  iata text not null,
  pool text not null default 'main' check (pool in ('main', 'regional')),
  applied integer not null,
  granted integer not null,
  primary key (user_id, month, iata, pool)
);
alter table public.co3_slot_grants enable row level security;
drop policy if exists co3_slot_grants_own on public.co3_slot_grants;
create policy co3_slot_grants_own on public.co3_slot_grants for select to authenticated using (user_id = (select auth.uid()));
revoke all on public.co3_slot_grants from public, anon, authenticated;
grant select on public.co3_slot_grants to authenticated;

-- いまの月（日本時間の月の1日）
create or replace function co3.month_now() returns date
language sql stable as $$ select date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date $$;
revoke all on function co3.month_now() from public, anon, authenticated;

-- 羽田の路線が「地方の枠」か（相手が大きい空港どうしでない）。羽田以外はいつも main
create or replace function co3.slot_pool(p_iata text, p_a text, p_b text) returns text
language sql stable security definer set search_path = public as $$
  select case when p_iata = 'HND' and not (co3.size_of(p_a) in ('xl', 'hub') and co3.size_of(p_b) in ('xl', 'hub')) then 'regional' else 'main' end
$$;
revoke all on function co3.slot_pool(text, text, text) from public, anon, authenticated;

-- 枠の大きさ（羽田は 8割が main、2割が regional）
create or replace function co3.slot_pool_cap(p_iata text, p_pool text, p_active integer) returns numeric
language sql immutable as $$
  select co3.slot_capacity(co3.slot_hourly(p_iata), co3.slot_hours(p_iata), p_active)
         * case when p_iata <> 'HND' then 1 when p_pool = 'regional' then 0.2 else 0.8 end
$$;
revoke all on function co3.slot_pool_cap(text, text, integer) from public, anon, authenticated;

-- 会社ごと・混雑空港ごとの、いま組んでいる1日の便（co3_slot_totals と同じ数え方）
create or replace function public.co3_slot_use(p_uid uuid) returns table (iata text, pool text, fl integer)
language sql stable security definer set search_path = public as $$
  with k as (
    select ac.user_id, ac.route_key,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 1)::int) else split_part(ac.route_key, '-', 1) end as a,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 2)::int) else split_part(ac.route_key, '-', 2) end as b
      from aircraft ac where ac.route_key is not null and ac.user_id = p_uid
  ), f as (
    select k.a, k.b, coalesce(p.flights, co3.legs_per_day(coalesce(co3_km(k.a, k.b), 800))) as fl
      from k left join co3_plans p on p.user_id = k.user_id and p.route_key = k.route_key
    union all select s.dep, s.arr, 1 from co3_sched s where s.user_id = p_uid
  )
  select u.ap, co3.slot_pool(u.ap, u.a, u.b), sum(u.fl)::int
    from (select a as ap, a, b, fl from f union all select b, a, b, fl from f) u
   where u.ap in ('HND', 'NRT', 'KIX', 'ITM', 'FUK') group by 1, 2
$$;
revoke all on function public.co3_slot_use(uuid) from public, anon, authenticated;

-- その月の枠を決める。もう決まっていれば何もしない
create or replace function public.co3_slots_decide(p_month date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare m date := coalesce(p_month, co3.month_now()); act int; n int := 0;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  if exists (select 1 from co3_slot_month where month = m) then return 0; end if;
  select count(*)::int into act from companies where last_collect > now() - interval '30 days';
  create temp table if not exists co3_tmp_req (user_id uuid, iata text, pool text, req int) on commit drop;
  delete from co3_tmp_req;
  -- おまかせ・格付け1・2：いまの便。自分で申し込む会社：申し込み、出していない空港はいまの便
  insert into co3_tmp_req
    select c.user_id, u.iata, u.pool, u.fl from companies c cross join lateral co3_slot_use(c.user_id) u
     where (c.slot_auto or coalesce(c.rating, 1) < 3)
        or not exists (select 1 from co3_slot_apps x where x.user_id = c.user_id and x.month = m and x.iata = u.iata and x.pool = u.pool);
  insert into co3_tmp_req
    select x.user_id, x.iata, x.pool, x.flights from co3_slot_apps x join companies c on c.user_id = x.user_id
     where x.month = m and not c.slot_auto and coalesce(c.rating, 1) >= 3;
  delete from co3_tmp_req where req <= 0;
  -- 枠（申し込みがなくても5つの空港は書く）
  insert into co3_slot_month (month, iata, pool, capacity, total)
    select m, p.iata, p.pool, round(co3.slot_pool_cap(p.iata, p.pool, act), 1), coalesce((select sum(r.req) from co3_tmp_req r where r.iata = p.iata and r.pool = p.pool), 0)
      from (values ('HND', 'main'), ('HND', 'regional'), ('NRT', 'main'), ('KIX', 'main'), ('ITM', 'main'), ('FUK', 'main')) p(iata, pool);
  insert into co3_slot_grants (user_id, month, iata, pool, applied, granted)
    select r.user_id, m, r.iata, r.pool, r.req, co3.slot_allot(r.req, s.total, s.capacity)
      from co3_tmp_req r join co3_slot_month s on s.month = m and s.iata = r.iata and s.pool = r.pool;
  get diagnostics n = row_count;
  -- 会社の新聞：削られた空港
  perform co3_news_add(g.user_id, 'slots', to_char(m, 'YYYY-MM') || g.iata || g.pool,
            to_char(m, 'FMMM') || '月の' || case g.iata when 'HND' then '羽田' when 'NRT' then '成田' when 'KIX' then '関西' when 'ITM' then '伊丹' else '福岡' end
            || case when g.pool = 'regional' then '（地方の枠）' else '' end || 'の発着枠は 1日' || g.granted || '便（申し込み ' || g.applied || '便）',
            case when g.granted < g.applied then '申し込みが多く、割合で分けました' else '申し込みどおり' end)
    from co3_slot_grants g where g.month = m and exists (select 1 from companies c where c.user_id = g.user_id);
  return n;
end;
$$;
revoke all on function public.co3_slots_decide(date) from public, anon, authenticated;

-- 自社の便のうち、その月に使える便。月が決まっていなければ今までどおり（いまの便数で分ける）
create or replace function public.co3_slot_fl(p_uid uuid, p_fl integer, p_a text, p_b text) returns integer
language sql stable security definer set search_path = public as $$
  with ends as (select x as iata, co3.slot_pool(x, p_a, p_b) as pool from unnest(array[p_a, p_b]) x where x in ('HND', 'NRT', 'KIX', 'ITM', 'FUK')),
  m as (select co3.month_now() as m)
  select case
    when not exists (select 1 from ends) then p_fl
    when not exists (select 1 from co3_slot_month s, m where s.month = m.m) then co3_slot_cap(p_fl, p_a, p_b)
    else least(p_fl, (select min(floor(p_fl * least(1, coalesce(g.granted, 4)::numeric / greatest(1, coalesce(u.fl, p_fl)))))::int
                        from ends e cross join m
                        left join co3_slot_grants g on g.user_id = p_uid and g.month = m.m and g.iata = e.iata and g.pool = e.pool
                        left join co3_slot_use(p_uid) u on u.iata = e.iata and u.pool = e.pool)) end
$$;
revoke all on function public.co3_slot_fl(uuid, integer, text, text) from public, anon, authenticated;

-- 申し込み（来月の分。格付け3から・自分で申し込む会社だけ）。p_flights が null なら取り消し（いまの便で申し込む）
create or replace function public.co3_slot_apply(p_iata text, p_pool text, p_flights integer) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); nm date := (co3.month_now() + interval '1 month')::date;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if (select slot_auto from companies where user_id = uid) then raise exception 'slot auto'; end if;
  if p_iata not in ('HND', 'NRT', 'KIX', 'ITM', 'FUK') or coalesce(p_pool, 'main') not in ('main', 'regional') or (p_pool = 'regional' and p_iata <> 'HND') then raise exception 'invalid airport'; end if;
  if p_flights is null then
    delete from co3_slot_apps where user_id = uid and month = nm and iata = p_iata and pool = coalesce(p_pool, 'main');
  else
    if p_flights < 0 or p_flights > 400 then raise exception 'invalid flights'; end if;
    insert into co3_slot_apps (user_id, month, iata, pool, flights) values (uid, nm, p_iata, coalesce(p_pool, 'main'), p_flights)
      on conflict (user_id, month, iata, pool) do update set flights = excluded.flights, updated_at = now();
  end if;
  return co_state();
end;
$$;
revoke all on function public.co3_slot_apply(text, text, integer) from public, anon;
grant execute on function public.co3_slot_apply(text, text, integer) to authenticated;

create or replace function public.co3_set_slot_auto(p_on boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  update companies set slot_auto = coalesce(p_on, true) where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_slot_auto(boolean) from public, anon;
grant execute on function public.co3_set_slot_auto(boolean) to authenticated;

-- 画面用：いまの月の枠と、来月の申し込み
create or replace function public.co3_slots_view(p_uid uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with m as (select co3.month_now() as m, (co3.month_now() + interval '1 month')::date as nm),
  p as (select * from (values ('HND', 'main', 1), ('HND', 'regional', 2), ('NRT', 'main', 3), ('KIX', 'main', 4), ('ITM', 'main', 5), ('FUK', 'main', 6)) v(iata, pool, o))
  select jsonb_build_object(
    'month', (select m from m), 'next', (select nm from m), 'decided', exists (select 1 from co3_slot_month s, m where s.month = m.m),
    'auto', coalesce((select slot_auto or coalesce(rating, 1) < 3 from companies where user_id = p_uid), true),
    'list', coalesce((select jsonb_agg(jsonb_build_object('iata', p.iata, 'pool', p.pool,
        'use', coalesce(u.fl, 0), 'granted', g.granted, 'applied', g.applied,
        'cong', (select round(sum(z.total) / nullif(sum(z.capacity), 0), 2) from co3_slot_month z where z.month = m.m and z.iata = p.iata),
        'apply', x.flights) order by p.o)
      from p cross join m
      left join co3_slot_use(p_uid) u on u.iata = p.iata and u.pool = p.pool
      left join co3_slot_month s on s.month = m.m and s.iata = p.iata and s.pool = p.pool
      left join co3_slot_grants g on g.user_id = p_uid and g.month = m.m and g.iata = p.iata and g.pool = p.pool
      left join co3_slot_apps x on x.user_id = p_uid and x.month = m.nm and x.iata = p.iata and x.pool = p.pool), '[]'::jsonb))
$$;
revoke all on function public.co3_slots_view(uuid) from public, anon, authenticated;

do $do$
declare fn text; src text; n0 text;
begin
  -- 旅客の便：その月に使える便まで
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_slot_fl' in src) = 0 then
    n0 := src;
    src := replace(src, $r$least(e.fl0,
                 coalesce((select min(co3.slot_allot(e.fl0, q.total::int, co3.slot_capacity(co3.slot_hourly(q.iata), co3.slot_hours(q.iata), (select n from active))))
                             from req q where q.iata in (e.a, e.b)), e.fl0)) as fl,$r$, $r$co3_slot_fl(p_uid, e.fl0, e.a, e.b) as fl,$r$);
    if src = n0 then raise exception 'co3_route_econ の形が変わっていて、毎月の発着枠を入れられない'; end if;
    execute src;
  end if;
  -- 貨物機の便
  select pg_get_functiondef('public.co3_cargo_econ(uuid)'::regprocedure) into src;
  if position('co3_slot_fl' in src) = 0 then
    n0 := src;
    src := replace(src, $r$co3_slot_cap(least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = cr.route_key), 99), co3.legs_per_day(cr.km)), cr.a, cr.b) as fl,$r$,
                        $r$co3_slot_fl(p_uid, least(coalesce((select p.flights from co3_plans p where p.user_id = p_uid and p.route_key = cr.route_key), 99), co3.legs_per_day(cr.km)), cr.a, cr.b) as fl,$r$);
    if src = n0 then raise exception 'co3_cargo_econ の形が変わっていて、毎月の発着枠を入れられない'; end if;
    execute src;
  end if;
  -- 会社の状態：発着枠
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_slots_view' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、発着枠を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'slots', case when v3 then co3_slots_view(uid) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

-- 混雑料金：その月が決まっていれば、決まった混み具合で固定する（いまの枠の大きさに合わせて合計を直して返す）
create or replace function public.co3_slot_totals() returns table (iata text, total numeric)
language sql stable security definer set search_path = public as $$
  with k as (
    select ac.user_id, ac.route_key,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 1)::int) else split_part(ac.route_key, '-', 1) end as a,
           case when ac.route_key ~ '^[0-9]+-[0-9]+$' then (select x.iata from airports x where x.id = split_part(ac.route_key, '-', 2)::int) else split_part(ac.route_key, '-', 2) end as b
      from aircraft ac where ac.route_key is not null
  ), f as (
    select k.a, k.b, coalesce(p.flights, co3.legs_per_day(coalesce(co3_km(k.a, k.b), 800))) as fl
      from k left join co3_plans p on p.user_id = k.user_id and p.route_key = k.route_key
  ), live as (
    select ap, sum(fl) as total from (
      select a as ap, fl from f union all select b, fl from f
      union all select s.dep, 1 from co3_sched s union all select s.arr, 1 from co3_sched s) u
     where ap in ('HND', 'NRT', 'KIX', 'ITM', 'FUK') group by ap
  ), dec as (
    select s.iata, sum(s.total)::numeric / nullif(sum(s.capacity), 0) as ratio from co3_slot_month s where s.month = co3.month_now() group by s.iata
  )
  select x.iata, coalesce(d.ratio * co3.slot_capacity(co3.slot_hourly(x.iata), co3.slot_hours(x.iata),
                                                      (select count(*)::int from companies where last_collect > now() - interval '30 days')), l.total)
    from (select unnest(array['HND', 'NRT', 'KIX', 'ITM', 'FUK']) as iata) x
    left join live l on l.ap = x.iata left join dec d on d.iata = x.iata
   where l.total is not null or d.ratio is not null
$$;
revoke all on function public.co3_slot_totals() from public, anon, authenticated;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-slots', '0 18 * * *', $job$ select public.co3_slots_decide() $job$) $q$;
  end if;
end
$$;
