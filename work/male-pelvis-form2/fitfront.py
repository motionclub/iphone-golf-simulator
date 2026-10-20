"""Evolutionary fit of the FRONT (groin) terms against the front / front-3/4 plate views under the standard rig.
python3 fitfront.py [generations] [lambda] [workers]   -> data/fitfront_best.json, prints progress; every eval renders into r/ff<k>_f/"""
import sys, os, json, time, copy
import numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
import f2_model2 as M, fitmetric as FM, quality as Q
BASE = json.loads(json.dumps(M.DEF)); M.deep_merge(BASE, json.load(open('data/P_FINAL0.json')))
PARAMS = [  # (path, lo, hi, init)
    (('mound', 'A'), 0.0, 8.0, 8.0), (('mound', 'su'), 0.035, 0.07, 0.05), (('mound', 'z'), 0.80, 0.87, 0.835), (('mound', 'sz'), 0.02, 0.05, 0.038),
    (('fpinch', 'k'), 0.0, 0.7, 0.5), (('fpinch', 'u1'), 0.025, 0.05, 0.040), (('fpinch', 'u2'), 0.06, 0.10, 0.085), (('fseam', 'iters'), 10, 150, 80),
    (('roof', 'f0'), 0.2, 1.0, 0.45), (('fseam', 'zc'), 0.77, 0.80, 0.78), (('fseam', 'hz'), 0.012, 0.03, 0.02)]
def make(theta):
    P = copy.deepcopy(BASE)
    for (path, lo, hi, init), t in zip(PARAMS, theta):
        v = lo + (hi - lo) * float(np.clip(t, 0, 1)); P[path[0]][path[1]] = int(round(v)) if path[1] == 'iters' else v
    P['mound']['on'] = P['fpinch']['on'] = P['fseam']['on'] = True
    return P
def evaluate(args):
    k, theta = args; tag = f'ff{k}'
    try:
        P = make(theta); V, info = M.build(P); np.save(f'data/V_{tag}.npy', V); q = Q.stats(V)
        FM.render_fit(tag, ['front', 'fl', 'fr']); L, res = FM.score(tag, ['front', 'fl', 'fr'])
        pen = 0.02 * max(0.0, q['max'] - 55.0) + 0.05 * max(0.0, q['p99'] - 33.0)
        return L + pen, L, q['max'], q['p99']
    except Exception as e:
        return 9.0, 9.0, 0, 0
def to_theta(P):
    return np.array([(P[p[0]][p[1]] - lo) / (hi - lo) for (p, lo, hi, init), in [((a,),) for a in PARAMS]]) if False else np.array([(BASE[a[0][0]][a[0][1]] - a[1]) / (a[2] - a[1]) for a in PARAMS])
if __name__ == '__main__':
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 10; lam = int(sys.argv[2]) if len(sys.argv) > 2 else 12; nw = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    rng = np.random.default_rng(7); n = len(PARAMS); mean = to_theta(BASE); sig = np.full(n, 0.18); best = (1e9, mean.copy(), None)
    mu = lam // 2; w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1)); w /= w.sum()
    with ProcessPoolExecutor(nw) as ex:
        L0 = evaluate((999, mean)); print('start (FINAL0) loss', L0, flush=True)
        for g in range(gens):
            pop = np.clip(mean + sig * rng.standard_normal((lam, n)), 0, 1); pop[0] = mean
            res = list(ex.map(evaluate, [(i, pop[i]) for i in range(lam)])); L = np.array([r[0] for r in res]); order = np.argsort(L)
            if L[order[0]] < best[0]: best = (L[order[0]], pop[order[0]].copy(), res[order[0]])
            el = pop[order[:mu]]; new = (w[:, None] * el).sum(0); step = np.sqrt(((el - mean) ** 2 * w[:, None]).sum(0)) + 1e-3
            sig = np.clip(0.7 * sig + 0.3 * np.maximum(step, 0.04), 0.04, 0.3); mean = new
            print(f'gen {g}: best this gen {L[order[0]]:.4f}  overall {best[0]:.4f}  (maxdih {best[2][2]:.0f}, p99 {best[2][3]:.1f})  mean sigma {sig.mean():.3f}', flush=True)
            Pb = make(best[1]); json.dump(dict(loss=best[0], P=Pb, theta=best[1].tolist()), open('data/fitfront_best.json', 'w'), indent=1)
    print('done; best loss', best[0], 'start loss', L0[0])
