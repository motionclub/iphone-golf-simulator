import sys, os, json; OUT=os.path.abspath(sys.argv[1]); SPEC=[(a.split('=')[0], os.path.abspath(a.split('=')[1])) for a in sys.argv[2:]]; sys.argv=['x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, nose_off as NO, render_off as RO
from PIL import Image, ImageDraw
rows=[]
for lab,p in SPEC:
    G=NO.head(json.load(open(p))); keep=G[NO.h.tri][:,:,1].min(1)>-175; ims=[]
    for yaw in (0,-35,-70):
        ims.append(Image.fromarray(RO.render(G,NO.h.tri,yaw,keep=keep,res=440,half=48,centre=(0,-88,10))[0]))
    row=Image.new('RGB',(1320,440)); [row.paste(im,(440*i,0)) for i,im in enumerate(ims)]; ImageDraw.Draw(row).text((6,6),lab,fill=(0,0,0)); rows.append(row)
out=Image.new('RGB',(1320,440*len(rows))); [out.paste(r,(0,440*i)) for i,r in enumerate(rows)]; out.save(OUT,quality=90)
