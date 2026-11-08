-- 表示の設定（全部乗せ＋自分で隠す）をサーバーに残す表（11/8 本人の決定・チェックイン担当の仕様 11/8 16時15分）
--   ・1人1行。中身（prefs）はアプリが決める JSON の「もの」（例：{"off": {...}, "tabs": [...], "aps": [...]}）。形はアプリの定数で持ち、
--     形を変えるときは fmt を上げる（サーバーは中身の項目を見ない。大きさだけ 16KB までに抑える）
--   ・本人だけが読める・作れる・直せる・消せる（消す＝全部乗せに戻す、に使ってよい）
--   ・rev は直すたびにサーバーが1つ上げる。別の端末で先に直されていないかを、update ... where rev = 前の値 で確かめられる
--   ・suggest_shown_at：新規登録のアンケートの答えから「これを隠しますか？」を出した日時（1回だけ出すため。別の端末でも出さない）
--     入れるのは view_prefs_claim_suggest() で。いちど入ったら空に戻せない（rev・更新日時と同じくサーバーが決める）。これを入れても rev は上がらない
--   ・ログインしていないときは端末に保存（この表は使わない）
--   ・退会（delete-account → auth.users の削除）で一緒に消える（on delete cascade）
--   影響：チェックインだけ（新しい表と関数を足すだけ。いまの表・関数・ひな形の動きは変えない）。経営には影響しない
create table if not exists public.user_view_prefs (
  user_id          uuid primary key references auth.users (id) on delete cascade,
  prefs            jsonb not null default '{}'::jsonb
                   check (jsonb_typeof(prefs) = 'object' and octet_length(prefs::text) <= 16384),
  fmt              smallint not null default 1 check (fmt between 1 and 100),   -- prefs の形の版（アプリが決める）
  suggest_shown_at timestamptz,                                                 -- 「これを隠しますか？」を出した日時
  rev              integer not null default 1,                                  -- 直した回数（サーバーが上げる）
  updated_at       timestamptz not null default now()
);

-- RLS：本人の行だけ。ログインしていない人は何もできない
alter table public.user_view_prefs enable row level security;
revoke all on public.user_view_prefs from public, anon, authenticated;
grant select, delete on public.user_view_prefs to authenticated;
grant insert (user_id, prefs, fmt) on public.user_view_prefs to authenticated;
grant update (prefs, fmt) on public.user_view_prefs to authenticated;
drop policy if exists user_view_prefs_own_read on public.user_view_prefs;
create policy user_view_prefs_own_read on public.user_view_prefs for select to authenticated using (user_id = auth.uid());
drop policy if exists user_view_prefs_own_insert on public.user_view_prefs;
create policy user_view_prefs_own_insert on public.user_view_prefs for insert to authenticated with check (user_id = auth.uid());
drop policy if exists user_view_prefs_own_update on public.user_view_prefs;
create policy user_view_prefs_own_update on public.user_view_prefs for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
drop policy if exists user_view_prefs_own_delete on public.user_view_prefs;
create policy user_view_prefs_own_delete on public.user_view_prefs for delete to authenticated using (user_id = auth.uid());

-- 回数と日時はサーバーが入れる：rev は作ったとき1・直すたびに＋1、提案の日時は一度入ったら変えない
create or replace function public.user_view_prefs_touch() returns trigger
language plpgsql set search_path = '' as $$
begin
  if tg_op = 'INSERT' then
    new.rev := 1;
    new.suggest_shown_at := null;
  else
    new.user_id := old.user_id;
    if current_setting('soramemo.claim_suggest', true) = 'on' then
      -- 提案を出したことを残すだけ（中身・rev は変えない。開いている別の端末の保存をぶつからせない）
      new.prefs := old.prefs; new.fmt := old.fmt; new.rev := old.rev;
      new.suggest_shown_at := coalesce(old.suggest_shown_at, now());
    else
      new.rev := old.rev + 1;
      new.suggest_shown_at := old.suggest_shown_at;
    end if;
  end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists user_view_prefs_touch on public.user_view_prefs;
create trigger user_view_prefs_touch before insert or update on public.user_view_prefs for each row execute function public.user_view_prefs_touch();

-- 「これを隠しますか？」を出してよいか：まだ出していなければ、いま出したことにして true。もう出していれば false
--   2つの端末で同時に開いても、true になるのは1回だけ（行の鍵を取ってから見る）。行がなければ空の設定で作る
create or replace function public.view_prefs_claim_suggest() returns boolean
language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid(); n int;
begin
  if uid is null then raise exception 'login required'; end if;
  insert into public.user_view_prefs (user_id) values (uid) on conflict (user_id) do nothing;
  perform set_config('soramemo.claim_suggest', 'on', true);
  update public.user_view_prefs set suggest_shown_at = now() where user_id = uid and suggest_shown_at is null;
  get diagnostics n = row_count;
  perform set_config('soramemo.claim_suggest', 'off', true);
  return n = 1;
end $$;
revoke all on function public.view_prefs_claim_suggest() from public, anon;
grant execute on function public.view_prefs_claim_suggest() to authenticated;
