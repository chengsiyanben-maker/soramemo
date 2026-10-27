-- エアライン経営 co-v3：ニュース（会社の新聞。仕様書2章「お知らせとニュース」）
--   自分の会社のことだけ（全員に見せる新聞は作らない）。どの記事にも「ゲームの中の出来事」と書く。本物の会社や事件には触れない
--   いま書くもの：新規就航（毎晩の記録で、初めて便が出た路線。1日の便数・搭乗率・機種）、神対応（対応したとき）、
--     格付けが上がった（上がったとき）、大きな実績（会社の価値が 100万・1,000万・1億 を初めて超えた日）
--   シーズンの順位は、シーズンを作るときに足す

create table if not exists public.co3_news (
  id        bigint generated always as identity primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  kind      text not null check (kind in ('route', 'god', 'rating', 'value')),
  ref       text,
  title     text not null check (length(title) <= 120),
  meta      text check (length(meta) <= 120),
  at        timestamptz not null default now(),
  unique (user_id, kind, ref)
);
create index if not exists co3_news_user on public.co3_news (user_id, at desc);
alter table public.co3_news enable row level security;
revoke all on public.co3_news from public, anon, authenticated;
grant select on public.co3_news to authenticated;
drop policy if exists "own news" on public.co3_news;
create policy "own news" on public.co3_news for select to authenticated using (user_id = auth.uid());

create or replace function public.co3_route_name(p_route text) returns text
language sql stable security definer set search_path = public as $$
  select case when p_route ~ '^[0-9]+-[0-9]+$' then
    (select regexp_replace(regexp_replace(a.name, '^.*（(.+)）$', '\1'), '(国際)?空港$', '') from airports a where a.id = split_part(p_route, '-', 1)::int) || '⇄' ||
    (select regexp_replace(regexp_replace(b.name, '^.*（(.+)）$', '\1'), '(国際)?空港$', '') from airports b where b.id = split_part(p_route, '-', 2)::int)
  else replace(p_route, '-', '⇄') end
$$;
revoke all on function public.co3_route_name(text) from public, anon, authenticated;

create or replace function public.co3_news_add(p_uid uuid, p_kind text, p_ref text, p_title text, p_meta text) returns void
language sql security definer set search_path = public as $$
  insert into co3_news (user_id, kind, ref, title, meta) values (p_uid, p_kind, p_ref, left(p_title, 120), left(p_meta, 120)) on conflict do nothing
$$;
revoke all on function public.co3_news_add(uuid, text, text, text, text) from public, anon, authenticated;

-- 神対応・格付け：その場で書く
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_trouble_do(uuid,bigint,text,boolean,timestamptz)'::regprocedure) into src;
  if position('co3_news_add' in src) = 0 then
    if position('if res = ''god'' then perform co3_sat_bump(p_uid, 8); end if;' in src) = 0 then raise exception 'co3_trouble_do の形が変わっていて、ニュースを入れられない'; end if;
    src := replace(src, 'if res = ''god'' then perform co3_sat_bump(p_uid, 8); end if;',
      'if res = ''god'' then perform co3_sat_bump(p_uid, 8);' || chr(10) ||
      '    perform co3_news_add(p_uid, ''god'', p_id::text, co3_route_name(t.route_key) || ''の'' || case when t.kind = ''delay'' then ''遅れ'' else ''欠航'' end || ''で神対応、話題に'',' || chr(10) ||
      '      case p_card when ''transfer'' then ''振替の手配'' when ''hotel'' then ''ホテルの手配'' else ''軽食とおわび'' end || ''・評判 +15・満足度 +8'');' || chr(10) ||
      '  end if;');
    execute src;
  end if;
  select pg_get_functiondef('public.co3_rating_refresh(uuid)'::regprocedure) into src;
  if position('co3_news_add' in src) = 0 then
    if position('update companies set rating = r, rating_at = now() where user_id = p_uid; return r;' in src) = 0 then raise exception 'co3_rating_refresh の形が変わっていて、ニュースを入れられない'; end if;
    src := replace(src, 'update companies set rating = r, rating_at = now() where user_id = p_uid; return r;',
      'update companies set rating = r, rating_at = now() where user_id = p_uid;' || chr(10) ||
      '    perform co3_news_add(p_uid, ''rating'', r::text, ''格付けが上がり、「'' || (array[''地域航空会社'', ''国内線の航空会社'', ''国内大手'', ''国際航空会社'', ''世界の航空会社''])[r] || ''」に'',' || chr(10) ||
      '      ''路線 '' || h.routes || ''本・機体 '' || h.fleet || ''機'');' || chr(10) ||
      '    return r;');
    execute src;
  end if;
end
$do$;

-- 毎晩の記録で：新規就航と大きな実績
create or replace function public.co3_news_daily(p_uid uuid) returns integer
language plpgsql security definer set search_path = public as $$
declare e record; v bigint; m bigint; n int := 0;
begin
  for e in select * from co3_route_econ(p_uid) r where r.flights > 0 loop
    if not exists (select 1 from co3_news where user_id = p_uid and kind = 'route' and ref = e.route_key) then
      perform co3_news_add(p_uid, 'route', e.route_key,
        co3_route_name(e.route_key) || 'に新規就航。' || case when e.seats > 0 and e.flights > 0 then '搭乗率 ' || round(e.carried / (e.seats * e.flights) * 100) || '%' else '' end,
        '1日' || e.flights || '便' || coalesce('・' || (select t.name from co3_types t where t.code = (co3_ac_spec(co3_assigned_ac(p_uid, e.route_key))).code), ''));
      n := n + 1;
    end if;
  end loop;
  v := co_value(p_uid);
  foreach m in array array[1000000, 10000000, 100000000]::bigint[] loop
    if v >= m then perform co3_news_add(p_uid, 'value', m::text, '会社の価値が' || case m when 1000000 then '100万' when 10000000 then '1,000万' else '1億' end || 'をこえた', null); end if;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_news_daily(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_daily_record(date)'::regprocedure) into src;
  if position('co3_news_daily' in src) = 0 then
    if position('get diagnostics n = row_count;' in src) = 0 then raise exception 'co3_daily_record の形が変わっていて、ニュースを入れられない'; end if;
    src := replace(src, 'get diagnostics n = row_count;', 'get diagnostics n = row_count;' || chr(10) || '  perform co3_news_daily(c.user_id) from companies c;');
    execute src;
  end if;
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''news''' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、ニュースを入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'news', case when v3 then (select coalesce(jsonb_agg(jsonb_build_object('kind', x.kind, 'title', x.title, 'meta', x.meta, 'at', x.at) order by x.at desc, x.id desc), '[]'::jsonb)
                 from (select * from co3_news where user_id = uid order by at desc, id desc limit 10) x) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
