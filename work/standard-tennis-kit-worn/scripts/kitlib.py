"""Core numeric/geometry helpers for the standard tennis kit build (run inside Blender's python: bpy + numpy).

Everything here works on plain numpy arrays (V: (n,3) float, F: (m,3) int tris) so garments can be built, fitted and checked
without touching the authority body meshes.
"""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = ROOT + '/work/standard-tennis-kit-worn'
OLD_WORK = ROOT + '/work/standard-tennis-kit-wb'      # previous (tucked) kit: read-only reference
MALE_BLEND = ROOT + '/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend'
FEMALE_BLEND = ROOT + '/ArtDir/hero/base_lock/blender/HeroBase_Female.blend'
MALE_SHA = 'fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347'
FEMALE_SHA = '200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd'


# ------------------------------------------------------------------------------------------------ mesh <-> numpy
def mesh_arrays(obj, world=True):
    """(V, F) numpy arrays of an object's mesh, triangulated, optionally in world space."""
    me = obj.data
    me.calc_loop_triangles()
    V = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get('co', V)
    V = V.reshape(-1, 3)
    T = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get('vertices', T)
    F = T.reshape(-1, 3)
    if world:
        M = np.array(obj.matrix_world)
        V = V @ M[:3, :3].T + M[:3, 3]
    return V, F


def load_body(blend, name):
    bpy.ops.wm.open_mainfile(filepath=blend)
    return bpy.data.objects[name]


def bvh_from(V, F):
    return BVHTree.FromPolygons([tuple(v) for v in V.tolist()], [tuple(f) for f in F.tolist()], epsilon=0.0)


def vertex_normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn)
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return vn / ln


def face_normals(V, F, unit=True):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    if unit:
        ln = np.linalg.norm(fn, axis=1, keepdims=True)
        ln[ln == 0] = 1
        fn = fn / ln
    return fn


# ------------------------------------------------------------------------------------------------ slicing
def slice_plane(V, F, axis, value):
    """Intersect the mesh with the plane V[:,axis] == value.  Returns list of closed/open polylines (arrays (k,3))."""
    d = V[:, axis] - value
    s = d[F]                                  # (m,3)
    pos = s >= 0
    cnt = pos.sum(1)
    sel = np.nonzero((cnt == 1) | (cnt == 2))[0]
    if len(sel) == 0:
        return []
    segs = []   # (key_a, pt_a, key_b, pt_b)
    for ti in sel:
        tri = F[ti]
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ia, ib = tri[a], tri[b]
            if (d[ia] >= 0) != (d[ib] >= 0):
                t = d[ia] / (d[ia] - d[ib])
                p = V[ia] + t * (V[ib] - V[ia])
                key = (ia, ib) if ia < ib else (ib, ia)
                pts.append((key, p))
        if len(pts) == 2:
            segs.append((pts[0][0], pts[0][1], pts[1][0], pts[1][1]))
    # chain
    adj = {}
    pt = {}
    for ka, pa, kb, pb in segs:
        adj.setdefault(ka, []).append(kb)
        adj.setdefault(kb, []).append(ka)
        pt[ka] = pa
        pt[kb] = pb
    seen = set()
    loops = []
    for k0 in adj:
        if k0 in seen:
            continue
        # walk both directions from k0
        chain = [k0]
        seen.add(k0)
        cur = k0
        prev = None
        while True:
            nxt = [k for k in adj[cur] if k != prev and k not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            chain.append(cur)
            seen.add(cur)
        # extend the other way
        cur = k0
        prev = None
        front = []
        nb = [k for k in adj[k0] if k not in chain]
        while nb:
            prev, cur = cur, nb[0]
            front.append(cur)
            seen.add(cur)
            nb = [k for k in adj[cur] if k != prev and k not in seen]
        chain = front[::-1] + chain
        loops.append(np.array([pt[k] for k in chain]))
    return loops


def poly_area_xy(P, a=0, b=1):
    x, y = P[:, a], P[:, b]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def loop_info(P, a=0, b=1):
    return dict(n=len(P), min=P.min(0).round(4).tolist(), max=P.max(0).round(4).tolist(),
                area=round(abs(poly_area_xy(P, a, b)), 5), c=P.mean(0).round(4).tolist())


# ------------------------------------------------------------------------------------------------ geometry
def smoothstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def make_object(name, V, F, collection=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(V, float).tolist(), [], np.asarray(F, int).tolist())
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    return o
