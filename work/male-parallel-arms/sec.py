import bpy, numpy as np
b=bpy.data.objects['Body_M']; v=np.array([tuple(x.co) for x in b.data.vertices])
# right side x>0: per x-bin report z range and y range
for x0 in np.arange(0.0,0.67,0.04):
    m=(v[:,0]>=x0)&(v[:,0]<x0+0.04)
    if m.sum(): print(f"x {x0:.2f} n={m.sum():5d} z {v[m,2].min():.3f}-{v[m,2].max():.3f} y {v[m,1].min():.3f}-{v[m,1].max():.3f}")
