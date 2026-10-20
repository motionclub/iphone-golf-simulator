import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy
from kitlib import *
from checklib import *
for g in ('male', 'female'):
    for f in 'RL':
        sh = np.load(f'{WORK}/data/shoe{f}_{g}.npz'); sk = np.load(f'{WORK}/data/sock{f}_{g}.npz')
        tsh, tsk = bvh(sh['V'], sh['F']), bvh(sk['V'], sk['F'])
        pairs = tsh.overlap(tsk)
        tg = [str(t) for t in sh['tagnames']]
        cnt = {}
        for a, b in pairs:
            t = tg[sh['T'][a]]
            cnt[t] = cnt.get(t, 0) + 1
        print(g, f, 'sock-vs-shoe overlapping triangle pairs:', len(pairs), cnt)
