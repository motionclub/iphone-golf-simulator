"""labeled-grid zoom of a plate region.  python3.13 plategrid.py <plate: head|bald|multi> x0 y0 x1 y1 zoom step out.png"""
import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from PIL import Image, ImageDraw, ImageFont
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
F={'head':'female_head_detail.jpg','bald':'female_body_bald.jpg','multi':'female_multiangle_body.jpg'}
plate,x0,y0,x1,y1,zoom,step,out=sys.argv[1],*map(int,sys.argv[2:8]),sys.argv[8]
im=Image.open(P+F[plate]).convert('RGB').crop((x0,y0,x1,y1))
im=im.resize((int((x1-x0)*zoom),int((y1-y0)*zoom)),Image.LANCZOS)
d=ImageDraw.Draw(im,'RGBA')
try: f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',12)
except Exception: f=ImageFont.load_default()
gx=(x0//step+1)*step
while gx<x1:
    X=(gx-x0)*zoom; major=(gx%(step*5)==0)
    d.line([(X,0),(X,im.height)],fill=(0,160,255,150 if major else 70),width=1)
    d.text((X+2,2),str(gx),fill=(0,90,200,255),font=f)
    gx+=step
gy=(y0//step+1)*step
while gy<y1:
    Y=(gy-y0)*zoom; major=(gy%(step*5)==0)
    d.line([(0,Y),(im.width,Y)],fill=(255,60,60,150 if major else 70),width=1)
    d.text((2,Y+1),str(gy),fill=(200,0,0,255),font=f)
    gy+=step
im.save(out)
