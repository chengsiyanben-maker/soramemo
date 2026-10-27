-- エアライン経営 co-v3：毎月の表彰（仕様書「会社の価値とランキング」）
--   月末（次の月の1日の朝6時、日本時間）に、全国の「今月の伸び」（月のはじめの毎朝の記録から月の終わりの記録までの会社の価値の増え方）の上位を表彰する
--     1位 30,000・2〜3位 20,000・4〜10位 10,000 と称号。会社の価値（通し）の1位は称号だけ
--   出さない設定の会社は表彰しない。同じ月を2回締めても増えない

alter table public.co3_awards drop constraint if exists co3_awards_kind_check;
alter table public.co3_awards add constraint co3_awards_kind_check
  check (kind in ('season_top10', 'season_champ', 'ally_top3', 'ally_champ', 'month_growth', 'month_value'));
alter table public.co3_awards enable row level security;

create or replace function public.co3_month_close(p_month date default null) returns integer
language plpgsql security definer set search_path = public as $$
#variable_conflict use_column
declare m date := coalesce(p_month, (date_trunc('month', (now() at time zone 'Asia/Tokyo')) - interval '1 month')::date);
        e date := (m + interval '1 month' - interval '1 day')::date; r record; n int := 0; prize int; v_label text;
begin
  for r in
    with d as (select * from co_rank_days where day between m and e),
    b as (select distinct on (user_id) user_id, value from d order by user_id, day),
    l as (select distinct on (user_id) user_id, value from d order by user_id, day desc)
    select l.user_id, l.value - b.value as g, rank() over (order by l.value - b.value desc) as no
      from b join l using (user_id) join companies c on c.user_id = l.user_id where not c.hide_rank
  loop
    exit when r.no > 10;
    prize := case when r.no = 1 then 30000 when r.no <= 3 then 20000 else 10000 end;
    v_label := extract(year from m)::int || '年' || extract(month from m)::int || '月 今月の伸び ' || r.no || '位';
    insert into co3_awards (user_id, kind, ref, label) values (r.user_id, 'month_growth', to_char(m, 'YYYY-MM'), v_label) on conflict do nothing;
    if found then
      update companies set cash = cash + prize where user_id = r.user_id;
      perform co3_news_add(r.user_id, 'rating', 'month:' || to_char(m, 'YYYY-MM'), v_label || '（' || prize || '）', '毎月の表彰');
      n := n + 1;
    end if;
  end loop;
  insert into co3_awards (user_id, kind, ref, label)
  select x.user_id, 'month_value', to_char(m, 'YYYY-MM'), extract(year from m)::int || '年' || extract(month from m)::int || '月 会社の価値 1位'
    from (select r.user_id from co_rank_days r join companies c on c.user_id = r.user_id
           where r.day = (select max(day) from co_rank_days where day between m and e) and not c.hide_rank order by r.value desc limit 1) x
  on conflict do nothing;
  if found then n := n + 1; end if;
  return n;
end;
$$;
revoke all on function public.co3_month_close(date) from public, anon, authenticated;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-month-close', '5 21 * * *', $job$
      select public.co3_month_close() where extract(day from (now() at time zone 'Asia/Tokyo')) = 1 $job$) $q$;
  end if;
end
$$;
