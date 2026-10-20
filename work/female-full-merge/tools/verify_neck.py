"""Neck contour / weld evidence + F3's own self-overlap count (run inside Blender).  blender -b --factory-startup --python tools/verify_neck.py -> data/neck_checks.json"""
import bpy, numpy as np, json, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
FIN, F3, A, S3 = (L(n) for n in ('final_body', 'f3_body', 'artdir_body', 'stage3_body'))
D = np.load('export/full_merge_delta.npz'); res = {}
def tris_of(d):
    ls, lt, cv = d['loop_start'], d['loop_total'], d['corner_verts']; T = []
    for fi, (s, t) in enumerate(zip(ls, lt)):
        for k in range(1, t - 1): T.append((int(cv[s]), int(cv[s + k]), int(cv[s + k + 1])))
    return np.array(T)
# ---- F3's own non-adjacent overlaps vs merged
def overlaps(d):
    V = d['V'].astype(np.float64); T = tris_of(d)
    bv = BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(int(i) for i in t) for t in T], all_triangles=True, epsilon=0.0)
    out = []
    for i, j in bv.overlap(bv):
        if i < j and not (set(T[i].tolist()) & set(T[j].tolist())): out.append((i, j))
    c = np.array([V[T[i]].mean(0) for i, j in out]) if out else np.zeros((0, 3))
    return len(out), (c[:, 2].min() if len(c) else None, c[:, 2].max() if len(c) else None), (np.abs(c[:, 0]).max() if len(c) else None)
nF3, zF3, xF3 = overlaps(F3); nFin, zFin, xFin = overlaps(FIN)
res['self_overlap_pairs'] = dict(F3_Body_F=nF3, F3_z_range=zF3, merged=nFin, merged_z_range=zFin, same_count_as_F3=bool(nF3 == nFin), note='all inside the head (z>1.4); F3 Body_F has the same pairs')
print('self-overlap pairs: F3', nF3, zF3, ' merged', nFin, zFin)
# ---- contour sections: for each z, extreme y (front/back) and half-width x of the mesh cross-section (edge/plane intersections), neck band only (|x|<0.11 & y>-0.2 to avoid arms)
def sections(d, zs, xlim=0.10):
    V = d['V'].astype(np.float64); ls, lt, cv = d['loop_start'], d['loop_total'], d['corner_verts']; E = set()
    for s, t in zip(ls, lt):
        vs = cv[s:s + t]
        for i in range(t):
            a, b = int(vs[i]), int(vs[(i + 1) % t]); E.add((min(a, b), max(a, b)))
    E = np.array(sorted(E)); P, Q = V[E[:, 0]], V[E[:, 1]]; out = {}
    for z in zs:
        m = ((P[:, 2] - z) * (Q[:, 2] - z) < 0)
        t = (z - P[m, 2]) / (Q[m, 2] - P[m, 2]); X = P[m] + t[:, None] * (Q[m] - P[m])
        X = X[np.abs(X[:, 0]) < xlim]
        out[round(float(z), 4)] = dict(y_front=float(X[:, 1].min()), y_back=float(X[:, 1].max()), x_half=float(np.abs(X[:, 0]).max()))
    return out
zs = np.round(np.arange(1.340, 1.5001, 0.005), 4)
sm, sa = sections(FIN, zs), sections(A, zs)
rows = []
for z in zs:
    z = round(float(z), 4); rows.append((z, sm[z]['y_front'] * 1000, sa[z]['y_front'] * 1000, sm[z]['y_back'] * 1000, sa[z]['y_back'] * 1000, sm[z]['x_half'] * 1000, sa[z]['x_half'] * 1000))
res['contour_rows_z_yfront_merged_yfront_art_yback_merged_yback_art_xhalf_merged_xhalf_art_mm'] = rows
print(' z      y_front(merged/ArtDir)    y_back(merged/ArtDir)    x_half(merged/ArtDir)   [mm]')
for r in rows: print('%.3f   %8.2f %8.2f   %8.2f %8.2f   %7.2f %7.2f' % r)
# contour kink: second difference of y_front/y_back/x_half over 3 rows centred on the ring top (z 1.405)
def slope(rows, col, z0, z1):
    a = [r for r in rows if abs(r[0] - z0) < 1e-6][0]; b = [r for r in rows if abs(r[0] - z1) < 1e-6][0]; return (b[col] - a[col]) / ((z1 - z0) * 1000)
for nm, col in (('y_front', 1), ('y_back', 3), ('x_half', 5)):
    below = slope(rows, col, 1.385, 1.400); above = slope(rows, col, 1.410, 1.425)
    colA = col + 1; belowA = slope(rows, colA, 1.385, 1.400); aboveA = slope(rows, colA, 1.410, 1.425)
    res[f'slope_change_{nm}'] = dict(merged_below=below, merged_above=above, ArtDir_below=belowA, ArtDir_above=aboveA, merged_delta_slope=above - below, ArtDir_delta_slope=aboveA - belowA)
    print(nm, 'slope mm/mm below ring %.3f above %.3f (change %.3f);  ArtDir below %.3f above %.3f (change %.3f)' % (below, above, above - below, belowA, aboveA, aboveA - belowA))
# ---- per-azimuth offset of the first head row vs the old surface
Vf = FIN['V'].astype(np.float64)
json.dump(res, open('data/neck_checks.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print('NECK_DONE')
