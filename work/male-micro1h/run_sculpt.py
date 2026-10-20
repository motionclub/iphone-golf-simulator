"""Iteration runner: proxy -> loft remap -> sculpt -> face parts -> plate-aligned renders (+Eevee close-ups).
blender -b --factory-startup --python run_sculpt.py -- <tag> [level=3] [parts=nose,orbit,...] [json-overrides] [--noparts] """
import sys, json, importlib, time
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX, sculpt as S, h1render as HR, faceparts as FP
for m in (H, L, PX, S, HR, FP): importlib.reload(m)
argv = [a for a in sys.argv[sys.argv.index('--') + 1:]]
noparts = '--noparts' in argv; argv = [a for a in argv if not a.startswith('--')]
tag = argv[0]; level = int(argv[1]) if len(argv) > 1 else 3
DEFAULT = 'nose,orbit,brow,cheek,eye,mouth,ear'
parts = tuple((argv[2] if len(argv) > 2 else DEFAULT).split(','))
over = json.loads(argv[3]) if len(argv) > 3 else {}
t0 = time.time()
V, F = PX.build_proxy(level)
lf = L.Loft()
P0, _, _ = L.remap(V, lf)
N0 = PX.vertex_normals(P0, F)
P1, info = S.apply(P0, N0, over, parts, F=F)
print('sculpt', info, 'secs %.1f' % (time.time() - t0))
np.save(H.W / f'data/P_{tag}.npy', P1)

bpy.ops.wm.read_factory_settings(use_empty=True)
Fh = FP.cut_eye_openings(P1, F) if ('eye' in parts) else np.asarray(F)
skin = H.make_mesh_object('proxy', P1, [f for f in Fh])
objs = []
if 'eye' in parts and not noparts:
    objs += [FP.make_eyeball(-1), FP.make_eyeball(+1)]
if not noparts:
    bvh = FP.bvh_of(P1, F)
    objs += [FP.make_brow(-1, bvh), FP.make_brow(+1, bvh)]
# silhouette sheet (workbench, transparent)
HR.setup(transparent=True)
out = HR.render_set(tag)
# Eevee close-ups
skin.data.materials.clear(); skin.data.materials.append(H.skin_material())
H.setup_eevee(res=(900, 900))
extra = {
    'head_front': ((0, -0.05, 1.58), 0, 0, 0.30, (900, 900)),
    'head_q3L': ((0, -0.05, 1.58), 32.5, 0, 0.30, (900, 900)),
    'head_q3R': ((0, -0.05, 1.58), 30.0, 0, 0.30, (900, 900)),
    'head_side': ((0, -0.05, 1.58), 90, 0, 0.30, (900, 900)),
    'face_front': ((0, -0.1, 1.55), 0, 0, 0.16, (900, 900)),
    'face_q3L': ((0, -0.1, 1.55), 32.5, 0, 0.16, (900, 900)),
    'face_q3R': ((0, -0.1, 1.55), 30.0, 0, 0.16, (900, 900)),
    'face_side': ((0, -0.1, 1.55), 90, 0, 0.16, (900, 900)),
    'face_below': ((0, -0.1, 1.53), 15, -40, 0.12, (900, 900)),
    'eye_front': ((0.036, -0.1, 1.585), 0, 0, 0.07, (900, 900)),
    'eye_q3L': ((0.0, -0.1, 1.585), 32.5, 0, 0.12, (900, 900)),
    'ear_side': ((0.09, -0.0115, 1.5628), 90, 0, 0.11, (900, 900)),
    'ear_front': ((0.09, -0.0115, 1.5628), 0, 0, 0.11, (900, 900)),
    'ear_back': ((0.09, -0.0115, 1.5628), 150, 8, 0.12, (900, 900)),
}
for n, (t, az, el, sc, res) in extra.items():
    H.shot(out / f'{n}.png', t, az, el, sc, res)
print('rendered', tag, 'secs %.1f' % (time.time() - t0))
