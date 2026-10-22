import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
a=np.asarray(Image.open(P+'female_head_detail.jpg').convert('RGB')).astype(float)
s=((a[...,0]-a[...,2])>28)&(a[...,0]>a[...,1])&(a[...,1]>a[...,2])&(a[...,0]>150)
def ext(x0,x1,r):
    xs=np.where(s[r,x0:x1])[0]
    return (xs.min()+x0,xs.max()+x0,len(xs)) if len(xs) else None
print('FRONT (x range 85..430)')
for r in range(68,270,6): print(r, ext(85,430,r))
print('LEFT (440..800)')
for r in range(68,270,6): print(r, ext(440,800,r))
