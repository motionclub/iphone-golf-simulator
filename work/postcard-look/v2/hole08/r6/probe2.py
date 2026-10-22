import bpy, numpy as np, sys
ob=bpy.data.objects["DRESS_PATH_01"]
me=ob.data
co=np.array([v.co[:] for v in me.vertices])
# vertex order: rows of (nl top + 2 skirt)
print("nverts",len(co))
sel=(co[:,1]>3.2)&(co[:,1]<4.6)&(np.abs(co[:,0]+2.0)<0.3)
idx=np.nonzero(sel)[0]
for i in idx[:60]:
    print(i, np.round(co[i],4))
tb=bpy.data.objects["TEE_BOX"]
tc=np.array([v.co[:] for v in tb.data.vertices])
print("tee outline front verts:", np.round(tc[tc[:,1]>3.5],3).tolist())
