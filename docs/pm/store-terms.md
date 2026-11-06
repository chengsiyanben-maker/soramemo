# ストアに出す前の外部データの利用条件の見直し（2026年11月6日・データ担当）

前提：1月上旬に iOS・Android のストアで配る（Capacitor で今の Web を包む）。無料（今は課金なし）、アーリーアクセスで数百人。
もとにしたもの：Project の「そらメモ_外部データの利用規約の確認表（11-04）」（リポジトリには同じものがない）と、main（14916e9）のコード。
コードは変えていない。

- 変えるファイル：docs/pm/store-terms.md（新）と帳面だけ
- 手順：今の使い方をコードで確かめる → 公式のページを読み直す → データごとに判定する
- 確かめ方：出典の URL と読んだ日を書く。読めなかったページは「読めなかった」と書き、前の記録のままにした

## 本人が今日中にやること（3つ、合わせて15分くらい）
1. **adsb.lol の作者にメールを送る**（info@adsb.lol）。API の説明に「本番で使うなら連絡を」とある。下の「送る文の案」をそのまま使える
2. **OpenSky をどうするか決める**：(a) ストアに出す前に OpenSky に連絡して商用の扱いを聞く、(b) 毎晩の照合を adsb.lol に置き換える（データ担当の仕事、1〜2回分）、のどちらか。おすすめは (b)（理由は下）
3. **ブラウザで2つのページを開いて、改定日が変わっていないか見る**（こちらの道具では中身が読めなかった）
   - ODPT 基本ライセンス https://developer.odpt.org/terms/data_basic_license.html （11/4 の記録は2021年6月1日改定版）
   - OpenSky 利用規約 https://opensky-network.org/about/terms-of-use

## まとめ
| データ | ストアのアプリで使ってよいか | 出典（どこに出すか） | 届け出・連絡 | だめなときの代わり |
|---|---|---|---|---|
| ODPT（JAL・ANA の時刻表・運航情報） | **よい**（営利・非営利とも可。ストアで配ることを禁じる決まりはない）。直す所あり | 今の ODPT_CREDIT（データを出す所）＋利用規約の11節。**データの時刻（dc:date）を出していない**のは直す | 届け出は要らない（11/4 の記録）。アクセスの鍵はサーバーにだけ置いている（アプリには入っていない＝今のままでよい） | なし（JAL・ANA の運航情報はここだけ） |
| adsb.lol（機体の位置） | **よい**（無料・ODbL 1.0） | 「機体の位置：adsb.lol（ODbL）」を位置を出す所に（今ある）。アプリの「データの出典」にも | **作者への連絡が要る**（本番で使うとき） | 自宅の受信機のデータ（自分のもの）。ほかの集め手（有料）は使わない方針 |
| OpenSky（毎晩の照合） | **ストアの前に要対応**。API の説明は「研究と非商用」向け、商用は連絡が要る | 使い続けるなら OpenSky の論文を引用＋URL | 商用なら事前に連絡 | **adsb.lol の記録（reg_legs・flight_history）で照合する**（おすすめ） |
| 国土地理院の地図タイル | **よい**（その場で読み込むなら出典だけで申請不要） | 地図の上に「国土地理院」＋一覧ページへのリンク。配色を変えているので「配色を変えて表示」を足す。淡色地図をズーム5〜8で出すときは海岸線の出典も | 要らない。**地図をアプリに入れて配る・端末に保存する場合は申請が要る**（今は保存していない） | 淡色地図（ラスター）だけで描く |
| aviationweather.gov（METAR・TAF） | **よい**（米国政府の公開データ。使い方の制限は回数だけ） | 「天気：aviationweather.gov（METAR）」 | 要らない。1分100回まで・独自の User-Agent | 気象庁の空港の実況（ただし形式が違う） |
| 気象庁（台風・アメダス・防災情報XML） | **よい**（商用も可） | 「出典：気象庁ホームページ」。加工したら「加工して作成」 | 要らない。**予報を書き換えて人に出すと許可が要る**（気象業務法17条） | なし |
| AIP（経路・滑走路の決まり） | **たぶんよい（要確認）**。今は PDF を手で読んで、事実（経路の名前・決まり）だけを入れている | 「経路は AIP JAPAN をもとに作成。航法には使えません」（今ある） | SWIM の条件は**まだ読めていない**（ポータルの中にある） | 事実だけを自分の言葉で書く（今のまま）。PDF そのものは配らない |
| 特別塗装機の一覧 | **よい**（登録記号・塗装名・期間は事実） | 一覧に出典のリンク（今ある） | 要らない | 写真・ロゴ・記事の文は使わない（今のまま） |

