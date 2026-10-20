import sys
from PIL import Image
import numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
plate=Image.open(R+'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
K=0.0013043874; TOP=1.70466
pdir=sys.argv[1] if len(sys.argv)>1 else 'r/panels_f12a'
def contours(name, box, rows_pl):
    p=np.asarray(plate.crop(box)).astype(float)
    m=np.asarray(Image.open(R+f'work/male-micro1h/{pdir}/{name}.png').convert('RGBA').resize((p.shape[1],p.shape[0]),Image.LANCZOS)).astype(float)
    a=m[...,3]>127
    sk=(p[...,0]-p[...,2]>35)&(p[...,0]>100)
    out=[]
    for r in rows_pl:
        rr=int(r-box[1])
        cs=np.where(sk[rr])[0]; cm=np.where(a[rr])[0]
        if len(cs)==0 or len(cm)==0: continue
        out.append((r, TOP-(r-397)*K, cs.min(), cm.min(), (cm.min()-cs.min())*K*1000, cs.max(), cm.max(), (cm.max()-cs.max())*K*1000))
    return out
for name,box in (('q3L',(5,390,433,668)),('q3R',(433,390,834,668))):
    print(name, ' row  z      L:plate mesh diff(mm)    R:plate mesh diff(mm)')
    for r,z,pl,ml,dl,pr,mr,dr in contours(name,box,range(430,600,10)):
        print('  %d %.4f   %4d %4d %6.1f      %4d %4d %6.1f'%(r,z,pl,ml,dl,pr,mr,dr))
