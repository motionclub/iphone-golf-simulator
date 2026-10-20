import sys, numpy as np, bpy
base = sys.argv[sys.argv.index('--') + 1]
def snap():
    me = bpy.data.objects['Body_M'].data
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn)
    return cn.reshape(-1, 3)
def cmp(a, b, name):
    ang = np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))
    print(f'{name}: worst {ang.max():.4f} deg, corners >0.01deg {int((ang > 0.01).sum())} of {len(ang)}')
bpy.ops.wm.open_mainfile(filepath=base)
me = bpy.data.objects['Body_M'].data
c0 = snap()
me.update(); c1 = snap(); cmp(c0, c1, 'load vs after me.update()')
me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
c2 = snap(); cmp(c0, c2, 'load vs after calc_normals_split')
# toggle: set a vertex to its own value (dirty) and read
v = me.vertices[0].co.copy(); me.vertices[0].co = v; me.update(); c3 = snap(); cmp(c0, c3, 'load vs after touching a vertex + update')
print('unique corners with big change near vertex 0 neighbours?')
