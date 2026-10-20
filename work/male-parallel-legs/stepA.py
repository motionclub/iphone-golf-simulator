import sys; sys.path.insert(0,'.')
from leglib import *
z=V0[:,2]
w=np.where(ZONE,1.0,0.0)*smoothstep(0.10,0.16,z)*smoothstep(ZT,ZT-0.06,z)
n0=normals(V0)
out={}
for it in (40,):
    S=taubin_aniso(V0,w,iters=it)
    d=((S-V0)*n0).sum(1)
    Vn=V0+d[:,None]*n0
    print('iters',it,'normal disp rms %.3f mm max %.3f mm'%(np.sqrt((d[w>0]**2).mean())*1000,np.abs(d).max()*1000))
    np.save(f'data/V_A{it}.npy',Vn)
