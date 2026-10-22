"""Separate face parts (eyeballs, brows) built from plate measurements; cut eye openings in the proxy.  Runs inside Blender.
These are NOT volume engines: skin forms (sockets, lids, brow ridge) live in the head surface; these are the eyeball spheres that sit in
the sockets and the dark brow-hair ribbons lying on the brow ridge."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import h1lib as H
import sculpt as S
from h1lib import K, zrow, ycol, xcol

mm = 0.001


# ------------------------------------------------------------------------------------------------ eye openings in the skin
def cut_eye_openings(P, F, margin=0.0):
    """drop quads whose centre lies inside the almond opening (either eye). returns new face list"""
    poly = S.smooth_poly(S.eye_poly())
    Fq = np.asarray(F)
    c = P[Fq].mean(axis=1)
    d = S.poly_dist(np.abs(c[:, 0]), c[:, 2], poly)
    keep = d > margin
    return Fq[keep]


# ------------------------------------------------------------------------------------------------ materials
def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def eye_material(side, name):
    """procedural eye: pupil / iris / limbal ring / sclera / catchlight from object-space position (world coords, mesh has no transform)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
    nt.links.new(sep.outputs['X'], ab.inputs[0])
    cx = H.LM['eye_x']; cz = H.LM['eye_z']
    dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'; dx.inputs[1].default_value = cx
    nt.links.new(ab.outputs[0], dx.inputs[0])
    dz = nt.nodes.new('ShaderNodeMath'); dz.operation = 'SUBTRACT'; dz.inputs[1].default_value = cz
    nt.links.new(sep.outputs['Z'], dz.inputs[0])
    # signed dx so the catchlight offset is the same screen direction for both eyes
    def sq(n):
        q = nt.nodes.new('ShaderNodeMath'); q.operation = 'POWER'; q.inputs[1].default_value = 2.0
        nt.links.new(n.outputs[0], q.inputs[0]); return q
    a2 = sq(dx); b2 = sq(dz)
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'
    nt.links.new(a2.outputs[0], ad.inputs[0]); nt.links.new(b2.outputs[0], ad.inputs[1])
    r = nt.nodes.new('ShaderNodeMath'); r.operation = 'SQRT'; nt.links.new(ad.outputs[0], r.inputs[0])
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'DIVIDE'; fac.inputs[1].default_value = 0.010
    nt.links.new(r.outputs[0], fac.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp; cr.interpolation = 'LINEAR'
    stops = [(0.0, (0.01, 0.006, 0.004)), (0.40, (0.01, 0.006, 0.004)), (0.42, (0.36, 0.20, 0.09)), (0.62, (0.28, 0.145, 0.06)),
             (0.72, (0.15, 0.075, 0.035)), (0.755, (0.07, 0.035, 0.02)), (0.775, (0.95, 0.93, 0.89)), (1.0, (0.95, 0.93, 0.89))]
    while len(cr.elements) < len(stops): cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, stops):
        el.position = pos; el.color = (_lin(col[0]), _lin(col[1]), _lin(col[2]), 1.0)
    nt.links.new(fac.outputs[0], ramp.inputs['Fac'])
    # catchlight: small white disc, same screen offset on both eyes (+1.3 mm right, +3.7 mm up) relative to the iris centre
    sx = -1.0 if side < 0 else 1.0
    sgn = nt.nodes.new('ShaderNodeMath'); sgn.operation = 'MULTIPLY'; sgn.inputs[1].default_value = 1.0
    x_signed = nt.nodes.new('ShaderNodeMath'); x_signed.operation = 'SUBTRACT'; x_signed.inputs[1].default_value = sx * cx
    nt.links.new(sep.outputs['X'], x_signed.inputs[0])
    cl_dx = nt.nodes.new('ShaderNodeMath'); cl_dx.operation = 'SUBTRACT'; cl_dx.inputs[1].default_value = 0.0013
    nt.links.new(x_signed.outputs[0], cl_dx.inputs[0])
    cl_dz = nt.nodes.new('ShaderNodeMath'); cl_dz.operation = 'SUBTRACT'; cl_dz.inputs[1].default_value = cz + 0.0037
    nt.links.new(sep.outputs['Z'], cl_dz.inputs[0])
    c2 = sq(cl_dx); d2 = sq(cl_dz)
    cad = nt.nodes.new('ShaderNodeMath'); cad.operation = 'ADD'
    nt.links.new(c2.outputs[0], cad.inputs[0]); nt.links.new(d2.outputs[0], cad.inputs[1])
    cr_ = nt.nodes.new('ShaderNodeMath'); cr_.operation = 'SQRT'; nt.links.new(cad.outputs[0], cr_.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.0014
    nt.links.new(cr_.outputs[0], lt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(lt.outputs[0], mix.inputs['Factor'])
    nt.links.new(ramp.outputs['Color'], mix.inputs[6]); mix.inputs[7].default_value = (1, 1, 1, 1)
    nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.18
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.8
    except Exception:
        pass
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


# ------------------------------------------------------------------------------------------------ eyeball
def make_eyeball(side, nu=64, nv=40):
    e = S.EYEBALL
    cz = H.LM['eye_z']
    th = np.linspace(0, math.pi, nv + 1)           # polar from front (-y) axis
    ph = np.linspace(0, 2 * math.pi, nu, endpoint=False)
    V = []; Fc = []
    for i, t in enumerate(th):
        for j, p in enumerate(ph):
            ux = math.sin(t) * math.cos(p); uz = math.sin(t) * math.sin(p); uy = -math.cos(t)    # t=0 -> front (-y)
            V.append((side * e['cx'] + e['ax'] * ux, e['cy'] + e['ay'] * uy, cz + e['az'] * uz))
    for i in range(nv):
        for j in range(nu):
            a = i * nu + j; b = i * nu + (j + 1) % nu; c = (i + 1) * nu + (j + 1) % nu; d = (i + 1) * nu + j
            Fc.append((a, b, c, d))
    V = np.array(V); Fc = [f for f in Fc]
    # collapse the poles' degenerate quads is not needed for a preview
    o = H.make_mesh_object(f'Eye_{"R" if side > 0 else "L"}', V, Fc)
    o.data.materials.append(eye_material(side, f'eye_mat_{side}'))
    return o


# ------------------------------------------------------------------------------------------------ brows
BROW_CL = [(214.0, 148.3), (206.0, 148.0), (198.0, 148.0), (190.0, 148.3), (184.0, 149.8), (180.0, 152.6), (177.0, 156.0), (175.6, 158.0)]
BROW_TH = [8.8, 9.0, 9.2, 8.8, 7.0, 5.0, 2.6, 0.8]            # rows (px) of thickness ~ plate px


def make_brow(side, bvh, nu=34, nv=7, lift_h=1.9, srgb=(0.165, 0.118, 0.082)):
    """ribbon with a rounded cross-section lying on the sculpted skin (ray cast along +y), side=-1: viewer-left brow"""
    cl = np.array(BROW_CL); th = np.array(BROW_TH)
    t = np.linspace(0, 1, 200)
    seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(cl, axis=0).T))]); seg /= seg[-1]
    colc = np.interp(np.linspace(0, 1, nu), seg, cl[:, 0]); rowc = np.interp(np.linspace(0, 1, nu), seg, cl[:, 1])
    thc = np.interp(np.linspace(0, 1, nu), seg, th)
    # tangent in plate px -> normal
    dcol = np.gradient(colc); drow = np.gradient(rowc)
    L = np.hypot(dcol, drow); nc = -drow / L; nr = dcol / L          # normal (col,row)
    V = []; Fc = []
    for i in range(nu):
        for k in range(nv):
            v = (k / (nv - 1)) * 2 - 1
            c = colc[i] + nc[i] * v * thc[i] / 2; r = rowc[i] + nr[i] * v * thc[i] / 2
            x = float(xcol(c)); z = float(zrow(r))
            if side > 0: x = -x
            hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 3.0)
            if hit[0] is None:
                raise RuntimeError('brow ray missed')
            p, n = hit[0], hit[1]
            hh = (lift_h * mm) * max(0.0, 1 - abs(v) ** 2.4) * (0.35 + 0.65 * min(1.0, thc[i] / 6.0)) + 0.25 * mm
            V.append((p.x + n.x * hh, p.y + n.y * hh, p.z + n.z * hh))
    for i in range(nu - 1):
        for k in range(nv - 1):
            a = i * nv + k; b = (i + 1) * nv + k; c = (i + 1) * nv + k + 1; d = i * nv + k + 1
            Fc.append((a, b, c, d))
    o = H.make_mesh_object(f'Brow_{"R" if side > 0 else "L"}', np.array(V), Fc)
    mat = H.flat_material('brow_mat', srgb, 0.6)
    o.data.materials.append(mat)
    return o


