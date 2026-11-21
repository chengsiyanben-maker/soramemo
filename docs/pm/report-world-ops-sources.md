# 海外の空港の止まり具合（地上待機など）の元を調べた報告

担当：データ（data）　ブランチ：data/world-ops-sources　調べた日：2026-11-14（土）
PM の指示：11/14 21時10分（本人「ヨーロッパとか日本から就航してる空港も欲しいね」）。今回は調べて案まで。取り込みのコード・表は作っていない。画面はあとでデザイン担当。

## 1. まとめ（先に結論）
- **すぐ使えて効き目が大きいのはアメリカの FAA「NAS Status」だけ**。地上待機（Ground Stop）・出発の間引き（Ground Delay Program）・閉鎖・15分以上の出発／到着の遅れ・除氷を、空港ごとに XML で出している（1分ごとに更新、登録も鍵も要らない）。11/14 朝の全米の地上待機は、これを2分ごとに読んでいれば拾えた
- **アジアは「空港ごとの止まり具合」の公式の元はなく、空港の便の一覧（運航状況）を数えて代わりにする**形になる。仁川（韓国の公共データポータル）と台湾（TDX）は公式・自由に使える API があるが、どちらも旅そらのアカウントで登録と鍵が要る。香港は前の日の分だけなので、いまの止まり具合には使えない
- **ヨーロッパは、アプリが使える公開の元が見つからなかった**。EUROCONTROL の公開の画面（NOP Public Portal）は登録してから見る画面で、機械で読む口がなく、再利用の条件も書かれていない。機械で読める B2B は管制・航空会社・空港など運航に関わる組織だけ。→「使わない」
- 中国・東南アジア・中東・オセアニアも、公開の公式の元は見つからなかった → 「使わない」。代わりに、**私たちがすでに持っている JAL・ANA の国際線の欠航・遅れ（ODPT）を海外の空港ごとに数える**案（外へ新しく問い合わせない）

## 2. 日本から直行便のある海外の空港の一覧
- リポジトリには「就航先の一覧」がない。world_airports.ts は世界の空港の位置と時間帯の表（OpenFlights、ODbL）で、就航しているかは分からない。海外の便の取り込みは2つ：
  - 時刻表 flight_schedule（ODPT、JAL・ANA だけ。国際線の海外側の時刻は world_airports.ts の時間帯で読んでいる）
  - airport-foreign（日本の空港の近くの海外の会社の機体＝adsb.lol、経路＝adsb.im の推定）
- 本当の一覧は、本人に読むだけの SQL **docs/pm/world-destinations.sql** を流してもらって作る（これから7日の JAL・ANA の便で、片方が日本の空港表にないものを空港ごとに数える。索引 flight_schedule_std で7日分だけ引く・20秒で止まる。手元の Postgres 16 の作り物のデータで流れることを確かめた）。海外の会社だけが飛ぶ空港は入らない
- 下は、表ができるまでの**見込み**（私の知っている範囲。確かめていない）：
  - アメリカ（FAA の対象）：ホノルル・コナ・グアム（米国の空港なので FAA）・ロサンゼルス・サンフランシスコ・サンノゼ・シアトル・サンディエゴ・ニューヨーク（JFK・ニューアーク）・ボストン・ワシントン・シカゴ・ダラス・ヒューストン・アトランタ・ミネアポリス
  - カナダ・メキシコ：バンクーバー・トロント・メキシコシティ
  - ヨーロッパ：ロンドン・パリ・フランクフルト・ミュンヘン・ヘルシンキ・アムステルダム・イスタンブール・ローマ・ミラノ・チューリッヒ・ウィーン・コペンハーゲン・マドリード・ブリュッセル・ワルシャワ
  - 中東：ドバイ・ドーハ・アブダビ
  - 韓国・台湾・中国・香港・マカオ・モンゴル：仁川・金浦・釜山・桃園・松山・高雄・台中・香港・マカオ・北京（首都・大興）・上海（浦東・虹橋）・広州・深圳・大連・青島ほか・ウランバートル
  - 東南アジア・南アジア：バンコク（2つ）・シンガポール・クアラルンプール・ジャカルタ・デンパサール・マニラ・セブ・ホーチミン・ハノイ・ダナン・デリー・ムンバイ・ベンガルール
  - オセアニア：シドニー・メルボルン・ブリスベン・ケアンズ・オークランド・サイパン

