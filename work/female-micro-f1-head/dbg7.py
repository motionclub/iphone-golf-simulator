import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, geo, facef, feat_f
poly = feat_f.eye_poly(6); I = feat_f.IRIS; c = np.array([I['cx'], I['cz']])
phis = np.linspace(0, 2*np.pi, 40, endpoint=False)
Rp = np.array([facef._ray_poly(poly, c, ph) for ph in phis])
print(np.round(Rp*1000, 1))
print('iris', I)
