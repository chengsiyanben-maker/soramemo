-- 日本中の空港の滑走路の学習：毎晩、1日の航跡（track_points）から、着陸・離陸した滑走路と来た方面・向かった方面を rwy_samples に残す（rwy-learn）
--   src＝'live' は羽田・成田の30秒ごとの見張り（airport-traffic）、'track' は毎晩の航跡から
alter table public.rwy_samples add column if not exists src text not null default 'live' check (src in ('live', 'track'));
create index if not exists rwy_samples_src_at on public.rwy_samples (src, at);
-- 同じ航跡を2回読んでも重ならないように
create unique index if not exists rwy_samples_once on public.rwy_samples (src, iata, dir, callsign, at);

-- 運営用（rwy-learn だけ）：期間の航跡を、呼び出し符号ごとに。p_parts に分けて少しずつ読む
create or replace function public.rwy_learn_points(p_from timestamptz, p_to timestamptz, p_part int, p_parts int) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('cs', callsign, 'p', pts)), '[]'::jsonb) from (
    select callsign, jsonb_agg(jsonb_build_array(extract(epoch from t)::bigint, lat, lon, alt) order by t) as pts
    from public.track_points
    where t >= p_from and t < p_to and callsign ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$' and abs(hashtext(callsign)) % greatest(p_parts, 1) = p_part
    group by callsign
  ) q
$$;
revoke all on function public.rwy_learn_points(timestamptz, timestamptz, int, int) from public, anon, authenticated;

-- だれでも読める（羽田・成田は30秒ごとの見張りの記録だけ。航跡からの記録と重ねて数えない）：空港ごとに、滑走路ごと・方角（45°ずつ8つ）ごとの数（着陸は来た方角、離陸は向かった方角）
create or replace function public.rwy_learned(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('iata', p_iata, 'n', coalesce(sum(n), 0), 'rows', coalesce(jsonb_agg(jsonb_build_object('dir', dir, 'rwy', rwy, 'sec', sec, 'n', n) order by dir, rwy, sec), '[]'::jsonb))
  from (
    select dir, rwy, case when b is null then null else (((b + 22) % 360) / 45)::int end as sec, count(*) as n
    from (select dir, rwy, case when dir = 'arr' then coalesce(ent60, ent30, ent120, first_brg) else coalesce(ex60, ex30) end as b
          from public.rwy_samples where iata = p_iata and (src = 'live' or iata not in ('HND', 'NRT')) and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 90))) s
    group by 1, 2, 3
  ) q
$$;
revoke all on function public.rwy_learned(text, int) from public;
grant execute on function public.rwy_learned(text, int) to anon, authenticated;

create or replace function public.rwy_sample_counts() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select iata || ':' || dir || ':' || rwy as k, count(*) as n from public.rwy_samples group by 1) q
$$;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 8つに分けて同時に頼む（1回の処理を軽くする）
  execute $q$ select cron.schedule('rwy-learn', '15 20 * * *', $job$
    select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/rwy-learn?part=' || p, headers := '{"User-Agent": "soramemo (rwy-learn)"}'::jsonb, timeout_milliseconds := 150000)
    from generate_series(0, 7) p
  $job$) $q$;
end
$outer$;
