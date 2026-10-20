"""Hard-light clay comparison of the lower face / cheek for several blends.
blender -b --factory-startup --python clay_l.py -- <outdir> <views comma> <light=hard|rake|soft> <tag:blend> [<tag:blend> ...]
views: front, q41, qm41, side, under_f, under_q, cheek_q, cheek_f   -> <outdir>/<light>_<view>_<tag>.png and sheet <outdir>/<light>_<views>.png"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
from PIL import Image, ImageDraw
argv = sys.argv[sys.argv.index('--') + 1:]
out = Path(argv[0]); out.mkdir(parents=True, exist_ok=True)
views = argv[1].split(','); light = argv[2]; items = [a.split(':', 1) for a in argv[3:]]
RES = 640
# name -> (az, el, target, ortho scale)
VIEWS = {'front': (0, 0, (0, -0.05, 1.50), 0.24), 'q41': (41, 0, (0, -0.05, 1.50), 0.24), 'qm41': (-41, 0, (0, -0.05, 1.50), 0.24), 'side': (90, 0, (0, -0.05, 1.50), 0.24),
         'under_f': (0, -28, (0, -0.06, 1.47), 0.20), 'under_q': (40, -26, (0, -0.06, 1.47), 0.20), 'cheek_q': (41, 0, (0.03, -0.06, 1.53), 0.17), 'cheek_f': (0, 0, (0.0, -0.06, 1.53), 0.20),
         'cheek_qm': (-41, 0, (-0.03, -0.06, 1.53), 0.17), 'jaw_q': (55, -8, (0.03, -0.06, 1.48), 0.17), 'jaw_s': (90, -6, (0, -0.08, 1.48), 0.17),
         'temple_q': (62, 6, (0.05, -0.06, 1.545), 0.20), 'temple_f': (20, 8, (0.06, -0.07, 1.54), 0.20), 'chin_zoom': (0, -4, (0, -0.08, 1.462), 0.085), 'chin_zoom_q': (30, -4, (0.01, -0.08, 1.462), 0.10), 'back_q': (140, 4, (0, -0.03, 1.50), 0.20), 'jaw_f': (0, -6, (0, -0.07, 1.48), 0.17), 'jaw_q3': (38, -4, (0, -0.07, 1.49), 0.19), 'mouth_f': (0, 0, (0, -0.05, 1.502), 0.062), 'mouth_q': (38, 0, (0, -0.05, 1.502), 0.062), 'mouth_s': (90, 0, (0, -0.12, 1.502), 0.062), 'mouth_qlo': (30, -22, (0, -0.05, 1.502), 0.062)}
LIGHTS = {'hard': ((0.75, -0.45, -0.5), 3.6, 0.33), 'rake': ((0.97, -0.1, -0.2), 3.8, 0.28), 'soft': (None, 3.2, 0.5), 'top': ((0.2, -0.95, -0.3), 3.6, 0.3), 'low': ((0.5, 0.7, -0.5), 3.6, 0.3)}
for tag, blend in items:
    bpy.ops.wm.open_mainfile(filepath=blend); H._cam = None
    for o in bpy.data.objects:
        if o.type == 'EMPTY': o.hide_render = True
    body = bpy.data.objects['Body_M']
    body.data.materials.clear(); body.data.materials.append(H.skin_material(rough=0.6, sss=0.0))
    face = bpy.data.objects.get('Face_M')
    if face: face.hide_render = True
    d, key, amb = LIGHTS[light]
    if d is None: H.setup_eevee(res=(RES, RES), key=key, ambient=amb)
    else:
        H.setup_eevee(res=(RES, RES), key=0.5, fill=0.0, ambient=amb)
        for nm in ('h1_key', 'h1_fill', 'h1_rim'):
            if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
        dl = bpy.data.lights.new('hl', 'SUN'); dl.energy = key; dl.angle = math.radians(6)
        ob = bpy.data.objects.new('hl', dl); bpy.context.scene.collection.objects.link(ob)
        ob.parent = H.camera(); ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = Vector(d).normalized().to_track_quat('-Z', 'Y')
    import os
    if os.environ.get('CLAY_NOSHADOW') == '1':
        bpy.context.scene.eevee.use_shadows = False
    for v in views:
        az, el, tgt, sc = VIEWS[v]
        H.shot(out / f'{light}_{v}_{tag}.png', tgt, az, el, sc, (RES, RES))
tags = [t for t, _ in items]
sheet = Image.new('RGB', (RES * len(tags), RES * len(views)))
for r, v in enumerate(views):
    for c, t in enumerate(tags):
        im = Image.open(out / f'{light}_{v}_{t}.png').convert('RGB'); ImageDraw.Draw(im).text((8, 6), f'{t} {v} {light}', fill=(255, 255, 0)); sheet.paste(im, (c * RES, r * RES))
sheet.save(out / f'{light}_{"-".join(views)}.png'); print('clay done', out / f'{light}_{"-".join(views)}.png', sheet.size)
