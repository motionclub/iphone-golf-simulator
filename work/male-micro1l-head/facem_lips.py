"""Micro1l: rebuild ONLY the lip + seam paint strips of Face_M on the (edited) Body_M surface; every other Face_M vertex/face is copied bit-for-bit.
blender -b --factory-startup --python facem_lips.py -- <in.blend> <out.blend> [json params]
Strips are ray-cast onto the skin like the Micro1i builder, but: taller vermilion (upper with a cupid's-bow, lower fuller), shorter/tapered seam (no long tails beyond the corners),
9 rows per lip and an adaptive lift so the skin can never poke through the paint (the 'white specks / stripes' of Micro1i)."""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
WK = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work'
for p in (WK + '/male-micro1i', WK + '/male-micro1h', WK + '/male-micro1e'): sys.path.insert(0, p)
import h1lib as H, sculpt as S, faceparts as FP
mm = 0.001
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = argv[1]
PRM = dict(up_h=6.6, bow_dip=0.9, bow_peak=0.5, bow_x=8.0, lo_h=12.0, up_w=34.0, lo_w=29.5, seam_w=2.4, seam_half=35.0, seam_pow=2.6, lift=0.34, seam_lift=0.60, nu=48, nv=7, margin=0.10, plan=None, seam_scale=1.0, seam_over=0.25)
if len(argv) > 2: PRM.update(json.loads(argv[2]))
body = bpy.data.objects['Body_M']; face = bpy.data.objects['Face_M']
me = body.data
P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
verts = [tuple(v) for v in P]; tris = []
for p in me.polygons:
    vs = list(p.vertices); tris.append((vs[0], vs[1], vs[2]))
    if len(vs) > 3: tris.append((vs[0], vs[2], vs[3]))
bvh = BVHTree.FromPolygons(verts, tris)


def skin_hit(x, z):
    h = bvh.ray_cast(Vector((float(x), -1.0, float(z))), Vector((0, 1, 0)), 3.0)
    return h


