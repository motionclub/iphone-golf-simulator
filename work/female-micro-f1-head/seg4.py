import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
a=np.asarray(Image.open(P+'female_head_detail.jpg').convert('RGB')).astype(float)
R,G,B=a[...,0],a[...,1],a[...,2]
V=(R+G+B)/3
sat=np.max(a,axis=2)-np.min(a,axis=2)
# grey body/collar & background: low saturation and bright-ish
grey=(sat<16)&(V>150)
fg=~grey
Image.fromarray((fg*255).astype(np.uint8)).save('plates/fg_mask_head.png')
# per panel extents on foreground (restrict rows to head+neck up to 252)
def runs(row,x0,x1):
    xs=np.where(fg[row,x0:x1])[0]+x0
    if len(xs)==0: return []
    rr=[];st=xs[0];pv=xs[0]
    for x in xs[1:]:
        if x!=pv+1: rr.append((int(st),int(pv))); st=x
        pv=x
    rr.append((int(st),int(pv))); return rr
for r in (100,140,145,150,160,200,240):
    print('left',r,runs(r,440,800),'front',runs(r,85,430))
