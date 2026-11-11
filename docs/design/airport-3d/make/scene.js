// そらメモ 空港の3D：画面案用の小さな描き手（外部の読み込みなし・止まった絵）
// 形は羽田のおおまかな配置（仮）。座標はメートル、x 東・y 北・z 上
(function(){
const R = Math.PI/180;
const d = [Math.sin(337*R), Math.cos(337*R)];   // A・C 滑走路の向き
const p = [d[1], -d[0]];                         // それと直角（東寄り）
const P = (a,b,z=0) => [a*p[0]+b*d[0], a*p[1]+b*d[1], z];
const dir = h => [Math.sin(h*R), Math.cos(h*R)];
function strip(cx,cy,h,len,w){ const u=dir(h), v=[u[1],-u[0]]; const L=len/2,W=w/2;
  return [[cx-u[0]*L-v[0]*W, cy-u[1]*L-v[1]*W,0],[cx+u[0]*L-v[0]*W, cy+u[1]*L-v[1]*W,0],[cx+u[0]*L+v[0]*W, cy+u[1]*L+v[1]*W,0],[cx-u[0]*L+v[0]*W, cy-u[1]*L+v[1]*W,0]]; }
const C = P(950,  100), A = P(-750, 250), B = P(-1300,-1650), D = P(2350,-2500);
const RW = [ {n:'A',c:A,h:337,len:3000}, {n:'C',c:C,h:337,len:3360}, {n:'B',c:B,h:40,len:2500}, {n:'D',c:D,h:50,len:2500} ];
const ISLAND = [P(-2600,-2350),P(-1950,-2550),P(-150,-1500),P(600,-1750),P(1350,-1850),P(1500,-1200),P(1450,2050),P(800,2300),P(-1100,2050),P(-1900,1500),P(-2100,0)];
const DISL   = strip(D[0],D[1],50,2900,520);
const DNW = [D[0]-dir(50)[0]*1250, D[1]-dir(50)[1]*1250, 0];
const TWY = [ [P(-560,-1400),P(-560,1700)], [P(760,-1500),P(760,1800)], [P(-560,-200),P(760,-200)], [P(-560,900),P(760,900)], [P(-560,-1300),P(-1000,-1600)], [P(760,-1500),P(1300,-1650)], [P(1300,-1650),DNW] ];
// 建物：中心(a,b)・幅・奥行き・高さ・向き
const DIRTMP=0;
const BLD = [ {n:'T1',a:-150,b:500,w:180,l:620,h:38}, {n:'T2',a:390,b:300,w:180,l:650,h:38}, {n:'T3',a:-1450,b:150,w:200,l:700,h:34},
  {n:'P1',a:120,b:500,w:120,l:260,h:22}, {n:'H',a:-1150,b:-1250,w:260,l:380,h:30}, {n:'H2',a:-1500,b:-700,w:220,l:300,h:26} ];
const TOWER = {a:640,b:-420,h:115};
window.HND = {P,d,p,RW,BLD,TOWER};

function sub(a,b){return [a[0]-b[0],a[1]-b[1],a[2]-b[2]]} function dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]}
function cross(a,b){return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]} function nrm(a){const l=Math.hypot(...a);return [a[0]/l,a[1]/l,a[2]/l]}
function hex(c){if(c.startsWith('rgb'))return c.match(/[\d.]+/g).slice(0,3).map(Number);c=c.replace('#','');return [parseInt(c.slice(0,2),16),parseInt(c.slice(2,4),16),parseInt(c.slice(4,6),16)]}
function mix(a,b,t){const A=hex(a),B=hex(b);return 'rgb('+A.map((v,i)=>Math.round(v+(B[i]-v)*t)).join(',')+')'}
function shade(c,k){return k>=1?mix(c,'#ffffff',Math.min(1,k-1)):mix(c,'#000000',1-k)}

