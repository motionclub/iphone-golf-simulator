"""Ortho front render of the racket for reference comparison. blender -b --python render_front_ortho.py -- <blend> <out.png> [zoom]"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

a = args_after_dashes()
blend, out = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=blend)
sock = bpy.data.objects['Hand_Racket']
sock.rotation_euler = (math.radians(90), 0, 0)
sock.location = (0, 0, 0.60)
bpy.context.view_layer.update()
bpy.data.objects['Collider_Racket'].hide_render = True
R.studio(bg=(0.45, 0.46, 0.48), samples=32)
# framing: racket from butt (-0.111) to top (0.577) -> centre y ~ 0.233 above grip centre
R.shot(out, (0, 0, 0.60 + 0.233), az=0, el=0, dist=3.0, ortho=0.80, res=(700, 1400))
print('ORTHO_DONE')
