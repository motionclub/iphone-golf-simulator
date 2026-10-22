import bpy, numpy as np
o = bpy.data.objects['Body_F']; me = o.data
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
z=V[:,2]
# unique z values (rounded to 0.1 mm) with counts, in neck/head-base band
zr=np.round(z,4)
u,c=np.unique(zr[(z>1.36)&(z<1.52)],return_counts=True)
for a,b in zip(u,c):
    if b>=20:
        m=zr==a
        sub=V[m]
        print(f'z={a:.4f} n={b:3d} x[{sub[:,0].min():+.4f},{sub[:,0].max():+.4f}] y[{sub[:,1].min():+.4f},{sub[:,1].max():+.4f}]')
