# 羽田の進入経路のデータを作る（AIP JAPAN 2026年10月1日版の進入チャート RJTT AD2.24-IAC から、座標を書き写したもの）。
# AIP が改訂されたら、チャートと見比べて座標を直し、python3 tools/hnd_approaches.py を実行して、出力を src/index.html の HND_APP に入れる。
# 実行すると、最後のフィックスが滑走路の延長線上の正しい距離にあるかを表示する（チャートの NM to THR と比べる）。
import math,json
def d(s):
  h=s[-1]; s=s[:-1]; k=3 if h=='E' else 2
  return round(int(s[:k])+int(s[k:k+2])/60+float(s[k+2:])/3600,6)
def P(a,b): return (d(a),d(b))
THR={'34L':P('353211.76N','1394708.41E'),'34R':P('353233.02N','1394811.34E'),'22':P('353402.88N','1394637.61E'),
 '23':P('353226.15N','1394919.61E'),'16L':P('353346.27N','1394719.34E'),'16R':P('353322.47N','1394618.19E')}
BRG={'34L':329.88,'34R':329.88,'22':215.01,'23':222.56,'16L':149.88,'16R':149.88}
R=3440.065
def dist(a,b):
  la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
  return 2*R*math.asin(math.sqrt(math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def brg(a,b):
  la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
  y=math.sin(lo2-lo1)*math.cos(la2); x=math.cos(la1)*math.sin(la2)-math.sin(la1)*math.cos(la2)*math.cos(lo2-lo1)
  return (math.degrees(math.atan2(y,x))+360)%360
def dest(a,b_deg,nm):
  la1,lo1=map(math.radians,a); t=math.radians(b_deg); dd=nm/R
  la2=math.asin(math.sin(la1)*math.cos(dd)+math.cos(la1)*math.sin(dd)*math.cos(t))
  lo2=lo1+math.atan2(math.sin(t)*math.sin(dd)*math.cos(la1),math.cos(dd)-math.sin(la1)*math.sin(la2))
  return (round(math.degrees(la2),6),round(math.degrees(lo2),6))
IKL=P('353614N','1394908E'); ITL=P('353410N','1394656E')
# 進入：[名前, 緯度, 経度]（AIP の順）。最後は滑走路の進入端
A={
 'ILS X 34L':[('KAIHO','351857.8N','1394642.4E'),('AVION','352437.2N','1395105.5E'),('ALLIE','352637.5N','1395105.3E'),('AZURE','352821.48N','1394951.68E')],
 'ILS Z 34L':[('CREAM','351743.4N','1400612.4E'),('ARLON','351525.3N','1395859.8E'),('APOLO','351919.32N','1395614.78E')],
 'ILS Z 34R':[('CREAM','351743.4N','1400612.4E'),('CLOAK','351548.0N','1400208.2E'),('CAMEL','351718.2N','1395857.8E'),('CACAO','352212.81N','1395530.14E')],
 'HIGHWAY 34R':[('CACAO','352212.81N','1395530.14E'),('D9.1','352448.50N','1395340.20E'),('D6.0','352729.78N','1395146.15E')],
 'LDA W 22':[('BACON','353155.0N','1401215.1E'),('BIBLO','353508.8N','1401108.1E'),('BEAST','353620.3N','1400834.5E'),('BONDO','353619.28N','1400442.48E')],
 'ILS 22':[('STEAM','355553.3N','1395708.4E'),('NINJA','355148.2N','1395855.9E'),('NEXUS','354748.9N','1395829.4E'),('NITRO','354610.70N','1395704.47E')],
 'LDA W 23':[('DATUM','354259.6N','1400824.3E'),('DARIO','353921.7N','1401240.5E'),('DISCO','353543.1N','1401415.4E'),('DANON','353418.1N','1401116.9E'),('DAMBO','353416.51N','1400443.37E')],
 'ILS Z 23':[('STEAM','355553.3N','1395708.4E'),('SWEET','355345.2N','1400203.7E'),('SNAKE','355235.0N','1400636.1E'),('SMILE','354436.4N','1400400.9E'),('SAROB','354053.05N','1395929.95E')],
 'RNP 16L':[('SANDY','354917.53N','1394402.84E'),('LYCEE','354454.12N','1394057.40E'),('LAUDA','354144.81N','1394139.05E'),('T6L61','353858.19N','1394337.69E'),('T6L64','353653.43N','1394506.41E')],
 'ILS 16L':[('SANDY','354917.5N','1394402.8E'),('LABAN','354917.1N','1394105.8E'),('LINEN','354916.6N','1393806.0E'),('LORRY','354642.5N','1393806.7E'),('LYCOS','354406.63N','1393957.91E')],
 'RNP 16R':[('NATTY','355350.86N','1394531.32E'),('RACER','355153.42N','1394034.41E'),('REMUS','354807.52N','1393755.52E'),('ROWAN','354506.89N','1393756.35E'),('RIPOD','354212.76N','1394000.68E'),('T6R73','353915.87N','1394206.79E'),('T6R74','353614.00N','1394416.28E')],
 'ILS 16R':[('NATTY','355350.9N','1394531.3E'),('RANGY','355231.6N','1394210.9E'),('RESIN','355027.5N','1393657.6E'),('RUGBY','354627.4N','1393658.8E'),('RONIE','354108.94N','1394046.23E')],
}
rw=lambda k:k.split()[-1]
out={}
for k,v in A.items():
  r=rw(k); t=THR[r]; pts=[(n,d(a),d(b)) for n,a,b in v]
  fa=pts[-1]; ext=(BRG[r]+180)%360
  dd=dist(t,(fa[1],fa[2])); off=(brg(t,(fa[1],fa[2]))-ext+540)%360-180
  print(f'{k:12s} 最後のフィックス {fa[0]} 進入端から {dd:.2f}NM 延長線とのずれ {off:+.2f}°', ' 区間:',' '.join(f'{pts[i][0]}-{pts[i+1][0]} {dist(pts[i][1:],pts[i+1][1:]):.1f}NM/{brg(pts[i][1:],pts[i+1][1:]):.0f}T' for i in range(len(pts)-1)))
  line=[[p[1],p[2]] for p in pts]
  if k.startswith('LDA W'):
    nav=IKL if r=='22' else ITL; dme=1.1 if r=='22' else 4.9
    mapt=dest(nav,brg(nav,(fa[1],fa[2])),dme)   # LDA の進入方向の上で、DME の距離
    fin=dest(t,ext,1.8)
    # 目で見て曲がる部分：MAPt から、最終の直線（1.8NM）の入口へ、なめらかな弧
    import itertools
    b0=brg((fa[1],fa[2]),mapt); b1=BRG[r]; n=8
    ctrl=dest(mapt,b0,dist(mapt,fin)*0.55)
    arc=[]
    for i in range(1,n):
      s=i/n; la=(1-s)**2*mapt[0]+2*(1-s)*s*ctrl[0]+s*s*fin[0]; lo=(1-s)**2*mapt[1]+2*(1-s)*s*ctrl[1]+s*s*fin[1]; arc.append([round(la,6),round(lo,6)])
    line+= [list(mapt)]+arc+[list(fin)]
    print('   MAPt',mapt,'終端入口',fin, '旋回', round((b1-b0+540)%360-180),'°')
  line.append(list(t))
  out[k]={'rw':r,'names':[p[0] for p in pts],'pts':line}
json.dump(out,open('tools/hnd_approaches.json','w'))
