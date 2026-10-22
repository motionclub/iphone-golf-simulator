"""Phase 1a: dump cage data + render the Micro1f 'blank' head in plate framing.
blender -b --factory-startup --python prep0.py"""
import sys, pickle
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H

body = H.get_body(str(H.W / 'baseline/HeroBase_Male_Silhouette.blend'))
me = body.data
V1g, F = H.mesh_arrays(me)
K5 = np.load(H.ROOT / 'work/male-micro1f/final/k5_verts.npy')
assert K5.shape == V1g.shape
d = np.linalg.norm(K5 - V1g, axis=1)
moved = d > 1e-7
print('moved by micro1g:', int(moved.sum()), 'z range of moved', V1g[moved, 2].min(), V1g[moved, 2].max(), 'x absmax', np.abs(V1g[moved, 0]).max())
(H.W / 'data').mkdir(exist_ok=True)
np.save(H.W / 'data/V_micro1g.npy', V1g)
np.save(H.W / 'data/V_micro1f.npy', K5)
pickle.dump([f.tolist() for f in F], open(H.W / 'data/F.pkl', 'wb'))
# mirror-symmetry of the head zone in K5
from mathutils.kdtree import KDTree
head = (K5[:, 2] > 1.40) & (np.abs(K5[:, 0]) < 0.16)
idx = np.where(head)[0]
kd = KDTree(len(K5))
for i, c in enumerate(K5): kd.insert(c, i)
kd.balance()
errs = []
for i in idx:
    c = K5[i]; m = (-c[0], c[1], c[2])
    j, p, dist = kd.find(m)[1], None, kd.find(m)[2]
    errs.append(dist)
errs = np.array(errs) * 1000
print('K5 head mirror-partner distance mm: mean %.3f  p95 %.3f  max %.3f' % (errs.mean(), np.percentile(errs, 95), errs.max()))
# render K5 head
H.set_verts(me, K5)
fm = bpy.data.objects.get('Face_M')
if fm: fm.hide_render = True
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
H.setup_render()
out = H.W / 'r/prep0'; out.mkdir(parents=True, exist_ok=True)
for n in H.PANELS:
    H.head_shot(out / f'k5_{n}.png', n)
print('rendered')
