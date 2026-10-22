import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
P='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
def skinmask(name):
    a=np.asarray(Image.open(P+name).convert('RGB')).astype(float)
    return ((a[...,0]-a[...,2])>28)&(a[...,0]>a[...,1])&(a[...,1]>a[...,2])&(a[...,0]>150)
s=skinmask('female_body_bald.jpg')
# front figure: columns < 640
for r in range(20,150,4):
    xs=np.where(s[r,:640])[0]; xb=np.where(s[r,640:])[0]+640
    print(r, (xs.min(),xs.max(),len(xs)) if len(xs) else None, (xb.min(),xb.max(),len(xb)) if len(xb) else None)
