const {openRec,drag,tab}=require('./rec');
(async()=>{const {p,mark,done,rec,W,D}=await openRec('L');
await p.waitForTimeout(1500); await rec(); mark('start'); await W(1500);
mark('tapPin'); await p.getByText('ピン止め',{exact:true}).first().click(); await W(3500);
mark('done'); await p.getByText('完了',{exact:true}).first().click(); await W(1500);
// open sheet upward
mark('sheet'); await D(195,356,195,110,30,20); await W(2500);
const pin=p.locator('text=ピン止めした空港').first(); if(await pin.count()){await pin.scrollIntoViewIfNeeded().catch(()=>{});} await W(2500);
mark('end'); await p.screenshot({path:'L_end.png'}); await done();})();
