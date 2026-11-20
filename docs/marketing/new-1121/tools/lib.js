const { chromium } = require('playwright');
async function open(dsf=1){
 const b=await chromium.launch(); const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:dsf,locale:'ja-JP',timezoneId:'Asia/Tokyo',geolocation:{latitude:35.5494,longitude:139.7798},permissions:['geolocation']});
 const p=await c.newPage(); await p.goto('https://soramemo.jp/',{waitUntil:'networkidle',timeout:60000});
 await p.waitForTimeout(2500);
 const t=p.getByText('とばす',{exact:true}); if(await t.count()) await t.first().click().catch(()=>{});
 await p.waitForTimeout(800);
 const inDlg=p.locator('#dAuth[open] button:has-text("デモ")');
 if(await inDlg.count()){ await inDlg.first().click(); } else { await p.evaluate(()=>document.getElementById('gateDemo').click()); }
 await p.waitForTimeout(4000);
 return {b,p};
}
async function vis(p){return (await p.$$eval('button,a,[role=tab],[data-pins-open]',els=>els.filter(e=>e.offsetParent).map(e=>e.innerText.trim().replace(/\s+/g,' ').slice(0,30)).filter(Boolean))).join(' | ');}
module.exports={open,vis};
