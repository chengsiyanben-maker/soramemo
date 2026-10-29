-- エアライン経営をアーリーアクセスで公開する（10/29 企画者の指示「ゲーム機能もアーリーアクセスでリリースしよう」）
--   ・本番のデータベースだけで、経営の公開（game_released）と新しい計算（co_v3）をオンにする
--     試験のデータベース（PGlite。pg_cron がない）では今までどおりオフのまま（試験は自分でスイッチを入れて確かめる）
--   ・運営の非常停止の関数 admin_set_flag で co_v3 も切り替えられるようにする（何かあれば運営が戻せる）
--   ・表は変えない（RLS もそのまま）

create or replace function public.admin_set_flag(p_key text, p_value jsonb) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_key not in ('maintenance', 'maintenance_message', 'checkin_enabled', 'logging_enabled', 'game_released', 'co_v3') then raise exception 'unknown flag'; end if;
  if p_key = 'maintenance_message' and (jsonb_typeof(p_value) <> 'string' or length(p_value #>> '{}') > 200) then raise exception 'bad value'; end if;
  if p_key <> 'maintenance_message' and jsonb_typeof(p_value) <> 'boolean' then raise exception 'bad value'; end if;
  update ops.flags set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  insert into ops.admin_actions (admin_id, action, target, detail) values (auth.uid(), 'set_flag', p_key, jsonb_build_object('value', p_value));
end;
$$;
revoke all on function public.admin_set_flag(text, jsonb) from public, anon;
grant execute on function public.admin_set_flag(text, jsonb) to authenticated;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    update ops.flags set value = 'true'::jsonb, updated_at = now() where key in ('game_released', 'co_v3');
  end if;
end
$$;
