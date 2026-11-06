-- エアライン経営 co-v3：ブロック買い取りで払った額（paid_amount）を残し、退会のときの返金をその額から計算する（関数だけ。表・RLS・権限は変えない）
--   列 paid_amount はデータ担当が 20261105000149 で足したもの。これまでは空のままだった
--   co3_cs_pay_block：払うときに、その月に払った額を paid_amount に書く
--   co3_leave_settle：返金＝払った額 × 月の残りの割合。払った額がない行（前からある行）は、前のとおり「いまの収益 × 5日分」から
--   影響：経営だけ（チェックインの表・関数は触らない）。満足度などの数字は変えない

-- ブロック買い取りの代金を払う（5日分）。払えなければ false
create or replace function public.co3_cs_pay_block(p_id bigint) returns boolean
language plpgsql security definer set search_path = public as $$
declare s record; amt numeric;
begin
  select * into s from co3_codeshares where id = p_id;
  amt := ceil(co3_op_revenue(s.op_id, s.route_key) * 5);
  update companies set cash = cash - amt where user_id = s.seller_id and cash >= amt;
  if not found then return false; end if;
  update companies set cash = cash + amt where user_id = s.op_id;
  update co3_codeshares set paid_month = date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date, paid_amount = amt::bigint where id = p_id;
  return true;
end;
$$;
revoke all on function public.co3_cs_pay_block(bigint) from public, anon, authenticated;

create or replace function public.co3_leave_settle(p_uid uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  s record; i record; m date := date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date;
  partner uuid; back bigint; aid bigint; aname text; was_leader boolean; nl uuid;
  n_cs int := 0; refunds jsonb := '{}'::jsonb; n_refund bigint := 0; n_inv int := 0; n_inv_back bigint := 0;
begin
  if p_uid is null then raise exception 'no user'; end if;
  if not exists (select 1 from companies where user_id = p_uid) then return jsonb_build_object('company', false); end if;

  -- 0. 相手の会社の稼ぎを先に締める
  for partner in
    select distinct x from (
      select case when op_id = p_uid then seller_id else op_id end as x from co3_codeshares where p_uid in (op_id, seller_id) and status = 'active'
      union select case when investor = p_uid then target else investor end from co3_invest where p_uid in (investor, target) and status = 'active'
    ) z where x is not null
  loop
    perform co_settle(partner);
  end loop;

  -- 1. 出資（共同運航を終える前の、いまの会社の価値で返す）
  for i in select * from co3_invest where p_uid in (investor, target) and status in ('offer', 'active') for update loop
    if i.status = 'offer' then
      update co3_invest set status = 'declined', closed_at = now() where id = i.id;
      n_inv := n_inv + 1;
      continue;
    end if;
    if i.target = p_uid then
      back := greatest(i.amount, floor(co_value(p_uid) * i.pct))::bigint;
      update companies set cash = cash + back where user_id = i.investor;
      update co3_invest set status = 'withdrawn', closed_at = now(), returned = back where id = i.id;
      perform co3_leave_news(i.investor, 'leave-inv-' || i.id, '出資していた会社が退会し、出資を引き上げました', '戻ったお金 ' || back);
      n_inv_back := n_inv_back + back;
    else
      update co3_invest set status = 'withdrawn', closed_at = now(), returned = 0 where id = i.id;
      perform co3_leave_news(i.target, 'leave-inv-' || i.id, '出資していた会社が退会し、出資の受け渡しが終わりました', '受けたお金はそのまま会社のもの');
    end if;
    n_inv := n_inv + 1;
  end loop;

  -- 2. 共同運航：先に返金の額をすべて決めて払う（ほかの共同運航を終えると運航会社の収益が変わるため）
  for s in select * from co3_codeshares where op_id = p_uid and status = 'active' and kind = 'block' and paid_month = m loop
    back := ceil(coalesce(s.paid_amount, co3_op_revenue(s.op_id, s.route_key) * 5) * co3.month_left_ratio())::bigint;   -- 払った額が残っていればそれから、なければ前のとおりいまの収益から
    if back > 0 then
      update companies set cash = cash + back where user_id = s.seller_id;
      refunds := refunds || jsonb_build_object(s.id::text, back);
      n_refund := n_refund + back;
    end if;
  end loop;
  for s in select * from co3_codeshares where p_uid in (op_id, seller_id) and status <> 'ended' for update loop
    partner := case when s.op_id = p_uid then s.seller_id else s.op_id end;
    back := coalesce((refunds ->> s.id::text)::bigint, 0);
    update co3_codeshares set status = 'ended', ended_at = now() where id = s.id;
    if s.status = 'active' then
      perform co3_leave_news(partner, 'leave-cs-' || s.id,
        '共同運航の相手の会社が退会し、' || co3_route_name(s.route_key) || 'の共同運航が終わりました',
        case when back > 0 then '今月のブロック買い取りの残り ' || back || ' を返金' else '取り分・倍率はきょうまでで締めました' end);
    end if;
    n_cs := n_cs + 1;
  end loop;

  -- 3. アライアンス
  select a.id, a.name, a.leader = p_uid into aid, aname, was_leader
    from co3_alliance_members mm join co3_alliances a on a.id = mm.alliance_id where mm.user_id = p_uid;
  if aid is not null then
    perform co3_ally_out(p_uid);
    if was_leader then
      select leader into nl from co3_alliances where id = aid;
      if nl is not null then
        perform co3_leave_news(nl, 'leave-ally-' || aid || '-' || to_char(now(), 'YYYYMMDDHH24MISS'),
          'アライアンス「' || aname || '」のリーダーを引き継ぎました', '前のリーダーの会社が退会したため');
      end if;
    end if;
  end if;

  return jsonb_build_object('company', true, 'codeshares', n_cs, 'refund', n_refund, 'invest', n_inv, 'invest_back', n_inv_back,
                            'alliance', aid, 'new_leader', case when was_leader then nl is not null end);
end;
$$;
revoke all on function public.co3_leave_settle(uuid) from public, anon, authenticated;
grant execute on function public.co3_leave_settle(uuid) to service_role;