def strip(pts, nu, nv, lift, flip, return_lift=False):
    """pts (nu,nv,2) x,z -> ray-cast verts lifted along the hit normal.  Poke-through control (r2b): the strip must clear the skin at EVERY sample of a 4x4 grid inside each quad (bilinear strip surface vs the
    skin ray-cast at the same x,z, measured along the skin normal) and at every skin vertex inside the footprint; deficits are spread to the quad corners (max), iterated, then the lift field is smoothed
    (3 passes, only ever increasing) so the paint does not zig-zag."""
    V = np.zeros((nu, nv, 3)); Nn = np.zeros((nu, nv, 3)); HIT = np.zeros((nu, nv, 3))
    for i in range(nu):
        for k in range(nv):
            h = skin_hit(*pts[i, k])
            if h[0] is None: p, n = Vector((pts[i, k][0], -0.15, pts[i, k][1])), Vector((0, -1, 0))
            else: p, n = h[0], h[1]
            lf = float(lift[i, k]) if hasattr(lift, 'shape') else lift
            V[i, k] = np.array(p) + np.array(n) * lf; Nn[i, k] = np.array(n); HIT[i, k] = np.array(p)
    mg = PRM['margin'] * mm
    xs_all = np.array([v[0] for v in verts]); zs_all = np.array([v[2] for v in verts]); ys_all = np.array([v[1] for v in verts])
    xmin, xmax = pts[:, :, 0].min() - 1e-4, pts[:, :, 0].max() + 1e-4; zmin, zmax = pts[:, :, 1].min() - 1e-4, pts[:, :, 1].max() + 1e-4
    cand = np.where((xs_all > xmin) & (xs_all < xmax) & (zs_all > zmin) & (zs_all < zmax) & (ys_all < -0.10))[0]
    S = np.linspace(0.0, 1.0, 4); lift_add = np.zeros((nu, nv))
    for it in range(12):
        deficit = np.zeros((nu, nv))
        for i in range(nu - 1):
            for k in range(nv - 1):
                c00, c10, c11, c01 = V[i, k], V[i + 1, k], V[i + 1, k + 1], V[i, k + 1]
                for su in S:
                    for sv in S:
                        pnt = (1 - su) * ((1 - sv) * c00 + sv * c01) + su * ((1 - sv) * c10 + sv * c11)
                        h = skin_hit(pnt[0], pnt[2])
                        if h[0] is None: continue
                        need = mg - (pnt - np.array(h[0])) @ np.array(h[1])
                        if need > 0:
                            for (a_, b_, w_) in ((i, k, (1 - su) * (1 - sv)), (i + 1, k, su * (1 - sv)), (i + 1, k + 1, su * sv), (i, k + 1, (1 - su) * sv)):
                                if w_ > 0.02: deficit[a_, b_] = max(deficit[a_, b_], need / max(w_ ** 0.5, 0.4))
        for v in cand:
            x, z, y = xs_all[v], zs_all[v], ys_all[v]
            col = np.searchsorted(pts[:, nv // 2, 0], x) - 1
            if col < 0 or col >= nu - 1: continue
            t = (x - pts[col, nv // 2, 0]) / max(pts[col + 1, nv // 2, 0] - pts[col, nv // 2, 0], 1e-9)
            zc = (1 - t) * pts[col, :, 1] + t * pts[col + 1, :, 1]
            order = np.argsort(zc); zsrt = zc[order]
            if z < zsrt[0] or z > zsrt[-1]: continue
            j = np.searchsorted(zsrt, z) - 1; j = min(max(j, 0), nv - 2); a, b = order[j], order[j + 1]
            if abs(a - b) != 1: continue
            k = min(a, b); u = (z - zsrt[j]) / max(zsrt[j + 1] - zsrt[j], 1e-9)
            u = u if a < b else 1 - u
            y_st = (1 - t) * ((1 - u) * V[col, k, 1] + u * V[col, k + 1, 1]) + t * ((1 - u) * V[col + 1, k, 1] + u * V[col + 1, k + 1, 1])
            need = (y_st - y) + mg
            if need > 0:
                for (aa, bb, w_) in ((col, k, (1 - t) * (1 - u)), (col, k + 1, (1 - t) * u), (col + 1, k, t * (1 - u)), (col + 1, k + 1, t * u)):
                    if w_ > 0.05: deficit[aa, bb] = max(deficit[aa, bb], need / max(abs(Nn[aa, bb, 1]), 0.4))
        if deficit.max() <= 1e-7: break
        # smooth the increase (never decrease) so neighbouring corners follow
        d2 = deficit.copy()
        for _ in range(2):
            e = d2.copy(); e[1:-1, :] = np.maximum(d2[1:-1, :], 0.6 * np.maximum(d2[:-2, :], d2[2:, :])); d2 = e
        V += Nn * d2[:, :, None]
    F = []
    for i in range(nu - 1):
        for k in range(nv - 1):
            a = i * nv + k; b = (i + 1) * nv + k; c = (i + 1) * nv + k + 1; d = i * nv + k + 1
            F.append([a, d, c, b] if flip else [a, b, c, d])
    if return_lift: return V.reshape(-1, 3), F, ((V - HIT) * Nn).sum(axis=2)
    return V.reshape(-1, 3), F


def smooth_rows(V, nu, nv, passes=2, w=0.5):
    A = np.array(V, float).reshape(nu, nv, 3)
    for _ in range(passes):
        B = A.copy(); B[1:-1] = (1 - w) * A[1:-1] + w * 0.5 * (A[:-2] + A[2:]); A = B
    return A.reshape(-1, 3)


PLAN = None
if PRM.get('plan'):
    PLAN = {k: np.asarray(v, float) for k, v in json.load(open(PRM['plan'])).items()}


def seam_z(x):
    """carved seam loop z (m) vs |x| from the lip plan (falls back to the Micro1h analytic seam)"""
    if PLAN is not None: return float(np.interp(abs(x) / mm, PLAN['x'], PLAN['seam_paint'] if 'seam_paint' in PLAN else PLAN['seam'])) * mm
    return float(S.seam_z(np.array([abs(x)]))[0])


def _border(kind, ax_mm):
    if PLAN is None: return None
    k = kind + '_paint' if (kind + '_paint') in PLAN else kind
    return float(np.interp(ax_mm, PLAN['x'], PLAN[k]))


def _extent(kind, thr=0.3):
    """largest |x| (mm) where the vermilion height above/below the seam still exceeds thr"""
    k = kind + '_paint' if (kind + '_paint') in PLAN else kind
    d = np.abs(PLAN[k] - (PLAN['seam_paint'] if 'seam_paint' in PLAN else PLAN['seam'])); ok = np.where(d > thr)[0]
    return float(PLAN['x'][ok.max()]) if len(ok) else 0.0


def lip_up(nu, nv):
    pts = np.zeros((nu, nv, 2))
    if PLAN is not None:
        Xe = _extent('up', 0.3) + 0.5
        for i, u in enumerate(np.linspace(-1, 1, nu)):
            x = u * Xe * mm; ax = abs(x) / mm; z0 = seam_z(x); z1 = max(_border('up', ax) * mm, z0 + 0.12 * mm)
            for k in range(nv): pts[i, k] = (x, z0 + (k / (nv - 1)) * (z1 - z0))
        return pts
    W = PRM['up_w'] * mm
    for i, u in enumerate(np.linspace(-1, 1, nu)):
        x = u * W; ax = abs(x) / mm
        h = PRM['up_h'] * mm * max(0.0, 1 - abs(u) ** 1.7) ** (1 / 1.7)
        h = h * (1.0 + (-PRM['bow_dip'] * math.exp(-(ax / 2.7) ** 2) + PRM['bow_peak'] * math.exp(-((ax - PRM['bow_x']) / 3.2) ** 2)) / max(PRM['up_h'], 1e-6))
        z0 = seam_z(x)
        for k in range(nv): pts[i, k] = (x, z0 + (k / (nv - 1)) * h)
    return pts


def lip_lo(nu, nv):
    pts = np.zeros((nu, nv, 2))
    if PLAN is not None:
        Xe = _extent('lo', 0.3) + 0.5
        for i, u in enumerate(np.linspace(-1, 1, nu)):
            x = u * Xe * mm; ax = abs(x) / mm; z0 = seam_z(x); z1 = min(_border('lo', ax) * mm, z0 - 0.12 * mm)
            for k in range(nv): pts[i, k] = (x, z0 + (k / (nv - 1)) * (z1 - z0))
        return pts
    W = PRM['lo_w'] * mm
    for i, u in enumerate(np.linspace(-1, 1, nu)):
        x = u * W; h = PRM['lo_h'] * mm * max(0.0, 1 - abs(u) ** 1.9) ** (1 / 1.9); z0 = seam_z(x)
        for k in range(nv): pts[i, k] = (x, z0 - (k / (nv - 1)) * h)
    return pts


def seam(nu=64, nv=3):
    Hh = PRM['seam_half'] * mm; pts = np.zeros((nu, nv, 2))
    if PLAN is not None and 'seam_t' in PLAN: Hh = float(PLAN['x'][np.where(PLAN['seam_t'] > 0.05)[0].max()]) * mm
    for i, x in enumerate(np.linspace(-Hh, Hh, nu)):
        if PLAN is not None and 'seam_t' in PLAN:
            ax_ = abs(x) / mm; wv = float(np.interp(ax_, PLAN['x'], PLAN['seam_t'])) * mm * PRM.get('seam_scale', 1.0)
            end = max(0.0, (ax_ - (Hh / mm - 1.6)) / 1.6); wv *= math.sqrt(max(0.0, 1.0 - end * end))        # rounded end (the plate corners are blunt dark dots)
        else:
            wv = PRM['seam_w'] * mm * math.sqrt(max(0.0, 1.0 - (abs(x) / Hh) ** PRM['seam_pow']))
        z0 = seam_z(x)
        for k, o in enumerate((-0.5, 0.0, 0.5)): pts[i, k] = (x, z0 + o * wv)
    return pts


newparts = {}
nu, nv = int(PRM['nu']), int(PRM['nv'])
Vu, Fu, Lu = strip(lip_up(nu, nv), nu, nv, PRM['lift'] * mm, False, True); newparts['LipUp'] = (smooth_rows(Vu, nu, nv), Fu)
Vl, Fl, Ll = strip(lip_lo(nu, nv), nu, nv, PRM['lift'] * mm, True, True); newparts['Lip'] = (smooth_rows(Vl, nu, nv), Fl)
# the seam ribbon must always lie ABOVE the two lip strips where they overlap (they start on its centre line): lift = max(base, lip lift near it) + 0.25 mm
sp = seam(); nsu = sp.shape[0]
def _lip_lift_at(x_m):
    out = 0.0
    for P_, L_ in ((lip_up(nu, nv), Lu), (lip_lo(nu, nv), Ll)):
        xs_ = P_[:, 0, 0]; xs_ = np.asarray(xs_)
        for kk in (0, 1):
            out = max(out, float(np.interp(x_m, xs_, L_[:, kk])) if (xs_.min() <= x_m <= xs_.max()) else 0.0)
    return out
slift = np.zeros((nsu, 3))
for i in range(nsu):
    for k in range(3): slift[i, k] = max(PRM['seam_lift'] * mm, _lip_lift_at(sp[i, k, 0]) + PRM.get('seam_over', 0.25) * mm)
Vs, Fs = strip(sp, nsu, 3, slift, False); newparts['Seam'] = (smooth_rows(Vs, nsu, 3, passes=3), Fs)
# ---- assemble: copy every non-lip face/vertex of the old Face_M bit-for-bit, append the new strips
omesh = face.data; mats = list(omesh.materials); names = [m.name for m in mats]
oldV = np.empty(len(omesh.vertices) * 3); omesh.vertices.foreach_get('co', oldV); oldV = oldV.reshape(-1, 3)
oldF = [list(p.vertices) for p in omesh.polygons]; oldS = [p.material_index for p in omesh.polygons]
replace = {names.index('Face_' + k) for k in ('Lip', 'LipUp', 'Seam')}
keepF = [(f, s) for f, s in zip(oldF, oldS) if s not in replace]
used = sorted({v for f, s in keepF for v in f}); remap = {v: i for i, v in enumerate(used)}
V_new = [tuple(oldV[v]) for v in used]; F_new = [[remap[v] for v in f] for f, s in keepF]; S_new = [s for f, s in keepF]
for slot, (Vn, Fn) in newparts.items():
    Fo = FP.orient_faces(Vn, Fn, 'front'); base = len(V_new)
    V_new.extend([tuple(v) for v in Vn]); F_new.extend([[base + int(i) for i in f] for f in Fo]); S_new.extend([names.index('Face_' + slot)] * len(Fo))
o = H.make_mesh_object('Face_M_new', np.array(V_new), F_new)
newme = o.data
newme.materials.clear()
for m in mats: newme.materials.append(m)
newme.polygons.foreach_set('material_index', np.array(S_new, np.int32)); newme.update()
bpy.data.objects.remove(o, do_unlink=True)
face.data = newme; newme.name = 'Face_M'
try:
    if omesh.users == 0: bpy.data.meshes.remove(omesh)
except Exception: pass
print('FACEM_LIPS verts', len(V_new), 'faces', len(F_new), '(old', len(oldV), len(oldF), ')', json.dumps(PRM))
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