## データごとのくわしいこと

### 1. ODPT（公共交通オープンデータ）
- 今の使い方：サーバー（odpt-status・timetable-sync・schedule-sync・airport-now）だけが取りに行く。アプリの中に ODPT の鍵はない（web/index.html の通信先は Supabase・地理院・人の確認の Cloudflare だけ）。ストアの包み直しでもこのまま
- ストア：基本ライセンスは営利・非営利とも成果物の公開を認めている（11/4 に原文で確かめた第4条7）。「ストアで配る」「無料」「数百人」はどれも条件を変えない
- 守ること（11/4 の記録から、ストアでも同じ）
  - 出典・正確さの保証なし・問い合わせ先：今の ODPT_CREDIT と利用規約の11節で満たしている
  - **データの時刻（dc:date）を画面に出していない** → ストアの前に直す（チェックイン担当への依頼。下）
  - 元データの大部分を戻せる形で第三者に出さない（第8条4）。共有画像・書き出しで時刻表を丸ごと出さない
  - 許諾が終わったらデータを消す決まり（第13条3）と「便の実績をずっと残す」の両立は、11/4 から本人の判断待ちのまま
- 今日の読み直し：ODPT の規約のページはスクリプトで描くページで、こちらの道具では本文が出なかった（2026-11-06）。11/4 に読んだ版（基本ライセンス 2021年6月1日改定、ガイドライン 2021年7月20日改定）のまま判定した
- 出典：https://developer.odpt.org/terms/data_basic_license.html 、https://developer.odpt.org/terms/data_basic_use_guideline.html 、https://developer.odpt.org/terms/center_use_rules.html （どれも 2026-11-06 は本文を読めず、2026-11-04 に読んだ記録を使った）

### 2. adsb.lol
- 今の使い方：サーバーから30秒ごとに位置を取り、航跡・全機の便（reg_legs）・滑走路の学習・運用予想（rot_pairs）に使う
- 読んだこと（2026-11-06）
  - API の説明（原文）："You can use the API for free."／"If you want to use the API for production purposes, please contact me so I do not break your application by accident."／"In the future, you will require an API key which you can get by feeding to adsb.lol."／"The license for the API as well as all data ADSB.lol makes public is ODbL."
  - 免責：データは "as is"。データの使い方が原因で第三者から請求を受けたときは、使った側が adsb.lol を補償する、とある
- ストア：使ってよい。商用・アプリを禁じる文はない
- 出典：位置を出す所に「adsb.lol（ODbL）」（今ある）。アプリの「データの出典」に「Contains information from adsb.lol, which is made available under the ODbL」を足すとよい
- ODbL の注意：adsb.lol から作ったデータベース（reg_legs・airport_tracks_all・rot_pairs など）を使った画面を公に出すときは、求められたらそのデータベース（adsb.lol 由来の部分）を ODbL で渡せるようにしておく。ODPT のデータとは混ぜずに渡せる形にする（rot_pairs は adsb.lol 由来だけで作ってある）
- 届け出：**作者への連絡**。数百人なら負荷は今と同じ（取りに行くのはサーバーだけで、人数で増えない）
- だめなとき：自宅の受信機のデータで HND 周りだけ続ける。鍵が要るようになったら、自宅の受信機から adsb.lol に送れば鍵がもらえる
- 出典の URL：https://api.adsb.lol/api/openapi.json 、https://www.adsb.lol/docs/open-data/api 、https://www.adsb.lol/docs/privacy-license （どれも 2026-11-06 に読んだ）

