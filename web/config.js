// サーバー（Supabase）の設定。空のままなら、サーバーを使わず端末の中だけで動く。
// Supabase の Project Settings → API の「Project URL」と「anon public」キーを入れる。
// anon キーは公開して問題ない種類のキー。service_role キーは絶対に入れない。
// turnstileSiteKey：ログインのロボット除け（Cloudflare Turnstile）の公開鍵。Supabase の Attack Protection で CAPTCHA を有効にしたときに入れる
// gameReleased：サーバーを使わない版で、エアライン経営を出すか（サーバー版は運営コンソールの「エアライン経営を公開する」で切り替える）
window.SORAMEMO_CONFIG = { supabaseUrl: "https://bygwdoypfrccgfjjrorc.supabase.co", supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ5Z3dkb3lwZnJjY2dmampyb3JjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTExMTMzNTgsImV4cCI6MjEwNjY4OTM1OH0.QuJOfafOAMCS3OD4vkmC1j6xEsWs-4Md64BgOLmsoAw", turnstileSiteKey: "0x4AAAAAAFReuLB8fZpkt9ez", gameReleased: false };
