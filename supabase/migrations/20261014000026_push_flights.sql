-- スマホへの通知：空港のほかに、「この便に乗る」で選んだ便（便名@運航日）も宛先に選べるようにする
alter table public.push_subs add column if not exists flights text[] not null default '{}';
alter table public.push_subs drop constraint if exists push_subs_flights_check;
alter table public.push_subs add constraint push_subs_flights_check check (cardinality(flights) <= 5);
