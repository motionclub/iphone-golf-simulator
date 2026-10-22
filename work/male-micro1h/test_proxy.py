"""Build the dense CC proxy, remap to the loft, render.  blender -b --factory-startup --python test_proxy.py -- <level>"""
import sys, time
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX

level = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else 3
t0 = time.time()
V, F = PX.build_proxy(level)
print('proxy', V.shape, F.shape, 'secs', round(time.time() - t0, 1))
lf = L.Loft()
P, rp, rl = L.remap(V, lf)
# edge length stats
E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 3]], F[:, [3, 0]]])
el = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1) * 1000
for lo, hi in ((1.43, 1.5), (1.5, 1.6), (1.6, 1.7)):
    m = (V[E[:, 0], 2] > lo) & (V[E[:, 0], 2] <= hi)
    print('edge mm z', lo, hi, 'mean %.2f min %.2f max %.2f' % (el[m].mean(), el[m].min(), el[m].max()))
bpy.ops.wm.read_factory_settings(use_empty=True)
o = H.make_mesh_object('proxy', P, [f for f in F])
H.setup_render()
out = H.W / 'r/proxy0'; out.mkdir(parents=True, exist_ok=True)
for n in H.PANELS:
    H.head_shot(out / f'{n}.png', n)
H.shot(out / 'q3.png', (0, -0.04, 1.58), 40, 5, 0.34, (900, 900))
