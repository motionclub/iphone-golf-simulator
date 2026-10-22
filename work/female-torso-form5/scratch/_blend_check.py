import bpy, numpy as np
for o in bpy.data.objects:
    me = o.data if o.type == 'MESH' else None
    if me is not None:
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
        print('OBJ', o.name, 'verts', len(me.vertices), 'tris~', sum(len(p.vertices) - 2 for p in me.polygons), 'nan', int(np.isnan(co).sum()), 'zrange', round(float(co.reshape(-1,3)[:,2].min()),3), round(float(co.reshape(-1,3)[:,2].max()),3))
