-- エアライン経営の公開スイッチ（アーリーアクセスはスタンプラリーだけで始め、経営は後で公開する）
-- 運営コンソールの「非常停止」の見出しにある「エアライン経営を公開する」で切り替える。最初はオフ。
-- 公開前は、運営者以外は会社の関数（資金・増便・機材・施設など）を使えない。チェックインやフライトの記録は公開前も残り、
-- 公開したときに、それまでに飛んだ路線から会社が始まる。

insert into ops.flags (key, value) values ('game_released', 'false') on conflict (key) do nothing;

create or replace function public.app_status() returns jsonb
language sql stable security definer set search_path = ops as $$
  select jsonb_build_object('maintenance', ops.flag('maintenance'), 'message', ops.flag('maintenance_message'),
                            'checkin_enabled', ops.flag('checkin_enabled'), 'game_released', ops.flag('game_released'))
$$;

create or replace function public.admin_set_flag(p_key text, p_value jsonb) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_key not in ('maintenance', 'maintenance_message', 'checkin_enabled', 'logging_enabled', 'game_released') then raise exception 'unknown flag'; end if;
  if p_key = 'maintenance_message' and (jsonb_typeof(p_value) <> 'string' or length(p_value #>> '{}') > 200) then raise exception 'bad value'; end if;
  if p_key <> 'maintenance_message' and jsonb_typeof(p_value) <> 'boolean' then raise exception 'bad value'; end if;
  update ops.flags set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  insert into ops.admin_actions (admin_id, action, target, detail) values (auth.uid(), 'set_flag', p_key, jsonb_build_object('value', p_value));
end;
$$;

-- 会社の状態：公開前は運営者だけ
create or replace function public.co_state() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare
  uid uuid := auth.uid(); c companies; d bigint; pts bigint; st integer;
begin
  if uid is null then raise exception 'not signed in'; end if;
  -- エアライン経営は公開前（運営者だけ試せる）。ほかの会社の関数もすべて co_state を通るので、ここで止まる
  if not coalesce((ops.flag('game_released'))::boolean, false) and not public.admin_registered() then raise exception 'game not released'; end if;
  insert into companies (user_id) values (uid) on conflict do nothing;
  select * into c from companies where user_id = uid;
  d := co_daily(uid); pts := co_rep_points(uid); st := rep_stars(pts);
  return jsonb_build_object(
    'name', c.name, 'cash', c.cash, 'last', c.last_collect, 'roles', c.roles, 'daily', d,
    'bonus', co_bonus(uid), 'rep_points', pts, 'stars', st, 'rep_bonus', 0.05 * (st - 1),
    'pending', floor(d * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400),
    'total_km', (select coalesce(sum(distance_km), 0) from flights where user_id = uid),
    'routes', (select coalesce(jsonb_agg(jsonb_build_object('k', route_key, 'base', base, 'level', level, 'cost', up_cost(base, level),
                 'min_size', min_size, 'ac', ac_type, 'mult', ac_mult, 'hub', hub_mult)), '[]'::jsonb) from co_routes(uid)),
    'fleet', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'type', type, 'route', route_key) order by id), '[]'::jsonb)
                from aircraft where user_id = uid),
    'facilities', (select coalesce(jsonb_object_agg(airport_id, level), '{}'::jsonb) from facilities where user_id = uid));
end;
$$;
