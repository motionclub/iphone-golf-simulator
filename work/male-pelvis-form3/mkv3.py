"""Build FORM3 variants:  python3 mkv3.py [--base data/P_X.json] 'tag={json overrides}' ...  -> data/V_<tag>.npy, data/P_<tag>.json  (uses f3_model; base default = model DEF merged with data/P_FINAL6.json cleft/lateral/pin tuning)"""
import sys, json
sys.path.insert(0, '.')
import numpy as np, f3_model as M, quality as Q
a = sys.argv[1:]; base = 'data/P_F3BASE.json'
if a and a[0] == '--base': base = a[1]; a = a[2:]
for s in a:
    tag, _, js = s.partition('='); P = json.loads(json.dumps(M.DEF)); M.deep_merge(P, json.load(open(base))); M.deep_merge(P, json.loads(js) if js else {})
    V, info = M.build(P); np.save(f'data/V_{tag}.npy', V); json.dump(P, open(f'data/P_{tag}.json', 'w'), indent=1)
    q = Q.stats(V); d = np.linalg.norm(V - M.V0, axis=1) * 1000; dd = Q.dihedral(V)
    print(f'{tag:8s} moved {int((d > 1e-4).sum()):5d} max {d.max():5.1f} mm  dihedral p99 {q["p99"]:.1f} max {q["max"]:.1f} (zone edges) new_sharp {q["new_sharp"]}')
