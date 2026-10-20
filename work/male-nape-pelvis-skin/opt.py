"""Parallel pattern search of the pelvis model parameters against the plate band-pass correlation.
python3.13 opt.py <base_params.json|-> <tag_prefix> [iters] [workers]
Objective J = weighted mean of metric regions (back_glute, front_groin, q3BL, q3BR, back_lumbar).  Params bounded to plausible ranges."""
import sys, json, copy, os, shutil, time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
import np_model6 as M
import metric as MT

SPEC = [  # path, lo, hi, step, is_int      (stage 2: plausibility bounds - cleft <= ~13 mm deep, >= ~2 cm wide)
    ('rear.cleft.scale', 0.0, 0.75, 0.15, False), ('rear.cleft.s0', 0.012, 0.040, 0.006, False), ('rear.cleft.s1', 0.009, 0.022, 0.003, False),
    ('rear.fold.A', 0.0, 6.0, 1.5, False), ('rear.fold.k', 0.0, 1.4, 0.3, False), ('rear.fold.sig', 0.008, 0.030, 0.006, False),
    ('rear.blur.sig', 0.004, 0.045, 0.006, False), ('rear.smile', 0.0, 2.5, 0.5, False), ('rear.shift.A', 0.0, 10.0, 2.0, False),
    ('gap.k', 0.0, 0.65, 0.12, False), ('gap.arch', 0.0, 10.0, 2.0, False),
    ('fillet.iters', 0, 40, 8, True), ('fillet.hz', 0.010, 0.050, 0.010, False), ('fillet.u1', 0.06, 0.16, 0.03, False),
    ('front.groove.A', 0.0, 8.0, 2.0, False), ('front.groove.sig', 0.008, 0.024, 0.004, False), ('front.mound.A', 0.0, 8.0, 2.0, False),
    ('front.blur.sig', 0.004, 0.040, 0.006, False), ('smooth.iters', 0, 16, 4, True)]
SRMAX, MU = 1.25, 3.0      # penalise render relief amplitude above 1.25x the plate's (band-passed std ratio)
W8 = {'back_glute': 1.5, 'front_groin': 1.0, 'q3BL_glute': 0.7, 'q3BR_glute': 0.7, 'back_lumbar': 0.3}

def getp(P, path):
    d = P
    for k in path.split('.'): d = d[k]
    return d
def setp(P, path, v):
    ks = path.split('.'); d = P
    for k in ks[:-1]: d = d[k]
    d[ks[-1]] = v

def evaluate(P, tag, keep=False):
    V, _ = M.build(P); np.save(f'data/V_{tag}.npy', V)
    r = MT.score(tag); J = sum(W8[k] * r[k] for k in W8) / sum(W8.values())
    pen = sum(W8[k] * max(0.0, r[k + '_sr'] - SRMAX) for k in ('back_glute', 'front_groin')) / sum(W8.values()); J -= MU * pen
    if not keep: shutil.rmtree(f'r/{tag}_m', ignore_errors=True); os.remove(f'data/V_{tag}.npy')
    return J, r

def main():
    base = json.loads(json.dumps(M.DEF))
    if sys.argv[1] != '-': M.deep_merge(base, json.load(open(sys.argv[1])))
    pre = sys.argv[2]; iters = int(sys.argv[3]) if len(sys.argv) > 3 else 10; nw = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    cur = copy.deepcopy(base); steps = {p[0]: p[3] for p in SPEC}
    J0, r0 = evaluate(cur, pre + '_c0', keep=False); print('start J %.4f' % J0, {k: round(v, 3) for k, v in r0.items()}, flush=True)
    best_J, best_r = J0, r0; log = []
    for it in range(iters):
        t0 = time.time(); cands = []
        for (path, lo, hi, st, isint) in SPEC:
            for sgn in (+1, -1):
                v = getp(cur, path) + sgn * steps[path]; v = min(max(v, lo), hi); v = int(round(v)) if isint else float(v)
                if v == getp(cur, path): continue
                P = copy.deepcopy(cur); setp(P, path, v); cands.append((path, v, P))
        def run(i): path, v, P = cands[i]; J, r = evaluate(P, f'{pre}_t{i % nw}_{i}', keep=False); return i, J, r
        with ThreadPoolExecutor(nw) as ex: res = list(ex.map(run, range(len(cands))))
        res.sort(key=lambda t: -t[1]); i, J, r = res[0]
        print(f'iter {it}: {len(cands)} cands in {time.time()-t0:.0f}s best {cands[i][0]}={cands[i][1]} J {J:.4f} (cur {best_J:.4f})', flush=True)
        if J > best_J + 1e-4:
            setp(cur, cands[i][0], cands[i][1]); best_J, best_r = J, r
            # also accept further non-conflicting improvements greedily (up to 3)
            for j, Jj, rj in res[1:4]:
                if Jj > best_J - 0.002 and cands[j][0] != cands[i][0]:
                    P2 = copy.deepcopy(cur); setp(P2, cands[j][0], cands[j][1]); J2, r2 = evaluate(P2, f'{pre}_g{j}', keep=False)
                    if J2 > best_J + 1e-4: cur = P2; best_J, best_r = J2, r2; print(f'   + {cands[j][0]}={cands[j][1]} J {J2:.4f}', flush=True)
        else:
            for k in steps: steps[k] *= 0.5
            print('   no improvement -> halve steps', flush=True)
        log.append(dict(it=it, J=best_J, r={k: round(v, 4) for k, v in best_r.items()}))
        json.dump(cur, open(f'data/P_{pre}_best.json', 'w'), indent=1); json.dump(log, open(f'data/log_{pre}.json', 'w'), indent=1)
    V, _ = M.build(cur); np.save(f'data/V_{pre}_best.npy', V); print('FINAL J %.4f' % best_J, {k: round(v, 3) for k, v in best_r.items()})
if __name__ == '__main__': main()
