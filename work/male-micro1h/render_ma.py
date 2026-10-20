"""Head-only Eevee renders (transparent) at the multiangle yaws, for overlay on face_lock crops 09-16.
blender -b --factory-startup --python render_ma.py -- <final.blend> <outdir>"""
import sys, math
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
me = body.data
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
faces = [list(p.vertices) for p in me.polygons if all(V[i, 2] > 1.40 for i in p.vertices)]
used = sorted({i for f in faces for i in f}); rem = {v: k for k, v in enumerate(used)}
head = H.make_mesh_object('HeadOnly', V[used], [[rem[i] for i in f] for f in faces]); head.data.materials.append(H.skin_material())
body.hide_render = True
H.setup_eevee(res=(1000, 1000), transparent=True, key=4.8, ambient=0.8)
for az in (0, 180, 90, -90, 35, -35, 145, -145, 30, -30, 40, -40):
    H.shot(out / f'az{az}.png', (0.0, -0.03, 1.58), az, 0, 0.50, (1000, 1000))
print('ma renders done')