const SKY = {
 day:   {top:'#8DB8E3', hor:'#E4EEF7', sea:'#9CC0DE', land:'#E4E9DF', land2:'#DCE3D5', rw:'#4F555D', twy:'#A3A9B0', bld:'#F7F8FA', roof:'#E4E7EC', mark:'#FFFFFF', fog:'#E7F0F8', fogd:16000, light:1.0, sun:null},
 dusk:  {top:'#5A6E9C', hor:'#F2B98A', sea:'#6E7FA8', land:'#C7C2BF', land2:'#BCB7B5', rw:'#4D4F57', twy:'#77777E', bld:'#EDE3DA', roof:'#D7CCC3', mark:'#F4EDE6', fog:'#E9B994', fogd:8000, light:.85, sun:'#FFD7A8'},
 night: {top:'#070B14', hor:'#18233A', sea:'#0B1322', land:'#1A2130', land2:'#161C29', rw:'#252B36', twy:'#2B3240', bld:'#3A4458', roof:'#30394B', mark:'#3B4456', fog:'#18233A', fogd:9000, light:.55, sun:null, lights:true},
 fog:   {top:'#BFC6CE', hor:'#D9DDE1', sea:'#C3CAD1', land:'#D3D7D6', land2:'#CDD1D0', rw:'#7B8087', twy:'#9EA3A9', bld:'#E8EAEC', roof:'#DADDE0', mark:'#EEF0F2', fog:'#D9DDE1', fogd:3800, light:.9, sun:null},
};

// 機体の見本（便名などは見本）
const PLANES = [
 {id:'NH241', fl:'NH 241', to:'福岡から', arr:true, st:'着陸まで約3分', ty:'B787-9', reg:'JA871A', alt:420,  pos:P(950,-3300), h:337, z:420, sp:true},
 {id:'JL109', fl:'JL 109', to:'伊丹へ',  st:'離陸中',         ty:'A350-900', reg:'JA06XJ', alt:0, pos:P(-750,-300), h:337, z:0},
 {id:'NH59',  fl:'NH 59',  to:'札幌へ',  st:'上昇中',  ty:'B777-200', reg:'JA743A', alt:1800, pos:P(1300,3400), h:337, z:900},
 {id:'JL903', fl:'JL 903', to:'那覇へ',  st:'出発準備',       ty:'B767-300ER', reg:'JA613J', alt:0, pos:P(-290,300), h:67, z:0},
 {id:'JL461', fl:'JL 461', to:'松山へ',  st:'出発準備',       ty:'B737-800', reg:'JA330J', alt:0, pos:P(-290,700), h:67, z:0},
 {id:'NH17',  fl:'NH 17',  to:'伊丹へ',  st:'駐機中',         ty:'B787-8', reg:'JA804A', alt:0, pos:P(530,100), h:247, z:0},
 {id:'NH255', fl:'NH 255', to:'福岡へ',  st:'駐機中',         ty:'B777-300', reg:'JA752A', alt:0, pos:P(530,450), h:247, z:0},
 {id:'BC509', fl:'BC 509', to:'神戸へ',  st:'地上を走行中',   ty:'B737-800', reg:'JA737X', alt:0, pos:P(760,-500), h:157, z:0},
 {id:'NH981', fl:'NH 981', to:'石垣へ',  st:'駐機中',         ty:'A321neo', reg:'JA136A', alt:0, pos:P(530,-30), h:247, z:0},
 {id:'JL123', fl:'JL 123', to:'伊丹へ',  st:'駐機中',         ty:'B767-300ER', reg:'JA654J', alt:0, pos:P(-290,-40), h:67, z:0},
 {id:'NH31',  fl:'NH 31',  to:'伊丹へ',  st:'駐機中',         ty:'B787-9', reg:'JA882A', alt:0, pos:P(-1290,300), h:67, z:0},
 {id:'JL43',  fl:'JL 43',  to:'ロンドンへ', st:'駐機中',       ty:'B777-300ER', reg:'JA731J', alt:0, pos:P(-1290,-100), h:67, z:0},
];
window.HND.PLANES = PLANES;

function camFrom(pos, tgt, fov, W, H){ const f=nrm(sub(tgt,pos)); const r=nrm(cross(f,[0,0,1])); const u=cross(r,f); const F=(H/2)/Math.tan(fov*R/2); return {pos,f,r,u,F,W,H}; }
function proj(c,q){ const v=sub(q,c.pos); const z=dot(v,c.f); return [c.W/2+dot(v,c.r)/z*c.F, c.H*c.cy-dot(v,c.u)/z*c.F, z]; }
function clip(c,pts){ const N=4; const out=[]; for(let i=0;i<pts.length;i++){ const a=pts[i],b=pts[(i+1)%pts.length]; const za=dot(sub(a,c.pos),c.f), zb=dot(sub(b,c.pos),c.f);
  if(za>=N) out.push(a); if((za>=N)!==(zb>=N)){ const t=(N-za)/(zb-za); out.push([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t]); } } return out; }

