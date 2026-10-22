"""blender -b --factory-startup --python probe_face.py -- in.blend out.npz : dump Face_F geometry per material (V, F polys, material index) + object transforms"""
import sys, bpy, numpy as np, json
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
fo = bpy.data.objects['Face_F']; me = fo.data
n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
mats = [m.name if m else '' for m in me.materials]
mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
offs = [0]; idx = []
for p in me.polygons: idx += list(p.vertices); offs.append(len(idx))
print('Face_F verts', n, 'polys', len(me.polygons), 'mats', mats)
print('vertex groups', [g.name for g in fo.vertex_groups])
print('matrix', [list(r) for r in fo.matrix_world])
np.savez(a[1], V=V, F=np.array(idx), Foff=np.array(offs), M=mi, mats=np.array(mats))
for k, m in enumerate(mats):
    sel = np.where(mi == k)[0]
    if len(sel): print(' ', m, 'polys', len(sel))
