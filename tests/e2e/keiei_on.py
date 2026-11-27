# エアライン経営の画面を確かめるテストのための道具（11/23 経営を非表示にしたため）
# アプリの切り替え KEIEI_VISIBLE は false（経営の入口を出さない）。経営の画面のテストは、
# 「切り替えを true にしたとき」の動きを確かめるので、この道具を import して、ページを開く前に
# window.__SORAMEMO_TEST_KEIEI = true を立てる（アプリの keieiShown() がこれを見る）。
# import するだけで、そのテストで作るブラウザの文脈（new_context）すべてに効く。
from playwright.async_api import Browser

_orig = Browser.new_context

async def _new_context(self, *a, **k):
    c = await _orig(self, *a, **k)
    await c.add_init_script('window.__SORAMEMO_TEST_KEIEI = true;')
    return c

Browser.new_context = _new_context
