"""Hard-light clay views of the neck/jaw (Body_M only).  blender -b --factory-startup --python neck_views.py -- <blend> <outdir> [mode=hard|soft] [target z] [scale]
Writes <outdir>/<view>.png and <outdir>/sheet.png (labelled contact sheet)."""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
from PIL import Image, ImageDraw
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
mode = argv[2] if len(argv) > 2 else 'hard'
tz = float(argv[3]) if len(argv) > 3 else 1.45
scale = float(argv[4]) if len(argv) > 4 else 0.27
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material(rough=0.6, sss=0.0))
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
RES = 760
if mode == 'hard':
    H.setup_eevee(res=(RES, RES), key=0.5, fill=0.0, ambient=0.33)
    for nm in ('h1_key', 'h1_fill', 'h1_rim'):
        if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    d = bpy.data.lights.new('hl', 'SUN'); d.energy = 3.6; d.angle = math.radians(6)
    ob = bpy.data.objects.new('hl', d); bpy.context.scene.collection.objects.link(ob)
    ob.parent = H.camera(); ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = Vector((0.75, -0.45, -0.5)).normalized().to_track_quat('-Z', 'Y')
else:
    H.setup_eevee(res=(RES, RES), key=3.2, ambient=0.5)
VIEWS = [('side', 90, 0), ('back', 180, 0), ('back145', 145, 0), ('backhi', 160, 22), ('front', 0, 0), ('q35', 35, 0), ('under_f', 0, -28), ('under_q', 40, -26)]
tgt = (0.0, -0.015, tz)
for n, az, el in VIEWS:
    H.shot(out / f'{n}.png', tgt, az, el, scale, (RES, RES))
tiles = [(n, Image.open(out / f'{n}.png').convert('RGB')) for n, _, _ in VIEWS]
cols = 4; rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * RES, rows * RES))
for i, (n, im) in enumerate(tiles):
    ImageDraw.Draw(im).text((8, 6), n, fill=(255, 255, 0)); sheet.paste(im, ((i % cols) * RES, (i // cols) * RES))
sheet = sheet.resize((sheet.width * 2 // 3, sheet.height * 2 // 3), Image.LANCZOS); sheet.save(out / 'sheet.png')
print('neck views done', out)
