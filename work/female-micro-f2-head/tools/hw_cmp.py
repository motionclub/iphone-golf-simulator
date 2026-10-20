"""front-view half-width of the lower face vs height: plate (sil.json front rows) vs mesh npz (dense z-slices).  python3 hw_cmp.py name=npz ..."""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml, slices as sl, fl
items = [a.split('=', 1) for a in sys.argv[1:]]
sil = json.load(open(fl.W / 'data/sil.json'))
rows = [r for r in range(196, 253) if sil['front'].get(str(r))]
zp = np.array([fl.zrow(r) for r in rows]); hwp = np.array([0.5 * (sil['front'][str(r)][1] - sil['front'][str(r)][0] + 1) * fl.K for r in rows])
cen = np.array([0.5 * (sil['front'][str(r)][1] + sil['front'][str(r)][0]) for r in rows])
res = {}
for name, path in items:
    V, F, d = ml.load(path); T = ml.tri_fan(F)
    out = []
    for z in zp:
        segs = sl.slice_axis(V, T, 2, float(z))
        if len(segs) == 0: out.append(np.nan); continue
        pts = segs.reshape(-1, 3)
        m = pts[:, 1] < 0.06
        out.append(np.abs(pts[m, 0]).max() if m.any() else np.nan)
    res[name] = np.array(out)
print('row   z(mm)  plate hw | ' + ' | '.join(f'{n:>8s} (d)' for n, _ in items))
for i in range(0, len(rows), 2):
    print(f'{rows[i]:4d} {zp[i]*1000:7.1f} {hwp[i]*1000:8.1f} | ' + ' | '.join(f'{res[n][i]*1000:8.1f} ({(res[n][i]-hwp[i])*1000:+5.1f})' for n, _ in items))
