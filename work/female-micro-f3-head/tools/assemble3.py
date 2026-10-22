"""MicroF3 assembly.  blender -b --factory-startup --python assemble3.py -- <start.blend> <variant.npz> <anorm.npz> <out.blend> <report.json> [lip_params.json]
- Body_F: new vertex positions (same topology / UVs / groups / materials); per-loop shading normals = analytic surface normals blended in by the zone weight (rest: unchanged auto normals)
- Face_F: every non-lip vertex follows its skin triangle (local-frame transfer, as in MicroF2); the lip paint (Face_Lip / Face_LipUp / Face_Seam) is REPLACED by lips3's plate-measured strips with pillow normals"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import fl, lips3
argv = sys.argv[sys.argv.index('--') + 1:]
start, npz, anpz, out, report = argv[:5]
lip_params = argv[5] if len(argv) > 5 else None
bpy.ops.wm.open_mainfile(filepath=start)
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
me = body.data; fm = face.data
V0, F = fl.mesh_arrays(me)
d = np.load(npz, allow_pickle=True)
Vn = d['V'].astype(np.float32).astype(np.float64)
assert Vn.shape == V0.shape, (Vn.shape, V0.shape)
tris = []
for fi, f in enumerate(F):
    for i in range(1, len(f) - 1): tris.append((int(f[0]), int(f[i]), int(f[i + 1])))
tris = np.array(tris, np.int64)
moved_v = np.linalg.norm(Vn - V0, axis=1) > 0.0
moved_tri = moved_v[tris].any(axis=1)
print('Body_F vertices moved:', int(moved_v.sum()), 'triangles touching a moved vertex:', int(moved_tri.sum()))
# ---- Face_F: non-lip vertices follow the skin (frame transfer) ----
bvh = BVHTree.FromPolygons([tuple(v) for v in V0], [tuple(t) for t in tris])
LV = np.array([v.co[:] for v in fm.vertices], np.float64); LVn = LV.copy(); nre = 0; maxshift = 0.0
def frame(P, t):
    a, b, c = P[t[0]], P[t[1]], P[t[2]]; u = b - a; w = c - a; n = np.cross(u, w); n /= max(np.linalg.norm(n), 1e-30)
    return a, u, w, n
for i, p in enumerate(LV):
    loc, nrm, idx, dist = bvh.find_nearest(Vector(p), 0.05)
    if loc is None or not moved_tri[idx]: continue
    t = tris[idx]; a, u, w, n = frame(V0, t)
    M = np.stack([u, w, n], 1); s, r, h = np.linalg.solve(M, p - a)
    a2, u2, w2, n2 = frame(Vn, t); p2 = a2 + s * u2 + r * w2 + h * n2
    LVn[i] = p2; nre += 1; maxshift = max(maxshift, float(np.linalg.norm(p2 - p)))
print('Face_F vertices re-projected:', nre, 'max shift mm %.3f' % (maxshift * 1000))
me.vertices.foreach_set('co', Vn.astype(np.float32).ravel()); me.update()
fm.vertices.foreach_set('co', LVn.astype(np.float32).ravel()); fm.update()
# ---- Body_F shading normals ----
an = np.load(anpz); N = an['N']; w = an['w']
nl = len(me.loops)
cn = np.empty(nl * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
wl = w[lv][:, None]; mix = wl * N[lv] + (1 - wl) * cn
mix /= np.maximum(np.linalg.norm(mix, axis=1, keepdims=True), 1e-12)
dang = np.degrees(np.arccos(np.clip((mix * cn).sum(1), -1, 1)))
me.normals_split_custom_set([tuple(v) for v in mix])
print('Body_F custom normals set: loops %d, changed >0.5 deg: %d, max change %.1f deg' % (nl, int((dang > 0.5).sum()), dang.max()))
# ---- lips ----
p = dict(lips3.P0)
if lip_params:
    for k, v in json.load(open(lip_params)).items(): p[k] = v
skin = lips3.skin_from_object(body)
S = lips3.build_strips(skin, p)
info = lips3.replace_in_face(face, S)
print('lips:', info, {k: v['miss'] for k, v in S.items()})
bpy.ops.wm.save_as_mainfile(filepath=out)
json.dump(dict(moved_vertices=int(moved_v.sum()), face_reprojected=int(nre), face_max_shift_mm=maxshift * 1000, normals_loops_changed=int((dang > 0.5).sum()), normals_max_change_deg=float(dang.max()), lips=info,
               lip_params={k: (list(v) if isinstance(v, tuple) else v) for k, v in p.items()}), open(report, 'w'), indent=1, default=float)
print('saved', out)
