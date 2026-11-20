from PIL import Image, ImageDraw, ImageFont, ImageFilter
FB='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; FM='/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc'; FK='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
def F(sz,w='b'): return ImageFont.truetype({'b':FB,'m':FM,'k':FK}[w],sz,index=0)
BG=(238,241,245); INK=(31,41,55); SUB=(107,114,128); MUTE=(156,163,175); WHITE=(255,255,255)
def text(d,xy,s,f,fill,anchor='la',spacing=14):
    d.multiline_text(xy,s,font=f,fill=fill,anchor=anchor,spacing=spacing)
def rounded(im,r):
    m=Image.new('L',im.size,0); ImageDraw.Draw(m).rounded_rectangle([0,0,im.size[0]-1,im.size[1]-1],r,fill=255); im=im.convert('RGBA'); im.putalpha(m); return im
def shadow(base,box,r,blur=40,alpha=50,dy=18):
    sh=Image.new('RGBA',base.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([box[0],box[1]+dy,box[2],box[3]+dy],r,fill=(17,24,39,alpha)); sh=sh.filter(ImageFilter.GaussianBlur(blur)); base.alpha_composite(sh)
LOGO='そらメモ'
def footer(base,right='画面はデモの見本',y=None,dark=False):
    d=ImageDraw.Draw(base); W,H=base.size; y=y or H-62
    text(d,(56,y),'そらメモ（非公式アプリ）',F(28),(232,236,241) if dark else INK,anchor='lm')
    if right:
        f=F(24,'m'); w=d.textlength(right,font=f)
        d.rounded_rectangle([W-56-w-36,y-24,W-56,y+24],24,fill=(52,62,78) if dark else (224,228,234))
        text(d,(W-56-w-18,y),right,f,(201,209,220) if dark else SUB,anchor='lm')
def slide(out,eyebrow,title,sub,shot,crop,no=None,shotw=780,right='画面はデモの見本',note=None):
    W,H=1080,1350; base=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(base)
    y=78
    if eyebrow: text(d,(64,y),eyebrow,F(26),SUB); y+=56
    text(d,(64,y),title,F(58),INK,spacing=18); tb=d.multiline_textbbox((64,y),title,font=F(58),spacing=18); y=tb[3]+22
    if sub: text(d,(64,y),sub,F(30,'m'),SUB,spacing=12); sb=d.multiline_textbbox((64,y),sub,font=F(30,'m'),spacing=12); y=sb[3]
    y+=44
    im=Image.open(shot).convert('RGB').crop(crop); s=shotw/im.width; im=im.resize((shotw,int(im.height*s)),Image.LANCZOS)
    maxh=H-130-y; 
    if im.height>maxh: im=im.crop((0,0,shotw,maxh))
    x=(W-shotw)//2; shadow(base,(x,y,x+shotw,y+im.height),40)
    base.alpha_composite(rounded(im,40),(x,y))
    if note:
        f=F(22,'m'); text(d,(W//2,H-112),note,f,MUTE,anchor='mm')
    footer(base,right)
    if no: text(d,(W-64,92),no,F(24,'m'),MUTE,anchor='ra')
    base.convert('RGB').save(out,quality=95)
def endslide(out,head,lines,src,no=None,story=False):
    W,H=(1080,1920) if story else (1080,1350); base=Image.new('RGBA',(W,H),BG+(255,)); d=ImageDraw.Draw(base)
    cy=H//2-200
    text(d,(W//2,cy),head,F(66),INK,anchor='mm',spacing=20)
    text(d,(W//2,cy+170),'soramemo.jp',F(76,'k'),INK,anchor='mm')
    text(d,(W//2,cy+260),'プロフィールのリンクから開けます',F(30,'m'),SUB,anchor='mm')
    yy=cy+380
    box=[90,yy,W-90,yy+60+len(lines)*52]; shadow(base,box,36,30,30,10); d.rounded_rectangle(box,36,fill=WHITE)
    for i,l in enumerate(lines): text(d,(W//2,yy+56+i*52),l,F(28,'m'),SUB,anchor='mm')
    if src: text(d,(W//2,box[3]+60),src,F(22,'m'),MUTE,anchor='mm',spacing=10)
    footer(base,None)
    if no: text(d,(W-64,92),no,F(24,'m'),MUTE,anchor='ra')
    base.convert('RGB').save(out,quality=95)
def overlay(out,cap,sub=None,W=1080,H=1920,top=150):
    o=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(o)
    f=F(64); tb=d.multiline_textbbox((0,0),cap,font=f,spacing=16,align='center'); tw,th=tb[2]-tb[0],tb[3]-tb[1]
    sh=0
    if sub: fs=F(32,'m'); sb=d.multiline_textbbox((0,0),sub,font=fs,spacing=10,align='center'); sh=sb[3]-sb[1]+26
    bw=max(tw, (sb[2]-sb[0]) if sub else 0)+110; bh=th+sh+90
    box=[(W-bw)//2,top,(W+bw)//2,top+bh]
    shadow(o,box,44,28,60,10); d=ImageDraw.Draw(o); d.rounded_rectangle(box,44,fill=(255,255,255,250))
    d.multiline_text((W//2,top+44),cap,font=f,fill=INK,anchor='ma',spacing=16,align='center')
    if sub: d.multiline_text((W//2,top+44+th+30),sub,font=fs,fill=SUB,anchor='ma',spacing=10,align='center')
    # badge under
    fb=F(26,'m'); bt='そらメモ（非公式アプリ）・画面はデモ'; w=d.textlength(bt,font=fb)
    by=box[3]+22; d.rounded_rectangle([(W-w)//2-26,by,(W+w)//2+26,by+50],25,fill=(31,41,55,215)); d.text((W//2,by+25),bt,font=fb,fill=(255,255,255),anchor='mm')
    o.save(out)
def badge_only(out,W=1080,H=1920,top=150):
    o=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(o)
    fb=F(26,'m'); bt='そらメモ（非公式アプリ）・画面はデモ'; w=d.textlength(bt,font=fb)
    d.rounded_rectangle([(W-w)//2-26,top,(W+w)//2+26,top+50],25,fill=(31,41,55,215)); d.text((W//2,top+25),bt,font=fb,fill=(255,255,255),anchor='mm'); o.save(out)