送る文の案（info@adsb.lol へ。英語のまま送る）：
> Hello, I run "Soramemo" (https://soramemo.jp/), a free, non-paid airport check-in app in Japan. Our server polls api.adsb.lol about every 30 seconds for aircraft around Japanese airports (one server, not per user), and we credit adsb.lol (ODbL) in the app. We plan to publish the app on the iOS/Android stores in early January for a few hundred early-access users. Please let me know if you would like us to change the polling interval or use an API key. We can also feed data from our own receiver. Thank you for running adsb.lol.

### 3. OpenSky（毎晩の照合）
- 今の使い方：verify-flights（GitHub の定期実行。Supabase からは届かないため）が、利用者の記録した便を OpenSky の記録で照合する
- 読んだこと（2026-11-06）
  - API の説明：ライブの空域情報は "research and non-commerical purposes" 向け。"If you want to retrieve live flight information for commercial purposes, please contact us"。公表物（ウェブページを含む）では論文 "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research" を引用し、URL も添える。クラウドの IP は止めることがある
  - ウィキペディアの紹介では「学術・政府の研究は無料、商用のライセンスもある」
  - 利用規約のページそのもの（opensky-network.org/about/terms-of-use）は、こちらでは開けなかった
- ストア：**無料でもストアで一般に配るアプリは「研究」ではない**。非商用と言えるかがあいまいで、将来そらメモ＋（plus-checkout がコードにある）を始めると商用になる。ストアに出す前に決める
- 代わり（おすすめ）：照合を adsb.lol の記録に置き換える。reg_legs（機体・便・日・出発・到着）と flight_history がすでにあり、OpenSky の鍵（OPENSKY_CLIENT_ID・SECRET）も要らなくなる。GitHub の定期実行も要らなくなる。データ担当の1〜2回分の仕事（照合の部品 verify_io.ts の取り先を差し替え、テストを足す）
- 使い続けるなら：OpenSky に連絡して、無料アプリの照合に使ってよいかを書面でもらう。アプリの「データの出典」に論文と URL
- 出典の URL：https://openskynetwork.github.io/opensky-api （2026-11-06 に読んだ）、https://github.com/openskynetwork/opensky-api （同）、https://en.wikipedia.org/wiki/OpenSky_Network （同）、https://opensky-network.org/about/terms-of-use （開けなかった）

### 4. 国土地理院の地図タイル
- 今の使い方：アプリが地理院のサーバーから直接読み込む。淡色地図（pale・ラスター）と、ベクトル地図（experimental_bvmap）を配色を変えて描く。サービスワーカーは地図を保存していない（保存するのは自分の画面とフォントと CDN の部品だけ）
- 読んだこと（2026-11-06）
  - Q&A Q1-12：地理院のサーバーのタイルをその場で読み込んで出すウェブサイト・ソフトウェアは、**出典を出すだけで申請不要**。出典は「国土地理院」か「地理院タイル」などと書き、地理院タイル一覧のページへリンクする
  - Q1-15：加工したら、出典とは別に加工したことを書く。国土地理院が作ったように見せない
  - 淡色地図はズーム5〜8（日本とその周り）で使うとき、VMAP0 由来の海岸線の出所も書くよう求めている。ホームの地図は minZoom 5 なので当たる
  - 最適化ベクトルタイルは「試験公開」。URL・データの作り・属性の名前が変わることがある、とある（使っている experimental_bvmap も同じく試験の扱い）
- ストア：よい。Capacitor でも「その場で読み込む」のは同じ。**地図をアプリの中に入れて配ったり、端末に保存して圏外で出したりすると申請が要る**ので、包み直しのときにそうしない
- 出典：今は「地図：国土地理院」（ホームと経営の凡例）と、リンク付きの GSI_ATTR（一部の地図）。直すと良いこと（チェックイン担当への依頼）：全部の地図で一覧ページへのリンクにそろえる・「配色を変えて表示」を足す・淡色地図を出す所に海岸線の出所を「データの出典」に足す
- 代わり：ベクトル地図が止まったら淡色地図だけで描く（コードにもう淡色地図の道がある）
- 出典の URL：https://www.gsi.go.jp/LAW/2930-qa.html 、https://maps.gsi.go.jp/development/ichiran.html 、https://github.com/gsi-cyberjapan/optimal_bvmap （どれも 2026-11-06 に読んだ）、全体の規約 https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html （今回は開いていない）

### 5. aviationweather.gov（METAR・TAF）
- 今の使い方：サーバーから毎時など（metar・wx-archive・co3-weather）
- 読んだこと（2026-11-06）："All requests are rate limited to 100 requests per minute."／"Set a custom user agent…"／大量なら1分ごと（METAR）・10分ごと（TAF）の全件ファイルを使う／過去30日まで。商用・アプリの利用を禁じる文はない（米国政府の公開データ）
- ストア：よい。人数で取りに行く回数は増えない（サーバーだけが取る）
- 出典：「天気：気象通報（METAR、aviationweather.gov）」を天気を出す所と「データの出典」に
- 出典の URL：https://aviationweather.gov/data/api/ （2026-11-06 に読んだ）

### 6. 気象庁（台風・アメダス・防災情報XML）
- 読んだこと（2026-11-06）：「ご利用上の留意事項」（平成29年3月3日）：二次利用は気象業務法の趣旨に反しない限り制限なし・商用も可。出典が気象庁ホームページであることを書く。加工したら加工したこと・編集の責任が編集者にあることを書く。予報値を変えて人に繰り返し出すのは予報業務の許可が要る（17条）。警報は気象庁だけ（23条）。地方気象台のページ（政府標準利用規約 2.0版に準拠）でも同じ書き方の例「〜を加工して作成」
- ストア：よい。経営の台風は「ゲームの中の出来事」として出し、予報として出さない（今のまま）
- 出典：「出典：気象庁ホームページ（台風の情報を加工して作成）」を、台風・アメダスを出す所と「データの出典」に
- 出典の URL：https://www.data.jma.go.jp/developer/ryuui.pdf 、https://www.data.jma.go.jp/akita/about/coment/coment.html （どちらも 2026-11-06 に読んだ）

### 7. AIP（SWIM）
- 今の使い方：AIP の PDF を本人が手で読み、経路・滑走路・夜の決まりを ops_core.js と空港の定義に入れた。SWIM からの取り込みはない
- 読んだこと（2026-11-06）：航空局の発表（令和6年12月25日）：AIS Japan は2025年2月10日に閉じ、AIP は SWIM ポータルの「閲覧」「PDF のダウンロード」「データ配信」に移った。二次利用・公開・出典の条件はこの発表にはなく、ポータル（https://top.swim.mlit.go.jp/swim/ 、スクリプトで描くページで本文が出なかった）の中の「情報サービス概要」「サービス説明書」にあるらしい（SWIM コミュニティの議事概要、令和8年5月14日）
- ストア：**たぶんよい**。経路の名前・滑走路・時間の決まりは事実で、PDF や図をそのまま配っていない。ただし「商用可・出典不要」という前の記録は AIS Japan のころのもので、SWIM の条件ではまだ確かめていない
- やること：本人が SWIM ポータルにログインして、サービス説明書の「利用の条件・二次利用」の節を読む（写真か文を貼ってもらえれば、データ担当が判定を書き直す）。急ぎではない（ストアの前までに）
- 代わり：今のとおり事実だけを自分の言葉で書き、「航法には使えません」を出す
- 出典の URL：https://www.mlit.go.jp/report/press/content/001853569.pdf 、https://www.mlit.go.jp/koku/content/002007362.pdf （どちらも 2026-11-06 に読んだ）、https://top.swim.mlit.go.jp/swim/ （本文が出なかった）

### 8. 特別塗装機の一覧
- 今の使い方：supabase/functions/_shared/liveries.ts に手で書いた一覧。出典のリンクは aviationwire.jp 31件・planespotters.net 30件・fujidream.co.jp 15件・ana.co.jp 5件 ほか（2026-11-06 に数えた）
- ストア：よい。登録記号・塗装名・期間は事実で、著作物ではない。記事の文・写真・ロゴは使っていない（今のまま）
- 注意：planespotters.net の利用規約は今回開けなかった（https://www.planespotters.net/about/termsofuse 、サイト側のエラー）。人が見て事実を書き写すのはよいが、自動で取り込むのはやめておく（今も手で書いている）。塗装名は自分の言葉で
- 出典：一覧の各行のリンク（今ある）

### 付け足し（対象の外だが、ストアの前に見ておくもの）
- adsb.im（海外の便の経路）と OpenFlights（海外の空港の位置・時間帯、ODbL）も使っている。adsb.im の条件は今回読んでいない。次の回で読む

## アプリのどこに出典を出すか（案）
- データを出すその場所に短く（今あるもの：ODPT_CREDIT・adsb.lol・地図の「国土地理院」）
- それに加えて、アプリの中に「データの出典」の一覧を1つ（設定やマイページの「このアプリについて」から開く）。ストアで配るアプリは Web の利用規約のページを開かずに使われるので、アプリの中で読めるようにする
- 画面が絡むので、作るのはデザイン担当の案を本人が見てから（データ担当はコードを変えない）

## ほかの担当への依頼
- チェックイン担当へ：①ODPT のデータを出す所に「データの時刻（dc:date）」を出す（11/4 からの依頼、ストアの前に）②地図の出典を全部の地図で一覧ページへのリンクにそろえ、「配色を変えて表示」を足す
- デザイン担当へ：アプリの中の「データの出典」の一覧の画面案（出典の文はデータ担当が用意する）

## 本人に決めてほしいこと
1. OpenSky：連絡して使い続けるか、adsb.lol に置き換えるか（おすすめは置き換え）
2. ODPT 第13条3（許諾が終わったらデータを消す）と「記録をずっと残す」の扱い（11/4 から）
3. SWIM ポータルのサービス説明書を読む日
