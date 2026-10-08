# 経済バランスのシミュレーション
# 4タイプの利用者（ライト・ふつう・ヘビー・修行）が2年間遊んだときの、収益と節目の時期を出す。
# 数値を変えるときは make_econ / current を変え、アプリの ECON とSQLの関数も同じ値にする。
#   python3 tools/economy_sim.py
import json, math, random
import os
A = {a['iata']: a for a in json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'airports_jp.json'))) if a['game_target'] and a['iata']}
def km(a,b):
    R=6371; r=math.pi/180; dl=(b['lat']-a['lat'])*r; dn=(b['lon']-a['lon'])*r
    h=math.sin(dl/2)**2+math.cos(a['lat']*r)*math.cos(b['lat']*r)*math.sin(dn/2)**2; return 2*R*math.asin(math.sqrt(h))
# ---- 現在の数値（アプリの ECON と同じ） ----
def make_econ(**o):
    E = dict(cap=7, size=lambda a: 3 if a['radius_m']>=2000 else 2 if a['radius_m']>=1500 else 1.5,
        daily=lambda k,s1,s2: round(math.sqrt(k)*(s1+s2)*2), lvmul=lambda lv: 1+.25*(lv-1), maxlv=5,
        upcost=lambda base,lv: base*3*lv, roles=[.10,.05,.15], rankb=.02,
        ac=[('prop',1.10,1000,0,1.5),('rj',1.25,2500,2000,1.5),('nb',1.50,5000,5000,2),('wb',1.90,15000,20000,3),('lg',2.30,40000,40075,3)],
        rep=dict(airport=10,route=20,upgrade=5,aircraft=15,facility=10,role=10), stars=[0,100,300,700,1500], perstar=.05,
        fac_cost=[0,3000,8000,20000], fac_per=.10)
    E.update(o); return E
