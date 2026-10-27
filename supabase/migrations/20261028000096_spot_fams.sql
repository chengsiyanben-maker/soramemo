-- 撮影の知らせを、撮る人の「表示する機体」と同じ選び方でも出せるようにする（10-28）
--   spot_fams：機種のまとまり（777・787・767・747・737・A350・A330・A380・A320・small・other）
--   spot_livs：1機ずつ選んだ特別塗装機の名前（30まで）
-- 表の守りは今のまま：push_subs は RLS を有効にしたうえで、public・anon・authenticated からはすべて取り上げている。
--   書くのは push-subscribe、読むのは airport-traffic（どちらも service_role）だけ
alter table public.push_subs add column if not exists spot_fams text[] not null default '{}';
alter table public.push_subs add column if not exists spot_livs text[] not null default '{}';
alter table public.push_subs drop constraint if exists push_subs_spot_sel_check;
alter table public.push_subs add constraint push_subs_spot_sel_check check (
  cardinality(spot_fams) <= 11
  and spot_fams <@ array['777', '787', '767', '747', '737', 'A350', 'A330', 'A380', 'A320', 'small', 'other']::text[]
  and cardinality(spot_livs) <= 30 and length(array_to_string(spot_livs, '|')) <= 2000);
alter table public.push_subs enable row level security;
revoke all on public.push_subs from public, anon, authenticated;
