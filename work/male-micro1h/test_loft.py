"""Radial-remap the Micro1f cage head onto the plate loft; silhouette table + renders.  blender -b --factory-startup --python test_loft.py"""
import sys, pickle, json
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L

V = np.load(H.W / 'data/V_micro1f.npy')
F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
lf = L.Loft()
head = (V[:, 2] > 1.40) & (np.abs(V[:, 0]) < 0.16)
P, rp, rl = L.remap(V[head], lf)
V2 = V.copy(); V2[head] = P
print('moved head verts', int(head.sum()), 'max move mm', float(np.abs(P - V[head]).max() * 1000))

# silhouette table vs plate (section extents of the remapped mesh)
E = set()
for f in F:
    for i in range(len(f)):
        a, b = int(f[i]), int(f[(i + 1) % len(f)]); E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
pe = H.plate_extents()


def section(Vv, z):
    a = Vv[E[:, 0]]; b = Vv[E[:, 1]]
    m = ((a[:, 2] - z) * (b[:, 2] - z) < 0)
    a = a[m]; b = b[m]
    t = (z - a[:, 2]) / (b[:, 2] - a[:, 2])
    p = a + (b - a) * t[:, None]
    return p[np.abs(p[:, 0]) < 0.14]


print('row   z      plateW  meshW   d | plate yf   mesh yf  d(mm)| plate yb  mesh yb d(mm)')
for r in range(84, 262, 6):
    z = float(H.zrow(r)); p = section(V2, z)
    if len(p) == 0: continue
    i = list(pe['rows']).index(r)
    mw = (p[:, 0].max() - p[:, 0].min()) * 1000
    pw = pe['hw'][i] * 2000
    print(f"{r:3d} {z:.4f} {pw:7.1f} {mw:7.1f} {mw - pw:+6.1f} | {pe['yf'][i]:+.4f} {p[:, 1].min():+.4f} {(p[:, 1].min() - pe['yf'][i]) * 1000:+6.1f} | {pe['yb'][i]:+.4f} {p[:, 1].max():+.4f} {(p[:, 1].max() - pe['yb'][i]) * 1000:+6.1f}")

body = H.get_body(str(H.W / 'baseline/HeroBase_Male_Silhouette.blend'))
H.set_verts(body.data, V2)
for o in bpy.data.objects:
    if o.type == 'EMPTY' or o.name == 'Face_M': o.hide_render = True
H.setup_render()
out = H.W / 'r/loft0'; out.mkdir(parents=True, exist_ok=True)
for n in H.PANELS:
    H.head_shot(out / f'{n}.png', n)
H.shot(out / 'top.png', (0, -0.03, 1.60), 0, 89, 0.30, (900, 900))
H.shot(out / 'q3.png', (0, -0.04, 1.58), 40, 5, 0.34, (900, 900))
