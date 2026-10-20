"""blender -b --python selfisect3.py -- <cand.npz|base> [out.json] : self-intersecting triangle pairs among arm-zone + hand triangles (non-adjacent)"""
import bpy, sys, json, numpy as np
from mathutils.bvhtree import BVHTree
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3')
a = sys.argv[sys.argv.index('--') + 1:]
path = W / 'data/mesh_start.npz' if a[0] == 'base' else W / f'data/cand_{a[0]}.npz'
D = np.load(path); V = D['V'].astype(np.float64); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
zone = np.load(W / 'data/zone_R.npy') | np.load(W / 'data/zone_L.npy')
flag = np.r_[zone, np.ones(max(len(V) - len(zone), 0), bool)]
tris = []; src = []
for pi, (s, t) in enumerate(zip(ls, lt)):
    p = [int(x) for x in cv[s:s + t]]
    if all(flag[i] for i in p):
        for k in range(1, t - 1): tris.append((p[0], p[k], p[k + 1])); src.append(pi)
T = np.array(tris)
tree = BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(map(int, t)) for t in T], epsilon=0.0)
pairs = tree.overlap(tree)
bad = []
for i, j in pairs:
    if i >= j: continue
    if set(T[i]) & set(T[j]): continue
    # polygons that share a vertex through a quad diagonal are also adjacent: skip pairs whose source polys share any vertex
    bad.append((i, j))
res = dict(tris=len(T), n_pairs=len(bad))
if bad:
    c = np.array([V[T[i]].mean(0) for i, j in bad])
    res['centroid_min'] = c.min(0).round(3).tolist(); res['centroid_max'] = c.max(0).round(3).tolist()
    res['right'] = int((c[:, 0] > 0).sum()); res['left'] = int((c[:, 0] < 0).sum())
    # hand region (local w > -0.05) vs arm
    res['pairs_xyz_samples'] = c[:8].round(4).tolist()
print('SELFISECT', a[0], json.dumps(res))
if len(a) > 1: json.dump(res, open(a[1], 'w'), indent=1)
