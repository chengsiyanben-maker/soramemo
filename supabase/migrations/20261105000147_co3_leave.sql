-- エアライン経営 co-v3：退会した人がいたときの、残った人の扱い（表と外部キーは変えない。関数だけ）
--   アカウントを消す直前に、サーバー（service_role）から co3_leave_settle(消す人) を呼ぶ。そのあと auth.users を消すと、残りは cascade で消える
--   これまで：リーダーが消えるとアライアンスごと消える・出資の相手が消えると出したお金が消える・コードシェアは知らせなしで消える
--   この関数でやること（残った人が損をしないように）
--     0. 相手の会社は、先にそれまでの稼ぎを資金に入れる（共同運航の +5%・出資の受け取りがある状態で締める）
--     1. 出資：退会した人の会社に出していた人には、出した額と「いまの会社の価値 × 割合」の大きいほうを返す
--        （30日の待ちと、相手の資金で止まる決まりは使わない。退会した人の資金からは引かない＝もう消える会社なので）
--        退会した人から受けていた出資は、そのまま相手のもの（返さない）。毎日の受け渡しが止まる。どちらも相手に知らせる
--        まだ認めていない申し込みは、断ったことにする（お金は動いていない）
--     2. 共同運航：すべて終わりにする。退会した人が運航会社で、今月のブロック買い取りを払っていた販売会社には、
--        今日を含む今月の残りの日数のぶんを返す（いまの収益の5日分 × 残りの日数 ÷ 月の日数。切り上げ。払った額は表に残っていないため）。相手に知らせる
--     3. アライアンス：いままでの「抜ける」と同じ（co3_ally_out）。リーダーなら会社の価値がいちばん高い仲間に引き継ぐ。
--        ひとりだけなら消える。新しいリーダーに知らせる
--   知らせ（ニュース）には退会した人の会社名を書かない（消えた人の名前を残さないため）
--   ニュースの種類は 'partner'。表の決まり（co3_news_kind_check）に足すのはデータ担当に頼む。足されるまでは 'event' で書く
--   ランキング・シーズン・月の表彰・中古機・発着枠は、退会した人の行が消えるだけで、残った人は損をしない（この関数では触らない）

create or replace function public.co3_leave_news(p_uid uuid, p_ref text, p_title text, p_meta text) returns void
language plpgsql security definer set search_path = public as $$
begin
  begin
    perform co3_news_add(p_uid, 'partner', p_ref, p_title, p_meta);
  exception when check_violation then
    perform co3_news_add(p_uid, 'event', p_ref, p_title, p_meta);
  end;
end;
$$;
revoke all on function public.co3_leave_news(uuid, text, text, text) from public, anon, authenticated;

-- 今月の残りの日数の割合（今日を含む。日本時間）
create or replace function co3.month_left_ratio() returns numeric
language sql stable as $$
  with t as (select (now() at time zone 'Asia/Tokyo')::date as d)
  select ((date_trunc('month', d) + interval '1 month')::date - d)::numeric
       / ((date_trunc('month', d) + interval '1 month')::date - date_trunc('month', d)::date)
    from t
$$;
revoke all on function co3.month_left_ratio() from public, anon, authenticated;

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
    back := ceil(co3_op_revenue(s.op_id, s.route_key) * 5 * co3.month_left_ratio())::bigint;
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
