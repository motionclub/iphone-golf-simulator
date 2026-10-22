"""light isotropic fairing of the leg tube (removes cm-scale lumps): python stepL.py <in.npy> <out.npy> <lam> [zlo zhi]"""
import sys; sys.path.insert(0,'.')
from leglib import *
V=np.load(sys.argv[1]); out=sys.argv[2]; lam=float(sys.argv[3])
zlo=float(sys.argv[4]) if len(sys.argv)>4 else 0.17; zhi=float(sys.argv[5]) if len(sys.argv)>5 else 0.74
z=V[:,2]
free=ZONE&(z>zlo)&(z<zhi)&(DEG>0)
# stiffer (omega up) within 4 cm of both ends of the band so the joins stay put
omega=1.0+9.0*smoothstep(zlo+0.05,zlo,z)+9.0*smoothstep(zhi-0.05,zhi,z)
Vn=fair(V,free,lam=lam,omega=omega,iters=500)
d=np.linalg.norm(Vn-V,axis=1)*1000
print('lam',lam,'rms %.2f max %.2f mm'%(np.sqrt((d[free]**2).mean()),d.max()))
np.save(out,Vn)
