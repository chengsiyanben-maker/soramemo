(function(){
  let session = null; const ls = [];
  let flagged = [{id:2, created_at:new Date().toISOString(), flags:['impossible_speed'], accuracy_m:20, lat:42.77, lon:141.69, airport:'新千歳空港', terminal_id:null, email:'user@example.com', user_checkins:3, user_flagged:2},
                 {id:3, created_at:new Date().toISOString(), flags:['low_accuracy','offline'], accuracy_m:600, lat:26.2, lon:127.65, airport:'那覇空港', terminal_id:null, email:'user@example.com', user_checkins:3, user_flagged:2}];
  let aal = 'aal1', factors = [], flags = {maintenance:{value:false, updated_at:new Date().toISOString()}, maintenance_message:{value:'', updated_at:new Date().toISOString()}, checkin_enabled:{value:true, updated_at:new Date().toISOString()}, logging_enabled:{value:true, updated_at:new Date().toISOString()}};
  window.__fa = { login(admin){ session = {user:{id: admin ? 'adm' : 'u'}}; window.__isAdmin = admin; aal = 'aal2'; ls.forEach(f => f('SIGNED_IN', session)); }, log:[], flags: () => flags };
  window.supabase = { createClient(){ return {
    auth:{ getSession: async () => ({data:{session}}), onAuthStateChange(f){ ls.push(f); },
      signInWithOtp: async (o) => { __fa.otpOpts = o.options; return {error:null}; },
      verifyOtp: async (o) => { if(!['123456','12345678'].includes(o.token)) return {error:{message:'invalid'}}; session = {user:{id: o.email.startsWith('admin') ? 'adm' : 'u'}}; window.__isAdmin = o.email.startsWith('admin'); aal = 'aal1'; return {data:{session}, error:null}; },
      signOut: async () => { session = null; aal = 'aal1'; ls.forEach(f => f('SIGNED_OUT', null)); },
      mfa:{ getAuthenticatorAssuranceLevel: async () => ({data:{currentLevel: aal, nextLevel: factors.some(x => x.status === 'verified') ? 'aal2' : 'aal1'}}),
            listFactors: async () => ({data:{totp: factors.filter(x => x.status === 'verified'), all: factors.map(x => Object.assign({factor_type:'totp'}, x))}}),
            unenroll: async (o) => { factors = factors.filter(x => x.id !== o.factorId); window.__unenrolled = (window.__unenrolled||0) + 1; return {error:null}; },
            enroll: async (o) => { if(factors.some(x => x.name === o.friendlyName)) return {error:{message:'A factor with the friendly name "' + o.friendlyName + '" for this user already exists'}};
              const id = 'f' + (factors.length + 1); factors.push({id, status:'unverified', name:o.friendlyName}); return {data:{id, totp:{qr_code:'data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22/>', secret:'ABCDEF'}}, error:null}; },
            challengeAndVerify: async (o) => { if(o.code !== '654321') return {error:{message:'bad'}}; factors.filter(x => x.id === o.factorId).forEach(x => x.status = 'verified'); aal = 'aal2'; return {data:{}, error:null}; } } },
    rpc: async (n, a) => { __fa.log.push(n);
      if(n === 'admin_registered') return {data: !!window.__isAdmin};
      if(n === 'is_admin') return {data: !!window.__isAdmin && aal === 'aal2'};
      if(n === 'admin_flags') return {data: flags};
      if(n === 'admin_last_backup') return {data: window.__lastBk || null};
      if(n === 'admin_backup'){ window.__lastBk = new Date().toISOString(); return {data:{app:'soramemo', format:1, users:[{id:'u',email:'u@x'}], checkins:[{id:1},{id:2}], flights:[{id:1}], manual_flights:[], companies:[], flags:[]}}; }
      if(n === 'admin_set_flag'){ if(!window.__isAdmin || aal !== 'aal2') return {error:{message:'admin only'}}; flags[a.p_key] = {value:a.p_value, updated_at:new Date().toISOString()}; return {data:null}; }
      if(!window.__isAdmin) return {error:{message:'admin only'}};
      if(n === 'admin_stats') return {data:{users:2, checkins_today:3, checkins_total:3, flagged:flagged.length, flights:1, verified:0, plus:0}};
      if(n === 'admin_flagged') return {data: flagged};
      if(n === 'admin_metrics'){ const daily = Array.from({length:a.p_days}, (_, i) => ({day:'2026-09-'+String(6+i).padStart(2,'0'), active:i%5+1, checkins:(i%7)*3+2, flights:i%4, signups:i%3, opens:(i%6)*2+3})); return {data:{daily, active7:12, active30:30, retention30:42.5, top_airports:[{name:'東京国際空港（羽田）', checkins:120, users:25},{name:'新千歳空港', checkins:80, users:20}], top_routes:[{route:'東京国際空港（羽田） ⇄ 新千歳空港', flights:44}], plus:{active:5, canceled_30:1}}}; }
      if(n === 'admin_usage') return {data:{sessions:320, platforms:[{platform:'ios', sessions:200},{platform:'android', sessions:110},{platform:'other', sessions:10}], events:[{event:'tab', prop:'book', n:500, sessions:180},{event:'checkin_ok', prop:'flight', n:90, sessions:80},{event:'share', prop:'stamp', n:30, sessions:25}]}};
      if(n === 'admin_errors') return {data:{rejections:[{reason:'out_of_range', n:40, queued:2},{reason:'low_accuracy', n:6, queued:0}], errors:[{kind:'js', message:'TypeError: Cannot read properties of null', n:7, sessions:4, last:new Date().toISOString(), version:'2026.10'}]}};
      if(n === 'admin_quality') return {data:[{id:5, name:'東京国際空港（羽田）', radius_m:2000, checkins:120, p50_m:330, p90_m:1720, max_m:2400, acc_p50_m:25, terminal_pct:88.5, near_miss:6},{id:6, name:'新千歳空港', radius_m:2000, checkins:80, p50_m:900, p90_m:1500, max_m:1900, acc_p50_m:30, terminal_pct:70, near_miss:0}]};
      if(n === 'admin_clear_flags'){ flagged = flagged.filter(x => x.id !== a.p_checkin); return {data:null}; }
      if(n === 'admin_void_checkin'){ __fa.reason = a.p_reason; flagged = flagged.filter(x => x.id !== a.p_checkin); return {data:1}; }
    } }; } };
})();
