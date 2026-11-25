# 送り直しても二重にならない（画面の側）checkin/idem-cid

PM の指示 11/26 1時30分（データ担当の data/idem・PR #240・移行200 の依頼 1〜4）。画面の見た目は変えていない。

- 変えるファイル：src/index.html（印を送る所・保留・記録帳・国際線・搭乗券・引き継ぎ）・web/（組み立て直し）・tests/e2e/fake_sb.js・tests/e2e/t200.py
- 手順：押すたびに ID を作る → 関数 checkin に cid で送る・保留にも同じ ID → 記録帳と国際線は client_id つきの upsert（列がなければ前の insert）
- 確かめ方：t200 を足す・印と保留と記録帳の既存のテスト・e2e 全部・tests/ops

## 作ったもの

- **ckCid()**：UUID を1つ作る（crypto.randomUUID、なければ getRandomValues で v4 の形）
- **checkinServer**：押すたびに `p = {...p, cid}`（使い回した位置でも、押すたびに別の ID）
- **sendCheckin**：本文に `cid` を足す（ID があるときだけ）
- **enqueue**：保留に `cid` を残す。**flushQueue**：前の版で積んだ ID なしの保留にも、送る前に ID を付けて保存する（返事が届かなかったら、次も同じ ID）
- **ckSend・checkinServerWait**：返事の `again: true` は成功のまま扱う（ハンコを取り消さない。初めての演出はサーバーが false で返す）。記録の名前だけ `checkin_again` に分けた
- **idemInsert(table, rows)**：`upsert(rows, { onConflict: "user_id,client_id", ignoreDuplicates: true })`。列や索引がまだないサーバー（移行200 の前：42P10・PGRST204・42703）なら、client_id を外した前と同じ insert で入れ直す。なので画面を先に出しても壊れない
- **formCid(key, row)・formCidDone(key)**：同じ中身でもう一度押したときは同じ ID（返事が届かず押し直しても1行）。保存できたら忘れるので、そのあとに同じ便を足すのは別の記録（同じ日の往復など）
- 使った所：記録帳の「追加」（mAdd の onclick）・国際線（addIntl）・搭乗券の「日誌に追加」（data-bp-act="manual" の処理）・ローカルの記録の引き継ぎ（data-migrate の処理。1行ごとに区間と日付で ID）

### 変えた関数（src/index.html）
checkinServer・sendCheckin・ckSend・checkinServerWait・enqueue・flushQueue・mAdd の onclick・addIntl・搭乗券の data-bp-act の click 処理・data-migrate の click 処理。足した関数：ckCid・formCid・formCidDone・idemNoCol・idemInsert

## 確かめた結果

- t200（18項目）成功：押すと UUID を送る・押すたびに別／返事だけ届かない → 同じ ID で保留 → 送り直すと again で印は1つ・画面の記録も1つ・「印が確定しました」の札／前の版の保留に ID を付けて残す／前の関数（cid を無視）でも押せる／記録帳・国際線は押し直しても1行・保存できたあとはもう1行足せる／移行200 の前のサーバーでも保存できる
- t195・t196・t24・t144・t11・t13・t15・t19・t30・t193・t189・t171・t31・t47・t61・t123・t48・t44・t8・tests/ops 成功
- e2e 全部（3D の t142・t159・t160〜t168・t181・t190 を除く）：4本に分けて 144/144 成功（運営コンソールが手元にない t33・t40・t42・t46 は飛ばした）。3D は今回触っていない

## 本人（PM）に決めてほしいこと

- 修行の「乗った」（sgRecordPlan・修行担当の持ち場）も記録帳に足すので、`idemInsert("manual_flights", {...row, client_id: formCid("sg:" + p.id, row)})` にするよう修行担当に頼むか（依頼文は帳面に書いた）
- flight-suggest（PR #239）の mfInsert も記録帳に足す。#239 と #240・この枝のどちらかが先に入ったら、あとの方で mfInsert を idemInsert につなぐ（列がないときの入れ直しは idemInsert にもある）
- 反映の順：関数 checkin（#240）が先でも、この画面が先でも壊れない（古い関数は cid を無視するだけ・列がなければ ID なしで入れる）
