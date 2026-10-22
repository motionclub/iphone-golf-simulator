import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R
a = args_after_dashes()
bpy.ops.wm.open_mainfile(filepath=a[0])
sock = bpy.data.objects['Hand_Racket']
sock.rotation_euler = (math.radians(90), 0, 0); sock.location = (0, 0, 0.60)
col = bpy.data.objects['Collider_Racket']
col.hide_render = False
col.display_type = 'SOLID'
mat = bpy.data.materials.new('Col'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.2, 0.2, 1)
col.data.materials.append(mat)
mod = col.modifiers.new('wf', 'WIREFRAME'); mod.thickness = 0.002
bpy.context.view_layer.update()
R.studio(bg=(0.36, 0.37, 0.39), samples=24)
R.shot(a[1] + '_front.png', (0, 0, 0.60 + 0.24), az=0, el=0, dist=2.4, lens=85, res=(700, 1100))
R.shot(a[1] + '_side.png', (0, 0, 0.60 + 0.24), az=90, el=0, dist=2.4, lens=85, res=(700, 1100))
