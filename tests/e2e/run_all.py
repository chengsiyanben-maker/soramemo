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
ADMIN = os.path.join(HERE, '..', '..', 'ops-console', 'index.html')   # 運営コンソール（公開しない）。手元にないときは、運営コンソールのテストを飛ばす
if os.path.exists(ADMIN): shutil.copy(ADMIN, os.path.join(WORK, 'admin_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
TESTS = sorted(f for f in os.listdir(HERE) if f.startswith('t') and f.endswith('.py') and f != 'run_all.py')
if not os.path.exists(ADMIN):
    skip = [t for t in TESTS if 'admin_test' in open(os.path.join(HERE, t), encoding='utf-8').read()]
    if skip: print('運営コンソールが手元にないので飛ばす:', ' '.join(skip))
    TESTS = [t for t in TESTS if t not in skip]
if len(sys.argv) > 1: TESTS = [t for t in TESTS if any(t.startswith(a) for a in sys.argv[1:])]   # 例: run_all.py t1 t2
fails = []
# 1本の上限（秒）。ふつうは 240 秒。3D の細かい形のテスト（t168）は画面のないソフトの描画で 850〜1000 秒かかるので長くする（11/24 PM の依頼）
LIMIT = {'t168.py': 1800, 't190.py': 900, 't196.py': 600}  # t190（3D を自由に動かす）は単独で約265秒・同時に流すと240秒を超える
def run1(t):
    """1本流す。(成功か, 最後の8行)"""
    try: r = subprocess.run([sys.executable, os.path.join(HERE, t)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=LIMIT.get(t, 240))
    except subprocess.TimeoutExpired:   # 上限を超えたら、止めずに「失敗」として次へ進む
        return False, [f'（{LIMIT.get(t, 240)} 秒の上限を超えた）']
    out = (r.stdout + r.stderr).strip().splitlines()
    last = out[-1] if out else ''
    ok = r.returncode == 0 and ('[]' in last or 'errors []' in last or 'errors: []' in last or last == '全部成功')   # 「全部成功」で終わるテスト（t165・t166 など）も成功に数える
    return ok, out[-8:]
for t in TESTS:
    ok, tail = run1(t)
    print(('OK   ' if ok else 'FAIL ') + t)
    if not ok: fails.append(t); print('\n'.join('     ' + l for l in tail))
# 落ちたテストは最後に1本ずつ流し直す（11/26 test-steady）。2回目で通ったものは「不安定」として別に書き出し、失敗の数からは外す。
#   2回とも落ちたものだけが本当の失敗。流し直さないときは SORAMEMO_NO_RETRY=1
flaky = []
if fails and os.environ.get('SORAMEMO_NO_RETRY') != '1':
    print(f'\n落ちた {len(fails)} 本を1本ずつ流し直す')
    for t in list(fails):
        ok, tail = run1(t)
        print(('2回目で通った ' if ok else '2回目も落ちた ') + t)
        if ok: fails.remove(t); flaky.append(t)
        else: print('\n'.join('     ' + l for l in tail))
    if flaky:
        open(os.path.join(WORK, 'flaky.txt'), 'w', encoding='utf-8').write('\n'.join(flaky) + '\n')
        print('2回目で通った（不安定）: ' + ' '.join(flaky) + f'（{os.path.join(WORK, "flaky.txt")} にも書いた）')
print(f'\n{len(TESTS) - len(fails)} / {len(TESTS)} 件成功' + (f'（うち2回目で通った {len(flaky)} 本）' if flaky else ''))
sys.exit(1 if fails else 0)
