import sys, numpy as np, json
a = np.load(sys.argv[1]); b = np.load(sys.argv[2])
def polys(D):
    cv, ls, lt = D['corner_verts'], D['loop_start'], D['loop_total']
    return [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
pa, pb = polys(a), polys(b)
def canon(p):
    p = list(p); k = p.index(min(p)); return tuple(p[k:] + p[:k])
from collections import Counter
res = dict(verts_equal=bool(a['V'].shape == b['V'].shape and np.array_equal(a['V'], b['V'])), polys_equal_multiset=Counter(map(canon, pa)) == Counter(map(canon, pb)), n_a=len(pa), n_b=len(pb),
           normals_equal=bool(a['custom_normal_i16'].shape == b['custom_normal_i16'].shape))
if res['verts_equal']:
    res['max_vertex_diff_mm'] = float(np.abs(a['V'] - b['V']).max() * 1000)
print(json.dumps(res))
