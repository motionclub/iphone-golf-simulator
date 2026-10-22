"""Zone / integrity audit of a candidate against the start blend (float32 positions).
blender -b --factory-startup --python audit_np.py -- <start.blend> <candidate.npy|candidate.blend> <out.json> [--selfx]
Checks: topology identical, NaN, moved-vertex zones (NAPE / PELVIS and the brief's nominal zones), protected sets untouched (Face_M, LOOP_* groups,
arms/hands |x|>0.215, legs/feet z<0.735, head z>1.47), flipped faces, self-intersections (BVH, optional), custom-normal consistency."""
import sys, json
import numpy as np, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; start, cand, outj = a[0], a[1], a[2]; selfx = '--selfx' in a
f32 = lambda x: np.asarray(x, np.float64).astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=start)
body = bpy.data.objects['Body_M']; me = body.data
n = len(me.vertices); V0 = np.empty(n * 3); me.vertices.foreach_get('co', V0); V0 = V0.reshape(-1, 3)
polys0 = [tuple(p.vertices) for p in me.polygons]
face0 = None
fm = bpy.data.objects.get('Face_M')
if fm: fv = np.empty(len(fm.data.vertices) * 3); fm.data.vertices.foreach_get('co', fv); face0 = fv.reshape(-1, 3)
groups = {g.index: g.name for g in body.vertex_groups}; loop = np.zeros(n, bool)
for v in me.vertices:
    for g in v.groups:
        if groups[g.group].startswith('LOOP_'): loop[v.index] = True
res = {}
if cand.endswith('.npy'): V1 = np.load(cand); polys1 = polys0; face1 = face0; topo = True
else:
    bpy.ops.wm.open_mainfile(filepath=cand); b1 = bpy.data.objects['Body_M']; m1 = b1.data
    V1 = np.empty(len(m1.vertices) * 3); m1.vertices.foreach_get('co', V1); V1 = V1.reshape(-1, 3); polys1 = [tuple(p.vertices) for p in m1.polygons]
    f1 = bpy.data.objects.get('Face_M'); face1 = None
    if f1: fv = np.empty(len(f1.data.vertices) * 3); f1.data.vertices.foreach_get('co', fv); face1 = fv.reshape(-1, 3)
    topo = polys1 == polys0
res['vertices'] = int(n); res['TOPOLOGY_IDENTICAL'] = bool(topo and len(V1) == n)
res['NAN'] = int(np.isnan(V1).sum())
A0, A1 = f32(V0), f32(V1); moved = np.any(A0 != A1, axis=1); res['moved'] = int(moved.sum())
d = np.linalg.norm(A1.astype(np.float64) - A0.astype(np.float64), axis=1) * 1000; res['max_move_mm'] = float(d.max()); res['mean_move_mm_moved'] = float(d[moved].mean()) if moved.any() else 0.0
dx = np.abs(A1[:, 0] - A0[:, 0]) * 1000; dz = np.abs(A1[:, 2] - A0[:, 2]) * 1000
res['max_dx_mm'] = float(dx.max()); res['max_dz_mm'] = float(dz.max()); res['n_dx_gt_0p01mm'] = int((dx > 0.01).sum()); res['n_dz_gt_0p01mm'] = int((dz > 0.01).sum())
X, Y, Z = A0[:, 0], A0[:, 1], A0[:, 2]
# declared zones (original positions)
NAPE = (Z >= 1.30) & (Z <= 1.50) & (np.abs(X) <= 0.18)
PELV = (Z >= 0.725) & (Z <= 1.07) & (np.abs(X) <= 0.22)
NOM_NAPE = (Z >= 1.28) & (Z <= 1.42) & (np.abs(X) <= 0.18); NOM_PELV = (Z >= 0.77) & (Z <= 1.05) & (np.abs(X) <= 0.22)
res['zones'] = dict(NAPE_ZONE='z in [1.30,1.50], |x|<=0.18 (original positions)', PELVIS_ZONE='z in [0.725,1.07], |x|<=0.22', brief_nominal_NAPE='z [1.28,1.42] |x|<=.18', brief_nominal_PELVIS='z [0.77,1.05] |x|<=.22')
res['ZONE_OUTSIDE_NAPE'] = int((moved & (Z >= 1.20) & ~NAPE & ~PELV).sum())      # moved vertices in the neck/upper-back band outside the declared nape zone
res['ZONE_OUTSIDE_PELVIS'] = int((moved & (Z < 1.20) & ~PELV).sum())
res['ZONE_OUTSIDE_NAPE_PELVIS'] = int((moved & ~NAPE & ~PELV).sum())
res['moved_in_NAPE'] = int((moved & NAPE).sum()); res['moved_in_PELVIS'] = int((moved & PELV).sum())
res['moved_outside_nominal_nape'] = int((moved & NAPE & ~NOM_NAPE).sum()); res['moved_outside_nominal_pelvis'] = int((moved & PELV & ~NOM_PELV).sum())
res['max_move_nape_mm'] = float(d[moved & NAPE].max()) if (moved & NAPE).any() else 0; res['max_move_pelvis_mm'] = float(d[moved & PELV].max()) if (moved & PELV).any() else 0
# graded by band for the legs-top extension disclosure
leg_ext = moved & PELV & (Z < 0.77); res['moved_below_z0p77'] = int(leg_ext.sum()); res['max_move_below_z0p77_mm'] = float(d[leg_ext].max()) if leg_ext.any() else 0
# protected sets
res['max_move_outside_nominal_nape_mm'] = float(d[moved & NAPE & ~NOM_NAPE].max()) if (moved & NAPE & ~NOM_NAPE).any() else 0.0; res['max_move_outside_nominal_pelvis_mm'] = float(d[moved & PELV & ~NOM_PELV].max()) if (moved & PELV & ~NOM_PELV).any() else 0.0
res['moved_loop_groups'] = int((moved & loop).sum()); res['moved_head_z_ge_1p47'] = int((moved & (Z > 1.47)).sum()); res['moved_arms_hands_absx_gt_0p215_z_gt_0p78'] = int((moved & (np.abs(X) > 0.215) & (Z > 0.78)).sum())
res['moved_legs_feet_z_lt_0p735'] = int((moved & (Z < 0.735)).sum()); res['moved_absx_gt_0p215'] = int((moved & (np.abs(X) > 0.215)).sum())
res['face_m_identical'] = bool(np.array_equal(face0, face1)) if face0 is not None and face1 is not None else None
# micro1k nape strip drift (z 1.362-1.395, |x|<=0.0245)
strip = (Z >= 1.362) & (Z <= 1.395) & (np.abs(X) <= 0.0245); res['micro1k_strip_vertices'] = int(strip.sum()); res['micro1k_strip_max_move_mm'] = float(d[strip].max()) if strip.any() else 0
# face flips
def fnormals(V, polys):
    out = np.zeros((len(polys), 3))
    for i, p in enumerate(polys):
        P = V[list(p)]; fn = np.zeros(3)
        for k in range(1, len(p) - 1): fn += np.cross(P[k] - P[0], P[k + 1] - P[0])
        out[i] = fn
    return out
