import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
a=np.asarray(Image.open(P+'female_head_detail.jpg').convert('RGB')).astype(float)
s=((a[...,0]-a[...,2])>28)&(a[...,0]>a[...,1])&(a[...,1]>a[...,2])&(a[...,0]>150)
# top panel: columns 905..1100, rows 410..615; body is grey so skin only head+ears
for r in range(416,612,8):
    xs=np.where(s[r,905:1100])[0]+905
    # split into runs
    if len(xs)==0: print(r,None); continue
    runs=[]; st=xs[0]; pv=xs[0]
    for x in xs[1:]:
        if x!=pv+1: runs.append((st,pv)); st=x
        pv=x
    runs.append((st,pv))
    print(r, runs, 'width of main run', max(b-a_+1 for a_,b in runs))
