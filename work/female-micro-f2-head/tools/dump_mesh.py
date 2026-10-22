"""dump Body_F / Face_F of a blend to npz (+ vertex groups json).   blender -b --factory-startup --python dump_mesh.py -- <in.blend> <out_prefix>
out_prefix.npz : V (n,3 float64 of the float32 coords), F (flat), Foff, MI (material idx), LV, LF, LFoff, LM ;  out_prefix_groups.json : {group: [vertex ids]}"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, bpy
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
blend, pref = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
ob = bpy.data.objects['Body_F']; me = ob.data
V, F = fl.mesh_arrays(me)
off = np.concatenate([[0], np.cumsum([len(f) for f in F])]); flat = np.concatenate([np.asarray(f, np.int64) for f in F])
mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
fo = bpy.data.objects['Face_F']; fm = fo.data
LV, LF = fl.mesh_arrays(fm)
loff = np.concatenate([[0], np.cumsum([len(f) for f in LF])]); lflat = np.concatenate([np.asarray(f, np.int64) for f in LF])
lm = np.empty(len(fm.polygons), np.int32); fm.polygons.foreach_get('material_index', lm)
np.savez(pref + '.npz', V=V, F=flat, Foff=off, MI=mi, LV=LV, LF=lflat, LFoff=loff, LM=lm)
groups = {g.name: [] for g in ob.vertex_groups}
for v in me.vertices:
    for ge in v.groups:
        groups[ob.vertex_groups[ge.group].name].append(v.index)
json.dump(groups, open(pref + '_groups.json', 'w'))
print('objects', [(o.name, o.type, o.hide_viewport) for o in bpy.data.objects])
print('Body_F verts', len(V), 'faces', len(F), 'tris', int(sum(len(f) - 2 for f in F)), 'Face_F verts', len(LV), 'faces', len(LF))
print('materials Body', [m.name if m else None for m in me.materials], 'Face', [m.name if m else None for m in fm.materials])
print('groups', {k: len(v) for k, v in groups.items()})
print('quads', int(sum(1 for f in F if len(f) == 4)), 'tris', int(sum(1 for f in F if len(f) == 3)), 'ngon', int(sum(1 for f in F if len(f) > 4)))
# custom split normals? uv layers
print('uv layers', [u.name for u in me.uv_layers], 'has_custom_normals', me.has_custom_normals)
print('z range', V[:, 2].min(), V[:, 2].max())
