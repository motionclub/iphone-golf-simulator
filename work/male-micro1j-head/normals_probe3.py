import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head'
bpy.ops.wm.open_mainfile(filepath=W + '/baseline/HeroBase_Male_Silhouette.blend')
body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
V = np.load(W + '/data/V_start.npy'); vn = np.load(W + '/data/vn_stored.npy')
# clear custom normals (operator needs the object active in object mode)
bpy.context.view_layer.objects.active = body
for o in bpy.context.view_layer.objects: o.select_set(o == body)
try:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
except Exception as e:
    print('operator failed', e)
print('has custom normals after clear:', me.has_custom_normals)
me.update()
nrm = np.empty(n * 3); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)   # pure geometry normals (Blender weighting)
np.save(W + '/data/vn_geom_blender.npy', nrm)
z = V[:, 2]
d = np.degrees(np.arccos(np.clip((nrm * vn).sum(1), -1, 1)))
print('Blender geometric normals vs stored: head z>1.43 mean %.3f p95 %.2f ; body mean %.3f' % (d[z > 1.43].mean(), np.percentile(d[z > 1.43], 95), d[z < 1.40].mean()))
F = [[v for v in p.vertices] for p in me.polygons]
E = set()
for f in F:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E)); deg = np.bincount(E.ravel(), minlength=n).astype(float)
def nm(P):
    s = np.zeros_like(P); np.add.at(s, E[:, 0], P[E[:, 1]]); np.add.at(s, E[:, 1], P[E[:, 0]]); return s / np.maximum(deg, 1)[:, None]
ring = (np.abs(z - 1.43) < 0.0015) & (np.abs(V[:, 0]) < 0.14); hv = (z > 1.43) & (np.abs(V[:, 0]) < 0.14) & ~ring
P = nrm.copy()
for its in range(0, 9):
    if its:
        t = 0.5 * P + 0.5 * nm(P); t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12); P = np.where(hv[:, None], t, P)
    dd = np.degrees(np.arccos(np.clip((P * vn).sum(1), -1, 1)))
    print(f'  recipe(Blender geometric normals, {its} its) vs stored: head mean {dd[z>1.43].mean():.3f} p95 {np.percentile(dd[z>1.43],95):.2f} max {dd[z>1.43].max():.1f} | body mean {dd[z<1.40].mean():.4f}')
