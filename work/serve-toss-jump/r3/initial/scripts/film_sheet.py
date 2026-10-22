"""film_sheet.py <dir> <view> <start> <stop> <step> <out> [cols] [crop x0,y0,x1,y1]"""
import sys
from PIL import Image, ImageDraw
d,view,a,b,s,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),sys.argv[6]
cols=int(sys.argv[7]) if len(sys.argv)>7 else 6
crop=tuple(int(x) for x in sys.argv[8].split(',')) if len(sys.argv)>8 else None
ims=[]
for i in range(a,b,s):
    try: im=Image.open(f'{d}/{view}_{i:05d}.png').convert('RGB')
    except Exception: continue
    if crop: im=im.crop(crop)
    ImageDraw.Draw(im).text((6,6),f'{view} {i}',fill=(255,255,0)); ims.append(im)
w,h=ims[0].size; sc=min(1.0,420/w); w2,h2=int(w*sc),int(h*sc)
rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(cols*w2,rows*h2))
for k,im in enumerate(ims): S.paste(im.resize((w2,h2)),((k%cols)*w2,(k//cols)*h2))
S.save(out,quality=85); print(S.size,len(ims))
