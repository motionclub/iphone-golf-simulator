"""blender -b --factory-startup --python lips_audit.py -- blend out.json : lip paint audit
 - plan fidelity of the strips vs the plate-measured borders (tools/lip_measure.py)
 - clearance of the strips over the skin (nearest distance) and poke-through: dense (x, z) front-ray samples, strip y vs skin y, with BOTH triangulations of the skin quads
   (Blender's loop triangles and a plain fan -- a game engine may split the quads the other way)"""
import sys, json, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import fl
blend, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
mb = body.data; mf = face.data
Vb = np.array([v.co[:] for v in mb.vertices]); Vf = np.array([v.co[:] for v in mf.vertices])
mats = [m.name for m in mf.materials]
mi = np.array([p.material_index for p in mf.polygons])
res = {}
# ---- strips as triangles
def tris_of(me, sel=None):
    T = []
    for p in me.polygons:
        if sel is not None and not sel(p): continue
        vs = list(p.vertices)
        for i in range(1, len(vs) - 1): T.append((vs[0], vs[i], vs[i + 1]))
    return T
lipk = {mats.index(m): m for m in ('Face_Lip', 'Face_LipUp', 'Face_Seam')}
Tstrip = tris_of(mf, lambda p: p.material_index in lipk)
bvh_strip = BVHTree.FromPolygons([tuple(v) for v in Vf], Tstrip)
mb.calc_loop_triangles()
T_blender = [tuple(t.vertices) for t in mb.loop_triangles]
T_fan = tris_of(mb)
bvh_b = BVHTree.FromPolygons([tuple(v) for v in Vb], T_blender); bvh_f = BVHTree.FromPolygons([tuple(v) for v in Vb], T_fan)
# ---- clearance of strip vertices over the skin (nearest point)
sv = set()
for p in mf.polygons:
    if p.material_index in lipk: sv.update(p.vertices)
sv = sorted(sv); d = []
for i in sv:
    loc, nrm, idx, dist = bvh_b.find_nearest(Vector(Vf[i]))
    d.append(dist)
d = np.array(d) * 1000
res['clearance_mm'] = dict(n=len(sv), min=float(d.min()), mean=float(d.mean()), max=float(d.max()))
print('strip vertices %d: nearest distance to the skin (Blender triangulation) min %.2f mean %.2f max %.2f mm' % (len(sv), d.min(), d.mean(), d.max()))
# ---- dense front-ray gap
xs = np.arange(-0.0345, 0.0345, 0.0005); zs = np.arange(1.458, 1.4865, 0.0004)
for nm, bvh in (('blender_tris', bvh_b), ('fan_tris', bvh_f)):
    gaps = []; nstrip = 0
    for z in zs:
        for x in xs:
            o = Vector((x, -0.30, z)); dd = Vector((0, 1, 0))
            hs = bvh_strip.ray_cast(o, dd)
            if hs[0] is None: continue
            hk = bvh.ray_cast(o, dd)
            if hk[0] is None: continue
            nstrip += 1; gaps.append((hk[0][1] - hs[0][1]) * 1000)      # skin y - strip y : > 0 means the strip is in front of the skin
    g = np.array(gaps)
    res['gap_' + nm] = dict(samples=int(nstrip), min_mm=float(g.min()), p1_mm=float(np.percentile(g, 1)), mean_mm=float(g.mean()), below_0_mm=int((g < 0).sum()), below_0p1_mm=int((g < 0.1).sum()))
    print('front-ray gap strip-vs-skin (%s): %d samples, min %.3f mm, p1 %.3f, mean %.3f, <0: %d, <0.1 mm: %d' % (nm, nstrip, g.min(), np.percentile(g, 1), g.mean(), (g < 0).sum(), (g < 0.1).sum()))
# ---- plan fidelity vs plate measures (strips' border rows)
def rows(matname, m1):
    k = mats.index(matname); ids = sorted({v for p in mf.polygons if p.material_index == k for v in p.vertices})
    P = Vf[ids]; return P
raw = json.load(open(fl.W / 'data/lip_plate_raw.json'))
PU, PL, PS = rows('Face_LipUp', 0), rows('Face_Lip', 0), rows('Face_Seam', 0)
def win(P, x, half=0.0005):
    m = np.abs(P[:, 0] - x) <= half
    return P[m, 2] if m.any() else None
err = {'top': [], 'seam': [], 'bot_core': [], 'bot_outer': []}
for r in raw:
    x = r['x']
    if abs(x) > 0.022: continue
    zu, zl, zs_ = win(PU, x), win(PL, x), win(PS, x)
    if zu is not None: err['top'].append((zu.max() - r['top']) * 1000)
    if zl is not None: err['bot_core' if abs(x) <= 0.0145 else 'bot_outer'].append((zl.min() - r['bot']) * 1000)      # outer part: intentionally narrower than the plate's thresholded border (a soft shadow there)
    if zs_ is not None: err['seam'].append((zs_.mean() - r['seam']) * 1000)
for k, v in err.items():
    v = np.array(v); res['plan_' + k] = dict(n=int(len(v)), mean_mm=float(v.mean()), rms_mm=float(np.sqrt((v ** 2).mean())), max_abs_mm=float(np.abs(v).max()))
    print('plan fidelity %-9s: n %d  mean %+.2f  rms %.2f  max|.| %.2f mm (plate rows are 1.54 mm)' % (k, len(v), v.mean(), np.sqrt((v ** 2).mean()), np.abs(v).max()))
json.dump(res, open(out, 'w'), indent=1)
