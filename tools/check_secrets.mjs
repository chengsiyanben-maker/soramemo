// 秘密の文字列とログの確かめ（CI の「テスト」で流す。依存なし）
//   1. 配る側（src・web・ios-app）とサーバーの関数・道具・移行に、秘密の文字列が直書きされていないか
//      service_role の鍵（JWT の role）・Supabase の秘密の鍵（sb_secret_）・Stripe の鍵（sk_live_／sk_test_／rk_live_／whsec_）・
//      秘密鍵（-----BEGIN ... PRIVATE KEY-----）・GitHub の鍵（ghp_／github_pat_）・ODPT の鍵の直書き（consumerKey=値）
//      ※ anon の鍵は配ってよい鍵なので数えない
//   2. サーバーの関数（supabase/functions）のログ（console.*）に、位置・メール・鍵・通知の宛先などを出していないか
//      文字列の中の言葉は数えず、出している値の名前だけを見る
//   使い方：node tools/check_secrets.mjs        （見つかれば一覧を出して 1 で終わる）
//           node tools/check_secrets.mjs --self-test
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SCAN_DIRS = ['src', 'web', 'ios-app', 'supabase/functions', 'supabase/migrations', 'tools', 'tests'];
const SKIP_DIR = /(^|\/)(node_modules|\.git|dist|build|Pods|DerivedData|fonts|play)(\/|$)/;
const EXT = /\.(html?|js|mjs|cjs|ts|tsx|json|sql|py|swift|plist|ya?ml|env|txt|md|sh)$/i;
const SELF = path.relative(ROOT, new URL(import.meta.url).pathname);

function b64json(s) {
  try { return JSON.parse(Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8')); } catch { return null; }
}

// 1. 秘密の文字列
export function findSecrets(text) {
  const hits = [];
  for (const m of text.matchAll(/eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]{10,}/g)) {
    const p = b64json(m[1]);
    if (p && p.role && p.role !== 'anon') hits.push(`JWT の鍵（role = ${p.role}）`);
  }
  const pats = [
    [/\bsb_secret_[A-Za-z0-9_-]{10,}/, 'Supabase の秘密の鍵（sb_secret_）'],
    [/\b(sk|rk)_live_[A-Za-z0-9]{10,}/, 'Stripe の本番の鍵'],
    [/\bsk_test_[A-Za-z0-9]{10,}/, 'Stripe の試しの鍵'],
    [/\bwhsec_[A-Za-z0-9]{10,}/, 'Stripe の Webhook の鍵'],
    [/-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/, '秘密鍵'],
    [/\b(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})/, 'GitHub の鍵'],
    [/consumerKey=[0-9a-zA-Z]{16,}/, 'ODPT の鍵の直書き'],
  ];
  for (const [re, label] of pats) if (re.test(text)) hits.push(label);
  return hits;
}

// 2. ログに出す値の名前（文字列とコメントを除いてから見る）
const BAD_NAME = /\b(email|e_mail|mail|password|passwd|token|access_token|refresh_token|jwt|authorization|apikey|api_key|secret|p256dh|endpoint|lat|lon|lng|latitude|longitude|accuracy|coords|position|ip)\b/i;
function stripStrings(s) {
  return s.replace(/`(?:\\.|[^`\\])*`/g, (t) => ' ' + [...t.matchAll(/\$\{([^}]*)\}/g)].map((m) => m[1]).join(' ') + ' ')   // テンプレートの ${…} の中だけ残す
          .replace(/'(?:\\.|[^'\\])*'/g, "''").replace(/"(?:\\.|[^"\\])*"/g, '""');
}
export function findLogLeaks(text) {
  const hits = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const at = lines[i].search(/\bconsole\.(log|error|warn|info|debug)\s*\(/);
    if (at < 0) continue;
    // 括弧が閉じるまで（最大6行）
    let s = lines[i].slice(at), depth = 0, j = i, out = '';
    for (;;) {
      for (const ch of s) { out += ch; if (ch === '(') depth++; else if (ch === ')') { depth--; if (depth === 0) break; } }
      if (depth <= 0 || j - i >= 5 || j + 1 >= lines.length) break;
      s = lines[++j]; out += '\n';
    }
    const code = stripStrings(out).replace(/\bconsole\.\w+/, '');
    const m = code.match(BAD_NAME);
    if (m) hits.push({ line: i + 1, name: m[1], text: lines[i].trim().slice(0, 120) });
  }
  return hits;
}

function* walk(dir) {
  if (!fs.existsSync(dir)) return;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name), rel = path.relative(ROOT, p);
    if (SKIP_DIR.test(rel)) continue;
    if (e.isDirectory()) yield* walk(p);
    else if (EXT.test(e.name) && fs.statSync(p).size < 5_000_000) yield rel;
  }
}

function selfTest() {
  const enc = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
  const jwt = (role) => `eyJhbGciOiJIUzI1NiJ9.${enc({ iss: 'supabase', role })}.abcdefghijklmnopqrstu`;
  const cases = [
    ['anon の鍵は数えない', findSecrets(`const k = "${jwt('anon')}"`).length === 0],
    ['service_role の鍵は見つける', findSecrets(`const k = "${jwt('service_role')}"`).length === 1],
    ['Stripe の本番の鍵', findSecrets('x = "sk_live_' + 'a'.repeat(20) + '"').length === 1],
    ['秘密鍵', findSecrets('-----BEGIN PRIVATE KEY-----').length === 1],
    ['ODPT の鍵の直書き', findSecrets('?acl:consumerKey=' + 'a1'.repeat(16)).length === 1],
    ['ODPT の鍵を環境から読むのはよい', findSecrets('`?acl:consumerKey=${KEY}`').length === 0],
    ['ログの文字列の中の言葉は数えない', findLogLeaks('console.log("token の取り直し ok", key);').length === 0],
    ['ログに位置の値', findLogLeaks('console.log("pos", lat, lon);').length === 1],
    ['ログにメール', findLogLeaks('console.error(`failed ${email}`);').length === 1],
    ['複数行のログ', findLogLeaks('console.log(JSON.stringify({\n  a: 1,\n  endpoint: s.endpoint }));').length === 1],
    ['ふつうのログ', findLogLeaks('console.log(JSON.stringify({ ev: "checkin_ms", total: Date.now() - t0 }));').length === 0],
  ];
  let bad = 0;
  for (const [label, ok] of cases) { console.log((ok ? 'OK ' : 'NG ') + label); if (!ok) bad++; }
  process.exit(bad ? 1 : 0);
}

if (process.argv.includes('--self-test')) selfTest();
else {
  const problems = [];
  for (const d of SCAN_DIRS) for (const rel of walk(path.join(ROOT, d))) {
    if (rel === SELF) continue;
    const text = fs.readFileSync(path.join(ROOT, rel), 'utf8');
    for (const h of findSecrets(text)) problems.push(`秘密の文字列：${rel}：${h}`);
    if (rel.startsWith('supabase/functions/') && /\.(ts|js|mjs)$/.test(rel) && !/_test\.|\.test\./.test(rel))
      for (const h of findLogLeaks(text)) problems.push(`ログ：${rel}:${h.line}：「${h.name}」を出している … ${h.text}`);
  }
  if (problems.length) { console.log(problems.join('\n')); console.log(`\n${problems.length} 件。直すか、出してよい値なら名前を変える`); process.exit(1); }
  console.log('秘密の文字列・ログ：問題なし');
}
