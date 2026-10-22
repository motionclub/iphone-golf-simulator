"""blender -b <final.blend> --python verify_blend_f.py -- <start_dump.npz> <out.json>
Independent checks on the WRITTEN blend: topology, signed volume, BVH self-intersections (hand vs hand / hand vs body), hair + other objects hash,
materials, UV of new faces, custom normals vs the start dump."""
import bpy, sys, json, hashlib, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
S0 = np.load(a[0]); outp = a[1]
N0 = 22419
o = bpy.data.objects['Body_F']; me = o.data
res = {}
n = len(me.vertices); V = np.zeros(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cv = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', cv)
ls = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
lt = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_total', lt)
mi = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
polys = [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
res['verts'] = n; res['polys'] = len(polys); res['loops'] = len(cv); res['tris'] = int(sum(t - 2 for t in lt))
res['materials'] = [m.name if m else None for m in me.materials]
# edge manifoldness / degenerate faces / loose verts
from collections import defaultdict
ec = defaultdict(list)
for fi, p in enumerate(polys):
    for k in range(len(p)):
        a_, b_ = p[k], p[(k + 1) % len(p)]; ec[(min(a_, b_), max(a_, b_))].append((a_, b_))
res['boundary_edges'] = sum(1 for v in ec.values() if len(v) == 1); res['nonmanifold_edges'] = sum(1 for v in ec.values() if len(v) > 2)
res['flipped_edges'] = sum(1 for v in ec.values() if len(v) == 2 and v[0] == v[1])
used = np.zeros(n, bool)
for p in polys: used[list(p)] = True
res['loose_verts'] = int((~used).sum())
deg = 0; minarea = 1e9
Vd = V.astype(np.float64); vol = 0.0
for p in polys:
    P = Vd[list(p)]
    ar = 0.0
    for k in range(1, len(p) - 1):
        c = np.cross(P[k] - P[0], P[k + 1] - P[0]); ar += 0.5 * np.linalg.norm(c); vol += np.dot(P[0], c) / 6.0
    minarea = min(minarea, ar)
    if ar < 1e-10: deg += 1
res['degenerate_faces'] = deg; res['min_face_area_mm2'] = minarea * 1e6; res['signed_volume_m3'] = vol
# UV / material of new faces (faces beyond the kept ones are the last ones)
uv = me.uv_layers[0]; uvd = np.zeros(len(cv) * 2, np.float32); uv.data.foreach_get('uv', uvd); uvd = uvd.reshape(-1, 2)
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
s_cv, s_ls, s_lt = S0['corner_verts'], S0['loop_start'], S0['loop_total']
s_polys = [tuple(int(x) for x in s_cv[s:s + t]) for s, t in zip(s_ls, s_lt)]
s_map = {canon(p): i for i, p in enumerate(s_polys)}
same = 0; newf = 0; uvdiff = 0; matdiff = 0; new_ids = []
for fi, p in enumerate(polys):
    k = canon(p)
    if k in s_map and all(x < N0 for x in p):
        sj = s_map[k]; same += 1
        if mi[fi] != S0['material_index'][sj]: matdiff += 1
        # corner uvs: compare after aligning rotation
        sp = s_polys[sj]; r = list(sp).index(p[0])
        ok = all(np.allclose(uvd[ls[fi] + j], S0['uv'][s_ls[sj] + (r + j) % lt[fi]]) for j in range(lt[fi]))
        if not ok: uvdiff += 1
    else:
        newf += 1; new_ids.append(fi)
res['faces_unchanged'] = same; res['faces_new'] = newf; res['unchanged_material_diffs'] = matdiff; res['unchanged_uv_diffs'] = uvdiff
res['new_faces_material'] = sorted(set(me.materials[int(mi[i])].name for i in new_ids))
res['new_faces_uv'] = sorted(set((float(np.round(uvd[ls[i] + j][0], 3)), float(np.round(uvd[ls[i] + j][1], 3))) for i in new_ids for j in range(lt[i])))
# custom normals vs the start dump (unchanged faces)
cn = me.attributes['custom_normal']; raw = np.zeros(len(cv) * 2, np.int16); cn.data.foreach_get('value', raw); raw = raw.reshape(-1, 2)
s_raw = S0['custom_normal_i16']
eq = 0; ne = 0; ne_verts = set()
for fi, p in enumerate(polys):
    k = canon(p)
    if k in s_map and all(x < N0 for x in p):
        sj = s_map[k]; sp = s_polys[sj]; r = list(sp).index(p[0])
        for j in range(lt[fi]):
            if np.array_equal(raw[ls[fi] + j], s_raw[s_ls[sj] + (r + j) % lt[fi]]): eq += 1
            else: ne += 1; ne_verts.add(p[j])
res['normals_loops_equal_start'] = eq; res['normals_loops_diff_start'] = ne; res['normals_diff_verts'] = len(ne_verts)
res['has_custom_normals'] = bool(me.has_custom_normals)
# BVH self-intersections (non-adjacent = sharing no vertex)
tris = []; tri_face = []
for fi, p in enumerate(polys):
    for k in range(1, len(p) - 1): tris.append((p[0], p[k], p[k + 1])); tri_face.append(fi)
tris = np.array(tris)
bvh = BVHTree.FromPolygons([tuple(v) for v in Vd], [tuple(int(i) for i in t) for t in tris], all_triangles=True, epsilon=0.0)
pairs = bvh.overlap(bvh)
hv = np.zeros(n, bool)
for sd in (1, -1): hv[np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers/data/start_hand_verts_%d.npy' % sd)] = True
hv[N0:] = True
cnt_all = 0; cnt_hand_hand = 0; cnt_hand_body = 0; cnt_arm = 0
seen = set()
for i, j in pairs:
    if i >= j: continue
    ti, tj = set(tris[i].tolist()), set(tris[j].tolist())
    if ti & tj: continue
    cnt_all += 1
    hi, hj = hv[tris[i]].any(), hv[tris[j]].any()
    if hi and hj: cnt_hand_hand += 1
    elif hi or hj: cnt_hand_body += 1
res['bvh_overlap_pairs_nonadjacent'] = cnt_all; res['bvh_hand_vs_hand'] = cnt_hand_hand; res['bvh_hand_vs_body'] = cnt_hand_body
# hair + other objects
h = bpy.data.objects['Hair_F']
hc = np.zeros(len(h.data.vertices) * 3, np.float32); h.data.vertices.foreach_get('co', hc)
res['hair_sha'] = hashlib.sha256(hc.tobytes()).hexdigest(); res['hair_tris'] = int(sum(len(p.vertices) - 2 for p in h.data.polygons))
res['objects'] = {ob.name: [round(x, 6) for x in list(ob.location) + list(ob.rotation_euler) + list(ob.scale)] for ob in bpy.data.objects}
json.dump(res, open(outp, 'w'), indent=1)
print('VERIFY', json.dumps({k: v for k, v in res.items() if k not in ('objects',)}))
