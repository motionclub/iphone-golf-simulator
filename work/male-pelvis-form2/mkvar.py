"""Build several variants of model v2: python3 mkvar.py '<tag>=<json overrides>' ...   (overrides deep-merged on DEF) -> data/V_<tag>.npy"""
import sys, json
sys.path.insert(0, '.')
import numpy as np, f2_model2 as M, quality as Q
for a in sys.argv[1:]:
    tag, _, js = a.partition('='); P = json.loads(json.dumps(M.DEF)); M.deep_merge(P, json.loads(js) if js else {})
    V, info = M.build(P); np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
    q = Q.stats(V); d = np.linalg.norm(V - M.V0, axis=1) * 1000
    print(f'{tag:6s} moved {int((d > 1e-4).sum()):5d} max {d.max():5.1f} mm  dihedral p99 {q["p99"]:.1f} max {q["max"]:.1f} new_sharp {q["new_sharp"]}')
