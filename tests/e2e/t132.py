import os, sys, json, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web'))
# サービスワーカーの push の受け取り：届いた中身の renotify を showNotification に渡す（11/13 データ担当 data/alert-merge の依頼）
#   同じ便の通知（tag が同じ）を上書きしたときにも鳴らすため。renotify は届いた中身に tag があるときだけ
#   web/sw.js を node の vm で読み、偽の self に push を送って、渡した中身を確かめる（ブラウザも網も使わない）
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
JS = r"""
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(process.argv[1], 'utf8');
const L = {}, shown = [];
const self = { addEventListener: (t, f) => { L[t] = f; }, registration: { showNotification: (title, o) => { shown.push({ title, o }); return Promise.resolve(); } },
  skipWaiting(){}, clients: { claim(){}, matchAll: async () => [] }, location: { origin: 'https://soramemo.jp' } };
vm.runInNewContext(src, { self, caches: { open: async () => ({}), keys: async () => [], match: async () => undefined }, fetch: async () => ({}), URL, Response: class {}, Promise, console });
const cases = JSON.parse(process.argv[2]);
(async () => {
  for (const c of cases) {
    const ps = []; const data = c === null ? null : { json: () => c, text: () => JSON.stringify(c) };
    L.push({ data, waitUntil: (p) => ps.push(p) }); await Promise.all(ps);
  }
  console.log(JSON.stringify(shown));
})();
"""
cases = [
    {'title': 'そらメモ：JL503', 'body': '出発が40分遅れ', 'tag': 'fw-JL503@2026-11-13@HND', 'renotify': True, 'url': './#ops-HND'},
    {'title': 'そらメモ：JL503', 'body': '【更新】', 'tag': 'fw-JL503@2026-11-13@HND', 'renotify': False, 'url': './#ops-HND'},
    {'title': 'そらメモ', 'body': 'tag なし', 'renotify': True},
    {'title': 'そらメモ', 'body': '古い形', 'tag': 'x'},
    None,
]
p = subprocess.run(['node', '-e', JS, os.path.join(WEB, 'sw.js'), json.dumps(cases)], capture_output=True, text=True, timeout=30)
check('node で sw.js を読めた', p.returncode == 0, p.stderr[-400:])
shown = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else []
check('push 5件すべてで通知を出した', len(shown) == 5, len(shown))
if len(shown) == 5:
    o = [s['o'] for s in shown]
    check('tag と renotify: true が届くと renotify: true（同じ便の上書きでも鳴る）', o[0].get('renotify') is True and o[0]['tag'] == 'fw-JL503@2026-11-13@HND', o[0])
    check('renotify: false なら鳴らさない', o[1].get('renotify') is False, o[1])
    check('tag がないときは renotify を立てない（決まった tag「soramemo」のまま）', o[2].get('renotify') is False and o[2]['tag'] == 'soramemo', o[2])
    check('renotify がない古い中身は今までどおり鳴らさない', o[3].get('renotify') is False and o[3]['tag'] == 'x', o[3])
    check('中身が空でも通知を出す（renotify なし）', shown[4]['title'] == 'そらメモ' and o[4].get('renotify') is False, shown[4])
    check('飛び先の url はそのまま（./#ops-HND）', o[0]['data']['url'] == './#ops-HND', o[0]['data'])
    check('ほかの中身（本文・アイコン）は今までどおり', o[0]['body'] == '出発が40分遅れ' and o[0]['icon'] == 'icon-192.png' and o[0]['badge'] == 'icon-192.png', o[0])
print('errors', fails)
sys.exit(1 if fails else 0)
