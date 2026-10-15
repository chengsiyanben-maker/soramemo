-- 航空会社の運航情報（ODPT）の、便ごとの実際の時刻・変更後の時刻・状態・搭乗口を、予定の便（flight_schedule）に残す（odpt-status が5分ごとに入れる）。
-- フライトの記録の照合（運航確認）と、記録で選ぶ便の候補に使う。予定の便と同じく14日で消える。
alter table public.flight_schedule
  add column if not exists dep_status text check (length(dep_status) <= 40),
  add column if not exists etd timestamptz, add column if not exists atd timestamptz,
  add column if not exists dep_gate text check (length(dep_gate) <= 4),
  add column if not exists arr_status text check (length(arr_status) <= 40),
  add column if not exists eta timestamptz, add column if not exists ata timestamptz,
  add column if not exists arr_gate text check (length(arr_gate) <= 4),
  add column if not exists status_at timestamptz;

-- まとめて入れる。届かなかった項目（キーがないもの）は変えず、一度入った実際の時刻（atd・ata）は消さない
create or replace function public.apply_flight_status(p jsonb) returns int
language sql security definer set search_path = public as $$
  with u as (
    select (x->>'id')::bigint id, x from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) x
  ), done as (
    update public.flight_schedule s set
      dep_status = case when u.x ? 'dep_status' then u.x->>'dep_status' else s.dep_status end,
      etd = case when u.x ? 'etd' then (u.x->>'etd')::timestamptz else s.etd end,
      atd = coalesce((u.x->>'atd')::timestamptz, s.atd),
      dep_gate = case when u.x ? 'dep_gate' then u.x->>'dep_gate' else s.dep_gate end,
      arr_status = case when u.x ? 'arr_status' then u.x->>'arr_status' else s.arr_status end,
      eta = case when u.x ? 'eta' then (u.x->>'eta')::timestamptz else s.eta end,
      ata = coalesce((u.x->>'ata')::timestamptz, s.ata),
      arr_gate = case when u.x ? 'arr_gate' then u.x->>'arr_gate' else s.arr_gate end,
      status_at = now()
    from u where s.id = u.id returning 1
  ) select count(*)::int from done
$$;
revoke all on function public.apply_flight_status(jsonb) from public, anon, authenticated;

-- 便の候補に、実際の出発・到着の時刻と状態も返す（分かっているときだけ）
create or replace function public.flight_candidates(p_dep text, p_arr text, p_dep_at timestamptz, p_arr_at timestamptz)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', flight, 'std', std, 'sta', sta, 'aircraft', aircraft, 'source', source, 'diff_min', diff,
           'atd', atd, 'ata', ata, 'cancelled', coalesce(dep_status ~* 'cancel' or arr_status ~* 'cancel', false)) order by diff, std), '[]'::jsonb)
  from (
    select flight, std, sta, aircraft, source, atd, ata, dep_status, arr_status,
           round((abs(extract(epoch from (coalesce(atd, std) - p_dep_at))) + abs(extract(epoch from (coalesce(ata, sta) - p_arr_at)))) / 60)::int as diff
    from public.flight_schedule
    where p_dep ~ '^[A-Z]{3}$' and p_arr ~ '^[A-Z]{3}$'
      and p_arr_at > p_dep_at and p_arr_at - p_dep_at < interval '24 hours'
      and dep = p_dep and arr = p_arr
      and std between p_dep_at - interval '3 hours' and p_arr_at
      and sta between p_dep_at and p_arr_at + interval '3 hours'
    order by diff, std
    limit 5
  ) c
$$;
revoke all on function public.flight_candidates(text, text, timestamptz, timestamptz) from public;
grant execute on function public.flight_candidates(text, text, timestamptz, timestamptz) to anon, authenticated;
