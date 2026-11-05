-- 利用者のプロフィール（新規登録で使う）：表示名・登録日・同意した規約とプライバシーポリシーの版と日時・使い方の答え
--   ・1人1行。アカウントができたとき（auth.users に行が入ったとき）に自動で作る。いまいる利用者の分も作る（登録日は auth.users の作成日）
--   ・本人だけが読める。本人が直せるのは表示名と使い方の答えだけ（列ごとの権限）。登録日・同意の日時はサーバーの時刻で入れる
--   ・同意は public.agree_terms(規約の版, プライバシーポリシーの版) で記録する（版は「改定日」の YYYY-MM-DD）
--   ・使い方の答え：spot（撮る）・shugyo（修行）・casual（気軽）・unanswered（未回答）。アプリの PERSONAS のキーと同じ。
--     あとでマイページから変えられる。答えた日時は答えが変わるたびに入れ直す（未回答に戻すと空にする）
--   ・アカウント削除（delete-account → auth.users の削除）で一緒に消える（on delete cascade）
--   影響：チェックイン・経営のどちらの表・関数も変えない。いまのアプリはこの表を読まない（つなぐのは画面の担当が別に行う）
create table if not exists public.user_profiles (
  user_id             uuid primary key references auth.users (id) on delete cascade,
  display_name        text check (display_name is null or (char_length(btrim(display_name)) between 1 and 20 and display_name !~ '[[:cntrl:]]')),
  created_at          timestamptz not null default now(),                -- 登録日
  terms_version       text check (terms_version is null or terms_version ~ '^\d{4}-\d{2}-\d{2}$'),
  privacy_version     text check (privacy_version is null or privacy_version ~ '^\d{4}-\d{2}-\d{2}$'),
  agreed_at           timestamptz,                                       -- 規約とプライバシーポリシーに同意した日時
  persona             text not null default 'unanswered' check (persona in ('spot', 'shugyo', 'casual', 'unanswered')),
  persona_answered_at timestamptz,
  updated_at          timestamptz not null default now(),
  check ((terms_version is null) = (agreed_at is null) and (privacy_version is null) = (agreed_at is null)),
  check ((persona = 'unanswered') = (persona_answered_at is null))
);

-- RLS：本人の行だけ読める・直せる。作る・消すのはサーバーだけ（自動で作る／アカウント削除で消える）
alter table public.user_profiles enable row level security;
revoke all on public.user_profiles from public, anon, authenticated;
grant select on public.user_profiles to authenticated;
grant update (display_name, persona) on public.user_profiles to authenticated;
drop policy if exists user_profiles_own_read on public.user_profiles;
create policy user_profiles_own_read on public.user_profiles for select to authenticated using (user_id = auth.uid());
drop policy if exists user_profiles_own_update on public.user_profiles;
create policy user_profiles_own_update on public.user_profiles for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- 時刻はサーバーが入れる：登録日は変えさせない・答えた日時は答えが変わったときだけ・更新日時はいつも
create or replace function public.user_profiles_touch() returns trigger
language plpgsql set search_path = '' as $$
begin
  if tg_op = 'UPDATE' then
    new.user_id := old.user_id;
    new.created_at := old.created_at;
    if new.persona is distinct from old.persona then
      new.persona_answered_at := case when new.persona = 'unanswered' then null else now() end;
    else
      new.persona_answered_at := old.persona_answered_at;
    end if;
    if new.display_name is not null then new.display_name := btrim(new.display_name); end if;
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists user_profiles_touch on public.user_profiles;
create trigger user_profiles_touch before update on public.user_profiles for each row execute function public.user_profiles_touch();

-- アカウントができたら、空のプロフィールを作る（未回答・同意はまだ）
create or replace function public.user_profiles_on_signup() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.user_profiles (user_id, created_at) values (new.id, coalesce(new.created_at, now())) on conflict (user_id) do nothing;
  return new;
end $$;
revoke all on function public.user_profiles_on_signup() from public, anon, authenticated;
drop trigger if exists user_profiles_on_signup on auth.users;
create trigger user_profiles_on_signup after insert on auth.users for each row execute function public.user_profiles_on_signup();

-- いまいる利用者の分（登録日は auth.users の作成日。同意は記録がないので空のまま）
insert into public.user_profiles (user_id, created_at)
select id, coalesce(created_at, now()) from auth.users
on conflict (user_id) do nothing;

-- 同意の記録：本人が、いま見せている規約とプライバシーポリシーの版（改定日）に同意した
create or replace function public.agree_terms(p_terms_version text, p_privacy_version text) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid(); r public.user_profiles;
begin
  if uid is null then raise exception 'login required'; end if;
  if coalesce(p_terms_version, '') !~ '^\d{4}-\d{2}-\d{2}$' or coalesce(p_privacy_version, '') !~ '^\d{4}-\d{2}-\d{2}$' then raise exception 'bad version'; end if;
  insert into public.user_profiles (user_id) values (uid) on conflict (user_id) do nothing;
  update public.user_profiles set terms_version = p_terms_version, privacy_version = p_privacy_version, agreed_at = now()
  where user_id = uid returning * into r;
  return jsonb_build_object('terms_version', r.terms_version, 'privacy_version', r.privacy_version, 'agreed_at', r.agreed_at);
end $$;
revoke all on function public.agree_terms(text, text) from public, anon;
grant execute on function public.agree_terms(text, text) to authenticated;
