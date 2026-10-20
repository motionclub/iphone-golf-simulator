"""Render bald_front/back masks from locked cameras for given coords. usage: blender -b --python sil_body.py -- coords.npy|base outdir"""
import sys; sys.path.insert(0,'.')
from lib import *
argv=sys.argv[sys.argv.index('--')+1:]
arg=argv[0]
out=Path(argv[1]); out.mkdir(parents=True,exist_ok=True)
if arg=='base': load(None)
elif arg.endswith('.blend'): load(None, blend=arg)
else: load(arg)
s=bpy.context.scene
s.render.film_transparent=True; s.render.image_settings.color_mode='RGBA'; s.render.image_settings.file_format='PNG'
s.render.resolution_x=1280; s.render.resolution_y=720; s.render.resolution_percentage=100
# do NOT change engine/settings: use the blend's own render setup (Workbench, transparent film, 1280x720)
orig=s.camera
for view in ['bald_front','bald_back']:
    s.camera=bpy.data.objects['Locked_'+view]; s.render.filepath=str(out/(view+'.png')); bpy.ops.render.render(write_still=True)
s.camera=orig
print('SIL_BODY_DONE')
