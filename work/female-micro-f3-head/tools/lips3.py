"""lips3 (Blender python): rebuild the lip paint of Face_F (materials Face_LipUp / Face_Lip / Face_Seam) from PLATE-MEASURED plan curves, ray-projected onto the final skin mesh,
with 'pillow' shading normals on the strips (the paint is what the viewer sees on the lips, so its normals carry the lip form).
Plan curves (front plane x, z) come from data/lip_plate_raw.json (tools/lip_measure.py): flat upper-lip top border, 6.8 mm upper / 12.8 mm lower vermilion at the centre, lower lip ending on the seam at |x| ~ 28 mm.

  import lips3;  S = lips3.build_strips(body_obj, P)         -> dict name -> dict(V, F, N, mat)
  lips3.replace_in_face(face_obj, S)                           -> removes the old lip strips from Face_F, appends the new ones (smooth, custom normals)
"""
import sys, json
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

K = 0.001537; ZTOP = 1.7039; ROW_TOP = 69.5
def zrow(r): return ZTOP - (r - ROW_TOP) * K
C_HEAD = np.array([0.0, -0.010, 1.575])

# ---------------------------------------------------------------------------------------------------------------- plan curves
P0 = dict(
    seam_zc=zrow(218.0), seam_zk=zrow(213.7), seam_hw=0.0355, seam_pow=1.6,       # F1's seam (mouth line): plate-fitted smile, unchanged
    top_c=1.4826, top_drop=0.0020, top_hw=0.0300, top_pow=4.0, up_end=0.0336,       # upper-lip top border: flat, falling toward the corners (plate rows 213-214)
    lo_t=0.0130, lo_hw=0.0252, lo_pow=2.5, lo_q=0.8,                                  # lower-lip thickness profile t_lo(x) = lo_t (1 - (|x|/lo_hw)^3)^0.8  (plate: 12.8 mm centre, 6.7 mm at 23 mm)
    bow_amp=0.00070, bow_x=0.0062, bow_w=0.0036, bow_dip=0.00040, dip_w=0.0030,
    seam_w0=0.00140, seam_w1=0.00035, seam_wpow=3.0,                                  # seam strip width: centre / corner
    lift=0.00055, lift_seam=0.00085,
    up_rows=6, lo_rows=8, n_up=85, n_lo=69, n_seam=89, nsig_x=0.0035, nsig_t=0.7,
    # pillow shading (degrees of pitch of the strip normal; + = up)
    lo_tilt=((0.0, 16.0), (0.45, 0.0), (1.0, -26.0)), up_tilt=((0.0, -18.0), (0.55, 0.0), (1.0, 9.0)),
)


def seam_z(x, p=P0):
    t = np.clip(np.abs(x) / p['seam_hw'], 0, 1)
    return p['seam_zc'] + (p['seam_zk'] - p['seam_zc']) * t ** p['seam_pow']