## 3. 元ごとの確かめた結果（外部データの確認表の形）
| 元 | 取れる中身 | 更新 | 取り方 | 規約・使ってよいか | 判定 |
|---|---|---|---|---|---|
| **FAA NAS Status**（アメリカ全土＋ハワイ・グアム） | 地上待機（延長の見込みつき）・出発の間引き（平均の遅れ）・閉鎖（理由・再開の時刻）・15分以上の出発／到着の遅れ（増えているか）・除氷・空域の流れの制限・その日の見込み | 1分ごと（利用者の手引き） | 公開の XML：https://nasstatus.faa.gov/api/airport-status-information （根は AIRPORT_STATUS_INFORMATION、Update_Time、Delay_type ごとの一覧。閉鎖は ARPT・Reason・Start・Reopen）。登録・鍵なし | サイトに個別の利用規約の文は見つからなかった（手引きにもなし。連絡先 fly-faa@faa.gov）。米国政府の職員が作った著作物は米国で著作権がない（17 U.S.C. §105）のが一般の決まり。FAA のデータの免責（https://www.faa.gov/air_traffic/flight_info/aeronav/FAA_DATA_DISCLAIMER/ ）は「第三者が手を加えた後の正しさは保証しない・責任を負わない」。→ 出典「FAA NAS Status」を書き、「運航に使えない・遅れることがある」と書けば使える見込み | **使う（第一候補）** |
| FAA Airport Status Web Service（services.faa.gov） | 空港ごとの状態 | — | data.gov の記載は 2018 年が最後の更新、ライセンス「不明」 | 止まっている見込み | 使わない |
| FAA NOTAM API | NOTAM（閉鎖・滑走路の閉鎖） | — | api.faa.gov で client_id・client_secret の登録が要る。古い仕組みで NMS へ移る途中 | 規約は未読 | 後回し（閉鎖は NAS Status に出る） |
| **EUROCONTROL NOP Public Portal**（ヨーロッパ） | 流れの制限（規制）の一覧・管制区ごとの遅れの色・ネットワークのお知らせ | — | 自分で登録してから見る画面。API・RSS はなし（手引き） | 再利用・自動で読むことの条件が書かれていない（手引き・ログインのページ・サイトの「プライバシーと利用条件」・免責のページのどれにも見つからず「© EUROCONTROL」だけ） | **使わない**（画面を自動で読むしかない・条件不明） |
| EUROCONTROL NM B2B | 規制・便ごとの情報 | すぐ | 証明書（PKI）と契約。管制・航空会社・空港・飛行計画の会社など運航に関わる組織だけ | アプリの作り手の枠はない | **使わない** |
| **仁川国際空港公社**（韓国の公共データポータル data.go.kr） | 「航空機運航現況 詳細照会」：便名・共同運航・予定と変わった時刻・出発／到着の空港・ゲート・**機体の登録記号**・駐機場・**運航の状態**（状態の値の一覧は活用ガイドにあり、未読） | 即時（記載） | REST（JSON／XML）。登録して鍵。開発用 1日500回、運用は申請で1日10万回まで（サービスの URL と使い方の説明が要る） | 利用許諾の範囲「制限なし」。ポータルの方針（https://www.data.go.kr/ugs/selectPortalPolicyView.do 、11/14 に読んだ）の「第0類型（自由利用）」は「商用・非商用とも利用可・出典の表示は条件でない・加工可」。ただし方針のページに「制限なし」という言葉そのものはなく、第0類型にあたると読んだのは私の読み。第三者の権利を含むデータは権利者の許諾が要る、とも書いてある。出典「仁川国際空港公社（韓国 公共データポータル）」は書いておく案 | **使える見込み**（旅そらで登録） |
| 台湾 **TDX**（交通部の運輸データ） | 台湾の空港（桃園・松山・高雄など）の便の動き（FIDS）：予定・見込み・実際の出発／到着。台湾から出る便は出発側だけ | 記載が不明確 | 会員登録して API キー。無料 | 政府資料開放授權條款 1.0（出典を書けば商用も可の政府のライセンス） | **使える見込み**（旅そらで登録） |
| 香港空港管理局（DATA.GOV.HK） | 香港の便の一覧（状態つき） | **前の日まで** | JSON（/flights/past） | 商用も無料で再利用可。出典と権利者（空港管理局・政府・DATA.GOV.HK）を書く・免責 | いまの止まり具合には**使わない**（前の日の欠航を数えるだけなら可） |
| Airservices Australia | 出発の間引き（シドニーなど） | — | 運航に関わる組織用の CDM の画面だけ（見つかった公開の資料は説明と月報） | — | 使わない |
| 中国（民航局）・東南アジア・中東 | 公開の公式の API は見つからなかった | — | — | 有料の民間の API（Variflight・FlightAware など）は使わない | 使わない |
| **JAL・ANA の国際線（ODPT、今あるもの）** | 海外の空港を発着する JAL・ANA の便の欠航・遅れ | 今の odpt-status（5分ごと） | 今の取り込みのまま。外へ新しく問い合わせない | ODPT の規約の範囲で今と同じ使い方 | **使う（第二候補）** |

読めなかったもの：nasstatus.faa.gov の XML の全部の項目（11/14 に開いたときは閉鎖の項目だけで、Update_Time が 2026-10-26 と出た。取得の道具のためた答えの可能性があるので、本人のブラウザで開いて今の時刻が出るか確かめたい）・FAA のサイトの「Disclaimer Statement」の本文・data.go.kr の活用ガイド（方針のページは 11/14 の2回目の回で読んだ）・TDX の FIDS の項目表・EUROCONTROL の再利用の条件。

