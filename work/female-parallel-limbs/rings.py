import bpy, bmesh, numpy as np
me=bpy.data.objects['Body_F'].data
v=np.array([tuple(x.co) for x in me.vertices])
ring=np.where((np.abs(v[:,2]-0.15728244)<1e-5)&(v[:,0]>0))[0]
print('ankle ring',len(ring),v[ring].mean(0).round(4),v[ring].min(0).round(4),v[ring].max(0).round(4))
# ring just above
for z in sorted(set(np.round(v[(v[:,0]>0.05)&(v[:,2]>0.157)&(v[:,2]<0.30),2],4)))[:8]:
    r=np.where((np.abs(v[:,2]-z)<1e-4)&(v[:,0]>0.05))[0]; print('leg ring z',z,len(r),v[r].mean(0).round(4),(v[r].max(0)-v[r].min(0)).round(4))
# arm rings (x>0.2), distinct z values
zs=sorted(set(np.round(v[(v[:,0]>0.2)&(v[:,2]>0.65)&(v[:,2]<1.0),2],4)))
for z in zs:
    r=np.where((np.abs(v[:,2]-z)<1e-4)&(v[:,0]>0.2))[0]
    print('arm z',z,len(r),v[r].mean(0).round(4),(v[r].max(0)-v[r].min(0)).round(4))
