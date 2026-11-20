import subprocess, json, os
from comp import *
from PIL import Image, ImageFilter
O='out/'
def run(a): subprocess.run(a,check=True)
# ---------- carousels ----------
FULL=(0,555,1170,2300)
slide(O+'c1-1.jpg','運用タブが新しくなりました','空港の今を、\nカード1枚ずつ','見出し1語と、大きな数字。\n押すと広がって、専用のページへ','st/ops_low.png',(0,0,1170,2250),'1/5')
slide(O+'c1-2.jpg','運用タブ｜地図','いま飛んでいる\n機体が、地図に','見る場所（展望デッキなど）も同じ地図に','st/ops_map.png',FULL,'2/5',note='機体の位置 adsb.lol（ODbL）・地図 国土地理院')
slide(O+'c1-3.jpg','運用タブ｜特別塗装機','これから飛ぶ予定まで\n1枚に','この3時間に来る機体と、これからの便','st/ops_sp.png',(0,700,1170,2150),'3/5',note='予定は航空会社の運航情報から。変わることがあります')
slide(O+'c1-4.jpg','運用タブ｜定時','行き先ごとの\n定時の割合','出発から15分以内に出た便の割合','st/ops_ontime.png',(0,620,1170,2300),'4/5',note='出典：公共交通オープンデータセンター')
endslide(O+'c1-5.jpg','空港で印を集める\n非公式アプリ',['各航空会社・空港とは関係ありません','画面はデモの見本です','数字はその時の記録で、保証するものではありません'],'機体の位置 adsb.lol（ODbL）／運航情報 公共交通オープンデータセンター','5/5')
slide(O+'c2-1.jpg','図鑑','国内86空港、\nいくつ行った？','地方ごとに、行った数が並ぶ','st/zk_top.png',(0,690,1170,2300),'1/6')
slide(O+'c2-2.jpg','図鑑｜地方別','押した空港に\n✓が付いていく','右端のツメで、行きたい地方へ','st/zk_region.png',(0,0,1170,2250),'2/6')
slide(O+'c2-3.jpg','図鑑｜もう1つの図鑑','飛行場・滑空場・\nヘリポートの図鑑','75か所。86空港とは別に数えます','st/af_top.png',FULL,'3/6')
slide(O+'c2-4.jpg','図鑑｜もう1つの図鑑','県名つきで\n種類が分かる','飛行場・滑空場・ヘリポートの札','st/af_list.png',(0,0,1170,2250),'4/6')
slide(O+'c2-5.jpg','図鑑｜もう1つの図鑑','ヘリポートだけ、\n滑空場だけも','上のピルで絞り込み','st/af_heli.png',(0,0,1170,2250),'5/6')
endslide(O+'c2-6.jpg','空港で印を集める\n非公式アプリ',['各航空会社・空港とは関係ありません','画面はデモの見本です','自衛隊の飛行場は、ほかの図鑑・実績の中にあります'],'','6/6')
# recap grid (11/23)
def grid(out):
    W,H=1080,1350; base=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(base)
    text(d,(64,78),'この3日で紹介したもの',F(26),SUB); text(d,(64,128),'そらメモで\n新しくなった6つ',F(58),INK,spacing=18)
    items=[('st/ops_low.png',(0,0,1170,2250),'運用タブ','カードの一覧'),('st/k_stamp.png',(0,0,1080,1920),'半券','指で切ってチェックイン'),
           ('st/af_top.png',FULL,'図鑑','飛行場・滑空場・ヘリポート'),('st/l_end.png',(0,0,1080,1920),'ピン止め','ホームにいつも出る'),
           ('st/fl_map.png',(0,555,1170,2300),'フライト','実際の時刻と航跡'),('a2.png',(0,0,390,693),'空港の3D','羽田から')]
    tw,th=290,300; gx=(W-3*tw-2*36)//2
    for i,(f,c,t,s) in enumerate(items):
        x=gx+(i%3)*(tw+36); y=330+(i//3)*(th+110)
        im=Image.open(f).convert('RGB').crop(c); sc=tw/im.width; im=im.resize((tw,int(im.height*sc)),Image.LANCZOS).crop((0,0,tw,th))
        shadow(base,(x,y,x+tw,y+th),28,24,40,10); base.alpha_composite(rounded(im,28),(x,y))
        text(d,(x+4,y+th+18),t,F(32),INK); text(d,(x+4,y+th+62),s,F(22,'m'),SUB)
    footer(base,'画面はデモの見本'); base.convert('RGB').save(out,quality=95)
grid(O+'c3-1.jpg')
endslide(O+'c3-2.jpg','空港で印を集める\n非公式アプリ',['各航空会社・空港とは関係ありません','画面はデモの見本です（フライトの航跡は見本の便にはありません）','予想・推定は保証するものではありません'],'機体の位置 adsb.lol（ODbL）／運航情報 公共交通オープンデータセンター','2/2')
# stories
def story(out,top,title,shot,crop,ask):
    W,H=1080,1920; base=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(base)
    text(d,(72,170),top,F(30),SUB); text(d,(72,226),title,F(70),INK,spacing=20)
    im=Image.open(shot).convert('RGB').crop(crop); sw=760; im=im.resize((sw,int(im.height*sw/im.width)),Image.LANCZOS).crop((0,0,sw,860))
    x=(W-sw)//2; y=520; shadow(base,(x,y,x+sw,y+im.height),40); base.alpha_composite(rounded(im,40),(x,y))
    text(d,(W//2,y+im.height+90),ask,F(30,'m'),MUTE,anchor='mm')
    footer(base,'画面はデモの見本',y=H-150); base.convert('RGB').save(out,quality=95)
story(O+'s1.jpg','11/21 のストーリーズ','半券、もう\n切りましたか？','st/home.png',(0,1350,1170,2300),'（ここにアンケートのスタンプ）')
story(O+'s3.jpg','11/23 のストーリーズ','3Dで見たい空港は？','a2.png',(0,0,390,693),'（ここに質問のスタンプ）')
# ---------- reels ----------
def endcard(out): endslide(out,'空港で印を集める\n非公式アプリ',['各航空会社・空港とは関係ありません','画面はデモの見本です'],'',story=True)
endcard(O+'end.png')
def reel(n,segs,caps,blur=None,src=None,hold={}):
    raw=f'vid/{n}_raw.mp4'; parts=[]
    for i,(a,b) in enumerate(segs):
        p=f'vid/{n}_s{i}.mp4'; vf=['-vf',f'tpad=stop_mode=clone:stop_duration={hold[i]}'] if i in hold else []; run(['ffmpeg','-y','-loglevel','error','-ss',str(a),'-to',str(b),'-i',raw,*vf,'-an','-c:v','libx264','-crf','18','-r','30',p]); parts.append(p)
    ec=f'vid/{n}_end.mp4'
    if src: endslide(f'vid/{n}_end.png','空港で印を集める\n非公式アプリ',['各航空会社・空港とは関係ありません','画面はデモの見本です'],src,story=True); ep=f'vid/{n}_end.png'
    else: ep=O+'end.png'
    run(['ffmpeg','-y','-loglevel','error','-loop','1','-t','2.5','-i',ep,'-vf','scale=1080:1920,format=yuv420p','-r','30','-c:v','libx264','-crf','18',ec]); parts.append(ec)
    open(f'vid/{n}_cat.txt','w').write('\n'.join(f"file '{os.path.basename(p)}'" for p in parts))
    cat=f'vid/{n}_cat.mp4'; run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',f'vid/{n}_cat.txt','-c','copy',cat])
    total=sum(b-a for a,b in segs)+sum(hold.values())
    inputs=['-i',cat]; fc=[]; last='[0:v]'
    if blur:
        (x1,y1,x2,y2,t1,t2)=blur
        fc.append(f"{last}split[bg][fg];[fg]crop={x2-x1}:{y2-y1}:{x1}:{y1},boxblur=18:3[bl];[bg][bl]overlay={x1}:{y1}:enable='between(t,{t1},{t2})'[vb]"); last='[vb]'
    for i,(t1,t2,cap,sub) in enumerate(caps):
        png=f'vid/{n}_cap{i}.png'; overlay(png,cap,sub); inputs+=['-i',png]
        fc.append(f"{last}[{i+1}:v]overlay=0:0:enable='between(t,{t1},{min(t2,total)})'[v{i}]"); last=f'[v{i}]'
    run(['ffmpeg','-y','-loglevel','error',*inputs,'-filter_complex',';'.join(fc),'-map',last,'-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',O+f'reel-{n}.mp4'])
    print(n,'ok',total+2.5)
import sys
if 'reels' in sys.argv:
  pass
  if 0: reel('J',[(0.0,6.0),(13.2,16.9)],[(0,1.5,'空港の今を、カードで',None),(1.5,6.0,'押すと広がって\n専用のページ','地図に、いま飛んでいる機体'),(6.0,9.7,'特別塗装機は\nこれから飛ぶ予定まで','予定は変わることがあります')],src='機体の位置 adsb.lol（ODbL）／運航情報 公共交通オープンデータセンター')
  if 0: reel('K',[(0.0,8.39)],[(0,1.5,'空港に着いたら',None),(1.5,3.0,'半券を、指で右へ',None),(3.0,8.39,'印がもらえる','押したときだけ位置を測ります')],blur=(262,1100,462,1172,2.3,8.4))
  if 0: reel('L',[(0.0,12.69)],[(0,1.5,'よく行く空港を',None),(1.5,5.0,'ピン止め','知らせる中身を選べる（推定・保証しません）'),(5.0,12.69,'ホームに、いつも出る',None)])
  if 0: reel('M',[(0.0,5.2),(7.6,9.4)],[(0,1.5,'図鑑は、空港だけじゃない',None),(1.5,4.0,'飛行場・滑空場・\nヘリポート 75か所','86空港とは別に数えます'),(4.0,6.0,'滑空場だけ',None),(6.0,9.3,'ヘリポートだけも','上のピルで絞り込み')],hold={0:0.8,1:1.5})
  if 0: reel('N',[(1.0,19.9)],[(0,6.0,'羽田を3Dで','押したときだけ読み込み（約0.2MB）'),(6.0,13.9,'指で回して見る',None),(13.9,18.9,'管制塔の目線',None)],src='機体の位置 adsb.lol（ODbL）・約1分遅れ')
  reel('E',[(0.0,10.98)],[(0,1.8,'空港の近くに、何がある？',None),(1.8,4.6,'飛行場も、近い順に','ほかに 20km 以内'),(4.6,7.4,'滑空場にいるときも',None),(7.4,10.98,'民間空港がなければ\nいちばん近い1つも','20km 以内にないとき。種類は札で見分けられます')],hold={0:0.6})