def bvh_of(P, F):
    verts = [tuple(v) for v in P]
    tris = []
    for f in F:
        tris.append((int(f[0]), int(f[1]), int(f[2]))); tris.append((int(f[0]), int(f[2]), int(f[3])))
    return BVHTree.FromPolygons(verts, tris)


# ======================================================================================================================
# Face_M assembly: thin paint-like parts (numpy mesh pieces -> one object with named slots)
# ======================================================================================================================
SLOTS = ['Brow', 'Sclera', 'Iris', 'Pupil', 'Limbal', 'Catch', 'LidLine', 'Lip', 'LipUp', 'Seam', 'Nostril']
SLOT_COL = {'Brow': ((0.165, 0.118, 0.082), 0.60), 'Sclera': ((0.93, 0.91, 0.86), 0.30), 'Iris': ((0.353, 0.204, 0.094), 0.28),
            'Pupil': ((0.04, 0.025, 0.015), 0.20), 'Limbal': ((0.12, 0.065, 0.035), 0.28), 'Catch': ((1.0, 1.0, 1.0), 0.10),
            'LidLine': ((0.20, 0.12, 0.08), 0.55), 'Lip': ((0.82, 0.54, 0.46), 0.45), 'LipUp': ((0.66, 0.40, 0.33), 0.50), 'Seam': ((0.42, 0.23, 0.165), 0.60), 'Nostril': ((0.30, 0.16, 0.11), 0.65)}


