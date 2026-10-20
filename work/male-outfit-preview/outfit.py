"""Garments for the male HeroBase example.  Each garment is an offset shell of Body_M (separate object, real thickness).

Body_M coordinates are never modified.  Run inside Blender (live MCP or headless).
"""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from preview_common import material, get_collection, clear_collection, make_mesh_obj


def sm01(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------------------------------
class Body:
    """Numpy view of Body_M + normals + BVH.  Right arm geometry constants measured from the delivered mesh."""

    ARM_C = np.array([0.407, -0.052, 1.096])
    ARM_A = np.array([0.665, -0.156, -0.730])
    ARM_A = ARM_A / np.linalg.norm(ARM_A)

    def __init__(self, obj):
        self.obj = obj
        me = obj.data
        self.V = np.array([v.co[:] for v in me.vertices], float)
        self.polys = [tuple(p.vertices) for p in me.polygons]
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        self.N = np.array([v.normal[:] for v in bm.verts], float)
        self.tree = BVHTree.FromBMesh(bm)
        bm.free()

    # arm helpers (sign = +1 right arm (x>0), -1 left arm (x<0)) --------------------------------------------------
    def arm_coords(self, P, sign):
        Q = P.copy()
        Q[:, 0] = Q[:, 0] * sign
        R = Q - self.ARM_C
        s = R @ self.ARM_A
        r = np.linalg.norm(R - np.outer(s, self.ARM_A), axis=1)
        return s, r

    def signed_gap(self, P):
        """distance of points to the body surface along the surface normal (negative = inside)."""
        out = np.empty(len(P))
        nrm = np.empty((len(P), 3))
        for i, p in enumerate(P):
            loc, n, idx, d = self.tree.find_nearest(Vector(p))
            out[i] = (Vector(p) - loc).dot(n)
            nrm[i] = n
        return out, nrm


# ----------------------------------------------------------------------------------------------------------------
def build_shell(B, name, pred, d_fn, mat_fn, mats, coll, snaps=(), thickness=0.004, min_gap=0.006,
                smooth_iters=18, pin_boundary=True, extra_pos=None, solid=True):
    """pred(V)->bool mask of body vertices;  snaps: list of callables f(P, bmask) that move boundary vertices in place;
    d_fn(P0, idx)->offsets (m) along body normals;  mat_fn(centroids)->int array for the OUTER faces."""
    V = B.V
    m = pred(V)
    polys = [p for p in B.polys if all(m[i] for i in p)]
    used = sorted(set(i for p in polys for i in p))
    remap = {v: k for k, v in enumerate(used)}
    faces = [tuple(remap[i] for i in p) for p in polys]
    P = V[used].copy()
    N = B.N[used].copy()
    # boundary verts
    ec = {}
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e = (min(a, b), max(a, b))
            ec[e] = ec.get(e, 0) + 1
    bverts = set()
    for (a, b), c in ec.items():
        if c == 1:
            bverts.add(a)
            bverts.add(b)
    bmask = np.zeros(len(P), bool)
    bmask[list(bverts)] = True
    # snap boundary onto cutting surfaces (moving along the surface direction)
    for fn in snaps:
        fn(P, bmask)
    P0 = P.copy()
    off = d_fn(P0, used)
    Q = P0 + N * off[:, None]
    for fn in snaps:                 # offsets move rim verts off their cutting surface: put them back
        fn(Q, bmask)
    # adjacency for smoothing
    E = set()
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            E.add((min(a, b), max(a, b)))
    E = np.array(sorted(E))
    deg = np.bincount(E.ravel(), minlength=len(P)).astype(float)

    def lap(X):
        s = np.zeros_like(X)
        np.add.at(s, E[:, 0], X[E[:, 1]])
        np.add.at(s, E[:, 1], X[E[:, 0]])
        return s / np.maximum(deg, 1)[:, None] - X

    loops = boundary_loops({'faces': faces})
    free = (~bmask) if pin_boundary else np.ones(len(P), bool)
    w = free.astype(float)[:, None]
    for it in range(3):
        # 1-D Taubin smoothing along the rim loops, then back onto the cutting surfaces
        for _ in range(6):
            for lp in loops:
                if len(lp) < 6:
                    continue
                X = Q[lp]
                L = 0.5 * (np.roll(X, 1, axis=0) + np.roll(X, -1, axis=0)) - X
                X = X + 0.5 * L
                L = 0.5 * (np.roll(X, 1, axis=0) + np.roll(X, -1, axis=0)) - X
                X = X - 0.53 * L
                Q[lp] = X
            for fn in snaps:
                fn(Q, bmask)
        for _ in range(smooth_iters // 3):
            Q = Q + 0.5 * w * lap(Q)
            Q = Q - 0.53 * w * lap(Q)
        g, nn = B.signed_gap(Q)
        push = np.maximum(min_gap - g, 0.0) * free
        Q = Q + nn * push[:, None]
    # materials for outer faces
    cent = np.array([Q[list(f)].mean(0) for f in faces])
    mi = mat_fn(cent) if mat_fn is not None else np.zeros(len(faces), int)
    obj = make_mesh_obj(name, [tuple(q) for q in Q], faces, None, coll)
    for mt in mats:
        obj.data.materials.append(mt)
    for f, k in zip(obj.data.polygons, mi):
        f.material_index = int(k)
    if solid:
        mod = obj.modifiers.new('Solid', 'SOLIDIFY')
        mod.thickness = thickness
        mod.offset = -1.0
        mod.use_even_offset = False
        mod.use_rim = True
        mod.material_offset = 0
        mod.material_offset_rim = 0
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me2 = bpy.data.meshes.new_from_object(ev)
        old = obj.data
        obj.modifiers.remove(mod)
        obj.data = me2
        bpy.data.meshes.remove(old)
        for f in obj.data.polygons:
            f.use_smooth = True
    return obj, dict(P0=P0, Q=Q, bmask=bmask, used=used, faces=faces, N=N)


def plane_snap(selector, plane_point, plane_normal, move_dir):
    pp, pn, md = (np.asarray(x, float) for x in (plane_point, plane_normal, move_dir))

    def fn(P, bmask):
        s = selector(P) & bmask
        t = ((pp - P[s]) @ pn) / (md @ pn)
        P[s] = P[s] + np.outer(t, md)
    return fn


def func_snap(selector, height_fn):
    """move selected boundary verts vertically to z = height_fn(P)."""
    def fn(P, bmask):
        s = selector(P) & bmask
        P[s, 2] = height_fn(P[s])
    return fn


def loop_tube(coll, name, pts, radius, mat, n=10, closed=True):
    """tube along a closed polyline."""
    pts = [Vector(p) for p in pts]
    M = len(pts)
    verts = []
    rings = []
    for i, p in enumerate(pts):
        a = pts[(i + 1) % M] - pts[(i - 1) % M]
        a.normalize()
        up = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
        side = a.cross(up).normalized()
        out = side.cross(a).normalized()
        r = radius[i] if hasattr(radius, '__len__') else radius
        ring = []
        for j in range(n):
            t = math.tau * j / n
            ring.append(len(verts))
            verts.append(tuple(p + side * (r * math.cos(t)) + out * (r * math.sin(t))))
        rings.append(ring)
    faces = []
    last = M if closed else M - 1
    for i in range(last):
        a, b = rings[i], rings[(i + 1) % M]
        for j in range(n):
            faces.append((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
    return make_mesh_obj(name, verts, faces, mat, coll)


def boundary_loops(info, which=lambda P: np.ones(len(P), bool)):
    """ordered boundary loops (list of index lists into info['Q']) of a shell, optionally filtered."""
    faces = info['faces']
    ec = {}
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e = (min(a, b), max(a, b))
            ec.setdefault(e, []).append((a, b))
    adj = {}
    for e, lst in ec.items():
        if len(lst) == 1:
            a, b = lst[0]
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    seen = set()
    loops = []
    for s in adj:
        if s in seen:
            continue
        loop = [s]
        seen.add(s)
        prev = None
        cur = s
        while True:
            nx = [v for v in adj[cur] if v != prev]
            if prev is None:
                nx = [adj[cur][0]]
            if not nx or nx[0] == s:
                break
            prev, cur = cur, nx[0]
            if cur in seen:
                break
            loop.append(cur)
            seen.add(cur)
        loops.append(loop)
    return loops
