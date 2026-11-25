# -*- coding: utf-8 -*-
# 見本で使う線の絵（そらメモのアイコンに近い細い線。ほかのアプリの絵はまねしない）
P = {
 'home': '<path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/>',
 'book': '<path d="M4 5.5c3-1.3 5.5-1 8 1 2.5-2 5-2.3 8-1v13c-3-1.3-5.5-1-8 1-2.5-2-5-2.3-8-1zM12 6.5v13"/>',
 'plane': '<path d="M21 4.5c-.6-.6-2-.5-2.9.4L14 9 5.5 7 4 8.5l7 3.5-3.2 3.2-2.6-.4L4 16l3.3 1.7L9 21l1.2-1.2-.4-2.6L13 14l3.5 7 1.5-1.5L16 11l4.1-4.1c.9-.9 1-2.3.4-2.9z"/>',
 'ops': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/><path d="M12 12l5.5-5.5"/>',
 'stairs': '<path d="M5 19h4v-4h4v-4h4V7h3"/>',
 'pin': '<path d="M9 3.5h6l-1 5.5 3 3H7l3-3zM12 12v8.5"/>',
 'bell': '<path d="M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15zM10 20.5a2 2 0 0 0 4 0"/>',
 'copy': '<rect x="8.5" y="8.5" width="11" height="11" rx="2.5"/><path d="M15.5 8.5V6.5a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
 'check': '<path d="M5 12.5l4.2 4L19 7"/>',
 'retry': '<path d="M19 12a7 7 0 1 1-2.05-4.95M19 4.5v3.8h-3.8"/>',
 'grip': '<path d="M7 8h10M7 12h10M7 16h10"/>',
 'chev': '<path d="M9 6l6 6-6 6"/>',
 'back': '<path d="M15 6l-6 6 6 6"/>',
 'pencil': '<path d="M4 20l1-4L16 5l3 3L8 19zM14 7l3 3"/>',
 'wifi': '<path d="M4 9a12 12 0 0 1 16 0M7 12.5a7.5 7.5 0 0 1 10 0M10 16a3 3 0 0 1 4 0M12 19.5h.01M3 3l18 18"/>',
 'user': '<circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
}
def ic(name, cls='ic'):
    return '<svg class="%s i-%s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>' % (cls, name, P[name])

def tabs(cur='home'):
    items = [('home','ホーム','home'),('book','図鑑','book'),('log','フライト','plane'),('ops','運用','ops'),('sg','修行','stairs')]
    out = ['<nav class="tabs" aria-label="下のタブ">']
    for k, lb, icn in items:
        out.append('<button type="button" class="tap"%s>%s%s</button>' % (' aria-current="page"' if k == cur else '', ic(icn), lb))
    out.append('<i class="dot" aria-hidden="true"></i></nav>')
    return ''.join(out)
