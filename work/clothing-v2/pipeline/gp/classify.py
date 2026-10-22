"""GARMENT PIPELINE: which garment covers which surface in the bind pose (Blender mathutils BVH rays).
A vertex is covered by garment c when no ray of a hemisphere fan around its normal escapes (every ray hits the body or a garment) and at
least one ray hits c first. Triangles: covered by c when all three vertices are. Bit k of the mask = coverer k (the order of `coverers`)."""
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def fan(n_ring=6, angles=(40.0, 72.0)):
    dirs = [(0.0, 0.0, 1.0)]
    for r, a in enumerate(angles):
        t = math.radians(a)
        for k in range(n_ring):
            ph = 2 * math.pi * (k + .5 * r) / n_ring
            dirs.append((math.sin(t) * math.cos(ph), math.sin(t) * math.sin(ph), math.cos(t)))
    return np.array(dirs)


def frame_of(n):
    a = np.where(np.abs(n[:, 0:1]) < .9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))
    t = np.cross(n, a); t /= np.linalg.norm(t, axis=1, keepdims=True)
    b = np.cross(n, t)
    return t, b


def vnormals(P, tri):
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, tri[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


class World:
    """one BVH over a list of (P, tri) meshes; face -> mesh index."""
    def __init__(self, meshes):
        verts, faces, owner, off = [], [], [], 0
        for i, (P, tri) in enumerate(meshes):
            verts.append(P); faces.append(tri + off); owner.append(np.full(len(tri), i)); off += len(P)
        self.V = np.concatenate(verts); self.F = np.concatenate(faces); self.owner = np.concatenate(owner)
        self.tree = BVHTree.FromPolygons([tuple(v) for v in self.V], [tuple(f) for f in self.F], all_triangles=True)

    def first_hit(self, o, d, maxd):
        r = self.tree.ray_cast(Vector(o), Vector(d), maxd)
        return -1 if r[2] is None else int(self.owner[r[2]])


def covered_mask(world, P, N, coverer_ids, maxd=.30, eps=6e-4, sample=None):
    """per vertex uint32 bitmask over coverer_ids (mesh indices in `world`). sample = vertex subset to test (others 0)."""
    F = fan(); t, b = frame_of(N)
    out = np.zeros(len(P), np.uint32)
    cid = {m: k for k, m in enumerate(coverer_ids)}
    idx = range(len(P)) if sample is None else sample
    for v in idx:
        o = P[v] + N[v] * eps
        bits = 0; escaped = False
        for d in F:
            dv = d[0] * t[v] + d[1] * b[v] + d[2] * N[v]
            h = world.first_hit(o, dv, maxd)
            if h < 0: escaped = True; break
            k = cid.get(h)
            if k is not None: bits |= 1 << k
        if not escaped: out[v] = bits
    return out
