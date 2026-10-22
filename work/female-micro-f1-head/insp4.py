import bpy, numpy as np
o = bpy.data.objects['Body_F']; me = o.data
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
z=V[:,2]
zr=np.round(z,4)
u,c=np.unique(zr[(z>1.30)&(z<1.44)],return_counts=True)
for a,b in zip(u,c):
    if b>=6:
        m=zr==a; sub=V[m]
        r=np.hypot(sub[:,0],sub[:,1]-sub[:,1].mean())
        print(f'z={a:.4f} n={b:3d} x[{sub[:,0].min():+.4f},{sub[:,0].max():+.4f}] y[{sub[:,1].min():+.4f},{sub[:,1].max():+.4f}]')
# neck ring candidates: connected structure. print vertices around z 1.40-1.43 at |x|<0.002 front/back (y extremes)
sel=(z>1.36)&(z<1.44)&(np.abs(V[:,0])<0.0015)
idx=np.where(sel)[0]
order=idx[np.argsort(z[idx])]
for i in order: print(i, np.round(V[i],4))
