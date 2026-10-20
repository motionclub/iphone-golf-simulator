import bpy, numpy as np
b=bpy.data.objects['Body_F']; me=b.data; uv=me.uv_layers.active
v=np.array([tuple(x.co) for x in me.vertices])
polys=[]; cat=[]
for p in me.polygons:
    zmax=max(v[i][2] for i in p.vertices)
    c=0
    if p.material_index==1 and zmax<0.1575: c=1
    elif p.material_index==1: c=2
    elif p.material_index==0 and all(abs(v[i][0])>0.195 and 0.65<v[i][2]<0.85 for i in p.vertices): c=3
    polys.append(np.array([tuple(uv.data[l].uv) for l in p.loop_indices])); cat.append(c)
np.savez('data/uvdump.npz',cat=np.array(cat),**{f'p{i}':q for i,q in enumerate(polys)})
