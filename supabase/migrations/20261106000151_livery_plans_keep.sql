-- 特別塗装機の予定の便（livery_plans）を、時刻表（flight_schedule）が14日で消えても残す（「航路と機体の記録は消さない」）
--   これまで：livery_plans.schedule_id が flight_schedule(id) を on delete cascade で参照していて、毎晩の掃除（flight-watch-cleanup）で14日より前の時刻表と一緒に消えていた
--   これから：外部キーを外す。schedule_id はそのまま主キー（時刻表は (運航日, 便名, 出発) で上書きされ id は変わらないので、同じ便が2行になることはない）
--     時刻表が消えたあとも、便名・出発・到着・定刻・塗装名・お知らせの文は残る。実績は flight_history と (運航日＝定刻の日本時間の日付, 便名, 出発) でつなげる
--   flight_schedule は今のまま14日で消す（掃除の処理は変えない）。flight_watch・flight_alerts の外部キーも変えない
--   livery_plans_upcoming は時刻表と inner join だったのを left join にする（時刻表がなくても予定は出る。到着の定刻・実際の出発・欠航は時刻表があるときだけ）
--   RLS：いまのまま（有効・ポリシーなし・利用者からは表を直接読めない。読むのは livery_plans_upcoming だけ）
--   影響：チェックイン（特別塗装機の予定の一覧と通知）は、返す形が変わらないので影響なし。経営は使っていない
do $$
declare c record;
begin
  for c in
    select con.conname from pg_constraint con
     where con.conrelid = 'public.livery_plans'::regclass and con.contype = 'f'
       and con.confrelid = 'public.flight_schedule'::regclass
  loop
    execute format('alter table public.livery_plans drop constraint %I', c.conname);
  end loop;
end
$$;
comment on table public.livery_plans is '特別塗装機で飛ぶ予定の便（航空会社の運航情報の文から）。消さずに残す。schedule_id は flight_schedule の id（時刻表は14日で消えるので、外部キーにはしない）';

create or replace function public.livery_plans_upcoming(p_iata text default null) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', p.flight, 'dep', p.dep, 'arr', p.arr, 'std', p.std, 'sta', s.sta,
           'livery', p.livery, 'note', p.note, 'atd', s.atd, 'cancelled', coalesce(s.dep_status ~* 'cancel', false))
           order by (p_iata is not null and (p.dep = p_iata or p.arr = p_iata)) desc, p.std), '[]'::jsonb)
  from public.livery_plans p left join public.flight_schedule s on s.id = p.schedule_id
  where p.std > now() - interval '1 hour' and p.std < now() + interval '36 hours'
$$;
revoke all on function public.livery_plans_upcoming(text) from public;
grant execute on function public.livery_plans_upcoming(text) to anon, authenticated;
