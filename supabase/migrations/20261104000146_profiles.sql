-- 利用者のプロフィール（新規登録のとき）
--   profiles      ：表示名・登録日・同意した規約の版と日時・使い方の答え（撮る・修行・気軽・未回答）と答えた日時。
--                   1人1行。本人だけが読み書きできる（消すのはアカウントの削除だけ）。使い方の答えはマイページからいつでも変えられる
--   terms_versions：利用規約の版の一覧（版＝改定日の文字）。だれでも読める。足すのは運営者が移行で
-- 登録日と同意の日時は、アプリからは書き換えられない（ログインした利用者が書くと、サーバーが決めた値に置きかわる）。
-- 規約に同意できるのは、いま有効な版だけ。版が変わったときは、アプリが新しい版で同意を取り直す（terms_version を変えると日時も新しくなる）。
-- アカウントを消すと行も消える（auth.users を on delete cascade で参照）。

create table if not exists public.terms_versions (
  version      text primary key check (version ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'),   -- 例：2026-10-15
  effective_on date not null,                                                       -- この日（日本時間）から有効
  url          text not null check (url ~ '^https://')
);
alter table public.terms_versions enable row level security;
revoke all on public.terms_versions from public, anon, authenticated;
grant select on public.terms_versions to anon, authenticated;
drop policy if exists "terms versions readable" on public.terms_versions;
create policy "terms versions readable" on public.terms_versions for select to anon, authenticated using (true);
insert into public.terms_versions (version, effective_on, url)
values ('2026-10-15', date '2026-10-15', 'https://soramemo.jp/terms.html')   -- いまの利用規約（制定 10/6、改定 10/15）
on conflict (version) do nothing;

-- いま有効な規約の版（日本時間の今日までに有効になった、いちばん新しいもの）
create or replace function public.terms_current() returns text
language sql stable set search_path = public as $$
  select version from public.terms_versions
  where effective_on <= (now() at time zone 'Asia/Tokyo')::date
  order by effective_on desc, version desc limit 1
$$;
grant execute on function public.terms_current() to anon, authenticated;

create table if not exists public.profiles (
  user_id         uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  display_name    text not null check (
                    char_length(display_name) between 1 and 20
                    and display_name = btrim(display_name)
                    and display_name !~ '[[:cntrl:]]'),
  registered_at   timestamptz not null default now(),   -- 登録日（ログインのアカウントを作った日時）
  terms_version   text not null references public.terms_versions (version),
  terms_agreed_at timestamptz not null default now(),   -- その版に同意した日時
  usage_answer    text not null default 'none'          -- 使い方の答え：spot＝撮る・shugyo＝修行・casual＝気軽・none＝未回答
                    check (usage_answer in ('spot', 'shugyo', 'casual', 'none')),   -- 記号はアプリのひな形と同じ
  usage_answered_at timestamptz,                        -- 答えた（変えた）日時。未回答なら空
  updated_at      timestamptz not null default now()
);
alter table public.profiles add column if not exists usage_answer text not null default 'none'
  check (usage_answer in ('spot', 'shugyo', 'casual', 'none'));
alter table public.profiles add column if not exists usage_answered_at timestamptz;
alter table public.profiles enable row level security;
revoke all on public.profiles from public, anon, authenticated;
grant select, insert, update on public.profiles to authenticated;   -- 消す権限は渡さない（アカウントの削除で消える）
drop policy if exists "own profile read" on public.profiles;
drop policy if exists "own profile insert" on public.profiles;
drop policy if exists "own profile update" on public.profiles;
create policy "own profile read"   on public.profiles for select to authenticated using (user_id = auth.uid());
create policy "own profile insert" on public.profiles for insert to authenticated with check (user_id = auth.uid());
create policy "own profile update" on public.profiles for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- 本人のアカウントを作った日時（auth.users は利用者から読めないので、ここだけ通す）
create or replace function public.my_signup_at() returns timestamptz
language sql stable security definer set search_path = auth, public as $$
  select created_at from auth.users where id = auth.uid()
$$;
revoke all on function public.my_signup_at() from public, anon;
grant execute on function public.my_signup_at() to authenticated;

-- 書かれるたびに：利用者（authenticated）が書いたときは、登録日・同意の日時をサーバーが決める。
-- 運営者がバックアップから戻すとき（SQL Editor・service_role）は、書かれた値をそのまま残す。
create or replace function public.profiles_guard() returns trigger
language plpgsql set search_path = public as $$
begin
  new.updated_at := now();
  if current_user <> 'authenticated' then return new; end if;
  if tg_op = 'INSERT' then
    new.registered_at := coalesce(public.my_signup_at(), now());
    if new.terms_version is distinct from public.terms_current() then raise exception 'terms version must be current'; end if;
    new.terms_agreed_at := now();
    new.usage_answered_at := case when new.usage_answer = 'none' then null else now() end;
  else
    new.user_id := old.user_id;
    if new.usage_answer is distinct from old.usage_answer then
      new.usage_answered_at := case when new.usage_answer = 'none' then null else now() end;
    else
      new.usage_answered_at := old.usage_answered_at;
    end if;
    new.registered_at := old.registered_at;
    if new.terms_version is distinct from old.terms_version then
      if new.terms_version is distinct from public.terms_current() then raise exception 'terms version must be current'; end if;
      new.terms_agreed_at := now();
    else
      new.terms_agreed_at := old.terms_agreed_at;
    end if;
  end if;
  return new;
end;
$$;
drop trigger if exists profiles_guard on public.profiles;
create trigger profiles_guard before insert or update on public.profiles for each row execute function public.profiles_guard();

-- バックアップに profiles を足す（バックアップは運営者が自分でとる。有料機能にしない）
create or replace function public.admin_backup() returns jsonb
language plpgsql security definer set search_path = ops, public, auth as $$
declare out jsonb;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  out := jsonb_build_object(
    'app', 'soramemo', 'format', 1, 'created_at', now(),
    'users',           (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'email', email, 'created_at', created_at) order by created_at), '[]') from auth.users),
    'profiles',        (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.profiles t),
    'checkins',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.checkins t),
    'flights',         (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.flights t),
    'manual_flights',  (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.manual_flights t),
    'intl_flights',    (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.intl_flights t),
    'shugyo_prefs',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.shugyo_prefs t),
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
revoke all on function public.admin_backup() from public, anon;
grant execute on function public.admin_backup() to authenticated;
