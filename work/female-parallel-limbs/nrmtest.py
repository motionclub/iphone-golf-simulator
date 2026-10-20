import bpy, bmesh, numpy as np
b=bpy.data.objects['Body_F']; me=b.data
print('attrs',[(a.name,a.domain,a.data_type) for a in me.attributes])
n0=np.array([tuple(n.vector) for n in me.corner_normals]); print('corner normals',n0.shape)
# compare to freshly computed smooth normals: vertex normals
vn=np.array([tuple(v.normal) for v in me.vertices]); lv=np.array([l.vertex_index for l in me.loops])
diff=np.linalg.norm(n0-vn[lv],axis=1); print('custom vs vertex normal diff: mean',diff.mean(),'max',diff.max(),'frac>0.05',(diff>0.05).mean())
bm=bmesh.new(); bm.from_mesh(me); bm.to_mesh(me); bm.free()
n1=np.array([tuple(n.vector) for n in me.corner_normals]); print('roundtrip identical',np.array_equal(n0,n1), np.abs(n0-n1).max())
