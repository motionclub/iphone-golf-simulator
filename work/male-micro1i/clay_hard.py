"""Hard-light clay views (single strong sun from a chosen direction + low ambient) to reveal facets.  blender -b --factory-startup --python clay_hard.py -- <blend> <outdir> <name> <tx> <ty> <tz> <scale>"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
name = argv[2]; tgt = tuple(float(v) for v in argv[3:6]); scale = float(argv[6])
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
body.data.materials.clear(); body.data.materials.append(H.skin_material(rough=0.6, sss=0.0))
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
s = bpy.context.scene
H.setup_eevee(res=(800, 800), key=0.5, fill=0.0, ambient=0.35)
for nm in ('h1_key', 'h1_fill', 'h1_rim'):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
def sun(nm, direction, energy):
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = energy; d.angle = math.radians(6)
    ob = bpy.data.objects.new(nm, d); bpy.context.scene.collection.objects.link(ob)
    ob.parent = H.camera(); ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = Vector(direction).normalized().to_track_quat('-Z', 'Y')
sun('hl', (0.8, -0.35, -0.5), 3.4)           # camera-local: from the left, slightly above
for az, el, tag in ((0, 0, 'f'), (41, 0, 'q'), (90, 0, 's'), (41, -25, 'qlo'), (0, -30, 'flo')):
    H.shot(out / f'{name}_{tag}.png', tgt, az, el, scale, (800, 800))
print('hard done')
