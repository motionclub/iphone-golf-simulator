"""Render mesh alpha masks for plate-aligned head panels. usage: blender -b --python sil_head.py -- coords.npy|base|file.blend prefix"""
import sys; sys.path.insert(0,'.')
from lib import *
argv=sys.argv[sys.argv.index('--')+1:]
arg=argv[0]; pre=argv[1]
if arg=='base': load(None)
elif arg.endswith('.blend'): load(None, blend=arg)
else: load(arg)
clay_setup()
s=bpy.context.scene; s.render.film_transparent=True; s.render.image_settings.color_mode='RGBA'
k=0.0013043874429196725
zc=1.7046599388122559-((66+352)/2-76)*k; ycl=0.065+((440+834)/2-712)*k
W1=410;H1=286;Wl=394
shot(f'{pre}_front.png',(0,-0.04,zc),0,0,W1*k,(W1*2,H1*2))
shot(f'{pre}_left.png',(0,ycl,zc),90,0,Wl*k,(Wl*2,H1*2))
print('SIL_HEAD_DONE')
