import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
B='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
sheet=Image.open(B+'female_multiangle_body.jpg').convert('L')
S2b=1.7039/290.5; V0b=668.5
S2=1.7039/288.5; V0=338.5
def enh(im,blur=8,gain=5):
    a=np.asarray(im).astype(float); bl=np.asarray(im.filter(ImageFilter.GaussianBlur(blur))).astype(float)
    return Image.fromarray(np.clip(128+(a-bl)*gain,0,255).astype(np.uint8))
def tile(cx,top_row,zc,half,scale=6):
    v0=V0 if top_row else V0b; s=S2 if top_row else S2b
    y0=v0-(zc+half)/s; y1=v0-(zc-half)/s; w=half/s
    c=sheet.crop((int(cx-w),int(y0),int(cx+w),int(y1)))
    c=c.resize((c.width*scale,c.height*scale),Image.LANCZOS)
    return c
# chest tiles: 3/4 FL (168), 3/4 FR (472), front(168 top), left profile (~ 790)  zc=1.22 half .22 ; glute tiles zc=0.90 half .22
cols_top={'front':168,'back':485,'Lprof':790,'Rprof':1095}
cols_bot={'3/4FL':168,'3/4FR':472,'3/4BL':775,'3/4BR':1078}
ims=[]
for nm,cx in cols_bot.items():
    zc=1.22 if 'F' in nm else 0.92
    t=tile(cx,False,zc,0.24,5); ims.append((nm,t,enh(t.resize((t.width//5,t.height//5),Image.LANCZOS),blur=3,gain=4).resize(t.size,Image.LANCZOS)))
W=Image.new('L',(sum(i[1].width for i in ims),ims[0][1].height*2))
x=0
for nm,t,e in ims:
    W.paste(t,(x,0)); W.paste(e,(x,t.height)); x+=t.width
W.save('data/plate_zoom_34.png'); print(W.size)
# profiles
pf=[]
for nm,cx in (('Lprof',790),('Rprof',1095)):
    t=tile(cx,True,1.05,0.42,5); pf.append((nm,t,enh(t.resize((t.width//5,t.height//5),Image.LANCZOS),blur=3,gain=4).resize(t.size,Image.LANCZOS)))
W2=Image.new('L',(sum(i[1].width for i in pf),pf[0][1].height*2)); x=0
for nm,t,e in pf:
    W2.paste(t,(x,0)); W2.paste(e,(x,t.height)); x+=t.width
W2.save('data/plate_zoom_prof.png'); print(W2.size)
