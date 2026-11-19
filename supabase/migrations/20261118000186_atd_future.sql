-- 実際の出発・到着の時刻に、まだ来ていない時刻を残さない（11/18 JL661：JAL は出発の前から「実際の出発時刻」の欄に見込みの時刻を入れることがある）
--   取り込み側（_shared/odpt_status.ts）でも、まだ来ていない「実際の時刻」は見込み（etd・eta）に回すようにした。これはデータベース側の守り：
--   1. 渡された atd・ata が今より1分を超えて先なら、atd・ata に入れない（etd・eta が渡されていなければ、その時刻を etd・eta にする）
--   2. 前に入ってしまった、まだ来ていない atd・ata は、次に書き直すときに外す（今までどおり、来た時刻の atd・ata は渡されなくても消さない）
-- 表・RLS は変えない（flight_schedule の列も権限も今までどおり。関数の実行は service_role だけ）
-- 影響：チェックイン（乗る便のカード・運用タブ・案内板・通知）は、出発の前に「出発しました」と出なくなる。経営の関数は変えない
-- create or replace は関数の設定を消すので、移行178 の lock_timeout を付け直す
create or replace function public.apply_flight_status(p jsonb) returns int
language sql security definer set search_path = public as $$
  with u as (
    select (x->>'id')::bigint id, x,
           (x->>'atd')::timestamptz as atd_in, (x->>'ata')::timestamptz as ata_in,
           now() + interval '1 minute' as lim
    from jsonb_array_elements(case when jsonb_typeof(p) = 'array' then p else '[]'::jsonb end) x
  ), done as (
    update public.flight_schedule s set
      dep_status = case when u.x ? 'dep_status' then u.x->>'dep_status' else s.dep_status end,
      etd = coalesce(case when u.x ? 'etd' then (u.x->>'etd')::timestamptz else s.etd end,
                     case when u.atd_in > u.lim then u.atd_in end),
      atd = coalesce(case when u.atd_in <= u.lim then u.atd_in end, case when s.atd <= u.lim then s.atd end),
      dep_gate = case when u.x ? 'dep_gate' then u.x->>'dep_gate' else s.dep_gate end,
      arr_status = case when u.x ? 'arr_status' then u.x->>'arr_status' else s.arr_status end,
      eta = coalesce(case when u.x ? 'eta' then (u.x->>'eta')::timestamptz else s.eta end,
                     case when u.ata_in > u.lim then u.ata_in end),
      ata = coalesce(case when u.ata_in <= u.lim then u.ata_in end, case when s.ata <= u.lim then s.ata end),
      arr_gate = case when u.x ? 'arr_gate' then u.x->>'arr_gate' else s.arr_gate end,
      status_at = now()
    from u where s.id = u.id returning 1
  ) select count(*)::int from done
$$;
revoke all on function public.apply_flight_status(jsonb) from public, anon, authenticated;
alter function public.apply_flight_status(jsonb) set lock_timeout = '10s';
