"""Build the final graded head with error-driven refinement and assemble the full body; report stats; render.
blender -b --factory-startup --python run_stage2.py -- <tag> [eps_mm=0.2] [maxlev=3] [minface=1]"""
import sys, pickle, time, json, importlib
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T, h1render as HR, faceparts as FP, wire
for m in (H, L, PX, S, S2, T, HR, FP): importlib.reload(m)
argv = sys.argv[sys.argv.index('--') + 1:]
tag = argv[0]; eps = float(argv[1]) * 1e-3 if len(argv) > 1 else 2e-4
maxlev = int(argv[2]) if len(argv) > 2 else 2
minface = int(argv[3]) if len(argv) > 3 else 1
t0 = time.time()
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi()
phi.attach_cc(Vcc, Fcc)
Vn, Fn, info = S2.build_final(V, F, phi, eps=eps, max_level=maxlev, min_face_level=minface)
print({k: v for k, v in info.items() if k not in ('used', 'depth')}, 'secs %.1f' % (time.time() - t0))
fidx = T.region_faces(V, F)
P1 = phi.stage1(Vn)
P2, _ = S.stage2(P1, Fn, S.PRM, phi.parts)
V_all, F_all, ring = S2.assemble(V, F, fidx, info['used'], Vn, Fn, P2)
tris = sum(len(f) - 2 for f in F_all)
print('full mesh verts', len(V_all), 'faces', len(F_all), 'tris', tris, ' (orig 49304)  head tris', info['tris'])
np.save(H.W / f'data/Vfinal_{tag}.npy', V_all)
pickle.dump([list(map(int, f)) for f in F_all], open(H.W / f'data/Ffinal_{tag}.pkl', 'wb'))
# edge-length stats in the face zone
E = set()
for f in Fn:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
el = np.linalg.norm(P2[E[:, 0]] - P2[E[:, 1]], axis=1) * 1000
zc = 0.5 * (P2[E[:, 0], 2] + P2[E[:, 1], 2]); yc = 0.5 * (P2[E[:, 0], 1] + P2[E[:, 1], 1])
face = (zc > 1.47) & (zc < 1.63) & (yc < -0.02)
print('face-zone edge mm: mean %.2f median %.2f p5 %.2f p95 %.2f max %.2f' % (el[face].mean(), np.median(el[face]), np.percentile(el[face], 5), np.percentile(el[face], 95), el[face].max()))
print('head edge mm: mean %.2f' % el.mean())
# render
bpy.ops.wm.read_factory_settings(use_empty=True)
H.make_mesh_object('Body_M', V_all, F_all)
HR.setup(transparent=True)
out = HR.render_set(tag)
frontv = (P2[:, 1] < -0.045)
wire.plot(P2, E, frontv, (0, 2), (-0.075, 0.075, 1.44, 1.64), 1400, str(out / 'wire_front.png'), pts=False)
wire.plot(P2, E, (P2[:, 0] > 0.0), (1, 2), (-0.06, 0.03, 1.50, 1.62), 1200, str(out / 'wire_ear.png'), pts=False)
print('done', tag)
