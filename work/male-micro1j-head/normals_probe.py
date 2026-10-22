"""Probe how the stored custom normals of the START blend were produced.  blender -b --factory-startup --python normals_probe.py"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head'
bpy.ops.wm.open_mainfile(filepath=W + '/baseline/HeroBase_Male_Silhouette.blend')
body = bpy.data.objects['Body_M']; me = body.data; n = len(me.vertices)
V = np.load(W + '/data/V_start.npy')
cn = np.load(W + '/data/cornernormals_start.npy')
lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
# per-vertex stored normal spread: do all corners of a vertex agree?
sumn = np.zeros((n, 3)); np.add.at(sumn, lv, cn); cnt = np.bincount(lv, minlength=n)
vn = sumn / np.maximum(cnt, 1)[:, None]; vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
spread = np.degrees(np.arccos(np.clip((cn * vn[lv]).sum(axis=1), -1, 1)))
print('corner-vs-vertex-mean spread: max %.3f deg, corners >0.05deg %d' % (spread.max(), (spread > 0.05).sum()))
np.save(W + '/data/vn_stored.npy', vn)
nrm = np.empty(n * 3); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
print('stored vs raw vertex_normals: mean %.3f deg max %.3f' % (np.degrees(np.arccos(np.clip((vn * nrm).sum(1), -1, 1))).mean(), np.degrees(np.arccos(np.clip((vn * nrm).sum(1), -1, 1))).max()))
F = [[v for v in p.vertices] for p in me.polygons]
E = set()
for f in F:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E)); deg = np.bincount(E.ravel(), minlength=n).astype(float)
def nm(P):
    s = np.zeros_like(P); np.add.at(s, E[:, 0], P[E[:, 1]]); np.add.at(s, E[:, 1], P[E[:, 0]]); return s / np.maximum(deg, 1)[:, None]
ring = (np.abs(V[:, 2] - 1.43) < 0.0015) & (np.abs(V[:, 0]) < 0.14)
for zmin in (1.43, 1.40, 1.30):
    hv = (V[:, 2] > zmin) & (np.abs(V[:, 0]) < 0.14) & ~ring
    P = nrm.copy()
    for it in range(1, 9):
        t = 0.5 * P + 0.5 * nm(P); t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
        P = np.where(hv[:, None], t, P)
        d = np.degrees(np.arccos(np.clip((P * vn).sum(1), -1, 1)))
        print(f'zmin {zmin} iters {it}: mean {d.mean():.4f} deg   max {d.max():.2f}  >0.05deg: {(d>0.05).sum()}   (head part mean {d[V[:,2]>1.43].mean():.4f}, body part mean {d[V[:,2]<1.40].mean():.4f})')
