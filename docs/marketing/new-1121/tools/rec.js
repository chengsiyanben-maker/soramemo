const { chromium } = require('playwright'); const fs=require('fs');
async function openRec(name){
 const b=await chromium.launch();
 const c=await b.newContext({viewport:{width:390,height:693},deviceScaleFactor:3,locale:'ja-JP',timezoneId:'Asia/Tokyo',geolocation:{latitude:35.5494,longitude:139.7798},permissions:['geolocation']});
 const p=await c.newPage();
 await p.goto('https://soramemo.jp/',{waitUntil:'networkidle',timeout:60000});
 await p.waitForTimeout(2500);
 const t=p.getByText('とばす',{exact:true}); if(await t.count()) await t.first().click().catch(()=>{});
 await p.waitForTimeout(800);
 const inDlg=p.locator('#dAuth[open] button:has-text("デモ")');
 if(await inDlg.count()){ await inDlg.first().click(); } else { await p.evaluate(()=>document.getElementById('gateDemo').click()); }
 await p.waitForTimeout(4000);
 const dir='vid/'+name; fs.mkdirSync(dir,{recursive:true});
 const s=await c.newCDPSession(p); const frames=[]; let recording=false;
 s.on('Page.screencastFrame',async f=>{ if(recording){const fn=`${dir}/f${String(frames.length).padStart(5,'0')}.jpg`; fs.writeFileSync(fn,Buffer.from(f.data,'base64')); frames.push([fn,f.metadata.timestamp]);} s.send('Page.screencastFrameAck',{sessionId:f.sessionId}).catch(()=>{});});
 const marks={}; let T0=0;
 let loop=null;
 const SLOW=4; const rec=async()=>{ await s.send('Animation.enable'); await s.send('Animation.setPlaybackRate',{playbackRate:1/SLOW}); recording=true; T0=Date.now()/1000; loop=(async()=>{ while(recording){ const t=Date.now()/1000; try{ const lm=await s.send('Page.getLayoutMetrics'); const vv=lm.cssVisualViewport; const r=await s.send('Page.captureScreenshot',{format:'jpeg',quality:90,optimizeForSpeed:true,clip:{x:vv.pageX,y:vv.pageY,width:390,height:693,scale:2.77}}); const fn=`${dir}/f${String(frames.length).padStart(5,'0')}.jpg`; fs.writeFileSync(fn,Buffer.from(r.data,'base64')); frames.push([fn,t]); }catch(e){} } })(); };
 const mark=k=>{marks[k]=Date.now()/1000-T0;};
 const done=async()=>{ recording=false; await loop; fs.writeFileSync(dir+'.json',JSON.stringify({frames,marks,T0,SLOW},null,0)); await c.close(); await b.close(); };
 const W=ms=>p.waitForTimeout(recording?ms*SLOW:ms); const D=(x1,y1,x2,y2,steps,dt)=>drag(p,x1,y1,x2,y2,steps,(dt||16)*(recording?SLOW:1));
 return {b,c,p,mark,done,rec,W,D};
}
async function drag(p,x1,y1,x2,y2,steps=30,dt=16){await p.mouse.move(x1,y1);await p.mouse.down();for(let i=1;i<=steps;i++){await p.mouse.move(x1+(x2-x1)*i/steps,y1+(y2-y1)*i/steps);await p.waitForTimeout(dt);}await p.mouse.up();}
const tab=async(p,n)=>{await p.locator('nav').getByText(n,{exact:true}).first().click().catch(async()=>{await p.getByText(n,{exact:true}).last().click()});};
module.exports={openRec,drag,tab};
