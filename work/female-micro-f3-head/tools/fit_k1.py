"""contour refit with a fixed (larger) underside blend radius k1:  python3 fit_k1.py <k1> <out.json>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, fit_contour as fc
k1 = float(sys.argv[1]); out = sys.argv[2]
kw0 = dict(nf_smooth=1, smin=2, k1=k1)
coef, par, r0, H = fc.solve(kw0, free=('cxb',), lamp=(0.15,))
par = dict(par); par['k1'] = k1
json.dump(dict(ZK=fc.ZK.tolist(), coef=coef.tolist(), par={k: float(v) for k, v in par.items()}), open(out, 'w'), indent=1)
print('saved', out, par)
