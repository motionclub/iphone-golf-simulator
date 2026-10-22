"""biharmonic fairing of the foot region (after the warp).  python stepF5.py <in.npy> <out.npy> <lam> [omega_foot]"""
import sys; sys.path.insert(0,'.')
from leglib import *
V=np.load(sys.argv[1]); out=sys.argv[2]; lam=float(sys.argv[3]); om_f=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
z=V[:,2]
free=ZONE&(z<0.15)&(DEG>0)
omega=np.where(z<0.10,om_f,om_f*(1+4*smoothstep(0.10,0.15,z)))       # stiffer towards the ankle/leg
sole=ZONE&(z<0.004)
Vn=fair(V,free,lam=lam,omega=omega,fixed_axes={2:sole},iters=600)
d=np.linalg.norm(Vn-V,axis=1)*1000
print('lam',lam,'moved',(d>1e-9).sum(),'rms %.2f max %.2f mm'%(np.sqrt((d[free]**2).mean()),d.max()),'min z %.5f'%Vn[ZONE,2].min())
np.save(out,Vn)
