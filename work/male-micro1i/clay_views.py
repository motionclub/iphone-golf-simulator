"""Clay contact sheet of the head from several angles (Eevee, studio rig).  blender -b --factory-startup --python clay_views.py -- <blend> <outdir> [tag]"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material())
m_sc = bpy.data.materials.get('Face_Sclera')
H.setup_eevee(res=(700, 700), key=3.2, ambient=0.5)
VIEWS = {'f': (0, 0), 'q41': (41, 0), 'q41_lo': (41, -22), 'q41_hi': (41, 25), 'prof': (90, 0), 'f_lo': (0, -25), 'q60': (60, 5), 'f_hi': (0, 25)}
for n, (az, el) in VIEWS.items():
    H.shot(out / f'{n}.png', (0, -0.06, 1.53), az, el, 0.30, (700, 700))
print('clay done')
