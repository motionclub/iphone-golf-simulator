import sys, numpy as np
from PIL import Image
A=sys.argv[1]+'/'; M='../male-silhouette/'
tiles={}
for v in ['bald_front','bald_back','left','right','sheet_front','sheet_back']:
    t=np.array(Image.open(M+v+'_target.png').convert('L'))>127
    r=np.array(Image.open(A+v+'.png').split()[3])>127
    d=t^r; u=t|r
    print(f'{v:12s} xor {d.sum():6d} union {u.sum():6d} {100*d.sum()/u.sum():.3f}%  ref-only {(t&~r).sum()} mdl-only {(r&~t).sum()}')
    out=np.zeros(t.shape+(3,),np.uint8); out[...]=(30,30,30)
    out[t&r]=(110,110,110); out[t&~r]=(60,230,150); out[r&~t]=(255,90,160)
    Image.fromarray(out).save(A+v+'_overlay.png')