def smax(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.maximum(a, b) + h * h * k * 0.25


def top_z(x, p=P0):
    z = p['top_c'] - p['top_drop'] * (np.abs(x) / p['top_hw']) ** p['top_pow']
    ax = np.abs(x)
    z = z + p['bow_amp'] * np.exp(-((ax - p['bow_x']) / p['bow_w']) ** 2) - p['bow_dip'] * np.exp(-(x / p['dip_w']) ** 2)      # soft cupid's bow: peaks at +-6 mm, dip at the centre
    return smax(z, seam_z(x, p) + 0.0003, 0.0004)


def lo_thick(x, p=P0):
    u = np.clip(np.abs(x) / p['lo_hw'], 0, 1)
    return p['lo_t'] * (1 - u ** p['lo_pow']) ** p['lo_q']


# ---------------------------------------------------------------------------------------------------------------- skin projection
class Skin:
    def __init__(self, V, F, vnorm):
        """V (n,3) positions, F list of index lists (quads/tris), vnorm (n,3) per-vertex shading normals used for interpolation"""
        self.V = np.asarray(V, float); self.vn = np.asarray(vnorm, float)
        tris = []
        for f in F:
            for i in range(1, len(f) - 1): tris.append((int(f[0]), int(f[i]), int(f[i + 1])))
        self.T = np.array(tris, np.int64)
        self.bvh = BVHTree.FromPolygons([tuple(v) for v in self.V], [tuple(t) for t in self.T])

    def hit(self, x, z):
        """front ray at (x, z) from y = -0.30 along +y -> (point, interpolated unit normal facing -y) ; None when missing"""
        loc, nrm, idx, dist = self.bvh.ray_cast(Vector((float(x), -0.30, float(z))), Vector((0.0, 1.0, 0.0)))
        if loc is None: return None
        a, b, c = self.T[idx]; p = np.array(loc)
        A, B, Cc = self.V[a], self.V[b], self.V[c]
        v0, v1, v2 = B - A, Cc - A, p - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        wb = (d11 * d20 - d01 * d21) / den if abs(den) > 1e-30 else 1 / 3.0
        wc = (d00 * d21 - d01 * d20) / den if abs(den) > 1e-30 else 1 / 3.0
        wa = 1.0 - wb - wc
        n = wa * self.vn[a] + wb * self.vn[b] + wc * self.vn[c]
        nn = np.linalg.norm(n)
        n = np.array(nrm) if nn < 1e-9 else n / nn
        if n[1] > 0: n = -n
        return p, n


def pitch(n, deg):
    """rotate normal n about the x axis so that it tilts upward by deg (positive = toward +z)"""
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.stack([n[..., 0], n[..., 1] * c + n[..., 2] * s, -n[..., 1] * s + n[..., 2] * c], -1)


def ease_interp(t, table):
    ts = np.array([a for a, b in table]); vs = np.array([b for a, b in table])
    u = np.interp(t, ts, vs)
    return u


def ribbon_xz(xa, za, xb, zb, m):
    n = len(xa); X = np.zeros((m + 1, n)); Z = np.zeros((m + 1, n)); T = np.zeros((m + 1, n))
    for j in range(m + 1):
        t = j / m; X[j] = (1 - t) * xa + t * xb; Z[j] = (1 - t) * za + t * zb; T[j] = t
    return X, Z, T


def quads(m, n, flip=False):
    F = []
    for j in range(m):
        for i in range(n - 1):
            a = j * n + i; b = a + 1; c = (j + 1) * n + i + 1; d = (j + 1) * n + i
            F.append([a, b, c, d] if not flip else [d, c, b, a])
    return F


def build_strips(skin, p=P0):
    out = {}
    # --- upper lip: from the seam (t = 0) up to the top border (t = 1)
    xs = np.linspace(-p['up_end'], p['up_end'], p['n_up']); zs = seam_z(xs, p); zt = top_z(xs, p)
    X, Z, T = ribbon_xz(xs, zs, xs, zt, p['up_rows'])
    out['LipUp'] = strip(skin, X, Z, T, p['lift'], tilt=p['up_tilt'], env_hw=p['up_end'], mat='Face_LipUp', p=p)
    # --- lower lip: from the seam (t = 0) down to the bottom border (t = 1)
    xl = np.linspace(-p['lo_hw'], p['lo_hw'], p['n_lo']); zsl = seam_z(xl, p); zb = zsl - lo_thick(xl, p)
    X, Z, T = ribbon_xz(xl, zsl, xl, zb, p['lo_rows'])
    out['Lip'] = strip(skin, X, Z, T, p['lift'], tilt=p['lo_tilt'], env_hw=p['lo_hw'], mat='Face_Lip', p=p)
    # --- seam: thin dark strip centred on the mouth line, tapering to the corners
    xe = np.linspace(-p['seam_hw'], p['seam_hw'], p['n_seam']); zse = seam_z(xe, p)
    w = p['seam_w0'] * (1 - (np.abs(xe) / p['seam_hw']) ** p['seam_wpow']) + p['seam_w1']
    X, Z, T = ribbon_xz(xe, zse + 0.5 * w, xe, zse - 0.5 * w, 1)
    out['Seam'] = strip(skin, X, Z, T, p['lift_seam'], tilt=None, env_hw=p['seam_hw'], mat='Face_Seam', p=p)
    return out


def gsmooth(A, sig_samples, axis):
    """Gaussian smoothing of an (m, n, 3) array along an axis (edge-padded)"""
    if sig_samples <= 0.05: return A
    r = int(np.ceil(3 * sig_samples)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig_samples) ** 2); k /= k.sum()
    Ap = np.moveaxis(A, axis, 0)
    pad = np.concatenate([np.repeat(Ap[:1], r, 0), Ap, np.repeat(Ap[-1:], r, 0)], 0)
    out = np.zeros_like(Ap)
    for i, w in enumerate(k): out += w * pad[i:i + Ap.shape[0]]
    return np.moveaxis(out, 0, axis)


