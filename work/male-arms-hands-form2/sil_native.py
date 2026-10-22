"""blender -b <blend> --python sil_native.py -- <outdir> : Blender-native alpha masks from the six Locked_* cameras (Body_M only)"""
import bpy, sys
from pathlib import Path
out = Path(sys.argv[sys.argv.index('--') + 1]); out.mkdir(parents=True, exist_ok=True)
s = bpy.context.scene
s.render.film_transparent = True; s.render.image_settings.color_mode = 'RGBA'; s.render.image_settings.file_format = 'PNG'
s.render.resolution_x = 1280; s.render.resolution_y = 720; s.render.resolution_percentage = 100
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_M': o.hide_render = True
for n in ['bald_front', 'bald_back', 'left', 'right', 'sheet_front', 'sheet_back']:
    cam = bpy.data.objects['Locked_' + n]; s.camera = cam; s.render.filepath = str(out / (n + '.png')); bpy.ops.render.render(write_still=True)
print('SIL_NATIVE_DONE')
