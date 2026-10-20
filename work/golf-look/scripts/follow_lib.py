"""Shared geometry helpers for the gate-3 measurement (measure_follow.py) and the weight fitter (fit_weights.py): one definition of the covered zone (GATE_DEFS A5-A8)."""
import numpy as np
from mathutils.bvhtree import BVHTree

COVER_RANGE, BEHIND, HOME_NEAR = 0.05, 0.04, 0.06
HUG = 0.040
GAP_MAX, MUTUAL_TOL = 0.035, 0.004
BEAM = ((0, 0), (5e-4, 0), (-5e-4, 0), (0, 5e-4), (0, -5e-4))


def tolist(arr):
    return [tuple(map(float, v)) for v in arr]


def bvh_from(co, tris):
    return BVHTree.FromPolygons(tolist(co), [tuple(map(int, t)) for t in tris], epsilon=0.0)


def vertex_normals(obj):
    me = obj.data
    me.calc_loop_triangles()
    n = np.empty(len(me.vertices) * 3, np.float32)
    me.vertex_normals.foreach_get('vector', n)
    return n.reshape(-1, 3).astype(np.float64)


def evaluated_normals(obj, dg):
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    n = np.empty(len(me.vertices) * 3, np.float32)
    me.vertex_normals.foreach_get('vector', n)
    ev.to_mesh_clear()
    n = n.reshape(-1, 3).astype(np.float64)
    M = np.array(ev.matrix_world, np.float64)[:3, :3]
    n = n @ M.T
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)


def beam_origins(v, n):
    t1 = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    return [v + t1 * a + t2 * b for a, b in BEAM]


def all_hits(bvh, o, d, maxd, limit=6):
    """every intersection along the ray: [(t, dot(d, N), tri index, location)]"""
    hits = []
    cur = np.array(o, float)
    travelled = 0.0
    for _ in range(limit):
        loc, nrm, idx, dist = bvh.ray_cast(tuple(map(float, cur)), tuple(map(float, d)), maxd - travelled)
        if loc is None:
            break
        travelled += dist
        hits.append((travelled, float(np.dot(np.array(nrm), d)), int(idx), np.array(loc)))
        cur = np.array(loc) + np.array(d) * 1e-6
        travelled += 1e-6
    return hits


def covered_pattern(hits):
    """exactly two hits, inner wall (front-facing: normal toward the ray origin) then outer wall (back-facing), <= 12 mm apart"""
    return len(hits) == 2 and hits[0][1] < 0 and hits[1][1] > 0 and hits[1][0] - hits[0][0] <= 0.012


def bary_of(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        return np.array([1.0, 0.0, 0.0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.array([1 - v - w, v, w])


def compute_zone(kco0, ktri, bco0, bn0, body_bvh0, kit_bvh=None):
    """Covered body vertices of one piece at bind (A5 + A8) with their home outer-wall triangle and barycentric coordinates.
    Returns (zone idx, home triangle idx, home barycentric (n,3), inner-wall triangle idx, inner barycentric)."""
    bv = kit_bvh if kit_bvh is not None else bvh_from(kco0, ktri)
    zone, ht, hb, it, ib = [], [], [], [], []
    for i in range(len(bco0)):
        v, n = bco0[i], bn0[i]
        if bv.find_nearest(tuple(map(float, v)), 0.08)[0] is None:
            continue
        good = 0
        for o in beam_origins(v, n):
            if covered_pattern(all_hits(bv, o, n, 1.0)):
                good += 1
        if good < 3:
            continue
        h = all_hits(bv, v, n, 1.0)
        if not covered_pattern(h):
            continue
        # mutual nearest (A8)
        if h[0][0] > GAP_MAX or body_bvh0.find_nearest(tuple(map(float, h[0][3])))[3] < h[0][0] - MUTUAL_TOL:
            continue
        t_in, t_out = ktri[h[0][2]], ktri[h[1][2]]
        zone.append(i)
        ht.append(h[1][2])
        hb.append(bary_of(h[1][3], kco0[t_out[0]], kco0[t_out[1]], kco0[t_out[2]]))
        it.append(h[0][2])
        ib.append(bary_of(h[0][3], kco0[t_in[0]], kco0[t_in[1]], kco0[t_in[2]]))
    return (np.array(zone, np.int64), np.array(ht, np.int64), np.array(hb), np.array(it, np.int64), np.array(ib))
