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
      if(name === 'co3_set_policy'){ if(!['fsc','mcc','lcc','cargo','pj','regional'].includes(a.p_policy)) return {error:{message:'invalid policy'}}; C.policy = a.p_policy; window.__setPol = a; return {data:{...C}, error:null}; }
      if(name === 'co3_seen_list'){ return {data:(window.__seen || []).map(x => ({...x, owned:(C.fleet.find(f => f.reg === x.reg) || {}).id || null})), error:null}; }
      if(name === 'co3_buy_seen'){ const x = (window.__seen || []).find(s => s.reg === a.p_reg); if(!x) return {error:{message:'not seen'}}; if(window.__seenLimit) return {error:{message:'seen limit per day'}}; if(C.cash < x.price) return {error:{message:'not enough cash'}}; C.cash -= x.price; C.fleet.push({id:C.fleet.length+1, ride:'s:'+x.reg, type:'wb', reg:x.reg, icao:x.code, intl:false, route:null, paid:x.price, age:1, value:x.price, sell:Math.round(x.price*.3), upkeep:39, bought_at:new Date().toISOString(), rode_on:null, flight:x.flight}); return {data:{...C}, error:null}; }
      if(name === 'co3_cargo_assign'){ const ac = C.fleet.find(x => x.id === a.p_aircraft); if(!ac || ac.kind !== 'freighter') return {error:{message:'not a freighter'}}; C.fleet.forEach(x => { if(a.p_route && x.route === a.p_route) x.route = null; }); ac.route = a.p_route; window.__cargoAssign = a;
        (C.cargo || []).forEach(e => { if(e.k === a.p_route){ e.ac_id = ac.id; e.flights = 2; e.payload = 268; e.carried = 227.8; e.revenue = 1685; e.cost = 694; e.landing = 39; e.profit = 952; } else if(e.ac_id === ac.id){ e.ac_id = null; e.flights = 0; e.payload = 0; e.carried = 0; e.revenue = 0; e.cost = 0; e.landing = 0; e.profit = 0; } }); return {data:{...C}, error:null}; }
      if(name === 'co3_set_flights'){ if(a.p_flights != null && a.p_flights % 2) return {error:{message:'invalid flights'}}; C.plans = Object.assign({}, C.plans); if(a.p_flights == null) delete C.plans[a.p_route]; else C.plans[a.p_route] = a.p_flights; window.__setFl = a;
        (C.pj || []).forEach(e => { if(e.k === a.p_route){ e.flights = a.p_flights == null ? 4 : Math.min(4, a.p_flights); } }); return {data:{...C}, error:null}; }
      if(name === 'co3_buy_small'){ const t = (C.small || []).find(x => x.code === a.p_code); if(!t) return {error:{message:'not a small aircraft'}}; if(C.cash < t.price) return {error:{message:'not enough cash'}}; C.cash -= t.price; C.fleet.push({id:C.fleet.length+1, ride:'m:'+t.code, type:'prop', reg:'SM-00'+(C.fleet.length+10), icao:t.code, kind:'light', intl:false, route:null, paid:t.price, age:1, value:t.price, sell:Math.round(t.price*.3), upkeep:2, bought_at:new Date().toISOString(), rode_on:null, flight:null}); window.__buySmall = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_home'){ C.home = a.p_airport; C.home_since = new Date().toISOString().slice(0, 10); window.__setHome = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_premium'){ const ok = C.policy === 'fsc' ? [0, 10, 20, 30] : C.policy === 'mcc' ? [0, 10] : [0]; if(!ok.includes(a.p_pct)) return {error:{message:'premium not allowed'}}; C.premium = a.p_pct; window.__setPrem = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_fare'){ C.fares = Object.assign({}, C.fares); const f = C.fares[a.p_route] || {level:0, others:[]}; const today = new Date(Date.now() + 9 * 36e5).toISOString().slice(0, 10); if(f.set_on === today && f.level !== a.p_level) return {error:{message:'fare once a day'}}; C.fares[a.p_route] = {...f, level:a.p_level, set_on:today}; window.__setFare = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_service'){ C.meal = a.p_meal; C.bag = a.p_bag; const sp = C.sat_parts = Object.assign({}, C.sat_parts); sp.meal = {free:8, paid:-3, none:-8}[a.p_meal]; sp.bag = a.p_bag === 'paid' ? -4 : 0; window.__setSvc = a; return {data:{...C}, error:null}; }
      if(name === 'co3_trouble_respond'){ const t = (C.troubles || []).find(x => x.id === a.p_id); if(!t) return {error:{message:'trouble not found'}}; if(t.result) return {error:{message:'already done'}};
        const rate = {transfer:.2, hotel:.3, snack:.1}[a.p_card], cost = Math.ceil(rate * t.rev_flight * t.cancelled); if(C.cash < cost) return {error:{message:'not enough cash'}};
        C.cash -= cost; t.card = a.p_card; t.cost = cost; t.done_at = new Date().toISOString(); t.result = a.p_card === 'transfer' && Date.now() <= Date.parse(t.god_until) ? 'god' : 'normal'; if(t.result === 'god') C.satisfaction = Math.min(100, C.satisfaction + 8); window.__trResp = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_auto_trouble'){ C.auto_trouble = !!a.p_on; window.__trAuto = a; return {data:{...C}, error:null}; }
      if(name === 'co3_set_schedule'){ const legs = a.p_legs; if(!legs.length) return {error:{message:'legs 1 to 16'}}; for(let i = 1; i < legs.length; i++) if(legs[i].dep !== legs[i - 1].arr) return {error:{message:'not connected at ' + (i + 1)}};
        if(legs[legs.length - 1].arr !== legs[0].dep) return {error:{message:'must end at ' + legs[0].dep}}; C.scheds = Object.assign({}, C.scheds); C.scheds[a.p_aircraft] = legs.map((l, i) => ({n:i + 1, k:'5-6', f:l.dep, to:l.arr, t:l.t, ta:l.t + 80})); window.__setSched = a; return {data:{...C}, error:null}; }
      if(name === 'co3_clear_schedule'){ C.scheds = Object.assign({}, C.scheds); delete C.scheds[a.p_aircraft]; window.__clearSched = a; return {data:{...C}, error:null}; }
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
