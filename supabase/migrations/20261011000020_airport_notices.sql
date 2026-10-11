-- 空港ごとのお知らせ。公式の発表（航空会社・空港・行政）だけを、運営者が運営画面から手で入れる。
-- 出典（発表元の名前とURL）と発表日は必須。非公式の運航予想や個人の撮影情報は入れない。
-- 表は直接読ませず、利用者には public.airport_notices()（掲載中のものだけ）を通して見せる。

create table if not exists ops.airport_notices (
  id           bigint generated always as identity primary key,
  airport_id   integer not null references public.airports(id) on delete cascade,
  title        text not null check (length(title) between 1 and 60),
  body         text not null default '' check (length(body) <= 400),
  source_name  text not null check (length(source_name) between 1 and 40),
  source_url   text not null check (source_url ~ '^https://[^\s<>"'']+$' and length(source_url) <= 500),
  published_on date not null,
  expires_on   date check (expires_on is null or expires_on >= published_on),
  active       boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  updated_by   uuid
);
create index if not exists airport_notices_airport on ops.airport_notices (airport_id, published_on desc);
alter table ops.airport_notices enable row level security;
revoke all on ops.airport_notices from public, anon, authenticated;

-- 利用者向け：掲載中（active で、期限が日本時間の今日以降か未設定）のお知らせ。ログインしていなくても読める
create or replace function public.airport_notices() returns jsonb
language sql stable security definer set search_path = ops, public as $$
  select coalesce(jsonb_agg(jsonb_build_object(
           'id', n.id, 'airport_id', n.airport_id, 'title', n.title, 'body', n.body,
           'source_name', n.source_name, 'source_url', n.source_url,
           'published_on', n.published_on, 'expires_on', n.expires_on)
         order by n.published_on desc, n.id desc), '[]'::jsonb)
  from (select * from ops.airport_notices
        where active and (expires_on is null or expires_on >= (now() at time zone 'Asia/Tokyo')::date)
        order by published_on desc, id desc limit 300) n
$$;
revoke all on function public.airport_notices() from public;
grant execute on function public.airport_notices() to anon, authenticated;

-- 運営者向け：すべて（取り下げたもの・期限切れも）
create or replace function public.admin_notices() returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return (select coalesce(jsonb_agg(jsonb_build_object(
            'id', n.id, 'airport_id', n.airport_id, 'airport', a.name, 'title', n.title, 'body', n.body,
            'source_name', n.source_name, 'source_url', n.source_url, 'published_on', n.published_on,
            'expires_on', n.expires_on, 'active', n.active, 'updated_at', n.updated_at)
          order by n.published_on desc, n.id desc), '[]'::jsonb)
          from ops.airport_notices n join public.airports a on a.id = n.airport_id);
end;
$$;

-- 運営者向け：追加（p_id が null）と書き換え。値の確かめは表の制約に任せる
create or replace function public.admin_save_notice(p_id bigint, p_airport integer, p_title text, p_body text,
  p_source_name text, p_source_url text, p_published date, p_expires date) returns bigint
language plpgsql security definer set search_path = ops, public as $$
declare nid bigint;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_id is null then
    insert into ops.airport_notices (airport_id, title, body, source_name, source_url, published_on, expires_on, updated_by)
      values (p_airport, trim(p_title), coalesce(trim(p_body), ''), trim(p_source_name), trim(p_source_url), p_published, p_expires, auth.uid())
      returning id into nid;
  else
    update ops.airport_notices set airport_id = p_airport, title = trim(p_title), body = coalesce(trim(p_body), ''),
      source_name = trim(p_source_name), source_url = trim(p_source_url), published_on = p_published, expires_on = p_expires,
      updated_at = now(), updated_by = auth.uid()
      where id = p_id returning id into nid;
    if nid is null then raise exception 'not found'; end if;
  end if;
  insert into ops.admin_actions (admin_id, action, target, detail)
    values (auth.uid(), case when p_id is null then 'notice_add' else 'notice_edit' end, nid::text,
            jsonb_build_object('airport_id', p_airport, 'title', left(p_title, 60)));
  return nid;
end;
$$;

-- 運営者向け：掲載の取り下げと再掲載（消さずに残す）
create or replace function public.admin_set_notice_active(p_id bigint, p_active boolean) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  update ops.airport_notices set active = p_active, updated_at = now(), updated_by = auth.uid() where id = p_id;
  if not found then raise exception 'not found'; end if;
  insert into ops.admin_actions (admin_id, action, target, detail)
    values (auth.uid(), case when p_active then 'notice_show' else 'notice_hide' end, p_id::text, '{}'::jsonb);
end;
$$;

revoke all on function public.admin_notices(), public.admin_save_notice(bigint, integer, text, text, text, text, date, date),
  public.admin_set_notice_active(bigint, boolean) from public, anon;
grant execute on function public.admin_notices(), public.admin_save_notice(bigint, integer, text, text, text, text, date, date),
  public.admin_set_notice_active(bigint, boolean) to authenticated;
