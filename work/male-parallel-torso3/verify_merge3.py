"""Post-merge verifier: the merged blend must differ from the pre-install blend ONLY at the delta vertices (positions), with identical topology/Face_M/groups/materials.
blender -b --factory-startup --python verify_merge3.py -- <pre.blend> <merged.blend> <out.json>   (exit code 1 on failure)"""
import sys, json, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3')
a = sys.argv[sys.argv.index('--') + 1:]; pre, mer, outj = a
D = np.load(W / 'export/form3_zone_delta.npz'); idx = D['indices']; f32 = lambda x: x.astype(np.float32).astype(np.float64)
def read(p):
    bpy.ops.wm.open_mainfile(filepath=p); b = bpy.data.objects['Body_M']; me = b.data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    polys = [list(q.vertices) for q in me.polygons]; fm = bpy.data.objects.get('Face_M'); F = None
    if fm: fv = np.empty(len(fm.data.vertices) * 3); fm.data.vertices.foreach_get('co', fv); F = fv.reshape(-1, 3)
    vg = {g.name: np.zeros(len(V)) for g in b.vertex_groups}; nm = {g.index: g.name for g in b.vertex_groups}
    for v in me.vertices:
        for g in v.groups: vg[nm[g.group]][v.index] = g.weight
    return dict(V=V, polys=polys, face=F, vg=vg, mats=[m.name for m in me.materials], objs=sorted(o.name for o in bpy.data.objects), cams={o.name: [list(map(float, r)) for r in o.matrix_world] for o in bpy.data.objects if o.type in ('CAMERA', 'EMPTY')}, custom=me.has_custom_normals)
A = read(pre); B = read(mer); res = {}
res['verts_pre'] = len(A['V']); res['verts_merged'] = len(B['V']); same = len(A['V']) == len(B['V'])
mv = np.zeros(len(A['V']), bool)
if same: mv = np.any(A['V'] != B['V'], axis=1)
res['verts_moved'] = int(mv.sum()); res['moved_subset_of_delta_indices'] = bool(set(np.where(mv)[0]) <= set(idx.tolist())) if same else False
res['delta_vertices'] = int(len(idx)); res['delta_at_new_positions'] = bool(np.all(B['V'][idx] == f32(D['new']))) if same else False
res['topology_identical'] = bool(A['polys'] == B['polys']); res['face_m_identical'] = bool(np.array_equal(A['face'], B['face'])) if A['face'] is not None else None
res['vertex_groups_identical'] = bool(set(A['vg']) == set(B['vg']) and all(np.array_equal(A['vg'][k], B['vg'][k]) for k in A['vg'])); res['materials_identical'] = A['mats'] == B['mats']; res['objects_identical'] = A['objs'] == B['objs']; res['cameras_empties_identical'] = A['cams'] == B['cams']
res['custom_normals_flag'] = (A['custom'], B['custom'])
ok = same and res['moved_subset_of_delta_indices'] and res['delta_at_new_positions'] and res['topology_identical'] and res['face_m_identical'] in (True, None) and res['vertex_groups_identical'] and res['materials_identical'] and res['objects_identical'] and res['cameras_empties_identical']
res['PASS'] = bool(ok); json.dump(res, open(outj, 'w'), indent=1); print('VERIFY_MERGE3', json.dumps(res))
sys.exit(0 if ok else 1)
