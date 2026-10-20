"""Test graded subdivision of the cage head region.  blender -b --factory-startup --python test_topo.py"""
import sys, pickle, time
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, topo as T, wire
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
fidx = T.region_faces(V, F)
print('region cage faces', len(fidx))
t0 = time.time()
Vn, Fn, info = T.build_graded(V, F, fidx)
print({k: v for k, v in info.items() if k != 'used'}, 'secs %.1f' % (time.time() - t0))
E = set()
for f in Fn:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
el = np.linalg.norm(Vn[E[:, 0]] - Vn[E[:, 1]], axis=1) * 1000
zc = 0.5 * (Vn[E[:, 0], 2] + Vn[E[:, 1], 2])
for lo, hi in ((1.43, 1.47), (1.47, 1.53), (1.53, 1.60), (1.60, 1.72)):
    m = (zc > lo) & (zc <= hi)
    print(f'edge mm z {lo}-{hi}: mean {el[m].mean():.2f} min {el[m].min():.2f} max {el[m].max():.2f}')
sel = np.ones(len(Vn), bool)
out = H.W / 'r/topo0'; out.mkdir(parents=True, exist_ok=True)
front = Vn[:, 1] < -0.045
wire.plot(Vn, E, front, (0, 2), (-0.10, 0.10, 1.43, 1.68), 1300, str(out / 'wire_front.png'), pts=False)
wire.plot(Vn, E, (Vn[:, 0] > 0), (1, 2), (-0.10, 0.08, 1.43, 1.68), 1300, str(out / 'wire_side.png'), pts=False)
np.savez(H.W / 'data/graded_v0.npz', V=Vn, F=np.array(Fn, dtype=object), used=np.array(info['used']))
print('done')
