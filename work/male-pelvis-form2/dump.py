"""Dump Body_M of a blend: positions, faces, loop normals, groups, objects.
blender -b --factory-startup --python dump.py -- <blend> <outprefix>"""
import sys, pickle, json
import numpy as np, bpy
a = sys.argv[sys.argv.index('--') + 1:]; src, pre = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=src)
info = {}
for o in bpy.data.objects:
    d = dict(type=o.type, parent=o.parent.name if o.parent else None, loc=list(o.location), hide_render=o.hide_render)
    if o.type == 'MESH':
        d.update(nv=len(o.data.vertices), nf=len(o.data.polygons), mats=[s.material.name if s.material else None for s in o.material_slots],
                 vgroups=[g.name for g in o.vertex_groups][:80], nvg=len(o.vertex_groups), shape_keys=o.data.shape_keys is not None,
                 mods=[m.type for m in o.modifiers], has_custom_normals=o.data.has_custom_normals)
    info[o.name] = d
body = bpy.data.objects['Body_M']; me = body.data
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
F = [tuple(p.vertices) for p in me.polygons]
np.savez(pre + '_mesh.npz', co=V)
pickle.dump(F, open(pre + '_faces.pkl', 'wb'))
# loop normals
try:
    me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
except Exception: pass
ln = np.empty(len(me.loops) * 3); me.loops.foreach_get('normal', ln); ln = ln.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
np.savez(pre + '_loopn.npz', n=ln, v=lv)
# vertex groups of Body_M
vg = {g.index: g.name for g in body.vertex_groups}
memb = {}
for v in me.vertices:
    for g in v.groups:
        memb.setdefault(vg[g.group], []).append(v.index)
np.savez(pre + '_groups.npz', **{k: np.array(v, np.int32) for k, v in memb.items()})
json.dump(info, open(pre + '_info.json', 'w'), indent=1)
print('DUMP_DONE', len(V), len(F), 'groups', {k: len(v) for k, v in memb.items()})