def _face_normals(V, F):
    V = np.asarray(V, float)
    out = np.zeros((len(F), 3)); cen = np.zeros((len(F), 3))
    for i, f in enumerate(F):
        p = V[list(f)]
        if len(f) == 4:
            n = np.cross(p[2] - p[0], p[3] - p[1])
        else:
            n = np.cross(p[1] - p[0], p[2] - p[0])
        out[i] = n / (np.linalg.norm(n) + 1e-18); cen[i] = p.mean(axis=0)
    return out, cen


def orient_faces(V, F, mode):
    """flip faces so normals point outward: mode 'front' -> n_y < 0 ; ('radial', centre) -> n.(c - centre) > 0"""
    n, c = _face_normals(V, F)
    G = []
    for i, f in enumerate(F):
        if mode == 'front':
            ok = n[i, 1] < 0
        elif mode is None:
            ok = True
        else:
            ctr = np.asarray(mode[1], float)
            ok = np.dot(n[i], c[i] - ctr) > 0
        G.append(list(f) if ok else list(f)[::-1])
    return G


class Parts:
    def __init__(self):
        self.V = []; self.F = []; self.S = []

    def add(self, V, F, slot, orient=None):
        F = orient_faces(V, F, orient) if orient is not None else F
        base = len(self.V)
        self.V.extend([tuple(v) for v in V])
        self.F.extend([[base + int(i) for i in f] for f in F])
        self.S.extend([SLOTS.index(slot[k]) for k in range(len(F))] if not isinstance(slot, str) else [SLOTS.index(slot)] * len(F))

    def object(self, name='Face_M'):
        o = H.make_mesh_object(name, np.array(self.V), self.F)
        for sl in SLOTS:
            col, rough = SLOT_COL[sl]
            m = H.flat_material('Face_' + sl, col, rough)
            o.data.materials.append(m)
        for p_, k in zip(o.data.polygons, self.S):
            p_.material_index = k
        return o


