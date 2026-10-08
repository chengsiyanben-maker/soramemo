(function(){
  const db = {checkins:[{airport_id:5, terminal_id:null, created_at:new Date(Date.now()-9e6).toISOString(), accuracy_m:20}], flights:[{id:7, from_airport:5, to_airport:6, dep_at:new Date(Date.now()-7.2e6).toISOString(), arr_at:new Date().toISOString(), distance_km:820, status:'verified', airline:null, flight_no:null},{id:8, from_airport:6, to_airport:5, dep_at:new Date(Date.now()-3*864e5).toISOString(), arr_at:new Date(Date.now()-3*864e5+7e6).toISOString(), distance_km:820, status:'no_data', airline:null, flight_no:null},{id:9, from_airport:5, to_airport:23, dep_at:new Date(Date.now()-2*864e5).toISOString(), arr_at:new Date(Date.now()-2*864e5+9e6).toISOString(), distance_km:1555, status:'provisional', airline:null, flight_no:null}], manual_flights:[]}; let session = null; const listeners = [];
  window.__fake = {db, login(){ session = {user:{id:'u1', email:'test@example.com'}}; listeners.forEach(f=>f('SIGNED_IN', session)); }};
  function q(table){ let lo = 0, hi = 999; window.__queries = (window.__queries || 0) + 1;
    const rows = () => db[table].slice(lo, Math.min(hi, lo + 999) + 1);   // 本物と同じく1回に1,000行まで
    const api = { select(){ return api; }, order(){ return api; }, range(a, b){ lo = a; hi = b; return api; },
      then(res){ res({data: rows(), error:null}); },
      insert(row){ (Array.isArray(row) ? row : [row]).forEach(r => db[table].push(Object.assign({id: db[table].length+1}, r))); window.__inserts = (window.__inserts||0) + 1; return Promise.resolve({error:null}); } };
    return api; }
  window.supabase = { createClient(){ return {
    auth:{ getSession: async()=>({data:{session}}), onAuthStateChange(f){ listeners.push(f); },
      signInWithOtp: async(o)=>{ window.__otp = o; return {error:null}; },
      verifyOtp: async(o)=>{ window.__verify = o; if(o.token !== '12345678') return {error:{message:'invalid'}}; session = {user:{id:'u1', email:o.email}}; listeners.forEach(f=>f('SIGNED_IN', session)); return {data:{session}, error:null}; }, signOut: async()=>{ session=null; return {error:null}; } },
    from: q,
    rpc: async (name, a) => { window.__rpcs = (window.__rpcs||[]).concat([name]);
      const C = window.__co = window.__co || {name:'そらメモ航空', cash:500000, last:new Date(Date.now()-2*864e5).toISOString(), roles:{}, daily:344, bonus:0, routes:[{k:'5-6', base:344, level:1, cost:10320, mult:1}], fleet:[], total_km:820, rep_points:80, stars:1, facilities:{}};
      if(name === 'set_flight_details'){ const r = db.flights.find(x => x.id === a.p_flight_id); if(!r) return {data:null, error:{message:'flight not found'}}; r.fare = a.p_fare; r.seat = a.p_seat; window.__details = a; return {data:null, error:null}; }
      if(name === 'app_status'){ return {data: window.__appStatus || {maintenance:false, checkin_enabled:true, message:'', game_released: window.__gameReleased !== false}, error:null}; }
      if(name === 'plus_status'){ return {data:{plus:!!window.__plus, status: window.__plus ? 'active' : null, until: window.__plus ? new Date(Date.now()+20*864e5).toISOString() : null}, error:null}; }
      if(name === 'import_manual_flights'){ if(!window.__plus) return {error:{message:'plus required'}}; a.p_rows.forEach((r,i)=>db.manual_flights.push({id:100+i, from_airport:r.from, to_airport:r.to, flown_on:r.date, airline:r.airline})); return {data:a.p_rows.length, error:null}; }
      if(name === 'co_state'){ window.__coCalls = (window.__coCalls||0) + 1; if(window.__gameReleased === false) return {data:null, error:{message:'game not released'}}; return {data:{...C, pending:Math.floor(C.daily*2)}, error:null}; }
      if(name === 'co_collect'){ C.cash += C.daily*2; C.last = new Date().toISOString(); return {data:{...C, pending:0}, error:null}; }
      if(name === 'co_upgrade'){ const r = C.routes.find(x=>x.k===a.p_route); if(!r) return {error:{message:'route not found'}}; if(C.cash < r.cost) return {error:{message:'not enough cash'}}; C.cash -= r.cost; r.level++; r.cost = r.base*3*r.level; C.daily = Math.round(r.base*(1+.25*(r.level-1))); return {data:{...C}, error:null}; }
      if(name === 'co_set_role'){ if(a.p_airport && a.p_airport !== 5) return {error:{message:'guardian not met'}}; C.roles[a.p_role] = a.p_airport; C.bonus = a.p_airport ? .1 : 0; return {data:{...C}, error:null}; }
      if(name === 'co_buy'){ if(a.p_type==='wb') return {error:{message:'aircraft locked'}}; C.cash -= 1000; C.fleet.push({id:C.fleet.length+1, type:a.p_type, route:null}); return {data:{...C}, error:null}; }
      if(name === 'co_assign'){ const ac = C.fleet.find(x=>x.id===a.p_aircraft); if(!ac) return {error:{message:'aircraft not found'}}; C.fleet.forEach(x=>{ if(x.route===a.p_route) x.route=null; }); ac.route = a.p_route; const r=C.routes.find(x=>x.k==='5-6'); r.mult = a.p_route ? 1.1 : 1; return {data:{...C}, error:null}; }
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
      return {data:{ok:true, at, airport_id:n.a.id, terminal_id:n.term?n.term.id:null, first_airport:first, first_terminal:true, flight:null, flags:[]}, error:null};
    }}
  }; } };
})();
