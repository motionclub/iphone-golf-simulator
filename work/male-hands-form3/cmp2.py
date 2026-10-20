"""before/after comparison sheet.  python3 cmp2.py <before_tag> <after_tag> <side> <out.png> [views] [scale] [center]"""
import subprocess, sys, os
from PIL import Image, ImageDraw
W='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0,W)
from sheetlib import font
a,b,side,out=sys.argv[1:5]
views=sys.argv[5] if len(sys.argv)>5 else 'q_dorsal_radial,q_palmar_radial,q_palmar_ulnar,radial'
scale=sys.argv[6] if len(sys.argv)>6 else '0.25'
center=sys.argv[7] if len(sys.argv)>7 else '0.0,0.0,0.065'
rows=[]
for tag in (a,b):
    subprocess.run(['python3',W+'/rv2.py',tag,side,views,scale,center],capture_output=True,text=True,cwd=W)
    im=Image.open(f'{W}/proof/it/{tag}_zoom_{side}.png').convert('RGB')
    d=ImageDraw.Draw(im); d.rectangle((0,0,im.width,34),fill=(15,15,17))
    d.text((8,6),('FORM2 (installed ArtDir 4287ba52)' if tag=='base' else 'FORM3 ('+tag+')')+f'  - {side} hand',fill=(255,230,120) if tag!='base' else (200,200,200),font=font(20)); rows.append(im)
w=max(i.width for i in rows); h=sum(i.height for i in rows)
S=Image.new('RGB',(w,h))
y=0
for i in rows: S.paste(i,(0,y)); y+=i.height
S.save(out); print(out,S.size)
