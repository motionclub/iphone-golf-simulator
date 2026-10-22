"""Ear close-ups: smooth-shaded clay vs flat-shaded clay + wireframe overlay, 3/4 and top views.  blender -b --python ear_geo.py -- <blend> <outdir>"""
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
body = bpy.data.objects['Body_M']; face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
body.data.materials.clear(); body.data.materials.append(H.skin_material(rough=0.7, sss=0.0))
H.setup_eevee(res=(900, 900), key=3.0, ambient=0.5)
tgt = (0.09, -0.0115, 1.572)
for az, el, tag in ((41, 0, 'q41'), (70, 10, 'q70'), (0, 0, 'f'), (90, 0, 's'), (0, 60, 'top'), (120, 10, 'b120')):
    H.shot(out / f'smooth_{tag}.png', tgt, az, el, 0.10, (900, 900))
# flat shading + wireframe modifier
for p in body.data.polygons: p.use_smooth = False
try:
    body.data.free_normals_split()
except Exception: pass
try:
    body.data.attributes.remove(body.data.attributes['sharp_face'])
except Exception: pass
wm = body.modifiers.new('wire', 'WIREFRAME'); wm.thickness = 0.00012; wm.use_replace = False
mat_w = bpy.data.materials.new('wire_m'); mat_w.use_nodes = True; mat_w.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1)
body.data.materials.append(mat_w); wm.material_offset = 1
for az, el, tag in ((41, 0, 'q41'), (0, 0, 'f'), (90, 0, 's'), (0, 60, 'top')):
    H.shot(out / f'flat_{tag}.png', tgt, az, el, 0.10, (900, 900))
print('ear geo done')
