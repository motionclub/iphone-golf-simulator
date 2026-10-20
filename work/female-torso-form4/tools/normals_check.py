"""blender -b <blend> --python normals_check.py -- out.json zone.npz
Angle between the decoded (custom) corner normals of Body_F and the angle-weighted geometric vertex normals, over the corners of zone vertices.
Custom-normal raw codes are relative to the computed loop normal, so after a positions-only edit the decoded normals should still follow the geometry."""
import bpy, sys, json
import numpy as np
out = sys.argv[sys.argv.index('--') + 1]
zone = np.load(sys.argv[sys.argv.index('--') + 2])['torso']
o = bpy.data.objects['Body_F']
me = o.data
nv, nl, npoly = len(me.vertices), len(me.loops), len(me.polygons)
co = np.empty(nv * 3, np.float64); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
ps = np.empty(npoly, np.int32); me.polygons.foreach_get('loop_start', ps)
pt = np.empty(npoly, np.int32); me.polygons.foreach_get('loop_total', pt)
cn = np.empty(nl * 3, np.float64); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
# angle-weighted vertex normals from polygons (fan of the first vertex is fine for these near-planar tris/quads)
vn = np.zeros((nv, 3))
for i in range(npoly):
    idx = lv[ps[i]:ps[i] + pt[i]]
    p = co[idx]
    n = np.cross(p[1] - p[0], p[2] - p[0])
    if pt[i] == 4:
        n = n + np.cross(p[2] - p[0], p[3] - p[0])
    ln = np.linalg.norm(n)
    if ln < 1e-18:
        continue
    n /= ln
    k = len(idx)
    for j in range(k):
        a = p[(j + 1) % k] - p[j]; b = p[(j - 1) % k] - p[j]
        ang = np.arccos(np.clip(a @ b / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-18), -1, 1))
        vn[idx[j]] += n * ang
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-18)
sel = zone[lv]
ang = np.degrees(np.arccos(np.clip((cn[sel] * vn[lv[sel]]).sum(1), -1, 1)))
json.dump({'corners': int(sel.sum()), 'median_deg': float(np.median(ang)), 'p95_deg': float(np.percentile(ang, 95)), 'max_deg': float(ang.max())}, open(out, 'w'))
print('NORMALS_OK')
