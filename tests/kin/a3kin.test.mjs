// 羽田の3D の「動きの推測」（A3K・11/26 checkin/3d-real）の単体テスト。ブラウザも three.js も使わない
//   node tests/kin/a3kin.test.mjs   （src/index.html の /*@A3_KIN@*/〜/*@A3_KIN_END@*/ だけを取り出して動かす）
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../../src/index.html", import.meta.url), "utf8");
const m = src.match(/\/\*@A3_KIN@\*\/([\s\S]*?)\/\*@A3_KIN_END@\*\//);
if (!m) { console.log("NG  A3_KIN のかたまりが見つからない"); process.exit(1); }
const A3K = new Function(m[1] + "\nreturn A3K;")();
const fails = [];
const check = (name, ok, detail = "") => { console.log((ok ? "OK  " : "NG  ") + name + (detail !== "" ? "  " + JSON.stringify(detail) : "")); if (!ok) fails.push(name); };
const D = Math.PI / 180, MLAT = 110574, mlon = (lat) => 111320 * Math.cos(lat * D);
const near = (a, b, e) => Math.abs(a - b) <= e;
const P = (o) => ({ id: "x", lat: 35.55, lon: 139.78, alt_ft: 3000, kt: 180, hdg: 0, fpm: 0, phase: "arr", ...o });
const move = (p, dx, dy) => ({ lat: p.lat + dy / MLAT, lon: p.lon + dx / mlon(p.lat) });
const xy = (o, p) => [(p.lon - o.lon) * mlon(o.lat), (p.lat - o.lat) * MLAT];

// ---- あいだをつなぐ
{ const a = P({}), v = 180 * 0.5144, b = P({ ...move(a, 0, v * 20) });
  const q0 = A3K.between({ t: 0, p: a }, { t: 20e3, p: b }, 0), q1 = A3K.between({ t: 0, p: a }, { t: 20e3, p: b }, 1), qm = A3K.between({ t: 0, p: a }, { t: 20e3, p: b }, 0.5);
  const [x0, y0] = xy(a, q0), [x1, y1] = xy(b, q1), [xm, ym] = xy(a, qm);
  check("まっすぐ：両端は答えの位置", Math.hypot(x0, y0) < .5 && Math.hypot(x1, y1) < .5, [x0, y0, x1, y1]);
  check("まっすぐ：真ん中は直線の真ん中・向きはそのまま", near(xm, 0, .5) && near(ym, v * 10, .5) && near(qm.hdg, 0, .1) || near(qm.hdg, 360, .1), [xm, ym, qm.hdg]); }
{ // 旋回：北向き→東向き（30秒で90度＝3度/秒）。半径 R＝v/ω
  const v = 160 * 0.5144, w = 3 * D, R = v / w, a = P({ kt: 160, hdg: 0 }), b = P({ ...move(a, R, R), kt: 160, hdg: 90 });
  const A = { t: 0, p: a }, B = { t: 30e3, p: b };
  const hs = [0, .25, .5, .75, 1].map((f) => A3K.between(A, B, f).hdg);
  check("旋回：向きは 0→90 へ少しずつ（角が立たない）", hs.every((h, i) => i === 0 || h > hs[i - 1] - .01) && near(hs[0], 0, 2) && near(hs[4], 90, 2) && near(hs[2], 45, 8), hs.map((h) => +h.toFixed(1)));
  const [xm, ym] = xy(a, A3K.between(A, B, .5)), dc = Math.hypot(xm - R, ym) ;
  check("旋回：真ん中は弧の近く（直線の真ん中より外）", Math.abs(dc - R) < R * .04 && Math.hypot(xm - R / 2, ym - R / 2) > R * .15, [Math.round(xm), Math.round(ym), Math.round(R)]);
  check("曲がり方：90度÷30秒＝3度/秒", near(A3K.turnRate(A, B), 3, .01), A3K.turnRate(A, B));
  check("曲がり方：6度/秒まで・間が長すぎる答えは 0", A3K.turnRate({ t: 0, p: P({ hdg: 0 }) }, { t: 5e3, p: P({ hdg: 90 }) }) === 6 && A3K.turnRate({ t: 0, p: a }, { t: 200e3, p: b }) === 0); }
{ const a = P({ ground: true, alt_ft: 0, kt: 8, hdg: 90, phase: "ground" }), b = P({ ...move(a, 400, 0), ground: true, alt_ft: 0, kt: 8, hdg: 90 });
  const [xm, ym] = xy(a, A3K.between({ t: 0, p: a }, { t: 20e3, p: b }, .5));
  check("速さ×時間が距離と合わない（地上でゆっくり）は直線", near(xm, 200, .5) && near(ym, 0, .5), [xm, ym]); }
{ const a = P({ alt_ft: 3000, fpm: -800 }), b = P({ ...move(a, 0, 1850), alt_ft: 2730, fpm: -800 });
  const alts = [0, .25, .5, .75, 1].map((f) => A3K.between({ t: 0, p: a }, { t: 20e3, p: b }, f).alt_ft);
  check("高さ：上昇率でつなぐ（両端は答え・あいだは単調）", near(alts[0], 3000, .1) && near(alts[4], 2730, .1) && alts.every((h, i) => i === 0 || h < alts[i - 1]), alts.map(Math.round)); }

// ---- 先を読む
{ const p = P({ kt: 160, hdg: 0 }), q = A3K.ahead(p, 30, 3), [x, y] = xy(p, q);
  check("先を読む：曲がり方のまま進む（30秒で90度）", near(q.hdg, 90, .5) && x > 300 && y > 300, [Math.round(x), Math.round(y), q.hdg]);
  const q2 = A3K.ahead(p, 90, 6); check("先を読む：向きは90度まで", near(q2.hdg, 90, .5), q2.hdg);
  check("先を読む：高さは上昇率で", near(A3K.ahead(P({ fpm: -600 }), 30).alt_ft, 2700, .1)); }

// ---- 姿勢
{ check("傾き：160ノットで3度/秒 → 約22度", near(A3K.bank(P({ kt: 160 }), 3), 23.7, 1.5), A3K.bank(P({ kt: 160 }), 3));
  check("傾き：左旋回は負・30度まで", A3K.bank(P({ kt: 160 }), -3) < 0 && A3K.bank(P({ kt: 300 }), 6) === 30);
  check("傾き：地上・ゆるい曲がり方は 0", A3K.bank(P({ ground: true, alt_ft: 0 }), 3) === 0 && A3K.bank(P({}), .1) === 0);
  const lvl = A3K.pitch(P({ phase: "dep", alt_ft: 20000, fpm: 0, kt: 400 })), climb = A3K.pitch(P({ phase: "dep", alt_ft: 5000, fpm: 2500, kt: 200 })), app = A3K.pitch(P({ alt_ft: 1500, fpm: -750, kt: 145 }), 1), flare = A3K.pitch(P({ alt_ft: 30, fpm: -300, kt: 135 }));
  check("機首：水平は約2度・上昇は上げる・進入はほぼ水平・引き起こしは進入より上", near(lvl, 2.2, .3) && climb > 8 && app > -1 && app < 3 && flare > app, [lvl, climb, app, flare].map((v) => +v.toFixed(1)));
  check("機首：離陸の引き起こし（地上 150ノット）は8度・130ノットは少し・止まっているのは0", A3K.pitch(P({ ground: true, alt_ft: 0, phase: "dep", kt: 150 })) === 8 && near(A3K.pitch(P({ ground: true, alt_ft: 0, phase: "dep", kt: 130 })), 1.6, .1) && A3K.pitch(P({ ground: true, alt_ft: 0, kt: 0 })) === 0);
  check("機首：着陸のあと遅くなると前輪を下ろす", A3K.pitch(P({ ground: true, alt_ft: 0, phase: "arr", kt: 125 })) === 4 && A3K.pitch(P({ ground: true, alt_ft: 0, phase: "arr", kt: 80 })) === 0); }

// ---- 脚・フラップ・着陸灯
{ check("脚：地上・着陸の前は出す、巡航・離陸のあと（800ft より上）はしまう", A3K.gear(P({ ground: true, alt_ft: 0 })) === 1 && A3K.gear(P({ alt_ft: 2500 })) === 1 && A3K.gear(P({ alt_ft: 9000 })) === 0 && A3K.gear(P({ phase: "dep", alt_ft: 600 })) === 1 && A3K.gear(P({ phase: "dep", alt_ft: 1500 })) === 0);
  const f = (o) => A3K.flaps(P(o));
  check("フラップ：着陸の前は段々に（7000→4000→2000ft）", f({ alt_ft: 6000, kt: 210 }) === .25 && f({ alt_ft: 3500 }) === .6 && f({ alt_ft: 1500 }) === 1 && f({ alt_ft: 12000 }) === 0);
  check("フラップ：離陸のはじめは少し・上昇でしまう・地上の走行はしまう", f({ phase: "dep", alt_ft: 800 }) === .35 && f({ phase: "dep", alt_ft: 4000 }) === 0 && f({ ground: true, alt_ft: 0, kt: 12 }) === 0 && f({ ground: true, alt_ft: 0, kt: 140, phase: "dep" }) === .35);
  check("着陸灯：脚を出した空・滑走路を走る間だけ", A3K.landLight(P({ alt_ft: 2000 })) && !A3K.landLight(P({ alt_ft: 9000 })) && A3K.landLight(P({ ground: true, alt_ft: 0, kt: 120 })) && !A3K.landLight(P({ ground: true, alt_ft: 0, kt: 15 }))); }

// ---- プッシュバック
{ const a = P({ ground: true, alt_ft: 0, kt: 0, hdg: 0 }), back = { ...a, ...move(a, 0, -20), kt: 3, hdg: 180 }, fwd = { ...a, ...move(a, 0, 20), kt: 3, hdg: 0 };
  check("プッシュバック：後ろへ動いたら機首は前の向きのまま（0度）", near(A3K.pushback(a, back), 0, 1) || near(A3K.pushback(a, back), 360, 1), A3K.pushback(a, back));
  check("プッシュバック：前へ動いた・速い・空の上は違う", A3K.pushback(a, fwd) === null && A3K.pushback(a, { ...back, kt: 20 }) === null && A3K.pushback(a, { ...back, ground: false, alt_ft: 2000 }) === null); }

// ---- 誘導路に寄せる
{ const S = A3K.segs([[30, 0, 0, 500, 0]]);   // 東西の線（z＝0）
  const s1 = A3K.snap(200, -10, 85, S), s2 = A3K.snap(200, 12, 260, S), s3 = A3K.snap(200, -60, 90, S), s4 = A3K.snap(200, -5, 0, S);
  check("誘導路：10m ずれた機体を線に寄せ、向きを線にそろえる（東向き 90）", s1 && near(s1.x, 200, .01) && near(s1.z, 0, .01) && near(s1.hdg, 90, .01), s1);
  check("誘導路：反対向き（西向き 270）にもそろえる", s2 && near(s2.hdg, 270, .01), s2);
  check("誘導路：35m より遠いと寄せない・横切る機体は向きそのまま", s3 === null && s4 && s4.hdg === 0, [s3, s4]);
  check("誘導路：形のファイルの線を線分に（2点で1本）", A3K.segs([[30, 0, 0, 10, 0, 10, 10]]).length === 8); }

// ---- 途切れた着陸機
{ const thr = [35.54, 139.80], opp = [35.54 + 2500 / MLAT, 139.80];   // 北向きの滑走路（端A→端B が北）
  const p = P({ lat: thr[0] - 8000 / MLAT, lon: thr[1] + 300 / mlon(thr[0]), hdg: 5, kt: 150, alt_ft: 2600, fpm: -750 }), rw = [[...thr, ...opp]];
  const q10 = A3K.approach(p, 10, rw), q30 = A3K.approach(p, 30, rw), q70 = A3K.approach(p, 70, rw);
  const d = (q) => (thr[0] - q.lat) * MLAT, cr = (q) => (q.lon - thr[1]) * mlon(thr[0]);
  check("途切れた：最終進入の道すじで進む（端へ近づき・延長線に寄り・降りる）", q30 && d(q30) < d(q10) && Math.abs(cr(q30)) < Math.abs(cr(q10)) && q30.alt_ft < q10.alt_ft && q30.est === "gap", q30 && [Math.round(d(q30)), Math.round(cr(q30)), Math.round(q30.alt_ft)]);
  check("途切れた：10秒までは濃いまま、そのあと薄く、60秒で消える", q10.op === 1 && q30.op < 1 && q30.op > 0 && q70 === null, [q10.op, q30.op]);
  check("途切れた：向きは滑走路へそろう", near(q30.hdg, 0, .5) || near(q30.hdg, 360, .5), q30.hdg);
  check("途切れた：高さは3度の道すじより上に浮かない", q30.alt_ft <= Math.max(d(q30) * Math.tan(3 * D) / 0.3048, p.alt_ft * (1 - 30 / 40)) + 1);
  const off = A3K.approach(P({ hdg: 90, phase: "dep", fpm: 1500, alt_ft: 3000 }), 10, rw);
  check("途切れた：合う滑走路がなければ、まっすぐ先へ・20秒で消える", off && off.est === "gap" && near(off.op, .5, .01) && A3K.approach(P({ hdg: 90 }), 25, rw) === null); }

// ---- 瞬間移動させない・姿勢を少しずつ
{ let st = A3K.smooth(null, { x: 0, z: 0, y: 100, vx: 10, vz: 0 }, 0);
  st = A3K.smooth(st, { x: 10, z: 0, y: 100, vx: 10, vz: 0 }, 1000);
  check("なめらか：速さどおりの動きはそのまま", near(st.x, 10, .01) && st.ox === 0, st);
  st = A3K.smooth(st, { x: 220, z: 0, y: 160, vx: 10, vz: 0 }, 1100);   // 次の答えで 200m 先に跳んだ
  check("なめらか：跳んだ所は前の続きから", near(st.x, 11, .5) && near(st.y, 100, .5), st);
  for (let t = 1200; t <= 6000; t += 100) st = A3K.smooth(st, { x: 220 + (t - 1100) / 100, z: 0, y: 160, vx: 10, vz: 0 }, t);
  check("なめらか：約5秒でほぼ答えの位置へ（差は 5% より小さく）", Math.abs(st.ox) < 10.5 && near(st.y, 160, 3), st);
  const far = A3K.smooth({ x: 0, z: 0, y: 0, ox: 0, oz: 0, oy: 0, t: 0 }, { x: 5000, z: 0, y: 0 }, 100);
  check("なめらか：3km より大きい差・5秒より空いたときは合わせない", far.x === 5000 && A3K.smooth({ x: 0, z: 0, y: 0, ox: 50, oz: 0, oy: 0, t: 0 }, { x: 10, z: 0, y: 0 }, 6000).x === 10);
  check("姿勢を少しずつ：1.2秒で約6割・はじめは目標そのまま", near(A3K.ease(0, 10, 1.2), 6.32, .01) && A3K.ease(undefined, 10, 1) === 10); }

console.log(fails.length ? `\n失敗 ${fails.length}` : "\nすべて成功");
process.exit(fails.length ? 1 : 0);
