import bpy, numpy as np, json
from mathutils.bvhtree import BVHTree
L = lambda n: np.load(f'data/{n}.npz', allow_pickle=True)
F3, FIN, B = L('f3_body'), L('final_body'), L('base_body')
def tris_of(d):
    ls, lt, cv = d['loop_start'], d['loop_total'], d['corner_verts']; T = []
    for fi, (s, t) in enumerate(zip(ls, lt)):
        for k in range(1, t - 1): T.append((int(cv[s]), int(cv[s + k]), int(cv[s + k + 1])))
    return np.array(T)
def pairs(d):
    V = d['V'].astype(np.float64); T = tris_of(d)
    bv = BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(int(i) for i in t) for t in T], all_triangles=True, epsilon=0.0)
    out = [(i, j) for i, j in bv.overlap(bv) if i < j and not (set(T[i].tolist()) & set(T[j].tolist()))]
    c = np.array([V[T[i]].mean(0) for i, j in out]); return out, c, V, T
o3, c3, V3, T3 = pairs(F3); of, cf, Vf, Tf = pairs(FIN)
m3 = c3[:, 2] > 1.40
print('F3: overlap pairs total', len(o3), ' with centroid z>1.40 (head):', int(m3.sum()), ' z<=1.40 (old lower body feet/hands):', int((~m3).sum()))
# are the merged's 32 the same pairs as F3's head pairs (compare by triangle vertex positions)
def key(V, T, i): return frozenset(tuple(V[v].astype(np.float32).tolist()) for v in T[i])
s3 = set(frozenset([key(V3, T3, i), key(V3, T3, j)]) for (i, j), z in zip(o3, c3[:, 2]) if z > 1.40)
sf = set(frozenset([key(Vf, Tf, i), key(Vf, Tf, j)]) for (i, j) in of)
print('merged pairs', len(of), ' identical (by position) to F3 head pairs:', len(sf & s3), ' only merged:', len(sf - s3), ' only F3 head:', len(s3 - sf))
print('merged pairs: x range [%.4f, %.4f] z range [%.4f, %.4f]' % (cf[:, 0].min(), cf[:, 0].max(), cf[:, 2].min(), cf[:, 2].max()))
json.dump(dict(F3_total=len(o3), F3_head=int(m3.sum()), merged=len(of), identical=len(sf & s3)), open('data/overlap_attrib.json', 'w'))
