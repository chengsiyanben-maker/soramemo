-- 航空会社と便名
-- airline は2文字の航空会社コード（JL, NH など）か、その他を表す 'OT'。
-- 利用者はフライトを直接書き換えられないので、本人のフライトに便を設定する関数だけを用意する。

alter table public.flights
  add column airline text check (airline is null or airline ~ '^([A-Z0-9]{2}|OT)$');
alter table public.flights
  add constraint flights_flight_no_format check (flight_no is null or flight_no ~ '^[A-Z0-9]{1,8}$');

alter table public.manual_flights
  add column airline text check (airline is null or airline ~ '^([A-Z0-9]{2}|OT)$');

create or replace function public.set_flight_airline(p_flight_id bigint, p_airline text, p_flight_no text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_airline is not null and p_airline !~ '^([A-Z0-9]{2}|OT)$' then
    raise exception 'invalid airline';
  end if;
  if p_flight_no is not null and p_flight_no !~ '^[A-Z0-9]{1,8}$' then
    raise exception 'invalid flight number';
  end if;
  update public.flights
     set airline   = p_airline,
         flight_no = case when p_airline is null then null else p_flight_no end,
         -- 運航確認済み・運航データなし は照合の結果なので、ここでは変えない
         status    = case when status in ('provisional', 'with_flight_no')
                          then case when p_airline is null then 'provisional' else 'with_flight_no' end
                          else status end
   where id = p_flight_id and user_id = auth.uid();
  if not found then
    raise exception 'flight not found';
  end if;
end;
$$;

revoke all on function public.set_flight_airline(bigint, text, text) from public, anon;
grant execute on function public.set_flight_airline(bigint, text, text) to authenticated;
