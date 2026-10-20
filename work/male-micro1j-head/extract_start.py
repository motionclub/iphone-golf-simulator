"""Extract Body_M (verts, faces, LOOP_* groups) from the START blend -> data/V_start.npy, F_start.pkl, loops_start.pkl.
blender -b --factory-startup --python extract_start.py -- <blend> <tag>"""
import sys, pickle, json
import numpy as np
import bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head'
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); tag = argv[1]
body = bpy.data.objects['Body_M']; me = body.data
n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
F = [[v for v in p.vertices] for p in me.polygons]
np.save(f'{W}/data/V_{tag}.npy', V); pickle.dump(F, open(f'{W}/data/F_{tag}.pkl', 'wb'))
loops = {}
for vg in body.vertex_groups:
    idx = [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
    loops[vg.name] = idx
pickle.dump(loops, open(f'{W}/data/loops_{tag}.pkl', 'wb'))
# custom normals (loop normals) -> per-corner array so the head-region shading recipe can be reproduced/compared
me.calc_loop_triangles()
cn = None
if me.has_custom_normals:
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    np.save(f'{W}/data/cornernormals_{tag}.npy', cn)
print('verts', n, 'faces', len(F), 'groups', {k: len(v) for k, v in loops.items()})
print('objects', [(o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects])
print('materials', [m.name for m in bpy.data.materials])
print('has custom normals', me.has_custom_normals, 'loops', len(me.loops))
face = bpy.data.objects.get('Face_M')
if face:
    print('Face_M verts', len(face.data.vertices), 'polys', len(face.data.polygons), 'mats', [m.name for m in face.data.materials])
sc = bpy.context.scene
print('scene objs', [(o.name, o.type, tuple(round(c, 3) for c in o.location)) for o in sc.objects if o.type != 'MESH'])
print('unit', sc.unit_settings.system, sc.unit_settings.scale_length)
