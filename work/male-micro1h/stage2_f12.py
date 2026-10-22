"""Stage 2: final head mesh = error-driven graded subdivision of the cage head region (weld ring untouched), vertices placed by the
analytic head function Phi (loft remap + sculpt).  Runs inside Blender (bmesh)."""
import pickle, time
import numpy as np
import bmesh
import h1lib as H
import loft as L
import sculpt as S
import proxy as PX
import topo as T

ZFIX = 1.462            # below this nothing moves (chin lock band & neck keep their exact cage geometry)


class Phi:
    """position function: flat cage-surface points -> final surface points (stage 1: remap + forward/vector fields)"""

    def __init__(self, prm=None, parts=('nose', 'orbit', 'brow', 'cheek', 'eye', 'mouth', 'ear'), loft=None):
        self.prm = prm or {}
        self.parts = parts
        self.loft = loft or L.Loft()
        self.cc = None

    def attach_cc(self, Vcc, Fcc):
        """smooth base (Catmull-Clark limit of the cage) for projecting flat cage points in the blend zone"""
        import bpy
        from mathutils.bvhtree import BVHTree
        tris = []
        for f in Fcc:
            tris.append((int(f[0]), int(f[1]), int(f[2])))
            if len(f) > 3:
                tris.append((int(f[0]), int(f[2]), int(f[3])))
        self.cc = BVHTree.FromPolygons([tuple(v) for v in Vcc], tris)

    def project_cc(self, P, zmax=1.50):
        out = P.copy()
        idx = np.where((P[:, 2] > ZFIX - 0.004) & (P[:, 2] < zmax))[0]
        for i in idx:
            hit = self.cc.find_nearest(tuple(P[i]))
            if hit[0] is not None:
                w = S.sstep(ZFIX - 0.004, ZFIX + 0.004, P[i, 2])
                out[i] = np.array(P[i]) * (1 - w) + np.array(hit[0]) * w
        return out

    def stage1(self, P):
        P = np.asarray(P, float)
        Pc = P            # no CC projection: it rounds the sharp under-chin crease (Micro1e chin lock); flat cage faces ARE the original surface
        P0, _, _ = L.remap(Pc, self.loft)
        N0 = np.zeros_like(P0)
        P1, info = S.apply(P0, N0, self.prm, self.parts, F=None)
        keep = P[:, 2] < ZFIX
        P1[keep] = P[keep]
        return P1


def region_bm(V, F, fidx):
    used = sorted({int(v) for i in fidx for v in F[i]})
    rem = {v: k for k, v in enumerate(used)}
    bm = bmesh.new()
    verts = [bm.verts.new(tuple(V[v])) for v in used]
    bm.verts.ensure_lookup_table()
    for i in fidx:
        bm.faces.new([verts[rem[int(v)]] for v in F[i]])
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.material_index = 0
    return bm, used


_EAR_POLY = None


def ear_footprint(c, margin=0.004):
    global _EAR_POLY
    if _EAR_POLY is None:
        _EAR_POLY = S.ear_poly()
    ax = np.abs(c[:, 0])
    d = S.poly_dist(c[:, 1], c[:, 2], _EAR_POLY)
    return (ax > 0.060) & (ax < 0.125) & (d < margin)


def feature_curves():
    """list of polylines in (|x|, z) with the half-width within which faces must reach the given level: [(pts, w1, w2)]"""
    poly = S.smooth_poly(S.eye_poly())
    curves = [(poly, 'closed')]
    # nostril ellipses
    n = S.PRM['nostril']
    t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    ell = np.stack([n['cx'] * S.mm + n['rx'] * S.mm * np.cos(t), float(H.zrow(n['row'])) + n['rz'] * S.mm * np.sin(t)], axis=1)
    curves.append((ell, 'closed'))
    # mouth seam
    xs = np.linspace(0, 40 * S.mm, 20)
    curves.append((np.stack([xs, S.seam_z(xs)], axis=1), 'open'))
    return curves


