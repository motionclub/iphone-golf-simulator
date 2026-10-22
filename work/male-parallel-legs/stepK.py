"""Step K: kneecap relief on the front of each knee.  python stepK.py <in.npy> <out.npy> [A_mm] [zc]"""
import sys; sys.path.insert(0,'.')
from leglib import *
V=np.load(sys.argv[1]); out=sys.argv[2]
A=float(sys.argv[3])/1000 if len(sys.argv)>3 else 0.0065
ZC=float(sys.argv[4]) if len(sys.argv)>4 else 0.525
SX=float(sys.argv[5]) if len(sys.argv)>5 else 0.034
SZ=float(sys.argv[6]) if len(sys.argv)>6 else 0.036
n=normals(V)
Vn=V.copy()
for sel0,side in ((LEFT,1),(RIGHT,-1)):
    sel=sel0&(V[:,2]>ZC-2.3*SZ)&(V[:,2]<ZC+2.3*SZ)
    P=V[sel]; nn=n[sel]
    # knee axis: mean x of the leg slice at ZC; front-most y there
    s0=sel0&(np.abs(V[:,2]-ZC)<0.01)
    cx=0.5*(V[s0,0].max()+V[s0,0].min())
    front=V[s0&(np.abs(V[:,0]-cx)<0.02),1].min()
    print('side',side,'knee centre x %.3f front y %.3f'%(cx,front))
    dx=(P[:,0]-cx)/SX; dz=(P[:,2]-ZC)/SZ
    t=np.sqrt(dx*dx+dz*dz)
    bump=np.where(t<1.0,(1-t*t)**2,0.0)
    ring=np.where((t>=0.8)&(t<2.2),-0.30*np.sin(np.pi*(t-0.8)/1.4)**2*np.where(t<1.5,1.0,(2.2-t)/0.7),0.0)
    facing=np.clip((-nn[:,1]-0.2)/0.5,0,1)                       # only the front side
    d=A*(bump+ring)*facing
    Vn[sel]=P+nn*d[:,None]
mv=np.linalg.norm(Vn-V,axis=1)*1000
print('moved',(mv>0).sum(),'max %.2f mm'%mv.max())
np.save(out,Vn)
