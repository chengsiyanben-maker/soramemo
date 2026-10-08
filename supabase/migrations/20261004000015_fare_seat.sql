-- 運賃（ステータスの目安の計算用）と座席（搭乗券の読み取りで入る）
-- 運賃は「会社:種類」の形（例：ANA:E_STD、JAL:Y_SAVER、ANAO:VALUE）。計算の表はアプリ側にある。
alter table public.flights        add column fare text check (fare is null or fare ~ '^[A-Z]{3,4}:[A-Z0-9_]{1,16}$');
alter table public.flights        add column seat text check (seat is null or seat ~ '^[0-9]{1,3}[A-Z]$');
alter table public.manual_flights add column fare text check (fare is null or fare ~ '^[A-Z]{3,4}:[A-Z0-9_]{1,16}$');
alter table public.manual_flights add column seat text check (seat is null or seat ~ '^[0-9]{1,3}[A-Z]$');

-- フライトそのもの（空港・時刻・距離）は書き換えられないまま、運賃と座席だけを本人が設定できる
create or replace function public.set_flight_details(p_flight_id bigint, p_fare text, p_seat text) returns void
language plpgsql security definer set search_path = public as $$
begin
  update public.flights set fare = p_fare, seat = p_seat where id = p_flight_id and user_id = auth.uid();
  if not found then raise exception 'flight not found'; end if;
end;
$$;
revoke all on function public.set_flight_details(bigint, text, text) from public, anon;
grant execute on function public.set_flight_details(bigint, text, text) to authenticated;

-- 記録帳の運賃も、あとから本人が変えられるようにする（変えられるのは運賃・座席・航空会社だけ）
create policy "update own manual" on public.manual_flights for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
revoke update on public.manual_flights from authenticated;
grant update (fare, seat, airline) on public.manual_flights to authenticated;
