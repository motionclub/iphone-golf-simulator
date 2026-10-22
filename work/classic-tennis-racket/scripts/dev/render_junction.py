import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R
a = args_after_dashes()
bpy.ops.wm.open_mainfile(filepath=a[0])
sock = bpy.data.objects['Hand_Racket']
sock.rotation_euler = (math.radians(90), 0, 0); sock.location = (0, 0, 0.60)
bpy.context.view_layer.update()
bpy.data.objects['Collider_Racket'].hide_render = True
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
# left-lower junction of the head (racket x=-0.11, y=0.30) -> world (x, z) = (-0.11, 0.60+0.30)
for name, az, el in (('a', 0, 0), ('b', -50, 20), ('c', 50, -20), ('d', 90, 0)):
    R.shot(a[1] + f'_{name}.png', (-0.09, 0, 0.60 + 0.29), az=az, el=el, dist=0.45, lens=85, res=(800, 800))
