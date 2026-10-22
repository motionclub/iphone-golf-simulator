"""blender -b <blend> --python verify_blend.py -- <cand.npz> <base_dump.npz> <out.json> : compare the written blend against the candidate and the baseline dump"""
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); B0 = np.load(a[1])
o = bpy.data.objects['Body_M']; me = o.data
n = len(me.vertices); V = np.zeros(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cv = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', cv)
ls = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_total', lt)
res = dict(verts=n, polys=len(me.polygons), loops=len(me.loops))
res['verts_equal_candidate'] = bool(np.array_equal(V, D['V']))
polys = [tuple(cv[s:s + t]) for s, t in zip(ls, lt)]
cpolys = [tuple(D['corner_verts'][s:s + t]) for s, t in zip(D['loop_start'], D['loop_total'])]
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
from collections import Counter
res['polys_equal_candidate_multiset'] = bool(len(polys) == len(cpolys) and Counter(canon(p) for p in polys) == Counter(canon(p) for p in cpolys))
for name in ('sharp_face', 'sharp_edge'):
    at = me.attributes.get(name)
    if at is None: res[name + '_true'] = 0
    else:
        arr = np.zeros(len(at.data), bool); at.data.foreach_get('value', arr); res[name + '_true'] = int(arr.sum())
cn = me.attributes.get('custom_normal')
if cn is not None:
    arr = np.zeros(len(cn.data) * 2, np.int16); cn.data.foreach_get('value', arr); arr = arr.reshape(-1, 2)
    res['custom_normal_loops'] = len(arr); res['custom_normal_nonzero'] = int((arr != 0).any(1).sum())
    # compare against baseline for kept loops: loops of baseline polys that still exist unchanged (same vertex tuple)
    b_cn = B0['custom_normal_i16']; b_cv = B0['corner_verts']; b_ls = B0['loop_start']; b_lt = B0['loop_total']
    base_map = {}
    for s, t in zip(b_ls, b_lt):
        base_map[canon(tuple(b_cv[s:s + t]))] = (s, t, tuple(b_cv[s:s + t]))
    same = 0; diff = 0
    for pi, (s, t) in enumerate(zip(ls, lt)):
        k = canon(polys[pi])
        if k in base_map:
            bs, bt, bp = base_map[k]
            # same cyclic order -> compare loop by loop with rotation
            mine = list(polys[pi]); ref = list(bp)
            if len(mine) == len(ref):
                r = ref.index(mine[0]) if mine[0] in ref else None
                if r is not None and all(mine[j] == ref[(r + j) % len(ref)] for j in range(len(ref))):
                    for j in range(t):
                        if np.array_equal(arr[s + j], b_cn[bs + (r + j) % t]): same += 1
                        else: diff += 1
    res['custom_normal_loops_same_as_baseline'] = same; res['custom_normal_loops_diff_from_baseline'] = diff
res['has_custom_normals'] = bool(me.has_custom_normals)
res['vertex_groups'] = [g.name for g in o.vertex_groups]
vg = 0
for v in me.vertices: vg += len(v.groups)
res['vertex_group_entries'] = vg; res['baseline_vertex_group_entries'] = int(len(B0['vg_idx']))
res['materials'] = [m.name for m in me.materials]
json.dump(res, open(a[2], 'w'), indent=1); print(json.dumps(res))
