import sys; sys.path.insert(0,'.')
from lib import *
argv=sys.argv[sys.argv.index('--')+1:]
blend=argv[0]; pre=argv[1]
load(None, blend=blend); clay_setup()
s=bpy.context.scene; s.render.film_transparent=False
c=(0.605,-0.105,0.875)
for name,az,el in [('front',0,0),('threequarter',35,-12),('left',90,0)]:
    shot(f'{pre}_{name}.png', c, az, el, 0.30, (700,700))
print('HAND_VIEWS_DONE')
