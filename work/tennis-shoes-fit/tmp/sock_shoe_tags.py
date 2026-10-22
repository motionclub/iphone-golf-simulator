import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy
from kitlib import *
from checklib import *
for g in ('male', 'female'):
    for f in 'RL':
        sh = np.load(f'{WORK}/data/shoe{f}_{g}.npz'); sk = np.load(f'{WORK}/data/sock{f}_{g}.npz')
        tg = [str(t) for t in sh['tagnames']]
        sktg = [str(t) for t in sk['tagnames']]
        out_ids = [i for i, t in enumerate(sktg) if t.endswith('_out')]
        vo = sk['V'][np.unique(sk['F'][np.isin(sk['T'], out_ids)])]
        res = {}
        for i, t in enumerate(tg):
            m = sh['T'] == i
            if not m.any():
                continue
            tr = bvh(sh['V'], sh['F'][m])
            d = nearest_dist(tr, vo[vo[:, 2] < 0.12])
            k = int(np.argmin(d))
            res[t] = (round(float(d.min() * 1000), 2), vo[vo[:, 2] < 0.12][k].round(3).tolist())
        best = sorted(res.items(), key=lambda kv: kv[1][0])[:5]
        print(g, f, best)
