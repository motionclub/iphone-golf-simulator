"""Stage-2 + eye carve test: close-up renders of the lids/eyeballs.  blender -b --factory-startup --python test_eyes.py"""
import sys, pickle, importlib
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX, sculpt as S, stage2 as S2, topo as T, finalize as FZ, faceparts as FP
for m in (H, L, PX, S, S2, T, FZ, FP): importlib.reload(m)
V = np.load(H.W / 'data/V_micro1f.npy'); F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
Vcc, Fcc = PX.build_proxy(3)
phi = S2.Phi(); phi.attach_cc(Vcc, Fcc)
Vn, Fn, info = S2.build_final(V, F, phi, max_level=2, verbose=False)
P1 = phi.stage1(Vn); P2, _ = S.stage2(P1, Fn, S.PRM, phi.parts)
P3, F3, einfo = FZ.carve_eyes(P2, Fn)
print({k: (v['removed'], v['n']) for k, v in einfo.items()})
bpy.ops.wm.read_factory_settings(use_empty=True)
skin = H.make_mesh_object('Body_M', P3, F3)
skin.data.materials.append(H.skin_material())
for side in (-1, 1):
    Ve, Fe, mat = FZ.eyeball_mesh(side)
    o = H.make_mesh_object(f'Eye{side}', Ve, Fe)
    cols = {0: (0.95, 0.93, 0.89), 1: (0.353, 0.204, 0.094), 2: (0.04, 0.025, 0.015), 3: (0.12, 0.065, 0.035), 4: (1, 1, 1)}
    mats = [H.flat_material(f'em{k}', cols[k], 0.25) for k in range(5)]
    for m_ in mats: o.data.materials.append(m_)
    for p_, m_ in zip(o.data.polygons, mat): p_.material_index = m_
H.setup_eevee(res=(900, 900))
out = H.W / 'r/eyes0'; out.mkdir(exist_ok=True, parents=True)
H.shot(out / 'eye_front.png', (0.036, -0.1, 1.585), 0, 0, 0.07, (900, 900))
H.shot(out / 'eyes_front.png', (0.0, -0.1, 1.585), 0, 0, 0.14, (900, 900))
H.shot(out / 'eye_q3L.png', (0.0, -0.1, 1.585), 32.5, 0, 0.12, (900, 900))
H.shot(out / 'eye_side.png', (0.04, -0.12, 1.585), 90, 0, 0.07, (900, 900))
print('ok')
