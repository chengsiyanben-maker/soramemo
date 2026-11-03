// そらメモ 試遊版：サーバー（Supabase）の代わりに、ブラウザの中のデータベース（PGlite）で動かす
//   本番と同じマイグレーションを流したデータベース（play-db.txt）を読み込み、アプリの呼び出しをそこへ流す
//   ・データベースは別の作業場所（Web Worker）で動かす。計算中も画面が固まらず、ボタンが効く
//     （作業場所を作れないブラウザでは、画面と同じ場所で動かす）
//   ・ログインは見本の利用者（play@example.com）。行の見える範囲（RLS）は本番と同じ
//   ・進み具合はこの端末のブラウザ（IndexedDB）に残る。「はじめから」で消える
(function () {
  const UID = "00000000-0000-4000-8000-00000000c0de";
  const IDB = "soramemo-play-v1";
  const user = { id: UID, email: "play@example.com" };
  const session = { user, access_token: "play" };
  try { localStorage.setItem("soramemo.onboarded", "1"); localStorage.setItem("soramemo.game", "1"); if (!localStorage.getItem("soramemo.mode")) localStorage.setItem("soramemo.mode", "game"); } catch (e) {}   // はじめの案内はとばし、経営を出しておく
  const status = (t) => { const el = document.getElementById("playLoad"); if (el) el.querySelector("p").textContent = t; };

  // ---- データベースの側（Worker の中でも、画面と同じ場所でも動く。外の変数は使わない） ----
  function backend(post) {
    const PG = "https://cdn.jsdelivr.net/npm/@electric-sql/pglite@0.5.8/dist/index.js";
    let db = null;
    // 置き場所に置ける形にするため、データベースの中身と部品は文字（base64）にしてある
    const b64 = async (u) => { const t = await (await fetch(u)).text(); const s = atob(t.trim()); const a = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i); return new Blob([a]); };
    async function init(o) {
      post({ status: "データベースの部品を読み込んでいます" });
      const { PGlite } = await import(PG);
      const [wasm, idbw, data] = await Promise.all([
        fetch(o.base + "pglite.wasm").then((r) => r.arrayBuffer()).then((b) => WebAssembly.compile(b)),
        fetch(o.base + "initdb.wasm").then((r) => r.arrayBuffer()).then((b) => WebAssembly.compile(b)),
        b64(o.base + "pglite-data.txt"),
      ]);
      const opts = { pgliteWasmModule: wasm, initdbWasmModule: idbw, fsBundle: data, relaxedDurability: true,
        parsers: { 1082: (v) => v, 1114: (v) => v, 1184: (v) => new Date(v.replace(" ", "T").replace(/([+-]\d\d)$/, "$1:00")).toISOString(), 1700: (v) => Number(v), 20: (v) => Number(v) } };
      let exists = false;
      try { exists = ((await indexedDB.databases?.()) || []).some((d) => d.name === "/pglite/" + o.idb); } catch (e) {}
      post({ status: exists ? "前回の続きを開いています" : "見本の会社を用意しています（はじめは少し時間がかかります）" });
      try {
        db = await PGlite.create({ ...opts, dataDir: "idb://" + o.idb, ...(exists ? {} : { loadDataDir: await b64(o.base + "play-db.txt") }) });
      } catch (e) {
        db = await PGlite.create({ ...opts, loadDataDir: await b64(o.base + "play-db.txt") });   // この端末に残せないときは、開いているあいだだけ
      }
      post({ status: "日付を今日に合わせています" });
      await db.query("select play.catch_up()");
      const r = await db.query(`select p.proname n, p.proretset s, coalesce(p.proargnames, '{}') a, (select array_agg(format_type(t, null) order by i) from unnest(p.proargtypes::oid[]) with ordinality u(t, i)) ty,
                                       pg_get_function_result(p.oid) res
                                  from pg_proc p join pg_namespace s on s.oid = p.pronamespace where s.nspname = 'public'`);
      return r.rows;
    }
    // stmts をひとまとめ（1つの処理）で流す。asUser なら見本の利用者として（RLS あり）
    async function run(stmts, asUser, uid) {
      return db.transaction(async (tx) => {
        if (asUser) await tx.exec(`set local role authenticated; select set_config('request.jwt.claim.sub', '${uid}', true);`);
        const out = [];
        for (const s of stmts) { const r = await tx.query(s.sql, s.params || []); out.push({ rows: r.rows, fields: r.fields.map((f) => f.name) }); }
        return out;
      });
    }
    async function handle(m) {
      if (m.op === "init") return init(m);
      if (m.op === "run") return run(m.stmts, m.asUser, m.uid);
      if (m.op === "close") { await db.close(); return true; }
      throw new Error("unknown op");
    }
    return handle;
  }

  // ---- 画面の側：Worker に頼む（だめなら同じ場所で） ----
  let call;
  const pending = new Map(); let seq = 0;
  function useWorker() {
    const src = `const handle = (${backend.toString()})((m) => postMessage(m));
onmessage = async (e) => { const { id, m } = e.data; try { postMessage({ id, ok: await handle(m) }); } catch (err) { postMessage({ id, err: String((err && err.message) || err) }); } };`;
    const w = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })), { type: "module" });
    w.onmessage = (e) => {
      const d = e.data;
      if (d.status) return status(d.status);
      const p = pending.get(d.id); if (!p) return; pending.delete(d.id);
      if ("err" in d) p.rej(new Error(d.err)); else p.res(d.ok);
    };
    w.onerror = (e) => { for (const p of pending.values()) p.rej(new Error("worker: " + (e.message || "error"))); pending.clear(); };
    return (m) => new Promise((res, rej) => { const id = ++seq; pending.set(id, { res, rej }); w.postMessage({ id, m }); });
  }
  function useMain() { const h = backend((m) => { if (m.status) status(m.status); }); return (m) => h(m); }

  // 計算中のしるし（0.2秒より長くかかるときだけ出す）
  let busyN = 0, busyT = null;
  const busy = (d) => {
    busyN += d;
    const el = document.getElementById("playBusy"); if (!el) return;
    if (busyN > 0 && !busyT && el.hidden) busyT = setTimeout(() => { busyT = null; if (busyN > 0) el.hidden = false; }, 200);
    if (busyN <= 0) { busyN = 0; clearTimeout(busyT); busyT = null; el.hidden = true; }
  };

  let fnInfo = null;
  const base = new URL(".", location.href).href;
  const ready = (async () => {
    let rows;
    try { call = useWorker(); rows = await call({ op: "init", base, idb: IDB }); }
    catch (e) { console.warn("試遊版：作業場所（Worker）が使えないので、画面と同じ場所で動かします", e); call = useMain(); rows = await call({ op: "init", base, idb: IDB }); }
    fnInfo = new Map(rows.map((x) => [x.n, x]));
    const el = document.getElementById("playLoad"); if (el) el.hidden = true;
    window.dispatchEvent(new Event("play-ready"));
  })().catch((e) => { status("試遊版を開けませんでした：" + (e && e.message || e)); throw e; });

  async function run(stmts, asUser = true) {
    await ready; busy(1);
    try { return await call({ op: "run", stmts, asUser, uid: UID }); } finally { busy(-1); }
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
    const c = `public.${name}(${parts.join(", ")})`;
    try {
      if (f.s || /^TABLE\(/.test(f.res)) {
        const [r] = await run([{ sql: `select * from ${c}`, params }]);
        return { data: r.fields.length === 1 && r.fields[0] === name ? r.rows.map((x) => x[name]) : r.rows, error: null };
      }
      const [r] = await run([{ sql: `select ${c} as v`, params }]);
      return { data: f.res === "void" ? null : r.rows[0].v, error: null };
    } catch (e) { return { data: null, error: errOf(e) }; }
  }

  function from(table) {
    let cols = "*", lo = null, hi = null, orders = [], eqs = [], single = false, op = "select", row = null;
    const exec = async () => {
      try {
        const w = eqs.length ? " where " + eqs.map((e, i) => `"${e[0]}" = $${i + 1}`).join(" and ") : "";
        const ps = eqs.map((e) => lit(e[1]));
        if (op === "select") {
          const sql = `select ${cols === "*" ? "*" : cols.split(",").map((c) => '"' + c.trim() + '"').join(", ")} from public.${table}${w}`
            + (orders.length ? " order by " + orders.map((o) => `"${o[0]}" ${o[1] ? "asc" : "desc"}`).join(", ") : "")
            + (lo != null ? ` offset ${lo} limit ${hi - lo + 1}` : "");
          const [r] = await run([{ sql, params: ps }]);
          return { data: single ? r.rows[0] || null : r.rows, error: null };
        }
        if (op === "delete") { await run([{ sql: `delete from public.${table}${w}`, params: ps }]); return { data: null, error: null }; }
        const rows = (Array.isArray(row) ? row : [row]).map((x) => (op === "upsert" ? { ...x } : { ...x, user_id: UID }));
        await run(rows.map((x) => {
          const ks = Object.keys(x);
          return { sql: `insert into public.${table} (${ks.map((k) => '"' + k + '"').join(", ")}) select ${ks.map((k) => 'x."' + k + '"').join(", ")} from jsonb_populate_record(null::public.${table}, $1::jsonb) x`
            + (op === "upsert" ? ` on conflict (user_id) do update set ${ks.filter((k) => k !== "user_id").map((k) => `"${k}" = excluded."${k}"`).join(", ")}` : ""), params: [JSON.stringify(x)] };
        }));
        return { data: null, error: null };
      } catch (e) { return { data: null, error: errOf(e) }; }
    };
    const api = {
      select(c) { if (op === "select") cols = c || "*"; return api; },
      order(c, o) { orders.push([c, !o || o.ascending !== false]); return api; },
      range(a, b) { lo = a; hi = b; return api; },
      eq(k, v) { eqs.push([k, v]); return op === "delete" ? exec() : api; },
      maybeSingle() { single = true; return exec(); },
      insert(r) { op = "insert"; row = r; return exec(); },
      upsert(r) { op = "upsert"; row = r; return exec(); },
      delete() { op = "delete"; return api; },
      then(res, rej) { return exec().then(res, rej); },
    };
    return api;
  }

  window.supabase = { createClient() { return {
    auth: {
      getSession: async () => ({ data: { session } }),
      onAuthStateChange() { return { data: { subscription: { unsubscribe() {} } } }; },
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
    async advance(n) { const [r] = await run([{ sql: `select play.advance(${Math.max(1, Math.min(31, n | 0))}) v` }], false); return r.rows[0].v; },
    async addCash(n) { await run([{ sql: `update public.companies set cash = cash + $1 where user_id = $2`, params: [n, UID] }], false); },
    uid: UID,
    busy() { return busyN; },
    async sql(q, params) { const [r] = await run([{ sql: q, params: params || [] }], false); return r.rows; },   // 調べるとき用（このブラウザの中のデータベースだけ）
    async info() { const [r] = await run([{ sql: `select (select v from play.state where k = 'day')::int d, (now() at time zone 'Asia/Tokyo')::date::text today, (select cash from public.companies where user_id = $1) cash`, params: [UID] }], false); return r.rows[0]; },
    async reset() { try { await call({ op: "close" }); } catch (e) {} try { indexedDB.deleteDatabase("/pglite/" + IDB); } catch (e) {} setTimeout(() => location.reload(), 300); },
  };
})();
