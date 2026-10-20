"""full structural dump of a blend for verification.  blender -b --factory-startup --python dump_full.py -- <in.blend> <out_prefix>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, bpy
import fl
blend, pref = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
out = {}
for nm in ('Body_F', 'Face_F'):
    ob = bpy.data.objects[nm]; me = ob.data
    V, F = fl.mesh_arrays(me)
    off = np.concatenate([[0], np.cumsum([len(f) for f in F])]); flat = np.concatenate([np.asarray(f, np.int64) for f in F])
    mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
    sm = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('use_smooth', sm)
    uvs = {l.name: np.array([d.uv[:] for d in l.data]) for l in me.uv_layers}
    out[nm + '_V'] = V; out[nm + '_F'] = flat; out[nm + '_Foff'] = off; out[nm + '_MI'] = mi; out[nm + '_smooth'] = sm
    for k, u in uvs.items(): out[f'{nm}_uv_{k}'] = u
    groups = {}
    for v in me.vertices:
        for g in v.groups: groups.setdefault(ob.vertex_groups[g.group].name, []).append((v.index, round(g.weight, 6)))
    json.dump(dict(groups=groups, materials=[m.name if m else None for m in me.materials], hide_viewport=ob.hide_viewport, loc=list(ob.location), rot=list(ob.rotation_euler), scale=list(ob.scale),
                   has_custom_normals=me.has_custom_normals, n_edges=len(me.edges)), open(f'{pref}_{nm}.json', 'w'))
np.savez(pref + '.npz', **out)
other = {o.name: (o.type, o.hide_viewport) for o in bpy.data.objects}
json.dump(other, open(pref + '_objects.json', 'w'))
print('dumped', blend, {k: v.shape for k, v in out.items() if k.endswith('_V')})
