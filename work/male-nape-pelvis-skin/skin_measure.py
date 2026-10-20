import sys, glob
import numpy as np
from PIL import Image
def hsv(a):
    mx=a.max(-1); mn=a.min(-1); d=mx-mn; S=np.where(mx>0,d/np.maximum(mx,1e-9),0)
    r,g,b=a[...,0],a[...,1],a[...,2]; H=np.zeros_like(mx); m=d>1e-9
    rc=(mx==r)&m; gc=(mx==g)&m&~rc; bc=m&~rc&~gc
    H[rc]=((g-b)[rc]/d[rc])%6; H[gc]=((b-r)[gc]/d[gc])+2; H[bc]=((r-g)[bc]/d[bc])+4
    return H*60,S,mx
def stats(files):
    allp=[]
    for f in files:
        a=np.asarray(Image.open(f).convert('RGB')).astype(float)/255; H,S,V=hsv(a)
        m=(H>8)&(H<45)&(S>0.2)&(V>0.3); allp.append(np.stack([S[m],V[m],H[m]],1))
    p=np.concatenate(allp); return p
if __name__=='__main__':
    for d in sys.argv[1:]:
        p=stats(sorted(glob.glob(d+'/yaw*.png')))
        print(f'{d:22s} n={len(p):7d} S={p[:,0].mean():.3f} V={p[:,1].mean():.3f} H={p[:,2].mean():.1f}')
