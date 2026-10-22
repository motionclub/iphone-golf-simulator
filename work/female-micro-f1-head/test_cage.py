import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, cage, loftf
d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
cg = cage.build_cage(ring_pos, geo.C)
H = geo.Head()
U = cg['u']; print('verts', len(U), 'faces', len(cg['faces']), 'shift', cg['shift'])
P = H.phi(U)
for v, p in cg['pinned'].items(): P[v] = p
# edge manifold check
cnt = {}
for f in cg['faces']:
    n = len(f)
    for i in range(n):
        a, b = f[i], f[(i + 1) % n]; k = (min(a, b), max(a, b)); cnt[k] = cnt.get(k, 0) + 1
print('edges', len(cnt), 'boundary', sum(1 for c in cnt.values() if c == 1), 'nonmanifold', sum(1 for c in cnt.values() if c > 2))
loftf.save_npz(str(fl.W / 'data/cage_L0.npz'), P, cg['faces'])
np.save(fl.W / 'data/cage_L0_u.npy', U)
# quad size stats
el = []
for f in cg['faces']:
    for i in range(len(f)): el.append(np.linalg.norm(P[f[i]] - P[f[(i + 1) % len(f)]]))
print('edge mm mean %.1f min %.1f max %.1f' % (np.mean(el) * 1000, np.min(el) * 1000, np.max(el) * 1000))
