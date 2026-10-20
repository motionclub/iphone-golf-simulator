import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath='baseline/start.blend')
for o in bpy.data.objects: print(o.name,o.type, [round(x,3) for x in o.location], o.parent.name if o.parent else None)
b=bpy.data.objects['Body_M']; me=b.data
n=len(me.vertices); V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
print(n, len(me.polygons), V.min(0), V.max(0))
print([vg.name for vg in b.vertex_groups])
np.save('data/V_start.npy',V)
import pickle
F=[list(p.vertices) for p in me.polygons]; pickle.dump(F,open('data/F.pkl','wb'))
print(b.matrix_world)
# leg z-slices: x extents
for z in np.arange(0.0,1.0,0.05):
    s=(np.abs(V[:,2]-z)<0.004)
    if s.sum(): print(round(z,2), s.sum(), 'x',V[s,0].min().round(3),V[s,0].max().round(3),'y',V[s,1].min().round(3),V[s,1].max().round(3))
