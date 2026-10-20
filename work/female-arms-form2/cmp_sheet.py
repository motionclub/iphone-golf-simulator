"""python3 cmp_sheet.py prefix out.png : plate | model, front & back arm crops (3x)"""
import sys
from PIL import Image
pre=sys.argv[1]; out=sys.argv[2]; K=3
P='../../ArtDir/hero/base_lock/female_body_bald.jpg'
pl=Image.open(P).convert('RGB').resize((1280*K,720*K),Image.LANCZOS)
rows=[]
for view,box in (('front',(300,130,580,430)),('back',(715,130,995,430))):
    m=Image.open(f'{pre}_{view}.png').convert('RGBA')
    bg=Image.new('RGBA',m.size,(225,225,228,255)); bg.alpha_composite(m); m=bg.convert('RGB')
    b=tuple(v*K for v in box)
    rows.append((pl.crop(b),m.crop(b)))
w,h=rows[0][0].size
s=Image.new('RGB',(w*2,h*2),'white')
for r,(a,b) in enumerate(rows): s.paste(a,(0,r*h)); s.paste(b,(w,r*h))
s=s.resize((s.width*2//3,s.height*2//3),Image.LANCZOS)
s.save(out)