function box(cx,cy,w,l,h,ang,z0=0){ const u=dir(ang), v=[u[1],-u[0]]; const L=l/2,W=w/2; const b=[[-W,-L],[W,-L],[W,L],[-W,L]].map(([s,t])=>[cx+v[0]*s+u[0]*t, cy+v[1]*s+u[1]*t]);
  const faces=[]; for(let i=0;i<4;i++){const a=b[i],c=b[(i+1)%4]; faces.push({pts:[[a[0],a[1],z0],[c[0],c[1],z0],[c[0],c[1],z0+h],[a[0],a[1],z0+h]]});}
  faces.push({pts:b.map(q=>[q[0],q[1],z0+h]), top:true}); return faces; }

function planeFaces(pl, s){ const u=dir(pl.h), v=[u[1],-u[0]]; const [x,y]=pl.pos; const z=pl.z; const L=34*s, Wd=3*s, Sp=30*s;
  const pt=(a,b,c)=>[x+u[0]*a+v[0]*b, y+u[1]*a+v[1]*b, z+c+ (z===0?3*s:0)];
  const F=[]; // 胴体（細い箱）
  const fb=[[-L,-Wd],[L,-Wd],[L,Wd],[-L,Wd]];
  for(let i=0;i<4;i++){const a=fb[i],c=fb[(i+1)%4]; F.push({pts:[pt(a[0],a[1],0),pt(c[0],c[1],0),pt(c[0],c[1],Wd*1.6),pt(a[0],a[1],Wd*1.6)], pl});}
  F.push({pts:fb.map(q=>pt(q[0],q[1],Wd*1.6)), pl, top:true});
  F.push({pts:[pt(4,-Wd,Wd*.6),pt(-10,-Sp,Wd*.6),pt(-16,-Sp,Wd*.6),pt(-8,-Wd,Wd*.6)], pl, wing:true});
  F.push({pts:[pt(4,Wd,Wd*.6),pt(-10,Sp,Wd*.6),pt(-16,Sp,Wd*.6),pt(-8,Wd,Wd*.6)], pl, wing:true});
  F.push({pts:[pt(-L+2,0,Wd*1.6),pt(-L+12,0,Wd*1.6),pt(-L+3,0,Wd*1.6+12*s)], pl, fin:true});
  F.push({pts:[pt(-L+4,-11*s,Wd*1.2),pt(-L+10,-1,Wd*1.2),pt(-L+10,1,Wd*1.2),pt(-L+4,11*s,Wd*1.2)], pl, wing:true});
  return F; }

