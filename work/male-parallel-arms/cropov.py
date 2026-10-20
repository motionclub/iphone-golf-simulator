import sys, numpy as np
from PIL import Image
A=sys.argv[1]+'/'; names=sys.argv[2].split(','); out=sys.argv[3]; sc=int(sys.argv[4]) if len(sys.argv)>4 else 2
tiles=[]
for n in names:
    im=Image.open(A+n+'_overlay.png'); a=np.array(im); m=(a!=30).any(2)
    ys,xs=np.nonzero(m); box=(max(xs.min()-10,0),max(ys.min()-10,0),xs.max()+10,ys.max()+10)
    c=im.crop(box); tiles.append(c.resize((c.width*sc,c.height*sc),Image.NEAREST)); print(n,box)
H=max(t.height for t in tiles); W=sum(t.width for t in tiles)+10*len(tiles)
S=Image.new('RGB',(W,H),(0,0,0)); x=0
for t in tiles: S.paste(t,(x,0)); x+=t.width+10
S.save(out); print(S.size)
