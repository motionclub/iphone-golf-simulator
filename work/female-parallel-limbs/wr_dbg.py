import bpy, numpy as np, collections
me=bpy.data.objects['Body_F'].data
v=np.array([tuple(x.co) for x in me.vertices])
for sgn in (1,-1):
    m=(sgn*v[:,0]>0.195)&(v[:,2]>0.74)&(v[:,2]<0.93)
    z=np.round(v[m][:,2],4); c=collections.Counter(z)
    print('side',sgn,[(k,n) for k,n in sorted(c.items()) if n>=6])
