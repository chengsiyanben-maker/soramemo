-- 印と便の「送り直しても二重にならない」仕組み（data/idem・移行200）の確かめ。読むだけ・軽い形（一時ファイルを使わない）
-- SQL Editor に1つずつ貼って流してください

-- 1.（反映の前でも後でも）この30日で、同じ人が同じ場所に2分以内に2つ印を持っている数（返事が届かず送り直した二重の候補）
--   0 なら今まで二重は起きていない。あれば、移行200 と画面の直しで今後は起きなくなる（前の行は消さない）
select count(*) as dup_candidates
from (
  select user_id, airport_id, terminal_id, created_at,
         lag(created_at) over (partition by user_id order by created_at) as prev_at,
         lag(airport_id) over (partition by user_id order by created_at) as prev_ap,
         lag(terminal_id) over (partition by user_id order by created_at) as prev_tm
  from public.checkins
  where created_at > now() - interval '30 days'
) x
where prev_ap = airport_id and prev_tm is not distinct from terminal_id and created_at - prev_at < interval '2 minutes';

-- 2.（反映のあと）列と一意の索引ができたか。4行・どれも unique
select indexrelid::regclass as index, indisunique as is_unique
from pg_index where indexrelid::regclass::text in ('checkins_user_cid', 'flights_user_cid', 'manual_flights_user_cid', 'intl_flights_user_cid');

-- 3.（画面の直しが入ったあと・次の日）ID 付きで届いた印・便・記録帳の割合
select 'checkins' as t, count(*) filter (where client_id is not null) as with_id, count(*) as all_rows from public.checkins where created_at > now() - interval '1 day'
union all
select 'manual_flights', count(*) filter (where client_id is not null), count(*) from public.manual_flights where created_at > now() - interval '1 day';
