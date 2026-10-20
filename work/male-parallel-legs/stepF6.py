"""second fairing after the profile warp (free region z<zmax, stiffer towards the top).  python stepF6.py <in.npy> <out.npy> <lam> [zmax]"""
import sys; sys.path.insert(0,'.')
from leglib import *
V=np.load(sys.argv[1]); out=sys.argv[2]; lam=float(sys.argv[3]); zmax=float(sys.argv[4]) if len(sys.argv)>4 else 0.22
z=V[:,2]
free=ZONE&(z<zmax)&(DEG>0)
omega=1.0+6.0*smoothstep(zmax-0.08,zmax,z)
sole=ZONE&(z<0.004)
Vn=fair(V,free,lam=lam,omega=omega,fixed_axes={2:sole},iters=600)
d=np.linalg.norm(Vn-V,axis=1)*1000
print('lam',lam,'rms %.2f max %.2f mm'%(np.sqrt((d[free]**2).mean()),d.max()),'min z %.5f'%Vn[ZONE,2].min())
np.save(out,Vn)
