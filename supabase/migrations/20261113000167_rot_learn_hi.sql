-- 運用予想を learn_hi に切り替える（11/13 17時30分 PM の指示・本人「切り替えて」）
-- predict_rotation_v2 が呼ぶ方式を 'learn'（2回以上・3割以上）から 'learn_hi'（3回以上・4割以上）に替える。
-- 返す形は今のまま（'method' の値だけ 'learn_hi' になる。便ごとの src は今までどおり livery／learn／base）。
-- 表・索引・RLS・毎晩の処理（rot-pairs・rot-eval の採点は base・learn・learn_hi の3通りのまま）は変えない。
-- 関数の権限も今のまま（anon・authenticated に実行だけ）。影響はチェックイン（運用予想の画面）だけ、経営なし。
-- 約4週間後（記録が42日そろったら）docs/pm/rotation-eval-view.sql で比べ直す。
set lock_timeout = '10s';

create or replace function public.predict_rotation_v2(p_reg text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare cur record;
begin
  if p_reg is null or p_reg !~ '^[A-Z0-9-]{2,10}$' then return null; end if;
  select day, callsign, dep, arr, first_at, last_at, type into cur from public.reg_legs
  where reg = p_reg and day >= (now() at time zone 'Asia/Tokyo')::date - 1 order by last_at desc limit 1;
  if cur is null then return jsonb_build_object('reg', p_reg, 'known', null, 'next', '[]'::jsonb, 'src', 'reg', 'method', 'learn_hi', 'estimate', true); end if;
  return jsonb_build_object('reg', p_reg, 'src', 'reg', 'method', 'learn_hi', 'estimate', true, 'type', cur.type,
    'known', jsonb_build_object('callsign', cur.callsign, 'dep', cur.dep, 'arr', cur.arr, 'first', cur.first_at, 'last', cur.last_at),
    'next', public.rot_predict('learn_hi', p_reg, cur.day, cur.callsign, cur.arr, (cur.first_at at time zone 'Asia/Tokyo')::time, 4));
end $$;
revoke all on function public.predict_rotation_v2(text) from public;
grant execute on function public.predict_rotation_v2(text) to anon, authenticated;

reset lock_timeout;
