# ブラウザでの動作テストをまとめて実行する
#   pip install playwright && playwright install chromium
#   python3 tests/e2e/run_all.py
# サーバー版のテストは、偽のサーバー（fake_sb.js / fake_admin.js）を使う。本物の Supabase には接続しない。
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# サーバー版のテスト用：偽のサーバーを指す config.js を、作業用フォルダに置く
import shutil
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
shutil.copy(os.path.join(HERE, '..', '..', 'ops-console', 'index.html'), os.path.join(WORK, 'admin_test.html'))   # 運営コンソール（公開しない）
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
TESTS = sorted(f for f in os.listdir(HERE) if f.startswith('t') and f.endswith('.py') and f != 'run_all.py')
if len(sys.argv) > 1: TESTS = [t for t in TESTS if any(t.startswith(a) for a in sys.argv[1:])]   # 例: run_all.py t1 t2
fails = []
for t in TESTS:
    r = subprocess.run([sys.executable, os.path.join(HERE, t)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
    out = (r.stdout + r.stderr).strip().splitlines()
    last = out[-1] if out else ''
    ok = r.returncode == 0 and ('[]' in last or 'errors []' in last or 'errors: []' in last)
    print(('OK   ' if ok else 'FAIL ') + t)
    if not ok: fails.append(t); print('\n'.join('     ' + l for l in out[-8:]))
print(f'\n{len(TESTS) - len(fails)} / {len(TESTS)} 件成功')
sys.exit(1 if fails else 0)
