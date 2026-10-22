"""Plate vs mesh silhouette table (head only). blender -b --factory-startup --python cmp_sil0.py -- <blend> [verts.npy]
Mesh section extents at each plate row (z from calibration), plate extents from plates/sil.json."""
import sys, json
import numpy as np
import bpy

R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
K = 0.0013043874429196725; TOP = 1.7046599388122559
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body_M'].data
V = np.array([v.co[:] for v in me.vertices], float)
if len(argv) > 1:
    V = np.load(argv[1])
E = np.array([e.vertices[:] for e in me.edges])
sil = json.load(open(R + '/work/male-micro1h/plates/sil.json'))


def section(z):
    a = V[E[:, 0]]; b = V[E[:, 1]]
    m = ((a[:, 2] - z) * (b[:, 2] - z) < 0)
    a = a[m]; b = b[m]
    t = (z - a[:, 2]) / (b[:, 2] - a[:, 2])
    p = a + (b - a) * t[:, None]
    p = p[np.abs(p[:, 0]) < 0.25]
    return p


rows = []
print('row   z      | front plate W(mm) mesh W(mm) d | left-plate depth mesh depth d | plate nose/front-y  mesh front-y')
for r in range(80, 282, 6):
    z = TOP - (r - 76) * K
    p = section(z)
    # restrict the section to the head column (exclude shoulders): |x|<0.13 above z=1.43
    if z > 1.43:
        p = p[np.abs(p[:, 0]) < 0.13] if z < 1.51 or z > 1.60 else p[np.abs(p[:, 0]) < 0.14]
    if len(p) == 0: continue
    mw = (p[:, 0].max() - p[:, 0].min()) * 1000
    md = (p[:, 1].max() - p[:, 1].min()) * 1000
    fs = sil['front'].get(str(r)); ls = sil['left'].get(str(r))
    pw = (fs[-1][1] - fs[0][0]) * K * 1000 if fs else float('nan')
    pd = (ls[-1][1] - ls[0][0]) * K * 1000 if ls else float('nan')
    # plate front-y (profile left col -> y) with anchor col 712 <-> y=+0.065
    py = 0.065 - (712 - ls[0][0]) * K if ls else float('nan')
    print(f'{r:3d} {z:.4f} | {pw:7.1f} {mw:7.1f} {mw - pw:+6.1f} | {pd:7.1f} {md:7.1f} {md - pd:+6.1f} | {py:+.4f} {p[:, 1].min():+.4f}')
