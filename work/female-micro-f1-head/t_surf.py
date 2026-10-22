import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, geo, feat_f
H = geo.Head()
for x in (0.0, 0.03, 0.06, 0.09, 0.098):
    P, u = H.surf_xz(np.array([x]), np.array([1.5556]))
    print(x, np.round(P[0], 4))
ep = H.ear
print('ear h samples', [round(float(ep.h(np.array([y]), np.array([1.54]))[0]) * 1000, 2) for y in (-0.01, -0.005, 0.0, 0.01, 0.02, 0.03, 0.038, 0.041, 0.045)])
