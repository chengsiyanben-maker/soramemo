// 照合の取り先の切り替え（VERIFY_SOURCE）と、全機の記録（reg_legs）からの到着の一覧（verify_io.ts）
import { assertEquals, assertRejects } from "jsr:@std/assert@1";
import { adsbArrivals, makeDeps, verifySource } from "../functions/_shared/verify_io.ts";
import { runVerification, type Row } from "../functions/_shared/verify_job.ts";

Deno.test("VERIFY_SOURCE は adsb のときだけ adsb、ほかは今までどおり opensky", () => {
  assertEquals(verifySource("adsb"), "adsb");
  assertEquals(verifySource(" ADSB "), "adsb");
  for (const v of [undefined, null, "", "opensky", "adsb.lol", "x"]) assertEquals(verifySource(v), "opensky");
});

Deno.test("adsb の到着の一覧：関数 verify_arrivals に ISO の時刻で渡し、配列でなければ空", async () => {
  const calls: unknown[] = [];
  const one = { icao24: "JA01XJ", callsign: "JAL501", estDepartureAirport: "RJTT", estArrivalAirport: "RJCC", firstSeen: 1, lastSeen: 2 };
  // deno-lint-ignore no-explicit-any
  const admin: any = { rpc: (n: string, a: unknown) => { calls.push([n, a]); return Promise.resolve({ data: [one], error: null }); } };
  assertEquals(await adsbArrivals(admin)("RJCC", 1793750400, 1793757600), [one]);
  assertEquals(calls, [["verify_arrivals", { p_arr_icao: "RJCC", p_begin: "2026-11-04T00:00:00.000Z", p_end: "2026-11-04T02:00:00.000Z" }]]);
  // deno-lint-ignore no-explicit-any
  const empty: any = { rpc: () => Promise.resolve({ data: null, error: null }) };
  assertEquals(await adsbArrivals(empty)("RJCC", 0, 1), []);
  // deno-lint-ignore no-explicit-any
  const ng: any = { rpc: () => Promise.resolve({ data: null, error: { message: "denied" } }) };
  await assertRejects(() => adsbArrivals(ng)("RJCC", 0, 1), Error, "verify_arrivals denied");
});

Deno.test("adsb のときは OpenSky に問い合わせず（航跡も取らず）、照合の決まりは同じ", async () => {
  const realFetch = globalThis.fetch;
  let fetched = 0;
  globalThis.fetch = (() => { fetched++; return Promise.reject(new Error("no network")); }) as typeof fetch;
  try {
    const sec = (s: string) => Math.floor(Date.parse(s) / 1000);
    // deno-lint-ignore no-explicit-any
    const admin: any = { rpc: () => Promise.resolve({ data: [{ icao24: "JA01XJ", callsign: "JAL501", estDepartureAirport: "RJTT", estArrivalAirport: "RJCC",
      firstSeen: sec("2026-10-03T08:32:00+09:00"), lastSeen: sec("2026-10-03T09:58:00+09:00") }], error: null }) };
    const d = makeDeps(admin, { clientId: "", clientSecret: "" }, "adsb");
    assertEquals(d.fetchTrack, undefined);
    const row: Row = { id: 1, fromIcao: "RJTT", toIcao: "RJCC", dep: Date.parse("2026-10-03T08:10:00+09:00"), arr: Date.parse("2026-10-03T10:05:00+09:00"), flightNo: "JL501", attempts: 0 };
    const saved: unknown[] = [];
    const sum = await runVerification({ ...d, loadFlights: async () => [row], save: async (...a) => { saved.push(a); }, officialCheck: undefined });
    assertEquals(sum.verified, 1);
    assertEquals(saved, [[1, "verified", "JAL501 便名一致", 1, null]]);
    assertEquals(fetched, 0);
    // 今までどおり（opensky）なら航跡を取る関数がある
    assertEquals(typeof makeDeps(admin, { clientId: "", clientSecret: "" }).fetchTrack, "function");
  } finally { globalThis.fetch = realFetch; }
});
