import sys, math
from pathlib import Path
import numpy as np, bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']; body.data.materials.clear(); body.data.materials.append(H.skin_material())
m_sc = bpy.data.materials.get('Face_Sclera')
H.setup_eevee(res=(900, 900), transparent=False, key=4.8, ambient=0.8)
for nm, (t, az, el, sc) in {'eyeR_front': ((0.0365, -0.12, 1.585), 0, 0, 0.06), 'eyeR_az50': ((0.0365, -0.12, 1.585), 50, 0, 0.07), 'eyeR_az80': ((0.045, -0.115, 1.585), 80, 0, 0.07), 'eyeR_top': ((0.0365, -0.12, 1.585), 0, 55, 0.07)}.items():
    H.shot(out / f'{nm}.png', t, az, el, sc, (900, 900))
print('eye zoom done')
