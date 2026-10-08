-- 自分でとるバックアップ（無料プランには毎日の自動バックアップがないため）
-- 運営コンソールの「バックアップ」から、全員の記録を1つのJSONファイルに書き出す。運営者（2段階認証つき）だけが使える。
-- 書き出したことは ops.admin_actions に残る。戻すときは tools/restore_from_backup.py でSQLを作り、SQL Editor で流す。
-- 注意：ログインのアカウントそのもの（auth.users）は、このファイルからは作り直せない。同じプロジェクトでデータが壊れた・消えたときに戻すためのもの。

create or replace function public.admin_backup() returns jsonb
language plpgsql security definer set search_path = ops, public, auth as $$
declare out jsonb;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  out := jsonb_build_object(
    'app', 'soramemo', 'format', 1, 'created_at', now(),
    'users',           (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'email', email, 'created_at', created_at) order by created_at), '[]') from auth.users),
    'checkins',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.checkins t),
    'flights',         (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.flights t),
    'manual_flights',  (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.manual_flights t),
    'companies',       (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.companies t),
    'route_levels',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.route_levels t),
    'aircraft',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.aircraft t),
    'facilities',      (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.facilities t),
    'subscriptions',   (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.subscriptions t),
    'admins',          (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.admins t),
    'flags',           (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.flags t));
  insert into ops.admin_actions (admin_id, action, target, detail)
  values (auth.uid(), 'backup', 'all', jsonb_build_object('users', jsonb_array_length(out->'users'), 'checkins', jsonb_array_length(out->'checkins'), 'flights', jsonb_array_length(out->'flights')));
  return out;
end;
$$;

-- 前回のバックアップの日時（運営コンソールの「7日以上たっています」の知らせに使う）
create or replace function public.admin_last_backup() returns timestamptz
language sql stable security definer set search_path = ops, public as $$
  select case when public.is_admin() then (select max(created_at) from ops.admin_actions where action = 'backup') end
$$;

revoke all on function public.admin_backup(), public.admin_last_backup() from public, anon;
grant execute on function public.admin_backup(), public.admin_last_backup() to authenticated;
