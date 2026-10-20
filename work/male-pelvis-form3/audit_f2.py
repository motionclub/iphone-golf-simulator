"""MALE_PELVIS_FORM2 audit: candidate vs start blend (float32 positions as stored).
blender -b --factory-startup --python audit_f2.py -- <start.blend> <candidate.blend> <out.json> [--selfx]
Declared zones (ORIGINAL positions): PELVIS z in [0.77,1.07], LEG_TOP strip z in [0.705,0.77), both |x| <= 0.22.
Checks: topology identical, NaN, moved vertices per zone, nothing outside the zones, protected sets untouched (Face_M, LOOP_* groups, arms/hands, calves/feet, head),
flipped faces, degenerate faces, self-intersections (BVH, optional), custom-normal consistency."""
import sys, json
import numpy as np, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; start, cand, outj = a[0], a[1], a[2]; selfx = '--selfx' in a
f32 = lambda x: np.asarray(x, np.float64).astype(np.float32)
bpy.ops.wm.open_mainfile(filepath=start)
body = bpy.data.objects['Body_M']; me = body.data
n = len(me.vertices); V0 = np.empty(n * 3); me.vertices.foreach_get('co', V0); V0 = V0.reshape(-1, 3)
polys0 = [tuple(p.vertices) for p in me.polygons]
fm = bpy.data.objects.get('Face_M'); face0 = None
if fm: fv = np.empty(len(fm.data.vertices) * 3); fm.data.vertices.foreach_get('co', fv); face0 = fv.reshape(-1, 3)
groups = {g.index: g.name for g in body.vertex_groups}; loop = np.zeros(n, bool)
for v in me.vertices:
    for g in v.groups:
        if groups[g.group].startswith('LOOP_'): loop[v.index] = True
bpy.ops.wm.open_mainfile(filepath=cand); b1 = bpy.data.objects['Body_M']; m1 = b1.data
V1 = np.empty(len(m1.vertices) * 3); m1.vertices.foreach_get('co', V1); V1 = V1.reshape(-1, 3); polys1 = [tuple(p.vertices) for p in m1.polygons]
f1 = bpy.data.objects.get('Face_M'); face1 = None
if f1: fv = np.empty(len(f1.data.vertices) * 3); f1.data.vertices.foreach_get('co', fv); face1 = fv.reshape(-1, 3)
res = {}
res['vertices'] = int(n); res['faces'] = len(polys0); res['TOPOLOGY_IDENTICAL'] = bool(polys1 == polys0 and len(V1) == n); res['NAN'] = int(np.isnan(V1).sum())
A0, A1 = f32(V0), f32(V1); moved = np.any(A0 != A1, axis=1); res['moved'] = int(moved.sum())
d = np.linalg.norm(A1.astype(np.float64) - A0.astype(np.float64), axis=1) * 1000
res['max_move_mm'] = float(d.max()); res['mean_move_mm_moved'] = float(d[moved].mean()) if moved.any() else 0.0
dx = np.abs(A1[:, 0] - A0[:, 0]) * 1000; dy = np.abs(A1[:, 1] - A0[:, 1]) * 1000; dz = np.abs(A1[:, 2] - A0[:, 2]) * 1000
res['max_dx_mm'] = float(dx.max()); res['max_dy_mm'] = float(dy.max()); res['max_dz_mm'] = float(dz.max())
X, Y, Z = A0[:, 0], A0[:, 1], A0[:, 2]; U = np.abs(X)
PEL = (Z >= 0.77) & (Z <= 1.07) & (U <= 0.22); LEG = (Z >= 0.705) & (Z < 0.77) & (U <= 0.22); IN = PEL | LEG
res['zones'] = dict(PELVIS='z in [0.77,1.07], |x|<=0.22 (original positions)', LEG_TOP='z in [0.705,0.77), |x|<=0.22 (original positions)')
res['moved_in_PELVIS'] = int((moved & PEL).sum()); res['moved_in_LEG_TOP'] = int((moved & LEG).sum())
res['max_move_PELVIS_mm'] = float(d[moved & PEL].max()) if (moved & PEL).any() else 0.0
res['max_move_LEG_TOP_mm'] = float(d[moved & LEG].max()) if (moved & LEG).any() else 0.0
res['ZONE_OUTSIDE'] = int((moved & ~IN).sum())
res['max_move_below_z0p735_mm'] = float(d[moved & (Z < 0.735)].max()) if (moved & (Z < 0.735)).any() else 0.0; res['moved_below_z0p735'] = int((moved & (Z < 0.735)).sum())
res['moved_below_z0p77'] = int((moved & (Z < 0.77)).sum())
res['moved_loop_groups'] = int((moved & loop).sum()); res['moved_head_z_ge_1p10'] = int((moved & (Z > 1.10)).sum())
res['moved_calves_feet_z_lt_0p70'] = int((moved & (Z < 0.70)).sum()); res['moved_arms_hands_absx_gt_0p215_z_gt_0p78'] = int((moved & (U > 0.215) & (Z > 0.78)).sum())
res['moved_absx_gt_0p215'] = int((moved & (U > 0.215)).sum())
res['face_m_identical'] = bool(np.array_equal(face0, face1)) if face0 is not None and face1 is not None else None
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
res['flipped_faces_vs_start'] = int((dot < 0).sum()); res['min_face_normal_dot'] = float(dot.min()); res['faces_turned_gt_45deg'] = int((dot < np.cos(np.radians(45))).sum()); res['faces_turned_gt_60deg'] = int((dot < np.cos(np.radians(60))).sum())
res['degenerate_faces_after'] = int((l1 < 1e-14).sum())
if selfx:
    def pairs(V):
        tris = []; owner = []
        for i, p in enumerate(polys0):
            for k in range(1, len(p) - 1): tris.append((p[0], p[k], p[k + 1])); owner.append(i)
        bvh = BVHTree.FromPolygons([tuple(v) for v in V.astype(np.float64)], tris, epsilon=0.0); ov = bvh.overlap(bvh); out = set()
        for a_, b_ in ov:
            if a_ >= b_: continue
            if set(tris[a_]) & set(tris[b_]): continue
            out.add((owner[a_], owner[b_]))
        return out
    P0 = pairs(A0); P1 = pairs(A1); new = P1 - P0
    res['self_intersections_start'] = len(P0); res['self_intersections_after'] = len(P1); res['self_intersections_new'] = len(new)
    zc = np.array([A1[list(polys0[a_])].mean(0) for a_, b_ in list(new)[:50]]) if new else np.zeros((0, 3))
    res['new_self_intersection_centroids_mm'] = [[round(float(c) * 1000, 1) for c in r] for r in zc[:20]]
m1.calc_loop_triangles(); cn = np.empty(len(m1.loops) * 3); m1.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(len(m1.loops), np.int32); m1.loops.foreach_get('vertex_index', lv); nv = np.zeros((n, 3))
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
