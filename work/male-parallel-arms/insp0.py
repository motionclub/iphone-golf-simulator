import bpy, sys, numpy as np
for o in bpy.data.objects:
    print(o.name, o.type, len(o.data.vertices) if o.type=='MESH' else '', [g.name for g in o.vertex_groups][:60] if o.type=='MESH' else '')
b=bpy.data.objects.get('Body_M')
if b:
    v=np.array([tuple(x.co) for x in b.data.vertices]); print(v.min(0), v.max(0), len(v), len(b.data.polygons))
