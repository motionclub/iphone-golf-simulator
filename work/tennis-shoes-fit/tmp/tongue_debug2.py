import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit/scripts')
import numpy as np, bpy
from kitlib import *
from checklib import *
g, f = 'female', 'R'
sh = np.load(f'{WORK}/data/shoe{f}_{g}_dbg.npz'); sk = np.load(f'{WORK}/data/sock{f}_{g}.npz')
tg = [str(t) for t in sh['tagnames']]; sktg = [str(t) for t in sk['tagnames']]
tsh, tsk = bvh(sh['V'], sh['F']), bvh(sk['V'], sk['F'])
pairs = tsh.overlap(tsk)
ti = tg.index('tongue')
rows = [(a, b) for a, b in pairs if sh['T'][a] == ti]
print('pairs', len(rows))
from collections import Counter
print('sock tags involved', Counter(sktg[sk['T'][b]] for a, b in rows))
a, b = rows[0]
print('tongue tri', sh['V'][sh['F'][a]].round(4).tolist())
print('sock tri', sk['V'][sk['F'][b]].round(4).tolist(), sktg[sk['T'][b]])
# tongue triangle area / normal, sock triangle normal
def tn(V, F, i):
    t = V[F[i]]; n = np.cross(t[1] - t[0], t[2] - t[0]); return n / np.linalg.norm(n), np.linalg.norm(n) / 2
print('tongue tri normal/area', tn(sh['V'], sh['F'], a), 'sock tri normal/area', tn(sk['V'], sk['F'], b))
# are overlapping tongue triangles part of the end cap (fan) or main body? count by vertex valence: use triangle area
areas = np.array([tn(sh['V'], sh['F'], a_)[1] for a_, b_ in rows])
print('overlapping tongue tri areas mm2: min/med/max', (areas.min() * 1e6).round(1), (np.median(areas) * 1e6).round(1), (areas.max() * 1e6).round(1))
