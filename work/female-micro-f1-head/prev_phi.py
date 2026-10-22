import sys, time
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, fl, geo, loftf
H = geo.Head()
u, nth, nph = geo.sphere_grid(200, 130)
t = time.time(); P = H.phi(u); print('phi', time.time() - t, P.shape)
# cut at the neck collar z<1.40 -> drop
F = []
for i in range(nph - 1):
    for j in range(nth):
        a = i * nth + j; b = i * nth + (j + 1) % nth; c = (i + 1) * nth + (j + 1) % nth; d = (i + 1) * nth + j
        F.append([a, b, c, d])
keep = [f for f in F if all(P[v, 2] > 1.405 for v in f)]
print(len(F), len(keep))
loftf.save_npz(str(fl.W / 'data/prev_phi.npz'), P, keep)
