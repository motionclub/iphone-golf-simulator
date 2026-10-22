"""blender -b <blend> --python dump_mesh.py -- out.npz : dump Body_F raw arrays (positions, topology, normals, UV, materials, sharp edges)"""
import bpy, sys, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body_F']; me = o.data
n = len(me.vertices); V = np.zeros(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
npoly = len(me.polygons); nl = len(me.loops)
cv = np.zeros(nl, np.int32); me.loops.foreach_get('vertex_index', cv)
ls = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_total', lt)
mat = np.zeros(npoly, np.int32); me.polygons.foreach_get('material_index', mat)
sm = np.zeros(npoly, bool); me.polygons.foreach_get('use_smooth', sm)
ne = len(me.edges); ev = np.zeros(ne * 2, np.int32); me.edges.foreach_get('vertices', ev); ev = ev.reshape(-1, 2)
res = dict(V=V, corner_verts=cv, loop_start=ls, loop_total=lt, material_index=mat, use_smooth=sm, edge_verts=ev)
uv = me.uv_layers[0]; u = np.zeros(nl * 2, np.float32); uv.data.foreach_get('uv', u); res['uv'] = u.reshape(-1, 2)
a = me.attributes['custom_normal']; arr = np.zeros(nl * 2, np.int16); a.data.foreach_get('value', arr); res['custom_normal_i16'] = arr.reshape(-1, 2)
a = me.attributes.get('sharp_edge')
if a is not None:
    arr = np.zeros(ne, bool); a.data.foreach_get('value', arr); res['sharp_edge'] = arr
np.savez(out, **res)
print('DUMP verts', n, 'polys', npoly, 'loops', nl, 'edges', ne, 'sharp_edge true', int(res.get('sharp_edge', np.zeros(1)).sum()), 'smooth faces', int(sm.sum()))
