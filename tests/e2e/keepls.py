# 読み込み直し（reload）をするテストのための道具
# file:// で開いたページを読み込み直すと、Chromium が直前に書いた localStorage をときどき（1〜3割）落とし、
# 前の中身のまま開いてしまう（鍵が消えることも、古い値に戻ることもある。空の html でも起きる）。
# http で開くと落ちないので、読み込み直すテストは手元の小さな http の窓口（127.0.0.1）から開く（2026-11-06 に確かめた）。
# 窓口が出すのは、このリポジトリと作業用フォルダの中のファイルだけ。URL の道すじはファイルの絶対パスと同じなので、
# '**/web/config.js' などの route はそのまま効く。
# http（127.0.0.1）だとアプリが sw.js（オフライン用）を登録してしまうので、テストでは sw.js を返さない（file:// のときと同じに保つ）。
import os, threading, functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS = [os.path.abspath(os.path.join(HERE, '..', '..')), os.path.abspath(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'))]
_BASE = None

class _H(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = os.path.abspath(unquote(urlsplit(path).path))
        return p if any(p == r or p.startswith(r + os.sep) for r in ROOTS) else '/nonexistent'
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()

def base():
    global _BASE
    if _BASE is None:
        srv = ThreadingHTTPServer(('127.0.0.1', 0), _H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        _BASE = f'http://127.0.0.1:{srv.server_address[1]}'
    return _BASE

def url(path):
    return base() + os.path.abspath(path)

async def goto_http(pg, path):
    if not getattr(pg.context, '_sm_sw', False):
        await pg.context.route('**/sw.js', lambda r: r.fulfill(status=404, body=''))
        pg.context._sm_sw = True
    return await pg.goto(url(path))

async def reload_keep(pg):
    await pg.reload(); await pg.wait_for_load_state('load')
