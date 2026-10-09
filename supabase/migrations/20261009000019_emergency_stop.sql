-- 非常停止（Claude からも止められるようにする）。止めるだけで、戻す機能は作らない。
-- 呼べるのは service_role（emergency-stop の Edge Function）だけ。anon・ログイン済みの利用者からは呼べない。
-- 操作は ops.admin_actions に残る（運営画面の操作ログで見える）。

create or replace function ops.emergency_stop(p_message text) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  update ops.flags set value = 'true'::jsonb, updated_at = now() where key = 'maintenance';
  update ops.flags set value = to_jsonb(left(coalesce(p_message, ''), 200)), updated_at = now() where key = 'maintenance_message';
  -- 運営者の操作ではないので、admin_id は全部0の UUID にし、detail で出どころを残す
  insert into ops.admin_actions (admin_id, action, target, detail)
    values ('00000000-0000-0000-0000-000000000000', 'emergency_stop', 'maintenance',
            jsonb_build_object('source', 'emergency-stop', 'message', left(coalesce(p_message, ''), 200)));
end;
$$;

-- Edge Function から呼べるように、public に service_role 専用の入口を作る
create or replace function public.emergency_stop(p_message text) returns void
language sql security definer set search_path = ops, public as $$
  select ops.emergency_stop(p_message)
$$;

revoke all on function public.emergency_stop(text) from public, anon, authenticated;
grant execute on function public.emergency_stop(text) to service_role;
revoke all on function ops.emergency_stop(text) from public, anon, authenticated;
