// 実際に飛んだ航路：間引き・範囲外の点・照合への組み込み
import { assertEquals } from "jsr:@std/assert@1";
import { compactTrack, simplify, TRACK } from "../functions/_shared/track.ts";
import { runVerification, type Row } from "../functions/_shared/verify_job.ts";

Deno.test("まっすぐな線の途中の点は消え、曲がり角は残る", () => {
  const line: [number, number][] = [[35, 139], [35.5, 139.5], [36, 140], [36, 141]];
  assertEquals(simplify(line, 0.01), [[35, 139], [36, 140], [36, 141]]);
});

Deno.test("OpenSky の path から [緯度, 経度] を取り出し、日本の外の点と壊れた点を捨てる", () => {
  const path = [[0, 35.5531, 139.7811, 0, 0, true], [1, 0, 0, 0, 0, false], [2, null, 140, 0, 0, false], [3, 42.7752, 141.6923, 0, 0, true]];
  assertEquals(compactTrack(path), [[35.553, 139.781], [42.775, 141.692]]);
  assertEquals(compactTrack(null), null);
  assertEquals(compactTrack([[0, 35, 139]]), null);   // 1点では線にならない
});

Deno.test("点が多くても上限まで減らす", () => {
  const path = Array.from({ length: 3000 }, (_, i) => [i, 35 + Math.sin(i / 20) * 2, 130 + i / 300, 0, 0, false]);
  const t = compactTrack(path)!;
  assertEquals(t.length <= TRACK.maxPoints, true);
  assertEquals(t[0], [35, 130]);
});

Deno.test("照合で確認できた便は航路も保存する。航路が取れなくても確認はそのまま", async () => {
  const t = (s: string) => Date.parse(s), sec = (s: string) => Math.floor(Date.parse(s) / 1000);
  const rows: Row[] = [{ id: 1, fromIcao: "RJTT", toIcao: "RJCC", dep: t("2026-10-03T08:10:00+09:00"), arr: t("2026-10-03T10:05:00+09:00"), flightNo: "JL501", attempts: 0 }];
  const arr = [{ icao24: "abc", callsign: "JAL501", estDepartureAirport: "RJTT", estArrivalAirport: "RJCC", firstSeen: sec("2026-10-03T08:32:00+09:00"), lastSeen: sec("2026-10-03T09:58:00+09:00") }];
  const saved: unknown[] = [];
  await runVerification({ loadFlights: async () => rows, fetchArrivals: async () => arr,
    fetchTrack: async () => [[0, 35.55, 139.78, 0, 0, true], [1, 42.77, 141.69, 0, 0, true]],
    save: async (id, status, _n, _a, track) => { saved.push([id, status, track]); } });
  assertEquals(saved, [[1, "verified", [[35.55, 139.78], [42.77, 141.69]]]]);
  saved.length = 0;
  await runVerification({ loadFlights: async () => rows, fetchArrivals: async () => arr,
    fetchTrack: async () => { throw new Error("503"); },
    save: async (id, status, _n, _a, track) => { saved.push([id, status, track]); } });
  assertEquals(saved, [[1, "verified", null]]);
});
