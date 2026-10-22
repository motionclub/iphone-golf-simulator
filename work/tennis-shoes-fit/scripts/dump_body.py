"""dump the evaluated body mesh of a blend to npz (V world float64, F tris int32).  usage: blender -b file.blend --python dump_body.py -- ObjName out.npz"""
import bpy, sys, numpy as np, hashlib
name, out = sys.argv[sys.argv.index('--') + 1:][:2]
o = bpy.data.objects[name]
dg = bpy.context.evaluated_depsgraph_get()
oe = o.evaluated_get(dg)
me = oe.to_mesh()
n = len(me.vertices)
V = np.empty(n * 3, np.float64)
me.vertices.foreach_get('co', V)
V = V.reshape(n, 3)
M = np.array(o.matrix_world)
V = V @ M[:3, :3].T + M[:3, 3]
me.calc_loop_triangles()
T = np.empty(len(me.loop_triangles) * 3, np.int32)
me.loop_triangles.foreach_get('vertices', T)
T = T.reshape(-1, 3)
mi = np.empty(len(me.loop_triangles), np.int32)
me.loop_triangles.foreach_get('material_index', mi)
print('modifiers:', [(m.type, m.name) for m in o.modifiers], 'shape_keys:', None if not o.data.shape_keys else [k.name for k in o.data.shape_keys.key_blocks])
print('verts', n, 'tris', len(T), 'bbox', V.min(0), V.max(0))
print('vgroups', [g.name for g in o.vertex_groups][:40])
np.savez_compressed(out, V=V, F=T, M=mi)
oe.to_mesh_clear()
