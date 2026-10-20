"""coronal (y=const) and plan (z=const) section comparison of several mesh npz files.  python3 sections.py out_prefix  name=npz [name=npz ...]"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, meshlib as ml, slices as sl, fl, json
from plot2d import plot2d
pref = sys.argv[1]; items = [a.split('=', 1) for a in sys.argv[2:]]
cols = [(255, 90, 60), (255, 235, 90), (110, 255, 140), (90, 200, 255), (210, 130, 255)]
meshes = []
for name, path in items:
    V, F, d = ml.load(path); meshes.append((name, V, ml.tri_fan(F)))
def section(axis, val, keep=None):
    out = []
    for k, (name, V, T) in enumerate(meshes):
        segs = sl.slice_axis(V, T, axis, val)
        polys = sorted(sl.chain(segs), key=len, reverse=True)
        out.append(polys)
    return out
# coronal sections: y = -105 (chin front), -85, -65, -45 mm ; axis=1 ; plot (x mm, z mm)
sil = json.load(open(fl.W / 'data/sil.json'))
fr = [(fl.xcol(0) * 0, 0)]
for yv in (-0.105, -0.085, -0.065, -0.050):
    secs = section(1, yv)
    cur = []
    for k, polys in enumerate(secs):
        for j, p in enumerate(polys[:2]):
            cur.append((np.stack([p[:, 0] * 1000, p[:, 2] * 1000], 1), cols[k], 2, meshes[k][0] if j == 0 else ''))
    plot2d(cur, (-75, 75, 1415, 1500), 9.0, f'{pref}_coronal_y{int(-yv*1000)}.png', grid=2.0, label_every=10, title=f'coronal y={yv*1000:.0f} (x mm, z mm)')
for zv in (1.430, 1.436, 1.442, 1.448, 1.456, 1.470):
    secs = section(2, zv)
    cur = []
    for k, polys in enumerate(secs):
        for j, p in enumerate(polys[:2]):
            m = p[:, 1] < -0.02
            if m.sum() > 2: cur.append((np.stack([p[m, 0] * 1000, -p[m, 1] * 1000], 1), cols[k], 2, meshes[k][0] if j == 0 else ''))
    plot2d(cur, (-80, 80, 25, 135), 8.0, f'{pref}_plan_z{int(zv*1000)}.png', grid=5.0, label_every=10, title=f'plan z={zv*1000:.0f} (x mm, -y mm: front at top)')
print('done')
