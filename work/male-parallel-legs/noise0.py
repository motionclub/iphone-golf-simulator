import sys; sys.path.insert(0,'.')
from leglib import *
w=np.zeros(N); w[ZONE]=1
S=taubin(V0,w,iters=25)
d=S-V0; n=normals(V0); dn=(d*n).sum(1)*1000
print('zone verts',ZONE.sum())
for z0 in np.arange(0.0,0.77,0.05):
    s=ZONE&(V0[:,2]>=z0)&(V0[:,2]<z0+0.05)
    if s.sum(): print('z %.2f-%.2f  n=%d  normal dev: rms %.2f mm  max %.2f   |d| rms %.2f'%(z0,z0+0.05,s.sum(),np.sqrt((dn[s]**2).mean()),np.abs(dn[s]).max(),np.sqrt((np.linalg.norm(d[s],axis=1)**2).mean())*1000))
# laplacian outliers (pits)
U=umbrella(V0); un=(U*n).sum(1)*1000
o=ZONE&(np.abs(un)>2.5)
print('umbrella normal comp >2.5mm outliers:',o.sum(), 'max', np.abs(un[ZONE]).max())
idx=np.nonzero(o)[0]; print(np.round(V0[idx[:25]],3).tolist())