def dist_to_curves(x, z, curves):
    d = np.full(x.shape, np.inf)
    for pts, kind in curves:
        n = len(pts)
        rng = range(n) if kind == 'closed' else range(n - 1)
        for i in rng:
            j = (i + 1) % n
            ax, az = pts[i]; bx, bz = pts[j]
            ex, ez = bx - ax, bz - az
            t = np.clip(((x - ax) * ex + (z - az) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
            d = np.minimum(d, np.hypot(x - (ax + t * ex), z - (az + t * ez)))
    return d


def build_final(V, F, phi, eps=0.00045, eps_far=0.0012, err_max_level=2, max_level=3, min_face_level=1, feat_dist=(0.0045, 0.0022), verbose=True, zring=T.ZRING, join_tris=True):
    """returns (Vflat, Fn, info). Vflat are the flat (pre-Phi) positions of the final topology; apply phi.stage1 to place them."""
    fidx = T.region_faces(V, F, zring)
    bm, used = region_bm(V, F, fidx)
    curves = feature_curves()
    ring_pos = {tuple(np.round(np.array(v.co[:]), 9)) for e in bm.edges if e.is_boundary for v in e.verts}
    for it in range(1, max_level + 1):
        bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
        faces = list(bm.faces)
        quad = np.array([len(f.verts) == 4 for f in faces])
        depth = np.array([f.material_index for f in faces])
        # arrays of corner positions
        corners = np.array([[v.co[:] for v in f.verts] if len(f.verts) == 4 else [v.co[:] for v in f.verts][:3] + [f.verts[2].co[:]] for f in faces])
        cen = corners.mean(axis=1)
        # error: Phi(centre) vs mean of Phi(corners); and edge midpoints
        Pc = phi.stage1(corners.reshape(-1, 3)).reshape(len(faces), 4, 3)
        P_cen = phi.stage1(cen)
        err = np.linalg.norm(P_cen - Pc.mean(axis=1), axis=1)
        mids = 0.5 * (corners + np.roll(corners, -1, axis=1))
        Pm = phi.stage1(mids.reshape(-1, 3)).reshape(len(faces), 4, 3)
        Pe = 0.5 * (Pc + np.roll(Pc, -1, axis=1))
        err = np.maximum(err, np.linalg.norm(Pm - Pe, axis=2).max(axis=1))
        want = depth >= 0
        face_zone0 = (cen[:, 1] < -0.020) & (np.abs(cen[:, 0]) < 0.088) & (cen[:, 2] > 1.470) & (cen[:, 2] < 1.628)
        ear0 = ear_footprint(cen, 0.007)
        tol = np.where(face_zone0 | ear0, eps, eps_far)
        need = (err > tol) & (it <= err_max_level) & (cen[:, 2] > 1.470)
        # minimum levels: face broad & feature proximity
        c = cen
        face_zone = (c[:, 1] < -0.020) & (np.abs(c[:, 0]) < 0.088) & (c[:, 2] > 1.470) & (c[:, 2] < 1.628)
        near1 = dist_to_curves(np.abs(c[:, 0]), c[:, 2], curves) < feat_dist[0]
        near2 = dist_to_curves(np.abs(c[:, 0]), c[:, 2], curves) < feat_dist[1]
        ear = ear_footprint(c, 0.007)
        mlev = np.zeros(len(faces), int)
        mlev[face_zone] = min_face_level
        nose_zone = (np.abs(c[:, 0]) < 0.030) & (c[:, 2] > 1.524) & (c[:, 2] < 1.604) & (c[:, 1] < -0.06)
        mlev[near1 | ear | nose_zone] = np.maximum(mlev[near1 | ear | nose_zone], 2)
        mlev[near2] = np.maximum(mlev[near2], 3 if max_level >= 3 else 2)
        mlev[cen[:, 2] < 1.470] = 0
        sel = quad & ((depth < it) & ((need & (depth == it - 1)) | (mlev >= it)))
        sel = sel & (depth == it - 1)
        # balance: neighbours (sharing an edge) of selected faces must be at least it-1 ; if lower -> refine them too (one level)
        selset = {faces[i] for i in np.where(sel)[0]}
        extra = set()
        for f in selset:
            for e in f.edges:
                for g in e.link_faces:
                    if g is not f and g not in selset and g.material_index < it - 1 and len(g.verts) == 4:
                        extra.add(g)
        edges = set()
        for f in selset | extra:
            for e in f.edges:
                if not e.is_boundary:
                    edges.add(e)
        if not edges:
            continue
        for f in selset:
            f.material_index = it
        for g in extra:
            g.material_index = g.material_index + 1
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True)
        if verbose:
            print(f'pass {it}: need {int((quad & need).sum())} min-level {int((quad & (mlev >= it)).sum())} -> subdivided {len(selset)}+{len(extra)} faces; faces now {len(bm.faces)}')
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='BEAUTY')
    if join_tris:
        tr = [f for f in bm.faces if len(f.verts) == 3]
        bmesh.ops.join_triangles(bm, faces=tr, cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False, cmp_materials=False,
                                 angle_face_threshold=0.9, angle_shape_threshold=0.9)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    Vn = np.array([v.co[:] for v in bm.verts], float)
    Fn = [[v.index for v in f.verts] for f in bm.faces]
    bnd = {tuple(np.round(Vn[v.index], 9)) for e in bm.edges if e.is_boundary for v in e.verts}
    depth = [f.material_index for f in bm.faces]
    info = dict(n_verts=len(Vn), n_faces=len(Fn), tris=int(sum(len(f) - 2 for f in Fn)), n_tri_faces=int(sum(1 for f in Fn if len(f) == 3)),
                n_quad_faces=int(sum(1 for f in Fn if len(f) == 4)), boundary_ring_unchanged=bnd == ring_pos, used=used, depth=depth)
    bm.free()
    return Vn, Fn, info


def assemble(V_full, F_full, fidx, used, Vn, Fn, P_final):
    """new full mesh keeping every original vertex index.  Region faces are replaced by the refined patch; ring vertices keep their
    exact original coordinates; original interior-region vertices get their new positions; new vertices are appended.
    P_final may have more rows than Vn (extra vertices appended by finalize steps)."""
    n_orig = len(V_full)
    region = set(fidx)
    ring = set()
    for i, f in enumerate(F_full):
        if i not in region:
            for v in f:
                ring.add(int(v))
    used_arr = np.array(used)
    nu = len(used)
    n_new = len(P_final)
    new_idx = {}
    for k in range(n_new):
        new_idx[k] = int(used_arr[k]) if k < nu else n_orig + (k - nu)
    V_all = np.concatenate([V_full, P_final[nu:]]) if n_new > nu else V_full.copy()
    for k in range(nu):
        gi = int(used_arr[k])
        if gi not in ring:
            V_all[gi] = P_final[k]
    F_out = [f for i, f in enumerate(F_full) if i not in region]
    F_out += [[new_idx[int(v)] for v in f] for f in Fn]
    return V_all, F_out, ring
