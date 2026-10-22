"""Scale line-up: both locked hero bodies (copies, A-pose) + the racket standing upright, ortho front view with known px/m.
blender -b --factory-startup --python render_scale_lineup.py -- <racket.blend> <out.png>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
import render_lib as R

racket_blend, out = args_after_dashes()
reset_scene()
mat = bpy.data.materials.new('G'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.30, 0.30, 0.32, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
heights = {}
for tag, x in (('male', -1.0), ('female', 1.0)):
    b = load_body_copy(tag)
    b.location = (x, 0, 0)
    b.data.materials.clear(); b.data.materials.append(mat)
    co = mesh_co(b)
    heights[tag] = float(co[:, 2].max() - co[:, 2].min())
with bpy.data.libraries.load(racket_blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket')]
parts = {o.name: o for o in dst.objects}
for o in parts.values():
    bpy.context.scene.collection.objects.link(o)
parts['Collider_Racket'].hide_render = True
sock = parts['Hand_Racket']
sock.rotation_euler = (math.radians(90), 0, 0)
sock.location = (0.0, -0.05, 0.111)          # butt end at the floor (z = 0)
bpy.context.view_layer.update()
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
W_, H = 1900, 1300
scale = 3.4                                   # ortho_scale = metres across the image WIDTH (landscape)
R.shot(out, (0, 0, 0.95), az=0, el=0, dist=6.0, ortho=scale, res=(W_, H))
json.dump(dict(px_per_m=W_ / scale, center_z=0.95, image_w=W_, image_h=H, body_heights_m=heights, racket_length_m=0.688), open(out + '.json', 'w'))
print('LINEUP_DONE', heights)
