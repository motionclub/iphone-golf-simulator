import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L
import pickle
d = np.load(H.W/'data/proxy_L3.npz')
V = d['V']; F = d['F']
lf = L.Loft()
P, rp, rl = L.remap(V, lf)
hi = V[:,2] > 1.655
Fv = lf.implicit(P[hi])
print('implicit after remap (dome zone): mean %.4f  max|F| %.4f' % (Fv.mean(), np.abs(Fv).max()))
bad = np.abs(Fv) > 0.02
print('bad count', int(bad.sum()), 'of', int(hi.sum()))
if bad.any():
    Pb = P[hi][bad]; Vb = V[hi][bad]
    print('bad sample (remap)', Pb[:5]); print('bad sample (orig)', Vb[:5])
# distribution of z for dome verts, as a function of radius from the axis
Ph = P[hi]; rr = np.hypot(Ph[:,0], Ph[:,1] - lf.at(Ph[:,2])['yw'])
for lo, hi_ in ((0,0.01),(0.01,0.02),(0.02,0.03),(0.03,0.04),(0.04,0.05)):
    m=(rr>=lo)&(rr<hi_)
    print('r in [%.0f,%.0f) mm: n=%d  z mean %.4f min %.4f max %.4f' % (lo*1000, hi_*1000, m.sum(), Ph[m,2].mean(), Ph[m,2].min(), Ph[m,2].max()))