// 描く：opt = {sky, cam:{pos,tgt,fov,cy}, planeScale, light:false(軽い版), labels:true, sel:'NH241'}
window.drawAirport = function(cv, opt){
  const dpr = window.devicePixelRatio||1; const W=cv.clientWidth, H=cv.clientHeight; cv.width=W*dpr; cv.height=H*dpr;
  const g=cv.getContext('2d'); g.setTransform(dpr,0,0,dpr,0,0);
  const S=SKY[opt.sky||'day']; const c=camFrom(opt.cam.pos,opt.cam.tgt,opt.cam.fov||50,W,H); c.cy=opt.cam.cy||.5;
  const fogT = z => 1-Math.exp(-Math.max(0,z)/S.fogd);
  const col = (cc,z) => mix(cc, S.fog, Math.min(.92,fogT(z)));
  // 空
  const fh=nrm([c.f[0],c.f[1],0]); const hy = c.H*c.cy - c.F*dot(fh,c.u)/dot(fh,c.f);
  const gr=g.createLinearGradient(0,0,0,Math.max(10,hy)); gr.addColorStop(0,S.top); gr.addColorStop(1,S.hor); g.fillStyle=gr; g.fillRect(0,0,W,H);
  if(S.sun){ const sg=g.createRadialGradient(W*.18,hy-8,2,W*.18,hy-8,120); sg.addColorStop(0,S.sun); sg.addColorStop(1,'rgba(255,215,168,0)'); g.fillStyle=sg; g.fillRect(0,0,W,H); }
  g.fillStyle=mix(S.sea,S.fog,.12); g.fillRect(0,hy,W,H-hy);
  const poly=(pts,fill,stroke)=>{ const q=clip(c,pts); if(q.length<3) return; g.beginPath(); q.forEach((pp,i)=>{const s=proj(c,pp); i?g.lineTo(s[0],s[1]):g.moveTo(s[0],s[1]);}); g.closePath(); g.fillStyle=fill; g.fill(); if(stroke){g.strokeStyle=stroke;g.lineWidth=.6;g.stroke();} };
  const avgz = pts => pts.reduce((s,q)=>s+dot(sub(q,c.pos),c.f),0)/pts.length;
  // 地面
  poly(ISLAND, col(S.land, avgz(ISLAND)*.6)); poly(DISL, col(S.land2, avgz(DISL)*.8));
  TWY.forEach(([a,b])=>{ const h=Math.atan2(b[0]-a[0],b[1]-a[1])/R; const len=Math.hypot(b[0]-a[0],b[1]-a[1]); const s=strip((a[0]+b[0])/2,(a[1]+b[1])/2,h,len,opt.light?60:45); poly(s,col(S.twy,avgz(s))); });
  RW.forEach(r=>{ const s=strip(r.c[0],r.c[1],r.h,r.len,60); poly(s,col(S.rw,avgz(s)));
    if(!opt.light){ const u=dir(r.h); for(let t=-r.len/2+120;t<r.len/2-120;t+=110){ const m=strip(r.c[0]+u[0]*t,r.c[1]+u[1]*t,r.h,45,2.5); poly(m,col(S.mark,avgz(m))); }
      [-1,1].forEach(e=>{ for(let k=-3;k<=3;k++){ if(!k) continue; const v=[u[1],-u[0]]; const cx=r.c[0]+u[0]*e*(r.len/2-40)+v[0]*k*7, cy=r.c[1]+u[1]*e*(r.len/2-40)+v[1]*k*7; const m=strip(cx,cy,r.h,40,3); poly(m,col(S.mark,avgz(m))); } }); } });
  // 夜の灯り（白＝滑走路の縁・緑＝誘導路の中心線・琥珀＝建物の窓）
  const dots=[];
  if(S.lights && !opt.light){
    RW.forEach(r=>{ const u=dir(r.h), v=[u[1],-u[0]]; for(let t=-r.len/2;t<=r.len/2;t+=90){ [-32,32].forEach(o=>dots.push({q:[r.c[0]+u[0]*t+v[0]*o, r.c[1]+u[1]*t+v[1]*o, 1], c:'#F4F7FB', s:1.3})); }
      // 進入灯（南の端から海へ）
      if(r.n==='A'||r.n==='C'){ for(let t=60;t<=900;t+=60){ dots.push({q:[r.c[0]-u[0]*(r.len/2+t), r.c[1]-u[1]*(r.len/2+t), 2], c:'#F4F7FB', s:1.6}); } } });
    TWY.forEach(([a,b])=>{ const n=Math.hypot(b[0]-a[0],b[1]-a[1])/70|0; for(let i=0;i<=n;i++){ dots.push({q:[a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n, 1], c:'#7EE2A8', s:1.1}); } });
  }
  // 立体（建物・塔・機体）を奥から
  const solids=[];
  BLD.forEach(b=>{ const q=P(b.a,b.b); const oz=dot(sub([q[0],q[1],0],c.pos),c.f); box(q[0],q[1],b.w,b.l,b.h*(opt.vx||1.6),337).forEach(f=>{f.kind='b'; f.bn=b.n; f.oz=oz; solids.push(f);}); });
  const tq=P(TOWER.a,TOWER.b); const th=TOWER.h*(opt.vx||1.6);
  if(!opt.hideTower){ const toz=dot(sub([tq[0],tq[1],0],c.pos),c.f); box(tq[0],tq[1],16,16,th,337).forEach(f=>{f.kind='b';f.oz=toz;solids.push(f);}); box(tq[0],tq[1],34,34,14,337,th).forEach(f=>{f.kind='cab';f.oz=toz-1;solids.push(f);}); }
  const ps = opt.planeScale||1;
  if(!opt.light && !opt.hideAll) PLANES.forEach(pl=>{ if(opt.hidePlane===pl.id) return; const oz=dot(sub([pl.pos[0],pl.pos[1],pl.z],c.pos),c.f); planeFaces(pl,ps*(pl.z?1.15:1)).forEach(f=>{f.kind='p';f.oz=oz;solids.push(f);}); });
  solids.forEach(f=>f.z=avgz(f.pts));
  const Ld=nrm([-.5,-.7,.6]);
  solids.sort((a,b)=>(b.oz-a.oz)||(b.z-a.z)).forEach(f=>{
    if(f.z<4) return;
    const e1=sub(f.pts[1],f.pts[0]), e2=sub(f.pts[2],f.pts[0]); let n=nrm(cross(e1,e2)); if(n[2]<0 && f.top) n=n.map(x=>-x);
    const lam=.72+.28*Math.abs(dot(n,Ld));
    let base = f.kind==='b' ? (f.top?S.roof:S.bld) : f.kind==='cab' ? (S.lights?'#3A4A5E':'#C9D6E3') : '#FFFFFF';
    if(f.kind==='p'){ base = S.lights ? '#9AA4B4' : (f.fin && f.pl.sp ? '#C9A24A' : (f.fin ? '#D5DAE1' : '#FFFFFF')); if(opt.sel && f.pl.id===opt.sel && !S.lights) base = f.fin?'#C9A24A':'#FFFFFF'; }
    if(f.kind==='p' && S.light<1 && !S.lights) base=mix(base,'#000000',(1-S.light)*.4);
    poly(f.pts, col(shade(base, lam*(S.lights?1:1)), f.z), f.kind==='p' ? 'rgba(40,50,64,.35)' : (S.lights?'rgba(150,170,200,.18)':'rgba(60,70,84,.12)'));
  });
  if(S.lights && !opt.light){
    BLD.forEach(b=>{ if(b.n[0]!=='T') return; const q=P(b.a,b.b); const u=dir(337), v=[u[1],-u[0]]; for(let t=-b.l/2+30;t<b.l/2;t+=40){ [-1,1].forEach(sd=>{ dots.push({q:[q[0]+u[0]*t+v[0]*sd*(b.w/2+1), q[1]+u[1]*t+v[1]*sd*(b.w/2+1), b.h*(opt.vx||1.6)*.55], c:'#FFB547', s:1.2}); }); } });
    dots.push({q:[tq[0],tq[1],th+8], c:'#7EE2A8', s:2.2});
    PLANES.forEach(pl=>{ if(opt.hidePlane===pl.id||opt.hideAll) return; dots.push({q:[pl.pos[0],pl.pos[1],pl.z+12*ps], c:'#F4F7FB', s:pl.z?2.6:1.6, glow:true}); });
  }
  dots.forEach(o=>{ const z=dot(sub(o.q,c.pos),c.f); if(z<5) return; const s=proj(c,o.q); if(s[0]<-10||s[0]>W+10||s[1]<-10||s[1]>H+10) return;
    const r=Math.max(.6,o.s*Math.min(1.6,2200/z)); const al=Math.max(.25,1-fogT(z));
    const gg=g.createRadialGradient(s[0],s[1],0,s[0],s[1],r*4); gg.addColorStop(0,o.c); gg.addColorStop(1,'rgba(0,0,0,0)'); g.globalAlpha=al*.55; g.fillStyle=gg; g.beginPath(); g.arc(s[0],s[1],r*4,0,7); g.fill();
    g.globalAlpha=al; g.fillStyle=o.c; g.beginPath(); g.arc(s[0],s[1],r,0,7); g.fill(); g.globalAlpha=1; });
  // 軽い版：機体は向きのある三角だけ
  if(opt.light) PLANES.forEach(pl=>{ const s=proj(c,[pl.pos[0],pl.pos[1],pl.z]); if(s[2]<5) return; const u=dir(pl.h); const a=proj(c,[pl.pos[0]+u[0]*120,pl.pos[1]+u[1]*120,pl.z]); const ang=Math.atan2(a[1]-s[1],a[0]-s[0]);
    g.save(); g.translate(s[0],s[1]); g.rotate(ang); g.fillStyle=opt.night?'#E8ECF1':'#2B3340'; g.beginPath(); g.moveTo(7,0); g.lineTo(-5,-4.5); g.lineTo(-3,0); g.lineTo(-5,4.5); g.closePath(); g.fill(); g.restore(); });
  // 機体の上の名札の位置を返す
  const tags={}; PLANES.forEach(pl=>{ const s=proj(c,[pl.pos[0],pl.pos[1],pl.z+ (pl.z?40:18)*ps]); tags[pl.id]={x:s[0],y:s[1],z:s[2]}; });
  const t2=proj(c,[tq[0],tq[1],th+20]); tags.TOWER={x:t2[0],y:t2[1],z:t2[2]};
  return tags;
};
})();