def strip(skin, X, Z, T, lift, tilt, env_hw, mat, p):
    m1, n = X.shape; V = np.zeros((m1, n, 3)); N = np.zeros((m1, n, 3)); miss = 0
    for j in range(m1):
        for i in range(n):
            h = skin.hit(X[j, i], Z[j, i])
            if h is None:
                miss += 1; V[j, i] = (X[j, i], -0.13, Z[j, i]); N[j, i] = (0, -1, 0); continue
            V[j, i], N[j, i] = h
    # base normal = the strip surface's OWN geometric normal (the skin mesh is coarse, 4-8 mm faces with irregular vertex normals: using them gave a mosaic),
    # low-passed, then the designed pillow tilt on top
    dx = abs(X[0, 1] - X[0, 0]) if n > 1 else 1e-3
    Vp = V + lift * N
    Tx = np.gradient(Vp, axis=1); Tt = np.gradient(Vp, axis=0)
    G = np.cross(Tx, Tt); G /= np.maximum(np.linalg.norm(G, axis=2, keepdims=True), 1e-30)
    flip = np.sum(G * (Vp - C_HEAD[None, None, :]), axis=2, keepdims=True) < 0
    G = np.where(flip, -G, G)
    Ns = gsmooth(G, p['nsig_x'] / dx, 1); Ns = gsmooth(Ns, p['nsig_t'], 0)
    Ns /= np.linalg.norm(Ns, axis=2, keepdims=True)
    Nt = Ns.copy()
    if tilt is not None:
        env = np.maximum(0.0, 1.0 - (np.abs(X) / env_hw) ** 2) ** 0.7
        ang = ease_interp(T, tilt) * env
        Nt = pitch(Ns, ang); Nt /= np.linalg.norm(Nt, axis=2, keepdims=True)
    V = Vp
    F = quads(m1 - 1, n)
    Vf = V.reshape(-1, 3); Nf = Nt.reshape(-1, 3)
    Fo = []
    for f in F:
        q = Vf[f]; c = q.mean(0); nrm = np.cross(q[1] - q[0], q[2] - q[0])
        Fo.append(f if np.dot(nrm, c - C_HEAD) > 0 else f[::-1])
    return dict(V=Vf, F=Fo, N=Nf, mat=mat, miss=miss)


# ---------------------------------------------------------------------------------------------------------------- write into Face_F
LIP_MATS = ('Face_Lip', 'Face_LipUp', 'Face_Seam')


def replace_in_face(face_obj, S, smooth=True, custom_normals=True):
    """bmesh re-uses freed memory slots, so the new faces do NOT end up last: they are tagged with an int face layer and found again after to_mesh"""
    me = face_obj.data
    mats = [m.name if m else '' for m in me.materials]
    lip_idx = {mats.index(m) for m in LIP_MATS}
    bm = bmesh.new(); bm.from_mesh(me)
    rm = [f for f in bm.faces if f.material_index in lip_idx]
    n_old = len(rm)
    bmesh.ops.delete(bm, geom=rm, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    n_keep_faces = len(bm.faces)
    lay = bm.faces.layers.int.new('lipnew')
    newN = []                                  # per new face: list of its corner normals (creation order of the face's vertices)
    for key in ('LipUp', 'Lip', 'Seam'):
        s = S[key]; vs = [bm.verts.new(tuple(v)) for v in s['V']]; mi = mats.index(s['mat'])
        for f in s['F']:
            face = bm.faces.new([vs[i] for i in f]); face.material_index = mi; face.smooth = smooth
            newN.append([s['N'][i] for i in f]); face[lay] = len(newN)
    bm.to_mesh(me); bm.free()
    me.update()
    att = me.attributes['lipnew']; tag = np.empty(len(me.polygons), np.int32); att.data.foreach_get('value', tag)
    me.attributes.remove(att)
    info = dict(old_faces=n_old, kept_faces=n_keep_faces, new_faces=len(newN), new_verts=sum(len(S[k]['V']) for k in S), tagged=int((tag > 0).sum()))
    if not custom_normals: return info
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    for pi in np.where(tag > 0)[0]:
        pl = me.polygons[pi]; nn = newN[tag[pi] - 1]
        assert pl.loop_total == len(nn)
        for k in range(pl.loop_total): cn[pl.loop_start + k] = nn[k]
    me.normals_split_custom_set([tuple(v) for v in cn])
    return info


def skin_from_object(body_obj):
    me = body_obj.data
    n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    vn = np.empty(n * 3); me.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
    F = [list(p.vertices) for p in me.polygons]
    return Skin(V, F, vn)
