"""opt4.py: bounded (mu,lambda)-ES over the FORM4 dome/wall parameters.  python3 tools/opt4.py <base.json> <tag> [gens] [procs]
Writes data/opt4_<tag>_best.json (full params) and data/opt4_<tag>_log.json.  Walls dF,dB are fixed from the base (front wall fit only touches z<1.12)."""
import sys, os, json, copy, time
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAMES = ['H', 'xc', 'zc', 'sxm', 'sxl', 'szd', 'szu', 'p', 'k', 'rot', 'wl_y', 'rd_R', 'p_lo', 'k_lo']
LO = np.array([0.014, 0.060, 1.200, 0.045, 0.045, 0.035, 0.050, 2.0, 1.8, -0.40, -0.1275, 0.0, 2.0, 1.6])
HI = np.array([0.034, 0.090, 1.232, 0.078, 0.078, 0.062, 0.082, 3.2, 3.2, 0.40, -0.1130, 0.014, 3.8, 3.6])

def to_params(base, x):
    P = copy.deepcopy(base)
    C = P['bm_list'][0]
    for n, v in zip(NAMES[:10], x[:10]):
        C[n] = float(v)
    P['wl_y'] = float(x[10]); P['rd_R'] = float(x[11]); P['bm_signed'] = 1
    C['p_lo'] = float(x[12]); C['k_lo'] = float(x[13])
    if x[11] > 1e-6:
        P.update(rd_bell=1, rd_zc=1.21, rd_wd=0.14, rd_wu=0.12, rd_x1=0.09)
    return P

_state = {}
def _init(base_path, wc_path):
    import torso4 as t4, score4
    _state['t4'] = t4; _state['sc'] = score4
    _state['base'] = json.load(open(base_path))
    _state['dF'], _state['dB'] = np.load(wc_path)

def _eval(x):
    t4, sc = _state['t4'], _state['sc']
    try:
        P = to_params(_state['base'], x)
        co = t4.build3(P, _state['dF'], _state['dB'])
        if not np.isfinite(co).all():
            return 99.0, {}
        r = sc.evaluate(co)
        return r['J'], r
    except Exception as e:
        return 99.0, {'err': str(e)}

if __name__ == '__main__':
    base_path, tag = sys.argv[1], sys.argv[2]
    gens = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    procs = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    base = json.load(open(base_path))
    wc_path = HERE + '/data/wc_try_m3.npy'
    C = base['bm_list'][0]
    x0 = np.array([C['H'], C['xc'], C['zc'], C['sxm'], C['sxl'], C['szd'], C['szu'], C['p'], C['k'], C.get('rot', 0.0), base['wl_y'], base.get('rd_R', 0.0), C.get('p_lo', C['p']), C.get('k_lo', C['k'])])
    x0 = np.clip(x0, LO, HI)
    rng = np.random.default_rng(7)
    mu, lam = 6, 18
    sigma = 0.18 * (HI - LO)
    mean = x0.copy()
    log = []
    best = (1e9, None, None)
    t0 = time.time()
    with Pool(procs, initializer=_init, initargs=(base_path, wc_path)) as pool:
        j0, r0 = pool.apply(_eval, (x0,))
        print('start J', round(j0, 3), {k: round(v, 3) for k, v in r0.items() if k in ('ncc1', 'ncc2', 'amp', 'rms_low', 'slope98', 'rc')}, flush=True)
        best = (j0, x0.copy(), r0)
        for g in range(gens):
            pop = np.clip(mean + rng.standard_normal((lam, len(x0))) * sigma, LO, HI)
            pop[0] = best[1]
            res = pool.map(_eval, list(pop))
            J = np.array([r[0] for r in res])
            order = np.argsort(J)
            sel = pop[order[:mu]]
            mean = 0.6 * mean + 0.4 * sel.mean(0)
            if J[order[0]] < best[0]:
                best = (float(J[order[0]]), pop[order[0]].copy(), res[order[0]][1])
            sigma *= 0.93
            r = best[2]
            print(f'gen {g:2d} best J {best[0]:.3f}  gen-best {J[order[0]]:.3f}  ncc {r.get("ncc1",0):.3f}/{r.get("ncc2",0):.3f} amp {r.get("amp",0):.2f} rms_low {r.get("rms_low",0):.1f} slope {r.get("slope98",0):.1f} Rc {r.get("rc",0):.1f}  [{time.time()-t0:.0f}s]', flush=True)
            log.append(dict(gen=g, best=best[0], x=best[1].tolist(), r=best[2]))
    P = to_params(base, best[1])
    json.dump(P, open(f'{HERE}/data/opt4_{tag}_best.json', 'w'), indent=1)
    json.dump(dict(names=NAMES, best_x=best[1].tolist(), best=best[2], log=log), open(f'{HERE}/data/opt4_{tag}_log.json', 'w'), indent=1)
    print('BEST', dict(zip(NAMES, np.round(best[1], 4))), best[2], flush=True)
