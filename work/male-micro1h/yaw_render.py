"""Render the face at a list of yaws (ortho, plate scale, transparent) for the 3/4 plate framings, pupils pre-centred on the plate pupil mid.
blender -b --factory-startup --python yaw_render.py -- <blend> <outdir>"""
import sys, math
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, h1render as HR
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material())
H.setup_eevee(res=(856, 556), transparent=True, key=4.8, ambient=0.8)
K = H.K
PUP_MID = {'q3L': 176.5, 'q3R': 589.5}     # plate pupil mid columns (full plate px)
BOX = {'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
for name in ('q3L', 'q3R'):
    x0, y0, x1, y1 = BOX[name]; w, h = x1 - x0, y1 - y0
    cxp = (x0 + x1) / 2
    zc = H.TOP - (((y0 + y1) / 2) - HR.Q3_APEX_ROW) * K
    for az in range(24, 50, 2):
        a = math.radians(az)
        # image offset of the pupil mid from the panel centre (metres, +right): (PUP_MID - cxp) * K ; pupil mid world (0,-0.1254)
        ty = -0.1254 - ((PUP_MID[name] - cxp) * K) / math.sin(a)
        # camera right = (cos a, sin a); target (0, ty): u_mid - u_t = (-0.1254 - ty) sin a = (PUP_MID - cxp) K
        H.shot(out / f'{name}_{az}.png', (0.0, ty, zc), az, 0, w * K, (w * 2, h * 2))
print('yaw renders done')
