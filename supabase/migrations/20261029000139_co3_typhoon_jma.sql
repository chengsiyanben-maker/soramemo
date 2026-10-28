-- エアライン経営 co-v3：台風の予報を、気象庁の台風解析・予報情報から自動で入れる。CAT III の空港の表を確かめ直す
--   台風：co3-typhoon 関数（毎時17分）が気象庁の防災情報XML（台風解析・予報情報 ５日予報）を読み、
--         予報の進路（中心の位置）が明日その空港から300km以内を通る空港を co3_typhoon_auto に渡す
--         ・出典は気象庁ホームページ。ゲームの「近づきそう」を決めるために加工して使う（画面にも書く）
--         ・運営が入れた予報（source = 'admin'）は自動では変えない
--         ・進路がそれて予報から外れた空港は消す。ただし、もうだれかが計画欠航を決めた空港と日は残す
--   CAT III：公開の資料（県・国の出先の資料、まとめの記事）で8空港を確かめ直した。滑走路と確かめた時点を書いておく
--         高松は国の事業で整備が始まったところで、運用はまだ（運用が始まったら足す）

alter table public.co3_typhoon_fcst add column if not exists source text not null default 'admin';
alter table public.co3_typhoon_fcst add column if not exists event text;
alter table public.co3_typhoon_fcst add column if not exists updated_at timestamptz not null default now();
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'co3_typhoon_fcst_source_check') then
    alter table public.co3_typhoon_fcst add constraint co3_typhoon_fcst_source_check check (source in ('admin', 'jma'));
  end if;
end $$;
-- 読み方は今までどおり（だれでも読める・アプリから書けない）
alter table public.co3_typhoon_fcst enable row level security;
revoke all on public.co3_typhoon_fcst from public, anon, authenticated;
grant select on public.co3_typhoon_fcst to authenticated;
drop policy if exists co3_typhoon_fcst_read on public.co3_typhoon_fcst;
create policy co3_typhoon_fcst_read on public.co3_typhoon_fcst for select to authenticated using (true);

-- 気象庁の予報から入れる（サーバーの関数だけが呼ぶ）。p_rows = [{"iata":"OKA","event":"TC2637","note":"台風第31号"}...]
create or replace function public.co3_typhoon_auto(p_day date, p_rows jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare added int := 0; removed int := 0;
begin
  if p_day is null or p_day < co3.today() or p_day > co3.today() + 2 then raise exception 'invalid day'; end if;
  if jsonb_typeof(coalesce(p_rows, '[]'::jsonb)) <> 'array' then raise exception 'invalid rows'; end if;
  with r as (
    select distinct on (upper(x->>'iata')) upper(x->>'iata') as iata, left(x->>'event', 10) as event, left(x->>'note', 60) as note
      from jsonb_array_elements(coalesce(p_rows, '[]'::jsonb)) x
     where upper(x->>'iata') ~ '^[A-Z]{3}$' and exists (select 1 from airports a where a.iata = upper(x->>'iata'))
  ), ins as (
    insert into co3_typhoon_fcst (iata, day, note, source, event, updated_at)
    select r.iata, p_day, r.note, 'jma', r.event, now() from r
    on conflict (iata, day) do update set note = excluded.note, event = excluded.event, updated_at = now()
      where co3_typhoon_fcst.source = 'jma'
    returning 1
  ) select count(*) into added from ins;
  with del as (
    delete from co3_typhoon_fcst f
     where f.day = p_day and f.source = 'jma'
       and not exists (select 1 from jsonb_array_elements(coalesce(p_rows, '[]'::jsonb)) x where upper(x->>'iata') = f.iata)
       and not exists (select 1 from co3_typhoon_plan p where p.day = f.day and p.iata = f.iata)
    returning 1
  ) select count(*) into removed from del;
  return jsonb_build_object('day', p_day, 'saved', added, 'removed', removed);
end;
$$;
revoke all on function public.co3_typhoon_auto(date, jsonb) from public, anon, authenticated;
grant execute on function public.co3_typhoon_auto(date, jsonb) to service_role;

-- 会社の状態の台風に、予報の出どころ（jma・admin）を足す（画面の出典の書き方に使う）。形が違えば足さない（画面は気象庁の出典を書く）
do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if src ~ '''iata'', f\.iata,\s*''k'', r\.route_key,' and position('''src'', f.source' in src) = 0 then
    src := regexp_replace(src, '''iata'', f\.iata,(\s*)''k'', r\.route_key,', '''iata'', f.iata, ''src'', f.source,\1''k'', r.route_key,');
    execute src;
  end if;
end
$do$;

-- CAT III の空港：確かめ直した滑走路と時点
update public.co3_cat3_airports set note = v.note
  from (values
    ('CTS', '19R・CAT IIIb。2026年10月に公開の資料で確認'),
    ('KUH', '17・CAT IIIb。2026年10月に公開の資料で確認'),
    ('AOJ', '24・CAT IIIb（2012年7月から）。2026年10月に公開の資料で確認'),
    ('NRT', '16R・CAT IIIb。2026年10月に公開の資料で確認'),
    ('HND', '34R・CAT IIIb（2016年1月から）。2026年10月に公開の資料で確認'),
    ('NGO', '36・CAT IIIb。2026年10月に公開の資料で確認'),
    ('HIJ', '10・CAT IIIb（2015年9月に事故のあと再開）。2026年10月に公開の資料で確認'),
    ('KMJ', '07・CAT IIIb。2026年10月に公開の資料で確認')
  ) as v(iata, note)
 where co3_cat3_airports.iata = v.iata;

-- 毎時17分に気象庁の台風の情報を読む（台風の情報は3時間か6時間ごと。1時間に1回で足りる）
do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') and exists (select 1 from pg_extension where extname = 'pg_net') then
    execute $q$ select cron.schedule('co3-typhoon', '17 * * * *', $job$
      select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/co3-typhoon', headers := '{"User-Agent": "soramemo (co3-typhoon)"}'::jsonb, timeout_milliseconds := 50000)
    $job$) $q$;
  end if;
end
$$;
