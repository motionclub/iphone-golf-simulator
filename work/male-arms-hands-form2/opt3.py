"""Bounded random-search fit of the hand parameters to the plate silhouettes (ROI xor, weighted) with anatomy-preserving bounds.
python opt3.py <iters> <seed> [start.json] -> data/opt3_best.json"""
import sys, json, time
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import evalp
SPACE = {   # name: (lo, hi)  -- anatomy-first bounds (depth/width <= 1.3, moderate splay, real IP bend)
    'r_a': (0.0114, 0.0128), 'r_n': (0.0148, 0.0164), 'kp_scale': (1.0, 1.25), 'flex_scale': (1.0, 3.5), 'mcp_flex': (-3.0, 6.0),
    'len_scale': (0.97, 1.04), 'splay_scale': (0.5, 1.4), 'thumb_r_scale': (0.94, 1.10), 'thumb_len_scale': (0.92, 1.06),
    'thumb_pitch': (-0.004, 0.010), 'thumb_ip_bend': (10.0, 28.0), 'gap': (0.0034, 0.0050),
}
KEYS = list(SPACE)
def decode(x): return {k: float(SPACE[k][0] + x[i] * (SPACE[k][1] - SPACE[k][0])) for i, k in enumerate(KEYS)}
def encode(p, base):
    return np.array([np.clip((p.get(k, base.get(k)) - SPACE[k][0]) / (SPACE[k][1] - SPACE[k][0]), 0, 1) for k in KEYS])
WEIGHT = {'bald_front': 1.0, 'bald_back': 1.0, 'sheet_front': 0.55, 'sheet_back': 0.55}
def cost(P):
    r = evalp.evaluate(P, full=True)
    c = sum(WEIGHT[k.rsplit('_', 1)[0]] * v for k, v in r['roi'].items())
    f = r['full']
    pen = 600 * max(0, f['bald_front'] - 4.55) + 600 * max(0, f['bald_back'] - 4.55)
    return c + pen, r
if __name__ == '__main__':
    iters = int(sys.argv[1]); seed = int(sys.argv[2]); rng = np.random.default_rng(seed)
    import hand3
    base = dict(hand3.P0)
    x = encode(json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}, base)
    c0, r0 = cost(decode(x)); best = (c0, x.copy(), r0); sigma = 0.18; succ = 0; tries = 0; t = time.time()
    print('start', round(c0, 1), r0['roi_total'], r0['full'])
    for it in range(iters):
        xn = np.clip(best[1] + rng.normal(0, sigma, len(KEYS)) * (rng.random(len(KEYS)) < 0.5), 0, 1)
        c, r = cost(decode(xn)); tries += 1
        if c < best[0]:
            best = (c, xn, r); succ += 1
        if tries % 20 == 0:
            sigma = sigma * (1.25 if succ / 20 > 0.2 else 0.8); sigma = float(np.clip(sigma, 0.02, 0.35)); succ = 0
        if it % 50 == 0: print(it, round(best[0], 1), best[2]['roi_total'], best[2]['full'], 'sigma %.3f' % sigma, '%.0fs' % (time.time() - t), flush=True)
    P = decode(best[1]); json.dump(dict(params=P, cost=best[0], result=best[2]), open(W / 'data/opt3_best.json', 'w'), indent=1)
    print('BEST', round(best[0], 1), best[2]['roi_total'], best[2]['full']); print(json.dumps(P))
