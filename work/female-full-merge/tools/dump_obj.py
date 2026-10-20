"""blender -b <blend> --python dump_obj.py -- <ObjName> <out.npz>
Full raw dump of one mesh object: positions, polygons, loops, edges, materials, smooth/sharp, UV, custom normal raw, vertex groups, attributes."""
import bpy, sys, numpy as np
name, out = sys.argv[sys.argv.index('--') + 1:][:2]
o = bpy.data.objects[name]; me = o.data
n = len(me.vertices); nl = len(me.loops); npoly = len(me.polygons); ne = len(me.edges)
V = np.zeros(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cv = np.zeros(nl, np.int32); me.loops.foreach_get('vertex_index', cv)
ce = np.zeros(nl, np.int32); me.loops.foreach_get('edge_index', ce)
ls = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(npoly, np.int32); me.polygons.foreach_get('loop_total', lt)
mat = np.zeros(npoly, np.int32); me.polygons.foreach_get('material_index', mat)
sm = np.zeros(npoly, bool); me.polygons.foreach_get('use_smooth', sm)
ev = np.zeros(ne * 2, np.int32); me.edges.foreach_get('vertices', ev); ev = ev.reshape(-1, 2)
res = dict(V=V, corner_verts=cv, corner_edges=ce, loop_start=ls, loop_total=lt, material_index=mat, use_smooth=sm, edge_verts=ev)
res['material_names'] = np.array([m.name if m else '' for m in me.materials])
if len(me.uv_layers):
    u = np.zeros(nl * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', u); res['uv'] = u.reshape(-1, 2)
a = me.attributes.get('custom_normal')
if a is not None:
    arr = np.zeros(nl * 2, np.int16); a.data.foreach_get('value', arr); res['custom_normal_i16'] = arr.reshape(-1, 2)
a = me.attributes.get('sharp_edge')
if a is not None:
    arr = np.zeros(ne, bool); a.data.foreach_get('value', arr); res['sharp_edge'] = arr
# vertex groups: names + dense weight matrix membership
vgn = [g.name for g in o.vertex_groups]; res['vg_names'] = np.array(vgn)
if vgn:
    W = np.zeros((len(vgn), n), np.float32)
    for v in me.vertices:
        for g in v.groups: W[g.group, v.index] = g.weight
    res['vg_weights'] = W
# evaluated computed corner normals (what the renderer sees)
cn = np.zeros(nl * 3, np.float32); me.corner_normals.foreach_get('vector', cn); res['corner_normals'] = cn.reshape(-1, 3)
vn = np.zeros(n * 3, np.float32); me.vertex_normals.foreach_get('vector', vn); res['vertex_normals'] = vn.reshape(-1, 3)
np.savez(out, **res)
tris = int((lt - 2).sum())
print('DUMP', name, 'verts', n, 'polys', npoly, 'loops', nl, 'edges', ne, 'tris', tris, 'smooth faces', int(sm.sum()), 'vgroups', len(vgn), 'zrange', float(V[:,2].min()), float(V[:,2].max()))