def grid_strip(bvh, pts_xz, nu, nv, lift, flip=False):
    """pts_xz: (nu,nv,2) array of (x,z); ray-cast each along +y onto the skin, lift along the hit normal. returns V, F (quads)"""
    V = []
    for i in range(nu):
        for k in range(nv):
            x, z = pts_xz[i, k]
            hit = bvh.ray_cast(Vector((float(x), -1.0, float(z))), Vector((0, 1, 0)), 3.0)
            if hit[0] is None:
                p = Vector((float(x), -0.15, float(z))); n = Vector((0, -1, 0))
            else:
                p, n = hit[0], hit[1]
            l = lift(i, k) if callable(lift) else lift
            V.append((p.x + n.x * l, p.y + n.y * l, p.z + n.z * l))
    F = []
    for i in range(nu - 1):
        for k in range(nv - 1):
            a = i * nv + k; b = (i + 1) * nv + k; c = (i + 1) * nv + k + 1; d = i * nv + k + 1
            F.append([a, d, c, b] if flip else [a, b, c, d])
    return V, F


def lid_line_strip(bvh, side, nu=40, width=1.7 * mm, lift=0.25 * mm):
    """dark upper lash line: strip lying on the skin just outside the upper half of the lid margin"""
    poly = S.smooth_poly(S.eye_poly(), n=160)
    # upper half: from the outer corner (max x) over the top to the inner corner (min x): polygon order is outer->inner along the upper margin
    m = len(poly)
    # find outer corner (max x) and inner corner (min x)
    io = int(np.argmax(poly[:, 0])); ii = int(np.argmin(poly[:, 0]))
    # walk from outer corner forward until inner corner (upper margin comes first in EYE_UP+EYE_LO order)
    idx = [(io + k) % m for k in range(m)]
    seq = []
    for j in idx:
        seq.append(j)
        if j == ii: break
    up = poly[seq]
    # smooth, resample
    seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(up, axis=0).T))]); t = np.linspace(0, seg[-1], nu)
    xs = np.interp(t, seg, up[:, 0]); zs = np.interp(t, seg, up[:, 1])
    dx = np.gradient(xs); dz = np.gradient(zs); L = np.hypot(dx, dz)
    nx, nz = dz / L, -dx / L                     # one of the normals
    # choose the normal pointing up (+z) for the upper margin
    if np.mean(nz) < 0: nx, nz = -nx, -nz
    pts = np.zeros((nu, 3, 2))
    taper = np.sin(np.linspace(0, math.pi, nu)) ** 0.5
    for k, off in enumerate([-0.15 * mm, 0.7 * mm, 1.7 * mm]):
        w = off / (1.7 * mm) * width
        pts[:, k, 0] = (xs + nx * off * (0.25 + 0.75 * taper)) * side
        pts[:, k, 1] = zs + nz * off * (0.25 + 0.75 * taper)
    return grid_strip(bvh, pts, nu, 3, lift, flip=(side < 0))


def lip_patch(bvh, which, nu=40, nv=4, lift=0.28 * mm):
    """vermilion tint: strip between the seam curve and the lip border (upper: above, lower: below)"""
    xs = np.linspace(-1, 1, nu)
    if which == 'up':
        W, Hh, p_ = 36.0 * mm, 6.2 * mm, 2.4
    else:
        W, Hh, p_ = 32.5 * mm, 9.4 * mm, 2.2
    pts = np.zeros((nu, nv, 2))
    for i, u in enumerate(xs):
        x = u * W
        z0 = float(S.seam_z(np.array([abs(x)]))[0])
        h = Hh * max(0.0, 1.0 - abs(u) ** p_) ** (1.0 / p_)
        for k in range(nv):
            v = k / (nv - 1)
            sgn = 1.0 if which == 'up' else -1.0
            pts[i, k] = (x, z0 + sgn * v * h * 1.0)
    return grid_strip(bvh, pts, nu, nv, lift, flip=(which != 'up'))