def tier(n): return 5 if n>=365 else 4 if n>=100 else 3 if n>=20 else 2 if n>=5 else 1 if n>=3 else 0
MAIN = ['CTS','FUK','OKA','ITM','KOJ','HIJ','KMJ','NGS','KMQ','SDJ','AOJ','HKD','OIT','MYJ','KCZ','TAK','OKJ','UBJ','MMY','ISG','ASJ','AXT','KUH','AKJ']
def run(E, trips_per_month, persona, months=24, seed=1, open_every=2):
    random.seed(seed); home = A['HND']
    visits = {}; routes = {}; fleet = []; fac = {}; cash = 0; totalkm = 0; levels = {}
    ev = {}; daily_at = {}; dest_i = 0; cur_dest = 'CTS'
    def addv(i): visits[i] = visits.get(i,0)+1
    def S(a): return E['size'](a)
    def route_rows():
        out=[]
        for k,(a,b,d) in routes.items():
            base=E['daily'](d,S(a),S(b)); lv=levels.get(k,1)
            ac=next((f for f in fleet if f['route']==k),None); m=ac['mult'] if ac else 1
            hub=1+E['fac_per']*(fac.get(a['iata'],0)+fac.get(b['iata'],0))
            out.append(dict(k=k,a=a,b=b,base=base,lv=lv,ac=ac,m=m,hub=hub,mins=min(S(a),S(b))))
        return out
    def roles_bonus():
        top = sorted(visits.items(), key=lambda x:-x[1])[:3]
        return sum(p + E['rankb']*tier(n) for p,(i,n) in zip(sorted(E['roles'],reverse=True), top))
    def rep():
        rs=route_rows(); R=E['rep']
        return (len(visits)*R['airport'] + len(rs)*R['route'] + sum(r['lv']-1 for r in rs)*R['upgrade'] + len(fleet)*R['aircraft']
                + sum(fac.values())*R['facility'] + min(3,len(visits))*R['role'])
    def stars(): p=rep(); return max(i+1 for i,t in enumerate(E['stars']) if p>=t)
    def daily():
        b = roles_bonus() + E['perstar']*(stars()-1)
        return round(sum(r['base']*E['lvmul'](r['lv'])*r['m']*r['hub'] for r in route_rows())*(1+b))
    def mark(name, day):
        if name not in ev: ev[name]=day
    last_collect = 0; flights_done = 0
    days = months*30; trip_days = sorted(random.sample(range(days), trips_per_month*months)) if trips_per_month*months<=days else list(range(days))
    trip_set = {}
    for d in trip_days: trip_set[d] = trip_set.get(d,0)+1
    for day in range(days):
        for _ in range(trip_set.get(day,0)):
            if persona=='shugyo': dest = random.choice(['OKA','OKA','ISG','CTS','FUK','MMY'])
            else:
                if flights_done % 4 == 0: cur_dest = MAIN[dest_i % len(MAIN)]; dest_i += 1
                dest = cur_dest
            a, b = home, A[dest]; d = km(a,b)
            for x,y in ((a,b),(b,a)):
                addv(x['iata']); addv(y['iata']); k='-'.join(sorted([x['iata'],y['iata']]))
                routes.setdefault(k,(x,y,d)); totalkm += d; flights_done += 1
        if day % open_every == 0 and routes:
            el = min(day-last_collect, E['cap']); cash += daily()*el; last_collect = day
            # 投資：回収日数が短い順に、払えるうちは買う
            for _ in range(50):
                best=None; rs=route_rows(); b=1+roles_bonus()+E['perstar']*(stars()-1)
                for r in rs:
                    if r['lv']<E['maxlv']:
                        c=E['upcost'](r['base'],r['lv']); g=r['base']*.25*r['m']*r['hub']*b
                        best=min(best or (9e9,0,None), (c/g, c, ('up',r['k'])))
                for (t,m,price,unl,mins) in E['ac']:
                    if totalkm < unl: continue
                    cand=[r for r in rs if r['mins']>=mins and r['m']<m]
                    if not cand: continue
                    r=max(cand,key=lambda r:r['base']*E['lvmul'](r['lv'])*r['hub']*(m-r['m']))
                    g=r['base']*E['lvmul'](r['lv'])*r['hub']*(m-r['m'])*b
                    pr=round(price*(1+E.get('ac_esc',0)*len(fleet)))
                    best=min(best or (9e9,0,None), (pr/g, pr, ('ac',t,m,r['k'])))
                slots=stars()
                for iata in visits:
                    lv=fac.get(iata,0)
                    if lv>=3 or (lv==0 and len(fac)>=slots): continue
                    c=E['fac_cost'][lv+1]; g=sum(r['base']*E['lvmul'](r['lv'])*r['m']*E['fac_per'] for r in rs if iata in (r['a']['iata'],r['b']['iata']))*b
                    if g<=0: continue
                    best=min(best or (9e9,0,None), (c/g, c, ('fac',iata)))
                if not best or best[2] is None or best[1]>cash or best[0]>365: break
                cash-=best[1]; act=best[2]
                if act[0]=='up': levels[act[1]]=levels.get(act[1],1)+1; mark('初の増便',day)
                elif act[0]=='ac':
                    for f in fleet:
                        if f['route']==act[3]: f['route']=None
                    fleet.append(dict(t=act[1],mult=act[2],route=act[3])); mark('初の機材',day); mark('機材:'+act[1],day)
                else: fac[act[1]]=fac.get(act[1],0)+1; mark('初の施設',day)
        st=stars()
        for s in range(2,st+1): mark(f'★{s}',day)
        for (t,m,price,unl,mins) in E['ac']:
            if totalkm>=unl and unl>0: mark('解放:'+t,day)
        for mth in (3,6,12,24):
            if day==mth*30-1: daily_at[mth]=(daily(), cash, round(totalkm), stars(), len(fleet), sum(fac.values()))
    return ev, daily_at
PERS=[('ライト',1,'n',7),('ふつう',2,'n',3),('ヘビー',4,'n',2),('修行',10,'shugyo',1)]
def report(E, title):
    print('=== ',title)
    for name,tpm,p,oe in PERS:
        ev,da=run(E,tpm,p,open_every=oe)
        mo=lambda k: f"{ev[k]/30:.1f}か月" if k in ev else '—'
        print(f"[{name}] 初の増便{mo('初の増便')} 初の機材{mo('初の機材')} 初の施設{mo('初の施設')} ★2{mo('★2')} ★3{mo('★3')} ★4{mo('★4')} ★5{mo('★5')} | 解放 rj{mo('解放:rj')} nb{mo('解放:nb')} wb{mo('解放:wb')} lg{mo('解放:lg')}")
        for m,(d,c,k,s,f,fa) in da.items(): print(f"    {m:>2}か月: 1日の収益{d:>6,}万円 手持ち{c:>8,}万円 累計{k:>6,}km ★{s} 機材{f} 施設段数{fa}")
def current():
    C=10; ac=[(t,m,p*C,u,sz) for (t,m,p,u,sz) in make_econ()['ac']]
    return make_econ(upcost=lambda base,lv: base*30*lv*lv, ac=ac, ac_esc=.25, fac_cost=[0,30000,80000,200000], stars=[0,100,250,550,1000])
if __name__ == '__main__':
    report(current(), '現在の数値（2026年10月の調整後）')
