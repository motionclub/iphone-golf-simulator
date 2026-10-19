import sys, os, json; OUT=os.path.abspath(sys.argv[1]); SPEC=[(a.split('=')[0], os.path.abspath(a.split('=')[1])) for a in sys.argv[2:]]; sys.argv=['x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, nose_off as NO, render_off as RO
from PIL import Image, ImageDraw
rows=[]
for lab,p in SPEC:
    G=NO.head(json.load(open(p))); keep=G[NO.h.tri][:,:,1].min(1)>-175; ims=[]
    for yaw,el in ((0,0),(-35,0),(0,20)):
        g=G
        if el: a=np.radians(el); R=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]]); g=(G-[0,-58,40])@R.T+[0,-58,40]
        ims.append(Image.fromarray(RO.render(g,NO.h.tri,yaw,keep=keep,res=420,half=26,centre=(0,-62,40))[0]))
    row=Image.new('RGB',(1260,420)); [row.paste(im,(420*i,0)) for i,im in enumerate(ims)]; ImageDraw.Draw(row).text((6,6),lab,fill=(0,0,0)); rows.append(row)
out=Image.new('RGB',(1260,420*len(rows))); [out.paste(r,(0,420*i)) for i,r in enumerate(rows)]; out.save(OUT,quality=90)
