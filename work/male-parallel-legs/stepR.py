"""tangential relaxation of the foot/ankle (re-projected onto the pre-relaxation surface).  python stepR.py <in.npy> <out.npy> [iters]"""
import sys; sys.path.insert(0,'.')
from leglib import *
V=np.load(sys.argv[1]); out=sys.argv[2]; iters=int(sys.argv[3]) if len(sys.argv)>3 else 20
z=V[:,2]
free=ZONE&(z<0.24)&(DEG>0)
w=smoothstep(0.24,0.16,z)*(z>-1)
# keep the sole plane vertices on it: they are re-projected onto the reference surface which contains the plane
zonetri=np.array([t for t in TRI if all(ZONE[i] and V[i,2]<0.34 for i in t)])
print('free',free.sum(),'ref tris',len(zonetri))
Vn=relax_project(V,free,w,iters=iters,lam=0.6,reg_tris=zonetri)
d=np.linalg.norm(Vn-V,axis=1)*1000
print('moved rms %.2f max %.2f mm; min z %.5f'%(np.sqrt((d[free]**2).mean()),d.max(),Vn[ZONE,2].min()))
np.save(out,Vn)
