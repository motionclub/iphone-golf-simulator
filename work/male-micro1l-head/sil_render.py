"""Render the mesh silhouette (Body_M only) with the blend's locked cameras -> <outdir>/<view>.png (alpha).  blender -b --factory-startup --python sil_render.py -- <blend> <outdir>"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
from pathlib import Path
import numpy as np, bpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); outdir = Path(argv[1]); outdir.mkdir(parents=True, exist_ok=True)
sc = bpy.context.scene
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True
for view in ('bald_front', 'bald_back'):
    sc.camera = bpy.data.objects['Locked_' + view]; sc.render.filepath = str((outdir / f'{view}.png').resolve()); bpy.ops.render.render(write_still=True)
print('sil done')
