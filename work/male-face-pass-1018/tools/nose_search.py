import sys, json, itertools, numpy as np
sys.argv=['x']; import nose_fit as F, nose_off as NO, off
v1 = json.load(open(NO.HERE + '/nose/v1.json'))
ys = np.arange(-30, -63, -2.0); ref = np.interp(ys, F.ref[::-1, 0], F.ref[::-1, 1])
ysn = np.arange(8, -9, -2.0); refn = np.interp(ysn, F.ref[::-1, 0], F.ref[::-1, 1])
def score(over):
    G = NO.head(over); _, g = off.slices(G, NO.h.tri, ys, xlim=4); _, gn = off.slices(G, NO.h.tri, ysn, xlim=4)
    o = np.nanmin(gn) - np.min(refn); d = g - (ref + o); return np.sqrt(np.nanmean(d * d)), np.nanmax(np.abs(d)), d
best = []
for ty, tsy, ta, fl, nb in itertools.product([-.052, -.055, -.058], [.016, .019, .022, .025], [.032, .038, .044], [(-.064, -.056), (-.066, -.060)], [.70, .85]):
    o = dict(v1); o.update(tip_y=ty, tip_sy=tsy, tip_amp=ta, nose_floor=list(fl), nose_blend=nb); r, m, d = score(o); best.append((r, m, o))
best.sort(key=lambda b: b[0])
for r, m, o in best[:6]: print(round(r, 2), round(m, 2), {k: o[k] for k in ("tip_y", "tip_sy", "tip_amp", "nose_floor", "nose_blend")})
json.dump(best[0][2], open(NO.HERE + '/nose/s1.json', 'w'))
