"""Analyse leg tube ring structure near the ankle + raw custom normals.  Run with Blender python (numpy)."""
import sys, pickle, numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-legs-feet-form2'
bpy.ops.wm.open_mainfile(filepath=W + '/baseline/start_7f145b94.blend')
me = bpy.data.objects['Body_M'].data
n = len(me.vertices)
V = np.load(W + '/data/V_start.npy')
F = pickle.load(open(W + '/data/F.pkl', 'rb'))
# raw custom normals
cn = me.attributes['custom_normal']
raw = np.zeros(len(me.loops) * 2, np.int32)
tmp = np.zeros(len(me.loops) * 2, np.int32)
try:
    cn.data.foreach_get('value', raw)
    print('raw sample', raw[:12])
except Exception as e:
    print('foreach_get value failed', e)
    print(dir(cn.data[0]))
    print(cn.data[0].value if hasattr(cn.data[0], 'value') else None)
if raw.any():
    r = raw.reshape(-1, 2)
    print('raw custom normal stats: min', r.min(0), 'max', r.max(0), 'frac zero', float((r == 0).all(1).mean()))
    print('abs percentile 50/90/99/99.9', np.percentile(np.abs(r), [50, 90, 99, 99.9]))
# adjacency
E = set()
for p in F:
    for k in range(len(p)):
        a, b = p[k], p[(k + 1) % len(p)]
        E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
nb = [[] for _ in range(n)]
for a, b in E:
    nb[a].append(b); nb[b].append(a)
ZONE = (V[:, 2] < 0.765) & (np.abs(V[:, 0]) < 0.27)
L = ZONE & (V[:, 0] > 0)
print('left zone verts', L.sum())
# z histogram of left leg verts z<0.30 in 2mm bins
zs = V[L, 2]
for lo in np.arange(0.0, 0.30, 0.01):
    s = L & (V[:, 2] >= lo) & (V[:, 2] < lo + 0.01)
    if s.sum():
        print(f'z[{lo:.2f},{lo+0.01:.2f}) n={s.sum():4d} xrange {V[s,0].min():.3f}..{V[s,0].max():.3f} yrange {V[s,1].min():.3f}..{V[s,1].max():.3f}')
# valence histogram
deg = np.array([len(x) for x in nb])
print('valence histogram (left zone):', np.bincount(deg[L]))
# find non-4-valent verts in left leg z>0.10
odd = np.where(L & (deg != 4) & (V[:, 2] > 0.10))[0]
print('non-4-valent verts left leg z>0.10:', len(odd))
for i in odd[:60]:
    print(i, deg[i], V[i].round(4))
