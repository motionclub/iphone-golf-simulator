import json, numpy as np, sys
sys.path.insert(0,'.')
from rearcmp import *
zs=np.arange(0.70,1.10,0.002); D=[]
for z in zs:
    i=int(round((z-0.70)/0.002)); pL,pR=pl['left'][i],pl['right'][i]; sL,sR=render_edge('start','left',z),render_edge('start','right',z)
    ok=[(p,s) for p,s in ((pL,sL),(pR,sR)) if p is not None and s is not None]
    D.append(np.mean([p-s for p,s in ok]) if ok else np.nan)
D=np.array(D); m=np.isfinite(D); D=np.interp(np.arange(len(D)),np.where(m)[0],D[m])
def smooth(x,s):
    k=int(3*s/0.002); w=np.exp(-0.5*(np.arange(-k,k+1)*0.002/s)**2); w/=w.sum(); return np.convolve(np.pad(x,k,mode='edge'),w,mode='valid')
Ds=smooth(D,float(sys.argv[1]) if len(sys.argv)>1 else 0.004)
json.dump(dict(z=zs.tolist(), D=Ds.tolist(), D_raw=D.tolist()), open('data/D_subpx.json','w'))
for z in np.arange(0.74,1.06,0.02):
    i=int(round((z-0.70)/0.002)); print(f'z {z:.2f}  plate-start {D[i]*1000:6.1f}   smoothed {Ds[i]*1000:6.1f} mm')
