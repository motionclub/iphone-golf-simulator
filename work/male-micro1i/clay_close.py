"""Close-up clay renders (Eevee) of a region from several angles.  blender -b --factory-startup --python clay_close.py -- <blend> <outdir> <name> <tx> <ty> <tz> <scale> [facem=1]"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
name = argv[2]; tgt = tuple(float(v) for v in argv[3:6]); scale = float(argv[6]); fm = (argv[7] == '1') if len(argv) > 7 else True
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material())
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = not fm
H.setup_eevee(res=(800, 800), key=3.2, ambient=0.5)
for az, el, tag in ((0, 0, 'f'), (41, 0, 'q'), (90, 0, 's'), (0, 22, 'hi'), (41, 20, 'qhi'), (41, -20, 'qlo')):
    H.shot(out / f'{name}_{tag}.png', tgt, az, el, scale, (800, 800))
print('close done')