## 4. どう出すかの案（効き目の大きい順）
1. **アメリカの止まり具合（FAA）**　手間：小　回数：2分に1回（1日720回、1回数KB〜数十KB）
   - 新しい毎分の処理（または odpt-status の中）で XML を読み、就航先の空港（上の一覧のアメリカの分）だけ残す。FAA の空港の記号はアメリカの大きな空港では IATA と同じ（HNL・GUM・LAX など）
   - 出す所：運用タブの海外の便に「アメリカ：ロサンゼルスで地上待機中（FAA・○時まで）」の札／乗る便の通知（決定事項どおり、1つの便の1つの通知に1行足す形。「到着地で地上待機中」）／空港のお知らせ（羽田・成田の「アメリカ行きの便に影響のおそれ」）
   - 持ち方：表 world_airport_status（iata・source・kind（ground_stop・gdp・closure・delay・deicing）・reason・starts・ends・avg_delay・fetched_at）を移行と RLS（誰でも select、書くのは service_role）で。終わったものは数日で消す（航路・機体の記録ではない）。影響はチェックイン（運用・通知）。経営は使わない（収益は日本の実際の便数のまま）
2. **海外の空港ごとの欠航・遅れ（今ある JAL・ANA の国際線から）**　手間：小　回数：外へは0
   - flight_schedule と odpt-status の結果を、海外の空港ごとに「今日の欠航 ○便・30分以上の遅れ ○便」に数える関数（索引 (dep, std)・(arr, std) は 165 で入っている）。全地域に効くが、JAL・ANA の便だけで、理由（地上待機か天気か）は分からない
3. **仁川・台湾の空港の便の一覧**　手間：中（旅そらで登録・鍵・申請）　回数：仁川は5分に1回で1日288回（開発用の500回に収まる。運用の申請もできる）、台湾も同じくらい
   - 空港ごとに「欠航の割合・平均の遅れ」に数えて「仁川で欠航が多い（○便）」と出す。仁川は登録記号も返すので、撮る人用・運用予想にも使える（別の話）
4. ヨーロッパ：今は出さない。どうしても欲しければ EUROCONTROL（nop.office@eurocontrol.int）に、アプリでの再利用の条件を旅そらのアカウントから問い合わせる案（文はあとで用意できる）

## 5. 本人に決めてほしいこと
1. 案1（FAA）を作ってよいか。作るなら、出す所（運用タブの札・乗る便の通知・羽田／成田のお知らせ）のどれからか。画面はデザイン担当の案を先に
2. 案2（今ある国際線の欠航を海外の空港ごとに数える）も一緒に作るか
3. 仁川・台湾の API の登録を旅そらのアカウントでするか（本人の手が要る。鍵はコードに書かず Supabase の秘密の値に入れる）
4. ヨーロッパを EUROCONTROL に問い合わせるか
5. docs/pm/world-destinations.sql を流して、就航先の表を貼ってもらえるか（案1・2の対象を決めるのに使う）
6. 本人のブラウザで https://nasstatus.faa.gov/api/airport-status-information を開き、Update_Time が今の時刻か見てもらえるか

## 出典（11/14 に開いたもの）
- FAA NAS Status 利用者の手引き https://nasstatus-alpha.faa.gov/static/media/NASStatusUserGuide.cccc6d48.pdf
- FAA NAS Status の XML https://nasstatus.faa.gov/api/airport-status-information
- FAA データの免責 https://www.faa.gov/air_traffic/flight_info/aeronav/FAA_DATA_DISCLAIMER/
- data.gov の Airport Status Web Service https://catalog.data.gov/dataset/airport-status-web-service
- FAA NOTAM API の説明（apis.io） https://apis.io/apis/faa/faa-notam-api/
- EUROCONTROL NOP Public Portal 利用者の手引き https://www.nm.eurocontrol.int/HELP_PUBLIC/pdf/NOP%20Public%20Portal%20-%20User%20Guide.pdf ・ログインの説明 https://www.nm.eurocontrol.int/HELP/Login_to_the_Public_Portal.html
- EUROCONTROL NM B2B https://www.eurocontrol.int/service/network-manager-business-business-b2b-web-services ・サイトの利用条件 https://www.eurocontrol.int/info/privacy-and-website-terms-use ・免責 https://www.eurocontrol.int/info/disclaimers
- 韓国 公共データポータルの方針 https://www.data.go.kr/ugs/selectPortalPolicyView.do
- 仁川 航空機運航現況 詳細照会 https://www.data.go.kr/data/15140153/openapi.do （ほか 15114085・15095069 は時刻表・月の統計で止まり具合には使わない）
- 台湾 TDX 空港の即時の出発便 https://data.gov.tw/en/datasets/161169 ・航空 API の注意 https://motc-ptx-api-documentation.gitbook.io/motc-ptx-api-documentation/api-zi-liao-shi-yong-zhu-yi-shi-xiang/aviation
- 香港 Flight Information https://data.gov.hk/en-data/dataset/aahk-team1-flight-info ・項目表 https://www.hongkongairport.com/iwov-resources/misc/opendata/Flight_Information_DataSpec_en.pdf ・利用条件 https://data.gov.hk/en/terms-and-conditions
- Airservices Australia ATFM https://www.airservicesaustralia.com/about-us/our-services/air-traffic-flow-management/