def seam_ribbon(bvh, nu=48, width=1.1 * mm, lift=0.34 * mm):
    xs = np.linspace(-38.0 * mm, 38.0 * mm, nu)
    pts = np.zeros((nu, 3, 2))
    for i, x in enumerate(xs):
        z0 = float(S.seam_z(np.array([abs(x)]))[0])
        wv = width * math.sqrt(max(0.0, 1.0 - (abs(x) / (38.0 * mm)) ** 2.5))
        for k, o in enumerate((-0.5, 0.0, 0.5)):
            pts[i, k] = (x, z0 + o * wv)
    return grid_strip(bvh, pts, nu, 3, lift)


def nostril_liner(bvh, side, nu=14, lift=0.10 * mm):
    """dark lens-shaped opening inside each nostril pit (thin paint; the pit itself is geometry)"""
    n = S.PRM['nostril']
    cx = side * n['cx'] * mm; cz = float(zrow(n['row']))
    rx, rz = 4.2 * mm, 1.5 * mm
    pts = np.zeros((nu, 3, 2))
    for i, u in enumerate(np.linspace(-1, 1, nu)):
        h = rz * max(0.0, 1.0 - abs(u) ** 2.0) ** 0.8
        x = cx + u * rx
        for k, v in enumerate((-1.0, 0.0, 1.0)):
            pts[i, k] = (x, cz + v * h + 0.2 * mm * (u))
    return grid_strip(bvh, pts, nu, 3, lift)


def build_face_m(P_skin, F_skin, with_eyes=True, name='Face_M'):
    """returns the Face_M object (in the current scene). skin mesh is used for ray casts"""
    import finalize as FZ
    bvh = bvh_of(P_skin, [f for f in F_skin if len(f) == 4] + [])
    # triangles too
    verts = [tuple(v) for v in P_skin]
    tris = []
    for f in F_skin:
        tris.append((int(f[0]), int(f[1]), int(f[2])))
        if len(f) > 3:
            tris.append((int(f[0]), int(f[2]), int(f[3])))
    bvh = BVHTree.FromPolygons(verts, tris)
    parts = Parts()
    if with_eyes:
        cmap = {0: 'Sclera', 1: 'Iris', 2: 'Pupil', 3: 'Limbal', 4: 'Catch'}
        for side in (-1, 1):
            V, F, mat = FZ.eyeball_mesh(side)
            parts.add(V, F, [cmap[m] for m in mat], orient=('radial', [side * S.EYEBALL['cx'], S.EYEBALL['cy'], H.LM['eye_z']]))
    for side in (-1, +1):
        # brows (ribbon on the skin)
        try:
            ob = make_brow(side, bvh)
            Vb = np.array([v.co[:] for v in ob.data.vertices]); Fb = [[v for v in p.vertices] for p in ob.data.polygons]
            bpy.data.objects.remove(ob, do_unlink=True)
            parts.add(Vb, Fb, 'Brow', orient='front')
        except RuntimeError:
            pass
        V, F = lid_line_strip(bvh, side)
        parts.add(V, F, 'LidLine', orient='front')
    for which in ('up', 'lo'):
        V, F = lip_patch(bvh, which)
        parts.add(V, F, 'LipUp' if which == 'up' else 'Lip', orient='front')
    V, F = seam_ribbon(bvh)
    parts.add(V, F, 'Seam', orient='front')
    for side in (-1, +1):
        V, F = nostril_liner(bvh, side)
        parts.add(V, F, 'Nostril', orient=('radial', [side * 0.0145, -0.06, 1.5368]))
    return parts.object(name), parts
