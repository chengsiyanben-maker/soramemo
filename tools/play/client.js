// そらメモ 試遊版：サーバー（Supabase）の代わりに、ブラウザの中のデータベース（PGlite）で動かす
//   本番と同じマイグレーションを流したデータベース（play.tgz）を読み込み、アプリの呼び出しをそこへ流す
//   ・ログインは見本の利用者（play@example.com）。行の見える範囲（RLS）は本番と同じ
//   ・進み具合はこの端末のブラウザ（IndexedDB）に残る。「はじめから」で消える
(function () {
  const UID = "00000000-0000-4000-8000-00000000c0de";
  const PG = "https://cdn.jsdelivr.net/npm/@electric-sql/pglite@0.5.8/dist/index.js";
  const IDB = "soramemo-play-v1";
  const user = { id: UID, email: "play@example.com" };
  const session = { user, access_token: "play" };
  let db = null, fnInfo = null;
  try { localStorage.setItem("soramemo.onboarded", "1"); localStorage.setItem("soramemo.game", "1"); if (!localStorage.getItem("soramemo.mode")) localStorage.setItem("soramemo.mode", "game"); } catch (e) {}   // はじめの案内はとばし、経営を出しておく
  const status = (t) => { const el = document.getElementById("playLoad"); if (el) el.querySelector("p").textContent = t; };

  // 置き場所に置ける形にするため、データベースの中身と部品は文字（base64）にしてある
  const b64 = async (f) => { const t = await (await fetch(f)).text(); const s = atob(t.trim()); const u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return new Blob([u]); };
  const ready = (async () => {
    status("データベースの部品を読み込んでいます");
    const { PGlite } = await import(PG);
    const [wasm, idbw, data] = await Promise.all([
      fetch("pglite.wasm").then((r) => r.arrayBuffer()).then((b) => WebAssembly.compile(b)),
      fetch("initdb.wasm").then((r) => r.arrayBuffer()).then((b) => WebAssembly.compile(b)),
      b64("pglite-data.txt"),
    ]);
    const opts = { pgliteWasmModule: wasm, initdbWasmModule: idbw, fsBundle: data, relaxedDurability: true,
      parsers: { 1082: (v) => v, 1114: (v) => v, 1184: (v) => new Date(v.replace(" ", "T").replace(/([+-]\d\d)$/, "$1:00")).toISOString(), 1700: (v) => Number(v), 20: (v) => Number(v) } };
    let exists = false;
    try { exists = ((await indexedDB.databases?.()) || []).some((d) => d.name === "/pglite/" + IDB); } catch (e) {}
    status(exists ? "前回の続きを開いています" : "見本の会社を用意しています（はじめは少し時間がかかります）");
    try {
      db = await PGlite.create({ ...opts, dataDir: "idb://" + IDB, ...(exists ? {} : { loadDataDir: await b64("play-db.txt") }) });
    } catch (e) {
      db = await PGlite.create({ ...opts, loadDataDir: await b64("play-db.txt") });   // この端末に残せないときは、開いているあいだだけ
    }
    status("日付を今日に合わせています");
    await db.query("select play.catch_up()");
    const r = await db.query(`select p.proname n, p.proretset s, coalesce(p.proargnames, '{}') a, (select array_agg(format_type(t, null) order by i) from unnest(p.proargtypes::oid[]) with ordinality u(t, i)) ty,
                                     pg_get_function_result(p.oid) res
                                from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public'`);
    fnInfo = new Map(r.rows.map((x) => [x.n, x]));
    window.__playDb = db;
    const el = document.getElementById("playLoad"); if (el) el.hidden = true;
    window.dispatchEvent(new Event("play-ready"));
  })().catch((e) => { status("試遊版を開けませんでした：" + (e && e.message || e)); throw e; });

  async function asUser(fn) {
    await ready;
    return db.transaction(async (tx) => {
      await tx.exec(`set local role authenticated; select set_config('request.jwt.claim.sub', '${UID}', true);`);
      return fn(tx);
    });
  }
  const errOf = (e) => ({ message: String((e && e.message) || e) });
  const lit = (v) => (v == null ? null : typeof v === "object" ? JSON.stringify(v) : String(v));

  async function rpc(name, args) {
    await ready;
    const f = fnInfo.get(name);
    if (!f) return { data: null, error: { message: "function not found: " + name } };
    const a = args || {}, params = [], parts = [];
    (f.a || []).forEach((n, i) => {
      if (!(n in a)) return;
      const ty = (f.ty || [])[i] || "text";
      params.push(lit(a[n]));
      const p = "$" + params.length;
      parts.push(`${n} => ` + (ty.endsWith("[]") ? `(select coalesce(array_agg(x), '{}') from jsonb_array_elements_text(${p}::jsonb) x)::${ty}` : `${p}::${ty}`));
    });
    const call = `public.${name}(${parts.join(", ")})`;
    try {
      const data = await asUser(async (tx) => {
        if (f.s || /^TABLE\(/.test(f.res)) {
          const r = await tx.query(`select * from ${call}`, params);
          const cols = r.fields.map((x) => x.name);
          return cols.length === 1 && cols[0] === name ? r.rows.map((x) => x[name]) : r.rows;
        }
        const r = await tx.query(`select ${call} as v`, params);
        return f.res === "void" ? null : r.rows[0].v;
      });
      return { data, error: null };
    } catch (e) { return { data: null, error: errOf(e) }; }
  }

  function from(table) {
    let cols = "*", lo = null, hi = null, orders = [], eqs = [], single = false, op = "select", row = null;
    const run = async () => {
      try {
        const data = await asUser(async (tx) => {
          const w = eqs.length ? " where " + eqs.map((e, i) => `${e[0]} = $${i + 1}`).join(" and ") : "";
          const ps = eqs.map((e) => lit(e[1]));
          if (op === "select") {
            const sql = `select ${cols === "*" ? "*" : cols.split(",").map((c) => '"' + c.trim() + '"').join(", ")} from public.${table}${w}`
              + (orders.length ? " order by " + orders.map((o) => `"${o[0]}" ${o[1] ? "asc" : "desc"}`).join(", ") : "")
              + (lo != null ? ` offset ${lo} limit ${hi - lo + 1}` : "");
            const r = await tx.query(sql, ps);
            return single ? r.rows[0] || null : r.rows;
          }
          if (op === "delete") { await tx.query(`delete from public.${table}${w}`, ps); return null; }
          const rows = (Array.isArray(row) ? row : [row]).map((x) => (op === "upsert" ? { ...x } : { ...x, user_id: UID }));
          for (const x of rows) {
            const ks = Object.keys(x);
            const q = `insert into public.${table} (${ks.map((k) => '"' + k + '"').join(", ")}) select * from jsonb_populate_record(null::public.${table}, $1::jsonb) x`
              .replace("select * from", `select ${ks.map((k) => 'x."' + k + '"').join(", ")} from`)
              + (op === "upsert" ? ` on conflict (user_id) do update set ${ks.filter((k) => k !== "user_id").map((k) => `"${k}" = excluded."${k}"`).join(", ")}` : "");
            await tx.query(q, [JSON.stringify(x)]);
          }
          return null;
        });
        return { data, error: null };
      } catch (e) { return { data: null, error: errOf(e) }; }
    };
    const api = {
      select(c) { if (op === "select") cols = c || "*"; return api; },
      order(c, o) { orders.push([c, !o || o.ascending !== false]); return api; },
      range(a, b) { lo = a; hi = b; return api; },
      eq(k, v) { eqs.push([k, v]); return op === "delete" ? run() : api; },
      maybeSingle() { single = true; return run(); },
      insert(r) { op = "insert"; row = r; return run(); },
      upsert(r) { op = "upsert"; row = r; return run(); },
      delete() { op = "delete"; return api; },
      then(res, rej) { return run().then(res, rej); },
    };
    return api;
  }

  const listeners = [];
  window.supabase = { createClient() { return {
    auth: {
      getSession: async () => ({ data: { session } }),
      onAuthStateChange(f) { listeners.push(f); return { data: { subscription: { unsubscribe() {} } } }; },
      signInWithOtp: async () => ({ error: { message: "試遊版では見本の利用者でログインしています" } }),
      verifyOtp: async () => ({ error: { message: "試遊版では見本の利用者でログインしています" } }),
      signOut: async () => ({ error: null }),
    },
    from, rpc,
    functions: { invoke: async () => ({ data: null, error: { message: "試遊版ではサーバーの機能（チェックインなど）は使えません" } }) },
  }; } };

  // 試遊用の操作（帯のボタンから呼ぶ）
  window.play = {
    ready,
    async advance(n) { await ready; const r = await db.query(`select play.advance(${Math.max(1, Math.min(31, n | 0))}) v`); return r.rows[0].v; },
    async addCash(n) { await ready; await db.query(`update public.companies set cash = cash + $1 where user_id = $2`, [n, UID]); },
    async info() { await ready; const r = await db.query(`select (select v from play.state where k = 'day')::int d, (now() at time zone 'Asia/Tokyo')::date::text today, (select cash from public.companies where user_id = $1) cash`, [UID]); return r.rows[0]; },
    async reset() { try { await db.close(); } catch (e) {} try { indexedDB.deleteDatabase("/pglite/" + IDB); } catch (e) {} location.reload(); },
  };
})();
