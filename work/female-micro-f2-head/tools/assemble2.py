"""Write new Body_F vertex positions into a copy of the staged blend (same topology), re-project the Face_F paint wherever the skin under it moved.
blender -b --factory-startup --python assemble2.py -- <start.blend> <variant.npz> <out.blend> [report.json]
- Body_F: only vertex coordinates change (faces, UVs, materials, vertex groups untouched)
- Face_F: a vertex is re-projected only if the old skin triangle under it moved; its offset is carried in the local (tangent, tangent, normal) frame of that triangle"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
start, npz, out = argv[0], argv[1], argv[2]
report = argv[3] if len(argv) > 3 else None
bpy.ops.wm.open_mainfile(filepath=start)
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
me = body.data; fm = face.data
V0, F = fl.mesh_arrays(me)
V0f = V0.copy()
d = np.load(npz, allow_pickle=True)
Vn = d['V'].astype(np.float32).astype(np.float64)       # compare/write at the blend's own float32 precision
assert Vn.shape == V0.shape, (Vn.shape, V0.shape)
# fan triangles + face map
tris = []
for fi, f in enumerate(F):
    for i in range(1, len(f) - 1): tris.append((int(f[0]), int(f[i]), int(f[i + 1])))
tris = np.array(tris, np.int64)
moved_v = np.linalg.norm(Vn - V0, axis=1) > 0.0
moved_tri = moved_v[tris].any(axis=1)
print('Body_F vertices moved:', int(moved_v.sum()), 'triangles touching a moved vertex:', int(moved_tri.sum()))
# ---- Face_F re-projection (frame transfer) ----
bvh = BVHTree.FromPolygons([tuple(v) for v in V0], [tuple(t) for t in tris])
LV = np.array([v.co[:] for v in fm.vertices], np.float64)
LVn = LV.copy(); nre = 0; maxshift = 0.0; nfar = 0
def frame(P, t):
    a, b, c = P[t[0]], P[t[1]], P[t[2]]
    u = b - a; w = c - a; n = np.cross(u, w); n /= max(np.linalg.norm(n), 1e-30)
    return a, u, w, n
for i, p in enumerate(LV):
    loc, nrm, idx, dist = bvh.find_nearest(Vector(p), 0.05)
    if loc is None: nfar += 1; continue
    if not moved_tri[idx]: continue
    t = tris[idx]
    a, u, w, n = frame(V0, t)
    # local coordinates of p in the old frame: p = a + s u + r w + h n
    M = np.stack([u, w, n], 1); s, r, h = np.linalg.solve(M, p - a)
    a2, u2, w2, n2 = frame(Vn, t)
    p2 = a2 + s * u2 + r * w2 + h * n2
    LVn[i] = p2; nre += 1; maxshift = max(maxshift, float(np.linalg.norm(p2 - p)))
print('Face_F vertices re-projected:', nre, 'max shift mm %.3f' % (maxshift * 1000), 'far (no skin within 5 cm):', nfar)
# ---- write ----
me.vertices.foreach_set('co', Vn.astype(np.float32).ravel()); me.update()
fm.vertices.foreach_set('co', LVn.astype(np.float32).ravel()); fm.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
if report:
    json.dump(dict(moved_vertices=int(moved_v.sum()), moved_triangles=int(moved_tri.sum()), face_reprojected=int(nre), face_max_shift_mm=maxshift * 1000), open(report, 'w'), indent=1)
print('saved', out)
