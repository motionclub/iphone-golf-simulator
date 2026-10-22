"""Compare the blend's stored corner normals with freshly computed angle-weighted vertex normals of the same geometry, binned by z.
blender -b --factory-startup --python nrmcheck.py -- <blend> <out.json>"""
import sys, json, numpy as np, bpy
a = sys.argv[sys.argv.index('--') + 1:]; src, outj = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=src); me = bpy.data.objects['Body_M'].data
n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
nv = np.zeros((n, 3)); polys = [list(p.vertices) for p in me.polygons]
for p in polys:
    P = V[p]; m = len(p); fn = np.zeros(3)
    for k in range(1, m - 1): fn += np.cross(P[k] - P[0], P[k + 1] - P[0])
    l = np.linalg.norm(fn)
    if l < 1e-18: continue
    fn /= l
    for k in range(m):
        u = P[(k + 1) % m] - P[k]; w = P[(k - 1) % m] - P[k]; ang = np.arccos(np.clip(u @ w / max(np.linalg.norm(u) * np.linalg.norm(w), 1e-18), -1, 1)); nv[p[k]] += fn * ang
nv /= np.maximum(np.linalg.norm(nv, axis=1, keepdims=True), 1e-18)
dev = np.degrees(np.arccos(np.clip((cn * nv[lv]).sum(1), -1, 1))); Z = V[lv, 2]
res = dict(has_custom=bool(me.has_custom_normals), bins={})
for z0 in np.arange(0.60, 1.20, 0.02):
    m = (Z >= z0) & (Z < z0 + 0.02) & (np.abs(V[lv, 0]) < 0.25)
    if m.sum(): res['bins'][f'{z0:.2f}'] = dict(n=int(m.sum()), median=float(np.median(dev[m])), p95=float(np.percentile(dev[m], 95)), max=float(dev[m].max()))
json.dump(res, open(outj, 'w'), indent=1)
for k, v in res['bins'].items(): print(k, v)
print('has_custom_normals', me.has_custom_normals, 'auto_smooth?', getattr(me, 'use_auto_smooth', None))
