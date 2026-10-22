(function(){
  const db = {checkins:[{airport_id:5, terminal_id:null, created_at:new Date(Date.now()-9e6).toISOString(), accuracy_m:20}], flights:[{id:7, from_airport:5, to_airport:6, dep_at:new Date(Date.now()-7.2e6).toISOString(), arr_at:new Date().toISOString(), distance_km:820, status:'verified', airline:null, flight_no:null},{id:8, from_airport:6, to_airport:5, dep_at:new Date(Date.now()-3*864e5).toISOString(), arr_at:new Date(Date.now()-3*864e5+7e6).toISOString(), distance_km:820, status:'no_data', airline:null, flight_no:null},{id:9, from_airport:5, to_airport:23, dep_at:new Date(Date.now()-2*864e5).toISOString(), arr_at:new Date(Date.now()-2*864e5+9e6).toISOString(), distance_km:1555, status:'provisional', airline:null, flight_no:null}], manual_flights:[], intl_flights:[], shugyo_prefs:[]}; let session = null; const listeners = [];
  window.__fake = {db, login(){ session = {user:{id:'u1', email:'test@example.com'}}; listeners.forEach(f=>f('SIGNED_IN', session)); }};
  function q(table){ let lo = 0, hi = 999; window.__queries = (window.__queries || 0) + 1;
    const rows = () => db[table].slice(lo, Math.min(hi, lo + 999) + 1);   // 本物と同じく1回に1,000行まで
    const api = { select(){ return api; }, order(){ return api; }, range(a, b){ lo = a; hi = b; return api; },
      then(res){ res({data: rows(), error:null}); },
      maybeSingle(){ return Promise.resolve({data: db[table][0] || null, error:null}); },
      upsert(row){ db[table] = db[table].filter(r => r.user_id !== row.user_id); db[table].push(JSON.parse(JSON.stringify(row))); window.__upserts = (window.__upserts||0) + 1; return Promise.resolve({error:null}); },
      insert(row){ (Array.isArray(row) ? row : [row]).forEach(r => db[table].push(Object.assign({id: db[table].length+1}, r))); window.__inserts = (window.__inserts||0) + 1; return Promise.resolve({error:null}); },
      delete(){ return { eq(k, v){ db[table] = db[table].filter(r => r[k] !== v); return Promise.resolve({error:null}); } }; } };
    return api; }
  window.supabase = { createClient(){ return {
    auth:{ getSession: async()=>({data:{session}}), onAuthStateChange(f){ listeners.push(f); },
      signInWithOtp: async(o)=>{ window.__otp = o; return {error:null}; },
      verifyOtp: async(o)=>{ window.__verify = o; if(o.token !== '12345678') return {error:{message:'invalid'}}; session = {user:{id:'u1', email:o.email}}; listeners.forEach(f=>f('SIGNED_IN', session)); return {data:{session}, error:null}; }, signOut: async()=>{ session=null; return {error:null}; } },
    from: q,
    rpc: async (name, a) => { window.__rpcs = (window.__rpcs||[]).concat([name]);
      const C = window.__co = window.__co || {name:'そらメモ航空', cash:500000, last:new Date(Date.now()-2*864e5).toISOString(), roles:{}, daily:344, gross:344, upkeep:0, bonus:0, routes:[{k:'5-6', a:'HND', b:'CTS', km:820, base:344, level:1, cost:10320, mult:.5, hub:1, sky:1, min_size:4.5, sa:6, sb:4.5, ac_id:null, intl:false}], fleet:[], sky:{}, total_km:820, rep_points:80, stars:1, facilities:{}, bought:0, value:510320, friend_code:'ABCD1234', hide_rank:false, friends:0};
      const H = window.__hangar = window.__hangar || [{ride:'r:JA01XJ', reg:'JA01XJ', icao:'A359', cls:'lg', intl:false, rode_on:'2026-10-20', flight:'JL501', n:2}, {ride:'f:9', reg:null, icao:'738', cls:'nb', intl:false, rode_on:'2026-10-19', flight:'NH56', n:1}];
      const SPEC = {prop:[1.1, 8000], rj:[1.25, 15000], nb:[1.5, 25000], wb:[1.9, 50000], lg:[2.3, 80000]}, price = cls => Math.round(SPEC[cls][1] * (1 + .25 * C.fleet.length) * (C.bought ? 1 : .5));
      if(name === 'set_flight_details'){ const r = db.flights.find(x => x.id === a.p_flight_id); if(!r) return {data:null, error:{message:'flight not found'}}; r.fare = a.p_fare; r.seat = a.p_seat; window.__details = a; return {data:null, error:null}; }
      if(name === 'set_flight_price'){ const r = db.flights.find(x => x.id === a.p_flight_id); if(!r) return {data:null, error:{message:'flight not found'}}; r.price = a.p_price; return {data:null, error:null}; }
      if(name === 'atc_new_feeder'){ window.__atcFeeder = a; if(!a.p_consent) return {data:null, error:{message:'consent required'}}; return {data:{id:'f1', token:'a'.repeat(64)}, error:null}; }
      if(name === 'my_data_prefs'){ return {data: window.__dp || {stats:true, offers:false, research:false}, error:null}; }
      if(name === 'set_data_prefs'){ window.__dp = {stats:a.p_stats, offers:a.p_offers, research:a.p_research}; return {data: window.__dp, error:null}; }
      if(name === 'my_livery_seen'){ return {data: window.__livSeen || [], error:null}; }
      if(name === 'current_events'){ return {data: window.__events || [], error:null}; }
      if(name === 'my_event_bonus'){ return {data: window.__evb || {pending:0, total:0, count:0}, error:null}; }
      if(name === 'app_status'){ return {data: window.__appStatus || {maintenance:false, checkin_enabled:true, message:'', game_released: window.__gameReleased !== false}, error:null}; }
      if(name === 'plus_status'){ return {data:{plus:!!window.__plus, status: window.__plus ? 'active' : null, until: window.__plus ? new Date(Date.now()+20*864e5).toISOString() : null}, error:null}; }
      if(name === 'import_manual_flights'){ if(!window.__plus) return {error:{message:'plus required'}}; a.p_rows.forEach((r,i)=>db.manual_flights.push({id:100+i, from_airport:r.from, to_airport:r.to, flown_on:r.date, airline:r.airline})); return {data:a.p_rows.length, error:null}; }
      if(name === 'co_state'){ window.__coCalls = (window.__coCalls||0) + 1; if(window.__gameReleased === false) return {data:null, error:{message:'game not released'}}; return {data:{...C, pending:Math.floor(C.daily*2)}, error:null}; }
      if(name === 'co_collect'){ C.cash += C.daily*2 + ((window.__evb && window.__evb.pending) || 0); if(window.__evb) window.__evb.pending = 0; C.last = new Date().toISOString(); return {data:{...C, pending:0}, error:null}; }
      if(name === 'co_upgrade'){ const r = C.routes.find(x=>x.k===a.p_route); if(!r) return {error:{message:'route not found'}}; if(C.cash < r.cost) return {error:{message:'not enough cash'}}; C.cash -= r.cost; r.level++; r.cost = r.base*3*r.level; C.daily = Math.round(r.base*(1+.25*(r.level-1))); return {data:{...C}, error:null}; }
      if(name === 'co_set_role'){ if(a.p_airport && a.p_airport !== 5) return {error:{message:'guardian not met'}}; C.roles[a.p_role] = a.p_airport; C.bonus = a.p_airport ? .1 : 0; return {data:{...C}, error:null}; }
      if(name === 'co_hangar'){ return {data:H.map(x => ({...x, owned:(C.fleet.find(f => f.ride === x.ride) || {}).id || null, price:price(x.cls), upkeep:SPEC[x.cls][1]/1000})), error:null}; }
      if(name === 'co_buy'){ const x = H.find(h => h.ride === a.p_ride); if(!x) return {error:{message:'not ridden'}}; const pr = price(x.cls); if(C.cash < pr) return {error:{message:'not enough cash'}}; C.cash -= pr; C.bought++; C.fleet.push({id:C.fleet.length+1, ride:x.ride, type:x.cls, reg:x.reg, icao:x.icao, intl:false, route:null, paid:pr, age:1, value:pr, sell:Math.round(pr*.3), upkeep:SPEC[x.cls][1]/1000, bought_at:new Date().toISOString(), rode_on:x.rode_on, flight:x.flight}); C.upkeep += SPEC[x.cls][1]/1000; return {data:{...C}, error:null}; }
      if(name === 'co_sell'){ const f = C.fleet.find(x => x.id === a.p_aircraft); if(!f) return {error:{message:'aircraft not found'}}; C.fleet = C.fleet.filter(x => x !== f); C.cash += f.sell; window.__sold = a; return {data:{...C}, error:null}; }
      if(name === 'co_ranking'){ window.__rk = (window.__rk || []).concat([a.p_scope]); const rows = a.p_scope === 'friends' ? (window.__friends || []) : [{no:1, name:'ひこうき雲エア', value:2840000, routes:41, fleet:23, me:false}];
        return {data:{scope:a.p_scope, day:'2026-10-22', rank:rows.length + 1, total:rows.length + 1, value:C.value, prev:a.p_scope === 'all' ? 4 : null, home:5, hidden:C.hide_rank, rows:[...rows, {no:rows.length + 1, name:C.name, value:C.value, routes:1, fleet:C.fleet.length, me:true}]}, error:null}; }
      if(name === 'co_add_friend'){ if(a.p_code.toUpperCase() !== 'ZZZZ9999') return {error:{message:'code not found'}}; window.__friends = [{no:1, name:'つばさ商会', value:9000000, routes:9, fleet:3, me:false, code:'ZZZZ9999'}]; return {data:{name:'つばさ商会'}, error:null}; }
      if(name === 'co_remove_friend'){ window.__friends = []; return {data:null, error:null}; }
      if(name === 'co_set_hide'){ C.hide_rank = a.p_hide; return {data:{...C}, error:null}; }
      if(name === 'co_assign'){ const ac = C.fleet.find(x=>x.id===a.p_aircraft); if(!ac) return {error:{message:'aircraft not found'}}; C.fleet.forEach(x=>{ if(x.route===a.p_route) x.route=null; }); ac.route = a.p_route; const r=C.routes.find(x=>x.k==='5-6'); r.mult = a.p_route ? 2.3 : .5; r.ac_id = a.p_route ? ac.id : null; return {data:{...C}, error:null}; }
      if(name === 'co_build'){ if(a.p_airport !== 5) return {error:{message:'airport not visited'}}; C.facilities[5] = (C.facilities[5]||0)+1; C.cash -= 3000; C.rep_points += 10; return {data:{...C}, error:null}; }
      if(name === 'co_rename'){ C.name = a.p_name.trim(); return {data:{...C}, error:null}; }
      const fl = db.flights.find(x=>x.id===a.p_flight_id); if(!fl) return {error:{message:'not found'}}; fl.airline=a.p_airline; fl.flight_no=a.p_flight_no; fl.status=a.p_airline?'with_flight_no':'provisional'; window.__lastRpc=a; return {error:null}; },
    functions:{ invoke: async (name, {body}) => {
      if(name === 'delete-account'){ window.__deleted = body; return {data:{ok: body.confirm === '削除'}, error:null}; }
      if(window.__offline) return {data:null, error:{name:'FunctionsFetchError', context:{}}};
      window.__calls = (window.__calls||[]).concat([{queued:body.queued, ts:body.ts}]);
      const n = nearest({lat:body.lat, lon:body.lon});
      if(!n.within) return {data:null, error:{context:{json: async()=>({ok:false, reason:'out_of_range', message:'範囲外（サーバー判定）'})}}};
      const at = new Date(body.queued ? body.ts : Date.now()).toISOString();
      const first = !db.checkins.some(c=>c.airport_id===n.a.id);
      db.checkins.push({airport_id:n.a.id, terminal_id:n.term?n.term.id:null, created_at:at, accuracy_m:body.acc});
      return {data:{ok:true, at, airport_id:n.a.id, terminal_id:n.term?n.term.id:null, first_airport:first, first_terminal:true, flight:null, flags:[], bonus: window.__bonus || []}, error:null};
    }}
  }; } };
})();
