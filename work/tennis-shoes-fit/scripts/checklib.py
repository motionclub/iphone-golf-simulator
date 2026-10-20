"""Fit measurements shared by the tuning script and the final gate script (numpy + Blender's BVH; run inside Blender's python).
All meshes are plain arrays in BODY space (metres, Z up, the toes point to -Y)."""
import math, json
import numpy as np
from mathutils.bvhtree import BVHTree


def bvh(V, F, eps=0.0):
    return BVHTree.FromPolygons([tuple(v) for v in np.asarray(V, float).tolist()], [tuple(f) for f in np.asarray(F).tolist()], epsilon=eps)


def mt_first(V, F, o, d, tmin=1e-6):
    """exact Moller-Trumbore, smallest positive ray parameter over ALL triangles (None = no hit).  Used to confirm every BVH miss
    (Blender's BVH ray_cast can miss rays that cross triangle edges)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(d[None, :], e2)
    det = np.einsum('ij,ij->i', e1, h)
    ok = np.abs(det) > 1e-14
    f = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0)
    s = o[None, :] - a
    u = f * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, e1)
    v = f * (q @ d)
    t = f * np.einsum('ij,ij->i', e2, q)
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > tmin)
    return float(t[hit].min()) if hit.any() else None


def winding_numbers(P, V, F, chunk=1500):
    """generalised winding number of the (closed, outward-oriented) triangle soup (V,F) at points P: ~ +1 inside a solid, 0 outside."""
    P = np.asarray(P, float)
    out = np.zeros(len(P))
    a0, b0, c0 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    for i in range(0, len(P), chunk):
        p = P[i:i + chunk][:, None, :]
        A, B, C = a0[None] - p, b0[None] - p, c0[None] - p
        la, lb, lc = np.linalg.norm(A, axis=2), np.linalg.norm(B, axis=2), np.linalg.norm(C, axis=2)
        num = np.einsum('ijk,ijk->ij', A, np.cross(B, C))
        den = la * lb * lc + np.einsum('ijk,ijk->ij', A, B) * lc + np.einsum('ijk,ijk->ij', A, C) * lb + np.einsum('ijk,ijk->ij', B, C) * la
        out[i:i + chunk] = 2.0 * np.arctan2(num, den).sum(1) / (4.0 * np.pi)
    return out


def sphere_dirs(n_az=16, elevs=(-90, -60, -35, -15, 0)):
    """directions for the enclosure test: straight down, and rings at the given (non-positive) elevations."""
    out = []
    for e in elevs:
        if e == -90:
            out.append(np.array([0.0, 0.0, -1.0]))
            continue
        ce, se = math.cos(math.radians(e)), math.sin(math.radians(e))
        for k in range(n_az):
            a = 2 * math.pi * k / n_az
            out.append(np.array([math.sin(a) * ce, -math.cos(a) * ce, se]))
    return out


def enclosed_mask(P, V, F, tree, dirs, far=1.0):
    """True where EVERY ray from the point (all given directions) hits the mesh; BVH misses are re-checked exactly."""
    ok = np.ones(len(P), bool)
    for i, p in enumerate(np.asarray(P, float).tolist()):
        for d in dirs:
            h = tree.ray_cast(p, d.tolist(), far)
            if h[2] is None:
                t = mt_first(V, F, np.array(p), d)
                if t is None or t > far:
                    ok[i] = False
                    break
    return ok


def nearest_dist(tree, P):
    return np.array([tree.find_nearest(p)[3] if tree.find_nearest(p)[2] is not None else 1e3 for p in np.asarray(P, float).tolist()])


def signed_dist(tree, P):
    out = np.empty(len(P))
    for i, p in enumerate(np.asarray(P, float).tolist()):
        loc, n, idx, d = tree.find_nearest(p)
        s = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
        out[i] = d if s >= 0 else -d
    return out


def view_dirs(els, n_az=24):
    out = []
    for e in els:
        for k in range(n_az):
            a = 2 * math.pi * k / n_az
            ce, se = math.cos(math.radians(e)), math.sin(math.radians(e))
            out.append((e, k * 360 / n_az, np.array([math.sin(a) * ce, -math.cos(a) * ce, se])))
    return out


def tri_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return n / ln


def skin_samples(V, F, side, zmax, step_tri=1, zmin=-1.0):
    """triangle-centroid samples of one leg's skin below zmax: (points, outward normals)."""
    cen = V[F].mean(1)
    sel = (cen[:, 0] * side > 0.02) & (cen[:, 2] < zmax) & (cen[:, 2] > zmin)
    n = tri_normals(V, F)
    return cen[sel][::step_tri], n[sel][::step_tri]


def exposed_skin(S, N, V_occ, F_occ, tree_occ, tree_body, V_body_all, els=(-10, 0, 10, 25, 45), n_az=24, R=3.0):
    """camera-side rays: a skin sample is EXPOSED if a 1 mm wide beam from a distant camera reaches it with nothing from the occluder meshes
    (shoe + sock) in front (exact ray-triangle confirmation of every unblocked ray).  The body itself must not be in front (the other leg)."""
    dirs = view_dirs(els, n_az)
    exposed = []
    tested = 0
    up = np.array([0, 0, 1.0])
    for s, n in zip(S, N):
        for e, a, d in dirs:
            if float(n @ d) <= 0.05:
                continue
            far = s + d * R
            hb = tree_body.ray_cast(far.tolist(), (-d).tolist())
            if hb[2] is None or hb[3] < R - 2e-3:
                continue                                        # the body (other leg / this leg's far side) is in front
            tested += 1
            h = tree_occ.ray_cast(far.tolist(), (-d).tolist())
            if h[2] is not None and h[3] < R - 1e-4:
                continue
            tt = mt_first(V_occ, F_occ, far, -d)
            if tt is not None and tt < R - 1e-4:
                continue
            sx = np.cross(d, up)
            sx /= np.linalg.norm(sx)
            sy = np.cross(d, sx)
            blocked = False
            for off in (0.0005 * sx, -0.0005 * sx, 0.0005 * sy, -0.0005 * sy):
                t2 = mt_first(V_occ, F_occ, far + off, -d)
                if t2 is not None and t2 < R - 1e-4:
                    blocked = True
                    break
            if blocked:
                continue
            exposed.append((s.round(4).tolist(), e, a, round(float(n @ d), 3)))
    return exposed, tested
