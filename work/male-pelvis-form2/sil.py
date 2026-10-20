"""Gate silhouette renders (blend's own workbench setup, transparent film) for front/back/left/right.
blender -b --factory-startup --python sil.py -- <blend|npy> <outdir> [withface 0|1]"""
import sys
from pathlib import Path
import numpy as np, bpy
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]; out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True); wf = len(argv) > 2 and argv[2] == '1'
if src.endswith('.npy'):
    bpy.ops.wm.open_mainfile(filepath=str(W / 'baseline/HeroBase_Male_Silhouette.blend')); V = np.load(src)
    bpy.data.objects['Body_M'].data.vertices.foreach_set('co', V.astype(np.float64).ravel()); bpy.data.objects['Body_M'].data.update()
else: bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
f = bpy.data.objects.get('Face_M')
if f: f.hide_render = not wf
for v in ('bald_front', 'bald_back', 'left', 'right'):
    cam = bpy.data.objects['Locked_' + v]; sc.camera = cam; sc.render.filepath = str((out / f'{v}.png').resolve()); bpy.ops.render.render(write_still=True)
print('SIL_DONE')
