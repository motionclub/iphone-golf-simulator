import sys; sys.path.insert(0,'.')
from lib import *
argv=sys.argv[sys.argv.index('--')+1:]
arg=argv[0]; out=Path(argv[1]); out.mkdir(parents=True,exist_ok=True)
load(None, blend=arg)
s=bpy.context.scene
s.render.film_transparent=True; s.render.image_settings.color_mode='RGBA'; s.render.image_settings.file_format='PNG'
s.render.resolution_x=1280; s.render.resolution_y=720; s.render.resolution_percentage=100
for view in ['left','right']:
    s.camera=bpy.data.objects['Locked_'+view]; s.render.filepath=str((out/(view+'.png')).resolve()); bpy.ops.render.render(write_still=True)
print('SIL_SIDE_DONE')