N0 = fnormals(A0.astype(np.float64), polys0); N1 = fnormals(A1.astype(np.float64), polys1)
l0 = np.linalg.norm(N0, axis=1); l1 = np.linalg.norm(N1, axis=1); ok = (l0 > 1e-14) & (l1 > 1e-14)
dot = np.where(ok, (N0 * N1).sum(1) / np.maximum(l0 * l1, 1e-30), 1.0)
res['flipped_faces_vs_start'] = int((dot < 0).sum()); res['min_face_normal_dot'] = float(dot.min()); res['faces_turned_gt_45deg'] = int((dot < np.cos(np.radians(45))).sum())
res['degenerate_faces_after'] = int((l1 < 1e-14).sum())
# boundary / non-manifold counts (unchanged topology => unchanged)
if selfx:
    def pairs(V):
        tris = []; owner = []
        for i, p in enumerate(polys0):
            for k in range(1, len(p) - 1): tris.append((p[0], p[k], p[k + 1])); owner.append(i)
        bvh = BVHTree.FromPolygons([tuple(v) for v in V.astype(np.float64)], tris, epsilon=0.0)
        ov = bvh.overlap(bvh); out = set()
        for a_, b_ in ov:
            if a_ >= b_: continue
            if set(tris[a_]) & set(tris[b_]): continue
            out.add((owner[a_], owner[b_]))
        return out
    P0 = pairs(A0); P1 = pairs(A1); new = P1 - P0
    res['self_intersections_start'] = len(P0); res['self_intersections_after'] = len(P1); res['self_intersections_new'] = len(new)
    zc = np.array([A1[list(polys0[i])].mean(0) for i, _ in [(a_, b_) for a_, b_ in list(new)[:50]]]) if new else np.zeros((0, 3))
    res['new_self_intersection_centroids_z'] = [round(float(z), 3) for z in zc[:, 2]] if len(zc) else []
# custom normals consistency (blend input only)
if not cand.endswith('.npy'):
    m1.calc_loop_triangles(); cn = np.empty(len(m1.loops) * 3); m1.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    lv = np.empty(len(m1.loops), np.int32); m1.loops.foreach_get('vertex_index', lv)
    nv = np.zeros((n, 3))
    for p in polys1:
        P = V1[list(p)]; m = len(p); fn = np.zeros(3)
        for k in range(1, m - 1): fn += np.cross(P[k] - P[0], P[k + 1] - P[0])
        ln = np.linalg.norm(fn)
        if ln < 1e-18: continue
        fn /= ln
        for k in range(m):
            u = P[(k + 1) % m] - P[k]; w = P[(k - 1) % m] - P[k]; ang = np.arccos(np.clip(u @ w / max(np.linalg.norm(u) * np.linalg.norm(w), 1e-18), -1, 1)); nv[p[k]] += fn * ang
    nv /= np.maximum(np.linalg.norm(nv, axis=1, keepdims=True), 1e-18)
    sel = moved[lv]; ang = np.degrees(np.arccos(np.clip((cn[sel] * nv[lv[sel]]).sum(1), -1, 1))) if sel.any() else np.zeros(1)
    res['custom_normals'] = dict(has_custom=bool(m1.has_custom_normals), moved_corner_count=int(sel.sum()), angle_deg_median=float(np.median(ang)), angle_deg_p95=float(np.percentile(ang, 95)), angle_deg_max=float(ang.max()))
json.dump(res, open(outj, 'w'), indent=1); print('AUDIT', json.dumps({k: v for k, v in res.items() if k not in ('zones',)}))
