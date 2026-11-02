-- エアライン経営 co-v3：見た機体の一覧から、乗ったことのある機体を外す
--   乗った機体は「買える」から乗った機体として買う（値段も安い）。見た機体の一覧にも出ていて、そこから買おうとすると
--   サーバーが 'ridden: use co_buy' で断り、画面には「保存できませんでした」と出ていた（11/02 一通り調べたときに見つけた）。
--   中身は今の co3_seen_list と同じで、乗った機体だけを外す。表は変えない（RLS もそのまま）
create or replace function public.co3_seen_list() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  return (select coalesce(jsonb_agg(jsonb_build_object('reg', s.reg, 'code', s.code, 'name', t.name, 'kind', s.kind, 'airport', s.airport,
            'seen_at', s.seen_at, 'flight', s.flight, 'dep', s.dep, 'arr', s.arr,
            'owned', a.id, 'price', co3_seen_price(uid, s.code), 'as_ridden', s.kind in ('freighter', 'bizjet'))
            order by s.seen_at desc), '[]'::jsonb)
    from co3_seen(uid) s join co3_types t on t.code = s.code
    left join aircraft a on a.user_id = uid and a.reg = s.reg
   where not exists (select 1 from co_rides(uid) r where r.reg = s.reg));
end;
$$;
revoke all on function public.co3_seen_list() from public, anon;
grant execute on function public.co3_seen_list() to authenticated;
